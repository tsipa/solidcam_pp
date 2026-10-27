"""gppl - offline SolidCAM GPPL engine and session emulator (stdlib only, no eval/exec).

Layers: lexer -> expr/program (immutable IR in nodes.py + load-time diagnostics)
-> runtime (Engine) -> output (NC stream) -> session (event replay, trace log,
expectations), with policies, formats, sysvars, vmid, coverage, calltrace and
analysis alongside. ``legacy.py`` is the previous engine, verbatim, kept as the
differential oracle and rollback target.
"""
import importlib

# Lazy exports: importing pp_tests.gppl.legacy (the GPPL_ENGINE=legacy rollback) must not load, and so
# must not depend on, the new engine's modules.
_EXPORTS = {
    'Engine': 'runtime', 'Policies': 'policies', 'UnsupportedGPPL': 'errors', 'GPPLSyntaxError': 'errors',
    'GPPLRuntimeError': 'errors', 'MissingInput': 'errors', 'PostAbort': 'errors',
    'PostprocessorStopped': 'errors', 'Diagnostic': 'errors'}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name in _EXPORTS:
        return getattr(importlib.import_module(f'.{_EXPORTS[name]}', __name__), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
