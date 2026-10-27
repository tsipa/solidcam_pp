"""GPP statement and branch coverage of the offline test suite.

usage (from the repository root):
    python -m pp_tests.coverage [--md report.md] [--json coverage.json]
                                [--fail-under PCT] [-k PATTERN] [--quiet]

Runs `unittest discover -s tests` in-process and records which statements of
the tested GPP run, with the engine the tests use:

* GPPL engine (default, pp_tests/gppl): the engine records statement lines and
  branch outcomes per program (pp_tests/gppl/coverage.py). This tool hooks the
  runtime's coverage factory, keeps one record per parsed program and counts a
  procedure only where its parsed body equals the tested GPP's (so mutated
  procedures of in-memory mutants do not count, as below). For a coverage file
  across processes use GPPL_COVERAGE_OUT and `python -m pp_tests.gppl coverage`.
* GPPL_ENGINE=legacy (pp_tests/gppl/legacy.py): sys.settrace hooked to the
  frames of the legacy Engine.call (LegacyCompatEngine and every other subclass
  execute the same code object), as described next.

Both modes report the same counting over the legacy (line, text) procedure
view, so their numbers are comparable.

Legacy mode: at three places of the statement loop it reads the frame locals
`name`, `number`, `active` (and `condition`):

  statement   the dispatch line `if low.startswith('while '):` runs once per
              GPP statement; the statement counts as executed when `active`
  if branch   `branches.append((active, condition, False))`: outcome
              `condition` of an `if` evaluated while `active`
  while       `loops.append(index - 1)` (condition true) and `nesting = 1`
              while `active` (condition false)

Only frames whose procedure body is the parse of the tested GPP count (stock
Engine parse or the LegacyCompatEngine parse of the same text, which rewrites
Print/trace lines in place): mutants built by the regression tests run other
text and are ignored for the mutated procedure. Statement counting matches the
baseline report (tools/cov_report.py): every procedure line except
else/endif/endw; each `if`/`while` contributes two branch outcomes.

Neither engine is modified; if the legacy statement loop changes, the anchor
lines below are no longer found and this tool stops with an explanation.
Procedures whose Print lines a helper rewrites (tests/program_session.py) do
not count from those runs in either mode.
The GPP is PP_TEST_SOURCE if set, else the shipped Gmill_540v_4x.gpp.
"""
import argparse
import inspect
import json
import os
import sys
import time
import unittest
from pathlib import Path

from .engine import Engine
from .gppl import legacy

LEGACY = Engine is legacy.Engine

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GPP = ROOT / 'siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.gpp'
NON_STATEMENTS = ('else', 'endif', 'endw')
ANCHORS = {
    'statement': "if low.startswith('while '):",
    'if': 'branches.append((active, condition, False))',
    'while_true': 'loops.append(index - 1)',
    'while_false': 'nesting = 1',
}


def anchor_lines():
    """Absolute line numbers of the anchor statements inside the legacy Engine.call."""
    lines, first = inspect.getsourcelines(legacy.Engine.call)
    found = {}
    for key, text in ANCHORS.items():
        hits = [first + offset for offset, line in enumerate(lines) if line.strip() == text]
        if len(hits) != 1:
            raise SystemExit(f'pp_tests/gppl/legacy.py changed: anchor {text!r} found {len(hits)} times in '
                             'Engine.call; update pp_tests/coverage.py ANCHORS')
        found[key] = hits[0]
    return found


class Recorder:
    """Collects (procedure, line) hits from Engine.call frames of the tested GPP."""

    def __init__(self, references):
        self.references = references            # procedure name -> list of accepted bodies
        self.code = legacy.Engine.call.__code__
        anchors = anchor_lines()
        self.line_statement = anchors['statement']
        self.line_if = anchors['if']
        self.line_while_true = anchors['while_true']
        self.line_while_false = anchors['while_false']
        self.statements = {}
        self.branches = {}
        self._accepted = {}                     # id(body) -> (body, accepted?)

    def _accept(self, frame):
        values = frame.f_locals                 # at the 'call' event only the arguments exist
        try:
            name = values['procedure'].lstrip('@').lower()
            body = values['self'].procedures[name]
        except (AttributeError, KeyError, TypeError):
            return False
        key = id(body)
        cached = self._accepted.get(key)
        if cached is None or cached[0] is not body:
            cached = (body, any(body == reference for reference in self.references.get(name, ())))
            self._accepted[key] = cached        # keep body alive so the id stays unique
        return cached[1]

    def global_trace(self, frame, event, arg):
        if event == 'call' and frame.f_code is self.code:
            return self.local_trace if self._accept(frame) else None
        return None

    def local_trace(self, frame, event, arg):
        if event != 'line':
            return self.local_trace
        line = frame.f_lineno
        if line == self.line_statement:
            values = frame.f_locals
            if values['active']:
                self.statements.setdefault(values['name'], set()).add(values['number'])
        elif line == self.line_if:
            values = frame.f_locals
            if values['active']:
                self.branches.setdefault((values['name'], values['number']), set()).add(bool(values['condition']))
        elif line == self.line_while_true:
            values = frame.f_locals
            self.branches.setdefault((values['name'], values['number']), set()).add(True)
        elif line == self.line_while_false:
            values = frame.f_locals
            if values['active']:
                self.branches.setdefault((values['name'], values['number']), set()).add(False)
        return self.local_trace


def reference_bodies(source):
    """Accepted procedure bodies: legacy parse plus the LegacyCompatEngine parse (if importable)."""
    references = {}
    for name, body in legacy.Engine(source).procedures.items():
        references.setdefault(name, []).append(body)
    try:
        from support.legacy_compat import LegacyCompatEngine
    except ImportError:
        return references
    for name, body in LegacyCompatEngine(source).procedures.items():
        if body not in references.get(name, []):
            references.setdefault(name, []).append(body)
    return references


class GpplRecorder:
    """Statement lines and branch outcomes from the GPPL engine's own coverage records.

    install() replaces the runtime's coverage factory: every Engine built from
    the same program text shares one Coverage. collect() keeps a procedure's
    records only where the program's parsed body equals the tested GPP's.
    """

    def __init__(self, source):
        from .gppl.program import load_program
        self.reference = {name: list(proc.raw) for name, proc in load_program(source).procedures.items()}
        self.programs = {}                      # digest -> (program, Coverage)
        self.statements = {}
        self.branches = {}
        self._saved = None

    def coverage_for(self, program):
        from .gppl.coverage import Coverage
        entry = self.programs.get(program.digest)
        if entry is None:
            entry = self.programs[program.digest] = (program, Coverage())
        return entry[1]

    def install(self):
        from .gppl import runtime
        self._saved = runtime.engine_coverage
        runtime.engine_coverage = self.coverage_for

    def uninstall(self):
        from .gppl import runtime
        runtime.engine_coverage = self._saved

    def collect(self):
        for program, coverage in self.programs.values():
            accepted = {name for name, proc in program.procedures.items()
                        if self.reference.get(name) == list(proc.raw)}
            for name, lines in coverage.lines.items():
                if name in accepted:
                    self.statements.setdefault(name, set()).update(lines)
            for (name, line), outcomes in coverage.branches.items():
                if name in accepted:
                    self.branches.setdefault((name, line), set()).update(outcomes)
        return self


def compress(numbers):
    """[1,2,3,7] -> 'L1-3, L7'."""
    numbers = sorted(numbers)
    spans, start, last = [], None, None
    for number in numbers:
        if start is None:
            start = last = number
        elif number == last + 1:
            last = number
        else:
            spans.append((start, last))
            start = last = number
    if start is not None:
        spans.append((start, last))
    return ', '.join(f'L{a}' if a == b else f'L{a}-{b}' for a, b in spans)


def build_report(source, recorder):
    rows = []
    totals = dict(statements=0, executed=0, branches=0, taken=0)
    for name, body in legacy.Engine(source).procedures.items():
        statements = [number for number, line in body if line.lower() not in NON_STATEMENTS]
        hit = recorder.statements.get(name, set())
        executed = [number for number in statements if number in hit]
        decisions = [(number, line) for number, line in body if line.lower().startswith(('if ', 'while '))]
        branch_rows, taken = [], 0
        for number, line in decisions:
            seen = recorder.branches.get((name, number), set())
            taken += len(seen)
            if len(seen) < 2:
                state = 'never evaluated' if not seen else ('only TRUE' if True in seen else 'only FALSE')
                branch_rows.append(dict(line=number, state=state, code=line))
        rows.append(dict(procedure=name, statements=len(statements), executed=len(executed),
                         missing=[n for n in statements if n not in hit],
                         branches=2 * len(decisions), taken=taken, partial=branch_rows))
        totals['statements'] += len(statements)
        totals['executed'] += len(executed)
        totals['branches'] += 2 * len(decisions)
        totals['taken'] += taken
    return dict(totals=totals, procedures=rows)


def percent(part, whole):
    return 100.0 * part / whole if whole else 100.0


def markdown(report, gpp, tests_summary):
    t = report['totals']
    out = [f'# GPP coverage of the offline test suite',
           '',
           f'GPP: `{gpp}`  ',
           f'Tests: {tests_summary}',
           '',
           f'- Statements: {t["executed"]}/{t["statements"]} = {percent(t["executed"], t["statements"]):.1f}%',
           f'- Branch outcomes (if/while true and false): {t["taken"]}/{t["branches"]} = '
           f'{percent(t["taken"], t["branches"]):.1f}%',
           '',
           '| procedure | statements | executed | % | branch outcomes | % |',
           '|---|---|---|---|---|---|']
    for row in report['procedures']:
        out.append(f'| {row["procedure"]} | {row["statements"]} | {row["executed"]} | '
                   f'{percent(row["executed"], row["statements"]):.0f}% | {row["taken"]}/{row["branches"]} | '
                   f'{percent(row["taken"], row["branches"]):.0f}% |')
    out += ['', '## Not executed and partially evaluated', '']
    for row in report['procedures']:
        if not row['missing'] and not row['partial']:
            continue
        out.append(f'### @{row["procedure"]}')
        if row['missing']:
            out.append(f'- statements never executed: {compress(row["missing"])}')
        for branch in row['partial']:
            code = branch['code'].replace('`', "'")[:120]
            out.append(f'- L{branch["line"]} [{branch["state"]}] `{code}`')
        out.append('')
    return '\n'.join(out) + '\n'


def run_suite(tests_dir, pattern, names, verbosity):
    loader = unittest.TestLoader()
    if names:
        loader.testNamePatterns = [n if '*' in n else f'*{n}*' for n in names]
    suite = loader.discover(start_dir=str(tests_dir), pattern=pattern, top_level_dir=str(tests_dir))
    stream = sys.stderr if verbosity else open(os.devnull, 'w')
    try:
        return unittest.TextTestRunner(stream=stream, verbosity=verbosity).run(suite)
    finally:
        if stream is not sys.stderr:
            stream.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='GPP statement and branch coverage of the offline tests')
    parser.add_argument('--tests', type=Path, default=ROOT / 'tests', help='test directory (default: tests)')
    parser.add_argument('--pattern', default='test*.py', help='test file pattern (default: test*.py)')
    parser.add_argument('-k', dest='names', action='append', default=[], help='only tests matching this pattern')
    parser.add_argument('--md', type=Path, help='write the markdown report here')
    parser.add_argument('--json', type=Path, help='write the raw report (statements, branches) as JSON')
    parser.add_argument('--fail-under', type=float, default=None, help='exit 2 if statement coverage is lower')
    parser.add_argument('--quiet', action='store_true', help='do not print unittest progress')
    args = parser.parse_args(argv)

    gpp = Path(os.environ.get('PP_TEST_SOURCE', DEFAULT_GPP))
    source = gpp.read_text(encoding='utf-8-sig')
    for path in (str(ROOT), str(args.tests.resolve())):
        if path not in sys.path:
            sys.path.insert(0, path)

    started = time.perf_counter()
    if LEGACY:
        recorder = Recorder(reference_bodies(source))
        previous = sys.gettrace()
        sys.settrace(recorder.global_trace)
        try:
            result = run_suite(args.tests, args.pattern, args.names, 0 if args.quiet else 1)
        finally:
            sys.settrace(previous)
    else:
        recorder = GpplRecorder(source)
        recorder.install()
        try:
            result = run_suite(args.tests, args.pattern, args.names, 0 if args.quiet else 1)
        finally:
            recorder.uninstall()
        recorder.collect()
    elapsed = time.perf_counter() - started

    report = build_report(source, recorder)
    mode = 'legacy engine, with tracing' if LEGACY else 'GPPL engine'
    summary = (f'{result.testsRun} run, {len(result.failures)} failures, {len(result.errors)} errors, '
               f'{len(result.skipped)} skipped, {elapsed:.1f} s ({mode})')
    text = markdown(report, gpp.relative_to(ROOT) if gpp.is_relative_to(ROOT) else gpp, summary)
    if args.md:
        args.md.write_text(text, encoding='utf-8')
    if args.json:
        report['tests'] = summary
        args.json.write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    totals = report['totals']
    statement_pct = percent(totals['executed'], totals['statements'])
    print(f'GPP statements {totals["executed"]}/{totals["statements"]} = {statement_pct:.1f}%, '
          f'branch outcomes {totals["taken"]}/{totals["branches"]} = '
          f'{percent(totals["taken"], totals["branches"]):.1f}% ({summary})')
    if not result.wasSuccessful():
        return 1
    if args.fail_under is not None and statement_pct < args.fail_under:
        print(f'statement coverage {statement_pct:.1f}% is below --fail-under {args.fail_under}')
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
