"""ZX (G18) arcs stop the post until the arc_direction convention is verified.

Oracle (INDEPENDENT): Sinumerik/DIN 66025 G3 in G18 turns Z->X viewed from +Y, while @usr_arc_math
turns X->Z for CCW; XY (G17) and YZ (G19) are consistent. Until SolidCAM's ZX convention is checked,
a ZX arc must not be posted silently.
"""
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from program_session import Program, post_abort_error, require_nc_stream, scripted_input_policies
from test_offline import PP

MESSAGE = r'POST ERROR: ZX arc direction is unverified'


def arc_engine(plane, source=None, policies=None):
    text = PP.read_text(encoding='utf-8-sig') if source is None else source
    engine = Engine(text) if policies is None else Engine(text, policies=policies)
    engine.set(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz', iFeedMode=94, arc_direction='ccw', arc_plane=plane,
               arc_size=90, iArcmode=2, radius=10, bFeedoutput=False, iDiametercomp=40, iCompActive=40, cWo='G',
               iWorkoffset=54, iAbsincmode=90, feed=100, mcode_f='2.0(p)', clear_change_after_gen=1,
               xstart=10, ystart=0, zstart=0, xcenter=0, ycenter=0, zcenter=0,
               xcenter_rel=-10, ycenter_rel=0, zcenter_rel=0, xpos=0, ypos=0, zpos=0, bCamLinkRetract=False)
    engine.changed.update({key: False for key in ('imotionmode', 'implane', 'idiametercomp', 'cwo',
                                                  'iworkoffset', 'iabsincmode', 'feed')})
    engine.changed.update(xpos=True, ypos=True, zpos=True)
    return engine


class ZxArcGuardTests(unittest.TestCase):
    def test_arc_zx_event_stops_the_post(self):
        engine = arc_engine('zx')
        engine.set(zpos=10)
        with self.assertRaisesRegex(UnsupportedGPPL, MESSAGE):
            engine.call('arc_zx')

    def test_generic_arc_event_in_zx_plane_stops_the_post(self):
        engine = arc_engine('zx')
        engine.set(zpos=-10)
        with self.assertRaisesRegex(UnsupportedGPPL, MESSAGE):
            engine.call('arc')

    def test_abort_stops_the_post_after_the_prompt(self):
        # With the prompt answered, the post must still stop: no G18 arc block after the error line.
        require_nc_stream()
        engine = arc_engine('zx', policies=scripted_input_policies())
        engine.set(zpos=10)
        with self.assertRaises(post_abort_error()):
            engine.call('arc_zx')
        self.assertTrue(engine.nc_lines()[-1].startswith('POST ERROR: ZX arc direction is unverified'))

    def test_removing_the_abort_is_detected(self):
        require_nc_stream()
        source = PP.read_text(encoding='utf-8-sig')
        anchor = '"POST ERROR: ZX arc direction is unverified in this post. Check usr_arc_math."}\n        abort\n'
        self.assertEqual(source.count(anchor), 1, 'ZX stop changed; review this test')
        engine = arc_engine('zx', source.replace(anchor, anchor.replace('        abort\n', ''), 1),
                            scripted_input_policies())
        engine.set(zpos=10)
        engine.call('arc_zx')
        self.assertTrue(any(line.startswith('G') for line in engine.nc_lines()))

    def test_error_text_is_its_own_nc_line_in_a_program(self):
        require_nc_stream()
        program = Program(policies=scripted_input_policies())
        program.start()
        program.ev('move_5x', xpos=10, ypos=0, zpos=5)
        program.ev('line_5x', zpos=0, feed=100)
        with self.assertRaises(post_abort_error()):
            program.ev('arc_zx', xpos=0, zpos=10, arc_plane='zx', arc_direction='ccw', arc_size=90, radius=10,
                       xstart=10, ystart=0, zstart=0, xcenter=0, ycenter=0, zcenter=0, xcenter_rel=-10,
                       ycenter_rel=0, zcenter_rel=0)
        nc = program.nc()
        self.assertTrue(nc[-1].startswith('POST ERROR: ZX arc direction is unverified'), nc[-2:])
        self.assertNotIn('POST ERROR', nc[-2])

    def test_xy_arc_is_still_posted(self):
        engine = arc_engine('xy')
        engine.set(ypos=10)
        engine.call('arc')
        self.assertIn('G3', ''.join(engine.output))


if __name__ == '__main__':
    unittest.main()
