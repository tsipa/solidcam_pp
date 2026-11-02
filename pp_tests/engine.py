"""Public engine names of the offline tests: a thin re-export of ``pp_tests.gppl``.

Public names: Engine, UnsupportedGPPL, uncomment (plus Policies).

The original engine (pp_tests/gppl/legacy.py) and its rollback switch
``GPPL_ENGINE=legacy`` were removed; an environment that still sets the switch
stops at this import instead of silently running the GPPL engine.
"""
import os

if os.environ.get('GPPL_ENGINE', '').strip().lower() == 'legacy':
    raise ImportError('GPPL_ENGINE=legacy: the original engine (pp_tests/gppl/legacy.py) was removed; '
                      'unset GPPL_ENGINE to run the GPPL engine')

from .gppl.errors import UnsupportedGPPL  # noqa: E402,F401
from .gppl.lexer import strip_comment  # noqa: E402
from .gppl.policies import Policies  # noqa: E402,F401
from .gppl.runtime import Engine  # noqa: E402,F401


def uncomment(line):
    """Strip a ';' comment outside quotes (the original engine's helper, kept by name)."""
    return strip_comment(line)


__all__ = ['Engine', 'UnsupportedGPPL', 'Policies', 'uncomment']
