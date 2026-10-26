"""Independent oracles for bugs documented by reviewed GPP commits."""
import json
import re
import unittest

from pp_tests.engine import Engine
from test_motion import motion_engine
from test_offline import PP, ROOT


FIXTURE = ROOT / 'tests/fixtures/history_regressions.json'


def history_engine(source=None):
    engine = motion_engine()
    if source is not None:
        candidate = Engine(source)
        candidate.set(**engine.state)
        candidate.changed.update(engine.changed)
        engine = candidate
    engine.set(COMP_LEFT='left', COMP_RIGHT='right', COMP_OFF='off',
               tool_number=7, last_tool=False, next_tool_number=8,
               drill_clearance_z=30, drill_upper_z=12, drill_lower_z=-15,
               safety=2, down_step=3, delay=0.25,
               G81='g81', G82='g82', G83='g83', G84='g84', G86='g86')
    return engine


def blocks(engine):
    return [block.strip() for block in ''.join(engine.output).splitlines() if block.strip()]


class HistoryRegressionTests(unittest.TestCase):
    def assert_fixture(self, case, source=None):
        engine = history_engine(source)
        engine.set(**case['initial'])
        kind = case['kind']
        if kind == 'compensation':
            engine.changed['idiametercomp'] = True
            codes = []
            for side in (None, 'right', 'off'):
                engine.output.clear()
                if side:
                    engine.set(side=side)
                    engine.call('compensation')
                engine.call('line_5x')
                text = ''.join(engine.output)
                codes.append([int(code) for code in re.findall(r'\bG(4[012])\b', text)])
            self.assertEqual(codes, case['expected_codes'])
        elif kind == 'fourth_axis':
            engine.call('fourth_axis')
            self.assertEqual(engine.state['nr1pos'], case['expected_a'])
            self.assertEqual(engine.state['apos'], case['expected_apos'])
            text = ''.join(engine.output)
            self.assertEqual(re.findall(r'A=(?:ACP|ACN|DC)\(([^)]+)\)', text), [str(case['expected_a'])])
        elif kind == 'axis_mapping':
            engine.call('usr_r1pos_calc')
            self.assertEqual(engine.state['nr1pos'], case['expected_a'])
            self.assertEqual(engine.state['nr2pos'], case['expected_secondary'])
        elif kind == 'tool_change':
            engine.call('usr_ct_toolchange')
            self.assertEqual(blocks(engine), case['expected_blocks'])
        elif kind == 'cycle':
            engine.call('drill')
            text = ''.join(engine.output)
            matches = re.findall(r'MCALL CYCLE(\d+)\s*\(([^)]*)\)', text)
            self.assertEqual(len(matches), 1)
            cycle, arguments = matches[0]
            self.assertEqual(int(cycle), case['expected_cycle'])
            self.assertEqual(arguments.split(','), case['expected_parameters'])
            self.assertIn('F100', text.replace(' ', ''))
        elif kind == 'stock':
            engine.call('usr_workpiece_stock')
            self.assertEqual(blocks(engine), case['expected_blocks'])
        else:
            self.fail(f'unknown fixture kind: {kind}')

    def test_historical_bug_fixtures(self):
        data = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.assertEqual(data['schema'], 1)
        for case in data['cases']:
            with self.subTest(case=case['name'], commit=case['commit'][:7]):
                self.assert_fixture(case)

    def test_reviewed_historical_code_reversions_are_detected(self):
        """Reverse focused lines from real commit diffs in memory, never on disk.

        A failed independent oracle must detect the regression. Interpreter
        errors do not count as a successful mutation kill.
        """
        source = PP.read_text(encoding='utf-8-sig')
        data = json.loads(FIXTURE.read_text(encoding='utf-8'))
        for case in data['cases']:
            if 'regression' not in case:
                continue
            with self.subTest(case=case['name'], commit=case['commit'][:7]):
                patch = case['regression']
                self.assertIn(patch['find'], source, 'historical reversal anchor changed; review the fixture')
                candidate = source.replace(patch['find'], patch['replace'])
                with self.assertRaises(AssertionError):
                    self.assert_fixture(case, candidate)
