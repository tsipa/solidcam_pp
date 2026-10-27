"""Optional maintenance tools for the offline test suite (stdlib only).

    python -m pp_tests.tools.findings --write   regenerate tests/PP_FINDINGS.md
    python -m pp_tests.tools.mutation            GPP mutation run (kill rate)
    python -m pp_tests.tools.revert_matrix       historical revert matrix

Statement/branch coverage of the GPP is `python -m pp_tests.coverage`.
Run every command from the repository root.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / 'tests'
GPP_RELATIVE = 'siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.gpp'
GPP = ROOT / GPP_RELATIVE


def use_test_support():
    """Make tests/support importable (it imports pp_tests from the repository root)."""
    for path in (str(ROOT), str(TESTS)):
        if path not in sys.path:
            sys.path.insert(0, path)
