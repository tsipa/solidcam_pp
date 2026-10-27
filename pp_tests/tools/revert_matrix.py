"""Historical revert matrix: does the suite notice when a GPP commit is undone?

usage (from the repository root of a git clone):
    python -m pp_tests.tools.revert_matrix [--md revert_matrix.md] [--json revert_matrix.json]
                                           [--commits c03e1b4,ab853be] [--jobs N]

For every commit that changed Gmill_540v_4x.gpp (git log --follow, so the old
Gmill_540v_3x.gpp name is included; the initial import and the pure rename are
skipped):

1. Reverse patch. The commit's change (difflib hunks with 3 context lines) is
   reverse-applied to the CURRENT GPP in memory, with a fuzz of up to 3 context
   lines per side like `patch -F3`. The whole suite runs on the result
   (PP_TEST_SOURCE, default mode) and its failures are recorded. When only
   some hunks apply, the suite runs on that partial reversion and the row says
   so. A FAIL is an AssertionError; ERRORs (engine gaps, StaleAnchor) are
   listed but do not count as detection.
2. Hand-crafted reversions. Later commits often rewrote the same lines, so the
   reverse patch no longer applies. The history tests carry hand-crafted
   in-memory reversions instead (support.mutation.mutate + assert_detected,
   fixture regression patches). A test counts only if it applies a reversion
   (calls mutate/assert_detected or expects an AssertionError, itself or through
   the self.<helper> methods and module helpers it calls) AND names the commit:
   in its code, in a module-level table or helper it uses, or in its own
   docstring. Every '*detect*' test that applies the 'regression' patches of a
   JSON fixture with a case for that commit counts too. These tests run on the
   current GPP; such a test passes only if each of its reversions fails an
   assertion. A test that cites the hash without applying any reversion is not
   evidence (the docstring rule still trusts the author that the reversion it
   applies is that commit's). Known-defect tests are reported as skips and
   ignored.

Verdict: DETECTED (reverse patch) when the complete reverse patch produced at
least one FAIL; DETECTED (hand-crafted) when the named tests pass (at least one
pass, no failure or error); DETECTED (partial reverse patch) when only a
partial reversion was possible and it produced a FAIL; otherwise NOT DETECTED
(each such commit is explained in tests/HISTORY_COVERAGE.md).
Nothing in the repository is modified; git is only read.
"""
import argparse
import ast
import concurrent.futures as cf
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest

from . import GPP_RELATIVE, ROOT, TESTS, use_test_support

RESULT_LINE = re.compile(r'^(FAIL|ERROR): (\w+) \(([\w.]+)\)', re.M)
FUZZ = 3
# Tests that only read the GPP text; a FAIL there is reported as static-only detection.
STATIC_FILES = frozenset({'test_gpp_static', 'test_machine_definition'})


def git(*args, repo=ROOT):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, check=True,
                          encoding='utf-8', errors='replace').stdout


def history(repo):
    """[(sha, short, date, subject, path)] newest first, following renames."""
    out = git('log', '--follow', '--format=%x00%H%x09%h%x09%ad%x09%s', '--date=short', '--name-only', '--',
              GPP_RELATIVE, repo=repo)
    commits = []
    for record in out.split('\x00')[1:]:
        lines = [line for line in record.splitlines() if line.strip()]
        sha, short, date, subject = lines[0].split('\t', 3)
        commits.append((sha, short, date, subject, lines[-1].strip()))
    return commits


def show(repo, sha, path):
    return git('show', f'{sha}:{path}', repo=repo)


def hunks(old_lines, new_lines):
    """[(old_block, new_block, new_start, context_before, context_after)] like a 3-line unified diff."""
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    result = []
    for group in matcher.get_grouped_opcodes(FUZZ):
        i1, j1 = group[0][1], group[0][3]
        i2, j2 = group[-1][2], group[-1][4]
        before = group[0][2] - group[0][1] if group[0][0] == 'equal' else 0
        after = group[-1][2] - group[-1][1] if group[-1][0] == 'equal' else 0
        result.append((old_lines[i1:i2], new_lines[j1:j2], j1, before, after))
    return result


def _find(lines, block, expected):
    if not block:
        return expected if 0 <= expected <= len(lines) else None
    width = len(block)
    hits = [index for index in range(len(lines) - width + 1) if lines[index:index + width] == block]
    return min(hits, key=lambda index: abs(index - expected)) if hits else None


def reverse_apply(current, old_text, new_text):
    """current with the old->new change undone: (text, applied hunks, total hunks).

    Hunks that cannot be placed are left out, so text is a partial reversion
    when applied < total.
    """
    lines = current.split('\n')
    old_lines, new_lines = old_text.split('\n'), new_text.split('\n')
    changes = hunks(old_lines, new_lines)
    offset, applied = 0, 0
    for old_block, new_block, new_start, before, after in changes:
        placed = None
        for fuzz in range(FUZZ + 1):
            cut_before, cut_after = min(fuzz, before), min(fuzz, after)
            new_core = new_block[cut_before:len(new_block) - cut_after]
            old_core = old_block[cut_before:len(old_block) - cut_after]
            if not new_core and not old_core:
                continue
            index = _find(lines, new_core, new_start + cut_before + offset)
            if index is not None:
                placed = (index, new_core, old_core)
                break
        if placed is None:
            continue
        index, new_core, old_core = placed
        lines[index:index + len(new_core)] = old_core
        offset += len(old_core) - len(new_core)
        applied += 1
    return '\n'.join(lines), applied, len(changes)


def run_suite(source, tests_dir, timeout):
    handle, path = tempfile.mkstemp(suffix='.gpp', prefix='pp_revert_')
    with os.fdopen(handle, 'w', encoding='utf-8', newline='') as stream:
        stream.write(source)
    env = dict(os.environ, PP_TEST_SOURCE=path, PYTHONDONTWRITEBYTECODE='1')
    env.pop('PP_STRICT_KNOWN_DEFECTS', None)
    try:
        proc = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(tests_dir)],
                              cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout)
        text = proc.stderr
    except subprocess.TimeoutExpired:
        return dict(summary='TIMEOUT', fails=[], errors=[])
    finally:
        os.unlink(path)
    fails, errors = set(), set()
    for kind, test, where in RESULT_LINE.findall(text):
        (fails if kind == 'FAIL' else errors).add(f'{where.split(".")[0]}::{test}')
    output = text.strip().splitlines()
    return dict(summary=output[-1] if output else '', fails=sorted(fails), errors=sorted(errors))


def fixture_regressions(tests_dir, short):
    """Names of JSON fixtures with a case for this commit that carries a 'regression' patch."""
    names = set()
    for path in sorted((tests_dir / 'fixtures').glob('*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            continue
        for case in data.get('cases', []) if isinstance(data, dict) else []:
            if (isinstance(case, dict) and str(case.get('commit', '')).startswith(short[:7])
                    and case.get('regression')):
                names.add(path.name)
    return names


REVERSION_CALLS = frozenset({'mutate', 'assert_detected'})


def _code_text(text, node):
    """Source of a node without its docstring and comments (a cited hash there is not evidence)."""
    segment = ast.get_source_segment(text, node) or ''
    body = getattr(node, 'body', None)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        segment = segment.replace(ast.get_source_segment(text, body[0]) or '', '', 1)
    return '\n'.join(line.split('#', 1)[0] for line in segment.splitlines())


def _applies_reversion(node):
    """True if node calls mutate/assert_detected or expects an AssertionError."""
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        name = call.func.id if isinstance(call.func, ast.Name) else getattr(call.func, 'attr', None)
        if name in REVERSION_CALLS:
            return True
        if name in ('assertRaises', 'assertRaisesRegex') and call.args and \
                isinstance(call.args[0], ast.Name) and call.args[0].id == 'AssertionError':
            return True
    return False


def handcrafted_tests(tests_dir, short):
    """unittest names 'module.Class.test' that carry a hand-crafted reversion of the commit (see module doc)."""
    found = set()
    pattern = re.compile(rf'\b{re.escape(short[:7])}')
    fixtures = fixture_regressions(tests_dir, short)
    for path in sorted(tests_dir.glob('test*.py')):
        text = path.read_text(encoding='utf-8')
        loads_fixture = any(name in text for name in fixtures)
        if not pattern.search(text) and not loads_fixture:
            continue
        tree = ast.parse(text)
        if loads_fixture:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if (isinstance(item, ast.FunctionDef) and item.name.startswith('test')
                                and 'detect' in item.name
                                and "'regression'" in (ast.get_source_segment(text, item) or '')):
                            found.add(f'{path.stem}.{node.name}.{item.name}')
        tagged_names = set()
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and pattern.search(_code_text(text, node)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                tagged_names |= {t.id for t in targets if isinstance(t, ast.Name)}
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        helpers = {name for name, node in functions.items() if _mentions(text, node, pattern, tagged_names)}
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            methods = {item.name: item for item in node.body if isinstance(item, ast.FunctionDef)}
            tagged = {name for name, item in methods.items() if _mentions(text, item, pattern, tagged_names | helpers)}
            for name, method in methods.items():
                if not name.startswith('test'):
                    continue
                reached = [method] + [methods[called] for called in _self_calls(method) if called in methods] + \
                    [functions[called] for called in _calls(method) if called in functions]
                docstring = ast.get_docstring(method) or ''
                cites = name in tagged or bool(_self_calls(method) & tagged) or bool(pattern.search(docstring))
                if cites and any(_applies_reversion(item) for item in reached):
                    found.add(f'{path.stem}.{node.name}.{name}')
    return sorted(found)


def _mentions(text, node, pattern, names):
    if pattern.search(_code_text(text, node)):
        return True
    return any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(node))


def _self_calls(method):
    return {n.attr for n in ast.walk(method)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'self'}


def _calls(method):
    return {n.func.id for n in ast.walk(method) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def run_named(names):
    """Run unittest names in-process on the current GPP; {name: 'pass'|'fail'|'error'|'skip'}."""
    use_test_support()
    if str(TESTS) not in sys.path:
        sys.path.insert(0, str(TESTS))
    outcome = {}
    for name in names:
        suite = unittest.defaultTestLoader.loadTestsFromName(name)
        result = unittest.TestResult()
        suite.run(result)
        outcome[name] = ('error' if result.errors else 'fail' if result.failures
                         else 'skip' if result.skipped else 'pass')
    return outcome


def markdown(rows):
    out = ['| commit | date | subject | reverse patch | suite on reverted GPP | hand-crafted reversion tests | verdict |',
           '|---|---|---|---|---|---|---|']
    for row in rows:
        suite = row.get('suite')
        if suite:
            shown = ', '.join(f.split('::')[1] for f in suite['fails'][:3])
            more = f' (+{len(suite["fails"]) - 3})' if len(suite['fails']) > 3 else ''
            suite_text = f'{len(suite["fails"])} FAIL, {len(suite["errors"])} ERROR' + (f': {shown}{more}' if shown else '')
        else:
            suite_text = '-'
        tests = row['handcrafted']
        passed = sum(1 for v in tests.values() if v == 'pass')
        broken = sum(1 for v in tests.values() if v in ('fail', 'error'))
        hand = f'{passed} pass' + (f', {broken} FAIL/ERROR' if broken else '') if passed or broken else 'none'
        if row.get('partial'):
            suite_text = f'partial ({row["partial"]}): ' + suite_text
        out.append(f'| {row["short"]} | {row["date"]} | {row["subject"]} | {row["patch"]} | {suite_text} | {hand} | '
                   f'{row["verdict"]} |')
    return '\n'.join(out) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Historical revert matrix over the GPP history')
    parser.add_argument('--repo', default=str(ROOT), help='git clone to read history from (default: this repo)')
    parser.add_argument('--commits', default='', help='comma-separated short hashes (default: all)')
    parser.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 2))
    parser.add_argument('--timeout', type=int, default=900)
    parser.add_argument('--json', help='write the full matrix as JSON')
    parser.add_argument('--md', help='write the matrix as a markdown table')
    args = parser.parse_args(argv)

    repo = args.repo
    current = (ROOT / GPP_RELATIVE).read_text(encoding='utf-8-sig')
    commits = history(repo)
    wanted = {c.strip() for c in args.commits.split(',') if c.strip()}
    rows, jobs = [], {}
    started = time.perf_counter()
    with cf.ThreadPoolExecutor(args.jobs) as pool:
        for index, (sha, short, date, subject, path) in enumerate(commits):
            if index + 1 >= len(commits):
                continue                                   # initial import: nothing to revert
            if wanted and not any(sha.startswith(w) for w in wanted):
                continue
            parent_sha, parent_path = commits[index + 1][0], commits[index + 1][4]
            new_text = show(repo, sha, path)
            old_text = show(repo, parent_sha, parent_path)
            if old_text == new_text:
                continue                                   # pure rename
            reverted, applied, total = reverse_apply(current, old_text, new_text)
            row = dict(sha=sha, short=short, date=date, subject=subject, hunks=total,
                       patch='applied' if applied == total else f'PATCH-FAILED ({total - applied}/{total} hunks)')
            if applied:
                if applied < total:
                    row['partial'] = f'{applied}/{total} hunks reverted'
                jobs[pool.submit(run_suite, reverted, TESTS, args.timeout)] = row
            rows.append(row)
        for future in cf.as_completed(jobs):
            jobs[future]['suite'] = future.result()
    for row in rows:
        row['handcrafted'] = run_named(handcrafted_tests(TESTS, row['short']))
        suite = row.get('suite')
        outcomes = list(row['handcrafted'].values())
        hand_ok = 'pass' in outcomes and not any(v in ('fail', 'error') for v in outcomes)
        behavioural = [f for f in (suite or {}).get('fails', []) if f.split('::')[0] not in STATIC_FILES]
        if suite:
            suite['behavioural_fails'] = behavioural
        if behavioural and not row.get('partial'):
            row['verdict'] = 'DETECTED (reverse patch)'
        elif hand_ok:
            row['verdict'] = 'DETECTED (hand-crafted)'
        elif behavioural:
            row['verdict'] = 'DETECTED (partial reverse patch)'
        elif suite and suite['fails']:
            row['verdict'] = 'DETECTED (static test only)'
        else:
            row['verdict'] = 'NOT DETECTED'
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as stream:
            json.dump(rows, stream, indent=1)
    table = markdown(rows)
    if args.md:
        with open(args.md, 'w', encoding='utf-8') as stream:
            stream.write(table)
    sys.stdout.write(table)
    counts = {}
    for row in rows:
        counts[row['verdict']] = counts.get(row['verdict'], 0) + 1
    print(f'{len(rows)} commits: ' + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())) +
          f'; {time.perf_counter() - started:.0f} s')
    return 0


if __name__ == '__main__':
    sys.exit(main())
