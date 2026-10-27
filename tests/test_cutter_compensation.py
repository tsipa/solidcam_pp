"""Cutter radius compensation (G40/G41/G42) is switched only on linear blocks.

Oracle (INDEPENDENT): Sinumerik Programming Manual Fundamentals, TRC (G40, G41, G42): in the block with
G40/G41/G42, G0 or G1 must be active and at least one axis of the working plane must be programmed;
selecting or deselecting it on a G2/G3 block raises an alarm. A rapid that switches TRC therefore
programs an axis of the working plane (X and Y in G17, Y in G19, X in G18, at the current position when
SolidCAM did not move them), so the change happens on that rapid, before any homing, index, tool change
or program end. Deselection moves the tool centre from the compensated point onto the programmed one, so
a G17 rapid that climbs deselects after the climb ('G0 Z50' / 'G40 X30 Y30'), not low near the wall.
A Z-only G1 plunge keeps its pre-fix form ('G1 G41 Z-1'). TRC must be off at a tool change, and the
post's TRC state must match the control's. TRC that no linear block deselected (CAM switched it off
after the last retract, or never) is deselected at the end of the job when the tool stands at or above
the clearance plane (G17), else right after the Z homing of the next post homing, before the XY homing.
"""
import re
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from test_history_regressions import history_engine
from test_offline import PP
from program_session import Program, post_abort_error, require_nc_stream, scripted_input_policies
from support import covers
from test_post_homing_reposition import Session


def engine_with_comp(active, source=None):
    engine = history_engine(source)
    engine.set(iDiametercomp=active, iCompActive=active)
    engine.changed['idiametercomp'] = False
    return engine


ARC = dict(xy='xy', zx='zx', yz='yz', arc_plane='xy', arc_direction='ccw', arc_size=90,
           radius=10, xstart=10, ystart=0, zstart=0, xcenter=0, ycenter=0, zcenter=0,
           xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)


def event(engine, call, changed=(), **values):
    engine.set(**values)
    for key in ('xpos', 'ypos', 'zpos', 'apos', 'bpos', 'feed'):
        engine.changed[key] = False
    engine.changed.update({key: True for key in changed})
    engine.output.clear()
    engine.call(call)
    return [block.strip() for block in ''.join(engine.output).splitlines() if block.strip()]


class CutterCompensationTests(unittest.TestCase):
    def test_compensation_off_on_a_z_retract_programs_the_plane_axes(self):
        engine = engine_with_comp(41)
        event(engine, 'compensation', side='off')
        self.assertEqual(event(engine, 'rapid_move', ['zpos'], zpos=50), ['G0 G40 X12 Y23 Z50'])
        self.assertEqual(event(engine, 'rapid_move', ['xpos', 'ypos'], xpos=30, ypos=40), ['X30 Y40'])

    def test_compensation_on_before_z_approach_is_selected_on_the_approach(self):
        engine = engine_with_comp(40)
        event(engine, 'compensation', side='left')
        self.assertEqual(event(engine, 'rapid_move', ['zpos'], zpos=5), ['G0 G41 X12 Y23 Z5'])
        self.assertEqual(event(engine, 'line', ['zpos'], zpos=-1), ['G1 Z-1'])

    def test_z_only_plunge_keeps_its_pre_fix_form(self):
        engine = engine_with_comp(40)
        event(engine, 'compensation', side='left')
        self.assertEqual(event(engine, 'line', ['zpos'], zpos=-1), ['G41 Z-1'])   # G1 is modal here

    def test_compensation_on_before_approach_rapid_is_posted_on_the_rapid(self):
        engine = engine_with_comp(40)
        event(engine, 'compensation', side='left')
        self.assertEqual(event(engine, 'rapid_move', ['xpos', 'ypos'], xpos=0, ypos=0), ['G0 G41 X0 Y0'])
        self.assertEqual(event(engine, 'line', ['xpos'], xpos=20), ['G1 X20'])  # G41 not repeated

    def test_unchanged_compensation_is_not_repeated_on_rapids(self):
        engine = engine_with_comp(41)
        self.assertEqual(event(engine, 'rapid_move', ['xpos'], xpos=5), ['G0 X5'])

    def test_tool_change_safety_blocks_cancel_compensation(self):
        for procedure, first in (('usr_ct_before_firsttool', True), ('usr_ct_before_notfirsttool', False)):
            with self.subTest(procedure=procedure):
                engine = engine_with_comp(41)
                engine.set(first_tool=first, machine_plane='xy', xy='xy', zx='zx', yz='yz', bStopM00difftool=True)
                output = event(engine, procedure)
                safety = [block for block in output if block.startswith('G17')]
                self.assertEqual(safety, ['G17 G40 G64 G90'])

    def test_second_tool_selects_compensation_after_the_safety_block(self):
        # The first tool change leaves bSafetyprep set; the safety block's G40 must reach the post state,
        # otherwise the next tool's G41 is an equal assignment and never posted.
        engine = engine_with_comp(41)
        engine.set(first_tool=False, bSafetyprep=True, machine_plane='xy', xy='xy', zx='zx', yz='yz',
                   bStopM00difftool=True)
        self.assertIn('G17 G40 G64 G90', event(engine, 'usr_ct_before_notfirsttool'))
        event(engine, 'compensation', side='left')
        output = event(engine, 'line', ['xpos'], xpos=20)
        self.assertRegex(' '.join(output), r'\bG41\b.*X20', output)

    def test_compensation_change_on_an_arc_stops_the_post(self):
        for before, side in ((40, 'left'), (41, 'off'), (41, 'right')):
            with self.subTest(before=before, side=side):
                engine = engine_with_comp(before)
                engine.set(**ARC)
                event(engine, 'compensation', side=side)
                with self.assertRaisesRegex(UnsupportedGPPL, 'Cutter compensation change on an arc'):
                    event(engine, 'arc', ['xpos', 'ypos'], xpos=0, ypos=10)

    def test_abort_stops_the_post_after_the_prompt(self):
        require_nc_stream()
        engine = history_engine()
        scripted = Engine(PP.read_text(encoding='utf-8-sig'), policies=scripted_input_policies())
        scripted.set(**engine.state)
        scripted.changed.update(engine.changed)
        scripted.set(iDiametercomp=40, iCompActive=40, **ARC)
        scripted.changed['idiametercomp'] = False
        event(scripted, 'compensation', side='left')
        with self.assertRaises(post_abort_error()):
            event(scripted, 'arc', ['xpos', 'ypos'], xpos=0, ypos=10)
        self.assertFalse(any(line.startswith('G3') for line in scripted.nc_lines()), scripted.nc_lines())

    def test_compensation_switched_back_before_an_arc_does_not_stop_the_post(self):
        engine = engine_with_comp(40)
        engine.set(**ARC)
        event(engine, 'compensation', side='left')
        event(engine, 'compensation', side='off')
        output = event(engine, 'arc', ['xpos', 'ypos'], xpos=0, ypos=10)
        self.assertTrue(any(re.match(r'G3\b', block) for block in output), output)
        self.assertFalse(re.search(r'\bG4[012]\b', ' '.join(output)), output)

    def test_arc_with_unchanged_compensation_has_no_trc_word(self):
        engine = engine_with_comp(41)
        engine.set(**ARC)
        output = event(engine, 'arc', ['xpos', 'ypos'], xpos=0, ypos=10)
        self.assertTrue(any(re.match(r'G3\b', block) for block in output), output)
        self.assertFalse(re.search(r'\bG4[012]\b', ' '.join(output)), output)

    def test_climb_puts_the_pending_compensation_on_the_xy_block(self):
        session = Session()
        session.engine.set(iDiametercomp=41, iCompActive=41, **{k: v for k, v in ARC.items() if k in ('xy', 'zx', 'yz')})
        session.engine.set(COMP_LEFT='left', COMP_RIGHT='right', COMP_OFF='off')
        session.step('line_5x', ['zpos'], zpos=5, feed_type='feed_cut')
        session.step('compensation', side='off')
        session.step('end_of_job')
        session.step('start_of_job')
        output = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=50)
        self.assertEqual(output, ['G0 Z50', 'G40 X100 Y100'])

    def test_work_offset_change_cancels_compensation_left_on(self):
        # Same tool, next job in G55 while the last job left G41 on: the control still has G41.
        session = Session()
        session.engine.set(iDiametercomp=41, iCompActive=41, first_tool=True, bLimit_3axis=False,
                           bWorkoffsettc=True, iWorkOffset_Method=1, home_user_name='54')
        session.step('line_5x', ['xpos'], xpos=20, feed_type='feed_cut')
        session.step('end_of_job')
        session.engine.set(home_user_name='55')
        self.assertIn('G55', ' '.join(session.step('start_of_job')))
        output = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=50)
        self.assertIn('G40', ' '.join(output), output)

    def test_climb_after_a_job_without_compensation_off_is_unchanged(self):
        session = Session()
        session.step('line_5x', ['zpos'], zpos=5, feed_type='feed_cut')
        session.step('end_of_job')
        session.step('start_of_job')
        self.assertEqual(session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=50),
                         ['G0 Z50', 'X100 Y100'])

    def test_removing_trc_from_rapids_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = "['G'iMplane' '],['G'iDiametercomp' '],['G'iAbsincmode ' '],[cWo,iWorkoffset' '],['X'xpos ' '],['Y'ypos ' ']"
        self.assertEqual(source.count(anchor), 1, 'rapid block changed; review this test')
        broken = source.replace(anchor, "['G'iMplane' '],['G'iAbsincmode ' '],[cWo,iWorkoffset' '],['X'xpos ' '],['Y'ypos ' ']", 1)
        engine = engine_with_comp(41, broken)
        event(engine, 'compensation', side='off')
        self.assertEqual(event(engine, 'rapid_move', ['xpos', 'ypos'], xpos=30, ypos=40), ['G0 X30 Y40'])



def contour_with_compensation(program):
    """Approach, compensation left, plunge, two cuts, compensation off: the tool stands at X30 Y30 Z-2."""
    program.ev('move_5x', xpos=0, ypos=0, zpos=5)
    program.ev('compensation', side='left')
    program.ev('line_5x', zpos=-2, feed=200)
    program.ev('line_5x', xpos=30, feed=200)
    program.ev('line_5x', ypos=30, feed=200)
    program.ev('compensation', side='off')


class CompensationProgramTests(unittest.TestCase):
    """Whole programs: compensation off before a Z-only retract must reach the control before the
    post homes, indexes, changes the tool, drills or ends the program."""

    def program(self, **options):
        program = Program(options=options)
        program.start()
        contour_with_compensation(program)
        return program

    def test_retract_before_tool_change_cancels_compensation(self):
        program = self.program()
        self.assertEqual(program.ev('move_5x', zpos=50), ['G0 Z50', 'G40 X30 Y30'])
        program.ev('end_of_job')
        program.ev('change_tool', tool_number=2, next_tool_number=3, first_tool=False)
        change = program.ev('start_of_job', job_name='op2')
        self.assertLess(change.index('G75 Z1=0.'), change.index('T2'), change)

    def test_retract_before_program_end_cancels_compensation(self):
        program = self.program()
        self.assertEqual(program.ev('move_5x', zpos=50), ['G0 Z50', 'G40 X30 Y30'])
        program.ev('end_of_job')
        self.assertNotIn('G40', ' '.join(program.ev('end_program')))

    def test_retract_before_index_cancels_compensation(self):
        program = self.program()
        self.assertEqual(program.ev('move_5x', zpos=50), ['G0 Z50', 'G40 X30 Y30'])
        program.ev('end_of_job')
        program.ev('tmatrix', angle_4x_around_x=90)
        program.engine.state['btmatrixindexpending'] = True
        index = program.ev('start_of_job', job_name='op2')
        self.assertIn('G75 Z1=0.', index)
        self.assertNotIn('G40', ' '.join(index))

    def test_retract_before_a_drill_job_at_the_same_xy_cancels_compensation(self):
        program = self.program()
        self.assertEqual(program.ev('move_5x', zpos=10), ['G0 Z10', 'G40 X30 Y30'])
        program.ev('end_of_job')
        program.ev('start_of_job', job_name='drill')
        cycle = program.ev('drill', xpos=30, ypos=30, zpos=10, drill_type='g81', drill_clearance_z=10,
                           drill_upper_z=0, drill_lower_z=-15, feed=80)
        self.assertNotIn('G40', ' '.join(cycle))

    def test_next_pass_deselects_on_the_retract_and_selects_on_the_plunge(self):
        program = self.program()
        self.assertEqual(program.ev('move_5x', zpos=2), ['G0 Z2', 'G40 X30 Y30'])
        program.ev('compensation', side='left')
        self.assertEqual(program.ev('line_5x', zpos=-4, feed=200), ['G1 G41 Z-4'])

    def test_next_job_plunge_does_not_carry_a_late_g40(self):
        program = self.program()
        program.ev('move_5x', zpos=50)
        program.ev('end_of_job')
        program.ev('start_of_job', job_name='op2')
        program.ev('move_5x', zpos=2)
        self.assertEqual(program.ev('line_5x', zpos=-2, feed=200), ['G1 Z-2'])

    def test_compensation_on_a_z_approach_before_an_arc_does_not_stop_the_post(self):
        program = Program()
        program.start()
        program.ev('move_5x', xpos=10, ypos=0, zpos=5)
        program.ev('compensation', side='left')
        self.assertEqual(program.ev('move_5x', zpos=-1), ['G41 X10 Y0 Z-1'])
        arc = program.ev('arc', xpos=20, ypos=0, arc_plane='xy', arc_direction='ccw', arc_size=180, radius=5,
                         xstart=10, ystart=0, zstart=-1, xcenter=15, ycenter=0, zcenter=-1, xcenter_rel=5,
                         ycenter_rel=0, zcenter_rel=0, feed=200)
        self.assertEqual(arc, ['G3 X20 Y0 I5 J0 F200'])

    def test_compensation_on_the_first_feed_move_after_homing_is_selected_on_the_xy_return(self):
        program = Program()
        program.start()
        program.ev('move_5x', xpos=30, ypos=10, zpos=5)
        program.ev('line_5x', zpos=-2, feed=200)
        program.ev('move_5x', zpos=50)
        program.ev('end_of_job')
        program.ev('tmatrix', angle_4x_around_x=90)
        program.engine.state['btmatrixindexpending'] = True
        program.ev('start_of_job', job_name='op2')
        program.ev('compensation', side='left')
        self.assertEqual(program.ev('line_5x', xpos=40, ypos=15, zpos=-1, feed=200), ['G0 G41 X40 Y15', 'G1 Z-1'])

    def test_yz_job_z_rapid_keeps_compensation_on_the_z_block(self):
        # In G19 Z is an axis of the working plane: no X/Y are added.
        program = Program(cam=dict(machine_plane='yz'))
        program.start()
        program.ev('move_5x', xpos=0, ypos=0, zpos=5)
        program.ev('compensation', side='left')
        self.assertEqual(program.ev('move_5x', zpos=4), ['G41 Z4'])


def index_next_job(program, angle=90):
    program.ev('end_of_job')
    program.ev('tmatrix', angle_4x_around_x=angle)
    program.engine.state['btmatrixindexpending'] = True
    return program.ev('start_of_job', job_name='op2', angle_4x_around_x=angle)


def compensation_left_on(test, side='left', options=None, retract=50, off=True, policies=None):
    """A contour whose compensation off comes after the last retract (or never): G41/G42 is still on at
    the retract height (Z50 by default)."""
    program = Program(options=options, policies=policies)
    program.start()
    program.ev('move_5x', xpos=0, ypos=0, zpos=5)
    program.ev('compensation', side=side)
    program.ev('line_5x', zpos=-2, feed=200)
    program.ev('line_5x', xpos=30, feed=200)
    program.ev('line_5x', ypos=30, feed=200)
    test.assertEqual(program.ev('move_5x', zpos=retract), [f'G0 Z{retract}'])
    if off:
        program.ev('compensation', side='off')
    return program


class CompensationAtPostHomingTests(unittest.TestCase):
    """Compensation still on at the control when the post homes, indexes, stops, changes the tool or
    ends the program: no linear block deselected it. It is deselected at the end of the job when the
    tool stands at or above the clearance plane, else right after the Z homing, above the part and
    before the XY homing ('G0 G40' with the last X and Y: a plane axis, module oracle)."""

    @covers('PP-062')
    def test_compensation_left_on_at_the_job_end_is_deselected_at_the_clearance_height(self):
        """INDEPENDENT: module oracle; G40 before any G75, index, M1 or tool change of the next job."""
        for side in ('left', 'right'):
            with self.subTest(side=side):
                program = compensation_left_on(self, side)
                self.assertEqual(program.ev('end_of_job'), ['G0 G40 X30 Y30'])
                program.ev('tmatrix', angle_4x_around_x=90)
                program.engine.state['btmatrixindexpending'] = True
                index = program.ev('start_of_job', job_name='op2', angle_4x_around_x=90)
                self.assertEqual(index[:2], ['M1', 'G75 Z1=0.'])
                self.assertNotIn('G40', ' '.join(index))

    @covers('PP-062')
    def test_compensation_left_on_at_an_index_is_deselected_before_the_index(self):
        """INDEPENDENT: owner rule; G40 right after the Z homing: the XY homing and the A word run with
        compensation off (M1 and G75 Z still with it on)."""
        program = compensation_left_on(self)
        program.engine.state['tool_start_plane'] = 60     # Z50 is below the clearance plane
        index = index_next_job(program)
        self.assertEqual(index[:5], ['M1', 'G75 Z1=0.', 'G0 G40 X30 Y30', 'G75 Y1=0 X1=0', 'G0 G54 A=ACP(90)'])
        self.assertEqual(program.ev('move_5x', xpos=10, ypos=10, zpos=5), ['X10 Y10', 'Z5'])

    @covers('PP-062')
    def test_compensation_left_on_at_a_tool_change_is_deselected_after_the_z_homing(self):
        """INDEPENDENT: TRC must be off at a tool change; G40 after the Z homing, before the XY homing and M1."""
        program = compensation_left_on(self)
        program.engine.state['tool_start_plane'] = 60
        program.ev('end_of_job')
        program.ev('change_tool', tool_number=2, next_tool_number=3, first_tool=False)
        change = program.ev('start_of_job', job_name='op2')
        z = change.index('G75 Z1=0.')
        self.assertEqual(change[z:z + 3], ['G75 Z1=0.', 'G0 G40 X30 Y30', 'G75 Y1=0 X1=0'])
        self.assertLess(z, change.index('M1'))

    @covers('PP-062')
    def test_compensation_left_on_at_program_end_is_deselected_after_the_z_homing(self):
        """INDEPENDENT: module oracle; M30 runs with compensation off."""
        program = compensation_left_on(self)
        program.engine.state['tool_start_plane'] = 60
        program.ev('end_of_job')
        end = program.ev('end_program', last_tool=True)
        self.assertEqual(end[-4:], ['G75 Z1=0.', 'G0 G40 X30 Y30', 'G75 Y1=0 X1=0', 'M30'])

    @covers('PP-062')
    def test_compensation_left_on_at_an_index_without_homing_is_deselected_at_the_clearance_height(self):
        """INDEPENDENT: owner rule; index clearance modes 1 and 2 retract Z without G75: G40 after the
        clearance block, before A turns."""
        for mode in (1, 2):
            with self.subTest(i4xIndexClearanceMode=mode):
                program = compensation_left_on(self, options=dict(i4xIndexClearanceMode=mode), retract=20)
                self.assertEqual(program.ev('end_of_job'), [])
                index = index_next_job(program)
                self.assertEqual(index[:4], ['M1', 'G54 Z50', 'G0 G40 X30 Y30', 'G0 A=ACP(90)'])

    def test_deselection_inside_a_feed_emulated_rapid_keeps_its_g1(self):
        """INDEPENDENT: bSyncdrapid false posts a '3-d model' rapid as G1 F<nRapidfeed>; the G40 block
        after the Z homing does not turn the rest of it into G0."""
        program = compensation_left_on(self, options=dict(bSyncdrapid=False), retract=20)
        self.assertEqual(program.ev('end_of_job'), [])
        program.ev('start_of_job', job_name='op2', job_type='3-d model')
        self.assertEqual(program.ev('move_5x', xpos=5, ypos=5, zpos=10, apos=90),
                         ['G75 Z1=0.', 'G0 G40 X30 Y30', 'G75 Y1=0 X1=0', 'G1 A=ACP(90)', 'X5 Y5', 'Z10 F650'])

    def test_compensation_left_on_at_a_combined_z_and_xy_homing_stops_the_post(self):
        """INDEPENDENT: owner rule; a homing line with Z and X/Y leaves no slot for G40 between the Z and
        the XY homing (before it: low near the part, after it: the XY homing undone): stop."""
        require_nc_stream()
        homing = '8::G75 Z1=0. Y1=0 X1=0'
        program = compensation_left_on(self, options=dict(sHomestrtc=homing, sHomestrend=homing), retract=20,
                                       policies=scripted_input_policies())
        program.ev('end_of_job')
        with self.assertRaises(post_abort_error()):
            program.ev('end_program', last_tool=True)
        self.assertEqual(program.nc()[-1], 'POST ERROR: Cutter compensation is still on at a homing line that '
                                           'moves Z with X/Y. Home Z alone first.')

    def test_deselection_after_a_drill_job_uses_the_last_hole(self):
        """INDEPENDENT: module oracle; the G0 G40 block programs the last programmed X/Y (the last hole)."""
        program = compensation_left_on(self, off=False)
        program.ev('end_of_job')
        program.ev('start_of_job', job_name='drill')
        program.ev('drill', xpos=10, ypos=10, zpos=50, drill_type='g81', drill_clearance_z=50, drill_upper_z=0,
                   drill_lower_z=-15, feed=80)
        program.ev('drill_point', xpos=100, ypos=80, zpos=50)
        program.ev('end_drill')
        self.assertEqual(program.ev('end_of_job'), ['G0 G40 X100 Y80'])

    def test_compensation_on_across_a_rotating_rapid_is_deselected_and_selected_again(self):
        """INDEPENDENT: module oracle; G40 after the Z homing, CAM's G41 again on the XY return above the part."""
        program = Program()
        program.start()
        program.ev('move_5x', xpos=0, ypos=0, zpos=5)
        program.ev('compensation', side='left')
        program.ev('line_5x', zpos=-2, feed=200)
        program.ev('line_5x', xpos=30, feed=200)
        self.assertEqual(program.ev('move_5x', apos=90, zpos=20),
                         ['G75 Z1=0.', 'G0 G40 X30 Y0', 'G75 Y1=0 X1=0', 'G0 A=ACP(90)', 'G41 X30 Y0', 'Z20'])
        self.assertEqual(program.ev('line_5x', zpos=-2, feed=200), ['G1 Z-2'])

    def test_homing_without_compensation_has_no_deselection_block(self):
        """INDEPENDENT: module oracle; nothing to deselect, no extra block."""
        program = Program()
        self.assertEqual(program.ev('start_program'), ['G75 Z1=0.', 'G75 Y1=0 X1=0'])
        program = Program()
        program.start()
        contour_with_compensation(program)
        program.ev('move_5x', zpos=50)                    # deselected here: 'G0 Z50' / 'G40 X30 Y30'
        self.assertEqual(program.ev('end_of_job'), [])
        self.assertNotIn('G40', ' '.join(program.ev('end_program', last_tool=True)))

    def test_yz_job_deselection_programs_a_plane_axis(self):
        """INDEPENDENT: module oracle; in G19 Y is a plane axis of the G0 G40 block."""
        program = Program(cam=dict(machine_plane='yz'))
        program.start(machine_plane='yz')
        program.ev('move_5x', xpos=10, ypos=-7.5, zpos=5)
        program.ev('compensation', side='right')
        program.ev('line_5x', zpos=-2, feed=200)
        program.ev('line_5x', ypos=-20.25, feed=200)
        program.ev('move_5x', zpos=50)
        program.ev('compensation', side='off')
        index = index_next_job(program)
        self.assertEqual(index[1:3], ['G75 Z1=0.', 'G0 G40 X10 Y-20.25'])


YZ_ARC = dict(arc_plane='yz', arc_direction='ccw', arc_size=90, radius=10)


def yz_arc(program, end, start, center, **values):
    (y, z), (ys, zs), (yc, zc) = end, start, center
    return program.ev('arc_yz', ypos=y, zpos=z, ystart=ys, zstart=zs, ycenter=yc, zcenter=zc,
                      xcenter=program.engine.state['xpos'], xcenter_rel=0, ycenter_rel=yc - ys,
                      zcenter_rel=zc - zs, **YZ_ARC, **values)


def same_tool_second_job(plane, source=None, **options):
    """A first job in `plane` that ends at X10 Y10 Z-1 (or Z2 after a link), then start_of_job op2."""
    program = Program(options=options, source=source)
    program.start(machine_plane=plane)
    program.ev('move_5x', xpos=10, ypos=10, zpos=5)
    program.ev('line_5x', zpos=-1, feed=200)
    program.ev('end_of_job')
    program.ev('start_of_job', job_name='op2', machine_plane=plane)
    return program


def without(source, text, count=1):
    if source.count(text) != count:
        raise AssertionError(f'{text!r} changed; review this test')
    return source.replace(text, '')


class CompensationPlaneAxisTests(unittest.TestCase):
    """The TRC word lands on a G0/G1 block that programs an axis of the working plane in every
    rapid path: climb, first-move split, drill positioning, rapids without a plane axis."""

    def yz_climb(self, source=None):
        require_nc_stream()
        # Without the M1 between the jobs (bOptstpjob) the climb follows the MSG block directly.
        program = same_tool_second_job('yz', source, bOptstpjob=False)
        program.ev('compensation', side='left')
        program.ev('move_5x', xpos=10, ypos=10, zpos=40)
        yz_arc(program, (0, 30), (10, 40), (10, 30), feed=200)
        program.ev('line_5x', ypos=-5, feed=200)
        return program.nc()[-4:]

    def test_yz_job_climb_selects_compensation_on_a_y_block(self):
        # Before: 'G0 Z40' and G41 never printed; the arc and the line ran uncompensated.
        self.assertEqual(self.yz_climb(), ['G0 Z40', 'G41 Y10', 'G3 Y0 Z30 J0 K-10', 'G1 Y-5'])

    def test_zx_job_climb_selects_compensation_on_an_x_block(self):
        program = same_tool_second_job('zx')
        program.ev('compensation', side='left')
        self.assertEqual(program.ev('move_5x', zpos=40), ['G0 Z40', 'G41 X10'])

    def test_yz_first_move_split_selects_compensation_on_a_y_block(self):
        program = same_tool_second_job('yz')
        program.ev('compensation', side='left')
        # Below the last Z: no climb, the first move splits XY then Z. Before: a bare 'G41' block.
        self.assertEqual(program.ev('move_5x', zpos=-2), ['G0 G41 Y10', 'Z-2'])

    def test_yz_rapid_with_z_keeps_compensation_on_the_z_block(self):
        program = same_tool_second_job('yz')
        program.ev('move_5x', zpos=5)
        program.ev('compensation', side='left')
        self.assertEqual(program.ev('move_5x', xpos=12, zpos=4), ['G41 X12 Z4'])

    def test_yz_rapid_without_y_or_z_gets_y(self):
        program = same_tool_second_job('yz')
        program.ev('move_5x', zpos=5)
        program.ev('compensation', side='left')
        self.assertEqual(program.ev('move_5x', xpos=12), ['G41 X12 Y10'])

    def test_yz_drill_positioning_cancels_compensation_with_a_y_word(self):
        program = Program()
        program.start(machine_plane='yz')
        program.ev('move_5x', xpos=30, ypos=30, zpos=5)
        program.ev('compensation', side='left')
        program.ev('line_5x', zpos=-2, feed=200)
        program.ev('line_5x', ypos=40, feed=200)
        program.ev('move_5x', zpos=30)
        program.ev('compensation', side='off')
        program.ev('end_of_job')
        program.ev('start_of_job', job_name='drill', machine_plane='yz')
        cycle = program.ev('drill', xpos=30, ypos=40, zpos=10, drill_type='g81', drill_clearance_z=10,
                           drill_upper_z=0, drill_lower_z=-15, feed=80)
        self.assertEqual(cycle[:2], ['G40 Y40', 'Z10'])

    def test_removing_the_yz_plane_axis_is_detected(self):
        source = without(PP.read_text(encoding='utf-8-sig'),
                         '    if iMplane eq 19 and !change(ypos) and (!change(zpos) or bFirstMove)\n'
                         '        change(ypos) = true\n'
                         '    endif\n')
        self.assertEqual(self.yz_climb(source)[:2], ['MSG("op2")', 'G0 Z40'])

    def null_rapid_after_compensated_cut(self, source=None):
        require_nc_stream()
        program = Program(source=source)
        program.start()
        program.ev('move_5x', xpos=10, ypos=10, zpos=5)
        program.ev('line_5x', zpos=-1, feed=200)
        program.ev('compensation', side='left')
        program.ev('line_5x', xpos=40, feed=200)
        program.ev('compensation', side='off')
        program.ev('move_5x', xpos=40, ypos=10, zpos=-1)
        return program.nc()[-2:]

    def test_rapid_without_motion_switching_compensation_is_its_own_nc_line(self):
        # Before: 'G41 X40 G0 G40 X40 Y10' (X twice in one block, the cut joined with the rapid).
        self.assertEqual(self.null_rapid_after_compensated_cut(), ['G41 X40', 'G0 G40 X40 Y10'])

    def test_job_start_rapid_without_motion_is_not_joined_to_the_msg_line(self):
        require_nc_stream()
        # Without the M1 between the jobs (bOptstpjob) the rapid follows the MSG block directly.
        program = Program(options=dict(bOptstpjob=False))
        program.start()
        program.ev('move_5x', xpos=10, ypos=10, zpos=5)
        program.ev('line_5x', zpos=-1, feed=200)
        program.ev('compensation', side='left')
        program.ev('line_5x', xpos=40, feed=200)
        program.ev('line_5x', zpos=40, feed=200)        # below the clearance plane: end_of_job keeps G41
        program.ev('compensation', side='off')
        program.ev('end_of_job')
        program.ev('start_of_job', job_name='op2')
        program.ev('move_5x', xpos=40, ypos=10, zpos=40)
        self.assertEqual(program.nc()[-2:], ['MSG("op2")', 'G0 G40 X40 Y10'])

    def test_deselecting_rapid_that_does_not_climb_stays_one_block(self):
        program = Program()
        program.start()
        contour_with_compensation(program)
        self.assertEqual(program.ev('move_5x', xpos=40, zpos=-3), ['G0 G40 X40 Z-3'])

    def test_removing_the_retract_split_is_detected(self):
        source = without(PP.read_text(encoding='utf-8-sig'),
                         '        if change(iDiametercomp) and iDiametercomp eq 40 and iMplane eq 17\n'
                         '            bClimbFirst = true\n        endif\n')
        program = Program(source=source)
        program.start()
        contour_with_compensation(program)
        self.assertEqual(program.ev('move_5x', zpos=50), ['G0 G40 X30 Y30 Z50'])


if __name__ == '__main__':
    unittest.main()
