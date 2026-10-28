"""CYCLE84 thread hand follows the tap's spindle direction.

Oracle (INDEPENDENT): Siemens CYCLE84(RTP,RFP,SDIS,DP,DPR,DTB,SDAC,MPIT,PIT,POSS,SST,SST1,...).
The sign of PIT selects the thread hand (positive = right-hand as M3, negative = left-hand as M4);
SDAC is the spindle direction after the cycle (3 = M3, 4 = M4). The repo's Vericut control maps
PIT < 0 to a CCW spindle as well. A right-hand (CW) tap must keep the exact pre-fix output.
"""
import re
import unittest

from pp_tests.engine import Engine
from support import DRILL_TYPE
from test_history_regressions import history_engine
from test_offline import PP

FIELDS = ('RTP', 'RFP', 'SDIS', 'DP', 'DPR', 'DTB', 'SDAC', 'MPIT', 'PIT', 'POSS', 'SST', 'SST1',
          '_AXN', '_PTAB', '_TECHNO')
RIGHT_HAND_SUFFIX = ['0.', '3', '', '1.25', '0', '500', '1000', '', '', '1221']
LEFT_HAND_SUFFIX = ['0.', '4', '', '-1.25', '0', '500', '1000', '', '', '1221']
PREFIX_BY_UPPER = {12: ['30', '10', '2', '-15', ''], -2: ['30', '-2', '', '-15', '0.']}


def cycle84_arguments(source=None, **state):
    engine = history_engine()
    if source is not None:
        candidate = Engine(source)
        candidate.set(**engine.state)
        candidate.changed.update(engine.changed)
        engine = candidate
    engine.set(drill_type=DRILL_TYPE['G84'], drill_upper_z=12, spin=500, feed=625, Step_Down=0, VarRetract=0,
               integer_def_f='5.0', feed_f='4.4(P)')
    engine.set(**state)
    engine.output.clear()
    engine.call('drill')
    text = ''.join(engine.output)
    calls = re.findall(r'MCALL CYCLE84\s*\(([^)]*)\)', text)
    if len(calls) != 1:
        raise AssertionError(f'expected exactly one MCALL CYCLE84, got {text!r}')
    # The offline engine lexes the PP's `',0,'''` idiom as an escaped quote and leaves one
    # apostrophe before SST (engine literal-quoting artifact, not PP output).
    return calls[0].replace("'", '').split(',')


class TappingDirectionTests(unittest.TestCase):
    def assert_tap(self, direction, expected_suffix, source=None):
        for upper, prefix in PREFIX_BY_UPPER.items():
            arguments = cycle84_arguments(source, tool_direction=direction, drill_upper_z=upper)
            self.assertEqual(arguments, prefix + expected_suffix, f'{direction} tap, drill_upper_z={upper}')

    def test_right_hand_tap_keeps_exact_cycle84_arguments(self):
        self.assert_tap('cw', RIGHT_HAND_SUFFIX)

    def test_left_hand_tap_uses_negative_pitch_and_m4_after_cycle(self):
        self.assert_tap('ccw', LEFT_HAND_SUFFIX)
        fields = dict(zip(FIELDS, cycle84_arguments(tool_direction='ccw')))
        self.assertLess(float(fields['PIT']), 0)
        self.assertEqual(fields['SDAC'], '4')

    def test_depth_step_parameters_are_independent_of_thread_hand(self):
        for direction, sdac, pit in (('cw', '3', '1.25'), ('ccw', '4', '-1.25')):
            arguments = cycle84_arguments(tool_direction=direction, Step_Down=3, VarRetract=1.5)
            self.assertEqual(arguments[-3:], ['1', '3', '1.5'], direction)
            self.assertEqual((arguments[6], arguments[8]), (sdac, pit), direction)

    def test_direction_other_than_cw_taps_left_hand_like_the_spindle_m4(self):
        # @start_tool posts M4 for any tool_direction that is not CW; the tap follows the same rule.
        fields = dict(zip(FIELDS, cycle84_arguments(tool_direction='unknown')))
        self.assertEqual((fields['SDAC'], fields['PIT']), ('4', '-1.25'))

    def test_reverting_the_left_hand_branch_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        branch = re.compile(r'(if drill_type eq G84 then[^\n]*\n(?:\s*;[^\n]*\n)*\s*)if tool_direction eq CW then')
        self.assertEqual(len(branch.findall(source)), 1, 'left-hand CYCLE84 branch changed; review this test')
        reverted = branch.sub(r'\1if true then', source, count=1)
        self.assert_tap('ccw', RIGHT_HAND_SUFFIX, reverted)  # reverted PP posts a right-hand cycle
        with self.assertRaises(AssertionError):
            self.assert_tap('ccw', LEFT_HAND_SUFFIX, reverted)


if __name__ == '__main__':
    unittest.main()
