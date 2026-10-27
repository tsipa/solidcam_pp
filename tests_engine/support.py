"""Shared paths and helpers for the engine tests (run from the repository root:
``python3 -m unittest discover -s tests_engine``)."""
import os
import re
import unittest

if os.environ.get('GPPL_ENGINE', '').strip().lower() == 'legacy':
    raise unittest.SkipTest('tests_engine tests the default GPPL engine; unset GPPL_ENGINE=legacy')
from pathlib import Path

from pp_tests.gppl import legacy  # noqa: F401  (verbatim legacy engine: differential oracle)
from pp_tests.gppl.policies import Policies

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'fixtures'
PP = Path(os.environ.get('PP_TEST_SOURCE', ROOT / 'siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.gpp'))
VMID = Path(os.environ.get('PP_TEST_VMID', PP.with_suffix('.vmid')))
SESSIONS = ('synthetic_session', 'options_session', 'machine_variants_session', 'oracle_session')
SESSION = Policies.session()
COMPAT = Policies()


def source():
    return PP.read_text(encoding='utf-8-sig')


# Source-derived expectations: line numbers and statement counts follow the GPP text, so editing the
# GPP does not require re-pinning numbers in the harness tests.
QUOTE_DOUBLING = re.escape(",0," + "'" * 3)     # the CYCLE84 doubled-quote idiom


def code_lines():
    from pp_tests.gppl.lexer import strip_comment
    return [strip_comment(line) for line in source().splitlines()]


def lines_matching(pattern, start=None):
    """1-based numbers of code lines (comments stripped) matching ``pattern`` (case-insensitive);
    with ``start``, only inside the procedure whose header line starts with ``start``."""
    lines = code_lines()
    first, last = 0, len(lines)
    if start is not None:
        first = next(i for i, line in enumerate(lines) if line.strip().split(' ')[0] == start)
        last = next(i for i in range(first + 1, len(lines)) if lines[i].strip().lower() == 'endp')
    rx = re.compile(pattern, re.I)
    return [i + 1 for i in range(first, last) if rx.search(lines[i])]


STATEMENT_PATTERNS = {
    'Abort': r'^\s*abort\s*$', 'Input': r'^\s*input\b', 'Print': r'^\s*print\b', 'While': r'^\s*while\b',
    'If': r'^\s*if\b', 'Declare': r'^\s*(global|local)\b', 'FlagAssign': r'^\s*change\s*\(',
    'Output': r'^\s*\{', 'CallProc': r'^\s*call\s+@', 'Assign': r'^\s*[A-Za-z_]\w*\s*=(?!=)'}


def statement_kinds_from_text():
    return {kind: len(lines_matching(pattern)) for kind, pattern in STATEMENT_PATTERNS.items()}


def declared_global_count():
    total = 0
    for line in code_lines():
        match = re.match(r'\s*global\s+(numeric|integer|logical|string)\s+(.+)', line, re.I)
        if match:
            total += len(match[2].replace(',', ' ').split())
    return total


def first_statement_line(proc):
    return lines_matching(r'\S', start='@' + proc)[1]


def require_vmid(case):
    if not VMID.exists():
        raise unittest.SkipTest(f'VMID not found at {VMID}')


def legacy_outcome(fn):
    """Run ``fn`` against the legacy engine; return ('ok', value) or ('error', exc)."""
    try:
        return 'ok', fn()
    except Exception as exc:                       # noqa: BLE001 - evidence only
        return 'error', exc
