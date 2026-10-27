"""Lexical layer: comment stripping and one tokenizer shared by expressions,
output statements, declarations and calls (the legacy engine used three regexes
plus Python's own tokenizer, which disagreed with each other).

Numbers and identifiers are ASCII-only: '07' is the integer 7 (GPPL, not
Python octal rules), '650.' and '.5' are numbers, '1e3' stays accepted as the
legacy engine accepted it; '0x10', '1_000', '2j' and Unicode digits are errors.
"""
import re

from .errors import GPPLSyntaxError

NUMBER = re.compile(r'(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)(?:[eE][+-]?[0-9]+)?')
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
SPACE = ' \t\r\n\f\v'
OPERATORS = ('!=', '==', '>=', '<=', '+', '-', '*', '/', '%', '<', '>',
             '=', '!', '(', ')', ',', '[', ']', ':', '@', '{', '}')
C_ESCAPES = {'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}


def strip_comment(line, escape='double'):
    """Remove a ';' comment outside quotes and surrounding whitespace (the legacy
    ``uncomment`` rule, including doubled quotes inside literals)."""
    escape = escape.split('+', 1)[0]
    quoted = None
    index = 0
    length = len(line)
    while index < length:
        char = line[index]
        if quoted:
            if char == quoted:
                if escape == 'double' and index + 1 < length and line[index + 1] == quoted:
                    index += 2
                    continue
                quoted = None
        elif char in '\'"':
            quoted = char
        elif char == ';':
            return line[:index].strip()
        index += 1
    return line.strip()


class Token:
    __slots__ = ('kind', 'value', 'pos', 'text', 'doubled')

    def __init__(self, kind, value, pos, text, doubled=False):
        self.kind, self.value, self.pos, self.text, self.doubled = kind, value, pos, text, doubled

    def is_op(self, *ops):
        return self.kind == 'op' and self.value in ops

    def is_word(self, *words):
        return self.kind == 'id' and self.value in words

    def __repr__(self):
        return f'Token({self.kind},{self.value!r}@{self.pos})'


def read_string(text, start, escape):
    """Read a literal starting at ``text[start]``. ``escape`` is the lexing key:
    'double' or 'none' for doubled quotes, optionally suffixed '+c' for backslash
    escapes (policy string_escapes='c'). Returns (value, end, doubled) where
    ``doubled`` reports a doubled quote whose meaning depends on the policy."""
    quote = text[start]
    index = start + 1
    parts = []
    c_escapes = escape.endswith('+c')
    escape = escape.split('+', 1)[0]
    doubled = False
    while index < len(text):
        char = text[index]
        if c_escapes and char == '\\' and index + 1 < len(text) and text[index + 1] in C_ESCAPES:
            parts.append(C_ESCAPES[text[index + 1]])
            index += 2
            continue
        if char == quote:
            if index + 1 < len(text) and text[index + 1] == quote:
                if escape == 'double':
                    parts.append(quote)
                    doubled = True
                    index += 2
                    continue
                doubled = True
            return ''.join(parts), index + 1, doubled
        parts.append(char)
        index += 1
    raise GPPLSyntaxError(f'unterminated string literal: {text[start:]}')


def tokenize(text, escape='double'):
    tokens = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char in SPACE:
            index += 1
            continue
        if char in '\'"':
            value, end, doubled = read_string(text, index, escape)
            tokens.append(Token('str', value, index, text[index:end], doubled))
            index = end
            continue
        if '0' <= char <= '9' or (char == '.' and index + 1 < length and '0' <= text[index + 1] <= '9'):
            match = NUMBER.match(text, index)
            raw = match.group()
            after = match.end()
            if after < length and (text[after].isalnum() or text[after] in '_.'):
                raise GPPLSyntaxError(f'invalid number literal near {text[index:after + 1]!r}')
            # GPPL accepts leading zeros: 07 == 7 (the GPP has 'iCoolantM5ON = 07').
            value = int(raw) if raw.isdigit() else float(raw)
            tokens.append(Token('num', value, index, raw))
            index = after
            continue
        match = IDENT.match(text, index)
        if match:
            raw = match.group()
            after = match.end()
            if after < length and text[after].isalnum() and not text[after].isascii():
                raise GPPLSyntaxError(f'non-ASCII character in identifier near {text[index:after + 1]!r}')
            tokens.append(Token('id', raw.lower(), index, raw))
            index = after
            continue
        if text.startswith('<>', index):
            raise GPPLSyntaxError("'<>' is not supported; use ne or !=")
        for op in OPERATORS:
            if text.startswith(op, index):
                tokens.append(Token('op', op, index, op))
                index += len(op)
                break
        else:
            raise GPPLSyntaxError(f'unexpected character {char!r} in {text!r}')
    tokens.append(Token('end', None, length, ''))
    return tokens
