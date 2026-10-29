"""A job runs in G17, also when SolidCAM leaves machine_plane empty or unknown.

Oracle (INDEPENDENT): G17/G18/G19 are modal on Sinumerik, so a plane word is needed only when the
plane changes. On this machine G18/G19 move the tool length compensation of a milling tool from Z to
Y/X (SD42940 $SC_TOOL_LENGTH_CONST = 0), so a YZ/ZX machining plane or arc stops the post
(usr_xy_plane_check, usr_side_arc_stop) and every job runs in G17: iMplane stays 17 when
machine_plane is empty or unknown. The plane restore after a YZ/ZX arc was deleted with the YZ/ZX
code 2026-10-28.
"""
import re
import unittest

from program_session import Program
from test_post_homing_reposition import Session


def two_jobs(machine_plane):
    """Two same-tool jobs whose machine_plane SolidCAM sends as `machine_plane`: their NC blocks."""
    program = Program(cam=dict(machine_plane=machine_plane))
    output = program.start(machine_plane=machine_plane)
    output += program.ev('move_5x', xpos=30, ypos=40, zpos=5)
    output += program.ev('line_5x', zpos=-1, feed=200)
    output += program.ev('end_of_job')
    output += program.ev('start_of_job', job_name='op2', machine_plane=machine_plane)
    return output + program.ev('move_5x', xpos=50, ypos=40, zpos=5)


def planes(output):
    return re.findall(r'\bG(1[789])\b', ' '.join(output))


class JobPlaneRestoreTests(unittest.TestCase):
    def test_empty_or_unknown_machine_plane_falls_back_to_g17(self):
        xy = two_jobs('xy')
        self.assertEqual(planes(xy), ['17', '17'], xy)   # tool change safety block, first G0 of the job
        for machine_plane in ('', 'unknown'):
            with self.subTest(machine_plane=machine_plane):
                self.assertEqual(two_jobs(machine_plane), xy)

    def test_side_change_in_g17_prints_no_plane_word(self):
        session = Session()
        session.engine.set(COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off', iDiametercomp=41, iCompActive=41)
        session.step('compensation', side='comp_right')
        output = session.step('line_5x', ['ypos'], ypos=40, feed_type='feed_rate')
        self.assertEqual(output, ['G42 Y40'])

    def test_no_plane_word_when_plane_did_not_change(self):
        session = Session()
        session.step('end_of_job')
        session.step('start_of_job')
        self.assertEqual(session.step('move_5x', ['xpos', 'ypos'], xpos=30, ypos=40), ['G0 X30 Y40'])


if __name__ == '__main__':
    unittest.main()
