"""ACP/ACN must turn A the way CAM turns it, or the post stops (modulo axis, 0 <= A < 360).

Oracle (INDEPENDENT): on the control ACP turns A from the programmed position to the new one in the
positive direction, ACN in the negative one, so the turn follows from the two PRINTED positions
(3 decimals, nR1pos_f '7.3') and the word. CAM's turn is the unwrapped CAM angle difference
(iR1dir=-1: machine A = CAM apos; increasing apos is 'ccw' = ACP in the recorded shit2 trace). They
must agree within the rounding of the two positions; CAM may turn whole turns more in the same
direction (a rapid drops them; a cutting block stops, test_rotary_modulo_range). Owner rule
(2026-10-27): when the control could turn A another way than CAM, the post stops: no silent flip of
the word. This covers every feed move and every rapid that turns A while the tool does not stand at
a Z homing (a CAM link, a rotation homing without Z or switched off), whatever event it comes from.
A rapid after a Z homing keeps CAM's word: the tool stands at the homing height. Printed positions
that are equal are no rotation (no A word, no G93).
"""
import json
import random
import re
import unittest

from pp_tests.engine import UnsupportedGPPL
from program_session import Program, post_abort_error, require_nc_stream, post_error_policies
from support import assert_detected, covers, mutate
from test_offline import ROOT

WORD = re.compile(r'A=(ACP|ACN|DC)\(([-\d.]+)\)')
WRONG_WAY = 'another way than in CAM'


def started(a0=20.0, source=None, options=None):
    program = Program(source=source, options=options)
    program.start()
    program.ev('move_5x', xpos=10, ypos=0, zpos=30, apos=a0, dir5a='ccw')
    program.ev('line_5x', zpos=25, feed=200, feed_type='feed_rate')
    return program


def travel(previous, mode, target):
    if mode == 'ACP':
        return (target - previous) % 360
    if mode == 'ACN':
        return -((previous - target) % 360)
    return (target - previous + 180) % 360 - 180


class RotaryDirectionGuardTests(unittest.TestCase):
    def assert_wrong_way_stop(self, run):
        with self.assertRaises(UnsupportedGPPL) as stop:
            run()
        self.assertIn(WRONG_WAY, str(stop.exception))

    @covers('PP-060')
    def test_wrong_way_feed_moves_stop_the_post(self):
        """INDEPENDENT: module oracle. CAM 20 -> 10 (-10 degrees) with ACP would turn +350 degrees while the tool feeds."""
        cases = {
            'line_5x': dict(apos=10, dir5a='ccw', feed_type='feed_rate'),
            'line': dict(apos=10, angle_4x_around_x_dir='ccw', feed_type='feed_rate'),
            'line_4x': dict(cpos=-10, dir5a='ccw', feed_type='feed_rate'),
            'line_5x link': dict(apos=10, dir5a='ccw', feed_type='feed_link', zpos=40),
        }
        for label, values in cases.items():
            with self.subTest(label):
                program = started()
                call = label.split()[0]
                self.assert_wrong_way_stop(lambda: program.ev(call, xpos=20, feed=200, **values))

    def test_wrong_way_stop_names_both_angles(self):
        """INDEPENDENT: module oracle; the POST ERROR line names both printed angles, CAM's turn and the control's."""
        require_nc_stream()
        program = Program(policies=post_error_policies())
        program.start()
        program.ev('move_5x', xpos=10, ypos=0, zpos=30, apos=20, dir5a='ccw')
        program.ev('line_5x', zpos=25, feed=200, feed_type='feed_rate')
        with self.assertRaises(post_abort_error()):
            program.ev('line_5x', xpos=20, apos=10, feed=200, feed_type='feed_rate', dir5a='ccw')
        self.assertEqual(program.nc()[-1].strip(), 'POST ERROR: A would turn another way than in CAM (ACP/ACN): '
                                                   'A20 to A10, CAM -10 deg, control 350 deg.')

    @covers('PP-060')
    def test_rounding_straddle_against_the_word_stops(self):
        """INDEPENDENT: owner rule. 20.0004 -> 20.0006 prints 20 -> 20.001; a 'cw' word makes ACN turn 359.999 degrees."""
        program = started(20.0004)
        program.ev('line_5x', xpos=15, feed=200, feed_type='feed_rate')
        self.assert_wrong_way_stop(
            lambda: program.ev('line_5x', xpos=20, apos=20.0006, feed=200, feed_type='feed_rate', dir5a='cw'))

    def test_rounding_straddle_with_the_word_posts_one_step(self):
        """INDEPENDENT: module oracle. The same straddle with 'ccw' is one output step on the control."""
        program = started(20.0004)
        program.ev('line_5x', xpos=15, feed=200, feed_type='feed_rate')
        output = program.ev('line_5x', xpos=20, apos=20.0006, feed=200, feed_type='feed_rate', dir5a='ccw')
        self.assertEqual(len(output), 1, output)
        self.assertIn('A=ACP(20.001)', output[0])

    def test_same_printed_position_is_no_rotation(self):
        """INDEPENDENT: module oracle. 20.0014 -> 20.0006 prints 20.001 twice: no A word and no G93 block."""
        program = started()
        program.ev('line_5x', xpos=15, apos=20.0014, feed=200, feed_type='feed_rate', dir5a='ccw')
        output = program.ev('line_5x', xpos=20, apos=20.0006, feed=200, feed_type='feed_rate', dir5a='ccw')
        self.assertEqual(len(output), 1, output)
        self.assertNotIn('A=', output[0])
        self.assertNotIn('G93', output[0])

    @covers('PP-060')
    def test_wrong_way_rotary_link_rapid_stops_the_post(self):
        """INDEPENDENT: module oracle. A CAM rotary link turns A without homing Z: the other way round sweeps the part under the tool."""
        program = started()
        program.ev('line_5x', zpos=40, feed=200, feed_type='feed_link')
        self.assert_wrong_way_stop(lambda: program.ev('move_5x', apos=10, dir5a='ccw'))

    @covers('PP-060')
    def test_wrong_way_rapid_without_rotation_homing_stops_the_post(self):
        """INDEPENDENT: owner rule. With the rotation homing switched off (sHomestrroth '' or
        bHomeroth false) the turn runs at the current Z."""
        for options in (dict(sHomestrroth=''), dict(bHomeroth=False)):
            with self.subTest(**options):
                program = started(options=options)
                program.ev('move_5x', zpos=60)
                self.assert_wrong_way_stop(lambda: program.ev('move_5x', apos=10, dir5a='ccw'))

    @covers('PP-060')
    def test_wrong_way_three_axis_rapid_without_rotation_homing_stops_the_post(self):
        """INDEPENDENT: owner rule. A @rapid_move takes its word from angle_4x_around_x_dir; with the
        rotation homing switched off it turns A at the current height, here +350 for CAM's -10."""
        for options in (dict(sHomestrroth=''), dict(bHomeroth=False)):
            with self.subTest(**options):
                program = started(options=options)
                program.ev('line_5x', zpos=30, feed=200, feed_type='feed_rate')
                self.assert_wrong_way_stop(lambda: program.ev('rapid_move', xpos=20, apos=10,
                                                              angle_4x_around_x_dir='ccw'))

    @covers('PP-060')
    def test_wrong_way_rapid_with_a_rotation_homing_without_z_stops_the_post(self):
        """INDEPENDENT: owner rule. A rotation homing of X/Y only leaves the tool at its height."""
        program = started(options=dict(sHomestrroth='8::G75 Y1=0 X1=0'))
        program.ev('move_5x', zpos=60)
        self.assert_wrong_way_stop(lambda: program.ev('move_5x', apos=10, dir5a='ccw'))

    def test_wrong_way_homed_rapid_keeps_the_word(self):
        """CHARACTERIZATION: after G75 Z the post keeps CAM's word (only time is at stake)."""
        program = started()
        program.ev('move_5x', zpos=60)
        output = program.ev('move_5x', apos=10, dir5a='ccw')
        self.assertEqual([block.strip() for block in output[:3]], ['G75 Z1=0.', 'G75 Y1=0 X1=0', 'G0 A=ACP(10)'])

    @covers('PP-060')
    def test_angles_that_jump_by_a_turn_stop_in_a_cut(self):
        """INDEPENDENT: owner rule. 179 -> -179 with 'ccw' is -358 degrees in CAM but +2 on the control."""
        program = started(179.0)
        self.assert_wrong_way_stop(
            lambda: program.ev('line_5x', xpos=15, apos=-179, feed=200, feed_type='feed_rate', dir5a='ccw'))

    def test_full_turn_hidden_by_rounding_stops_the_post(self):
        """INDEPENDENT: 20.0004 -> 379.9998 is 359.9994 degrees but prints A20 twice: the control would not turn."""
        program = started(20.0004)
        with self.assertRaises(UnsupportedGPPL) as stop:
            program.ev('line_5x', xpos=15, apos=379.9998, feed=200, feed_type='feed_rate', dir5a='ccw')
        self.assertIn('360 degrees or more', str(stop.exception))

    @covers('PP-060')
    def test_first_feed_move_after_toolchange_unwind_stops(self):
        """INDEPENDENT: DESIGN-005 path. The third tool change puts A back to 0; SolidCAM's word for the
        next job's first feed move (30, 'cw' from its own 37) would make ACN turn 330 degrees from 0."""
        program = Program()
        program.start()
        for tool in (2, 3):
            program.ev('move_5x', xpos=10, ypos=0, zpos=30, apos=37, dir5a='ccw')
            program.ev('line_5x', zpos=25, feed=200, feed_type='feed_rate')
            program.ev('move_5x', zpos=60)
            program.ev('end_of_job')
            program.ev('change_tool', tool_number=tool, next_tool_number=tool + 1, first_tool=False)
            program.ev('start_of_job', job_name=f'op{tool}')
        self.assert_wrong_way_stop(
            lambda: program.ev('line_5x', xpos=12, zpos=50, apos=30, feed=200, feed_type='feed_rate', dir5a='cw'))

    @covers('PP-060')
    def test_extra_turn_after_the_post_unwind_stops(self):
        """INDEPENDENT: owner rule (2026-10-28). After the third tool change (A unwound to 0 by the post) or
        @fourth_axis, CAM goes 37 -> 40 'ccw' (+3) but ACP(40) turns the control +40 from 0: stop, even
        though the direction agrees."""
        program = Program()
        program.start()
        for tool in (2, 3):
            program.ev('move_5x', xpos=10, ypos=0, zpos=30, apos=37, dir5a='ccw')
            program.ev('line_5x', zpos=25, feed=200, feed_type='feed_rate')
            program.ev('move_5x', zpos=60)
            program.ev('end_of_job')
            program.ev('change_tool', tool_number=tool, next_tool_number=tool + 1, first_tool=False)
            program.ev('start_of_job', job_name=f'op{tool}')
        self.assert_wrong_way_stop(
            lambda: program.ev('line_5x', xpos=12, zpos=50, apos=40, feed=200, feed_type='feed_rate', dir5a='ccw'))
        program = started(37.0)
        program.ev('move_5x', zpos=60)
        program.ev('end_of_job')
        program.ev('start_of_job', job_name='op2')
        program.ev('fourth_axis', angle=0, angle_4x_around_x_dir='ccw')
        self.assert_wrong_way_stop(
            lambda: program.ev('line_5x', xpos=12, zpos=50, apos=40, feed=200, feed_type='feed_rate', dir5a='ccw'))

    def test_recorded_slide_angles_turn_exactly_the_cam_steps(self):
        """INDEPENDENT: the 482 recorded Slide A angles (both directions, steps down to 0.001) as one
        simultaneous cut with dir5a from the step sign: no stop, every A word turns the control by
        CAM's step within the rounding of the two positions."""
        angles = [case['state']['apos'] for case in
                  json.loads((ROOT / 'tests/fixtures/slide_rotary.json').read_text())['cases']]
        program = started(angles[0])
        current, previous_cam = round(angles[0] % 360, 3), angles[0]
        for number, angle in enumerate(angles[1:]):
            output = program.ev('line_5x', xpos=10 + 0.1 * number, apos=angle, feed=300, feed_type='feed_rate',
                                dir5a='ccw' if angle > previous_cam else 'cw')
            words = [WORD.search(block).groups() for block in output if WORD.search(block)]
            if not words:
                self.assertAlmostEqual(angle, previous_cam, delta=0.0011, msg=output)
                previous_cam = angle
                continue
            mode, target = words[0][0], float(words[0][1])
            self.assertAlmostEqual(travel(current, mode, target), angle - previous_cam, delta=0.0011)
            current, previous_cam = target, angle

    def test_sub_resolution_steps_stop_or_turn_one_step(self):
        """INDEPENDENT: module oracle as a property: a random walk with steps below the output
        resolution and a random direction word either stops the post or turns the control by at
        most one output step; it never posts a long turn."""
        rng = random.Random(540)
        for walk in range(20):
            program = started(20.0)
            current, cam = 20.0, 20.0
            for number in range(60):
                cam += rng.uniform(-0.0009, 0.0009)
                try:
                    output = program.ev('line_5x', xpos=10 + 0.01 * number, apos=cam, feed=300,
                                        feed_type='feed_rate', dir5a=rng.choice(['cw', 'ccw']))
                except UnsupportedGPPL as stop:
                    self.assertIn(WRONG_WAY, str(stop))
                    break
                for block in output:
                    match = WORD.search(block)
                    if match:
                        target = float(match.group(2))
                        self.assertLessEqual(abs(travel(current, match.group(1), target)), 0.0011, block)
                        current = target

    def test_removing_the_stops_is_detected(self):
        """INDEPENDENT: mutation self-check; without the feed-move stop or the link-rapid stop the
        wrong-way cases post."""
        feed = mutate('    if bR1wrongWay\n        call @usr_r1_wrong_way_stop\n    endif\n', '')
        rapid = mutate('    if bR1wrongWay and !(bPostHomed and bPostHomedZ) and !bIndexTurn\n', '    if false\n')

        def feed_case(source):
            program = started(source=source)
            self.assert_wrong_way_stop(
                lambda: program.ev('line_5x', xpos=20, apos=10, feed=200, feed_type='feed_rate', dir5a='ccw'))

        def rapid_case(source):
            program = started(source=source)
            program.ev('line_5x', zpos=40, feed=200, feed_type='feed_link')
            self.assert_wrong_way_stop(lambda: program.ev('move_5x', apos=10, dir5a='ccw'))
        assert_detected(self, feed_case, feed, 'feed-move stop removed')
        assert_detected(self, rapid_case, rapid, 'link-rapid stop removed')


if __name__ == '__main__':
    unittest.main()
