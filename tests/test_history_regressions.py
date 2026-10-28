"""Independent oracles for bugs documented by reviewed GPP commits.

Every test docstring names its oracle (checked by tests/test_known_defect_registry.py).
The cases in tests/fixtures/history_regressions.json run on the legacy mid-job harness
history_engine (support.legacy, re-exported here for older importers). Every
check compares parsed NC blocks or words (support.nc), never substrings.

Fixture rules
  * expected values are explicit and independent of the interpreter;
  * a cycle parameter written as {"unpinned": "<reason>"} is deliberately not
    pinned; the reason must name a registered id (e.g. PP-055). The note sits
    inside expected_parameters, so the case keys stay those of the fixture schema
    that tests/test_gpp_static.py checks;
  * cycle cases pass tool_direction and spin (CAM inputs SolidCAM supplies with
    every drilling job), so a PP-028/PP-029 fix that reads them anywhere in @drill
    cannot turn a case into an UnsupportedGPPL error;
  * no case pins a registered defect: CYCLE84 (stray apostrophe ENGINE-004,
    positive PIT for CCW taps PP-028) is covered in tests/test_cycles_spindle.py,
    and CYCLE86 SDIR 3 is pinned for a CW tool only (PP-029 is the CCW case);
  * a "regression" patch reverses focused lines of the real commit diff in
    memory. support.mutation.mutate requires the anchor to occur exactly
    "count" times (default 1), so a rewritten GPP raises StaleAnchor instead of
    turning the reversion into a no-op.
"""
import json
import re
import unittest

from support import ENGINE_NAME, FIXTURES, REGISTRY, block_texts, mutate, parse_blocks, replay, state_before
from support.legacy import history_engine  # also re-exported for older importers

FIXTURE = FIXTURES / 'history_regressions.json'
TRC_CODES = (40, 41, 42)
DIRECTED_MODES = ('ACP', 'ACN', 'DC')
REGISTRY_ID = re.compile(r'(?:PP|ENGINE)-\d{3}')


class HistoryRegressionTests(unittest.TestCase):
    def load_cases(self):
        """Fixture cases; every unpinned cycle parameter must name a registered id.

        Validation runs before any reversion, so a malformed fixture can never be
        counted as a detected regression.
        """
        data = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.assertEqual(data['schema'], 1)
        for case in data['cases']:
            for index, value in enumerate(case.get('expected_parameters', ())):
                if isinstance(value, str):
                    continue
                note = value.get('unpinned', '') if isinstance(value, dict) else ''
                ids = REGISTRY_ID.findall(note)
                self.assertTrue(ids and all(i in REGISTRY for i in ids) and set(value) == {'unpinned'},
                                f'{case["name"]} parameter {index}: neither a string nor an unpinned note '
                                f'naming a registered id: {value!r}')
        return data['cases']

    def assert_fixture(self, case, source=None):
        engine = history_engine(source)
        engine.set(**case['initial'])
        kind = case['kind']
        if kind == 'compensation':
            engine.changed['idiametercomp'] = True
            codes = []
            for side in (None, 'comp_right', 'comp_off'):
                engine.output.clear()
                if side:
                    engine.set(side=side)
                    engine.call('compensation')
                engine.call('line_5x')
                blocks = parse_blocks(''.join(engine.output))
                codes.append([code for block in blocks for code in block.g if code in TRC_CODES])
            self.assertEqual(codes, case['expected_codes'])
        elif kind == 'fourth_axis':
            engine.call('fourth_axis')
            self.assertEqual(engine.state['nr1pos'], case['expected_a'])
            self.assertEqual(engine.state['apos'], case['expected_apos'])
            rotary = [block.rotary('A') for block in parse_blocks(''.join(engine.output)) if block.rotary('A')]
            self.assertEqual(len(rotary), 1, rotary)
            mode, value = rotary[0]
            self.assertIn(mode, DIRECTED_MODES, rotary)
            self.assertEqual(value, case['expected_a'])
        elif kind == 'axis_mapping':
            engine.call('usr_r1pos_calc')
            self.assertEqual(engine.state['nr1pos'], case['expected_a'])
            self.assertEqual(engine.state['nr2pos'], case['expected_secondary'])
        elif kind == 'tool_change':
            engine.call('usr_ct_toolchange')
            self.assertEqual(block_texts(''.join(engine.output)), case['expected_blocks'])
        elif kind == 'cycle':
            feed = engine.state['feed']
            engine.call('drill')
            replayed = replay(''.join(engine.output))
            calls = [index for index, (block, _) in enumerate(replayed) if block.has('MCALL')]
            self.assertEqual(len(calls), 1, [block.raw for block, _ in replayed])
            call = replayed[calls[0]][0].cycle
            self.assertIsNotNone(call, f'MCALL without arguments: {replayed[calls[0]][0].raw!r}')
            name, arguments = call
            self.assertEqual(name, f'CYCLE{case["expected_cycle"]}')
            expected = case['expected_parameters']
            self.assertEqual(len(arguments), len(expected), arguments)
            # {"unpinned": ...} entries are validated in load_cases and skipped here.
            pinned = [(index, value) for index, value in enumerate(expected) if isinstance(value, str)]
            self.assertEqual([(index, arguments[index]) for index, _ in pinned], pinned, arguments)
            # Drilling cycles use the modal F: the job feed must be active at the MCALL block.
            self.assertEqual(state_before(replayed, calls[0]).feed, feed)
        elif kind == 'stock':
            if ENGINE_NAME == 'legacy':
                # usr_workpiece_data builds the WORKPIECE arguments with tostr(value:xpos_f); the stock
                # legacy engine has no tostr (ENGINE-007), the compat engine and the default engine do.
                self.skipTest('stock legacy engine has no tostr(value:fmt) (ENGINE-007)')
            engine.set(bWorkpieceBuffered=False, bWorkpieceUsesA=case['initial'].get('bWorkpieceUsesA', False))
            engine.call('usr_workpiece_stock')
            self.assertEqual(block_texts(''.join(engine.output)), case['expected_blocks'])
        else:
            self.fail(f'unknown fixture kind: {kind}')

    def test_historical_bug_fixtures(self):
        """INDEPENDENT: explicit expected values derived from reviewed commit diffs."""
        for case in self.load_cases():
            with self.subTest(case=case['name'], commit=case['commit'][:7]):
                self.assert_fixture(case)

    def test_reviewed_historical_code_reversions_are_detected(self):
        """INDEPENDENT: reverse focused lines from real commit diffs in memory, never on disk.

        A failed independent oracle must detect the regression. Interpreter
        errors do not count as a successful mutation kill, and a missing or
        miscounted anchor raises StaleAnchor.
        """
        for case in self.load_cases():
            if 'regression' not in case:
                continue
            with self.subTest(case=case['name'], commit=case['commit'][:7]):
                patch = case['regression']
                candidate = mutate(patch['find'], patch['replace'], count=patch.get('count', 1))
                with self.assertRaises(AssertionError):
                    self.assert_fixture(case, candidate)


if __name__ == '__main__':
    unittest.main()
