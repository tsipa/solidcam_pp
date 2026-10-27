"""First rapid of a job: climb before traversing when the new Z is above the current Z.

Oracle (INDEPENDENT): between jobs with the same tool nothing retracts, so the tool stands at the
last programmed Z of the previous job. Traversing XY below the new job's start height risks
hitting clamps or the part; standard order is climb, traverse, descend. When the new Z is lower
(or after a post-inserted homing, where Z is at the top) XY first and then Z stays correct.
"""
import re
import unittest

from program_session import Program
from test_offline import PP
from test_post_homing_reposition import Session


def same_tool_next_job(last_z, first_move, source=None):
    session = Session(source)
    session.step('line_5x', ['zpos'], zpos=last_z, feed_type='feed_cut')
    session.step('end_of_job')
    session.step('start_of_job')
    changed, values = first_move
    output = session.step('move_5x', changed, **values)
    same_tool_next_job.last_engine = session.engine
    return output


def drill_job_then(next_z, rtp=30, drill_z=10, source=None):
    """A same-tool drill job (the machine ends at RTP), then the next job's first rapid."""
    program = Program(source=source)
    program.start()
    program.ev('move_5x', xpos=10, ypos=10, zpos=50)
    program.ev('end_of_job')
    program.ev('start_of_job', job_name='drill')
    program.ev('drill', xpos=20, ypos=20, zpos=drill_z, drill_type='g81', drill_clearance_z=rtp,
               drill_upper_z=0, drill_lower_z=-10, feed=80)
    program.ev('drill_point', xpos=30, ypos=20)
    program.ev('end_drill')
    program.ev('end_of_job')
    program.ev('start_of_job', job_name='op3')
    return program.ev('move_5x', xpos=100, ypos=100, zpos=next_z)


def index_job_then(next_z, clearance, homing=None, source=None):
    """Simple-rotation index between same-tool jobs, then the next job's first rapid."""
    options = dict(i4xIndexClearanceMode=clearance)
    program = Program(options=options, source=source)
    program.start()
    program.ev('move_5x', xpos=10, ypos=10, zpos=5)
    program.ev('line_5x', zpos=-1, feed=100)
    program.ev('move_5x', zpos=5)
    program.ev('end_of_job')
    program.ev('tmatrix', angle_4x_around_x=90)
    program.engine.state['btmatrixindexpending'] = True
    if homing is not None:
        program.engine.state['shomestrrot'] = homing
    index = program.ev('start_of_job', job_name='op2', tool_z_level=40, tool_start_plane=45)
    return index, program.ev('move_5x', xpos=100, ypos=100, zpos=next_z)


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
        raw = ''.join(same_tool_next_job.last_engine.output)
        self.assertEqual([line for line in raw.split('\n')[1:] if not line.strip()], [], repr(raw))

    def test_climb_counts_as_the_first_move(self):
        session = Session()
        session.step('line_5x', ['zpos'], zpos=5, feed_type='feed_cut')
        session.step('end_of_job')
        session.step('start_of_job')
        self.assertEqual(session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=50),
                         ['G0 Z50', 'X100 Y100'])
        self.assertEqual(session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=110, ypos=110, zpos=20),
                         ['X110 Y110 Z20'])

    def test_rotation_with_homing_on_the_first_rapid_does_not_climb(self):
        session = Session()
        session.step('line_5x', ['zpos'], zpos=5, feed_type='feed_cut')
        session.step('end_of_job')
        session.step('start_of_job')
        output = session.step('move_5x', ['apos', 'xpos', 'ypos', 'zpos'], apos=30, xpos=100, ypos=100, zpos=50,
                              prev_command='@start_of_job')
        self.assertEqual(output[-2:], ['X100 Y100', 'Z50'], output)

    def test_after_index_homing_xy_goes_first_even_if_z_is_higher(self):
        session = Session()
        session.engine.set(bR1forceOutput=True)
        session.step('line_5x', ['zpos'], zpos=5, feed_type='feed_cut')
        session.step('end_of_job')
        session.step('tmatrix', angle_4x_around_x=90)
        self.assertIn('G75 Z1=0.', session.step('start_of_job'))
        output = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=50)
        self.assertEqual(output, ['X100 Y100', 'Z50'])

    def test_after_a_drill_job_the_current_z_is_rtp(self):
        # CYCLE81 ends at RTP=30, above the drill rapid Z10: a lower next start must not descend first.
        self.assertEqual(drill_job_then(20), ['X100 Y100', 'Z20'])
        self.assertEqual(drill_job_then(50), ['Z50', 'X100 Y100'])

    def test_index_without_homing_keeps_the_climb(self):
        index, first = index_job_then(50, clearance=0, homing='')
        self.assertNotIn('G75 Z1=0.', index)
        self.assertEqual(first, ['Z50', 'X100 Y100'])

    def test_index_clearance_move_sets_the_current_z(self):
        index, first = index_job_then(50, clearance=2)
        self.assertEqual(index[-2:], ['Z45', 'MSG("op2")'], index)
        self.assertEqual(first, ['Z50', 'X100 Y100'])
        self.assertEqual(index_job_then(30, clearance=2)[1], ['X100 Y100', 'Z30'])

    def test_work_offset_change_between_jobs_does_not_climb(self):
        # Z of another fixture offset is not comparable: traverse first as before.
        session = Session()
        session.engine.set(first_tool=True, bLimit_3axis=False, bWorkoffsettc=True, iWorkOffsetmode=2,
                           home_user_name='P54')
        session.step('line_5x', ['zpos'], zpos=60, feed_type='feed_cut')
        session.step('end_of_job')
        session.engine.set(home_user_name='P55')
        self.assertIn('G55', ' '.join(session.step('start_of_job')))
        self.assertEqual(session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=70),
                         ['X100 Y100', 'Z70'])

    def test_removing_the_climb_branch_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        condition = re.compile(r'if bFirstMove and change\(zpos\) and bClimbZValid and !bHomedReposition and nLastPathWorkoffset eq iWorkoffset and zpos gt nLastPathZ')
        self.assertEqual(len(condition.findall(source)), 1, 'climb condition changed; review this test')
        broken = condition.sub('if false', source, count=1)
        output = same_tool_next_job(5, (['xpos', 'ypos', 'zpos'], dict(xpos=100, ypos=100, zpos=50)), broken)
        self.assertEqual(output, ['G0 X100 Y100', 'Z50'])


if __name__ == '__main__':
    unittest.main()
