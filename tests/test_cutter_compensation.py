"""Cutter radius compensation (G40/G41/G42) is switched only on linear blocks.

Oracle (INDEPENDENT): on Sinumerik, TRC is selected/deselected in a G0/G1 block; selecting or
deselecting it on a G2/G3 block raises an alarm. A compensation change that SolidCAM sends before a
rapid must take effect on that rapid, not on the next cutting move. TRC must be off at a tool change.
"""
import re
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from test_history_regressions import history_engine
from test_offline import PP


def engine_with_comp(active, source=None):
    engine = history_engine(source)
    engine.set(iDiametercomp=active)
    engine.changed['idiametercomp'] = False
    return engine


def event(engine, call, changed=(), **values):
    engine.set(**values)
    for key in ('xpos', 'ypos', 'zpos', 'apos', 'bpos', 'feed'):
        engine.changed[key] = False
    engine.changed.update({key: True for key in changed})
    engine.output.clear()
    engine.call(call)
    return [block.strip() for block in ''.join(engine.output).splitlines() if block.strip()]


class CutterCompensationTests(unittest.TestCase):
    def test_compensation_off_before_retract_rapid_is_posted_on_the_rapid(self):
        engine = engine_with_comp(41)
        event(engine, 'compensation', side='off')
        self.assertEqual(event(engine, 'rapid_move', ['zpos'], zpos=50), ['G0 G40 Z50'])

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

    def test_compensation_change_on_an_arc_stops_the_post(self):
        engine = engine_with_comp(40)
        engine.set(xy='xy', zx='zx', yz='yz', arc_plane='xy', arc_direction='ccw', arc_size=90, iArcmode=2,
                   radius=10, xstart=10, ystart=0, zstart=0, xcenter=0, ycenter=0, zcenter=0,
                   xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)
        event(engine, 'compensation', side='left')
        with self.assertRaisesRegex(UnsupportedGPPL, 'Cutter compensation change on an arc'):
            event(engine, 'arc', ['xpos', 'ypos'], xpos=0, ypos=10)

    def test_arc_with_unchanged_compensation_has_no_trc_word(self):
        engine = engine_with_comp(41)
        engine.set(xy='xy', zx='zx', yz='yz', arc_plane='xy', arc_direction='ccw', arc_size=90, iArcmode=2,
                   radius=10, xstart=10, ystart=0, zstart=0, xcenter=0, ycenter=0, zcenter=0,
                   xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0)
        output = event(engine, 'arc', ['xpos', 'ypos'], xpos=0, ypos=10)
        self.assertTrue(any(re.match(r'G3\b', block) for block in output), output)
        self.assertFalse(re.search(r'\bG4[012]\b', ' '.join(output)), output)

    def test_removing_trc_from_rapids_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = "['G'iMplane' '],['G'iDiametercomp' '],['G'iAbsincmode ' '],[cWo,iWorkoffset' '],['X'xpos ' '],['Y'ypos ' ']"
        self.assertEqual(source.count(anchor), 1, 'rapid block changed; review this test')
        broken = source.replace(anchor, "['G'iMplane' '],['G'iAbsincmode ' '],[cWo,iWorkoffset' '],['X'xpos ' '],['Y'ypos ' ']", 1)
        engine = engine_with_comp(41, broken)
        event(engine, 'compensation', side='off')
        self.assertEqual(event(engine, 'rapid_move', ['zpos'], zpos=50), ['G0 Z50'])


if __name__ == '__main__':
    unittest.main()
