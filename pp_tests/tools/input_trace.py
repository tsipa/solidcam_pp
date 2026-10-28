"""Keep native CAM event inputs, remove post output, neutralize part identities.

Works on bytes: numeric spelling, whitespace, change flags and line endings are
preserved. The gzip header contains neither the original filename nor a timestamp.
"""
import argparse
import gzip
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


HEADER = re.compile(rb'^\((\d+)\)@(\w+)\s*==>')
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
    names = NeutralNames()
    events = Counter()
    source_hash, input_hash = hashlib.sha256(), hashlib.sha256()
    source_bytes = input_bytes = parameter_lines = 0
    public = False
    forbidden = [word.encode('ascii').lower() for word in forbidden]
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open('rb') as original, destination.open('wb') as compressed:
            with gzip.GzipFile(fileobj=compressed, mode='wb', filename='', mtime=0) as output:
                for line in original:
                    source_hash.update(line)
                    source_bytes += len(line)
                    header = HEADER.match(line)
                    if header:
                        public = int(header[1]) <= 1
                        if not public:
                            continue
                        events[header[2].decode('ascii')] += 1
                    elif public and re.match(rb'^\s*\.\.>', line):
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
        'schema': 1,
        'source_bytes': source_bytes,
        'source_sha256': source_hash.hexdigest(),
        'input_trace_bytes': input_bytes,
        'input_trace_sha256': input_hash.hexdigest(),
        'gzip_bytes': destination.stat().st_size,
        'gzip_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'event_count': sum(events.values()),
        'events': dict(sorted(events.items())),
        'parameter_lines': parameter_lines,
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
