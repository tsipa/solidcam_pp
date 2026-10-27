"""Engine harness: GPPL semantics of the test engine and the compatibility layer.

The engine is the one pp_tests/engine.py selects: the GPPL engine
(pp_tests/gppl) by default, the original engine (pp_tests/gppl/legacy.py) with
GPPL_ENGINE=legacy. Neither is edited by this suite. This file is the hand-off
to the engine track:

* Stock-engine gap tests (@known_defect('ENGINE-xxx')) assert the GPPL
  behaviour a faithful interpreter needs, on the unmodified
  pp_tests.engine.Engine with its default policies. Where the gap is a
  rejected construct, the UnsupportedGPPL is turned into an AssertionError
  (self.fail), because the rejection IS the registered defect. Default runs
  report them as skips; PP_STRICT_KNOWN_DEFECTS=1 runs them as plain failing
  tests; a fixed gap makes the default run fail with "no longer reproduces".
  Gaps the GPPL engine fixes (Defect.gppl_fixed) are known defects only under
  GPPL_ENGINE=legacy; on the GPPL engine the same test is a plain guard.
* EngineSemanticsPins pin the current engine rule for equal-value assignments
  (ENGINE-001, unverified against SolidCAM) so changing it is deliberate.
* Static guards over the GPP: every POST ERROR prompt is followed by abort
  (the engine cannot see a missing abort, ENGINE-009), and the GPP avoids the
  constructs the engine would evaluate with Python semantics without an error.
* GpplCompatEngine self-tests: each documented workaround behaves as
  described, and the default options are strictly additive (identical state,
  flags and NC text to the stock engine on flows the stock engine can run).
  The output-layer additivity guards and the line-by-line mirror of the legacy
  Engine._render always run against the legacy classes (LegacyCompatEngine
  and pp_tests.gppl.legacy.Engine), whichever engine is active.
"""
import difflib
import functools
import inspect
import re
import textwrap
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from pp_tests.gppl import legacy as legacy_engine

from support import (DRILL_DEFAULTS, LEGACY, WORKAROUNDS, GpplCompatEngine, LegacyCompatEngine, Session,
                     adopt_state, assert_detected, covers, fresh_engine, known_defect, motion_engine, mutate,
                     nc_text, parse_blocks, pp_source, rotary_engine)
from support.engines import declared_globals
from support.session import event


def run_stock(testcase, function, *args, gap=None):
    """Run an engine operation on the stock engine.

    gap is a regex for the UnsupportedGPPL message of the registered engine gap
    the test probes (the rejection IS the defect): a matching rejection becomes
    a test failure. Any other UnsupportedGPPL (and any rejection when gap is
    None) propagates as a test error, so an unrelated engine stop is never
    counted as reproducing the defect.
    """
    try:
        return function(*args)
    except UnsupportedGPPL as exc:
        if gap is None or not re.search(gap, str(exc)):
            raise
        testcase.fail(f'stock engine rejects the construct: {exc}')


# --------------------------------------------------------------------------
# Stock-engine gaps (ENGINE-xxx). Each test asserts the GPPL behaviour.
# --------------------------------------------------------------------------
class ScopeAndDeclarationGaps(unittest.TestCase):
    @known_defect('ENGINE-012', facet='redeclare')
    def test_local_redeclared_in_loop_restores_global(self):
        """INDEPENDENT: a local declaration shadows the global for the procedure
        call only; leaving the procedure restores the global value (t=42).
        UNVERIFIED: GPPL procedure scoping of locals is assumed (registry
        ENGINE-012 is uncertain). The engine re-saves the local's own value when
        `local numeric t` runs again in the loop, so t comes back as 5."""
        engine = Engine('@test\nlocal integer i\ni = 0\nwhile i < 2\nlocal numeric t\nt = 5\n'
                        'i = i + 1\nendw\nendp')
        engine.set(t=42)
        run_stock(self, engine.call, 'test')
        self.assertEqual(engine.state['t'], 42)

    @known_defect('ENGINE-012', facet='dynamic-scope')
    def test_callee_assignment_to_caller_local_name_reaches_global(self):
        """INDEPENDENT: with procedure-scoped locals a callee cannot see its
        caller's local k, so its assignment k = 99 writes the global.
        UNVERIFIED: GPPL procedure scoping is assumed (ENGINE-012 uncertain).
        The engine's flat state dict gives dynamic scope: the callee writes the
        caller's local and the write is discarded on return (k stays 0)."""
        engine = Engine('@test\nlocal numeric k\nk = 1\ncall @setk\nendp\n@setk\nk = 99\nendp')
        engine.set(k=0)
        run_stock(self, engine.call, 'test')
        self.assertEqual(engine.state['k'], 99)

    @known_defect('ENGINE-014')
    def test_declaration_with_initializer_is_not_silently_accepted(self):
        """INDEPENDENT: declared names must be identifiers (GPPL declaration
        syntax). `local numeric q = 5` must either be rejected (UnsupportedGPPL
        is the correct outcome here) or initialise q; the engine declares the
        names 'q', '=' and '5' and leaves q = 0."""
        engine = Engine('@test\nlocal numeric q = 5\nr = q\nendp')
        try:
            engine.call('test')
        except UnsupportedGPPL:
            return
        self.assertEqual(engine.state.get('r'), 5)

    @known_defect('ENGINE-005')
    def test_declared_global_has_change_flag(self):
        """INDEPENDENT: a declared GPPL variable has a change flag, so change(g)
        is defined. c03e1b4 shows a declared global starts with flag false and
        an equal-value assignment does not raise it (the first index lost its G0
        when iMotionmode = 0 re-assigned the default). The GPP reads change flags
        of declared globals this way (the removed @usr_HSM_mode did it for
        nG187_E_gpp); the engine raises 'change(g) was not supplied'."""
        engine = Engine('@test\nglobal numeric g\ng = 0\nc = change(g)\nendp')
        run_stock(self, engine.call, 'test', gap=r'change\(g\) was not supplied')
        self.assertIs(engine.state['c'], False)

    @known_defect('ENGINE-013')
    def test_integer_variable_does_not_hold_fraction(self):
        """INDEPENDENT: a GPPL integer variable holds a whole number, so
        500.4 stored in `local integer s` is 500 (truncated) or 500 (rounded),
        and s > 500 is false either way. UNVERIFIED: the GPPL integer
        assignment rule is not documented in the repository (ENGINE-013
        uncertain); the oracle holds under both truncation and rounding.
        @usr_spindle_output uses this pattern for its dwell decision."""
        engine = Engine('@test\nlocal integer s\ns = 500.4\nbig = s > 500\nendp')
        run_stock(self, engine.call, 'test')
        self.assertFalse(engine.state['big'])


class ExpressionGaps(unittest.TestCase):
    @known_defect('ENGINE-011')
    def test_python_only_syntax_is_rejected(self):
        """INDEPENDENT: pp_tests/README.md promises that unsupported expressions
        fail. GPPL has no hex literals, no string repetition, no chained
        comparisons and no negative-count left(); the engine maps them onto
        Python and silently returns 16, 'abab', True and 'ab'."""
        engine = Engine('')
        engine.set(a=3, b=2, c=1, s='ab')
        accepted = []
        for expression in ('0x10', 's * 2', 'a > b > c', "left('abc', -1)"):
            try:
                value = engine.expression(expression)
            except UnsupportedGPPL:
                continue
            accepted.append((expression, value))
        self.assertEqual(accepted, [], 'Python-only expressions evaluated without UnsupportedGPPL')

    @known_defect('ENGINE-006')
    def test_leading_zero_integer_literal(self):
        """INDEPENDENT: `07` is an integer literal in GPPL; the GPP ships it at
        @usr_coolant (iCoolantM5ON = 07, through-tool coolant 30 bar). Python's
        parser rejects leading zeros, so the engine stops on that path. (Whether
        7 is the right M-code is PP-008, not this test.)"""
        engine = Engine('@t\nvalue = 07\nendp')
        run_stock(self, engine.call, 't', gap='leading zeros')
        self.assertEqual(engine.state['value'], 7)

    @known_defect('ENGINE-007')
    def test_right_and_tostr_builtins(self):
        """INDEPENDENT: GPPL string built-ins used by shipped template code
        (@usr_sof_progname, @usr_US_date, @usr_US_time, @Multiple_Fixtures):
        right(s, n) is the last n characters ('' for n = 0) and tostr(v:'fmt')
        formats a number with the descriptor's decimals (7 with '5.0(p)' is
        '7'). The engine has neither built-in."""
        engine = Engine('')
        # right() is an unknown call node; tostr(v:'fmt') is a Python syntax error.
        results = {expression: run_stock(self, engine.expression, expression, gap=r"id='right'|invalid syntax")
                   for expression in ("right('abcdef', 2)", "right('abc-', 0)", "tostr(7:'5.0(p)')")}
        self.assertEqual(results, {"right('abcdef', 2)": 'ef', "right('abc-', 0)": '',
                                   "tostr(7:'5.0(p)')": '7'})

    @known_defect('ENGINE-010')
    def test_tonum_of_non_numeric_text_returns_zero(self):
        """INDEPENDENT: @home_number and @home_data rely on tonum() returning 0
        for text without a number: tonum(substr(home_user_name, ...)) is
        followed by `if iWorkoffset eq 0` fallbacks (try 'p', then position).
        That chain only works with atof-like tonum ('G5' -> 0, '55' -> 55);
        the engine raises for 'G5' (the GPPL engine has policy tonum=atof,
        not its default)."""
        results = {}
        for text in ('55', 'G5'):
            engine = Engine('@t\nvalue = tonum(text)\nendp')
            engine.set(text=text)
            run_stock(self, engine.call, 't',
                      gap=r'could not convert string to float|tonum\(\) of non-numeric string')
            results[text] = engine.state['value']
        self.assertEqual(results, {'55': 55, 'G5': 0})


class OutputGaps(unittest.TestCase):
    @known_defect('ENGINE-003')
    def test_numeric_def_f_formats_unformatted_numeric_variables(self):
        """INDEPENDENT: @init_post sets numeric_def_f = '8.5' (GPP line 53), the
        GPPL default format for numbers without a <name>_f format (drill
        locals rtp/rfp/sdis/dp, arc centres). The engine ignores it and prints
        three decimals ('V1.235' instead of 'V1.23456')."""
        engine = Engine("@test\nlocal numeric v\nv = 1.23456\n{'V'v}\nendp")
        engine.set(numeric_def_f='8.5')
        run_stock(self, engine.call, 'test')
        self.assertEqual(engine.output, ['V1.23456'])

    @known_defect('ENGINE-002')
    def test_skipline_false_joins_the_next_block(self):
        """INDEPENDENT: `skipline = false` makes the next nb continue the current
        block. The GPP joins `{nl,'N'iTcnumber' '}` with `{nb,'G17 G64 G90'}`
        this way (@usr_ct_before_firsttool) and the author's Mach3 template
        uses `{nb,'G'gcode,' '}` then `skipline = FALSE` in
        @relative_mode/@absolute_mode. The NC program is read from the
        engine's own NC view (support.engines.nc_text): the GPPL engine's NC
        stream joins (fixed there); the legacy engine treats skipline as a
        plain variable and always starts a new block."""
        engine = Engine("@test\n{nb,'G91 '}\nskipline = false\n{nb,'X1'}\nendp")
        run_stock(self, engine.call, 'test')
        blocks = [block.strip() for block in nc_text(engine).splitlines() if block.strip()]
        self.assertEqual(blocks, ['G91 X1'])

    @known_defect('ENGINE-015')
    def test_double_quoted_literal_escape_matches_expression_parser(self):
        """INDEPENDENT: internal consistency of the engine's two literal parsers.
        _render tokenises a double-quoted literal with doubled quotes inside
        without the escape ('say hi') while expression() applies it
        ('say "hi"'). Whichever literal
        model the engine track adopts (the dossier evidence favours no escape),
        output and expressions must agree."""
        engine = Engine('@test\n{"say ""hi"""}\nendp')
        run_stock(self, engine.call, 'test')
        self.assertEqual(engine.output, [engine.expression('"say ""hi"""')])

    @known_defect('ENGINE-018')
    def test_historical_formats_and_trace_statements_are_accepted(self):
        """INDEPENDENT: constructs shipped in GPP revisions that ran in SolidCAM
        must not stop the interpreter: '+8.5' (newshift_*_f, until the fixup round),
        tostr(...:'5.0(n)') ('5.0(n)', current @Multiple_Fixtures),
        '<(>5.3<)>' (nR1pos_f before c03e1b4), '5.4(*-1)' (zpos_f before
        6294822) and `trace "all":5` (active in bff5ed0..ab853be). Where the
        descriptor's decimal count is unambiguous the printed digits must use
        it; the (*k) modifier's exact meaning is left to the GPPL manual."""
        rejected = []
        for descriptor, digits in (('+8.5', '1.23456'), ('5.0(n)', '7'), ('<(>5.3<)>', '1.235'),
                                   ('5.4(*-1)', None)):
            engine = Engine("@t\n{'V'v:fmt}\nendp")
            engine.set(v=7 if digits == '7' else 1.23456, fmt=descriptor)
            try:
                engine.call('t')
            except UnsupportedGPPL as exc:
                rejected.append((descriptor, str(exc)))
                continue
            # The number must appear as a whole token ('1.235' must not be satisfied
            # by '1.2350' or '11.235'); the sign/wrapper characters around it are
            # left to the GPPL manual.
            if digits is not None and not re.search(r'(?<![\d.])' + re.escape(digits) + r'(?!\d)',
                                                    ''.join(engine.output)):
                rejected.append((descriptor, f'printed {engine.output!r}, expected the number {digits}'))
        engine = Engine('@t\ntrace "all":5\nx = 1\nendp')
        try:
            engine.call('t')
        except UnsupportedGPPL as exc:
            rejected.append(('trace "all":5', str(exc)))
        self.assertEqual(rejected, [])

    @known_defect('ENGINE-020', match="change flag of 'a' cleared")
    def test_expression_output_token_keeps_operand_change_flags(self):
        """INDEPENDENT: clear_change_after_gen clears the change flag of a
        variable that is output; '(a+1)' outputs a computed value, not a, so
        a's pending flag survives. UNVERIFIED: GPPL's rule for identifiers inside
        '(expr)' output tokens is undocumented here (ENGINE-020 uncertain);
        the GPP prints ((iWorkoffset-1)+i) and (tool_offset*2) this way. The
        engine clears every identifier found in the parentheses."""
        engine = Engine("@t\n{'X'(a+1)}\nendp")
        engine.set(a=1, clear_change_after_gen=1)
        engine.changed['a'] = True
        run_stock(self, engine.call, 't')
        self.assertEqual(engine.output, ['X2'])
        self.assertIs(engine.changed['a'], True, "change flag of 'a' cleared by the '(a+1)' output token")


class StatementGaps(unittest.TestCase):
    @known_defect('ENGINE-008')
    def test_print_statement_does_not_stop_the_post(self):
        """INDEPENDENT: `Print <expr>` is a GPPL statement (the GPP uses it for
        the index clearance warnings in @usr_4x_index); it shows a message and
        generation continues, so y = 1 runs. UNVERIFIED: where SolidCAM shows
        the message and that it never stops the post are assumed (ENGINE-008
        uncertain). The engine rejects Print as an unknown statement."""
        engine = Engine("@t\nPrint 'WARNING'\ny = 1\nendp")
        run_stock(self, engine.call, 't', gap='unsupported statement: Print')
        self.assertEqual(engine.state['y'], 1)

    @known_defect('ENGINE-009', facet='input-terminal', match='postprocessor stopped')
    def test_engine_input_prompt_is_not_terminal(self):
        """INDEPENDENT: GPPL `input` prompts for a value and generation
        continues; only `abort` terminates (the GPP's dummy_var idiom: it asks
        for a value it never uses, then aborts explicitly). The engine treats
        input as a terminal stop."""
        engine = Engine("@test\nx = 0\ninput 'value?' x\ny = 1\nendp")
        run_stock(self, engine.call, 'test', gap='postprocessor stopped: input')
        self.assertEqual(engine.state['y'], 1)

    @known_defect('ENGINE-019')
    def test_code_outside_procedures_is_reported(self):
        """INDEPENDENT: pp_tests/README.md: unknown statements fail with the
        source line. A statement outside @proc..endp is never executed by
        SolidCAM's call model, so the harness must report it instead of
        silently dropping it (the parser ignores such lines)."""
        for source in ('stray = 1\n@t\nendp', "@t\nendp\n{'X1'}\n"):
            try:
                Engine(source)
            except UnsupportedGPPL:
                continue
            self.fail(f'text outside procedures was silently ignored: {source!r}')


# --------------------------------------------------------------------------
# ENGINE-001: the current change-flag rule for equal-value assignments.
# --------------------------------------------------------------------------
class EngineSemanticsPins(unittest.TestCase):
    @covers('ENGINE-001')
    def test_system_variable_equal_assignment_keeps_flag(self):
        """CHARACTERIZATION (UNVERIFIED rule, ENGINE-001): an equal-value
        assignment to an undeclared (CAM/system) variable neither raises nor
        clears its flag; a value change raises it; output with
        clear_change_after_gen clears it. The arc end-point commit relies on
        the keep rule (`zpos = calculated_zpos` re-assigns the CAM value and Z
        must stay in a helix). Alternatives: uniform reset-on-equal (drops
        helical X/Y/Z from arcs) and H5 (declared variables reset, CAM
        variables keep). Settle with the 10-line SolidCAM probe in the registry."""
        engine = Engine('@t\nx=1\n{x}\nx=1\nendp\n@u\nx=2\nx=2\nendp\n@v\nchange(x)=true\nx=x\nendp')
        engine.set(clear_change_after_gen=1)
        engine.call('t')
        self.assertFalse(engine.changed['x'], 'output clears; equal assignment must not raise')
        engine.call('u')
        self.assertTrue(engine.changed['x'], 'different value raises; equal re-assignment keeps it')
        engine.changed['x'] = False
        engine.call('v')
        self.assertTrue(engine.changed['x'], 'explicit change(x)=true survives an equal assignment')

    @covers('ENGINE-001')
    def test_declared_variable_equal_assignment_keeps_flag(self):
        """CHARACTERIZATION (UNVERIFIED rule, ENGINE-001): the engine also keeps a
        stale TRUE flag of a GPP-declared variable across an equal assignment.
        Under this reading every first job of a flags='persist' session prints
        M8 followed by seven M9 (PP-054; also 'G187 P2' until the G187 output was
        removed). The alternative H5
        ('declared variables: change := new != old') passes the original suite
        and yields a clean program. A first-job SolidCAM trace decides; this pin
        makes the interpreter choice explicit."""
        engine = Engine('@init\nglobal integer i\ni=9\nendp\n@again\ni=9\nendp')
        engine.call('init')
        self.assertTrue(engine.changed['i'])
        engine.call('again')
        self.assertTrue(engine.changed['i'])


# --------------------------------------------------------------------------
# POST ERROR paths must abort (the engine cannot see a missing abort).
# --------------------------------------------------------------------------
def post_error_blocks(source):
    """Yield (procedure, line, statements-after) for every POST ERROR statement.

    statements-after are the lower-case statements following it in the same
    if/else block (up to the block's else/endif or the procedure end).
    """
    engine = fresh_engine(source)
    for name, lines in engine.procedures.items():
        for index, (number, line) in enumerate(lines):
            if 'POST ERROR' not in line:
                continue
            depth = 0
            following = []
            for _, statement in lines[index + 1:]:
                low = statement.lower()
                if low.startswith('if ') or low.startswith('while '):
                    depth += 1
                elif low in ('endif', 'endw') or (low == 'else' and depth == 0):
                    if depth == 0:
                        break
                    depth -= 1
                if depth == 0:
                    following.append(low)
            yield name, number, line, following


def without_abort_lines(source, keep=lambda index: False):
    lines = source.split('\n')
    return '\n'.join(line for index, line in enumerate(lines)
                     if line.strip().lower() != 'abort' or keep(index))


class PostAbortGuardTests(unittest.TestCase):
    def assert_post_errors_abort(self, source):
        found = list(post_error_blocks(source))
        self.assertGreaterEqual(len(found), 5, 'expected POST ERROR paths in usr_arc_check, usr_r1_output, '
                                'usr_arc_math (ZX arcs), usr_arc (compensation change on an arc) and '
                                'usr_line (a cutting block that turns A by 360 degrees or more)')
        for name, number, line, following in found:
            self.assertIn('abort', following, f'@{name}:{number}: POST ERROR statement is not followed by abort')

    def test_every_post_error_prompt_is_followed_by_abort(self):
        """INDEPENDENT: GPPL semantics: `input` prompts and generation continues,
        `abort` terminates. A POST ERROR prompt or NC text that is not followed
        by abort in the same block lets SolidCAM keep generating code after the
        error (ENGINE-009: the engine stops at input, so behaviour tests cannot
        see a deleted abort)."""
        self.assert_post_errors_abort(pp_source())

    def test_guard_detects_removed_abort(self):
        """INDEPENDENT: mutation self-check. Deleting any abort of the ten
        POST ERROR guards (@usr_arc_check, @usr_r1_output, the ZX arc stop of
        5408e5c in @usr_arc_math, the compensation-on-arc stop of b999f65, the
        full-turn cutting block stop of b94251b in @usr_line, the two option
        stops of @usr_check_options, @usr_unsupported_event, the homing mode
        stop of @usr_home_axis and the G187 smoothing stop of
        @usr_check_smoothing) must fail the guard with AssertionError."""
        lines = pp_source().split('\n')
        abort_lines = [index for index, line in enumerate(lines) if line.strip().lower() == 'abort']
        self.assertEqual(len(abort_lines), 10, 'abort sites changed; review the guard')
        for removed in abort_lines:
            mutant = '\n'.join(line for index, line in enumerate(lines) if index != removed)
            assert_detected(self, self.assert_post_errors_abort, mutant, f'abort at line {removed + 1} removed')

    @known_defect('ENGINE-009', facet='abort-observable', match='postprocessor stopped')
    def test_removed_abort_changes_observable_result(self):
        """INDEPENDENT: GPPL semantics: without `abort`, @usr_r1_output's invalid
        direction path prompts, writes the POST ERROR text and continues. On a
        GPP copy with every abort deleted the engine must therefore not report
        a stopped post; the stock engine stops at `input`, so the deleted abort
        is invisible to every behaviour test. Structural probe: iR1dirMode=0
        (the state an unknown CAM direction leads to) is preset directly on
        the legacy rotary harness."""
        engine = rotary_engine(without_abort_lines(pp_source()), iR1dirMode=0, nR1pos=90)
        run_stock(self, engine.call, 'usr_r1_output', gap='postprocessor stopped: input')


# --------------------------------------------------------------------------
# The GPP must avoid constructs the engine evaluates with Python semantics.
# --------------------------------------------------------------------------
_STRING = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
_COMPARE = r'(?:\b(?:eq|ne|gt|lt|ge|le)\b|==|!=|<=|>=|(?<![<>!=])[<>](?![=]))'


def _top_level(text):
    """Text outside parentheses, with string literals blanked."""
    text = _STRING.sub("''", text)
    depth, out = 0, []
    for character in text:
        if character == '(':
            depth += 1
        elif character == ')':
            depth -= 1
        elif depth == 0:
            out.append(character)
    return ''.join(out)


def _expression_part(low):
    if low.startswith('if '):
        return re.sub(r'\s+then$', '', low[3:])
    if low.startswith('while '):
        return low[6:]
    match = re.fullmatch(r'(?:change\(\w+\)|\w+)\s*=\s*(.+)', low)
    return match[1] if match else None


def silent_divergences(source):
    """[(rule, where)] for constructs the engine evaluates without UnsupportedGPPL
    but with Python semantics or dynamic scope (engine-impl-critic-08/09/11)."""
    engine = fresh_engine(source)
    found = []
    locals_by_proc, calls, names = {}, {}, {}
    for proc, lines in engine.procedures.items():
        loop_depth = 0
        locals_by_proc[proc] = set(engine.arguments[proc])
        calls[proc], names[proc] = set(), set()
        for number, line in lines:
            low = line.lower()
            where = f'@{proc}:{number}: {line}'
            if low.startswith('while '):
                loop_depth += 1
            elif low == 'endw':
                loop_depth -= 1
            declaration = re.fullmatch(r'(local|global) (numeric|integer|logical|string) (.+)', low)
            if declaration:
                declared = declaration[3].replace(',', ' ').split()
                if any(not re.fullmatch(r'[a-z_]\w*', name) for name in declared):
                    found.append(('declaration initializer/invalid name', where))
                if declaration[1] == 'local':
                    locals_by_proc[proc].update(declared)
                    if loop_depth:
                        found.append(('local declared inside while', where))
                continue
            calls[proc].update(re.findall(r'call @(\w+)', low))
            names[proc].update(re.findall(r'\b[a-z_]\w*\b', _STRING.sub("''", low)))
            if line.startswith('{'):
                blanked = _STRING.sub('S', line)
                depth = 0
                for character in blanked:
                    depth += character == '['
                    if depth > 1:
                        found.append(('nested modal group', where))
                        break
                    depth -= character == ']'
                for literal in re.findall(r'"(?:[^"]|"")*"', line):
                    if '""' in literal[1:-1]:
                        found.append(('doubled quote in double-quoted output literal', where))
                continue
            expression = _expression_part(low)
            if expression is None:
                continue
            flat = _top_level(expression)
            if re.search(r'\band\b', flat) and re.search(r'\bor\b', flat):
                found.append(('mixed and/or without parentheses', where))
            if len(re.findall(_COMPARE, flat)) > 1 and not re.search(r'\b(?:and|or)\b', flat):
                found.append(('chained comparison', where))
            if re.search(r'!\s*\w+(?:\([^()]*\))?\s*' + _COMPARE, _STRING.sub("''", expression)):
                found.append(('negation applied to a comparison operand', where))
            if re.search(r'(?<![\w.])0(?:[xob]\w|\d+(?![\d.]))', _STRING.sub("''", expression)):
                found.append(('non-decimal or leading-zero literal', where))

    def reach(proc, seen):
        for callee in calls.get(proc, ()):
            if callee in engine.procedures and callee not in seen:
                seen.add(callee)
                reach(callee, seen)
        return seen

    for proc, local_names in locals_by_proc.items():
        for callee in reach(proc, set()):
            shared = (names[callee] & local_names) - locals_by_proc[callee]
            if shared:
                found.append(('caller local visible to callee (engine uses dynamic scope)',
                              f'@{proc} -> @{callee}: {sorted(shared)}'))
    return found


# The 07 literal is a LOUD engine gap (ENGINE-006: UnsupportedGPPL on the stock
# engine, handled by GpplCompatEngine), not a silent divergence.
KNOWN_LOUD = {('non-decimal or leading-zero literal', 'iCoolantM5ON = 07')}


class EngineAssumptionGuardTests(unittest.TestCase):
    def assert_clean(self, source):
        problems = [(kind, where) for kind, where in silent_divergences(source)
                    if not any(kind == known and where.endswith(text) for known, text in KNOWN_LOUD)]
        self.assertEqual(problems, [], 'GPP uses constructs the engine evaluates with non-GPPL semantics')

    def test_current_gpp_avoids_silently_divergent_constructs(self):
        """INDEPENDENT: engine source analysis (ENGINE-011/012/014/015): these
        constructs run under Python semantics or dynamic scope without any
        UnsupportedGPPL, so a GPP edit introducing one could change real
        behaviour while every behaviour test stays green. None occurs today."""
        self.assert_clean(pp_source())

    def test_guard_detects_each_construct(self):
        """INDEPENDENT: mutation self-check; each injected construct must fail
        the guard with AssertionError."""
        anchor = '    bCamLinkRapid = false\n'
        injections = {
            'mixed and/or': '    if X5_job or bTlchg and bFirstRapid\n        bCamLinkRapid = false\n    endif\n',
            'chained comparison': '    if 0 < zpos < 10\n        bCamLinkRapid = false\n    endif\n',
            'negated comparison operand': '    if !bTlchg eq bFirstRapid\n        bCamLinkRapid = false\n    endif\n',
            'nested modal group': "    {['G'iMotionmode ['X'xpos]]}\n",
            'local inside while': '    while false\n        local numeric zz\n    endw\n',
            'declaration initializer': '    local numeric zz = 5\n',
            'hex literal': '    bCamLinkRapid = 0x0\n',
        }
        for name, text in injections.items():
            assert_detected(self, self.assert_clean, mutate(anchor, anchor + text), name)
        caller = '\n@usr_line\n'
        assert_detected(self, self.assert_clean, mutate(caller, caller + '    local numeric nR2pos\n'),
                        'dynamic scope')


# --------------------------------------------------------------------------
# GpplCompatEngine: documented workarounds and their additivity.
# --------------------------------------------------------------------------
class GpplCompatEngineTests(unittest.TestCase):
    def test_workaround_switches_cite_engine_gaps(self):
        """INDEPENDENT: tests/support/engines.py contract: every workaround
        switch is a constructor option, and only the five additive ones are on
        by default."""
        engine = GpplCompatEngine('')
        self.assertEqual(set(engine.options), set(WORKAROUNDS))
        self.assertEqual({name for name, value in engine.options.items() if value},
                         {'leading_zero_literals', 'string_builtins', 'print_statement',
                          'trace_statement', 'extended_formats'})

    @covers('ENGINE-006', 'ENGINE-007')
    def test_setup_engine_builtins(self):
        """INDEPENDENT: GPPL semantics of the literal and built-ins the stock
        legacy engine rejects: 07 is 7; right(s, n) is the last n characters, ''
        for n <= 0 (Python's s[-0:] would return everything and make
        @usr_sof_progname loop); tostr(v[:'fmt']) uses the descriptor's
        decimals, the default numeric format without one, and returns strings
        unchanged. The default numeric format of tostr(v) is numeric_def_f on
        LegacyCompatEngine and needs default_formats=True (typed_default_formats,
        ENGINE-003) on the GPPL engine. right(s, n) for n > len(s) is
        test_right_count_beyond_the_string_returns_the_whole_string (ENGINE-021)."""
        options = {} if LEGACY else {'default_formats': True}
        engine = GpplCompatEngine('', **options)
        engine.set(numeric_def_f='8.5')
        cases = {'07': 7, '-05 + 1': -4, "right('abcdef', 2)": 'ef', "right('abc-', 0)": '',
                 "right('abc', -1)": '', "right('abc', 3)": 'abc', "tostr(7:'5.0(p)')": '7',
                 'tostr(2.5)': '2.5', 'tostr(1.234567)': '1.23457', "tostr('x')": 'x',
                 "'07' + tostr(3:'5.0(n)')": '073'}
        self.assertEqual({expression: engine.expression(expression) for expression in cases}, cases)

    @covers('ENGINE-021')
    def test_right_count_beyond_the_string_returns_the_whole_string(self):
        """INDEPENDENT: GPPL right(s, n) returns the last n characters of s, so a
        count larger than the string is the whole string (LegacyCompatEngine
        clamps). The GPPL engine's right() sliced s[len(s) - n:], a negative Python
        index for n > len(s) ('bc' for right('abc', 5)); fixed, this guards it. No
        GPP call reaches it (@usr_sof_progname passes at most strlen - 1)."""
        engine = GpplCompatEngine('')
        self.assertEqual(engine.expression("right('abc', 5)"), 'abc')

    @covers('ENGINE-008', 'ENGINE-018')
    def test_print_and_trace_statements_continue(self):
        """INDEPENDENT: GPPL `Print` shows a message and continues (UNVERIFIED
        assumption, ENGINE-008); `trace` is a debug directive without NC
        effect in the interpreter (ENGINE-018). LegacyCompatEngine keeps a
        message with commas as an assignment (gppl_print_log) because the legacy
        call parser splits on every comma; the GPPL engine records every Print
        (policy print_stmt=console)."""
        engine = GpplCompatEngine('@t\nPrint \'first\'\ntrace "all":5\nPrint \'a, b\'\ny = 1\nendp')
        engine.call('t')
        if LEGACY:
            self.assertEqual((engine.messages, engine.state['y'], engine.state['gppl_print_log']),
                             (['first'], 1, 'a, b'))
        else:
            self.assertEqual((engine.messages, engine.state['y']), (['first', 'a, b'], 1))
        self.assertEqual(fresh_engine('@t\nPrint \'x\'\nendp', GpplCompatEngine).messages, [])

    @covers('ENGINE-018')
    def test_extended_format_descriptors(self):
        """INDEPENDENT: support/engines.py documents the extended grammar:
        <prefix>/<suffix> literals, '+' always prints the sign, (n)/(p) do not
        change the digits, (*k) multiplies the value. Stock descriptors render
        exactly like the stock engine (three decimals by default, trailing
        zeros stripped, '-0' printed as '0')."""
        engine = GpplCompatEngine('')
        cases = [(1.5, '+8.5', '+1.5'), (-1.5, '+8.5', '-1.5'), (1.23456, '<(>5.3<)>', '(1.235)'),
                 (3, '5.4(*-1)', '-3'), (7, '5.0(n)', '7'), (2.0, '4.4(P)', '2'), (-0.0004, '7.3', '0'),
                 (1.23456, None, '1.235')]
        self.assertEqual([engine.format_number(value, descriptor) for value, descriptor, _ in cases],
                         [expected for _, _, expected in cases])
        with self.assertRaises(UnsupportedGPPL):
            GpplCompatEngine('', extended_formats=False).format_number(1.0, '+8.5')

    @covers('ENGINE-002', 'ENGINE-003', 'ENGINE-005')
    def test_opt_in_emulations(self):
        """INDEPENDENT: the opt-in switches emulate the GPPL semantics asserted
        by the ENGINE-002/003/005 gap tests: skipline=False joins exactly one
        following block (read from the engine's NC view, nc_text()),
        numeric_def_f/integer_def_f format unformatted numbers, declared globals
        get a false change flag (legacy: when a top-level call returns; GPPL
        engine: when the declaration runs). With the switches off the legacy
        behaviour is kept."""
        source = "@test\n{nb,'G91 '}\nskipline = false\n{nb,'X1'}\n{nb,'Y2'}\nendp"
        joined = GpplCompatEngine(source, skipline=True)
        joined.call('test')
        default = GpplCompatEngine(source)
        default.call('test')
        self.assertEqual([b.strip() for b in nc_text(joined).splitlines() if b.strip()], ['G91 X1', 'Y2'])
        self.assertEqual([b.strip() for b in nc_text(default).splitlines() if b.strip()], ['G91', 'X1', 'Y2'])

        formats = "@test\nglobal integer n\nlocal numeric v\nv = 1.23456\nn = 1250\n{'V'v,' S'n}\nendp"
        for options, expected in (({'default_formats': True}, 'V1.23456 S1250'), ({}, 'V1.235 S1250')):
            engine = GpplCompatEngine(formats, **options)
            engine.set(numeric_def_f='8.5', integer_def_f='5.0(p)')
            engine.call('test')
            self.assertEqual(engine.output, [expected], options)

        flags = '@init\nglobal numeric g\nendp\n@t\nc = change(g)\nendp'
        engine = GpplCompatEngine(flags, declared_global_flags=True)
        engine.call('init')
        engine.call('t')
        self.assertIs(engine.state['c'], False)
        stock_like = GpplCompatEngine(flags)
        stock_like.call('init')
        with self.assertRaises(UnsupportedGPPL):
            stock_like.call('t')

    @covers('ENGINE-007')
    def test_compat_runs_us_date_and_time_conversion(self):
        """INDEPENDENT: US date order (Mon-DD-YYYY) and 12-hour clock rules
        (00:30 is 12:30AM, 12:00 is 12:00PM); @usr_US_date/@usr_US_time need
        right() and tostr(v:'fmt'), which only the workaround provides.
        CHARACTERIZATION of the layout only: no leading zero on the hour and the
        AM/PM suffix without a blank are the GPP's own format choice."""
        engine = Session().engine
        times = []
        for clock in ('14:05:09', '00:30:00', '12:00:00', '09:15:00'):
            engine.set(time=clock)
            engine.call('usr_US_time')
            times.append(engine.state['sus_time'])
        engine.set(date='26-Oct-2026')
        engine.call('usr_US_date')
        self.assertEqual((times, engine.state['sus_date']),
                         (['2:05:09PM', '12:30:00AM', '12:00:00PM', '9:15:00AM'], 'Oct-26-2026'))

    @covers('ENGINE-006')
    def test_compat_evaluates_the_through_coolant_literal(self):
        """INDEPENDENT: GPPL integer literal semantics: the literal @usr_coolant
        assigns for through-tool coolant 30 bar (`iCoolantM5ON = 07` today) is
        a decimal integer, so the path runs and stores int(literal, 10). The
        expected value is read from the GPP line, not pinned: whether 07 is the
        right M-code is PP-008 (area A), and fixing it to 70 must not trip this
        workaround check."""
        procedure = fresh_engine().procedures['usr_coolant']
        statements = [line for _, line in procedure]
        branch = statements.index('if through_coolant_val eq 30')
        literal = re.fullmatch(r'iCoolantM5ON\s*=\s*(\d+)', statements[branch + 1])
        self.assertIsNotNone(literal, f'30 bar branch changed: {statements[branch + 1]!r}')
        session = Session(through_ival_coolant=1, through_coolant_val=30)
        session.engine.call('usr_coolant')
        self.assertEqual(session.state['icoolantm5on'], int(literal[1], 10))

    @covers('ENGINE-008')
    def test_compat_print_lets_the_index_warning_continue(self):
        """INDEPENDENT: GPPL Print semantics (UNVERIFIED assumption, ENGINE-008):
        the @usr_4x_index clearance warning (i4xIndexClearanceMode=1, tool Z
        level below the start plane) is recorded and the index still rotates
        A. Whether the warning text also belongs in the NC file is PP-039."""
        # Print records its argument: the expected message is the literal of the
        # first Print statement of @usr_4x_index (read from the GPP, not pinned).
        prints = [re.fullmatch(r"Print\s+'([^']*)'", line, re.I) for _, line in
                  fresh_engine().procedures['usr_4x_index_rotate']]
        expected = [match[1] for match in prints if match][:1]
        self.assertEqual(len(expected), 1, '@usr_4x_index_rotate has no Print statement')
        session = Session(options={'i4xIndexClearanceMode': 1}, tool_z_level=20, tool_start_plane=35,
                          nPtool_z_level=40)
        text = event(session.engine, 'usr_4x_index', angle_4x_around_x=90)
        self.assertEqual(session.engine.messages, expected)
        self.assertEqual([block.rotary('A')[1] for block in parse_blocks(text) if block.rotary('A')], [90])


def _program_flow(engine_class, flags):
    """A representative two-tool program the stock engine can run.

    Structural engine-contract input: both engines receive the same event
    stream, so the oracle does not depend on how faithfully the stream models
    SolidCAM. The events are still kept consistent (the arc starts at the
    current tool position, tmatrix comes between jobs).
    """
    session = Session(engine_class=engine_class, flags=flags)
    session.first_tool(tool=1, next_tool=2)
    session.cut(10, 20, 5, -3, apos=30)
    session.ev('move_5x', ('xpos', 'ypos'), xpos=10, ypos=0, zpos=5)
    session.ev('line_5x', ('zpos',), zpos=-3, feed_type='feed_cut')
    session.ev('arc', ('xpos', 'ypos', 'feed'), arc_plane='xy', arc_direction='ccw', arc_size=90, radius=10,
               xstart=10, ystart=0, zstart=-3, xcenter=0, ycenter=0, zcenter=-3, xcenter_rel=-10,
               ycenter_rel=0, zcenter_rel=0, xpos=0, ypos=10, zpos=-3, feed=300)
    session.next_tool(2, 3, tmatrix=90)
    for drill_type in ('g81', 'g82', 'g83', 'g84', 'g86'):
        session.ev('drill', ('xpos', 'ypos'), drill_type=drill_type, xpos=5, ypos=6, **DRILL_DEFAULTS)
        session.ev('drill_point', ('xpos', 'ypos'), xpos=7, ypos=8)
        session.ev('end_drill')
    session.next_tool(3, 3, last_tool=True)
    session.cut(15, 25, 5, -2)
    session.ev('end_of_job')
    session.ev('end_program')
    return session


def _normalized_source(function):
    lines = textwrap.dedent(inspect.getsource(function)).splitlines()
    return [line.rstrip() for line in lines if line.strip() and not line.strip().startswith('#')]


class CompatAdditivityTests(unittest.TestCase):
    """Default GpplCompatEngine options must not change any result the stock
    engine already produces (tests/support/engines.py workaround policy)."""

    def run_compat(self, function, *args, **kwargs):
        """Run a compat-engine step; any exception where the stock engine ran
        is an additivity violation, reported as a test failure."""
        try:
            return function(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - every compat-only exception is a violation
            self.fail(f'GpplCompatEngine fails where the stock engine runs: {exc!r}')

    def assert_same_engine_result(self, stock, compat, label):
        self.assertEqual(compat.state, stock.state, f'{label}: state differs')
        self.assertEqual(compat.changed, stock.changed, f'{label}: change flags differ')
        self.assertEqual(compat.output, stock.output, f'{label}: output differs')

    @covers('ENGINE-006', 'ENGINE-007', 'ENGINE-008', 'ENGINE-018')
    def test_default_options_reproduce_stock_sessions(self):
        """INDEPENDENT: additivity contract of the default workarounds: a whole
        program (tool changes, tmatrix index, rotary cut, arc, CYCLE81..86,
        program end) gives identical NC text per event, state and change flags
        on the stock engine and on GpplCompatEngine, under both flag policies."""
        for flags in ('clear', 'persist'):
            stock = _program_flow(Engine, flags)
            compat = self.run_compat(_program_flow, GpplCompatEngine, flags)
            self.assertEqual(compat.log, stock.log, f'flags={flags}: NC text per event differs')
            self.assertEqual(compat.state, stock.state, f'flags={flags}: state differs')
            self.assertEqual(compat.engine.changed, stock.engine.changed, f'flags={flags}: change flags differ')
            self.assertGreater(len(parse_blocks(stock.text())), 80)

    def test_default_options_reproduce_legacy_harness_flows(self):
        """INDEPENDENT: additivity contract on the legacy mid-job presets: the
        rotary procedures over positive/negative/whole-turn angles and the
        motion procedures (rapid, feed, 4x feed) give identical results when the
        same preset is adopted by GpplCompatEngine."""
        for apos in (0, 30, -30, 90, 180, 270, 359.9996, 360, -360, 725):
            for direction in ('cw', 'ccw'):
                stock = rotary_engine(apos=apos, dir5a=direction, nPR1pos=45, nR1pos=45)
                stock.changed.update({key: False for key in stock.state})
                compat = self.run_compat(adopt_state, stock, pp_source(), GpplCompatEngine)
                for engine in (stock, compat):
                    call = engine.call if engine is stock else functools.partial(self.run_compat, engine.call)
                    call('usr_r1pos_calc')
                    call('usr_r1_select_dir')
                    if engine.state['ir1dirmode'] in (1, 2, 3):
                        call('usr_r1_output')
                self.assert_same_engine_result(stock, compat, f'apos={apos} dir5a={direction}')
        stock = motion_engine()
        compat = self.run_compat(adopt_state, stock, pp_source(), GpplCompatEngine)
        steps = [('move_5x', dict(xpos=40, ypos=5, zpos=30, apos=90), ('xpos', 'ypos', 'zpos', 'apos')),
                 ('line_5x', dict(zpos=-2, feed=250), ('zpos', 'feed')),
                 ('line_5x', dict(xpos=60), ('xpos',)),
                 ('line_4x', dict(cpos=45, feed=120), ('cpos', 'feed')),
                 ('rapid_move', dict(zpos=35), ('zpos',))]
        for procedure, values, changed in steps:
            event(stock, procedure, changed, **values)
            self.run_compat(event, compat, procedure, changed, **values)
            self.assert_same_engine_result(stock, compat, procedure)

    def test_render_matches_stock_on_supported_output(self):
        """INDEPENDENT: additivity contract at the output layer: every output
        body the legacy _render accepts renders to the same fragment and the
        same variable set in LegacyCompatEngine (numbers with and without formats,
        ties, negative zero, logicals, both quote kinds, modal groups,
        parenthesised expressions, nb/nl). Runs on the legacy classes under
        either engine (the GPPL engine has no _render(body))."""
        bodies = ["'V'v", "'V'v:'5.3'", "'V'v:fmt", "nb,'G'g:'2.0(p)',' '", "['X'x' '],['Y'y]",
                  "(v*2),' ',(g+1):'5.0(p)'", '"dq",\'sq\'', "'it''s',nl", 'flag', "'S'v:'5.0'"]
        values = [0, 3, -3, 1.23456, 2.5, 3.5, 0.125, -0.0004, 1250.5, 10.0, True, 'txt']
        compared = rejected = 0
        for body in bodies:
            for value in values:
                for fmt in (None, '8.5', '4.4(P)', '5.0(p)', '+8.5'):
                    state = dict(v=value, g=17, x=1.5, y=-2, flag=False, fmt=fmt or '5.3')
                    if fmt:
                        state['v_f'] = fmt
                    stock, compat = legacy_engine.Engine(''), LegacyCompatEngine('')
                    for engine in (stock, compat):
                        engine.set(**state)
                        engine.changed.update(x=True, y=False)
                    try:
                        expected = stock._render(body)
                    except (legacy_engine.UnsupportedGPPL, TypeError):
                        rejected += 1
                        continue
                    compared += 1
                    self.assertEqual(self.run_compat(compat._render, body), expected,
                                     f'body={body!r} v={value!r} v_f={fmt!r}')
        self.assertGreater(compared, 400)
        self.assertGreater(rejected, 0)

    def test_render_mirror_differs_only_in_the_documented_hooks(self):
        """INDEPENDENT: tests/support/engines.py states LegacyCompatEngine._render
        mirrors pp_tests.gppl.legacy.Engine._render line by line except for the
        _newline() and format_number() hooks. Any other difference (for example
        an edit of the legacy Engine._render) fails here and the mirror must
        be updated; format_number must keep the stock descriptor grammar and
        number formatting."""
        stock = _normalized_source(legacy_engine.Engine._render)
        compat = _normalized_source(LegacyCompatEngine._render)
        removed, added = [], []
        for line in difflib.ndiff(stock, compat):
            if line.startswith('- '):
                removed.append(line[2:].strip())
            elif line.startswith('+ '):
                added.append(line[2:].strip())
        self.assertEqual(removed, [
            "result += '\\n'",
            "descriptor = descriptor or self.state.get(token.lower() + '_f')",
            'precision = 3',
            'if descriptor:',
            "fmt = re.fullmatch(r'\\d+\\.(\\d+)(?:\\([pP]\\))?', descriptor)",
            'if not fmt:',
            "raise UnsupportedGPPL(f'unsupported numeric format: {descriptor}')",
            'precision = int(fmt[1])',
            "value = format(value, f'.{precision}f')",
            'if precision:',
            "value = value.rstrip('0').rstrip('.')",
            "if value == '-0':",
            "value = '0'"])
        self.assertEqual(added, [
            'result += self._newline()',
            "descriptor = (descriptor or self.state.get(token.lower() + '_f')",
            'or self._default_descriptor(token, value))',
            'value = self.format_number(value, descriptor)'])
        formatter = inspect.getsource(LegacyCompatEngine.format_number)
        for fragment in (r"re.fullmatch(r'\d+\.(\d+)(?:\([pP]\))?', descriptor)", "format(value, f'.{precision}f')",
                         "rstrip('0').rstrip('.')", "== '-0'"):
            self.assertIn(fragment, formatter)

    def test_declared_globals_helper_matches_the_parser(self):
        """INDEPENDENT: GPPL declaration syntax; declared_globals() (used by the
        declared_global_flags and default_formats options) must find every name
        a `global <type>` statement of the GPP declares, with its type."""
        declared = declared_globals(pp_source())
        self.assertEqual((declared['imotionmode'], declared['btlchg'], declared['cwo'], declared['nlastpathz']),
                         ('integer', 'logical', 'string', 'numeric'))
        engine = fresh_engine()
        engine.call('init_post')
        self.assertEqual(sorted(set(declared) - set(engine.state)), [])


if __name__ == '__main__':
    unittest.main()
