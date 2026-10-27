"""Meta-tests for the known-defect registry (tests/support/defects.py) and the
@known_defect / @covers markers (tests/support/markers.py).

Rules enforced (all by static AST inspection of tests/test*.py, so a marker is
checked even when its test is skipped):
  1. Every registry entry is complete and uses the documented vocabularies.
  2. Every marker references a registered id, with string-literal arguments.
  3. @known_defect is only used for PP-/ENGINE- entries; DESIGN- entries are
     referenced with @covers (one CHARACTERIZATION pin of the current behaviour).
  4. An id marked by more than one @known_defect test needs a distinct facet=
     on every marker (exactly one canonical test per defect facet).
  5. No marked test uses subTest (a failing subTest is recorded without raising,
     which would turn a reproduced defect into "no longer reproduces").
  6. Marked tests state an INDEPENDENT oracle in their docstring; tests of
     entries (or facets, Defect.facet_confidence) with confidence 'uncertain' or
     'likely-engine-artifact' also say UNVERIFIED and name the assumption.
  7. Every test states its oracle: INDEPENDENT or CHARACTERIZATION (files
     listed in LEGACY_FILES are exempt; the list is empty since every former
     legacy file was annotated by its area owner). The review-fix test files in
     MODULE_ORACLE_FILES state one 'Oracle (INDEPENDENT)' for the whole file in
     the module docstring; their tests inherit it.
  8. Pending-port rule: an entry must be referenced by at least one marker once
     the sentinel file of its owner area (AREAS[area].sentinel) exists. Before
     that the entry is pending-port and not required. This lets areas port in
     parallel without editing the registry.
  9. Area file ownership is exclusive, and tests/support contains no tests.
 10. Every registry entry names its location, and tests/PP_FINDINGS.md equals
     the document rendered from the registry and the markers
     (python -m pp_tests.tools.findings --write regenerates it).
 11. Status: open | fixed | accepted per entry (and per facet, facet_status);
     a fixed entry or facet names its fixing commit, an accepted one the owner
     decision. @known_defect is used only for open entries and facets; a fixed
     or accepted entry keeps at least one @covers test (its regression guard or
     characterization pin). Engine scopes name known engines.
The decorator semantics themselves are checked with synthetic test cases built
at runtime (not with decorator syntax, so they do not count as references).
"""
import ast
import os
import re
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from support import defects, findings
from support import markers as markers_module
from support.engines import WORKAROUNDS
from support.paths import ROOT, TESTS

SELF = Path(__file__).name
# Files exempt from rule 7. Empty: test_offline, test_motion, test_arcs,
# test_arc_link_boundary and test_history_regressions now state their oracles.
LEGACY_FILES = frozenset()
# Review-fix test files (git log f1803b4..): one module-level oracle for the file.
MODULE_ORACLE_FILES = frozenset({
    'test_post_homing_reposition.py', 'test_job_start_climb.py', 'test_zx_arc_guard.py',
    'test_cutter_compensation.py', 'test_job_plane_restore.py', 'test_tapping_direction.py',
    'test_rotary_modulo_range.py', 'test_move_4x_axial_x.py', 'test_inverse_time_feed.py',
    'test_unsupported_features.py'})
COMMIT = re.compile(r'[0-9a-f]{7} ')
MARKER_NAMES = ('known_defect', 'covers')
ID_PATTERN = re.compile(r'(PP|ENGINE|DESIGN)-\d{3}')


def _test_files():
    return sorted(path for path in TESTS.glob('test*.py') if path.name != SELF)


def _decorator_name(node):
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


class Marker:
    def __init__(self, path, owner, function, decorator):
        self.path, self.owner, self.function, self.decorator = path, owner, function, decorator
        self.name = _decorator_name(decorator)
        self.args = list(decorator.args) if isinstance(decorator, ast.Call) else []
        self.keywords = {k.arg: k.value for k in decorator.keywords} if isinstance(decorator, ast.Call) else {}

    @property
    def where(self):
        return f'{self.path.name}::{self.owner}.{self.function.name}'

    def literal_ids(self):
        return [arg.value for arg in self.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]

    def facet(self):
        value = self.keywords.get('facet')
        return value.value if isinstance(value, ast.Constant) else None


def _functions(tree):
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield node.name, item
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield '<module>', node


def collect():
    """(markers, test_functions) over all test files except this one."""
    found, tests = [], []
    for path in _test_files():
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for owner, function in _functions(tree):
            if function.name.startswith('test'):
                tests.append((path, owner, function))
            for decorator in function.decorator_list:
                if _decorator_name(decorator) in MARKER_NAMES:
                    found.append(Marker(path, owner, function, decorator))
    return found, tests


class RegistryContentTests(unittest.TestCase):
    def test_registry_entries_are_complete(self):
        """INDEPENDENT: the registry schema documented in tests/support/defects.py."""
        problems = []
        for key, entry in defects.REGISTRY.items():
            if key != entry.id or not ID_PATTERN.fullmatch(entry.id):
                problems.append(f'{key}: malformed id')
                continue
            if entry.kind != defects.KINDS[entry.id.split('-')[0]]:
                problems.append(f'{entry.id}: kind {entry.kind!r} does not match the id prefix')
            for field in ('title', 'reachability', 'settle_evidence'):
                if len(str(getattr(entry, field)).strip()) < 10:
                    problems.append(f'{entry.id}: {field} is empty or too short')
            if entry.severity not in defects.SEVERITIES:
                problems.append(f'{entry.id}: severity {entry.severity!r}')
            if entry.confidence not in defects.CONFIDENCES:
                problems.append(f'{entry.id}: confidence {entry.confidence!r}')
            if entry.owner_area not in defects.AREAS:
                problems.append(f'{entry.id}: owner_area {entry.owner_area!r}')
            if not entry.source_findings or not all(isinstance(s, str) and s.strip() for s in entry.source_findings):
                problems.append(f'{entry.id}: source_findings missing')
            if len(entry.location.strip()) < 10:
                problems.append(f'{entry.id}: location is empty or too short')
            for facet, confidence in entry.facet_confidence:
                if not isinstance(facet, str) or confidence not in defects.CONFIDENCES:
                    problems.append(f'{entry.id}: facet_confidence {facet!r}: {confidence!r}')
            for facet, status, resolution in ((None, entry.status, entry.resolution),) + entry.facet_status:
                label = entry.id if facet is None else f'{entry.id}[{facet}]'
                if status not in defects.STATUSES:
                    problems.append(f'{label}: status {status!r}')
                elif status == 'fixed' and not COMMIT.match(resolution):
                    problems.append(f'{label}: a fixed entry names its commit first: {resolution!r}')
                elif status == 'accepted' and len(resolution.strip()) < 20:
                    problems.append(f'{label}: an accepted entry states the owner decision')
                elif status == 'open' and resolution:
                    problems.append(f'{label}: an open entry has no resolution')
            for facet, engines in entry.engines:
                if not engines or set(engines) - set(defects.ENGINES):
                    problems.append(f'{entry.id}: engines {facet!r}: {engines!r}')
            if entry.engines and entry.kind != 'engine':
                problems.append(f'{entry.id}: only ENGINE entries are engine-scoped')
        self.assertEqual(problems, [])

    def test_findings_document_is_current(self):
        """INDEPENDENT: tests/PP_FINDINGS.md is derived data (support/findings.py, rule 10)."""
        expected = findings.render()
        current = findings.DOCUMENT.read_text(encoding='utf-8') if findings.DOCUMENT.exists() else ''
        self.assertTrue(current == expected,
                        'tests/PP_FINDINGS.md is out of date; run: python -m pp_tests.tools.findings --write')

    def test_area_ownership_is_exclusive(self):
        """INDEPENDENT: each repo file is owned by exactly one migration area."""
        owners = {}
        problems = []
        for area, info in defects.AREAS.items():
            if info.sentinel not in info.files:
                problems.append(f'area {area}: sentinel {info.sentinel} is not one of its files')
            for name in info.files:
                if not name.startswith('tests/') or name.startswith('tests/support/'):
                    problems.append(f'area {area}: {name} is outside the area-owned test tree')
                if name in owners:
                    problems.append(f'{name} owned by {owners[name]} and {area}')
                owners[name] = area
        self.assertEqual(problems, [])

    def test_every_engine_workaround_is_registered(self):
        """INDEPENDENT: every GpplCompatEngine workaround cites an ENGINE entry."""
        for switch, defect_id in WORKAROUNDS.items():
            self.assertIn(defect_id, defects.REGISTRY, switch)
            self.assertEqual(defects.REGISTRY[defect_id].kind, 'engine', switch)

    def test_support_package_contains_no_tests(self):
        """INDEPENDENT: discovery must not collect helpers as tests."""
        self.assertEqual(sorted(p.name for p in (TESTS / 'support').glob('test*.py')), [])


class MarkerUsageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markers, cls.tests = collect()

    def test_markers_reference_registered_ids(self):
        """INDEPENDENT: every marker names registry ids as string literals."""
        problems = []
        for marker in self.markers:
            if not marker.args or len(marker.literal_ids()) != len(marker.args):
                problems.append(f'{marker.where}: @{marker.name} needs string-literal ids')
            if marker.name == 'known_defect' and len(marker.args) != 1:
                problems.append(f'{marker.where}: @known_defect takes exactly one id')
            for defect_id in marker.literal_ids():
                if defect_id not in defects.REGISTRY:
                    problems.append(f'{marker.where}: unknown id {defect_id}')
        self.assertEqual(problems, [])

    def test_known_defect_is_not_used_for_design_questions(self):
        """INDEPENDENT: DESIGN entries are owner decisions, not failing defects."""
        bad = [f'{m.where}: {i}' for m in self.markers if m.name == 'known_defect'
               for i in m.literal_ids() if i in defects.REGISTRY and defects.REGISTRY[i].kind == 'design']
        self.assertEqual(bad, [])

    def test_repeated_markers_have_distinct_facets(self):
        """INDEPENDENT: exactly one canonical test per defect facet."""
        by_id = {}
        for marker in self.markers:
            if marker.name == 'known_defect':
                for defect_id in marker.literal_ids():
                    by_id.setdefault(defect_id, []).append(marker)
        problems = []
        for defect_id, group in by_id.items():
            if len(group) < 2:
                continue
            facets = [marker.facet() for marker in group]
            if None in facets or len(set(facets)) != len(facets):
                problems.append(f'{defect_id}: {[(m.where, f) for m, f in zip(group, facets)]}')
        self.assertEqual(problems, [])

    def test_marked_tests_do_not_use_subtest(self):
        """INDEPENDENT: a failing subTest does not raise, so the marker would misreport."""
        bad = []
        for marker in self.markers:
            if marker.name != 'known_defect':
                continue
            for node in ast.walk(marker.function):
                if isinstance(node, ast.Attribute) and node.attr == 'subTest':
                    bad.append(marker.where)
                    break
        self.assertEqual(bad, [])

    def test_marked_tests_state_an_independent_oracle(self):
        """INDEPENDENT: quality bar; uncertain entries must name the unverified assumption."""
        problems = []
        for marker in self.markers:
            if marker.name != 'known_defect':
                continue
            if not marker.function.name.startswith('test'):
                problems.append(f'{marker.where}: @known_defect on a non-test function')
            doc = ast.get_docstring(marker.function) or ''
            if 'INDEPENDENT' not in doc:
                problems.append(f'{marker.where}: docstring must state the INDEPENDENT oracle')
            for defect_id in marker.literal_ids():
                entry = defects.REGISTRY.get(defect_id)
                confidence = entry.confidence_for(marker.facet()) if entry else None
                if entry and confidence != 'confirmed' and 'UNVERIFIED' not in doc:
                    problems.append(f'{marker.where}: {defect_id} is {confidence}; docstring must say UNVERIFIED')
        self.assertEqual(problems, [])

    def test_facet_confidence_names_marked_facets(self):
        """INDEPENDENT: a per-facet confidence must belong to a canonical test of that facet."""
        marked = {(i, m.facet()) for m in self.markers if m.name == 'known_defect' for i in m.literal_ids()}
        stale = [f'{entry.id}[{facet}]' for entry in defects.REGISTRY.values()
                 for facet, _ in entry.facet_confidence if (entry.id, facet) not in marked]
        self.assertEqual(stale, [])

    def test_new_test_files_state_the_oracle(self):
        """INDEPENDENT: quality bar; every non-legacy test names its oracle (module
        docstring 'Oracle (INDEPENDENT)' for MODULE_ORACLE_FILES)."""
        problems = []
        module_oracle = {}
        for path, owner, function in self.tests:
            if path.name in LEGACY_FILES:
                continue
            if path.name in MODULE_ORACLE_FILES:
                if path.name not in module_oracle:
                    tree = ast.parse(path.read_text(encoding='utf-8'))
                    module_oracle[path.name] = 'Oracle (INDEPENDENT)' in (ast.get_docstring(tree) or '')
                if module_oracle[path.name]:
                    continue
            doc = ast.get_docstring(function) or ''
            if 'INDEPENDENT' not in doc and 'CHARACTERIZATION' not in doc:
                problems.append(f'{path.name}::{owner}.{function.name}')
        self.assertEqual(problems, [])
        self.assertEqual(sorted(name for name in MODULE_ORACLE_FILES if not (TESTS / name).exists()), [])

    def test_known_defect_marks_only_open_entries_and_facets(self):
        """INDEPENDENT: rule 11; a fixed or accepted defect has no failing canonical test."""
        bad = [f'{m.where}: {i}[{m.facet()}] is {defects.REGISTRY[i].status_for(m.facet())}'
               for m in self.markers if m.name == 'known_defect' for i in m.literal_ids()
               if i in defects.REGISTRY and defects.REGISTRY[i].status_for(m.facet()) != 'open']
        self.assertEqual(bad, [])

    def test_resolved_entries_keep_a_covers_test(self):
        """INDEPENDENT: rule 11; a fixed entry keeps its regression guard, an accepted
        one its characterization pin, and a partly fixed entry has guards for the fixed
        facets (@covers) besides the canonical tests of its open facets."""
        covered = {i for m in self.markers if m.name == 'covers' for i in m.literal_ids()}
        resolved = [entry.id for entry in defects.REGISTRY.values()
                    if entry.status != 'open' or entry.fixed_facets]
        self.assertEqual(sorted(set(resolved) - covered), [])

    def test_entries_of_ported_areas_are_referenced(self):
        """INDEPENDENT: pending-port rule (module docstring, rule 8)."""
        referenced = {i for marker in self.markers for i in marker.literal_ids()}
        active = {area for area, info in defects.AREAS.items() if (ROOT / info.sentinel).exists()}
        missing = sorted(entry.id for entry in defects.REGISTRY.values()
                         if entry.owner_area in active and entry.id not in referenced)
        self.assertEqual(missing, [], f'unreferenced entries of ported areas {sorted(active)}')


def _synthetic_case(body, defect_id='PP-004', **options):
    """A one-test TestCase whose test is wrapped by known_defect at runtime."""
    case = type('Synthetic', (unittest.TestCase,), {
        'test_body': markers_module.known_defect(defect_id, **options)(body)})
    result = unittest.TestResult()
    case('test_body').run(result)
    return result


def _fails(self):
    self.assertEqual(1, 2, 'reproduced')


def _passes(self):
    self.assertEqual(1, 1)


def _errors(self):
    raise KeyError('engine gap')


def _uses_subtest(self):
    with self.subTest(x=1):
        self.assertEqual(1, 2)


class DecoratorSemanticsTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(markers_module.STRICT_ENV, None)

    def test_reproduced_defect_is_reported_as_skip(self):
        """INDEPENDENT: documented default-mode semantics (support/markers.py)."""
        result = _synthetic_case(_fails)
        self.assertEqual((len(result.skipped), len(result.failures), len(result.errors)), (1, 0, 0))
        self.assertTrue(result.skipped[0][1].startswith('known defect PP-004 reproduced: '), result.skipped)

    def test_fixed_defect_fails_with_update_instruction(self):
        """INDEPENDENT: documented default-mode semantics."""
        result = _synthetic_case(_passes)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('PP-004 no longer reproduces: update the registry and remove the marker',
                      result.failures[0][1])

    def test_other_exceptions_are_errors(self):
        """INDEPENDENT: engine gaps never count as reproducing a defect."""
        result = _synthetic_case(_errors)
        self.assertEqual((len(result.skipped), len(result.failures), len(result.errors)), (0, 0, 1))

    def test_match_rejects_an_unrelated_assertion(self):
        """INDEPENDENT: match= narrows the accepted failure."""
        result = _synthetic_case(_fails, match='something else')
        self.assertEqual((len(result.skipped), len(result.failures)), (0, 1))
        self.assertEqual(len(_synthetic_case(_fails, match='reproduced').skipped), 1)

    def test_subtest_inside_marked_test_is_an_error(self):
        """INDEPENDENT: runtime guard behind rule 5."""
        result = _synthetic_case(_uses_subtest)
        self.assertEqual(len(result.errors), 1)
        self.assertIn('subTest is not allowed', result.errors[0][1])

    def test_strict_mode_runs_plain_tests(self):
        """INDEPENDENT: PP_STRICT_KNOWN_DEFECTS=1 makes the marker transparent."""
        os.environ[markers_module.STRICT_ENV] = '1'
        failing, passing = _synthetic_case(_fails), _synthetic_case(_passes)
        self.assertEqual((len(failing.failures), len(failing.skipped)), (1, 0))
        self.assertTrue(passing.wasSuccessful())

    def test_facet_appears_in_the_skip_reason(self):
        """INDEPENDENT: facet labels identify the canonical test of one facet."""
        result = _synthetic_case(_fails, defect_id='PP-002', facet='negative-mode')
        self.assertTrue(result.skipped[0][1].startswith('known defect PP-002[negative-mode] reproduced'))

    def test_fixed_and_accepted_entries_are_rejected(self):
        """INDEPENDENT: rule 11 at import time; resolved entries take @covers."""
        for defect_id, facet in (('PP-001', None), ('PP-002', 'whole-turn'), ('PP-008', None)):
            with self.assertRaises(ValueError, msg=f'{defect_id}[{facet}]'):
                markers_module.known_defect(defect_id, facet=facet)

    def test_marker_is_transparent_on_an_engine_without_the_defect(self):
        """INDEPENDENT: documented engine scope (support/markers.py): a defect that does
        not reproduce on the active engine runs as a plain test there."""
        other = 'gppl' if markers_module.ENGINE_NAME == 'legacy' else 'legacy'
        scoped = replace(defects.REGISTRY['PP-004'], engines=(('*', (other,)),))
        with mock.patch.dict(defects.REGISTRY, {'PP-004': scoped}), \
                mock.patch.dict(markers_module.REGISTRY, {'PP-004': scoped}):
            failing, passing = _synthetic_case(_fails), _synthetic_case(_passes)
        self.assertEqual((len(failing.failures), len(failing.skipped)), (1, 0))
        self.assertTrue(passing.wasSuccessful())

    def test_unknown_ids_are_rejected(self):
        """INDEPENDENT: markers cannot reference ids outside the registry."""
        with self.assertRaises(KeyError):
            markers_module.known_defect('PP-999')
        with self.assertRaises(KeyError):
            markers_module.covers('DESIGN-999')


if __name__ == '__main__':
    unittest.main()
