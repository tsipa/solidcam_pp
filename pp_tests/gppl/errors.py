"""Exception hierarchy and load-time diagnostics.

Every engine error is an ``UnsupportedGPPL`` (a ``ValueError``), because the
legacy suite catches that class and matches message fragments ('POST ERROR',
'ARC end mismatch', 'keyword', 'unclosed while', 'modal output requires explicit
change flags'). Subclasses keep the GPPL text in ``str(exc)`` and append one GPPL
call chain (``@proc:line <- @caller:line``) instead of re-wrapping the message at
every frame like the legacy engine did.
"""


class UnsupportedGPPL(ValueError):
    """Base class: a construct, input or semantic the engine refuses."""


class GPPLSyntaxError(UnsupportedGPPL):
    """Source could not be parsed. Raised lazily when the construct executes, or
    at load time under ``Policies(load_errors='raise')``."""

    def __init__(self, message, proc=None, line=None):
        self.proc, self.line, self.message = proc, line, message
        where = f'@{proc}:{line}: ' if proc and line else ''
        super().__init__(where + message)


class GPPLRuntimeError(UnsupportedGPPL):
    """Execution failed; ``gppl_stack`` is innermost-first [(proc, line), ...]."""

    def __init__(self, message, gppl_stack=()):
        self.message = message
        self.gppl_stack = list(gppl_stack)
        super().__init__(self._render())

    def _render(self):
        if not self.gppl_stack:
            return self.message
        head = '@%s:%s' % self.gppl_stack[0]
        chain = ' <- '.join('@%s:%s' % frame for frame in self.gppl_stack[1:])
        return f'{head}: {self.message}' + (f' [call chain: {chain}]' if chain else '')

    def with_stack(self, gppl_stack):
        self.gppl_stack = list(gppl_stack)
        self.args = (self._render(),)
        return self


class MissingInput(GPPLRuntimeError):
    """A variable or change/active flag was read but never supplied."""


class PostprocessorStopped(GPPLRuntimeError):
    """``input`` reached under the default 'abort' input policy."""


class PostAbort(GPPLRuntimeError):
    """The GPPL ``abort`` statement executed."""


class Diagnostic:
    """One load-time or lint finding.

    severity: 'error' (raises when executed; fails a strict load), 'warning',
    'info'. ``code`` is a stable identifier (E-SYNTAX, E-STRUCT, E-CALL, ...).
    """
    __slots__ = ('severity', 'code', 'proc', 'line', 'message')

    def __init__(self, severity, code, proc, line, message):
        self.severity, self.code, self.proc, self.line, self.message = severity, code, proc, line, message

    def __str__(self):
        where = f'@{self.proc}:{self.line}' if self.proc else f'line {self.line}'
        return f'{self.severity} {self.code} {where}: {self.message}'

    def __repr__(self):
        return f'Diagnostic({str(self)!r})'

    def as_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}
