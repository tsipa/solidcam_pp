"""gppl - offline SolidCAM GPPL engine and session emulator (stdlib only, no eval/exec).

Layers: lexer -> expr/program (immutable IR in nodes.py + load-time diagnostics)
-> runtime (Engine) -> output (NC stream) -> session (event replay, trace log,
expectations), with policies, formats, sysvars, vmid, coverage, calltrace and
analysis alongside. ``legacy.py`` is the previous engine, verbatim, kept as the
differential oracle and rollback target.
"""
from .errors import (Diagnostic, GPPLRuntimeError, GPPLSyntaxError, MissingInput, PostAbort,
                     PostprocessorStopped, UnsupportedGPPL)
from .policies import Policies
from .runtime import Engine

__all__ = ['Engine', 'Policies', 'UnsupportedGPPL', 'GPPLSyntaxError', 'GPPLRuntimeError',
           'MissingInput', 'PostAbort', 'PostprocessorStopped', 'Diagnostic']
