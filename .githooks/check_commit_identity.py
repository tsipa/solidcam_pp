"""Refuse commits whose author or committer is not the repository owner.

Owner rule 2026-10-28: every commit is authored and committed as tsipa740@gmail.com, never under
another identity (git falls back to user@host when user.email is not set). Commits made in GitHub's
web interface keep the owner as author and have 'GitHub <noreply@github.com>' as committer (the
first commit of main); that committer is allowed.

--staged          pre-commit: the author and committer git is about to use
--pre-push REMOTE pre-push: every outgoing commit (refs on stdin as git sends them)
--history [REV]   every commit reachable from REV (default HEAD)
"""
import argparse
import subprocess
import sys

OWNER = 'tsipa740@gmail.com'
COMMITTERS = {OWNER, 'noreply@github.com'}
FORMAT = '--format=%H %ae %ce'


def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.PIPE).decode('utf-8', errors='replace')


def email(ident):
    """The address of a git ident line 'Name <address> 1700000000 +0000'."""
    return ident[ident.index('<') + 1:ident.index('>')] if '<' in ident and '>' in ident else ''


def problems(author, committer, where):
    found = []
    if author.lower() != OWNER:
        found.append(f'{where}: author {author or "(none)"} is not {OWNER}')
    if committer.lower() not in COMMITTERS:
        found.append(f'{where}: committer {committer or "(none)"} is not {OWNER}')
    return found


def logged_problems(*rev_args):
    found = []
    for line in git('log', FORMAT, *rev_args).splitlines():
        sha, author, committer = (line.split(' ') + ['', ''])[:3]
        found += problems(author, committer, sha[:12])
    return found


def outgoing_problems(remote, lines):
    found = []
    for line in lines:
        if not line.strip():
            continue
        local_ref, local_sha, remote_ref, remote_sha = line.split()
        if set(local_sha) == {'0'}:  # deleting a remote ref sends no commits
            continue
        if set(remote_sha) == {'0'}:
            found += logged_problems(local_sha, '--not', f'--remotes={remote}')
        else:
            found += logged_problems(f'{remote_sha}..{local_sha}')
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--staged', action='store_true')
    mode.add_argument('--pre-push', metavar='REMOTE')
    mode.add_argument('--history', nargs='?', const='HEAD', metavar='REV')
    args = parser.parse_args()
    try:
        if args.staged:
            found = problems(email(git('var', 'GIT_AUTHOR_IDENT')), email(git('var', 'GIT_COMMITTER_IDENT')),
                             'new commit')
        elif args.pre_push:
            found = outgoing_problems(args.pre_push, sys.stdin)
        else:
            found = logged_problems(args.history)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        # Fail closed: an identity git cannot tell is not the owner's.
        print(f'Commit identity check failed ({type(exc).__name__}); set user.name and user.email '
              f'to Sergei Iudin <{OWNER}>.', file=sys.stderr)
        return 1
    for problem in found:
        print(f'BLOCKED {problem}', file=sys.stderr)
    if found:
        print(f'Commits must be authored as Sergei Iudin <{OWNER}>: git config user.email {OWNER}', file=sys.stderr)
    return 1 if found else 0


if __name__ == '__main__':
    raise SystemExit(main())
