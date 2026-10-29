"""Regenerate or check the NC pins of the recorded SolidCAM replays (tests/fixtures/recorded_cam_nc_pins.json).

usage (from the repository root; NAME is recorded_cam_001 .. recorded_cam_005, default all five;
recorded_cam_001 takes about 60 s and 2 GB):
    python -m pp_tests.tools.recorded_pins --write [NAME ...]   replay and rewrite their pins
    python -m pp_tests.tools.recorded_pins --check [NAME ...]   exit 1 and show the first differing lines
    python -m pp_tests.tools.recorded_pins --nc DIR [NAME ...]  write their normalized NC to DIR/NAME.nc
The pins are what tests/test_recorded_replays.py compares; PP_TEST_SOURCE selects another GPP.
"""
import argparse
import sys
from pathlib import Path

from . import use_test_support


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true', help='rewrite the pins of the named recordings')
    group.add_argument('--check', action='store_true', help='fail if a named recording differs from its pin')
    group.add_argument('--nc', metavar='DIR', help='write the normalized NC of the named recordings')
    parser.add_argument('names', nargs='*', metavar='NAME')
    args = parser.parse_args(argv)
    use_test_support()
    from support import recorded
    names = args.names or list(recorded.RECORDINGS)
    unknown = sorted(set(names) - set(recorded.RECORDINGS))
    if unknown:
        parser.error(f'unknown recordings {unknown}; known: {list(recorded.RECORDINGS)}')
    pins = recorded.load_pins()
    status = 0
    for name in names:
        result = recorded.replay(name)
        stop = f'stopped at event {result.errors[0][0]} @{result.errors[0][1]}' if result.errors else 'end_of_file'
        if args.nc:
            path = Path(args.nc) / f'{name}.nc'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(result.nc, encoding='utf-8', newline='\n')
            print(f'{name}: {stop}, wrote {path}')
        elif args.write:
            pins[name] = recorded.make_pin(result)
            print(f"{name}: {stop}, {pins[name]['nc_lines']} NC lines, sha256 {pins[name]['sha256'][:16]}")
        elif name not in pins:
            print(f'{name}: no pin')
            status = 1
        elif recorded.make_pin(result)['sha256'] != pins[name]['sha256']:
            print(recorded.mismatch_message(name, pins[name], result))
            status = 1
        else:
            print(f'{name}: {stop}, matches its pin')
        for error in result.errors:
            print(f'  error: event {error[0]} @{error[1]} ({error[2]} {error[3]}): {error[4]}')
        for line in result.post_errors:
            print(f'  {line}')
    if args.write:
        recorded.write_pins(pins)
        print(f'wrote {recorded.PINS}')
    return status


if __name__ == '__main__':
    sys.exit(main())
