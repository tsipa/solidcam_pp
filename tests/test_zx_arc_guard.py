"""ZX (G18) arcs stop the post until the arc_direction convention is verified.

Oracle (INDEPENDENT): Sinumerik/DIN 66025 G3 in G18 turns Z->X viewed from +Y, while @usr_arc_math
turns X->Z for CCW; XY (G17) and YZ (G19) are consistent. Until SolidCAM's ZX convention is checked,
a ZX arc must not be posted silently.
"""
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from test_offline import PP

MESSAGE = r'POST ERROR: ZX \(G18\) arc direction is unverified'


def arc_engine(plane):
    engine = Engine.from_path(PP)
    engine.set(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz', iFeedMode=94, arc_direction='ccw', arc_plane=plane,
               arc_size=90, iArcmode=2, radius=10, bFeedoutput=False, iDiametercomp=40, cWo='G',
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

    def test_xy_arc_is_still_posted(self):
        engine = arc_engine('xy')
        engine.set(ypos=10)
        engine.call('arc')
        self.assertIn('G3', ''.join(engine.output))


if __name__ == '__main__':
    unittest.main()
