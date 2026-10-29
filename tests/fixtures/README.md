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
messages use neutral identifiers; the user account is `USER`. Original
identity mappings are not included.
All other native parameter text is retained, including numeric spelling, change
flags (`T`/`F`), operation types, tool data, whitespace, and line endings. This
uses targeted identity replacement, not the capture command's blanket string
redaction.

The complete enriched text is about 108 MB; XZ stores it losslessly in 5.72 MB
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
- `def_tool`: `next_command`; `move_4x`, `move_5x`: `prev_command`;
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

## Sanitization rules

These rules apply to all recorded fixtures and accompanying examples, debug logs,
filenames, manifests and documentation in the repository, including compressed
files. Sanitize before staging: original part and operation identities must never
enter Git history, even in a temporary commit. Keep raw recordings outside the
repository and leave the source unchanged.

- Replace part names, model names, source/output filenames and paths with neutral
  values such as `PART`, `REFERENCE.MPF` and `C:\reference`. Name the exported
  fixture generically as well.
- Replace the SolidCAM user account (`user_account` in `start_of_file`) with
  `USER`. Account, computer/host and Windows user names, including user-profile
  paths such as `C:\Users\<name>`, are identities wherever they appear.
- Replace operation names consistently with `operation_001`, `operation_002`, etc.
  Cover `job_name`, `original_job_name`, `next_job_name` and `prev_job_name`;
  SolidCAM's underscore/hyphen variants must resolve to the same alias.
- Neutralize geometry, setup, fixture and origin names, descriptive messages and
  comments that can reveal the part or operation. Do not retain original-name
  mappings or identity-bearing source paths in manifests or documentation.
- Tool names, descriptions and tool data may remain unchanged. Preserve machining
  coordinates, angles, numeric precision, event order and native change flags.
  An original part/operation identity copied into a tool label still needs removal.
- With `trace_level = 5`, the post writes CAMDBG alongside the native trace and NC.
  Use the extractor to promote supported debug values into event parameters and
  remove generated NC, raw debug comments and nested implementation traces. The
  debug field allowlist is not a general identity filter: inspect any new string
  fields and extend neutral naming before retaining them. Do not silently drop
  unrecognized debug fields to make extraction succeed.

For example (use neutral destination names; the source stays outside the repo):

```powershell
python -m pp_tests.tools.input_trace C:\capture\recording.mpf tests/fixtures/reference_multijob.trace.txt.xz --manifest tests/fixtures/reference_multijob.manifest.json --forbid ORIGINAL_PART --forbid ORIGINAL_OPERATION
```

Supply actual original names and distinctive fragments to `--forbid` locally;
never save those terms or the alias mapping in tracked commands or files. Check
all known names, case variants, underscore/hyphen spellings and source path
fragments in the **decompressed** export and accompanying text before staging.
Review retained string fields, including strings recovered from CAMDBG, rather
than assuming a successful extraction guarantees sanitization. An unfamiliar
identity-bearing field requires an extractor update, not an exception to these
rules. Run `python -m unittest discover -s tests_engine -p test_input_trace.py`
after changing the extractor.

## Additional recorded CAM fixtures

`recorded_cam_001.trace.txt.xz` through `recorded_cam_005.trace.txt.xz` are
five separate recordings exported with the current CAMDBG-aware extractor.
Each has a matching `.manifest.json` with source/content hashes, event counts,
neutral identity counts and diagnostic recovery statistics. Source paths and
original identity mappings are intentionally excluded. Operation aliases are
local to each recording; matching alias numbers across files do not imply the
same operation.

Only public CAM inputs and supported diagnostic values are retained. Original
part, operation, geometry, setup, message and user account identities are
neutralized; tool names and data are preserved. The additional stock/target
labels and machine configuration fields were reviewed for part/operation
identities. These files are input examples rather than expected NC output.
`tests/test_recorded_replays.py` replays them through the post: each must reach
`@end_of_file` without a POST ERROR (or stop exactly at an open registered defect:
`recorded_cam_004` at PP-063), and the sha256 of its NC must equal the pin in
`recorded_cam_nc_pins.json`. The pins record the current post's output, not an
oracle; `python -m pp_tests.tools.recorded_pins --write` regenerates them.
`recorded_cam_001` (about 60 s and 2 GB) is replayed only with `PP_RECORDED_ALL=1`.

The exports use lossless XZ with preset `9 | lzma.PRESET_EXTREME` (retaining the
smaller preset-6 stream if necessary). Decompressed bytes are verified after
compression; use streaming `lzma.open` to read them without an unpacked copy.
The XZ decoder can need roughly 65 MiB for its compression dictionary.

| Recording | Public events | CAMDBG readouts | XZ bytes |
| --- | ---: | ---: | ---: |
| `recorded_cam_001` | 154,995 | 101,499 | 4,318,600 |
| `recorded_cam_002` | 11,831 | 1,505 | 211,476 |
| `recorded_cam_003` | 5,997 | 8,685 | 278,884 |
| `recorded_cam_004` | 41,574 | 22,995 | 1,152,796 |
| `recorded_cam_005` | 25,533 | 19,151 | 871,432 |
