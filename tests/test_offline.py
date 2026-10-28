"""Original offline tests: rotary procedure unit tests and engine harness checks.

Every test docstring names its oracle (INDEPENDENT or CHARACTERIZATION; the
meta-test tests/test_known_defect_registry.py checks it). The rotary unit tests run single
procedures on the legacy rotary_engine() preset; whole-program rotary
behaviour, the reversion guards and the canonical known-defect tests
(PP-002 modulo range, PP-004 iR1dir, PP-037 shortest distance, ...) live in
tests/test_rotary.py.

ROOT, PP and rotary_engine stay importable from here: test_motion,
test_history_regressions, test_arcs and test_arc_link_boundary import them.
"""
import json
import os
import unittest
from pathlib import Path

from pp_tests.engine import Engine, UnsupportedGPPL
from pp_tests.trace import parse_trace, sanitize

ROOT = Path(__file__).resolve().parents[1]
PP = Path(os.environ.get('PP_TEST_SOURCE', ROOT / 'siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.gpp'))


# Legacy rotary harness; single definition lives in tests/support/legacy.py (cached parse).
from support.legacy import rotary_engine  # noqa: E402,F401  (re-exported)
from support.engines import adopt_state, fresh_engine  # noqa: E402
from support.markers import covers  # noqa: E402
from support.mutation import mutate  # noqa: E402
from support.nc import parse_blocks  # noqa: E402

SLIDE_STATE_KEYS = {'angle_4x_around_x', 'angle', 'cpos', 'apos', 'bpos', 'x_angle_const_z'}


def rotary_words(engine):
    """[(mode, value)] of the A words an engine has emitted."""
    return [block.rotary('A') for block in parse_blocks(''.join(engine.output))
            if block.rotary('A') is not None]


class PostprocessorTests(unittest.TestCase):
    def test_actual_user_options(self):
        """CHARACTERIZATION of the shipped rotary options every rotary test assumes:
        iR1dir=-1, cR1='A' (GPP @usr_ip_useroptions). iR1dir=-1 agrees with the
        recorded shit2 data (apos 3.035 posted as A=ACP(3.035)). This pin is also
        the practical guard against shipping the non-default option behind PP-004
        (iR1dir=+1)."""
        engine = fresh_engine()
        engine.call('usr_ip_useroptions')
        self.assertEqual(engine.state['ir1dir'], -1)
        self.assertEqual(engine.state['cr1'], 'A')

    def test_positive_angles_and_boundaries(self):
        """INDEPENDENT: modulo arithmetic of the modulo A axis with
        iR1dir=-1: the machine A is apos reduced into [0, 360), so whole turns
        (+/-360) post 0 (fixed in 6228b3d, PP-002 facet whole-turn; the guards
        for every emitted A word are in tests/test_rotary.py and
        tests/test_rotary_modulo_range.py)."""
        for angle, expected in [(-359.999, .001), (-90, 270), (0, 0),
                                (90, 90), (359.999, 359.999), (-360, 0), (360, 0)]:
            with self.subTest(angle=angle):
                engine = rotary_engine(apos=angle)
                engine.call('usr_r1pos_calc')
                self.assertAlmostEqual(engine.state['nr1pos'], expected)

    def test_combines_coordinate_transform_cpos_and_simultaneous_angle(self):
        """CHARACTERIZATION of the GPP @usr_r1pos_calc composition: CoordSys
        (tmatrix), 4x-transform, cpos and apos angles add up with the same sign
        (30 + 20 + 10 + 5 = 65 with iR1dir=-1). Only the apos sign is backed by
        recorded data (shit2, slide); no trace has a non-zero CoordSys, transform
        or cpos angle, so their sign is the GPP's convention."""
        engine = rotary_engine(angle_4x_around_x=30, angle=20, cpos=10, apos=5)
        engine.call('usr_r1pos_calc')
        self.assertEqual(engine.state['nr1pos'], 65)

    def test_removed_position_modes_change_nothing(self):
        """INDEPENDENT: the A axis is modulo (program range 0 <= A < 360); the post has
        no other position mode. A leftover iR1posControl setting of the removed modes
        (0 SolidCAM direct, 2 negative, 3 shortest) must post the modulo position."""
        for control in (0, 2, 3):
            for apos, expected in ((90, 90), (-90, 270), (370, 10)):
                engine = rotary_engine(apos=apos, iR1posControl=control)
                engine.call('usr_r1pos_calc')
                self.assertAlmostEqual(engine.state['nr1pos'], expected, msg=f'iR1posControl={control} apos={apos}')

    def test_first_rotation_dc_then_direction_and_unchanged(self):
        """INDEPENDENT: ab853be (the first A word after a forced output is DC and
        clears the force), bff5ed0 (later moves carry a direction; dir5a 'ccw' is
        ACP per the recorded shit2 data) and the change rule (an unchanged target
        raises no change flag and selects no direction)."""
        engine = rotary_engine(apos=-90, bR1forceOutput=True)
        engine.call('usr_r1pos_calc')
        engine.call('usr_r1_output')
        self.assertEqual(engine.output, ['A=DC(270) '])
        self.assertFalse(engine.state['br1forceoutput'])
        engine.set(apos=-80, dir5a='ccw')
        engine.call('usr_r1pos_calc')
        engine.call('usr_r1_output')
        self.assertEqual(engine.output[-1], 'A=ACP(280) ')
        engine.call('usr_r1pos_calc')
        self.assertFalse(engine.changed['nr1pos'])
        self.assertEqual(engine.state['ir1dirmode'], 0)

    def test_clockwise_output(self):
        """INDEPENDENT: dir5a 'cw' (decreasing apos, mirror of the recorded ccw -> ACP)
        is posted as ACN (bff5ed0)."""
        engine = rotary_engine(apos=90)
        engine.call('usr_r1pos_calc')
        engine.call('usr_r1_output')
        self.assertEqual(engine.output, ['A=ACN(90) '])

    def test_3axis_suppresses_rotary_change(self):
        """INDEPENDENT: meaning of the VMID machine parameter bLimit_3axis: no A word. A bpos only
        selects the head homing; a CAM A turn stops the post (owner rule 2026-10-28). (The forced
        initial DC that still prints is PP-036, test_rotary.)"""
        engine = rotary_engine(bpos=15, bLimit_3axis=True)
        engine.call('usr_r1pos_calc')
        self.assertFalse(engine.changed['nr1pos'])
        engine = rotary_engine(apos=90, bLimit_3axis=True)
        with self.assertRaises(UnsupportedGPPL):
            engine.call('usr_r1pos_calc')

    def test_tmatrix_invalidates_clearance(self):
        """INDEPENDENT: @tmatrix intent ('Conservatively require clearance even when
        only the translation changed', d5952a2/37ab3b9): a CoordSys change cancels any
        CAM-link authorization and makes the next index pending with clearance."""
        engine = fresh_engine()
        engine.set(bCamLinkRetract=True, bIndexClearancePending=False, bTmatrixIndexPending=False)
        engine.call('tmatrix')
        self.assertTrue(engine.state['bindexclearancepending'])
        self.assertTrue(engine.state['btmatrixindexpending'])
        self.assertFalse(engine.state['bcamlinkretract'])

    @covers('ENGINE-009')
    def test_invalid_direction_is_not_silently_emitted(self):
        """CHARACTERIZATION of the stock engine's abort model (ENGINE-009): with no
        direction mode selected @usr_r1_output must stop the post with its POST ERROR
        and print no A word. The stock engine treats `input` as a terminal stop and
        raises UnsupportedGPPL carrying the prompt; with GPPL semantics (`input`
        prompts and continues, `abort` ends generation) the POST ERROR line is printed
        and `abort` stops. Both are accepted: 'POST ERROR' must appear in the stop
        message or in the output, and nR1pos is supplied because that error line
        reads it. Known gap: deleting only `abort` still passes (ENGINE-009)."""
        engine = rotary_engine(iR1dirMode=0, nR1pos=90)
        with self.assertRaises(UnsupportedGPPL) as stop:
            engine.call('usr_r1_output')
        self.assertIn('POST ERROR', str(stop.exception) + ''.join(engine.output))
        self.assertEqual(rotary_words(engine), [])

    def test_sanitized_slide_motion_inputs(self):
        """CHARACTERIZATION against recorded SolidCAM data (TSR-08): 482 sanitized
        motion inputs of a real Slide trace in three classes (positive apos posted
        unchanged, one zero, negative apos posted +360). The expected A values were
        captured from NC of an earlier revision of this post (golden, not
        independent), so each one is also checked against the independent rule
        A = (angle_4x_around_x + angle + cpos + apos) mod 360 (iR1dir=-1; bpos and
        x_angle_const_z do not move A). Every case has a zero CoordSys, transform,
        cpos, bpos and x_angle_const_z, so the data backs the apos term only. One
        collected mismatch list, one assertion."""
        fixture = json.loads((ROOT / 'tests/fixtures/slide_rotary.json').read_text())
        self.assertEqual(fixture['schema'], 1)
        cases = fixture['cases']
        self.assertGreater(len(cases), 100)
        classes = {'positive': 0, 'zero': 0, 'negative': 0}
        mismatches = []
        for case in cases:
            state, expected = case['state'], case['expected_a']
            if set(state) != SLIDE_STATE_KEYS or not all(type(value) in (int, float) for value in state.values()):
                mismatches.append(f"event {case['event']}: malformed state {state}")
                continue
            apos = state['apos']
            classes['positive' if apos > 0 else 'negative' if apos < 0 else 'zero'] += 1
            rule = (state['angle_4x_around_x'] + state['angle'] + state['cpos'] + apos) % 360
            if abs(expected - rule) > 1e-9:
                mismatches.append(f"event {case['event']}: recorded A {expected} != rule {rule}")
            engine = rotary_engine(**state)
            engine.call('usr_r1pos_calc')
            if abs(engine.state['nr1pos'] - expected) >= 0.0005:
                mismatches.append(f"event {case['event']}: nR1pos {engine.state['nr1pos']} != recorded {expected}")
        self.assertEqual(mismatches, [])
        self.assertTrue(all(classes.values()), f'fixture lost an equivalence class: {classes}')

    def test_source_mutation_changes_result(self):
        """INDEPENDENT: harness self-check: an in-memory mutation of the apos sign must
        change the computed A, so mutation runs (support.mutation, PP_TEST_SOURCE)
        really exercise the mutated source."""
        engine = rotary_engine(apos=90)
        mutant = adopt_state(engine, mutate('nR1pos5x = (-apos) * iR1dir', 'nR1pos5x = (apos) * iR1dir'))
        mutant.call('usr_r1pos_calc')
        self.assertNotEqual(mutant.state['nr1pos'], 90)
        engine.call('usr_r1pos_calc')
        self.assertEqual(engine.state['nr1pos'], 90)


class HarnessTests(unittest.TestCase):
    def test_trace_flags_and_nested_calls(self):
        """CHARACTERIZATION of the SolidCAM debug-trace format read by pp_tests.trace:
        'T'/'F' change flags, '..>' continuation parameters, '>' NC output lines and
        redaction of identities by the sanitizer."""
        events = parse_trace("(1)@line_5x ==> apos:-90.000T dir5a:cw\n"
                             "                    ..> xpos:1.250F user_account:'Person'\n"
                             "(2)@usr_line ==>\n"
                             "                      > A=ACN(270)\n")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].parameters['apos'], -90)
        self.assertEqual(events[0].changed, {'apos': True, 'xpos': False})
        self.assertEqual(events[0].output, ['A=ACN(270)'])
        self.assertEqual(sanitize(events)[0]['parameters']['user_account'], '<redacted>')

    def test_empty_job_parameter_keeps_the_next_one(self):
        """INDEPENDENT: SolidCAM trace of 2026-10-27 (tests/fixtures/reference_multijob.trace.txt.xz):
        VMID job parameters print as 'name : value' with string values unquoted, so an empty string
        is followed directly by the next name or by the line end; the next parameter keeps its
        value (iG187_P was read as the value of sStopMessage)."""
        events = parse_trace("(1)@start_of_job ==> job_name:'op1' machine_plane:xy omachine_plane:zc\n"
                             "                    ..> bStopM00 : 0  sStopMessage :   iG187_P : 2  nG187_E : 0.00000  \n"
                             "                    ..> Message1 :   Message2 :   Message3 : text  sWorkpcDir :   \n")
        parameters = events[0].parameters
        self.assertEqual((parameters['bstopm00'], parameters['sstopmessage'], parameters['ig187_p'],
                          parameters['ng187_e']), (0, '', 2, 0))
        self.assertEqual((parameters['message1'], parameters['message2'], parameters['message3'],
                          parameters['sworkpcdir']), ('', '', 'text', ''))
        self.assertEqual((parameters['machine_plane'], parameters['omachine_plane']), ('xy', 'zc'))

    def test_printed_drill_type_names_are_read_as_numbers(self):
        """INDEPENDENT: SolidCAM traces tests/fixtures/recorded_cam_003/005: @drill prints drill_type as a
        number and d_drill_type by its constant name; the CAMDBG readout of the same job gives that
        d_drill_type as the number SolidCAM sends (D_Drilling 0, D_Peck 2)."""
        events = parse_trace("(1)@drill           ==> drill_depth:2.200 down_step:0.000 num_down_steps:1 \n"
                             "                    ..> drill_type:0 d_drill_type:D_Drilling drill_cycle_name:'G81' \n"
                             "(1)@drill           ==> drill_depth:24.000 down_step:2.000 num_down_steps:12 \n"
                             "                    ..> drill_type:2 d_drill_type:D_Peck drill_cycle_name:'G83' \n")
        self.assertEqual([(event.parameters['drill_type'], event.parameters['d_drill_type'],
                           event.parameters['drill_cycle_name']) for event in events], [(0, 0, 'G81'), (2, 2, 'G83')])

    def test_plain_nc_is_not_a_trace(self):
        """INDEPENDENT: harness contract: plain NC text is rejected as a trace."""
        with self.assertRaises(ValueError):
            parse_trace('G0 X10\nM30\n')

    def test_unknown_syntax_and_missing_inputs_fail(self):
        """INDEPENDENT: harness contract: unknown statements, missing inputs and
        Python escapes raise UnsupportedGPPL instead of being silently accepted."""
        for source in ['@test\nx = missing\nendp', '@test\nexec something\nendp',
                       '@test\nx = __import__(\'os\')\nendp']:
            with self.subTest(source=source), self.assertRaises(UnsupportedGPPL):
                Engine(source).call('test')

    def test_nested_branch_and_literal_semicolon(self):
        """INDEPENDENT: GPPL: ';' starts a comment only outside string literals; the
        untaken branch of a nested if is not evaluated."""
        engine = Engine("@test\nif false\nif missing\nx=1\nendif\nelse\nx='A;B' ; comment\nendif\nendp")
        engine.call('test')
        self.assertEqual(engine.state['x'], 'A;B')

    def test_apostrophe_in_comment(self):
        """INDEPENDENT: GPPL: comment text is ignored, apostrophes included."""
        engine = Engine("@test\nx=true ; machine's setting\nendp")
        engine.call('test')
        self.assertTrue(engine.state['x'])

    @covers('ENGINE-004')
    def test_string_case_and_escaped_quotes(self):
        """CHARACTERIZATION of the engine's literal model: ';' inside a double-quoted
        string is text, and a doubled quote inside a single-quoted literal is an
        escaped apostrophe. That '' escape model is disputed (ENGINE-004: it renders a
        stray apostrophe in the CYCLE84 argument list), so this pins the engine, not
        GPPL."""
        engine = Engine('@test\nx="ABC; DEF" ; comment\ny=\'can\'\'t\'\nendp')
        engine.call('test')
        self.assertEqual(engine.state['x'], 'ABC; DEF')
        self.assertEqual(engine.state['y'], "can't")

    def test_locals_and_arguments_restore_state_and_change_flags(self):
        """CHARACTERIZATION of the engine's scoping model: locals and arguments are
        restored with their change flags when the procedure returns (GPPL local scope
        itself is unverified, ENGINE-012)."""
        engine = Engine('@test(numeric x)\nlocal numeric y\nx=1\ny=2\nendp')
        engine.set(x=7, y=8)
        engine.changed.update(x=False, y=False)
        engine.call('test', [3])
        self.assertEqual(engine.state, {'x':7,'y':8})
        self.assertEqual(engine.changed, {'x':False,'y':False})

    def test_keyword_arguments_are_rejected(self):
        """INDEPENDENT: GPPL has no keyword arguments; the harness rejects them."""
        with self.assertRaisesRegex(UnsupportedGPPL, 'keyword'):
            Engine('').expression('abs(-2, unexpected=missing)')

    def test_nested_while_and_parameter_scope(self):
        """INDEPENDENT: arithmetic of nested while loops (sum of i+j for i<3, j<2 is 9);
        procedure parameters do not leak into the caller's change flags."""
        source = ('@test\nlocal integer i j\nresult=0\ni=0\nwhile i < 3\n'
                  'j=0\nwhile j < 2\ncall @add((i+j))\nj=j+1\nendw\ni=i+1\nendw\nendp\n'
                  '@add(numeric value)\nresult=result+value\nendp')
        engine = Engine(source)
        engine.call('test')
        self.assertEqual(engine.state, {'result':9})
        self.assertNotIn('value', engine.changed)

    def test_unclosed_while_is_rejected_for_any_condition(self):
        """INDEPENDENT: harness contract: a while without endw is a syntax error,
        whatever its condition evaluates to."""
        for body in ('while true\nx=1', 'while false\nx=1',
                     'while true\nwhile false\nx=1\nendw'):
            with self.subTest(body=body), self.assertRaisesRegex(UnsupportedGPPL, 'unclosed while'):
                Engine('@test\n' + body + '\nendp').call('test')

    def test_modal_output_consumes_flags_and_reassignment_reactivates(self):
        """INDEPENDENT: GPPL modal output: a [..] group prints only changed variables,
        clear_change_after_gen=1 clears the flag after output, and assigning a
        different value raises it again."""
        engine = Engine("@test\n{['X'xpos ' ']}\n{['X'xpos ' ']}\nxpos=2\n{['X'xpos ' ']}\nendp")
        engine.set(xpos=1, clear_change_after_gen=1)
        engine.changed['xpos'] = True
        engine.call('test')
        self.assertEqual(engine.output, ['X1 ', '', 'X2 '])
        self.assertFalse(engine.changed['xpos'])

    def test_degree_trigonometry_and_one_based_strings(self):
        """INDEPENDENT: GPPL trigonometry works in degrees; instr/substr are 1-based
        and instr returns 0 when not found."""
        engine = Engine('')
        self.assertAlmostEqual(engine.expression('sin(90)'), 1)
        self.assertAlmostEqual(engine.expression('cos(180)'), -1)
        self.assertEqual(engine.expression("instr('abcd', 'cd')"), 3)
        self.assertEqual(engine.expression("instr('abcd', 'X')"), 0)
        self.assertEqual(engine.expression("substr('abcdef', 2, 3)"), 'bcd')


if __name__ == '__main__':
    unittest.main()
