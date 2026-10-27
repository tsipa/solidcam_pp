"""Cutter radius compensation (G40/G41/G42) is switched only on linear blocks.

Oracle (INDEPENDENT): Sinumerik Programming Manual Fundamentals, TRC (G40, G41, G42): in the block with
G40/G41/G42, G0 or G1 must be active and at least one axis of the working plane must be programmed;
selecting or deselecting it on a G2/G3 block raises an alarm. A rapid that moves X or Y carries a
pending change; a Z-only rapid leaves it for the next block with a plane axis. TRC must be off at a tool
change, and the post's TRC state must match what the control has.
"""
import re
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from test_history_regressions import history_engine
from test_offline import PP
from test_post_homing_reposition import Session


def engine_with_comp(active, source=None):
    engine = history_engine(source)
    engine.set(iDiametercomp=active, iCompActive=active)
    engine.changed['idiametercomp'] = False
    return engine


ARC = dict(xy='xy', zx='zx', yz='yz', arc_plane='xy', arc_direction='ccw', arc_size=90, iArcmode=2,
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
    def test_compensation_off_before_retract_waits_for_the_next_xy_rapid(self):
        engine = engine_with_comp(41)
        event(engine, 'compensation', side='off')
        self.assertEqual(event(engine, 'rapid_move', ['zpos'], zpos=50), ['G0 Z50'])
        self.assertEqual(event(engine, 'rapid_move', ['xpos', 'ypos'], xpos=30, ypos=40), ['G40 X30 Y40'])

    def test_compensation_on_before_z_approach_keeps_the_plunge_form(self):
        # Z-only rapid: no TRC word; the G1 plunge carries it as before the fix.
        engine = engine_with_comp(40)
        event(engine, 'compensation', side='left')
        self.assertEqual(event(engine, 'rapid_move', ['zpos'], zpos=5), ['G0 Z5'])
        self.assertEqual(event(engine, 'line', ['zpos'], zpos=-1), ['G1 G41 Z-1'])

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
                           bWorkoffsettc=True, iWorkOffsetmode=2, home_user_name='P54')
        session.step('line_5x', ['xpos'], xpos=20, feed_type='feed_cut')
        session.step('end_of_job')
        session.engine.set(home_user_name='P55')
        self.assertIn('G55', ' '.join(session.step('start_of_job')))
        output = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=100, ypos=100, zpos=50)
        self.assertIn('G40', ' '.join(output), output)

    def test_removing_trc_from_rapids_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = "['G'iMplane' '],['G'iDiametercomp' '],['G'iAbsincmode ' '],[cWo,iWorkoffset' '],['X'xpos ' '],['Y'ypos ' ']"
        self.assertEqual(source.count(anchor), 1, 'rapid block changed; review this test')
        broken = source.replace(anchor, "['G'iMplane' '],['G'iAbsincmode ' '],[cWo,iWorkoffset' '],['X'xpos ' '],['Y'ypos ' ']", 1)
        engine = engine_with_comp(41, broken)
        event(engine, 'compensation', side='off')
        self.assertEqual(event(engine, 'rapid_move', ['xpos', 'ypos'], xpos=30, ypos=40), ['G0 X30 Y40'])


if __name__ == '__main__':
    unittest.main()
