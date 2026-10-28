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
field. No change flags are invented for diagnostic-only values. Generated NC
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

`python -m pp_tests.tools.input_trace SOURCE DESTINATION --manifest MANIFEST`
performs the extraction and neutral naming. The destination suffix selects XZ
(`.xz`) or gzip (`.gz`). Optional `--forbid` terms make the export fail if a
specified identity remains. Source files are never rewritten.
