# GPPL engine: a SolidCAM session emulator on an immutable, validated IR

Python 3.10+ (also runs on 3.9), standard library only, no `eval`/`exec`, no
Python `ast`. It replaces the original `pp_tests/engine.py`, which is now a
24-line shim over the `pp_tests/gppl/` package; `GPPL_ENGINE=legacy` selects the
original engine (`pp_tests/gppl/legacy.py`, a verbatim copy). The numbers below
were measured on the post before the review fixes; the harness tests live in
`tests_engine/`.
`examples/` and `tools/` below refer to reports and helper scripts produced during
the engine review; they are not part of the repository.

## 1. Results

| measure | legacy engine | final engine |
|---|---|---|
| existing 35 tests, test code unchanged | OK, 5.8 to 6.2 s | **OK, 0.69 s** (0.94 s on a busy host) |
| same suite under `GPPL_POLICY=session` | n/a | OK |
| rollback switch `GPPL_ENGINE=legacy` (verbatim legacy engine behind the shim) | n/a | OK, 6.2 s |
| shadow run: every Engine of the legacy suite mirrored by the legacy engine (`tests_engine/shadow_v1.py`) | n/a | **831 top-level calls, 6 expressions, 34 raised in both, 0 mismatches** (also against the repository's own `pp_tests/engine.py` file) |
| historical-fix revert matrix (26 commits, 14 reverse-applicable) | baseline | **identical**: same applicable commits, same per-revert failing tests and error counts (`examples/revert_matrix.txt`) |
| harness tests (`tests_engine`, 113 tests) | n/a | **OK in 11.3 s** (1 corpus test skipped unless `GPPL_CORPUS` is set; with it: OK) |
| whole GPP loaded and validated at construction | no (lines are only looked at when executed) | **95 procedures, 1479 statements, 201 globals, 46 entry points; 0 errors under the session policy** (strict load passes); cold load 39 ms, cached 0.02 ms, full lint 18 ms |
| GPP statement coverage | 534/1479 with the review's monkey patch (2 of those lines were run only by in-memory mutants) | legacy suite 532/1479 = 36.0 %; **suite + 6 session fixtures 1388/1479 = 93.8 %**; branch outcomes 32.9 % to **81.4 %** |
| never-executed statements explained | no | suite only: 806 live code without test input, 130 dead under the shipped configuration, 11 in unreachable procedures; after sessions: 57 / 23 / 11 |
| full session `init_post .. end_of_file` | impossible | 6 synthetic sessions (39 events replay in 59 ms) with inline per-event oracles; raw SolidCAM trace replay with a per-event, word-level NC diff |
| judges' adversarial corpora (384 hand cases, 5,399 random expressions, 3,000 random output statements) | baseline | 0 raw Python exceptions, 0 timeouts, 0 unintended value differences (section 9) |

## 2. Basis and what was grafted

**Basis.** Combined judge totals: session-emulator 38 + 44 = **82**, incremental
38.5 + 42.5 = 81, parser-first 41 + 39.5 = 80.5. The final engine therefore keeps
the session-emulator's runtime model (event driver, NC output stream with
skipline and block numbers, trace-format log and diff, contract analysis,
format engine, VMID reader, system-variable registry) and its five synthetic
session fixtures, which still produce byte-identical NC.

**Problems the judges found in the basis, all fixed** (each has a test in
`tests_engine/test_grafts.py`, `test_session.py` or `test_policies.py`):

| problem | fix |
|---|---|
| `replay` crashed with "session already started" on every capture from `python -m pp_tests capture` (first event `init_post`) | `Session.replay` starts the session from a leading `init_post` event (or skips it if already started); `replay_file` no longer calls `start()` itself. Test runs the repository's own capture CLI end to end. |
| `GPPL_COVERAGE_OUT` overwrote the file (one CLI run per session reported 59.7 % instead of 93.8 %) | coverage store keyed by GPP source digest, merged into the file at exit (read, merge, atomic replace, `fcntl` lock where available) |
| no `GPPL_POLICY` switch | `GPPL_POLICY=preset[,name=value...]` reaches every Engine and every fixture replay |
| tuple IR (`item[5]`) and a string-kind if-chain in the executor | frozen dataclass nodes with `Span`, class-dispatch tables for compilation and execution |
| defaults silently differed from legacy: `string_index=clamp`, `'+8.5'`, `'5.0(n)'`, `'5.3()'`, `' 5.3'` accepted, `1 <> 2` evaluated, `trace` no-op, `Print` accepted | `Policies()` reproduces legacy: format grammar `legacy`, `print_stmt=error`, `trace_stmt=error`, `<>` rejected; `string_index` raises (see 5.1); the old behaviour is one policy switch away (`Policies.session()`) |
| `global v` while a local/parameter `v` is active created and leaked a global | the declaration is a no-op when the name is shadowed, exactly as in legacy |
| format on a string literal (`{'abc':'5.3'}`) rejected | accepted like legacy: formats apply to numbers only |
| `if(...)` / `while(...)` gave a misleading "endif without if" | block structure is kept; the condition reports "'if(' needs a space before the condition" |
| 150 nested parentheses, a 3,000-term sum or 1,500 unary minuses raised a raw `RecursionError` at load; 62 nested calls inside nested blocks failed | expression depth capped (policy `max_expr_depth`, default 100) with a located syntax error that is deferred to the procedure; precedence-climbing parser (about 4 Python frames per nesting level); procedures execute from a flat instruction list, so 600 nested ifs run and the 64-call limit is the only depth limit |
| `tonum(1)` returned `1` instead of legacy `1.0` | returns `float` like legacy |

**Grafts from the runners-up** (all implemented and tested):

| graft | source | where |
|---|---|---|
| immutable typed IR with spans, class dispatch | parser-first | `nodes.py`, `expr.py` (`_COMPILERS`), `runtime.py` (`_HANDLERS`) |
| recursion hardening (cap, deferred diagnostic, flat execution) | correctness judge | `expr.py`, `program.py`, `nodes.Instr` |
| missing procedure and arity checks at load; strict load (`load_errors=raise`) also rejects code outside procedures and missing `endp` | incremental, correctness judge | `program.py` (`_check_calls`, `structural`) |
| permanent randomized differential test against the legacy engine plus the shadow runner as CI checks | incremental + session-emulator | `tests_engine/test_differential.py` (1,500 expressions, 600 output statements, 300 rotary and 150 arc states), `tests_engine/shadow_v1.py` |
| coverage keyed by source digest, merged across processes | incremental | `coverage.py` |
| `CallTrace` with `emitted_by('G75')` (call chain with call sites) | incremental | `calltrace.py`; CLI `replay --emitted-by TEXT` |
| `%`, exponent literals, `trace` as explicit choices (policy `modulo`; `1e3` stays accepted as in legacy; policy `trace_stmt`) | incremental, correctness judge | `policies.py`, `expr.py` |
| CAM-interface inventory and per-event change-flag contracts | incremental | `analysis.py` (`interface`, `external_flags`); CLI `interface`, `contracts` |
| per-event inline oracles in session JSON (`blocks/contains/absent/order/count/state/error`) and whole-NC expectations | parser-first | `session.py` (`check_expectations`); `tests_engine/fixtures/oracle_session.json` |
| session fields `after_init` (alias of `overrides`) and expected errors | incremental | `session.py` |
| replay of raw SolidCAM trace text with `--tolerance` | incremental | `session.load_events`, CLI `replay` (exit 3 on NC differences) |
| config-dead analysis, coverage-gap split, policy-sensitive literal sites | parser-first | `analysis.py` (`config_constants`, `_reach`, `coverage_split`, `_policy_sites`) |
| policy-sensitivity tool | incremental | `tools/policy_sensitivity.py` |
| PR-sequenced migration with rollback (legacy engine moved behind the shim) | incremental, pragmatic judge | `pp_tests/gppl/legacy.py`, `GPPL_ENGINE`, section 11 |
| ASCII-only numbers and identifiers; `call @f` and `@name(` spacing as in legacy | correctness judge | `lexer.py`, `program.py` |

**Deliberately not taken:** incremental's strict typing of logical arithmetic
(`true + true` is 2 in legacy; kept), rejecting `%` (kept with a policy) and
rejecting `1e3` (legacy accepted it; kept); parser-first's lenient spacing
(`call@f`, `@test (numeric a)`, `if(`), which legacy rejects; `int()`/`frac()`
builtins whose meaning (truncate or floor) is unknown.

## 3. Architecture

```
 .gpp ─► lexer.py ─► expr.py / program.py ─► Program (immutable IR + diagnostics, cached by
          tokens        parse, compile        source digest, lexing policy and depth cap)
                                                   │
 .vmid ─► vmid.py ─┐                               ├─► runtime.py  Engine (legacy API, frames, flags,
 sysvars.py ───────┤                               │      │        formats, flat execution, coverage, tracer)
 policies.py ──────┴──── consulted everywhere ─────┤      └─► output.py  NC stream (nb/nl, skipline,
                                                   │                     block numbers, provenance)
                                                   ├─► session.py  events, flags, contracts, trace log,
                                                   │               expectations, trace diff, replay_file
                                                   ├─► analysis.py lint, contracts, CAM interface,
                                                   │               config-dead, coverage-gap split
                                                   └─► coverage.py, calltrace.py
 pp_tests/engine.py: shim (GPPL_ENGINE=legacy -> gppl/legacy.py, the verbatim old engine)
```

| module | lines | role |
|---|---|---|
| `engine.py` (shim) | 24 | `Engine`, `UnsupportedGPPL`, `uncomment`, `Policies`; rollback switch |
| `errors.py` | 78 | `UnsupportedGPPL` hierarchy with one GPPL call chain; `Diagnostic` |
| `policies.py` | 199 | every uncertain semantic; presets; `GPPL_POLICY` parsing |
| `lexer.py` | 135 | comment stripping (legacy `uncomment` rule), one ASCII tokenizer; flags doubled quotes |
| `nodes.py` | 372 | frozen dataclass IR (12 expression, 4 output-item, 12 statement kinds), walkers, `Procedure`, `Instr` |
| `expr.py` | 349 | precedence-climbing parser with depth caps; closures compiled through a class-dispatch table |
| `builtins.py` | 138 | builtin registry with provenance ('used' by the GPP family or 'assumed') |
| `formats.py` | 160 | `legacy` and `extended` format grammars, rendering policies |
| `program.py` | 479 | whole-file loader: statements, block matching (tree **and** flat code in one pass), diagnostics, call checks, policy diagnostics |
| `runtime.py` | 484 | `Engine`: variable model, change/active flags, formats, flat execution, statement handlers |
| `output.py` | 133 | NC output stream next to the legacy fragment list |
| `session.py` | 504 | session driver, trace recorder, expectations, trace comparison, capture/trace loading |
| `analysis.py` | 506 | static analysis and lint |
| `coverage.py` | 175 | digest-keyed statement/branch coverage, cross-process merge, markdown |
| `calltrace.py` | 135 | tracer protocol, `CallTrace`, `Tee` |
| `sysvars.py`, `vmid.py`, `__main__.py` | 144, 95, 149 | SolidCAM runtime model, VMID reader (refuses DOCTYPE/ENTITY), CLI |
| **total new code** | **4,274** | plus `legacy.py` (342, verbatim copy), harness tests and tools (1,891) |

## 4. Data model

**IR (nodes.py).** Expressions: `Num Str(doubled) Bool Var Flag(change|active)
Unary Binary Compare(paren) Logical(paren) Call Formatted FmtLit FmtVar`. Output
items: `Text(doubled) NewLine Value(expr, fmt, hint, names, fn) Modal(items,
names)`; a modal group's `names` come from `Var`/`Flag` nodes only, never from
function names or string contents. Statements carry `Span(line, col)` and the
comment-free text: `Assign FlagAssign If(then, orelse, else_line, end_line) While
CallProc Output Declare Input Abort Print Trace Bad`. Nodes that evaluate
expressions also carry `fn`, the closure compiled once at load.

**Two procedure shapes from one pass.** `Procedure.body` is the statement tree
(analysis, lint, coverage reports, the legacy `(line, text)` view).
`Procedure.code` is a flat list of `Instr(op, line, stmt, fn, target)` with
`EXEC`, `BRANCH` (if/while condition; jump when false) and `JUMP`. The runtime
executes it with a program counter, so block nesting never uses the Python stack.

**Program.** Parsed once per (source, lexing policy, depth cap) and shared by
every Engine (the legacy suite builds about 700). It records `diagnostics`
(syntax, structure, calls), `structural` (outside code, missing/stray `endp`),
`globals` (declared types, known statically) and `policy_diagnostics(policies)`
(constructs that raise under a given policy). Fatal at load, as in legacy: an
invalid header and a duplicate procedure. Everything else is deferred: a `Bad`
node or a poisoned condition raises only when executed, and a procedure with a
structural error refuses to run before any side effect.

**Engine.** `state`, `changed`, `output` stay plain dicts/lists (tests copy them
between engines). Locals and parameters live in frames; lookups follow the
`local_scoping` policy (dynamic like legacy, or lexical); flags live with the
owning scope; types come from frame declarations, then `global` declarations,
then VMID parameters, then the registry. `engine.procedures` is a private copy
per engine, so mutating it cannot affect another engine. Errors: everything is an
`UnsupportedGPPL`; subclasses `GPPLSyntaxError`, `GPPLRuntimeError(gppl_stack)`,
`MissingInput`, `PostprocessorStopped`, `PostAbort`; one message plus
`[call chain: @b:5 <- @a:2]`. No raw Python exception escapes `call()` or
`expression()`.

## 5. Semantics policies

`Policies()` (preset `compat`) reproduces the legacy engine. The first value in
`CHOICES` is the default and a test enforces it. `Policies.session()` adds what a
whole session needs where legacy had no behaviour; `Policies.best_guess()` adds
what the GPP itself argues for. `python -m pp_tests.gppl policies` prints the
table; `tools/policy_sensitivity.py` measures what each alternative changes
(`examples/policy_sensitivity_full.txt`). "Suite" below is the unchanged 35-test
suite run under `GPPL_POLICY=compat,<policy>=<value>`; "sessions" are the six
fixtures under `session,<policy>=<value>`.

| policy | compat (= legacy) | session / best_guess | evidence and measured sensitivity | confidence |
|---|---|---|---|---|
| change_on_equal_assign | keep | keep / **clear_user** | clear: suite 156 failures (arc end points lost); set: 3 failures; clear_user: suite OK. Sessions under keep emit 7x M9 after the first M8 and G187 P2 (not a Sinumerik code); clear_user satisfies all four PP invariants (section 7.4) | hypothesis, low-medium; one real trace decides |
| declared_flag | none (reading `change()` of a fresh global raises) | false | every session stops at `@usr_hsm_mode:1085 change(nG187_E_gpp)` without it | medium |
| event_input_flags | trace T/F, else differs from the value SolidCAM last supplied | same | `usr_ct_after` writes `xpos = nTcXnext`; comparing with state hid the first drill XY | medium |
| event_flag_reset | none | none | globals_after_event loses G41 on the move after `@compensation` | low |
| skipline (NC stream only) | join_next_nb (one-shot per assignment) | same | `'N'iTcnumber` + `'G17 G64 G90'`, `G43 H` + Z; `ignore`: suite OK, every session changes (52 to 2,066 differing NC lines by difflib count) | medium-high (join), medium (one-shot) |
| empty_lines, block_numbers (stream only) | drop, blknum_exist | same | block numbers only in options_session (107 lines) | low-medium |
| trailing_zeros | trim | trim | real trace excerpts `X132`, `Z15.8333`; keep: suite 31 failures | high for non-integral values |
| flag_p, flag_n, plus_zero | trim, trim, no sign | same | unobserved; keep_point changes 1 to 9 session lines | low |
| rounding | python (binary, ties to even) | same | half_away changes nothing observed | low |
| typed_default_formats | off (3 decimals) | on (`numeric_def_f`/`integer_def_f`) | no observed difference in the sessions | medium-high |
| format_grammar | legacy (`N.M[(p)]`) | extended | `'5.0(n)'` in `@Multiple_Fixtures` needs it; `'+8.5'` only in unused format variables | grammar: medium; meaning of `(n)`, `+`: low |
| quote_escape | double (`'can''t'`) | double / **none** | suite pins double (1 error under none); under double CYCLE84 prints `,0,'500` (lines 1883/1886, lint W-QUOTE-DOUBLING) | low-medium |
| string_escapes | literal | literal / **c** | `usr_ct_after` splits msg at `instr(msg,'\n')` with poz1-2/poz1+1: only right for one LF in a CRLF message | low-medium |
| tonum | strict (error) | strict / **atof** | `home_number`/`home_data` parse `'G54P4'` and fall back when 0 (C atof); machine_variants fixture sets atof | medium |
| string_index | **error** (legacy: Python slicing) | error / **clamp** | `left('abc',-1)` gave `'ab'`: a Python artefact, not a GPPL rule, so compat raises loudly; `python` keeps the legacy value | medium |
| integer_assign | keep | keep | 5 sensitive sites (620, 622, 629, 2620, 2622); no observed effect | unknown, low |
| typed_assign, undeclared_assign | off, allow | same | strictness options; undeclared=error: suite 4 errors | n/a |
| local_scoping | dynamic | dynamic | lexical changes nothing in suite or sessions | low |
| not precedence (fixed, documented) | `!` below comparisons, `and` above `or` | same | lint W-NOT-COMPARE: 0 sites in this GPP | low (irrelevant here) |
| string_compare, mixed_compare | case-sensitive, python | same | no effect; `mixed_compare=error` works as a strictness guard | low |
| modulo | python (floor) | same | `%` is unused by the GPP | low |
| constants | none | registry | XY/ZX/YZ/CW/CCW/COMP_*/D_Tapping + VMID drill cycles as lower-case strings (the suite's convention); every session stops without them | low-medium (values are opaque) |
| logical_default, logical_output | 0, `True`/`False` | false, python | cosmetic | low |
| print_stmt | error (legacy: unsupported statement) | console | `usr_4x_index` emits the same text via Print and an NC line, so Print is not NC output | medium |
| trace_stmt | error | ignore | debugging directive (commented out in this GPP) | high |
| input_stmt | abort | abort / **scripted** | SolidCAM shows a dialog; scripted answers, writes the POST ERROR block, then `abort` raises `PostAbort`; suite 25 failures (it pins stop-at-input) | high that it prompts |
| load_errors | lazy | lazy | `raise` fails the load on any error diagnostic, outside code or missing endp | n/a |
| max_steps, max_depth, max_expr_depth | 100000, 64, 100 | same | 100 nested parentheses is deliberate (legacy ran 150) | n/a |

### 5.1 Two departures from "default = legacy", both loud

* `string_index` defaults to `error`, not to legacy Python slicing: the legacy
  values (`left('abc',-1)='ab'`, `substr(s,0,3)=''`, `substr('2026',1,-1)='202'`)
  are artefacts. No test, session or GPP path reaches them; `string_index=python`
  restores them exactly for differential work.
* Constructs the legacy engine crashed on with a Python artefact are fixed
  (section 8): `07`, Python keywords as identifiers, call arguments containing
  commas, `call @p()`, doubled double quotes in output, function names in modal
  groups. These are not semantic choices.

## 6. Session replay and fidelity hooks

* **Event model.** `Session.start()` seeds VMID machine/job/drill-cycle
  parameters, runs `@init_post`, applies overrides (`after_init`). `event()`
  writes parameters, sets `active()` and change flags (trace T/F wins), records
  contract warnings, calls the procedure (skips and records events the PP does
  not define), and attributes NC lines, console output and errors to the event.
* **Inputs.** Capture JSON (`trace.py` schema plus an optional `session`
  extension) or a raw SolidCAM trace (`(1)@event ==>`). `trace.sanitize()`
  redactions: free text gets reported stand-ins; branch-driving enums
  (`d_drill_type`, `side`, `feed_type`, ...) stop the replay with a clear message;
  `sanitize_for_replay()` keeps them.
* **Oracles.** Per-event `expect` with `blocks/contains/absent/order/count/state/
  error`, plus whole-NC `session.expect`. New session tests need no Python.
  `oracle_session.json` catches the change-flag flips: under `clear` the arc loses
  `X50 Y20` and the M9 count changes; under `globals_after_event` `G41` disappears.
* **Trace log and diff.** The recorder writes a log that the unchanged
  `pp_tests/trace.py` parses back (names, parameters, numeric T/F flags,
  per-event NC); replaying the parsed log reproduces the NC byte for byte.
  `compare_with_trace` is a word-level per-event diff with numeric tolerance; the
  CLI replays raw trace text and exits 3 on differences.
* **Provenance.** Every NC line knows its event, `@proc:line` and call stack
  (`--annotate`); `CallTrace.emitted_by('M9')` gives the full call chains with
  call sites (`@start_of_job ... @usr_coolant_output:1045`).
* **Semantics probe.** The same stream under competing change-flag hypotheses
  (`SemanticsProbeTests`): only `clear_user` satisfies all four PP invariants.

## 7. Whole-GPP load and validation report

`python -m pp_tests.gppl validate GPP --vmid VMID --strict` (output in
`examples/validate_4x_gpp.session.txt` and `.json`):

* **Load.** 95 procedures, 1479 statements (Assign 643, FlagAssign 97, If 309,
  Output 229, CallProc 132, Declare 57, While 6, Input 2, Abort 2, Print 2), 201
  globals, 46 SolidCAM entry points. Session policy: **0 errors, 2 warnings, 71
  info**; strict load passes. Compat policy (`examples/validate_4x_gpp.compat.txt`):
  exactly the 5 constructs the legacy engine cannot run (3x `tostr(x:'5.0(n)')`
  at 2221/2229/2256, 2x `Print` at 2426/2456), plus 3 warnings for the unused
  `'+8.5'` format variables (65-67); strict compat load fails, as it should.
* **Warnings.** `W-QUOTE-DOUBLING` at 1883/1886: `',0,'''` in the G84/CYCLE84
  output; the legacy reading prints a stray apostrophe before the spindle speed.
* **Shipped configuration.** 84 configuration constants (assigned once,
  unconditionally, to a literal in `@init_post`'s closure); 37 branches with 147
  statements never run with them (for example `if bSubs` in `@start_of_job`, 21
  statements, because `bSubs = false` at line 180); `usr_trig_macro_call` and
  `usr_trig_macro_output` are reachable only through such branches;
  `usr_heightcomp_on/off` are never called.
* **Policy-sensitive sites.** `I-POLICY-INTEGER` at 620/622/629/2620/2622
  (`iWorkoffset = tonum(...)`), `I-POLICY-TONUM` (309, 620, 622, 629, 2104, ...),
  `I-POLICY-STMT` for the 2 inputs and 2 Prints. No `!` over an unparenthesised
  comparison.
* **Contracts and CAM interface** (`examples/event_contracts.json`,
  `examples/cam_interface.json`). Per event: inferred SolidCAM/VMID inputs, the
  change flags the event closure reads (`move_4x`: xpos/ypos/zpos; `arc`:
  feed/xpos/ypos/zpos), cross-event dependencies (`def_tool` reads `stock_*`
  from `start_of_file`). Whole GPP: 111 CAM inputs, 17 CAM inputs the GPP also
  rewrites (xpos, spin, shift_y, msg, part_name, ...), 8 change flags read for
  CAM variables, 18 runtime switches written but never read
  (`clear_change_after_gen`, `skipline`, `blknum_*`, `numeric_def_f`, ...).
* **Other posts from the repository history** (extracted read-only with
  `git show`): `Gmill_540v_3x.gpp` (1344 statements) and `Mach3_4X_Y.gpp` (212;
  uses `active()`, `trace`, `not`, `'7.0(*1000P)'`) load with 0 errors under the
  session policy (`GPPL_CORPUS=<dir>` enables `CorpusTests`).

## 8. Legacy defects fixed (each reproduced on the legacy engine inside its test)

`tests_engine/test_v1_defects.py` runs every repro against `pp_tests.gppl.legacy`
first, then checks the fix: leading-zero literal `07` (the GPP has
`iCoolantM5ON = 07`); Python-only syntax evaluated (`0x10`, `1_000`, `2j`,
`1<2<3`, `'ab'*2`, `'a' 'b'`, `'%s!'%5`); Python keywords rejected as
identifiers; negative string indexes wrapping; `tonum('nan'/'1_000'/'infinity')`;
raw `ZeroDivisionError`/`AttributeError`/`TypeError`/`ValueError` escaping;
function names and words inside string literals treated as modal-group
variables (and `changed['abs']` created); call arguments split on raw commas and
`call @p()`; local redeclaration, local-shadows-parameter and loop
redeclaration leaks; `5 = x` creating `state['5']`; `{"a""b"}` printing `ab`;
"list index out of range" for `else` without `if`; structural errors raised after
side effects; mis-nested `endw` executing; code after a stray `endp` silently
dropped; unexecuted unsupported code invisible; errors re-wrapped per frame;
`right()`/`tostr()` missing.

## 9. Compatibility evidence

* Unchanged suite OK (0.69 s); under `GPPL_POLICY=session` OK; shadow run 0
  mismatches over 831 calls; revert matrix identical; uncomment identical on the
  judge's 18 cases; the repository's `python -m pp_tests run` CLI works through
  the shim.
* Judges' corpora rerun against the final engine: of 384 hand cases, 203 behave
  exactly like legacy and 181 differ, every one reviewed: located messages instead
  of "pop from empty list", refusal before side effects, the defect fixes above,
  the policy-guarded constructs, and the depth cap (legacy ran 150 nested
  parentheses). Of 5,399 random expressions, 4,355 are identical, 222 fail in
  both, and 822 are rejected where legacy returned a value: chained comparisons and
  string arithmetic only, with no value differences. Of 3,000 random output
  statements, 2,751 are identical; 166 that legacy rejected now run (the
  function-name modal fix), 81 differ only by legacy's spurious `changed['abs']`,
  and 2 by the doubled double quote.
* `tests_engine/test_differential.py` keeps 2,550 randomized cases against the legacy
  engine as a permanent guard.

## 10. What it unlocks for testing this PP

* **Procedures the legacy engine cannot run at all** (reproduced by
  `tools/legacy_session_probe.py`, which drives the legacy engine through the same
  sessions with every session advantage): `@usr_sof_progname` (`right()`, line
  251) and `@usr_us_date`/`@usr_us_time` (`right()`, `tostr(:'5.0(p)')`), so the
  whole `@start_of_file` event; `@usr_coolant` with 30 bar through-coolant
  (`07`, line 990), and with it `@start_of_job`; `@Multiple_Fixtures`
  (`tostr(:'5.0(n)')`), and with it `@end_program`, `@end_of_file`, `@call_proc`
  and `@start_of_job` when `iNumber_of_Fixtures > 1`; the `@usr_4x_index` warning
  path (`Print`), reached from `@start_of_job`, `@fourth_axis` and `@call_proc`;
  `@home_number`/`@home_data` with home names such as `'G54P4'` (`tonum=atof`).
* **Coverage.** 57 procedures are never executed by the legacy suite; the
  sessions execute 55 of them (only the two dead `usr_heightcomp_*` remain):
  `init_post`, `start_of_file`, `def_tool`, `start_program`, `end_program`,
  `end_of_file`, `change_tool` and the whole `usr_ct*` family, `usr_coolant*`,
  `line`, stops (`usr_forcedstop`, `usr_stopm00_*`), `drill_point`, `end_drill`,
  `m_feed_spin`, `start_tool`, spindle output, `call_proc`/`proc`/`end_proc`/
  loops, `multiple_fixtures`, `move_4x`/`line_4x`, the trig macro and
  `home_data`. Statements 36.0 % to 93.8 %, branch outcomes 32.9 % to 81.4 %.
* **What to write next.** The coverage-gap split names the 57 live statements
  still without input and the 23 dead under the shipped configuration;
  `contracts` lists, per event, exactly which inputs and flags a fixture must
  supply.
* **Characterised PP behaviour** (`tests_engine/test_replay_findings.py`; hypotheses
  until a real trace confirms them): the first hole after `MCALL CYCLE83` is not
  repositioned; coolant is not restored after a same-tool `M0`; the
  multiple-fixtures cleanup writes 2002 delete markers for 2 temp files; the
  index warning is an uncommented NC block; CYCLE84 gets a stray apostrophe under
  doubled-quote lexing; `M9`/`M5` repeat after `M0` with a tool change;
  `@call_proc` prints the literal `cR1`; `bSubs` leaks the `G9999` sentinel; the
  `msg` split loses a character with literal escapes.
* **The one trace that settles the open semantics.** A real 2-tool job with a
  drill cycle, `M0`, compensation, an arc and a 4x index, captured with
  `sanitize_for_replay` semantics and replayed with
  `python -m pp_tests.gppl replay GPP trace.txt --vmid VMID`, decides
  `change_on_equal_assign` (7x M9?), skipline joining, quote/backslash lexing and
  number formatting at once.

## 11. Migration plan (small PRs, suite green and rollback available at every step)

Each PR is reviewable on its own (roughly 150 to 650 lines of code plus tests);
CI runs the unchanged suite on every step.

1. **Shim and legacy move (about 40 lines).** Copy `pp_tests/engine.py`
   verbatim to `pp_tests/gppl/legacy.py`; `engine.py` re-exports it. No behaviour
   change. Rollback: revert one file.
2. **Errors and policies (about 280 lines).** `errors.py`, `policies.py` with
   `GPPL_POLICY` parsing and `test_policies.py::test_choices_*`. Not wired yet.
3. **Lexer and IR (about 510 lines).** `lexer.py`, `nodes.py` with lexer/IR unit
   tests (ASCII, `07`, doubled-quote flag, frozen nodes, walkers).
4. **Expressions (about 490 lines).** `expr.py`, `builtins.py`; expression half
   of `test_differential.py` against `legacy.py` (1,500 random expressions,
   intended rejections only).
5. **Program loader (about 640 lines).** `program.py`, `formats.py`; whole-GPP
   load test (0 errors under session, the 5 compat errors), recursion tests.
6. **Runtime and switch-over (about 930 lines).** `runtime.py`, `output.py`,
   `coverage.py`, `calltrace.py`; the shim now defaults to the new engine and
   `GPPL_ENGINE=legacy` selects the old one. Gates: unchanged suite OK,
   `tests_engine/shadow_v1.py` 0 mismatches, `test_differential.py`, revert matrix
   identical. Rollback: `GPPL_ENGINE=legacy`, or revert the shim line.
7. **Session driver (about 750 lines plus fixtures).** `session.py`,
   `sysvars.py`, `vmid.py`, the six fixtures, `test_session.py`,
   `test_replay_findings.py`.
8. **Analysis and CLI (about 650 lines).** `analysis.py`, `__main__.py`,
   `test_static.py`; README section on `validate`, `contracts`, `replay`.
9. **CI hardening.** Add `python -m pp_tests.gppl validate <gpp> --vmid <vmid>
   --strict`, `python -m unittest discover -s tests_engine`, `tests_engine/shadow_v1.py`
   and a coverage job (`GPPL_COVERAGE_OUT`); retire `tools/cov_patch.py`.
10. **Real trace.** Extend `trace.py` capture to keep the replay enums
    (`sanitize_for_replay`), add one real session, set the `session` preset to the
    policies it supports, and replace the synthetic NC expectations it covers.
11. **Retire `legacy.py`** and the switch after the shadow run has stayed green
    for an agreed period; keep `test_differential.py` pinned to recorded outputs.

## 12. Risks and open questions

* **No ground truth offline.** Session semantics (flags, skipline, block numbers,
  format flags, escapes, constant values) are inferred from the GPP; synthetic NC
  expectations are characterisation, not an oracle.
* **The system-variable registry and event contracts were inferred from this
  GPP**, so "0 unknown identifiers" is partly circular (the Mach3 post shows 33
  registry gaps). Contract warnings are heuristics.
* **The trace log is trace-like**, parseable by `trace.py`, not byte-identical
  to SolidCAM's (column prefix, number style, lines continuing across events use
  a `>+` row).
* **Not implemented** (absent from this GPP): arrays, multi-line output, file I/O
  statements, `trace` levels, user-assigned `blknum_gen`, integer-digit overflow.
* **Dynamic local scoping** is kept for compatibility; lexical is one switch away
  and changes nothing here.
* **Depth cap.** Expressions deeper than 100 levels are rejected (legacy accepted
  150 parentheses); configurable.
* **Size.** 4,274 lines replace 342; the migration plan keeps each review small
  and every step reversible.

## 13. How to run

```bash
python3 -m unittest discover -s tests            # post tests (GPPL_ENGINE=legacy: original engine)
python3 -m unittest discover -s tests_engine     # engine harness (GPPL_CORPUS=<dir of .gpp> enables the corpus test)
python3 tests_engine/shadow_v1.py                # mirror every post-test Engine through the legacy engine
G=siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.gpp; V=${G%.gpp}.vmid
python3 -m pp_tests.gppl validate $G --vmid $V --strict
python3 -m pp_tests.gppl replay $G tests_engine/fixtures/oracle_session.json --vmid $V --annotate
python3 -m pp_tests.gppl replay $G <raw SolidCAM trace.txt> --vmid $V --tolerance 0.0005
GPPL_POLICY=session,change_on_equal_assign=clear_user python3 -m unittest discover -s tests
```
