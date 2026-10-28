"""CYCLE832 High Speed Settings per operation (usr_smoothing).

Owner decision 2026-10-27: CYCLE832 by the wall allowance of the operation, the job parameters
iG187_P / nG187_E override it; simultaneous 4x jobs keep the reset settings. Within a job by
allowance the finishing passes take finishing (reference trace 2026-10-27: 8 of 31 operations
are pockets that finish walls and floor after roughing, with the roughing allowance as
wall_offset). Machine check
2026-10-27 (TEST832.MPF on the 828D): CYCLE832(0.01,1,1) selects G645, SOFT, COMPSURF and
DYNFINISH, CYCLE832(0.1,3,1) the same with DYNROUGH, CYCLE832(0,0,1) returns to the reset state
G64, SOFT, COMPOF, DYNNORM. The machine's cycle setting data hold the same tolerances
($SCS_MILL_TOL_VALUE_ROUGH/SEMIFIN/FINISH = 0.1/0.05/0.01).

The tests read the blocks each event returns (no skipline joining) unless they need the NC lines.
"""
import unittest

from program_session import Program, require_nc_stream
from support import assert_detected, mutate

DESELECT = 'CYCLE832(0,0,1)'
ROUGH, SEMI, FINISH = 'CYCLE832(0.1,3,1)', 'CYCLE832(0.05,2,1)', 'CYCLE832(0.01,1,1)'
MILLING = dict(x5_job=False, job_type='spiral_pocket')


def calls(blocks):
    return [block for block in blocks if block.startswith('CYCLE832')]


def first_job(source=None, options=None, **cam):
    """Program start, tool 1, op1 with the given CAM job values; returns (program, start blocks)."""
    p = Program(options=options, cam={**MILLING, **cam}, source=source)
    return p, p.start(tool=1, next_tool=2, next_job_tool_number=1)


def cut(p, x=10):
    blocks = p.ev('rapid_move', xpos=x, ypos=10, zpos=50)
    blocks += p.ev('line', zpos=-2, feed=200)
    blocks += p.ev('rapid_move', zpos=50)
    return blocks


def same_tool_job(p, name, next_tool=1, **cam):
    p.ev('end_of_job', next_job_tool_number=1)
    return p.ev('start_of_job', job_name=name, next_job_tool_number=next_tool, **cam)


def second_tool(p, **cam):
    """End the tool-1 job, change to tool 2 and start op2; returns (boundary blocks, job blocks)."""
    boundary = p.ev('end_of_job', next_job_tool_number=2)
    boundary += p.ev('change_tool', tool_number=2, next_tool_number=1, first_tool=False, last_tool=True,
                     xnext=0, ynext=0)
    return boundary, p.ev('start_of_job', job_name='op2', next_job_tool_number=0, **cam)


class AutoModeTests(unittest.TestCase):
    def test_machining_type_follows_the_wall_allowance(self):
        """INDEPENDENT: owner rule 2026-10-27. Wall allowance from nCycle832RoughAllow (0.1 mm)
        roughing, from the semi-finishing tolerance (0.05 mm) semi-finishing, below finishing: the
        smoothed path may leave the programmed one by the tolerance, which must stay within the
        allowance. The tolerances are the machine's $SCS_MILL_TOL_VALUE_* defaults."""
        for wall, expected in ((0.3, ROUGH), (0.1, ROUGH), (0.099, SEMI), (0.05, SEMI), (0.049, FINISH),
                               (0.02, FINISH), (0, FINISH)):
            with self.subTest(wall_offset=wall):
                _, blocks = first_job(wall_offset=wall, floor_offset=0.3)
                self.assertEqual(calls(blocks), [expected])

    def test_floor_allowance_counts_only_on_a_3d_profile(self):
        """INDEPENDENT: a 2.5D path keeps its Z, so only the walls take the contour tolerance; a 3D
        profile also moves in Z, so the smaller allowance decides (reference fixture operations
        18/19: profile_3D with wall_offset 2.0 = the radius of the 4 mm ball, floor_offset 0)."""
        for job_type, wall, floor, expected in (('profile_3D', 2.0, 0, FINISH), ('profile', 2.0, 0, ROUGH),
                                                ('profile_3D', 0.3, 0.2, ROUGH), ('profile_3D', 0.3, 0.05, SEMI),
                                                ('spiral_pocket', 0, 0.15, FINISH)):
            with self.subTest(job_type=job_type, wall=wall, floor=floor):
                _, blocks = first_job(job_type=job_type, wall_offset=wall, floor_offset=floor)
                self.assertEqual(calls(blocks), [expected])

    def test_simultaneous_and_drilling_jobs_keep_the_reset_settings(self):
        """INDEPENDENT: owner rule 2026-10-27, 4x simultaneous jobs without CYCLE832 (X5_job); a
        drilling job has no wall allowance to judge. iG187_P still selects CYCLE832 there."""
        for cam in (dict(x5_job=True), dict(job_type='drilling')):
            with self.subTest(**cam):
                self.assertEqual(calls(first_job(wall_offset=0.3, **cam)[1]), [])
                self.assertEqual(calls(first_job(wall_offset=0.3, iG187_P=1, **cam)[1]), [ROUGH])

    def test_job_parameters_override_the_allowance(self):
        """INDEPENDENT: iG187_P 1/2/3 = rough/semi/finish, -1 = none; nG187_E replaces the tolerance."""
        for cam, expected in ((dict(iG187_P=3), [FINISH]), (dict(iG187_P=1, wall_offset=0), [ROUGH]),
                              (dict(iG187_P=-1), []), (dict(nG187_E=0.02), ['CYCLE832(0.02,3,1)']),
                              (dict(iG187_P=2, nG187_E=0.03), ['CYCLE832(0.03,2,1)'])):
            with self.subTest(**cam):
                self.assertEqual(calls(first_job(**{'wall_offset': 0.3, **cam})[1]), expected)

    def test_options(self):
        """INDEPENDENT: the user options set the tolerances and the roughing allowance; bCycle832
        false writes no CYCLE832."""
        for options, wall, expected in ((dict(nCycle832TolRough=0.2), 0.3, ['CYCLE832(0.2,3,1)']),
                                        (dict(nCycle832TolSemi=0.04), 0.05, ['CYCLE832(0.04,2,1)']),
                                        (dict(nCycle832TolFinish=0.005), 0, ['CYCLE832(0.005,1,1)']),
                                        (dict(nCycle832RoughAllow=0.5), 0.3, [SEMI]),
                                        (dict(nCycle832TolRough=0.2), 0.15, [SEMI]),
                                        (dict(bCycle832=False), 0.3, [])):
            with self.subTest(**options):
                self.assertEqual(calls(first_job(options=options, wall_offset=wall)[1]), expected)


class PlacementTests(unittest.TestCase):
    def test_call_follows_the_spindle_start_and_precedes_the_first_move(self):
        """INDEPENDENT: 828D Operating Manual 07/2021 programs CYCLE832 before the machining it
        sets; here after M06 and the spindle start, on its own line, and the first rapid writes G0
        again."""
        require_nc_stream()
        p, _ = first_job(wall_offset=0.3)
        cut(p)
        nc = p.nc()
        call = nc.index(ROUGH)
        self.assertLess(nc.index('M06'), call)
        self.assertTrue(any('M3' in line.split() for line in nc[:call]), nc)
        self.assertEqual(nc[call + 1:call + 3], ['G0 X10 Y10', 'Z50'], nc)

    def test_same_tool_jobs_write_only_changes(self):
        """INDEPENDENT: the call is modal; the next job of the same tool writes it only when the
        type or the tolerance changes, and deselects it when it has none."""
        p, _ = first_job(wall_offset=0.3)
        cut(p)
        self.assertEqual(calls(same_tool_job(p, 'op2', wall_offset=0.2)), [])
        cut(p, 20)
        self.assertEqual(calls(same_tool_job(p, 'op3', wall_offset=0)), [FINISH])
        cut(p, 30)
        self.assertEqual(calls(same_tool_job(p, 'op4', x5_job=True)), [DESELECT])
        cut(p, 40)
        self.assertEqual(calls(same_tool_job(p, 'op5', x5_job=True)), [])
        cut(p, 50)
        self.assertEqual(calls(same_tool_job(p, 'op6', iG187_P=1)), [ROUGH])
        cut(p, 60)
        self.assertEqual(calls(same_tool_job(p, 'op7', iG187_P=1, nG187_E=0.05)), ['CYCLE832(0.05,3,1)'])

    def check_tool_change(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        cut(p)
        boundary, job = second_tool(p, wall_offset=0.3)
        blocks = boundary + job
        self.assertIn(DESELECT, blocks)
        deselect = blocks.index(DESELECT)
        self.assertEqual(blocks[deselect - 1:deselect + 3], ['M1', DESELECT, ';', 'G17 G40 G64 G90'], blocks)
        self.assertEqual(calls(blocks[blocks.index('M06'):]), [ROUGH], blocks)

    def test_tool_change_deselects_before_the_safety_block(self):
        """INDEPENDENT: M06 and the safety block run in the reset settings of the control; the new
        tool selects its own CYCLE832 after M06, also with the type the last tool had."""
        self.check_tool_change()

    def check_program_end(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        cut(p)
        p.ev('end_of_job', next_job_tool_number=0)
        end = p.ev('end_program')
        self.assertEqual(end[-2:], [DESELECT, 'M30'], end)

    def test_program_end_deselects_before_m30(self):
        """INDEPENDENT: the program ends in the reset settings also where M30 would not reset the G
        groups (machine data GCODE_RESET_MODE) or the end is M2."""
        self.check_program_end()

    def test_drill_cycle_deselects_before_the_cycle(self):
        """INDEPENDENT: drilling cycles run in the reset settings of the control (a CYCLE832 that
        iG187_P selected on a drilling job ends before the cycle call)."""
        p, blocks = first_job(job_type='drilling', iG187_P=1)
        self.assertEqual(calls(blocks), [ROUGH])
        drill = p.ev('drill', xpos=10, ypos=10, zpos=10)
        deselect = drill.index(DESELECT)
        cycle = next(index for index, block in enumerate(drill) if block.startswith('MCALL CYCLE8'))
        self.assertLess(deselect, cycle, drill)

    def test_no_cycle832_job_after_a_tool_change_writes_nothing(self):
        """INDEPENDENT: after the tool change deselected it, a job without CYCLE832 has nothing more
        to deselect after M06."""
        p, _ = first_job(wall_offset=0.3)
        cut(p)
        _, job = second_tool(p, x5_job=True)
        self.assertEqual(calls(job), [DESELECT])
        self.assertLess(job.index(DESELECT), job.index('M06'), job)

    def test_removed_deselections_are_detected(self):
        """INDEPENDENT: mutation self-check of the tool-change and program-end deselections."""
        tool_change = ('    if iCycle832Mode ne 0\n        ; M06 and the safety block run',
                       '    if false\n        ; M06 and the safety block run')
        program_end = ('    if iCycle832Mode ne 0\n        ; M30 resets', '    if false\n        ; M30 resets')
        for label, (old, new), check in (('tool change', tool_change, self.check_tool_change),
                                         ('program end', program_end, self.check_program_end)):
            with self.subTest(mutant=label):
                assert_detected(self, check, mutate(old, new), label)


class AutoModeMutationTests(unittest.TestCase):
    def check_rules(self, source, options=None):
        if options:
            # A rough tolerance above the roughing allowance: 0.15 mm stays semi-finishing.
            self.assertEqual(calls(first_job(source, options, wall_offset=0.15)[1]), [SEMI])
            return
        for cam, expected in ((dict(wall_offset=0.3), [ROUGH]), (dict(wall_offset=0.05), [SEMI]),
                              (dict(wall_offset=0.02), [FINISH]), (dict(wall_offset=0.3, x5_job=True), []),
                              (dict(job_type='profile_3D', wall_offset=2.0, floor_offset=0), [FINISH])):
            self.assertEqual(calls(first_job(source, **cam)[1]), expected, cam)

    def test_rule_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the allowance rules."""
        mutants = {
            'X5_job ignored': ("iG187_P eq 0 and !X5_job and", "iG187_P eq 0 and"),
            '3D profile floor ignored': ("        if job_type eq 'profile_3D' and floor_offset < nAllow\n",
                                         "        if false\n"),
            'roughing threshold exclusive': (' if nAllow >= nCycle832RoughAllow and', ' if nAllow > 0.3 and'),
            'semi-finishing never': ('        if nAllow >= nCycle832TolSemi\n            iMode = 2\n',
                                     '        if false\n            iMode = 2\n'),
            'semi-finishing above 0': ('        if nAllow >= nCycle832TolSemi\n',
                                       '        if nAllow > 0\n'),
            'roughing tolerance ignored': (' and nAllow >= nCycle832TolRough\n', '\n'),
        }
        for label, (old, new) in mutants.items():
            with self.subTest(mutant=label):
                options = dict(nCycle832TolRough=0.2) if label == 'roughing tolerance ignored' else None
                assert_detected(self, lambda source: self.check_rules(source, options), mutate(old, new), label)


def finish_pass(p, feed_type='finish_feed', x=10, side=None):
    """A pocket's finishing pass in SolidCAM order: retract, approach, plunge (z_feed), then the
    finishing move, with the compensation event before it when side is given."""
    blocks = p.ev('rapid_move', zpos=50)
    blocks += p.ev('rapid_move', xpos=x, ypos=10)
    blocks += p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
    if side:
        blocks += p.ev('compensation', side=side)
    blocks += p.ev('line', xpos=x + 10, feed=300, feed_type=feed_type)
    return blocks


def rough_move(p, x=40):
    return p.ev('line', xpos=x, feed=600, feed_type='feed_rate')


class FinishPassTests(unittest.TestCase):
    def check_switch(self, source=None):
        for feed_type in ('finish_feed', 'finish_feed_floor'):
            p, start = first_job(source, wall_offset=0.3)
            self.assertEqual(calls(start), [ROUGH])
            self.assertEqual(calls(rough_move(p)), [])
            blocks = finish_pass(p, feed_type)
            self.assertEqual(calls(blocks), [FINISH], feed_type)
            self.assertTrue(blocks[blocks.index(FINISH) + 1].startswith('G1 X20'), blocks)
            # Links and plunges keep the type; the cutting feed takes the allowance's type again.
            self.assertEqual(calls(p.ev('line', zpos=5, feed_type='feed_link')
                                   + p.ev('line', zpos=-2, feed_type='z_feed')), [])
            self.assertEqual(calls(rough_move(p)), [ROUGH])

    def test_finishing_passes_switch_to_finishing(self):
        """INDEPENDENT: reference trace 2026-10-27, operation 16 (spiral_pocket, wall_offset 0.15):
        after the roughing at feed_rate a floor pass at finish_feed_floor and a wall pass at
        finish_feed cut the final contour; they take the finishing type, on a line of their own
        before the first finishing move, which writes G1 again. A later cut at feed_rate goes back
        to the type of the allowance."""
        self.check_switch()

    def test_finishing_keeps_the_job_tolerance_parameter(self):
        """INDEPENDENT: nG187_E replaces the tolerance of every call of its job."""
        p, start = first_job(wall_offset=0.3, nG187_E=0.02)
        self.assertEqual(calls(start), ['CYCLE832(0.02,3,1)'])
        self.assertEqual(calls(finish_pass(p)), ['CYCLE832(0.02,1,1)'])

    def test_explicit_type_and_simultaneous_jobs_do_not_switch(self):
        """INDEPENDENT: iG187_P 1-3 is the type of the whole job, -1 none; X5_job keeps the reset
        settings."""
        for cam in (dict(iG187_P=1), dict(iG187_P=2), dict(iG187_P=-1), dict(x5_job=True)):
            with self.subTest(**cam):
                p, _ = first_job(wall_offset=0.3, **cam)
                self.assertEqual(calls(finish_pass(p) + rough_move(p)), [])

    def test_finishing_job_has_nothing_to_switch(self):
        """INDEPENDENT: a job finished by allowance (wall_offset 0) is already finishing."""
        p, start = first_job(job_type='profile', wall_offset=0)
        self.assertEqual(calls(start), [FINISH])
        self.assertEqual(calls(finish_pass(p, side='left')), [])

    def test_finishing_move_is_its_own_nc_line(self):
        """INDEPENDENT: with the skipline joining of the NC stream the call stays on its own line."""
        require_nc_stream()
        p, _ = first_job(wall_offset=0.3)
        finish_pass(p)
        nc = p.nc()
        call = nc.index(FINISH)
        self.assertEqual(nc[call - 1:call + 2], ['G1 Z-2 F4000', FINISH, 'G1 X20 F300'], nc)


class CompensationTests(unittest.TestCase):
    def check_before_selection(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        blocks = finish_pass(p, side='left')
        self.assertEqual(calls(blocks), [FINISH])
        selection = next(index for index, block in enumerate(blocks) if 'G41' in block)
        self.assertEqual(blocks.index(FINISH), selection - 1, blocks)

    def test_call_precedes_the_compensation_selection(self):
        """INDEPENDENT: reference trace 2026-10-27, operations 8 and 11: the compensation event comes
        before the first finishing move, which selects G41; the call goes before that block, while
        the control has no compensation on."""
        self.check_before_selection()

    def check_waits_for_g40(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='left')
        self.assertEqual(calls(rough_move(p)), [])
        on = p.ev('line', xpos=60, feed=300, feed_type='finish_feed')
        on += p.ev('compensation', side='off')
        on += p.ev('line', xpos=70, feed_type='finish_feed')
        self.assertEqual(calls(on), [], on)
        self.assertIn('G40', on[-1])
        after = p.ev('rapid_move', zpos=50)
        self.assertEqual(after[0], FINISH, after)

    def test_call_waits_for_the_move_after_g40(self):
        """INDEPENDENT: no CYCLE832 while compensation is on at the control: its blocks without
        motion count as empty blocks of TRC (MD20250 CUTCOM_MAXNUM_DUMMY_BLOCKS = 5 on this machine,
        backups/NOLOG.ard; alarm 10762 above). The call follows the block that writes G40."""
        self.check_waits_for_g40()

    def test_same_tool_job_with_compensation_on_waits(self):
        """INDEPENDENT: compensation the last job left on below the clearance plane (end_of_job
        cancels it only above) holds the next job's call until G40."""
        p, _ = first_job(wall_offset=0.3)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='left')
        rough_move(p)
        self.assertEqual(calls(same_tool_job(p, 'op2', wall_offset=0)), [])
        off = p.ev('compensation', side='off') + p.ev('line', xpos=50, feed_type='finish_feed')
        self.assertEqual(calls(off), [], off)
        self.assertEqual(p.ev('rapid_move', zpos=50)[0], FINISH)


class FinishPassMutationTests(unittest.TestCase):
    def test_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the finishing switch and the compensation hold."""
        finish = "        if feed_type eq 'finish_feed' or feed_type eq 'finish_feed_floor'\n"
        mutants = {
            'finishing switch removed': ((finish, '        if false\n'), FinishPassTests.check_switch),
            'floor finishing ignored': ((finish, "        if feed_type eq 'finish_feed'\n"),
                                        FinishPassTests.check_switch),
            'cutting feed keeps finishing': (("        if feed_type eq 'feed_rate'\n", '        if false\n'),
                                             FinishPassTests.check_switch),
            'compensation hold removed': (('        if iCompActive ne 41 and iCompActive ne 42\n',
                                           '        if true\n'), CompensationTests.check_waits_for_g40),
            'rapid does not apply': (('    call @usr_smoothing_apply\n    call @usr_rapid\n',
                                      '    call @usr_rapid\n'), CompensationTests.check_waits_for_g40),
            'apply after the line': (('    call @usr_smoothing_feed\n    call @usr_line\nendp',
                                      '    call @usr_line\n    call @usr_smoothing_feed\nendp'),
                                     CompensationTests.check_before_selection),
        }
        for label, ((old, new), check) in mutants.items():
            with self.subTest(mutant=label):
                owner = FinishPassTests() if check.__qualname__.startswith('FinishPass') else CompensationTests()
                assert_detected(self, lambda source: check(owner, source), mutate(old, new), label)


if __name__ == '__main__':
    unittest.main()
