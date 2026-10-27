"""Homing and optional-stop options: every G75 homing point and every M1 point can be switched off.

Owner rule 2026-10-27: the G75 homings and the M1 optional stops are safety; each is a user option,
on by default (bHomebegin, bHometc, bHomeend, bHomerotv, bHomeroth; bOptstptc, bOptstpjob,
bOptstpindex). Switching one off removes exactly that point and nothing else. The M1 between two
operations of the same tool (bOptstpjob) is not repeated where the boundary already stopped
(the M0 of bStopM00, the M1 of an A index).

The tests read the blocks each event returns (no skipline joining), so they run on both engines.
"""
import unittest

from program_session import Program
from support import assert_detected, mutate

HOMING = ['G75 Z1=0.', 'G75 Y1=0 X1=0']
HOMING_OPTIONS = ('bHomebegin', 'bHometc', 'bHomeend', 'bHomerotv', 'bHomeroth')
STOP_OPTIONS = ('bOptstptc', 'bOptstpjob', 'bOptstpindex')


def program(source=None, cam=None, **options):
    return Program(options=options, cam=cam, source=source)


def first_job(source=None, cam=None, **options):
    """Program start, tool 1, job op1 cut at X10 Y10, retracted to Z50; returns (program, blocks)."""
    p = program(source, cam, **options)
    blocks = p.start(tool=1, next_tool=2, next_job_tool_number=1)
    blocks += p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
    blocks += p.ev('line', zpos=-2, feed=200)
    blocks += p.ev('rapid_move', zpos=50)
    return p, blocks


def homings(blocks):
    return [block for block in blocks if block.startswith('G75')]


class DefaultTests(unittest.TestCase):
    def test_all_homing_and_stop_options_are_on_by_default(self):
        """CHARACTERIZATION: owner decision 2026-10-27, homings and optional stops on by default."""
        state = program().engine.state
        self.assertEqual({name: state[name.lower()] for name in HOMING_OPTIONS + STOP_OPTIONS},
                         dict.fromkeys(HOMING_OPTIONS + STOP_OPTIONS, True))


class HomingOptionTests(unittest.TestCase):
    def test_program_start_homing(self):
        """INDEPENDENT: bHomebegin = sHomestrbegin at the program start."""
        self.assertEqual(program().ev('start_program'), HOMING)
        self.assertEqual(program(bHomebegin=False).ev('start_program'), [])

    def end_blocks(self, **options):
        p, _ = first_job(**options)
        p.ev('end_of_job', next_job_tool_number=0)
        return p.ev('end_program')

    def test_program_end_homing(self):
        """INDEPENDENT: bHomeend = sHomestrend between M5 and M30; off keeps M9, M5 and M30."""
        self.assertEqual(self.end_blocks(), ['M9', 'M5', *HOMING, 'M30'])
        self.assertEqual(self.end_blocks(bHomeend=False), ['M9', 'M5', 'M30'])

    def second_tool_change(self, **options):
        p, _ = first_job(**options)
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
        return p.ev('start_of_job', job_name='op2', next_job_tool_number=0)

    def test_tool_change_homing(self):
        """INDEPENDENT: bHometc = sHomestrtc after M5, before M1 and T; off keeps M5, M1 and the change."""
        on = self.second_tool_change()
        self.assertEqual(on[:6], ['M9', 'M5', *HOMING, 'M1', ';'])
        off = self.second_tool_change(bHometc=False)
        self.assertEqual(off[:4], ['M9', 'M5', 'M1', ';'])
        self.assertEqual(homings(off), [])
        self.assertIn('T2', off)
        self.assertIn('M06', off)

    def test_first_rapid_homing(self):
        """INDEPENDENT: bHomerotv = sHomestrrotv at the first rapid of the program. Off, the head
        homing selection still runs: Z switches to its 4-decimal format (PP-006)."""
        for value, expected in ((True, HOMING), (False, [])):
            with self.subTest(bHomerotv=value):
                p = program(bHomerotv=value)
                blocks = p.start(tool=1, next_tool=2)
                self.assertEqual(homings(blocks[blocks.index('MSG("op1")'):]), expected)
                self.assertEqual(p.engine.state['zpos_f'], '5.4')

    def a_turn(self, **options):
        p = program(**options)
        p.start(tool=1, next_tool=2, next_job_tool_number=0)
        p.ev('move_5x', xpos=10, ypos=0, zpos=40, apos=0, dir5a='ccw')
        return p, p.ev('move_5x', apos=90, dir5a='ccw', prev_command='@move_5x')

    def test_a_turn_homing(self):
        """INDEPENDENT: bHomeroth = sHomestrroth before an A turn outside a CAM link; off, A turns at
        the current height in its own block."""
        _, on = self.a_turn()
        self.assertEqual(on[:3], [*HOMING, 'G0 A=ACP(90)'])
        _, off = self.a_turn(bHomeroth=False)
        self.assertEqual(off, ['G0 A=ACP(90)'])

    def test_index_clearance_homing_does_not_follow_the_a_turn_option(self):
        """INDEPENDENT: the index clearance is i4xIndexClearanceMode (0 = home), not bHomeroth."""
        p, _ = first_job(bHomeroth=False)
        p.ev('end_of_job', next_job_tool_number=1)
        index = p.ev('fourth_axis', angle=45, angle_4x_around_x_dir='ccw')
        self.assertEqual(index, ['M1', *HOMING, 'A=ACP(45)'])

    def test_removing_a_homing_gate_is_detected(self):
        """INDEPENDENT: mutation self-check; a homing that ignores its option fails the guards."""
        checks = {
            'bHomebegin ignored': ('    if bHomebegin\n', '    if true\n', self.check_start_off),
            'bHomeroth ignored': ('        if bHomeroth\n', '        if true\n', self.check_a_turn_off),
        }
        for label, (old, new, check) in checks.items():
            with self.subTest(mutant=label):
                assert_detected(self, check, mutate(old, new), label)

    def check_start_off(self, source):
        self.assertEqual(program(source, bHomebegin=False).ev('start_program'), [])

    def check_a_turn_off(self, source):
        p = program(source, bHomeroth=False)
        p.start(tool=1, next_tool=2, next_job_tool_number=0)
        p.ev('move_5x', xpos=10, ypos=0, zpos=40, apos=0, dir5a='ccw')
        self.assertEqual(p.ev('move_5x', apos=90, dir5a='ccw', prev_command='@move_5x'), ['G0 A=ACP(90)'])


class OptionalStopOptionTests(unittest.TestCase):
    def second_same_tool_job(self, source=None, cam=None, **options):
        p, _ = first_job(source, cam, **options)
        boundary = p.ev('end_of_job', next_job_tool_number=1)
        if cam and cam.get('bstopm00'):
            p.engine.state['bstopm00'] = False
        return boundary, p.ev('start_of_job', job_name='op2', next_job_tool_number=0)

    def test_m1_between_operations_of_the_same_tool(self):
        """INDEPENDENT: bOptstpjob = M1 after the next operation's message (shown during the stop)."""
        self.assertEqual(self.second_same_tool_job()[1], ['MSG("op2")', 'M1'])
        self.assertEqual(self.second_same_tool_job(bOptstpjob=False)[1], ['MSG("op2")'])

    def check_no_m1_after_m0(self, source=None):
        boundary, start = self.second_same_tool_job(source, cam=dict(bstopm00=True, sstopmessage='CHECK'))
        self.assertIn('M0', boundary)
        self.assertNotIn('M1', start, 'second stop after the M0 of the same boundary')

    def test_no_m1_after_the_m0_of_the_same_boundary(self):
        """INDEPENDENT: the M0 stop (bStopM00) already stops between the operations."""
        self.check_no_m1_after_m0()

    def test_one_stop_at_an_index_between_operations(self):
        """INDEPENDENT: a CoordSys index at the job start prints its M1; the job M1 is not repeated."""
        p, _ = first_job()
        p.ev('end_of_job', next_job_tool_number=1)
        p.ev('tmatrix', angle_4x_around_x=90, angle_4x_around_x_dir='ccw')
        start = p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
        self.assertEqual(start.count('M1'), 1, start)
        turn = next(i for i, block in enumerate(start) if 'A=ACP(90)' in block)
        self.assertLess(start.index('M1'), turn)

    def test_index_m1_option(self):
        """INDEPENDENT: bOptstpindex = M1 before an A index turn."""
        for value, expected in ((True, ['M1', *HOMING, 'A=ACP(45)']), (False, [*HOMING, 'A=ACP(45)'])):
            with self.subTest(bOptstpindex=value):
                p, _ = first_job(bOptstpindex=value)
                p.ev('end_of_job', next_job_tool_number=1)
                self.assertEqual(p.ev('fourth_axis', angle=45, angle_4x_around_x_dir='ccw'), expected)

    def test_tool_change_keeps_its_own_single_stop(self):
        """INDEPENDENT: a tool change stops once (bOptstptc, before T); no job M1 after its message."""
        p, _ = first_job()
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
        start = p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
        self.assertEqual(start.count('M1'), 1, start)
        self.assertLess(start.index('M1'), start.index('T2'))
        self.assertEqual(program(bOptstptc=False).ev('start_program').count('M1'), 0)

    def test_repeating_the_stop_after_an_m0_is_detected(self):
        """INDEPENDENT: mutation self-check; a job M1 that ignores the boundary stop fails the guard."""
        mutant = mutate('        if bOptstpjob and !bBoundaryStop\n', '        if bOptstpjob\n')
        assert_detected(self, self.check_no_m1_after_m0, mutant, 'M1 after M0', match='second stop')


if __name__ == '__main__':
    unittest.main()
