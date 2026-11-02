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

Owner decision 2026-10-28: face and thread milling, which have no allowance, go by the feed type
(roughing, their finishing passes finishing); any other operation without an allowance stops the
post. Recorded traces 001-005 and the reference trace (121 operations; 001 and the reference trace
are one program): SolidCAM sends wall_offset and floor_offset with start_of_job of all 100 milling
operations of the other types and with no face milling, thread milling, drilling or 4x morphing
operation; the variables keep the last job's values there.

Owner decision 2026-10-28 (option bCycle832X5, default on): a simultaneous 4x/5x job goes by its
allowance too. SolidCAM sends Stock_to_leave and Drive_surface_Offset with it, not wall_offset
(recorded traces 001/002 and the reference trace: the two 4x morphing operations, 0 and 0, with
Cut_tolerance 0.01); the smaller decides. Without TRAORI (none on this machine) the control holds A
to ATOL[A] or else MD33100 COMPRESS_POS_TOL (0.1 deg here, 0.087 mm at R50), not to the contour
tolerance (Job Planning 08/2018 12.11), so ATOL[A] follows each CYCLE832 of a 4x/5x job: the
contour tolerance in degrees at the stock's largest radius about A, which is at Y0 Z0 (owner rule).

Machine 2026-11-01: a finishing wall pass with cutter compensation at the control in
CYCLE832(0.01,1,1) (G41 line, 45 deg lead-in arc, contour, lead-out arc, G40 line along its normal;
tool radius 2.991) stopped with alarm 10751 "danger of collision" at the lead-out arc. The same
program ran with COMPOF before the G41 block, and with CYCLE832(0,0,1) before the pass; it stopped
with G64 before the G41 block (G645 off, COMPSURF kept) and with the arcs as I/J instead of AR=.
So the compressor is off while
G41/G42 is selected: COMPOF before the block that selects compensation; G645, the tolerance and the
dynamics of the call stay. After G40 the call of the cut's type comes again and the cycle selects
the compressor it selected before (COMPSURF on this machine). Owner 2026-11-01: a drilling cycle
with compensation still on at the control or still asked for by CAM, and a deselection of CYCLE832
with compensation on, stop the post; CYCLE832 goes off before every M0/M1 (StopTests).

The tests read the blocks each event returns (no skipline joining) unless they need the NC lines.
"""
import unittest

from program_session import Program, post_abort_error, post_error_policies
from support import assert_detected, mutate
from support.session import HEADER_DEFAULTS, NOT_SENT

DESELECT = 'CYCLE832(0,0,1)'
COMPOF = 'COMPOF'
COMP_STOP = ('POST ERROR: Cutter compensation is still on where CYCLE832 is deselected (program end or tool '
             'change). Switch it off (G40) in CAM before.')
DRILL_COMP_STOP = ('POST ERROR: Cutter compensation is still on at a drilling cycle. Switch it off (G40) in CAM '
                   'before the drilling job.')
ROUGH, SEMI, FINISH = 'CYCLE832(0.1,3,1)', 'CYCLE832(0.05,2,1)', 'CYCLE832(0.01,1,1)'
MILLING = dict(x5_job=False, job_type='spiral_pocket')
# Without the M1 between two jobs of the same tool (bOptstpjob), which deselects CYCLE832 before it
# (StopTests): the other tests follow the type and tolerance across job boundaries.
NO_JOB_STOP = {'bOptstpjob': False}
# start_of_job of an operation without an allowance: SolidCAM sends neither variable.
NO_ALLOWANCE = dict(wall_offset=NOT_SENT, floor_offset=NOT_SENT)
NO_ALLOWANCE_STOP = ('POST ERROR: CYCLE832: the operation has no wall allowance (wall_offset): set the job '
                     'parameter iG187_P (1 rough, 2 semi, 3 finish, -1 none).')


def calls(blocks):
    return [block for block in blocks if block.startswith('CYCLE832')]


def first_job(source=None, options=None, **cam):
    """Program start, tool 1, op1 with the given CAM job values; returns (program, start blocks)."""
    p = Program(options={**NO_JOB_STOP, **(options or {})}, cam={**MILLING, **cam}, source=source)
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
        """INDEPENDENT: a simultaneous 4x/5x job (X5_job) without Stock_to_leave/Drive_surface_Offset
        keeps the reset settings (its wall_offset does not count); a drilling job has no wall
        allowance to judge. iG187_P still selects CYCLE832 there."""
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

    def check_z_only_first_move(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        cut(p)
        job = same_tool_job(p, 'op2', wall_offset=0)
        move = p.ev('rapid_move', xpos=10, ypos=10, zpos=5)
        self.assertEqual((calls(job), move), ([FINISH], ['G0 Z5']), (job, move))

    def test_z_only_first_move_joins_the_restated_motion_word(self):
        """INDEPENDENT: the first rapid after the call writes G0 again; a job starting over the X/Y
        where the last one ended moves only in Z, in one block instead of a bare 'G0' block and a
        'Z5' block."""
        self.check_z_only_first_move()
        old = ('    if bFirstMove and change(zpos) and !change(xpos) and !change(ypos)\n'
               '        bClimbFirst = true\n')
        assert_detected(self, self.check_z_only_first_move, mutate(old, old.replace('bClimbFirst = true',
                                                                                    'bClimbFirst = false')),
                        'Z-only first move split')

    def check_tool_change(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        cut(p)
        boundary, job = second_tool(p, wall_offset=0.3)
        blocks = boundary + job
        self.assertIn(DESELECT, blocks)
        deselect = blocks.index(DESELECT)
        self.assertEqual(blocks[deselect:deselect + 4], [DESELECT, 'M1', ';', 'G17 G40 G64 G90'], blocks)
        self.assertEqual(calls(blocks[blocks.index('M06'):]), [ROUGH], blocks)

    def test_tool_change_deselects_before_the_safety_block(self):
        """INDEPENDENT: M06 and the safety block run in the reset settings of the control, and the
        M1 of the tool change (bOptstptc) comes after CYCLE832(0,0,1) (owner 2026-11-01, StopTests);
        the new tool selects its own CYCLE832 after M06, also with the type the last tool had."""
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
        tool_change = ('    if iCycle832Mode ne 0\n        ; The optional stop, M06 and the safety block run',
                       '    if false\n        ; The optional stop, M06 and the safety block run')
        program_end = ('    if iCycle832Mode ne 0\n        ; Before the optional stop', '    if false\n        ; Before the optional stop')
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
            'X5_job ignored': ("iG187_P eq 0 and (!X5_job or nAllow ne nNoAllowance) and", "iG187_P eq 0 and"),
            '3D profile floor ignored': ("            if job_type eq 'profile_3D' and floor_offset < nAllow\n",
                                         "            if false\n"),
            'roughing threshold exclusive': (' if nAllow >= nCycle832RoughAllow and', ' if nAllow > 0.3 and'),
            'semi-finishing never': ('            if nAllow >= nCycle832TolSemi\n                iMode = 2\n',
                                     '            if false\n                iMode = 2\n'),
            'semi-finishing above 0': ('            if nAllow >= nCycle832TolSemi\n',
                                       '            if nAllow > 0\n'),
            'roughing tolerance ignored': (' and nAllow >= nCycle832TolRough\n', '\n'),
        }
        for label, (old, new) in mutants.items():
            with self.subTest(mutant=label):
                options = dict(nCycle832TolRough=0.2) if label == 'roughing tolerance ignored' else None
                assert_detected(self, lambda source: self.check_rules(source, options), mutate(old, new), label)


# A simultaneous 4x job as SolidCAM sends it (recorded traces: 4x morphing, X5_job 1).
# Its stock (start_of_file): Y and Z -19.5 to 19.5, the farthest corner 27.577 mm from the A axis.
SIMULTANEOUS = dict(x5_job=True, job_type='4x_morph_between_curves', stock_y=39, stock_y_minus=-19.5,
                    stock_z_plus=19.5, stock_z_minus=-19.5)
# tolerance * 180 / pi / 27.577: 0.01 mm -> 0.02078 deg, 0.05 -> 0.10388, 0.1 -> 0.20777.
ATOL_FINISH, ATOL_SEMI, ATOL_ROUGH = 'ATOL[A]=0.02078', 'ATOL[A]=0.10388', 'ATOL[A]=0.20777'
# Off-centre stocks with the same farthest corner (Y 30, Z 32: 43.863 mm): 0.01 mm -> 0.01306 deg.
OFF_CENTRE_STOCKS = (dict(stock_y_minus=-10, stock_y=40, stock_z_minus=-32, stock_z_plus=0),
                     dict(stock_y_minus=-30, stock_y=40, stock_z_minus=-5, stock_z_plus=32))


def stock(stock_to_leave, drive_surface_offset=NOT_SENT):
    return dict(stock_to_leave=stock_to_leave, drive_surface_offset=drive_surface_offset)


def smoothing(blocks):
    return [block for block in blocks if block.startswith(('CYCLE832', 'ATOL'))]


class SimultaneousJobTests(unittest.TestCase):
    def test_machining_type_follows_the_stock_allowance(self):
        """INDEPENDENT: owner decision 2026-10-28. A simultaneous 4x/5x job takes the type of the
        smaller of Stock_to_leave and Drive_surface_Offset by the wall allowance rule; wall_offset
        does not count there. Recorded traces: 4x morphing sends 0 and 0 (finishing)."""
        for cam, expected in ((stock(0, 0), FINISH), (stock(0.3, 0.3), ROUGH), (stock(0.06), SEMI),
                              (stock(NOT_SENT, 0.02), FINISH), (stock(0.3, 0), FINISH), (stock(0, 0.3), FINISH),
                              (stock(0.3, 0.06), SEMI)):
            with self.subTest(**cam):
                self.assertEqual(calls(first_job(wall_offset=0.3, **SIMULTANEOUS, **cam)[1]), [expected])

    def check_option_off(self, source=None):
        for options, cam, expected in ((dict(bCycle832X5=False), stock(0, 0), []), (None, stock(NOT_SENT), []),
                                       (dict(bCycle832X5=False), dict(iG187_P=2, **stock(0, 0)), [SEMI, ATOL_SEMI])):
            with self.subTest(options=options, **cam):
                self.assertEqual(smoothing(first_job(source, options, **SIMULTANEOUS, **cam)[1]), expected)

    def test_option_off_and_missing_allowance_keep_the_reset_settings(self):
        """INDEPENDENT: bCycle832X5 false, or a 4x/5x job that sends neither variable, keeps the
        reset settings without stopping the post; iG187_P still selects CYCLE832 there, and ATOL[A]
        follows it (bCycle832X5 covers only the type by allowance)."""
        self.check_option_off()

    def test_atol_follows_the_call_on_simultaneous_jobs(self):
        """INDEPENDENT: ATOL[A] in degrees = the contour tolerance at the stock's largest radius
        about A (Y0 Z0): the corner of the stock's Y/Z extent. It follows the CYCLE832 call of a
        4x/5x job, also one selected by iG187_P; a stock of no Y/Z extent takes 30 mm (owner
        2026-10-29: 0.01 mm -> 0.0191 deg); none with bCycle832AtolA false or on a job without
        simultaneous moves."""
        for options, cam, expected in ((None, stock(0, 0), [FINISH, ATOL_FINISH]),
                                       (None, stock(0.06), [SEMI, ATOL_SEMI]),
                                       (None, stock(0.3), [ROUGH, ATOL_ROUGH]),
                                       (None, dict(iG187_P=1), [ROUGH, ATOL_ROUGH]),
                                       (dict(bCycle832AtolA=False), stock(0), [FINISH]),
                                       (None, dict(stock_y_minus=0, stock_y=0, stock_z_minus=0, stock_z_plus=0,
                                                   **stock(0)), [FINISH, 'ATOL[A]=0.0191']),
                                       (None, dict(x5_job=False, job_type='profile', wall_offset=0), [FINISH])):
            with self.subTest(options=options, **cam):
                self.assertEqual(smoothing(first_job(options=options, **{**SIMULTANEOUS, **cam})[1]), expected)

    def check_stock_radius(self, source=None):
        for cam in OFF_CENTRE_STOCKS:
            with self.subTest(**cam):
                blocks = first_job(source, **{**SIMULTANEOUS, **cam, **stock(0)})[1]
                self.assertEqual(smoothing(blocks), [FINISH, 'ATOL[A]=0.01306'])

    def test_atol_radius_is_the_farthest_stock_corner_from_the_axis(self):
        """INDEPENDENT: the stock's farthest point from the A axis (Y0 Z0) is the corner of its Y/Z
        extent, Y from stock_y_minus to stock_y_minus + stock_y and Z from stock_z_minus to
        stock_z_plus as WORKPIECE takes them: Y 30 and Z 32 give 43.863 mm on either side."""
        self.check_stock_radius()

    def check_atol_state(self, source=None):
        # Same tool: a finishing profile, then a 4x job with the same call: ATOL[A] alone.
        p, start = first_job(source, job_type='profile', wall_offset=0)
        self.assertEqual(smoothing(start), [FINISH])
        cut(p)
        self.assertEqual(smoothing(same_tool_job(p, 'op2', **SIMULTANEOUS, **stock(0, 0))), [ATOL_FINISH])
        cut(p)
        self.assertEqual(smoothing(same_tool_job(p, 'op3', **SIMULTANEOUS, **stock(0, 0))), [])
        # A call in between (roughing profile): the next finishing 4x job writes ATOL[A] again.
        cut(p)
        self.assertEqual(smoothing(same_tool_job(p, 'op3b', job_type='profile', x5_job=False, wall_offset=0.3)),
                         [ROUGH])
        cut(p)
        self.assertEqual(smoothing(same_tool_job(p, 'op3c', **SIMULTANEOUS, **stock(0, 0))), [FINISH, ATOL_FINISH])
        # A roughing 4x job: its finishing passes and the cut after them write ATOL[A] again.
        cut(p)
        self.assertEqual(smoothing(same_tool_job(p, 'op4', **SIMULTANEOUS, **stock(0.3))), [ROUGH, ATOL_ROUGH])
        self.assertEqual(smoothing(finish_pass(p)), [FINISH, ATOL_FINISH])
        self.assertEqual(smoothing(rough_move(p)), [ROUGH, ATOL_ROUGH])
        # The tool change (made at the next start_of_job) deselects; the 4x job selects both again.
        _, blocks = second_tool(p, **SIMULTANEOUS, **stock(0.3))
        self.assertEqual(smoothing(blocks), [DESELECT, ROUGH, ATOL_ROUGH])

    def test_atol_is_written_when_the_control_lacks_it(self):
        """INDEPENDENT: ATOL[A] is written after every CYCLE832 call of a 4x/5x job (the cycle may
        set the rotary axes itself; unverified on this control) and when a 4x/5x job keeps the call
        of a job without simultaneous moves, not again while it holds."""
        self.check_atol_state()

    def test_atol_is_its_own_nc_line_before_the_first_move(self):
        """INDEPENDENT: with the skipline joining of the NC stream ATOL[A] stays on its own line
        after the call, before the first move, which writes G0 again."""
        p, _ = first_job(**SIMULTANEOUS, **stock(0, 0))
        cut(p)
        nc = p.nc()
        call = nc.index(FINISH)
        self.assertEqual(nc[call + 1], ATOL_FINISH, nc)
        self.assertTrue(nc[call + 2].startswith('G0'), nc)

    def check_simultaneous_moves(self, source=None):
        p, start = first_job(source, **SIMULTANEOUS, **stock(0.3))
        self.assertEqual(smoothing(start), [ROUGH, ATOL_ROUGH])
        p.ev('move_5x', xpos=10, ypos=10, zpos=50)
        moves = p.ev('line_5x', zpos=-2, feed=4000, feed_type='z_feed')
        moves += p.ev('line_5x', xpos=12, feed=300, feed_type='feed_lead_in')
        moves += p.ev('line_5x', xpos=30, feed=600, feed_type='feed_rate')
        moves += p.ev('line_5x', xpos=32, feed=300, feed_type='feed_lead_out')
        self.assertEqual(smoothing(moves), [])
        self.assertEqual(smoothing(p.ev('line_5x', xpos=40, feed_type='finish_feed')), [FINISH, ATOL_FINISH])
        self.assertEqual(smoothing(p.ev('line_5x', xpos=42, feed_type='feed_lead_out')), [])
        self.assertEqual(smoothing(p.ev('line_5x', xpos=50, feed_type='feed_rate')), [ROUGH, ATOL_ROUGH])

    def test_moves_of_a_simultaneous_job_switch_only_on_finishing_passes(self):
        """INDEPENDENT: SolidCAM sends the moves of a 4x job as move_5x/line_5x (recorded 4x
        morphing: 502 move_5x, 5304 line_5x). Owner decision 2026-10-28: lead-ins, lead-outs and
        plunges keep the job's type; a finishing pass switches to finishing and the next cut at
        feed_rate back, each call with its ATOL[A]."""
        self.check_simultaneous_moves()

    def check_atol_waits_for_g40(self, source=None):
        p, _ = first_job(source, job_type='profile', wall_offset=0)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='comp_left')
        p.ev('line', xpos=40, feed=300, feed_type='finish_feed')
        self.assertEqual(smoothing(same_tool_job(p, 'op2', **SIMULTANEOUS, **stock(0, 0))), [])
        off = p.ev('compensation', side='comp_off') + p.ev('line_5x', xpos=50, feed_type='finish_feed')
        self.assertEqual(smoothing(off), [], off)
        self.assertIn('G40', off[-1])
        self.assertEqual(smoothing(p.ev('line_5x', xpos=60, feed_type='finish_feed')), [FINISH, ATOL_FINISH])

    def test_atol_waits_for_the_move_after_g40(self):
        """INDEPENDENT: like CYCLE832, ATOL[A] is a block without motion, so it is not written while
        compensation is on at the control (MD20250 = 5 empty blocks, alarm 10762): compensation the
        last job left on holds a 4x job's ATOL[A] until the move after G40, where it follows the
        call that selects the compressor again."""
        self.check_atol_waits_for_g40()

    def check_first_job_stock(self, source=None):
        p = stop_program(source, **SIMULTANEOUS, **stock(0, 0))
        p.ev('start_of_file', **HEADER_DEFAULTS)
        p.ev('start_program')
        p.ev('change_tool', tool_number=1, next_tool_number=2, next_job_tool_number=1)
        self.assertEqual(smoothing(p.ev('start_of_job', job_name='op1')), [])

    def test_first_job_has_no_stock_allowance_until_it_sends_one(self):
        """INDEPENDENT: start_of_file resets Stock_to_leave and Drive_surface_Offset: a first 4x job
        that sends neither keeps the reset settings, whatever the variables held before."""
        self.check_first_job_stock()

    def check_reset(self, source=None):
        p, start = first_job(source, **SIMULTANEOUS, **stock(0.3, 0.3))
        self.assertEqual(calls(start), [ROUGH])
        cut(p)
        self.assertEqual(calls(same_tool_job(p, 'op2', **SIMULTANEOUS)), [DESELECT])

    def test_next_job_does_not_take_the_last_stock_allowance(self):
        """INDEPENDENT: the post resets Stock_to_leave and Drive_surface_Offset between jobs like the
        wall allowance: a 4x job that sends neither keeps the reset settings."""
        self.check_reset()


class SimultaneousJobMutationTests(unittest.TestCase):
    def check_rules(self, source):
        for cam, expected in ((stock(0.3, 0.06), [SEMI]), (stock(NOT_SENT, 0.02), [FINISH]), (stock(0.3), [ROUGH])):
            self.assertEqual(calls(first_job(source, wall_offset=0.3, **SIMULTANEOUS, **cam)[1]), expected, cam)
        self.assertEqual(calls(first_job(source, dict(bCycle832X5=False), **SIMULTANEOUS, **stock(0))[1]), [])
        self.assertEqual(smoothing(first_job(source, **SIMULTANEOUS, **stock(0.06))[1]), [SEMI, ATOL_SEMI])
        self.assertEqual(smoothing(first_job(source, job_type='profile', wall_offset=0)[1]), [FINISH])

    def test_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the 4x/5x allowance and ATOL[A]."""
        tests = SimultaneousJobTests()
        line_5x = ('@line_5x\n    ; SolidCAM event: 5x feed move (usr_smoothing_feed, usr_line; the A direction comes from dir5a,\n'
                   '    ; bR1useDir5a).\n    call @usr_smoothing_feed\n')
        mutants = {
            'line_5x without the smoothing call': ((line_5x, line_5x.replace('    call @usr_smoothing_feed\n', '')),
                                                   tests.check_simultaneous_moves),
            'leads take finishing': (("        if feed_type eq 'finish_feed' or feed_type eq 'finish_feed_floor'\n",
                                      "        if feed_type eq 'finish_feed' or feed_type eq 'finish_feed_floor' or feed_type eq 'feed_lead_in' or feed_type eq 'feed_lead_out'\n"),
                                     tests.check_simultaneous_moves),
            'ATOL under compensation': (('    if iCycle832Mode ne 0 and bCycle832AtolA and iCompActive ne 41 and iCompActive ne 42\n',
                                         '    if iCycle832Mode ne 0 and bCycle832AtolA\n'), tests.check_atol_waits_for_g40),
            'radius from Y alone': (('            nR = nY * nY + nZ * nZ\n', '            nR = nY * nY\n'), tests.check_stock_radius),
            'far Y side ignored': (('            if abs(stock_y_minus + stock_y) > nY\n', '            if false\n'),
                                   tests.check_stock_radius),
            'near Y side ignored': (('            nY = abs(stock_y_minus)\n', '            nY = 0\n'), tests.check_stock_radius),
            'upper Z ignored': (('            if abs(stock_z_plus) > nZ\n', '            if false\n'), tests.check_stock_radius),
            'ATOL only by allowance': (('    if iCycle832Mode ne 0 and bCycle832AtolA and', '    if iCycle832Mode ne 0 and bCycle832AtolA and bCycle832X5 and'),
                                       tests.check_option_off),
            'start_of_file resets only the wall allowance': (('    bWorkpieceUsesA = false\n    call @usr_allowance_reset\n',
                                                              '    bWorkpieceUsesA = false\n    wall_offset = nNoAllowance\n'
                                                              '    floor_offset = nNoAllowance\n'), tests.check_first_job_stock),
            'Drive_surface_Offset ignored': (('        if Drive_surface_Offset ne nNoAllowance and (',
                                              '        if false and ('), self.check_rules),
            'larger allowance decides': ((' or Drive_surface_Offset < nAllow)', ' or Drive_surface_Offset > nAllow)'),
                                         self.check_rules),
            'option ignored': (('    if X5_job and bCycle832X5\n', '    if X5_job\n'), self.check_rules),
            'ATOL in mm': (('(nCycle832Tol * 57.2957795 / nR)', '(nCycle832Tol / nR)'), self.check_rules),
            'ATOL on every job': (('        if X5_job and nCycle832Tol ne nCycle832TolA\n', '        if nCycle832Tol ne nCycle832TolA\n'),
                                  self.check_rules),
            'ATOL kept over a call': (('            nCycle832TolA = -1\n            ; The next move',
                                       '            ; The next move'), tests.check_atol_state),
            'reset keeps the stock allowance': (('    Stock_to_leave = nNoAllowance\n    Drive_surface_Offset = nNoAllowance\n',
                                                 ''), tests.check_reset),
        }
        for label, ((old, new), check) in mutants.items():
            with self.subTest(mutant=label):
                assert_detected(self, check, mutate(old, new), label)


def stop_program(source=None, **cam):
    """A program whose POST ERROR stops it (print, then abort)."""
    return Program(options=NO_JOB_STOP, cam={**MILLING, **cam}, source=source, policies=post_error_policies())


def posted(run, *args, **values):
    """CYCLE832 calls of what run returns; a stop of the post fails the test."""
    try:
        return calls(run(*args, **values))
    except post_abort_error() as exc:
        raise AssertionError(f'the post stopped: {exc}') from exc


def start(p):
    return p.start(tool=1, next_tool=2, next_job_tool_number=1)


class NoAllowanceTests(unittest.TestCase):
    def check_feed_type_jobs(self, source=None):
        for job_type in ('face_milling', 'thread'):
            p = stop_program(source, job_type='profile', wall_offset=0)
            self.assertEqual(posted(start, p), [FINISH])
            cut(p)
            self.assertEqual(posted(same_tool_job, p, 'op2', job_type=job_type), [ROUGH], job_type)
            self.assertEqual(calls(finish_pass(p)), [FINISH], job_type)
            self.assertEqual(calls(rough_move(p)), [ROUGH], job_type)
            # An allowance sent with them does not count: the feed type decides.
            p = stop_program(source, job_type=job_type, wall_offset=0)
            self.assertEqual(posted(start, p), [ROUGH], job_type)

    def test_face_and_thread_milling_go_by_the_feed_type(self):
        """INDEPENDENT: owner rule 2026-10-28. SolidCAM sends no allowance with face and thread
        milling and marks their finishing passes: recording 004, a face job of 5032 moves at
        feed_rate, then 148 at finish_feed; recording 005, five thread turns at feed_rate 0.02 to
        0.05 mm apart, the last turn at finish_feed. They rough and finish those passes. The last
        job's allowance is not theirs: after a profile at wall_offset 0 the face job roughs (before
        the fix it took finishing for all its moves)."""
        self.check_feed_type_jobs()

    def check_missing_allowance(self, source=None):
        p = stop_program(source, wall_offset=0.3)
        self.assertEqual(posted(start, p), [ROUGH])
        cut(p)
        # wall_offset 0 is an allowance: finishing.
        self.assertEqual(posted(same_tool_job, p, 'op2', job_type='profile', wall_offset=0), [FINISH])
        cut(p, 20)
        with self.assertRaises(post_abort_error()):
            same_tool_job(p, 'op3', job_type='profile', **NO_ALLOWANCE)
        self.assertEqual(p.nc()[-1], NO_ALLOWANCE_STOP)

    def test_operation_without_an_allowance_stops(self):
        """INDEPENDENT: owner rule 2026-10-28. An operation without an allowance that is not face or
        thread milling stops the post: its job needs iG187_P. A wall allowance of 0 is an
        allowance (finishing), and the last job's 0.3 mm is not this job's."""
        self.check_missing_allowance()
        p = stop_program(job_type='other_operation', wall_offset=0.3)
        self.assertEqual(posted(start, p), [ROUGH])
        cut(p)
        with self.assertRaises(post_abort_error()):
            same_tool_job(p, 'op2', job_type='other_operation', **NO_ALLOWANCE)
        self.assertEqual(p.nc()[-1], NO_ALLOWANCE_STOP)

    def test_job_parameters_simultaneous_and_drilling_jobs_need_no_allowance(self):
        """INDEPENDENT: iG187_P 1/2/3/-1 sets the type without an allowance; simultaneous 4x jobs and
        drilling jobs take no CYCLE832 by the operation (owner rules 2026-10-27)."""
        # The first job roughs, so iG187_P 1 keeps its call.
        for cam, expected in ((dict(iG187_P=1), []), (dict(iG187_P=2), [SEMI]), (dict(iG187_P=3), [FINISH]),
                              (dict(iG187_P=-1), [DESELECT]), (dict(x5_job=True), [DESELECT]),
                              (dict(job_type='drill'), [DESELECT])):
            with self.subTest(**cam):
                p = stop_program(wall_offset=0.3)
                self.assertEqual(posted(start, p), [ROUGH])
                cut(p)
                self.assertEqual(posted(same_tool_job, p, 'op2', **{'job_type': 'profile', **NO_ALLOWANCE, **cam}),
                                 expected)

    def check_first_job(self, source=None):
        p = stop_program(source, job_type='face_milling')
        p.ev('start_of_file', **HEADER_DEFAULTS)
        self.assertEqual(posted(start, p), [ROUGH])
        p = stop_program(source, job_type='profile')
        p.ev('start_of_file', **HEADER_DEFAULTS)
        p.ev('start_program')
        p.ev('change_tool', tool_number=1, next_tool_number=2, next_job_tool_number=1)
        with self.assertRaises(post_abort_error()):
            p.ev('start_of_job', job_name='op1', **NO_ALLOWANCE)
        self.assertEqual(p.nc()[-1], NO_ALLOWANCE_STOP)

    def test_first_job_of_the_program_has_no_allowance_until_it_sends_one(self):
        """INDEPENDENT: recording 004 starts with a face job; nothing sent wall_offset before it (the
        offline replay had no value to read). A first profile job without one stops."""
        self.check_first_job()


class NoAllowanceMutationTests(unittest.TestCase):
    def test_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the rules for operations without an allowance."""
        feed_jobs = "        if job_type eq 'face_milling' or job_type eq 'thread'\n"
        tests = NoAllowanceTests()
        mutants = {
            'end_of_job keeps the allowance': (('    nPtool_start_plane = tool_start_plane\n    call @usr_allowance_reset\n',
                                                '    nPtool_start_plane = tool_start_plane\n'),
                                               tests.check_missing_allowance),
            'start_of_file keeps the allowance': (('    bWorkpieceUsesA = false\n    call @usr_allowance_reset\n',
                                                   '    bWorkpieceUsesA = false\n'), tests.check_first_job),
            'stop removed': (('            if !X5_job and wall_offset eq nNoAllowance\n', '            if false\n'),
                             tests.check_missing_allowance),
            'marker is a real allowance': (('    nNoAllowance = -9999\n', '    nNoAllowance = 0\n'),
                                           tests.check_missing_allowance),
            'thread by allowance': ((feed_jobs, "        if job_type eq 'face_milling'\n"),
                                    tests.check_feed_type_jobs),
            'face milling by allowance': ((feed_jobs, "        if job_type eq 'thread'\n"),
                                          tests.check_feed_type_jobs),
            'face and thread finishing': ((feed_jobs + '            iMode = 3\n', feed_jobs + '            iMode = 1\n'),
                                          tests.check_feed_type_jobs),
        }
        for label, ((old, new), check) in mutants.items():
            with self.subTest(mutant=label):
                assert_detected(self, check, mutate(old, new), label)


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


def xy_arc(end, start, rel, size, direction, feed_type='finish_feed'):
    return dict(xpos=end[0], ypos=end[1], zpos=end[2], xstart=start[0], ystart=start[1], zstart=start[2],
                xcenter_rel=rel[0], ycenter_rel=rel[1], zcenter_rel=0, arc_size=size, arc_direction=direction,
                arc_plane='xy', feed_type=feed_type)


def machine_pass(p):
    """The compensated finishing wall pass that stopped with alarm 10751 on the machine (2026-11-01),
    in SolidCAM's event order and values (trace of the program): approach, plunge, G41 line along the
    normal of a 45 deg helical lead-in arc, the wall with R3.04 corners and an R1 corner, the 45 deg
    lead-out arc, the G40 line along its normal, the retract."""
    blocks = p.ev('rapid_move', xpos=210.37456, ypos=-17.48355, zpos=25)
    blocks += p.ev('rapid_move', zpos=13.75)
    blocks += p.ev('line', zpos=9.08, feed=4000, feed_type='z_feed')
    blocks += p.ev('compensation', side='comp_left')
    blocks += p.ev('line', xpos=212.65003, ypos=-19.75902, feed=592, feed_type='finish_feed')
    blocks += p.ev('arc', **xy_arc((214, -16.4999, 9), (212.65003, -19.75902, 9.08), (-3.25912, 3.25912), 45, 'ccw',
                                   'feed_link'))
    blocks += p.ev('line', ypos=-10.04, feed_type='finish_feed')
    blocks += p.ev('arc', **xy_arc((210.96, -7, 9), (214, -10.04, 9), (-3.04, 0), 90, 'ccw'))
    blocks += p.ev('line', xpos=192.04, feed_type='finish_feed')
    blocks += p.ev('arc', **xy_arc((189, -10.04, 9), (192.04, -7, 9), (0, -3.04), 90, 'ccw'))
    blocks += p.ev('line', ypos=-12, feed_type='finish_feed')
    blocks += p.ev('arc', **xy_arc((188.0777, -12.99698, 9), (189, -12, 9), (-1, 0), 85.54359, 'cw'))
    blocks += p.ev('line', xpos=187.57792, ypos=-13.03593, feed_type='finish_feed')
    blocks += p.ev('arc', **xy_arc((184.43355, -14.63505, 9.08), (187.57792, -13.03593, 9), (0.35813, -4.59515), 45,
                                   'ccw', 'feed_link'))
    blocks += p.ev('compensation', side='comp_off')
    blocks += p.ev('line', xpos=186.87894, ypos=-16.72684, feed_type='finish_feed')
    blocks += p.ev('rapid_move', zpos=25)
    return blocks


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
        """INDEPENDENT: iG187_P 1-3 is the type of the whole job, -1 none; an X5_job without its
        allowance keeps the reset settings."""
        for cam in (dict(iG187_P=1), dict(iG187_P=2), dict(iG187_P=-1), dict(x5_job=True)):
            with self.subTest(**cam):
                p, _ = first_job(wall_offset=0.3, **cam)
                self.assertEqual(calls(finish_pass(p) + rough_move(p)), [])

    def test_finishing_job_has_nothing_to_switch(self):
        """INDEPENDENT: a job finished by allowance (wall_offset 0) is already finishing."""
        p, start = first_job(job_type='profile', wall_offset=0)
        self.assertEqual(calls(start), [FINISH])
        self.assertEqual(calls(finish_pass(p, side='comp_left')), [])

    def test_finishing_move_is_its_own_nc_line(self):
        """INDEPENDENT: with the skipline joining of the NC stream the call stays on its own line."""
        p, _ = first_job(wall_offset=0.3)
        finish_pass(p)
        nc = p.nc()
        call = nc.index(FINISH)
        self.assertEqual(nc[call - 1:call + 2], ['G1 Z-2 F4000', FINISH, 'G1 X20 F300'], nc)


def compressor(blocks):
    return [block for block in blocks if block.startswith(('CYCLE832', 'COMPOF', 'COMPSURF'))]


class CompensationTests(unittest.TestCase):
    def check_before_selection(self, source=None, side='comp_left', word='G41'):
        p, _ = first_job(source, wall_offset=0.3)
        blocks = finish_pass(p, side=side)
        selection = next(index for index, block in enumerate(blocks) if word in block)
        self.assertEqual(compressor(blocks), [FINISH, COMPOF], blocks)
        self.assertEqual(blocks[selection - 2:selection], [FINISH, COMPOF], blocks)
        on = p.ev('line', xpos=30, feed_type='finish_feed')
        on += p.ev('compensation', side='comp_off')
        on += p.ev('line', xpos=40, feed_type='finish_feed')
        self.assertEqual(compressor(on), [], on)
        self.assertIn('G40', on[-1])
        self.assertEqual(compressor(p.ev('rapid_move', zpos=50)), [])
        self.assertEqual(compressor(p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')), [FINISH])

    def test_compressor_is_off_from_the_compensation_selection_to_g40(self):
        """INDEPENDENT: machine 2026-11-01 (module docstring). Reference trace 2026-10-27, operations
        8 and 11: the compensation event comes before the first finishing move, which selects G41;
        the finishing call and COMPOF go before that block, while the control has no compensation
        on, and the finishing call comes again before the first feed move after G40, not on the
        rapid between."""
        self.check_before_selection()

    def check_right_side(self, source=None):
        self.check_before_selection(source, side='comp_right', word='G42')

    def test_right_side_compensation_too(self):
        """INDEPENDENT: G42 is the same 2D tool radius compensation on the other side of the contour."""
        self.check_right_side()

    def check_machine_pass(self, source=None):
        p, start = first_job(source, job_type='profile', wall_offset=0)
        self.assertEqual(calls(start), [FINISH])
        machine_pass(p)
        nc = p.nc()
        g41 = next(index for index, line in enumerate(nc) if 'G41' in line)
        g40 = next(index for index, line in enumerate(nc) if 'G40' in line and index > g41)
        self.assertEqual(nc[g41 - 1], COMPOF, nc)
        self.assertTrue(nc[g41].startswith('G41 X212.65003 Y-19.75902'), nc[g41])
        window = nc[g41:g40 + 1]
        self.assertEqual(compressor(window), [], window)
        self.assertEqual(sum(' AR=' in line for line in window), 5, window)
        self.assertEqual(nc[g40 + 1], 'G0 Z25', nc)
        self.assertEqual(calls(nc), [FINISH], nc)

    def test_machine_pass_runs_without_the_compressor(self):
        """INDEPENDENT: machine 2026-11-01 (module docstring): this pass stopped with alarm 10751 at
        its lead-out arc with COMPSURF on and ran with COMPOF before its G41 block. COMPOF is the NC
        line before the G41 block, nothing comes between it and the G40 block, the finishing call
        of the job stays over the pass (G645, tolerance, dynamics), and the retract after G40 gets no
        call back (a rapid; the next feed move would)."""
        self.check_machine_pass()

    def check_two_passes(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        blocks = finish_pass(p, side='comp_left')
        blocks += p.ev('compensation', side='comp_off')
        blocks += p.ev('line', xpos=45, feed_type='finish_feed')
        blocks += p.ev('line', zpos=-4, feed=4000, feed_type='z_feed')
        blocks += p.ev('compensation', side='comp_left')
        blocks += p.ev('line', xpos=40, feed=300, feed_type='finish_feed')
        blocks += p.ev('compensation', side='comp_off')
        blocks += p.ev('line', xpos=10, feed_type='finish_feed')
        blocks += p.ev('rapid_move', zpos=50)
        blocks += p.ev('rapid_move', xpos=0)
        self.assertEqual(compressor(blocks), [FINISH, COMPOF, FINISH, COMPOF], blocks)
        selections = [index for index, block in enumerate(blocks) if 'G41' in block]
        self.assertEqual([blocks[index - 1] for index in selections], [COMPOF, COMPOF], blocks)
        plunge = blocks.index('G1 Z-4 F4000')
        self.assertEqual(blocks[plunge - 1], FINISH, blocks)

    def test_second_pass_of_the_same_call_switches_again(self):
        """INDEPENDENT: two compensated finishing passes of one CYCLE832, with a plunge between them:
        the call again before the plunge (a feed move), COMPOF again before the second G41 block,
        and nothing on the rapids after its G40."""
        self.check_two_passes()

    def check_thread_passes(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        blocks = finish_pass(p, side='comp_left')
        blocks += p.ev('compensation', side='comp_off')
        blocks += p.ev('line', xpos=30, feed_type='finish_feed')
        blocks += p.ev('rapid_move', xpos=10, ypos=10)
        blocks += p.ev('compensation', side='comp_right')
        blocks += p.ev('line', xpos=20, feed=300, feed_type='finish_feed')
        self.assertEqual(compressor(blocks), [FINISH, COMPOF], blocks)
        self.assertIn('G42', blocks[-1])

    def test_next_compensated_pass_gets_no_call_back(self):
        """INDEPENDENT: the call comes back for a feed move without compensation only. A feed move
        that selects G41/G42 again after G40 (the next pass of a thread: G40, G0, G42) keeps the
        compressor off: no call, which would select the compressor, and no second COMPOF."""
        self.check_thread_passes()

    def check_4x_rapid_selection(self, source=None):
        for event in ('move_4x', 'move_5x'):
            with self.subTest(event=event):
                p, _ = first_job(source, wall_offset=0.3)
                p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
                p.ev('line', zpos=20, feed=4000, feed_type='z_feed')
                p.ev('compensation', side='comp_left')
                blocks = p.ev(event, xpos=20, ypos=12, zpos=20, apos=5, dir5a='ccw')
                selection = next(index for index, block in enumerate(blocks) if 'G41' in block)
                self.assertEqual(compressor(blocks), [COMPOF], blocks)
                self.assertLess(blocks.index(COMPOF), selection, blocks)

    def test_4x_rapid_that_selects_compensation(self):
        """INDEPENDENT: a 4x/5x rapid can carry the G41/G42 selection like a G0 (usr_rapid writes it);
        its COMPOF comes before that block as with rapid_move and the feed moves."""
        self.check_4x_rapid_selection()

    def check_waits_for_g40(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='comp_left')
        self.assertEqual(compressor(rough_move(p)), [COMPOF])
        on = p.ev('line', xpos=60, feed=300, feed_type='finish_feed')
        on += p.ev('compensation', side='comp_off')
        on += p.ev('line', xpos=70, feed_type='finish_feed')
        self.assertEqual(compressor(on), [], on)
        self.assertIn('G40', on[-1])
        after = p.ev('rapid_move', zpos=50)
        self.assertEqual(after[0], FINISH, after)
        # The call selects the compressor of its type again.
        self.assertEqual(compressor(after), [FINISH], after)

    def test_call_waits_for_the_move_after_g40(self):
        """INDEPENDENT: no CYCLE832 while compensation is on at the control: its blocks without
        motion count as empty blocks of TRC (MD20250 CUTCOM_MAXNUM_DUMMY_BLOCKS = 5 on this machine,
        backups/NOLOG.ard; alarm 10762 above). The call follows the block that writes G40 and
        selects the compressor again by itself.
        CHARACTERIZATION of the late call: a finishing pass that starts while compensation is
        already on keeps the job's type (here roughing, without its compressor) until G40. With
        the VMID's CompensationRoughPasses="0" SolidCAM compensates only finishing passes, which
        select G41 on their first move and get the call before it
        (test_compressor_is_off_from_the_compensation_selection_to_g40)."""
        self.check_waits_for_g40()

    def test_same_tool_job_with_compensation_on_waits(self):
        """INDEPENDENT: compensation the last job left on below the clearance plane (end_of_job
        cancels it only above) holds the next job's call until G40."""
        p, _ = first_job(wall_offset=0.3)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='comp_left')
        rough_move(p)
        self.assertEqual(compressor(same_tool_job(p, 'op2', wall_offset=0)), [])
        off = p.ev('compensation', side='comp_off') + p.ev('line', xpos=50, feed_type='finish_feed')
        self.assertEqual(compressor(off), [], off)
        self.assertEqual(p.ev('rapid_move', zpos=50)[0], FINISH)

    def check_deselection_clears(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='comp_left')
        self.assertEqual(compressor(rough_move(p)), [COMPOF])
        p.ev('compensation', side='comp_off')
        p.ev('rapid_move', xpos=50, ypos=10, zpos=50)
        boundary, job = second_tool(p, iG187_P=-1)
        self.assertEqual(compressor(boundary + job), [DESELECT])
        self.assertEqual(compressor(cut(p) + finish_pass(p, side='comp_left')), [])

    def check_drilling_stops(self, source=None):
        # The pass ends with compensation on below the clearance plane (end_of_job cancels it only
        # above), the same with CAM's comp_off after the last move (no block wrote G40), or at the
        # clearance plane without comp_off (end_of_job cancels it, CAM still asks for it).
        for side in ('comp_left', 'comp_right'):
            for cam in (dict(iG187_P=1), dict(iG187_P=-1)):
                for ending in ('on', 'off', 'asked'):
                    with self.subTest(side=side, ending=ending, **cam):
                        p = stop_program(source, wall_offset=0.3)
                        posted(start, p)
                        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
                        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
                        p.ev('compensation', side=side)
                        rough_move(p)
                        if ending == 'off':
                            p.ev('compensation', side='comp_off')
                        if ending == 'asked':
                            p.ev('rapid_move', zpos=50)
                        posted(same_tool_job, p, 'op2', job_type='drilling', **cam)
                        with self.assertRaises(post_abort_error()):
                            p.ev('drill', xpos=10, ypos=10, zpos=10)
                        self.assertEqual(p.nc()[-1], DRILL_COMP_STOP)
                        self.assertNotIn('MCALL', ' '.join(p.nc()))

    def test_drilling_cycle_with_compensation_on_stops(self):
        """INDEPENDENT: owner 2026-11-01: compensation still on at a drilling cycle stops the post,
        with or without a CYCLE832 to deselect: compensation the last job left on below the
        clearance plane (end_of_job cancels it only above), also after a comp_off that no block
        followed, and compensation CAM still asks for after end_of_job cancelled it at the
        clearance plane (the drill job's rapid would select it again). No cycle is written."""
        self.check_drilling_stops()

    def check_program_end_stops(self, source=None):
        for side in ('comp_left', 'comp_right'):
            with self.subTest(side=side):
                p = Program(options={'bHomeend': False}, cam={**MILLING, 'wall_offset': 0.3}, source=source,
                            policies=post_error_policies())
                posted(start, p)
                p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
                p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
                p.ev('compensation', side=side)
                rough_move(p)
                p.ev('end_of_job', next_job_tool_number=0)
                with self.assertRaises(post_abort_error()):
                    p.ev('end_program')
                self.assertEqual(p.nc()[-1], COMP_STOP)

    def test_program_end_with_compensation_on_stops(self):
        """INDEPENDENT: owner 2026-11-01: without the end homing, whose Z homing would cancel it,
        compensation still on at the program end meets the deselection of CYCLE832 (blocks without
        motion under TRC, MD20250 / alarm 10762): the post stops."""
        self.check_program_end_stops()

    def test_deselection_ends_the_compressor_switch(self):
        """INDEPENDENT: CYCLE832(0,0,1) returns the control to COMPOF and ends the switch, and without
        a CYCLE832 the compressor is off already: after a pass that ended with G40 on its last move,
        the tool change deselects and a job without CYCLE832 gets no call and no COMPOF, also when
        it compensates."""
        self.check_deselection_clears()


class StopTests(unittest.TestCase):
    """Owner 2026-11-01: CYCLE832 goes off before every M1/M0 of the post, so an operator who stops or
    resets there is not left in G645, the compressor and DYN* (a reset may keep the G groups)."""

    def check_job_stop(self, source=None):
        p, _ = first_job(source, {'bOptstpjob': True}, wall_offset=0.3)
        cut(p)
        job = same_tool_job(p, 'op2', wall_offset=0.3)
        self.assertEqual(calls(job), [DESELECT, ROUGH], job)
        self.assertLess(job.index(DESELECT), job.index('M1'), job)
        self.assertLess(job.index('M1'), job.index(ROUGH), job)

    def test_job_m1_comes_after_the_deselection(self):
        """INDEPENDENT: the M1 between two jobs of the same tool (bOptstpjob) comes after
        CYCLE832(0,0,1); the next job selects its type after the stop, also the same one."""
        self.check_job_stop()

    def check_job_stop_under_compensation(self, source=None):
        p = Program(options={'bOptstpjob': True}, cam={**MILLING, 'wall_offset': 0.3}, source=source,
                    policies=post_error_policies())
        posted(start, p)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='comp_left')
        rough_move(p)
        job = p.ev('end_of_job', next_job_tool_number=1)
        try:
            job += p.ev('start_of_job', job_name='op2', next_job_tool_number=1, wall_offset=0.3)
        except post_abort_error() as exc:
            raise AssertionError(f'the post stopped: {exc}') from exc
        self.assertIn('M1', job)
        self.assertEqual(calls(job), [], job)

    def test_job_m1_with_compensation_on_keeps_the_held_call(self):
        """INDEPENDENT: compensation the last job left on below the clearance plane holds the call
        (MD20250, alarm 10762), also its deselection before the job M1: the M1 comes, no call."""
        self.check_job_stop_under_compensation()

    def check_m0_stop(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        cut(p)
        end = p.ev('end_of_job', next_job_tool_number=1, bStopM00=True)
        self.assertEqual(calls(end), [DESELECT], end)
        self.assertLess(end.index(DESELECT), end.index('M0'), end)
        job = p.ev('start_of_job', job_name='op2', next_job_tool_number=1, wall_offset=0.3)
        self.assertEqual(calls(job), [ROUGH], job)

    def test_m0_comes_after_the_deselection(self):
        """INDEPENDENT: the M0 of a job boundary (bStopM00) comes after CYCLE832(0,0,1); the return
        move after it selects nothing and the next job its own type."""
        self.check_m0_stop()

    def check_m0_homing_under_compensation(self, source=None):
        p = Program(options={**NO_JOB_STOP, 'sHomestrstpsame': '8::G75 Z1=0.'}, cam={**MILLING, 'wall_offset': 0.3},
                    source=source, policies=post_error_policies())
        posted(start, p)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='comp_left')
        rough_move(p)
        try:
            end = p.ev('end_of_job', next_job_tool_number=1, bStopM00=True)
        except post_abort_error() as exc:
            raise AssertionError(f'the post stopped: {exc}') from exc
        g40 = next(index for index, block in enumerate(end) if 'G40' in block)
        self.assertEqual(end[g40 - 1:g40 + 3], ['G75 Z1=0.', end[g40], DESELECT, 'M0'], end)

    def test_m0_homing_cancels_compensation_before_the_deselection(self):
        """INDEPENDENT: the Z homing of the M0 (sHomestrstpsame) cancels compensation the job left
        on below the clearance plane (G40 after the Z homing, PP-062), so CYCLE832(0,0,1) follows it
        and comes before the M0, not held over the stop."""
        self.check_m0_homing_under_compensation()

    def check_program_end_stop(self, source=None):
        p, _ = first_job(source, {'bOptstpend': True}, wall_offset=0.3)
        cut(p)
        p.ev('end_of_job', next_job_tool_number=0)
        end = p.ev('end_program')
        self.assertEqual(end[-3:], [DESELECT, 'M1', 'M30'], end)

    def test_program_end_m1_comes_after_the_deselection(self):
        """INDEPENDENT: the M1 before the program end (bOptstpend) comes after CYCLE832(0,0,1)."""
        self.check_program_end_stop()

    def check_index_stop(self, source=None):
        p, _ = first_job(source, wall_offset=0.3)
        cut(p)
        blocks = p.ev('end_of_job', next_job_tool_number=1)
        blocks += p.ev('tmatrix', angle_4x_around_x=90)
        blocks += p.ev('start_of_job', job_name='op2', next_job_tool_number=1, wall_offset=0.05)
        turn = next(index for index, block in enumerate(blocks) if 'A=' in block)
        self.assertEqual(calls(blocks), [DESELECT, SEMI], blocks)
        self.assertLess(blocks.index(DESELECT), blocks.index('M1'), blocks)
        self.assertLess(blocks.index('M1'), turn, blocks)
        self.assertLess(turn, blocks.index(SEMI), blocks)

    def test_index_m1_comes_after_the_deselection(self):
        """INDEPENDENT: the M1 before an A index between two jobs (tmatrix, bOptstpindex) comes after
        CYCLE832(0,0,1); the job after the turn selects its type."""
        self.check_index_stop()

    def check_boundary_index(self, source=None):
        p, _ = first_job(source, {'i4xIndexMode': 1}, wall_offset=0.3)
        cut(p)
        finish_pass(p)
        blocks = p.ev('rapid_move', zpos=50)
        blocks += p.ev('end_of_job', next_job_tool_number=1)
        blocks += p.ev('tmatrix', angle_4x_around_x=90)
        blocks += p.ev('start_of_job', job_name='op2', next_job_tool_number=1, position=2, wall_offset=0.05)
        self.assertEqual(calls(blocks), [DESELECT, SEMI], blocks)
        self.assertLess(blocks.index('G0 G17 G90 G55'), blocks.index(SEMI), blocks)

    def test_index_with_a_work_offset_step_selects_only_the_next_job(self):
        """INDEPENDENT: an index between two jobs of the same tool that also steps the work offset
        (i4xIndexMode 1): after CYCLE832(0,0,1) and the M1 the work-offset block selects no type,
        not the finishing one of the last job's last pass (review 2026-11-01); the next job selects
        its own after it."""
        self.check_boundary_index()

    def check_index_before_the_boundary(self, source=None):
        # No subTest: the mutation self-check runs this on its own test case.
        for stop in ('job M1', 'M0'):
            p, _ = first_job(source, {'bOptstpjob': stop == 'job M1'}, wall_offset=0.3, iWorkOffset_Method=1,
                             home_user_name='54')
            cut(p)
            finish_pass(p)
            p.ev('rapid_move', zpos=50)
            blocks = p.ev('fourth_axis', angle=90)
            blocks += p.ev('end_of_job', next_job_tool_number=1, bStopM00=stop == 'M0')
            blocks += p.ev('start_of_job', job_name='op2', next_job_tool_number=1, home_user_name='55',
                           wall_offset=0.05)
            self.assertEqual(calls(blocks), [DESELECT, SEMI], (stop, blocks))
            self.assertLess(blocks.index('G0 G17 G90 G55'), blocks.index(SEMI), (stop, blocks))

    def test_type_kept_over_an_index_ends_with_the_job(self):
        """INDEPENDENT: an index after the last move of a job keeps the job's type for its next move;
        there is none. The return move after an M0 (bStopM00) and the work-offset block of the next
        job select no type, not the finishing one of the last pass; the next job selects its own."""
        self.check_index_before_the_boundary()

    def check_index_inside_job(self, source=None, iG187_P=None):
        cam = dict(wall_offset=0.3) if iG187_P is None else dict(wall_offset=0.3, iG187_P=iG187_P)
        want = ROUGH if iG187_P is None else SEMI
        p, _ = first_job(source, **cam)
        cut(p)
        blocks = p.ev('fourth_axis', angle=90)
        blocks += p.ev('rapid_move', xpos=20, ypos=10, zpos=50)
        blocks += p.ev('line', zpos=-2, feed=200, feed_type='z_feed')
        self.assertEqual(calls(blocks), [DESELECT, want], blocks)
        self.assertLess(blocks.index(DESELECT), blocks.index('M1'), blocks)
        rapid = next(index for index, block in enumerate(blocks) if 'X20' in block)
        self.assertLess(blocks.index(want), rapid, blocks)

    def test_index_inside_a_job_selects_the_type_again(self):
        """INDEPENDENT: the M1 of an A index inside a job (fourth_axis) comes after CYCLE832(0,0,1);
        the job's next move selects its type again before it, by allowance or by iG187_P (a plunge
        would not switch the type by itself)."""
        self.check_index_inside_job()
        self.check_index_inside_job(iG187_P=2)

    def check_index_stop_under_compensation(self, source=None):
        p = stop_program(source, wall_offset=0.3)
        posted(start, p)
        p.ev('rapid_move', xpos=10, ypos=10, zpos=50)
        p.ev('line', zpos=-2, feed=4000, feed_type='z_feed')
        p.ev('compensation', side='comp_left')
        rough_move(p)
        try:
            blocks = p.ev('fourth_axis', angle=90)
        except post_abort_error() as exc:
            raise AssertionError(f'the post stopped: {exc}') from exc
        self.assertIn('M1', blocks)
        self.assertEqual(calls(blocks), [], blocks)

    def test_index_m1_with_compensation_on_keeps_the_held_call(self):
        """INDEPENDENT: compensation still on at an A index inside a job holds the call (MD20250,
        alarm 10762), also its deselection before the index M1; the index homing cancels G41 after
        the stop (PP-062)."""
        self.check_index_stop_under_compensation()

    def test_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the deselections before the stops."""
        tool_change = ('    if iCycle832Mode ne 0\n        ; The optional stop, M06 and the safety block run in the reset settings of the control; the\n'
                       '        ; next operation selects its own after M06 (usr_smoothing).\n        call @usr_smoothing_off\n    endif\n'
                       '    if !bStopM00difftool and bOptstptc\n        call @usr_optionalstop\n    endif\n')
        program_end_off = ('    if iCycle832Mode ne 0\n        ; Before the optional stop, so the control is in its reset settings at a stop or reset\n'
                           '        ; there; M30 resets the G groups too (machine data), M2 or a reset that keeps them would not.\n'
                           '        call @usr_smoothing_off\n    endif\n')
        program_end_stop = '    if bOptstpend\n        call @usr_optionalstop\n    endif\n'
        mutants = {
            'job M1 keeps CYCLE832': (('            call @usr_smoothing_job_stop\n            call @usr_optionalstop\n',
                                       '            call @usr_optionalstop\n'), self.check_job_stop),
            'job stop under compensation': (('    if iCycle832Mode ne 0 and iCompActive ne 41 and iCompActive ne 42\n        call @usr_smoothing_off\n',
                                             '    if iCycle832Mode ne 0\n        call @usr_smoothing_off\n'),
                                            self.check_job_stop_under_compensation),
            'M0 keeps CYCLE832': (('    call @usr_smoothing_job_stop\n    call @usr_forcedstop\n', '    call @usr_forcedstop\n'),
                                  self.check_m0_stop),
            'index M1 keeps CYCLE832': (('            ; Not right after another stop with no motion since (the job M1 of a same-tool job).\n'
                                         '            call @usr_smoothing_index_stop\n',
                                         '            ; Not right after another stop with no motion since (the job M1 of a same-tool job).\n'),
                                        self.check_index_stop),
            'tool change M1 before the deselection': ((tool_change, tool_change.split('    if !bStopM00difftool')[0].replace(
                '    if iCycle832Mode ne 0', '    if !bStopM00difftool and bOptstptc\n        call @usr_optionalstop\n    endif\n    if iCycle832Mode ne 0')),
                PlacementTests().check_tool_change),
            'program end M1 before the deselection': ((program_end_off + program_end_stop, program_end_stop + program_end_off),
                                                      self.check_program_end_stop),
            'M0 deselection before its homing': (('    call @usr_prep_home_axis\n    call @usr_smoothing_job_stop\n',
                                                  '    call @usr_smoothing_job_stop\n    call @usr_prep_home_axis\n'),
                                                 self.check_m0_homing_under_compensation),
            'work-offset block selects a type': (('            bTlchg = true\n            call @usr_rapid\n',
                                                  '            bTlchg = true\n            call @rapid_move\n'),
                                                 self.check_boundary_index),
            'M0 return selects a type': (('    ; A index (usr_smoothing_index_stop) is no longer asked for, and the next job selects its own.\n'
                                          '    call @usr_rapid\n',
                                          '    call @rapid_move\n'), self.check_index_before_the_boundary),
            'index M1 inside a job drops the type': (('        call @usr_smoothing_off\n        iCycle832Want = iWant\n'
                                                      '        nCycle832WantTol = nWantTol\n', '        call @usr_smoothing_off\n'),
                                                     self.check_index_inside_job),
            'index stop under compensation': (('    if iCycle832Mode ne 0 and iCompActive ne 41 and iCompActive ne 42\n'
                                               '        iWant = iCycle832Want\n',
                                               '    if iCycle832Mode ne 0\n        iWant = iCycle832Want\n'),
                                              self.check_index_stop_under_compensation),
        }
        for label, ((old, new), check) in mutants.items():
            with self.subTest(mutant=label):
                assert_detected(self, check, mutate(old, new), label)


class FinishPassMutationTests(unittest.TestCase):
    def test_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the finishing switch, the compensation hold, the
        compressor switch and the compensation stops."""
        finish = "        if feed_type eq 'finish_feed' or feed_type eq 'finish_feed_floor'\n"
        compof = '            if iCycle832Mode ne 0 and !bCycle832CompOff\n'
        back = ('    if bCycle832CompOff and bCycle832FeedApply and iDiametercomp ne 41 and iDiametercomp ne 42\n'
                '        bCompBack = true\n')
        drill_stop = ("    if iCompActive eq 41 or iCompActive eq 42 or iDiametercomp eq 41 or iDiametercomp eq 42\n"
                      "        print 'POST ERROR: Cutter compensation is still on at a drilling")
        deselect_stop = ("    if iCompActive eq 41 or iCompActive eq 42\n"
                         "        print 'POST ERROR: Cutter compensation is still on where")
        mutants = {
            'finishing switch removed': ((finish, '        if false\n'), FinishPassTests.check_switch),
            'floor finishing ignored': ((finish, "        if feed_type eq 'finish_feed'\n"),
                                        FinishPassTests.check_switch),
            'cutting feed keeps finishing': (("        if feed_type eq 'feed_rate'\n", '        if false\n'),
                                             FinishPassTests.check_switch),
            'compensation hold removed': (('        if iCompActive ne 41 and iCompActive ne 42\n            skipline',
                                           '        if true\n            skipline'), CompensationTests.check_waits_for_g40),
            'rapid does not apply': (('    call @usr_smoothing_apply\n    call @usr_rapid\n',
                                      '    call @usr_rapid\n'), CompensationTests.check_waits_for_g40),
            'apply after the line': (('    call @usr_smoothing_feed\n    call @usr_line\nendp',
                                      '    call @usr_line\n    call @usr_smoothing_feed\nendp'),
                                     CompensationTests.check_before_selection),
            'compressor kept under compensation': ((compof, '            if false\n'),
                                                   CompensationTests.check_machine_pass),
            'COMPOF without CYCLE832': ((compof, '            if !bCycle832CompOff\n'),
                                        CompensationTests.check_deselection_clears),
            'right side keeps the compressor': (('        if iDiametercomp eq 41 or iDiametercomp eq 42\n',
                                                 '        if iDiametercomp eq 41\n'), CompensationTests.check_right_side),
            'compressor not restored': ((back, '    if false\n        bCompBack = true\n'),
                                        CompensationTests.check_two_passes),
            'restored on rapids': ((back, back.replace(' and bCycle832FeedApply', '')),
                                   CompensationTests.check_machine_pass),
            'feed moves not marked': (('    bCycle832FeedApply = true\n    call @usr_smoothing_apply\n',
                                       '    call @usr_smoothing_apply\n'), CompensationTests.check_two_passes),
            'call keeps the switch': (('            bCycle832CompOff = false\n            nCycle832TolA = -1\n',
                                       '            nCycle832TolA = -1\n'), CompensationTests.check_two_passes),
            'drilling under compensation': ((drill_stop, "    if false\n" + drill_stop.split('\n', 1)[1]),
                                            CompensationTests.check_drilling_stops),
            'drilling with compensation asked for': ((drill_stop, drill_stop.replace(
                ' or iDiametercomp eq 41 or iDiametercomp eq 42', '')), CompensationTests.check_drilling_stops),
            'drilling stop on the left side only': ((drill_stop, drill_stop.replace(
                'iCompActive eq 41 or iCompActive eq 42', 'iCompActive eq 41')), CompensationTests.check_drilling_stops),
            'deselection stop on the left side only': ((deselect_stop, deselect_stop.replace(
                'iCompActive eq 41 or iCompActive eq 42', 'iCompActive eq 41')), CompensationTests.check_program_end_stops),
            'restored on the next selection': ((back, back.replace(' and iDiametercomp ne 41 and iDiametercomp ne 42', '')),
                                               CompensationTests.check_thread_passes),
            'deselection under compensation': ((deselect_stop, "    if false\n" + deselect_stop.split('\n', 1)[1]),
                                               CompensationTests.check_program_end_stops),
            'COMPOF does not set the switch': (("                {nb,'COMPOF'}\n                bCycle832CompOff = true\n",
                                                "                {nb,'COMPOF'}\n"), CompensationTests.check_two_passes),
            'move_4x without the apply': (('    call @usr_camdbg_move((4))\n    call @usr_smoothing_apply\n',
                                           '    call @usr_camdbg_move((4))\n'), CompensationTests.check_4x_rapid_selection),
            'move_5x without the apply': (('    call @usr_camdbg_move((5))\n    call @usr_smoothing_apply\n',
                                           '    call @usr_camdbg_move((5))\n'), CompensationTests.check_4x_rapid_selection),
            'deselection keeps the switch': (('    nCycle832Tol = 0\n    bCycle832CompOff = false\n',
                                              '    nCycle832Tol = 0\n'), CompensationTests.check_deselection_clears),
        }
        for label, ((old, new), check) in mutants.items():
            with self.subTest(mutant=label):
                owner = FinishPassTests() if check.__qualname__.startswith('FinishPass') else CompensationTests()
                assert_detected(self, lambda source: check(owner, source), mutate(old, new), label)


if __name__ == '__main__':
    unittest.main()
