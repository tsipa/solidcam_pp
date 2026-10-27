"""Tracer protocol, the call-trace recorder and a tee for several tracers.

Attach with ``Engine(..., tracer=CallTrace())`` or ``engine.tracer = ...``.
``CallTrace.render()`` prints an indented call tree; ``emitted_by('G75')``
answers "which call chain printed this NC word?" (call sites included).
"""


class Tracer:
    """No-op base class: the hooks the Engine calls when a tracer is attached."""
    wants_assignments = False

    def on_call(self, depth, proc, arguments, site):
        pass

    def on_return(self, depth, proc, error):
        pass

    def on_output(self, pieces, origin, text):
        pass

    def on_console(self, kind, text):
        pass

    def on_assign(self, proc, line, name, old, new, flag):
        pass


class CallTrace(Tracer):
    def __init__(self, record_assignments=False, limit=500000):
        self.wants_assignments = record_assignments
        self.limit = limit
        self.events = []
        self.truncated = False
        self._depth = 0

    def _add(self, event):
        if len(self.events) < self.limit:
            self.events.append(event)
        else:
            self.truncated = True

    def on_call(self, depth, proc, arguments, site):
        self._depth = depth
        self._add(('call', depth, proc.name, tuple(arguments), site))

    def on_return(self, depth, proc, error):
        self._depth = depth - 1
        self._add(('return', depth, proc.name, None if error is None else str(error)))

    def on_output(self, pieces, origin, text):
        self._add(('output', self._depth, origin[0], origin[1], text))

    def on_console(self, kind, text):
        self._add(('console', self._depth, kind, text))

    def on_assign(self, proc, line, name, old, new, flag):
        self._add(('assign', self._depth, proc, line, name, old, new, flag))

    # ---- queries -----------------------------------------------------------
    def calls(self):
        return [event[2] for event in self.events if event[0] == 'call']

    def emitted_by(self, needle):
        """[(call chain outermost first, (proc, line), fragment)] for every output
        fragment containing ``needle``. Chain entries are '@proc' or
        '@proc<-@caller:line'."""
        chains, stack = [], []
        for event in self.events:
            kind = event[0]
            if kind == 'call':
                site = event[4]
                stack.append(f'@{event[2]}' + (f'<-@{site[0]}:{site[1]}' if site else ''))
            elif kind == 'return':
                if stack:
                    stack.pop()
            elif kind == 'output' and needle in event[4]:
                chains.append((list(stack), (event[2], event[3]), event[4]))
        return chains

    def render(self, max_value=40):
        lines = []
        for event in self.events:
            kind, depth = event[0], event[1]
            pad = '  ' * depth
            if kind == 'call':
                args = ', '.join(_short(a, max_value) for a in event[3])
                site = f'   <- @{event[4][0]}:{event[4][1]}' if event[4] else ''
                lines.append(f'{pad}@{event[2]}({args}){site}')
            elif kind == 'return' and event[3]:
                lines.append(f'{pad}  !! {event[3]}')
            elif kind == 'output':
                lines.append(f'{pad}  L{event[3]} > {event[4]!r}')
            elif kind == 'console':
                lines.append(f'{pad}  {event[2].upper()} {event[3]!r}')
            elif kind == 'assign':
                lines.append(f'{pad}  L{event[3]} {event[4]} = {_short(event[6], max_value)}'
                             f'  (was {_short(event[5], max_value)}, change={event[7]})')
        if self.truncated:
            lines.append(f'... truncated after {self.limit} events')
        return '\n'.join(lines)


class Tee(Tracer):
    """Forward every hook to several tracers (e.g. a session's trace log and a CallTrace)."""

    def __init__(self, *tracers):
        self.tracers = [tracer for tracer in tracers if tracer is not None]
        self.wants_assignments = any(getattr(t, 'wants_assignments', False) for t in self.tracers)

    def on_call(self, *args):
        for tracer in self.tracers:
            tracer.on_call(*args)

    def on_return(self, *args):
        for tracer in self.tracers:
            tracer.on_return(*args)

    def on_output(self, *args):
        for tracer in self.tracers:
            tracer.on_output(*args)

    def on_console(self, *args):
        for tracer in self.tracers:
            tracer.on_console(*args)

    def on_assign(self, *args):
        for tracer in self.tracers:
            if getattr(tracer, 'wants_assignments', False):
                tracer.on_assign(*args)


def _short(value, limit):
    text = repr(value)
    return text if len(text) <= limit else text[:limit - 3] + '...'
