"""Homing and optional-stop options: every G75 homing point and every M1 point can be switched off.

Owner rule 2026-10-27: the G75 homings and the M1 optional stops are safety; each is a user option,
on by default (bHomebegin, bHometc, bHomeend, bHomerotv, bHomeroth; bOptstptc, bOptstpjob,
bOptstpindex). Switching one off removes exactly that point and nothing else. The M1 between two
operations of the same tool (bOptstpjob) is not repeated where the boundary already stopped
(the M0 of bStopM00, the M1 of an A index), and an index right after the job M1 adds no second M1.
Without a Z homing at a tool change, compensation still on would run through M06: the post stops.
Owner decision 2026-10-28 (DESIGN-003): an index pending at a tool change has no M1, homing or A block
of its own; the tool change's positioning block turns A after the tool change's homing and M1.

The tests read the blocks each event returns (no skipline joining), so they run on both engines.
"""
import difflib
import unittest

from pp_tests.engine import UnsupportedGPPL
from program_session import Program, require_nc_stream
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


def second_tool_change(**options):
    """first_job, then T2 and its job op2; returns the blocks of that start_of_job."""
    p, _ = first_job(**options)
    p.ev('end_of_job', next_job_tool_number=2)
    p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
    return p.ev('start_of_job', job_name='op2', next_job_tool_number=0)


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
        self.assertEqual(self.end_blocks(), ['M9', 'M5', 'WAITS', *HOMING, 'M30'])
        self.assertEqual(self.end_blocks(bHomeend=False), ['M9', 'M5', 'WAITS', 'M30'])

    def test_tool_change_homing(self):
        """INDEPENDENT: bHometc = sHomestrtc after M5, before M1 and T; off keeps M5, M1 and the change."""
        on = second_tool_change()
        self.assertEqual(on[:7], ['M9', 'M5', 'WAITS', *HOMING, 'M1', ';'])
        off = second_tool_change(bHometc=False)
        self.assertEqual(off[:5], ['M9', 'M5', 'WAITS', 'M1', ';'])
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
            'bHomeroth ignored': ('        else\n            if bHomeroth\n', '        else\n            if true\n',
                                  self.check_a_turn_off),
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
        start = second_tool_change()
        self.assertEqual(start.count('M1'), 1, start)
        self.assertLess(start.index('M1'), start.index('T2'))

    def test_tool_change_stop_option(self):
        """INDEPENDENT: bOptstptc off removes the M1 before T and adds no job M1 instead."""
        off = second_tool_change(bOptstptc=False)
        self.assertEqual(off[:6], ['M9', 'M5', 'WAITS', *HOMING, ';'])
        self.assertNotIn('M1', off)

    def test_no_job_stop_at_the_first_tool(self):
        """INDEPENDENT: the job M1 belongs to same-tool boundaries; the first tool's start has none."""
        self.assertNotIn('M1', program().start(tool=1, next_tool=2))

    def test_job_stop_returns_after_an_earlier_boundary_stop(self):
        """INDEPENDENT: a stop at one boundary (tool change M1, index M1) does not hide the job M1 of a
        later same-tool boundary (bBoundaryStop is cleared at end_of_job)."""
        p, _ = first_job()
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
        p.ev('start_of_job', job_name='op2', next_job_tool_number=2)
        p.ev('rapid_move', xpos=20, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=200)
        p.ev('rapid_move', zpos=50)
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('fourth_axis', angle=45, angle_4x_around_x_dir='ccw')
        self.assertNotIn('M1', p.ev('start_of_job', job_name='op3', next_job_tool_number=2))
        p.ev('rapid_move', xpos=30, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=200)
        p.ev('rapid_move', zpos=50)
        p.ev('end_of_job', next_job_tool_number=2)
        self.assertEqual(p.ev('start_of_job', job_name='op4', next_job_tool_number=0), ['MSG("op4")', 'M1'])

    def test_repeating_the_stop_after_an_m0_is_detected(self):
        """INDEPENDENT: mutation self-check; a job M1 that ignores the boundary stop fails the guard."""
        mutant = mutate('        if bOptstpjob and !bBoundaryStop\n', '        if bOptstpjob\n')
        assert_detected(self, self.check_no_m1_after_m0, mutant, 'M1 after M0', match='second stop')


class ToolChangeCompensationTests(unittest.TestCase):
    """Only a Z homing deselects compensation still on at a tool change (usr_prep_home_axis); the
    safety block's G40 has no axis, so M06 would run with it on. Oracle (INDEPENDENT): Sinumerik
    deselects TRC only in a G0/G1 block with an axis of the working plane."""

    @staticmethod
    def tool_change_with_compensation_on(**options):
        p = program(**options)
        p.start(tool=1, next_tool=2, next_job_tool_number=2)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=5)
        p.ev('line', zpos=-1, feed=200)
        p.ev('compensation', side='comp_left')
        p.ev('line', xpos=40, feed=200)
        p.ev('line', zpos=20, feed=200)          # below tool_start_plane 50: end_of_job keeps G41
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
        return p.ev('start_of_job', job_name='op2', next_job_tool_number=0)

    def test_z_homing_deselects_compensation_before_m06(self):
        """INDEPENDENT: the default tool-change homing deselects it at the homed Z (PP-062)."""
        blocks = self.tool_change_with_compensation_on()
        self.assertLess(blocks.index('G75 Z1=0.'), blocks.index('G0 G40 X40 Y10'))
        self.assertLess(blocks.index('G0 G40 X40 Y10'), blocks.index('M06'))

    def test_tool_change_without_z_homing_stops_the_post(self):
        """INDEPENDENT: bHometc off, or a tool-change homing without Z: POST ERROR before M06."""
        require_nc_stream()
        from program_session import post_abort_error, post_error_policies
        for options in (dict(bHometc=False), dict(sHomestrtc='8::G75 Y1=0 X1=0')):
            with self.subTest(**options):
                p = Program(options=options, policies=post_error_policies())
                p.start(tool=1, next_tool=2, next_job_tool_number=2)
                p.ev('rapid_move', xpos=10, ypos=10, zpos=5)
                p.ev('line', zpos=-1, feed=200)
                p.ev('compensation', side='comp_left')
                p.ev('line', xpos=40, feed=200)
                p.ev('line', zpos=20, feed=200)
                p.ev('end_of_job', next_job_tool_number=2)
                p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True,
                     xnext=0, ynext=0)
                with self.assertRaises(post_abort_error()):
                    p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
                self.assertTrue(p.nc()[-1].startswith('POST ERROR: Cutter compensation is still on at a tool change'))
                self.assertEqual(p.nc().count('M06'), 1, 'the second tool change must not be posted')

    def test_compensation_off_tool_change_without_homing_posts(self):
        """INDEPENDENT: with compensation off the option only drops the homing."""
        p, _ = first_job(bHometc=False)
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
        self.assertIn('M06', p.ev('start_of_job', job_name='op2', next_job_tool_number=0))


class IndexStopTests(unittest.TestCase):
    def test_index_right_after_the_job_stop_adds_no_second_stop(self):
        """INDEPENDENT: a @fourth_axis right after the start of a same-tool job: one M1, before the
        homing and the turn."""
        p, _ = first_job()
        p.ev('end_of_job', next_job_tool_number=1)
        start = p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
        index = p.ev('fourth_axis', angle=45, angle_4x_around_x_dir='ccw')
        self.assertEqual(start, ['MSG("op2")', 'M1'])
        self.assertEqual(index, [*HOMING, 'A=ACP(45)'])

    def test_index_after_motion_keeps_its_stop(self):
        """INDEPENDENT: an index after the job has moved stops again before the turn."""
        p, _ = first_job()
        p.ev('end_of_job', next_job_tool_number=1)
        p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
        p.ev('rapid_move', xpos=20, ypos=10, zpos=50)
        self.assertEqual(p.ev('fourth_axis', angle=45, angle_4x_around_x_dir='ccw'), ['M1', *HOMING, 'A=ACP(45)'])

    def test_index_after_a_feed_move_keeps_its_stop(self):
        """INDEPENDENT: a feed move after the job M1 is motion too: the index stops again."""
        p, _ = first_job()
        p.ev('end_of_job', next_job_tool_number=1)
        p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
        p.ev('line', zpos=40, feed=200)
        self.assertEqual(p.ev('fourth_axis', angle=45, angle_4x_around_x_dir='ccw'), ['M1', *HOMING, 'G0 A=ACP(45)'])

    def test_first_index_homes_without_the_program_start_homing(self):
        """INDEPENDENT: the first index of a program, the positioning block of the first tool change
        (DESIGN-003), turns A after a Z homing also with bHomebegin off: the tool stands wherever the
        last program left it (PP-053). With the first-rapid and A-turn homings off too, the index
        homes itself (i4xIndexClearanceMode 0). No M1 before the first tool."""
        for options in (dict(bHomebegin=False), dict(bHomebegin=False, bHomerotv=False, bHomeroth=False)):
            with self.subTest(**options):
                p = program(**options)
                self.assertEqual(p.ev('start_program'), [])
                p.ev('change_tool', tool_number=1, next_tool_number=2)
                p.ev('tmatrix', angle_4x_around_x=90, angle_4x_around_x_dir='ccw')
                blocks = p.ev('start_of_job', job_name='op1', next_job_tool_number=0)
                turn = next(i for i, block in enumerate(blocks) if 'A=' in block)
                self.assertEqual(blocks[turn - 2:turn + 1], [*HOMING, 'G0 G17 G90 G54 A=DC(90)'])
                self.assertLess(blocks.index('M06'), turn - 2)
                self.assertNotIn('M1', blocks)


def indexed_tool_change(source=None, direction='ccw', **options):
    """first_job, then T2 for job op2 on a CoordSys at 90 (index position 2); returns the blocks of
    that start_of_job."""
    p, _ = first_job(source, **options)
    p.ev('end_of_job', next_job_tool_number=2)
    p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
    p.ev('tmatrix', angle_4x_around_x=90, angle_4x_around_x_dir=direction, position=2)
    return p.ev('start_of_job', job_name='op2', next_job_tool_number=0)


TOOL_CHANGE_T2 = [';', 'G17 G40 G64 G90', 'T2', 'M06', 'D1', 'MSG("op2")']


class IndexAtToolChangeTests(unittest.TestCase):
    """The index of a tool change is the tool change's positioning block. What the index did on its
    own (M1, clearance, index mode 1 offset, turning the word's way) stays where the tool change
    does not do it already."""

    def test_default_one_stop_one_homing_then_the_turn(self):
        """INDEPENDENT: owner decision 2026-10-28; M5, one homing, one M1, M06, then the A turn of
        the positioning block."""
        self.assertEqual(indexed_tool_change()[:13],
                         ['M9', 'M5', 'WAITS', *HOMING, 'M1', *TOOL_CHANGE_T2, 'G0 G17 G90 G54 A=ACP(90)'])

    def check_index_stop(self, source=None):
        self.assertEqual(indexed_tool_change(source, bOptstptc=False)[:12],
                         ['M9', 'M5', 'WAITS', *HOMING, *TOOL_CHANGE_T2, 'M1'])
        self.assertNotIn('M1', indexed_tool_change(source, bOptstptc=False, bOptstpindex=False))

    def test_index_stop_without_the_tool_change_stop(self):
        """INDEPENDENT: bOptstpindex = M1 before an A index turn: without the tool change's M1
        (bOptstptc off) the index stops after M06, before the turn; with both off, no M1."""
        self.check_index_stop()

    def check_index_clearance(self, source=None):
        cases = {  # options: blocks between the message and the positioning block
            (('bHometc', False),): HOMING,
            (('bHometc', False), ('bHomeroth', False)): HOMING,
            (('bHometc', False), ('i4xIndexClearanceMode', 1)): HOMING,
            (('bHometc', False), ('i4xIndexClearanceMode', 2), ('bHomeroth', False)): [],
        }
        for options, expected in cases.items():
            blocks = indexed_tool_change(source, **dict(options))
            turn = next(i for i, block in enumerate(blocks) if 'A=' in block)
            self.assertEqual(blocks[blocks.index('MSG("op2")') + 1:turn], expected, f'{dict(options)}: {blocks}')
            self.assertEqual(homings(blocks[:turn]), expected, f'{dict(options)}: {blocks}')

    def test_index_clearance_without_the_tool_change_homing(self):
        """INDEPENDENT: option documentation. Without a Z homing at the tool change (bHometc off)
        the index clearance i4xIndexClearanceMode 0 homes before the turn, also with bHomeroth off;
        modes 1/2 (Z levels of the previous tool's job) home with bHomeroth like any A turn outside
        a CAM link, else A turns where M06 left the tool."""
        self.check_index_clearance()

    def check_index_mode_offset(self, source=None):
        blocks = indexed_tool_change(source, i4xIndexMode=1)
        self.assertIn('G0 G17 G90 G55 A=ACP(90)', blocks)

    def test_index_mode_1_steps_the_offset_of_the_positioning_block(self):
        """INDEPENDENT: i4xIndexMode 1 = turn A and step the work offset: index position 2 is G55,
        stated by the positioning block that turns A."""
        self.check_index_mode_offset()

    def check_unhomed_index_follows_the_word(self, source=None):
        try:
            blocks = indexed_tool_change(source, 'cw', bHometc=False, i4xIndexClearanceMode=1, bHomeroth=False)
        except UnsupportedGPPL as stop:
            self.fail(f'the index of a tool change stopped the post: {stop}')
        self.assertIn('G0 G17 G90 G54 A=ACN(90)', blocks)

    def test_unhomed_index_of_a_tool_change_follows_the_word(self):
        """INDEPENDENT: an index turns A the way its word says (angle_4x_around_x_dir), like every
        index and every turn after a Z homing; the wrong-way stop (PP-060) is for CAM motion. Here
        'cw' 0 -> 90 (ACN, -270 degrees) with no homing at all."""
        self.check_unhomed_index_follows_the_word()

    def test_removing_an_index_duty_is_detected(self):
        """INDEPENDENT: mutation self-check of the index duties the positioning block took over."""
        mutants = {
            'no index M1': ('        if bOptstpindex and !bStopSinceMotion and !first_tool\n            call @usr_optionalstop\n',
                            '        if false\n            call @usr_optionalstop\n', self.check_index_stop),
            'mode 0 does not home': ('                if i4xIndexClearanceMode eq 0\n                    sHomestr = sHomestrrot\n',
                                     '                if false\n                    sHomestr = sHomestrrot\n',
                                     self.check_index_clearance),
            'no offset step': ('            if i4xIndexMode eq 1\n                iWorkoffset = iWorkoffset + (position-1)\n',
                               '            if false\n                iWorkoffset = iWorkoffset + (position-1)\n',
                               self.check_index_mode_offset),
            'wrong-way stop': (' and !(bPostHomed and bPostHomedZ) and !bIndexTurn\n', ' and !(bPostHomed and bPostHomedZ)\n',
                               self.check_unhomed_index_follows_the_word),
        }
        for label, (old, new, check) in mutants.items():
            with self.subTest(mutant=label):
                assert_detected(self, check, mutate(old, new), label)


class RepositionWithoutHomingTests(unittest.TestCase):
    """M06 moves the axes and D1 changes the tool length: the first move after a tool change programs
    X, Y and Z whether or not a homing ran (bTcReprogram). Oracle (INDEPENDENT): absolute G90 words
    that are left out keep whatever position the control has, which after M06 is not CAM's."""

    def test_first_rapid_after_a_tool_change_without_homing_programs_all_axes(self):
        """INDEPENDENT: bHometc off, the new tool starts over the old tool's last X/Y/Z."""
        p, _ = first_job(bHometc=False)
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=10, ynext=10)
        p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
        self.assertEqual(p.ev('rapid_move', xpos=10, ypos=10, zpos=50), ['X10 Y10', 'Z50'])
        self.assertEqual(p.ev('rapid_move', zpos=5), ['Z5'])

    def test_first_rapid_of_the_program_without_homing_programs_all_axes(self):
        """INDEPENDENT: bHomebegin and bHomerotv off, the first rapid has CAM X 0 (the initial value)."""
        p = program(bHomebegin=False, bHomerotv=False)
        p.start(tool=1, next_tool=2, next_job_tool_number=0)
        self.assertEqual(p.ev('rapid_move', xpos=0, ypos=20, zpos=50), ['X0 Y20', 'Z50'])

    def test_first_feed_move_after_a_tool_change_without_homing_returns_in_rapid(self):
        """INDEPENDENT: a feed move first: X/Y in rapid at the current height, then the feed in Z."""
        p, _ = first_job(bHometc=False)
        p.ev('end_of_job', next_job_tool_number=2)
        p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=10, ynext=10)
        p.ev('start_of_job', job_name='op2', next_job_tool_number=0)
        self.assertEqual(p.ev('line', xpos=10, ypos=10, zpos=5, feed=150), ['G0 X10 Y10', 'G1 Z5 F150'])


def representative(source=None, **options):
    """Tool 1: op1, same-tool op2, CoordSys index op3, @fourth_axis index op4; tool 2: op5 with a 5x
    A turn outside a CAM link and a G93 cut, same-tool op6; program end. Returns the NC lines."""
    p = Program(options=options, source=source)
    p.start(tool=1, next_tool=2, next_job_tool_number=1)

    def cut(x):
        p.ev('rapid_move', xpos=x, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=200)
        p.ev('rapid_move', zpos=50)

    cut(10)
    p.ev('end_of_job', next_job_tool_number=1)
    p.ev('start_of_job', job_name='op2', next_job_tool_number=1)
    cut(20)
    p.ev('end_of_job', next_job_tool_number=1)
    p.ev('tmatrix', angle_4x_around_x=90, angle_4x_around_x_dir='ccw')
    p.ev('start_of_job', job_name='op3', next_job_tool_number=1)
    cut(30)
    p.ev('end_of_job', next_job_tool_number=1)
    p.ev('fourth_axis', angle=45, angle_4x_around_x_dir='ccw')
    p.ev('start_of_job', job_name='op4', next_job_tool_number=2)
    cut(40)
    p.ev('end_of_job', next_job_tool_number=2)
    p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True, xnext=0, ynext=0)
    p.ev('start_of_job', job_name='op5', next_job_tool_number=2)
    p.ev('move_5x', xpos=10, ypos=0, zpos=40, apos=0, dir5a='ccw')
    p.ev('move_5x', apos=90, dir5a='ccw', prev_command='@move_5x')
    p.ev('move_5x', zpos=25)
    p.ev('line_5x', xpos=20, apos=120, feed=300, dir5a='ccw', feed_type='feed_rate')
    p.ev('move_5x', zpos=50)
    p.ev('end_of_job', next_job_tool_number=2)
    p.ev('start_of_job', job_name='op6', next_job_tool_number=0)
    cut(50)
    p.ev('end_of_job', next_job_tool_number=0)
    p.ev('end_program')
    return p.nc()


# The pre-option post (2394bff) printed exactly this without the two job M1 lines (after MSG("op2")
# and MSG("op6")), without the M9 before the first tool change (bCooloffend, as before the others)
# and with a G04 F6.3 spindle dwell after each 'M3 S3000' block; WAITS now follows each spindle
# start and each M5 (bSpinWait). Compared old vs new on 2026-10-27.
DEFAULT_NC = [
    'G75 Z1=0.', 'G75 Y1=0 X1=0', 'M9', ';', 'G17 G40 G64 G90', 'T1', 'M06', 'D1', 'T2', 'MSG("op1")',
    'G75 Z1=0.', 'G75 Y1=0 X1=0', 'G0 G17 G90 G54 A=DC(0) M8 M3 S3000', 'WAITS', 'X10 Y10', 'Z50',
    'G1 Z-2 F200', 'G0 Z50', 'MSG("op2")', 'M1', 'X20', 'G1 Z-2', 'G0 Z50',
    'M1', 'G75 Z1=0.', 'G75 Y1=0 X1=0', 'G54 A=ACP(90)', 'MSG("op3")', 'X30 Y10', 'Z50', 'G1 Z-2', 'G0 Z50',
    'M1', 'G75 Z1=0.', 'G75 Y1=0 X1=0', 'A=ACP(135)', 'MSG("op4")', 'X40 Y10', 'Z50', 'G1 Z-2', 'G0 Z50',
    'M9', 'M5', 'WAITS', 'G75 Z1=0.', 'G75 Y1=0 X1=0', 'M1', ';', 'G17 G40 G64 G90', 'T2', 'M06', 'D1',
    'MSG("op5")', 'G0 G17 G90 G54 M8 M3 S3000', 'WAITS', 'X10 Y0', 'Z40', 'G75 Z1=0.', 'G75 Y1=0 X1=0',
    'G0 A=ACP(225)', 'X10 Y0', 'Z40', 'Z25', 'G1 G93 X20 A=ACP(255) F18.212', 'G0 Z50', 'G94 F300',
    'MSG("op6")', 'M1', 'X50 Y10', 'G1 Z-2 F200', 'G0 Z50', 'M9', 'M5', 'WAITS', 'G75 Z1=0.', 'G75 Y1=0 X1=0',
    'M30',
]

# Each option switched off, as edits of DEFAULT_NC (difflib opcodes: tag, i1, i2, inserted lines).
OPTION_OFF_EDITS = {
    'bHomebegin': [('delete', 0, 2, [])],
    'bHometc': [('delete', 44, 46, [])],
    'bHomeend': [('delete', 74, 76, [])],
    'bHomerotv': [('delete', 10, 12, [])],
    # No homing before the A turn: no X/Y/Z reprogramming after it either.
    'bHomeroth': [('delete', 57, 59, []), ('delete', 60, 62, [])],
    'bOptstptc': [('delete', 46, 47, [])],
    'bOptstpjob': [('delete', 19, 20, []), ('delete', 67, 68, [])],
    # Without the index M1 the boundary has no stop yet: the job M1 follows the next MSG.
    'bOptstpindex': [('delete', 23, 24, []), ('insert', 28, 28, ['M1']),
                     ('delete', 32, 33, []), ('insert', 37, 37, ['M1'])],
}


class RepresentativeProgramTests(unittest.TestCase):
    def test_default_output(self):
        """CHARACTERIZATION: the default output is the pre-option output plus the job M1 lines."""
        require_nc_stream()
        self.assertEqual(representative(), DEFAULT_NC)

    def test_each_option_removes_only_its_own_blocks(self):
        """INDEPENDENT: switching one option off changes only the blocks of that point."""
        require_nc_stream()
        for name, edits in OPTION_OFF_EDITS.items():
            with self.subTest(option=name):
                actual = representative(**{name: False})
                opcodes = [(tag, i1, i2, actual[j1:j2]) for tag, i1, i2, j1, j2
                           in difflib.SequenceMatcher(a=DEFAULT_NC, b=actual, autojunk=False).get_opcodes()
                           if tag != 'equal']
                self.assertEqual(opcodes, edits)


if __name__ == '__main__':
    unittest.main()
