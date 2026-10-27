import json
import re
import unittest

from test_offline import ROOT, rotary_engine
from test_offline import PP
from pp_tests.engine import Engine


def motion_engine():
    engine = rotary_engine()
    engine.call('usr_ip_useroptions')
    engine.set(X5_job=True, bJobPositioned=True, bCamLinkRetract=False, bPostHomed=False, bClimbZValid=False,
               machine_plane='xy', xy='xy', zx='zx', yz='yz',
               iFeedMode=94, bFeedPrevValid=True, nFeedPrevX=12, nFeedPrevY=23, nFeedPrevZ=10,
               nFeedPrevA=0, nFeedPrevR1=0, nInvFeed_f='5.3',
               bIndexClearancePending=False, bTlchg=False, bFirstRapid=False,
               bFirstMove=False, bFirstMovetlch=False, bVertical=False,
               bFirstVert=False, bSkipxyrapid=False, bFeedoutput=False,
               nLastPathZ=10, nLastPathWorkoffset=54, iWorkoffset=54,
               iPworkoffset=54, iMplane=17, iAbsincmode=90, iDiametercomp=40, iCompActive=40,
               iMotionmode=1, xpos=12, ypos=23, zpos=10, feed=100,
               tool_start_plane=35, tool_z_level=35, nPtool_z_level=35,
               nPtool_start_plane=35, prev_command='@line_5x',
               feed_type='feed_cut', job_type='contour', bStopM00=False,
               iWorkOffset_Method=0, rotate_angle_x=0, rotate_angle_y=0,
               rotate_angle_z=0, shift_x=0, shift_y=0, shift_z=0, position=1,
               rot_axis_coord=0, bSubs=False, bPrintloop=False, transform_type=0,
               job_name='fixture_operation', iG187_P=2, nG187_E=0,
               iG187_P_gpp=2, nG187_E_gpp=0,
               bStopM00difftool=False, bTmatrixIndexPending=False,
               sHomestrrot=engine.state['shomestrroth'],
               mcode_f='2.0(p)', clear_change_after_gen=1,
               xpos_f='8.5', ypos_f='8.5', zpos_f='8.5')
    engine.changed.clear()
    engine.changed.update({key: False for key in engine.state})
    engine.changed.update({key: False for key in ('apos','bpos','nrapidfeed')})
    engine.output.clear()
    return engine


class MotionSequenceTests(unittest.TestCase):
    def assert_nc_blocks(self, text, expected):
        blocks = [block.split() for block in text.splitlines() if block.strip()]
        self.assertEqual(len(blocks), len(expected), f'Unexpected NC blocks: {text!r}')
        number = r'([+-]?(?:\d+(?:\.\d*)?|\.\d+))'
        word = re.compile(r'([A-Z](?:=(?:ACP|ACN|DC)\()?)' + number + r'(\)?)')
        for actual_words, expected_block in zip(blocks, expected):
            expected_words = expected_block.split()
            self.assertEqual(len(actual_words), len(expected_words), f'Unexpected NC words: {actual_words!r}')
            for actual_token, expected_token in zip(actual_words, expected_words):
                actual, reference = word.fullmatch(actual_token), word.fullmatch(expected_token)
                if actual is None or reference is None:
                    self.assertEqual(actual_token, expected_token)
                    continue
                self.assertEqual((actual[1], actual[3]), (reference[1], reference[3]))
                if reference[1] in ('X','Y','Z'):
                    # Trace Z uses four decimal places; harness retains five.
                    self.assertAlmostEqual(float(actual[2]), float(reference[2]), delta=0.000051)
                else:
                    self.assertEqual(float(actual[2]), float(reference[2]))

    def assert_actual_shit2_link(self, source=None):
        fixture = json.loads((ROOT / 'tests/fixtures/shit2_contiguous_link.json').read_text())
        engine = motion_engine()
        if source is not None:
            candidate = Engine(source)
            candidate.set(**engine.state)
            candidate.changed.update(engine.changed)
            engine = candidate
        engine.set(**fixture['initial'])
        for step in fixture['steps']:
            engine.set(**step['set'])
            for key in ('xpos','ypos','zpos','apos','bpos','feed'):
                engine.changed[key] = False
            engine.changed.update({key: True for key in step['changed']})
            engine.output.clear()
            engine.call(step['call'])
            text = ''.join(engine.output)
            self.assertNotIn('G75', text, f'Unexpected homing before {step["a"]}')
            if step['a']:
                self.assertIn(step['a'], text)
            else:
                self.assertNotIn('A=', text)
            self.assert_nc_blocks(text, step['blocks'])

    def test_actual_shit2_contiguous_link(self):
        self.assert_actual_shit2_link()

    def test_actual_shit2_detects_one_rotation_authorization_regression(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = 'if bCamLinkRapid\n        bCamLinkRetract = true'
        self.assertEqual(source.count(anchor), 1)
        broken = source.replace(anchor, 'if bCamLinkRapid and !bRapidRotaryChanged\n        bCamLinkRetract = true', 1)
        with self.assertRaisesRegex(AssertionError, 'G75'):
            self.assert_actual_shit2_link(broken)

    def test_actual_shit2_rejects_extra_xyz_move(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = '    if bCamLinkRapid\n        bCamLinkRetract = true'
        self.assertEqual(source.count(anchor), 1)
        broken = source.replace(anchor, "    if bCamLinkRapid\n        {nb,'G0 X999 Y999 Z-999'}\n        bCamLinkRetract = true", 1)
        with self.assertRaisesRegex(AssertionError, 'Unexpected NC blocks'):
            self.assert_actual_shit2_link(broken)

    def test_recorded_synthetic_sequences(self):
        fixture = json.loads((ROOT / 'tests/fixtures/motion_sequences.json').read_text())
        for scenario in fixture['scenarios']:
            with self.subTest(scenario=scenario['name']):
                engine = motion_engine()
                engine.set(**scenario.get('initial', {}))
                for ordinal, step in enumerate(scenario['steps']):
                    with self.subTest(step=ordinal, procedure=step['call']):
                        engine.set(**step.get('set', {}))
                        for key in ('xpos','ypos','zpos','apos','bpos'):
                            engine.changed[key] = False
                        engine.changed.update({key.lower(): True for key in step.get('changed', [])})
                        engine.output.clear()
                        engine.call(step['call'])
                        text = ''.join(engine.output)
                        if 'blocks' in step:
                            self.assertEqual([block.strip() for block in text.splitlines() if block.strip()], step['blocks'])
                        for token in step.get('contains', []):
                            self.assertIn(token, text)
                        for token in step.get('absent', []):
                            self.assertNotIn(token, text)
                        position = 0
                        for token in step.get('order', []):
                            found = text.find(token, position)
                            self.assertGreaterEqual(found, 0, f'{token!r} missing/out of order in {text!r}')
                            position = found + len(token)
                        for key, expected in step.get('state', {}).items():
                            self.assertEqual(engine.state[key.lower()], expected, key)

    def test_index_clearance_modes_and_work_offsets(self):
        for index_mode in (0, 1):
            for clearance in (0, 1, 2):
                with self.subTest(index_mode=index_mode, clearance=clearance):
                    engine = motion_engine()
                    engine.set(angle_4x_around_x=90, bR1forceOutput=True,
                               i4xIndexMode=index_mode, i4xIndexClearanceMode=clearance,
                               position=2, nPtool_z_level=40, nPtool_start_plane=45)
                    engine.changed.update(imotionmode=True, cwo=True, iworkoffset=True)
                    engine.call('usr_4x_index')
                    text = ''.join(engine.output)
                    self.assertIn('M1', text)
                    self.assertIn('A=DC(90)', text)
                    if clearance == 0:
                        self.assertLess(text.index('G75 Z1=0'), text.index('A=DC(90)'))
                    else:
                        retract = 'Z40' if clearance == 1 else 'Z45'
                        self.assertLess(text.index(retract), text.index('A=DC(90)'))
                        self.assertGreater(text.index('Z35'), text.index('A=DC(90)'))
                    self.assertEqual(engine.state['iworkoffset'], 55 if index_mode else 54)
