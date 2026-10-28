"""Rotating G1 blocks are posted in G93 (inverse time) with F = feed / path length on the part.

Oracle (INDEPENDENT): under G94 a Sinumerik applies F to the linear axes only (deg/min for A alone),
so a rotating block would not cut at the CAM feed. In G93 F is 1/time of the block. The A axis lies
along X with its centre at Y0 Z0; the path is measured in the part frame, part = Rx(-A) * machine.
That sign is the one in which the recorded SolidCAM rotary link (tests/fixtures/shit2_contiguous_link.json)
is a straight, evenly stepped line; the opposite sign bends it.
"""
import json
import math
import re
import unittest

from program_session import Program
from test_offline import PP, ROOT
from test_post_homing_reposition import Session


def part_point(x, y, z, a):
    t = math.radians(a)
    return x, y * math.cos(t) + z * math.sin(t), -y * math.sin(t) + z * math.cos(t)


def path_length(start, end, steps=2000):
    """Independent numeric length of the linearly interpolated machine move, measured on the part."""
    total, previous = 0.0, part_point(*start)
    for i in range(1, steps + 1):
        u = i / steps
        point = part_point(*[s + (e - s) * u for s, e in zip(start, end)])
        total += math.dist(previous, point)
        previous = point
    return total


def feed_word(block):
    return float(re.search(r'\bF([\d.]+)', block).group(1))


def start_at(x, y, z, apos=0, **state):
    session = Session()
    session.engine.set(**state)
    session.step('move_5x', ['xpos', 'ypos', 'zpos', 'apos'], xpos=x, ypos=y, zpos=z, apos=apos,
                 prev_command='@line_5x', dir5a='ccw')
    return session


class InverseTimeFeedTests(unittest.TestCase):
    def test_wrap_helix_block(self):
        session = start_at(12, 0, 25)
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertEqual(len(output), 1, output)
        self.assertTrue(output[0].startswith('G1 G93 X22 A=ACP(30) F'), output)
        expected = 200 / math.hypot(10, 25 * math.pi / 6)
        self.assertAlmostEqual(feed_word(output[0]), expected, delta=0.0006)

    def test_pure_rotation_block(self):
        session = start_at(12, 0, 25)
        output = session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertAlmostEqual(feed_word(output[0]), 200 / (25 * math.pi / 6), delta=0.0006)

    def test_lateral_motion_uses_part_frame_sign(self):
        steps = json.loads((ROOT / 'tests/fixtures/shit2_contiguous_link.json').read_text())['steps']
        a, b = steps[2]['set'], steps[3]['set']
        session = start_at(a['xpos'], a['ypos'], a['zpos'], apos=a['apos'])
        output = session.step('line_5x', ['xpos', 'ypos', 'zpos', 'apos'], xpos=b['xpos'], ypos=b['ypos'],
                              zpos=b['zpos'], apos=b['apos'], feed=600, dir5a='ccw', feed_type='feed_rate')
        length = path_length((a['xpos'], a['ypos'], a['zpos'], a['apos']), (b['xpos'], b['ypos'], b['zpos'], b['apos']))
        self.assertAlmostEqual(feed_word(output[-1]), 600 / length, delta=0.001)
        wrong_sign = path_length((a['xpos'], a['ypos'], a['zpos'], -a['apos']), (b['xpos'], b['ypos'], b['zpos'], -b['apos']))
        self.assertGreater(abs(600 / wrong_sign - 600 / length), 0.1, 'test would not detect a sign error')

    def test_varying_radius_block_matches_numeric_path(self):
        session = start_at(0, 5, 40)
        output = session.step('line_5x', ['xpos', 'ypos', 'zpos', 'apos'], xpos=3, ypos=-4, zpos=18, apos=47,
                              feed=300, dir5a='ccw', feed_type='feed_rate')
        length = path_length((0, 5, 40, 0), (3, -4, 18, 47))
        self.assertAlmostEqual(feed_word(output[0]), 300 / length, delta=0.002)

    def test_non_rotating_line_returns_to_g94_with_feed(self):
        session = start_at(12, 0, 25)
        session.step('line_5x', ['xpos', 'apos'], xpos=22, apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertEqual(session.step('line_5x', ['xpos'], xpos=30), ['G94 X30 F200'])

    def test_end_of_job_leaves_g93_and_reprograms_feed(self):
        session = start_at(12, 0, 25)
        session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertEqual(session.step('end_of_job'), ['G94 F200'])
        self.assertEqual(session.step('end_of_job'), [])

    def test_next_job_first_feed_move_has_feed_after_g93(self):
        # Sinumerik needs F after G93 -> G94; a same-feed plunge without F would run at the inverse value.
        session = start_at(12, 0, 25)
        session.step('line_5x', ['apos'], apos=30, feed=300, dir5a='ccw', feed_type='feed_rate')
        session.step('end_of_job')
        session.step('start_of_job')
        session.step('move_5x', ['zpos'], zpos=40, prev_command='@end_of_job')
        output = session.step('line_5x', ['zpos'], zpos=-2, feed=300, feed_type='feed_rate')
        self.assertEqual(output, ['G1 Z-2 F300'])

    def test_next_job_first_arc_has_feed_after_g93(self):
        session = start_at(10, 0, 25)
        session.step('line_5x', ['apos'], apos=30, feed=300, dir5a='ccw', feed_type='feed_rate')
        session.step('end_of_job')
        session.step('start_of_job')
        session.engine.set(arc_plane='xy', arc_direction='ccw', arc_size=90, radius=10,
                           xstart=10, ystart=0, zstart=25, xcenter=0, ycenter=0, zcenter=25,
                           xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)
        output = session.step('arc', ['xpos', 'ypos'], xpos=0, ypos=10, feed=300)
        self.assertTrue(output[-1].endswith('F300'), output)

    def test_feed_emulated_rapid_leaves_g93_first(self):
        session = start_at(12, 0, 25, bSyncdrapid=False, job_type='3-d model')
        session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        output = session.step('move_5x', ['zpos'], zpos=50, prev_command='@line_5x')
        self.assertEqual(output[0], 'G94 F200', output)

    def test_arc_after_rotation_leaves_g93_first(self):
        session = start_at(10, 0, 25)
        session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        session.engine.set(arc_plane='xy', arc_direction='ccw', arc_size=90, radius=10,
                           xstart=10, ystart=0, zstart=25, xcenter=0, ycenter=0, zcenter=25,
                           xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)
        output = session.step('arc', ['xpos', 'ypos'], xpos=0, ypos=10)
        self.assertEqual(output[0], 'G94 F200', output)
        self.assertTrue(output[1].startswith('G3'), output)

    def test_zero_radius_rotation_is_clamped(self):
        session = start_at(12, 0, 0)
        output = session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertEqual(feed_word(output[0]), 59999.99)

    def test_programmed_feed_mode_keeps_g94(self):
        session = start_at(12, 0, 25, i4xFeedMode=0)
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertNotIn('G93', ' '.join(output))
        self.assertEqual(feed_word(output[0]), 200)

    def test_unknown_start_after_homing_falls_back_to_g94(self):
        # An index between jobs homes the axes; the first rotating feed move has no known start point.
        session = start_at(12, 0, 25)
        session.engine.set(bR1forceOutput=True)
        session.step('end_of_job')
        session.step('tmatrix', angle_4x_around_x=90)
        self.assertIn('G75 Z1=0.', session.step('start_of_job'))
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertNotIn('G93', ' '.join(output))
        self.assertTrue(output[-1].endswith('F200'), output)

    def test_negative_direction_uses_the_travel_the_control_makes(self):
        # 0 -> -30 posted as ACN(330): the control turns 30 degrees negative, not the 330 between the positions.
        session = start_at(12, 0, 25)
        output = session.step('line_5x', ['apos'], apos=-30, feed=200, dir5a='cw', feed_type='feed_rate')
        self.assertIn('A=ACN(330)', output[0])
        self.assertAlmostEqual(feed_word(output[0]), 200 / (25 * math.radians(30)), delta=0.0006)

    def test_crossing_180_uses_modulo_travel_not_the_cam_difference(self):
        # A link 179 -> 541 counter-clockwise: the control drops the whole turn (ACP(181), 2 degrees of
        # travel), so F is for 2 degrees, not for CAM's 362. A cutting block would stop (full turn).
        session = start_at(12, 0, 25, apos=179)
        output = session.step('line_5x', ['xpos', 'apos'], xpos=13, apos=541, feed=200, dir5a='ccw', feed_type='feed_link')
        self.assertIn('A=ACP(181)', output[0])
        length = path_length((12, 0, 25, 179), (13, 0, 25, 181))
        self.assertAlmostEqual(feed_word(output[0]), 200 / length, delta=0.01)

    def test_sub_resolution_a_change_is_no_rotation(self):
        # 30 -> 29.99999 -> 30.00001 prints A=30 every time: the control does not turn, so no A word,
        # no G93 and the programmed feed.
        session = start_at(12, 0, 25, apos=30)
        first = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=20, apos=29.99999, feed=300, dir5a='cw',
                             feed_type='feed_rate')
        second = session.step('line_5x', ['xpos', 'apos'], xpos=28, apos=30.00001, feed=300, dir5a='ccw',
                              feed_type='feed_rate')
        for output in (first, second):
            self.assertEqual(len(output), 1, output)
            self.assertNotIn('A=', output[0])
            self.assertNotIn('G93', output[0])
        self.assertEqual(feed_word(first[0]), 300)

    def test_index_without_homing_leaves_no_known_feed_start(self):
        # Clearance mode 1 moves Z and A without homing: the next rotating G1 falls back to G94.
        program = Program(options=dict(i4xIndexClearanceMode=1))
        program.start()
        program.ev('move_5x', xpos=12, ypos=0, zpos=25)
        program.ev('line_5x', xpos=14, apos=30, feed=200)
        program.ev('end_of_job')
        program.ev('tmatrix', angle_4x_around_x=90)
        program.engine.state['btmatrixindexpending'] = True
        program.ev('start_of_job', job_name='op2', tool_z_level=50)
        output = program.ev('line_5x', xpos=16, apos=10, feed=200, dir5a='cw')   # A 120 -> 100
        self.assertNotIn('G93', ' '.join(output))
        self.assertIn('A=ACN(100)', ' '.join(output))

    def test_m00_homing_leaves_no_known_feed_start(self):
        program = Program(options=dict(sHomestrstpsame='8::G75 Z1=0. ;8::G75 Y1=0 X1=0'),
                          cam=dict(bStopM00=True, next_job_tool_number=1))
        program.start()
        program.ev('move_5x', xpos=30, ypos=10, zpos=5)
        program.ev('line_5x', zpos=-2, feed=200)
        program.ev('end_of_job')
        program.ev('start_of_job', job_name='op2')
        output = program.ev('line_5x', xpos=40, ypos=15, zpos=-1, apos=-10, dir5a='cw', feed=200)
        self.assertEqual(output[0], 'G0 X40 Y15')
        self.assertNotIn('G93', ' '.join(output))

    def test_drill_cycle_after_rotation_leaves_g93_with_its_feed(self):
        program = Program()
        program.start()
        program.ev('move_5x', xpos=12, ypos=0, zpos=25)
        program.ev('line_5x', xpos=14, apos=30, feed=200)
        output = program.ev('drill', xpos=30, ypos=0, zpos=30, drill_type='g81', drill_clearance_z=30,
                            drill_upper_z=0, drill_lower_z=-10, feed=80)
        self.assertIn('G94 F80', output)
        self.assertLess(output.index('G94 F80'), next(i for i, b in enumerate(output) if 'CYCLE81' in b), output)

    def test_part_frame_sign_straightens_the_recorded_link(self):
        # Oracle for the sign itself: SolidCAM's rotary link is a straight, evenly stepped line on the part.
        steps = json.loads((ROOT / 'tests/fixtures/shit2_contiguous_link.json').read_text())['steps']
        points = [s['set'] for s in steps if {'xpos', 'ypos', 'zpos', 'apos'} <= set(s['set'])]
        self.assertGreaterEqual(len(points), 4)

        def bend(sign):
            part = [part_point(p['xpos'], p['ypos'], p['zpos'], sign * p['apos']) for p in points]
            return max(math.dist([2 * b - a - c for a, b, c in zip(p0, p1, p2)], [0, 0, 0])
                       for p0, p1, p2 in zip(part, part[1:], part[2:]))
        self.assertLess(bend(1), 0.05)
        self.assertGreater(bend(-1), 0.1)

    def test_removing_inverse_time_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = 'if i4xFeedMode eq 1 and change(nR1pos) and bFeedPrevValid'
        self.assertEqual(source.count(anchor), 1, 'inverse-time condition changed; review this test')
        session = Session(source.replace(anchor, 'if false', 1))
        session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=12, ypos=0, zpos=25, prev_command='@line_5x')
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='ccw', feed_type='feed_rate')
        self.assertEqual(feed_word(output[0]), 200)


if __name__ == '__main__':
    unittest.main()
