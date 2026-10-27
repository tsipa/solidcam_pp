"""A positions for ACP/ACN/DC stay inside the modulo range 0 <= A < 360.

Oracle (INDEPENDENT): ACP/ACN/DC address a modulo rotary axis; the programmed position must lie in
0..359.999 degrees and the direction comes from ACP/ACN, not from the sign or size of the value.
360 is the same position as 0; with the 3-decimal A format any value >= 359.9995 prints as 360.
The post works with the position the A word prints (nR1pos_f '7.3'): nR1pos is the angle rounded
to 0.001, so its change test and travel checks see what the control receives.

FullTurnBaselineTests (owner decision 2026-10-27, variant E): a cutting block stops when the control
drops a whole turn of CAM's own A step. Frame angles and the post's own apos = 0 (tool change,
@fourth_axis) are not CAM motion, so they never make a full turn on their own.
"""
import random
import unittest

from pp_tests.engine import UnsupportedGPPL
from program_session import Program
from support import covers
from test_offline import rotary_engine


def a_position(**state):
    engine = rotary_engine(**state)
    engine.call('usr_r1pos_calc')
    return engine


class RotaryModuloRangeTests(unittest.TestCase):
    def test_positions_are_normalized_into_modulo_range(self):
        cases = [(370, 10), (720, 0), (-400, 320), (-720, 0), (1085, 5), (-0.0004, 0), (359.9996, 0),
                 (359.9994, 359.999), (-359.9994, 0.001)]
        for apos, expected in cases:
            with self.subTest(apos=apos):
                self.assertAlmostEqual(a_position(apos=apos).state['nr1pos'], expected, places=6)

    def test_position_is_inside_the_range_for_any_angle_sum(self):
        rng = random.Random(828)
        for _ in range(400):
            parts = dict(angle_4x_around_x=rng.choice([0, 90, 10.1, -45.5, 300]),
                         angle=round(rng.uniform(-400, 400), rng.choice([0, 1, 3])),
                         apos=round(rng.uniform(-800, 800), rng.choice([0, 1, 3, 4])))
            if rng.random() < 0.25:     # land within a few 0.0001 of a whole turn
                parts['apos'] = round(360 * rng.randint(-2, 2) + rng.uniform(-0.0008, 0.0008)
                                      - parts['angle_4x_around_x'] - parts['angle'], 4)
            with self.subTest(**parts):
                value = a_position(**parts).state['nr1pos']
                self.assertTrue(0 <= value < 360, value)
                expected = (parts['angle_4x_around_x'] + parts['angle'] + parts['apos']) % 360
                if expected >= 359.9995 or expected < 0.0005:      # prints as 0.000/360.000: position 0
                    expected = 0
                # The printed position: a multiple of 0.001 within half an output step of the angle.
                self.assertAlmostEqual(value * 1000, round(value * 1000), places=6)
                self.assertAlmostEqual(value, expected, delta=0.0005 + 1e-9)

    def test_angle_sum_with_float_noise_is_exactly_zero(self):
        # 10.1 + 20.2 - 30.3 is -3.5e-15 in binary floating point, not 0.
        value = a_position(angle_4x_around_x=10.1, angle=20.2, apos=-30.3).state['nr1pos']
        self.assertEqual(value, 0)

    def test_snap_boundary(self):
        self.assertEqual(a_position(apos=359.9995).state['nr1pos'], 0)
        self.assertEqual(a_position(apos=0.0004).state['nr1pos'], 0)
        self.assertAlmostEqual(a_position(apos=0.0006).state['nr1pos'], 0.001, places=9)

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


FULL_TURN = 'One cutting block turns A by 360 degrees or more'


def _first_job(program, end_apos=0, **cam):
    program.start(**cam)
    program.ev('move_5x', xpos=12, ypos=0, zpos=25, apos=0)
    program.ev('line_5x', zpos=10, feed=200)
    for apos in range(90, end_apos, 90):
        program.ev('line_5x', xpos=12 + apos / 90, apos=apos, feed=200, dir5a='ccw')
    if end_apos:
        program.ev('line_5x', xpos=30, apos=end_apos, feed=200, dir5a='ccw')
    program.ev('move_5x', zpos=40)
    program.ev('end_of_job')


def _second_tool_job(program, end_apos):
    program.ev('change_tool', tool_number=2, next_tool_number=3, first_tool=False)
    program.ev('start_of_job', job_name='op2')
    program.ev('move_5x', xpos=12, ypos=0, zpos=25, apos=0)
    program.ev('line_5x', zpos=10, feed=200)
    for apos in range(90, end_apos, 90):
        program.ev('line_5x', xpos=12 + apos / 90, apos=apos, feed=200, dir5a='ccw')
    program.ev('line_5x', xpos=30, apos=end_apos, feed=200, dir5a='ccw')
    program.ev('move_5x', zpos=40)
    program.ev('end_of_job')


def _third_tool_after(end_apos):
    """Tool 2 ends at CAM A end_apos; from the 3rd tool change on the post sets apos = 0 and turns A back."""
    program = Program()
    _first_job(program)
    _second_tool_job(program, end_apos)
    program.ev('change_tool', tool_number=3, next_tool_number=4, first_tool=False)
    program.ev('start_of_job', job_name='op3')
    return program


class FullTurnBaselineTests(unittest.TestCase):
    """The full-turn step is the CAM A motion of the block: frame angles and the post's own apos = 0 are not."""

    def test_whole_turn_change_of_the_coordinate_system_is_not_a_cutting_turn(self):
        for start, job in ((dict(), dict(angle=360)), (dict(), dict(angle_4x_around_x=360)),
                           (dict(angle=300), dict(angle=-60))):
            with self.subTest(start=start, job=job):
                program = Program()
                _first_job(program, **start)
                program.ev('start_of_job', job_name='op2', **job)
                self.assertEqual(program.ev('line_5x', xpos=20, zpos=10, feed=200), ['G1 X20 Z10'])

    @covers('PP-061')
    def test_post_reset_of_a_is_not_a_cutting_turn(self):
        # CAM A unchanged across the 3rd tool change: no full-turn stop; the NC is what cfd5787 posts for CAM A 5.
        for end_apos, a_word in ((5, ' A=ACP(5)'), (725, ' A=ACP(5)'), (720, '')):
            with self.subTest(end_apos=end_apos):
                program = _third_tool_after(end_apos)
                output = program.ev('line_5x', xpos=20, zpos=10, apos=end_apos, feed=200, dir5a='ccw',
                                    force=dict(apos=False))
                self.assertEqual(output, ['G0 X20 Y0', f'G1 Z10{a_word} F200'])

    @covers('PP-061')
    def test_fourth_axis_and_offset_change_resets_are_not_cutting_turns(self):
        program = Program()
        _first_job(program, end_apos=725)
        program.ev('fourth_axis', angle=90)
        program.ev('start_of_job', job_name='op2')
        output = program.ev('line_5x', xpos=20, zpos=10, apos=725, feed=200, dir5a='ccw', force=dict(apos=False))
        self.assertNotIn('POST ERROR', ' '.join(output))
        program = Program(cam=dict(home_user_name='54'))
        program.engine.state['iworkoffset_method'] = 1
        _first_job(program)
        _second_tool_job(program, 725)
        program.ev('start_of_job', job_name='op3', home_user_name='55')
        output = program.ev('line_5x', xpos=20, zpos=10, apos=725, feed=200, dir5a='ccw', force=dict(apos=False))
        self.assertNotIn('POST ERROR', ' '.join(output))

    def test_cam_full_turn_after_a_post_reset_still_stops(self):
        # The CAM A turns 360 in the first block after the post's apos = 0: a real turn that the modulo
        # axis would drop (3rd tool change, @fourth_axis, offset change, and an arc in front of the block).
        for end_apos, target in ((0, 360), (720, 1080), (90, 450), (725, 365)):
            with self.subTest(tool=3, end_apos=end_apos, target=target):
                program = _third_tool_after(end_apos)
                with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
                    program.ev('line_5x', xpos=20, zpos=10, apos=target, feed=200, dir5a='ccw')
        with self.subTest('fourth_axis'):
            program = Program()
            _first_job(program)
            program.ev('fourth_axis', angle=90)
            program.ev('start_of_job', job_name='op2')
            with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
                program.ev('line_5x', xpos=20, zpos=10, apos=360, feed=200, dir5a='ccw')
        with self.subTest('offset change'):
            program = Program(cam=dict(home_user_name='54'))
            program.engine.state['iworkoffset_method'] = 1
            _first_job(program)
            _second_tool_job(program, 0)
            program.ev('start_of_job', job_name='op3', home_user_name='55')
            with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
                program.ev('line_5x', xpos=20, zpos=10, apos=360, feed=200, dir5a='ccw')
        with self.subTest('arc first'):
            program = _third_tool_after(0)
            program.ev('arc', xpos=20, ypos=0, zpos=10, arc_plane='xy', arc_direction='ccw', arc_size=180,
                       radius=5, xstart=10, ystart=0, zstart=10, xcenter=15, ycenter=0, zcenter=10,
                       xcenter_rel=5, ycenter_rel=0, zcenter_rel=0, feed=200)
            with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
                program.ev('line_5x', xpos=25, apos=360, feed=200, dir5a='ccw')

    def test_later_turns_after_a_post_reset_are_checked(self):
        program = _third_tool_after(725)
        program.ev('line_5x', xpos=20, zpos=10, apos=725, feed=200, dir5a='ccw', force=dict(apos=False))
        with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
            program.ev('line_5x', xpos=25, apos=1085, feed=200, dir5a='ccw')
        # The CAM baseline follows the CAM again after the first feed block.
        program = _third_tool_after(725)
        program.ev('line_5x', xpos=20, zpos=10, apos=725, feed=200, dir5a='ccw', force=dict(apos=False))
        program.ev('line_5x', xpos=22, apos=400, feed=200, dir5a='cw')
        with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
            program.ev('line_5x', xpos=25, apos=760, feed=200, dir5a='ccw')

    def test_plain_job_after_a_post_reset_is_posted(self):
        # A 2.5D job sends no apos: the post's 0 stays, so the CAM A of the previous job is no start point.
        program = _third_tool_after(725)
        output = program.ev('line', xpos=20, ypos=0, zpos=10, feed=200, feed_type='feed_cut')
        self.assertNotIn('POST ERROR', ' '.join(output))

    def test_whole_cam_turn_after_a_coordinate_change_still_stops(self):
        program = Program()
        _first_job(program)
        program.ev('start_of_job', job_name='op2', angle=90)
        with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
            program.ev('line_5x', xpos=20, zpos=10, apos=360, feed=200, dir5a='ccw')
        program = Program()
        _first_job(program)
        program.ev('start_of_job', job_name='op2', angle=360)
        program.ev('line_5x', xpos=20, zpos=10, feed=200)
        with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
            program.ev('line_5x', xpos=25, apos=360, feed=200, dir5a='ccw')

    def test_job_first_cam_turn_without_a_reset_still_stops(self):
        program = Program()
        _first_job(program)
        program.ev('start_of_job', job_name='op2')
        with self.assertRaisesRegex(UnsupportedGPPL, FULL_TURN):
            program.ev('line_5x', xpos=20, zpos=10, apos=360, feed=200, dir5a='ccw')


if __name__ == '__main__':
    unittest.main()
