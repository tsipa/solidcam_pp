"""After a homing inserted by the post, X, Y and Z are programmed again before cutting.

Oracle (INDEPENDENT): 'G75 Y1=0 X1=0' leaves X/Y at the machine fixed point and 'G75 Z1=0.' leaves
Z at the top. The axes stay there until they are programmed again, so the next positioning move
must output X, Y and Z even when the CAM values did not change (SolidCAM flags only changed values).
"""
import re
import unittest

from pp_tests.engine import Engine
from test_motion import motion_engine
from test_offline import PP

HOME_XY = 'G75 Y1=0 X1=0'


def blocks(text):
    return [block.strip() for block in text.splitlines() if block.strip()]


def words(block):
    return dict(re.findall(r'\b([XYZ])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', block))


class Session:
    def __init__(self, source=None):
        engine = motion_engine()
        if source is not None:
            candidate = Engine(source)
            candidate.set(**engine.state)
            candidate.changed.update(engine.changed)
            engine = candidate
        self.engine = engine

    def step(self, call, changed=(), **values):
        self.engine.set(**values)
        for key in ('xpos', 'ypos', 'zpos', 'apos', 'bpos', 'feed'):
            self.engine.changed[key] = False
        self.engine.changed.update({key.lower(): True for key in changed})
        self.engine.output.clear()
        self.engine.call(call)
        return blocks(''.join(self.engine.output))


def axes_after_homing(output):
    """X/Y/Z values programmed after the last XY homing block, in order of appearance."""
    index = max(i for i, block in enumerate(output) if block == HOME_XY)
    seen = []
    for block in output[index + 1:]:
        for axis, value in re.findall(r'\b([XYZ])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', block):
            seen.append((axis, float(value)))
    return seen


class PostHomingRepositionTests(unittest.TestCase):
    def rotate_only_scenario(self, source=None):
        session = Session(source)
        session.step('move_5x', ['zpos'], zpos=50, prev_command='@line_5x')
        rotation = session.step('move_5x', ['apos'], apos=90, prev_command='@move_5x')
        approach = session.step('move_5x', ['zpos'], zpos=10, prev_command='@move_5x')
        return rotation, approach

    def assert_xy_restored_before_descent(self, rotation, approach):
        self.assertIn(HOME_XY, rotation)
        programmed = axes_after_homing(rotation) + [
            (axis, float(value)) for block in approach for axis, value in words(block).items()]
        first_descent = next(i for i, (axis, value) in enumerate(programmed) if axis == 'Z' and value < 50)
        before = dict(programmed[:first_descent])
        self.assertEqual((before.get('X'), before.get('Y')), (12.0, 23.0),
                         f'X/Y not reprogrammed after homing before descending: {rotation + approach}')

    def test_rotation_homing_reprograms_unchanged_xy(self):
        rotation, approach = self.rotate_only_scenario()
        self.assert_xy_restored_before_descent(rotation, approach)
        self.assertEqual(axes_after_homing(rotation)[-1], ('Z', 50.0), 'Z must be programmed after homing')

    def test_index_between_jobs_reprograms_unchanged_y(self):
        session = Session()
        session.engine.set(bR1forceOutput=True)
        session.step('end_of_job')
        session.step('tmatrix', angle_4x_around_x=90)
        index = session.step('start_of_job')
        self.assertIn(HOME_XY, index)
        first = session.step('move_5x', ['xpos', 'zpos'], xpos=15, zpos=20)
        xy = [words(block) for block in first if 'X' in words(block) or 'Y' in words(block)]
        self.assertTrue(xy, first)
        self.assertEqual((xy[0].get('X'), xy[0].get('Y')), ('15', '23'), first)
        self.assertIn('Z20', first)

    def test_without_homing_unchanged_axes_stay_modal(self):
        session = Session()
        session.step('move_5x', ['zpos'], zpos=50, prev_command='@line_5x')
        self.assertEqual(session.step('move_5x', ['zpos'], zpos=40, prev_command='@move_5x'), ['Z40'])

    def test_removing_the_homing_marker_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = '    bPostHomed = true\nendp'
        self.assertEqual(source.count(anchor), 1, 'homing marker moved; review this test')
        rotation, approach = self.rotate_only_scenario(source.replace(anchor, 'endp', 1))
        with self.assertRaises(AssertionError):
            self.assert_xy_restored_before_descent(rotation, approach)


if __name__ == '__main__':
    unittest.main()
