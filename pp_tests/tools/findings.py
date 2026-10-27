"""Regenerate or check tests/PP_FINDINGS.md from the registry and the test markers.

usage (from the repository root):
    python -m pp_tests.tools.findings --write    rewrite the file
    python -m pp_tests.tools.findings --check    exit 1 if the file is out of date
    python -m pp_tests.tools.findings            print the rendered document
"""
import argparse
import sys

from . import use_test_support


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true', help='rewrite tests/PP_FINDINGS.md')
    group.add_argument('--check', action='store_true', help='fail if tests/PP_FINDINGS.md is stale')
    args = parser.parse_args(argv)
    use_test_support()
    from support import findings
    text = findings.render()
    if args.write:
        findings.DOCUMENT.write_text(text, encoding='utf-8', newline='\n')
        print(f'wrote {findings.DOCUMENT}')
        return 0
    if args.check:
        current = findings.DOCUMENT.read_text(encoding='utf-8') if findings.DOCUMENT.exists() else ''
        if current != text:
            print(f'{findings.DOCUMENT} is out of date; run python -m pp_tests.tools.findings --write')
            return 1
        print('up to date')
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
