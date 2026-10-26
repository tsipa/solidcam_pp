import json
import os
import unittest
from pathlib import Path

from pp_tests.engine import Engine, UnsupportedGPPL
from pp_tests.trace import parse_trace, sanitize

ROOT = Path(__file__).resolve().parents[1]
PP = Path(os.environ.get('PP_TEST_SOURCE', ROOT / 'siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.gpp'))


def rotary_engine(**overrides):
    engine = Engine.from_path(PP)
    # Explicit CAM/environment defaults for isolated rotary procedure tests.
    engine.set(angle_4x_around_x=0, angle=0, cpos=0, apos=0, bpos=0,
               x_angle_const_z=0, iR1dir=-1, iR2dir=1, iR1posControl=1,
               nPR1postemp=0, nPR1pos=0, nPR2pos=0, bLimit_3axis=False,
               bR1forceOutput=False, bR1useDir5a=True, dir5a='cw',
               angle_4x_around_x_dir='cw', cw='cw', ccw='ccw', cR1='A')
    engine.set(**overrides)
    return engine


class PostprocessorTests(unittest.TestCase):
    def test_actual_user_options(self):
        engine = Engine.from_path(PP)
        engine.call('usr_ip_useroptions')
        self.assertEqual(engine.state['ir1dir'], -1)
        self.assertEqual(engine.state['cr1'], 'A')
        self.assertEqual(engine.state['ir1poscontrol'], 1)

    def test_positive_angles_and_boundaries(self):
        for angle, expected in [(-359.999, .001), (-90, 270), (0, 0),
                                (90, 90), (359.999, 359.999), (-360, -360), (360, 360)]:
            with self.subTest(angle=angle):
                engine = rotary_engine(apos=angle)
                engine.call('usr_r1pos_calc')
                self.assertAlmostEqual(engine.state['nr1pos'], expected)

    def test_combines_coordinate_transform_cpos_and_simultaneous_angle(self):
        engine = rotary_engine(angle_4x_around_x=30, angle=20, cpos=10, apos=5)
        engine.call('usr_r1pos_calc')
        self.assertEqual(engine.state['nr1pos'], 65)

    def test_negative_and_direct_modes(self):
        for mode, expected in [(0, 90), (2, -270)]:
            engine = rotary_engine(apos=90, iR1posControl=mode)
            engine.call('usr_r1pos_calc')
            self.assertEqual(engine.state['nr1pos'], expected)

    def test_first_rotation_dc_then_direction_and_unchanged(self):
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
        engine = rotary_engine(apos=90)
        engine.call('usr_r1pos_calc')
        engine.call('usr_r1_output')
        self.assertEqual(engine.output, ['A=ACN(90) '])

    def test_3axis_suppresses_rotary_change(self):
        engine = rotary_engine(apos=90, bpos=15, bLimit_3axis=True)
        engine.call('usr_r1pos_calc')
        self.assertFalse(engine.changed['nr1pos'])
        self.assertFalse(engine.changed['nr2pos'])

    def test_tmatrix_invalidates_clearance(self):
        engine = Engine.from_path(PP)
        engine.set(bCamLinkRetract=True)
        engine.call('tmatrix')
        self.assertTrue(engine.state['bindexclearancepending'])
        self.assertTrue(engine.state['btmatrixindexpending'])
        self.assertFalse(engine.state['bcamlinkretract'])

    def test_invalid_direction_is_not_silently_emitted(self):
        engine = rotary_engine(iR1dirMode=0)
        with self.assertRaisesRegex(UnsupportedGPPL, 'POST ERROR'):
            engine.call('usr_r1_output')

    def test_sanitized_slide_motion_inputs(self):
        fixture = json.loads((ROOT / 'tests/fixtures/slide_rotary.json').read_text())
        self.assertEqual(fixture['schema'], 1)
        self.assertGreater(len(fixture['cases']), 100)
        for case in fixture['cases']:
            with self.subTest(event=case['event']):
                self.assertEqual(set(case['state']), {'angle_4x_around_x','angle','cpos','apos','bpos','x_angle_const_z'})
                self.assertTrue(all(type(value) in (int, float) for value in case['state'].values()))
                engine = rotary_engine(**case['state'])
                engine.call('usr_r1pos_calc')
                self.assertAlmostEqual(engine.state['nr1pos'], case['expected_a'], places=3)

    def test_source_mutation_changes_result(self):
        source = PP.read_text(encoding='utf-8-sig')
        original = 'nR1pos5x = (-apos) * iR1dir'
        self.assertIn(original, source)
        engine = rotary_engine(apos=90)
        mutant = Engine(source.replace(original, 'nR1pos5x = (apos) * iR1dir', 1))
        mutant.set(**engine.state)
        mutant.call('usr_r1pos_calc')
        self.assertNotEqual(mutant.state['nr1pos'], 90)


class HarnessTests(unittest.TestCase):
    def test_trace_flags_and_nested_calls(self):
        events = parse_trace("(1)@line_5x ==> apos:-90.000T dir5a:cw\n"
                             "                    ..> xpos:1.250F user_account:'Person'\n"
                             "(2)@usr_line ==>\n"
                             "                      > A=ACN(270)\n")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].parameters['apos'], -90)
        self.assertEqual(events[0].changed, {'apos': True, 'xpos': False})
        self.assertEqual(events[0].output, ['A=ACN(270)'])
        self.assertEqual(sanitize(events)[0]['parameters']['user_account'], '<redacted>')

    def test_plain_nc_is_not_a_trace(self):
        with self.assertRaises(ValueError):
            parse_trace('G0 X10\nM30\n')

    def test_unknown_syntax_and_missing_inputs_fail(self):
        for source in ['@test\nx = missing\nendp', '@test\nexec something\nendp',
                       '@test\nx = __import__(\'os\')\nendp']:
            with self.subTest(source=source), self.assertRaises(UnsupportedGPPL):
                Engine(source).call('test')

    def test_nested_branch_and_literal_semicolon(self):
        engine = Engine("@test\nif false\nif missing\nx=1\nendif\nelse\nx='A;B' ; comment\nendif\nendp")
        engine.call('test')
        self.assertEqual(engine.state['x'], 'A;B')

    def test_apostrophe_in_comment(self):
        engine = Engine("@test\nx=true ; machine's setting\nendp")
        engine.call('test')
        self.assertTrue(engine.state['x'])

    def test_string_case_and_escaped_quotes(self):
        engine = Engine('@test\nx="ABC; DEF" ; comment\ny=\'can\'\'t\'\nendp')
        engine.call('test')
        self.assertEqual(engine.state['x'], 'ABC; DEF')
        self.assertEqual(engine.state['y'], "can't")

    def test_locals_and_arguments_restore_state_and_change_flags(self):
        engine = Engine('@test(numeric x)\nlocal numeric y\nx=1\ny=2\nendp')
        engine.set(x=7, y=8)
        engine.changed.update(x=False, y=False)
        engine.call('test', [3])
        self.assertEqual(engine.state, {'x':7,'y':8})
        self.assertEqual(engine.changed, {'x':False,'y':False})

    def test_keyword_arguments_are_rejected(self):
        with self.assertRaisesRegex(UnsupportedGPPL, 'keyword'):
            Engine('').expression('abs(-2, unexpected=missing)')

    def test_nested_while_and_parameter_scope(self):
        source = ('@test\nlocal integer i j\nresult=0\ni=0\nwhile i < 3\n'
                  'j=0\nwhile j < 2\ncall @add(i+j)\nj=j+1\nendw\ni=i+1\nendw\nendp\n'
                  '@add(numeric value)\nresult=result+value\nendp')
        engine = Engine(source)
        engine.call('test')
        self.assertEqual(engine.state, {'result':9})
        self.assertNotIn('value', engine.changed)

    def test_unclosed_while_is_rejected_for_any_condition(self):
        for body in ('while true\nx=1', 'while false\nx=1',
                     'while true\nwhile false\nx=1\nendw'):
            with self.subTest(body=body), self.assertRaisesRegex(UnsupportedGPPL, 'unclosed while'):
                Engine('@test\n' + body + '\nendp').call('test')

    def test_modal_output_consumes_flags_and_reassignment_reactivates(self):
        engine = Engine("@test\n{['X'xpos ' ']}\n{['X'xpos ' ']}\nxpos=2\n{['X'xpos ' ']}\nendp")
        engine.set(xpos=1, clear_change_after_gen=1)
        engine.changed['xpos'] = True
        engine.call('test')
        self.assertEqual(engine.output, ['X1 ', '', 'X2 '])
        self.assertFalse(engine.changed['xpos'])

    def test_degree_trigonometry_and_one_based_strings(self):
        engine = Engine('')
        self.assertAlmostEqual(engine.expression('sin(90)'), 1)
        self.assertAlmostEqual(engine.expression('cos(180)'), -1)
        self.assertEqual(engine.expression("instr('abcd', 'cd')"), 3)
        self.assertEqual(engine.expression("instr('abcd', 'X')"), 0)
        self.assertEqual(engine.expression("substr('abcdef', 2, 3)"), 'bcd')


if __name__ == '__main__':
    unittest.main()
