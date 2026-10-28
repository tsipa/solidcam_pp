"""Whole-GPP static analysis on the load-time IR (never executes code).

* call graph, entry points (SolidCAM events), reachability;
* symbol classification (PP global, local, VMID parameter, system variable,
  control variable, constant, implicit PP variable, unknown);
* interprocedural definite-assignment flow -> per-event inferred SolidCAM inputs
  and change flags (the fixture-authoring checklist) and the CAM-interface
  inventory;
* lint: unknown identifiers, undeclared assignments, unreachable/unused code,
  format and type issues, policy-sensitive sites (doubled quotes, formats, '!'
  over a comparison, integer assignments, tonum, Print/input/trace), constant conditions,
  statements after abort, and branches dead under the *shipped configuration*
  (variables assigned exactly once, unconditionally, to a literal inside
  @init_post's call closure);
* coverage-gap split: never-executed statements -> dead under the shipped
  configuration / procedure unreachable / live code without test input.
"""
import operator
from collections import Counter
from dataclasses import dataclass, field

from . import nodes as N
from . import sysvars
from .builtins import BUILTINS
from .errors import Diagnostic
from .policies import Policies

UNKNOWN = object()
_CMP = {'eq': operator.eq, 'ne': operator.ne, 'lt': operator.lt, 'gt': operator.gt,
        'le': operator.le, 'ge': operator.ge}
_ARITH = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv}
CONFIG_ROOTS = ('init_post',)


@dataclass
class Facts:
    reads: dict = field(default_factory=dict)         # name -> first line (values, flags, format vars)
    flag_reads: dict = field(default_factory=dict)    # change(x) reads and modal-group variables
    writes: dict = field(default_factory=dict)        # name -> first line
    write_count: Counter = field(default_factory=Counter)
    flag_writes: dict = field(default_factory=dict)
    calls: dict = field(default_factory=dict)         # proc -> [(line, argc)]
    locals: set = field(default_factory=set)
    params: set = field(default_factory=set)
    functions: dict = field(default_factory=dict)     # builtin -> first line
    implicit_formats: set = field(default_factory=set)  # '<var>_f' read by bare output values


def procedure_facts(program):
    facts = {}
    for name, proc in program.procedures.items():
        fact = Facts()
        fact.params = set(proc.param_names)
        for stmt in N.walk_statements(proc.body):
            kind = type(stmt)
            for expr in N.statement_expressions(stmt):
                if type(expr) is N.FmtVar:
                    fact.reads.setdefault(expr.name, stmt.line)
                    continue
                if type(expr) is N.FmtLit:
                    continue
                for read in N.names_read(expr):
                    fact.reads.setdefault(read, stmt.line)
                for flag in N.flags_read(expr):
                    fact.flag_reads.setdefault(flag, stmt.line)
                for function in N.functions_used(expr):
                    fact.functions.setdefault(function, stmt.line)
            if kind in (N.Output, N.Print):
                for item in N.walk_items(stmt.items):
                    if type(item) is N.Modal:
                        for flag in item.names:
                            fact.flag_reads.setdefault(flag, stmt.line)
                    elif type(item) is N.Value and item.hint and item.fmt is None:
                        fact.implicit_formats.add(item.hint + '_f')
            if kind in (N.Assign, N.Input):
                fact.writes.setdefault(stmt.target, stmt.line)
                fact.write_count[stmt.target] += 1
            elif kind is N.FlagAssign:
                fact.flag_writes.setdefault(stmt.target, stmt.line)
            elif kind is N.Declare and stmt.scope == 'local':
                fact.locals.update(stmt.names)
            elif kind is N.CallProc:
                fact.calls.setdefault(stmt.proc, []).append((stmt.line, len(stmt.args)))
        facts[name] = fact
    return facts


def closure(facts, roots, skip_lines=None):
    """Procedures reachable from ``roots``; ``skip_lines`` {proc: lines} ignores
    call sites on those lines (calls inside dead branches)."""
    seen, todo = set(), list(roots)
    while todo:
        name = todo.pop()
        if name in seen or name not in facts:
            continue
        seen.add(name)
        for callee, sites in facts[name].calls.items():
            if skip_lines and all(line in skip_lines.get(name, ()) for line, _ in sites):
                continue
            todo.append(callee)
    return seen


def entry_points(program):
    known = set(sysvars.EVENT_CONTRACTS) | set(sysvars.LIFECYCLE)
    return [name for name in program.procedures if name in known]


def fold(expr, env):
    """Partial evaluation: the constant value of ``expr`` under ``env`` or UNKNOWN."""
    kind = type(expr)
    if kind in (N.Num, N.Str, N.Bool):
        return expr.value
    if kind is N.Var:
        return env.get(expr.name, UNKNOWN)
    if kind is N.Unary:
        value = fold(expr.operand, env)
        if value is UNKNOWN:
            return UNKNOWN
        if expr.op == 'not':
            return not value
        if isinstance(value, (int, float)):
            return -value if expr.op == '-' else +value
        return UNKNOWN
    if kind is N.Logical:
        left, right = fold(expr.left, env), fold(expr.right, env)
        for value in (left, right):
            if value is not UNKNOWN:
                if expr.op == 'and' and not value:
                    return False
                if expr.op == 'or' and value:
                    return True
        if left is UNKNOWN or right is UNKNOWN:
            return UNKNOWN
        return bool(right)
    if kind is N.Compare:
        left, right = fold(expr.left, env), fold(expr.right, env)
        if left is UNKNOWN or right is UNKNOWN:
            return UNKNOWN
        if isinstance(left, str) != isinstance(right, str):
            return UNKNOWN
        return _CMP[expr.op](left, right)
    if kind is N.Binary and expr.op in _ARITH:
        left, right = fold(expr.left, env), fold(expr.right, env)
        if UNKNOWN in (left, right) or isinstance(left, str) or isinstance(right, str):
            return UNKNOWN
        if expr.op == '/' and right == 0:
            return UNKNOWN
        return _ARITH[expr.op](left, right)
    return UNKNOWN


def _literal(expr):
    if type(expr) in (N.Num, N.Str, N.Bool):
        return True, expr.value
    if type(expr) is N.Unary and expr.op in ('-', '+') and type(expr.operand) is N.Num:
        return True, -expr.operand.value if expr.op == '-' else expr.operand.value
    return False, None


class Analysis:
    def __init__(self, program, vmid=None, policies=None):
        self.program = program
        self.vmid = vmid
        self.policies = policies or Policies()
        self.facts = procedure_facts(program)
        self.vmid_params = vmid.all_params() if vmid is not None else {}
        self.vmid_constants = vmid.constants() if vmid is not None else {}
        self.pp_globals = set(program.globals)
        self.pp_written = {name for fact in self.facts.values() for name in fact.writes}
        self.all_locals = {name for fact in self.facts.values() for name in fact.locals | fact.params}
        self.diagnostics = []
        self.constants = {}
        self.dead_lines = {}
        self._flow = {}

    # ---- classification ------------------------------------------------
    def classify(self, name, proc=None):
        fact = self.facts.get(proc)
        if fact and (name in fact.locals or name in fact.params):
            return 'local'
        if name in self.pp_globals:
            return 'pp-global'
        if name in self.vmid_params:
            return 'vmid-param'
        if name in sysvars.CONSTANTS or name in self.vmid_constants:
            return 'constant'
        if name in sysvars.CONTROL_VARIABLES or name in sysvars.SYSTEM_FORMATS:
            return 'control'
        if name in sysvars.SYSTEM_TYPES:
            return 'system'
        if name in self.pp_written:
            return 'pp-undeclared'
        return 'unknown'

    def flow(self, proc, _visiting=None):
        """Interprocedural definite-assignment summary in program order.

        Returns (reads, writes): ``reads`` may be read before being definitely
        assigned (descending into calls); ``writes`` are assigned on every path.
        if/else merges by intersection, loop bodies may not run. Used for
        contract warnings only, never for semantics."""
        if proc in self._flow:
            return self._flow[proc]
        visiting = _visiting if _visiting is not None else set()
        if proc in visiting or proc not in self.program.procedures:
            return {}, set()
        visiting.add(proc)
        reads = {}
        local_names = self.facts[proc].locals | self.facts[proc].params

        def note(name, where, written):
            if name not in written and name not in local_names:
                reads.setdefault(name, where)

        def visit(body, written):
            written = set(written)
            for stmt in body:
                kind = type(stmt)
                for expr in N.statement_expressions(stmt):
                    if type(expr) is N.FmtLit:
                        continue
                    names = {expr.name} if type(expr) is N.FmtVar else N.names_read(expr)
                    for name in names:
                        note(name, (proc, stmt.line), written)
                if kind is N.CallProc:
                    callee_reads, callee_writes = self.flow(stmt.proc, visiting)
                    for name, where in callee_reads.items():
                        note(name, where, written)
                    written |= callee_writes
                elif kind in (N.Assign, N.Input):
                    written.add(stmt.target)
                elif kind is N.Declare:
                    written.update(stmt.names)
                elif kind is N.If:
                    written = visit(stmt.then, written) & visit(stmt.orelse, written)
                elif kind is N.While:
                    visit(stmt.body, written)
            return written

        try:
            writes = visit(self.program.procedures[proc].body, set()) - local_names
        except RecursionError:
            writes = set()
        visiting.discard(proc)
        result = (reads, writes)
        if _visiting is None or not visiting:
            self._flow[proc] = result
        return result

    def external_inputs(self, root):
        """Names ``root``'s call tree may read before the PP assigns them and that
        are not PP-owned: what SolidCAM (or the VMID) must provide."""
        result = {}
        for read, (proc, line) in sorted(self.flow(root)[0].items()):
            kind = self.classify(read, proc)
            if kind in ('system', 'vmid-param', 'unknown'):
                result[read] = (kind, proc, line)
        return result

    def external_flags(self, root):
        """change() flags (and modal-group variables) read in ``root``'s call tree
        for variables the PP does not own: SolidCAM must supply these flags."""
        flags = set()
        for proc in closure(self.facts, [root]):
            for name in self.facts[proc].flag_reads:
                if self.classify(name, proc) in ('system', 'vmid-param', 'unknown'):
                    flags.add(name)
        return sorted(flags)

    def event_contracts(self):
        report = {}
        for event in entry_points(self.program):
            inferred = self.external_inputs(event)
            registry = set(sysvars.EVENT_CONTRACTS.get(event, ()))
            report[event] = {
                'inferred': {name: info[0] for name, info in sorted(inferred.items())},
                'flags': self.external_flags(event),
                'registry': sorted(registry),
                'persisted_from_earlier_events': sorted(
                    name for name, info in inferred.items() if info[0] == 'system' and name not in registry),
            }
        return report

    def interface(self):
        """CAM-interface inventory of the whole GPP."""
        reads, flags, writes, implicit = set(), set(), set(), set()
        for fact in self.facts.values():
            reads |= set(fact.reads)
            flags |= set(fact.flag_reads)
            writes |= set(fact.writes)
            implicit |= fact.implicit_formats
        owned = self.pp_globals | self.all_locals
        constants = set(sysvars.CONSTANTS) | set(self.vmid_constants)
        cam_inputs = sorted(n for n in reads - writes - owned - constants)
        modified = sorted(n for n in reads & writes - owned
                          if self.classify(n) in ('system', 'vmid-param'))
        flag_inputs = sorted(n for n in flags - owned if self.classify(n) in ('system', 'vmid-param', 'unknown'))
        switches = sorted(n for n in writes - reads - implicit
                          if self.classify(n) in ('control', 'system') or n.endswith('_f'))
        return {
            'entry_points': entry_points(self.program),
            'cam_inputs': {n: self.classify(n) for n in cam_inputs},
            'cam_inputs_modified_by_gpp': modified,
            'flag_inputs': flag_inputs,
            'runtime_switches_written_never_read': switches,
        }

    # ---- shipped configuration ---------------------------------------------
    def config_constants(self):
        roots = [root for root in CONFIG_ROOTS if root in self.program.procedures]
        config = closure(self.facts, roots)
        totals = Counter()
        for fact in self.facts.values():
            totals.update(fact.write_count)
        candidates = {}
        for proc in config:
            for stmt in self.program.procedures[proc].body:     # unconditional statements only
                if type(stmt) is N.Assign:
                    ok, value = _literal(stmt.expr)
                    if ok and stmt.target not in candidates:
                        candidates[stmt.target] = (value, stmt.line)
        constants = {}
        for name, entry in candidates.items():
            if totals[name] != 1 or name in self.all_locals:
                continue
            if self.classify(name) not in ('pp-global', 'pp-undeclared'):
                continue
            constants[name] = entry
        self.constants = constants
        return {name: value for name, (value, _) in constants.items()}

    def _reach(self, body, proc, env, dead=False):
        after_abort = False
        for stmt in body:
            if after_abort and not dead:
                self.diag('warning', 'W-UNREACHABLE', proc, stmt.line, 'statement after abort is unreachable')
                dead = True
            if dead:
                self.dead_lines.setdefault(proc, set()).add(stmt.line)
            kind = type(stmt)
            if kind is N.Abort:
                after_abort = True
            if kind is N.If and stmt.cond is not None:
                literal, configured = fold(stmt.cond, {}), fold(stmt.cond, env)
                then_dead = else_dead = False
                if literal is not UNKNOWN and not dead:
                    self.diag('warning', 'W-CONSTANT-CONDITION', proc, stmt.line,
                              f'condition is always {bool(literal)}')
                    then_dead, else_dead = not literal, bool(literal)
                elif configured is not UNKNOWN and not dead:
                    then_dead, else_dead = not configured, bool(configured)
                    dead_body = stmt.then if then_dead else stmt.orelse
                    count = sum(1 for _ in N.walk_statements(dead_body))
                    if count:
                        names = sorted({n.name for n in N.walk_expr(stmt.cond)
                                        if type(n) is N.Var and n.name in self.constants})
                        because = ', '.join(f'{n}={self.constants[n][0]!r} (L{self.constants[n][1]})'
                                            for n in names)
                        self.diag('info', 'I-CONFIG-DEAD', proc, stmt.line,
                                  f'{"then" if then_dead else "else"} branch never runs with the shipped '
                                  f'configuration ({because}); {count} statement(s)')
                self._reach(stmt.then, proc, env, dead or then_dead)
                self._reach(stmt.orelse, proc, env, dead or else_dead)
            elif kind is N.While and stmt.cond is not None:
                literal, configured = fold(stmt.cond, {}), fold(stmt.cond, env)
                body_dead = False
                if literal is not UNKNOWN and not dead and not literal:
                    self.diag('warning', 'W-CONSTANT-CONDITION', proc, stmt.line, 'while condition is always false')
                    body_dead = True
                elif configured is not UNKNOWN and not configured and not dead:
                    body_dead = True
                self._reach(stmt.body, proc, env, dead or body_dead)

    def reachability(self):
        env = self.config_constants()
        self.dead_lines = {}
        for name, proc in self.program.procedures.items():
            try:
                self._reach(proc.body, name, env)
            except RecursionError:
                self.diag('warning', 'W-ANALYSIS', name, proc.line, 'nesting too deep for reachability analysis')
        entries = entry_points(self.program)
        self.reachable = closure(self.facts, entries)
        self.live = closure(self.facts, entries, self.dead_lines)

    def coverage_split(self, coverage):
        """Never-executed statements by cause."""
        if not hasattr(self, 'live'):
            self.reachability()
        split = Counter()
        for name, proc in self.program.procedures.items():
            for stmt in N.walk_statements(proc.body):
                if coverage.executed(name, stmt.line):
                    split['executed'] += 1
                elif name not in self.reachable:
                    split['never executed: procedure unreachable from any SolidCAM event'] += 1
                elif name not in self.live or stmt.line in self.dead_lines.get(name, ()):
                    split['never executed: dead under the shipped configuration'] += 1
                else:
                    split['never executed: live code without test input'] += 1
        return dict(split)

    # ---- diagnostics -----------------------------------------------------
    def diag(self, severity, code, proc, line, message):
        self.diagnostics.append(Diagnostic(severity, code, proc, line, message))

    def run(self):
        program, facts = self.program, self.facts
        self.diagnostics = list(program.diagnostics) + list(program.policy_diagnostics(self.policies))
        self.reachability()
        for name, fact in facts.items():
            proc = program.procedures[name]
            for read, line in fact.reads.items():
                if self.classify(read, name) == 'unknown':
                    self.diag('warning', 'W-UNKNOWN-IDENT', name, line,
                              f'{read!r} is not declared by the PP, not a VMID parameter and not in the '
                              f'system-variable registry (typo or missing registry entry?)')
            for write, line in fact.writes.items():
                if self.classify(write, name) == 'pp-undeclared':
                    self.diag('warning', 'W-UNDECLARED-WRITE', name, line,
                              f'{write!r} assigned without a declaration; not a VMID parameter and not in the '
                              f'system-variable registry (implicit global: a misspelt option or setting?)')
            for function, line in fact.functions.items():
                if BUILTINS[function][3] == 'assumed':
                    self.diag('info', 'I-ASSUMED-BUILTIN', name, line,
                              f'{function}() semantics are assumed, not verified')
            for local in sorted(fact.locals | fact.params):
                if local in sysvars.SYSTEM_TYPES:
                    self.diag('info', 'I-SHADOW', name, proc.line, f'local {local!r} shadows a SolidCAM system variable')
            if name not in self.reachable:
                self.diag('info', 'I-UNREACHABLE', name, proc.line,
                          'procedure is not an event and is not called from any event (dead code)')
            elif name not in self.live:
                self.diag('info', 'I-CONFIG-DEAD-PROC', name, proc.line,
                          'procedure is only called from branches dead under the shipped configuration')
        self._policy_sites()
        all_reads = {}
        for name, fact in facts.items():
            for read, line in fact.reads.items():
                all_reads.setdefault(read, (name, line))
        implicit = set().union(*(fact.implicit_formats for fact in facts.values())) if facts else set()
        for name, (vtype, proc, line) in sorted(program.globals.items()):
            if name not in all_reads and name not in self.pp_written and name not in implicit:
                self.diag('info', 'I-UNUSED-GLOBAL', proc, line, f'global {vtype} {name} is never used')
            elif name in all_reads and name not in self.pp_written and self.classify(name) == 'pp-global':
                where = all_reads[name]
                self.diag('warning', 'W-NEVER-ASSIGNED', where[0], where[1],
                          f'global {name} is read but never assigned (always its declared default)')
        return self.diagnostics

    def _policy_sites(self):
        program = self.program
        numeric_globals = {n for n, (t, _, _) in program.globals.items() if t == 'numeric'}
        for name, proc in program.procedures.items():
            for stmt in N.walk_statements(proc.body):
                kind = type(stmt)
                doubled = False
                if kind in (N.Output, N.Print):
                    doubled = any(type(i) is N.Text and i.doubled for i in N.walk_items(stmt.items))
                for expr in N.statement_expressions(stmt):
                    if type(expr) in (N.FmtLit, N.FmtVar):
                        continue
                    for node in N.walk_expr(expr):
                        if type(node) is N.Str and node.doubled:
                            doubled = True
                        if type(node) is N.Unary and node.op == 'not' and type(node.operand) is N.Compare \
                                and not node.operand.paren:
                            self.diag('warning', 'W-NOT-COMPARE', name, stmt.line,
                                      "'!'/'not' applied to an unparenthesised comparison: the legacy "
                                      'precedence (below comparisons) is an assumption')
                        if type(node) is N.Call and node.name == 'tonum' and type(node.args[0]) is not N.Str:
                            self.diag('info', 'I-POLICY-TONUM', name, stmt.line,
                                      'tonum() of a runtime value: non-numeric text depends on policy tonum')
                if doubled:
                    self.diag('warning', 'W-QUOTE-DOUBLING', name, stmt.line,
                              f'literal with a doubled quote is policy-sensitive (quote_escape=double reads an '
                              f'escaped quote, none reads two literals): {stmt.text[:80]}')
                if kind is N.Assign and program.globals.get(stmt.target, ('',))[0] == 'integer':
                    if any((type(n) is N.Binary and n.op == '/') or (type(n) is N.Call and n.name in
                           ('tonum', 'sin', 'cos', 'tan', 'sqrt', 'asin', 'acos', 'atan'))
                           or (type(n) is N.Var and n.name in numeric_globals)
                           or (type(n) is N.Num and isinstance(n.value, float))
                           for n in N.walk_expr(stmt.expr)):
                        self.diag('info', 'I-POLICY-INTEGER', name, stmt.line,
                                  f'integer {stmt.target} may receive a fractional value: depends on policy '
                                  f'integer_assign')
                if kind is N.Assign and type(stmt.expr) is N.Str:
                    declared = program.globals.get(stmt.target)
                    if declared and declared[0] in ('integer', 'numeric'):
                        self.diag('warning', 'W-TYPE', name, stmt.line,
                                  f'string literal assigned to {declared[0]} {stmt.target}')
                if kind in (N.Print, N.Input, N.Trace):
                    policy = {N.Print: 'print_stmt', N.Input: 'input_stmt', N.Trace: 'trace_stmt'}[kind]
                    self.diag('info', 'I-POLICY-STMT', name, stmt.line,
                              f'{kind.__name__.lower()} statement: behaviour depends on policy {policy}')

    def summary(self):
        counts = Counter(d.severity for d in self.diagnostics)
        statements = sum(1 for _ in self.program.walk())
        kinds = Counter(type(stmt).__name__ for stmt in self.program.walk())
        return {'procedures': len(self.program.procedures), 'statements': statements,
                'statement_kinds': dict(sorted(kinds.items())),
                'globals_declared': len(self.program.globals), 'diagnostics': dict(sorted(counts.items())),
                'entry_points': len(entry_points(self.program)),
                'config_constants': len(self.constants),
                'statements_dead_under_shipped_configuration': sum(len(v) for v in self.dead_lines.values())}
