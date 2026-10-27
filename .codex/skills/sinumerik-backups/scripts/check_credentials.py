#!/usr/bin/env python3
"""Local Git guard for credential-bearing machine backups. Never logs values."""
import argparse
import re
import subprocess
import sys
import zlib
from pathlib import Path


LIMIT = 128 * 1024 * 1024
ZLIB = re.compile(rb'\x78[\x01\x5e\x9c\xda]')
KEY = r'(?:password|passwd|passwort|kennwort|pwd|secret|token|api[_-]?key|private[_-]?key)'
FIELD = rf'[\w.$:-]*{KEY}[\w.$:-]*'
ASSIGNMENT = re.compile(rf'^[ \t]*["\']?({FIELD})["\']?[ \t]*[:=][ \t]*(.*?)[ \t]*[,;]?[ \t]*$', re.I | re.M)
XML = re.compile(rf'<({FIELD})\b[^>]*?(?<!/)>(.*?)</\1\s*>', re.I | re.S)
ATTRIBUTE = re.compile(rf'\b({KEY})\s*=\s*(["\'])(.*?)\2', re.I)
PRIVATE_KEY = re.compile(r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----')
URL = re.compile(r'\b(?:smb|ftp|sftp|https?)://[^\s/:@]+:([^\s/@]+)@', re.I)
EMPTY = {'', '""', "''", 'null', 'none', '<redacted>', '[redacted]'}


def candidate(path):
    p = Path(path)
    name = p.name.lower()
    if p.suffix.lower() == '.ard':
        return True
    if name.startswith(('logdrive.', 'logdrive_')):
        return True
    if name in ('.env', 'logdrive.ini', 'logdrive_ini.sav', 'logdrive.oldstyle',
                'smb.conf', 'smbcredentials', '.smbcredentials'):
        return True
    return p.suffix.lower() in {'.ini', '.cfg', '.conf', '.xml', '.json', '.txt',
                               '.yaml', '.yml', '.env', '.dat'} and any(
        part.lower() in {'backup', 'backups', 'smb', 'samba'} for part in p.parts)


def text_findings(text):
    findings = []
    for pattern in (ASSIGNMENT, XML):
        for match in pattern.finditer(text):
            value = match[2].strip().strip('"\'').strip()
            if value.lower() not in EMPTY:
                findings.append('populated credential field ' + match[1])
    for match in ATTRIBUTE.finditer(text):
        if match[3].strip().lower() not in EMPTY:
            findings.append('populated credential attribute ' + match[1])
    if PRIVATE_KEY.search(text):
        findings.append('private key material')
    if URL.search(text):
        findings.append('URL with embedded credentials')
    return sorted(set(findings))


def archive_streams(data):
    """Validate/decompress independently framed ARD zlib streams in memory."""
    pos, total, streams = 0, 0, []
    while match := ZLIB.search(data, pos):
        offset = match.start()
        try:
            decoder = zlib.decompressobj()
            decoded = decoder.decompress(data[offset:], LIMIT + 1)
        except zlib.error:
            pos = offset + 2
            continue
        if len(decoded) > LIMIT or decoder.unconsumed_tail:
            raise ValueError('archive exceeds decompression limit; manual audit required')
        if not decoder.eof:
            pos = offset + 2
            continue
        total += len(decoded)
        if total > LIMIT:
            raise ValueError('archive exceeds decompression limit; manual audit required')
        streams.append(decoded)
        pos = len(data) - len(decoder.unused_data)
    if not streams or not streams[0].lstrip().startswith(b'<dc '):
        raise ValueError('unsupported ARD encoding; manual audit required')
    return streams


def audit(path, data):
    if len(data) > LIMIT:
        return ['file exceeds inspection limit; manual audit required']
    streams = [data]
    if Path(path).suffix.lower() == '.ard':
        try:
            streams += archive_streams(data)
        except ValueError as exc:
            return [str(exc)]
    findings = []
    for index, stream in enumerate(streams):
        for encoding in ('utf-8', 'utf-16le', 'utf-16be'):
            for finding in text_findings(stream.decode(encoding, errors='ignore')):
                findings.append(f'stream {index}: {finding}')
    return sorted(set(findings))


def git(*args):
    return subprocess.check_output(['git', *args])


def paths_changed(*args):
    return [p.decode('utf-8', errors='surrogateescape') for p in git(*args).split(b'\0') if p]


def check_blobs(entries):
    failed, seen = False, set()
    for ref, path in entries:
        if not candidate(path):
            continue
        blob = git('rev-parse', f'{ref}:{path}').strip().decode()
        if (blob, Path(path).suffix.lower()) in seen:
            continue
        seen.add((blob, Path(path).suffix.lower()))
        problems = audit(path, git('cat-file', 'blob', blob))
        for problem in problems:
            print(f'BLOCKED {path}: {problem}', file=sys.stderr)
            failed = True
    return failed


def outgoing_entries(remote):
    commits = set()
    for line in sys.stdin:
        local_ref, local_sha, remote_ref, remote_sha = line.split()
        if set(local_sha) == {'0'}:  # deleting a remote ref sends no new data
            continue
        if set(remote_sha) == {'0'}:
            args = ('rev-list', local_sha, '--not', f'--remotes={remote}')
        else:
            args = ('rev-list', f'{remote_sha}..{local_sha}')
        commits.update(git(*args).decode().splitlines())
    for commit in sorted(commits):
        for path in paths_changed('diff-tree', '--root', '--no-commit-id', '-r', '-m',
                                  '--name-only', '--diff-filter=ACMRT', '-z', commit):
            yield commit, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--files', nargs='+')
    mode.add_argument('--staged', action='store_true')
    mode.add_argument('--pre-push', metavar='REMOTE')
    args = parser.parse_args()
    try:
        if args.files:
            failed = False
            for name in args.files:
                problems = audit(name, Path(name).read_bytes())
                for problem in problems:
                    print(f'BLOCKED {name}: {problem}', file=sys.stderr)
                    failed = True
                if not problems:
                    print(f'PASS {name}: no known credential patterns found')
        elif args.staged:
            paths = paths_changed('diff', '--cached', '--name-only', '--diff-filter=ACMRT', '-z')
            failed = check_blobs(('', path) for path in paths)
        else:
            failed = check_blobs(outgoing_entries(args.pre_push))
        return 1 if failed else 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        # Fail closed on parser/Git errors without printing file contents.
        print('Credential check failed: ' + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
