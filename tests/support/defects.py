"""Canonical registry of suspected PP defects, engine gaps and open design
questions: the single source of truth for @known_defect / @covers markers.

Ids: PP-xxx suspected postprocessor defects (this suite never edits the GPP; a
canonical test documents each one), ENGINE-xxx gaps or fidelity issues of the
test engines (the GPPL engine pp_tests/gppl and the original engine
pp_tests/gppl/legacy.py, selected by GPPL_ENGINE=legacy; neither is edited by
this suite; workarounds live in tests/support/engines.py), DESIGN-xxx policy
questions the owner must decide (never @known_defect; one CHARACTERIZATION pin
with @covers documents the current behaviour).

Status: an entry (or one facet, facet_status) is
  open      the canonical test carries @known_defect and fails while it exists;
  fixed     an owner-approved GPP commit fixed it (resolution names the commit);
            the former canonical test is a regression guard marked @covers;
  accepted  the owner decided the behaviour is intended (resolution says why);
            a @covers CHARACTERIZATION test pins it.
Engine scope: `engines` lists facets that reproduce only on some engines
('gppl' = pp_tests/gppl, 'legacy' = GPPL_ENGINE=legacy). On any other engine
the marker is transparent and the canonical test is a plain guard.

Fields
  severity      after verifier corrections: high | medium-high | medium |
                low-medium | low | very-low | informational
  reachability  default config, or the non-default option / VMID parameter /
                unverified SolidCAM event assumption needed to reach it
  confidence    confirmed | uncertain | likely-engine-artifact
  settle_evidence  the single piece of evidence that would settle the item
  source_findings  dossier finding ids merged into this entry
  owner_area    area (see AREAS) that owns the canonical test(s)
  location      where the behaviour lives (GPP procedure and line numbers at
                f1803b4, pp_tests/*.py, VMID or Vericut file)
  facet_confidence  optional ((facet, confidence), ...) for facets whose
                confidence differs from the entry's (e.g. a confirmed defect
                with one facet that rests on an unverified GPPL semantic)
  status        open | fixed | accepted (see above)
  resolution    fixed: '<commit> <subject>' of the fixing commit (plus
                follow-ups); accepted: the owner decision
  facet_status  optional ((facet, status, resolution), ...) for facets whose
                status differs from the entry's (a partly fixed defect)
  engines       optional ((facet, (engine, ...)), ...): the engines a facet
                reproduces on; facet None is the facetless entry, '*' every facet
  gppl          ENGINE entries: how the GPPL engine handles the gap (fixed, or
                the policy that implements the GPPL behaviour when it is not
                the default)
  fix_tests     fixed entries: the test files that came with the fixing
                commits (further guards besides the @covers tests)

tests/PP_FINDINGS.md is generated from this registry plus the markers in the
test files (tests/support/findings.py); a meta-test keeps it in sync.

Reference rule (tests/test_known_defect_registry.py): an entry must be
referenced by at least one @known_defect or @covers marker once its owner
area's sentinel file (AREAS[area].sentinel) exists. Until then the entry is
pending-port. Area agents never edit this file; corrections go back to the
integrator.
"""
from dataclasses import dataclass, replace

KINDS = {'PP': 'pp', 'ENGINE': 'engine', 'DESIGN': 'design'}
SEVERITIES = ('high', 'medium-high', 'medium', 'low-medium', 'low', 'very-low', 'informational')
CONFIDENCES = ('confirmed', 'uncertain', 'likely-engine-artifact')
STATUSES = ('open', 'fixed', 'accepted')
ENGINES = ('gppl', 'legacy')


@dataclass(frozen=True)
class Defect:
    id: str
    kind: str
    title: str
    severity: str
    reachability: str
    confidence: str
    settle_evidence: str
    source_findings: tuple
    owner_area: str
    location: str = ''
    facet_confidence: tuple = ()
    status: str = 'open'
    resolution: str = ''
    facet_status: tuple = ()
    engines: tuple = ()
    gppl: str = ''
    fix_tests: tuple = ()

    def confidence_for(self, facet=None):
        """Confidence of one facet (the entry's confidence unless overridden)."""
        return dict(self.facet_confidence).get(facet, self.confidence)

    def status_for(self, facet=None):
        """Status of one facet (the entry's status unless facet_status overrides it)."""
        for name, status, _ in self.facet_status:
            if name == facet:
                return status
        return self.status

    def resolution_for(self, facet=None):
        for name, _, resolution in self.facet_status:
            if name == facet:
                return resolution
        return self.resolution

    def reproduces_on(self, engine, facet=None):
        """False when the facet is known not to reproduce on this engine ('gppl'/'legacy')."""
        scope = dict(self.engines)
        engines = scope.get(facet, scope.get('*'))
        return engines is None or engine in engines

    @property
    def fixed_facets(self):
        return tuple(name for name, status, _ in self.facet_status if status != 'open')


@dataclass(frozen=True)
class Area:
    name: str
    sentinel: str          # first new file of the area; its presence activates the reference rule
    files: tuple           # repo-relative files the area owns exclusively


AREAS = {
    'A': Area('session-program: program start/end, header, tool list and stock, tool change, coolant, '
              'stops, HSM, homing strings', 'tests/test_session_program.py',
              ('tests/test_session_program.py', 'tests/test_toolchange_session.py')),
    'B': Area('rotary: r1pos/select_dir/output, modulo range, iR1dir, index direction, move_4x, '
              '3-axis limit, home_data', 'tests/test_rotary.py',
              ('tests/test_rotary.py', 'tests/test_offline.py', 'tests/fixtures/slide_rotary.json')),
    'C': Area('indexing, CAM-link state machine, work offsets and multiple fixtures', 'tests/test_indexing_link.py',
              ('tests/test_indexing_link.py', 'tests/test_work_offsets_fixtures.py', 'tests/test_motion.py',
               'tests/test_arc_link_boundary.py', 'tests/fixtures/motion_sequences.json',
               'tests/fixtures/shit2_contiguous_link.json', 'tests/fixtures/arc_link_boundary.json',
               'tests/ARC_LINK_FINDING.md', 'tests/CAM_LINK_POSTMORTEM.md', 'tests/HISTORY_COVERAGE.md')),
    'D': Area('motion: rapids and approach order, homing restore, feed emulation, arcs, compensation, plane, '
              'Z precision, rotary feed mode',
              'tests/test_motion_rapids.py',
              ('tests/test_motion_rapids.py', 'tests/test_arc_compensation_plane.py', 'tests/test_arcs.py',
               'tests/fixtures/ambiguous_arcs.json')),
    'E': Area('cycles and spindle: CYCLE81-86, MCALL cancel, tapping, spindle start and dwell',
              'tests/test_cycles_spindle.py',
              ('tests/test_cycles_spindle.py', 'tests/test_history_regressions.py',
               'tests/fixtures/history_regressions.json')),
    'F': Area('static checks, engine harness, trace/fixture/machine-definition contracts, Mach3',
              'tests/test_engine_harness.py',
              ('tests/test_engine_harness.py', 'tests/test_gpp_static.py', 'tests/test_contracts.py',
               'tests/test_machine_definition.py', 'tests/test_mach3_feed_force.py')),
}


def _d(id, title, severity, reachability, confidence, settle_evidence, source_findings, owner_area,
       facet_confidence=()):
    return Defect(id, KINDS[id.split('-')[0]], title, severity, reachability, confidence,
                  settle_evidence, tuple(source_findings), owner_area, facet_confidence=tuple(facet_confidence))


# Owner-approved GPP fixes (git log f1803b4..): id -> (status, resolution). A facet
# entry 'PP-002[rounding]' sets one facet only. The former canonical test of a
# fixed entry is its regression guard and carries @covers(id).
RESOLUTIONS = {
    'PP-001': ('fixed', '345cb49 Reprogram X, Y and Z after post-inserted homing (follow-ups 3577b70, ebf9c57). '
                        'Also covers the tool-change case whose first point keeps the previous X/Y.'),
    'PP-002[rounding]': ('fixed', '6228b3d Keep A positions inside 0 <= A < 360 (values that print as 360.000 '
                                  'post 0; follow-up c33ebd0 snaps float noise below 0.0005 to 0).'),
    'PP-002[whole-turn]': ('fixed', '6228b3d Keep A positions inside 0 <= A < 360 (mode 1 wraps into [0, 360); '
                                    'ebf9c57 stops the post on a cutting block that turns A by 360 degrees or more).'),
    'PP-003': ('fixed', '5408e5c Stop the post on ZX (G18) arcs. Owner decision: every ZX arc stops the post with a '
                        'POST ERROR until the arc_direction convention is verified (text simplified in a71e102, '
                        'written on its own NC line in 0ed0b78). Since the machine run of 2026-10-28 one stop, '
                        '@usr_side_arc_stop, covers every YZ and ZX arc instead (G18/G19 move the tool length '
                        'compensation off Z, SD42940 = 0); its text no longer names the ZX direction, and the '
                        'ZX arc math behind it is deleted.'),
    'PP-007': ('fixed', 'ca63502 Post the CAM X in @move_4x.'),
    'PP-008': ('accepted', 'Owner decision: the machine has no through-spindle coolant and M7 stays the code for '
                           '30 bar; the test is a CHARACTERIZATION pin, not a defect.'),
    'PP-013': ('fixed', '49f8b80 Climb before traversing on a job\'s first rapid (follow-ups 399ef13 and ebf9c57: the '
                        'current Z is tracked through drill cycles, indexing and M00).'),
    'PP-019': ('fixed', 'b999f65 Switch cutter compensation only on linear blocks (rapids carry the pending G40/G41/'
                        'G42; the tool-change safety block is G17 G40 G64 G90). 0cfd586 deferred the TRC change of '
                        'a Z-only rapid to the next X/Y block; 6f6f6ce writes it on that rapid with explicit X and Y '
                        "('G0 G40 X.. Y.. Z50')."),
    'PP-020': ('fixed', 'b999f65 Switch cutter compensation only on linear blocks. Owner decision: a compensation '
                        'change on an arc stops the post with a POST ERROR (use a linear lead-in/lead-out); '
                        '0cfd586 compares against the TRC state last posted; 0ed0b78 writes the text on its own NC '
                        'line.'),
    'PP-021': ('fixed', '88695c9 Restore the machining plane at the start of each job (follow-ups 7aeae99: G17 '
                        'fallback, TRC selected in the job plane; 6f6f6ce: the plane is re-selected when TRC is '
                        'selected from G40). Since the machine run of 2026-10-28 YZ/ZX arcs and machining planes '
                        'stop the post, so no arc leaves G18/G19 modal; the restore after one is deleted.'),
    'PP-028': ('fixed', 'a38f158 Post left-hand tapping with a negative CYCLE84 pitch (follow-up a71e102).'),
    'PP-049': ('fixed', '9f48a3a Post rotating G1 blocks in G93 inverse time (follow-ups 1bdfecc: F reprogrammed '
                        'after G93, control A travel; ebf9c57: indexes and M00 invalidate the G93 start).'),
    'PP-002[negative-mode]': ('fixed', '71bac54 Keep only the modulo A range: the iR1posControl 0/2 modes are '
                                       'removed.'),
    'PP-012': ('fixed', 'd9b120b A job that sets the G187 smoothing parameters stops the post; no G187 is written '
                        '(6ce4055: iG187_P 2 stops too; 3fde1a5: iG187_P 1/2/3/-1 and nG187_E select CYCLE832, '
                        'only values out of range or set with bCycle832 off stop).'),
    'PP-022': ('fixed', '6ea969d Keep only Sinumerik arc words (incremental I/J/K): iArcmode 1/3/4 are removed.'),
    'PP-037': ('fixed', '71bac54 Keep only the modulo A range: the shortest-distance mode is removed.'),
    'PP-040': ('fixed', 'd64e209 The homing parser splits entries on ; and :, the prefix is optional.'),
    'PP-041': ('fixed', 'd64e209 Homing modes 1-7 (G53 among them) stop the post; only mode 8 is left.'),
    'PP-042': ('fixed', 'd64e209 Homing modes 1-7 (mode 7 G90 G54 among them) stop the post; only mode 8 is left.'),
    'PP-054[g187-default]': ('fixed', 'd9b120b No G187 output exists any more.'),
    'PP-054[coolant-burst]': ('fixed', '3fde1a5 usr_init_gmstates clears the change flags of its coolant OFF '
                                       'assignments, usr_coolant_output prints each M code once, and the first tool '
                                       'change switches coolant off once like the others (bCooloffend).'),
    'PP-024[ramp-dwell]': ('fixed', 'fb66cad WAITS after the M3/M4 of the M00 restart, as after every spindle '
                                    'start (bSpinWait); the timed G04 is gone.'),
    'PP-026': ('fixed', 'fb66cad The G04 spindle dwell and its literal 500 are gone: WAITS lets the control '
                        'decide when the spindle is at speed.'),
    'PP-053': ('fixed', '467979d The first index before any rapid homes with sHomestrrotv in clearance mode 0, also with the program start homing off (bHomebegin).'),
    'PP-057': ('fixed', 'dde4db6 Remove the Fanuc template paths (follow-ups d64e209 homing modes, 8e19c10 '
                        'O number, d9b120b G187): the post writes no Fanuc/Haas-only words.'),
    'PP-033': ('fixed', 'dde4db6 Remove the multiple-fixture scheme (owner decision 2026-10-27): more than one '
                        'fixture stops the post with a POST ERROR.'),
    'PP-034': ('fixed', 'dde4db6 Remove the multiple-fixture scheme: more than one fixture stops the post.'),
    'PP-035': ('fixed', 'dde4db6 Remove the multiple-fixture scheme: no fixture temp files (TEMPFILE<n>) are '
                        'opened or deleted. The WORKPIECE body buffer (67c62fd) is a separate, balanced file.'),
    'PP-038': ('fixed', 'dde4db6 Remove the trig macro: i4xIndexMode other than 0/1 stops the post.'),
    'PP-043': ('fixed', '937cae2 @home_data no longer writes shift_y (its only reader, the trig macro, is gone).'),
    'PP-059': ('fixed', 'fb78a2b A rapid without axis motion prints its pending modal words in a block of their own.'),
    'PP-046': ('fixed', '1add48e nR1pos is rounded to the output step: a sub-step A change is no rotation (no A word, '
                        'no homing).'),
    'PP-060': ('fixed', '1add48e A feed move or a rotary rapid at the cutting height stops when the A word would turn A '
                        'another way than CAM; 1f3d25d extends it to every rapid not at a Z homing.'),
    'PP-061': ('fixed', "1add48e The full-turn stop counts CAM's own A step; the post's apos = 0 no longer trips it "
                        '(1f3d25d: cpos/apos references, cnext, 3-axis events keep them).'),
    'PP-062': ('fixed', '01dd68f Compensation left on is deselected at the job end (clearance height) or right after '
                        'the Z homing; 1f3d25d adds index modes 1/2 and stops at a combined Z+X/Y homing line.'),
    'PP-044': ('fixed', 'dde4db6 @call_proc, @proc and @end_proc stop the post with a POST ERROR (VMID GenProc=0).'),
    'PP-045': ('fixed', 'dde4db6 @change_ref_point stops the post with a POST ERROR instead of writing G10 L2.'),
    'PP-047': ('fixed', '6ce4055 @rotate and @mirror stop the post with a POST ERROR (owner rule 2026-10-28).'),
    'DESIGN-002': ('fixed', '3e0c345 Split XY and Z when returning from post-inserted homing (owner decision; '
                            'follow-up 3577b70).'),
    'ENGINE-004': ('fixed', "6d4ea82 The CYCLE84 line writes ',0,' instead of the doubled-quote literal, so every "
                            'reading of GPPL quoting gives the same quote-free argument list.'),
    'ENGINE-021': ('fixed', '709e40f Clamp right() to the whole string when the count exceeds its length.'),
    'DESIGN-003': ('fixed', 'f6e4e4d Index at a tool change: the tool-change block turns A, no separate M1 and homing '
                            '(owner decision 2026-10-28; the index M1 only without bOptstptc, none before the first '
                            'tool).'),
    'PP-015[first-tool-index]': ('fixed', "f6e4e4d Index at a tool change: the tool-change block turns A, no separate "
                                          "M1 and homing (the first job's tmatrix index moves no Z; the first-job "
                                          '@fourth_axis facet stays open).'),
    'PP-005': ('fixed', 'd3e51a6 Start of a job that is not simultaneous: drop the apos/cpos the last 4x/5x job left '
                        '(SolidCAM keeps them: recorded_cam_001 operation_023, X5_job 0, starts with apos -88.693; a '
                        'job with X5_job true keeps them, its first 4x/5x move sets A).'),
    'PP-055': ('fixed', 'aece7d6 Drill cycles: RFP is the hole top below Z0 too (no DPR 0 branch): every hole gets '
                        'RFP = drill_upper_z - safety and SDIS = safety (SolidCAM sends drill_upper_z = hole top + '
                        'safety), so FDPR counts from the hole top on both sides of Z0.'),
    'PP-063': ('fixed', '2e7cc30 CYCLE832: face and thread milling by feed type; no allowance stops the post '
                        '(@usr_allowance_reset marks a job that sent no allowance).'),
}

# Test files that came with the fixing commits (git show <commit> --stat).
FIX_TESTS = {
    'PP-001': ('tests/test_post_homing_reposition.py',),
    'PP-002': ('tests/test_rotary_modulo_range.py',),
    'PP-003': ('tests/test_side_plane_guard.py',),
    'PP-007': ('tests/test_move_4x_axial_x.py',),
    'PP-013': ('tests/test_job_start_climb.py',),
    'PP-019': ('tests/test_cutter_compensation.py',),
    'PP-020': ('tests/test_cutter_compensation.py',),
    'PP-021': ('tests/test_job_plane_restore.py',),
    'PP-028': ('tests/test_tapping_direction.py',),
    'PP-049': ('tests/test_inverse_time_feed.py',),
    'PP-012': ('tests/test_toolchange_session.py', 'tests/test_cycle832.py'),
    'PP-054': ('tests/test_session_program.py', 'tests/test_coolant_codes.py'),
    'PP-026': ('tests/test_cycles_spindle.py',),
    'PP-022': ('tests/test_arc_compensation_plane.py',),
    'PP-037': ('tests/test_rotary.py',),
    'PP-040': ('tests/test_session_program.py',),
    'PP-041': ('tests/test_session_program.py',),
    'PP-042': ('tests/test_session_program.py',),
    'PP-033': ('tests/test_unsupported_features.py',),
    'PP-034': ('tests/test_unsupported_features.py',),
    'PP-035': ('tests/test_unsupported_features.py',),
    'PP-038': ('tests/test_unsupported_features.py',),
    'PP-043': ('tests/test_rotary.py',),
    'PP-044': ('tests/test_unsupported_features.py',),
    'PP-059': ('tests/test_motion_rapids.py',),
    'PP-046': ('tests/test_rotary.py',),
    'PP-060': ('tests/test_rotary_direction_guard.py',),
    'PP-061': ('tests/test_rotary_modulo_range.py',),
    'PP-062': ('tests/test_cutter_compensation.py',),
    'PP-045': ('tests/test_unsupported_features.py',),
    'PP-047': ('tests/test_contracts.py',),
    'DESIGN-002': ('tests/test_post_homing_reposition.py',),
    'DESIGN-003': ('tests/test_indexing_link.py', 'tests/test_safety_options.py'),
    'PP-005': ('tests/test_indexing_link.py',),
    'PP-055': ('tests/test_cycles_spindle.py',),
    'PP-063': ('tests/test_recorded_replays.py', 'tests/test_cycle832.py'),
}

# Engine scope and GPPL engine handling of the ENGINE entries.
ENGINE_SCOPE = {
    'ENGINE-002': ((('*', ('legacy',)),), 'Fixed in the NC stream: engine.nc_lines()/nc_text() join one block per '
                   'skipline=false assignment (policy skipline=join_next_nb). engine.output, the fragment list '
                   'most tests read, never joins.'),
    'ENGINE-006': ((('*', ('legacy',)),), 'Fixed: 07 is the integer 7.'),
    'ENGINE-007': ((('*', ('legacy',)),), "Fixed: right() and tostr(v:'fmt') are built in; right() of a count above "
                   'the string length is ENGINE-021.'),
    'ENGINE-011': ((('*', ('legacy',)),), 'Fixed: its own expression parser rejects the Python-only syntax.'),
    'ENGINE-012': ((('redeclare', ('legacy',)),), 'Facet redeclare fixed (locals live in call frames); dynamic '
                   'scope is the default (policy local_scoping=lexical is the alternative).'),
    'ENGINE-014': ((('*', ('legacy',)),), 'Fixed: declarations are parsed and validated at load.'),
    'ENGINE-015': ((('*', ('legacy',)),), 'Fixed: output and expressions share one literal model.'),
    'ENGINE-021': ((('*', ('gppl',)),), 'GPPL engine only (pp_tests/gppl/builtins.py f_right); the legacy engine has '
                   'no right() (ENGINE-007) and LegacyCompatEngine clamps.'),
}
GPPL_NOTES = {
    'ENGINE-001': 'Same default rule (policy change_on_equal_assign=keep; alternatives clear, clear_user, set).',
    'ENGINE-003': 'Policy typed_default_formats=on implements it (default off).',
    'ENGINE-004': 'Same default (policy quote_escape=double; alternative none).',
    'ENGINE-005': 'Policy declared_flag=false implements it (default none).',
    'ENGINE-008': 'Policy print_stmt=console implements it (default error).',
    'ENGINE-009': 'input and abort are separate statements: policy input_stmt=scripted answers the prompt and abort '
                  'raises PostAbort; the default input_stmt=abort still stops at input. The POST ERROR stops print '
                  'instead, and tests/program_session.post_error_policies (print_stmt=console) runs them up to their '
                  'abort.',
    'ENGINE-010': 'Policy tonum=atof implements it (default strict).',
    'ENGINE-013': 'Policy integer_assign=truncate or round_half_away implements it (default keep).',
    'ENGINE-016': 'Not engine code: pp_tests/trace.py is shared by both engines.',
    'ENGINE-017': 'Not engine code: pp_tests/trace.py is shared by both engines.',
    'ENGINE-018': 'Policies format_grammar=extended and trace_stmt=ignore implement it (defaults legacy and error).',
    'ENGINE-019': 'Policy load_errors=raise implements it (default lazy).',
    'ENGINE-020': 'Same default behaviour.',
}


_ENTRIES = [
    # ------------------------------------------------------------------ PP
    _d('PP-001', 'PP-inserted G75 Y1=0 X1=0 homing is not followed by X/Y re-programming; the next move '
       'starts from the machine reference point', 'high',
       'Default config (every sHomestr* homes Z then XY). Mid-job rotation rapid (@usr_rapid) and job-start/'
       'tmatrix index (@usr_4x_index) whenever the CAM does not flag X or Y as changed (common: A turns about X, '
       'Y0 on the rotary centreline). Assumes SolidCAM flags only changed coordinates (shit2 trace: line_5x '
       'flagged with zpos/feed only).',
       'confirmed',
       'SolidCAM trace or MPF of a non-link rotary rapid with unchanged X and of an index with unchanged Y '
       '(or a Vericut run); a trace showing whether a PP-set change(xpos)=true survives into an event whose CAM X '
       'is unchanged (the harness resets CAM flags per event, which rejects that sticky-flag fix).',
       ['TSR-04', 'pp-weird-hunter-01', 'pp3-engine-change-flags', 'pp3-diagonal-plunge-after-homing(missed)'], 'D'),
    _d('PP-002', 'Directed A positions outside the modulo range 0 <= A < 360 (A=ACP(360), ACN(-360), ACP(400))',
       'low-medium',
       'Default iR1posControl=1 when apos/angle sums leave the range (4x simultaneous jobs, tmatrix -360, '
       'CoordSys/transform sums of 390, 400, 720). Facet rounding (UNVERIFIED): every value that posts exactly '
       '360 (tiny negatives such as -0.0004/-1e-9 and exact whole-turn sums); it depends on GPPL round/compare '
       'semantics of the 7.3 format and on whether 360 is an inclusive bound. Facet negative-mode: non-default '
       'iR1posControl=2, and iR1posControl=0 for negative CAM angles (A=ACN(-90)), emit negative directed '
       'positions.',
       'confirmed',
       'Whole turns: Siemens 828D modulo-axis rule (program range 0..<360, alarm 16830) or one controller dry '
       'run of A=ACP(360). Rounding facet (uncertain): GPPL statement on round-vs-truncate for the 7.3 format '
       'and on float compare.',
       ['TSR-11', 'efc-07', 'history-rotary-07', 'pp-region-4-cycles-rotary-05', 'pp-region-4-cycles-rotary-06',
        'pp-weird-hunter-03'], 'B'),
    _d('PP-003', 'G18 (ZX) arc validation/rotation is the mirror of the G18 convention: the post aborts or the '
       'control sweeps 360-arc_size', 'medium',
       'Default iArcmode=2 whenever SolidCAM emits @arc in ZX (VMID ArcDirectionBy="0", '
       'SupportGrt180degArcs="0"). Outcome depends on the UNVERIFIED arc_direction convention in ZX: loud abort '
       '(standard convention, medium) or silent reversed arc (front-view convention, high).',
       'uncertain',
       'One real @arc trace in the ZX plane (start, center_rel, arc_size, arc_direction, CAD end point) plus '
       'the meaning of the VMID ArcDirectionBy setting, or a Vericut run of a posted ZX arc.',
       ['pp3-zx-orientation', 'history-misc-04', 'pp-weird-hunter-02', 'pp3-test-arcs-pins-wrong-conventions'], 'D'),
    _d('PP-004', 'ACP/ACN direction selection ignores iR1dir; with iR1dir=+1 short moves become near full turns',
       'low',
       'Non-default iR1dir=+1 (documented option) without changing the VMID/Vericut A direction; default '
       'iR1dir=-1 is correct.',
       'confirmed',
       'Machine check of which way +A turns; decides whether iR1dir=+1 is ever a valid configuration.',
       ['history-rotary-10', 'pp-region-4-cycles-rotary-04'], 'B'),
    _d('PP-005', "A tmatrix index adds the previous simultaneous job's apos (stale apos carry-over)", 'medium',
       'Default config, indexed job after a 4x/5x simultaneous job that ended with apos != 0, only if SolidCAM '
       'carries apos over between jobs (UNVERIFIED); a later tool change does not repair it.',
       'uncertain',
       "SolidCAM trace of a 4x simultaneous job followed by an indexed job: apos in the second job's @tmatrix "
       'and @start_of_job parameter dump.',
       ['TSR-14', 'history-rotary-08', 'pp-region-4-cycles-rotary(missed-3)'], 'C'),
    _d('PP-006', "zpos_f becomes '5.4' after the first rapid / tool-change rapid: Z has 4 decimals, X/Y 5", 'low',
       "Default config: every program after the first rapid (@usr_rapid L1256/L1269); later tool changes do not "
       "restore '8.5' (@usr_ct_before_notfirsttool L724 re-applies '5.4' only when bVertical/bFirstVert is set, "
       "and bVertical needs nR2pos != 0, which is always 0 on this 4x-A machine). The legacy motion_engine sets "
       "zpos_f=8.5 and hides it.",
       'confirmed',
       'Settled as real output by tests/fixtures/shit2_contiguous_link.json (4-decimal Z); owner decides whether '
       '0.0001 mm is acceptable against VMID MovementPrecision=5.',
       ['history-rotary-09', 'pp3-zpos-precision', 'pp-weird-hunter-13'], 'D'),
    _d('PP-007', '@move_4x replaces any changed X with X0', 'medium',
       'Only if SolidCAM emits @move_4x on this machine (legacy 4X/wrap operations); UNVERIFIED.',
       'uncertain',
       'SolidCAM debug trace of one wrap/4x rotary operation showing that @move_4x fires and that xpos is the '
       'axial X.',
       ['pp-region-4-cycles-rotary-01', 'pp-weird-hunter-07'], 'B'),
    _d('PP-008', 'Through-tool coolant 30 bar selects M07, the mist code (table 77/76/75/07/71..74)', 'low',
       'Non-default CAM coolant: through_ival_coolant=1 with through_coolant_val=30; executable only with the '
       'leading-zero workaround (ENGINE-006).',
       'uncertain',
       "The machine builder's M-code list for through-spindle coolant pressures (is M70 the 30 bar code?).",
       ['history-misc-14', 'tc-08', 'pp-weird-hunter-09', 'efc-14'], 'A'),
    _d('PP-009', "@usr_coolant overwrites the option iCoolantM5ON, so an unlisted pressure inherits the previous "
       "job's code instead of the default 77", 'low-medium',
       'Non-default: two jobs with through-tool coolant where the later pressure is not in the table.',
       'confirmed',
       'None needed for the behaviour (deterministic); owner decides the intended code for unlisted pressures.',
       ['pp-weird-hunter-09'], 'A'),
    _d('PP-010', "bCoolofftc/bSpinofftc ('between tool changes') are dead; tool-change M9/M5 follow the "
       'end-of-program flags bCooloffend/bSpinoffend', 'low',
       'Non-default option values (defaults are all true and safe); with bSpinoffend=false the post-M06 ramp '
       'dwell also disappears.',
       'confirmed',
       'None needed (copy-paste visible in @usr_ct_before_notfirsttool L692/L712).',
       ['tc-05', 'pp-weird-hunter-04', 'pp-weird-hunter-18'], 'A'),
    _d('PP-011', 'Spindle M3/M4 is emitted one block before its S word', 'low',
       'With bCoolspinaftertc=true, M3 joins the MSG block and S follows, under any skipline semantics. On the '
       'default tool change, @usr_ct_after sets skipline=false before @start_tool, evidently to join S to the M3 '
       'block; PP-011 holds there only if skipline does not join (ENGINE-002). Exposure: single-block prove-out '
       '(the spindle starts at the previous S).',
       'confirmed',
       'One posted default tool change: is S on the M3 block? (Siemens rule: S must be programmed in or before '
       'the M3/M4 block.)',
       ['pp-weird-hunter-05', 'history-misc-17', 'pp-region-4-cycles-rotary-22', 'efc-05'], 'E'),
    _d('PP-012', 'Haas G187 HSM codes are emitted for the VMID job parameters iG187_P/nG187_E (828D needs CYCLE832)',
       'low-medium',
       'Non-default VMID job parameters iG187_P != 0 or nG187_E != 0 (fail-safe: unknown G function alarm).',
       'confirmed',
       'Siemens 828D G-function list (G187 undefined; repository Vericut control has no G187).',
       ['tc-07', 'efc-02', 'pp-weird-hunter-17'], 'A'),
    _d('PP-013', 'First rapid of a same-tool job traverses XY before climbing to a higher Z', 'medium',
       'Default config when the previous same-tool job ends lower than the new job\'s first rapid Z (different '
       'clearance levels).',
       'confirmed',
       'Trace of two same-tool operations with different clearance levels (how often it occurs).',
       ['tc-01', 'pp3-first-rapid-climb'], 'D'),
    _d('PP-014', "Same-tool work-offset change traverses XY in the new offset at the previous job's machine Z",
       'medium',
       'Non-default iWorkOffset_Method=1 (or any path that changes iWorkoffset between same-tool jobs).',
       'confirmed',
       'Trace of two same-tool jobs on different CoordSys with iWorkOffset_Method=1.',
       ['critic-08'], 'C'),
    _d('PP-015', 'First-job deferred index with i4xIndexClearanceMode 1/2 retracts to the uninitialised Z0 '
       'before rotating A', 'medium',
       'Non-default i4xIndexClearanceMode=1 or 2 (default 0 homes Z); also a first-job @fourth_axis in '
       'clearance mode 1/2 (history-indexing-link-06); collision-class when used.',
       'confirmed',
       "SolidCAM trace of the first job in mode 1 (trace '@usr_4x_index':5).",
       ['history-indexing-link-06', 'tc-02'], 'C'),
    _d('PP-016', 'i4xIndexMode=1: the next job at the same index position is machined in G54', 'low-medium',
       'Non-default i4xIndexMode=1 (start_of_job comment says multiple MAC offsets are not used with 4x). '
       "Assumes SolidCAM reports the same CoordSys position in 'position' for both operations "
       '(pp3-fourth-axis-position).',
       'confirmed',
       "SolidCAM run with i4xIndexMode=1 and two consecutive operations on CoordSys position 2: what SolidCAM "
       "puts in 'position'.",
       ['history-indexing-link-07', 'pp3-fourth-axis-position'], 'C'),
    _d('PP-017', 'i4xIndexMode=1 accumulates position-1 over successive @fourth_axis events (54->55->57->60)',
       'medium',
       'Non-default i4xIndexMode=1 with several @fourth_axis index events. Assumes SolidCAM reports the '
       "CoordSys position in 'position' (pp3-fourth-axis-position).",
       'confirmed',
       'None needed (deterministic); intended mapping is one offset per position.',
       ['pp-region-4-cycles-rotary-10'], 'C'),
    _d('PP-018', 'Straight-retract (CAM-link) check ignores cpos, the rotary input of @line_4x/@move_4x',
       'low',
       'Only if SolidCAM 4x feed links carry the rotation in cpos with X5_job true (UNVERIFIED).',
       'uncertain',
       "SolidCAM debug trace of a 4-axis simultaneous operation (trace '@line_4x':5 / '@move_4x':5) showing "
       'X5_job and whether feed_link line_4x events combine Z and cpos changes.',
       ['history-indexing-link-08'], 'C'),
    _d('PP-019', 'A compensation change before a rapid is never written: G40/G41 deferred, G40 lost across a '
       'tool change', 'medium-high',
       'Default config if SolidCAM emits @compensation immediately before a rapid (e.g. lead-out None); the '
       'tool-change facet also needs no line/arc between the COMP_OFF rapid and end_of_job. Event order '
       'UNVERIFIED.',
       'uncertain',
       'SolidCAM trace of a compensated profile with lead-out None, then a Vericut/828D run of the result.',
       ['pp3-trc-change-before-rapid-lost'], 'D'),
    _d('PP-020', 'G41/G42/G40 are written inside G2/G3 blocks (Sinumerik alarms 10753/10754)', 'medium',
       'Default config when @compensation immediately precedes an @arc (arc lead-in/lead-out, 2aa6df0 removed '
       'the lookahead); event order UNVERIFIED.',
       'uncertain',
       'Trace of a profile with an arc lead-in or lead-out showing @compensation directly before @arc.',
       ['pp3-trc-in-arc', 'pp-weird-hunter-12'], 'D'),
    _d('PP-021', 'G18/G19 set by an arc stays active into the next same-tool job: G41 and drill cycles run in '
       'the wrong plane', 'medium',
       'Default config: a ZX/YZ arc followed by a same-tool job (only the tool-change path re-emits the plane). '
       'UNVERIFIED: assumes SolidCAM does not deliver @machine_plane at every job start.',
       'uncertain',
       'Trace of a ZX/YZ arc job followed by a same-tool XY profile or drill job.',
       ['pp3-plane-persistence'], 'D'),
    _d('PP-022', 'iArcmode 1/3/4 emit Fanuc arc words (absolute centre as plain I/J, R instead of CR=)', 'low',
       'Non-default iArcmode 1, 3 or 4 (default 2 is correct); silent hazard only for full circles in mode 1/3. '
       'The full-circle facet also needs SolidCAM to send 360-degree arcs although the VMID has '
       'SupportGrt180degArcs="0" (UNVERIFIED).',
       'confirmed',
       'Siemens 828D programming manual (I=AC() for absolute centres, CR= for the radius).',
       ['pp3-arc-mode-syntax', 'efc-12', 'history-misc-13', 'TSR-18'], 'D'),
    _d('PP-023', 'Feed-emulated rapids write G1 rotary/XY blocks without the rapid feed (stale cutting feed or '
       '"feedrate not programmed")', 'low',
       'Non-default bSyncdrapid=false (feed-emulated rapids). The tool-change positioning G1 block (A=DC(0)) '
       'and the first XY block of a split first move have no F under both flag policies; the first-job split Z '
       'block without F depends on ENGINE-001 (it prints F650 under the persisting policy). The rotary G1 '
       'block after a post-inserted homing has no F either.',
       'confirmed',
       'None needed for the behaviour; owner decides the intended F on every emulated block.',
       ['pp3-emulated-rapid-no-feed'], 'D'),
    _d('PP-024', 'M00 between same-tool jobs switches coolant off and never restores it; spindle restart has no '
       'ramp dwell', 'medium',
       'VMID job parameter bStopM00=true on a same-tool job boundary (default false). Facet ramp-dwell: low; '
       "the expected dwell is the PP's own spindle_accel policy, not machine physics.",
       'confirmed',
       'Coolant: none needed. Dwell: MD35500 / spindle acceleration on the target 828D.',
       ['tc-03', 'pp3-m00-sametool-coolant'], 'A'),
    _d('PP-025', "Coolant is evaluated only at tool changes: a same-tool job's coolant request is ignored",
       'low-medium',
       'Default config when consecutive same-tool jobs request different coolant channels.',
       'uncertain',
       'Trace of two same-tool jobs with different coolant settings (does SolidCAM expect the post to switch?).',
       ['tc-04'], 'A'),
    _d('PP-026', 'Spindle ramp dwell divides by the literal 500 instead of spindle_accel', 'low',
       'Latent: spindle_accel is an @init_post constant (500 rpm/s), not a user option; the dwell differs '
       'from the documented policy only if that constant is edited (tc-09 correction). From 3fde1a5 until '
       'fb66cad removed it, the dwell existed only with the option bSpinDwell true (default false).',
       'confirmed',
       'None needed for the formula; MD35500 on the target 828D for the intended ramp time.',
       ['tc-09', 'history-misc-17'], 'E'),
    _d('PP-027', 'The second tool change skips the full modal reset because the first-tool path leaves '
       'bSafetyprep=true', 'low',
       'Default config, second and later tool changes.',
       'confirmed',
       'None needed (state flow visible in @usr_ct_before_firsttool L754 and @usr_tc_init_gmstates).',
       ['tc-10', 'TSR-02'], 'A'),
    _d('PP-028', 'Left-hand tap (CCW tool) gets a positive CYCLE84 pitch, i.e. right-hand tapping', 'medium',
       'Default config, G84 job with a counter-clockwise (left-hand) tap. SDAC 3 (spindle M3 after the cycle) '
       'is also wrong for a left-hand tap (pp-region-4-cycles-rotary-08 correction); the canonical test asserts '
       'the PIT sign only.',
       'confirmed',
       'Siemens CYCLE84 (PIT sign selects the direction; repository Vericut control: PIT<0 -> CCW).',
       ['history-misc-07', 'pp-region-4-cycles-rotary-08'], 'E'),
    _d('PP-029', 'CYCLE86 SDIR is hard-coded to 3 (M3) even for CCW boring tools', 'low',
       'Default config, G86 job with a counter-clockwise tool.',
       'confirmed',
       'Siemens CYCLE86 SDIR parameter definition.',
       ['critic-09'], 'E'),
    _d('PP-030', 'First drill hole may not trigger the modal cycle (empty block after MCALL)', 'low',
       'Default drilling flow; depends on whether SolidCAM positions to the first hole before @drill_point '
       '(UNVERIFIED; the cycles were proven on the machine in bea8c62).',
       'uncertain',
       'SolidCAM drilling trace (@drill, @drill_point sequence) or the posted MPF of a 2-hole job run in '
       'Vericut.',
       ['TSR-15', 'pp-region-4-cycles-rotary-15'], 'E'),
    _d('PP-031', "Unsupported drill_type falls through to a stale 'MCALL CYCLE<gcode>' without arguments", 'low',
       'Only for drill types the VMID does not offer (VMID offers parameterised cycles only).',
       'confirmed',
       'None needed; owner decides abort vs explicit rejection.',
       ['pp-region-4-cycles-rotary-20'], 'E'),
    _d('PP-032', 'home_number with iWorkOffset_Method=1 emits any operator number as the work offset (G1, G500, '
       'G58, ...)', 'medium',
       'Non-default VMID machine parameter iWorkOffset_Method=1 plus a wrong operator entry.',
       'confirmed',
       'Siemens settable offsets list (G54..G57, G505..G599); none needed for the behaviour.',
       ['R1-01'], 'C'),
    _d('PP-033', 'Multiple-fixture loop emits G58/G59 for the 5th/6th fixture (axial offsets, not settable '
       'G505/G506)', 'medium',
       'Non-default VMID part parameter iNumber_of_Fixtures >= 5; copies 5/6 rerun in G57 or alarm.',
       'confirmed',
       "Siemens PG Fundamentals 'Axial zero offset G58/G59' or a Vericut/828D run of a bare G58.",
       ['R1-02'], 'C'),
    _d('PP-034', 'Multiple fixtures plus 4x indexing: fixture copies 2..N run at the wrong A angle and fall back '
       'to G54', 'high',
       'Non-default iNumber_of_Fixtures > 1 together with a tmatrix/fourth_axis index (crash risk).',
       'confirmed',
       'Vericut run of an expanded multi-fixture program with an index between tools or jobs.',
       ['critic-01', 'pp-region-4-cycles-rotary-26'], 'C'),
    _d('PP-035', 'End-of-file tempfile cleanup deletes TEMPFILE1..iTcnumber although numbering starts at 2001',
       'low',
       'Non-default iNumber_of_Fixtures > 1.',
       'confirmed',
       'What SolidCAM does with !!delete file!! for files that do not exist.',
       ['R1-09'], 'C'),
    _d('PP-036', 'bLimit_3axis still emits A=DC(...) at the first rapid after a tool change', 'medium',
       'Non-default VMID machine parameter bLimit_3axis=1 (shipped 0).',
       'confirmed',
       'None needed (bR1forceOutput overrides the 3-axis clear, ab853be/ad2537a).',
       ['pp-region-4-cycles-rotary-12'], 'B'),
    _d('PP-037', "iR1posControl=3 ('shortest distance') negates the target angle", 'low',
       'Non-default iR1posControl=3.',
       'confirmed',
       'None needed; a static guard that the shipped option is 1 is the practical protection.',
       ['pp-region-4-cycles-rotary-11'], 'B'),
    _d('PP-038', 'i4xIndexMode=2 (trig macro) emits Haas macro code and aborts on unchanged angles', 'low',
       'Non-default i4xIndexMode=2.',
       'confirmed',
       'None needed (Fanuc/Haas-only output; regression from bff5ed0 for the abort).',
       ['pp-region-4-cycles-rotary-16', 'history-misc-16', 'R1-06'], 'C'),
    _d('PP-039', 'Index clearance warning is written into the NC file as a bare text block (no comment prefix)',
       'low',
       'Non-default i4xIndexClearanceMode=1 with tool_z_level below tool_start_plane; the 828D raises a syntax '
       'alarm on that block (safe stop). The preceding Print needs the ENGINE-008 workaround to execute.',
       'confirmed',
       "None needed for the behaviour ({nl,'WARNING!! ...'} at @usr_4x_index L2427/L2457).",
       ['pp-region-4-cycles-rotary-18', 'efc-14'], 'C'),
    _d('PP-040', "Homing parser merges lines after ';' when the optional prep string is omitted", 'low',
       'Non-default user-edited homing string without the prep colon in a multi-line definition.',
       'confirmed',
       'None needed (string parsing in @usr_prep_home_axis L2108-2113).',
       ['pp-region-4-cycles-rotary-14'], 'A'),
    _d('PP-041', "G53 homing with iWorkOffsetmode=2 prints cWo+0, i.e. 'G0 Z0' in work coordinates", 'low',
       'Non-default homing mode with G53 and iWorkOffsetmode=2.',
       'confirmed',
       'None needed (@usr_home_axis L2159-2161).',
       ['pp-region-4-cycles-rotary-17'], 'A'),
    _d('PP-042', 'Homing mode 7 hard-codes G54 instead of the active work offset', 'low',
       'Non-default homing definition using mode 7.',
       'confirmed',
       'None needed; owner decides the intended offset for mode 7.',
       ['pp-region-4-cycles-rotary(missed)'], 'A'),
    _d('PP-043', '@home_data overwrites the CAM input shift_y (its output is commented out)', 'very-low',
       'Default config (VMID HomeDataAtStart="1"); no NC output depends on it today.',
       'confirmed',
       'None needed (@home_data L2646-2648).',
       ['pp-region-4-cycles-rotary-23'], 'B'),
    _d('PP-044', "@call_proc emits Fanuc syntax (M98 H, literal 'cR1'; G20 on its tool-change path) and indexes "
       'A without being an index boundary', 'low',
       'Subroutines disabled in the VMID (SubroutinesExist/LoopExist off); reachable only if enabled.',
       'confirmed',
       'None needed; VMID subroutine setting decides reachability.',
       ['history-indexing-link-11', 'history-rotary-14', 'pp-region-4-cycles-rotary-19'], 'C'),
    _d('PP-045', "@change_ref_point says 'Not Supported' but writes Fanuc 'G91 G10 L2 P.. X Y Z'", 'low',
       'Only if SolidCAM emits @change_ref_point (reference point change inside a job).',
       'confirmed',
       'None needed; owner decides abort vs Sinumerik equivalent.',
       ['pp3-change-ref-point-g10', 'TSR-18'], 'D'),
    _d('PP-046', 'Exact float compare on A triggers a full G75 Z+XY homing for sub-resolution angle changes',
       'low',
       'Default config when consecutive A targets differ below the 0.001 output resolution; depends on GPPL '
       'numeric compare semantics (UNVERIFIED).',
       'uncertain',
       'GPPL manual statement or a trace with sub-resolution apos differences.',
       ['pp-weird-hunter-08'], 'B'),
    _d('PP-047', '@rotate/@mirror are empty while the VMID delegates transformations to the post '
       '(SoftwareTransform="0")', 'medium',
       'Only if a SolidCAM job uses rotate/mirror transformations with this VMID; event delivery UNVERIFIED.',
       'uncertain',
       'SolidCAM run of a mirrored/rotated job with this VMID: are @rotate/@mirror called and is the toolpath '
       'already transformed?',
       ['critic-02'], 'F'),
    _d('PP-048', 'SolidCAM MCO, dwell, spindle-stop and rotate-to-plane events have no procedure (an MCO Halt '
       'produces no M0)', 'medium',
       'Only if those events are used. SolidCAM skips an event the post does not define: the reference trace of '
       '2026-10-27 has (0)@vmid_info (3) and (0)@setup (1), which have no procedure, while defined events print '
       'at depth (1), and posting went on through all 31 operations. Whether SolidCAM delivers the MCO events to '
       'this post is UNVERIFIED. The 4x drill point (@drill4x_pnt) and the other 4x polar/Cartesian, 4x drill and '
       '5x arc events stop the post (@usr_unsupported_motion_event).',
       'uncertain',
       'SolidCAM run with an MCO Halt/optional stop and a dwell: is anything posted?',
       ['critic-03'], 'F'),
    _d('PP-049', 'i4xFeedMode=1 (inverse time) is never implemented: simultaneous rotary moves use mm/min F '
       'under G94', 'medium',
       'Default i4xFeedMode=1 option is dead; reachable in every 4x simultaneous feed move with an A word.',
       'uncertain',
       'Controller behaviour of a G94 block with an A word (F as deg/min on a rotary-only block) and the '
       "owner's intended feed mode.",
       ['critic-04', 'pp-weird-hunter-18', 'pp-region-4-cycles-rotary-26'], 'D'),
    _d('PP-050', 'vericut/GcodeSim.ini maps MAC 1-3 and 5-10 to G54 but omits MAC 4', 'medium',
       'Default machine definition; Vericut and the NC disagree for CoordSys 4.',
       'confirmed',
       'None needed (c85f5f7 intent: all MACs map to G54).',
       ['critic-06'], 'F'),
    _d('PP-051', 'Vericut K word format left at 5.3 while I/J were widened to 8.5 (f88de47)', 'low',
       'None while the post writes arcs as end point and AR= (no centre word); YZ arcs printed K with 5 decimals '
       'before.',
       'uncertain',
       'Vericut run of a ZX arc with a K word below 0.001 resolution.',
       ['critic-07'], 'F'),
    _d('PP-052', 'VMID job parameters M50/M51 appear in every job dialog but the GPP never reads them', 'low',
       'Default VMID; operator entries are silently ignored.',
       'confirmed',
       "Owner's intent for M50/M51 (air blast / low-pressure through coolant?).",
       ['critic-10'], 'F'),
    _d('PP-053', 'First index of a program in default Z-homing mode has no G75 (sHomestrrot assigned lazily)',
       'low',
       'Default i4xIndexClearanceMode=0, first job indexed before any rapid; safe in practice because '
       'start_program already homed. With bHomebegin false (or sHomestrbegin empty) that index turns A '
       'with no clearance at all.',
       'confirmed',
       'None needed; owner decides whether the index must home explicitly.',
       ['history-indexing-link-13'], 'C'),
    _d('PP-054', "First job under persisting init flags: 'G187 P2' and flood M8 cancelled by seven M9", 'low',
       "Default config but ONLY under the flags='persist' session policy (stock-engine change-flag rule for "
       'initial assignments, ENGINE-001); the clear policy prints neither.',
       'likely-engine-artifact',
       "grep any MPF generated by HEAD for 'G187' and for M8 followed by M9 before the first cut; or a SolidCAM "
       'trace "all":5 of a first job showing change(iCoolantM2) and change(iG187_P_gpp).',
       ['TSR-12', 'TSR-13', 'efc-02', 'efc-03', 'tc-06', 'pp-weird-hunter-06', 'history-misc-15',
        'engine-impl-critic-07', 'history-indexing-link-14'], 'A'),
    _d('PP-055', 'CYCLE83 first peck depth jumps by SDIS when drill_upper_z crosses 0 (FDPR relative to RFP)',
       'low',
       'Default config, G83 holes whose top is near Z0; harmless (shallower first peck below Z0).',
       'confirmed',
       'Siemens CYCLE83 FDPR definition; owner decides fix vs documentation.',
       ['pp-weird-hunter-21(missed)'], 'E'),
    _d('PP-056', 'bStopM00difftool is set and cleared in the same @end_of_job: the skip path is dead and is what '
       'keeps the G75 retract before M06', 'low',
       'VMID job parameter bStopM00=true before a different-tool job; current output is safe by accident.',
       'confirmed',
       'None needed; a pin must protect the retract before M06 against a naive "fix".',
       ['tc-11', 'pp3-difftool-flag-fragile', 'pp-weird-hunter-16'], 'A'),
    _d('PP-057', 'Dormant option/event paths emit Fanuc/Haas-only code (G65/G112/O777 macros, M98/M99, G20, '
       "G43/G49, '#' macros, WHILE[ loop)", 'low',
       'Only with non-default options (i4xIndexMode=2, bUseprognum, iProgendmode) or VMID-disabled events '
       '(subroutines, loops).',
       'confirmed',
       'None needed; static allowlist pins the legacy procedures and VMID guards keep them disabled.',
       ['TSR-18', 'history-misc-16', 'R1-06', 'tc-13', 'tc-17', 'pp-weird-hunter-17', 'pp-region-4-cycles-rotary-19'],
       'F'),
    _d('PP-058', 'Mach3 4x post (6efcad8): the feed re-statement remedy is missing on @line_5x and @arc', 'low',
       'Mach3 post only (uninitialised submodule mach3/4x or MACH3_PP_SOURCE).',
       'uncertain',
       'A recorded Mach3 run of a line_5x/arc feed change, and the post version the submodule would pin.',
       ['history-misc-18'], 'F'),
    _d('PP-059', "A rapid without axis motion appends its modal words to the previous NC line ('G1 Z-1 F200 G0', "
       "'Z35 F300 F650', 'MSG(\"op\")G0')", 'high',
       'Any rapid event whose X/Y/Z/A do not change while a modal word is pending (motion mode after a feed move, '
       'the emulated-rapid F, a work offset): 648 of 4000 generated runs.',
       'confirmed',
       'Sinumerik reads one motion G code and one F per block: a G0 on the cutting line makes the plunge a rapid '
       'or alarms; a trace of SolidCAM sending a rapid to the current position settles how often.',
       ['ralph-iteration-8-empty-rapid'], 'D'),
    _d('PP-060', 'ACP/ACN can turn A the other way round than CAM (a silent flip: 350 degrees instead of -10) in a '
       'cut or a CAM-link rotary rapid', 'high',
       "Any feed move or unhomed rotary rapid whose A word disagrees with CAM's step: dir5a against the angle "
       'step, angles wrapped to +-180, the tool-change unwind (DESIGN-005), frame changes without an index, '
       'rounding straddles. 418 of 6000 generated runs with dir5a following the CAM step.',
       'confirmed',
       'A SolidCAM trace of a 4x/5x job across 180 degrees and of the first move after the third tool change.',
       ['owner-review-2026-10-27-1'], 'B'),
    _d('PP-061', 'False full-turn stop: the tool-change apos = 0 or @fourth_axis makes the next cutting block look '
       'like a 360 degree CAM turn', 'medium',
       'A 4x/5x job ending at a whole turn (e.g. CAM A 720 or 725) followed by a reset of apos by the post and a '
       'first cutting block at the same CAM A.',
       'confirmed',
       'A SolidCAM trace of a multi-turn wrap job followed by a tool change.',
       ['owner-review-2026-10-27-2'], 'B'),
    _d('PP-062', 'Cutter compensation left on runs through the post homing, index, M0/M1, tool change or M30 '
       '(no linear block carries the G40)', 'medium',
       'CAM switches compensation off after the last retract or never (lead-out None, the retract is a rapid); '
       '1128 of 6000 generated runs.',
       'confirmed',
       'A SolidCAM trace of a compensated profile whose compensation off follows the retract.',
       ['owner-review-2026-10-27-3'], 'D'),
    _d('PP-063', 'face_milling and thread jobs: @usr_smoothing takes the CYCLE832 type from wall_offset/floor_offset, '
       'which SolidCAM does not send for them', 'medium',
       'Default config (bCycle832, job parameter iG187_P 0): every face_milling and thread job. Their @start_of_job '
       'has neither wall_offset nor floor_offset (recorded_cam_004 operation_001/002/009/011 face_milling, '
       'recorded_cam_005 operation_025 thread), so a job after one that sent them takes that allowance silently. '
       'One before any job that sent them reads a variable SolidCAM never set: recorded_cam_004 starts with face '
       'milling and its replay stops at event 25; which value SolidCAM gives an unset variable is UNVERIFIED '
       '(presumably 0, finishing).',
       'confirmed',
       'None needed for the inputs (the recordings show which jobs send no allowance); the owner decides the '
       'CYCLE832 type of face and thread milling (a fix is in progress on the refactoring branch).',
       ['recorded-cam-replay-2026-10-28'], 'A'),
    # -------------------------------------------------------------- ENGINE
    _d('ENGINE-001', 'Change-flag rule for equal-value assignment is unverified (engine: only a value change '
       'raises a flag, nothing clears it)', 'medium',
       'Every session test: decides whether init assignments leave flags pending (PP-054) and what a first job '
       'prints.',
       'uncertain',
       "10-line probe GPP in SolidCAM (global integer i; init i=9; start_of_job i=9; if change(i) {nb,'CHANGED'}) "
       'or a trace "all":5 of a first job.',
       ['efc-01', 'pp3-engine-change-flags', 'TSR-17'], 'F'),
    _d('ENGINE-002', 'skipline block joining is not emulated (nb/nl always start a new block)', 'low-medium',
       'GPP sets skipline 21 times (usr_rapid, usr_ct_after, coolant, drill); a mutation that joins the rotary '
       'and XYZ rapid survives.',
       'confirmed',
       'One real trace showing a skipline=false join and whether nl also consumes it (auto-reset semantics).',
       ['engine-impl-critic-03', 'efc-05'], 'F'),
    _d('ENGINE-003', 'numeric_def_f / integer_def_f are ignored: unformatted numbers use 3 decimals instead of '
       "'8.5'", 'low-medium',
       'CYCLE parameters and any number without a <name>_f format (arcs write no centre word since AR=).',
       'confirmed',
       'A posted MPF with an unformatted arc centre (number of decimals).',
       ['engine-impl-critic-05', 'efc-04', 'engine-impl-critic-12'], 'F'),
    _d('ENGINE-004', "The engine's doubled-quote ('') escape renders a stray apostrophe in the CYCLE84 "
       "argument list (',0,''')", 'low-medium',
       'Every G84 job (@drill L1883/L1886); bea8c62 edited the line without touching the quote, so a real PP '
       'defect is unlikely.',
       'likely-engine-artifact',
       'One SolidCAM G84 run (posted CYCLE84 line) or a GPPL manual statement on literal quoting.',
       ['engine-impl-critic-06', 'history-misc-06', 'pp-region-4-cycles-rotary-24', 'pp-weird-hunter-10'], 'E'),
    _d('ENGINE-005', 'Declared globals get no change flag (locals get False); change(<global>) raises KeyError',
       'medium',
       'Sessions from @init_post die at @usr_hsm_mode without blanket flag filling.',
       'confirmed',
       'GPPL manual statement on the initial change flag of declared variables.',
       ['engine-impl-critic-04'], 'F'),
    _d('ENGINE-006', 'Leading-zero integer literal 07 raises (Python parser)', 'low',
       'GPP line 990 (@usr_coolant, through coolant 30 bar).',
       'confirmed',
       'None needed (GPP ships the literal).',
       ['efc-06', 'engine-impl-critic-14', 'tc-16'], 'F'),
    _d('ENGINE-007', "right() and tostr(value:'fmt') built-ins are missing", 'low',
       '@usr_sof_progname, @usr_US_date/@usr_US_time (start_of_file header) and @Multiple_Fixtures.',
       'confirmed',
       'None needed (shipped template code); clamp right() to the string length.',
       ['R1-10', 'efc-06', 'engine-impl-critic-14', 'pp-region-4-cycles-rotary-25'], 'F'),
    _d('ENGINE-008', 'Print statement is unsupported (assumed: message window, generation continues)', 'low',
       '@usr_4x_index index clearance warnings (L2426/L2456) and, since they replaced input, the message of '
       'every POST ERROR stop (print, then abort).',
       'uncertain',
       'GPPL manual or a SolidCAM run showing where Print output goes. A SolidCAM run by the post owner '
       '(2026-10-28) showed that print followed by abort works.',
       ['efc-06', 'pp-region-4-cycles-rotary-25'], 'F'),
    _d('ENGINE-009', 'input is treated as a terminal stop and abort raises the same exception as engine gaps; '
       'deleting abort leaves the suite green', 'medium',
       'The POST ERROR guards (@usr_arc_check, @usr_r1_output, and since the review fixes the ZX arc, '
       'TRC-on-arc and full-turn cutting block stops).',
       'confirmed',
       'GPPL semantics: input prompts and continues, abort terminates (the dummy_var idiom the GPP used '
       'before its POST ERROR stops switched to print).',
       ['engine-impl-critic-01'], 'F'),
    _d('ENGINE-010', "tonum() of a non-numeric string raises (tonum('G5'))", 'low',
       '@home_number and @home_data with operator-entered CoordSys names.',
       'confirmed',
       'GPPL manual statement on tonum() of non-numeric text.',
       ['engine-impl-critic-14', 'pp-region-4-cycles-rotary-25'], 'F'),
    _d('ENGINE-011', 'Python-superset expression semantics are accepted silently (chained comparisons, hex, '
       'string*int, negative left/substr, precedence)', 'low',
       'Latent: no current GPP line depends on it.',
       'confirmed',
       'GPPL manual expression grammar.',
       ['engine-impl-critic-08', 'efc-15'], 'F'),
    _d('ENGINE-012', 'Re-executing a local declaration loses the outer value; flat dict gives dynamic scope',
       'low',
       'Latent; GPPL local scoping itself is unproven.',
       'uncertain',
       'GPPL manual statement on local variable scope.',
       ['engine-impl-critic-09'], 'F'),
    _d('ENGINE-013', 'Integer-typed variables hold fractions (no truncation/rounding on assignment)', 'low',
       '@usr_spindle_output, @home_number, @usr_prep_home_axis integer arithmetic.',
       'uncertain',
       'GPPL manual statement on integer assignment (truncate vs round).',
       ['engine-impl-critic-10'], 'F'),
    _d('ENGINE-014', 'Declaration parser accepts junk names; assignments to undeclared names are accepted',
       'low',
       'Latent; no current GPP typo found.',
       'confirmed',
       'SolidCAM load of a GPP with an undeclared variable (rejected or not).',
       ['engine-impl-critic-11'], 'F'),
    _d('ENGINE-015', 'Rendering details: "" escape differs between _render and expression(), half-even ties, '
       "bool printed as True, '(p)' ignored", 'low',
       'Latent; affects exact-text assertions only.',
       'confirmed',
       'GPPL manual statement on literal escapes and numeric rounding.',
       ['engine-impl-critic-12'], 'F'),
    _d('ENGINE-016', 'trace.py: nested-call ..> lines become NC output; fixed-width indentation is assumed',
       'low',
       'Only when importing new SolidCAM traces as fixtures.',
       'confirmed',
       'A captured trace with nested calls and different indentation.',
       ['engine-impl-critic-13'], 'F'),
    _d('ENGINE-017', 'Trace sanitizer redacts the enum inputs (feed_type, prev_command, ...) that drive the '
       'CAM-link homing bypass', 'low',
       'Only when importing new SolidCAM traces as fixtures.',
       'confirmed',
       'None needed (allowlist in pp_tests/trace.py).',
       ['efc-10'], 'F'),
    _d('ENGINE-018', "Historical-revision constructs are unsupported: active trace statements and numeric "
       "formats '<(>5.3<)>', '(*k)', '+8.5', '(n)'", 'low',
       'Reversion tests against older GPP revisions; newshift_*_f and tostr(...:5.0(n)) in the current GPP.',
       'confirmed',
       'None needed for support; GPPL manual for the exact meaning of the (n) and (*k) modifiers.',
       ['history-rotary-15', 'history-indexing-link-12', 'engine-impl-critic-12'], 'F'),
    _d('ENGINE-019', 'Text outside procedures is silently ignored by the parser', 'low',
       'Latent: a stray statement between procedures would not be executed or reported.',
       'confirmed',
       'GPPL manual: is code outside procedures an error at load?',
       ['TSR-17'], 'F'),
    _d('ENGINE-020', "Identifiers inside '(expr)' output tokens get their change flags cleared", 'low',
       'Latent; no current GPP output depends on it.',
       'uncertain',
       'GPPL manual statement on clear_change_after_gen for expression output tokens.',
       ['efc-15'], 'F'),
    _d('ENGINE-021', "GPPL engine right(s, n) with n > strlen(s) returns a Python slice ('bc' for right('abc', 5)) "
       'instead of the whole string', 'very-low',
       'Latent: no GPP call passes a count above the string length (@usr_sof_progname passes at most strlen - 1, '
       '@usr_US_date right(date, 4)).',
       'confirmed',
       'None needed (right() returns the last n characters; LegacyCompatEngine already clamps).',
       ['integration-review'], 'F'),
    # -------------------------------------------------------------- DESIGN
    _d('DESIGN-001', 'CAM-link trust: a rapid that descends inside a confirmed link keeps the authorization, and '
       'any positive Z step (0.001 mm) authorizes an unhomed rotation', 'low',
       'Default config inside CAM links of 4x/5x jobs.',
       'uncertain',
       'Real SolidCAM 4x/5x link traces: does a descending rapid ever precede a rotary rapid inside one link, '
       'and what retract heights occur?',
       ['history-indexing-link-10', 'pp-weird-hunter-19'], 'C'),
    _d('DESIGN-002', "After G75 homing for a rotation the approach is one diagonal 'X Y Z' G0", 'medium',
       'Default config, first rotary link of a 4x/5x job and every homed rotary rapid; high for low-Z targets '
       'or RTLIOF (non-linear G0).',
       'uncertain',
       'Machine data MD20730 G0_LINEAR_MODE / RTLION vs RTLIOF and the fixture layout; owner policy.',
       ['history-indexing-link-09', 'pp3-diagonal-plunge-after-homing'], 'D'),
    _d('DESIGN-003', 'A deferred tmatrix index runs before the tool change (old tool, spindle and coolant on, '
       'double M1)', 'low',
       'Default config, index between different-tool jobs.',
       'confirmed',
       'Owner policy: index before or after the tool change.',
       ['efc-13', 'tc-12', 'pp-weird-hunter-15'], 'C'),
    _d('DESIGN-004', 'In confirmed CAM links the rotary block always precedes the XYZ block, even when Z rises in '
       'the same event', 'low',
       'Default config; pinned by tests/fixtures/shit2_contiguous_link.json. With bHomeroth false (or '
       'sHomestrroth empty) the same order applies to every A-turn rapid outside a CAM link, where CAM '
       'planned no clearance.',
       'confirmed',
       'Owner policy (rise first vs rotate first within a confirmed link).',
       ['pp3-rising-link-rotary-order'], 'C'),
    _d('DESIGN-005', 'A tool change zeroes CAM apos/bpos/cpos, so A unwinds/rewinds between 5x jobs and the '
       'direction comes from angle_4x_around_x_dir (abort if not cw/ccw)', 'low',
       'Default config, tool change between simultaneous jobs.',
       'uncertain',
       'Trace showing angle_4x_around_x_dir at a tool change; owner policy for the rewind.',
       ['history-rotary-12', 'pp-weird-hunter-14'], 'B'),
    _d('DESIGN-006', 'Single origin: the shipped home_number maps every CoordSys to G54 and newshift/ORGXYZ are '
       'computed but unused', 'low',
       'Default iWorkOffset_Method=0 (c85f5f7 deliberately maps all MACs to G54; pp-weird-hunter-11 refuted).',
       'confirmed',
       'Owner policy: confirm all CoordSys share one origin (G54).',
       ['R1-11', 'pp-weird-hunter-11(refuted)'], 'C'),
    _d('DESIGN-007', 'Non-zero secondary rotation (bpos / x_angle_const_z) is silently ignored apart from the '
       'old vertical-head toggle', 'low',
       'Only for CAM output with a secondary rotation, which a 4-axis machine should not receive.',
       'confirmed',
       'Owner policy: abort on a non-zero secondary rotation or ignore it.',
       ['history-rotary-13', 'pp-region-4-cycles-rotary-26'], 'B'),
]

# Where each entry lives. GPP line numbers refer to Gmill_540v_4x.gpp at f1803b4
# (the GPP is never edited by this suite; the review fixes moved later lines);
# engine entries name pp_tests/*.py (pp_tests/gppl/legacy.py is the original
# engine, formerly pp_tests/engine.py).
LOCATIONS = {
    'PP-001': 'GPP @usr_rapid L1278-1288 (homing + rotation) and L1322-1334 (modal X/Y); @usr_4x_index L2415-2422; '
              '@usr_prep_home_axis/@usr_home_axis L2091-2190 set no change(xpos/ypos)',
    'PP-002': 'GPP @usr_r1pos_calc L2282-2288 (only (-360,0) is adjusted), L2312; @usr_r1_output L2381-2396; '
              "nR1pos_f '7.3' (@init_post L60)",
    'PP-003': 'GPP @usr_arc_math L1494-1498 (G2/G3 from arc_direction) and L1541-1549 (ZX rotation); output '
              '@usr_arc L1585/L1601-1614',
    'PP-004': 'GPP @usr_r1_select_dir L2361-2379, @usr_r1_output L2381-2392; nR1pos = -angle*iR1dir L2273-2277; '
              'option iR1dir L165',
    'PP-005': 'GPP @start_of_job L1110-1115 -> @usr_4x_index L2411 -> @usr_r1pos_calc L2277 '
              '(nR1pos5x = (-apos)*iR1dir); compare @fourth_axis L1797 (apos = 0)',
    'PP-006': "GPP @init_post L59 (zpos_f '8.5'); @usr_rapid L1256/L1269 and @usr_ct_before_notfirsttool L724 "
              "(zpos_f '5.4')",
    'PP-007': 'GPP @move_4x L2489-2500 (L2494-2496: if change(xpos) xpos = 0)',
    'PP-008': "GPP @usr_coolant L989-991 (iCoolantM5ON = 07); option iCoolantM2ON = 7 'Mist Coolant ON' L115",
    'PP-009': 'GPP @usr_coolant L979-1006 (assigns the option variable iCoolantM5ON); option default L121',
    'PP-010': 'GPP @usr_ct_before_notfirsttool L692 (bCooloffend) and L712 (bSpinoffend); options L104-107',
    'PP-011': 'GPP @start_tool L1950-1963, @usr_spindle_mcode_output L1977-1983 (no nb), @usr_spindle_output '
              'L1965-1971; @usr_ct_after skipline before @start_tool',
    'PP-012': 'GPP @usr_HSM_mode L1077-1099 (G187 output L1086/L1094), called from @start_of_job L1173; VMID '
              'ParamJobs iG187_P/nG187_E',
    'PP-013': 'GPP @start_of_job L1149-1158 (same-tool branch: no retract), @usr_rapid L1322-1333 (first move: XY '
              'block before Z)',
    'PP-014': 'GPP @start_of_job L1154-1158 (iPworkoffset ne iWorkoffset -> usr_tc_init_gmstates, rapid_move); '
              '@usr_rapid bTlchg branch L1289-1316 and L1323-1330',
    'PP-015': 'GPP @usr_4x_index L2430/L2437 (Z nPtool_z_level / nPtool_start_plane); assigned only in @end_of_job '
              'L1200-1201; first-job index from @start_of_job L1110-1115',
    'PP-016': 'GPP @home_number L616 (iWorkoffset = 54 every job); @usr_4x_index L2450/L2461/L2469 (position-1 '
              'added only when change(nR1pos)); @fourth_axis L1785-1789',
    'PP-017': 'GPP @usr_4x_index L2450/L2461/L2469 (iWorkoffset = iWorkoffset + (position-1)); @fourth_axis '
              'L1782-1800 increments position',
    'PP-018': "GPP @usr_line L1389 (!change(apos) and !change(bpos), no cpos); @usr_rapid L1224 ('@line_4x'/"
              "'@move_4x' whitelist); @usr_r1pos_calc L2276",
    'PP-019': 'GPP @compensation L1635-1652; @usr_rapid L1286/L1294/L1303/L1323 (no TRC word); '
              '@usr_tc_init_gmstates L896 (iDiametercomp = 40 without output)',
    'PP-020': "GPP @usr_arc L1585 (['G'iDiametercomp' '] in the circular block); @compensation L1635-1652",
    'PP-021': 'GPP @usr_arc_math L1501-1509 (sets the global iMplane); only @usr_tc_init_gmstates L867/L884 calls '
              '@machine_plane',
    'PP-022': 'GPP @usr_arc L1587-1628 (absolute centre L1589/L1603/L1617, R word L1594-1627); option iArcmode L82',
    'PP-023': 'GPP @usr_rapid A block (rotary G1), @usr_rapid_tc_block (tool-change block), @usr_rapid_xy_then_z '
              '(split XY block of a first move); F only from @usr_emulated_rapid_feed',
    'PP-024': 'GPP @usr_StopM00_sametool L1679-1719 (M9, M5, M0, spindle restart without @usr_coolant or dwell); '
              '@start_of_job same-tool branch L1145-1159',
    'PP-025': 'GPP @usr_coolant callers: @usr_ct_after L832/L852 only (@end_of_job call commented out L1203-1205)',
    'PP-026': 'GPP @usr_spindle_output L1969-1972 (G04 F (0.3+(sdiff/500))); spindle_accel = 500 in @init_post',
    'PP-027': 'GPP @usr_ct_safety_block (bSafetyprep = true); @usr_tc_init_gmstates (first-tool '
              'branch never clears it)',
    'PP-028': "GPP @drill G84 branch L1881-1897 (''(FEED/SPIN) always positive, SDAC 3 at L1883/L1886); Vericut "
              'ctl L1933-1960 (PIT<0 -> CCW)',
    'PP-029': "GPP @drill G86 branch L1900-1905 (SDIR ',,,3' hard-coded); compare @start_tool/@m_feed_spin "
              'L1937-1955',
    'PP-030': 'GPP @drill L1826 (rapid_move before MCALL), L1844; @drill_point L1913-1918 (modal [X][Y][Z])',
    'PP-031': 'GPP @drill L1828-1844 (no else branch for unknown drill_type)',
    'PP-032': 'GPP @home_number L628-630 (iWorkOffset_Method=1 branch), @usr_homenumber_output L633-638; VMID '
              'UserDefParams iWorkOffset_Method',
    'PP-033': 'GPP @Multiple_Fixtures L2213-2217 and L2240-2244 ({nb,cWo,((iWorkoffset-1)+i)}); enabled by '
              '@start_of_file L193-196',
    'PP-034': 'GPP @start_of_job L1110-1115 (index before @usr_ct L1146); @usr_ct L657-660/L682-685 -> '
              '@Multiple_Fixtures L2209-2245',
    'PP-035': 'GPP @usr_init_gmstates L340 (iTcnumber = 2001); @Multiple_Fixtures L2252-2261 (delete loop from 1), '
              'called from @end_of_file L561-564',
    'PP-036': 'GPP @usr_r1pos_calc L2338-2345 (bR1forceOutput sets iR1dirMode=3 after the 3-axis clear); @usr_rapid '
              'L1297-1309',
    'PP-037': 'GPP @usr_r1pos_calc L2296-2312 (nR1pdir = -1 multiplies the position); option doc L170',
    'PP-038': 'GPP @usr_4x_index L2476-2486 (mode 2 outside if change(nR1pos)); @usr_trig_macro_call L2551-2556, '
              '@usr_trig_macro_output L2558-2614; @usr_ct_after L820-825',
    'PP-039': "GPP @usr_4x_index L2425-2428 and L2455-2458 ({nl,'WARNING!! ...'} after Print)",
    'PP-040': "GPP @usr_prep_home_axis L2108-2113 (second ':' searched across the whole remainder)",
    'PP-041': 'GPP @usr_home_axis L2159-2161 (iWorkOffsetmode 2: cWo + 0)',
    'PP-042': "GPP @usr_home_axis L2182-2184 (mode 7: 'G90 G54 ' literal)",
    'PP-043': 'GPP @home_data (shift_y overwritten); VMID HomeDataAtStart="1"',
    'PP-044': "GPP @call_proc L2000-2041 (L2015 'G20 ', L2031 @usr_4x_index, L2036 'cR1' literal, L2037 'M98 H')",
    'PP-045': "GPP @change_ref_point L1759-1766 ('G91 G10 L2 P..')",
    'PP-046': "GPP @usr_r1pos_calc ('if nPR1pos ne nR1pos' on the unrounded angle, refactoring branch before "
              "1add48e); @usr_rapid",
    'PP-047': 'GPP @rotate L1770-1773 and @mirror L1776-1779 (empty, refactoring branch before 6ce4055); VMID '
              'SoftwareTransform="0"',
    'PP-048': 'GPP: procedures absent (@halt_program, @machine_opt_stop, @delay/@dwell, @stop_tool, '
              '@rotate_to_plane, MCO events; @drill4x_pnt stops the post); reference: the Mach3 4x template at '
              'ffd296c',
    'PP-049': 'GPP option i4xFeedMode L173 (never read); F output @usr_line L1419-1424, @line_4x L2502-2510, '
              '@line_5x L2535-2543',
    'PP-050': 'vericut/GcodeSim.ini [MAC] (1,2,3,5..10 = 54; MAC 4 missing)',
    'PP-051': 'vericut/sin840d_special.ctl <Word Name="K"> MetricFormat="5.3" (I/J 8.5); GPP @usr_arc L1606/L1620',
    'PP-052': 'Gmill_540v_4x.vmid ParamJobs GppName="M50"/"M51" (never read by the GPP)',
    'PP-053': "GPP @usr_4x_index_rotate (sHomestr = sHomestrrot; '' = no homing in @usr_prep_home_axis); sHomestrrot "
              'assigned only in @usr_rapid and @usr_head_home_select (first rapid / tool change)',
    'PP-054': 'GPP @usr_init_gmstates L341-350 (coolant channels OFF, iG187_P_gpp = 2); @usr_coolant_output '
              'L1038-1075; @usr_HSM_mode L1077-1099; pp_tests/gppl/legacy.py assignment flag rule',
    'PP-055': 'GPP @drill G83 branch L1846-1907 (FDPR relative to RFP, RFP shifted by SDIS when drill_upper_z <= 0)',
    'PP-056': 'GPP @usr_StopM00_difftool L1754 (flag set), @end_of_job L1193 (cleared), '
              '@usr_ct_before_notfirsttool L691 (read)',
    'PP-057': 'GPP @call_proc L2015/L2036-2037, @proc/@end_proc L2043-2061, @end_loop L2080-2087, @start_of_job '
              'L1163-1168, @usr_trig_macro_* L2551-2614, @usr_4x_index L2483',
    'PP-058': 'mach3/4x/Mach3_4X_Y.gpp at 6efcad8 (@line_5x and @arc lack the feed re-statement of @line)',
    'PP-059': "GPP @usr_rapid_xyz (refactoring branch before fb78a2b): 'skipline = false' when no axis moved",
    'PP-060': 'GPP @usr_r1pos_calc / @usr_r1_select_dir / @usr_r1_output (refactoring branch before 1add48e): the '
              'word followed dir5a or angle_4x_around_x_dir whatever the two positions were',
    'PP-061': "GPP @usr_line (refactoring branch before 1add48e): 'abs(nR1posstep) >= 359.9995' with nPR1postemp "
              'taken after the post zeroed apos',
    'PP-062': 'GPP @end_of_job and @usr_prep_home_axis (refactoring branch before 01dd68f): no G40 unless a G0/G1 '
              'block carried the CAM compensation change',
    'PP-063': 'GPP @usr_smoothing L1251-1256 (nAllow = wall_offset, or floor_offset on profile_3D, when bCycle832, '
              'iG187_P 0, not X5_job and not a drill job), called by @start_of_job L1412',
    'ENGINE-001': 'pp_tests/gppl/legacy.py Engine.call assignment branch (a flag is raised only when the value changes '
                  'and never cleared)',
    'ENGINE-002': "pp_tests/gppl/legacy.py Engine._render (nb/nl always start a new block; 'skipline' is a plain variable)",
    'ENGINE-003': "pp_tests/gppl/legacy.py Engine._render numeric descriptor fallback (precision 3 when no <name>_f)",
    'ENGINE-004': "pp_tests/gppl/legacy.py uncomment()/_render literal regex '(?:[^']|'')*'; GPP @drill L1883/L1886",
    'ENGINE-005': 'pp_tests/gppl/legacy.py Engine.call declaration branch (global: state only, no change flag)',
    'ENGINE-006': 'pp_tests/gppl/legacy.py Engine.expression (ast.parse rejects 07); GPP @usr_coolant L990',
    'ENGINE-007': 'pp_tests/gppl/legacy.py Engine._node function table (no right/tostr); GPP L251/L300/L325/L2221',
    'ENGINE-008': 'pp_tests/gppl/legacy.py Engine.call (Print is an unsupported statement); GPP @usr_4x_index L2426/L2456',
    'ENGINE-009': "pp_tests/gppl/legacy.py Engine.call ('abort' and 'input' raise UnsupportedGPPL); GPP @usr_arc_check "
                  'L1460-1462, @usr_r1_output L2399-2401',
    'ENGINE-010': 'pp_tests/gppl/legacy.py Engine._node tonum (float() of the text); GPP @home_number L620-624, '
                  '@home_data L2620',
    'ENGINE-011': 'pp_tests/gppl/legacy.py Engine.expression/_node (Python AST subset)',
    'ENGINE-012': 'pp_tests/gppl/legacy.py Engine.call local declaration branch (locals_saved overwritten; one flat dict)',
    'ENGINE-013': 'pp_tests/gppl/legacy.py Engine.call declarations (types parsed but discarded)',
    'ENGINE-014': 'pp_tests/gppl/legacy.py Engine.call declaration regex and assignment branch',
    'ENGINE-015': 'pp_tests/gppl/legacy.py Engine._render (token regex, numeric rounding, bool rendering)',
    'ENGINE-016': 'pp_tests/trace.py parse_trace (fixed-width ..> continuation and nested-call handling)',
    'ENGINE-017': 'pp_tests/trace.py sanitize (identifier allowlist)',
    'ENGINE-018': 'pp_tests/gppl/legacy.py Engine.call statement dispatch (trace) and Engine._render descriptor regex',
    'ENGINE-019': 'pp_tests/gppl/legacy.py Engine.__init__ (lines outside @...endp are dropped)',
    'ENGINE-020': "pp_tests/gppl/legacy.py Engine._render ('(expr)' tokens clear the flags of their identifiers)",
    'ENGINE-021': 'pp_tests/gppl/builtins.py f_right (text[len(text) - count:] without an upper clamp)',
    'DESIGN-001': "GPP @usr_rapid L1222-1230 and L1362-1366 (link kept without a Z check); @usr_line L1387-1394 "
                  "('zpos gt nLastPathZ')",
    'DESIGN-002': "GPP @usr_rapid L1278-1288 (homing + rotation) and L1322-1333 (Z on the XY line unless bFirstMove)",
    'DESIGN-003': 'GPP @start_of_job L1110-1115 (deferred index) before L1145-1148 (@usr_ct)',
    'DESIGN-004': 'GPP @usr_rapid (A block first, then @usr_rapid_xyz)',
    'DESIGN-005': 'GPP @usr_tc_init_gmstates L908-913 (apos/bpos/cpos = 0); @usr_ct_after L836-849; '
                  '@usr_r1_select_dir L2371-2376 (abort L2397-2401)',
    'DESIGN-006': 'GPP @home_number (iWorkoffset = 54; the template newshift/ORGXYZ values were never output and '
                  'were deleted from @home_data); vericut/GcodeSim.ini [MAC]',
    'DESIGN-007': 'GPP @usr_r1pos_calc L2315-2340 (nR2pos never output); @usr_rapid L1248-1273 (bVertical toggle)',
}

# Observations the area reviews raised that are NOT registered (owner questions
# or possible facets without a test). Rendered in tests/PP_FINDINGS.md.
OBSERVATIONS = (
    ('Homing modes 3/4 (user-edited G53 homing)', "The homing block has no motion word, so after a cut "
     "'G53 Z0' runs at the modal G1 feed. The shipped G75 homing (mode 8) is unaffected.", 'area A review'),
    ('Empty sWorkpcDir header path', "';$PATH=/_N_WKS_DIR/_N_WPD' is written for an empty workpiece directory; "
     'intended, or should it be /_N_MPF_DIR? Pinned as CHARACTERIZATION only.', 'area A review'),
    ('CYCLE86 lift-off parameters', 'RPA/RPO/RPAP are omitted, so there is no lift-off after the oriented spindle '
     'stop (critic-09 second facet). Owner decision; no test because there is no id.', 'area E review'),
)

_missing_locations = sorted(entry.id for entry in _ENTRIES if entry.id not in LOCATIONS)
if _missing_locations or len(LOCATIONS) != len(_ENTRIES):
    raise ValueError(f'LOCATIONS must name exactly the registry ids; missing {_missing_locations}')
_ENTRIES = [replace(entry, location=LOCATIONS[entry.id]) for entry in _ENTRIES]


def _resolved(entry):
    changes = {}
    if entry.id in RESOLUTIONS:
        changes['status'], changes['resolution'] = RESOLUTIONS[entry.id]
    facets = tuple((key[len(entry.id) + 1:-1], status, resolution) for key, (status, resolution)
                   in RESOLUTIONS.items() if key.startswith(entry.id + '['))
    if facets:
        changes['facet_status'] = facets
    if entry.id in ENGINE_SCOPE:
        changes['engines'], changes['gppl'] = ENGINE_SCOPE[entry.id]
    elif entry.id in GPPL_NOTES:
        changes['gppl'] = GPPL_NOTES[entry.id]
    if entry.id in FIX_TESTS:
        changes['fix_tests'] = FIX_TESTS[entry.id]
    return replace(entry, **changes) if changes else entry


_unknown = sorted(({key.split('[')[0] for key in RESOLUTIONS} | set(ENGINE_SCOPE) | set(GPPL_NOTES)
                   | set(FIX_TESTS))
                  - {entry.id for entry in _ENTRIES})
if _unknown:
    raise ValueError(f'RESOLUTIONS/ENGINE_SCOPE/GPPL_NOTES name unknown ids: {_unknown}')
_ENTRIES = [_resolved(entry) for entry in _ENTRIES]

REGISTRY = {entry.id: entry for entry in _ENTRIES}
if len(REGISTRY) != len(_ENTRIES):
    raise ValueError('duplicate registry id in tests/support/defects.py')


def entries(kind=None, area=None, status=None):
    return [entry for entry in _ENTRIES
            if (kind is None or entry.kind == kind) and (area is None or entry.owner_area == area)
            and (status is None or entry.status == status)]
