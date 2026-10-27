"""A positions for ACP/ACN/DC stay inside the modulo range 0 <= A < 360.

Oracle (INDEPENDENT): ACP/ACN/DC address a modulo rotary axis; the programmed position must lie in
0..359.999 degrees and the direction comes from ACP/ACN, not from the sign or size of the value.
360 is the same position as 0; with the 3-decimal A format any value >= 359.9995 prints as 360.
"""
import unittest

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


if __name__ == '__main__':
    unittest.main()
