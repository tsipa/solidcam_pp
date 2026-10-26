# Repeated G75 inside a continuous CAM rapid link

The supplied second Slide trace shows a straight Z `feed_link` retract followed
by XYZ-only rapid motion and several rotary rapid blocks in the same operation.
In the numeric excerpt around original trace lines 21277–21363, the rotary
angles are 3.035, 6.070, 9.105 and 12.140 degrees. There is no intervening feed,
new job, tmatrix or work-offset change. The old output homes before 6.070 and
subsequent rotations.

In commit `d5952a2`, `usr_rapid` clears `bCamLinkRetract` on entry, then restores
it only when the current rapid did not rotate. XYZ-only subdivisions therefore
retain authorization, but the first rotary subdivision consumes it. The next
subdivision fails `bCamLinkRapid` and falls into the normal G75 homing branch.
The current external PP change restores confirmation throughout the contiguous
rapid chain, until a feed or indexing/job boundary invalidates it.

## Why the initial tests accepted the defect

The initial synthetic oracle copied the one-rotation contract from the source
comment without checking a real multi-rotation transition. Its first scenario
expected the flag to become false after the first rotary rapid and explicitly
required G75 before the second. The split-XYZ scenario also expected the flag
to become false after its first rotation. Those were incorrect expectations,
not evidence that the new PP behavior was broken.

The external PP fix caused three assertion failures: two flag expectations and
one requirement for G75. The 482 Slide angle cases did not detect this earlier:
they validate isolated rotary calculations, not emitted homing or link history.
The source-mutation tests validate only the scenarios they mutate; they cannot
prove completeness of the scenario set.

## Changed coverage

- `shit2_contiguous_link.json` preserves numeric inputs of the real failing
  transition. Its expected result forbids G75 across the whole rapid chain and
  requires all four directed A outputs. Old erroneous NC output is not copied
  as an expected baseline.
- A focused in-memory reversal restores one-rotation authorization and must
  fail specifically on unexpected G75, rather than an interpreter exception.
- Synthetic cases retain the permission through XYZ and repeated rotary
  subdivisions and revoke it after feed, end_of_job, tmatrix or offset changes.
  Diagonal/non-link feed retracts cannot establish permission.
- First move and indexing tests still require their homing/clearance behavior;
  the continuous-link fix must not simply suppress every G75.

## Remaining risks

Unwanted G75 inserts machine-homing travel into a CAM-planned transition,
changing the intended motion path and cycle time. Physical clearance cannot be
established by these source-level tests.

Overbroad permission retention could cause the opposite error: missing required
clearance at a new job, tool change, offset or indexing boundary. Current cases
cover the boundaries named above; they are not exhaustive for all CAM event
types, transformations, aborts or real fixture geometry.

The interpreter is partial, normalizes formatting and does not emulate the
special skipline runtime switch or full machine motion. A green suite establishes
the saved contracts, not complete equivalence with SolidCAM or collision safety.
