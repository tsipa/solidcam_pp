"""CLI: python -m pp_tests.gppl {validate,contracts,interface,replay,coverage,policies} ...

validate   load the whole GPP, print diagnostics and lint (exit 1 with --strict on errors)
contracts  per-event inferred SolidCAM inputs and change flags
interface  CAM-interface inventory of the whole GPP
replay     replay a capture JSON or a raw SolidCAM GPPL debug trace (per-event NC diff)
coverage   render a GPPL_COVERAGE_OUT file as markdown (+ coverage-gap split)
policies   list every semantics policy, its choices and the presets
"""
import argparse
import json
import sys
from pathlib import Path

from .analysis import Analysis
from .calltrace import CallTrace
from .coverage import load_for
from .policies import CHOICES, PRESETS
from .program import load_program
from .session import compare_with_trace, replay_file
from .vmid import load_vmid


def _policies(name, sets):
    changes = dict(item.split('=', 1) for item in sets)
    return PRESETS[name](**changes)


def _program(path, policies):
    return load_program(Path(path).read_text(encoding='utf-8-sig'), policies.lexing_key(), policies.max_expr_depth)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m pp_tests.gppl', description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)

    def common(sub, default_policy):
        sub.add_argument('gpp', type=Path)
        sub.add_argument('--vmid', type=Path)
        sub.add_argument('--policy', choices=sorted(PRESETS), default=default_policy)
        sub.add_argument('--set', action='append', default=[], metavar='POLICY=VALUE')

    validate = commands.add_parser('validate', help='parse and lint the whole GPP')
    common(validate, 'session')
    validate.add_argument('--json', action='store_true')
    validate.add_argument('--strict', action='store_true', help='exit 1 on any error diagnostic')
    validate.add_argument('--coverage', type=Path, help='GPPL_COVERAGE_OUT file: add the coverage-gap split')
    validate.add_argument('--quiet-info', action='store_true', help='omit info diagnostics from the listing')
    contracts = commands.add_parser('contracts', help='per-event inferred SolidCAM inputs and flags')
    common(contracts, 'session')
    interface = commands.add_parser('interface', help='CAM-interface inventory')
    common(interface, 'session')
    replay = commands.add_parser('replay', help='replay a capture JSON or a raw GPPL debug trace')
    common(replay, 'session')
    replay.add_argument('events', type=Path)
    replay.add_argument('--nc', type=Path, help='write NC text')
    replay.add_argument('--trace', type=Path, help='write the GPPL-debug-trace-like log')
    replay.add_argument('--coverage', type=Path, help='write coverage markdown')
    replay.add_argument('--annotate', action='store_true', help='print NC with event and @proc:line provenance')
    replay.add_argument('--tolerance', type=float, default=5e-4, help='numeric tolerance for the trace diff')
    replay.add_argument('--emitted-by', metavar='TEXT', help='print the call chains that emitted TEXT')
    report = commands.add_parser('coverage', help='render a coverage JSON as markdown')
    report.add_argument('gpp', type=Path)
    report.add_argument('coverage_json', type=Path)
    report.add_argument('out', type=Path)
    report.add_argument('--vmid', type=Path)
    commands.add_parser('policies', help='list policies and presets')
    args = parser.parse_args(argv)

    if args.command == 'policies':
        rows = {'policy': list(CHOICES), 'compat': [], 'session': [], 'best_guess': []}
        for preset in ('compat', 'session', 'best_guess'):
            values = PRESETS[preset]().describe()
            rows[preset] = [values[name] for name in CHOICES]
        for index, name in enumerate(CHOICES):
            print(f"{name:24} {'|'.join(CHOICES[name]):45} compat={rows['compat'][index]:14} "
                  f"session={rows['session'][index]:14} best_guess={rows['best_guess'][index]}")
        return 0

    vmid = load_vmid(args.vmid) if getattr(args, 'vmid', None) else None
    if args.command == 'coverage':
        program = load_program(args.gpp.read_text(encoding='utf-8-sig'))
        coverage = load_for(program, args.coverage_json)
        text = coverage.markdown(program)
        split = Analysis(program, vmid).coverage_split(coverage)
        text += '\n# Never-executed statements by cause\n\n' + '\n'.join(f'- {k}: {v}' for k, v in split.items()) + '\n'
        args.out.write_text(text, encoding='utf-8')
        print(text.splitlines()[0])
        for key, value in split.items():
            print(f'  {key}: {value}')
        return 0

    policies = _policies(args.policy, args.set)
    if args.command in ('validate', 'contracts', 'interface'):
        program = _program(args.gpp, policies)
        analysis = Analysis(program, vmid, policies)
        diagnostics = analysis.run()
        if args.command == 'contracts':
            print(json.dumps(analysis.event_contracts(), indent=2))
            return 0
        if args.command == 'interface':
            print(json.dumps(analysis.interface(), indent=2))
            return 0
        summary = analysis.summary()
        summary['policy'] = args.policy + ''.join(f',{item}' for item in args.set)
        if args.coverage:
            summary['coverage_split'] = analysis.coverage_split(load_for(program, args.coverage))
        if args.json:
            print(json.dumps({'summary': summary, 'diagnostics': [d.as_dict() for d in diagnostics]}, indent=2))
        else:
            print(json.dumps(summary, indent=1))
            for diagnostic in diagnostics:
                if args.quiet_info and diagnostic.severity == 'info':
                    continue
                print(diagnostic)
        errors = program.errors(policies, strict=True)
        return 1 if (args.strict and errors) else 0

    # replay
    tracer = CallTrace() if args.emitted_by else None
    session, result = replay_file(args.gpp, args.events, vmid=args.vmid, policy=args.policy,
                                  stop_on_error=True, tracer=tracer, **dict(item.split('=', 1) for item in args.set))
    if args.nc:
        args.nc.write_text(result.nc_text, encoding='utf-8')
    if args.trace:
        args.trace.write_text(result.trace_text, encoding='utf-8')
    if args.coverage:
        args.coverage.write_text(result.coverage.markdown(session.engine.program), encoding='utf-8')
    print(session.annotated() if args.annotate else result.nc_text, end='')
    summary = result.summary()
    status = 0 if result.ok else 2
    if result.recorded is not None:
        diff = compare_with_trace(result.recorded, result, args.tolerance)
        summary['trace_diff'] = diff
        if diff and status == 0:
            status = 3
    if tracer is not None:
        summary['emitted_by'] = [{'chain': chain, 'origin': f'@{origin[0]}:{origin[1]}', 'text': text}
                                 for chain, origin, text in tracer.emitted_by(args.emitted_by)]
    print(json.dumps(summary, indent=1), file=sys.stderr)
    return status


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BrokenPipeError:          # e.g. piped into head
        sys.exit(0)
