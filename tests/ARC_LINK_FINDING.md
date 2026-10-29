# Arc endpoint tracking and CAM-link authorization

The additional critic pass found a cross-procedure state gap in the current PP.
`usr_line` and `usr_rapid` update `nLastPathZ`; `usr_arc` does not. The tests in
`test_arc_link_boundary.py` are ordinary regression tests. They initially failed
on the old PP and now pass after endpoint tracking was synchronized.

The saved numeric fixture supplies a mixed event sequence:

1. XY helical arc: start `(12,23,10)`, center `(2,23,10)`, CCW 90 degrees,
   endpoint `(2,33,30)`.
2. Straight Z `feed_link` from actual Z30 down to Z20, with unchanged XY/A/B.
3. Rotary rapid to A10.

After the arc, actual `zpos=30` but tracking still says `nLastPathZ=10`.
The following descent is classified as an upward retract because `20>10`.
The rotary rapid then bypasses G75. The regression requires tracking to match
the committed endpoint and rejects that bypass.

This is a synthetic source-level reproduction using `X5_job=true`. Whether a
particular SolidCAM operation emits this exact mixture of arc and line_5x
events has not been established from the supplied traces. The tests preserve a
conservative tracking contract; they do not establish an observed machine crash.
If the CAM event model categorically forbids that combination, that constraint
must be documented and checked explicitly before narrowing the regression.

The correction synchronizes endpoint/work-offset tracking after successful arc
calculation and invalidates preceding rapid-link confirmation. It leaves the
independent contiguous-rapid correction in `usr_rapid` intact.

## Current coverage

- `test_arc_link_boundary.py` keeps the XY helix case on the legacy mid-job
  harness, compares parsed NC words and includes an in-memory reversion of the
  `@usr_arc` endpoint tracking that must fail with an AssertionError.
- `test_indexing_link.py::CamLinkTransitionTests::test_arc_revokes_and_tracks_endpoint`
  checks the contract on a realistic rotated 5x session with an XY arc. YZ and
  ZX arcs stop the post since the machine run of 2026-10-28 (SD42940 = 0), and
  their arc code is deleted.
