# Recorded CAM inputs

`reference_multijob.trace.txt.gz` is a native SolidCAM input trace recorded on
2026-10-27, build 153065. It contains 154,995 public events across 31 operations,
including XYZ lines/arcs, indexed planes, simultaneous rotary motion, tool
definitions, tool changes, and compensation events.

Only public depth-0/depth-1 event headers and their parameter continuation lines
are retained. Generated NC text and nested postprocessor implementation traces
are removed. This is a record of CAM inputs, not an oracle for correct NC output
or a claim that the current offline interpreter can replay every event.

Operations are consistently named `operation_001` through `operation_031`.
Geometry names, part/file paths, setup/fixture names, and nonempty descriptive
messages use neutral identifiers. Original identity mappings are not included.
All other native parameter text is retained, including numeric spelling, change
flags (`T`/`F`), operation types, tool data, whitespace, and line endings. This
uses targeted identity replacement, not the capture command's blanket string
redaction.

The full text is about 104 MB; gzip stores it losslessly in about 8 MB.
`reference_multijob.manifest.json` records hashes, sizes, event counts, and the
fields renamed. The gzip header has no source filename or timestamp.

Read the first lines without unpacking the full file:

```python
import gzip
from itertools import islice

with gzip.open('tests/fixtures/reference_multijob.trace.txt.gz', 'rt', encoding='utf-8') as trace:
    print(''.join(islice(trace, 20)))
```

`python -m pp_tests.tools.input_trace SOURCE DESTINATION --manifest MANIFEST`
performs the extraction and neutral naming. Optional `--forbid` terms make the
export fail if a specified identity remains. Source files are never rewritten.
