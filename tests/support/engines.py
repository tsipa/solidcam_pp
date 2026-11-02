"""Engine construction: the GPPL compatibility engine and the engine helpers.

The tests run on the GPPL engine (pp_tests/gppl, through pp_tests/engine.py).
This suite never edits it; every workaround below is tied to a registered
engine gap (tests/support/defects.py, ENGINE-xxx).

GpplCompatEngine is the engine Session uses: a subclass of the GPPL Engine that
maps the workaround switches onto engine policies (pp_tests/gppl/policies.py):
the 07 literal and right()/tostr() are native; Print -> print_stmt=console
(messages kept in engine.console, exposed as engine.messages); trace ->
trace_stmt=ignore; extended formats -> format_grammar=extended; right() of a
negative count -> string_index=clamp; default formats -> typed_default_formats=on;
declared global flags -> declared_flag=false; skipline -> the NC stream's
skipline policy (engine.output, the fragment list, never joins blocks;
engine.nc_text() returns the NC program view).

Workaround policy
-----------------
* Default-on workarounds only cover constructs the stock engine REJECTS with
  UnsupportedGPPL (Print, trace, extended numeric format descriptors, right()
  of a negative count; the leading-zero literal, right() and tostr(x:'fmt'),
  which the original engine rejected, are native). They are strictly
  additive: any path the stock engine can execute produces identical state and
  output under GpplCompatEngine.
* Emulations that would CHANGE results of paths the stock engine already runs
  (skipline block joining, numeric_def_f/integer_def_f default formats,
  declared globals starting with a false change flag) are opt-in keyword
  arguments, because their exact GPPL semantics are unverified.
"""
import copy
import re
import types

from pp_tests.engine import Engine, UnsupportedGPPL  # noqa: F401  (UnsupportedGPPL re-exported)
from pp_tests.gppl.formats import parse_format, render_number
from pp_tests.gppl.policies import Policies

from .paths import pp_source

# Workaround switch -> registered engine gap it compensates.
WORKAROUNDS = {
    'leading_zero_literals': 'ENGINE-006',
    'string_builtins': 'ENGINE-007',
    'print_statement': 'ENGINE-008',
    'trace_statement': 'ENGINE-018',
    'extended_formats': 'ENGINE-018',
    'skipline': 'ENGINE-002',
    'default_formats': 'ENGINE-003',
    'declared_global_flags': 'ENGINE-005',
}
_DEFAULT_OPTIONS = dict(leading_zero_literals=True, string_builtins=True, print_statement=True,
                        trace_statement=True, extended_formats=True, skipline=False, default_formats=False,
                        declared_global_flags=False)


def declared_globals(source):
    """Lower-case names declared with `global <type> ...` in a GPP source."""
    names = {}
    for raw in source.splitlines():
        line = raw.split(';', 1)[0].strip()
        match = re.fullmatch(r'global\s+(numeric|integer|logical|string)\s+(.+)', line, re.I)
        if match:
            for name in match[2].replace(',', ' ').split():
                names[name.lower()] = match[1].lower()
    return names


def fresh_engine(source=None, engine_class=None, **engine_options):
    """A ready-to-run engine for source (default: the tested GPP).

    engine_class defaults to the stock Engine. The GPPL engine caches the
    parsed program itself (by source digest), so a new engine is constructed
    every time.
    """
    text = pp_source() if source is None else source
    engine_class = Engine if engine_class is None else engine_class
    return engine_class(text, **engine_options)


def adopt_state(engine, source, engine_class=None, **engine_options):
    """Engine for another source (e.g. a mutant) carrying engine's state and flags.

    Replaces the repeated `candidate = Engine(source); candidate.set(**engine.state);
    candidate.changed.update(engine.changed)` pattern of the legacy tests.
    """
    if engine_class is None:
        engine_class = type(engine)
        if not engine_options and isinstance(engine, GpplCompatEngine):
            engine_options = dict(engine.options)
    candidate = fresh_engine(source, engine_class, **engine_options)
    candidate.state.update(engine.state)
    candidate.changed.update(engine.changed)
    return candidate


def fork_engine(engine):
    """Independent copy of an engine mid-session (state, flags, output, messages).

    The parsed program stays shared. The NC stream, the active flags and the
    console are copied too, so the copy never writes into the original's stream.
    """
    clone = copy.copy(engine)
    clone.state, clone.changed = dict(engine.state), dict(engine.changed)
    clone.output, clone.stack = list(engine.output), []
    clone.active = dict(engine.active)
    clone.frames = []
    clone.console = list(engine.console)
    clone.scripted_inputs = list(engine.scripted_inputs)
    stream = copy.copy(engine.stream)
    stream.engine = clone
    stream.lines = list(engine.stream.lines)
    stream.current = copy.copy(engine.stream.current)
    clone.stream = stream
    return clone


class GpplCompatEngine(Engine):
    """GPPL engine with the workaround switches mapped onto policies.

    On top of the caller's policies (default: Policies.from_env(), so
    GPPL_POLICY still applies):
      leading_zero_literals  native (07 is 7); the switch has no effect
      string_builtins        right()/tostr() are native; string_index=clamp
                             (right(s, n <= 0) is '')
      print_statement        print_stmt=console (engine.messages lists the texts)
      trace_statement        trace_stmt=ignore
      extended_formats       format_grammar=extended
      skipline               the NC stream joins on skipline=false
                             (policy skipline=join_next_nb) only when True;
                             engine.output never joins
      default_formats        typed_default_formats=on
      declared_global_flags  declared_flag=false (set when the declaration runs)
    """

    def __init__(self, source, *, policies=None, **options):
        unknown = set(options) - set(_DEFAULT_OPTIONS)
        if unknown:
            raise TypeError(f'unknown GpplCompatEngine options: {sorted(unknown)}')
        values = dict(_DEFAULT_OPTIONS, **options)
        self.options = types.MappingProxyType(values)
        changes = {'skipline': 'join_next_nb' if values['skipline'] else 'ignore'}
        if values['string_builtins']:
            changes['string_index'] = 'clamp'
        if values['print_statement']:
            changes['print_stmt'] = 'console'
        if values['trace_statement']:
            changes['trace_stmt'] = 'ignore'
        if values['extended_formats']:
            changes['format_grammar'] = 'extended'
        if values['default_formats']:
            changes['typed_default_formats'] = 'on'
        if values['declared_global_flags']:
            changes['declared_flag'] = 'false'
        base = policies if policies is not None else Policies.from_env()
        super().__init__(source, policies=base.with_(**changes))

    @property
    def messages(self):
        """Texts of the Print statements executed so far."""
        return [text for kind, text in self.console if kind == 'print']

    def format_number(self, value, descriptor):
        """Render a number under this engine's format grammar and policies."""
        spec = parse_format(descriptor, self.policies.format_grammar) if descriptor else None
        return render_number(value, spec, self.policies)
