import json
import re
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from test_offline import PP, ROOT


class ArcTests(unittest.TestCase):
    def test_ambiguous_arcs_all_planes_and_modes(self):
        fixture = json.loads((ROOT / 'tests/fixtures/ambiguous_arcs.json').read_text())
        for case in fixture['cases']:
            for plane, axes, plane_code in [('xy', ('x','y','z'), 17), ('zx', ('x','z','y'), 18), ('yz', ('y','z','x'), 19)]:
                for mode in (1, 2, 3, 4):
                    with self.subTest(case=case['name'], plane=plane, mode=mode):
                        engine = Engine.from_path(PP)
                        engine.set(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz',
                                   arc_direction=case['direction'], arc_plane=plane,
                                   arc_size=case['size'], iArcmode=mode, radius=10,
                                   bFeedoutput=False, iDiametercomp=40, cWo='G',
                                   iWorkoffset=54, iAbsincmode=90, feed=100,
                                   mcode_f='2.0(p)', clear_change_after_gen=1)
                        u, v, w = axes
                        delta = case.get('cad_delta', [0,0])
                        values = {u+'start': case['start'][0], v+'start': case['start'][1], w+'start': 2,
                                  u+'center': case['center'][0], v+'center': case['center'][1], w+'center': 2,
                                  u+'center_rel': case['center'][0]-case['start'][0],
                                  v+'center_rel': case['center'][1]-case['start'][1], w+'center_rel': 0,
                                  u+'pos': case['end'][0]+delta[0], v+'pos': case['end'][1]+delta[1], w+'pos': -7}
                        engine.set(**values)
                        engine.changed.update({key: True for key in ('imotionmode','implane','idiametercomp','cwo','iworkoffset','iabsincmode','xpos','ypos','zpos','feed')})
                        if 'error' in case:
                            with self.assertRaisesRegex(UnsupportedGPPL, case['error']):
                                engine.call({'xy':'arc','zx':'arc_zx','yz':'arc_yz'}[plane])
                            self.assertEqual(engine.output, [])
                            continue
                        engine.call({'xy':'arc','zx':'arc_zx','yz':'arc_yz'}[plane])
                        self.assertAlmostEqual(engine.state[u+'pos'], case['end'][0], places=8)
                        self.assertAlmostEqual(engine.state[v+'pos'], case['end'][1], places=8)
                        self.assertEqual(engine.state[w+'pos'], -7)  # helical orthogonal endpoint
                        self.assertEqual(engine.state['implane'], plane_code)
                        self.assertEqual(engine.state['imotionmode'], 3 if case['direction']=='ccw' else 2)
                        text = ''.join(engine.output)
                        self.assertEqual([int(g) for g in re.findall(r'\bG(\d+)', text)],
                                         [3 if case['direction']=='ccw' else 2, plane_code, 40, 54, 90])
                        positions = {key: float(value) for key,value in re.findall(r'\b([XYZF])([+-]?[\d.]+)', text)}
                        self.assertEqual(set(positions), {'X','Y','Z','F'})
                        for axis in ('x','y','z'):
                            self.assertAlmostEqual(positions[axis.upper()], engine.state[axis+'pos'], delta=0.00051)
                        self.assertEqual(positions['F'], 100)
                        words = {key: float(value) for key,value in re.findall(r'\b([IJKR])([+-]?[\d.]+)', text)}
                        if mode in (3,4) and case['r'] is not None:
                            self.assertEqual(words, {'R': case['r']})
                        else:
                            absolute = mode in (1,3)
                            expected = {dict(x='I',y='J',z='K')[axis]: case['center'][index] if absolute else case['center'][index]-case['start'][index]
                                        for index,axis in enumerate((u,v))}
                            self.assertEqual(words, expected)
                        self.assertTrue(engine.changed['nrapidfeed'])

    def test_exact_mismatch_tolerance_each_axis(self):
        fixture = json.loads((ROOT / 'tests/fixtures/ambiguous_arcs.json').read_text())
        for case in fixture['tolerance_cases']:
            for axis in range(3):
                with self.subTest(case=case, axis=axis):
                    engine = Engine.from_path(PP)
                    values = [0,0,0]
                    values[axis] = case['delta']
                    if case['abort']:
                        with self.assertRaisesRegex(UnsupportedGPPL, 'ARC end mismatch'):
                            engine.call('usr_arc_check', values)
                    else:
                        engine.call('usr_arc_check', values)
