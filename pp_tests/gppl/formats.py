"""GPPL numeric format declarations, parsed once into FormatSpec and rendered
under the formatting policies.

Two grammars (policy ``format_grammar``):

* ``legacy`` (compat): exactly what the legacy engine accepted,
  ``digits '.' digits ['(p)'|'(P)']``; only the decimals matter.
* ``extended`` (session): the grammar found in this PP family (the 4x GPP, its
  3x predecessor and the Mach3 GPP in the repository history)::

      format := ['<' prefix '>'] ['+'] digits '.' digits ['(' flag {flag} ')'] ['/' number] ['<' suffix '>']
      flag   := '*' signed-number | '/' number | 'p' | 'P' | 'n' | 'N'

  No whitespace is allowed anywhere (' 5.3' is rejected) and '()' is invalid.

Observed (real trace excerpts): no flag -> trailing zeros and the point are
trimmed ('X132', 'Z15.8333'); '2.0(p)' prints 0 as 'G0'. Not observed: '(p)'/'(n)'
on integral values with decimals, '+' on zero, integer-digit overflow. Those are
policies (flag_p, flag_n, plus_zero), not hard-coded guesses.
"""
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .errors import UnsupportedGPPL

LEGACY_RE = re.compile(r'([0-9]+)\.([0-9]+)(?:\(([pP])\))?')
EXTENDED_RE = re.compile(
    r'(?:<(?P<prefix>[^>]*)>)?(?P<plus>\+)?(?P<int>[0-9]+)\.(?P<dec>[0-9]+)'
    r'(?:\((?P<flags>[^)]+)\))?(?:/(?P<div>[0-9]+(?:\.[0-9]+)?))?(?:<(?P<suffix>[^>]*)>)?')
FLAG_RE = re.compile(r'\*(?P<mul>[+-]?[0-9]+(?:\.[0-9]+)?)|/(?P<div>[0-9]+(?:\.[0-9]+)?)|(?P<letter>[pPnN])')


@dataclass(frozen=True)
class FormatSpec:
    text: str
    int_digits: int
    dec_digits: int
    zero_pad: bool = False
    plus: bool = False
    flags: frozenset = frozenset()
    scale: float = 1.0
    prefix: str = ''
    suffix: str = ''


_CACHE = {}


def parse_format(text, grammar='legacy'):
    key = (text, grammar) if isinstance(text, str) else None
    spec = _CACHE.get(key) if key else None
    if spec is not None:
        return spec
    if not isinstance(text, str):
        raise UnsupportedGPPL(f'numeric format must be a string, got {text!r}')
    spec = _parse_legacy(text) if grammar == 'legacy' else _parse_extended(text)
    _CACHE[key] = spec
    return spec


MAX_DIGITS = 30


def _check_digits(spec, integer_digits_matter=True):
    # The legacy grammar ignores the integer digits ('99.0' renders like '5.0'), so only
    # the decimals are capped there; the extended grammar zero-pads to them.
    if spec.dec_digits > MAX_DIGITS or (integer_digits_matter and spec.int_digits > MAX_DIGITS):
        raise UnsupportedGPPL(f'unsupported numeric format: {spec.text} (more than {MAX_DIGITS} digits)')
    return spec


def _parse_legacy(text):
    match = LEGACY_RE.fullmatch(text)
    if not match:
        hint = ''
        try:
            _parse_extended(text)
            hint = ' (accepted under policy format_grammar=extended)'
        except UnsupportedGPPL:
            pass
        raise UnsupportedGPPL(f'unsupported numeric format: {text}{hint}')
    return _check_digits(FormatSpec(text=text, int_digits=int(match[1]), dec_digits=int(match[2]),
                                    flags=frozenset({'p'}) if match[3] else frozenset()), False)


def _parse_extended(text):
    match = EXTENDED_RE.fullmatch(text)
    if not match:
        raise UnsupportedGPPL(f'unsupported numeric format: {text}')
    flags = set()
    scale = 1.0
    raw_flags = match['flags'] or ''
    position = 0
    while position < len(raw_flags):
        flag = FLAG_RE.match(raw_flags, position)
        if not flag:
            raise UnsupportedGPPL(f'unsupported numeric format flag {raw_flags[position:]!r} in {text}')
        if flag['mul']:
            scale *= float(flag['mul'])
        elif flag['div']:
            scale /= float(flag['div'])
        else:
            flags.add(flag['letter'].lower())
        position = flag.end()
    if match['div']:
        scale /= float(match['div'])
    return _check_digits(FormatSpec(text=text, int_digits=int(match['int']), dec_digits=int(match['dec']),
                                    zero_pad=len(match['int']) > 1 and match['int'].startswith('0'),
                                    plus=bool(match['plus']), flags=frozenset(flags), scale=scale,
                                    prefix=match['prefix'] or '', suffix=match['suffix'] or ''))


def check_literal(text):
    """(legacy_error, extended_error) for a format literal; None means accepted."""
    result = []
    for grammar in ('legacy', 'extended'):
        try:
            parse_format(text, grammar)
            result.append(None)
        except UnsupportedGPPL as exc:
            result.append(str(exc))
    return tuple(result)


def _fixed(value, decimals, rounding):
    if rounding == 'half_away':
        quantum = Decimal(1).scaleb(-decimals)
        return str(Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_UP))
    return format(value, f'.{decimals}f')


def render_number(value, spec, policies):
    """Render a number; ``spec`` None means the legacy default precision."""
    if spec is None:
        decimals, scale, flags, plus = policies.default_precision, 1.0, frozenset(), False
    else:
        decimals, scale, flags, plus = spec.dec_digits, spec.scale, spec.flags, spec.plus
    if scale != 1.0:
        value = value * scale
    text = _fixed(value, decimals, policies.rounding)
    if decimals:
        if policies.trailing_zeros != 'keep':
            trimmed = text.rstrip('0')
            if trimmed.endswith('.') and 'p' in flags and policies.flag_p == 'keep_point':
                text = trimmed
            else:
                text = trimmed.rstrip('.')
        if 'n' in flags and policies.flag_n == 'no_point' and text.endswith('.'):
            text = text[:-1]
    if text.lstrip('-').strip('0.') == '':
        text = text.lstrip('-')                     # '-0', '-0.000' -> '0'
    if spec is not None and spec.zero_pad:
        negative = text.startswith('-')
        whole, dot, frac = text.lstrip('-').partition('.')
        text = ('-' if negative else '') + whole.zfill(spec.int_digits) + dot + frac
    if plus and not text.startswith('-'):
        if text.strip('0.') != '' or policies.plus_zero == 'plus':
            text = '+' + text
    if spec is not None:
        text = spec.prefix + text + spec.suffix
    return text
