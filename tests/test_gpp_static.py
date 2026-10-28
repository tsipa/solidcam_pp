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
from pp_tests.gppl.program import load_program

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


STRING_OR_DESCRIPTOR = re.compile(r":\s*'([^']*)'|'(?:[^']|'')*'|\"[^\"]*\"")


def format_descriptors(code):
    """Literal formats of output items (value:'5.3'); a ':' inside a string literal is text."""
    return [match.group(1) for match in STRING_OR_DESCRIPTOR.finditer(code) if match.group(1) is not None]


def option_state(source=None):
    """Post options as @init_post leaves them (stock engine; init_post runs there)."""
    engine = fresh_engine(source)
    engine.call('init_post')
    return engine.state


class GppStructureTests(unittest.TestCase):
    def setUp(self):
        self.lines = load_lines(pp_source())

    def assert_valid_variable_names(self, source):
        errors = [str(d) for d in load_program(source).diagnostics
                  if d.severity == 'error' and 'reserved GPPL function name' in d.message]
        self.assertEqual(errors, [])

    def test_variable_names_do_not_conflict_with_gppl_functions(self):
        """INDEPENDENT: SolidCAM rejects the `dist` local as invalid;
        function names must not be accepted as user variable names."""
        self.assert_valid_variable_names(pp_source())

    def test_original_inverse_feed_dist_name_is_rejected(self):
        """INDEPENDENT: replay the source rejected by SolidCAM, rather than
        trusting successful numeric execution in our interpreter."""
        # Recreate the actual compiler failure, including every use of the local.
        source = pp_source()
        self.assertIn('nSegmentLengthSquared', source)
        mutant = source.replace('nSegmentLengthSquared', 'dist')
        assert_detected(self, self.assert_valid_variable_names, mutant,
                        'original SolidCAM dist declaration conflict')

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
                for descriptor in format_descriptors(code):
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
        Removing an occurrence passes (allowlist, not an exact pin): G187 is
        PP-012. The subprogram, loop, G10 L2 and trig-macro output went in
        f5c74cd (PP-044, PP-045, PP-038)."""
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
        # 1 accumulates work offsets (PP-016/PP-017); 2 (the Fanuc trig macro) stops the post in
        # @usr_check_options.
        self.assertEqual(state['i4xindexmode'], 0, 'i4xIndexMode')
        self.assertEqual(state['cr1'], 'A', 'the rotary axis is A')
        self.assertEqual(state['cwo'], 'G', 'G54-style work offsets')
        self.assertIn(state['iprogendmode'], (1, 2), 'any other value silently omits the program end')
        self.assertEqual((state['ccb'], state['cce'], state['comb'], state['come']), (';', '', 'MSG("', '")'),
                         'Sinumerik comment and operator-message syntax')
        # @end_program would emit 'M06 T<n>' (change before select).
        self.assertIs(state['btoolchangeatend'], False, 'bToolChangeAtEnd')

    def test_safety_relevant_user_options(self):
        """INDEPENDENT: Sinumerik 828D syntax and the GPP's own option
        documentation: the shipped options select the only modes that are
        valid for this control (i4xIndexMode 0,
        G54 offsets, M30/M2 program end, ';' comments and MSG() messages, no
        tool change at end). The alternative modes are registered
        defects (PP-016/017) or stop the post
        (i4xIndexMode 2); this static guard is their practical protection."""
        self.assert_safe_options()

    def test_option_guard_detects_unsafe_values(self):
        """INDEPENDENT: mutation self-check; each unsafe option value must fail
        the guard with AssertionError."""
        mutants = {
            'i4xIndexMode 1': ('    i4xIndexMode          = 0 ', '    i4xIndexMode          = 1 '),
            'i4xIndexMode 2': ('    i4xIndexMode          = 0 ', '    i4xIndexMode          = 2 '),
            'iProgendmode 3': ('    iProgendmode          = 1 ', '    iProgendmode          = 3 '),
            'cR1 B': ("    cR1                   = 'A'", "    cR1                   = 'B'"),
        }
        for label, (old, new) in mutants.items():
            assert_detected(self, self.assert_safe_options, mutate(old, new), label)

    def test_user_options_that_have_no_effect_are_pinned(self):
        """CHARACTERIZATION: user options assigned in @usr_ip_useroptions that no
        statement reads; editing one changes nothing in the NC program. None is
        left (the Fanuc G84 strings, the gear and pallet options and the second
        rotary letter were deleted). bCoolofftc/bSpinofftc (PP-010) and
        i4xFeedMode (PP-049) are registered defects with their own canonical tests
        and are excluded, as are the blknum* block-numbering settings SolidCAM
        consumes itself. A new dead option fails."""
        self.assertEqual(options_without_consumers(pp_source()), set())

    def test_dead_option_pin_detects_a_new_consumer(self):
        """INDEPENDENT: mutation self-check; a new option nobody reads appears in
        the computed set, and disappears once a statement reads it."""
        option = "    cR1                   = 'A'"
        dead = mutate(option, option + "\n    cNewDead = 'X'")
        self.assertIn('cnewdead', options_without_consumers(dead))
        anchor = '\n@usr_check_smoothing\n'
        read = mutate(anchor, anchor + "    {nb, cNewDead}\n", source=dead)
        self.assertNotIn('cnewdead', options_without_consumers(read))


class StaticSourceTests(unittest.TestCase):
    def scan(self, source):
        problems = []
        lines = [uncomment(raw).strip() for raw in source.splitlines()]
        levels = [line for line in lines if re.match(r'trace_level\s*=', line, re.I)]
        if [re.sub(r'\s+', ' ', line) for line in levels] != ['trace_level = 0']:
            problems.append((None, 'trace_level is not set once to 0', levels))
        for number, line in enumerate(lines, 1):
            if re.match(r'trace\b', line, re.I):
                gated = (re.fullmatch(r"trace\s+(['\"])all\1\s*:\s*trace_level", line, re.I)
                         and re.fullmatch(r'if\s+trace_level\s*>\s*0', lines[number - 2], re.I))
                if not gated:
                    problems.append((number, 'active trace statement', line))
            if re.match(r'input\b', line, re.I) and 'POST ERROR' not in line:
                problems.append((number, 'interactive input prompt', line))
        self.assertEqual(problems, [])

    def test_no_active_trace_or_interactive_input(self):
        """INDEPENDENT: c8b79bd 'Disable postprocessor trace': an active GPPL
        trace writes '(n)@proc ==> ...' records into the NC file ('(' does not
        start a comment on Sinumerik, so the program alarms on load);
        revisions bff5ed0 and ab853be shipped with `trace "all":5` and no
        behaviour test executes @usr_ip_postwriteroptions. The only trace is
        `trace 'all':trace_level` under `if trace_level > 0`, with the post-writer
        option trace_level set once, to 0 (it also gates the CAMDBG readouts).
        `input` prompts are allowed only on the POST ERROR paths."""
        self.scan(pp_source())

    def test_c8b79bd_reversion_is_detected(self):
        """INDEPENDENT: mutation self-check; re-activating the trace (the
        c8b79bd reversion: trace_level 5, or the trace statement without its
        gate) must fail the scan with AssertionError."""
        level = '    trace_level           = 0 '
        gate = "    if trace_level > 0\n        trace 'all':trace_level\n    endif\n"
        for label, (old, new) in (('trace_level 5', (level, level.replace('= 0', '= 5'))),
                                  ('ungated trace', (gate, "    trace 'all':trace_level\n")),
                                  ('commented level', (level, '    ; trace_level = 0 '))):
            with self.subTest(mutant=label):
                assert_detected(self, self.scan, mutate(old, new), label)


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
# occurrence). Area E's fixture states that number as regression.count (default 1),
# which tests/test_history_regressions.py passes to support.mutation.mutate.


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
                expected = regression.get('count', 1)
                count = source.count(regression['find'])
                if count != expected:
                    problems.append((case['name'], f'anchor occurs {count} times, expected {expected}'))
        self.assertEqual(problems, [])


if __name__ == '__main__':
    unittest.main()
