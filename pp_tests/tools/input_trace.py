"""Keep native CAM event inputs, remove post output, neutralize part identities.

Works on bytes: native numeric spelling, whitespace, change flags and line endings
are preserved. Temporary CAMDBG readouts supply missing event parameters without
inventing flags, and restate a native number with more decimals when they agree
with its native spelling (the native change flag is kept). XZ/gzip output contains
no source filename or timestamp.
"""
import argparse
import gzip
import hashlib
import json
import lzma
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path


HEADER = re.compile(rb'^\((\d+)\)@(\w+)\s*==>')
DEBUG = re.compile(rb'(?:^.{22}> ?|==>[ \t]*); CAMDBG (\w+) ([^\r\n]*)')
DEBUG_VALUE = re.compile(rb'([A-Za-z_]\w*):([^ \t\r\n]*)')
PARAMETER = re.compile(rb'\b([A-Za-z_]\w*)\s*:')
NUMBER = rb'[+-]?(?:\d+(?:\.\d*)?|\.\d+)'
# The CAMDBG readouts of the 828D post (usr_camdbg_*, trace_level 5). *_value: the number of a
# field the trace prints as a name; d_tapping_value: the drill type constant D_Tapping.
ARC_FIELDS = {b'xstart', b'ystart', b'zstart', b'xcenter_rel', b'ycenter_rel', b'zcenter_rel', b'arc_size'}
DEBUG_FIELDS = {
    b'arc': ARC_FIELDS,
    b'arc_yz': ARC_FIELDS,
    b'arc_zx': ARC_FIELDS,
    b'def_tool': {b'next_command'},
    b'move_4x': {b'prev_command'},
    b'move_5x': {b'prev_command'},
    b'start_of_file': {b'date', b'time', b'd_tapping_value'},
    b'start_of_job': {b'angle', b'cpos', b'apos', b'bpos', b'd_drill_type', b'rot_axis_coord_value',
                      b'flood_coolant_value', b'mist_coolant_value', b'hp_flood_coolant_value',
                      b'lp_flood_coolant_value', b'through_ival_coolant_value', b'lp_through_coolant_value',
                      b'air_blast_coolant_value', b'air_through_coolant_value', b'through_coolant_val'},
}
STRING_FIELDS = {b'date', b'time', b'next_command', b'prev_command'}
QUOTED = re.compile(rb"(\w+)(\s*:\s*)'((?:[^']|'')*)'")
FIXED = {
    b'g_file_name': b'REFERENCE.MPF',
    b'full_g_file_name': br'C:\reference\REFERENCE.MPF',
    b'part_name': b'PART',
    b'part_model_name': br'C:\reference\PART.SLDPRT',
    b'part_full_name': br'C:\reference\PART',
    b'path_part': br'C:\reference',
}
GROUPS = {
    b'job_name': 'operation', b'original_job_name': 'operation',
    b'next_job_name': 'operation', b'prev_job_name': 'operation',
    b'geom_name': 'geometry', b'fixture_name': 'fixture',
    b'setup_name': 'setup', b'home_user_name': 'origin',
    b'message': 'message', b'msg': 'message', b'split_name': 'split',
}


class NeutralNames:
    def __init__(self):
        self.names = {}
        self.counts = Counter()
        self.changed = Counter()

    def replace(self, match):
        original_key, separator, value = match.groups()
        key = original_key.lower()
        replacement = value
        if value and key in FIXED:
            replacement = FIXED[key]
        elif value and key in GROUPS:
            group = GROUPS[key]
            # SolidCAM converts underscores to hyphens in job_name while
            # original_job_name retains them. Both must get the same alias.
            identity = value.lower().replace(b'_', b'-') if group == 'operation' else value
            if group == 'message' and not re.search(rb'[A-Za-z0-9\x80-\xff]', value):
                return match[0]  # separator-only messages contain no identity
            lookup = group, identity
            if lookup not in self.names:
                self.counts[group] += 1
                self.names[lookup] = f'{group}_{self.counts[group]:03}'.encode('ascii')
            replacement = self.names[lookup]
        if replacement != value:
            self.changed[key.decode('ascii')] += 1
        return original_key + separator + b"'" + replacement + b"'"


def decimals(number):
    return len(number.partition(b'.')[2])


def upgrade_native(lines, key, value):
    """Respell the one native number of ``key`` in ``lines`` as ``value``, keeping its flag.

    Only when ``value`` has more decimals and lies within half a unit of the last native
    digit (the native spelling is the CAM value rounded; either tie rule). Returns False
    when the native value is kept: not exactly one numeric native, fewer decimals, or a
    disagreeing readout (the extractor never chooses between disagreeing readouts)."""
    token = re.compile(rb'(?<!\w)' + re.escape(key) + rb'\s*:\s*(' + NUMBER + rb')[TF]?(?![^ \t\r\n])')
    hits = [(index, match) for index, line in enumerate(lines) for match in token.finditer(line)]
    if len(hits) != 1:
        return False
    index, match = hits[0]
    native = match[1]
    if decimals(value) <= decimals(native):
        return False
    unit = Decimal(1).scaleb(-decimals(native))
    if 2 * abs(Decimal(value.decode('ascii')) - Decimal(native.decode('ascii'))) > unit:
        return False
    lines[index] = lines[index][:match.start(1)] + value + lines[index][match.end(1):]
    return True


def extract(source, destination, forbidden=()):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('source and destination must be different files')
    compression = destination.suffix.lower().lstrip('.')
    if compression not in ('gz', 'xz'):
        raise ValueError('destination must end in .gz or .xz')
    names = NeutralNames()
    events = Counter()
    source_hash, input_hash = hashlib.sha256(), hashlib.sha256()
    source_bytes = input_bytes = parameter_lines = 0
    debug_lines = 0
    debug_parameters = Counter()
    upgraded_parameters = Counter()
    kept_native = Counter()
    public = False
    current_event, current_fields = None, set()
    pending = []  # neutral lines of the current public event; a later CAMDBG may respell one
    forbidden = [word.encode('ascii').lower() for word in forbidden]

    def flush(output):
        nonlocal input_bytes
        for neutral in pending:
            if any(word in neutral.lower() for word in forbidden):
                raise ValueError('forbidden identity remains in a public input line')
            output.write(neutral)
            input_hash.update(neutral)
            input_bytes += len(neutral)
        pending.clear()

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open('rb') as original, destination.open('wb') as compressed:
            compressor = (lzma.LZMAFile(compressed, 'w', preset=6) if compression == 'xz' else
                          gzip.GzipFile(fileobj=compressed, mode='wb', filename='', mtime=0))
            with compressor as output:
                for line in original:
                    source_hash.update(line)
                    source_bytes += len(line)
                    header = HEADER.match(line)
                    if header:
                        public = int(header[1]) <= 1
                        if public:
                            flush(output)
                            current_event, current_fields = header[2], set()
                            events[current_event.decode('ascii')] += 1
                    diagnostic = DEBUG.search(line)
                    if diagnostic:
                        event, payload = diagnostic.groups()
                        if event != current_event or event not in DEBUG_FIELDS:
                            raise ValueError('diagnostic does not match the current public event')
                        fields = DEBUG_VALUE.findall(payload)
                        if not fields or any(key not in DEBUG_FIELDS[event] for key, _ in fields):
                            raise ValueError('unexpected diagnostic parameter')
                        additions = []
                        for key, value in fields:
                            if key not in STRING_FIELDS and value and not re.fullmatch(NUMBER, value):
                                raise ValueError('nonnumeric diagnostic value')
                            if key in current_fields:
                                # Native data and its change flag stay; a number may gain decimals.
                                if key not in STRING_FIELDS and value and upgrade_native(pending, key, value):
                                    upgraded_parameters[key.decode('ascii')] += 1
                                else:
                                    kept_native[key.decode('ascii')] += 1
                                continue
                            if key in STRING_FIELDS or not value:
                                value = b"'" + value.replace(b"'", b"''") + b"'"
                            additions.append(key + b':' + value)
                            current_fields.add(key)
                            debug_parameters[key.decode('ascii')] += 1
                        debug_lines += 1
                        if not additions:
                            continue
                        ending = b'\r\n' if line.endswith(b'\r\n') else b'\n'
                        line = b'                    ..> ' + b' '.join(additions) + ending
                        parameter_lines += 1
                    elif header:
                        if not public:
                            continue
                        current_fields.update(PARAMETER.findall(line))
                    elif public and re.match(rb'^\s*\.\.>', line):
                        current_fields.update(PARAMETER.findall(line))
                        parameter_lines += 1
                    else:
                        continue
                    pending.append(QUOTED.sub(names.replace, line))
                flush(output)
        if not events:
            raise ValueError('no public CAM events found')
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {
        'schema': 2,
        'source_bytes': source_bytes,
        'source_sha256': source_hash.hexdigest(),
        'input_trace_bytes': input_bytes,
        'input_trace_sha256': input_hash.hexdigest(),
        'compression': compression,
        'compressed_bytes': destination.stat().st_size,
        'compressed_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'event_count': sum(events.values()),
        'events': dict(sorted(events.items())),
        'parameter_lines': parameter_lines,
        'diagnostic_lines_read': debug_lines,
        'parameters_from_diagnostics': dict(sorted(debug_parameters.items())),
        'parameters_upgraded_from_diagnostics': dict(sorted(upgraded_parameters.items())),
        'diagnostics_kept_native': dict(sorted(kept_native.items())),
        'neutral_identity_counts': dict(sorted(names.counts.items())),
        'renamed_fields': dict(sorted(names.changed.items())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--forbid', nargs='*', default=[])
    args = parser.parse_args()
    if args.source.resolve() == args.destination.resolve():
        parser.error('source and destination must be different files')
    manifest = extract(args.source, args.destination, args.forbid)
    if args.manifest:
        args.manifest.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
