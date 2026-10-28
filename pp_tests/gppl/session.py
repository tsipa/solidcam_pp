"""Full-session driver: replay a SolidCAM event stream (init_post ..
end_of_file) through the real GPP; produce the NC file, a GPPL-debug-trace-like
log that ``pp_tests/trace.py`` parses back, per-event provenance, input-contract
warnings, inline per-event expectations and coverage; compare against a recorded
trace.

Event semantics (each a documented assumption, see DESIGN.md section 5):
* event parameters are written into the global SolidCAM variables and persist;
* each supplied parameter gets ``active(x)=true`` and a change flag: the flag
  recorded in the trace (``T``/``F``) if present, otherwise per policy
  ``event_input_flags`` (differs from the value SolidCAM supplied last, or always
  true);
* ``prev_command``/``next_command`` are synthesised when the capture lacks them;
* an event whose procedure the PP does not define is recorded and skipped;
* redacted free-text strings from trace.sanitize() get format-valid stand-ins
  (reported); redacted branch-driving CAM enums stop the replay.

Fixture format: trace.py capture JSON ``{"schema": 1, "events": [{"name",
"parameters", "changed"}]}`` plus optional ``"session": {"user_params",
"overrides" (alias "after_init"), "policy", "policies", "expect"}`` and an optional per-event
``"expect": {"blocks", "contains", "absent", "order", "state", "error"}``.
"""
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import sysvars
from .analysis import Analysis
from .calltrace import Tracer
from .errors import UnsupportedGPPL
from .policies import NUMERIC, PRESETS
from .runtime import Engine
from .vmid import load_vmid

ENUM_TOKEN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*$')
TRACE_INDENT = ' ' * 22
PARAM_INDENT = ' ' * 20


# ------------------------------------------------------------------ records --
@dataclass
class EventRecord:
    index: int
    name: str
    params: dict
    flags: dict
    called: bool = False
    nc: list = field(default_factory=list)
    error: object = None
    substitutions: dict = field(default_factory=dict)
    contract_warnings: list = field(default_factory=list)
    console: list = field(default_factory=list)
    failures: list = field(default_factory=list)


@dataclass
class ReplayReport:
    events: list
    nc_text: str
    trace_text: str
    errors: list
    coverage: object
    failures: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors and not self.failures

    def summary(self):
        called = sum(1 for event in self.events if event.called)
        return {'events': len(self.events), 'procedures_called': called,
                'nc_lines': len(self.nc_text.splitlines()), 'errors': [str(e) for e in self.errors],
                'expectation_failures': list(self.failures), 'notes': list(self.notes),
                'substitutions': sum(len(event.substitutions) for event in self.events),
                'contract_warnings': sum(len(event.contract_warnings) for event in self.events)}


# ------------------------------------------------------------------- tracer --
def format_param(name, value, flag=None, number_style='exact'):
    if isinstance(value, bool):
        return f'{name}:{"true" if value else "false"}'
    if isinstance(value, (int, float)):
        text = repr(float(value)) if number_style == 'exact' else f'{float(value):.3f}'
        if text.endswith('.0') and number_style == 'exact':
            text = text[:-2] + '.000'
        return f'{name}:{text}' + ('' if flag is None else ('T' if flag else 'F'))
    text = str(value)
    if ENUM_TOKEN.match(text) and text.lower() not in ('true', 'false') and text.lower() in _ENUMS:
        return f'{name}:{text}'
    return f"{name}:'" + text.replace("'", "''") + "'"


_ENUMS = {value for value in sysvars.CONSTANTS.values() if isinstance(value, str)} | {'yes', 'no', 'no_action'}


class TraceRecorder(Tracer):
    """Writes a log in the shape pp_tests/trace.py parses:

        (1)@line_5x ==> apos:-90.000T dir5a:cw
                            ..> xpos:1.250F
        (2)@usr_line ==>
                              > G1 X10
    """

    def __init__(self, number_style='exact', params_per_line=6):
        self.lines = []
        self.pending = None
        self.number_style = number_style
        self.params_per_line = params_per_line

    def on_call(self, depth, proc, arguments, site):
        if depth == 1 and self.pending is not None:
            params, flags = self.pending
            self.pending = None
            tokens = [format_param(k, v, flags.get(k), self.number_style) for k, v in params.items()]
            head, rest = tokens[:self.params_per_line], tokens[self.params_per_line:]
            self.lines.append(f'(1)@{proc.name} ==> ' + ' '.join(head) if head else f'(1)@{proc.name} ==>')
            while rest:
                chunk, rest = rest[:self.params_per_line], rest[self.params_per_line:]
                self.lines.append(PARAM_INDENT + '..> ' + ' '.join(chunk))
        else:
            self.lines.append(f'({depth})@{proc.name} ==>')

    def on_console(self, kind, text):
        self.lines.append(f'{TRACE_INDENT}! {kind}: {text}')

    def output_line(self, text, continuation=False):
        self.lines.append(f'{TRACE_INDENT}>{"+" if continuation else " "}{text}')

    def text(self):
        return '\n'.join(self.lines) + '\n'


# ----------------------------------------------------------------- policies --
def resolve_policies(policy=None, changes=None, extension=None, env=True):
    """Preset (argument, fixture 'policy', or 'session') + fixture 'policies' +
    explicit changes; GPPL_POLICY (preset and/or name=value) is applied last, so
    an unchanged fixture can be re-run under any hypothesis."""
    extension = extension or {}
    preset = policy or extension.get('policy') or 'session'
    merged = dict(extension.get('policies', {}))
    merged.update(changes or {})
    text = os.environ.get('GPPL_POLICY', '') if env else ''
    parts = [part.strip() for part in text.split(',') if part.strip()]
    if parts and '=' not in parts[0]:
        preset = parts.pop(0)
    for part in parts:
        if '=' not in part:
            raise ValueError(f'GPPL_POLICY: expected name=value, got {part!r}')
        name, value = (item.strip() for item in part.split('=', 1))
        merged[name] = int(value) if name in NUMERIC else value
    if preset not in PRESETS:
        raise ValueError(f'unknown policy preset {preset!r}; known: {sorted(PRESETS)}')
    return PRESETS[preset](**merged)


# ------------------------------------------------------------------ session --
class Session:
    def __init__(self, source, vmid=None, policies=None, trace=True, number_style='exact', tracer=None):
        if isinstance(vmid, (str, Path)):
            vmid = load_vmid(vmid)
        self.vmid = vmid
        self.engine = Engine(source, policies=policies or resolve_policies(), vmid=vmid)
        self.analysis = Analysis(self.engine.program, vmid)
        self._inputs = {}
        self.recorder = TraceRecorder(number_style) if trace else None
        if tracer is not None and self.recorder is not None:
            from .calltrace import Tee
            self.engine.tracer = Tee(self.recorder, tracer)
        else:
            self.engine.tracer = self.recorder or tracer
        self.events = []
        self.notes = []
        self.started = False
        self._emitted = {}       # id(NCLine) -> characters already written to the trace
        self._scan_from = 0
        self._supplied = {}      # last value SolidCAM supplied per variable

    @classmethod
    def from_paths(cls, gpp, vmid=None, **kwargs):
        return cls(Path(gpp).read_text(encoding='utf-8-sig'), vmid=vmid, **kwargs)

    # ---- lifecycle -------------------------------------------------------
    def start(self, overrides=None, params=None, user_params=None):
        """Seed VMID user parameters, run @init_post, then apply overrides."""
        if self.started:
            raise UnsupportedGPPL('session already started')
        engine = self.engine
        if self.vmid is not None:
            for name, param in self.vmid.all_params().items():
                engine.state[name] = param.value
                engine.changed[name] = False
                engine.active[name] = True
        for name, value in (user_params or {}).items():
            engine.state[name.lower()] = value
            engine.changed[name.lower()] = False
            engine.active[name.lower()] = True
        self.started = True
        record = self.event('init_post', params or {})
        for name, value in (overrides or {}).items():
            engine.state[name.lower()] = value
        return record

    def event(self, name, params=None, changed=None, expect=None):
        if not self.started and name.lower().lstrip('@') != 'init_post':
            self.start()
        name = name.lower().lstrip('@')
        engine = self.engine
        index = len(self.events)
        params = {key.lower(): value for key, value in (params or {}).items()}
        changed = {key.lower(): value for key, value in (changed or {}).items()}
        record = EventRecord(index, name, {}, {})
        for key, value in params.items():
            if value == sysvars.REDACTED:
                if key in sysvars.REPLAY_ENUMS:
                    self.events.append(record)
                    record.error = UnsupportedGPPL(
                        f'@{name}: {key} was redacted by trace.sanitize(); this CAM enum selects PP '
                        f'branches and cannot be guessed (capture with sanitize_for_replay)')
                    raise record.error
                substitute = sysvars.REDACTION_SUBSTITUTES.get(key, 'REDACTED')
                record.substitutions[key] = substitute
                value = substitute
            if sysvars.system_type(key) == 'integer' and isinstance(value, float) and value.is_integer():
                value = int(value)
            if key in changed:
                flag = bool(changed[key])
            elif engine.policies.event_input_flags == 'supplied_or_true':
                flag = True
            else:
                # SolidCAM compares with the value *it* supplied last, not with
                # whatever the PP may have assigned to the variable since.
                flag = key not in self._supplied or self._supplied[key] != value
            self._supplied[key] = value
            engine.state[key] = value
            engine.changed[key] = flag
            engine.active[key] = True
            record.params[key] = value
            record.flags[key] = flag
        record.contract_warnings = self._contract_warnings(name)
        engine.stream.event = index
        line_mark = max(len(engine.stream.lines) - 1, 0)   # the open line may get its first text now
        console_mark = len(engine.console)
        if self.recorder is not None:
            numeric_flags = {k: v for k, v in record.flags.items()
                             if isinstance(record.params[k], (int, float)) and not isinstance(record.params[k], bool)}
            self.recorder.pending = (record.params, numeric_flags)
        self.events.append(record)
        try:
            if name in engine.program.procedures:
                record.called = True
                engine.call(name)
            elif self.recorder is not None:
                self.recorder.pending = None
                self.recorder.lines.append(f'(1)@{name} ==> ' + ' '.join(
                    format_param(k, v, None) for k, v in record.params.items()) + '   ; no procedure in PP')
        except UnsupportedGPPL as exc:
            record.error = exc
            if expect is None or 'error' not in expect:
                raise
        finally:
            record.console = engine.console[console_mark:]
            record.nc = [line.full for line in engine.stream.lines_for_event(index, line_mark)]
            self._flush_trace(index)
            if engine.policies.event_flag_reset == 'globals_after_event':
                for key in engine.changed:
                    engine.changed[key] = False
        if expect:
            record.failures = check_expectations(record, expect, engine)
        return record

    def finish(self):
        self.engine.stream.finish()
        return self.engine.stream.text()

    # ---- contracts -------------------------------------------------------
    def _contract_warnings(self, name):
        if name not in self.engine.program.procedures:
            return []
        inputs = self._inputs.get(name)
        if inputs is None:
            inputs = self._inputs[name] = self.analysis.external_inputs(name)
        state = self.engine.state
        constants = self.engine._constants or {}
        return sorted(var for var in inputs if var not in state and var not in constants)

    # ---- trace -----------------------------------------------------------
    def _flush_trace(self, index):
        if self.recorder is None:
            return
        for line in self.engine.stream.lines_since(self._scan_from):
            done = self._emitted.get(id(line))
            full = line.full
            if done is None:
                if line.event == index:
                    self.recorder.output_line(full)
                    self._emitted[id(line)] = len(full)
            elif len(full) > done:
                self.recorder.output_line(full[done:], continuation=True)
                self._emitted[id(line)] = len(full)
        self._scan_from = len(self.engine.stream.lines)

    # ---- replay ------------------------------------------------------------
    def replay(self, events, overrides=None, user_params=None, stop_on_error=True,
               synthesize_commands=True, expect=None):
        """Replay events (capture dicts or trace.py Events). A leading init_post
        event starts the session (or is skipped if the caller already started it)."""
        events = [_normalize_event(event) for event in events]
        if synthesize_commands:
            names = [event['name'] for event in events]
            for position, event in enumerate(events):
                params = event['parameters']
                if params.get('prev_command', sysvars.REDACTED) == sysvars.REDACTED:
                    params['prev_command'] = '@' + names[position - 1] if position else ''
                if params.get('next_command', sysvars.REDACTED) == sysvars.REDACTED:
                    params['next_command'] = '@' + names[position + 1] if position + 1 < len(names) else ''
        errors = []
        if events and events[0]['name'] == 'init_post':
            first = events.pop(0)
            if self.started:
                self.notes.append('leading init_post event skipped: session already started')
            else:
                self.start(overrides=overrides, params=first['parameters'], user_params=user_params)
        elif not self.started:
            self.start(overrides=overrides, user_params=user_params)
        for event in events:
            try:
                self.event(event['name'], event['parameters'], event.get('changed'), event.get('expect'))
            except UnsupportedGPPL as exc:
                errors.append(exc)
                if stop_on_error:
                    break
        nc_text = self.finish()
        failures = [failure for record in self.events for failure in record.failures]
        if expect:
            failures += check_text(nc_text, expect, 'whole NC')
        return ReplayReport(self.events, nc_text, self.recorder.text() if self.recorder else '',
                            errors, self.engine.coverage, failures, list(self.notes))

    def annotated(self):
        return self.engine.stream.annotated()


# -------------------------------------------------------------- expectations --
def _normalize_line(line):
    return ' '.join(line.split())


def check_text(text, expect, label):
    failures = []
    lines = [_normalize_line(line) for line in text.splitlines() if line.strip()]
    if 'blocks' in expect and lines != [_normalize_line(b) for b in expect['blocks']]:
        failures.append(f'{label}: blocks {lines!r} != {expect["blocks"]!r}')
    for token in expect.get('contains', []):
        if token not in text:
            failures.append(f'{label}: missing {token!r}')
    for token in expect.get('absent', []):
        if token in text:
            failures.append(f'{label}: unexpected {token!r}')
    position = 0
    for token in expect.get('order', []):
        found = text.find(token, position)
        if found < 0:
            failures.append(f'{label}: {token!r} missing or out of order')
            break
        position = found + len(token)
    for token, count in expect.get('count', {}).items():
        actual = sum(1 for line in lines if line.startswith(token))
        if actual != count:
            failures.append(f'{label}: {actual} line(s) start with {token!r}, expected {count}')
    return failures


def check_expectations(record, expect, engine):
    """Per-event oracle: blocks/contains/absent/order/count on the event's NC
    lines, state after the event, and an expected error (regex)."""
    label = f'event #{record.index} @{record.name}'
    failures = check_text('\n'.join(record.nc), expect, label)
    for key, value in expect.get('state', {}).items():
        actual = engine.state.get(key.lower(), '<missing>')
        if actual != value:
            failures.append(f'{label}: state {key}={actual!r} != {value!r}')
    pattern = expect.get('error')
    if pattern is not None:
        if record.error is None:
            failures.append(f'{label}: expected error /{pattern}/, none raised')
        elif not re.search(pattern, str(record.error)):
            failures.append(f'{label}: error {str(record.error)!r} does not match /{pattern}/')
    return failures


def _normalize_event(event):
    if hasattr(event, 'name') and hasattr(event, 'parameters'):     # trace.Event
        return {'name': event.name.lower(), 'parameters': dict(event.parameters),
                'changed': dict(event.changed)}
    result = {'name': event['name'].lower().lstrip('@'), 'parameters': dict(event.get('parameters', {})),
              'changed': dict(event.get('changed', {}))}
    if 'expect' in event:
        result['expect'] = event['expect']
    return result


def sanitize_for_replay(events):
    """Like trace.sanitize() (strings redacted) but keeps REPLAY_ENUMS values that
    look like CAM vocabulary, so the capture stays replayable."""
    vocabulary = re.compile(r'[@A-Za-z0-9_ .-]{0,32}$')
    result = []
    for event in events:
        event = _normalize_event(event)
        values = {}
        for key, value in event['parameters'].items():
            keep = (not isinstance(value, str) or value.lower() in _ENUMS
                    or (key in sysvars.REPLAY_ENUMS and vocabulary.match(value)))
            values[key] = value if keep else sysvars.REDACTED
        result.append({'name': event['name'], 'parameters': values, 'changed': event['changed']})
    return result


def load_events(path):
    """Read a capture JSON ({'schema':1,'events':[...]} plus optional 'session'
    extension) or a raw SolidCAM GPPL debug trace. Returns (events, extension,
    recorded) where ``recorded`` is the list of trace.py Events (with their NC
    output) for a raw trace, else None."""
    text = Path(path).read_text(encoding='utf-8-sig', errors='replace')
    try:
        data = json.loads(text)
    except ValueError:
        from ..trace import parse_trace           # pp_tests/trace.py, unchanged
        recorded = parse_trace(text)
        return list(recorded), {}, recorded
    if data.get('schema') != 1 or 'events' not in data:
        raise ValueError('expected trace capture JSON with schema 1 and events')
    return data['events'], data.get('session', {}), None


# --------------------------------------------------------------- comparison --
WORD = re.compile(r'([A-Za-z#$_]+(?:=(?:ACP|ACN|DC)\()?)([+-]?(?:\d+(?:\.\d*)?|\.\d+))(\)?)$')


def compare_nc(expected_lines, actual_lines, tolerance=5e-4):
    """Word-level NC comparison with numeric tolerance; returns mismatch strings."""
    problems = []
    expected = [line.rstrip() for line in expected_lines if line.strip()]
    actual = [line.rstrip() for line in actual_lines if line.strip()]
    for position in range(max(len(expected), len(actual))):
        want = expected[position] if position < len(expected) else None
        got = actual[position] if position < len(actual) else None
        if want is None or got is None:
            problems.append(f'line {position}: expected {want!r}, got {got!r}')
            continue
        want_words, got_words = want.split(), got.split()
        if len(want_words) != len(got_words):
            problems.append(f'line {position}: expected {want!r}, got {got!r}')
            continue
        for a, b in zip(want_words, got_words):
            ma, mb = WORD.match(a), WORD.match(b)
            if ma and mb and ma[1] == mb[1] and ma[3] == mb[3]:
                if abs(float(ma[2]) - float(mb[2])) > tolerance:
                    problems.append(f'line {position}: {a} vs {b}')
            elif a != b:
                problems.append(f'line {position}: {a!r} vs {b!r} in {got!r}')
    return problems


def join_trace_output(rows):
    """Re-join '+continuation' rows written by TraceRecorder for cross-event lines."""
    lines = []
    for row in rows:
        if row.startswith('+') and lines:
            lines[-1] = lines[-1] + ' ' + row[1:]
        else:
            lines.append(row)
    return lines


def compare_with_trace(trace_events, report, tolerance=5e-4):
    """Per-event NC diff between a recorded trace (trace.py Events) and a replay."""
    replayed = [event for event in report.events if event.name != 'init_post']
    recorded = [event for event in trace_events if event.name != 'init_post']
    problems = []
    if [e.name for e in recorded] != [e.name for e in replayed[:len(recorded)]]:
        problems.append('event sequence differs')
    for position, (want, got) in enumerate(zip(recorded, replayed)):
        for problem in compare_nc(join_trace_output(want.output), got.nc, tolerance):
            problems.append(f'event {position} @{got.name}: {problem}')
    return problems


def replay_file(gpp, events_path, vmid=None, policy=None, stop_on_error=True, tracer=None, **policy_changes):
    """Replay a capture JSON or raw trace through ``gpp``. Returns (session, report);
    for a raw trace ``report.trace_diff`` holds the per-event NC comparison."""
    events, extension, recorded = load_events(events_path)
    policies = resolve_policies(policy, policy_changes, extension)
    session = Session.from_paths(gpp, vmid=vmid, policies=policies, tracer=tracer)
    overrides = dict(extension.get('overrides', {}))
    overrides.update(extension.get('after_init', {}))         # alias: option overrides after @init_post
    report = session.replay(events, overrides=overrides,
                            user_params=extension.get('user_params'), stop_on_error=stop_on_error,
                            synthesize_commands=True, expect=extension.get("expect"))
    report.recorded = recorded
    return session, report
