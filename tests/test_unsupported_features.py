"""Template features for other controls stop the post instead of writing code the 828D cannot run.

Oracle (INDEPENDENT): Sinumerik 828D (Siemens mode) has no Fanuc macro B (G65 P777, #-variables,
WHILE/END loops, G103), no M98/M99 subprogram calls, no G10 L2 data setting, and G112 is polar
programming, not a work offset. The SolidCAM GPP '!!open/copy/delete file!!' multiple-fixture scheme
was never verified on this machine (owner decision 2026-10-27: remove it; the WORKPIECE header buffer
of f004bdf uses the same directives for one balanced file and is not part of it). A post that meets such a
setting or event must stop with a POST ERROR (GPPL: input prompts, abort ends generation), not write
NC for another control. The same holds for SolidCAM motion events the post has no output for (4x
polar/Cartesian motion, 4x drill, 5x arcs): SolidCAM skips an event the post does not define (the
reference trace tests/fixtures/reference_multijob.trace.txt.xz has (0)@vmid_info and (0)@setup, which
have no procedure, and posting went on), so without a procedure the motion would be dropped silently.
"""
import re
import unittest

from program_session import Program, post_abort_error, require_nc_stream, scripted_input_policies
from support import Session, covers
from support.session import HEADER_DEFAULTS
from test_offline import PP

OPTION_STOP = 'POST ERROR: Multiple fixtures (more than one fixture in the job) are not supported by this post.'
INDEX_STOP = 'POST ERROR: i4xIndexMode must be 0 or 1.'
FEED_MODE_STOP = 'POST ERROR: i4xFeedMode must be 0 or 1.'
CLEARANCE_STOP = 'POST ERROR: i4xIndexClearanceMode must be 0, 1 or 2.'
EVENT_STOP = 'POST ERROR: SolidCAM subprograms, loops and reference point changes are not supported by this post.'
MOTION_STOP = 'POST ERROR: SolidCAM 4x polar/Cartesian, 4x drill and 5x face arc events are not supported by this post.'
MOTION_EVENTS = ('drill4x_pnt', 'drill4x_cartesian', 'drill4x_polar', 'move4x_polar', 'line4x_polar', 'arc_4x_polar',
                 'arc4x_polar', 'move4x_cartesian', 'line4x_cartesian', 'arc_4x_cartesian', 'arc4x_cartesian', 'arc_5x')


def stopped_with(test, program, event, **values):
    """Run one event that must stop the post; return the NC lines (with the POST ERROR line)."""
    with test.assertRaises(post_abort_error()):
        program.ev(event, **values)
    return program.nc()


def start_of_file(program):
    return program.ev('start_of_file', **HEADER_DEFAULTS)


class UnsupportedOptionTests(unittest.TestCase):
    def program(self, source=None, options=None, **cam):
        require_nc_stream()
        return Program(options=options, cam=cam, source=source, policies=scripted_input_policies())

    @covers('PP-033', 'PP-034', 'PP-035')
    def test_several_fixtures_stop_the_post(self):
        nc = stopped_with(self, self.program(iNumber_of_Fixtures=2), 'start_of_file', **HEADER_DEFAULTS)
        self.assertEqual(nc[-1], OPTION_STOP)
        self.assertFalse([line for line in nc if '!!' in line and '.workpiece.tmp' not in line], nc)

    def test_one_fixture_posts(self):
        for fixtures in (0, 1):
            with self.subTest(fixtures=fixtures):
                program = self.program(iNumber_of_Fixtures=fixtures)
                start_of_file(program)
                self.assertFalse([line for line in program.nc() if 'POST ERROR' in line
                                  or ('!!' in line and '.workpiece.tmp' not in line)])

    @covers('PP-038')
    def test_trig_macro_index_mode_stops_the_post(self):
        nc = stopped_with(self, self.program(options=dict(i4xIndexMode=2)), 'start_of_file', **HEADER_DEFAULTS)
        self.assertEqual(nc[-1], INDEX_STOP)

    def test_index_modes_0_and_1_post(self):
        for mode in (0, 1):
            with self.subTest(i4xIndexMode=mode):
                program = self.program(options=dict(i4xIndexMode=mode))
                start_of_file(program)
                self.assertFalse([line for line in program.nc() if 'POST ERROR' in line])

    def test_unknown_rotary_feed_mode_stops_the_post(self):
        # i4xFeedMode 2 was degrees per minute in the template; another value posted G94 silently.
        for mode in (2, -1):
            with self.subTest(i4xFeedMode=mode):
                program = self.program(options=dict(i4xFeedMode=mode))
                nc = stopped_with(self, program, 'start_of_file', **HEADER_DEFAULTS)
                self.assertEqual(nc[-1], FEED_MODE_STOP)

    def test_rotary_feed_modes_0_and_1_post(self):
        for mode in (0, 1):
            with self.subTest(i4xFeedMode=mode):
                program = self.program(options=dict(i4xFeedMode=mode))
                start_of_file(program)
                self.assertFalse([line for line in program.nc() if 'POST ERROR' in line])

    def test_unknown_index_clearance_mode_stops_the_post(self):
        # Another value used to skip the clearance move silently before the A index.
        for mode in (-1, 3):
            with self.subTest(i4xIndexClearanceMode=mode):
                program = self.program(options=dict(i4xIndexClearanceMode=mode))
                nc = stopped_with(self, program, 'start_of_file', **HEADER_DEFAULTS)
                self.assertEqual(nc[-1], CLEARANCE_STOP)

    def test_a_direction_other_than_minus_one_stops_the_post(self):
        # Owner rule 2026-10-28: only iR1dir -1 matches the recorded SolidCAM directions (PP-004).
        program = self.program(options=dict(iR1dir=1))
        nc = stopped_with(self, program, 'start_of_file', **HEADER_DEFAULTS)
        self.assertEqual(nc[-1], 'POST ERROR: iR1dir must be -1 (the A direction checked against SolidCAM).')

    def test_rot_axis_coord_2_stops_the_post(self):
        # Owner rule 2026-10-28: the template zeroed X for rot_axis_coord 2 (no known reason); stop instead.
        program = self.program(rot_axis_coord=2)
        with self.assertRaises(post_abort_error()):
            program.start()
        nc = program.nc()
        self.assertEqual(nc[-1], 'POST ERROR: rot_axis_coord 2 is not supported by this post.')
        self.assertFalse([line for line in nc if line.startswith(('G0', 'G1'))], nc)

    def test_index_clearance_modes_0_1_2_post(self):
        for mode in (0, 1, 2):
            with self.subTest(i4xIndexClearanceMode=mode):
                program = self.program(options=dict(i4xIndexClearanceMode=mode))
                start_of_file(program)
                self.assertFalse([line for line in program.nc() if 'POST ERROR' in line])

    def test_removing_the_fixture_check_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        check = re.compile(r'    if iNumber_of_Fixtures > 1\n(?:        .*\n)*?    endif\n')
        self.assertEqual(len(check.findall(source)), 1, 'fixture check changed; review this test')
        program = self.program(source=check.sub('', source, count=1), iNumber_of_Fixtures=2)
        start_of_file(program)
        self.assertNotIn(OPTION_STOP, program.nc())


class UnsupportedEventTests(unittest.TestCase):
    @covers('PP-044', 'PP-045', 'PP-057')
    def test_subprogram_loop_and_reference_point_events_stop_the_post(self):
        require_nc_stream()
        for event in ('call_proc', 'proc', 'end_proc', 'loop', 'end_loop', 'change_ref_point'):
            with self.subTest(event=event):
                program = Program(policies=scripted_input_policies())
                program.start()
                nc = stopped_with(self, program, event, label=1)
                self.assertEqual(nc[-1], EVENT_STOP)
                fanuc = [line for line in nc if re.search(r'\bM9[89]\b|\bG10\b|\bG65|WHILE|#', line)]
                self.assertEqual(fanuc, [], nc)

    def test_motion_events_the_post_cannot_output_stop_it(self):
        # support.session.Session runs the GPP text unchanged (Program rewrites Print), so the suite's
        # coverage record (tests_engine CoverageTests) counts these procedures.
        require_nc_stream()
        for event in MOTION_EVENTS:
            with self.subTest(event=event):
                session = Session(start=True, engine_options=dict(policies=scripted_input_policies()))
                session.ev('start_of_job', job_name='op1')
                engine = session.engine
                before = len(engine.output)
                with self.assertRaises(post_abort_error()):
                    session.ev(event, xpos=10, ypos=20, zpos=-5, apos=90, feed=500)
                blocks = [block.strip() for block in ''.join(engine.output[before:]).splitlines() if block.strip()]
                self.assertEqual(blocks, [MOTION_STOP])

    def test_template_switches_are_gone(self):
        # bSubs (subprogram output), the trig macro and the multiple-fixture files are not in the post.
        source = PP.read_text(encoding='utf-8-sig')
        for name in ('bSubs', 'usr_trig_macro', 'Multiple_Fixtures', 'TEMPFILE', 'G65P777', 'M98', 'M99'):
            with self.subTest(name=name):
                self.assertNotIn(name, source)


if __name__ == '__main__':
    unittest.main()
