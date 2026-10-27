"""Render tests/PP_FINDINGS.md from the registry and the test markers.

The document is derived data: tests/support/defects.py (REGISTRY, LOCATIONS,
OBSERVATIONS) plus an AST scan of the @known_defect / @covers markers in
tests/test*.py. tests/test_known_defect_registry.py fails when the committed
file differs from render(); regenerate it with

    python -m pp_tests.tools.findings --write
"""
import ast
from collections import Counter
from dataclasses import dataclass

from .defects import AREAS, CONFIDENCES, REGISTRY, SEVERITIES, STATUSES, OBSERVATIONS
from .paths import TESTS

DOCUMENT = TESTS / 'PP_FINDINGS.md'
REGISTRY_TEST = 'test_known_defect_registry.py'
MARKER_NAMES = ('known_defect', 'covers')
KIND_TITLES = (('pp', 'Suspected postprocessor defects (PP-xxx)'),
               ('engine', 'Engine gaps and fidelity issues (ENGINE-xxx)'),
               ('design', 'Design questions for the owner (DESIGN-xxx)'))


@dataclass(frozen=True)
class MarkerUse:
    defect_id: str
    marker: str          # 'known_defect' or 'covers'
    facet: str
    path: str            # repo-relative, '/' separated
    owner: str
    function: str

    @property
    def test(self):
        return f'{self.path}::{self.owner}::{self.function}'


def _name(node):
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def scan_markers(tests_dir=TESTS):
    """Every marker use in tests/test*.py (the registry meta-test excluded), sorted."""
    uses = []
    for path in sorted(tests_dir.glob('test*.py')):
        if path.name == REGISTRY_TEST:
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in tree.body:
            members = ([(node.name, item) for item in node.body] if isinstance(node, ast.ClassDef)
                       else [('<module>', node)])
            for owner, function in members:
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for decorator in function.decorator_list:
                    marker = _name(decorator)
                    if marker not in MARKER_NAMES or not isinstance(decorator, ast.Call):
                        continue
                    facet = None
                    for keyword in decorator.keywords:
                        if keyword.arg == 'facet' and isinstance(keyword.value, ast.Constant):
                            facet = keyword.value.value
                    for argument in decorator.args:
                        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                            uses.append(MarkerUse(argument.value, marker, facet, f'tests/{path.name}',
                                                  owner, function.name))
    return sorted(uses, key=lambda u: (u.defect_id, u.marker, u.facet or '', u.path, u.owner, u.function))


def _one_line(text):
    return ' '.join(str(text).split())


def _cell(text):
    return _one_line(text).replace('|', '\\|')


def render(uses=None):
    """The complete text of tests/PP_FINDINGS.md."""
    uses = scan_markers() if uses is None else uses
    by_id = {}
    for use in uses:
        by_id.setdefault(use.defect_id, []).append(use)
    entries = list(REGISTRY.values())
    out = [
        '# Registered findings: suspected PP defects, engine gaps, design questions',
        '',
        'Generated from `tests/support/defects.py` (the registry) and the `@known_defect` / `@covers`',
        'markers in `tests/test*.py`. Do not edit by hand; regenerate with',
        '',
        '    python -m pp_tests.tools.findings --write',
        '',
        '`tests/test_known_defect_registry.py` fails when this file is out of date.',
        '',
        'The postprocessor is never changed by this suite. Each open suspected defect has exactly one',
        'canonical test per facet, marked `@known_defect(id)`. The test asserts the correct behaviour',
        'with an independent oracle; in the default run it is reported as a skip',
        '("known defect ... reproduced"). Run it red with',
        '',
        '    PP_STRICT_KNOWN_DEFECTS=1 python -m unittest discover -s tests -k <test name>',
        '',
        '(PowerShell: `$env:PP_STRICT_KNOWN_DEFECTS = "1"` first). When the behaviour is fixed, the',
        'default run fails with "no longer reproduces" until the entry is marked fixed (status and fixing',
        'commit) and the marker becomes `@covers`: the test is then a regression guard (section Fixed).',
        'Entries the owner accepted as intended are listed under Accepted and pinned by a',
        'CHARACTERIZATION test. DESIGN entries are owner decisions: they are pinned with `@covers`',
        'CHARACTERIZATION tests, never with `@known_defect`. ENGINE entries refer to the test engines:',
        'the GPPL engine (`pp_tests/gppl`, default) and the original engine (`GPPL_ENGINE=legacy`);',
        'an entry scoped to one engine is a plain guard on the other. Severity and confidence are after',
        'the adversarial verifier corrections. GPP line numbers refer to `Gmill_540v_4x.gpp` at f1803b4.',
        '',
    ]
    open_entries = [entry for entry in entries if entry.status == 'open']
    fixed_entries = [entry for entry in entries if entry.status == 'fixed' or entry.fixed_facets]
    accepted_entries = [entry for entry in entries if entry.status == 'accepted']
    kinds = Counter(entry.kind for entry in entries)
    out.append('## Summary')
    out.append('')
    out.append('| kind | entries | ' + ' | '.join(SEVERITIES) + ' |')
    out.append('|---|---|' + '---|' * len(SEVERITIES))
    for kind, _ in KIND_TITLES:
        counts = Counter(entry.severity for entry in entries if entry.kind == kind)
        out.append(f'| {kind} | {kinds[kind]} | ' + ' | '.join(str(counts[s]) for s in SEVERITIES) + ' |')
    out.append('')
    out.append('| kind | ' + ' | '.join(CONFIDENCES) + ' |')
    out.append('|---|' + '---|' * len(CONFIDENCES))
    for kind, _ in KIND_TITLES:
        counts = Counter(entry.confidence for entry in entries if entry.kind == kind)
        out.append(f'| {kind} | ' + ' | '.join(str(counts[c]) for c in CONFIDENCES) + ' |')
    out.append('')
    out.append('| kind | ' + ' | '.join(STATUSES) + ' | partly fixed |')
    out.append('|---|' + '---|' * (len(STATUSES) + 1))
    for kind, _ in KIND_TITLES:
        counts = Counter(entry.status for entry in entries if entry.kind == kind)
        partly = sum(1 for entry in entries if entry.kind == kind and entry.status == 'open' and entry.fixed_facets)
        out.append(f'| {kind} | ' + ' | '.join(str(counts[s]) for s in STATUSES) + f' | {partly} |')
    out.append('')
    legacy_only = [entry.id for entry in entries if any(engines == ('legacy',) for _, engines in entry.engines)]
    gppl_only = [entry.id for entry in entries if any(engines == ('gppl',) for _, engines in entry.engines)]
    out.append(f'Engine scope: {", ".join(legacy_only)} reproduce (in whole or in one facet) only on the legacy '
               f'engine; {", ".join(gppl_only) or "none"} only on the GPPL engine.')
    out.append('')
    reproducing = sum(1 for use in uses if use.marker == 'known_defect')
    out.append(f'Canonical `@known_defect` tests: {reproducing}. `@covers` references: '
               f'{sum(1 for use in uses if use.marker == "covers")}.')
    out.append('')
    out.append('## Index of open entries')
    out.append('')
    out.append('| id | severity | confidence | area | title | reproduced by |')
    out.append('|---|---|---|---|---|---|')
    for entry in open_entries:
        canonical = [use for use in by_id.get(entry.id, []) if use.marker == 'known_defect']
        tests = ', '.join(f'`{use.function}`' + (f' [{use.facet}]' if use.facet else '') for use in canonical)
        if not canonical:
            tests = 'pinned only (@covers)' if by_id.get(entry.id) else 'none'
        out.append(f'| [{entry.id}](#{entry.id.lower()}) | {entry.severity} | {entry.confidence} | '
                   f'{entry.owner_area} | {_cell(entry.title)} | {tests} |')
    out.append('')
    for kind, title in KIND_TITLES:
        out.append(f'## {title}')
        out.append('')
        for entry in (e for e in open_entries if e.kind == kind):
            out.extend(_entry_section(entry, by_id.get(entry.id, [])))
    out.append('## Fixed')
    out.append('')
    out.append('Fixed by owner-approved GPP commits. The former canonical test of each entry (or facet) is')
    out.append('now a regression guard marked `@covers`.')
    out.append('')
    out.append('| id | fixing commit | guarded by (`@covers`) | tests of the fix |')
    out.append('|---|---|---|---|')
    for entry in fixed_entries:
        guards = ', '.join(f'`{use.function}`' for use in by_id.get(entry.id, []) if use.marker == 'covers')
        files = ', '.join(f'`{name}`' for name in entry.fix_tests)
        rows = [(entry.id, entry.resolution)] if entry.status == 'fixed' else \
            [(f'{entry.id} [{facet}]', resolution) for facet, status, resolution in entry.facet_status
             if status == 'fixed']
        for label, resolution in rows:
            out.append(f'| [{label}](#{entry.id.lower()}) | {_cell(resolution.split(" ", 1)[0])} | {guards} | '
                       f'{files} |')
    out.append('')
    for entry in fixed_entries:
        if entry.status == 'fixed':
            out.extend(_entry_section(entry, by_id.get(entry.id, [])))
    out.append('## Accepted by the owner')
    out.append('')
    out.append('Behaviour the owner decided to keep; a CHARACTERIZATION test pins it.')
    out.append('')
    for entry in accepted_entries:
        out.extend(_entry_section(entry, by_id.get(entry.id, [])))
    out.append('## Observations not registered')
    out.append('')
    out.append('Raised by the area reviews; they have no registry id and no canonical test (owner decision).')
    out.append('')
    for title, text, source in OBSERVATIONS:
        out.append(f'- **{_one_line(title)}** ({source}): {_one_line(text)}')
    out.append('')
    return '\n'.join(out)


def _entry_section(entry, uses):
    lines = [f'### {entry.id}', '', f'**{_one_line(entry.title)}**', '']
    confidence = entry.confidence
    if entry.facet_confidence:
        confidence += ' (' + ', '.join(f'facet {facet}: {value}' for facet, value in entry.facet_confidence) + ')'
    area = AREAS[entry.owner_area]
    lines += [
        f'- Severity: {entry.severity}',
        f'- Confidence: {confidence}',
        f'- Reachability: {_one_line(entry.reachability)}',
        f'- Location: {_one_line(entry.location)}',
        f'- Evidence that would settle it: {_one_line(entry.settle_evidence)}',
        f'- Owner area: {entry.owner_area} ({_one_line(area.name)})',
        f'- Source findings: {", ".join(entry.source_findings)}',
    ]
    if entry.status != 'open':
        lines.append(f'- Status: {entry.status}: {_one_line(entry.resolution)}')
    for facet, status, resolution in entry.facet_status:
        lines.append(f'- Facet `{facet}`: {status}: {_one_line(resolution)}')
    for facet, engines in entry.engines:
        where = 'every facet' if facet == '*' else ('the entry' if facet is None else f'facet `{facet}`')
        lines.append(f'- Engine scope: {where} reproduces only on {" and ".join(engines)} '
                     '(gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)')
    if entry.gppl:
        lines.append(f'- GPPL engine: {_one_line(entry.gppl)}')
    if entry.fix_tests:
        lines.append(f'- Tests of the fix: {", ".join(entry.fix_tests)}')
    canonical = [use for use in uses if use.marker == 'known_defect']
    pins = [use for use in uses if use.marker == 'covers']
    if canonical:
        lines.append('- Reproduced by:')
        for use in canonical:
            facet = f' (facet `{use.facet}`, confidence {entry.confidence_for(use.facet)})' if use.facet else ''
            lines.append(f'  - `{use.test}`{facet}')
    elif entry.status == 'fixed':
        lines.append('- Reproduced by: none (fixed; the regression guards are listed below)')
    elif entry.status == 'accepted':
        lines.append('- Reproduced by: none (accepted by the owner; pinned by the CHARACTERIZATION test below)')
    elif entry.kind == 'design':
        lines.append('- Reproduced by: none (owner decision; pinned by the CHARACTERIZATION test below)')
    elif entry.kind == 'engine':
        lines.append('- Reproduced by: none (an unverified engine rule; pinned by the CHARACTERIZATION tests below)')
    else:
        lines.append('- Reproduced by: none (current output is safe or the path is disabled; pinned by the test '
                     'below)')
    if pins:
        label = 'Guarded by (`@covers`)' if entry.status == 'fixed' else 'Pinned or exercised by (`@covers`)'
        lines.append(f'- {label}:')
        for use in pins:
            lines.append(f'  - `{use.test}`')
    lines.append('')
    return lines
