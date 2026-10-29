"""Arc endpoint tracking versus CAM-link authorization (f1803b4, tests/ARC_LINK_FINDING.md).

Area C, legacy file on the mid-job harness (motion_engine). XY-specific
complement of test_indexing_link.py::test_arc_revokes_and_tracks_endpoint
(an XY helix on a realistic session; YZ/ZX arcs stop the post).

Fixture tests/fixtures/arc_link_boundary.json: an XY helix raises the actual Z
from 10 to 30, then a straight feed_link descends to Z20, then a rotary rapid
follows. Oracle: geometry (a descent is not a retract) and the d5952a2 link
contract (only a confirmed straight upward retract authorizes a rotation
without G75). The event mixture is synthetic (X5_job=true); reachability in a
particular SolidCAM job is not established (ARC_LINK_FINDING.md).
"""
import json
import unittest

from support import index_of, last_index_of, mutate, parse_block, parse_blocks
from support.engines import adopt_state
from support.legacy import motion_engine
from support.paths import FIXTURES


class ArcLinkBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((FIXTURES / 'arc_link_boundary.json').read_text())

    def engine_for(self, source=None):
        engine = motion_engine()
        if source is not None:
            engine = adopt_state(engine, source)
        engine.set(xy='xy', zx='zx', yz='yz')
        return engine

    @staticmethod
    def step(engine, event):
        engine.set(**event['set'])
        for key in ('xpos', 'ypos', 'zpos', 'apos', 'bpos'):
            engine.changed[key] = False
        engine.changed.update({key: True for key in event['changed']})
        engine.output.clear()
        engine.call(event['call'])
        return ''.join(engine.output)

    def test_arc_updates_last_path_z(self):
        """INDEPENDENT: geometry: after the helix the tool is at its endpoint
        Z30, so the link tracking (nLastPathZ) must be 30, not the start Z10."""
        engine = self.engine_for()
        self.step(engine, self.fixture['arc'])
        self.assertEqual(engine.state['zpos'], 30)
        self.assertEqual(engine.state['nlastpathz'], self.fixture['expected_last_z_after_arc'])

    def check_descending_link_after_arc(self, source=None):
        engine = self.engine_for(source)
        self.step(engine, self.fixture['arc'])
        self.step(engine, self.fixture['link'])
        text = self.step(engine, self.fixture['rotation'])
        blocks = parse_blocks(text)
        rotation = index_of(blocks, lambda block: block.rotary('A') is not None)
        self.assertGreaterEqual(rotation, 0, f'no rotary output: {text!r}')
        self.assertEqual(blocks[rotation].rotary('A'), ('ACP', 10.0), text)
        required = parse_block(self.fixture['required_output_before_rotation']).homing_axes
        self.assertGreaterEqual(last_index_of(blocks, lambda block: required <= block.homing_axes, 0, rotation), 0,
                                f'Descending Z30->20 after the arc was mistaken for a retract from stale Z10: {text!r}')

    def test_descending_link_after_arc_does_not_bypass_homing(self):
        """INDEPENDENT: geometry and the d5952a2 link contract: the feed_link
        from the arc endpoint Z30 down to Z20 is a descent, so the following
        rotation to A10 must home Z first (G75 Z1=0. before A=ACP(10))."""
        self.check_descending_link_after_arc()

    def test_arc_invalidates_previous_link_and_tracks_workoffset(self):
        """INDEPENDENT: f1803b4: a completed arc starts a new link context, so a
        previous retract confirmation is revoked, and the work offset of the
        arc endpoint is recorded for the offset-equality guard. Structural: the
        confirmation and G55 are injected on the legacy harness."""
        engine = self.engine_for()
        engine.set(bCamLinkRetract=True, iWorkoffset=55)
        self.step(engine, self.fixture['arc'])
        self.assertFalse(engine.state['bcamlinkretract'])
        self.assertEqual(engine.state['nlastpathworkoffset'], 55)

    def test_arc_tracking_reversion_is_detected(self):
        """INDEPENDENT: negative validation: removing the f1803b4 endpoint
        tracking (nLastPathZ = zpos in @usr_arc) must fail the descending-link
        check with AssertionError."""
        broken = mutate('    bCamLinkRetract = false\n    nLastPathZ = zpos\n    nLastPathWorkoffset = iWorkoffset\n'
                        '    bClimbZValid = true\n    if bFeedoutput',
                        '    bCamLinkRetract = false\n    nLastPathWorkoffset = iWorkoffset\n'
                        '    bClimbZValid = true\n    if bFeedoutput')
        with self.assertRaisesRegex(AssertionError, 'mistaken for a retract'):
            self.check_descending_link_after_arc(broken)
