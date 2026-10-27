"""First rapid of a job: climb before traversing when the new Z is above the current Z.

Oracle (INDEPENDENT): between jobs with the same tool nothing retracts, so the tool stands at the
last programmed Z of the previous job. Traversing XY below the new job's start height risks
hitting clamps or the part; standard order is climb, traverse, descend. When the new Z is lower
(or after a post-inserted homing, where Z is at the top) XY first and then Z stays correct.
"""
import re
import unittest

from test_offline import PP
from test_post_homing_reposition import Session


def same_tool_next_job(last_z, first_move, source=None):
    session = Session(source)
    session.step('line_5x', ['zpos'], zpos=last_z, feed_type='feed_cut')
    session.step('end_of_job')
    session.step('start_of_job')
    changed, values = first_move
    return session.step('move_5x', changed, **values)


class JobStartClimbTests(unittest.TestCase):
    def test_climb_before_traverse_when_new_z_is_higher(self):
        output = same_tool_next_job(5, (['xpos', 'ypos', 'zpos'], dict(xpos=100, ypos=100, zpos=50)))
        self.assertEqual(output, ['G0 Z50', 'X100 Y100'])

    def test_traverse_before_descent_when_new_z_is_lower(self):
        output = same_tool_next_job(60, (['xpos', 'ypos', 'zpos'], dict(xpos=100, ypos=100, zpos=50)))
        self.assertEqual(output, ['G0 X100 Y100', 'Z50'])

    def test_equal_z_keeps_traverse_then_z_order(self):
        output = same_tool_next_job(50, (['xpos', 'ypos', 'zpos'], dict(xpos=100, ypos=100, zpos=50)))
        self.assertEqual(output, ['G0 X100 Y100', 'Z50'])

    def test_climb_without_xy_change_emits_no_empty_block(self):
        output = same_tool_next_job(5, (['zpos'], dict(zpos=50)))
        self.assertEqual(output, ['G0 Z50'])

    def test_after_index_homing_xy_goes_first_even_if_z_is_higher(self):
        session = Session()
        session.engine.set(bR1forceOutput=True)
        session.step('line_5x', ['zpos'], zpos=5, feed_type='feed_cut')
        session.step('end_of_job')
        session.step('tmatrix', angle_4x_around_x=90)
        self.assertIn('G75 Z1=0.', session.step('start_of_job'))
        output = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=50)
        self.assertEqual(output, ['X100 Y100', 'Z50'])

    def test_removing_the_climb_branch_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        condition = re.compile(r'if bFirstMove and change\(zpos\) and bClimbZValid and !bHomedReposition and nLastPathWorkoffset eq iWorkoffset and zpos gt nLastPathZ')
        self.assertEqual(len(condition.findall(source)), 1, 'climb condition changed; review this test')
        broken = condition.sub('if false', source, count=1)
        output = same_tool_next_job(5, (['xpos', 'ypos', 'zpos'], dict(xpos=100, ypos=100, zpos=50)), broken)
        self.assertEqual(output, ['G0 X100 Y100', 'Z50'])


if __name__ == '__main__':
    unittest.main()
