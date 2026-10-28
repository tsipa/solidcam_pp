"""Coolant block: each M code at most once per call (usr_coolant_output / usr_coolant_code).

Every OFF code of the eight coolant channels is M9. usr_init_gmstates sets all eight channels OFF;
the change flags of those assignments reached the first operation (GPPL replay of the 2026-10-27
reference trace, under both the session and the best_guess policies: its coolant fields are
no_action, which assigns nothing), so it printed 'M9 M9 M9 M9 M9 M9 M9 M9'. usr_init_gmstates now
clears them, and the first tool change switches coolant off once like the others (bCooloffend).
Program() clears all flags after usr_init_gmstates, so these tests set them again.
"""
import re
import unittest

from program_session import ENGINE_HAS_NC_STREAM, Program
from support import assert_detected, mutate

CHANNELS = [f'icoolantm{k}' for k in range(1, 9)]


def coolant_block(p, values):
    """Set the channel values, flag them changed, run usr_coolant_output; return its M codes."""
    engine = p.engine
    for name, value in values.items():
        engine.state[name] = value
        engine.changed[name] = True
    start = len(engine.output)
    engine.call('usr_coolant_output')
    return re.findall(r'\bM\d+', ''.join(engine.output[start:]))


class CoolantCodeTests(unittest.TestCase):
    def check_once(self, source=None):
        p = Program(source=source)
        self.assertEqual(coolant_block(p, dict.fromkeys(CHANNELS, 9)), ['M9'])
        self.assertEqual(coolant_block(p, {'icoolantm1': 8, 'icoolantm4': 8}), ['M8'])

    def test_a_shared_code_is_printed_once(self):
        """INDEPENDENT: one M9 switches all coolant off; repeating it in one block adds nothing
        (and fills the block's M function slots). Flood and LP flood share M8 the same way."""
        self.check_once()

    def test_distinct_codes_keep_the_channel_order(self):
        """CHARACTERIZATION: different codes of one call stay, in channel order (flood, mist, ...)."""
        p = Program()
        self.assertEqual(coolant_block(p, {'icoolantm1': 8, 'icoolantm2': 7, 'icoolantm7': 50}), ['M8', 'M7', 'M50'])

    def test_each_call_starts_a_new_list(self):
        """INDEPENDENT: a code printed by the previous call is printed again when it changes again."""
        p = Program()
        self.assertEqual(coolant_block(p, {'icoolantm1': 8}), ['M8'])
        self.assertEqual(coolant_block(p, {'icoolantm1': 9}), ['M9'])
        self.assertEqual(coolant_block(p, {'icoolantm1': 8}), ['M8'])

    def first_job_codes(self, source=None, keep_equal_assignment_flags=False, options=None, **cam):
        """The M codes of the first job when the change flags of usr_init_gmstates reach it (SolidCAM
        keeps flags set by @init_post-time procedures; Program() clears them, so they are set again
        and usr_init_gmstates runs once more)."""
        policies = None
        if keep_equal_assignment_flags and ENGINE_HAS_NC_STREAM:
            from pp_tests.gppl.policies import Policies
            policies = Policies.from_env().with_(change_on_equal_assign='keep')
        p = Program(source=source, options=options, cam=cam, policies=policies)
        for name in CHANNELS:
            p.engine.changed[name] = True
        p.engine.call('usr_init_gmstates')
        return [code for block in p.start(tool=1, next_tool=2) for code in re.findall(r'\bM\d+', block)]

    def test_first_operation_prints_only_what_it_switches_on(self):
        """INDEPENDENT: reference trace 2026-10-27 (all coolant fields no_action): the first
        operation wrote M9 eight times; with flood on it wrote M8 and then M9 seven times, switching
        the flood off again. Now one M9 before M06, as at every tool change (bCooloffend: the control
        may still have coolant on from an earlier program), and after M06 only what the job
        switches on."""
        for flood, switched_on in ((0, []), (1, ['M8'])):
            with self.subTest(flood_coolant=flood):
                codes = self.first_job_codes(flood_coolant=flood)
                tool_change = codes.index('M06')
                self.assertEqual(codes[:tool_change], ['M9'], codes)
                self.assertEqual([code for code in codes[tool_change:] if code in ('M7', 'M8', 'M9')],
                                 switched_on, codes)
        self.assertNotIn('M9', self.first_job_codes(options=dict(bCooloffend=False), flood_coolant=1))

    def test_removing_the_init_flag_reset_is_detected(self):
        """INDEPENDENT: mutation self-check, under the rule that an equal assignment keeps the change
        flag (ENGINE-001 default; a rule that clears it hides the init flags without the reset), with
        bCooloffend false (the coolant off before the first M06 consumes the flags otherwise)."""
        def check(source):
            codes = self.first_job_codes(source, keep_equal_assignment_flags=True,
                                         options=dict(bCooloffend=False), flood_coolant=1)
            self.assertIn('M8', codes)
            self.assertNotIn('M9', codes)
        anchor = '    ; which switched the flood off again) unless SolidCAM clears a flag on an equal assignment.\n'
        resets = ''.join(f'    change(iCoolantM{k}) = false\n' for k in range(1, 9))
        assert_detected(self, check, mutate(anchor + resets, anchor), 'init flag reset removed')

    def test_removing_the_repeat_check_is_detected(self):
        """INDEPENDENT: mutation self-check."""
        mutant = mutate('    if !bRepeat\n', '    if true\n')
        assert_detected(self, self.check_once, mutant, 'repeat check removed')


if __name__ == '__main__':
    unittest.main()
