"""Differential check: run the *legacy* suite with every Engine mirrored by the legacy engine.

    python3 tests_engine/shadow_v1.py                      # oracle: pp_tests/gppl/legacy.py (verbatim copy)
    GPPL_V1_ENGINE=/path/to/engine.py python3 tests_engine/shadow_v1.py

Each top-level ``call()``/``expression()`` executes on the new engine and on the
legacy engine from an identical state copy; state, change flags, emitted
fragments and error/no-error outcome must match exactly. Prints a summary;
exit 1 on mismatch. Meant as a permanent CI check next to the suite.
"""
import copy
import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

import pp_tests.engine as v2  # noqa: E402

V1_PATH = os.environ.get('GPPL_V1_ENGINE')
if V1_PATH:
    spec = importlib.util.spec_from_file_location('gppl_v1_engine', V1_PATH)
    v1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v1)
else:
    from pp_tests.gppl import legacy as v1  # noqa: E402

STATS = {'calls': 0, 'expressions': 0, 'errors_both': 0, 'mismatches': []}


def _outcome(fn):
    try:
        return fn(), None
    except Exception as exc:                       # noqa: BLE001 - compared, then re-raised
        return None, exc


class ShadowEngine(v2.Engine):
    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)
        # The legacy engine has no policies: mirror only engines built with the compat defaults.
        self._v1 = v1.Engine(source) if self.policies == v2.Policies() else None

    def _sync(self):
        self._v1.state = copy.deepcopy(self.state)
        self._v1.changed = dict(self.changed)
        self._v1.output = []

    def call(self, procedure, arguments=()):
        if self.frames or self._v1 is None:          # nested call from inside v2, or not comparable
            return super().call(procedure, arguments)
        STATS['calls'] += 1
        self._sync()
        before = len(self.output)
        _, error1 = _outcome(lambda: self._v1.call(procedure, list(arguments)))
        _, error2 = _outcome(lambda: super(ShadowEngine, self).call(procedure, arguments))
        where = f'call @{procedure}'
        if (error1 is None) != (error2 is None):
            STATS['mismatches'].append(f'{where}: v1 error={error1!r} v2 error={error2!r}')
        elif error1 is not None:
            STATS['errors_both'] += 1
        else:
            for label, a, b in (('state', self._v1.state, self.state), ('changed', self._v1.changed, self.changed),
                                ('output', self._v1.output, self.output[before:])):
                if a != b:
                    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k)) if isinstance(a, dict) else (a, b)
                    STATS['mismatches'].append(f'{where}: {label} differs: {diff}')
        if error2 is not None:
            raise error2

    def expression(self, text):
        STATS['expressions'] += 1
        self._sync()
        value1, error1 = _outcome(lambda: self._v1.expression(text))
        value2, error2 = _outcome(lambda: super(ShadowEngine, self).expression(text))
        if (error1 is None) != (error2 is None) or (error1 is None and value1 != value2):
            STATS['mismatches'].append(f'expression {text!r}: v1={value1!r}/{error1!r} v2={value2!r}/{error2!r}')
        if error2 is not None:
            raise error2
        return value2


v2.Engine = ShadowEngine
result = unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.discover(str(ROOT / 'tests')))
print(f"shadow: {STATS['calls']} top-level calls, {STATS['expressions']} expressions, "
      f"{STATS['errors_both']} raised in both engines, {len(STATS['mismatches'])} mismatches")
for line in STATS['mismatches'][:40]:
    print('  MISMATCH', line)
sys.exit(0 if result.wasSuccessful() and not STATS['mismatches'] else 1)
