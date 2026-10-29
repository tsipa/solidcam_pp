"""YZ and ZX (G19/G18) arcs and machining planes stop the post: only the XY plane (G17) is posted.

Oracle (INDEPENDENT): the machine has SD42940 $SC_TOOL_LENGTH_CONST = 0
(siemens_sinumerik_828d/noname_vmc500_4x/backups/NOLOG.ard), so the plane selection sets the infeed
axis of the tool length compensation (PGsl 03/2013 section 8.2): a milling tool's length acts in Z
under G17 and moves to Y under G18 and to X under G19. On the machine run of 2026-10-28 'G19 G3 Y-10
Z55 AR=90' of ARTEST.MPF drove Z down by about the tool length. So a YZ or ZX arc (events arc_yz and
arc_zx, or arc with arc_plane yz/zx) and a YZ or ZX machining plane (machine_plane, read by the
@machine_plane event and at start_of_job) must stop the post with a POST ERROR on its own NC line,
with no G2/G3/G18/G19 block written; an XY arc posts, and an XY, empty or unknown machining plane
posts G17 (the empty/unknown fallback is the owner's 7aeae99 rule). ZX arcs stopped before for a
reason of their own (PP-003: the arc_direction convention of G18 is unverified); the YZ/ZX arc stop
keeps that guard.
"""
import re
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from program_session import Program, post_abort_error, require_nc_stream, post_error_policies
from support import assert_detected, covers, mutate, parse_block, parse_blocks, replay
from test_offline import PP

ARC_STOP = ('POST ERROR: YZ/ZX arc: G18/G19 would move the tool length compensation off Z (SD42940 = 0 on '
            'this machine). Only XY arcs are supported.')
PLANE_STOP = ('POST ERROR: YZ/ZX machining plane: G18/G19 would move the tool length compensation off Z '
              '(SD42940 = 0 on this machine). Only the XY plane is supported.')
ARC_ABORT = '{nb,"' + ARC_STOP + '"}\n    abort\n'
PLANE_ABORT = '{nb,"' + PLANE_STOP + '"}\n        abort\n'
NOT_STOPPED = 'PostAbort not raised'

# Quarter arcs about the origin, counterclockwise, radius 10. The YZ and ZX end points follow the
# post's own rotation of the start, so a post without the stop would write the arc block.
YZ = dict(arc_plane='yz', xstart=0, ystart=10, zstart=0, xpos=0, ypos=0, zpos=10,
          xcenter_rel=0, ycenter_rel=-10, zcenter_rel=0)
ZX = dict(arc_plane='zx', xstart=10, ystart=0, zstart=0, xpos=0, ypos=0, zpos=10,
          xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)
XY = dict(arc_plane='xy', xstart=10, ystart=0, zstart=0, xpos=0, ypos=10, zpos=0,
          xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)
ARC = dict(arc_direction='ccw', arc_size=90, radius=10, xcenter=0, ycenter=0, zcenter=0)
SIDE_ARCS = {'arc_yz': ('arc_yz', YZ), 'arc_zx': ('arc_zx', ZX), 'arc yz': ('arc', YZ), 'arc zx': ('arc', ZX)}


def arc_engine(plane, source=None, policies=None):
    text = PP.read_text(encoding='utf-8-sig') if source is None else source
    engine = Engine(text) if policies is None else Engine(text, policies=policies)
    engine.set(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz', iFeedMode=94, arc_direction='ccw', arc_plane=plane,
               arc_size=90, radius=10, bFeedoutput=False, iDiametercomp=40, iCompActive=40, cWo='G',
               iWorkoffset=54, iAbsincmode=90, feed=100, mcode_f='2.0(p)', clear_change_after_gen=1,
               xstart=10, ystart=0, zstart=0, xcenter=0, ycenter=0, zcenter=0,
               xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0, xpos=0, ypos=0, zpos=0, bCamLinkRetract=False,
               bCycle832Auto=False, iCycle832Want=0, nCycle832WantTol=0, iCycle832Mode=0, nCycle832Tol=0, trace_level=0,
               nArcAR_f='3.5')
    engine.changed.update({key: False for key in ('imotionmode', 'implane', 'idiametercomp', 'cwo',
                                                  'iworkoffset', 'iabsincmode', 'feed')})
    engine.changed.update(xpos=True, ypos=True, zpos=True)
    return engine


def cut_to_arc_start(arc, source=None, policies=None):
    """A program that has cut down to the start point of `arc`."""
    program = Program(source=source, policies=policies)
    program.start()
    program.ev('rapid_move', xpos=arc['xstart'], ypos=arc['ystart'], zpos=5)
    program.ev('line', zpos=arc['zstart'], feed=100)
    return program


def side_plane_blocks(nc):
    """NC lines that program a circle (G2/G3) or a YZ/ZX plane (G18/G19)."""
    return [line for line in nc if set(parse_block(line).g) & {2, 3, 18, 19}]


class SidePlaneArcStopTests(unittest.TestCase):
    def assert_arc_stop(self, event, arc, source=None):
        program = cut_to_arc_start(arc, source, post_error_policies())
        before = program.nc()
        with self.assertRaises(post_abort_error()):
            program.ev(event, **ARC, **arc)
        nc = program.nc()
        self.assertEqual(nc, before + [ARC_STOP])
        self.assertEqual(side_plane_blocks(nc), [])

    @covers('PP-003')
    def test_arc_zx_event_stops_the_post(self):
        """INDEPENDENT: module oracle; regression guard of PP-003: a ZX arc never reaches the NC program."""
        engine = arc_engine('zx')
        engine.set(xpos=0, zpos=10)
        with self.assertRaisesRegex(UnsupportedGPPL, re.escape(ARC_STOP)):
            engine.call('arc_zx')

    def test_yz_arcs_and_generic_side_plane_arcs_stop_the_post(self):
        """INDEPENDENT: module oracle; arc_yz, and arc with arc_plane yz or zx, stop with the arc message."""
        for label in ('arc_yz', 'arc yz', 'arc zx'):
            event, arc = SIDE_ARCS[label]
            with self.subTest(label):
                engine = arc_engine(arc['arc_plane'])
                engine.set(**arc)
                with self.assertRaisesRegex(UnsupportedGPPL, re.escape(ARC_STOP)):
                    engine.call(event)

    @covers('PP-021')
    def test_error_text_is_the_last_nc_line_and_no_arc_block_is_written(self):
        """INDEPENDENT: module oracle; with print + abort run as in SolidCAM (post_error_policies) the
        program up to the arc is unchanged, the error text is one more NC line of its own, and no
        G2/G3/G18/G19 block is written. Regression guard of PP-021: no arc leaves G18/G19 modal for
        the next job."""
        require_nc_stream()
        for label, (event, arc) in SIDE_ARCS.items():
            with self.subTest(label):
                self.assert_arc_stop(event, arc)

    def test_xy_arc_is_still_posted(self):
        """INDEPENDENT: module oracle; G17 keeps the length compensation in Z, so an XY arc posts:
        G3 to X0 Y10 with AR=90, in G17, without a POST ERROR."""
        engine = arc_engine('xy')
        engine.set(ypos=10)
        engine.call('arc')
        self.assertIn('G3', ''.join(engine.output))
        program = cut_to_arc_start(XY)
        blocks = program.ev('arc', **ARC, **XY)
        self.assertEqual(len(blocks), 1, blocks)
        arc = parse_block(blocks[0])
        self.assertIn(3, arc.g)
        self.assertEqual(arc.axes, {'X': 0, 'Y': 10})
        self.assertEqual(arc.get('AR'), 90)
        self.assertEqual(replay(''.join(program.engine.output))[-1][1].plane, 17)

    def test_removing_the_arc_abort_is_detected(self):
        """INDEPENDENT: self-check of test_error_text_is_the_last_nc_line_and_no_arc_block_is_written:
        without the abort of the arc stop every YZ/ZX arc event goes on past the error line: arc_yz and
        arc_zx return without a stop, and arc with a YZ/ZX arc_plane runs on into the XY arc math (whose
        end mismatch stop adds a line after the error)."""
        require_nc_stream()
        mutant = mutate(ARC_ABORT, ARC_ABORT.replace('    abort\n', ''))
        for label, (event, arc) in SIDE_ARCS.items():
            with self.subTest(label):
                assert_detected(self, lambda source: self.assert_arc_stop(event, arc, source), mutant,
                                f'arc stop without abort, {label}',
                                match=NOT_STOPPED if event != 'arc' else 'Lists differ')

    def test_error_text_without_a_block_of_its_own_is_detected(self):
        """INDEPENDENT: self-check of the own-line assertion of
        test_error_text_is_the_last_nc_line_and_no_arc_block_is_written: without nb (0ed0b78 reverted for
        this stop) the error text joins the last cut block."""
        require_nc_stream()
        mutant = mutate('{nb,"' + ARC_STOP, '{"' + ARC_STOP)
        for label, (event, arc) in SIDE_ARCS.items():
            with self.subTest(label):
                assert_detected(self, lambda source: self.assert_arc_stop(event, arc, source), mutant,
                                f'0ed0b78 reverted, {label}', match='Lists differ')


class SidePlaneMachiningPlaneStopTests(unittest.TestCase):
    def assert_start_of_job_stop(self, plane, x5_job, same_tool=False, source=None):
        program = Program(cam=dict(machine_plane='xy' if same_tool else plane, x5_job=x5_job), source=source,
                          policies=post_error_policies())
        if same_tool:
            program.start()
            program.ev('rapid_move', xpos=10, ypos=0, zpos=5)
            program.ev('line', zpos=0, feed=100)
            program.ev('end_of_job')
        else:
            program.ev('start_program')
            program.ev('change_tool', tool_number=1, next_tool_number=2)
        before = program.nc()
        with self.assertRaises(post_abort_error()):
            program.ev('start_of_job', job_name='op2' if same_tool else 'op1', machine_plane=plane)
        nc = program.nc()
        self.assertEqual(nc, before + [PLANE_STOP])
        self.assertEqual(side_plane_blocks(nc), [])

    def assert_event_stop(self, plane, after_cut, source=None):
        program = Program(source=source, policies=post_error_policies())
        if after_cut:
            program.start()
            program.ev('rapid_move', xpos=10, ypos=0, zpos=5)
            program.ev('line', zpos=0, feed=100)
        before = program.nc()
        with self.assertRaises(post_abort_error()):
            program.ev('machine_plane', machine_plane=plane)
        nc = program.nc()
        self.assertEqual(nc, before + [PLANE_STOP])
        self.assertEqual(side_plane_blocks(nc), [])

    def test_yz_and_zx_planes_stop_at_start_of_job(self):
        """INDEPENDENT: module oracle; start_of_job of a YZ or ZX job (simultaneous or not, after a tool
        change or with the same tool after an XY job) stops with the plane message on its own NC line,
        before any block of the job."""
        require_nc_stream()
        for plane in ('yz', 'zx'):
            for x5_job in (False, True):
                for same_tool in (False, True):
                    with self.subTest(machine_plane=plane, x5_job=x5_job, same_tool=same_tool):
                        self.assert_start_of_job_stop(plane, x5_job, same_tool)

    def test_yz_and_zx_planes_stop_at_the_machine_plane_event(self):
        """INDEPENDENT: module oracle; the @machine_plane event stops with the plane message, both where
        SolidCAM sends it (before @start_program, tests/fixtures/reference_multijob.trace.txt.xz) and
        after a cut."""
        require_nc_stream()
        for plane in ('yz', 'zx'):
            for after_cut in (False, True):
                with self.subTest(machine_plane=plane, after_cut=after_cut):
                    self.assert_event_stop(plane, after_cut)

    def test_xy_empty_and_unknown_planes_post_g17(self):
        """INDEPENDENT: module oracle for xy; '' and an unknown value fall back to G17 (owner's 7aeae99
        rule). The @machine_plane event and start_of_job post the job in G17 without a POST ERROR."""
        for plane in ('xy', '', 'unknown'):
            for x5_job in (False, True):
                with self.subTest(machine_plane=plane, x5_job=x5_job):
                    program = Program(cam=dict(machine_plane=plane, x5_job=x5_job))
                    blocks = program.ev('machine_plane', machine_plane=plane)
                    blocks += program.start()
                    blocks += program.ev('rapid_move', xpos=10, ypos=0, zpos=5)
                    blocks += program.ev('line', zpos=0, feed=100)
                    self.assertFalse([line for line in blocks if 'POST ERROR' in line], blocks)
                    parsed = parse_blocks('\n'.join(blocks))
                    planes = {code for block in parsed for code in block.g if code in (17, 18, 19)}
                    self.assertEqual(planes, {17}, blocks)
                    self.assertTrue([block for block in parsed if block.is_motion and 17 in block.g], blocks)

    def test_removing_the_plane_abort_is_detected(self):
        """INDEPENDENT: self-check of the two stop tests above: without the abort of usr_xy_plane_check a
        YZ or ZX plane goes on past the error line at start_of_job and at the @machine_plane event."""
        require_nc_stream()
        mutant = mutate(PLANE_ABORT, PLANE_ABORT.replace('        abort\n', ''))
        for plane in ('yz', 'zx'):
            for x5_job in (False, True):
                for same_tool in (False, True):
                    with self.subTest(event='start_of_job', machine_plane=plane, x5_job=x5_job,
                                      same_tool=same_tool):
                        assert_detected(
                            self, lambda source: self.assert_start_of_job_stop(plane, x5_job, same_tool, source),
                            mutant, f'plane stop without abort, start_of_job {plane}', match=NOT_STOPPED)
            for after_cut in (False, True):
                with self.subTest(event='machine_plane', machine_plane=plane, after_cut=after_cut):
                    assert_detected(self, lambda source: self.assert_event_stop(plane, after_cut, source),
                                    mutant, f'plane stop without abort, @machine_plane {plane}', match=NOT_STOPPED)

    def test_job_start_plane_check_reversions_are_detected(self):
        """INDEPENDENT: self-check of the same-tool case of test_yz_and_zx_planes_stop_at_start_of_job (a
        job after a tool change also reaches @machine_plane through usr_tc_init_gmstates): without the
        plane check of start_of_job (88695c9 reverted; it took the place of the job-plane restore), a
        same-tool YZ or ZX job starts without a stop."""
        require_nc_stream()
        mutants = {
            '88695c9 reverted': mutate('    call @usr_xy_plane_check\n    if bTmatrixIndexPending\n',
                                       '    if bTmatrixIndexPending\n'),
        }
        for label, mutant in mutants.items():
            for plane in ('yz', 'zx'):
                with self.subTest(label, machine_plane=plane):
                    assert_detected(self, lambda source: self.assert_start_of_job_stop(plane, False, True, source),
                                    mutant, f'{label}, same-tool {plane} job', match=NOT_STOPPED)

    def test_error_text_without_a_block_of_its_own_is_detected(self):
        """INDEPENDENT: self-check of the own-line assertion of the two stop tests above: without nb the
        error text joins the block before it (a homing block at start_of_job, a cut at the event)."""
        require_nc_stream()
        mutant = mutate('{nb,"' + PLANE_STOP, '{"' + PLANE_STOP)
        assert_detected(self, lambda source: self.assert_start_of_job_stop('yz', False, False, source), mutant,
                        'plane stop without nb, start_of_job', match='Lists differ')
        assert_detected(self, lambda source: self.assert_event_stop('zx', True, source), mutant,
                        'plane stop without nb, @machine_plane after a cut', match='Lists differ')


if __name__ == '__main__':
    unittest.main()
