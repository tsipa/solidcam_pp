"""GPPL function library with provenance.

``status``: 'used' = called by the 4x GPP (or the Mach3 GPP in the repository
history) and therefore required; 'assumed' = common GPPL function whose meaning
is unambiguous given the 'used' ones (degrees, like sin/cos), provided for other
posts. Lint reports every 'assumed' function a PP calls. Functions whose meaning
is uncertain (int: truncate or floor? frac?) are deliberately absent: calling
them is an 'unknown function' syntax error.
"""
import math
import re

from .errors import GPPLRuntimeError

NUMERIC_TEXT = re.compile(r'[ \t]*[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?[ \t]*')
NUMERIC_PREFIX = re.compile(r'[ \t]*[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')


def _num(value, fname):
    if isinstance(value, (int, float)):        # bool is an int, as in the legacy engine
        return value
    raise GPPLRuntimeError(f'{fname}() expects a number, got {value!r}')


def _str(value, fname):
    if not isinstance(value, str):
        raise GPPLRuntimeError(f'{fname}() expects a string, got {value!r}')
    return value


def _count(value, fname):
    return int(_num(value, fname))


def _bad_index(rt, fname, detail):
    raise GPPLRuntimeError(f'{fname}(): {detail} (policy string_index=error; '
                           f"'python' keeps the legacy slice result, 'clamp' clips to the string)")


def f_left(rt, text, count):
    text, count = _str(text, 'left'), _count(count, 'left')
    if count < 0:
        mode = rt.pol.string_index
        if mode == 'error':
            _bad_index(rt, 'left', f'negative count {count}')
        if mode == 'clamp':
            return ''
    return text[:count]


def f_right(rt, text, count):
    text, count = _str(text, 'right'), _count(count, 'right')
    if count < 0:
        if rt.pol.string_index == 'error':
            _bad_index(rt, 'right', f'negative count {count}')
        return ''                                # 'python' (text[len+|n|:]) and 'clamp' agree
    return text[len(text) - count:] if count else ''


def f_substr(rt, text, start, count):
    text, start, count = _str(text, 'substr'), _count(start, 'substr'), _count(count, 'substr')
    if start < 1 or count < 0:
        mode = rt.pol.string_index
        if mode == 'error':
            _bad_index(rt, 'substr', f'start={start} count={count} (start is 1-based)')
        if mode == 'python':
            return text[start - 1:start - 1 + count]
        end = start + max(count, 0)
        start = max(start, 1)
        return text[start - 1:end - 1] if end > start else ''
    return text[start - 1:start - 1 + count]


def f_instr(rt, text, sub):
    return _str(text, 'instr').find(_str(sub, 'instr')) + 1


def f_strlen(rt, text):
    return len(_str(text, 'strlen'))


def f_tonum(rt, text):
    if isinstance(text, (int, float)):
        return float(text)                       # legacy: float(x)
    text = _str(text, 'tonum')
    if NUMERIC_TEXT.fullmatch(text):
        return float(text)
    if rt.pol.tonum == 'strict':
        raise GPPLRuntimeError(f'tonum() of non-numeric string {text!r} (policy tonum=strict)')
    prefix = NUMERIC_PREFIX.match(text)
    return float(prefix.group()) if prefix else 0.0


def f_tostr(rt, value, spec=None):
    if isinstance(value, str):
        return value
    return rt.render_value(value, spec, None)


def _deg(fn, name):
    return lambda rt, x: fn(math.radians(_num(x, name)))


def _inv_deg(fn, name):
    def inner(rt, x):
        try:
            return math.degrees(fn(_num(x, name)))
        except ValueError as exc:
            raise GPPLRuntimeError(f'{name}({x}): {exc}') from exc
    return inner


def f_sqrt(rt, x):
    x = _num(x, 'sqrt')
    if x < 0:
        raise GPPLRuntimeError(f'sqrt of negative number {x}')
    return math.sqrt(x)


# name: (min_args, max_args, implementation, status)
BUILTINS = {
    'abs': (1, 1, lambda rt, x: abs(_num(x, 'abs')), 'used'),
    'sin': (1, 1, _deg(math.sin, 'sin'), 'used'),
    'cos': (1, 1, _deg(math.cos, 'cos'), 'used'),
    'tan': (1, 1, _deg(math.tan, 'tan'), 'assumed'),
    'asin': (1, 1, _inv_deg(math.asin, 'asin'), 'assumed'),
    'acos': (1, 1, _inv_deg(math.acos, 'acos'), 'assumed'),
    'atan': (1, 1, _inv_deg(math.atan, 'atan'), 'assumed'),
    'sqrt': (1, 1, f_sqrt, 'assumed'),
    'strlen': (1, 1, f_strlen, 'used'),
    'instr': (2, 2, f_instr, 'used'),
    'left': (2, 2, f_left, 'used'),
    'right': (2, 2, f_right, 'used'),
    'substr': (3, 3, f_substr, 'used'),
    'tonum': (1, 1, f_tonum, 'used'),
    'tostr': (1, 1, f_tostr, 'used'),     # tostr(expr[:format]); the format is parsed specially
}
FLAG_FUNCTIONS = ('change', 'active')
