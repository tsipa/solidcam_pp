"""Load-time compilation of a whole GPP into the immutable IR (nodes.py).

Every line of the file is parsed when it loads. Statement-level problems do not
abort loading (legacy contract: unexecuted unsupported constructs are allowed);
they become ``Bad`` nodes or poisoned conditions plus diagnostics, and raise only
when executed. A procedure with a structural error (unclosed if, endw without
while, ...) refuses to run before any side effect. ``Policies(load_errors=
'raise')`` turns every error diagnostic, plus code outside procedures and missing
endp, into a load failure.

Fatal at load, exactly like the legacy engine: an invalid procedure header and a
duplicate procedure name.
"""
import hashlib
import re

from . import nodes as N
from .builtins import BUILTINS, RESERVED_FUNCTION_NAMES
from .errors import Diagnostic, GPPLSyntaxError, UnsupportedGPPL
from .expr import DEFAULT_MAX_DEPTH, KEYWORDS, Parser, compile_expr, parse_expression
from .formats import check_literal
from .lexer import strip_comment, tokenize

TYPES = ('numeric', 'integer', 'logical', 'string')
# Words of the statement, declaration, expression and output syntax this loader parses. Unlike function
# names (check_variable_name) they load as variable names; lint W-KEYWORD-NAME reports such a name.
SYNTAX_WORDS = frozenset(TYPES) | frozenset(KEYWORDS) | frozenset({
    'if', 'then', 'else', 'endif', 'while', 'endw', 'endp', 'call', 'local', 'global', 'abort', 'input',
    'print', 'trace', 'nb', 'nl'})
HEADER = re.compile(r'@([A-Za-z0-9_]+)(?:\((.*)\))?')
BLOCK_WORD = re.compile(r'(if|while)(?![A-Za-z0-9_])', re.I)


def check_variable_name(name):
    if name.lower() in RESERVED_FUNCTION_NAMES:
        raise GPPLSyntaxError(f'{name!r} is a reserved GPPL function name, not a variable')


# ------------------------------------------------------------- output items --
def parse_output_items(parser, allow_groups=True, closing=None):
    items = []
    while True:
        token = parser.tok
        if token.kind == 'end':
            if closing:
                parser.error('unclosed [ in output')
            return tuple(items)
        if closing and token.is_op(closing):
            parser.advance()
            return tuple(items)
        if token.is_op(','):
            parser.advance()
            continue
        if token.kind == 'id' and token.value in ('nb', 'nl'):
            parser.advance()
            items.append(N.NewLine(token.value))
            continue
        if token.is_op('['):
            if not allow_groups:
                parser.error('modal group not allowed here')
            parser.advance()
            parser._enter()                            # modal nesting shares the depth cap
            inner = parse_output_items(parser, True, ']')
            parser.depth -= 1
            items.append(N.Modal(inner, N.item_names(inner)))
            continue
        if token.kind == 'str' and not parser.peek().is_op(':'):
            parser.advance()
            items.append(N.Text(token.value, token.doubled))
            continue
        if token.kind == 'str':                        # 'text':fmt - the format applies to numbers only
            parser.advance()
            tree = N.Str(token.value, token.doubled)
            parser.advance()
            items.append(N.Value(tree, parser.parse_format_ref(), None, frozenset(), compile_expr(tree)))
            continue
        if token.kind == 'id' or token.is_op('('):
            hint = None
            if token.kind == 'id' and token.value in BUILTINS and parser.peek().is_op('('):
                tree = parser.parse_primary()          # builtin call, e.g. tostr(x:'5.0(n)')
            elif token.kind == 'id':
                parser.advance()
                if token.value in ('true', 'false'):
                    tree = N.Bool(token.value == 'true')
                else:
                    tree = N.Var(token.value)
                    hint = token.value
            else:
                tree = parser.parse_primary()
            tree = parser.finish(tree)
            fmt = None
            if parser.tok.is_op(':'):
                parser.advance()
                fmt = parser.parse_format_ref()
            items.append(N.Value(tree, fmt, hint, frozenset(N.value_names(tree)), compile_expr(tree)))
            continue
        parser.error(f'unsupported output near: {parser.source[token.pos:]}')


# ---------------------------------------------------------------- statements --
def parse_simple(text, span, escape, max_depth=DEFAULT_MAX_DEPTH):
    """Parse one non-block statement; raises GPPLSyntaxError."""
    def expr_at(position):
        tree = parse_expression(text[position:].strip(), escape, max_depth)
        return tree, compile_expr(tree)

    if text.startswith('{'):
        if not text.endswith('}'):
            raise GPPLSyntaxError('multiline output is unsupported')
        body = text[1:-1]
        parser = Parser(tokenize(body, escape), body, max_depth)
        items = parse_output_items(parser)
        return N.Output(span, text, items, N.item_names(items))
    tokens = tokenize(text, escape)
    tokens += [tokens[-1]] * 5             # trailing 'end' tokens: safe look-ahead
    first, second = tokens[0], tokens[1]
    if first.kind == 'id' and second.is_op('='):
        check_variable_name(first.value)
        tree, fn = expr_at(second.pos + 1)
        return N.Assign(span, text, first.value, tree, fn)
    if first.kind == 'id' and first.value in ('change', 'active') and second.is_op('('):
        if not (tokens[2].kind == 'id' and tokens[3].is_op(')') and tokens[4].is_op('=')):
            raise GPPLSyntaxError(f'malformed {first.value}() assignment')
        tree, fn = expr_at(tokens[4].pos + 1)
        return N.FlagAssign(span, text, first.value, tokens[2].value, tree, fn)
    word = first.value if first.kind == 'id' else None
    if word in ('local', 'global'):
        if second.kind != 'id' or second.value not in TYPES:
            raise GPPLSyntaxError(f'unsupported declaration type: {second.text}')
        names = []
        for token in tokens[2:]:
            if token.kind == 'end':
                break
            if token.is_op(','):
                continue
            if token.kind != 'id':
                raise GPPLSyntaxError(f'unsupported declaration syntax near {token.text!r} (arrays are not supported)')
            check_variable_name(token.value)
            names.append(token.value)
        if not names:
            raise GPPLSyntaxError('declaration without names')
        return N.Declare(span, text, word, second.value, tuple(names))
    if word == 'call':
        if not re.match(r'call[ \t]+@', text, re.I) or tokens[2].kind != 'id':
            raise GPPLSyntaxError(f"unsupported call: {text} (write 'call @name(...)')")
        parser = Parser(tokens, text, max_depth)
        parser.index = 3
        trees = []
        if parser.tok.is_op('('):
            if text[parser.tok.pos - 1] in ' \t':
                raise GPPLSyntaxError(f"unsupported call: {text} (no space before '(')")
            parser.advance()
            if not parser.tok.is_op(')'):
                while True:
                    trees.append(parser.finish(parser.parse_expression()))
                    if parser.tok.is_op(','):
                        parser.advance()
                        continue
                    break
            parser.expect_op(')')
        if not parser.at_end():
            raise GPPLSyntaxError(f'unexpected text after call: {text}')
        return N.CallProc(span, text, tokens[2].value, tuple(trees), tuple(compile_expr(t) for t in trees))
    if word == 'abort':
        if second.kind != 'end':
            raise GPPLSyntaxError('abort takes no arguments')
        return N.Abort(span, text)
    if word == 'input':
        parser = Parser(tokens, text, max_depth)
        parser.index = 1
        tree = parser.finish(parser.parse_expression())
        if parser.tok.is_op(','):                      # input 'prompt', var
            parser.advance()
        target = parser.advance()
        if target.kind != 'id' or not parser.at_end():
            raise GPPLSyntaxError(f'unsupported input statement: {text}')
        return N.Input(span, text, tree, compile_expr(tree), target.value)
    if word == 'print':
        body = text[second.pos:]
        parser = Parser(tokenize(body, escape), body, max_depth)
        return N.Print(span, text, parse_output_items(parser, allow_groups=False))
    if word == 'trace':
        return N.Trace(span, text)
    raise GPPLSyntaxError(f'unsupported statement: {text}')


def _strip_then(text):
    return re.sub(r'\s+then\s*$', '', text, flags=re.I)


class _Block:
    """An open if/while while the loader scans a procedure."""
    __slots__ = ('kind', 'span', 'text', 'cond', 'fn', 'error', 'then', 'orelse', 'in_else',
                 'else_line', 'branch_at', 'jump_at')

    def __init__(self, kind, span, text, cond, fn, error, branch_at):
        self.kind, self.span, self.text = kind, span, text
        self.cond, self.fn, self.error = cond, fn, error
        self.then, self.orelse = [], []
        self.in_else = False
        self.else_line = None
        self.branch_at = branch_at
        self.jump_at = None

    def add(self, stmt):
        (self.orelse if self.in_else else self.then).append(stmt)


class Program:
    """Immutable compiled GPP shared by every Engine built from the same text."""

    def __init__(self, source, escape='double', max_depth=DEFAULT_MAX_DEPTH):
        self.source = source
        self.escape = escape
        self.max_depth = max_depth
        self.digest = hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]
        self.procedures = {}
        self.diagnostics = []
        self.structural = []       # code outside procedures, missing/stray endp (strict-load errors)
        self.globals = {}          # name -> (type, proc, line) from 'global' declarations
        self._load()
        self._check_calls()

    # ---- loading ---------------------------------------------------------
    def _load(self):
        current = None
        for number, raw in enumerate(self.source.splitlines(), 1):
            line = strip_comment(raw, self.escape)
            if not line:
                continue
            if line.startswith('@'):
                match = HEADER.fullmatch(line)
                if not match:
                    raise UnsupportedGPPL(f'invalid procedure at line {number}: {line}')
                name = match[1].lower()
                params = []
                if match[2] is not None and match[2].strip():
                    for argument in match[2].split(','):
                        parts = argument.strip().split()
                        if len(parts) != 2:
                            raise UnsupportedGPPL(f'invalid parameter {argument.strip()!r} at line {number}: '
                                                  f'parameter must be "<type> <name>"')
                        kind, variable = parts
                        if kind.lower() not in TYPES:
                            raise UnsupportedGPPL(f'unsupported argument type: {kind}')
                        check_variable_name(variable)
                        params.append((kind.lower(), variable.lower()))
                if name in self.procedures:
                    raise UnsupportedGPPL(f'duplicate procedure {name}')
                if current is not None:
                    self._structural('W-MISSING-ENDP', current.name, current.line,
                                     f'@{current.name} is not closed by endp before @{name} (line {number})')
                current = N.Procedure(name, match[1], number, params)
                self.procedures[name] = current
            elif line.lower() == 'endp':
                if current is None:
                    self._structural('W-ENDP', None, number, 'endp outside a procedure')
                else:
                    current.end_line = number
                current = None
            elif current is not None:
                current.raw.append((number, line))
            else:
                self._structural('W-OUTSIDE', None, number, f'statement outside any procedure ignored: {line}')
        if current is not None:
            self._structural('W-MISSING-ENDP', current.name, current.line,
                             f'@{current.name} is not closed by endp before end of file')
        for proc in self.procedures.values():
            self._build(proc)

    def diag(self, severity, code, proc, line, message):
        self.diagnostics.append(Diagnostic(severity, code, proc, line, message))

    def _structural(self, code, proc, line, message):
        diagnostic = Diagnostic('warning', code, proc, line, message)
        self.diagnostics.append(diagnostic)
        self.structural.append(diagnostic)

    def _condition(self, kind, text, span, proc, raw):
        """Parse an if/while condition; a bad one keeps the block structure and
        raises only when evaluated."""
        try:
            if raw[len(kind):len(kind) + 1] == '(':
                raise GPPLSyntaxError(f"'{kind}(' needs a space before the condition (write '{kind} (...)')")
            if not text:
                raise GPPLSyntaxError(f'{kind} without condition')
            cond = parse_expression(text, self.escape, self.max_depth)
            return cond, compile_expr(cond), None
        except UnsupportedGPPL as exc:
            error = GPPLSyntaxError(getattr(exc, 'message', str(exc)), proc.name, span.line)
            self.diag('error', 'E-SYNTAX', proc.name, span.line, error.message)

            def raiser(rt, error=error):
                raise error
            return None, raiser, error

    def _build(self, proc):
        root = []
        stack = []                 # open _Block objects
        code = []                  # mutable [op, line, stmt, fn, target]
        declared = dict.fromkeys(proc.param_names)     # local name -> declaration line (None: parameter)

        def fail(number, message):
            self.diag('error', 'E-STRUCT', proc.name, number, message)
            if proc.error is None:
                proc.error = GPPLSyntaxError(message, proc.name, number)

        def add(stmt):
            (stack[-1].add if stack else root.append)(stmt)

        for number, text in proc.raw:
            low = text.lower()
            span = N.Span(number, 0)
            block = BLOCK_WORD.match(low)
            if block and not re.match(r'(if|while)\s*=', low):
                kind = block[1]
                condition = text[len(kind):].strip()
                if kind == 'if':
                    condition = _strip_then(condition).strip()
                cond, fn, error = self._condition(kind, condition, span, proc, low)
                code.append([N.BRANCH, number, None, fn, None])
                stack.append(_Block(kind, span, text, cond, fn, error, len(code) - 1))
            elif low == 'else':
                top = stack[-1] if stack else None
                if top is None or top.kind != 'if':
                    fail(number, 'else without if' if top is None else 'else inside while (unclosed while)')
                    continue
                if top.in_else:
                    fail(number, 'duplicate else')
                    continue
                code.append([N.JUMP, number, None, None, None])
                top.jump_at = len(code) - 1
                code[top.branch_at][4] = len(code)
                top.in_else, top.else_line = True, number
            elif low in ('endif', 'endw'):
                want = 'if' if low == 'endif' else 'while'
                top = stack[-1] if stack else None
                if top is None or top.kind != want:
                    if top is None:
                        fail(number, f'{low} without {want}')
                    else:
                        fail(number, f'{low} inside {top.kind} (unclosed {top.kind} at line {top.span.line})')
                    continue
                stack.pop()
                if want == 'if':
                    code[top.jump_at if top.in_else else top.branch_at][4] = len(code)
                    node = N.If(top.span, top.text, top.cond, top.fn, tuple(top.then), tuple(top.orelse),
                                top.in_else, top.else_line, number, top.error)
                else:
                    code.append([N.JUMP, number, None, None, top.branch_at])
                    code[top.branch_at][4] = len(code)
                    node = N.While(top.span, top.text, top.cond, top.fn, tuple(top.then), number, top.error)
                code[top.branch_at][2] = node
                add(node)
            else:
                try:
                    node = parse_simple(text, span, self.escape, self.max_depth)
                except (UnsupportedGPPL, RecursionError) as exc:
                    message = getattr(exc, 'message', None) or str(exc)
                    if isinstance(exc, RecursionError):
                        message = f'statement too deeply nested: {text[:60]}'
                    error = GPPLSyntaxError(message, proc.name, number)
                    node = N.Bad(span, text, error)
                    self.diag('error', 'E-SYNTAX', proc.name, number, message)
                self._declared(node, proc, declared)
                code.append([N.EXEC, number, node, None, None])
                add(node)
        while stack:
            top = stack.pop()
            fail(top.span.line, f'unclosed {top.kind}')
        proc.body = tuple(root)
        proc.code = tuple(N.Instr(*instr) for instr in code)

    def _declared(self, node, proc, declared):
        """Declaration bookkeeping; ``declared`` maps the procedure's parameters and the locals declared
        so far to their declaration line (None for a parameter)."""
        if type(node) is not N.Declare:
            return
        seen = set()
        for name in node.names:
            if name in seen:
                self.diag('warning', 'W-DUPLICATE-NAME', proc.name, node.line,
                          f'{name} listed twice in one declaration (names are case-insensitive)')
            elif node.scope == 'local' and name in declared:
                earlier = 'a parameter' if declared[name] is None else f'declared at line {declared[name]}'
                self.diag('warning', 'W-DUPLICATE-NAME', proc.name, node.line,
                          f'local {name} is already {earlier} of @{proc.name} (names are case-insensitive)')
            seen.add(name)
            if node.scope == 'local':
                declared.setdefault(name, node.line)
            if node.scope == 'global':
                previous = self.globals.get(name)
                if previous and previous[0] != node.vtype:
                    self.diag('warning', 'W-REDECLARE', proc.name, node.line,
                              f'global {name} declared {node.vtype}, earlier {previous[0]} at line {previous[2]}')
                self.globals.setdefault(name, (node.vtype, proc.name, node.line))

    def _check_calls(self):
        for name, proc in self.procedures.items():
            for stmt in N.walk_statements(proc.body):
                if type(stmt) is not N.CallProc:
                    continue
                target = self.procedures.get(stmt.proc)
                if target is None:
                    self.diag('error', 'E-CALL', name, stmt.line, f'call to undefined procedure @{stmt.proc}')
                elif len(stmt.args) != len(target.params):
                    self.diag('error', 'E-ARITY', name, stmt.line,
                              f'@{stmt.proc} takes {len(target.params)} argument(s), called with {len(stmt.args)}')

    # ---- policy-dependent diagnostics ---------------------------------------
    def policy_diagnostics(self, policies):
        """Constructs that raise when executed under ``policies`` (cached)."""
        key = (policies.format_grammar, policies.print_stmt, policies.trace_stmt)
        cache = self.__dict__.setdefault('_policy_diags', {})
        if key in cache:
            return cache[key]
        result = []
        grammar_index = 0 if policies.format_grammar == 'legacy' else 1
        for name, proc in self.procedures.items():
            for stmt in N.walk_statements(proc.body):
                kind = type(stmt)
                if kind is N.Print and policies.print_stmt == 'error':
                    result.append(Diagnostic('error', 'E-POLICY', name, stmt.line,
                                             'Print is unsupported under policy print_stmt=error '
                                             '(session/best_guess record it as console output)'))
                elif kind is N.Trace and policies.trace_stmt == 'error':
                    result.append(Diagnostic('error', 'E-POLICY', name, stmt.line,
                                             'trace is unsupported under policy trace_stmt=error '
                                             '(session/best_guess ignore it)'))
                for literal, assigned in _format_literals(stmt):
                    problems = check_literal(literal)
                    problem = problems[grammar_index]
                    if problem is None:
                        continue
                    if problems[0] and problems[1]:
                        result.append(Diagnostic('error' if not assigned else 'warning', 'E-FORMAT', name,
                                                 stmt.line, problem))
                    elif assigned:
                        result.append(Diagnostic('warning', 'W-FORMAT-POLICY', name, stmt.line,
                                                 f'{problem}; assigned to a format variable, raises only '
                                                 f'when a number is rendered with it'))
                    else:
                        result.append(Diagnostic('error', 'E-POLICY', name, stmt.line, problem))
        cache[key] = result
        return result

    # ---- queries -----------------------------------------------------------
    def walk(self, body=None):
        """Every statement (depth-first) of a body or of all procedures."""
        if body is not None:
            yield from N.walk_statements(body)
            return
        for proc in self.procedures.values():
            yield from N.walk_statements(proc.body)

    def statement_lines(self, proc):
        """Executable statement lines (legacy coverage counting: no else/endif/endw)."""
        return sorted(stmt.line for stmt in N.walk_statements(self.procedures[proc].body))

    def errors(self, policies=None, strict=False):
        found = [d for d in self.diagnostics if d.severity == 'error']
        if policies is not None:
            found += [d for d in self.policy_diagnostics(policies) if d.severity == 'error']
        if strict:
            found += self.structural
        return found

    def validate(self, strict=False, policies=None):
        problems = self.errors(policies, strict=strict)
        if strict and problems:
            raise UnsupportedGPPL('GPP validation failed:\n' + '\n'.join(map(str, problems)))
        return self.diagnostics + (self.policy_diagnostics(policies) if policies is not None else [])


def _format_literals(stmt):
    """(literal, assigned_to_variable) format literals in a statement."""
    kind = type(stmt)
    if kind is N.Assign and stmt.target.endswith('_f') and type(stmt.expr) is N.Str:
        yield stmt.expr.value, True
    for expr in N.statement_expressions(stmt):
        if type(expr) is N.FmtLit:
            yield expr.text, False
            continue
        for node in N.walk_expr(expr):
            if type(node) is N.FmtLit:
                yield node.text, False


_PROGRAMS = {}


def load_program(source, escape='double', max_depth=DEFAULT_MAX_DEPTH):
    """Parse once per (source, lexing policy, depth cap); Programs are immutable."""
    key = (escape, max_depth, source)
    program = _PROGRAMS.get(key)
    if program is None:
        program = Program(source, escape, max_depth)
        if len(_PROGRAMS) > 256:
            _PROGRAMS.clear()
        _PROGRAMS[key] = program
    return program
