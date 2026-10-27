# Offline postprocessor tests

Python 3.10+; standard library only. Run from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The tests load the actual `.gpp` on every run. They execute its procedures rather
than a Python translation of the rotary formulas. To test another copy:

```powershell
$env:PP_TEST_SOURCE = 'C:\path\candidate.gpp'
python -m unittest discover -s tests -v
```

## Engine

`pp_tests/engine.py` is a shim over the `pp_tests/gppl/` package (design and
semantics in [DESIGN.md](DESIGN.md)). `GPPL_ENGINE=legacy` runs the original
engine (`pp_tests/gppl/legacy.py`) with the same tests. Unverified GPPL semantics
are policies (`GPPL_POLICY`, see DESIGN.md); the default reproduces the original
engine. The engine's own tests:

```powershell
python -m unittest discover -s tests_engine -v
```

Whole programs: `tests/program_session.py` drives init_post, tool changes and
CAM events through the real post for tests; `python -m pp_tests.gppl replay
<post.gpp> <session.json> --vmid <post.vmid>` replays a recorded or synthetic
session (fixtures in `tests_engine/fixtures/`), and `python -m pp_tests.gppl
validate <post.gpp> --vmid <post.vmid> --strict` checks the whole post statically.

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
headers and names verbatim. Nested calls are not input events.

## Interpreter coverage

Supported: procedures/parameterized calls, case-insensitive identifiers,
numeric/string/logical assignments, scoped declarations, nested if/else and
bounded while loops, arithmetic/comparisons/boolean logic, degree-based sin/cos,
`abs`, strlen/instr/left/substr/tonum, explicit `change(variable)` flags,
assignment-driven changes, optional modal output groups and simple numeric
precision descriptors. `clear_change_after_gen=1` clears emitted change flags.
Expressions use a restricted AST
walker, never Python `eval`. Missing variables, unknown statements and unsupported
expressions fail with procedure/source line. With the default engine `input` stops
(or, with policy `input_stmt=scripted`, answers and continues) and `abort` raises
`PostAbort`; the legacy engine fails at both.

The acceptance suite covers `usr_ip_useroptions`, `usr_r1pos_calc`,
`usr_r1_select_dir`, `usr_r1_output` and `tmatrix`: positive/negative/direct
angles and boundaries, combined rotations, first DC output, ACP/ACN direction,
unchanged positions, 3-axis flags, clearance invalidation, recorded Slide
angles and a source-mutation check proving results depend on the GPP source.

`ambiguous_arcs.json` supplies hand-authored endpoints for minor/major arcs
sharing endpoints, both semicircle directions, 179.999/180/180.001 degrees,
359.999 versus 360, nonzero centers, CAD endpoint roundoff and mismatch errors.
Cases run in XY/ZX/YZ and modes 1..4 through the actual `arc*` entrypoints,
`usr_arc_math`, parameterized mismatch check and `usr_arc` output. They assert
the emitted G2/G3, G17/G18/G19, XYZ, feed and signed R versus absolute/relative
IJK. Orthogonal helical endpoints are preserved. Boundary checks cover each
axis at exactly 0.001 and either side. Plane orientation expectations capture
the current source formulas; they do not independently certify controller
conventions.

`motion_sequences.json` exercises the actual rapid/line procedures, homing-string
parser and indexing, including `end_of_job → tmatrix → start_of_job → move_5x`.
It checks first-move NC block order, forced DC after tool change, indexing
clearance modes and offsets, CW/CCW changes inside a job, unchanged rotary
positions, contiguous CAM-link retract authorization, split XYZ/rotary rapids and
invalidation by diagonal cutting, non-link feed, offsets and tmatrix.
The contiguous-link expectation follows the current working PP change; a
subsequent feed event or indexing/job boundary must invalidate authorization.
These fixtures are synthetic and reviewable, not captured machine simulations.

Historical bug-fix fixtures and their commit evidence are documented in
[tests/HISTORY_COVERAGE.md](../tests/HISTORY_COVERAGE.md).
The repeated-G75 defect, the initial incorrect test oracle, and the numeric
second-Slide regression fixture are documented in
[tests/CAM_LINK_POSTMORTEM.md](../tests/CAM_LINK_POSTMORTEM.md).
An additional cross-procedure arc/link regression and its PP correction
are described in [tests/ARC_LINK_FINDING.md](../tests/ARC_LINK_FINDING.md).

This is not a complete SolidCAM emulator. The default engine replays whole
sessions (`start_of_file` to `end_of_file`) from JSON event streams; file
operations, formatting modifiers and built-ins are covered as DESIGN.md lists.
Numeric output is normalized to the supplied simple precision, or three decimals
by default; padding, trailing dots and exact GPPL whitespace are not emulated.
Tests compare normalized blocks and numeric words. Unsupported constructs in
unexecuted procedures are allowed; encountering them during execution fails.
In `engine.output`, `nb`/`nl` are line breaks; `engine.nc_lines()` (default
engine) applies GPPL's one-shot `skipline` joining, which the legacy engine does
not emulate. First-move XY/Z separation was checked against the Slide trace;
arbitrary toolchange/coolant/spindle block joining is not certified.
There is no collision, clearance-distance or machine safety simulation.

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
