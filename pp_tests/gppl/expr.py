"""GPPL expressions: recursive-descent parser -> immutable nodes -> closures.

No eval/exec and no Python ``ast``: only the grammar below is accepted, so the
Python-only syntax the legacy engine silently evaluated (0x10, 1_000, 2j,
'ab'*2, 'a' 'b', 1 < 2 < 3, Python keywords) is rejected or treated as GPPL.

    expr     := binary(or)
    binary   := prefix { binop binary(prec(binop) + 1) }      (precedence climbing)
    prefix   := ('not' | '!') binary(not) | ('-' | '+') prefix | primary
    primary  := number | string | true | false | name | func '(' args ')'
              | ('change' | 'active') '(' name ')' | '(' expr ')'
    args     := expr [':' fmtref] { ',' expr }    (':fmt' only inside tostr)

    precedence, loosest first: or < and < not < comparisons (non-associative)
                               < + - < * / % < unary - +

Precedence (and above or, '!'/'not' below comparisons) mirrors the legacy
engine, which inherited it from Python; it is a documented assumption.

Depth: recursion while parsing and the depth of the finished tree are both
capped (policy max_expr_depth, default 100) with a located syntax error, so a
pathological expression can never exhaust the Python stack at load or run time.
"""
import math
import operator

from . import nodes as N
from .builtins import BUILTINS, FLAG_FUNCTIONS
from .errors import GPPLRuntimeError, GPPLSyntaxError
from .lexer import tokenize

CMP_WORDS = {'eq': 'eq', 'ne': 'ne', 'gt': 'gt', 'lt': 'lt', 'ge': 'ge', 'le': 'le'}
CMP_SYMBOLS = {'==': 'eq', '!=': 'ne', '>': 'gt', '<': 'lt', '>=': 'ge', '<=': 'le'}
CMP_FUNCS = {'eq': operator.eq, 'ne': operator.ne, 'gt': operator.gt, 'lt': operator.lt,
             'ge': operator.ge, 'le': operator.le}
KEYWORDS = {'and', 'or', 'not', 'true', 'false'} | set(CMP_WORDS)
DEFAULT_MAX_DEPTH = 100
OR, AND, NOT, CMP, ADD, MUL, UNARY = range(1, 8)        # precedence levels, loosest first


class Parser:
    def __init__(self, tokens, source, max_depth=DEFAULT_MAX_DEPTH):
        self.tokens = tokens
        self.index = 0
        self.source = source
        self.max_depth = max_depth
        self.depth = 0

    @property
    def tok(self):
        return self.tokens[self.index]

    def peek(self, offset=1):
        return self.tokens[min(self.index + offset, len(self.tokens) - 1)]

    def advance(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def error(self, message):
        raise GPPLSyntaxError(f'expression {self.source!r}: {message}')

    def expect_op(self, op):
        if not self.tok.is_op(op):
            self.error(f'expected {op!r} near {self.tok.text or "end"!r}')
        return self.advance()

    def at_end(self):
        return self.tok.kind == 'end'

    def _enter(self):
        self.depth += 1
        if self.depth > self.max_depth:
            self.error(f'nested deeper than {self.max_depth} levels (policy max_expr_depth)')

    def parse_expression(self):
        self._enter()
        try:
            return self.parse_binary(OR)
        finally:
            self.depth -= 1

    def finish(self, node):
        """Check the depth of a complete tree (binary chains are built by loops)."""
        if N.expr_depth(node) > self.max_depth:
            self.error(f'nested deeper than {self.max_depth} levels (policy max_expr_depth)')
        return node

    def binary_op(self):
        """(node class, op, precedence) of the binary operator at the cursor, or None."""
        token = self.tok
        if token.kind == 'id':
            if token.value in ('and', 'or'):
                return N.Logical, token.value, AND if token.value == 'and' else OR
            if token.value in CMP_WORDS:
                return N.Compare, CMP_WORDS[token.value], CMP
        elif token.kind == 'op':
            if token.value in CMP_SYMBOLS:
                return N.Compare, CMP_SYMBOLS[token.value], CMP
            if token.value in ('+', '-'):
                return N.Binary, token.value, ADD
            if token.value in ('*', '/', '%'):
                return N.Binary, token.value, MUL
            if token.value == '=':
                self.error("'=' is assignment; use eq or ==")
        return None

    def parse_binary(self, min_prec):
        """Precedence climbing: left-associative and/or/+-/*%, non-associative
        comparisons. Python stack use is ~4 frames per nesting level."""
        node = self.parse_prefix(min_prec)
        while True:
            found = self.binary_op()
            if found is None or found[2] < min_prec:
                return node
            kind, op, prec = found
            self.advance()
            right = self.parse_binary(prec + 1)
            node = kind(op, node, right)
            if kind is N.Compare and self.binary_op() and self.binary_op()[2] == CMP:
                self.error('chained comparisons are not GPPL')

    def parse_prefix(self, min_prec):
        token = self.tok
        if token.is_word('not') or token.is_op('!'):
            if min_prec > NOT:
                self.error(f'{token.text!r} must start an operand of and/or (use parentheses)')
            self.advance()
            self._enter()
            try:
                return N.Unary('not', self.parse_binary(NOT))   # '!' binds looser than comparisons
            finally:
                self.depth -= 1
        if token.is_op('-', '+'):
            self.advance()
            self._enter()
            try:
                return N.Unary(token.value, self.parse_prefix(UNARY))
            finally:
                self.depth -= 1
        return self.parse_primary()

    def parse_primary(self):
        token = self.tok
        if token.kind == 'num':
            self.advance()
            return N.Num(token.value)
        if token.kind == 'str':
            self.advance()
            if self.tok.kind == 'str':
                self.error('adjacent string literals are not concatenated in GPPL; use +')
            return N.Str(token.value, token.doubled)
        if token.is_op('('):
            self.advance()
            node = self.parse_expression()
            self.expect_op(')')
            if type(node) in (N.Compare, N.Logical):
                node = type(node)(node.op, node.left, node.right, paren=True)
            return node
        if token.kind == 'id':
            self.advance()
            name = token.value
            if name in ('true', 'false'):
                return N.Bool(name == 'true')
            if name in KEYWORDS:
                self.error(f'unexpected keyword {token.text!r}')
            if self.tok.is_op('('):
                return self.parse_call(name, token.text)
            return N.Var(name)
        self.error(f'unexpected {token.text or "end of expression"!r}')

    def parse_call(self, name, text):
        self.expect_op('(')
        if name in FLAG_FUNCTIONS:
            target = self.advance()
            if target.kind != 'id' or not self.tok.is_op(')'):
                self.error(f'{name}() takes a single variable name')
            self.advance()
            return N.Flag(name, target.value)
        if name not in BUILTINS:
            self.error(f'unknown function {text}()')
        args = []
        if not self.tok.is_op(')'):
            while True:
                if self.tok.kind == 'id' and self.peek().is_op('='):
                    self.error('keyword arguments are unsupported')
                arg = self.parse_expression()
                if self.tok.is_op(':'):
                    if name != 'tostr':
                        self.error("':format' is only allowed inside tostr()")
                    self.advance()
                    arg = N.Formatted(arg, self.parse_format_ref())
                args.append(arg)
                if self.tok.is_op(','):
                    self.advance()
                    continue
                break
        self.expect_op(')')
        low, high, _, _ = BUILTINS[name]
        if not low <= len(args) <= high:
            self.error(f'{text}() takes {low} argument(s), got {len(args)}')
        return N.Call(name, tuple(args))

    def parse_format_ref(self):
        token = self.advance()
        if token.kind == 'str':
            return N.FmtLit(token.value)
        if token.kind == 'id':
            return N.FmtVar(token.value)
        self.error(f'format must be a string literal or a variable, got {token.text or "end"!r}')


_CACHE = {}


def parse_expression(text, escape='double', max_depth=DEFAULT_MAX_DEPTH):
    """Parse a complete expression (cached by text, lexing policy and depth cap)."""
    key = (text, escape, max_depth)
    tree = _CACHE.get(key)
    if tree is None:
        tokens = tokenize(text, escape)
        parser = Parser(tokens, text, max_depth)
        if parser.at_end():
            parser.error('empty expression')
        try:
            tree = parser.finish(parser.parse_expression())
        except RecursionError:
            parser.error('too deeply nested')
        if not parser.at_end():
            parser.error(f'unexpected {parser.tok.text!r}')
        if len(_CACHE) > 20000:
            _CACHE.clear()
        _CACHE[key] = tree
    return tree


# ----------------------------------------------------------------- compile --
def _is_number(value):
    return isinstance(value, (int, float))     # bool counts, as in the legacy engine


def compile_expr(node):
    """Return a closure ``f(rt)`` evaluating ``node`` against runtime ``rt``."""
    return _COMPILERS[type(node)](node)


def _c_const(node):
    value = node.value
    return lambda rt: value


def _c_var(node):
    name = node.name
    return lambda rt: rt.lookup(name)


def _c_flag(node):
    kind, name = node.kind, node.name
    return lambda rt: rt.get_flag(kind, name)


def _c_unary(node):
    inner = compile_expr(node.operand)
    if node.op == 'not':
        return lambda rt: not inner(rt)
    negate = node.op == '-'

    def unary(rt):
        value = inner(rt)
        if not _is_number(value):
            raise GPPLRuntimeError(f'unary {node.op} on non-number {value!r}')
        return -value if negate else +value
    return unary


def _c_logical(node):
    left, right = compile_expr(node.left), compile_expr(node.right)
    if node.op == 'and':
        return lambda rt: bool(left(rt)) and bool(right(rt))
    return lambda rt: bool(left(rt)) or bool(right(rt))


def _c_binary(node):
    op, left, right = node.op, compile_expr(node.left), compile_expr(node.right)
    if op == '+':
        def add(rt):
            a, b = left(rt), right(rt)
            if (isinstance(a, str) and isinstance(b, str)) or (_is_number(a) and _is_number(b)):
                return a + b
            raise GPPLRuntimeError(f'cannot add {a!r} and {b!r}')
        return add
    function = {'-': operator.sub, '*': operator.mul, '/': operator.truediv, '%': None}[op]

    def arith(rt):
        a, b = left(rt), right(rt)
        if not (_is_number(a) and _is_number(b)):
            raise GPPLRuntimeError(f'arithmetic {op!r} on non-numbers {a!r}, {b!r}')
        try:
            if function is None:                       # '%': policy modulo
                if rt.pol.modulo == 'truncate' and b:
                    result = math.fmod(a, b)
                    return int(result) if isinstance(a, int) and isinstance(b, int) else result
                return a % b
            return function(a, b)
        except ZeroDivisionError:
            raise GPPLRuntimeError(f'division by zero in {a!r} {op} {b!r}') from None
    return arith


def _c_compare(node):
    op = node.op
    function = CMP_FUNCS[op]
    left, right = compile_expr(node.left), compile_expr(node.right)

    def compare(rt):
        a, b = left(rt), right(rt)
        a_str, b_str = isinstance(a, str), isinstance(b, str)
        if a_str and b_str:
            if rt.pol.string_compare == 'case_insensitive':
                a, b = a.lower(), b.lower()
            return function(a, b)
        if a_str or b_str:
            if rt.pol.mixed_compare == 'error' or op not in ('eq', 'ne'):
                raise GPPLRuntimeError(f'comparison {op} between {a!r} and {b!r}')
            return op == 'ne'
        return function(a, b)
    return compare


def _c_call(node):
    name = node.name
    impl = BUILTINS[name][2]
    if name == 'tostr' and type(node.args[0]) is N.Formatted:
        value_fn = compile_expr(node.args[0].expr)
        fmt = node.args[0].fmt
        return lambda rt: impl(rt, value_fn(rt), rt.resolve_format(fmt))
    args = [compile_expr(arg) for arg in node.args]
    if len(args) == 1:
        only = args[0]
        return lambda rt: impl(rt, only(rt))
    return lambda rt: impl(rt, *[arg(rt) for arg in args])


_COMPILERS = {
    N.Num: _c_const, N.Str: _c_const, N.Bool: _c_const, N.Var: _c_var, N.Flag: _c_flag,
    N.Unary: _c_unary, N.Logical: _c_logical, N.Binary: _c_binary, N.Compare: _c_compare,
    N.Call: _c_call,
}
