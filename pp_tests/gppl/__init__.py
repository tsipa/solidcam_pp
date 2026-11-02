"""gppl - offline SolidCAM GPPL engine and session emulator (stdlib only, no eval/exec).

Layers: lexer -> expr/program (immutable IR in nodes.py + load-time diagnostics)
-> runtime (Engine) -> output (NC stream) -> session (event replay, trace log,
expectations), with policies, formats, sysvars, vmid, coverage, calltrace and
analysis alongside. The previous engine (``legacy.py``) was the differential
oracle until it was removed; tests_engine/test_language_golden.py keeps the
compat outcomes, recorded from the GPPL engine and equal to the original
engine's except the 15 string repetitions it evaluated.
"""
import importlib

# Lazy exports: importing one submodule (e.g. pp_tests.gppl.formats) does not load the runtime.
_EXPORTS = {
    'Engine': 'runtime', 'Policies': 'policies', 'UnsupportedGPPL': 'errors', 'GPPLSyntaxError': 'errors',
    'GPPLRuntimeError': 'errors', 'MissingInput': 'errors', 'PostAbort': 'errors',
    'PostprocessorStopped': 'errors', 'Diagnostic': 'errors'}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name in _EXPORTS:
        return getattr(importlib.import_module(f'.{_EXPORTS[name]}', __name__), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
