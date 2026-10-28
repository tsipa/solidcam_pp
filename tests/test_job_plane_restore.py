"""A job starts in its machining plane even if the previous job ended with a YZ/ZX arc.

Oracle (INDEPENDENT): G17/G18/G19 are modal on Sinumerik. Cutter compensation and drilling cycles
work in the active plane (CYCLE81 drills along the plane's applicate axis), so an XY job after a
G19 arc must re-select G17 before it moves.
"""
import os
import re
import unittest
from unittest import mock

from program_session import Program, require_nc_stream
from test_offline import PP
from test_post_homing_reposition import Session

YZ_ARC = dict(arc_plane='yz', arc_direction='ccw', arc_size=90, radius=10,
              xstart=12, ystart=10, zstart=0, xcenter=12, ycenter=0, zcenter=0,
              xcenter_rel=0, ycenter_rel=-10, zcenter_rel=0)


def yz_arc(session):
    session.engine.set(**YZ_ARC)
    return session.step('arc_yz', ['ypos', 'zpos'], ypos=0, zpos=10)


def job_after_yz_arc(source=None, machine_plane='xy'):
    session = Session(source)
    arc = yz_arc(session)
    session.step('end_of_job')
    session.engine.set(machine_plane=machine_plane)
    session.step('start_of_job')
    return session, arc


def planes(output):
    return re.findall(r'\bG(1[789])\b', ' '.join(output))


class JobPlaneRestoreTests(unittest.TestCase):
    def test_first_move_after_yz_arc_reselects_g17(self):
        session, arc = job_after_yz_arc()
        self.assertTrue(arc[0].startswith('G3 G19'), arc)
        first = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=30, ypos=40, zpos=5)
        self.assertEqual(first, ['G0 G17 X30 Y40', 'Z5'])

    def test_drill_cycle_after_yz_arc_runs_in_g17(self):
        session, _ = job_after_yz_arc()
        session.engine.set(drill_type='g81', drill_upper_z=12, drill_clearance_z=30, drill_lower_z=-15,
                           safety=2, G81='g81', G82='g82', G83='g83', G84='g84', G86='g86')
        output = session.step('drill', ['xpos', 'ypos'], xpos=30, ypos=40)
        text = '\n'.join(output)
        self.assertIn('G17', text, output)
        self.assertLess(text.index('G17'), text.index('MCALL CYCLE81'), output)

    def test_empty_or_unknown_machine_plane_falls_back_to_g17(self):
        for machine_plane in ('', 'unknown'):
            with self.subTest(machine_plane=machine_plane):
                session, _ = job_after_yz_arc(machine_plane=machine_plane)
                first = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=30, ypos=40, zpos=5)
                self.assertEqual(first, ['G0 G17 X30 Y40', 'Z5'])

    def test_yz_job_starts_in_g19(self):
        session = Session()
        session.step('end_of_job')
        session.engine.set(machine_plane='yz')
        session.step('start_of_job')
        first = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=30, ypos=40, zpos=5)
        self.assertEqual(planes(first), ['19'], first)

    def test_compensation_after_yz_arc_in_the_same_job_is_selected_in_g17(self):
        session = Session()
        session.engine.set(COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off', iCompActive=40)
        yz_arc(session)
        session.step('compensation', side='comp_left')
        output = session.step('line_5x', ['xpos'], xpos=50, feed_type='feed_rate')
        self.assertRegex(' '.join(output), r'\bG17\b.*\bG41\b', output)
        session.step('compensation', side='comp_off')
        session.step('line_5x', ['ypos'], ypos=5, feed_type='feed_rate')
        session.step('compensation', side='comp_right')
        rapid = session.step('move_5x', ['xpos', 'ypos'], xpos=60, ypos=10)
        self.assertEqual(planes(rapid), [], rapid)   # plane already G17: no repeat
        self.assertIn('G42', ' '.join(rapid))

    def test_compensation_off_after_yz_arc_keeps_the_arc_plane(self):
        session = Session()
        session.engine.set(COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off', iDiametercomp=41, iCompActive=41)
        yz_arc(session)
        session.step('compensation', side='comp_off')
        output = session.step('line_5x', ['xpos'], xpos=50, feed_type='feed_rate')
        self.assertEqual(planes(output), [], output)

    def test_side_change_after_a_yz_arc_restores_the_job_plane(self):
        # The YZ arc already changed the plane with TRC active. Staying in G19 would compensate the
        # X/Y moves in the YZ plane (cut one radius off, silently); 'G17 G42' either works or alarms.
        session = Session()
        session.engine.set(COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off', iDiametercomp=41, iCompActive=41)
        yz_arc(session)
        session.step('compensation', side='comp_right')
        output = session.step('line_5x', ['ypos'], ypos=40, feed_type='feed_rate')
        self.assertEqual(planes(output), ['17'], output)
        self.assertIn('G42', ' '.join(output))

    def test_side_change_on_a_rapid_after_a_yz_arc_restores_the_job_plane(self):
        session = Session()
        session.engine.set(COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off', iDiametercomp=41, iCompActive=41)
        yz_arc(session)
        session.step('compensation', side='comp_right')
        output = session.step('move_5x', ['xpos'], xpos=40)
        self.assertEqual(output, ['G0 G17 G42 X40'])

    def test_side_change_in_g17_prints_no_plane_word(self):
        session = Session()
        session.engine.set(COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off', iDiametercomp=41, iCompActive=41)
        session.step('compensation', side='comp_right')
        output = session.step('line_5x', ['ypos'], ypos=40, feed_type='feed_rate')
        self.assertEqual(output, ['G42 Y40'])

    def test_first_tool_selection_after_yz_arc_restores_g17(self):
        program = Program()
        program.start()
        program.ev('move_5x', xpos=10, ypos=10, zpos=0)
        program.ev('line_5x', zpos=-1, feed=200)
        program.engine.set(**YZ_ARC)
        program.ev('arc_yz', ypos=0, zpos=9, ystart=10, zstart=-1, ycenter=0, zcenter=-1, xcenter=10,
                   xcenter_rel=0, ycenter_rel=-10, zcenter_rel=0)
        program.ev('compensation', side='comp_left')
        self.assertEqual(program.ev('line_5x', xpos=40, feed=200), ['G1 G17 G41 X40'])

    def test_restore_does_not_depend_on_equal_assignment_flags(self):
        # Unverified GPPL rule: an equal-value assignment may clear a change flag (policy clear_user).
        require_nc_stream()
        with mock.patch.dict(os.environ, GPPL_POLICY='change_on_equal_assign=clear_user'):
            session, _ = job_after_yz_arc()
            first = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=30, ypos=40, zpos=5)
        self.assertEqual(first, ['G0 G17 X30 Y40', 'Z5'])

    def test_restore_with_compensation_on_the_first_move_does_not_depend_on_equal_assignment_flags(self):
        # @start_of_job restores G17; the TRC selection asks for it again before any block prints it.
        require_nc_stream()
        with mock.patch.dict(os.environ, GPPL_POLICY='change_on_equal_assign=clear_user'):
            session, _ = job_after_yz_arc()
            session.engine.set(COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off')
            session.step('compensation', side='comp_left')
            first = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=30, ypos=40, zpos=5)
        self.assertEqual(first, ['G0 G17 G41 X30 Y40', 'Z5'])

    def test_no_plane_word_when_plane_did_not_change(self):
        session = Session()
        session.step('end_of_job')
        session.step('start_of_job')
        self.assertEqual(session.step('move_5x', ['xpos', 'ypos'], xpos=30, ypos=40), ['G0 X30 Y40'])

    def test_removing_the_plane_restore_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        start = source.index('\n@start_of_job\n')
        body = source[start:source.index('\nendp', start)]
        restore = '    call @usr_job_plane\n'
        self.assertEqual(body.count(restore), 1, 'plane restore in @start_of_job changed; review this test')
        position = source.index(restore, start)
        broken = source[:position] + source[position + len(restore):]
        session, _ = job_after_yz_arc(broken)
        first = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=30, ypos=40, zpos=5)
        self.assertNotIn('17', planes(first), first)


if __name__ == '__main__':
    unittest.main()
