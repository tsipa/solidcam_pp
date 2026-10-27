"""Motion-sequence regression tests on the legacy mid-job harness (area C, legacy file).

motion_engine is re-exported from support.legacy (single definition on the
cached parse), so `from test_motion import motion_engine` keeps working. It is
a mid-job harness that never runs @init_post: its hand-copied state
(iMotionmode=1, iWorkoffset=54, nPtool_* = 35, every change flag False) models
a program in the middle of a job, and its zpos_f='8.5' preset hides PP-006
(real output prints Z with 4 decimals after the first rapid; area D). New tests
use support.session.Session (tests/test_indexing_link.py).

All NC checks compare parsed words (support.nc), never substrings: 'X15' does
not match 'X150' and 'M1' does not match 'M10'.
"""
import json
import unittest

from support import covers, index_of, last_index_of, mutate, parse_block, parse_blocks
from support.engines import adopt_state
from support.legacy import motion_engine  # noqa: F401  (re-exported for other test modules)
from support.paths import FIXTURES

# The shit2 trace prints Z with 4 decimals (zpos_f '5.4' after the first
# rapid, PP-006) while the legacy harness prints 5 (zpos_f '8.5'): the largest
# rounding difference is 0.00005; 0.000001 more absorbs float representation.
TRACE_Z_DELTA = 0.000051


def word_key(word):
    return word.address, word.mode, word.kind


def word_spec(token):
    """One fixture token as a parsed NC word ('X15', 'A=DC(90)', 'Z1=0', bare 'A')."""
    words = parse_block(token).words
    if len(words) != 1:
        raise ValueError(f'fixture token {token!r} must be exactly one NC word')
    return words[0]


def word_matches(word, spec):
    """Exact word match; a bare address ('A', kind keyword) matches any word with it."""
    if word.address != spec.address:
        return False
    if spec.kind == 'keyword':
        return True
    return word_key(word) == word_key(spec) and word.value == spec.value


def block_matches(block, pattern):
    """Every word of the space-separated pattern occurs in this one block."""
    return all(any(word_matches(word, spec) for word in block.words) for spec in pattern)


def pattern_of(text):
    return [word_spec(token) for token in text.split()]


class MotionSequenceTests(unittest.TestCase):
    def assert_nc_blocks(self, text, expected):
        """Parsed comparison of emitted blocks with expected block texts.

        Same words in the same order; X/Y/Z values within TRACE_Z_DELTA (trace
        precision, see above), every other value exact.
        """
        actual, reference = parse_blocks(text), parse_blocks('\n'.join(expected))
        self.assertEqual(len(actual), len(reference), f'Unexpected NC blocks: {text!r}')
        for got, want in zip(actual, reference):
            self.assertEqual([word_key(word) for word in got.words], [word_key(word) for word in want.words],
                             f'Unexpected NC words: {got.raw!r} (expected {want.raw!r})')
            for word, model in zip(got.words, want.words):
                if model.address in ('X', 'Y', 'Z') and model.kind == 'word':
                    self.assertAlmostEqual(word.value, model.value, delta=TRACE_Z_DELTA, msg=got.raw)
                else:
                    self.assertEqual((word.value, word.args), (model.value, model.args), got.raw)

    def assert_actual_shit2_link(self, source=None):
        fixture = json.loads((FIXTURES / 'shit2_contiguous_link.json').read_text())
        engine = motion_engine()
        if source is not None:
            engine = adopt_state(engine, source)
        engine.set(**fixture['initial'])
        for step in fixture['steps']:
            engine.set(**step['set'])
            for key in ('xpos', 'ypos', 'zpos', 'apos', 'bpos', 'feed'):
                engine.changed[key] = False
            engine.changed.update({key: True for key in step['changed']})
            engine.output.clear()
            engine.call(step['call'])
            text = ''.join(engine.output)
            blocks = parse_blocks(text)
            self.assertEqual([block.raw for block in blocks if 75 in block.g], [],
                             f'Unexpected G75 homing before {step["a"]}: {text!r}')
            expected = [parse_block(step['a']).rotary('A')] if step['a'] else []
            self.assertEqual([block.rotary('A') for block in blocks if block.rotary('A')], expected, text)
            self.assert_nc_blocks(text, step['blocks'])

    @covers('DESIGN-004')
    def test_actual_shit2_contiguous_link(self):
        """INDEPENDENT (37ab3b9, CAM_LINK_POSTMORTEM.md) plus CHARACTERIZATION of DESIGN-004.

        Real numeric inputs of the second Slide trace: a straight feed_link
        retract followed by XYZ and four rotary rapids of one contiguous CAM
        link must never home (G75) and must emit every directed A position.
        The exact block lists also pin the current order inside confirmed
        links: the rotary block precedes the XYZ block even when Z rises in the
        same event (DESIGN-004; alternative: rise first, then rotate). Z values
        are compared within TRACE_Z_DELTA (4-decimal trace Z, PP-006).
        """
        self.assert_actual_shit2_link()

    def test_actual_shit2_detects_one_rotation_authorization_regression(self):
        """INDEPENDENT: negative validation of the shit2 check: restoring the
        one-rotation authorization of d5952a2 must fail on an unexpected G75."""
        broken = mutate('if bCamLinkRapid\n        bCamLinkRetract = true',
                        'if bCamLinkRapid and !bRapidRotaryChanged\n        bCamLinkRetract = true')
        with self.assertRaisesRegex(AssertionError, 'G75'):
            self.assert_actual_shit2_link(broken)

    def test_actual_shit2_rejects_extra_xyz_move(self):
        """INDEPENDENT: negative validation: an extra block inside the link must
        fail the exact block comparison."""
        broken = mutate('    if bCamLinkRapid\n        bCamLinkRetract = true',
                        "    if bCamLinkRapid\n        {nb,'G0 X999 Y999 Z-999'}\n        bCamLinkRetract = true")
        with self.assertRaisesRegex(AssertionError, 'Unexpected NC blocks'):
            self.assert_actual_shit2_link(broken)

    def check_step(self, text, step, state):
        """Fixture step expectations on parsed words (schema in motion_sequences.json)."""
        blocks = parse_blocks(text)
        if 'blocks' in step:
            self.assertEqual([[(word_key(word), word.value) for word in block.words] for block in blocks],
                             [[(word_key(word), word.value) for word in block.words]
                              for block in parse_blocks('\n'.join(step['blocks']))],
                             f'Unexpected NC blocks: {text!r}')
        for token in step.get('contains', []):
            self.assertGreaterEqual(index_of(blocks, lambda block: block_matches(block, pattern_of(token))), 0,
                                    f'{token!r} missing in {text!r}')
        for token in step.get('absent', []):
            self.assertEqual(last_index_of(blocks, lambda block: block_matches(block, pattern_of(token))), -1,
                             f'{token!r} unexpectedly present in {text!r}')
        position = 0
        for token in step.get('order', []):
            found = index_of(blocks, lambda block: block_matches(block, pattern_of(token)), position)
            self.assertGreaterEqual(found, 0, f'{token!r} missing/out of order in {text!r}')
            position = found + 1
        for key, expected in step.get('state', {}).items():
            self.assertEqual(state[key.lower()], expected, key)

    def test_recorded_synthetic_sequences(self):
        """INDEPENDENT: synthetic event sequences of motion_sequences.json, with
        expectations from the d5952a2/37ab3b9 link contract, c03e1b4/92e2b23
        index rules and ab853be (first A output DC). PP-001 symptoms (no X/Y
        re-programming after PP-inserted homing) are deliberately not asserted
        (see the 'note' fields). Scenarios noted 'Structural' use event orders
        SolidCAM likely does not produce (efc-11) to pin one state-machine rule
        in isolation."""
        fixture = json.loads((FIXTURES / 'motion_sequences.json').read_text())
        for scenario in fixture['scenarios']:
            with self.subTest(scenario=scenario['name']):
                engine = motion_engine()
                engine.set(**scenario.get('initial', {}))
                for ordinal, step in enumerate(scenario['steps']):
                    with self.subTest(step=ordinal, procedure=step['call']):
                        engine.set(**step.get('set', {}))
                        for key in ('xpos', 'ypos', 'zpos', 'apos', 'bpos'):
                            engine.changed[key] = False
                        engine.changed.update({key.lower(): True for key in step.get('changed', [])})
                        engine.output.clear()
                        engine.call(step['call'])
                        self.check_step(''.join(engine.output), step, engine.state)

    def test_index_clearance_modes_and_work_offsets(self):
        """INDEPENDENT: index option documentation (i4xIndexMode 0/1,
        i4xIndexClearanceMode 0/1/2) and 92e2b23 (M1 before the index).

        The nPtool_* presets (40/45) model a mid-program index after a job whose
        levels end_of_job recorded, which is legitimate and does not hide PP-015
        (the first index of a program, tests/test_indexing_link.py). Mode 0
        homes Z before A; modes 1/2 retract to the recorded tool Z level / start
        plane before A and approach the current level (35) after it; mode 1
        moves position 2 to G55.
        """
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
                    blocks = parse_blocks(text)
                    rotation = index_of(blocks, lambda block: block.rotary('A') == ('DC', 90))
                    self.assertGreaterEqual(rotation, 0, f'A=DC(90) missing: {text!r}')
                    self.assertGreaterEqual(index_of(blocks, lambda block: 1 in block.m, 0, rotation), 0,
                                            f'M1 missing before the index: {text!r}')
                    if clearance == 0:
                        home = last_index_of(blocks, lambda block: 'Z' in block.homing_axes, 0, rotation)
                        self.assertGreaterEqual(home, 0, f'no G75 Z before the index: {text!r}')
                    else:
                        retract = 40 if clearance == 1 else 45
                        self.assertGreaterEqual(
                            index_of(blocks, lambda block: block.axes.get('Z') == retract, 0, rotation), 0,
                            f'no Z{retract} retract before the index: {text!r}')
                        self.assertGreaterEqual(
                            index_of(blocks, lambda block: block.axes.get('Z') == 35, rotation + 1), 0,
                            f'no Z35 approach after the index: {text!r}')
                    self.assertEqual(engine.state['iworkoffset'], 55 if index_mode else 54)
