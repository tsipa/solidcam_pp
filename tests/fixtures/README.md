# Recorded CAM inputs

`reference_multijob.trace.txt.xz` is a native SolidCAM input trace recorded on
2026-10-27, build 153065. It contains 154,995 public events across 31 operations,
including XYZ lines/arcs, indexed planes, simultaneous rotary motion, tool
definitions, tool changes, and compensation events.

Public depth-0/depth-1 event headers and their parameter continuation lines are
retained. The updated recording also supplies missing parameters from 50,199
temporary `CAMDBG` readouts, promoted into parameter continuation lines:

- Every one of the 50,196 arcs now has observed `xstart`, `ystart`, and
  `zcenter_rel`. All recorded `zcenter_rel` values are zero.
- `start_of_file` includes the observed `date` and `time`.
- The first `start_of_job` includes observed `angle`, `cpos`, `apos`, `bpos`,
  and `d_drill_type`. The latter is `-1`, not an inferred empty string.

Native values and their change flags take precedence if a diagnostic repeats a
field; a numeric diagnostic that agrees with the native spelling (within half a
unit of its last digit) and has more decimals respells the native number and
keeps its flag. The manifest counts these as `parameters_upgraded_from_diagnostics`
and the repeats that left the native value as `diagnostics_kept_native`. No change
flags are invented for diagnostic-only values. Generated NC
text, the debug comments themselves, and nested postprocessor implementation
traces are removed. This is a record of CAM inputs, not an oracle for correct NC
output or a claim that the current offline interpreter can replay every event.

Operations are consistently named `operation_001` through `operation_031`.
Geometry names, part/file paths, setup/fixture names, and nonempty descriptive
messages use neutral identifiers. Original identity mappings are not included.
All other native parameter text is retained, including numeric spelling, change
flags (`T`/`F`), operation types, tool data, whitespace, and line endings. This
uses targeted identity replacement, not the capture command's blanket string
redaction.

The complete enriched text is about 108 MB; XZ stores it losslessly in 5.71 MB
(5.45 MiB), smaller than the previous 8.08 MB gzip fixture despite the added data.
`reference_multijob.manifest.json` records hashes, sizes, event counts, and the
fields renamed or recovered from diagnostics. The compressed file has no source
filename or timestamp.

Read the first lines without unpacking the full file:

```python
import lzma
from itertools import islice

with lzma.open('tests/fixtures/reference_multijob.trace.txt.xz', 'rt', encoding='utf-8') as trace:
    print(''.join(islice(trace, 20)))
```

## Recording a new trace

The 828D post writes the readouts itself: set the post-writer option
`trace_level = 5` in `@usr_ip_postwriteroptions`. It runs `trace 'all':5` and
prints `; CAMDBG <event> name:value` lines (`@usr_camdbg_*`):

- `start_of_file`: `date`, `time`, and `d_tapping_value` (the drill type constant
  `D_Tapping`);
- `def_tool`: `next_command`; `rapid_move`: `prev_command` (CAM rapids only);
- `start_of_job`: `angle`, `cpos`, `apos`, `bpos`, `d_drill_type`,
  `through_coolant_val`, and the numbers of the fields the trace prints as names
  (`rot_axis_coord_value`, `flood_coolant_value` and the other coolant `*_value`
  keys);
- `arc`, `arc_yz`, `arc_zx`: `xstart`, `ystart`, `zstart`, `xcenter_rel`,
  `ycenter_rel`, `zcenter_rel`, `arc_size` with 9 decimals (the trace prints
  `arc_size` with 3; the post rotates the start point by it and checks the CAM end
  point to 0.001).

The trace goes into the NC file, so such an NC is for recording only; the shipped
post keeps `trace_level = 0`.

`python -m pp_tests.tools.input_trace SOURCE DESTINATION --manifest MANIFEST`
performs the extraction and neutral naming. The destination suffix selects XZ
(`.xz`) or gzip (`.gz`). Optional `--forbid` terms make the export fail if a
specified identity remains. Source files are never rewritten.
