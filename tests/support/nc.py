"""Exact NC block/word parsing for Sinumerik output.

Assertions should compare parsed words, never substrings ('X15' must not match
'X150', 'M3' must not match 'M30'). Numbers are compared as floats, so 'M09'
equals 'M9' and 'X12.50' equals 'X12.5'.

Word shapes recognised (address is upper-case):
  G0 X12.345 M06 S8000 F500 T1 D1        address + number
  A=DC(270) A=ACP(22.3) I=AC(5)          address '=' mode '(' number ')'
  Z1=0. X1=0 CR=5                        address '=' number
  CYCLE81(30,12,2,-15,,0.25) WORKPIECE(..)  call with raw comma arguments
  MCALL CYCLE81 (30,..)                  (blank before '(' allowed, as the PP prints it)
  MSG("text")                            operator message (text kept verbatim)
  MCALL TRANS                            bare keyword (value None)
Anything else becomes a word with address None and the raw text, so unknown
syntax is visible to assertions instead of being dropped.
"""
import math
import re
from dataclasses import dataclass, field

_NUMBER = r'[+-]?(?:\d+\.?\d*|\.\d+)'
_TOKEN = re.compile(r'''
    (?P<msg>MSG\("[^"]*"\))
  | (?P<mode>(?P<maddr>[A-Z][A-Z0-9]*)=(?P<mname>ACP|ACN|DC|AC|IC)\((?P<mval>[^()]*)\))
  | (?P<call>(?P<cname>[A-Z_][A-Z0-9_]*)[ \t]*\((?P<cargs>(?:[^()"]|"[^"]*"|\([^()]*\))*)\))
  | (?P<assign>(?P<aaddr>[A-Z][A-Z0-9]*)=(?P<aval>''' + _NUMBER + r'''))(?=\s|$)
  | (?P<word>(?P<waddr>[A-Z])(?P<wval>''' + _NUMBER + r'''))(?=\s|$)
  | (?P<keyword>[A-Z_][A-Z0-9_]*)(?=\s|$)
  | (?P<other>\S+)
''', re.X)


def _number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class Word:
    raw: str
    address: str = None     # 'G', 'X', 'A', 'Z1', 'CYCLE81', 'MSG', 'MCALL', ...
    value: float = None     # numeric value (None for keywords, calls, MSG)
    mode: str = None        # 'ACP', 'ACN', 'DC', 'AC', 'IC' for A=ACP(..) style words
    args: tuple = ()        # raw call arguments for CYCLE81(...)
    kind: str = 'other'     # 'word', 'mode', 'assign', 'call', 'msg', 'keyword', 'other'

    def is_(self, address, value=None, tolerance=0.0):
        if self.address != address:
            return False
        if value is None:
            return True
        return self.value is not None and abs(self.value - value) <= tolerance


def parse_words(code):
    """Words of the code part of one block (comment already removed)."""
    words = []
    for match in _TOKEN.finditer(code.strip()):
        raw = match[0]
        if match['msg']:
            words.append(Word(raw, 'MSG', kind='msg', args=(raw[5:-2],)))
        elif match['mode']:
            words.append(Word(raw, match['maddr'], _number(match['mval']), match['mname'], kind='mode'))
        elif match['call']:
            args = tuple(_split_args(match['cargs']))
            words.append(Word(raw, match['cname'], args=args, kind='call'))
        elif match['assign']:
            words.append(Word(raw, match['aaddr'], _number(match['aval']), kind='assign'))
        elif match['word']:
            words.append(Word(raw, match['waddr'], _number(match['wval']), kind='word'))
        elif match['keyword']:
            words.append(Word(raw, match['keyword'], kind='keyword'))
        else:
            words.append(Word(raw))
    return words


def _split_args(text):
    args, depth, quoted, current = [], 0, False, ''
    for character in text:
        if character == '"':
            quoted = not quoted
        elif not quoted and character == '(':
            depth += 1
        elif not quoted and character == ')':
            depth -= 1
        if character == ',' and depth == 0 and not quoted:
            args.append(current.strip())
            current = ''
        else:
            current += character
    args.append(current.strip())
    return args


def split_comment(line):
    """(code, comment) split at the first ';' outside quotes and parentheses."""
    depth, quoted = 0, False
    for index, character in enumerate(line):
        if character == '"':
            quoted = not quoted
        elif not quoted and character == '(':
            depth += 1
        elif not quoted and character == ')':
            depth = max(0, depth - 1)
        elif character == ';' and not quoted and depth == 0:
            return line[:index].rstrip(), line[index + 1:]
    return line.rstrip(), None


@dataclass(frozen=True)
class Block:
    raw: str
    code: str
    comment: str = None
    words: tuple = field(default_factory=tuple)

    def __str__(self):
        return self.raw

    # word access ------------------------------------------------------------
    def find(self, address):
        return [word for word in self.words if word.address == address]

    def get(self, address, default=None):
        """Value of the first word with this address (default if absent)."""
        for word in self.words:
            if word.address == address:
                return word.value
        return default

    def has(self, address, value=None, tolerance=0.0):
        return any(word.is_(address, value, tolerance) for word in self.words)

    def codes(self, address):
        """Integer codes of all words with this address (G and M lists)."""
        return [int(word.value) if word.value is not None and float(word.value).is_integer() else word.value
                for word in self.words if word.address == address and word.kind == 'word']

    @property
    def g(self):
        return self.codes('G')

    @property
    def m(self):
        return self.codes('M')

    @property
    def axes(self):
        """Plain linear axis words {'X': .., 'Y': .., 'Z': ..} (G75 Z1=0 excluded)."""
        return {word.address: word.value for word in self.words
                if word.kind == 'word' and word.address in ('X', 'Y', 'Z')}

    def rotary(self, axis='A'):
        """(mode, value) of the rotary word (mode None for a plain 'A90'), or None."""
        for word in self.words:
            if word.address == axis and word.kind in ('mode', 'word'):
                return word.mode, word.value
        return None

    @property
    def homing_axes(self):
        """Axes referenced by a G75 block ('X1=0' -> 'X'), empty otherwise."""
        if 75 not in self.g:
            return set()
        return {word.address[0] for word in self.words
                if word.kind == 'assign' and re.fullmatch(r'[XYZA]1', word.address)}

    @property
    def cycle(self):
        """(name, args) of a CYCLExx call in this block, or None."""
        for word in self.words:
            if word.kind == 'call' and word.address.startswith('CYCLE'):
                return word.address, word.args
        return None

    @property
    def is_motion(self):
        return bool(self.axes) or self.rotary() is not None


def parse_block(line):
    code, comment = split_comment(line.strip())
    if code.lstrip().startswith('MSG('):
        code, comment = line.strip(), None
    return Block(line.strip(), code, comment, tuple(parse_words(code)))


def parse_blocks(text):
    """Non-empty NC blocks of text, in order."""
    return [parse_block(line) for line in text.splitlines() if line.strip()]


def block_texts(text):
    """Stripped non-empty lines (exact block comparison)."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def index_of(blocks, predicate, start=0, end=None):
    """Index of the first block in [start, end) matching predicate, or -1."""
    for index in range(start, len(blocks) if end is None else end):
        if predicate(blocks[index]):
            return index
    return -1


def last_index_of(blocks, predicate, start=0, end=None):
    found = -1
    for index in range(start, len(blocks) if end is None else end):
        if predicate(blocks[index]):
            found = index
    return found


# Sinumerik plane axes (abscissa, ordinate) and centre words. DIN 66025 /
# Siemens 828D programming manual: G17 X/Y viewed from +Z, G18 Z/X viewed from
# +Y, G19 Y/Z viewed from +X; G2 clockwise, G3 counter-clockwise; I/J/K are
# incremental from the start point unless written I=AC(..).
ARC_PLANES = {'xy': ('X', 'Y'), 'zx': ('Z', 'X'), 'yz': ('Y', 'Z')}
CENTER_WORDS = {'X': 'I', 'Y': 'J', 'Z': 'K'}


def arc_center(plane, start, block):
    """Centre (abscissa, ordinate) a Sinumerik control derives from a G2/G3 block.

    plane: 'xy' | 'zx' | 'yz'; start: {'X':..,'Y':..,'Z':..} start point. I/J/K
    written as I=AC(v) are absolute, plain I/J/K are incremental from start, a
    missing centre word means offset 0 (Siemens 828D programming manual).
    """
    if isinstance(block, str):
        block = parse_block(block)
    center = []
    for axis in ARC_PLANES[plane]:
        words = block.find(CENTER_WORDS[axis])
        if words and words[0].mode == 'AC':
            center.append(words[0].value)
        else:
            center.append(start[axis] + (words[0].value if words else 0.0))
    return tuple(center)


def arc_sweep_degrees(plane, start, block):
    """Sweep in degrees that a Sinumerik control executes for a G2/G3 block.

    plane: 'xy' | 'zx' | 'yz'; start: {'X':..,'Y':..,'Z':..} start point;
    block: Block or text. Missing end words keep the start coordinate; missing
    centre words mean offset 0. Returns a value in [0, 360); a full circle
    returns 0. CR= radius blocks are rejected (centre is not unique).
    """
    if isinstance(block, str):
        block = parse_block(block)
    if block.has('CR'):
        raise ValueError('CR= radius arcs have no unique centre')
    direction = [code for code in block.g if code in (2, 3)]
    if len(direction) != 1:
        raise ValueError(f'not a single G2/G3 block: {block.raw!r}')
    abscissa, ordinate = ARC_PLANES[plane]
    end = {axis: block.get(axis, start[axis]) for axis in 'XYZ'}
    center = dict(zip((abscissa, ordinate), arc_center(plane, start, block)))
    t_start = math.degrees(math.atan2(start[ordinate] - center[ordinate], start[abscissa] - center[abscissa]))
    t_end = math.degrees(math.atan2(end[ordinate] - center[ordinate], end[abscissa] - center[abscissa]))
    ccw = (t_end - t_start) % 360
    return ccw if direction[0] == 3 else (360 - ccw) % 360
