"""Mutation run: generate simple GPP mutants and run the whole suite on each one.

usage (from the repository root):
    python -m pp_tests.tools.mutation [--out mutation.json] [--jobs N] [--sample N]
                                      [--procs usr_rapid,drill] [--compare previous.json]

Mutation operators (applied to the code part of one GPP line; comments and
string literals are untouched). They are the operators of the original
mutation experiment (TSR-20), so the default target set reproduces its 802
mutants and the kill rates are comparable:
  ROR  relational operator replacement (eq<->ne, gt->ge, lt->le, ge->gt, le->lt, < <= > >=)
  LCR  logical connector replacement (and<->or)
  NEG  removal of a '!' negation in a condition
  AOR  arithmetic operator replacement in assignments (+ <-> -, * -> /)
  UOI  unary minus removal
  CRP  numeric constant replacement (n -> n+1, decimals x10)
  BOOL true<->false in assignments
  SDL  statement deletion (assignment / call / output line commented out)

Each mutant is written to a temporary file and the suite runs in a subprocess
with PP_TEST_SOURCE pointing at it. Status per mutant:
  KILLED       at least one test outside STATIC_FILES fails (AssertionError);
               a known-defect test that reports "no longer reproduces" counts,
               because the mutant changed observable behaviour
  STATIC_ONLY  only text-pinning static tests fail (STATIC_FILES)
  ERROR_ONLY   only errors (engine gaps, StaleAnchor of an in-memory mutation)
  SURVIVED     the suite stays green
  TIMEOUT      the suite did not finish within --timeout seconds
The GPP in the repository is never modified.
"""
import argparse
import concurrent.futures as cf
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter

from . import GPP, ROOT

sys.path.insert(0, str(ROOT))
from pp_tests.engine import uncomment  # noqa: E402

TARGETS = ('usr_r1pos_calc', 'usr_r1_select_dir', 'usr_r1_output', 'usr_4x_index', 'usr_rapid',
           'usr_line', 'usr_arc_math', 'usr_arc', 'usr_arc_check', 'drill', 'fourth_axis', 'tmatrix',
           'start_of_job', 'end_of_job', 'usr_ct_toolchange', 'usr_workpiece_stock', 'compensation')
# Tests that only read the GPP text (allowlists, option pins, format pins).
STATIC_FILES = frozenset({'test_gpp_static', 'test_machine_definition'})
RESULT_LINE = re.compile(r'^(FAIL|ERROR): (\w+) \(([\w.]+)\)', re.M)


def crp(token):
    value = float(token)
    if value != int(value):
        return repr(value * 10)
    return str(int(value) + 1)


def mutants_for_line(raw):
    """[(operator, mutated raw line, description)] for one GPP line."""
    code = uncomment(raw)
    index = raw.find(code) if code else -1
    if not code or index < 0:
        return []
    low = code.lower()
    out = []

    def put(op, new_code, desc):
        if new_code != code:
            out.append((op, raw[:index] + new_code + raw[index + len(code):], desc))

    parts = re.split(r"('(?:[^']|'')*'|\"[^\"]*\")", code)

    def sub_outside(pattern, replacement, flags=0):
        results = []
        for part in range(0, len(parts), 2):
            for match in re.finditer(pattern, parts[part], flags):
                new_parts = list(parts)
                segment = parts[part]
                text = replacement(match) if callable(replacement) else replacement
                new_parts[part] = segment[:match.start()] + text + segment[match.end():]
                results.append((''.join(new_parts), match.group(0), text))
        return results

    if low in ('else', 'endif', 'endw', 'endp') or re.match(r'(local|global)\s', low):
        return []
    if low.startswith(('if ', 'while ')):
        ror = {'eq': 'ne', 'ne': 'eq', 'gt': 'ge', 'lt': 'le', 'ge': 'gt', 'le': 'lt'}
        for new, old, rep in sub_outside(r'\b(eq|ne|gt|lt|ge|le)\b', lambda m: ror[m.group(1).lower()], re.I):
            put('ROR', new, f'{old} -> {rep}')
        symbols = {'<=': '<', '>=': '>', '<': '<=', '>': '>=', '==': '!='}
        for new, old, rep in sub_outside(r'<=|>=|==|(?<![<>!=])<(?!=)|(?<![<>!=])>(?!=)',
                                         lambda m: symbols[m.group(0)]):
            put('ROR', new, f'{old} -> {rep}')
        for new, old, rep in sub_outside(r'\b(and|or)\b', lambda m: 'or' if m.group(1).lower() == 'and' else 'and',
                                         re.I):
            put('LCR', new, f'{old} -> {rep}')
        for new, old, rep in sub_outside(r'!(?!=)\s*', ''):
            put('NEG', new, 'remove !')
        for new, old, rep in sub_outside(r'(?<![\w.])(\d+\.?\d*)(?![\w.])', lambda m: crp(m.group(1))):
            put('CRP', new, f'{old} -> {rep}')
        return out
    if low.startswith('call ') or code.startswith('{') or low == 'abort' or low.startswith('input '):
        if not low.startswith('input ') and low != 'abort':
            put('SDL', ';' + code, 'delete statement')
        return out
    match = re.fullmatch(r'(change\(\w+\)|\w+)\s*=\s*(.+)', code, re.I)
    if not match:
        return out
    put('SDL', ';' + code, 'delete assignment')
    for new, old, rep in sub_outside(r'(?<=[\w)\s])\s\+\s|(?<=[\w)\s])\s-\s',
                                     lambda m: ' - ' if '+' in m.group(0) else ' + '):
        put('AOR', new, f'{old.strip()} -> {rep.strip()}')
    for new, old, rep in sub_outside(r'\)\s*\*\s*', lambda m: ') / '):
        put('AOR', new, '* -> /')
    for new, old, rep in sub_outside(r'\(-(\w+)\)', lambda m: '(' + m.group(1) + ')'):
        put('UOI', new, f'{old} -> {rep}')
    for new, old, rep in sub_outside(r'(?<=\s)-(?=\w)', ''):
        put('UOI', new, 'remove unary -')
    for new, old, rep in sub_outside(r'\b(true|false)\b', lambda m: 'false' if m.group(1).lower() == 'true' else 'true',
                                     re.I):
        put('BOOL', new, f'{old} -> {rep}')
    rhs = match.group(2)
    for constant in re.finditer(r'(?<![\w.])(\d+\.?\d*)(?![\w.])', rhs):
        if re.search(r"'", rhs[:constant.start()]):
            continue
        new_rhs = rhs[:constant.start()] + crp(constant.group(1)) + rhs[constant.end():]
        put('CRP', code[:len(code) - len(rhs)] + new_rhs, f'{constant.group(1)} -> {crp(constant.group(1))}')
    return out


def catalog(source, targets):
    lines = source.split('\n')
    current, found = None, []
    for number, raw in enumerate(lines, 1):
        code = uncomment(raw)
        if code.startswith('@'):
            current = re.match(r'@(\w+)', code).group(1).lower()
            continue
        if code.lower() == 'endp':
            current = None
            continue
        if current in targets:
            for op, new_line, desc in mutants_for_line(raw):
                found.append(dict(id=len(found), proc=current, line=number, op=op, desc=desc,
                                  original=raw.strip(), mutant=new_line.strip()))
    return found


def run_one(entry, source, workdir, timeout, tests_dir):
    lines = source.split('\n')
    lines[entry['line'] - 1] = entry['raw']
    handle, path = tempfile.mkstemp(suffix='.gpp', dir=workdir)
    with os.fdopen(handle, 'w', encoding='utf-8', newline='') as stream:
        stream.write('\n'.join(lines))
    env = dict(os.environ, PP_TEST_SOURCE=path, PYTHONDONTWRITEBYTECODE='1')
    env.pop('PP_STRICT_KNOWN_DEFECTS', None)
    try:
        proc = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', tests_dir],
                              cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout)
        text = proc.stderr
    except subprocess.TimeoutExpired:
        text = None
    finally:
        os.unlink(path)
    if text is None:
        return dict(status='TIMEOUT', fails=[], errors=[], summary='TIMEOUT')
    fails, errors = set(), set()
    for kind, test, where in RESULT_LINE.findall(text):
        (fails if kind == 'FAIL' else errors).add(f'{where.split(".")[0]}::{test}')
    behavioural = [f for f in fails if f.split('::')[0] not in STATIC_FILES]
    if behavioural:
        status = 'KILLED'
    elif fails:
        status = 'STATIC_ONLY'
    elif errors:
        status = 'ERROR_ONLY'
    else:
        status = 'SURVIVED'
    output = text.strip().splitlines()
    return dict(status=status, fails=sorted(fails), errors=sorted(errors), summary=output[-1] if output else '')


def summarize(report):
    counts = Counter(entry['status'] for entry in report)
    total = len(report)
    killed = counts['KILLED']
    lines = [f'{total} mutants: ' + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())),
             f'kill rate (behavioural): {killed}/{total} = {100.0 * killed / total:.1f}%' if total else 'no mutants',
             f'kill rate (incl. static-only): {killed + counts["STATIC_ONLY"]}/{total} = '
             f'{100.0 * (killed + counts["STATIC_ONLY"]) / total:.1f}%' if total else '']
    per_proc = {}
    for entry in report:
        stats = per_proc.setdefault(entry['proc'], Counter())
        stats['total'] += 1
        stats[entry['status']] += 1
    lines.append('per procedure (killed/total):')
    for proc, stats in sorted(per_proc.items()):
        lines.append(f'  {proc:24s} {stats["KILLED"]:4d}/{stats["total"]:<4d} '
                     f'{100.0 * stats["KILLED"] / stats["total"]:5.1f}%')
    return '\n'.join(line for line in lines if line)


def compare(report, previous_path):
    previous = json.loads(open(previous_path, encoding='utf-8').read())
    key = lambda e: (e['proc'], e['line'], e['op'], e['desc'], e.get('mutant'))  # noqa: E731
    old = {key(e): e.get('status') or e.get('final_status') or e.get('baseline_status') for e in previous}
    gained = [e for e in report if e['status'] == 'KILLED' and old.get(key(e)) not in (None, 'KILLED')]
    lost = [e for e in report if e['status'] != 'KILLED' and old.get(key(e)) == 'KILLED']
    lines = [f'compared with {previous_path}: {len(gained)} newly killed, {len(lost)} no longer killed']
    for entry in lost:
        lines.append(f'  no longer killed: {entry["proc"]}:{entry["line"]} {entry["op"]} {entry["desc"]} '
                     f'-> {entry["status"]}')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='GPP mutation run over the offline suite')
    parser.add_argument('--gpp', default=str(GPP), help='GPP to mutate (default: the shipped post)')
    parser.add_argument('--out', default='mutation_report.json', help='JSON report path')
    parser.add_argument('--jobs', type=int, default=os.cpu_count() or 2, help='parallel suite runs')
    parser.add_argument('--timeout', type=int, default=600, help='seconds per suite run')
    parser.add_argument('--sample', type=int, default=0, help='run a reproducible random sample of N mutants')
    parser.add_argument('--seed', type=int, default=20261026, help='seed for --sample')
    parser.add_argument('--procs', default='', help='comma-separated procedures (default: the TSR-20 set)')
    parser.add_argument('--tests', default='tests', help='test directory passed to unittest discover')
    parser.add_argument('--compare', help='previous report (this tool or the TSR-20 JSON) to diff against')
    parser.add_argument('--list', action='store_true', help='only list the mutants')
    args = parser.parse_args(argv)

    source = open(args.gpp, encoding='utf-8-sig').read()
    targets = tuple(p.strip().lower() for p in args.procs.split(',') if p.strip()) or TARGETS
    entries = catalog(source, targets)
    if args.sample and args.sample < len(entries):
        entries = sorted(random.Random(args.seed).sample(entries, args.sample), key=lambda e: e['id'])
    print(f'{len(entries)} mutants over {len(targets)} procedures', flush=True)
    if args.list:
        for entry in entries:
            print(f'{entry["id"]:4d} {entry["proc"]}:{entry["line"]} {entry["op"]} {entry["desc"]}: {entry["mutant"]}')
        return 0
    lines = source.split('\n')
    started = time.perf_counter()
    report = []
    with tempfile.TemporaryDirectory(prefix='pp_mutants_') as workdir, cf.ThreadPoolExecutor(args.jobs) as pool:
        futures = {}
        for entry in entries:
            raw = lines[entry['line'] - 1]
            mutated = next(new for op, new, desc in mutants_for_line(raw)
                           if op == entry['op'] and desc == entry['desc'] and new.strip() == entry['mutant'])
            job = dict(entry, raw=mutated)
            futures[pool.submit(run_one, job, source, workdir, args.timeout, args.tests)] = entry
        for done, future in enumerate(cf.as_completed(futures), 1):
            report.append(dict(futures[future], **future.result()))
            if done % 50 == 0 or done == len(futures):
                print(f'{done}/{len(futures)} ({time.perf_counter() - started:.0f} s)', flush=True)
    report.sort(key=lambda e: e['id'])
    with open(args.out, 'w', encoding='utf-8') as stream:
        json.dump(report, stream, indent=1)
    print(summarize(report))
    if args.compare:
        print(compare(report, args.compare))
    print(f'report: {args.out}; {time.perf_counter() - started:.0f} s')
    return 0


if __name__ == '__main__':
    sys.exit(main())
