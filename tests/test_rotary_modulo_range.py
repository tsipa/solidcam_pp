"""A positions for ACP/ACN/DC stay inside the modulo range 0 <= A < 360.

Oracle (INDEPENDENT): ACP/ACN/DC address a modulo rotary axis; the programmed position must lie in
0..359.999 degrees and the direction comes from ACP/ACN, not from the sign or size of the value.
360 is the same position as 0; with the 3-decimal A format any value >= 359.9995 prints as 360.
"""
import random
import unittest

from pp_tests.engine import UnsupportedGPPL
from program_session import Program
from test_offline import rotary_engine


def a_position(**state):
    engine = rotary_engine(**state)
    engine.call('usr_r1pos_calc')
    return engine


class RotaryModuloRangeTests(unittest.TestCase):
    def test_positions_are_normalized_into_modulo_range(self):
        cases = [(370, 10), (720, 0), (-400, 320), (-720, 0), (1085, 5), (-0.0004, 0), (359.9996, 0),
                 (359.9994, 359.9994), (-359.9994, 0.0006)]
        for apos, expected in cases:
            with self.subTest(apos=apos):
                self.assertAlmostEqual(a_position(apos=apos).state['nr1pos'], expected, places=6)

    def test_position_is_inside_the_range_for_any_angle_sum(self):
        rng = random.Random(828)
        for _ in range(400):
            parts = dict(angle_4x_around_x=rng.choice([0, 90, 10.1, -45.5, 300]),
                         angle=round(rng.uniform(-400, 400), rng.choice([0, 1, 3])),
                         apos=round(rng.uniform(-800, 800), rng.choice([0, 1, 3, 4])))
            with self.subTest(**parts):
                value = a_position(**parts).state['nr1pos']
                self.assertTrue(0 <= value < 360, value)
                total = -(parts['angle_4x_around_x'] + parts['angle'] + parts['apos']) * -1
                offset = (value - total) / 360
                self.assertAlmostEqual(offset, round(offset), places=6)

    def test_angle_sum_with_float_noise_is_exactly_zero(self):
        # 10.1 + 20.2 - 30.3 is -3.5e-15 in binary floating point, not 0.
        value = a_position(angle_4x_around_x=10.1, angle=20.2, apos=-30.3).state['nr1pos']
        self.assertEqual(value, 0)

    def test_snap_boundary(self):
        self.assertEqual(a_position(apos=359.9995).state['nr1pos'], 0)
        self.assertEqual(a_position(apos=0.0004).state['nr1pos'], 0)
        self.assertAlmostEqual(a_position(apos=0.0006).state['nr1pos'], 0.0006, places=9)

    def test_cutting_block_turning_a_full_revolution_stops_the_post(self):
        # The CAM A axis is unlimited (VMID); one ACP/ACN block turns less than a revolution on the modulo axis.
        for apos in (360, 370, -720):
            with self.subTest(apos=apos):
                program = Program()
                program.start()
                program.ev('move_5x', xpos=12, ypos=0, zpos=25)
                with self.assertRaisesRegex(UnsupportedGPPL, 'One cutting block turns A by 360 degrees or more'):
                    program.ev('line_5x', xpos=20, apos=apos, feed=200, feed_type='feed_cut')

    def test_link_block_turning_a_full_revolution_is_dropped(self):
        program = Program()
        program.start()
        program.ev('move_5x', xpos=12, ypos=0, zpos=25)
        self.assertEqual(program.ev('line_5x', xpos=20, apos=360, feed=200, feed_type='feed_link'), ['G1 X20 F200'])

    def test_cutting_block_just_under_a_revolution_is_posted(self):
        program = Program()
        program.start()
        program.ev('move_5x', xpos=12, ypos=0, zpos=25)
        output = program.ev('line_5x', xpos=20, apos=359, feed=200, feed_type='feed_cut', dir5a='ccw')
        self.assertIn('A=ACP(359)', ' '.join(output))

    def test_coordinate_system_angle_plus_simultaneous_angle_wraps(self):
        self.assertAlmostEqual(a_position(angle_4x_around_x=300, apos=100).state['nr1pos'], 40)

    def test_directed_output_uses_normalized_value(self):
        engine = a_position(apos=350, nPR1pos=350, nPR1postemp=350, dir5a='ccw')
        engine.set(apos=370)
        engine.call('usr_r1pos_calc')
        engine.call('usr_r1_output')
        self.assertEqual(engine.output, ['A=ACP(10) '])

    def test_first_dc_output_uses_normalized_value(self):
        engine = a_position(apos=-360, bR1forceOutput=True)
        engine.call('usr_r1_output')
        self.assertEqual(engine.output, ['A=DC(0) '])

    def test_360_and_0_are_the_same_position(self):
        engine = a_position(apos=360, nPR1pos=0)
        self.assertFalse(engine.changed['nr1pos'])

    def test_negative_and_direct_modes_are_unchanged(self):
        self.assertEqual(a_position(apos=90, iR1posControl=0).state['nr1pos'], 90)
        self.assertEqual(a_position(apos=370, iR1posControl=0).state['nr1pos'], 370)
        self.assertEqual(a_position(apos=90, iR1posControl=2).state['nr1pos'], -270)

    def test_modes_2_and_3_sequences_match_the_pre_fix_post(self):
        # Recorded from the post before the modulo change (main): the restructured block keeps modes 2/3.
        sequence = [10, 350, -10, 200, -200, 359, 0, -90, 90, 400]
        expected = {2: [-350, -10, -10, -160, -200, -1, 0, -90, -270, 400],
                    3: [10, 350, 350, 200, 160, 359, 0, 270, 90, 400]}
        for mode, values in expected.items():
            engine = rotary_engine(iR1posControl=mode)
            got = []
            for apos in sequence:
                engine.set(apos=apos)
                engine.call('usr_r1pos_calc')
                got.append(round(engine.state['nr1pos'], 6))
            self.assertEqual(got, values, f'mode {mode}')

    def test_feed_moves_across_the_wrap_keep_the_direction(self):
        engine = rotary_engine(apos=350, nPR1pos=350, nPR1postemp=350, dir5a='ccw')
        posted = []
        for apos in (355, 360, 365, 370):
            engine.set(apos=apos)
            engine.output.clear()
            engine.call('usr_r1pos_calc')
            engine.call('usr_r1_output')
            posted.append(''.join(engine.output).strip())
        self.assertEqual(posted, ['A=ACP(355)', 'A=ACP(0)', 'A=ACP(5)', 'A=ACP(10)'])


if __name__ == '__main__':
    unittest.main()
