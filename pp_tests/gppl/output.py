"""NC output stream: the file SolidCAM would write.

Every ``{...}`` statement is recorded twice:

* ``Engine.output`` - the v1 *fragment list* (one string per statement, nb/nl
  as '\\n'), kept byte-identical for the legacy suite;
* ``OutputStream`` - NC *lines* with block numbers, ``skipline`` line joining,
  ``end_block_text``/``remove_blanks``, empty-line policy and provenance
  (opening statement ``@proc:line`` and the session event index).
"""


class NCLine:
    __slots__ = ('text', 'numbered', 'number', 'origin', 'event', 'stack')

    def __init__(self, numbered, origin, event, stack):
        self.text = ''
        self.numbered = numbered
        self.number = ''
        self.origin = origin
        self.event = event
        self.stack = stack

    @property
    def full(self):
        return self.number + self.text


class OutputStream:
    def __init__(self, engine):
        self.engine = engine
        self.lines = []
        self.current = None
        self.event = None
        self._consumed_epoch = -1

    # ---- writing -------------------------------------------------------
    def write(self, pieces, origin):
        engine = self.engine
        for kind, text in pieces:
            if kind == 'text':
                if self.current is None:
                    self._open(False, origin)
                line = self.current
                if text and not line.text:
                    line.event = self.event          # attribute to the event writing first text
                line.text += text
            elif kind == 'nb':
                if engine.policies.skipline == 'join_next_nb' and self.current is not None \
                        and self._consumed_epoch != engine.skipline_epoch \
                        and not _truthy(engine.peek('skipline', True)):
                    # one-shot: this nb continues the current line; the PP-visible
                    # variable is left alone, the stream remembers which assignment it used
                    self._consumed_epoch = engine.skipline_epoch
                    continue
                self._open(True, origin)
            else:   # nl
                self._open(False, origin)

    def _open(self, numbered, origin):
        self._close()
        self.current = NCLine(numbered, origin, self.event, tuple(self.engine.stack))

    def _close(self):
        line = self.current
        if line is None:
            return
        self.current = None
        engine = self.engine
        if _truthy(engine.peek('remove_blanks', False)):
            line.text = line.text.replace(' ', '')
        if line.text.strip() == '' and engine.policies.empty_lines == 'drop':
            return
        suffix = engine.peek('end_block_text', '')
        if isinstance(suffix, str) and suffix:
            line.text += suffix
        if line.numbered and engine.policies.block_numbers == 'blknum_exist' and \
                _truthy(engine.peek('blknum_exist', False)):
            line.number = self._next_block_number()
        self.lines.append(line)

    def _next_block_number(self):
        engine = self.engine
        number = engine.peek('blknum', 1)
        delta = engine.peek('blknum_delta', 1)
        maximum = engine.peek('blknum_max', None)
        letter = engine.peek('blknum_letter', 'N')
        spec_text = engine.peek('blknum_f', None)
        from .formats import parse_format, render_number
        spec = parse_format(spec_text, engine.policies.format_grammar) if isinstance(spec_text, str) else None
        rendered = letter + render_number(number, spec, engine.policies) + ' '
        number += delta
        if isinstance(maximum, (int, float)) and number > maximum:
            number = delta
        engine.poke('blknum', number)
        return rendered

    def finish(self):
        self._close()

    # ---- reading -------------------------------------------------------
    def all_lines(self):
        lines = list(self.lines)
        if self.current is not None and (self.current.text.strip() or self.engine.policies.empty_lines == 'keep'):
            lines.append(self.current)
        return lines

    def text(self):
        return ''.join(line.full + '\n' for line in self.all_lines())

    def lines_since(self, position):
        """Closed lines from ``position`` plus the open line (O(new lines))."""
        lines = self.lines[position:]
        if self.current is not None and (self.current.text.strip() or self.engine.policies.empty_lines == 'keep'):
            lines.append(self.current)
        return lines

    def lines_for_event(self, index, since=0):
        return [line for line in self.lines_since(since) if line.event == index]

    def annotated(self):
        rows = []
        for line in self.all_lines():
            proc, number = line.origin
            event = '' if line.event is None else f'#{line.event}'
            rows.append(f'{event:>5} @{proc}:{number:<5} | {line.full}')
        return '\n'.join(rows) + '\n'


def _truthy(value):
    if isinstance(value, str):
        return value != ''
    return bool(value)
