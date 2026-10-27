"""Built-in GPP statement/branch coverage (replaces tools/cov_patch.py).

Counting matches the review's cov_report.py: every executable statement line
counts (if/while headers, declarations, assignments, outputs, calls), else/
endif/endw do not; a line counts only when it ran.

``GPPL_COVERAGE_OUT=<file.json>``: every Engine in the process records into a
store keyed by the SHA-256 digest of its GPP source, so in-memory mutants (the
suite builds several) never count toward the real GPP. At exit the store is
*merged* into the file (read, merge, atomic replace, under a lock where the
platform has fcntl), so one process per session/suite accumulates correctly.
"""
import atexit
import json
import os

from . import nodes as N

FORMAT = 'gppl-coverage/2'


class Coverage:
    def __init__(self):
        self.lines = {}      # proc -> set(line)
        self.branches = {}   # (proc, line) -> set(bool)

    def merge(self, other):
        for proc, lines in other.lines.items():
            self.lines.setdefault(proc, set()).update(lines)
        for key, outcomes in other.branches.items():
            self.branches.setdefault(key, set()).update(outcomes)
        return self

    def as_json(self):
        return {'lines': {proc: sorted(lines) for proc, lines in self.lines.items() if lines},
                'branches': {f'{proc}:{line}': sorted(outcomes)
                             for (proc, line), outcomes in self.branches.items()}}

    @classmethod
    def from_json(cls, data):
        coverage = cls()
        for proc, lines in data.get('lines', {}).items():
            coverage.lines[proc] = set(lines)
        for key, outcomes in data.get('branches', {}).items():
            proc, line = key.rsplit(':', 1)
            coverage.branches[(proc, int(line))] = set(outcomes)
        return coverage

    def executed(self, proc, line):
        return line in self.lines.get(proc, ())

    def summary(self, program):
        rows = []
        total = hit = 0
        outcomes = seen = 0
        for name in program.procedures:
            lines = program.statement_lines(name)
            executed = self.lines.get(name, set())
            count = sum(1 for line in lines if line in executed)
            total += len(lines)
            hit += count
            rows.append((name, len(lines), count, [line for line in lines if line not in executed]))
        for name, proc in program.procedures.items():
            for stmt in program.walk(proc.body):
                if type(stmt) in (N.If, N.While):
                    outcomes += 2
                    seen += len(self.branches.get((name, stmt.line), ()))
        return {'total': total, 'hit': hit, 'percent': 100.0 * hit / total if total else 100.0,
                'branch_outcomes': outcomes, 'branch_outcomes_seen': seen,
                'branch_percent': 100.0 * seen / outcomes if outcomes else 100.0, 'rows': rows}

    def branch_gaps(self, program):
        gaps = []
        for name, proc in program.procedures.items():
            for stmt in program.walk(proc.body):
                if type(stmt) in (N.If, N.While):
                    seen = self.branches.get((name, stmt.line), set())
                    if len(seen) < 2:
                        state = 'never evaluated' if not seen else 'only ' + ('TRUE' if True in seen else 'FALSE')
                        gaps.append((name, stmt.line, state, stmt.text))
        return gaps

    def markdown(self, program, title='GPP statement coverage'):
        summary = self.summary(program)
        out = [f"# {title}: {summary['hit']}/{summary['total']} = {summary['percent']:.1f}% "
               f"(branch outcomes {summary['branch_outcomes_seen']}/{summary['branch_outcomes']} = "
               f"{summary['branch_percent']:.1f}%)\n",
               '| procedure | stmts | executed | % |', '|---|---|---|---|']
        for name, count, executed, _ in summary['rows']:
            percent = 100 * executed / count if count else 100
            out.append(f'| {name} | {count} | {executed} | {percent:.0f}% |')
        out.append('\n# Branch gaps (never evaluated / one-sided)\n')
        current = None
        for name, line, state, text in self.branch_gaps(program):
            if name != current:
                out.append(f'## @{name}')
                current = name
            out.append(f'- L{line} [{state}] `{text[:140]}`')
        return '\n'.join(out) + '\n'


class CoverageStore:
    """Process-wide coverage keyed by GPP source digest."""

    def __init__(self):
        self.by_digest = {}
        self.statements = {}

    def for_program(self, program):
        if program.digest not in self.by_digest:
            self.by_digest[program.digest] = Coverage()
            self.statements[program.digest] = sum(1 for _ in program.walk())
        return self.by_digest[program.digest]

    def dump(self, path):
        _merge_into_file(path, self.by_digest, self.statements)


def _merge_into_file(path, by_digest, statements=None):
    lock = None
    try:
        import fcntl                                     # POSIX only; Windows: unlocked merge
        lock = open(str(path) + '.lock', 'w')
        fcntl.flock(lock, fcntl.LOCK_EX)
    except (ImportError, OSError):
        lock = None
    try:
        data = {}
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as handle:
                    data = json.load(handle)
            except (OSError, ValueError):
                data = {}
        if data.get('format') != FORMAT:
            data = {'format': FORMAT, 'programs': {}}
        programs = data['programs']
        for digest, coverage in by_digest.items():
            entry = programs.get(digest, {})
            merged = Coverage.from_json(entry).merge(coverage)
            programs[digest] = dict(merged.as_json(),
                                    statements=(statements or {}).get(digest, entry.get('statements')))
        temporary = f'{path}.{os.getpid()}.tmp'
        with open(temporary, 'w', encoding='utf-8') as handle:
            json.dump(data, handle)
        os.replace(temporary, path)
    finally:
        if lock is not None:
            lock.close()


def load_for(program, path):
    """Coverage recorded for ``program`` (matched by source digest) in a coverage
    file; also reads the legacy flat {'lines','branches'} format."""
    with open(path, encoding='utf-8') as handle:
        data = json.load(handle)
    if data.get('format') == FORMAT:
        return Coverage.from_json(data['programs'].get(program.digest, {}))
    return Coverage.from_json(data)


PROCESS_STORE = CoverageStore()
_REGISTERED = []


def engine_coverage(program):
    """Coverage object for a new Engine: the process store when GPPL_COVERAGE_OUT
    is set, else a private Coverage."""
    path = os.environ.get('GPPL_COVERAGE_OUT')
    if not path:
        return Coverage()
    if not _REGISTERED:
        _REGISTERED.append(True)
        atexit.register(lambda: PROCESS_STORE.dump(os.environ.get('GPPL_COVERAGE_OUT') or path))
    return PROCESS_STORE.for_program(program)
