"""Immutable IR of a GPP: expression, output-item and statement nodes.

All nodes are frozen dataclasses. Statements carry ``span`` (GPP line and the
column of the statement text) and the comment-free source ``text``. Nodes that
evaluate expressions also carry ``fn``, the closure compiled from the
expression once at load time (``expr.compile_expr``); it is excluded from
equality and repr.

Procedures have two shapes built in one pass:
* ``body``: the statement tree (If.then/orelse, While.body) used by analysis,
  lint, coverage reports and the legacy ``(line, text)`` view;
* ``code``: a flat instruction list (EXEC / BRANCH / JUMP) executed by the
  runtime with an explicit program counter, so block nesting never consumes
  Python stack frames (600 nested ifs run; only GPPL calls recurse).
"""
from collections import namedtuple
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class Span:
    line: int
    col: int = 0


# ------------------------------------------------------------- expressions --
@dataclass(frozen=True)
class Num:
    value: Any


@dataclass(frozen=True)
class Str:
    value: str
    doubled: bool = False          # literal contained a doubled quote (policy-sensitive)


@dataclass(frozen=True)
class Bool:
    value: bool


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Flag:
    kind: str                      # 'change' | 'active'
    name: str


@dataclass(frozen=True)
class Unary:
    op: str                        # '-' | '+' | 'not'
    operand: Any


@dataclass(frozen=True)
class Binary:
    op: str                        # '+' '-' '*' '/' '%'
    left: Any
    right: Any


@dataclass(frozen=True)
class Compare:
    op: str                        # 'eq' 'ne' 'gt' 'lt' 'ge' 'le'
    left: Any
    right: Any
    paren: bool = field(default=False, compare=False)


@dataclass(frozen=True)
class Logical:
    op: str                        # 'and' | 'or'
    left: Any
    right: Any
    paren: bool = field(default=False, compare=False)


@dataclass(frozen=True)
class Call:
    name: str
    args: tuple


@dataclass(frozen=True)
class FmtLit:
    text: str


@dataclass(frozen=True)
class FmtVar:
    name: str


@dataclass(frozen=True)
class Formatted:                   # tostr(value:'5.0(p)') argument
    expr: Any
    fmt: Any                       # FmtLit | FmtVar


def children(node):
    """Direct sub-expressions of an expression node."""
    kind = type(node)
    if kind is Unary:
        return (node.operand,)
    if kind in (Binary, Compare, Logical):
        return (node.left, node.right)
    if kind is Call:
        return node.args
    if kind is Formatted:
        return (node.expr, node.fmt)
    return ()


def walk_expr(node):
    """Every node of an expression tree, iteratively (no recursion)."""
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(children(current)))


def expr_depth(node):
    best = 0
    stack = [(node, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > best:
            best = depth
        stack.extend((child, depth + 1) for child in children(current))
    return best


def value_names(node):
    """Variables whose values or change/active flags an expression reads: what a
    modal group depends on. Function names and string contents never count."""
    names = set()
    for item in walk_expr(node):
        kind = type(item)
        if kind is Var:
            names.add(item.name)
        elif kind is Flag:
            names.add(item.name)
    return names


def names_read(node):
    """value_names plus format variables (tostr(x:fmtvar))."""
    names = value_names(node)
    names.update(item.name for item in walk_expr(node) if type(item) is FmtVar)
    return names


def flags_read(node):
    return {item.name for item in walk_expr(node) if type(item) is Flag and item.kind == 'change'}


def functions_used(node):
    return {item.name for item in walk_expr(node) if type(item) is Call}


# ------------------------------------------------------------ output items --
@dataclass(frozen=True)
class Text:
    value: str
    doubled: bool = False


@dataclass(frozen=True)
class NewLine:
    kind: str                      # 'nb' | 'nl'


@dataclass(frozen=True, eq=False)
class Value:
    expr: Any
    fmt: Any                       # FmtLit | FmtVar | None
    hint: Optional[str]            # bare variable name: '<hint>_f' is its default format
    names: frozenset
    fn: Callable = field(repr=False)


@dataclass(frozen=True, eq=False)
class Modal:
    items: tuple
    names: frozenset


def walk_items(items):
    stack = list(reversed(items))
    while stack:
        item = stack.pop()
        yield item
        if type(item) is Modal:
            stack.extend(reversed(item.items))


def item_names(items):
    names = set()
    for item in items:
        if type(item) is Value:
            names |= item.names
        elif type(item) is Modal:
            names |= item.names
    return frozenset(names)


# --------------------------------------------------------------- statements --
@dataclass(frozen=True, eq=False)
class Stmt:
    span: Span
    text: str

    @property
    def line(self):
        return self.span.line


@dataclass(frozen=True, eq=False)
class Assign(Stmt):
    target: str
    expr: Any
    fn: Callable = field(repr=False)


@dataclass(frozen=True, eq=False)
class FlagAssign(Stmt):
    flag: str                      # 'change' | 'active'
    target: str
    expr: Any
    fn: Callable = field(repr=False)


@dataclass(frozen=True, eq=False)
class If(Stmt):
    cond: Any                      # None when the condition failed to parse (see error)
    fn: Callable = field(repr=False)
    then: tuple = ()
    orelse: tuple = ()
    has_else: bool = False
    else_line: Optional[int] = None
    end_line: Optional[int] = None
    error: Any = None


@dataclass(frozen=True, eq=False)
class While(Stmt):
    cond: Any
    fn: Callable = field(repr=False)
    body: tuple = ()
    end_line: Optional[int] = None
    error: Any = None


@dataclass(frozen=True, eq=False)
class CallProc(Stmt):
    proc: str
    args: tuple
    fns: tuple = field(repr=False)


@dataclass(frozen=True, eq=False)
class Output(Stmt):
    items: tuple
    names: frozenset


@dataclass(frozen=True, eq=False)
class Declare(Stmt):
    scope: str                     # 'local' | 'global'
    vtype: str
    names: tuple


@dataclass(frozen=True, eq=False)
class Input(Stmt):
    prompt: Any
    fn: Callable = field(repr=False)
    target: str = ''


@dataclass(frozen=True, eq=False)
class Abort(Stmt):
    pass


@dataclass(frozen=True, eq=False)
class Print(Stmt):
    items: tuple


@dataclass(frozen=True, eq=False)
class Trace(Stmt):
    pass


@dataclass(frozen=True, eq=False)
class Bad(Stmt):
    error: Any                     # GPPLSyntaxError raised when executed


def statement_children(stmt):
    kind = type(stmt)
    if kind is If:
        return stmt.then + stmt.orelse
    if kind is While:
        return stmt.body
    return ()


def walk_statements(body):
    """Every statement of a body, depth-first in source order, iteratively."""
    stack = list(reversed(body))
    while stack:
        stmt = stack.pop()
        yield stmt
        stack.extend(reversed(statement_children(stmt)))


def statement_expressions(stmt):
    """Expressions a statement evaluates (format references included)."""
    kind = type(stmt)
    if kind in (Assign, FlagAssign):
        return [stmt.expr]
    if kind in (If, While):
        return [stmt.cond] if stmt.cond is not None else []
    if kind is CallProc:
        return list(stmt.args)
    if kind is Input:
        return [stmt.prompt]
    if kind in (Output, Print):
        result = []
        for item in walk_items(stmt.items):
            if type(item) is Value:
                result.append(item.expr)
                if item.fmt is not None:
                    result.append(item.fmt)
        return result
    return []


# ----------------------------------------------------------------- program --
EXEC, BRANCH, JUMP = 'exec', 'branch', 'jump'
# op: EXEC runs ``stmt``; BRANCH evaluates ``fn`` (if/while condition of ``stmt``)
# and jumps to ``target`` when false; JUMP continues at ``target``.
Instr = namedtuple('Instr', 'op line stmt fn target')


class Procedure:
    """A compiled procedure. Built once by the loader, then treated as immutable
    (shared by every Engine created from the same source)."""

    def __init__(self, name, display, line, params):
        self.name, self.display, self.line, self.params = name, display, line, tuple(params)
        self.raw = []              # [(line, text)] comment-free statement lines (legacy view)
        self.body = ()
        self.code = ()
        self.end_line = None
        self.error = None          # first structural GPPLSyntaxError: the procedure refuses to run

    @property
    def param_names(self):
        return [name for _, name in self.params]

    def statements(self):
        return list(walk_statements(self.body))
