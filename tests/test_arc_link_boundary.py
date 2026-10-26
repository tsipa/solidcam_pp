import json
import unittest

from test_motion import motion_engine
from test_offline import ROOT


class ArcLinkBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / 'tests/fixtures/arc_link_boundary.json').read_text())
        self.engine = motion_engine()
        self.engine.set(xy='xy', zx='zx', yz='yz')

    def step(self, event):
        self.engine.set(**event['set'])
        for key in ('xpos','ypos','zpos','apos','bpos'):
            self.engine.changed[key] = False
        self.engine.changed.update({key: True for key in event['changed']})
        self.engine.output.clear()
        self.engine.call(event['call'])
        return ''.join(self.engine.output)

    def test_arc_updates_last_path_z(self):
        self.step(self.fixture['arc'])
        self.assertEqual(self.engine.state['zpos'], 30)
        self.assertEqual(self.engine.state['nlastpathz'], self.fixture['expected_last_z_after_arc'])

    def test_descending_link_after_arc_does_not_bypass_homing(self):
        self.step(self.fixture['arc'])
        self.step(self.fixture['link'])
        text = self.step(self.fixture['rotation'])
        self.assertIn(self.fixture['required_output_before_rotation'], text,
                      'Descending Z30→20 after arc was mistaken for retract from stale Z10')
        self.assertIn('A=ACN(10)', text)

    def test_arc_invalidates_previous_link_and_tracks_workoffset(self):
        self.engine.set(bCamLinkRetract=True, iWorkoffset=55)
        self.step(self.fixture['arc'])
        self.assertFalse(self.engine.state['bcamlinkretract'])
        self.assertEqual(self.engine.state['nlastpathworkoffset'], 55)
