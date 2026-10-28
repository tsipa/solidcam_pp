"""Keep native CAM event inputs, remove post output, neutralize part identities.

Works on bytes: native numeric spelling, whitespace, change flags and line endings
are preserved. Temporary CAMDBG readouts supply missing event parameters without
inventing flags. XZ/gzip output contains no source filename or timestamp.
"""
import argparse
import gzip
import hashlib
import json
import lzma
import re
from collections import Counter
from pathlib import Path


HEADER = re.compile(rb'^\((\d+)\)@(\w+)\s*==>')
DEBUG = re.compile(rb'(?:^.{22}> ?|==>[ \t]*); CAMDBG (\w+) ([^\r\n]*)')
DEBUG_VALUE = re.compile(rb'([A-Za-z_]\w*):([^ \t\r\n]*)')
PARAMETER = re.compile(rb'\b([A-Za-z_]\w*)\s*:')
DEBUG_FIELDS = {
    b'arc': {b'xstart', b'ystart', b'zcenter_rel'},
    b'start_of_file': {b'date', b'time'},
    b'start_of_job': {b'angle', b'cpos', b'apos', b'bpos', b'd_drill_type'},
}
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
    public = False
    current_event, current_fields = None, set()
    forbidden = [word.encode('ascii').lower() for word in forbidden]
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
                            if key in current_fields:
                                continue  # retain native data and its change flag
                            if key in (b'date', b'time') or not value:
                                value = b"'" + value.replace(b"'", b"''") + b"'"
                            elif not re.fullmatch(rb'[+-]?(?:\d+(?:\.\d*)?|\.\d+)', value):
                                raise ValueError('nonnumeric diagnostic value')
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
                    neutral = QUOTED.sub(names.replace, line)
                    if any(word in neutral.lower() for word in forbidden):
                        raise ValueError('forbidden identity remains in a public input line')
                    output.write(neutral)
                    input_hash.update(neutral)
                    input_bytes += len(neutral)
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
