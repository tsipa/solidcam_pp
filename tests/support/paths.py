"""Locations of the files under test and their machine definition.

PP_TEST_SOURCE overrides the GPP path (same variable as tests/test_offline.py),
so mutation runs can point the whole suite at a modified copy. The VMID is the
one next to the tested GPP when that exists, else the repository's. The
Vericut files (CTL, MCH, GCODESIM_INI) always come from the repository's
machine directory, whatever PP_TEST_SOURCE says. require_file() skips a test
with a reason when an optional file is absent.
"""
import functools
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / 'tests'
FIXTURES = TESTS / 'fixtures'
PP = Path(os.environ.get('PP_TEST_SOURCE',
                         ROOT / 'siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.gpp'))
MACHINE_DIR = ROOT / 'siemens_sinumerik_828d/noname_vmc500_4x'
VMID = PP.with_suffix('.vmid') if PP.with_suffix('.vmid').exists() else MACHINE_DIR / 'Gmill_540v_4x.vmid'
VERICUT = MACHINE_DIR / 'vericut'
CTL = VERICUT / 'sin840d_special.ctl'
MCH = VERICUT / 'qwe.mch'
GCODESIM_INI = VERICUT / 'GcodeSim.ini'
# The Mach3 4x post lives in an (often empty) submodule; MACH3_PP_SOURCE overrides it.
MACH3_PP = Path(os.environ.get('MACH3_PP_SOURCE', ROOT / 'mach3/4x/Mach3_4X_Y.gpp'))


@functools.lru_cache(maxsize=None)
def read_text(path, encoding='utf-8-sig'):
    """Cached file read (the GPP is read by hundreds of tests)."""
    return Path(path).read_text(encoding=encoding)


def pp_source():
    """Text of the tested GPP (cached)."""
    return read_text(PP)


def require_file(path, encoding='latin-1'):
    """Return the text of an optional machine-definition file or skip the test."""
    path = Path(path)
    if not path.exists():
        raise unittest.SkipTest(f'{path.name} not found ({path}); scratch copies may omit it')
    return read_text(path, encoding)
