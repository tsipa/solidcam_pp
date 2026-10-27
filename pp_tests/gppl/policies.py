"""Explicit, documented semantics policies.

Every place where real SolidCAM GPPL behaviour is not known for certain is a
named policy here; nothing is silently chosen elsewhere in the package.

* ``Policies()`` (preset ``compat``) reproduces the legacy engine
  (pp_tests/engine.py, kept verbatim as ``gppl.legacy``). For each policy the
  first entry of ``CHOICES`` is the legacy behaviour, and a test enforces that.
  Constructs the legacy engine rejected and whose meaning is uncertain (Print,
  trace, the extended format grammar) stay rejected under compat.
* ``Policies.session()`` adds what a whole SolidCAM session needs where the
  legacy engine had no defined behaviour.
* ``Policies.best_guess()`` adds the alternatives that the GPP source itself
  argues for (DESIGN.md, section 5).

``GPPL_POLICY`` re-runs any unchanged suite under another hypothesis:
``GPPL_POLICY=session`` or ``GPPL_POLICY=compat,change_on_equal_assign=clear``
or just ``GPPL_POLICY=tonum=atof`` (applied on top of the caller's base preset).
"""
import os
from dataclasses import dataclass, fields, replace

CHOICES = {
    # --- lexing ---------------------------------------------------------------
    'quote_escape': ('double', 'none'),          # 'can''t' -> can't | two adjacent literals
    'string_escapes': ('literal', 'c'),          # '\n' stays 2 chars | becomes LF
    # --- constructs the legacy engine rejected -------------------------------
    'print_stmt': ('error', 'console'),          # Print 'x': unsupported | recorded in engine.console
    'trace_stmt': ('error', 'ignore'),           # trace "all":5: unsupported | no-op
    'input_stmt': ('abort', 'scripted'),         # input: stop | answer from engine.scripted_inputs
    'format_grammar': ('legacy', 'extended'),    # 'N.M[(p)]' only | '+', (n), (*k), /k, <pre>/<suf>, 0-pad
    # --- values / assignment --------------------------------------------------
    'integer_assign': ('keep', 'truncate', 'round_half_away'),
    'typed_assign': ('off', 'coerce'),           # coerce values to the declared type
    'undeclared_assign': ('allow', 'error'),
    'local_scoping': ('dynamic', 'lexical'),     # callee sees caller locals?
    'logical_default': ('zero', 'false'),        # value of a fresh 'global logical'
    # --- change flags ---------------------------------------------------------
    'change_on_equal_assign': ('keep', 'clear', 'clear_user', 'set'),
    'declared_flag': ('none', 'false'),          # flag created by a 'global' declaration
    'missing_change_flag': ('error', 'false'),
    'modal_missing_flag': ('error', 'unchanged'),
    'event_flag_reset': ('none', 'globals_after_event'),
    'event_input_flags': ('supplied_or_compare', 'supplied_or_true'),
    # --- expressions ----------------------------------------------------------
    'string_compare': ('case_sensitive', 'case_insensitive'),
    'mixed_compare': ('python', 'error'),        # 'a' eq 1 -> False | error
    'tonum': ('strict', 'atof'),                 # tonum('G5'): error | 0 (C atof prefix)
    'string_index': ('error', 'python', 'clamp'),  # left(s,-1), substr(s,0,n)
    'modulo': ('python', 'truncate'),            # -7 % 3: 2 (floor) | -1 (C fmod)
    'constants': ('none', 'registry'),           # XY, CW, COMP_LEFT, G81 ... resolve
    # --- formatting -----------------------------------------------------------
    'rounding': ('python', 'half_away'),
    'trailing_zeros': ('trim', 'keep'),          # 12.50000 -> 12.5 | keep D digits
    'flag_p': ('trim', 'keep_point'),            # meaning of '(p)' when the value is integral
    'flag_n': ('trim', 'no_point'),
    'typed_default_formats': ('off', 'on'),      # numeric_def_f / integer_def_f
    'logical_output': ('python', 'numeric'),     # True -> 'True' | '1'
    'plus_zero': ('no_sign', 'plus'),            # '+8.5' applied to 0
    # --- NC stream (never touches the legacy fragment list) -------------------
    'skipline': ('join_next_nb', 'ignore'),
    'empty_lines': ('drop', 'keep'),
    'block_numbers': ('blknum_exist', 'never'),
    # --- loading --------------------------------------------------------------
    'load_errors': ('lazy', 'raise'),            # raise only when executed | refuse to load
}

# string_index: the legacy engine used Python slicing, so left('abc', -1) gave 'ab'.
# That is a Python artefact, not a GPPL rule; compat therefore raises (loud) and
# 'python' keeps the old value for exact differential runs. It is listed first
# among the semantic choices only for documentation; LEGACY_VALUES records it.
LEGACY_VALUES = {'string_index': 'python'}

NUMERIC = {'default_precision': int, 'max_steps': int, 'max_depth': int, 'max_expr_depth': int}


@dataclass(frozen=True)
class Policies:
    quote_escape: str = 'double'
    string_escapes: str = 'literal'
    print_stmt: str = 'error'
    trace_stmt: str = 'error'
    input_stmt: str = 'abort'
    format_grammar: str = 'legacy'
    integer_assign: str = 'keep'
    typed_assign: str = 'off'
    undeclared_assign: str = 'allow'
    local_scoping: str = 'dynamic'
    logical_default: str = 'zero'
    change_on_equal_assign: str = 'keep'
    declared_flag: str = 'none'
    missing_change_flag: str = 'error'
    modal_missing_flag: str = 'error'
    event_flag_reset: str = 'none'
    event_input_flags: str = 'supplied_or_compare'
    string_compare: str = 'case_sensitive'
    mixed_compare: str = 'python'
    tonum: str = 'strict'
    string_index: str = 'error'
    modulo: str = 'python'
    constants: str = 'none'
    rounding: str = 'python'
    trailing_zeros: str = 'trim'
    flag_p: str = 'trim'
    flag_n: str = 'trim'
    typed_default_formats: str = 'off'
    logical_output: str = 'python'
    plus_zero: str = 'no_sign'
    skipline: str = 'join_next_nb'
    empty_lines: str = 'drop'
    block_numbers: str = 'blknum_exist'
    load_errors: str = 'lazy'
    default_precision: int = 3
    max_steps: int = 100000
    max_depth: int = 64
    max_expr_depth: int = 100

    def __post_init__(self):
        for f in fields(self):
            allowed = CHOICES.get(f.name)
            value = getattr(self, f.name)
            if allowed and value not in allowed:
                raise ValueError(f'policy {f.name}={value!r}; allowed: {allowed}')
            if f.name in NUMERIC and (not isinstance(value, int) or value < 0):
                raise ValueError(f'policy {f.name}={value!r} must be a non-negative integer')

    def with_(self, **changes):
        return replace(self, **changes)

    # ---- presets -----------------------------------------------------------
    @classmethod
    def compat(cls, **changes):
        return cls(**changes)

    @classmethod
    def session(cls, **changes):
        """Compat plus the runtime model a whole session needs where the legacy
        engine had no behaviour: declared globals get change flag false,
        enumeration constants (XY, CW, COMP_LEFT, VMID drill cycles) resolve,
        numeric_def_f/integer_def_f act as default formats, logicals are
        booleans, the format grammar of this PP family is accepted, Print goes to
        the console and trace is a no-op."""
        base = dict(declared_flag='false', constants='registry', typed_default_formats='on',
                    logical_default='false', format_grammar='extended', print_stmt='console',
                    trace_stmt='ignore')
        base.update(changes)
        return cls(**base)

    @classmethod
    def best_guess(cls, **changes):
        """Session plus the alternatives supported by evidence inside the GPP."""
        base = dict(tonum='atof', input_stmt='scripted', change_on_equal_assign='clear_user',
                    quote_escape='none', string_escapes='c', string_index='clamp')
        base.update(changes)
        return cls.session(**base)

    @classmethod
    def from_env(cls, text=None, base='compat'):
        """Parse 'preset[,name=value...]' (GPPL_POLICY syntax). Without a preset the
        assignments apply to ``base`` (compat for Engine, session for Session)."""
        if text is None:
            text = os.environ.get('GPPL_POLICY', '')
        key = (text, base)
        cached = _ENV_CACHE.get(key)
        if cached is not None:
            return cached
        parts = [part.strip() for part in text.split(',') if part.strip()]
        preset = base
        if parts and '=' not in parts[0]:
            preset = parts.pop(0)
        if preset not in PRESETS:
            raise ValueError(f'GPPL_POLICY: unknown preset {preset!r}; known: {sorted(PRESETS)}')
        changes = {}
        names = {f.name for f in fields(cls)}
        for part in parts:
            if '=' not in part:
                raise ValueError(f'GPPL_POLICY: expected name=value, got {part!r}')
            name, value = (item.strip() for item in part.split('=', 1))
            if name not in names:
                raise ValueError(f'GPPL_POLICY: unknown policy {name!r}')
            changes[name] = int(value) if name in NUMERIC else value
        policies = PRESETS[preset](**changes)
        _ENV_CACHE[key] = policies
        return policies

    def differences(self, other=None):
        other = other or Policies()
        return {f.name: getattr(self, f.name) for f in fields(self)
                if getattr(self, f.name) != getattr(other, f.name)}

    def lexing_key(self):
        return self.quote_escape + ('+c' if self.string_escapes == 'c' else '')

    def describe(self):
        return {f.name: getattr(self, f.name) for f in fields(self)}


PRESETS = {'compat': Policies.compat, 'session': Policies.session, 'best_guess': Policies.best_guess}
_ENV_CACHE = {}
