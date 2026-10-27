"""Randomized differential tests against the verbatim legacy engine.

A permanent regression guard next to tests_engine/shadow_v1.py: identical inputs go
through ``pp_tests.gppl.legacy`` (the repository's engine, unchanged) and the new
engine; state, change flags and output must match exactly, and an error in one
must be an error in the other. Inputs stay inside the language both engines
share (the documented defect fixes are tested in test_v1_defects.py).
"""
import random
import unittest

from pp_tests.engine import Engine
from pp_tests.gppl import legacy
from support import source

BASE = dict(angle_4x_around_x=0, angle=0, cpos=0, apos=0, bpos=0, x_angle_const_z=0, iR1dir=-1, iR2dir=1,
            nPR1postemp=0, nPR1poscam=0, bR1StepReset=False, nPR1pos=0, nPR2pos=0, bLimit_3axis=False,
            bR1forceOutput=False,
            bR1useDir5a=True, dir5a='cw', angle_4x_around_x_dir='cw', cw='cw', ccw='ccw', cR1='A')


def outcome(engine_class, src, procedure, state, changed=None, args=()):
    engine = engine_class(src)
    engine.set(**state)
    engine.changed.update(changed or {})
    try:
        engine.call(procedure, list(args))
    except Exception as exc:                       # noqa: BLE001 - compared below
        return ('error', type(exc).__name__ in ('UnsupportedGPPL', 'ZeroDivisionError', 'GPPLRuntimeError',
                                                'MissingInput', 'PostprocessorStopped', 'PostAbort'), engine.output)
    return ('ok', engine.state, engine.changed, engine.output)


class GppDifferentialTests(unittest.TestCase):
    def setUp(self):
        self.src = source()

    def both(self, procedure, state, changed=None, args=()):
        old = outcome(legacy.Engine, self.src, procedure, state, changed, args)
        new = outcome(Engine, self.src, procedure, state, changed, args)
        self.assertEqual(old, new)
        return old

    def test_rotary_calculation_and_output(self):
        rng = random.Random(20261026)
        for _ in range(300):
            state = dict(BASE, angle_4x_around_x=rng.choice([0, 30, 90, -90, 180]),
                         angle=rng.choice([0, 15, -45]), cpos=rng.uniform(-400, 400),
                         apos=rng.uniform(-400, 400), bpos=rng.choice([0, 10]),
                         nPR1pos=rng.choice([0, 90]),
                         nPR1postemp=rng.choice([0, 90]), bLimit_3axis=rng.random() < .2,
                         bR1forceOutput=rng.random() < .3, bR1useDir5a=rng.random() < .5,
                         dir5a=rng.choice(['cw', 'ccw']), angle_4x_around_x_dir=rng.choice(['cw', 'ccw', 'x']))
            with self.subTest(state=state):
                first = self.both('usr_r1pos_calc', state)
                if first[0] == 'ok':
                    self.both('usr_r1_output', first[1], first[2])

    def test_arc_math_and_check(self):
        rng = random.Random(7)
        for _ in range(150):
            start = [rng.uniform(-50, 50) for _ in range(3)]
            rel = [rng.uniform(-20, 20) for _ in range(3)]
            state = dict(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz', arc_direction=rng.choice(['cw', 'ccw']),
                         arc_plane=rng.choice(['xy', 'zx', 'yz']), arc_size=rng.uniform(1, 360),
                         xstart=start[0], ystart=start[1], zstart=start[2],
                         xcenter_rel=rel[0], ycenter_rel=rel[1], zcenter_rel=rel[2],
                         xpos=rng.uniform(-50, 50), ypos=rng.uniform(-50, 50), zpos=rng.uniform(-50, 50))
            with self.subTest(state=state):
                self.both('usr_arc_math', state)


class LanguageDifferentialTests(unittest.TestCase):
    def expression(self, rng, depth=0):
        if depth > 3 or rng.random() < 0.3:
            return rng.choice(['a', 'b', 'n', '2', '0.5', '3', "'ab'", "'Q'", 's', 'true', 'false'])
        kind = rng.random()
        left, right = self.expression(rng, depth + 1), self.expression(rng, depth + 1)
        if kind < 0.35:
            return f'({left} {rng.choice(["+", "-", "*", "/"])} {right})'
        if kind < 0.55:
            return f'({left} {rng.choice(["eq", "ne", "gt", "lt", "ge", "le", "==", "!="])} {right})'
        if kind < 0.7:
            return f'({left} {rng.choice(["and", "or"])} {right})'
        if kind < 0.8:
            return f'!({left})'
        function = rng.choice(['abs({0})', 'sin({0})', 'cos({0})', 'strlen({0})', "instr({0}, 'b')",
                               'left({0}, 1)', 'substr({0}, 1, 1)', 'tonum({0})'])
        return function.format(left)

    def test_random_expressions(self):
        rng = random.Random(42)
        agreed = 0
        for _ in range(1500):
            text = self.expression(rng)
            results = []
            for engine_class in (legacy.Engine, Engine):
                engine = engine_class('')
                engine.set(a=1.5, b=-2, n=0, s='xyz')
                try:
                    results.append(('ok', engine.expression(text)))
                except Exception as exc:           # noqa: BLE001
                    results.append(('error', str(exc)))
            old, new = results
            if old[0] == 'ok' and new[0] == 'ok':
                self.assertEqual(repr(old[1]), repr(new[1]), text)
                agreed += 1
            elif old[0] == 'ok':
                # the only accepted divergence: Python string repetition (str * number),
                # which the legacy engine evaluated and the new engine rejects
                self.assertRegex(new[1], r"arithmetic '\*' on non-numbers .*'", (text, old))
            else:
                self.assertEqual(new[0], 'error', (text, new))
        self.assertGreater(agreed, 700)

    def test_random_output_statements(self):
        rng = random.Random(3)
        atoms = ["'G1'", "' '", 'x', 'y', 's', '(x*2)', 'nb', 'nl', "x:'8.5'", "y:'5.0(p)'", "x:fmt", "'A='"]
        for _ in range(600):
            parts = []
            for _ in range(rng.randint(1, 6)):
                if rng.random() < 0.3:
                    inner = ', '.join(rng.choice(atoms) for _ in range(rng.randint(1, 3)))
                    parts.append(f'[{inner}]')
                else:
                    parts.append(rng.choice(atoms))
            src = '@t\n{' + ', '.join(parts) + '}\nendp'
            state = dict(x=rng.choice([1.23456789, -0.0004, 12, 650.0]), y=rng.choice([0, 7.5, -3]), s='S',
                         fmt='7.3', clear_change_after_gen=rng.choice([0, 1]))
            changed = {name: rng.random() < 0.5 for name in ('x', 'y', 's')}
            with self.subTest(src=src):
                old = outcome(legacy.Engine, src, 't', state, changed)
                new = outcome(Engine, src, 't', state, changed)
                self.assertEqual(old, new)


if __name__ == '__main__':
    unittest.main()
