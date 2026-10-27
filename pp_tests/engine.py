"""Drop-in replacement for the legacy engine: a thin compatibility shim.

The implementation lives in ``pp_tests.gppl``. Public names kept: Engine,
UnsupportedGPPL, uncomment (plus Policies).

Rollback switch: ``GPPL_ENGINE=legacy`` selects the verbatim legacy engine
(``pp_tests/gppl/legacy.py``) without touching any test.
"""
import os

if os.environ.get('GPPL_ENGINE', '').strip().lower() == 'legacy':
    from .gppl.legacy import Engine, UnsupportedGPPL, uncomment  # noqa: F401
    from .gppl.policies import Policies  # noqa: F401
else:
    from .gppl.errors import UnsupportedGPPL  # noqa: F401
    from .gppl.lexer import strip_comment
    from .gppl.policies import Policies  # noqa: F401
    from .gppl.runtime import Engine  # noqa: F401

    def uncomment(line):
        """Legacy helper: strip a ';' comment outside quotes."""
        return strip_comment(line)

__all__ = ['Engine', 'UnsupportedGPPL', 'Policies', 'uncomment']
