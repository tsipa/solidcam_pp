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
                 prev_command='@line_5x', dir5a='cw')
    return session


class InverseTimeFeedTests(unittest.TestCase):
    def test_wrap_helix_block(self):
        session = start_at(12, 0, 25)
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertEqual(len(output), 1, output)
        self.assertTrue(output[0].startswith('G1 G93 X22 A=ACN(30) F'), output)
        expected = 200 / math.hypot(10, 25 * math.pi / 6)
        self.assertAlmostEqual(feed_word(output[0]), expected, delta=0.0006)

    def test_pure_rotation_block(self):
        session = start_at(12, 0, 25)
        output = session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertAlmostEqual(feed_word(output[0]), 200 / (25 * math.pi / 6), delta=0.0006)

    def test_lateral_motion_uses_part_frame_sign(self):
        steps = json.loads((ROOT / 'tests/fixtures/shit2_contiguous_link.json').read_text())['steps']
        a, b = steps[2]['set'], steps[3]['set']
        session = start_at(a['xpos'], a['ypos'], a['zpos'], apos=a['apos'])
        output = session.step('line_5x', ['xpos', 'ypos', 'zpos', 'apos'], xpos=b['xpos'], ypos=b['ypos'],
                              zpos=b['zpos'], apos=b['apos'], feed=600, dir5a='ccw', feed_type='feed_cut')
        length = path_length((a['xpos'], a['ypos'], a['zpos'], a['apos']), (b['xpos'], b['ypos'], b['zpos'], b['apos']))
        self.assertAlmostEqual(feed_word(output[-1]), 600 / length, delta=0.001)
        wrong_sign = path_length((a['xpos'], a['ypos'], a['zpos'], -a['apos']), (b['xpos'], b['ypos'], b['zpos'], -b['apos']))
        self.assertGreater(abs(600 / wrong_sign - 600 / length), 0.1, 'test would not detect a sign error')

    def test_varying_radius_block_matches_numeric_path(self):
        session = start_at(0, 5, 40)
        output = session.step('line_5x', ['xpos', 'ypos', 'zpos', 'apos'], xpos=3, ypos=-4, zpos=18, apos=47,
                              feed=300, dir5a='cw', feed_type='feed_cut')
        length = path_length((0, 5, 40, 0), (3, -4, 18, 47))
        self.assertAlmostEqual(feed_word(output[0]), 300 / length, delta=0.002)

    def test_non_rotating_line_returns_to_g94_with_feed(self):
        session = start_at(12, 0, 25)
        session.step('line_5x', ['xpos', 'apos'], xpos=22, apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertEqual(session.step('line_5x', ['xpos'], xpos=30), ['G94 X30 F200'])

    def test_end_of_job_leaves_g93(self):
        session = start_at(12, 0, 25)
        session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertEqual(session.step('end_of_job'), ['G94'])
        self.assertEqual(session.step('end_of_job'), [])

    def test_feed_emulated_rapid_leaves_g93_first(self):
        session = start_at(12, 0, 25, bSyncdrapid=False, job_type='3-d model')
        session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        output = session.step('move_5x', ['zpos'], zpos=50, prev_command='@line_5x')
        self.assertEqual(output[0], 'G94', output)

    def test_arc_after_rotation_leaves_g93_first(self):
        session = start_at(10, 0, 25)
        session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        session.engine.set(arc_plane='xy', arc_direction='ccw', arc_size=90, iArcmode=2, radius=10,
                           xstart=10, ystart=0, zstart=25, xcenter=0, ycenter=0, zcenter=25,
                           xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)
        output = session.step('arc', ['xpos', 'ypos'], xpos=0, ypos=10)
        self.assertEqual(output[0], 'G94', output)
        self.assertTrue(output[1].startswith('G3'), output)

    def test_zero_radius_rotation_is_clamped(self):
        session = start_at(12, 0, 0)
        output = session.step('line_5x', ['apos'], apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertEqual(feed_word(output[0]), 59999.99)

    def test_programmed_feed_mode_keeps_g94(self):
        session = start_at(12, 0, 25, i4xFeedMode=0)
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertNotIn('G93', ' '.join(output))
        self.assertEqual(feed_word(output[0]), 200)

    def test_unknown_start_after_homing_falls_back_to_g94(self):
        session = start_at(12, 0, 25)
        session.engine.set(bFeedPrevValid=False)
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertNotIn('G93', ' '.join(output))

    def test_removing_inverse_time_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = 'if i4xFeedMode eq 1 and change(nR1pos) and bFeedPrevValid'
        self.assertEqual(source.count(anchor), 1, 'inverse-time condition changed; review this test')
        session = Session(source.replace(anchor, 'if false', 1))
        session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=12, ypos=0, zpos=25, prev_command='@line_5x')
        output = session.step('line_5x', ['xpos', 'apos', 'feed'], xpos=22, apos=30, feed=200, dir5a='cw', feed_type='feed_cut')
        self.assertEqual(feed_word(output[0]), 200)


if __name__ == '__main__':
    unittest.main()
