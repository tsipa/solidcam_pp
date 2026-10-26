"""Strict, deliberately partial GPPL interpreter. No eval or SolidCAM required."""
import ast
import operator
import math
import re
from pathlib import Path


class UnsupportedGPPL(ValueError):
    pass


def uncomment(line):
    quoted = None
    index = 0
    while index < len(line):
        if line[index] in "'\"":
            if quoted == line[index] and index + 1 < len(line) and line[index + 1] == quoted:
                index += 2
                continue
            if quoted is None:
                quoted = line[index]
            elif quoted == line[index]:
                quoted = None
        elif line[index] == ';' and not quoted:
            return line[:index].strip()
        index += 1
    return line.strip()


class Engine:
    def __init__(self, source):
        self.procedures = {}
        self.state = {}
        self.changed = {}
        self.output = []
        self.stack = []
        self.arguments = {}
        current = None
        for number, raw in enumerate(source.splitlines(), 1):
            line = uncomment(raw)
            if not line:
                continue
            if line.startswith('@'):
                signature = re.fullmatch(r'@(\w+)(?:\((.*)\))?', line)
                if not signature:
                    raise UnsupportedGPPL(f'invalid procedure at line {number}: {line}')
                current = signature[1].lower()
                self.arguments[current] = []
                if signature[2]:
                    for argument in signature[2].split(','):
                        kind, variable = argument.strip().split()
                        if kind.lower() not in ('numeric', 'integer', 'logical', 'string'):
                            raise UnsupportedGPPL(f'unsupported argument type: {kind}')
                        self.arguments[current].append(variable.lower())
                if current in self.procedures:
                    raise UnsupportedGPPL(f'duplicate procedure {current}')
                self.procedures[current] = []
            elif line.lower() == 'endp':
                current = None
            elif current:
                self.procedures[current].append((number, line))

    @classmethod
    def from_path(cls, path):
        return cls(Path(path).read_text(encoding='utf-8-sig'))

    def set(self, **values):
        self.state.update({k.lower(): v for k, v in values.items()})

    def expression(self, value):
        # Transform identifiers/operators only outside quoted literals.
        chunks = re.split(r'''('(?:[^']|'')*'|"(?:[^"]|"")*")''', value)
        for i in range(1, len(chunks), 2):
            quote = chunks[i][0]
            chunks[i] = repr(chunks[i][1:-1].replace(quote + quote, quote))
        for i in range(0, len(chunks), 2):
            s = chunks[i].lower()
            for word, symbol in {'eq': '==', 'ne': '!=', 'gt': '>', 'lt': '<',
                                 'ge': '>=', 'le': '<='}.items():
                s = re.sub(r'\b' + word + r'\b', symbol, s)
            chunks[i] = re.sub(r'!(?!=)', ' not ', s)
        try:
            tree = ast.parse(''.join(chunks).strip(), mode='eval')
            return self._node(tree.body)
        except (SyntaxError, KeyError, TypeError) as exc:
            raise UnsupportedGPPL(f'expression {value!r}: {exc}') from exc

    def _node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in ('true', 'false'):
                return node.id == 'true'
            return self.state[node.id]
        if isinstance(node, ast.UnaryOp):
            ops = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}
            if type(node.op) in ops:
                return ops[type(node.op)](self._node(node.operand))
        if isinstance(node, ast.BinOp):
            ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                   ast.Div: operator.truediv, ast.Mod: operator.mod}
            if type(node.op) in ops:
                return ops[type(node.op)](self._node(node.left), self._node(node.right))
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(self._node(v) for v in node.values)
            return any(self._node(v) for v in node.values)
        if isinstance(node, ast.Compare):
            ops = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
                   ast.Gt: operator.gt, ast.LtE: operator.le, ast.GtE: operator.ge}
            left = self._node(node.left)
            for op, right_node in zip(node.ops, node.comparators):
                right = self._node(right_node)
                if type(op) not in ops:
                    break
                if not ops[type(op)](left, right):
                    return False
                left = right
            else:
                return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.keywords:
                raise UnsupportedGPPL('keyword arguments are unsupported')
            if node.func.id == 'change' and len(node.args) == 1 and isinstance(node.args[0], ast.Name):
                name = node.args[0].id
                if name not in self.changed:
                    raise UnsupportedGPPL(f'change({name}) was not supplied')
                return self.changed[name]
            if node.func.id == 'abs' and len(node.args) == 1:
                return abs(self._node(node.args[0]))
            if node.func.id in ('sin', 'cos') and len(node.args) == 1:
                return getattr(math, node.func.id)(math.radians(self._node(node.args[0])))
            functions = {'strlen': lambda s: len(s),
                         'instr': lambda s, sub: s.find(sub) + 1,
                         'left': lambda s, count: s[:int(count)],
                         'substr': lambda s, start, count: s[int(start) - 1:int(start) - 1 + int(count)],
                         'tonum': lambda s: float(s)}
            if node.func.id in functions and not node.keywords:
                return functions[node.func.id](*(self._node(a) for a in node.args))
        raise UnsupportedGPPL(f'unsupported expression node: {ast.dump(node)}')

    def call(self, procedure, arguments=()):
        name = procedure.lstrip('@').lower()
        if name not in self.procedures:
            raise UnsupportedGPPL(f'missing procedure @{name}')
        if len(self.stack) >= 64:
            raise UnsupportedGPPL('call depth exceeded')
        self.stack.append(name)
        locals_saved = {}
        locals_changed = {}
        if len(arguments) != len(self.arguments[name]):
            self.stack.pop()
            raise UnsupportedGPPL(f'@{name}: expected {len(self.arguments[name])} arguments, got {len(arguments)}')
        for variable, value in zip(self.arguments[name], arguments):
            locals_saved[variable] = (variable in self.state, self.state.get(variable))
            locals_changed[variable] = (variable in self.changed, self.changed.get(variable))
            self.state[variable] = value
            self.changed[variable] = False
        branches = []
        active = True
        try:
            lines = self.procedures[name]
            index = 0
            loops = []
            steps = 0
            while index < len(lines):
                steps += 1
                if steps > 100000:
                    raise UnsupportedGPPL(f'@{name}: execution step limit exceeded')
                number, line = lines[index]
                index += 1
                low = line.lower()
                try:
                    if low.startswith('while '):
                        if active and self.expression(line[6:]):
                            loops.append(index - 1)
                        else:
                            nesting = 1
                            while index < len(lines) and nesting:
                                statement = lines[index][1].lower()
                                if statement.startswith('while '):
                                    nesting += 1
                                elif statement == 'endw':
                                    nesting -= 1
                                index += 1
                            if nesting:
                                raise UnsupportedGPPL('unclosed while')
                    elif low == 'endw':
                        index = loops.pop()
                    elif low.startswith('if '):
                        condition = bool(self.expression(re.sub(r'\s+then$', '', line[3:], flags=re.I))) if active else False
                        branches.append((active, condition, False))
                        active = active and condition
                    elif low == 'else':
                        parent, condition, seen = branches[-1]
                        if seen:
                            raise UnsupportedGPPL('duplicate else')
                        branches[-1] = (parent, condition, True)
                        active = parent and not condition
                    elif low == 'endif':
                        active = branches.pop()[0]
                    elif active:
                        declaration = re.fullmatch(r'(local|global) (numeric|integer|logical|string) (.+)', low)
                        if declaration:
                            scope, kind, names = declaration.groups()
                            for variable in names.replace(',', ' ').split():
                                if scope == 'local':
                                    locals_saved[variable] = (variable in self.state, self.state.get(variable))
                                    locals_changed[variable] = (variable in self.changed, self.changed.get(variable))
                                    self.state[variable] = '' if kind == 'string' else 0
                                    self.changed[variable] = False
                                elif variable not in self.state:
                                    self.state[variable] = '' if kind == 'string' else 0
                        elif low.startswith('call @'):
                            invocation = re.fullmatch(r'call @(\w+)(?:\((.*)\))?', line, re.I)
                            if not invocation:
                                raise UnsupportedGPPL(f'unsupported call: {line}')
                            # Current parameterized procedures take scalar expressions, no nested commas.
                            arguments = [] if invocation[2] is None else [self.expression(a) for a in invocation[2].split(',')]
                            self.call(invocation[1], arguments)
                        elif low == 'abort' or low.startswith('input '):
                            raise UnsupportedGPPL(f'postprocessor stopped: {line}')
                        elif line.startswith('{'):
                            self._output(line)
                        else:
                            assignment = re.fullmatch(r'(change\((\w+)\)|(\w+))\s*=\s*(.+)', line, re.I)
                            if not assignment:
                                raise UnsupportedGPPL(f'unsupported statement: {line}')
                            _, changed_name, variable, rhs = assignment.groups()
                            target = self.changed if changed_name else self.state
                            key = (changed_name or variable).lower()
                            value = self.expression(rhs)
                            if not changed_name and (key not in target or target[key] != value):
                                self.changed[key] = True
                            target[key] = value
                except (ValueError, IndexError, ZeroDivisionError) as exc:
                    raise UnsupportedGPPL(f'@{name}:{number}: {exc}') from exc
            if branches:
                raise UnsupportedGPPL(f'@{name}: unclosed if')
            if loops:
                raise UnsupportedGPPL(f'@{name}: unclosed while')
        finally:
            for variable, (existed, old) in locals_saved.items():
                if existed:
                    self.state[variable] = old
                else:
                    self.state.pop(variable, None)
            for variable, (existed, old) in locals_changed.items():
                if existed:
                    self.changed[variable] = old
                else:
                    self.changed.pop(variable, None)
            self.stack.pop()

    def _output(self, line):
        if not line.endswith('}'):
            raise UnsupportedGPPL('multiline output is unsupported')
        fragment, variables = self._render(line[1:-1])
        self.output.append(fragment)
        if self.state.get('clear_change_after_gen', 0):
            for variable in variables:
                self.changed[variable] = False

    def _render(self, body):
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
                    result += '\n'
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
                descriptor = descriptor or self.state.get(token.lower() + '_f')
                precision = 3
                if descriptor:
                    fmt = re.fullmatch(r'\d+\.(\d+)(?:\([pP]\))?', descriptor)
                    if not fmt:
                        raise UnsupportedGPPL(f'unsupported numeric format: {descriptor}')
                    precision = int(fmt[1])
                value = format(value, f'.{precision}f')
                if precision:
                    value = value.rstrip('0').rstrip('.')
                if value == '-0':
                    value = '0'
            result += str(value)
        return result, variables

    @staticmethod
    def _closing(body, start, opening, closing):
        depth = 0
        quoted = None
        for index in range(start, len(body)):
            character = body[index]
            if character in "'\"":
                if quoted is None:
                    quoted = character
                elif quoted == character:
                    quoted = None
            elif quoted is None:
                if character == opening:
                    depth += 1
                elif character == closing:
                    depth -= 1
                    if depth == 0:
                        return index
        raise UnsupportedGPPL(f'unclosed {opening} in output')
