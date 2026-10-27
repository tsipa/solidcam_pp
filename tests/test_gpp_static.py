"""Static checks over the GPP source text and the fixture schemas.

These tests never execute GPPL (except @init_post for the option values).
They cover properties the behaviour suite cannot see: code that no scenario
executes, and defects that do not show in the interpreter's NC blocks (an
active SolidCAM trace switch writes debug records into the program; the
engine ignores text outside procedures, ENGINE-019).

Pinned lists name the current legacy findings explicitly. The dead-option and
constant-condition pins are exact (a new occurrence fails, and removing a pinned
occurrence also fails, so the list is trimmed in the same change). The
Fanuc-only output pin is an allowlist: a new occurrence fails, but removing one
passes, because several pinned occurrences are registered defects owned by
other areas (PP-012, PP-038, PP-044, PP-045) and fixing a defect must flip only
its canonical test. Option values and dead-option pins exclude the options whose
defects are registered elsewhere (PP-010, PP-049) for the same reason.
"""
import functools
import json
import re
import unittest
from collections import Counter, defaultdict

from pp_tests.engine import uncomment

from support import assert_detected, covers, fresh_engine, mutate, pp_source
from support.paths import FIXTURES, read_text

NUMERIC_FORMAT = re.compile(r"^\+?\d+\.\d+(?:\([pPnN]\))?$")
CONTROL = ('if ', 'while ')


@functools.lru_cache(maxsize=8)
def load_lines(source):
    """((line_number, code_without_comment, procedure_or_None), ...) of a GPP source."""
    result = []
    current = None
    for number, raw in enumerate(source.splitlines(), 1):
        code = uncomment(raw)
        if not code:
            continue
        if code.startswith('@'):
            current = re.match(r'@(\w+)', code).group(1).lower()
            result.append((number, code, None))
            continue
        if code.lower() == 'endp':
            result.append((number, code, current))
            current = None
            continue
        result.append((number, code, current))
    return tuple(result)


def strip_strings(code):
    return re.sub(r"'(?:[^']|'')*'|\"[^\"]*\"", "''", code)


def option_state(source=None):
    """Post options as @init_post leaves them (stock engine; init_post runs there)."""
    engine = fresh_engine(source)
    engine.call('init_post')
    return engine.state


class GppStructureTests(unittest.TestCase):
    def setUp(self):
        self.lines = load_lines(pp_source())

    @covers('ENGINE-019')
    def test_every_statement_is_inside_a_procedure(self):
        """INDEPENDENT: GPPL program structure: statements belong to @proc..endp.
        The interpreter silently ignores text outside procedures (ENGINE-019),
        so only this static check sees a stray statement."""
        stray = [(n, code) for n, code, proc in self.lines if proc is None and not code.startswith('@')]
        self.assertEqual(stray, [])

    def test_block_structure_is_balanced_in_every_procedure(self):
        """INDEPENDENT: GPPL block syntax (if/else/endif, while/endw). Runtime
        checks only cover executed procedures; this covers all of them."""
        problems = []
        stack = []
        current = None
        for number, code, proc in self.lines:
            low = code.lower()
            if code.startswith('@'):
                if stack:
                    problems.append((current, 'unclosed ' + ','.join(kind for kind, _ in stack)))
                stack, current = [], low[1:].split('(')[0].split()[0]
                continue
            if low.startswith('if '):
                stack.append(('if', number))
            elif low.startswith('while '):
                stack.append(('while', number))
            elif low == 'else':
                if not stack or stack[-1][0] != 'if':
                    problems.append((current, f'else without if at {number}'))
            elif low == 'endif':
                if not stack or stack.pop()[0] != 'if':
                    problems.append((current, f'unbalanced endif at {number}'))
            elif low == 'endw':
                if not stack or stack.pop()[0] != 'while':
                    problems.append((current, f'unbalanced endw at {number}'))
            elif low == 'endp' and stack:
                problems.append((current, f'endp with open {stack} at {number}'))
                stack = []
        self.assertEqual(problems, [])

    def test_call_targets_exist_with_matching_arity(self):
        """INDEPENDENT: GPPL call semantics: every `call @name(...)` targets a
        defined procedure with the declared number of arguments, including
        calls in procedures no scenario executes."""
        engine = fresh_engine()
        problems = []
        for number, code, proc in self.lines:
            for target, args in re.findall(r'call\s+@(\w+)(?:\(([^)]*)\))?', code, re.I):
                name = target.lower()
                if name not in engine.procedures:
                    problems.append((number, f'missing @{name}'))
                    continue
                count = 0 if not args else len(args.split(','))
                if count != len(engine.arguments[name]):
                    problems.append((number, f'@{name} takes {len(engine.arguments[name])} args, got {count}'))
        self.assertEqual(problems, [])

    def test_global_declarations_are_unique_and_single_typed(self):
        """INDEPENDENT: GPPL declarations: a global is declared once with one
        type (a second declaration with another type is ambiguous)."""
        seen = defaultdict(set)
        counts = Counter()
        for number, code, proc in self.lines:
            match = re.fullmatch(r'global\s+(numeric|integer|logical|string)\s+(.+)', code, re.I)
            if match:
                for name in match.group(2).replace(',', ' ').split():
                    seen[name.lower()].add(match.group(1).lower())
                    counts[name.lower()] += 1
        self.assertEqual({n for n, c in counts.items() if c > 1}, set())
        self.assertEqual({n for n, kinds in seen.items() if len(kinds) > 1}, set())

    def test_numeric_format_descriptors_are_well_formed(self):
        """INDEPENDENT: GPPL numeric format grammar ([+]digits.decimals with an
        optional (p)/(n) modifier); every named format an output uses
        (`value:name_f`) is assigned somewhere (integer_def_f is a system
        default)."""
        problems = []
        format_variables = set()
        for number, code, proc in self.lines:
            assignment = re.fullmatch(r"(\w+_f)\s*=\s*'([^']*)'", code, re.I)
            if assignment:
                format_variables.add(assignment.group(1).lower())
                if not NUMERIC_FORMAT.match(assignment.group(2)):
                    problems.append((number, assignment.group(2)))
            if code.startswith('{') or 'tostr(' in code.lower():
                for descriptor in re.findall(r":'([^']*)'", code):
                    if not NUMERIC_FORMAT.match(descriptor):
                        problems.append((number, descriptor))
        self.assertEqual(problems, [])
        used = set()
        for number, code, proc in self.lines:
            if code.startswith('{'):
                used.update(name.lower() for name in re.findall(r':([A-Za-z_]\w*_f)\b', strip_strings(code)))
        self.assertEqual(used - format_variables - {'integer_def_f'}, set())

    def test_constant_change_conditions_are_pinned(self):
        """CHARACTERIZATION: `change(x) = false` immediately followed by
        `if change(x)` is dead code. Pinned: the single occurrence in
        @end_program; a new one fails, removing it requires trimming the pin."""
        dead = []
        for (n1, c1, p1), (n2, c2, p2) in zip(self.lines, self.lines[1:]):
            match = re.fullmatch(r'change\((\w+)\)\s*=\s*false', c1, re.I)
            if match and re.fullmatch(rf'if\s+change\({match.group(1)}\)', c2, re.I):
                dead.append((p2, c2))
        self.assertEqual(dead, [])

    @covers('PP-057')
    def test_fanuc_only_output_is_pinned_to_legacy_procedures(self):
        """INDEPENDENT: Sinumerik 828D native programs have no Fanuc/Haas words
        (G28/G30 reference returns, G65 macro calls, G10 L2 offset writes, G20,
        G103, G187, M98/M99 subprograms, O-numbers, '#' macro variables,
        WHILE [..] loops). PP-057: the template keeps such output in procedures
        that the shipped options and VMID keep unreachable. This pins exactly
        where; a new occurrence or a move into another procedure fails.
        Removing an occurrence passes (allowlist, not an exact pin): G187
        (PP-012), the G10 L2 write (PP-045), @call_proc (PP-044) and the trig
        macro (PP-038) are registered defects of other areas, and their fixes
        must not trip this test."""
        pattern = re.compile(r"(?<![A-Z0-9])(G28|G30|G65|G10|G20|G103|G187|M98|M99|O777)(?![\d.])"
                             r"|\bL2 P|#|WHILE \[")
        found = defaultdict(set)
        for number, code, proc in self.lines:
            if not code.startswith('{'):
                continue
            literals = ' '.join(re.findall(r"'((?:[^']|'')*)'", code))
            for match in pattern.finditer(literals):
                found[proc].add(match.group(0))
        allowed = {
            'usr_home_axis': {'G28', 'G30'},            # iHomingmode 1,2,5,6; the options use mode 8
            'usr_hsm_mode': {'G187'},                   # PP-012 (VMID job parameters iG187_P/nG187_E)
            'change_ref_point': {'L2 P'},               # PP-045: G91 G10 L2 P.. (Fanuc offset write)
            'call_proc': {'G20', 'M98'},                # PP-044: VMID ProceduresDef GenProc=0
            'end_proc': {'M99'},
            'usr_trig_macro_call': {'G65'},             # PP-038: i4xIndexMode 2 only
            'usr_trig_macro_output': {'O777', 'G103', '#', 'M99'},
            'start_of_job': {'#', 'WHILE ['},           # bPrintloop; VMID LoopExist=0
            'end_loop': {'#'},
        }
        unexpected = {proc: sorted(words - allowed.get(proc, set())) for proc, words in found.items()
                      if words - allowed.get(proc, set())}
        self.assertEqual(unexpected, {}, 'Fanuc/Haas-only output outside the pinned legacy procedures')


# Options a GPPL system consumes itself (block numbering), not GPP code.
SYSTEM_SETTINGS = frozenset({'blknum_exist', 'blknum', 'blknum_delta', 'blknum_max'})
# Dead options with a registered defect and their own canonical tests:
# PP-010 (bCoolofftc/bSpinofftc, area A) and PP-049 (i4xFeedMode, area D).
REGISTERED_DEAD = frozenset({'bcoolofftc', 'bspinofftc', 'i4xfeedmode'})


def options_without_consumers(source):
    """Options assigned in @usr_ip_useroptions that no statement ever reads.

    A read is any use outside an assignment target: a right-hand side, a
    condition, an output or a call argument. `change(x) = false` and
    declarations are not reads.
    """
    options = set()
    reads = Counter()
    for number, code, proc in load_lines(source):
        if proc == 'usr_ip_useroptions':
            match = re.fullmatch(r'(\w+)\s*=.*', code)
            if match:
                options.add(match.group(1).lower())
        if re.match(r'(local|global)\s', code, re.I):
            continue
        assignment = re.fullmatch(r'(?:change\(\w+\)|\w+)\s*=(.*)', code, re.I)
        text = strip_strings(assignment.group(1) if assignment and not code.lower().startswith(CONTROL) else code)
        for word in re.findall(r'\b[a-z_]\w*\b', text.lower()):
            reads[word] += 1
    return {name for name in options if reads[name] == 0} - SYSTEM_SETTINGS - REGISTERED_DEAD


class OptionTests(unittest.TestCase):
    def assert_safe_options(self, source=None):
        state = option_state(source)
        # 1/3 print absolute centres as plain I/J/K (Sinumerik reads them
        # incremental, absolute needs I=AC()); 3/4 print R (the 828D radius
        # word is CR=, R is an arithmetic parameter). Only 2 is valid (PP-022).
        self.assertEqual(state['iarcmode'], 2, 'iArcmode')
        # 0 passes raw CAM angles; 2 emits negative directed positions on the
        # modulo A axis (PP-002); 3 is documented 'Not Working yet' (PP-037).
        self.assertEqual(state['ir1poscontrol'], 1, 'iR1posControl')
        # 1 accumulates work offsets (PP-016/PP-017); 2 emits Fanuc macro B
        # (G65 P777, #7041, G103) and G112 (Sinumerik polar pole) (PP-038).
        self.assertEqual(state['i4xindexmode'], 0, 'i4xIndexMode')
        self.assertEqual(state['cr1'], 'A', 'the rotary axis is A')
        # bSubs=true skips @usr_ct_before_*/@usr_ct_after at every tool change
        # (M9/M5 and G75 homing before M06; spindle, coolant and the first rapid
        # after it) and restarts each job with a G1 positioning (@start_of_job). @call_proc is NOT gated by bSubs
        # (history-misc-16 correction); the VMID ProceduresDef guard in
        # test_machine_definition.py keeps it unreachable (PP-044).
        self.assertIs(state['bsubs'], False, 'bSubs')
        self.assertIs(state['buseprognum'], False, "'O<number>' is not a Sinumerik address")
        self.assertEqual((state['iworkoffsetmode'], state['cwo']), (1, 'G'), 'G54-style work offsets')
        self.assertIn(state['iprogendmode'], (1, 2), 'any other value silently omits the program end')
        self.assertEqual((state['ccb'], state['cce'], state['comb'], state['come']), (';', '', 'MSG("', '")'),
                         'Sinumerik comment and operator-message syntax')
        # @end_program would emit 'M06 T<n>' (change before select).
        self.assertIs(state['btoolchangeatend'], False, 'bToolChangeAtEnd')

    def test_safety_relevant_user_options(self):
        """INDEPENDENT: Sinumerik 828D syntax and the GPP's own option
        documentation: the shipped options select the only modes that are
        valid for this control (iArcmode 2, iR1posControl 1, i4xIndexMode 0,
        G54 offsets, M30/M2 program end, ';' comments and MSG() messages, no
        O-number, bSubs off so tool changes keep their preparation, no tool
        change at end). The alternative modes are registered defects (PP-022,
        PP-002, PP-037, PP-016/017, PP-038); this static guard is their
        practical protection."""
        self.assert_safe_options()

    def test_option_guard_detects_unsafe_values(self):
        """INDEPENDENT: mutation self-check; each unsafe option value must fail
        the guard with AssertionError."""
        mutants = {
            'iArcmode 1': ('    iArcmode              = 2 ', '    iArcmode              = 1 '),
            'iArcmode 4': ('    iArcmode              = 2 ', '    iArcmode              = 4 '),
            'iR1posControl 2': ('    iR1posControl         = 1 ', '    iR1posControl         = 2 '),
            'iR1posControl 3': ('    iR1posControl         = 1 ', '    iR1posControl         = 3 '),
            'i4xIndexMode 1': ('    i4xIndexMode          = 0 ', '    i4xIndexMode          = 1 '),
            'i4xIndexMode 2': ('    i4xIndexMode          = 0 ', '    i4xIndexMode          = 2 '),
            'bUseprognum true': ('    bUseprognum           = false', '    bUseprognum           = true'),
            'iProgendmode 3': ('    iProgendmode          = 1 ', '    iProgendmode          = 3 '),
            'bSubs true': ('    bSubs = false ', '    bSubs = true '),
            'cR1 B': ("    cR1                   = 'A'", "    cR1                   = 'B'"),
        }
        for label, (old, new) in mutants.items():
            assert_detected(self, self.assert_safe_options, mutate(old, new), label)

    def test_user_options_that_have_no_effect_are_pinned(self):
        """CHARACTERIZATION: user options assigned in @usr_ip_useroptions that no
        statement reads; editing one changes nothing in the NC program (G84
        tapping strings, gear and pallet options, the second rotary letter).
        bCoolofftc/bSpinofftc (PP-010) and i4xFeedMode (PP-049) are registered
        defects with their own canonical tests and are excluded, as are the
        blknum* block-numbering settings SolidCAM consumes itself. A new dead
        option fails; a pinned option that gains a reader must be trimmed."""
        self.assertEqual(options_without_consumers(pp_source()), {
            'bg84spin', 'fg84spin', 'cg84', 'cg84p', 'cdr', 'ccycs',
            'igear1', 'igear2', 'igear3', 'igear4', 'ipal1', 'ipal2', 'cr2',
        })

    def test_dead_option_pin_detects_a_new_consumer(self):
        """INDEPENDENT: mutation self-check; giving a pinned option a reader
        (cDr printed in @usr_hsm_mode) must change the computed set."""
        anchor = '\n@usr_HSM_mode\n'
        mutant = mutate(anchor, anchor + "    {nb, cDr}\n")
        self.assertNotIn('cdr', options_without_consumers(mutant))
        self.assertIn('cdr', options_without_consumers(pp_source()))


class StaticSourceTests(unittest.TestCase):
    def scan(self, source):
        problems = []
        for number, raw in enumerate(source.splitlines(), 1):
            line = uncomment(raw)
            if re.match(r'trace\b', line, re.I):
                problems.append((number, 'active trace statement', raw.strip()))
            if re.match(r'input\b', line, re.I) and 'POST ERROR' not in line:
                problems.append((number, 'interactive input prompt', raw.strip()))
        self.assertEqual(problems, [])

    def test_no_active_trace_or_interactive_input(self):
        """INDEPENDENT: c8b79bd 'Disable postprocessor trace': an active GPPL
        trace writes '(n)@proc ==> ...' records into the NC file ('(' does not
        start a comment on Sinumerik, so the program alarms on load);
        revisions bff5ed0 and ab853be shipped with `trace "all":5` and no
        behaviour test executes @usr_ip_postwriteroptions. `input` prompts are
        allowed only on the POST ERROR paths."""
        self.scan(pp_source())

    def test_c8b79bd_reversion_is_detected(self):
        """INDEPENDENT: mutation self-check; re-activating the trace (the
        c8b79bd reversion) must fail the scan with AssertionError."""
        assert_detected(self, self.scan, mutate('    ; trace "all":5\n', '    trace "all":5\n'), 'c8b79bd reverted')


STEP_KEYS = {'call', 'set', 'changed', 'blocks', 'contains', 'absent', 'order', 'state'}
# Scenario keys per motion_sequences.json schema version. Area C owns the fixture
# and its harness (tests/test_motion.py); schema 2 changed the token semantics to
# exact NC words and added the documentation-only 'note'; the step keys are the
# same in both versions.
SCENARIO_KEYS = {1: {'name', 'initial', 'steps'}, 2: {'name', 'initial', 'steps', 'note'}}
# 'unpinned' is area E's note naming why a cycle parameter is deliberately not
# pinned (case level in some fixture revisions, inside expected_parameters in others).
HISTORY_KEYS = {'name', 'kind', 'commit', 'reason', 'initial', 'regression', 'related_commits',
                'expected_codes', 'expected_a', 'expected_apos', 'expected_secondary', 'expected_blocks',
                'expected_cycle', 'expected_parameters', 'unpinned'}
REGRESSION_KEYS = {'find', 'replace', 'count'}
# A reversal anchor may occur several times (the real commit changed every
# occurrence). Area E's fixture states that number as regression.count, which
# tests/test_history_regressions.py passes to support.mutation.mutate; for a
# fixture revision without 'count' these are the expected occurrence counts.
LEGACY_ANCHOR_COUNTS = {'cycle81_positive_reference_plane': 3, 'cycle82_positive_reference_and_dwell': 3,
                        'cycle83_positive_reference_and_upper_dwell': 2,
                        'cycle83_nonpositive_reference_keeps_relative_depth_zero': 2}


def load_fixture(name):
    return json.loads(read_text(FIXTURES / name, 'utf-8'))


def unknown_step_keys(fixture):
    """Keys the motion harness would silently ignore (a typo drops an assertion)."""
    scenario_keys = SCENARIO_KEYS.get(fixture.get('schema'))
    if scenario_keys is None:
        return [('unknown schema', fixture.get('schema'))]
    found = []
    for scenario in fixture['scenarios']:
        if set(scenario) - scenario_keys:
            found.append((scenario['name'], sorted(set(scenario) - scenario_keys)))
        for number, step in enumerate(scenario['steps']):
            extra = set(step) - STEP_KEYS
            if extra or 'call' not in step:
                found.append((scenario['name'], number, sorted(extra)))
    return found


class FixtureSchemaTests(unittest.TestCase):
    """The harnesses read fixture keys with dict.get(); unknown keys are ignored."""

    def test_motion_sequence_steps_use_known_keys_only(self):
        """INDEPENDENT: the motion_sequences.json schema the harness implements
        (schema 1 or 2; step keys call/set/changed/blocks/contains/absent/order/
        state, scenario keys name/initial/steps plus 'note' in schema 2); the
        check itself must catch a typo such as 'contians'. A new schema version
        fails until SCENARIO_KEYS knows it."""
        fixture = load_fixture('motion_sequences.json')
        self.assertEqual(unknown_step_keys(fixture), [])
        broken = json.loads(json.dumps(fixture))
        broken['scenarios'][0]['steps'][0]['contians'] = ['X1']
        self.assertTrue(unknown_step_keys(broken))

    def test_history_cases_use_known_keys_and_unique_reversal_anchors(self):
        """INDEPENDENT: the history_regressions.json schema; case names are
        unique, case and regression keys are known (a misspelt 'regression'
        would silently drop a reversal check), and every reversal anchor occurs
        exactly as often as the case states (str.replace rewrites all
        occurrences, so a new duplicate would silently widen a reversal)."""
        fixture = load_fixture('history_regressions.json')
        source = pp_source()
        names = [case['name'] for case in fixture['cases']]
        self.assertEqual(len(names), len(set(names)))
        problems = []
        for case in fixture['cases']:
            if set(case) - HISTORY_KEYS:
                problems.append((case['name'], sorted(set(case) - HISTORY_KEYS)))
            if 'regression' in case:
                regression = case['regression']
                if set(regression) - REGRESSION_KEYS:
                    problems.append((case['name'], sorted(set(regression) - REGRESSION_KEYS)))
                expected = regression.get('count', LEGACY_ANCHOR_COUNTS.get(case['name'], 1))
                count = source.count(regression['find'])
                if count != expected:
                    problems.append((case['name'], f'anchor occurs {count} times, expected {expected}'))
        self.assertEqual(problems, [])


if __name__ == '__main__':
    unittest.main()
