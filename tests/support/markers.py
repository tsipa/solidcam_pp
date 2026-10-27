"""The shared known-defect marker and the registry reference marker.

@known_defect('PP-001') marks the ONE canonical test of a registered defect
(or of one facet of it: @known_defect('PP-002', facet='whole-turn')). The test
body asserts the CORRECT behaviour with an independent oracle, so it fails
while the defect exists.

Default mode (PP_STRICT_KNOWN_DEFECTS unset or not '1'):
  * AssertionError            -> skipTest('known defect <id> reproduced: <title> | <message>')
                                 (with match=<regex>, only an AssertionError whose
                                 message matches is accepted; any other one is re-raised
                                 as a real failure)
  * the test passes           -> self.fail('<id> no longer reproduces: update the
                                 registry and remove the marker')
  * any other exception       -> propagates as a test ERROR (an engine gap, KeyError
                                 or UnsupportedGPPL never counts as reproducing a defect)
Strict mode (PP_STRICT_KNOWN_DEFECTS=1):
  * the marker is transparent: the test runs as a plain test and fails red while
    the defect exists, passes once it is fixed.
Engine scope: when the registry says the defect (facet) does not reproduce on
the active engine (Defect.engines, e.g. an ENGINE gap the GPPL engine fixes),
the marker is transparent too, so the test is a plain guard on that engine.

Only open entries and facets take @known_defect; a fixed or accepted one
(Defect.status / facet_status) raises ValueError at import: its former
canonical test is a regression guard or a characterization pin with @covers.

subTest is forbidden inside marked tests: a failing subTest is recorded by
unittest without raising, which would make the marker report "no longer
reproduces". The meta-test enforces this with an AST check and the wrapper
also replaces self.subTest with a function that raises TypeError.

@covers('DESIGN-002', 'ENGINE-006') records that a test exercises or pins a
registry item without expecting a failure (design-question pins, engine
workaround guards, characterization next to an open question). The meta-test
counts both markers as references.
"""
import functools
import os
import re
import unittest

from .defects import REGISTRY
from .engines import ENGINE_NAME

STRICT_ENV = 'PP_STRICT_KNOWN_DEFECTS'


def strict_mode():
    return os.environ.get(STRICT_ENV) == '1'


def _lookup(defect_id):
    if defect_id not in REGISTRY:
        raise KeyError(f'unknown registry id {defect_id!r}; add it to tests/support/defects.py')
    return REGISTRY[defect_id]


def _forbidden_subtest(*args, **kwargs):
    raise TypeError('subTest is not allowed inside a @known_defect test (failures would be swallowed)')


def known_defect(defect_id, *, facet=None, match=None):
    """Mark the canonical test of a registered defect (see module docstring)."""
    entry = _lookup(defect_id)
    label = defect_id if facet is None else f'{defect_id}[{facet}]'
    if entry.status_for(facet) != 'open':
        raise ValueError(f'{label} is {entry.status_for(facet)} ({entry.resolution_for(facet)}); mark its test with '
                         f'@covers({defect_id!r}) instead of @known_defect')
    pattern = re.compile(match) if match else None
    transparent = not entry.reproduces_on(ENGINE_NAME, facet)

    def decorate(test):
        @functools.wraps(test)
        def wrapper(self, *args, **kwargs):
            if transparent or strict_mode():
                return test(self, *args, **kwargs)
            self.subTest = _forbidden_subtest
            try:
                test(self, *args, **kwargs)
            except AssertionError as exc:
                message = str(exc)
                if pattern is not None and not pattern.search(message):
                    raise
                first = message.strip().splitlines()[0][:300] if message.strip() else ''
                raise unittest.SkipTest(f'known defect {label} reproduced: {entry.title} | {first}') from None
            finally:
                del self.subTest
            self.fail(f'{label} no longer reproduces: update the registry and remove the marker')

        wrapper.__known_defect__ = defect_id
        wrapper.__known_defect_facet__ = facet
        wrapper.__known_defect_target__ = test
        return wrapper
    return decorate


def covers(*defect_ids):
    """Record registry items a passing test exercises (no failure expected)."""
    for defect_id in defect_ids:
        _lookup(defect_id)

    def decorate(test):
        test.__registry_refs__ = tuple(getattr(test, '__registry_refs__', ())) + defect_ids
        return test
    return decorate


def run_unmarked(testcase, method_name):
    """Run the undecorated body of a @known_defect test (for harness self-tests)."""
    return getattr(type(testcase), method_name).__known_defect_target__(testcase)
