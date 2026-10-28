# Regression coverage of the GPP history

Every commit that changed `Gmill_540v_4x.gpp` (including its older name
`Gmill_540v_3x.gpp`) was reviewed against the suite. This file says, per commit,
which tests guard the change and what happened when it was undone. The fixtures are
synthetic inputs derived from the recorded bug fixes; they are not recovered SolidCAM
jobs. The `reason` field in `fixtures/history_regressions.json` separates explicit
commit/source explanations from narrower conclusions drawn from a diff.

Run everything offline from the repository root (`python3` on Linux/macOS):

```
python -m unittest discover -s tests
```

Run only the legacy historical fixture suite:

```
python -m unittest discover -s tests -p test_history_regressions.py -v
```

Re-run the revert matrix (needs a git clone with history; nothing is modified):

```
python -m pp_tests.tools.revert_matrix --md revert_matrix.md
```

## Revert matrix (all GPP commits)

`pp_tests/tools/revert_matrix.py` takes each commit's GPP change and reverse-applies
it to the current GPP in memory (3 context lines, fuzz up to 3 like `patch -F3`),
then runs the whole suite on the result through `PP_TEST_SOURCE`. Later commits
often rewrote the same lines; then the reverse patch cannot be applied, and the
hand-crafted in-memory reversions in the tests are the evidence instead
(`support.mutation.mutate` + `assert_detected`, or a fixture `regression` patch).
Such a test passes only if every one of its reversions fails an assertion, and it
counts only if it applies a reversion and names the commit (a hash quoted in a
docstring of a test that reverts nothing is not evidence). A FAIL is an
AssertionError; ERRORs (engine gaps, or the `StaleAnchor` of an in-memory mutation
whose anchor the reversion removed) never count as detection.

Measured on the GPP of `0ed0b78` (default engine, 48 commits): **47 of 48 commits
are detected**: 18 by the complete reverse patch, 21 by hand-crafted reversions, 8
by a partial reverse patch. Not detected: `a71e102`, which by design does not change
the output (below). With the original 35-test suite (`revert_matrix.txt` of the
review, 26 commits from e574716 on), 14 reverse patches applied and 4 of those went
undetected (797fc88, e4af180, 961facc, c8b79bd); the 12 others could not be applied
and were not assessed. The mutation figures in `pp_tests/README.md` were measured on
the `f1803b4` GPP and were not re-run.

### Commits before the review fixes

| commit | subject | kind | reverse patch on HEAD | guarded by | verdict |
| --- | --- | --- | --- | --- | --- |
| `f1803b4` | Add offline GPPL regression tests and refresh arc link tracking | bug fix | applied; 4 FAIL | `test_arc_link_boundary.py` (an arc revokes the link and tracks Z and offset), `test_motion.py` descending link after an arc, `test_indexing_link.py::CamLinkTransitionTests.test_arc_in_any_plane_revokes_and_tracks_endpoint` | detected (reverse patch) |
| `37ab3b9` | Preserve CAM link clearance across consecutive rotary rapids | bug fix | applied; 2 FAIL | `test_motion.py` shit2 contiguous link and recorded sequences, `CamLinkBoundaryTests` | detected (reverse patch) |
| `d5952a2` | Preserve index clearance while skipping homing on confirmed CAM links | bug fix | 4 of 11 hunks no longer apply | `test_indexing_link.py` `CamLink*Tests` and `ReversionDetectionTests` (state-machine reversions), `test_motion.py` one-rotation authorization regression; the partial reversion (7 of 11 hunks) fails 17 tests | detected (hand-crafted) |
| `797fc88` | Add holder name and tool stickout to tool list comments | comment format | applied; 2 FAIL | `test_session_program.py::ToolListTests` (CHARACTERIZATION of the tool-list comment) and `test_tool_list_reversion_797fc88_is_detected` | detected (reverse patch) |
| `55d9935` | Use BOX workpiece for non-rotary stock | bug fix | applied; 2 FAIL | fixture `off_center_stock_*`, `ToolListTests.test_tool_list_trailer_once_after_last_tool` (independent BOX extent oracle) | detected (reverse patch) |
| `e4af180` | Document CYCLE83 dwell parameters | documentation | applied; 1 FAIL | `test_cycles_spindle.py::DrillCycleGeometryTests.test_cycle83_documentation_matches_output` (the comment must describe the posted DTB/DTS/FRF/VARI) | detected (reverse patch) |
| `1710187` | Reduce CYCLE83 upper dwell | behaviour change | applied; 2 FAIL | fixtures `cycle83_*`, the CYCLE83 documentation test | detected (reverse patch) |
| `961facc` | Terminate program end blocks with blank line | whitespace | applied; 4 FAIL | `ProgramEndTests` (CHARACTERIZATION of nb/nl rendering, TSR-16), two-job session test | detected (reverse patch) |
| `a03b38e` | Remove trailing spaces from program end codes | whitespace | no longer applies (961facc rewrote the line) | `ProgramEndTests.test_program_end_regressions_are_detected` (a03b38e mutants for M30 and M2) | detected (hand-crafted) |
| `115bd14` | Emit Sinumerik WORKPIECE stock definition | feature | no longer applies (55d9935 rewrote the block) | `ToolListTests.test_workpiece_reversion_115bd14_is_detected`; the parent GPP also fails (area A check) | detected (hand-crafted) |
| `420c4ab` | Initialize tool offset with D1 | bug fix | applied; 5 FAIL | fixture `tool_change_selects_d1_before_preselection`, `ToolChangeSequenceTests` (D1 before the first motion), tool-change session tests | detected (reverse patch) |
| `2aa6df0` | Fix diameter compensation lookahead in zigzag profile | bug fix | applied; 1 FAIL, 55 ERROR | fixture `zigzag_compensation_changes_only_on_cam_event` (AssertionError); the errors come from the restored lookahead reading CAM inputs the harness does not supply | detected (reverse patch) |
| `bea8c62` | Fix Sinumerik drill cycle parameters | bug fix | 1 of 4 hunks no longer applies (1710187 changed CYCLE83) | fixture regression patches for CYCLE81/82/83 (3 anchor occurrences) and CYCLE86, `RigidTappingTests.test_bea8c62_cycle84_reversion_is_detected`, the cycle geometry guard | detected (hand-crafted) |
| `719e946` | Avoid double-counting fourth-axis index angle | bug fix | applied; 4 FAIL | fixture `fourth_axis_transform_angle_is_not_counted_twice`, `FourthAxisIndexTests.test_fourth_axis_emits_single_index_word` | detected (reverse patch) |
| `ad2537a` | Force initial A-axis DC output | bug fix | applied; 7 FAIL | `test_rotary.py::RotaryRegressionTests.test_program_start_forces_dc`, `test_session_program.py` init_post and two-job tests, `test_offline.py` first rotation | detected (reverse patch) |
| `c8b79bd` | Disable postprocessor trace | configuration | applied; 1 FAIL (static), 45 ERROR | `test_gpp_static.py::StaticSourceTests` (no active trace; `test_c8b79bd_reversion_is_detected`); the errors are tests that build an engine without the trace workaround: both engines reject `trace` by default (ENGINE-018; GPPL engine policy `trace_stmt=error`) | detected (hand-crafted; static guard) |
| `ab853be` | Initialize A-axis with DC output | bug fix | 1 of 5 hunks no longer applies (ad2537a rewrote it) | `test_rotary.py` REVERSIONS (`ab853be` init DC), the initial-DC mutants of the init_post and two-job session tests; the parent GPP fails with AssertionError (area A check) | detected (hand-crafted) |
| `bff5ed0` | Force explicit A-axis direction output | bug fix | 9 of 17 hunks no longer apply | `test_rotary.py` REVERSIONS (six bff5ed0 entries: plain A, dropped A, swapped index words, index uses dir5a, wrappers keep bR1useDir5a, unknown dir5a defaults to ACP), the half-turn and index-direction guards | detected (hand-crafted) |
| `8966d35` | Guard ambiguous A-axis modulo moves | bug fix | no longer applies (bff5ed0 deliberately replaced the GPP guard) | `test_rotary.py` half-turn guard and its `8966d35` entry (labelled a mutation: `8966d35^` posted a plain A180, not DC); the .ctl half by `test_machine_definition.py` (below) | detected (hand-crafted) |
| `611b188` | Fix A-axis output for 5x rotary moves | bug fix | 1 of 3 hunks no longer applies | fixture `distinct_apos_and_bpos_map_to_separate_axes` (its regression patch swaps apos/bpos) | detected (hand-crafted) |
| `3696aa2` | Defer tmatrix index moves until work offset is set | bug fix | 1 of 5 hunks no longer applies (the review fixes rewrote the index path); the partial reversion fails 15 tests | `IndexHistoryTests.test_first_program_index_is_explicit_rapid_with_resolved_offset` and `test_index_after_feed_moves_is_rapid_and_states_work_offset`, `ReversionDetectionTests` | detected (hand-crafted) |
| `8d6b044` | Fix 4-axis indexing from SolidCAM tmatrix | bug fix | applied; 1 FAIL, 288 ERROR | `IndexHistoryTests.test_tmatrix_index_uses_angle_4x_around_x`; the errors come from the old formula reading inputs the harness does not supply | detected (reverse patch) |
| `92e2b23` | Add optional stop before 4th-axis index moves | safety feature | no longer applies (later index fixes rewrote the line) | the `92e2b23` reversion (no M1) in `test_indexing_link.py` (two tests) | detected (hand-crafted) |
| `c03e1b4` | Fix missing G0 on first 4th-axis index move | bug fix | 1 of 3 hunks no longer applies | `test_indexing_link.py` reversions `iMotionmode 9999 -> 0` and `nR1pos_f 7.3 -> 7.1`, the two-job session mutation; the parent GPP needs CAM variables a Session does not supply, so the hand-crafted reversion is the evidence (area A check) | detected (hand-crafted) |
| `dc916d7` | Arcs must be handled mathematically in post | bug fix | 3 of 4 hunks no longer apply | `test_arc_compensation_plane.py::ArcGuardTests` (19 arc-math mutants including the dc916d7 ZX K-word and precision reversions), `test_arcs.py` mismatch tests; the VMID half by the precision pins (below) | detected (hand-crafted) |
| `e574716` | Fix indexing | bug fix | applied; 53 FAIL (2 more static) | `FourthAxisIndexTests.test_default_indexing_is_simple_rotation`, `test_fourth_axis_emits_single_index_word`, the CAM-link state-machine tests | detected (reverse patch) |
| `21a6334` | Add machsim (output precision 5.4 -> 5.3, end-of-program XY homing) | mixed | the precision hunk no longer applies (dc916d7 later set 8.5) | the partial reversion (end homing back to Z only) fails the program-end tests; the superseded precision is guarded at its current value by the VMID precision pins | detected (partial reverse patch) |
| `77c03c6` | Remove extra rotation. (HVV macro, Z inversion and CTRANS frame commented out) | bug fix | 1 of 2 hunks no longer applies | `test_rotary.py` REVERSIONS (77c03c6 CTRANS frames, HVV macro, Z inversion), `test_home_data_writes_no_frames`, the DESIGN-007 pin | detected (hand-crafted) |

### Review fixes (f1803b4..0ed0b78)

The rows name the registry entry a commit fixed (`tests/PP_FINDINGS.md`, section
Fixed) where there is one. Most of these commits came with their own test file;
those files are part of the suite unchanged.

| commit | subject | registry | reverse patch on HEAD | guarded by | verdict |
| --- | --- | --- | --- | --- | --- |
| `345cb49` | Reprogram X, Y and Z after post-inserted homing | PP-001 | 3 of 5 hunks no longer apply; the partial reversion fails 16 tests | `test_post_homing_reposition.py`, `test_motion_rapids.py` X/Y re-establishment after homing | detected (partial reverse patch) |
| `3e0c345` | Split XY and Z when returning from post-inserted homing | DESIGN-002 | 1 of 3 hunks no longer applies; the partial reversion only errors | `ApproachAfterHomingTests.test_3e0c345_reversion_is_detected` (Z back on the XY block), `test_post_homing_reposition.py` | detected (hand-crafted) |
| `49f8b80` | Climb before traversing on a job's first rapid | PP-013 | 2 of 9 hunks no longer apply; the partial reversion fails 12 tests | `test_job_start_climb.py`, `test_cutter_compensation.py` climb tests | detected (partial reverse patch) |
| `5408e5c` | Stop the post on ZX (G18) arcs | PP-003 | 1 of 2 hunks no longer applies | `PostAbortGuardTests.test_guard_detects_removed_abort` (the ZX abort site), `test_zx_arc_guard.py`, the PP-003 stop test in `test_arc_compensation_plane.py` | detected (hand-crafted) |
| `b999f65` | Switch cutter compensation only on linear blocks | PP-019, PP-020 | 2 of 5 hunks no longer apply; the partial reversion fails 19 tests | `PostAbortGuardTests.test_guard_detects_removed_abort` (the TRC-on-arc abort site), the TRC tests in `test_arc_compensation_plane.py` and `test_cutter_compensation.py` | detected (hand-crafted) |
| `88695c9` | Restore the machining plane at the start of each job | PP-021 | no longer applies (7aeae99 rewrote the call) | `PlaneModalityTests.test_88695c9_reversion_is_detected` (drill cycle after a YZ arc), `test_job_plane_restore.py` | detected (hand-crafted) |
| `a38f158` | Post left-hand tapping with a negative CYCLE84 pitch | PP-028 | no longer applies (a71e102 rewrote the line) | `RigidTappingTests.test_a38f158_reversion_is_detected`, `test_tapping_direction.py` | detected (hand-crafted) |
| `6228b3d` | Keep A positions inside 0 <= A < 360 | PP-002 whole-turn, rounding | no longer applies (c33ebd0 rewrote both blocks) | `FixedRotaryDefectGuards.test_6228b3d_reversion_is_detected` (both PP-002 guards), `test_rotary_modulo_range.py` | detected (hand-crafted) |
| `ca63502` | Post the CAM X in @move_4x | PP-007 | applied; 3 FAIL | `test_move_4x_axial_x.py`, `FixedRotaryDefectGuards.test_move_4x_preserves_axial_x` | detected (reverse patch) |
| `9f48a3a` | Post rotating G1 blocks in G93 inverse time | PP-049 | 3 of 15 hunks no longer apply; the partial reversion fails 1 test (1 more static) | `test_inverse_time_feed.py` (`test_removing_inverse_time_is_detected`) | detected (partial reverse patch) |
| `1bdfecc` | Reprogram F when leaving G93 and use the control's A travel | PP-049 | 2 of 7 hunks no longer apply; the partial reversion fails 9 tests | `test_inverse_time_feed.py` | detected (partial reverse patch) |
| `0cfd586` | Keep the post's cutter compensation state in step with the control | PP-020 | 5 of 11 hunks no longer apply; the partial reversion fails 3 tests | `test_cutter_compensation.py`, `test_arc_compensation_plane.py` TRC tests | detected (partial reverse patch) |
| `3577b70` | Keep explicit Z holds after homing and avoid a diagonal feed from home | PP-001 follow-up | 3 of 5 hunks no longer apply; the partial reversion fails 1 test | `test_job_start_climb.py` (`test_removing_the_climb_branch_is_detected`) | detected (partial reverse patch) |
| `399ef13` | Track the current Z through drill cycles and indexing for the climb | PP-013 follow-up | applied; 5 FAIL | `test_job_start_climb.py` | detected (reverse patch) |
| `7aeae99` | Fall back to G17 at job start and select TRC in the job plane | PP-021 follow-up | 3 of 4 hunks no longer apply; the partial reversion fails 2 tests | `test_job_plane_restore.py` | detected (partial reverse patch) |
| `c33ebd0` | Snap float-noise A positions to 0 and keep the wrap loops simple | PP-002 follow-up | applied; 3 FAIL | `test_rotary_modulo_range.py` | detected (reverse patch) |
| `a71e102` | Write the left-hand tap pitch as a binary minus; plain ZX error text | none | 1 of 2 hunks no longer applies | nothing behavioural: `((0-FEED)/SPIN)` posts the same value as `(-FEED/SPIN)`, and the ZX error text only lost `(G18)` and `@` (the commit's reason is GPPL string and expression syntax, which the engines do not model) | not detected (no output change) |
| `6f6f6ce` | Switch TRC on the retract with explicit X/Y instead of holding it | PP-019, PP-020 | applied; 14 FAIL | `test_cutter_compensation.py`, `test_arc_compensation_plane.py` TRC off-before-rapid guard | detected (reverse patch) |
| `ebf9c57` | Track Z and the feed start through indexes, M00 and subs; stop on full-turn cuts | PP-002 full-turn cut | 1 of 11 hunks no longer applies; the partial reversion fails 3 tests | `PostAbortGuardTests.test_guard_detects_removed_abort` (the full-turn abort site), `test_rotary_modulo_range.py`, `test_job_start_climb.py`, `test_post_homing_reposition.py` | detected (hand-crafted) |
| `0ed0b78` | Write the new POST ERROR texts on their own NC line; harden tests | none | applied; 1 FAIL | `test_zx_arc_guard.py::test_error_text_is_its_own_nc_line_in_a_program` | detected (reverse patch) |

FAIL counts are behavioural tests; the static text checks (`test_gpp_static.py`,
`test_machine_definition.py`) are excluded except where a row says so. Not reverted:
`ffd296c` (initial import) and `6294822` (pure rename, no content change). A partial
reverse patch places only the hunks that still match, so its failure list is
indicative; the verdict prefers the hand-crafted evidence.

### Machine-definition commits

The GPP revert matrix does not see fixes in the VMID and the Vericut files. They
were reverse-applied the same way to scratch copies, with the GPP unchanged:

| commit | file | guard | result |
| --- | --- | --- | --- |
| `5c0271d` | VMID `OutputGcodePartCoordinate`, qwe.mch A link `-X` | `test_5x_callbacks_are_in_part_coordinates`, `test_vericut_a_axis_link_matches_post_rotary_direction` | 2 FAIL |
| `8966d35` | ctl A-axis rotary mode | `test_vericut_absolute_rotary_direction_mode`, `test_vericut_models_a_as_modulo_axis` | 2 FAIL |
| `c85f5f7` | GcodeSim.ini MAC table | `test_vericut_mac_table_matches_post_work_offsets` (PP-050 canonical test, no `match=`): with the reverted table the test passes, so its known-defect marker fails with 'PP-050 no longer reproduces' | 1 FAIL (through the marker) |
| `f88de47` | ctl I/J word format 8.5 | `test_vericut_ij_words_keep_post_precision` (added during integration; K is PP-051) | 1 FAIL |
| `dc916d7` | VMID `RotaryAxisPrecision` | `test_rotary_output_precision_matches_vmid`, `test_vmid_movement_precision_matches_output_decimals` | the hunk no longer applies (5c0271d rewrote the line); the real `dc916d7^` VMID fails both pins (area F check) |
| `9a04de5` | ctl data-format conversion | none | not guarded: a file-format conversion with no behaviour to assert |

The Mach3 fork fix `6efcad8` (feed re-statement) is guarded by
`test_mach3_feed_force.py`: the test passes on the 6efcad8 post and fails on
`ffd296c`. It runs only when `MACH3_PP_SOURCE` names that post (the `mach3/4x`
submodule is not initialised and would point at a different fork revision).

## Fixture cases (`fixtures/history_regressions.json`)

| Fix | Recorded problem and independent oracle | Fixture |
| --- | --- | --- |
| `2aa6df0` | Lookahead changed diameter compensation on the current lead-out/zigzag block. Output must remain G41 until the explicit CAM compensation event, then G42, then G40. | `zigzag_compensation_changes_only_on_cam_event` |
| `719e946` | `angle` was also copied into `apos`, adding the same fourth-axis transform twice. A 90-degree transform must yield A90, not A180, and clear the supplied stale `apos`. | `fourth_axis_transform_angle_is_not_counted_twice` |
| `611b188` | Primary A previously used `bpos`. Distinct inputs `apos=123`, `bpos=17` must produce primary 123 and secondary -17 with current axis signs. | `distinct_apos_and_bpos_map_to_separate_axes` |
| `420c4ab` | Tool offset initialization adds D1 after M06. Check every block including following tool preselection. The commit does not explain the underlying mechanical failure. | `tool_change_selects_d1_before_preselection` |
| `bea8c62` | Correct RFP/SDIS/DP/DPR ordering with a positive reference plane. Cases give independently specified complete positional argument arrays for CYCLE81, CYCLE82 and CYCLE86. | `cycle81_*`, `cycle82_*`, `cycle86_*` |
| `1710187`, clarified by `e4af180` | CYCLE83 upper dwell DTS changes from 1 to 0.5. Verify its exact argument index and every other field except FDPR (index 6, unpinned: PP-055) for both positive and nonpositive reference-plane branches. | `cycle83_positive_*`, `cycle83_nonpositive_*` |
| `55d9935` | Nonrotary off-center stock was recentered through RECTANGLE. Check BOX with X0/Y0 and incremental extents. The 2026-10-27 WORKPIECE change supersedes the old rotary RECTANGLE characterization: A-clamped stock now preserves the same BOX extents. | `off_center_stock_*`, `rotary_stock_*` |

All 11 cases execute procedures loaded from the tested `.gpp` with the same strict
interpreter as the motion/arc suite. Cycle cases execute the real `drill` entry
point including its rapid move; no procedure is replaced by a Python stub.
Tool-change, stock and compensation tests inspect the emitted NC blocks. The cycle
cases pass the CAM inputs of a drilling job (`tool_direction`, `spin`), so a fix of
PP-028 or PP-029 does not turn them into harness errors.

### Negative validation

`test_reviewed_historical_code_reversions_are_detected` reverses focused changes
from the reviewed diffs in memory. Ten cases with a historical regression patch
must fail an independent assertion. Each patch is built with
`support.mutation.mutate`; `regression.count` states how many anchor occurrences
the real commit changed (bea8c62 G81/82/83: 3, 1710187: 2), so a rewritten GPP
raises `StaleAnchor` instead of silently skipping the reversion. Interpreter errors
do not count as detecting a regression. The rotary stock case has
no historical regression patch: its expected geometry was updated to BOX by the
2026-10-27 user requirement. The original RECTANGLE expectation is superseded.

During the original implementation each of those ten cases was also run against the
full real `commit^` GPP from `git show`. All ten parent versions failed the expected
oracle with `AssertionError`. Those Git reads were a development check; normal test
runs use the saved fixtures and the current source and need neither Git history nor
SolidCAM.

## Corrections to earlier claims

An earlier version of this file said the original suites covered `c03e1b4`
(explicit G0 on the first index move), the initial DC output and the whole of
`3696aa2` and `d5952a2`. Measured with the revert matrix and hand-crafted
reversions, that was not true:

- `c03e1b4` was not covered. The legacy `motion_engine()` presets `iMotionmode=1`
  and never runs `@usr_init_gmstates`, and
  `test_index_clearance_modes_and_work_offsets` forces `change(iMotionmode)`, so
  reverting `iMotionmode = 9999` to `0` left every test green (the real first index
  became `G17 G54 G90 A=DC(90)` without G0).
- The initial DC output (`ab853be`, `ad2537a`) was only partly covered. The legacy
  `rotary_engine()` presets `bR1forceOutput=False` and never runs `@init_post`, so
  the start-of-program force was invisible; only the per-call DC selection was
  exercised (the original `ad2537a` reverse patch produced 9 failures through that
  path). `RotaryRegressionTests.test_program_start_forces_dc` and the init_post
  session tests now run the real program start.
- The other half of `3696aa2` (index after `home_number`, forced G54, no `G9999`
  sentinel) and most single rules of the `d5952a2`/`37ab3b9` state machine were
  hidden by the same presets.
- `797fc88`, `e4af180`, `961facc` and `c8b79bd` reverted cleanly without any
  failure.

The canonical tests run on realistic sessions (`support.session.Session`, which
executes `@init_post` and `@usr_init_gmstates`): `test_indexing_link.py` for
`c03e1b4`, `3696aa2`, `92e2b23`, `8d6b044`, `e574716`, `719e946` and the CAM-link
commits; `test_rotary.py` for the A-axis commits; `test_session_program.py` and
`test_toolchange_session.py` for program start and end, the tool list, WORKPIECE
and D1; `test_cycles_spindle.py` for the drill cycles (CYCLE84 tapping fields
including the bea8c62 CYCLE84 hunk, the MCALL cancel, spindle start and
acceleration); `test_arc_compensation_plane.py` for `dc916d7`.

## Boundaries

Not every commit is a distinct bug fix. Trace switches, comments, tool-list
decoration and end-of-program whitespace are pinned as CHARACTERIZATION or static
checks, not as safety regressions. No specific spindle-acceleration fix was found
in the path history, so no commit-to-bug association was invented for it. Physical
controller behaviour (plane conventions on the machine, the 828D alarm set, how
Vericut interprets word formats) stays outside this source-level engine; the open
questions are registered in `tests/PP_FINDINGS.md`.
