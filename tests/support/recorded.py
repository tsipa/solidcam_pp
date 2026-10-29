"""Replays of the recorded SolidCAM programs and the pins of their NC.

tests/fixtures/recorded_cam_001..005.trace.txt.xz are native SolidCAM input traces
(tests/fixtures/README.md). replay(name) decompresses one in memory, parses it with
pp_tests/trace.py and replays every event through the tested GPP and its VMID (PP_TEST_SOURCE,
support.paths) with the session API (pp_tests.gppl.session, preset 'session', GPPL_POLICY
ignored), stopping at the first error, as SolidCAM stops at a POST ERROR.

The NC pin of a recording (PINS) is the sha256 of its normalized NC: the NC stream of the replay
(file directives such as '!!open file=...!!' included, so a stopped replay has one too) with
every line's whitespace runs collapsed to one space, empty lines dropped, each line ended by
'\\n'. The pin also keeps the line count, the sha256 (12 hex digits) of every CHUNK lines, to
locate a difference without the old NC, and the git blob ids of the GPP and VMID it was made
with: mismatch_message() replays those through the current engine, when git still has them, to
show the first differing lines. Regenerate the pins with
python -m pp_tests.tools.recorded_pins --write [NAME ...].
"""
import difflib
import functools
import hashlib
import json
import lzma
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .paths import FIXTURES, PP, ROOT, VMID

RECORDINGS = tuple(f'recorded_cam_{number:03d}' for number in range(1, 6))
PINS = FIXTURES / 'recorded_cam_nc_pins.json'
CHUNK = 1000
# The replays an open registry entry stops: name -> (id, event, pattern of the error). The
# replay must stop exactly there while the entry is open; once it is fixed the entry goes and
# the recording must reach @end_of_file.
KNOWN_STOPS = {
}
REGENERATE = 'python -m pp_tests.tools.recorded_pins --write'


@dataclass(frozen=True)
class Replay:
    name: str
    events: int             # events replayed (all of them unless the replay stopped)
    last_event: str
    errors: tuple           # (event index, event name, job_name, job_type, message)
    post_errors: tuple      # NC lines and console messages that say POST ERROR
    nc: str                 # normalized NC


def trace_path(name):
    return FIXTURES / f'{name}.trace.txt.xz'


def load_events(name):
    """The parsed events of a recording (pp_tests/trace.py), decompressed in memory."""
    from pp_tests.trace import parse_trace
    with lzma.open(trace_path(name), 'rt', encoding='utf-8') as trace:
        return parse_trace(trace.read())


def normalize(nc_text):
    return ''.join(' '.join(line.split()) + '\n' for line in nc_text.splitlines() if line.strip())


def _read_source(path):
    return Path(path).read_bytes().replace(b'\r\n', b'\n')


def blob_id(data):
    """git hash-object of the bytes (CRLF read as LF, as a Windows checkout of the LF blob gives)."""
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def run_replay(name, gpp_text, vmid_text):
    """Replay a recording through the GPP and VMID texts; returns a Replay."""
    from pp_tests.gppl.session import Session, resolve_policies
    from pp_tests.gppl.vmid import parse_vmid
    session = Session(gpp_text, vmid=parse_vmid(vmid_text), policies=resolve_policies(env=False), trace=False)
    report = session.replay(load_events(name), stop_on_error=True)
    errors, post_errors, job = [], [], {}
    for record in report.events:
        if record.name == 'start_of_job':
            job = record.params
        if record.error is not None:
            errors.append((record.index, record.name, job.get('job_name'), job.get('job_type'), str(record.error)))
        post_errors += [f'event {record.index} @{record.name} {kind}: {text}' for kind, text in record.console
                        if 'POST ERROR' in str(text)]
    post_errors += [f'NC: {line}' for line in report.nc_text.splitlines() if 'POST ERROR' in line]
    last = report.events[-1].name if report.events else ''
    return Replay(name, len(report.events), last, tuple(errors), tuple(post_errors), normalize(report.nc_text))


@functools.lru_cache(maxsize=None)
def replay(name):
    """The replay of a recording through the tested GPP (cached per process)."""
    return run_replay(name, _read_source(PP).decode('utf-8-sig'), _read_source(VMID).decode('latin-1'))


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def make_pin(result, gpp=PP, vmid=VMID):
    lines = result.nc.splitlines(keepends=True)
    return {'events': result.events, 'nc_lines': len(lines), 'sha256': _sha(result.nc),
            'chunks': [_sha(''.join(lines[start:start + CHUNK]))[:12] for start in range(0, len(lines), CHUNK)],
            'gpp_blob': blob_id(_read_source(gpp)), 'vmid_blob': blob_id(_read_source(vmid))}


def load_pins():
    return json.loads(PINS.read_text(encoding='utf-8'))['recordings'] if PINS.exists() else {}


def write_pins(pins):
    data = {'about': 'sha256 of the normalized NC of each recorded_cam replay (tests/support/recorded.py); '
                     f'regenerate with {REGENERATE} [NAME ...]',
            'chunk_lines': CHUNK, 'recordings': dict(sorted(pins.items()))}
    PINS.write_text(json.dumps(data, indent=1) + '\n', encoding='utf-8', newline='\n')


def git_blob(blob):
    """The bytes of a git blob of this repository, or None (no git, unknown blob)."""
    try:
        done = subprocess.run(['git', 'cat-file', 'blob', blob], cwd=ROOT, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def first_differing_lines(old, new, context=3, limit=40):
    """Unified diff of the first difference between two NC texts (at most `limit` lines)."""
    old_lines, new_lines = old.splitlines(), new.splitlines()
    start = 0
    while start < min(len(old_lines), len(new_lines)) and old_lines[start] == new_lines[start]:
        start += 1
    begin = max(start - context, 0)
    window = 300
    diff = difflib.unified_diff(old_lines[begin:start + window], new_lines[begin:start + window],
                                'pinned', 'now', n=context, lineterm='')
    shown = []
    for line in diff:
        if line.startswith('@@'):
            # re-number the hunk header from the window to the whole NC
            head, _, rest = line[3:].partition(' @@')
            parts = []
            for part in head.split():
                sign, numbers = part[0], part[1:].split(',')
                numbers[0] = str(int(numbers[0]) + begin)
                parts.append(sign + ','.join(numbers))
            line = '@@ ' + ' '.join(parts) + ' @@' + rest
        shown.append(line)
        if len(shown) >= limit:
            shown.append('...')
            break
    return shown


def mismatch_message(name, pin, result, gpp=PP, vmid=VMID):
    """Why the NC of `result` does not match `pin`: sizes, the first differing chunk and, when git
    has the GPP/VMID the pin was made with, the first differing lines."""
    now = make_pin(result, gpp, vmid)
    lines = [f'{name}: the NC differs from its pin in {PINS.relative_to(ROOT).as_posix()}',
             f"  pinned: {pin['nc_lines']} lines, {pin['events']} events, sha256 {pin['sha256'][:16]}",
             f"  now:    {now['nc_lines']} lines, {now['events']} events, sha256 {now['sha256'][:16]}"]
    chunk = next((i for i, (a, b) in enumerate(zip(pin['chunks'], now['chunks'])) if a != b),
                 min(len(pin['chunks']), len(now['chunks'])))
    last = min((chunk + 1) * CHUNK, max(pin['nc_lines'], now['nc_lines']))
    lines.append(f'  first difference in NC lines {chunk * CHUNK + 1}-{last}')
    if (pin['gpp_blob'], pin['vmid_blob']) == (now['gpp_blob'], now['vmid_blob']):
        lines.append('  the GPP and VMID are the pinned ones: the engine, pp_tests/trace.py or the recording '
                     'changed the NC')
    else:
        gpp_bytes, vmid_bytes = git_blob(pin['gpp_blob']), git_blob(pin['vmid_blob'])
        if gpp_bytes is None or vmid_bytes is None:
            lines.append(f"  git has no blob {pin['gpp_blob'][:10]} (GPP) / {pin['vmid_blob'][:10]} (VMID) of the "
                         'pin, so the old NC cannot be shown; python -m pp_tests.tools.recorded_pins --nc DIR writes '
                         'the NC of a checkout for a manual diff')
        else:
            old = run_replay(name, gpp_bytes.decode('utf-8-sig'), vmid_bytes.decode('latin-1'))
            same = _sha(old.nc) == pin['sha256']
            lines.append(f"  first differing lines (pinned GPP {pin['gpp_blob'][:10]} and VMID {pin['vmid_blob'][:10]} "
                         'replayed through the current engine' + ('' if same else ', which no longer gives the '
                                                                   'pinned NC either: the engine changed too') + '):')
            lines += ['    ' + line for line in first_differing_lines(old.nc, result.nc)]
    lines.append(f'If the change is intended, regenerate the pin: {REGENERATE} {name}')
    return '\n'.join(lines)
