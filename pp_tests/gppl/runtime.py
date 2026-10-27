"""GPPL interpreter over the compiled Program IR.

``Engine`` keeps the legacy public surface (state/changed/output/call/
expression/set/procedures/arguments/stack) as plain dicts and lists, so legacy
tests that copy state between engines keep working. Locals and parameters live
in call frames (no save/restore into the global dict), flags live with the
variable's owning scope, every runtime error carries the GPPL call chain, and
each procedure runs from its flat instruction list (nodes.Instr) with a class
dispatch table, so only GPPL calls use the Python stack.
"""
from pathlib import Path

from . import nodes as N
from . import sysvars
from .coverage import engine_coverage
from .errors import GPPLRuntimeError, MissingInput, PostAbort, PostprocessorStopped, UnsupportedGPPL
from .expr import compile_expr, parse_expression
from .formats import parse_format, render_number
from .output import OutputStream, _truthy
from .policies import Policies
from .program import load_program

_PY_ERRORS = (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError, OverflowError,
              AttributeError)
_TYPE_DEFAULTS = {'string': '', 'numeric': 0, 'integer': 0}


class Frame:
    __slots__ = ('proc', 'values', 'changed', 'types', 'steps', 'cov')

    def __init__(self, proc, cov):
        self.proc = proc
        self.values = {}
        self.changed = {}
        self.types = {}
        self.steps = 0
        self.cov = cov


class Engine:
    def __init__(self, source, policies=None, vmid=None, coverage=None, tracer=None):
        self.policies = self.pol = policies if policies is not None else Policies.from_env()
        pol = self.policies
        self.program = load_program(source, pol.lexing_key(), pol.max_expr_depth)
        if pol.load_errors == 'raise':
            self.program.validate(strict=True, policies=pol)
        self.state = {}
        self.changed = {}
        self.active = {}
        self.output = []
        self.stream = OutputStream(self)
        self.frames = []
        self.stack = []
        self.console = []
        self.scripted_inputs = []
        self.tracer = tracer
        self.vmid = vmid
        self.skipline_epoch = 0
        self.coverage = coverage if coverage is not None else engine_coverage(self.program)
        self._dynamic = pol.local_scoping == 'dynamic'
        self._constants = None
        if pol.constants == 'registry':
            self._constants = dict(sysvars.CONSTANTS)
            if vmid is not None:
                self._constants.update(vmid.constants())
        self._compiled = {}
        self._vmid_params = vmid.all_params() if vmid is not None else {}
        self._legacy_procedures = None

    @classmethod
    def from_path(cls, path, *args, **kwargs):
        return cls(Path(path).read_text(encoding='utf-8-sig'), *args, **kwargs)

    # ---- legacy views --------------------------------------------------
    @property
    def procedures(self):
        """{name: [(line, text), ...]} like the legacy engine (a private copy)."""
        if self._legacy_procedures is None:
            self._legacy_procedures = {name: list(proc.raw) for name, proc in self.program.procedures.items()}
        return self._legacy_procedures

    @property
    def arguments(self):
        return {name: proc.param_names for name, proc in self.program.procedures.items()}

    @property
    def diagnostics(self):
        return list(self.program.diagnostics) + list(self.program.policy_diagnostics(self.policies))

    def set(self, **values):
        values = {key.lower(): value for key, value in values.items()}
        if 'skipline' in values:
            self.skipline_epoch += 1
        self.state.update(values)

    # ---- variable model ------------------------------------------------
    def lookup(self, name):
        frames = self.frames
        if frames:
            if self._dynamic:
                for frame in reversed(frames):
                    if name in frame.values:
                        return frame.values[name]
            elif name in frames[-1].values:
                return frames[-1].values[name]
        state = self.state
        if name in state:
            return state[name]
        if self._constants is not None and name in self._constants:
            return self._constants[name]
        raise MissingInput(f'missing variable {name!r} (not supplied, declared or a known constant)')

    def _owner(self, name):
        frames = self.frames
        if frames:
            if self._dynamic:
                for frame in reversed(frames):
                    if name in frame.values:
                        return frame
            elif name in frames[-1].values:
                return frames[-1]
        return None

    def peek(self, name, default=None):
        """Read without strictness (runtime control variables)."""
        frame = self._owner(name)
        if frame is not None:
            return frame.values[name]
        return self.state.get(name, sysvars.CONTROL_DEFAULTS.get(name, default))

    def poke(self, name, value):
        """Write a runtime-owned control variable without touching change flags."""
        frame = self._owner(name)
        (frame.values if frame is not None else self.state)[name] = value

    def type_of(self, name):
        frame = self._owner(name)
        if frame is not None and name in frame.types:
            return frame.types[name]
        declared = self.program.globals.get(name)
        if declared:
            return declared[0]
        param = self._vmid_params.get(name)
        if param is not None:
            return param.vtype
        return sysvars.system_type(name)

    def assign(self, name, value):
        frame = self._owner(name)
        if frame is None:
            values, flags = self.state, self.changed
            if self.policies.undeclared_assign == 'error' and name not in values \
                    and name not in self.program.globals and not sysvars.is_known_system(name):
                raise GPPLRuntimeError(f'assignment to undeclared variable {name!r} (policy undeclared_assign=error)')
        else:
            values, flags = frame.values, frame.changed
        value = self._coerce(name, value)
        if name == 'skipline':
            self.skipline_epoch += 1
        if name not in values or values[name] != value:
            flags[name] = True
        else:
            rule = self.policies.change_on_equal_assign
            if rule == 'clear' or (rule == 'clear_user' and self._is_user_variable(name, frame)):
                flags[name] = False
            elif rule == 'set':
                flags[name] = True
        values[name] = value

    def _is_user_variable(self, name, frame):
        """PP-owned (declared, local or unknown to SolidCAM) vs SolidCAM system variable."""
        return frame is not None or name in self.program.globals or not sysvars.is_known_system(name)

    def _coerce(self, name, value):
        pol = self.policies
        if pol.integer_assign == 'keep' and pol.typed_assign == 'off':
            return value
        vtype = self.type_of(name)
        if vtype == 'integer' and isinstance(value, float):
            if pol.integer_assign == 'truncate':
                value = int(value)
            elif pol.integer_assign == 'round_half_away':
                value = int(value + (0.5 if value >= 0 else -0.5))
        if pol.typed_assign == 'coerce' and vtype:
            if vtype in ('integer', 'numeric') and isinstance(value, str):
                raise GPPLRuntimeError(f'string {value!r} assigned to {vtype} {name}')
            if vtype == 'string' and not isinstance(value, str):
                raise GPPLRuntimeError(f'non-string {value!r} assigned to string {name}')
            if vtype == 'logical' and not isinstance(value, str):
                value = bool(value)
        return value

    def _flags_for(self, kind, name):
        if kind == 'active':
            return self.active
        frame = self._owner(name)
        return frame.changed if frame is not None else self.changed

    def get_flag(self, kind, name):
        flags = self._flags_for(kind, name)
        if name in flags:
            return flags[name]
        if self.policies.missing_change_flag == 'false':
            return False
        raise MissingInput(f'{kind}({name}) was not supplied')

    def set_flag(self, kind, name, value):
        self._flags_for(kind, name)[name] = value

    def has_flag(self, name):
        return name in self._flags_for('change', name)

    # ---- formats ---------------------------------------------------------
    def resolve_format(self, ref):
        if ref is None:
            return None
        text = ref.text if type(ref) is N.FmtLit else self.lookup(ref.name)
        return parse_format(text, self.policies.format_grammar)

    def render_value(self, value, spec, hint, fmt_text=None):
        if isinstance(value, bool):
            if self.policies.logical_output == 'numeric':
                return '1' if value else '0'
            return str(value)
        if isinstance(value, (int, float)):
            grammar = self.policies.format_grammar
            if spec is None and fmt_text:
                spec = parse_format(fmt_text, grammar)
            if spec is None and hint:
                text = self.state.get(hint + '_f')
                if text:
                    spec = parse_format(text, grammar)
            if spec is None and self.policies.typed_default_formats == 'on':
                vtype = (self.type_of(hint) if hint else None) or 'numeric'
                text = self.state.get('integer_def_f' if vtype == 'integer' else 'numeric_def_f')
                if isinstance(text, str) and text:
                    spec = parse_format(text, grammar)
            return render_number(value, spec, self.policies)
        return str(value)

    # ---- expressions -----------------------------------------------------
    def expression(self, text):
        fn = self._compiled.get(text)
        try:
            if fn is None:
                pol = self.policies
                fn = compile_expr(parse_expression(text, pol.lexing_key(), pol.max_expr_depth))
                self._compiled[text] = fn
            return fn(self)
        except UnsupportedGPPL:
            raise
        except RecursionError as exc:
            raise GPPLRuntimeError(f'expression {text!r}: too deeply nested') from exc
        except _PY_ERRORS as exc:
            raise GPPLRuntimeError(f'expression {text!r}: {type(exc).__name__}: {exc}') from exc

    # ---- execution -------------------------------------------------------
    def call(self, procedure, arguments=()):
        """Run a procedure (legacy API). Nested GPPL calls use ``_call`` directly,
        so subclasses overriding ``call`` see only top-level calls."""
        return self._call(procedure, arguments, None)

    def _call(self, procedure, arguments, site):
        name = procedure.lstrip('@').lower()
        proc = self.program.procedures.get(name)
        if proc is None:
            raise GPPLRuntimeError(f'missing procedure @{name}')
        if len(self.frames) >= self.policies.max_depth:
            raise GPPLRuntimeError('call depth exceeded')
        arguments = list(arguments)
        if len(arguments) != len(proc.params):
            raise GPPLRuntimeError(f'@{name}: expected {len(proc.params)} arguments, got {len(arguments)}')
        if proc.error is not None:
            error = GPPLRuntimeError(proc.error.message, [(name, proc.error.line)])
            error._depths = {len(self.frames) + 1}
            raise error
        frame = Frame(name, self.coverage.lines.setdefault(name, set()))
        for (vtype, param), value in zip(proc.params, arguments):
            frame.values[param] = value
            frame.changed[param] = False
            frame.types[param] = vtype
        self.frames.append(frame)
        self.stack.append(name)
        tracer = self.tracer
        if tracer is not None:
            tracer.on_call(len(self.frames), proc, arguments, site)
        failure = None
        try:
            self._run(proc, frame)
        except BaseException as exc:
            failure = exc
            raise
        finally:
            self.frames.pop()
            self.stack.pop()
            if tracer is not None:
                tracer.on_return(len(self.frames) + 1, proc, failure)

    def _run(self, proc, frame):
        code = proc.code
        end = len(code)
        limit = self.policies.max_steps
        cov = frame.cov
        branches = self.coverage.branches
        handlers = _HANDLERS
        pc = 0
        while pc < end:
            ins = code[pc]
            frame.steps += 1
            try:
                if frame.steps > limit:
                    raise GPPLRuntimeError(f'execution step limit exceeded ({limit} steps, policy max_steps)')
                op = ins.op
                if op is N.EXEC:
                    cov.add(ins.line)
                    handlers[type(ins.stmt)](self, ins.stmt, frame)
                    pc += 1
                elif op is N.BRANCH:
                    cov.add(ins.line)
                    condition = bool(ins.fn(self))
                    key = (frame.proc, ins.line)
                    seen = branches.get(key)
                    if seen is None:
                        branches[key] = {condition}
                    else:
                        seen.add(condition)
                    pc = pc + 1 if condition else ins.target
                else:
                    pc = ins.target
            except GPPLRuntimeError as exc:
                self._annotate(exc, frame, ins.line)
                raise
            except UnsupportedGPPL as exc:
                error = GPPLRuntimeError(getattr(exc, 'message', None) or str(exc))
                self._annotate(error, frame, ins.line)
                raise error from exc
            except RecursionError as exc:
                error = GPPLRuntimeError(f'Python recursion limit reached in {ins.stmt.text if ins.stmt else ""!r}')
                self._annotate(error, frame, ins.line)
                raise error from exc
            except _PY_ERRORS as exc:
                text = ins.stmt.text if ins.stmt is not None else ''
                error = GPPLRuntimeError(f'{type(exc).__name__}: {exc} in {text!r}')
                self._annotate(error, frame, ins.line)
                raise error from exc

    def _annotate(self, exc, frame, line):
        depth = len(self.frames)
        recorded = exc.__dict__.setdefault('_depths', set())
        if depth not in recorded:
            recorded.add(depth)
            exc.with_stack(exc.gppl_stack + [(frame.proc, line)])

    # ---- statement handlers (dispatch by node class) -------------------------
    def _exec_assign(self, stmt, frame):
        value = stmt.fn(self)
        if self.tracer is not None and getattr(self.tracer, 'wants_assignments', False):
            owner = self._owner(stmt.target)
            store = owner.values if owner is not None else self.state
            old = store.get(stmt.target, '<unset>')
            self.assign(stmt.target, value)
            flags = owner.changed if owner is not None else self.changed
            self.tracer.on_assign(frame.proc, stmt.line, stmt.target, old, value, flags.get(stmt.target))
            return
        self.assign(stmt.target, value)

    def _exec_flag_assign(self, stmt, frame):
        self.set_flag(stmt.flag, stmt.target, stmt.fn(self))

    def _exec_call(self, stmt, frame):
        self._call(stmt.proc, [fn(self) for fn in stmt.fns], (frame.proc, stmt.line))

    def _exec_output(self, stmt, frame):
        pieces = []
        self._render(stmt.items, pieces)
        text = ''.join('\n' if kind != 'text' else value for kind, value in pieces)
        self.output.append(text)
        origin = (frame.proc, stmt.line)
        self.stream.write(pieces, origin)
        if self.tracer is not None:
            self.tracer.on_output(pieces, origin, text)
        if _truthy(self.state.get('clear_change_after_gen', 0)):
            for name in stmt.names:
                self.set_flag('change', name, False)

    def _exec_declare(self, stmt, frame):
        vtype = stmt.vtype
        if vtype == 'logical':
            default = 0 if self.policies.logical_default == 'zero' else False
        else:
            default = _TYPE_DEFAULTS[vtype]
        if stmt.scope == 'local':
            for name in stmt.names:
                frame.values[name] = default
                frame.changed[name] = False
                frame.types[name] = vtype
            return
        flag = self.policies.declared_flag == 'false'
        for name in stmt.names:
            if self._owner(name) is not None:
                continue           # shadowed by a visible local/parameter: legacy no-op, no leak
            if name not in self.state:
                self.state[name] = default
                if flag:
                    self.changed.setdefault(name, False)

    def _exec_input(self, stmt, frame):
        prompt = stmt.fn(self)
        self.console.append(('input', str(prompt)))
        if self.tracer is not None:
            self.tracer.on_console('input', str(prompt))
        if self.policies.input_stmt == 'abort':
            raise PostprocessorStopped(f'postprocessor stopped: {stmt.text}')
        if self.scripted_inputs:
            value = self.scripted_inputs.pop(0)
        else:
            value = '' if self.type_of(stmt.target) == 'string' else 0
        self.assign(stmt.target, value)

    def _exec_abort(self, stmt, frame):
        tail = self.stream.lines_since(max(len(self.stream.lines) - 1, 0))
        last = tail[-1].full if tail else ''
        prompts = '; '.join(text for what, text in self.console if what == 'input')
        raise PostAbort(f'postprocessor stopped: abort (line {stmt.line})'
                        + (f'; last output: {last!r}' if last else '')
                        + (f'; prompts: {prompts}' if prompts else ''))

    def _exec_print(self, stmt, frame):
        if self.policies.print_stmt == 'error':
            raise GPPLRuntimeError(f'unsupported statement: {stmt.text} (policy print_stmt=error; '
                                   f'Policies.session() records Print as console output)')
        pieces = []
        self._render(stmt.items, pieces)
        message = ''.join(text for _, text in pieces)
        self.console.append(('print', message))
        if self.tracer is not None:
            self.tracer.on_console('print', message)

    def _exec_trace(self, stmt, frame):
        if self.policies.trace_stmt == 'error':
            raise GPPLRuntimeError(f'unsupported statement: {stmt.text} (policy trace_stmt=error; '
                                   f'Policies.session() ignores trace)')

    def _exec_bad(self, stmt, frame):
        raise GPPLRuntimeError(stmt.error.message)

    # ---- output ------------------------------------------------------------
    def _render(self, items, pieces):
        for item in items:
            kind = type(item)
            if kind is N.Text:
                pieces.append(('text', item.value))
            elif kind is N.Value:
                fmt = item.fmt
                fmt_text = None
                if fmt is not None:
                    fmt_text = fmt.text if type(fmt) is N.FmtLit else self.lookup(fmt.name)
                pieces.append(('text', self.render_value(item.fn(self), None, item.hint, fmt_text)))
            elif kind is N.Modal:
                inner = []
                self._render(item.items, inner)
                names = item.names
                missing = [name for name in names if not self.has_flag(name)]
                if missing and self.policies.modal_missing_flag == 'error':
                    raise GPPLRuntimeError(f'modal output requires explicit change flags: {sorted(missing)}')
                if any(self.has_flag(name) and self.get_flag('change', name) for name in names):
                    pieces.extend(inner)
            else:
                pieces.append((item.kind, ''))

    # ---- convenience -------------------------------------------------------
    def nc_text(self):
        return self.stream.text()

    def nc_lines(self):
        return [line.full for line in self.stream.all_lines()]


_HANDLERS = {
    N.Assign: Engine._exec_assign, N.FlagAssign: Engine._exec_flag_assign, N.CallProc: Engine._exec_call,
    N.Output: Engine._exec_output, N.Declare: Engine._exec_declare, N.Input: Engine._exec_input,
    N.Abort: Engine._exec_abort, N.Print: Engine._exec_print, N.Trace: Engine._exec_trace,
    N.Bad: Engine._exec_bad,
}
