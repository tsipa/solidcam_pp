import argparse
import json
import re
from pathlib import Path

from .engine import Engine
from .trace import parse_trace, sanitize


def main():
    parser = argparse.ArgumentParser(description='Offline GPPL procedure harness')
    commands = parser.add_subparsers(dest='command', required=True)
    capture = commands.add_parser('capture', help='Sanitize trace inputs into portable JSON')
    capture.add_argument('trace', type=Path)
    capture.add_argument('destination', type=Path)
    capture.add_argument('--encoding', default='utf-8-sig')
    capture.add_argument('--rotary', action='store_true', help='Extract numeric rotary cases with trace-output oracle')
    run = commands.add_parser('run', help='Execute a GPPL procedure with explicit state')
    run.add_argument('pp', type=Path)
    run.add_argument('procedure')
    run.add_argument('state', type=Path, help='JSON with state and optional changed maps')
    args = parser.parse_args()
    if args.command == 'capture':
        events = parse_trace(args.trace.read_text(encoding=args.encoding))
        if args.rotary:
            context = dict(angle_4x_around_x=0, angle=0, cpos=0, apos=0,
                           bpos=0, x_angle_const_z=0)
            cases = []
            for index, event in enumerate(events):
                for key in context:
                    if key in event.parameters:
                        context[key] = event.parameters[key]
                if event.name not in ('line_5x', 'move_5x', 'line_4x', 'move_4x'):
                    continue
                for line in event.output:
                    match = re.search(r'\bA=(?:ACN|ACP|DC)\(([+-]?[\d.]+)\)', line)
                    if match:
                        cases.append({'event': index, 'state': dict(context),
                                      'expected_a': float(match[1])})
            if not cases:
                raise ValueError('No rotary output oracle found in trace')
            fixture = {'schema': 1, 'description': 'Numeric motion inputs and A angles observed in SolidCAM trace; no paths or identities',
                       'initial_context': 'Zero coordinate/transform angles before first corresponding event',
                       'cases': cases}
        else:
            fixture = {'schema': 1, 'events': sanitize(events)}
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        args.destination.write_text(json.dumps(fixture, indent=2) + '\n', encoding='utf-8')
        print(f'Captured {len(events)} events')
    else:
        inputs = json.loads(args.state.read_text(encoding='utf-8'))
        engine = Engine.from_path(args.pp)
        engine.set(**inputs['state'])
        engine.changed.update({k.lower(): v for k, v in inputs.get('changed', {}).items()})
        engine.call(args.procedure)
        print(json.dumps({'state': engine.state, 'changed': engine.changed,
                          'output': engine.output}, indent=2))


if __name__ == '__main__':
    main()
