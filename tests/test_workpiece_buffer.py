"""INDEPENDENT: WORKPIECE clamping follows emitted nonzero A, including later
operations, while its BOX dimensions and position before machining are preserved.
Trace oracles supplied on 2026-10-27: Slide/12_slide_hold (A90),
Slide/17v2_finish_4ax (A0..359.39), platev2/iRough_iFinish_faces (A0 only).
File routing is modeled in memory; native SolidCAM execution remains a separate
integration check.
"""
import unittest

from pp_tests.file_commands import assemble_files
from support import Session, assert_detected, mutate, parse_blocks
from test_session_program import NO_TOOL_MESSAGES, SIMPLE_TOOLS, workpiece_blocks


STOCK = dict(stock_z_plus=19.5, stock_z_minus=-19.5, target_z_minus=-13,
             stock_x_minus=0, stock_y_minus=-19.5, stock_x=270, stock_y=39)


def begin(source=None):
    session = Session(source=source, header=True, fourth_axis_used=False, **STOCK)
    session.ev('def_tool', **NO_TOOL_MESSAGES, **SIMPLE_TOOLS[0], next_command='@start_program')
    session.ev('start_program')
    return session


def move(session, angle):
    session.ev('move_5x', ('xpos', 'ypos', 'zpos', 'apos'),
               xpos=10, ypos=0, zpos=35, apos=angle, dir5a='ccw')


def finish(session):
    session.ev('end_program', last_tool=True)
    session.ev('end_of_file')
    return assemble_files(session.text())


class WorkpieceBufferTests(unittest.TestCase):
    def assert_case(self, angles, reference, source=None):
        session = begin(source)
        self.assertNotIn('WORKPIECE(', session.text())
        for angle in angles:
            move(session, angle)
        text = finish(session)
        blocks = parse_blocks(text)
        pieces = workpiece_blocks(blocks)
        self.assertEqual(len(pieces), 1, text)
        self.assertEqual(pieces[0].words[0].args,
                         ('', reference, '', '"BOX"', '0', '19.5', '-39', '-32.5', '0', '-19.5', '270', '39'))
        stock_index = blocks.index(pieces[0])
        first_motion = next(i for i, block in enumerate(blocks) if block.axes or block.rotary('A'))
        self.assertLess(stock_index, first_motion, text)
        self.assertNotIn('!!', text)
        self.assertEqual(blocks[-1].m, [30], text)
        return session, text

    def test_three_recorded_program_cases(self):
        """INDEPENDENT: A-angle sequences from the three user-supplied traces."""
        for name, angles, ref in (('12_slide_hold', [90], '"A"'),
                                  ('17v2_finish_4ax', [0, 10, 359.39], '"A"'),
                                  ('iRough_iFinish_faces', [0], '')):
            with self.subTest(trace=name):
                self.assert_case(angles, ref)

    def test_late_rotation_and_return_to_zero_keep_a_clamping(self):
        """INDEPENDENT: a later nonzero A remains evidence after a return to A0."""
        self.assert_case([0, 0, 90, 0], '"A"')
        self.assert_case([0, 90, -90, 0], '"A"')

    def test_rotation_below_output_resolution_does_not_attach_to_a(self):
        """INDEPENDENT: an angle rounded to zero at 0.001 degrees is A0."""
        self.assert_case([0, 0.0004], '')
        self.assert_case([0, 0.0006], '"A"')

    def test_stock_snapshot_survives_later_cam_and_format_changes(self):
        """INDEPENDENT: header geometry belongs to the initial MAC and stock."""
        session = begin()
        move(session, 90)
        session.engine.set(**{name: 999 for name in STOCK}, xpos_f='5.0(p)')
        text = finish(session)
        self.assertIn('WORKPIECE(,"A",,"BOX",0,19.5,-39,-32.5,0,-19.5,270,39)', text)

    def test_clamping_flag_resets_between_files(self):
        """INDEPENDENT: a rotation in one output file must not affect the next."""
        session, _ = self.assert_case([90], '"A"')
        session.ev('start_of_file', full_g_file_name='C:\\cam\\next file.mpf')
        self.assertFalse(session.engine.state['bworkpieceusesa'])
        self.assertFalse(session.engine.state['bworkpiecebuffered'])

    def test_clamping_tracker_and_flush_regressions_are_detected(self):
        """INDEPENDENT: dropping the tracker or A reference must fail the oracle."""
        check = lambda source: self.assert_case([0, 90, 0], '"A"', source)
        for old, new in (
                ('        bWorkpieceUsesA = true\n', ''),
                ('    if abs(nR1pos) >= 0.0005\n', '    if false\n'),
                ("        {nl, 'WORKPIECE(,\"A\",' sWorkpieceArgs}",
                 "        {nl, 'WORKPIECE(,,' sWorkpieceArgs}")):
            with self.subTest(mutation=old):
                assert_detected(self, check, mutate(old, new))

    def test_file_directive_model_preserves_order_and_cleans_up(self):
        """INDEPENDENT: open diverts output; copy inserts it at the current point."""
        text = ('HEADER\n!!open file=body with spaces.tmp!!\nG0 A90\nM30\n'
                '!!close file=body with spaces.tmp!!\nWORKPIECE\n'
                '!!copy file=body with spaces.tmp!!\n!!delete file=body with spaces.tmp!!\n')
        self.assertEqual(assemble_files(text), 'HEADER\nWORKPIECE\nG0 A90\nM30\n')
        with self.assertRaises(KeyError):
            assemble_files('!!copy file=missing!!\n')
        with self.assertRaisesRegex(AssertionError, 'unclosed'):
            assemble_files('!!open file=unfinished!!\nM30\n')
