"""Randomized expressions and output statements pinned to recorded outcomes (default policies).

fixtures/language_golden.json replaces the randomized differential test against the original
engine (pp_tests/gppl/legacy.py, removed): the same generated cases, recorded from the GPPL engine
at 7c52a4d after a last check against the original engine. Expressions: 1032 distinct texts of the
1500 draws (301 values, 731 errors), the original engine agreeing on every one except the 15 string
repetitions (str * number) it evaluated and the GPPL engine rejects. Output statements: 598 distinct
cases of the 600 draws, with clear_change_after_gen 0 and 1 (the GPP itself always sets 1), output
and change flags identical on both engines. The fixture is the compat semantics frozen; change an
entry only for a deliberate change of them.
"""
import ast
import json
import math
import unittest

from pp_tests.engine import Engine
from support import COMPAT, FIXTURES

GOLDEN = json.loads((FIXTURES / 'language_golden.json').read_text(encoding='utf-8'))


def expression_outcome(text):
    engine = Engine('', policies=COMPAT)
    engine.set(a=1.5, b=-2, n=0, s='xyz')
    try:
        return repr(engine.expression(text))
    except Exception as exc:                       # noqa: BLE001 - compared below
        return 'error ' + type(exc).__name__


def same_outcome(actual, expected):
    """Equal reprs, or two floats of the same sign within 1e-12 (sin/cos come from the platform's C
    library; the sign check keeps -0.0 apart from 0.0)."""
    if actual == expected:
        return True
    try:
        values = ast.literal_eval(actual), ast.literal_eval(expected)
    except (ValueError, SyntaxError):
        return False
    return (all(type(value) is float for value in values)
            and math.copysign(1, values[0]) == math.copysign(1, values[1])
            and math.isclose(*values, rel_tol=1e-12, abs_tol=1e-15))


class LanguageGoldenTests(unittest.TestCase):
    def test_random_expressions(self):
        for text, expected in GOLDEN['expressions']:
            with self.subTest(text=text):
                actual = expression_outcome(text)
                if not same_outcome(actual, expected):
                    self.assertEqual(actual, expected)
        self.assertEqual(len(GOLDEN['expressions']), 1032)

    def test_random_output_statements(self):
        for case in GOLDEN['output_statements']:
            with self.subTest(body=case['body']):
                engine = Engine('@t\n' + case['body'] + '\nendp', policies=COMPAT)
                state = dict(x=case['x'], y=case['y'], s='S', fmt='7.3', clear_change_after_gen=case['clear'])
                engine.set(**state)
                engine.changed.update(case['changed'])
                engine.call('t')
                self.assertEqual((engine.output, engine.changed, engine.state),
                                 (case['output'], case['changed_after'], state))
        self.assertEqual(len(GOLDEN['output_statements']), 598)


if __name__ == '__main__':
    unittest.main()
