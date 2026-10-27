"""LegacyCompatEngine: the legacy engine (pp_tests/gppl/legacy.py) plus the
documented GPPL workarounds (tests/support/engines.py explains the policy).

Kept in its own module so the class body can use the legacy engine's names
(Engine, UnsupportedGPPL, uncomment) verbatim: its _render mirrors the legacy
Engine._render line by line (guarded by tests/test_engine_harness.py), and it
is importable under either GPPL_ENGINE setting.
"""
import ast
import re
import types

from pp_tests.gppl.legacy import Engine, UnsupportedGPPL, uncomment

_QUOTED = re.compile(r'''('(?:[^']|'')*'|"(?:[^"]|"")*")''')
_LEADING_ZERO = re.compile(r'(?<![\w.])0+(?=\d)')
_PRINT = re.compile(r'(?im)^([ \t]*)print[ \t]+(.+?)[ \t]*$')
_TRACE = re.compile(r'(?im)^([ \t]*)trace[ \t]+.*$')
# Stock grammar is r'\d+\.(\d+)(?:\([pP]\))?'. The extended grammar adds literal
# <prefix>/<suffix> wrappers (e.g. '<(>5.3<)>' in older revisions), a leading
# '+' (always print the sign), and the (n)/(N) and (*k) modifiers.
_EXTENDED_FORMAT = re.compile(
    r'(?:<(?P<prefix>[^>]*)>)?(?P<sign>\+)?\d+\.(?P<decimals>\d+)'
    r'(?P<modifiers>(?:\((?:[pPnN]|\*[-+]?\d+(?:\.\d*)?)\))*)(?:<(?P<suffix>[^>]*)>)?')

def _unquoted_map(text, function):
    """Apply function to the parts of an expression outside string literals."""
    chunks = _QUOTED.split(text)
    for index in range(0, len(chunks), 2):
        chunks[index] = function(chunks[index], index, chunks)
    return ''.join(chunks)


def declared_globals(source):
    """Lower-case names declared with `global <type> ...` in a GPP source."""
    names = {}
    for raw in source.splitlines():
        line = raw.split(';', 1)[0].strip()
        match = re.fullmatch(r'global\s+(numeric|integer|logical|string)\s+(.+)', line, re.I)
        if match:
            for name in match[2].replace(',', ' ').split():
                names[name.lower()] = match[1].lower()
    return names


class LegacyCompatEngine(Engine):
    """Legacy engine (pp_tests/gppl/legacy.py) plus documented GPPL workarounds.

    Default-on (additive; the stock engine raises on these constructs):
      leading_zero_literals  ENGINE-006  `07` is an integer literal (GPP line 990).
      string_builtins        ENGINE-007  right(s, n) (clamped: '' for n <= 0, whole
                                         string for n > len) and tostr(v[:'fmt']).
      print_statement        ENGINE-008  `Print <expr>` records the message in
                                         self.messages and continues (assumed
                                         SolidCAM message-window semantics).
      trace_statement        ENGINE-018  `trace ...` lines are ignored (needed to run
                                         historical revisions with an active trace).
      extended_formats       ENGINE-018  '<(>5.3<)>', '+8.5', '(n)', '(*k)' descriptors.
    Opt-in (change results of paths the stock engine runs; semantics unverified):
      skipline               ENGINE-002  `skipline = false` makes the next nb/nl
                                         continue the current block, then resets.
      default_formats        ENGINE-003  numbers without <name>_f use numeric_def_f /
                                         integer_def_f instead of three decimals.
      declared_global_flags  ENGINE-005  declared globals get change flag False when
                                         a top-level call returns (no KeyError).
    """

    def __init__(self, source, *, leading_zero_literals=True, string_builtins=True,
                 print_statement=True, trace_statement=True, extended_formats=True,
                 skipline=False, default_formats=False, declared_global_flags=False):
        self.options = types.MappingProxyType(dict(
            leading_zero_literals=leading_zero_literals, string_builtins=string_builtins,
            print_statement=print_statement, trace_statement=trace_statement,
            extended_formats=extended_formats, skipline=skipline, default_formats=default_formats,
            declared_global_flags=declared_global_flags))
        if trace_statement:
            source = _TRACE.sub(r'\1; trace ignored by GpplCompatEngine (ENGINE-018)', source)
        if print_statement:
            source = _PRINT.sub(self._print_rewrite, source)
        super().__init__(source)
        if print_statement:
            self.procedures['gppl_print'] = []
            self.arguments['gppl_print'] = ['gppl_message']
        self.global_types = declared_globals(source)
        self.messages = []

    @staticmethod
    def _print_rewrite(match):
        indent, expression = match[1], uncomment(match[2])
        if ',' in expression:
            # The stock call parser splits arguments on every comma; keep such a
            # message as a plain assignment (its value lands in gppl_print_log).
            return f'{indent}gppl_print_log = {expression}'
        return f'{indent}call @gppl_print({expression})'

    def reset_runtime(self):
        self.messages = []

    # -- statements -------------------------------------------------------
    def call(self, procedure, arguments=()):
        name = procedure.lstrip('@').lower()
        if name == 'gppl_print' and self.options['print_statement']:
            self.messages.append(arguments[0] if arguments else '')
            return None
        try:
            return super().call(procedure, arguments)
        finally:
            if self.options['declared_global_flags'] and not self.stack:
                for variable in self.global_types:
                    if variable in self.state:
                        self.changed.setdefault(variable, False)

    # -- expressions ------------------------------------------------------
    def expression(self, value):
        options = self.options
        if options['leading_zero_literals'] or options['string_builtins']:
            def rewrite(chunk, index, chunks):
                if options['leading_zero_literals']:
                    chunk = _LEADING_ZERO.sub('', chunk)
                if options['string_builtins'] and index + 1 < len(chunks) and re.search(r':\s*$', chunk):
                    chunk = re.sub(r':\s*$', ', ', chunk)  # tostr(value:'fmt') -> tostr(value, 'fmt')
                return chunk
            value = _unquoted_map(value, rewrite)
        return super().expression(value)

    def _node(self, node):
        if (self.options['string_builtins'] and isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id in ('right', 'tostr')):
            if node.keywords:
                raise UnsupportedGPPL('keyword arguments are unsupported')
            arguments = [self._node(argument) for argument in node.args]
            if node.func.id == 'right':
                if len(arguments) != 2:
                    raise UnsupportedGPPL('right() takes two arguments')
                text, count = arguments
                count = int(count)
                return text[max(0, len(text) - count):] if count > 0 else ''
            if not 1 <= len(arguments) <= 2:
                raise UnsupportedGPPL('tostr() takes one or two arguments')
            value = arguments[0]
            if isinstance(value, str):
                return value
            descriptor = arguments[1] if len(arguments) > 1 else self.state.get('numeric_def_f')
            return self.format_number(value, descriptor)
        return super()._node(node)

    # -- output -----------------------------------------------------------
    def format_number(self, value, descriptor):
        """Render a number like the stock engine; extended descriptors when enabled."""
        precision, prefix, suffix, sign, factor = 3, '', '', False, 1
        if descriptor:
            stock = re.fullmatch(r'\d+\.(\d+)(?:\([pP]\))?', descriptor)
            extended = None if stock or not self.options['extended_formats'] else \
                _EXTENDED_FORMAT.fullmatch(descriptor)
            if stock:
                precision = int(stock[1])
            elif extended:
                precision = int(extended['decimals'])
                prefix, suffix = extended['prefix'] or '', extended['suffix'] or ''
                sign = bool(extended['sign'])
                for multiplier in re.findall(r'\(\*([-+]?\d+(?:\.\d*)?)\)', extended['modifiers'] or ''):
                    factor *= float(multiplier)
            else:
                raise UnsupportedGPPL(f'unsupported numeric format: {descriptor}')
        value = value * factor if factor != 1 else value
        text = format(value, f'.{precision}f')
        if precision:
            text = text.rstrip('0').rstrip('.')
        if text == '-0':
            text = '0'
        if sign and not text.startswith('-'):
            text = '+' + text
        return prefix + text + suffix

    def _default_descriptor(self, token, value):
        if not self.options['default_formats']:
            return None
        kind = self.global_types.get(token.lower())
        if kind is None:
            kind = 'integer' if isinstance(value, int) else 'numeric'
        return self.state.get('integer_def_f' if kind == 'integer' else 'numeric_def_f')

    def _newline(self):
        """nb/nl: a new block, unless skipline emulation swallows one request."""
        if self.options['skipline'] and self.state.get('skipline', True) is False:
            self.state['skipline'] = True
            return ''
        return '\n'

    def _render(self, body):
        # Mirrors pp_tests.gppl.legacy.Engine._render line by line; the only
        # differences are the _newline() and format_number() hooks above, which
        # reproduce the stock behaviour exactly when the opt-in options are off.
        result = ''
        variables = set()
        offset = 0
        while offset < len(body):
            if body[offset].isspace() or body[offset] == ',':
                offset += 1
                continue
            if body[offset] == '[':
                end = self._closing(body, offset, '[', ']')
                fragment, group_variables = self._render(body[offset + 1:end])
                missing = group_variables - self.changed.keys()
                if missing:
                    raise UnsupportedGPPL(f'modal output requires explicit change flags: {sorted(missing)}')
                if any(self.changed[v] for v in group_variables):
                    result += fragment
                variables.update(group_variables)
                offset = end + 1
                continue
            if body[offset] == '(':
                end = self._closing(body, offset, '(', ')')
                token = body[offset:end + 1]
                variables.update(re.findall(r'\b[a-zA-Z_]\w*\b', token.lower()))
                offset = end + 1
            else:
                match = re.match(r"'(?:[^']|'')*'|\"[^\"]*\"|[A-Za-z_]\w*", body[offset:])
                if not match:
                    raise UnsupportedGPPL(f'unsupported output near: {body[offset:]}')
                token = match[0]
                offset += len(token)
                if token.lower() in ('nb', 'nl'):
                    result += self._newline()
                    continue
                if token[0] not in "'\"":
                    variables.add(token.lower())
            descriptor = None
            if offset < len(body) and body[offset] == ':':
                fmt = re.match(r":('(?:[^']|'')*'|[A-Za-z_]\w*)", body[offset:])
                if not fmt:
                    raise UnsupportedGPPL(f'unsupported format: {body[offset:]}')
                descriptor = self.expression(fmt[1])
                offset += len(fmt[0])
            value = self.expression(token)
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                descriptor = (descriptor or self.state.get(token.lower() + '_f')
                              or self._default_descriptor(token, value))
                value = self.format_number(value, descriptor)
            result += str(value)
        return result, variables
