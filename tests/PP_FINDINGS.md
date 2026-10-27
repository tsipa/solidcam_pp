# Registered findings: suspected PP defects, engine gaps, design questions

Generated from `tests/support/defects.py` (the registry) and the `@known_defect` / `@covers`
markers in `tests/test*.py`. Do not edit by hand; regenerate with

    python -m pp_tests.tools.findings --write

`tests/test_known_defect_registry.py` fails when this file is out of date.

The postprocessor is never changed by this suite. Each open suspected defect has exactly one
canonical test per facet, marked `@known_defect(id)`. The test asserts the correct behaviour
with an independent oracle; in the default run it is reported as a skip
("known defect ... reproduced"). Run it red with

    PP_STRICT_KNOWN_DEFECTS=1 python -m unittest discover -s tests -k <test name>

(PowerShell: `$env:PP_STRICT_KNOWN_DEFECTS = "1"` first). When the behaviour is fixed, the
default run fails with "no longer reproduces" until the entry is marked fixed (status and fixing
commit) and the marker becomes `@covers`: the test is then a regression guard (section Fixed).
Entries the owner accepted as intended are listed under Accepted and pinned by a
CHARACTERIZATION test. DESIGN entries are owner decisions: they are pinned with `@covers`
CHARACTERIZATION tests, never with `@known_defect`. ENGINE entries refer to the test engines:
the GPPL engine (`pp_tests/gppl`, default) and the original engine (`GPPL_ENGINE=legacy`);
an entry scoped to one engine is a plain guard on the other. Severity and confidence are after
the adversarial verifier corrections. GPP line numbers refer to `Gmill_540v_4x.gpp` at f1803b4.

## Summary

| kind | entries | high | medium-high | medium | low-medium | low | very-low | informational |
|---|---|---|---|---|---|---|---|---|
| pp | 58 | 2 | 1 | 18 | 5 | 31 | 1 | 0 |
| engine | 21 | 0 | 0 | 3 | 3 | 14 | 1 | 0 |
| design | 7 | 0 | 0 | 1 | 0 | 6 | 0 | 0 |

| kind | confirmed | uncertain | likely-engine-artifact |
|---|---|---|---|
| pp | 41 | 16 | 1 |
| engine | 15 | 5 | 1 |
| design | 4 | 3 | 0 |

| kind | open | fixed | accepted | partly fixed |
|---|---|---|---|---|
| pp | 48 | 9 | 1 | 1 |
| engine | 20 | 1 | 0 | 0 |
| design | 6 | 1 | 0 | 0 |

Engine scope: ENGINE-002, ENGINE-006, ENGINE-007, ENGINE-011, ENGINE-012, ENGINE-014, ENGINE-015 reproduce (in whole or in one facet) only on the legacy engine; ENGINE-021 only on the GPPL engine.

Canonical `@known_defect` tests: 78. `@covers` references: 55.

## Index of open entries

| id | severity | confidence | area | title | reproduced by |
|---|---|---|---|---|---|
| [PP-002](#pp-002) | low-medium | confirmed | B | Directed A positions outside the modulo range 0 <= A < 360 (A=ACP(360), ACN(-360), ACP(400)) | `test_negative_position_control_posts_valid_modulo_positions` [negative-mode] |
| [PP-004](#pp-004) | low | confirmed | B | ACP/ACN direction selection ignores iR1dir; with iR1dir=+1 short moves become near full turns | `test_direction_matches_machine_motion_reversed_sign` |
| [PP-005](#pp-005) | medium | uncertain | C | A tmatrix index adds the previous simultaneous job's apos (stale apos carry-over) | `test_tmatrix_index_ignores_previous_job_apos` |
| [PP-006](#pp-006) | low | confirmed | D | zpos_f becomes '5.4' after the first rapid / tool-change rapid: Z has 4 decimals, X/Y 5 | `test_z_keeps_coordinate_precision_after_first_rapid` [first-rapid], `test_z_keeps_coordinate_precision_after_tool_change` [tool-change] |
| [PP-009](#pp-009) | low-medium | confirmed | A | @usr_coolant overwrites the option iCoolantM5ON, so an unlisted pressure inherits the previous job's code instead of the default 77 | `test_through_coolant_code_does_not_leak_between_jobs` |
| [PP-010](#pp-010) | low | confirmed | A | bCoolofftc/bSpinofftc ('between tool changes') are dead; tool-change M9/M5 follow the end-of-program flags bCooloffend/bSpinoffend | `test_tool_change_options_control_spindle_and_coolant_off` |
| [PP-011](#pp-011) | low | confirmed | E | Spindle M3/M4 is emitted one block before its S word | `test_spindle_speed_programmed_with_or_before_start` |
| [PP-012](#pp-012) | low-medium | confirmed | A | Haas G187 HSM codes are emitted for the VMID job parameters iG187_P/nG187_E (828D needs CYCLE832) | `test_hsm_job_parameters_emit_only_sinumerik_g_functions` |
| [PP-014](#pp-014) | medium | confirmed | C | Same-tool work-offset change traverses XY in the new offset at the previous job's machine Z | `test_new_work_offset_is_entered_from_a_machine_z_retract` |
| [PP-015](#pp-015) | medium | confirmed | C | First-job deferred index with i4xIndexClearanceMode 1/2 retracts to the uninitialised Z0 before rotating A | `test_first_index_tool_level_clearance_never_plunges_to_z0` |
| [PP-016](#pp-016) | low-medium | confirmed | C | i4xIndexMode=1: the next job at the same index position is machined in G54 | `test_same_index_position_keeps_new_workoffset` |
| [PP-017](#pp-017) | medium | confirmed | C | i4xIndexMode=1 accumulates position-1 over successive @fourth_axis events (54->55->57->60) | `test_new_workoffset_mode_maps_position_to_offset` |
| [PP-018](#pp-018) | low | uncertain | C | Straight-retract (CAM-link) check ignores cpos, the rotary input of @line_4x/@move_4x | `test_rotary_4x_link_is_not_a_straight_retract` |
| [PP-022](#pp-022) | low | confirmed | D | iArcmode 1/3/4 emit Fanuc arc words (absolute centre as plain I/J, R instead of CR=) | `test_mode1_partial_arc_center` [absolute-center], `test_full_circle_center_in_modes_1_and_3` [full-circle], `test_radius_modes_use_cr_word` [radius-word] |
| [PP-023](#pp-023) | low | confirmed | D | Feed-emulated rapids write G1 rotary/XY blocks without the rapid feed (stale cutting feed or "feedrate not programmed") | `test_every_g1_block_of_emulated_rapid_moves_at_rapid_feed` |
| [PP-024](#pp-024) | medium | confirmed | A | M00 between same-tool jobs switches coolant off and never restores it; spindle restart has no ramp dwell | `test_m00_same_tool_restores_coolant_before_next_cut` [coolant], `test_m00_same_tool_waits_for_spindle_ramp` [ramp-dwell] |
| [PP-025](#pp-025) | low-medium | uncertain | A | Coolant is evaluated only at tool changes: a same-tool job's coolant request is ignored | `test_same_tool_job_applies_its_coolant_request` |
| [PP-026](#pp-026) | low | confirmed | E | Spindle ramp dwell divides by the literal 500 instead of spindle_accel | `test_spindle_dwell_uses_configured_acceleration` |
| [PP-027](#pp-027) | low | confirmed | A | The second tool change skips the full modal reset because the first-tool path leaves bSafetyprep=true | `test_tool_change_does_not_depend_on_previous_tool_being_first` |
| [PP-029](#pp-029) | low | confirmed | E | CYCLE86 SDIR is hard-coded to 3 (M3) even for CCW boring tools | `test_left_hand_boring_tool_runs_m4` |
| [PP-030](#pp-030) | low | uncertain | E | First drill hole may not trigger the modal cycle (empty block after MCALL) | `test_first_drill_point_is_a_motion_block` |
| [PP-031](#pp-031) | low | confirmed | E | Unsupported drill_type falls through to a stale 'MCALL CYCLE<gcode>' without arguments | `test_unknown_drill_type_is_rejected` |
| [PP-032](#pp-032) | medium | confirmed | C | home_number with iWorkOffset_Method=1 emits any operator number as the work offset (G1, G500, G58, ...) | `test_user_defined_offset_must_be_a_settable_offset` |
| [PP-033](#pp-033) | medium | confirmed | C | Multiple-fixture loop emits G58/G59 for the 5th/6th fixture (axial offsets, not settable G505/G506) | `test_fifth_and_sixth_fixture_use_extended_settable_offsets` |
| [PP-034](#pp-034) | high | confirmed | C | Multiple fixtures plus 4x indexing: fixture copies 2..N run at the wrong A angle and fall back to G54 | `test_copies_run_at_the_rotary_angle_of_their_tool_block` [next-tool-index], `test_fixture_copy_keeps_its_work_offset_after_a_same_tool_index` [same-tool-offset], `test_fixture_copy_restores_the_starting_angle_of_its_tool_block` [start-angle] |
| [PP-035](#pp-035) | low | confirmed | C | End-of-file tempfile cleanup deletes TEMPFILE1..iTcnumber although numbering starts at 2001 | `test_end_of_file_deletes_only_created_tempfiles` |
| [PP-036](#pp-036) | medium | confirmed | B | bLimit_3axis still emits A=DC(...) at the first rapid after a tool change | `test_limit_3axis_never_outputs_rotary` |
| [PP-037](#pp-037) | low | confirmed | B | iR1posControl=3 ('shortest distance') negates the target angle | `test_shortest_distance_mode_keeps_target_angle` |
| [PP-038](#pp-038) | low | confirmed | C | i4xIndexMode=2 (trig macro) emits Haas macro code and aborts on unchanged angles | `test_trig_macro_mode_unchanged_angle_does_not_abort` [abort], `test_trig_macro_mode_emits_sinumerik_code` [syntax] |
| [PP-039](#pp-039) | low | confirmed | C | Index clearance warning is written into the NC file as a bare text block (no comment prefix) | `test_index_clearance_warning_is_a_comment` |
| [PP-040](#pp-040) | low | confirmed | A | Homing parser merges lines after ';' when the optional prep string is omitted | `test_homing_lines_without_prep_string` |
| [PP-041](#pp-041) | low | confirmed | A | G53 homing with iWorkOffsetmode=2 prints cWo+0, i.e. 'G0 Z0' in work coordinates | `test_g53_homing_stays_in_machine_coordinates_for_every_offset_mode` |
| [PP-042](#pp-042) | low | confirmed | A | Homing mode 7 hard-codes G54 instead of the active work offset | `test_homing_mode_7_keeps_the_active_work_offset` |
| [PP-043](#pp-043) | very-low | confirmed | B | @home_data overwrites the CAM input shift_y (its output is commented out) | `test_home_data_does_not_modify_cam_inputs` |
| [PP-044](#pp-044) | low | confirmed | C | @call_proc emits Fanuc syntax (M98 H, literal 'cR1'; G20 on its tool-change path) and indexes A without being an index boundary | `test_call_proc_index_is_an_index_boundary` [index-boundary], `test_call_proc_emits_sinumerik_syntax` [syntax] |
| [PP-045](#pp-045) | low | confirmed | D | @change_ref_point says 'Not Supported' but writes Fanuc 'G91 G10 L2 P.. X Y Z' | `test_change_ref_point_emits_no_fanuc_data_setting` |
| [PP-046](#pp-046) | low | uncertain | B | Exact float compare on A triggers a full G75 Z+XY homing for sub-resolution angle changes | `test_sub_resolution_rotary_change_does_not_home` |
| [PP-047](#pp-047) | medium | uncertain | F | @rotate/@mirror are empty while the VMID delegates transformations to the post (SoftwareTransform="0") | `test_mirror_event_changes_the_frame_or_stops` [mirror], `test_rotate_event_changes_the_frame_or_stops` [rotate] |
| [PP-048](#pp-048) | medium | uncertain | F | SolidCAM MCO, dwell, 4x drill-point and rotate-to-plane events have no procedure (an MCO Halt produces no M0) | `test_every_event_of_the_authors_4x_template_is_handled` [event-coverage], `test_mco_halt_program_stops_the_machine` [mco-halt] |
| [PP-050](#pp-050) | medium | confirmed | F | vericut/GcodeSim.ini maps MAC 1-3 and 5-10 to G54 but omits MAC 4 | `test_vericut_mac_table_matches_post_work_offsets` |
| [PP-051](#pp-051) | low | uncertain | F | Vericut K word format left at 5.3 while I/J were widened to 8.5 (f88de47) | `test_vericut_arc_center_words_keep_post_precision` |
| [PP-052](#pp-052) | low | confirmed | F | VMID job parameters M50/M51 appear in every job dialog but the GPP never reads them | `test_every_vmid_user_parameter_is_read_by_the_post` |
| [PP-053](#pp-053) | low | confirmed | C | First index of a program in default Z-homing mode has no G75 (sHomestrrot assigned lazily) | `test_first_index_in_z_homing_mode_homes_z` |
| [PP-054](#pp-054) | low | likely-engine-artifact | A | First job under persisting init flags: 'G187 P2' and flood M8 cancelled by seven M9 | `test_flood_coolant_is_not_cancelled_before_the_first_cut` [coolant-burst], `test_no_fanuc_g187_in_a_default_program` [g187-default] |
| [PP-055](#pp-055) | low | confirmed | E | CYCLE83 first peck depth jumps by SDIS when drill_upper_z crosses 0 (FDPR relative to RFP) | `test_cycle83_first_peck_is_continuous_across_z0` |
| [PP-056](#pp-056) | low | confirmed | A | bStopM00difftool is set and cleared in the same @end_of_job: the skip path is dead and is what keeps the G75 retract before M06 | pinned only (@covers) |
| [PP-057](#pp-057) | low | confirmed | F | Dormant option/event paths emit Fanuc/Haas-only code (G65/G112/O777 macros, M98/M99, G20, G43/G49, '#' macros, WHILE[ loop) | pinned only (@covers) |
| [PP-058](#pp-058) | low | uncertain | F | Mach3 4x post (6efcad8): the feed re-statement remedy is missing on @line_5x and @arc | `test_line_5x_and_arc_feed_changes_are_restated_too` |
| [ENGINE-001](#engine-001) | medium | uncertain | F | Change-flag rule for equal-value assignment is unverified (engine: only a value change raises a flag, nothing clears it) | pinned only (@covers) |
| [ENGINE-002](#engine-002) | low-medium | confirmed | F | skipline block joining is not emulated (nb/nl always start a new block) | `test_skipline_false_joins_the_next_block` |
| [ENGINE-003](#engine-003) | low-medium | confirmed | F | numeric_def_f / integer_def_f are ignored: unformatted numbers use 3 decimals instead of '8.5' | `test_numeric_def_f_formats_unformatted_numeric_variables` |
| [ENGINE-004](#engine-004) | low-medium | likely-engine-artifact | E | The engine's doubled-quote ('') escape renders a stray apostrophe in the CYCLE84 argument list (',0,''') | `test_cycle84_arguments_are_numeric_and_ordered` |
| [ENGINE-005](#engine-005) | medium | confirmed | F | Declared globals get no change flag (locals get False); change(<global>) raises KeyError | `test_declared_global_has_change_flag` |
| [ENGINE-006](#engine-006) | low | confirmed | F | Leading-zero integer literal 07 raises (Python parser) | `test_leading_zero_integer_literal` |
| [ENGINE-007](#engine-007) | low | confirmed | F | right() and tostr(value:'fmt') built-ins are missing | `test_right_and_tostr_builtins` |
| [ENGINE-008](#engine-008) | low | uncertain | F | Print statement is unsupported (assumed: message window, generation continues) | `test_print_statement_does_not_stop_the_post` |
| [ENGINE-009](#engine-009) | medium | confirmed | F | input is treated as a terminal stop and abort raises the same exception as engine gaps; deleting abort leaves the suite green | `test_removed_abort_changes_observable_result` [abort-observable], `test_engine_input_prompt_is_not_terminal` [input-terminal] |
| [ENGINE-010](#engine-010) | low | confirmed | F | tonum() of a non-numeric string raises (tonum('G5')) | `test_tonum_of_non_numeric_text_returns_zero` |
| [ENGINE-011](#engine-011) | low | confirmed | F | Python-superset expression semantics are accepted silently (chained comparisons, hex, string*int, negative left/substr, precedence) | `test_python_only_syntax_is_rejected` |
| [ENGINE-012](#engine-012) | low | uncertain | F | Re-executing a local declaration loses the outer value; flat dict gives dynamic scope | `test_callee_assignment_to_caller_local_name_reaches_global` [dynamic-scope], `test_local_redeclared_in_loop_restores_global` [redeclare] |
| [ENGINE-013](#engine-013) | low | uncertain | F | Integer-typed variables hold fractions (no truncation/rounding on assignment) | `test_integer_variable_does_not_hold_fraction` |
| [ENGINE-014](#engine-014) | low | confirmed | F | Declaration parser accepts junk names; assignments to undeclared names are accepted | `test_declaration_with_initializer_is_not_silently_accepted` |
| [ENGINE-015](#engine-015) | low | confirmed | F | Rendering details: "" escape differs between _render and expression(), half-even ties, bool printed as True, '(p)' ignored | `test_double_quoted_literal_escape_matches_expression_parser` |
| [ENGINE-016](#engine-016) | low | confirmed | F | trace.py: nested-call ..> lines become NC output; fixed-width indentation is assumed | `test_nested_call_parameters_are_not_nc_output` |
| [ENGINE-017](#engine-017) | low | confirmed | F | Trace sanitizer redacts the enum inputs (feed_type, prev_command, ...) that drive the CAM-link homing bypass | `test_safety_relevant_enums_survive_sanitizing` |
| [ENGINE-018](#engine-018) | low | confirmed | F | Historical-revision constructs are unsupported: active trace statements and numeric formats '<(>5.3<)>', '(*k)', '+8.5', '(n)' | `test_historical_formats_and_trace_statements_are_accepted` |
| [ENGINE-019](#engine-019) | low | confirmed | F | Text outside procedures is silently ignored by the parser | `test_code_outside_procedures_is_reported` |
| [ENGINE-020](#engine-020) | low | uncertain | F | Identifiers inside '(expr)' output tokens get their change flags cleared | `test_expression_output_token_keeps_operand_change_flags` |
| [DESIGN-001](#design-001) | low | uncertain | C | CAM-link trust: a rapid that descends inside a confirmed link keeps the authorization, and any positive Z step (0.001 mm) authorizes an unhomed rotation | pinned only (@covers) |
| [DESIGN-003](#design-003) | low | confirmed | C | A deferred tmatrix index runs before the tool change (old tool, spindle and coolant on, double M1) | pinned only (@covers) |
| [DESIGN-004](#design-004) | low | confirmed | C | In confirmed CAM links the rotary block always precedes the XYZ block, even when Z rises in the same event | pinned only (@covers) |
| [DESIGN-005](#design-005) | low | uncertain | B | A tool change zeroes CAM apos/bpos/cpos, so A unwinds/rewinds between 5x jobs and the direction comes from angle_4x_around_x_dir (abort if not cw/ccw) | pinned only (@covers) |
| [DESIGN-006](#design-006) | low | confirmed | C | Single origin: the shipped home_number maps every CoordSys to G54 and newshift/ORGXYZ are computed but unused | pinned only (@covers) |
| [DESIGN-007](#design-007) | low | confirmed | B | Non-zero secondary rotation (bpos / x_angle_const_z) is silently ignored apart from the old vertical-head toggle | pinned only (@covers) |

## Suspected postprocessor defects (PP-xxx)

### PP-002

**Directed A positions outside the modulo range 0 <= A < 360 (A=ACP(360), ACN(-360), ACP(400))**

- Severity: low-medium
- Confidence: confirmed
- Reachability: Default iR1posControl=1 when apos/angle sums leave the range (4x simultaneous jobs, tmatrix -360, CoordSys/transform sums of 390, 400, 720). Facet rounding (UNVERIFIED): every value that posts exactly 360 (tiny negatives such as -0.0004/-1e-9 and exact whole-turn sums); it depends on GPPL round/compare semantics of the 7.3 format and on whether 360 is an inclusive bound. Facet negative-mode: non-default iR1posControl=2, and iR1posControl=0 for negative CAM angles (A=ACN(-90)), emit negative directed positions.
- Location: GPP @usr_r1pos_calc L2282-2288 (only (-360,0) is adjusted), L2312; @usr_r1_output L2381-2396; nR1pos_f '7.3' (@init_post L60)
- Evidence that would settle it: Whole turns: Siemens 828D modulo-axis rule (program range 0..<360, alarm 16830) or one controller dry run of A=ACP(360). Rounding facet (uncertain): GPPL statement on round-vs-truncate for the 7.3 format and on float compare.
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: TSR-11, efc-07, history-rotary-07, pp-region-4-cycles-rotary-05, pp-region-4-cycles-rotary-06, pp-weird-hunter-03
- Facet `rounding`: fixed: 6228b3d Keep A positions inside 0 <= A < 360 (values that print as 360.000 post 0; follow-up 9c89feb snaps float noise below 0.0005 to 0).
- Facet `whole-turn`: fixed: 6228b3d Keep A positions inside 0 <= A < 360 (mode 1 wraps into [0, 360); b94251b stops the post on a cutting block that turns A by 360 degrees or more).
- Tests of the fix: tests/test_rotary_modulo_range.py
- Reproduced by:
  - `tests/test_rotary.py::KnownRotaryDefects::test_negative_position_control_posts_valid_modulo_positions` (facet `negative-mode`, confidence confirmed)
- Pinned or exercised by (`@covers`):
  - `tests/test_rotary.py::FixedRotaryDefectGuards::test_directed_a_positions_stay_in_modulo_range`
  - `tests/test_rotary.py::FixedRotaryDefectGuards::test_emitted_a_positions_are_valid_modulo_positions`

### PP-004

**ACP/ACN direction selection ignores iR1dir; with iR1dir=+1 short moves become near full turns**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default iR1dir=+1 (documented option) without changing the VMID/Vericut A direction; default iR1dir=-1 is correct.
- Location: GPP @usr_r1_select_dir L2361-2379, @usr_r1_output L2381-2392; nR1pos = -angle*iR1dir L2273-2277; option iR1dir L165
- Evidence that would settle it: Machine check of which way +A turns; decides whether iR1dir=+1 is ever a valid configuration.
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: history-rotary-10, pp-region-4-cycles-rotary-04
- Reproduced by:
  - `tests/test_rotary.py::RotaryDirectionTests::test_direction_matches_machine_motion_reversed_sign`

### PP-005

**A tmatrix index adds the previous simultaneous job's apos (stale apos carry-over)**

- Severity: medium
- Confidence: uncertain
- Reachability: Default config, indexed job after a 4x/5x simultaneous job that ended with apos != 0, only if SolidCAM carries apos over between jobs (UNVERIFIED); a later tool change does not repair it.
- Location: GPP @start_of_job L1110-1115 -> @usr_4x_index L2411 -> @usr_r1pos_calc L2277 (nR1pos5x = (-apos)*iR1dir); compare @fourth_axis L1797 (apos = 0)
- Evidence that would settle it: SolidCAM trace of a 4x simultaneous job followed by an indexed job: apos in the second job's @tmatrix and @start_of_job parameter dump.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: TSR-14, history-rotary-08, pp-region-4-cycles-rotary(missed-3)
- Reproduced by:
  - `tests/test_indexing_link.py::FourthAxisIndexTests::test_tmatrix_index_ignores_previous_job_apos`

### PP-006

**zpos_f becomes '5.4' after the first rapid / tool-change rapid: Z has 4 decimals, X/Y 5**

- Severity: low
- Confidence: confirmed
- Reachability: Default config: every program after the first rapid (@usr_rapid L1256/L1269); later tool changes do not restore '8.5' (@usr_ct_before_notfirsttool L724 re-applies '5.4' only when bVertical/bFirstVert is set, and bVertical needs nR2pos != 0, which is always 0 on this 4x-A machine). The legacy motion_engine sets zpos_f=8.5 and hides it.
- Location: GPP @init_post L59 (zpos_f '8.5'); @usr_rapid L1256/L1269 and @usr_ct_before_notfirsttool L724 (zpos_f '5.4')
- Evidence that would settle it: Settled as real output by tests/fixtures/shit2_contiguous_link.json (4-decimal Z); owner decides whether 0.0001 mm is acceptable against VMID MovementPrecision=5.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: history-rotary-09, pp3-zpos-precision, pp-weird-hunter-13
- Reproduced by:
  - `tests/test_motion_rapids.py::ZPrecisionTests::test_z_keeps_coordinate_precision_after_first_rapid` (facet `first-rapid`, confidence confirmed)
  - `tests/test_motion_rapids.py::ZPrecisionTests::test_z_keeps_coordinate_precision_after_tool_change` (facet `tool-change`, confidence confirmed)

### PP-009

**@usr_coolant overwrites the option iCoolantM5ON, so an unlisted pressure inherits the previous job's code instead of the default 77**

- Severity: low-medium
- Confidence: confirmed
- Reachability: Non-default: two jobs with through-tool coolant where the later pressure is not in the table.
- Location: GPP @usr_coolant L979-1006 (assigns the option variable iCoolantM5ON); option default L121
- Evidence that would settle it: None needed for the behaviour (deterministic); owner decides the intended code for unlisted pressures.
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: pp-weird-hunter-09
- Reproduced by:
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_through_coolant_code_does_not_leak_between_jobs`

### PP-010

**bCoolofftc/bSpinofftc ('between tool changes') are dead; tool-change M9/M5 follow the end-of-program flags bCooloffend/bSpinoffend**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default option values (defaults are all true and safe); with bSpinoffend=false the post-M06 ramp dwell also disappears.
- Location: GPP @usr_ct_before_notfirsttool L692 (bCooloffend) and L712 (bSpinoffend); options L104-107
- Evidence that would settle it: None needed (copy-paste visible in @usr_ct_before_notfirsttool L692/L712).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: tc-05, pp-weird-hunter-04, pp-weird-hunter-18
- Reproduced by:
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_tool_change_options_control_spindle_and_coolant_off`

### PP-011

**Spindle M3/M4 is emitted one block before its S word**

- Severity: low
- Confidence: confirmed
- Reachability: With bCoolspinaftertc=true, M3 joins the MSG block and S follows, under any skipline semantics. On the default tool change, @usr_ct_after sets skipline=false before @start_tool, evidently to join S to the M3 block; PP-011 holds there only if skipline does not join (ENGINE-002). Exposure: single-block prove-out (the spindle starts at the previous S).
- Location: GPP @start_tool L1950-1963, @usr_spindle_mcode_output L1977-1983 (no nb), @usr_spindle_output L1965-1971; @usr_ct_after skipline before @start_tool
- Evidence that would settle it: One posted default tool change: is S on the M3 block? (Siemens rule: S must be programmed in or before the M3/M4 block.)
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: pp-weird-hunter-05, history-misc-17, pp-region-4-cycles-rotary-22, efc-05
- Reproduced by:
  - `tests/test_cycles_spindle.py::SpindleTests::test_spindle_speed_programmed_with_or_before_start`

### PP-012

**Haas G187 HSM codes are emitted for the VMID job parameters iG187_P/nG187_E (828D needs CYCLE832)**

- Severity: low-medium
- Confidence: confirmed
- Reachability: Non-default VMID job parameters iG187_P != 0 or nG187_E != 0 (fail-safe: unknown G function alarm).
- Location: GPP @usr_HSM_mode L1077-1099 (G187 output L1086/L1094), called from @start_of_job L1173; VMID ParamJobs iG187_P/nG187_E
- Evidence that would settle it: Siemens 828D G-function list (G187 undefined; repository Vericut control has no G187).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: tc-07, efc-02, pp-weird-hunter-17
- Reproduced by:
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_hsm_job_parameters_emit_only_sinumerik_g_functions`

### PP-014

**Same-tool work-offset change traverses XY in the new offset at the previous job's machine Z**

- Severity: medium
- Confidence: confirmed
- Reachability: Non-default iWorkOffset_Method=1 (or any path that changes iWorkoffset between same-tool jobs).
- Location: GPP @start_of_job L1154-1158 (iPworkoffset ne iWorkoffset -> usr_tc_init_gmstates, rapid_move); @usr_rapid bTlchg branch L1289-1316 and L1323-1330
- Evidence that would settle it: Trace of two same-tool jobs on different CoordSys with iWorkOffset_Method=1.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: critic-08
- Reproduced by:
  - `tests/test_work_offsets_fixtures.py::SameToolWorkOffsetChangeTests::test_new_work_offset_is_entered_from_a_machine_z_retract`

### PP-015

**First-job deferred index with i4xIndexClearanceMode 1/2 retracts to the uninitialised Z0 before rotating A**

- Severity: medium
- Confidence: confirmed
- Reachability: Non-default i4xIndexClearanceMode=1 or 2 (default 0 homes Z); also a first-job @fourth_axis in clearance mode 1/2 (history-indexing-link-06); collision-class when used.
- Location: GPP @usr_4x_index L2430/L2437 (Z nPtool_z_level / nPtool_start_plane); assigned only in @end_of_job L1200-1201; first-job index from @start_of_job L1110-1115
- Evidence that would settle it: SolidCAM trace of the first job in mode 1 (trace '@usr_4x_index':5).
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: history-indexing-link-06, tc-02
- Reproduced by:
  - `tests/test_indexing_link.py::FirstIndexClearanceTests::test_first_index_tool_level_clearance_never_plunges_to_z0`

### PP-016

**i4xIndexMode=1: the next job at the same index position is machined in G54**

- Severity: low-medium
- Confidence: confirmed
- Reachability: Non-default i4xIndexMode=1 (start_of_job comment says multiple MAC offsets are not used with 4x). Assumes SolidCAM reports the same CoordSys position in 'position' for both operations (pp3-fourth-axis-position).
- Location: GPP @home_number L616 (iWorkoffset = 54 every job); @usr_4x_index L2450/L2461/L2469 (position-1 added only when change(nR1pos)); @fourth_axis L1785-1789
- Evidence that would settle it: SolidCAM run with i4xIndexMode=1 and two consecutive operations on CoordSys position 2: what SolidCAM puts in 'position'.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: history-indexing-link-07, pp3-fourth-axis-position
- Reproduced by:
  - `tests/test_indexing_link.py::IndexWorkOffsetModeTests::test_same_index_position_keeps_new_workoffset`

### PP-017

**i4xIndexMode=1 accumulates position-1 over successive @fourth_axis events (54->55->57->60)**

- Severity: medium
- Confidence: confirmed
- Reachability: Non-default i4xIndexMode=1 with several @fourth_axis index events. Assumes SolidCAM reports the CoordSys position in 'position' (pp3-fourth-axis-position).
- Location: GPP @usr_4x_index L2450/L2461/L2469 (iWorkoffset = iWorkoffset + (position-1)); @fourth_axis L1782-1800 increments position
- Evidence that would settle it: None needed (deterministic); intended mapping is one offset per position.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: pp-region-4-cycles-rotary-10
- Reproduced by:
  - `tests/test_indexing_link.py::IndexWorkOffsetModeTests::test_new_workoffset_mode_maps_position_to_offset`

### PP-018

**Straight-retract (CAM-link) check ignores cpos, the rotary input of @line_4x/@move_4x**

- Severity: low
- Confidence: uncertain
- Reachability: Only if SolidCAM 4x feed links carry the rotation in cpos with X5_job true (UNVERIFIED).
- Location: GPP @usr_line L1389 (!change(apos) and !change(bpos), no cpos); @usr_rapid L1224 ('@line_4x'/'@move_4x' whitelist); @usr_r1pos_calc L2276
- Evidence that would settle it: SolidCAM debug trace of a 4-axis simultaneous operation (trace '@line_4x':5 / '@move_4x':5) showing X5_job and whether feed_link line_4x events combine Z and cpos changes.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: history-indexing-link-08
- Reproduced by:
  - `tests/test_indexing_link.py::CamLinkTransitionTests::test_rotary_4x_link_is_not_a_straight_retract`
- Pinned or exercised by (`@covers`):
  - `tests/test_indexing_link.py::CamLinkTransitionTests::test_straight_4x_link_keeps_authorization`

### PP-022

**iArcmode 1/3/4 emit Fanuc arc words (absolute centre as plain I/J, R instead of CR=)**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default iArcmode 1, 3 or 4 (default 2 is correct); silent hazard only for full circles in mode 1/3. The full-circle facet also needs SolidCAM to send 360-degree arcs although the VMID has SupportGrt180degArcs="0" (UNVERIFIED).
- Location: GPP @usr_arc L1587-1628 (absolute centre L1589/L1603/L1617, R word L1594-1627); option iArcmode L82
- Evidence that would settle it: Siemens 828D programming manual (I=AC() for absolute centres, CR= for the radius).
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: pp3-arc-mode-syntax, efc-12, history-misc-13, TSR-18
- Reproduced by:
  - `tests/test_arc_compensation_plane.py::ArcModeSyntaxTests::test_mode1_partial_arc_center` (facet `absolute-center`, confidence confirmed)
  - `tests/test_arc_compensation_plane.py::ArcModeSyntaxTests::test_full_circle_center_in_modes_1_and_3` (facet `full-circle`, confidence confirmed)
  - `tests/test_arc_compensation_plane.py::ArcModeSyntaxTests::test_radius_modes_use_cr_word` (facet `radius-word`, confidence confirmed)

### PP-023

**Feed-emulated rapids write G1 rotary/XY blocks without the rapid feed (stale cutting feed or "feedrate not programmed")**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default bSyncdrapid=false (feed-emulated rapids). The tool-change positioning G1 block (A=DC(0)) and the first XY block of a split first move have no F under both flag policies; the first-job split Z block without F depends on ENGINE-001 (it prints F650 under the persisting policy). The rotary G1 block after a post-inserted homing has no F either.
- Location: GPP @usr_rapid L1286 (rotary G1), L1303 (tool-change block), L1323 (split XY block); F only at L1337
- Evidence that would settle it: None needed for the behaviour; owner decides the intended F on every emulated block.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: pp3-emulated-rapid-no-feed
- Reproduced by:
  - `tests/test_motion_rapids.py::FeedEmulatedRapidTests::test_every_g1_block_of_emulated_rapid_moves_at_rapid_feed`

### PP-024

**M00 between same-tool jobs switches coolant off and never restores it; spindle restart has no ramp dwell**

- Severity: medium
- Confidence: confirmed
- Reachability: VMID job parameter bStopM00=true on a same-tool job boundary (default false). Facet ramp-dwell: low; the expected dwell is the PP's own spindle_accel policy, not machine physics.
- Location: GPP @usr_StopM00_sametool L1679-1719 (M9, M5, M0, spindle restart without @usr_coolant or dwell); @start_of_job same-tool branch L1145-1159
- Evidence that would settle it: Coolant: none needed. Dwell: MD35500 / spindle acceleration on the target 828D.
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: tc-03, pp3-m00-sametool-coolant
- Reproduced by:
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_m00_same_tool_restores_coolant_before_next_cut` (facet `coolant`, confidence confirmed)
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_m00_same_tool_waits_for_spindle_ramp` (facet `ramp-dwell`, confidence confirmed)

### PP-025

**Coolant is evaluated only at tool changes: a same-tool job's coolant request is ignored**

- Severity: low-medium
- Confidence: uncertain
- Reachability: Default config when consecutive same-tool jobs request different coolant channels.
- Location: GPP @usr_coolant callers: @usr_ct_after L832/L852 only (@end_of_job call commented out L1203-1205)
- Evidence that would settle it: Trace of two same-tool jobs with different coolant settings (does SolidCAM expect the post to switch?).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: tc-04
- Reproduced by:
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_same_tool_job_applies_its_coolant_request`

### PP-026

**Spindle ramp dwell divides by the literal 500 instead of spindle_accel**

- Severity: low
- Confidence: confirmed
- Reachability: Latent: spindle_accel is an @init_post constant (500 rpm/s), not a user option; the dwell differs from the documented policy only if that constant is edited (tc-09 correction).
- Location: GPP @usr_spindle_output L1969-1972 (G04 F (0.3+(sdiff/500))); spindle_accel = 500 in @init_post
- Evidence that would settle it: None needed for the formula; MD35500 on the target 828D for the intended ramp time.
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: tc-09, history-misc-17
- Reproduced by:
  - `tests/test_cycles_spindle.py::SpindleTests::test_spindle_dwell_uses_configured_acceleration`

### PP-027

**The second tool change skips the full modal reset because the first-tool path leaves bSafetyprep=true**

- Severity: low
- Confidence: confirmed
- Reachability: Default config, second and later tool changes.
- Location: GPP @usr_ct_before_firsttool L754 (bSafetyprep = true); @usr_tc_init_gmstates L863-915 (first-tool branch never clears it)
- Evidence that would settle it: None needed (state flow visible in @usr_ct_before_firsttool L754 and @usr_tc_init_gmstates).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: tc-10, TSR-02
- Reproduced by:
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_tool_change_does_not_depend_on_previous_tool_being_first`

### PP-029

**CYCLE86 SDIR is hard-coded to 3 (M3) even for CCW boring tools**

- Severity: low
- Confidence: confirmed
- Reachability: Default config, G86 job with a counter-clockwise tool.
- Location: GPP @drill G86 branch L1900-1905 (SDIR ',,,3' hard-coded); compare @start_tool/@m_feed_spin L1937-1955
- Evidence that would settle it: Siemens CYCLE86 SDIR parameter definition.
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: critic-09
- Reproduced by:
  - `tests/test_cycles_spindle.py::BoringCycleTests::test_left_hand_boring_tool_runs_m4`

### PP-030

**First drill hole may not trigger the modal cycle (empty block after MCALL)**

- Severity: low
- Confidence: uncertain
- Reachability: Default drilling flow; depends on whether SolidCAM positions to the first hole before @drill_point (UNVERIFIED; the cycles were proven on the machine in bea8c62).
- Location: GPP @drill L1826 (rapid_move before MCALL), L1844; @drill_point L1913-1918 (modal [X][Y][Z])
- Evidence that would settle it: SolidCAM drilling trace (@drill, @drill_point sequence) or the posted MPF of a 2-hole job run in Vericut.
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: TSR-15, pp-region-4-cycles-rotary-15
- Reproduced by:
  - `tests/test_cycles_spindle.py::ModalCycleTests::test_first_drill_point_is_a_motion_block`

### PP-031

**Unsupported drill_type falls through to a stale 'MCALL CYCLE<gcode>' without arguments**

- Severity: low
- Confidence: confirmed
- Reachability: Only for drill types the VMID does not offer (VMID offers parameterised cycles only).
- Location: GPP @drill L1828-1844 (no else branch for unknown drill_type)
- Evidence that would settle it: None needed; owner decides abort vs explicit rejection.
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: pp-region-4-cycles-rotary-20
- Reproduced by:
  - `tests/test_cycles_spindle.py::ModalCycleTests::test_unknown_drill_type_is_rejected`

### PP-032

**home_number with iWorkOffset_Method=1 emits any operator number as the work offset (G1, G500, G58, ...)**

- Severity: medium
- Confidence: confirmed
- Reachability: Non-default VMID machine parameter iWorkOffset_Method=1 plus a wrong operator entry.
- Location: GPP @home_number L628-630 (iWorkOffset_Method=1 branch), @usr_homenumber_output L633-638; VMID UserDefParams iWorkOffset_Method
- Evidence that would settle it: Siemens settable offsets list (G54..G57, G505..G599); none needed for the behaviour.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: R1-01
- Reproduced by:
  - `tests/test_work_offsets_fixtures.py::WorkOffsetTests::test_user_defined_offset_must_be_a_settable_offset`

### PP-033

**Multiple-fixture loop emits G58/G59 for the 5th/6th fixture (axial offsets, not settable G505/G506)**

- Severity: medium
- Confidence: confirmed
- Reachability: Non-default VMID part parameter iNumber_of_Fixtures >= 5; copies 5/6 rerun in G57 or alarm.
- Location: GPP @Multiple_Fixtures L2213-2217 and L2240-2244 ({nb,cWo,((iWorkoffset-1)+i)}); enabled by @start_of_file L193-196
- Evidence that would settle it: Siemens PG Fundamentals 'Axial zero offset G58/G59' or a Vericut/828D run of a bare G58.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: R1-02
- Reproduced by:
  - `tests/test_work_offsets_fixtures.py::MultipleFixtureTests::test_fifth_and_sixth_fixture_use_extended_settable_offsets`

### PP-034

**Multiple fixtures plus 4x indexing: fixture copies 2..N run at the wrong A angle and fall back to G54**

- Severity: high
- Confidence: confirmed
- Reachability: Non-default iNumber_of_Fixtures > 1 together with a tmatrix/fourth_axis index (crash risk).
- Location: GPP @start_of_job L1110-1115 (index before @usr_ct L1146); @usr_ct L657-660/L682-685 -> @Multiple_Fixtures L2209-2245
- Evidence that would settle it: Vericut run of an expanded multi-fixture program with an index between tools or jobs.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: critic-01, pp-region-4-cycles-rotary-26
- Reproduced by:
  - `tests/test_work_offsets_fixtures.py::MultipleFixtureIndexTests::test_copies_run_at_the_rotary_angle_of_their_tool_block` (facet `next-tool-index`, confidence confirmed)
  - `tests/test_work_offsets_fixtures.py::MultipleFixtureIndexTests::test_fixture_copy_keeps_its_work_offset_after_a_same_tool_index` (facet `same-tool-offset`, confidence confirmed)
  - `tests/test_work_offsets_fixtures.py::MultipleFixtureIndexTests::test_fixture_copy_restores_the_starting_angle_of_its_tool_block` (facet `start-angle`, confidence confirmed)

### PP-035

**End-of-file tempfile cleanup deletes TEMPFILE1..iTcnumber although numbering starts at 2001**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default iNumber_of_Fixtures > 1.
- Location: GPP @usr_init_gmstates L340 (iTcnumber = 2001); @Multiple_Fixtures L2252-2261 (delete loop from 1), called from @end_of_file L561-564
- Evidence that would settle it: What SolidCAM does with !!delete file!! for files that do not exist.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: R1-09
- Reproduced by:
  - `tests/test_work_offsets_fixtures.py::MultipleFixtureTests::test_end_of_file_deletes_only_created_tempfiles`

### PP-036

**bLimit_3axis still emits A=DC(...) at the first rapid after a tool change**

- Severity: medium
- Confidence: confirmed
- Reachability: Non-default VMID machine parameter bLimit_3axis=1 (shipped 0).
- Location: GPP @usr_r1pos_calc L2338-2345 (bR1forceOutput sets iR1dirMode=3 after the 3-axis clear); @usr_rapid L1297-1309
- Evidence that would settle it: None needed (bR1forceOutput overrides the 3-axis clear, ab853be/ad2537a).
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: pp-region-4-cycles-rotary-12
- Reproduced by:
  - `tests/test_rotary.py::KnownRotaryDefects::test_limit_3axis_never_outputs_rotary`

### PP-037

**iR1posControl=3 ('shortest distance') negates the target angle**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default iR1posControl=3.
- Location: GPP @usr_r1pos_calc L2296-2312 (nR1pdir = -1 multiplies the position); option doc L170
- Evidence that would settle it: None needed; a static guard that the shipped option is 1 is the practical protection.
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: pp-region-4-cycles-rotary-11
- Reproduced by:
  - `tests/test_rotary.py::KnownRotaryDefects::test_shortest_distance_mode_keeps_target_angle`

### PP-038

**i4xIndexMode=2 (trig macro) emits Haas macro code and aborts on unchanged angles**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default i4xIndexMode=2.
- Location: GPP @usr_4x_index L2476-2486 (mode 2 outside if change(nR1pos)); @usr_trig_macro_call L2551-2556, @usr_trig_macro_output L2558-2614; @usr_ct_after L820-825
- Evidence that would settle it: None needed (Fanuc/Haas-only output; regression from bff5ed0 for the abort).
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: pp-region-4-cycles-rotary-16, history-misc-16, R1-06
- Reproduced by:
  - `tests/test_indexing_link.py::FourthAxisIndexTests::test_trig_macro_mode_unchanged_angle_does_not_abort` (facet `abort`, confidence confirmed)
  - `tests/test_indexing_link.py::FourthAxisIndexTests::test_trig_macro_mode_emits_sinumerik_code` (facet `syntax`, confidence confirmed)

### PP-039

**Index clearance warning is written into the NC file as a bare text block (no comment prefix)**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default i4xIndexClearanceMode=1 with tool_z_level below tool_start_plane; the 828D raises a syntax alarm on that block (safe stop). The preceding Print needs the ENGINE-008 workaround to execute.
- Location: GPP @usr_4x_index L2425-2428 and L2455-2458 ({nl,'WARNING!! ...'} after Print)
- Evidence that would settle it: None needed for the behaviour ({nl,'WARNING!! ...'} at @usr_4x_index L2427/L2457).
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: pp-region-4-cycles-rotary-18, efc-14
- Reproduced by:
  - `tests/test_indexing_link.py::FourthAxisIndexTests::test_index_clearance_warning_is_a_comment`

### PP-040

**Homing parser merges lines after ';' when the optional prep string is omitted**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default user-edited homing string without the prep colon in a multi-line definition.
- Location: GPP @usr_prep_home_axis L2108-2113 (second ':' searched across the whole remainder)
- Evidence that would settle it: None needed (string parsing in @usr_prep_home_axis L2108-2113).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: pp-region-4-cycles-rotary-14
- Reproduced by:
  - `tests/test_session_program.py::HomingStringTests::test_homing_lines_without_prep_string`

### PP-041

**G53 homing with iWorkOffsetmode=2 prints cWo+0, i.e. 'G0 Z0' in work coordinates**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default homing mode with G53 and iWorkOffsetmode=2.
- Location: GPP @usr_home_axis L2159-2161 (iWorkOffsetmode 2: cWo + 0)
- Evidence that would settle it: None needed (@usr_home_axis L2159-2161).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: pp-region-4-cycles-rotary-17
- Reproduced by:
  - `tests/test_session_program.py::HomingStringTests::test_g53_homing_stays_in_machine_coordinates_for_every_offset_mode`

### PP-042

**Homing mode 7 hard-codes G54 instead of the active work offset**

- Severity: low
- Confidence: confirmed
- Reachability: Non-default homing definition using mode 7.
- Location: GPP @usr_home_axis L2182-2184 (mode 7: 'G90 G54 ' literal)
- Evidence that would settle it: None needed; owner decides the intended offset for mode 7.
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: pp-region-4-cycles-rotary(missed)
- Reproduced by:
  - `tests/test_session_program.py::HomingStringTests::test_homing_mode_7_keeps_the_active_work_offset`

### PP-043

**@home_data overwrites the CAM input shift_y (its output is commented out)**

- Severity: very-low
- Confidence: confirmed
- Reachability: Default config (VMID HomeDataAtStart="1"); no NC output depends on it today.
- Location: GPP @home_data L2646-2648 (shift_y overwritten); VMID HomeDataAtStart="1"
- Evidence that would settle it: None needed (@home_data L2646-2648).
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: pp-region-4-cycles-rotary-23
- Reproduced by:
  - `tests/test_rotary.py::KnownRotaryDefects::test_home_data_does_not_modify_cam_inputs`

### PP-044

**@call_proc emits Fanuc syntax (M98 H, literal 'cR1'; G20 on its tool-change path) and indexes A without being an index boundary**

- Severity: low
- Confidence: confirmed
- Reachability: Subroutines disabled in the VMID (SubroutinesExist/LoopExist off); reachable only if enabled.
- Location: GPP @call_proc L2000-2041 (L2015 'G20 ', L2031 @usr_4x_index, L2036 'cR1' literal, L2037 'M98 H')
- Evidence that would settle it: None needed; VMID subroutine setting decides reachability.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: history-indexing-link-11, history-rotary-14, pp-region-4-cycles-rotary-19
- Reproduced by:
  - `tests/test_indexing_link.py::SubroutineIndexTests::test_call_proc_index_is_an_index_boundary` (facet `index-boundary`, confidence confirmed)
  - `tests/test_indexing_link.py::SubroutineIndexTests::test_call_proc_emits_sinumerik_syntax` (facet `syntax`, confidence confirmed)
- Pinned or exercised by (`@covers`):
  - `tests/test_machine_definition.py::ConfigurationGuards::test_vmid_keeps_subroutines_and_loops_disabled`

### PP-045

**@change_ref_point says 'Not Supported' but writes Fanuc 'G91 G10 L2 P.. X Y Z'**

- Severity: low
- Confidence: confirmed
- Reachability: Only if SolidCAM emits @change_ref_point (reference point change inside a job).
- Location: GPP @change_ref_point L1759-1766 ('G91 G10 L2 P..')
- Evidence that would settle it: None needed; owner decides abort vs Sinumerik equivalent.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: pp3-change-ref-point-g10, TSR-18
- Reproduced by:
  - `tests/test_motion_rapids.py::ChangeRefPointTests::test_change_ref_point_emits_no_fanuc_data_setting`

### PP-046

**Exact float compare on A triggers a full G75 Z+XY homing for sub-resolution angle changes**

- Severity: low
- Confidence: uncertain
- Reachability: Default config when consecutive A targets differ below the 0.001 output resolution; depends on GPPL numeric compare semantics (UNVERIFIED).
- Location: GPP @usr_r1pos_calc L2328-2332 ('if nPR1pos ne nR1pos', exact compare); @usr_rapid L1278-1288
- Evidence that would settle it: GPPL manual statement or a trace with sub-resolution apos differences.
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: pp-weird-hunter-08
- Reproduced by:
  - `tests/test_rotary.py::KnownRotaryDefects::test_sub_resolution_rotary_change_does_not_home`

### PP-047

**@rotate/@mirror are empty while the VMID delegates transformations to the post (SoftwareTransform="0")**

- Severity: medium
- Confidence: uncertain
- Reachability: Only if a SolidCAM job uses rotate/mirror transformations with this VMID; event delivery UNVERIFIED.
- Location: GPP @rotate L1770-1773 and @mirror L1776-1779 (empty); VMID SoftwareTransform="0"
- Evidence that would settle it: SolidCAM run of a mirrored/rotated job with this VMID: are @rotate/@mirror called and is the toolpath already transformed?
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: critic-02
- Reproduced by:
  - `tests/test_contracts.py::TransformEventTests::test_mirror_event_changes_the_frame_or_stops` (facet `mirror`, confidence uncertain)
  - `tests/test_contracts.py::TransformEventTests::test_rotate_event_changes_the_frame_or_stops` (facet `rotate`, confidence uncertain)

### PP-048

**SolidCAM MCO, dwell, 4x drill-point and rotate-to-plane events have no procedure (an MCO Halt produces no M0)**

- Severity: medium
- Confidence: uncertain
- Reachability: Only if those events are used; whether SolidCAM silently skips undefined procedures is UNVERIFIED.
- Location: GPP: procedures absent (@halt_program, @machine_opt_stop, @delay/@dwell, @drill4x_pnt, @rotate_to_plane, MCO events); reference: the Mach3 4x template at ffd296c
- Evidence that would settle it: SolidCAM run with an MCO Halt/optional stop and a dwell: is anything posted?
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: critic-03
- Reproduced by:
  - `tests/test_contracts.py::SolidCamEventCoverageTests::test_every_event_of_the_authors_4x_template_is_handled` (facet `event-coverage`, confidence uncertain)
  - `tests/test_contracts.py::SolidCamEventCoverageTests::test_mco_halt_program_stops_the_machine` (facet `mco-halt`, confidence uncertain)

### PP-050

**vericut/GcodeSim.ini maps MAC 1-3 and 5-10 to G54 but omits MAC 4**

- Severity: medium
- Confidence: confirmed
- Reachability: Default machine definition; Vericut and the NC disagree for CoordSys 4.
- Location: vericut/GcodeSim.ini [MAC] (1,2,3,5..10 = 54; MAC 4 missing)
- Evidence that would settle it: None needed (c85f5f7 intent: all MACs map to G54).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: critic-06
- Reproduced by:
  - `tests/test_machine_definition.py::MachineDefinitionKnownDefects::test_vericut_mac_table_matches_post_work_offsets`

### PP-051

**Vericut K word format left at 5.3 while I/J were widened to 8.5 (f88de47)**

- Severity: low
- Confidence: uncertain
- Reachability: ZX/YZ arcs only (K is printed with 5 decimals).
- Location: vericut/sin840d_special.ctl <Word Name="K"> MetricFormat="5.3" (I/J 8.5); GPP @usr_arc L1606/L1620
- Evidence that would settle it: Vericut run of a ZX arc with a K word below 0.001 resolution.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: critic-07
- Reproduced by:
  - `tests/test_machine_definition.py::MachineDefinitionKnownDefects::test_vericut_arc_center_words_keep_post_precision`

### PP-052

**VMID job parameters M50/M51 appear in every job dialog but the GPP never reads them**

- Severity: low
- Confidence: confirmed
- Reachability: Default VMID; operator entries are silently ignored.
- Location: Gmill_540v_4x.vmid ParamJobs GppName="M50"/"M51" (never read by the GPP)
- Evidence that would settle it: Owner's intent for M50/M51 (air blast / low-pressure through coolant?).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: critic-10
- Reproduced by:
  - `tests/test_machine_definition.py::MachineDefinitionKnownDefects::test_every_vmid_user_parameter_is_read_by_the_post`

### PP-053

**First index of a program in default Z-homing mode has no G75 (sHomestrrot assigned lazily)**

- Severity: low
- Confidence: confirmed
- Reachability: Default i4xIndexClearanceMode=0, first job indexed before any rapid; safe in practice because start_program already homed.
- Location: GPP @usr_4x_index L2416 (if sHomestrrot ne ''); sHomestrrot assigned only in @usr_rapid L1250/L1263/L1279 and @usr_ct_before_notfirsttool L718
- Evidence that would settle it: None needed; owner decides whether the index must home explicitly.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: history-indexing-link-13
- Reproduced by:
  - `tests/test_indexing_link.py::FirstIndexClearanceTests::test_first_index_in_z_homing_mode_homes_z`

### PP-054

**First job under persisting init flags: 'G187 P2' and flood M8 cancelled by seven M9**

- Severity: low
- Confidence: likely-engine-artifact
- Reachability: Default config but ONLY under the flags='persist' session policy (stock-engine change-flag rule for initial assignments, ENGINE-001); the clear policy prints neither.
- Location: GPP @usr_init_gmstates L341-350 (coolant channels OFF, iG187_P_gpp = 2); @usr_coolant_output L1038-1075; @usr_HSM_mode L1077-1099; pp_tests/gppl/legacy.py assignment flag rule
- Evidence that would settle it: grep any MPF generated by HEAD for 'G187' and for M8 followed by M9 before the first cut; or a SolidCAM trace "all":5 of a first job showing change(iCoolantM2) and change(iG187_P_gpp).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: TSR-12, TSR-13, efc-02, efc-03, tc-06, pp-weird-hunter-06, history-misc-15, engine-impl-critic-07, history-indexing-link-14
- Reproduced by:
  - `tests/test_session_program.py::FirstJobPersistingFlagTests::test_flood_coolant_is_not_cancelled_before_the_first_cut` (facet `coolant-burst`, confidence likely-engine-artifact)
  - `tests/test_session_program.py::FirstJobPersistingFlagTests::test_no_fanuc_g187_in_a_default_program` (facet `g187-default`, confidence likely-engine-artifact)

### PP-055

**CYCLE83 first peck depth jumps by SDIS when drill_upper_z crosses 0 (FDPR relative to RFP)**

- Severity: low
- Confidence: confirmed
- Reachability: Default config, G83 holes whose top is near Z0; harmless (shallower first peck below Z0).
- Location: GPP @drill G83 branch L1846-1907 (FDPR relative to RFP, RFP shifted by SDIS when drill_upper_z <= 0)
- Evidence that would settle it: Siemens CYCLE83 FDPR definition; owner decides fix vs documentation.
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: pp-weird-hunter-21(missed)
- Reproduced by:
  - `tests/test_cycles_spindle.py::DrillCycleGeometryTests::test_cycle83_first_peck_is_continuous_across_z0`

### PP-056

**bStopM00difftool is set and cleared in the same @end_of_job: the skip path is dead and is what keeps the G75 retract before M06**

- Severity: low
- Confidence: confirmed
- Reachability: VMID job parameter bStopM00=true before a different-tool job; current output is safe by accident.
- Location: GPP @usr_StopM00_difftool L1754 (flag set), @end_of_job L1193 (cleared), @usr_ct_before_notfirsttool L691 (read)
- Evidence that would settle it: None needed; a pin must protect the retract before M06 against a naive "fix".
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: tc-11, pp3-difftool-flag-fragile, pp-weird-hunter-16
- Reproduced by: none (current output is safe or the path is disabled; pinned by the test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_toolchange_session.py::ToolChangeSafetyTests::test_m00_with_different_tool_still_retracts_before_m06`

### PP-057

**Dormant option/event paths emit Fanuc/Haas-only code (G65/G112/O777 macros, M98/M99, G20, G43/G49, '#' macros, WHILE[ loop)**

- Severity: low
- Confidence: confirmed
- Reachability: Only with non-default options (i4xIndexMode=2, bUseprognum, iProgendmode) or VMID-disabled events (subroutines, loops).
- Location: GPP @call_proc L2015/L2036-2037, @proc/@end_proc L2043-2061, @end_loop L2080-2087, @start_of_job L1163-1168, @usr_trig_macro_* L2551-2614, @usr_heightcomp_on/off L919-938, @usr_4x_index L2483
- Evidence that would settle it: None needed; static allowlist pins the legacy procedures and VMID guards keep them disabled.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: TSR-18, history-misc-16, R1-06, tc-13, tc-17, pp-weird-hunter-17, pp-region-4-cycles-rotary-19
- Reproduced by: none (current output is safe or the path is disabled; pinned by the test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_gpp_static.py::GppStructureTests::test_fanuc_only_output_is_pinned_to_legacy_procedures`
  - `tests/test_machine_definition.py::ConfigurationGuards::test_vmid_keeps_subroutines_and_loops_disabled`

### PP-058

**Mach3 4x post (6efcad8): the feed re-statement remedy is missing on @line_5x and @arc**

- Severity: low
- Confidence: uncertain
- Reachability: Mach3 post only (uninitialised submodule mach3/4x or MACH3_PP_SOURCE).
- Location: mach3/4x/Mach3_4X_Y.gpp at 6efcad8 (@line_5x and @arc lack the feed re-statement of @line)
- Evidence that would settle it: A recorded Mach3 run of a line_5x/arc feed change, and the post version the submodule would pin.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: history-misc-18
- Reproduced by:
  - `tests/test_mach3_feed_force.py::Mach3FeedForceTests::test_line_5x_and_arc_feed_changes_are_restated_too`

## Engine gaps and fidelity issues (ENGINE-xxx)

### ENGINE-001

**Change-flag rule for equal-value assignment is unverified (engine: only a value change raises a flag, nothing clears it)**

- Severity: medium
- Confidence: uncertain
- Reachability: Every session test: decides whether init assignments leave flags pending (PP-054) and what a first job prints.
- Location: pp_tests/gppl/legacy.py Engine.call assignment branch (a flag is raised only when the value changes and never cleared)
- Evidence that would settle it: 10-line probe GPP in SolidCAM (global integer i; init i=9; start_of_job i=9; if change(i) {nb,'CHANGED'}) or a trace "all":5 of a first job.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: efc-01, pp3-engine-change-flags, TSR-17
- GPPL engine: Same default rule (policy change_on_equal_assign=keep; alternatives clear, clear_user, set).
- Reproduced by: none (an unverified engine rule; pinned by the CHARACTERIZATION tests below)
- Pinned or exercised by (`@covers`):
  - `tests/test_cycles_spindle.py::MutationKillTests::test_guards_detect_mutations`
  - `tests/test_engine_harness.py::EngineSemanticsPins::test_declared_variable_equal_assignment_keeps_flag`
  - `tests/test_engine_harness.py::EngineSemanticsPins::test_system_variable_equal_assignment_keeps_flag`

### ENGINE-002

**skipline block joining is not emulated (nb/nl always start a new block)**

- Severity: low-medium
- Confidence: confirmed
- Reachability: GPP sets skipline 21 times (usr_rapid, usr_ct_after, coolant, drill); a mutation that joins the rotary and XYZ rapid survives.
- Location: pp_tests/gppl/legacy.py Engine._render (nb/nl always start a new block; 'skipline' is a plain variable)
- Evidence that would settle it: One real trace showing a skipline=false join and whether nl also consumes it (auto-reset semantics).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-03, efc-05
- Engine scope: every facet reproduces only on legacy (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: Fixed in the NC stream: engine.nc_lines()/nc_text() join one block per skipline=false assignment (policy skipline=join_next_nb). engine.output, the fragment list most tests read, never joins.
- Reproduced by:
  - `tests/test_engine_harness.py::OutputGaps::test_skipline_false_joins_the_next_block`
- Pinned or exercised by (`@covers`):
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_opt_in_emulations`

### ENGINE-003

**numeric_def_f / integer_def_f are ignored: unformatted numbers use 3 decimals instead of '8.5'**

- Severity: low-medium
- Confidence: confirmed
- Reachability: Arc centre words I/J/K/R, CYCLE parameters and any number without a <name>_f format.
- Location: pp_tests/gppl/legacy.py Engine._render numeric descriptor fallback (precision 3 when no <name>_f)
- Evidence that would settle it: A posted MPF with an unformatted arc centre (number of decimals).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-05, efc-04, engine-impl-critic-12
- GPPL engine: Policy typed_default_formats=on implements it (default off).
- Reproduced by:
  - `tests/test_engine_harness.py::OutputGaps::test_numeric_def_f_formats_unformatted_numeric_variables`
- Pinned or exercised by (`@covers`):
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_opt_in_emulations`

### ENGINE-004

**The engine's doubled-quote ('') escape renders a stray apostrophe in the CYCLE84 argument list (',0,''')**

- Severity: low-medium
- Confidence: likely-engine-artifact
- Reachability: Every G84 job (@drill L1883/L1886); bea8c62 edited the line without touching the quote, so a real PP defect is unlikely.
- Location: pp_tests/gppl/legacy.py uncomment()/_render literal regex '(?:[^']|'')*'; GPP @drill L1883/L1886
- Evidence that would settle it: One SolidCAM G84 run (posted CYCLE84 line) or a GPPL manual statement on literal quoting.
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: engine-impl-critic-06, history-misc-06, pp-region-4-cycles-rotary-24, pp-weird-hunter-10
- GPPL engine: Same default (policy quote_escape=double; alternative none).
- Reproduced by:
  - `tests/test_cycles_spindle.py::RigidTappingTests::test_cycle84_arguments_are_numeric_and_ordered`
- Pinned or exercised by (`@covers`):
  - `tests/test_cycles_spindle.py::RigidTappingTests::test_cycle84_rigid_tapping_fields`
  - `tests/test_offline.py::HarnessTests::test_string_case_and_escaped_quotes`

### ENGINE-005

**Declared globals get no change flag (locals get False); change(<global>) raises KeyError**

- Severity: medium
- Confidence: confirmed
- Reachability: Sessions from @init_post die at @usr_hsm_mode without blanket flag filling.
- Location: pp_tests/gppl/legacy.py Engine.call declaration branch (global: state only, no change flag)
- Evidence that would settle it: GPPL manual statement on the initial change flag of declared variables.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-04
- GPPL engine: Policy declared_flag=false implements it (default none).
- Reproduced by:
  - `tests/test_engine_harness.py::ScopeAndDeclarationGaps::test_declared_global_has_change_flag`
- Pinned or exercised by (`@covers`):
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_opt_in_emulations`

### ENGINE-006

**Leading-zero integer literal 07 raises (Python parser)**

- Severity: low
- Confidence: confirmed
- Reachability: GPP line 990 (@usr_coolant, through coolant 30 bar).
- Location: pp_tests/gppl/legacy.py Engine.expression (ast.parse rejects 07); GPP @usr_coolant L990
- Evidence that would settle it: None needed (GPP ships the literal).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: efc-06, engine-impl-critic-14, tc-16
- Engine scope: every facet reproduces only on legacy (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: Fixed: 07 is the integer 7.
- Reproduced by:
  - `tests/test_engine_harness.py::ExpressionGaps::test_leading_zero_integer_literal`
- Pinned or exercised by (`@covers`):
  - `tests/test_engine_harness.py::CompatAdditivityTests::test_default_options_reproduce_stock_sessions`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_compat_evaluates_the_through_coolant_literal`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_setup_engine_builtins`

### ENGINE-007

**right() and tostr(value:'fmt') built-ins are missing**

- Severity: low
- Confidence: confirmed
- Reachability: @usr_sof_progname, @usr_US_date/@usr_US_time (start_of_file header) and @Multiple_Fixtures.
- Location: pp_tests/gppl/legacy.py Engine._node function table (no right/tostr); GPP L251/L300/L325/L2221
- Evidence that would settle it: None needed (shipped template code); clamp right() to the string length.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: R1-10, efc-06, engine-impl-critic-14, pp-region-4-cycles-rotary-25
- Engine scope: every facet reproduces only on legacy (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: Fixed: right() and tostr(v:'fmt') are built in; right() of a count above the string length is ENGINE-021.
- Reproduced by:
  - `tests/test_engine_harness.py::ExpressionGaps::test_right_and_tostr_builtins`
- Pinned or exercised by (`@covers`):
  - `tests/test_engine_harness.py::CompatAdditivityTests::test_default_options_reproduce_stock_sessions`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_compat_runs_us_date_and_time_conversion`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_setup_engine_builtins`

### ENGINE-008

**Print statement is unsupported (assumed: message window, generation continues)**

- Severity: low
- Confidence: uncertain
- Reachability: @usr_4x_index index clearance warnings (L2426/L2456).
- Location: pp_tests/gppl/legacy.py Engine.call (Print is an unsupported statement); GPP @usr_4x_index L2426/L2456
- Evidence that would settle it: GPPL manual or a SolidCAM run showing where Print output goes.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: efc-06, pp-region-4-cycles-rotary-25
- GPPL engine: Policy print_stmt=console implements it (default error).
- Reproduced by:
  - `tests/test_engine_harness.py::StatementGaps::test_print_statement_does_not_stop_the_post`
- Pinned or exercised by (`@covers`):
  - `tests/test_engine_harness.py::CompatAdditivityTests::test_default_options_reproduce_stock_sessions`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_compat_print_lets_the_index_warning_continue`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_print_and_trace_statements_continue`

### ENGINE-009

**input is treated as a terminal stop and abort raises the same exception as engine gaps; deleting abort leaves the suite green**

- Severity: medium
- Confidence: confirmed
- Reachability: The POST ERROR guards (@usr_arc_check, @usr_r1_output, and since the review fixes the ZX arc, TRC-on-arc and full-turn cutting block stops).
- Location: pp_tests/gppl/legacy.py Engine.call ('abort' and 'input' raise UnsupportedGPPL); GPP @usr_arc_check L1460-1462, @usr_r1_output L2399-2401
- Evidence that would settle it: GPPL semantics: input prompts and continues, abort terminates (dummy_var idiom in the GPP).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-01
- GPPL engine: input and abort are separate statements: policy input_stmt=scripted answers the prompt and abort raises PostAbort (tests/test_zx_arc_guard.py uses it); the default input_stmt=abort still stops at input.
- Reproduced by:
  - `tests/test_engine_harness.py::PostAbortGuardTests::test_removed_abort_changes_observable_result` (facet `abort-observable`, confidence confirmed)
  - `tests/test_engine_harness.py::StatementGaps::test_engine_input_prompt_is_not_terminal` (facet `input-terminal`, confidence confirmed)
- Pinned or exercised by (`@covers`):
  - `tests/test_arc_compensation_plane.py::ArcGuardTests::test_off_axis_center_words_and_negative_mismatch`
  - `tests/test_arcs.py::ArcTests::test_cad_mismatch_stops_before_the_arc_block`
  - `tests/test_arcs.py::ArcTests::test_exact_mismatch_tolerance_each_axis`
  - `tests/test_offline.py::PostprocessorTests::test_invalid_direction_is_not_silently_emitted`

### ENGINE-010

**tonum() of a non-numeric string raises (tonum('G5'))**

- Severity: low
- Confidence: confirmed
- Reachability: @home_number and @home_data with operator-entered CoordSys names.
- Location: pp_tests/gppl/legacy.py Engine._node tonum (float() of the text); GPP @home_number L620-624, @home_data L2620
- Evidence that would settle it: GPPL manual statement on tonum() of non-numeric text.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-14, pp-region-4-cycles-rotary-25
- GPPL engine: Policy tonum=atof implements it (default strict).
- Reproduced by:
  - `tests/test_engine_harness.py::ExpressionGaps::test_tonum_of_non_numeric_text_returns_zero`

### ENGINE-011

**Python-superset expression semantics are accepted silently (chained comparisons, hex, string*int, negative left/substr, precedence)**

- Severity: low
- Confidence: confirmed
- Reachability: Latent: no current GPP line depends on it.
- Location: pp_tests/gppl/legacy.py Engine.expression/_node (Python AST subset)
- Evidence that would settle it: GPPL manual expression grammar.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-08, efc-15
- Engine scope: every facet reproduces only on legacy (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: Fixed: its own expression parser rejects the Python-only syntax.
- Reproduced by:
  - `tests/test_engine_harness.py::ExpressionGaps::test_python_only_syntax_is_rejected`

### ENGINE-012

**Re-executing a local declaration loses the outer value; flat dict gives dynamic scope**

- Severity: low
- Confidence: uncertain
- Reachability: Latent; GPPL local scoping itself is unproven.
- Location: pp_tests/gppl/legacy.py Engine.call local declaration branch (locals_saved overwritten; one flat dict)
- Evidence that would settle it: GPPL manual statement on local variable scope.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-09
- Engine scope: facet `redeclare` reproduces only on legacy (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: Facet redeclare fixed (locals live in call frames); dynamic scope is the default (policy local_scoping=lexical is the alternative).
- Reproduced by:
  - `tests/test_engine_harness.py::ScopeAndDeclarationGaps::test_callee_assignment_to_caller_local_name_reaches_global` (facet `dynamic-scope`, confidence uncertain)
  - `tests/test_engine_harness.py::ScopeAndDeclarationGaps::test_local_redeclared_in_loop_restores_global` (facet `redeclare`, confidence uncertain)

### ENGINE-013

**Integer-typed variables hold fractions (no truncation/rounding on assignment)**

- Severity: low
- Confidence: uncertain
- Reachability: @usr_spindle_output, @home_number, @usr_prep_home_axis integer arithmetic.
- Location: pp_tests/gppl/legacy.py Engine.call declarations (types parsed but discarded)
- Evidence that would settle it: GPPL manual statement on integer assignment (truncate vs round).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-10
- GPPL engine: Policy integer_assign=truncate or round_half_away implements it (default keep).
- Reproduced by:
  - `tests/test_engine_harness.py::ScopeAndDeclarationGaps::test_integer_variable_does_not_hold_fraction`

### ENGINE-014

**Declaration parser accepts junk names; assignments to undeclared names are accepted**

- Severity: low
- Confidence: confirmed
- Reachability: Latent; no current GPP typo found.
- Location: pp_tests/gppl/legacy.py Engine.call declaration regex and assignment branch
- Evidence that would settle it: SolidCAM load of a GPP with an undeclared variable (rejected or not).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-11
- Engine scope: every facet reproduces only on legacy (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: Fixed: declarations are parsed and validated at load.
- Reproduced by:
  - `tests/test_engine_harness.py::ScopeAndDeclarationGaps::test_declaration_with_initializer_is_not_silently_accepted`

### ENGINE-015

**Rendering details: "" escape differs between _render and expression(), half-even ties, bool printed as True, '(p)' ignored**

- Severity: low
- Confidence: confirmed
- Reachability: Latent; affects exact-text assertions only.
- Location: pp_tests/gppl/legacy.py Engine._render (token regex, numeric rounding, bool rendering)
- Evidence that would settle it: GPPL manual statement on literal escapes and numeric rounding.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-12
- Engine scope: every facet reproduces only on legacy (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: Fixed: output and expressions share one literal model.
- Reproduced by:
  - `tests/test_engine_harness.py::OutputGaps::test_double_quoted_literal_escape_matches_expression_parser`

### ENGINE-016

**trace.py: nested-call ..> lines become NC output; fixed-width indentation is assumed**

- Severity: low
- Confidence: confirmed
- Reachability: Only when importing new SolidCAM traces as fixtures.
- Location: pp_tests/trace.py parse_trace (fixed-width ..> continuation and nested-call handling)
- Evidence that would settle it: A captured trace with nested calls and different indentation.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: engine-impl-critic-13
- GPPL engine: Not engine code: pp_tests/trace.py is shared by both engines.
- Reproduced by:
  - `tests/test_contracts.py::TraceContractTests::test_nested_call_parameters_are_not_nc_output`

### ENGINE-017

**Trace sanitizer redacts the enum inputs (feed_type, prev_command, ...) that drive the CAM-link homing bypass**

- Severity: low
- Confidence: confirmed
- Reachability: Only when importing new SolidCAM traces as fixtures.
- Location: pp_tests/trace.py sanitize (identifier allowlist)
- Evidence that would settle it: None needed (allowlist in pp_tests/trace.py).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: efc-10
- GPPL engine: Not engine code: pp_tests/trace.py is shared by both engines.
- Reproduced by:
  - `tests/test_contracts.py::TraceContractTests::test_safety_relevant_enums_survive_sanitizing`

### ENGINE-018

**Historical-revision constructs are unsupported: active trace statements and numeric formats '<(>5.3<)>', '(*k)', '+8.5', '(n)'**

- Severity: low
- Confidence: confirmed
- Reachability: Reversion tests against older GPP revisions; newshift_*_f and tostr(...:5.0(n)) in the current GPP.
- Location: pp_tests/gppl/legacy.py Engine.call statement dispatch (trace) and Engine._render descriptor regex
- Evidence that would settle it: None needed for support; GPPL manual for the exact meaning of the (n) and (*k) modifiers.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: history-rotary-15, history-indexing-link-12, engine-impl-critic-12
- GPPL engine: Policies format_grammar=extended and trace_stmt=ignore implement it (defaults legacy and error).
- Reproduced by:
  - `tests/test_engine_harness.py::OutputGaps::test_historical_formats_and_trace_statements_are_accepted`
- Pinned or exercised by (`@covers`):
  - `tests/test_engine_harness.py::CompatAdditivityTests::test_default_options_reproduce_stock_sessions`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_extended_format_descriptors`
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_print_and_trace_statements_continue`

### ENGINE-019

**Text outside procedures is silently ignored by the parser**

- Severity: low
- Confidence: confirmed
- Reachability: Latent: a stray statement between procedures would not be executed or reported.
- Location: pp_tests/gppl/legacy.py Engine.__init__ (lines outside @...endp are dropped)
- Evidence that would settle it: GPPL manual: is code outside procedures an error at load?
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: TSR-17
- GPPL engine: Policy load_errors=raise implements it (default lazy).
- Reproduced by:
  - `tests/test_engine_harness.py::StatementGaps::test_code_outside_procedures_is_reported`
- Pinned or exercised by (`@covers`):
  - `tests/test_gpp_static.py::GppStructureTests::test_every_statement_is_inside_a_procedure`

### ENGINE-020

**Identifiers inside '(expr)' output tokens get their change flags cleared**

- Severity: low
- Confidence: uncertain
- Reachability: Latent; no current GPP output depends on it.
- Location: pp_tests/gppl/legacy.py Engine._render ('(expr)' tokens clear the flags of their identifiers)
- Evidence that would settle it: GPPL manual statement on clear_change_after_gen for expression output tokens.
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: efc-15
- GPPL engine: Same default behaviour.
- Reproduced by:
  - `tests/test_engine_harness.py::OutputGaps::test_expression_output_token_keeps_operand_change_flags`

## Design questions for the owner (DESIGN-xxx)

### DESIGN-001

**CAM-link trust: a rapid that descends inside a confirmed link keeps the authorization, and any positive Z step (0.001 mm) authorizes an unhomed rotation**

- Severity: low
- Confidence: uncertain
- Reachability: Default config inside CAM links of 4x/5x jobs.
- Location: GPP @usr_rapid L1222-1230 and L1362-1366 (link kept without a Z check); @usr_line L1387-1394 ('zpos gt nLastPathZ')
- Evidence that would settle it: Real SolidCAM 4x/5x link traces: does a descending rapid ever precede a rotary rapid inside one link, and what retract heights occur?
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: history-indexing-link-10, pp-weird-hunter-19
- Reproduced by: none (owner decision; pinned by the CHARACTERIZATION test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_indexing_link.py::DesignPinTests::test_cam_link_trusts_any_positive_z_step_and_descending_rapids`

### DESIGN-003

**A deferred tmatrix index runs before the tool change (old tool, spindle and coolant on, double M1)**

- Severity: low
- Confidence: confirmed
- Reachability: Default config, index between different-tool jobs.
- Location: GPP @start_of_job L1110-1115 (deferred index) before L1145-1148 (@usr_ct)
- Evidence that would settle it: Owner policy: index before or after the tool change.
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: efc-13, tc-12, pp-weird-hunter-15
- Reproduced by: none (owner decision; pinned by the CHARACTERIZATION test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_indexing_link.py::DesignPinTests::test_deferred_tmatrix_index_runs_before_tool_change`

### DESIGN-004

**In confirmed CAM links the rotary block always precedes the XYZ block, even when Z rises in the same event**

- Severity: low
- Confidence: confirmed
- Reachability: Default config; pinned by tests/fixtures/shit2_contiguous_link.json.
- Location: GPP @usr_rapid L1285-1288 (A block first) vs L1322-1333 (XYZ block after)
- Evidence that would settle it: Owner policy (rise first vs rotate first within a confirmed link).
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: pp3-rising-link-rotary-order
- Reproduced by: none (owner decision; pinned by the CHARACTERIZATION test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_motion.py::MotionSequenceTests::test_actual_shit2_contiguous_link`

### DESIGN-005

**A tool change zeroes CAM apos/bpos/cpos, so A unwinds/rewinds between 5x jobs and the direction comes from angle_4x_around_x_dir (abort if not cw/ccw)**

- Severity: low
- Confidence: uncertain
- Reachability: Default config, tool change between simultaneous jobs.
- Location: GPP @usr_tc_init_gmstates L908-913 (apos/bpos/cpos = 0); @usr_ct_after L836-849; @usr_r1_select_dir L2371-2376 (abort L2397-2401)
- Evidence that would settle it: Trace showing angle_4x_around_x_dir at a tool change; owner policy for the rewind.
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: history-rotary-12, pp-weird-hunter-14
- Reproduced by: none (owner decision; pinned by the CHARACTERIZATION test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_rotary.py::RotaryDesignPins::test_pin_toolchange_zeroes_cam_apos_and_round_trips_a`

### DESIGN-006

**Single origin: the shipped home_number maps every CoordSys to G54 and newshift/ORGXYZ are computed but unused**

- Severity: low
- Confidence: confirmed
- Reachability: Default iWorkOffset_Method=0 (c85f5f7 deliberately maps all MACs to G54; pp-weird-hunter-11 refuted).
- Location: GPP @home_number L611-618 (iWorkoffset = 54; newshift computed, output commented out in @home_data L2658-2661); vericut/GcodeSim.ini [MAC]
- Evidence that would settle it: Owner policy: confirm all CoordSys share one origin (G54).
- Owner area: C (indexing, CAM-link state machine, work offsets and multiple fixtures)
- Source findings: R1-11, pp-weird-hunter-11(refuted)
- Reproduced by: none (owner decision; pinned by the CHARACTERIZATION test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_work_offsets_fixtures.py::WorkOffsetTests::test_shipped_method_ignores_coordsys_position`

### DESIGN-007

**Non-zero secondary rotation (bpos / x_angle_const_z) is silently ignored apart from the old vertical-head toggle**

- Severity: low
- Confidence: confirmed
- Reachability: Only for CAM output with a secondary rotation, which a 4-axis machine should not receive.
- Location: GPP @usr_r1pos_calc L2315-2340 (nR2pos never output); @usr_rapid L1248-1273 (bVertical toggle)
- Evidence that would settle it: Owner policy: abort on a non-zero secondary rotation or ignore it.
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: history-rotary-13, pp-region-4-cycles-rotary-26
- Reproduced by: none (owner decision; pinned by the CHARACTERIZATION test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_rotary.py::RotaryDesignPins::test_secondary_rotation_adds_no_extra_rotation`

## Fixed

Fixed by owner-approved GPP commits. The former canonical test of each entry (or facet) is
now a regression guard marked `@covers`.

| id | fixing commit | guarded by (`@covers`) | tests of the fix |
|---|---|---|---|
| [PP-001](#pp-001) | 345cb49 | `test_xy_reestablished_after_homing_in_rotary_rapid`, `test_y_reestablished_after_job_start_index_homing` | `tests/test_post_homing_reposition.py` |
| [PP-002 [rounding]](#pp-002) | 6228b3d | `test_directed_a_positions_stay_in_modulo_range`, `test_emitted_a_positions_are_valid_modulo_positions` | `tests/test_rotary_modulo_range.py` |
| [PP-002 [whole-turn]](#pp-002) | 6228b3d | `test_directed_a_positions_stay_in_modulo_range`, `test_emitted_a_positions_are_valid_modulo_positions` | `tests/test_rotary_modulo_range.py` |
| [PP-003](#pp-003) | 5408e5c | `test_zx_arc_stops_the_post` | `tests/test_zx_arc_guard.py` |
| [PP-007](#pp-007) | ca63502 | `test_move_4x_preserves_axial_x` | `tests/test_move_4x_axial_x.py` |
| [PP-013](#pp-013) | 49f8b80 | `test_same_tool_job_climbs_before_xy_traverse` | `tests/test_job_start_climb.py` |
| [PP-019](#pp-019) | b999f65 | `test_compensation_off_before_retract_reaches_controller_before_next_tool_cuts`, `test_compensation_off_emitted_on_following_rapid`, `test_compensation_on_emitted_on_following_rapid` | `tests/test_cutter_compensation.py` |
| [PP-020](#pp-020) | b999f65 | `test_compensation_not_activated_in_circular_block`, `test_compensation_not_deactivated_in_circular_block` | `tests/test_cutter_compensation.py` |
| [PP-021](#pp-021) | 88695c9 | `test_drill_cycle_after_yz_arc_runs_in_g17`, `test_xy_compensation_after_yz_arc_runs_in_g17` | `tests/test_job_plane_restore.py` |
| [PP-028](#pp-028) | a38f158 | `test_left_hand_tap_uses_negative_pitch` | `tests/test_tapping_direction.py` |
| [PP-049](#pp-049) | 9f48a3a | `test_rotary_feed_moves_use_the_documented_inverse_time_mode` | `tests/test_inverse_time_feed.py` |
| [ENGINE-021](#engine-021) | 0eb3cef | `test_right_count_beyond_the_string_returns_the_whole_string` |  |
| [DESIGN-002](#design-002) | 3e0c345 | `test_homed_rotary_rapid_returns_xy_then_z` | `tests/test_post_homing_reposition.py` |

### PP-001

**PP-inserted G75 Y1=0 X1=0 homing is not followed by X/Y re-programming; the next move starts from the machine reference point**

- Severity: high
- Confidence: confirmed
- Reachability: Default config (every sHomestr* homes Z then XY). Mid-job rotation rapid (@usr_rapid) and job-start/tmatrix index (@usr_4x_index) whenever the CAM does not flag X or Y as changed (common: A turns about X, Y0 on the rotary centreline). Assumes SolidCAM flags only changed coordinates (shit2 trace: line_5x flagged with zpos/feed only).
- Location: GPP @usr_rapid L1278-1288 (homing + rotation) and L1322-1334 (modal X/Y); @usr_4x_index L2415-2422; @usr_prep_home_axis/@usr_home_axis L2091-2190 set no change(xpos/ypos)
- Evidence that would settle it: SolidCAM trace or MPF of a non-link rotary rapid with unchanged X and of an index with unchanged Y (or a Vericut run); a trace showing whether a PP-set change(xpos)=true survives into an event whose CAM X is unchanged (the harness resets CAM flags per event, which rejects that sticky-flag fix).
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: TSR-04, pp-weird-hunter-01, pp3-engine-change-flags, pp3-diagonal-plunge-after-homing(missed)
- Status: fixed: 345cb49 Reprogram X, Y and Z after post-inserted homing (follow-ups ed07c3f, b94251b). Also covers the tool-change case whose first point keeps the previous X/Y.
- Tests of the fix: tests/test_post_homing_reposition.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_motion_rapids.py::HomingRestoreTests::test_xy_reestablished_after_homing_in_rotary_rapid`
  - `tests/test_motion_rapids.py::HomingRestoreTests::test_y_reestablished_after_job_start_index_homing`

### PP-003

**G18 (ZX) arc validation/rotation is the mirror of the G18 convention: the post aborts or the control sweeps 360-arc_size**

- Severity: medium
- Confidence: uncertain
- Reachability: Default iArcmode=2 whenever SolidCAM emits @arc in ZX (VMID ArcDirectionBy="0", SupportGrt180degArcs="0"). Outcome depends on the UNVERIFIED arc_direction convention in ZX: loud abort (standard convention, medium) or silent reversed arc (front-view convention, high).
- Location: GPP @usr_arc_math L1494-1498 (G2/G3 from arc_direction) and L1541-1549 (ZX rotation); output @usr_arc L1585/L1601-1614
- Evidence that would settle it: One real @arc trace in the ZX plane (start, center_rel, arc_size, arc_direction, CAD end point) plus the meaning of the VMID ArcDirectionBy setting, or a Vericut run of a posted ZX arc.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: pp3-zx-orientation, history-misc-04, pp-weird-hunter-02, pp3-test-arcs-pins-wrong-conventions
- Status: fixed: 5408e5c Stop the post on ZX (G18) arcs. Owner decision: every ZX arc stops the post with a POST ERROR until the arc_direction convention is verified (text simplified in 595df73, written on its own NC line in e797c18).
- Tests of the fix: tests/test_zx_arc_guard.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_arc_compensation_plane.py::ArcSweepConventionTests::test_zx_arc_stops_the_post`

### PP-007

**@move_4x replaces any changed X with X0**

- Severity: medium
- Confidence: uncertain
- Reachability: Only if SolidCAM emits @move_4x on this machine (legacy 4X/wrap operations); UNVERIFIED.
- Location: GPP @move_4x L2489-2500 (L2494-2496: if change(xpos) xpos = 0)
- Evidence that would settle it: SolidCAM debug trace of one wrap/4x rotary operation showing that @move_4x fires and that xpos is the axial X.
- Owner area: B (rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, 3-axis limit, home_data)
- Source findings: pp-region-4-cycles-rotary-01, pp-weird-hunter-07
- Status: fixed: ca63502 Post the CAM X in @move_4x.
- Tests of the fix: tests/test_move_4x_axial_x.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_rotary.py::FixedRotaryDefectGuards::test_move_4x_preserves_axial_x`

### PP-013

**First rapid of a same-tool job traverses XY before climbing to a higher Z**

- Severity: medium
- Confidence: confirmed
- Reachability: Default config when the previous same-tool job ends lower than the new job's first rapid Z (different clearance levels).
- Location: GPP @start_of_job L1149-1158 (same-tool branch: no retract), @usr_rapid L1322-1333 (first move: XY block before Z)
- Evidence that would settle it: Trace of two same-tool operations with different clearance levels (how often it occurs).
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: tc-01, pp3-first-rapid-climb
- Status: fixed: 49f8b80 Climb before traversing on a job's first rapid (follow-ups fc664ce and b94251b: the current Z is tracked through drill cycles, indexing and M00).
- Tests of the fix: tests/test_job_start_climb.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_motion_rapids.py::FirstRapidTests::test_same_tool_job_climbs_before_xy_traverse`

### PP-019

**A compensation change before a rapid is never written: G40/G41 deferred, G40 lost across a tool change**

- Severity: medium-high
- Confidence: uncertain
- Reachability: Default config if SolidCAM emits @compensation immediately before a rapid (e.g. lead-out None); the tool-change facet also needs no line/arc between the COMP_OFF rapid and end_of_job. Event order UNVERIFIED.
- Location: GPP @compensation L1635-1652; @usr_rapid L1286/L1294/L1303/L1323 (no TRC word); @usr_tc_init_gmstates L896 (iDiametercomp = 40 without output)
- Evidence that would settle it: SolidCAM trace of a compensated profile with lead-out None, then a Vericut/828D run of the result.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: pp3-trc-change-before-rapid-lost
- Status: fixed: b999f65 Switch cutter compensation only on linear blocks (rapids carry the pending G40/G41/G42; the tool-change safety block is G17 G40 G64 G90). 264be29 deferred the TRC change of a Z-only rapid to the next X/Y block; 2f5b759 writes it on that rapid with explicit X and Y ('G0 G40 X.. Y.. Z50').
- Tests of the fix: tests/test_cutter_compensation.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_arc_compensation_plane.py::CompensationTests::test_compensation_off_before_retract_reaches_controller_before_next_tool_cuts`
  - `tests/test_arc_compensation_plane.py::CompensationTests::test_compensation_off_emitted_on_following_rapid`
  - `tests/test_arc_compensation_plane.py::CompensationTests::test_compensation_on_emitted_on_following_rapid`

### PP-020

**G41/G42/G40 are written inside G2/G3 blocks (Sinumerik alarms 10753/10754)**

- Severity: medium
- Confidence: uncertain
- Reachability: Default config when @compensation immediately precedes an @arc (arc lead-in/lead-out, 2aa6df0 removed the lookahead); event order UNVERIFIED.
- Location: GPP @usr_arc L1585 (['G'iDiametercomp' '] in the circular block); @compensation L1635-1652
- Evidence that would settle it: Trace of a profile with an arc lead-in or lead-out showing @compensation directly before @arc.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: pp3-trc-in-arc, pp-weird-hunter-12
- Status: fixed: b999f65 Switch cutter compensation only on linear blocks. Owner decision: a compensation change on an arc stops the post with a POST ERROR (use a linear lead-in/lead-out); 264be29 compares against the TRC state last posted; e797c18 writes the text on its own NC line.
- Tests of the fix: tests/test_cutter_compensation.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_arc_compensation_plane.py::CompensationTests::test_compensation_not_activated_in_circular_block`
  - `tests/test_arc_compensation_plane.py::CompensationTests::test_compensation_not_deactivated_in_circular_block`

### PP-021

**G18/G19 set by an arc stays active into the next same-tool job: G41 and drill cycles run in the wrong plane**

- Severity: medium
- Confidence: uncertain
- Reachability: Default config: a ZX/YZ arc followed by a same-tool job (only the tool-change path re-emits the plane). UNVERIFIED: assumes SolidCAM does not deliver @machine_plane at every job start.
- Location: GPP @usr_arc_math L1501-1509 (sets the global iMplane); only @usr_tc_init_gmstates L867/L884 calls @machine_plane
- Evidence that would settle it: Trace of a ZX/YZ arc job followed by a same-tool XY profile or drill job.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: pp3-plane-persistence
- Status: fixed: 88695c9 Restore the machining plane at the start of each job (follow-ups 9767011: G17 fallback, TRC selected in the job plane; 2f5b759: the plane is re-selected when TRC is selected from G40).
- Tests of the fix: tests/test_job_plane_restore.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_arc_compensation_plane.py::PlaneModalityTests::test_drill_cycle_after_yz_arc_runs_in_g17`
  - `tests/test_arc_compensation_plane.py::PlaneModalityTests::test_xy_compensation_after_yz_arc_runs_in_g17`

### PP-028

**Left-hand tap (CCW tool) gets a positive CYCLE84 pitch, i.e. right-hand tapping**

- Severity: medium
- Confidence: confirmed
- Reachability: Default config, G84 job with a counter-clockwise (left-hand) tap. SDAC 3 (spindle M3 after the cycle) is also wrong for a left-hand tap (pp-region-4-cycles-rotary-08 correction); the canonical test asserts the PIT sign only.
- Location: GPP @drill G84 branch L1881-1897 (''(FEED/SPIN) always positive, SDAC 3 at L1883/L1886); Vericut ctl L1933-1960 (PIT<0 -> CCW)
- Evidence that would settle it: Siemens CYCLE84 (PIT sign selects the direction; repository Vericut control: PIT<0 -> CCW).
- Owner area: E (cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell)
- Source findings: history-misc-07, pp-region-4-cycles-rotary-08
- Status: fixed: a38f158 Post left-hand tapping with a negative CYCLE84 pitch (follow-up 595df73).
- Tests of the fix: tests/test_tapping_direction.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_cycles_spindle.py::RigidTappingTests::test_left_hand_tap_uses_negative_pitch`

### PP-049

**i4xFeedMode=1 (inverse time) is never implemented: simultaneous rotary moves use mm/min F under G94**

- Severity: medium
- Confidence: uncertain
- Reachability: Default i4xFeedMode=1 option is dead; reachable in every 4x simultaneous feed move with an A word.
- Location: GPP option i4xFeedMode L173 (never read); F output @usr_line L1419-1424, @line_4x L2502-2510, @line_5x L2535-2543
- Evidence that would settle it: Controller behaviour of a G94 block with an A word (F as deg/min on a rotary-only block) and the owner's intended feed mode.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: critic-04, pp-weird-hunter-18, pp-region-4-cycles-rotary-26
- Status: fixed: 9f48a3a Post rotating G1 blocks in G93 inverse time (follow-ups f0ffada: F reprogrammed after G93, control A travel; b94251b: indexes and M00 invalidate the G93 start).
- Tests of the fix: tests/test_inverse_time_feed.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_motion_rapids.py::RotaryFeedModeTests::test_rotary_feed_moves_use_the_documented_inverse_time_mode`

### ENGINE-021

**GPPL engine right(s, n) with n > strlen(s) returns a Python slice ('bc' for right('abc', 5)) instead of the whole string**

- Severity: very-low
- Confidence: confirmed
- Reachability: Latent: no GPP call passes a count above the string length (@usr_sof_progname passes at most strlen - 1, @usr_US_date right(date, 4)).
- Location: pp_tests/gppl/builtins.py f_right (text[len(text) - count:] without an upper clamp)
- Evidence that would settle it: None needed (right() returns the last n characters; LegacyCompatEngine already clamps).
- Owner area: F (static checks, engine harness, trace/fixture/machine-definition contracts, Mach3)
- Source findings: integration-review
- Status: fixed: 0eb3cef Clamp right() to the whole string when the count exceeds its length.
- Engine scope: every facet reproduces only on gppl (gppl = pp_tests/gppl, legacy = GPPL_ENGINE=legacy)
- GPPL engine: GPPL engine only (pp_tests/gppl/builtins.py f_right); the legacy engine has no right() (ENGINE-007) and LegacyCompatEngine clamps.
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_engine_harness.py::GpplCompatEngineTests::test_right_count_beyond_the_string_returns_the_whole_string`

### DESIGN-002

**After G75 homing for a rotation the approach is one diagonal 'X Y Z' G0**

- Severity: medium
- Confidence: uncertain
- Reachability: Default config, first rotary link of a 4x/5x job and every homed rotary rapid; high for low-Z targets or RTLIOF (non-linear G0).
- Location: GPP @usr_rapid L1278-1288 (homing + rotation) and L1322-1333 (Z on the XY line unless bFirstMove)
- Evidence that would settle it: Machine data MD20730 G0_LINEAR_MODE / RTLION vs RTLIOF and the fixture layout; owner policy.
- Owner area: D (motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, Z precision, rotary feed mode)
- Source findings: history-indexing-link-09, pp3-diagonal-plunge-after-homing
- Status: fixed: 3e0c345 Split XY and Z when returning from post-inserted homing (owner decision; follow-up ed07c3f).
- Tests of the fix: tests/test_post_homing_reposition.py
- Reproduced by: none (fixed; the regression guards are listed below)
- Guarded by (`@covers`):
  - `tests/test_motion_rapids.py::ApproachAfterHomingTests::test_homed_rotary_rapid_returns_xy_then_z`

## Accepted by the owner

Behaviour the owner decided to keep; a CHARACTERIZATION test pins it.

### PP-008

**Through-tool coolant 30 bar selects M07, the mist code (table 77/76/75/07/71..74)**

- Severity: low
- Confidence: uncertain
- Reachability: Non-default CAM coolant: through_ival_coolant=1 with through_coolant_val=30; executable only with the leading-zero workaround (ENGINE-006).
- Location: GPP @usr_coolant L989-991 (iCoolantM5ON = 07); option iCoolantM2ON = 7 'Mist Coolant ON' L115
- Evidence that would settle it: The machine builder's M-code list for through-spindle coolant pressures (is M70 the 30 bar code?).
- Owner area: A (session-program: program start/end, header, tool list and stock, tool change, coolant, stops, HSM, homing strings)
- Source findings: history-misc-14, tc-08, pp-weird-hunter-09, efc-14
- Status: accepted: Owner decision: the machine has no through-spindle coolant and M7 stays the code for 30 bar; the test is a CHARACTERIZATION pin, not a defect.
- Reproduced by: none (accepted by the owner; pinned by the CHARACTERIZATION test below)
- Pinned or exercised by (`@covers`):
  - `tests/test_toolchange_session.py::ToolChangeDefectTests::test_through_coolant_pressure_codes_pin`

## Observations not registered

Raised by the area reviews; they have no registry id and no canonical test (owner decision).

- **Homing modes 3/4 (user-edited G53 homing)** (area A review): The homing block has no motion word, so after a cut 'G53 Z0' runs at the modal G1 feed. The shipped G75 homing (mode 8) is unaffected.
- **Empty sWorkpcDir header path** (area A review): ';$PATH=/_N_WKS_DIR/_N_WPD' is written for an empty workpiece directory; intended, or should it be /_N_MPF_DIR? Pinned as CHARACTERIZATION only.
- **CYCLE86 lift-off parameters** (area E review): RPA/RPO/RPAP are omitted, so there is no lift-off after the oriented spindle stop (critic-09 second facet). Owner decision; no test because there is no id.
