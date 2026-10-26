# Regression fixtures from GPP history

Reviewed the complete path-specific `git log --all` and the relevant commit
messages/diffs for `Gmill_540v_4x.gpp`. These are synthetic inputs derived from
recorded bug fixes, not claims that we recovered the original SolidCAM jobs.
The `reason` field in `fixtures/history_regressions.json` distinguishes explicit
commit/source explanations from narrower conclusions supported only by a diff.

Run everything offline:

```powershell
python -m unittest discover -s tests -v
```

Run this historical regression suite alone:

```powershell
python -m unittest discover -s tests -p test_history_regressions.py -v
```

## Added cases

| Fix | Recorded problem and independent oracle | Fixture |
| --- | --- | --- |
| `2aa6df0` | Lookahead changed diameter compensation on the current lead-out/zigzag block. Output must remain G41 until the explicit CAM compensation event, then G42, then G40. | `zigzag_compensation_changes_only_on_cam_event` |
| `719e946` | `angle` was also copied into `apos`, adding the same fourth-axis transform twice. A 90-degree transform must yield A90, not A180, and clear the supplied stale `apos`. | `fourth_axis_transform_angle_is_not_counted_twice` |
| `611b188` | Primary A previously used `bpos`. Distinct inputs `apos=123`, `bpos=17` must produce primary 123 and secondary -17 with current axis signs. | `distinct_apos_and_bpos_map_to_separate_axes` |
| `420c4ab` | Tool offset initialization adds D1 after M06. Check every block including following tool preselection. The commit does not explain the underlying mechanical failure. | `tool_change_selects_d1_before_preselection` |
| `bea8c62` | Correct RFP/SDIS/DP/DPR ordering with a positive reference plane. Cases give independently specified complete positional argument arrays for CYCLE81, CYCLE82 and CYCLE86. | `cycle81_*`, `cycle82_*`, `cycle86_*` |
| `1710187`, clarified by `e4af180` | CYCLE83 upper dwell DTS changes from 1 to 0.5. Verify its exact argument index and every other field for both positive and nonpositive reference-plane branches. | `cycle83_positive_*`, `cycle83_nonpositive_*` |
| `55d9935` | Nonrotary off-center stock was recentered through RECTANGLE. Check BOX with X0/Y0 and incremental extents; separately preserve A-clamped RECTANGLE for rotary stock. | `off_center_stock_*`, `rotary_stock_*` |

All 11 cases execute procedures loaded from the tested `.gpp`, using the same
strict interpreter as the motion/arc suite. Cycle cases execute the real `drill`
entrypoint including its rapid move; no procedures are replaced by Python stubs.
Tool-change, stock and compensation tests inspect actual emitted NC blocks.

## Negative validation

`test_reviewed_historical_code_reversions_are_detected` reverses focused changes
from the reviewed diffs in memory. Ten cases with a historical regression patch
must fail an independent assertion. Interpreter errors do not count as detecting
a regression. The rotary RECTANGLE preservation case has no regression patch:
its purpose is to keep the unaffected branch stable while BOX evolves.

During implementation, each of those ten cases was also executed against the
full real `commit^` GPP obtained through `git show`, without changing any working
file. All ten historical parent versions failed the expected oracle with
`AssertionError`; none required an unsupported-runtime exception to fail.
Those Git reads are a development check only. Normal test runs use the saved
fixtures and current source and do not require Git history or SolidCAM.

## Existing coverage and boundaries

The original suites already cover `dc916d7` mathematical endpoint reconstruction
and mismatch tolerance, ZX I/K selection, CW/CCW/full-circle boundaries;
`c03e1b4` first-index G0; `92e2b23` optional stop; `3696aa2` deferred tmatrix
indexing through `start_of_job`; initial DC versus later directed A output; and
`d5952a2` CAM-link clearance authorization. These were not duplicated here.

Not every commit is a distinct bug fix. Trace switches, comments, tool-list
decoration and end-of-program whitespace do not justify fabricated safety
regressions. Older path renames/removals such as `6294822` also need comparison
across the historical 3x path before assigning a precise behavior claim.

This suite does not yet cover CYCLE84 tapping fields, full start/end-program
sessions, spindle acceleration or every GPPL output-format modifier. No specific
spindle-acceleration fix was identified in the reviewed path history, so no
invented commit-to-bug association was added. Machine/VMID precision and physical
controller plane conventions remain outside this source-level test engine.
