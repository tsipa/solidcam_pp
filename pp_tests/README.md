# Offline postprocessor tests

Python 3.10+; standard library only; no SolidCAM, Vericut or network needed. Run
from the repository root. There are two suites:

- `tests/` tests the post `Gmill_540v_4x.gpp` (and the VMID/Vericut files next to it);
- `tests_engine/` tests the GPPL engine in `pp_tests/gppl` that runs the post.

Linux / macOS:

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests_engine -v
```

Windows (PowerShell):

```powershell
py -m unittest discover -s tests -v
py -m unittest discover -s tests_engine -v
```

The post tests load the actual `.gpp` on every run (one cached parse per process).
They execute its procedures rather than a Python translation of them. To test
another copy, point `PP_TEST_SOURCE` at it (the VMID is looked up next to that file
first):

```sh
PP_TEST_SOURCE=/path/to/candidate.gpp python3 -m unittest discover -s tests
```

```powershell
$env:PP_TEST_SOURCE = 'C:\path\candidate.gpp'
py -m unittest discover -s tests
```

## Engines

`pp_tests/engine.py` is a shim over the `pp_tests/gppl/` package (design and
semantics in [DESIGN.md](DESIGN.md)). Two engines run the same post tests:

- the GPPL engine (default): `pp_tests/gppl`. Unverified GPPL semantics are
  policies (`GPPL_POLICY`, see DESIGN.md); the default preset reproduces the
  original engine where it had a behaviour. It also models what the original engine
  rejected: `input` stops the post (`PostprocessorStopped`), `abort` raises
  `PostAbort`, and `engine.nc_lines()` / `nc_text()` apply GPPL's one-shot
  `skipline` joining to the NC stream.
- the original engine: `GPPL_ENGINE=legacy` selects `pp_tests/gppl/legacy.py`.

```sh
GPPL_ENGINE=legacy python3 -m unittest discover -s tests
```

```powershell
$env:GPPL_ENGINE = 'legacy'; py -m unittest discover -s tests
```

The test support code works on both engines. `support.engines.GpplCompatEngine` is
the engine the isolated procedure tests use: on the GPPL engine it is an `Engine`
with policies that match the documented workarounds (`print_stmt=console`,
`trace_stmt=ignore`, `string_index=clamp`, extended formats, typed default formats,
`skipline=join_next_nb` when a test opts in); on the legacy engine it is
`support.legacy_compat.LegacyCompatEngine`, the original text-rewriting workaround
class. Tests that need the NC stream or the stop/abort model
(`tests/program_session.py` and the files that use it) skip on the legacy engine
with "needs the default GPPL engine". `tests_engine/` tests the GPPL engine itself
and is skipped as a whole under `GPPL_ENGINE=legacy`.

Whole programs outside the tests: `python -m pp_tests.gppl replay <post.gpp>
<session.json> --vmid <post.vmid>` replays a recorded or synthetic session (fixtures
in `tests_engine/fixtures/`), and `python -m pp_tests.gppl validate <post.gpp> --vmid
<post.vmid> --strict` checks the whole post statically.

## Post test suite (`tests/`)

### Running and reading the result

The default run has 441 tests, takes about 40 s and must end `OK`. Its 73 skips
have two causes:

- `known defect PP-xxx reproduced: ...` (71 tests). Each open suspected defect has
  one canonical test per facet that asserts the correct behaviour; while the defect
  exists the test is reported as a skip. If the behaviour changes so that the test
  passes, the default run FAILS with `PP-xxx no longer reproduces: update the registry
  and remove the marker`, so a silent fix or a change of behaviour is never missed.
- `Mach3 post not available` (2 tests): the `mach3/4x` submodule is not
  initialised. Set `MACH3_PP_SOURCE` to the 6efcad8 Mach3 post (`git show
  6efcad8:mach3/4x/Mach3_4X_Y.gpp > mach3.gpp`) to run them.

With `GPPL_ENGINE=legacy` the run takes about 2.5 minutes and has 87 skips: 77 known
defects (seven ENGINE facets reproduce only on the legacy engine, ENGINE-021 only on
the default engine), 8 tests that need the default engine and the 2 Mach3 tests.

Strict mode runs every open known-defect test as a plain test, so they fail red
while the defects exist. It is meant for working on a defect, not for the green
build:

```sh
PP_STRICT_KNOWN_DEFECTS=1 python3 -m unittest discover -s tests
```

```powershell
$env:PP_STRICT_KNOWN_DEFECTS = '1'; py -m unittest discover -s tests
```

The expected strict result is exactly 71 failures on the default engine and 77 on
the legacy engine, all AssertionError, no errors (one more with `MACH3_PP_SOURCE`
set: PP-058). A known-defect test whose entry does not reproduce on the running
engine (an ENGINE gap of the other engine) runs as a plain passing test. Select
single tests with `-k`, for example `python3 -m unittest discover -s tests -k
test_program_start_forces_dc`.

### Layout

| file | scope |
| --- | --- |
| `test_session_program.py`, `test_toolchange_session.py` | program start/end, header, tool list and WORKPIECE, init_post session, tool change, coolant, M00/M01 stops, HSM, homing strings |
| `test_rotary.py`, `test_offline.py`, `test_rotary_modulo_range.py`, `test_move_4x_axial_x.py` | A-axis position/direction/output, modulo range and full-turn stop, iR1dir, index direction, move_4x, bLimit_3axis, home_data; recorded Slide angles |
| `test_indexing_link.py`, `test_work_offsets_fixtures.py`, `test_motion.py`, `test_arc_link_boundary.py` | indexing, the CAM-link state machine, work offsets; recorded shit2 link |
| `test_unsupported_features.py` | the POST ERROR stops for template features of other controls: multiple fixtures, the trig-macro index mode, subprograms, loops, reference point changes |
| `test_motion_rapids.py`, `test_post_homing_reposition.py`, `test_job_start_climb.py`, `test_inverse_time_feed.py` | rapids and approach order, return after post-inserted homing, the first-rapid climb, feed emulation, Z precision, G93 inverse-time feed |
| `test_arc_compensation_plane.py`, `test_cutter_compensation.py`, `test_job_plane_restore.py`, `test_zx_arc_guard.py`, `test_arcs.py` | arcs, the ZX-arc stop, cutter compensation, machining plane |
| `test_cycles_spindle.py`, `test_tapping_direction.py`, `test_history_regressions.py` | CYCLE81-86, MCALL cancel, tapping, spindle start and dwell; historical fixture cases |
| `test_engine_harness.py`, `test_gpp_static.py`, `test_contracts.py`, `test_machine_definition.py`, `test_mach3_feed_force.py` | engine gaps and the compatibility engine, static GPP checks, trace/fixture contracts, VMID/Vericut contracts, Mach3 |
| `test_known_defect_registry.py` | meta-tests for the registry, the markers and `PP_FINDINGS.md` |

The files `test_cutter_compensation.py`, `test_inverse_time_feed.py`,
`test_job_plane_restore.py`, `test_job_start_climb.py`, `test_move_4x_axial_x.py`,
`test_post_homing_reposition.py`, `test_rotary_modulo_range.py`,
`test_tapping_direction.py` and `test_zx_arc_guard.py` came with the owner's fixes;
they build whole programs with `tests/program_session.py`.

`tests/support/` is a shared package with no tests in it:

- `session.Session` builds a realistic program from SolidCAM-like events: it runs
  the GPP's own `@init_post`, VMID defaults and `@start_of_file` (or its state part),
  then events such as `first_tool()`, `next_tool()`, `same_tool_job()`, `cut()` or
  `ev('drill', ...)`. `Session.segment()`, `replay_tail()`, `event_replay()` and
  `fork()` inspect or copy it.
- `nc.parse_blocks()` parses NC text into blocks and words (`Block.has('X', 15)`
  never matches `X150`; `Block.rotary('A')`, `.cycle`, `.homing_axes`), and
  `nc.arc_sweep_degrees()` / `arc_center()` give the Sinumerik arc geometry.
- `modal.replay()` replays Sinumerik modal state (motion, plane, TRC, work offset,
  distance and feed mode, feed, spindle, coolant, tool, A, homed axes, MCALL) for
  oracles such as "coolant is on at the first cut".
- `engines` selects the engine: `GpplCompatEngine` (above), `fresh_engine()` (a new
  engine on the tested GPP; cached parse), `fork_engine()` and `nc_text()`.
  `ENGINE_NAME` is `gppl` or `legacy`.
- `mutation.mutate()` / `assert_detected(match=)` prove that a guard fails with an
  AssertionError when the GPP behaviour it protects is changed in memory.
- `defects.REGISTRY` is the registry; `markers.known_defect` / `covers` reference it.

### Known defects and the registry

`tests/support/defects.py` registers every suspected postprocessor defect (PP-xxx),
engine gap (ENGINE-xxx) and open design question (DESIGN-xxx) with severity,
reachability, confidence, location, the evidence that would settle it, the owning
test area and a status:

- `open`: the defect exists. `@known_defect('PP-002', facet='negative-mode',
  match=...)` marks the ONE canonical test of each open facet. The test asserts the
  correct behaviour with an independent oracle; with `match=` only the targeted
  assertion counts as reproducing the defect, and any other exception (engine gap,
  KeyError) is a real error.
- `fixed`: an owner commit fixed it. The entry names the fixing commit and the test
  files that came with the fix; the former canonical test asserts the fixed
  behaviour and carries `@covers(id)` as its regression guard. Facets can be fixed
  one at a time (PP-002: `rounding` and `whole-turn` fixed, `negative-mode` open).
- `accepted`: the owner accepted the behaviour (PP-008, M7 for 30 bar); a
  CHARACTERIZATION test pins it.
- DESIGN entries are owner decisions: pinned with `@covers` CHARACTERIZATION tests,
  never `@known_defect`. ENGINE entries can be scoped to one engine: on the other
  engine their test is a plain guard.

Current state: PP 58 entries (48 open, PP-002 partly fixed; 9 fixed; 1 accepted),
ENGINE 21 open (7 reproduce only on the legacy engine, 1 only on the GPPL engine),
DESIGN 7 (1 fixed by an owner decision). [`tests/PP_FINDINGS.md`](../tests/PP_FINDINGS.md)
is generated from the registry and the markers: summary, index of open entries, per
id the details and the reproducing test, and the sections Fixed (id, fixing commit,
guard, tests of the fix) and Accepted. Regenerate it after a registry or marker
change with `python -m pp_tests.tools.findings --write`; the meta-test and CI fail
when it is stale.

The meta-test `tests/test_known_defect_registry.py` enforces the rules: registered
ids only, exactly one canonical test per open facet, `@known_defect` only on open
entries, fixed entries name their commit, no `subTest` inside marked tests, every
test docstring states its oracle (`INDEPENDENT` with a source such as the Sinumerik
828D manual, geometry or commit intent, or `CHARACTERIZATION` for an intentional
current behaviour that is not a registered defect), `UNVERIFIED` where the result
rests on an unverified SolidCAM/GPPL semantic, and every entry of an area is
referenced.

### What is covered

| measure | original suite | this suite |
| --- | --- | --- |
| tests | 35 | 441, of which 79 are canonical known-defect tests (71 open on the default engine, 77 on the legacy engine, PP-058 needs the Mach3 post) |
| GPP statements executed (`python -m pp_tests.coverage`, default engine) | 36.1% (534/1479) | 88.6% (1513/1708; legacy engine 88.3%) |
| GPP branch outcomes (if/while true and false) | 32.9% (207/630) | 82.1% (591/720; same on the legacy engine) |
| mutation kill rate, 802 mutants over 17 procedures (measured on the `f1803b4` GPP, not re-run) | 45.9% (368) | 62.8% (504) |
| GPP commits whose reversion is detected (`tests/HISTORY_COVERAGE.md`, `e797c18` GPP) | 10 of the 14 whose reverse patch applied (12 not assessable) | 47 of 48 (595df73 changes no output) |

The original-suite figures were measured on the `f1803b4` GPP.

Covered behaviour, in short: realistic multi-job programs from `@init_post` to
`@end_of_file`; program start/end homing and codes, the header, the tool list and
the WORKPIECE blank; tool change ordering (spindle/coolant off, Z retract, M06, D1,
work offset, spindle start) and M00/M01 paths; coolant channels per tool; the A
axis (DC/ACP/ACN selection, modulo range, index direction, initial DC, tool-change
rapids, G93 inverse time); indexing and the CAM-link homing bypass state machine;
work offsets; the stops on unsupported template features; rapids, the return after post-inserted homing,
the first-rapid climb, feed emulation and Z precision; arcs in XY/YZ (DIN sweep
oracle, off-axis centres, CAD mismatch abort) and the ZX stop; cutter compensation
and plane codes; CYCLE81/82/83/84/86 parameters and MCALL cancel; spindle speed
order and ramp dwell; static GPP structure, user options, dead options and
Fanuc-only code; VMID/Vericut contracts; engine gaps and the compatibility engine.
Many guards have in-memory reversion checks that must fail with AssertionError; not
every guard has one.

### Coverage tool

```sh
python3 -m pp_tests.coverage --md coverage.md --json coverage.json
GPPL_ENGINE=legacy python3 -m pp_tests.coverage --md coverage.md
```

It runs the post suite in-process and records which GPP statements and branch
outcomes run. On the default engine it hooks the engine's coverage factory
(`pp_tests/gppl/coverage.py`); with `GPPL_ENGINE=legacy` it uses `sys.settrace` on
the frames of the legacy `Engine.call`. Both modes count over the same procedure
view, so their numbers are comparable; neither engine is modified. Only engines
running the tested GPP text count (procedures changed by in-memory mutants are
ignored), and procedures whose `Print` lines `tests/program_session.py` rewrites do
not count from those runs. The report lists per procedure the executed statements,
the branch outcomes, the statements never executed and the conditions evaluated one
way only. `-k PATTERN` restricts the tests, `--fail-under PCT` turns it into a gate.

### Mutation and revert-matrix tools

```sh
python3 -m pp_tests.tools.mutation --jobs 32 --out mutation.json
python3 -m pp_tests.tools.revert_matrix --md revert_matrix.md
```

`mutation` applies the TSR-20 operators (relational, logical, negation, arithmetic,
unary minus, constant, boolean, statement deletion) to 17 procedures, runs the whole
suite per mutant in a subprocess and classifies KILLED / STATIC_ONLY / ERROR_ONLY /
SURVIVED (`--sample N` for a quick run, `--compare old.json` to diff two runs).
`revert_matrix` reverse-applies every historical GPP commit to the current GPP and
runs the suite; when the patch no longer applies it runs the hand-crafted reversion
tests that name the commit (details in `tests/HISTORY_COVERAGE.md`).
Both use the engine selected by `GPPL_ENGINE` and need only the standard library;
the revert matrix also needs `git` and the repository history.

### Continuous integration

`.github/workflows/tests.yml` runs the post suite and `tests_engine` on
ubuntu-latest and windows-latest with Python 3.10 and 3.12 and checks that
`PP_FINDINGS.md` is current. A second job runs the post suite with
`GPPL_ENGINE=legacy`. A strict job (`PP_STRICT_KNOWN_DEFECTS=1`) is allowed to fail:
it shows the open defects as red tests.

### Honest limits

- Both engines are partial GPPL interpreters. Their gaps are registered as
  ENGINE-001..021, scoped to the engine that has them; the compatibility engine
  works around the ones that block execution, and each workaround or policy encodes
  an assumption (for example that `Print` writes to a message window and generation
  continues).
- The change-flag rule for assignments of an unchanged value is unverified
  (ENGINE-001). Sessions clear all flags after initialisation by default; results
  that differ under the persisting policy are marked (PP-054).
- Most tests read `engine.output`, the list of fragments, which never applies
  `skipline` joining. Only `nc_lines()` / `nc_text()` on the default engine join
  blocks (the legacy engine never does, ENGINE-002), so block boundaries after
  `skipline = false` are certified only by the tests that read the NC stream.
- Event sequences are synthetic. Only the Slide rotary angles and the shit2 CAM link
  come from real SolidCAM traces; event order around compensation, `@move_4x`,
  `@machine_plane`, coolant and apos carry-over between jobs is assumed, and the
  tests that depend on such an assumption say UNVERIFIED (registry confidence
  `uncertain`).
- No controller, Vericut, collision or clearance-distance simulation. Oracles for
  828D behaviour come from the programming manual and the repository's Vericut
  control, not from a machine.
- Whitespace of rendered blocks is pinned only as CHARACTERIZATION of the engine's
  nb/nl rendering.
- Surviving mutants (f1803b4 run): 256 of 802. Large groups were `@start_of_job`
  (loop and subroutine branches disabled by the VMID), the `@usr_arc` iArcmode 1/3/4
  branches (deliberately not pinned, because their output is the registered defect
  PP-022) and parts of `@usr_r1pos_calc` (whole-turn handling, since rewritten by
  6228b3d). The owner's fixes changed those procedures; the mutation run has not
  been repeated on the current GPP.
- Still not executed: `@loop_matrix_info`, `@offset_change` and
  `@usr_homenumber_output` (dormant or disabled by the VMID). The Fanuc template
  paths (subprogram output, loops, multiple-fixture files, the trig macro, G10) were
  removed in the refactor; their events and settings stop the post with a POST ERROR.
  `@usr_heightcomp_on/off` were deleted in the refactor.

## Recording fixtures

SolidCAM is needed only to generate a GPPL debug trace. A plain MPF containing
only NC output cannot recover the original CAM event inputs. The supplied Slide
MPF contains `(1)@line_5x ==> ...` events, `..>` parameter continuations, nested
PP calls and generated NC fragments. This is enough to extract portable inputs.

```powershell
python -m pp_tests capture 'Z:\gcodes\Slide\shit.mpf' tests/fixtures/slide_rotary.json --rotary
```

`--rotary` records only six numeric rotary input fields, event ordinals and
the expected A angle observed in the trace output. It removes paths, account
names, dates, part names, comments and other strings. Geometry/angles themselves
are retained: this is identity sanitization, not geometry anonymization.
The network drive and SolidCAM are unnecessary after capture.

Expected angles come from recorded NC output, not the interpreter being tested.
Capture assumes zero transform/coordinate angles until corresponding trace
parameters appear, carries those values across events, and uses the post's
positive-angle configuration with `iR1dir=-1`. This is a focused rotary fixture,
not an assertion that arbitrary trace sessions can be replayed from zero state.
Review regenerated fixtures: updating a baseline must be intentional.

Without `--rotary`, capture preserves all public input events and change flags
in JSON and redacts string values except a small enum allowlist. That export is
input data for future broader replay; redacted string inputs cannot reproduce
headers and names verbatim. Nested calls are not input events. The sanitizer
currently also redacts enum inputs that drive the CAM-link homing bypass
(ENGINE-017), and nested-call lines are treated as NC output (ENGINE-016); check
both before importing a new trace.

## Interpreter coverage

Supported: procedures/parameterized calls, case-insensitive identifiers,
numeric/string/logical assignments, scoped declarations, nested if/else and
bounded while loops, arithmetic/comparisons/boolean logic, degree-based sin/cos,
`abs`, strlen/instr/left/substr/tonum, explicit `change(variable)` flags,
assignment-driven changes, optional modal output groups and simple numeric
precision descriptors. `clear_change_after_gen=1` clears emitted change flags.
Expressions use a restricted AST walker, never Python `eval`. Missing variables,
unknown statements and unsupported expressions fail with procedure/source line.
With the default engine `input` stops (or, with policy `input_stmt=scripted`,
answers and continues) and `abort` raises `PostAbort`; the legacy engine fails at
both. The default engine replays whole sessions (`start_of_file` to `end_of_file`)
from JSON event streams; file operations, formatting modifiers and built-ins are
covered as DESIGN.md lists. `tests/support/engines.py` adapts either engine for the
post tests without changing `pp_tests/gppl` (see Engines).

Fixture files: `ambiguous_arcs.json` supplies hand-authored XY/YZ arcs for the
shipped `iArcmode=2` (minor/major arcs sharing endpoints, both semicircle
directions, 179.999/180/180.001 degrees, nonzero centres, CAD endpoint roundoff and
mismatch errors); ZX arcs stop the post (PP-003, fixed in 5408e5c) and the Fanuc arc
modes live only in the PP-022 tests. `motion_sequences.json` exercises the
rapid/line procedures, the homing-string parser and indexing with exact word
tokens. `history_regressions.json` holds the historical bug-fix cases
(`tests/HISTORY_COVERAGE.md`). The repeated-G75 defect and its test oracle history
are in [tests/CAM_LINK_POSTMORTEM.md](../tests/CAM_LINK_POSTMORTEM.md); the
cross-procedure arc/link regression in
[tests/ARC_LINK_FINDING.md](../tests/ARC_LINK_FINDING.md).

Numeric output is normalized to the supplied precision, or three decimals by
default (ENGINE-003); padding, trailing dots and exact GPPL whitespace are not
emulated. In `engine.output`, `nb`/`nl` are line breaks; `engine.nc_lines()`
(default engine) applies the `skipline` joining. Unsupported constructs in
unexecuted procedures are allowed; encountering them during execution fails.

## Running a procedure directly

Create JSON with `state` and optional `changed` objects containing explicit
inputs; then run:

```powershell
python -m pp_tests run path/to/post.gpp usr_r1pos_calc inputs.json
```

The command prints resulting state, change flags and generated fragments.
To extend coverage, add a recorded or hand-authored input case and an independent
expected result, then implement any newly reached GPPL construct with harness
tests. Do not silently skip unknown statements or replace missing inputs by zero.
