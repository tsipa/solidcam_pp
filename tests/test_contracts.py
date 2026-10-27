"""Contracts between SolidCAM, the captured traces, the sequence fixtures and the GPP.

* Trace contract: pp_tests/trace.py must keep the inputs a capture is meant
  to preserve (pp_tests/README.md: "preserves all public input events and
  change flags ... input data for future broader replay") and must not mix
  trace parameters into NC output (ENGINE-016, ENGINE-017).
* Fixture event contract: hand-written sequence fixtures may only deliver
  inputs SolidCAM can produce, in an order SolidCAM can produce, or carry a
  written justification.
* SolidCAM event contract: events SolidCAM delivers under this VMID must be
  implemented or stop the post (PP-047 transformations, PP-048 MCO/dwell/4x
  drill events). Both depend on unverified SolidCAM event delivery.
"""
import json
import re
import unittest

from pp_tests.engine import UnsupportedGPPL
from pp_tests.trace import parse_trace, sanitize

from support import Session, fresh_engine, known_defect, parse_blocks, pp_source, vmid_user_parameters
from support.engines import declared_globals
from support.paths import FIXTURES, VMID, read_text, require_file
from support.session import SOLIDCAM_EVENTS
from support.vericut import VMID_FALLBACK

TRACE = ("(1)@line_5x ==> zpos:15.833T feed_type:feed_link dir5a:cw\n"
         "                    ..> prev_command:'@line_5x' job_type:'contour' user_name:'Person'\n"
         "(1)@move_5x ==> apos:3.035T dir5a:ccw prev_command:'@line_5x' tool_direction:cw\n"
         "(1)@drill ==> drill_type:G83 feed:100.000T\n")


class TraceContractTests(unittest.TestCase):
    def test_identities_are_still_redacted(self):
        """INDEPENDENT: pp_tests/README.md capture contract: free-text identities
        (user names, paths) are redacted, enum identifiers in the allowlist
        (cw/ccw, planes, logicals) survive, and change flags are kept."""
        events = sanitize(parse_trace(TRACE))
        self.assertEqual(events[0]['parameters']['user_name'], '<redacted>')
        self.assertEqual(events[1]['parameters']['dir5a'], 'ccw')
        self.assertEqual(events[0]['changed'], {'zpos': True})

    @known_defect('ENGINE-017')
    def test_safety_relevant_enums_survive_sanitizing(self):
        """INDEPENDENT: README capture contract ("input data for future broader
        replay") and the GPP inputs that drive safety branches: feed_type
        (@usr_line CAM-link test) and prev_command (@usr_rapid) decide whether
        G75 homing is skipped; job_type and drill_type select paths. They are
        enumerations, not identities; sanitize() redacts four of them
        (tool_direction 'cw' is already in the allowlist)."""
        events = sanitize(parse_trace(TRACE))
        kept = {
            'feed_type': events[0]['parameters']['feed_type'],
            'prev_command': events[1]['parameters']['prev_command'],
            'job_type': events[0]['parameters']['job_type'],
            'tool_direction': events[1]['parameters']['tool_direction'],
            'drill_type': events[2]['parameters']['drill_type'],
        }
        self.assertEqual(kept, {'feed_type': 'feed_link', 'prev_command': '@line_5x', 'job_type': 'contour',
                                'tool_direction': 'cw', 'drill_type': 'G83'})

    @known_defect('ENGINE-016')
    def test_nested_call_parameters_are_not_nc_output(self):
        """INDEPENDENT: GPPL trace format: '..>' marks a parameter continuation
        line, never generated NC. After a nested (depth >= 2) call header the
        parser appends such lines to the parent event's NC output. The nested
        continuation is placed at column 20 like the top-level ones; no trace
        with nested-call parameters is in the repository (engine-impl-critic-13
        correction), so that column is an assumption of the probe."""
        events = parse_trace("(1)@line_5x ==> apos:-90.000T\n"
                             "(2)@usr_line ==>\n"
                             "                    ..> nested_param:5.0T\n"
                             "                      > G1 X1\n")
        self.assertEqual(events[0].output, ['G1 X1'])


# ----------------------------------------------------------------------------
# Hand-written sequence fixtures vs the SolidCAM event contract (efc-11).
# ----------------------------------------------------------------------------
MOTION_EVENTS = frozenset({'rapid_move', 'line', 'arc', 'arc_zx', 'arc_yz', 'move_5x', 'line_5x',
                           'move_4x', 'line_4x', 'drill', 'drill_point'})
# Events whose GPP code reaches @usr_rapid, the only reader of prev_command.
RAPID_EVENTS = frozenset({'move_5x', 'move_4x', 'rapid_move', 'drill'})

ALLOWED = {
    ('motion_sequences', 'index_between_jobs_and_repeated_same_angle', 4, 'prev_command'):
        'move_5x after start_of_job inherits a stale @line_5x; harmless (bCamLinkRetract is false)',
    ('motion_sequences', 'offset_change_invalidates_cam_authorization', 1, 'pp_owned:iworkoffset'):
        'defensive: SolidCAM changes offsets only via start_of_job/home_number',
    ('motion_sequences', 'job_end_invalidates_confirmed_rapid_link', 2, 'job_closed'):
        'defensive: move_5x directly after end_of_job is not a SolidCAM sequence',
    ('motion_sequences', 'job_end_invalidates_confirmed_rapid_link', 2, 'prev_command'):
        'defensive: prev_command forced to @line_5x after end_of_job',
    ('motion_sequences', 'tmatrix_invalidates_cam_authorization', 1, 'tmatrix_inside_job'):
        'defensive: SolidCAM likely never emits tmatrix between two moves of one job',
    ('motion_sequences', 'tmatrix_invalidates_cam_authorization', 2, 'prev_command'):
        'defensive: prev_command forced to @line_5x after tmatrix',
}


def fixture_sequences():
    data = json.loads(read_text(FIXTURES / 'motion_sequences.json', 'utf-8'))
    for scenario in data['scenarios']:
        yield 'motion_sequences', scenario['name'], scenario['steps']
    data = json.loads(read_text(FIXTURES / 'shit2_contiguous_link.json', 'utf-8'))
    yield 'shit2_contiguous_link', 'trace_excerpt', data['steps']
    data = json.loads(read_text(FIXTURES / 'arc_link_boundary.json', 'utf-8'))
    yield 'arc_link_boundary', 'arc_link_rotation', [data['arc'], data['link'], data['rotation']]


def contract_violations(sequences, pp_owned):
    """{(fixture, scenario, step, rule)} for steps SolidCAM is unlikely to produce.

    Rules: a CAM event may not set a GPP-declared variable (SolidCAM cannot
    produce it); motion events need an open job (start_of_job .. end_of_job)
    and tmatrix comes between jobs (3696aa2); for events reaching @usr_rapid,
    prev_command is '@' + the previous CAM event (@usr_rapid compares it with
    '@line_5x' etc.).
    """
    found = set()
    for fixture, name, steps in sequences:
        job_open = True              # fixtures start mid-job (motion_engine baseline)
        previous_event = 'line_5x'   # motion_engine prev_command
        prev_command = '@line_5x'
        for ordinal, step in enumerate(steps):
            call = step['call'].lower()
            values = {key.lower(): value for key, value in (step.get('set') or {}).items()}
            if call in SOLIDCAM_EVENTS:
                for key in sorted(set(values) & pp_owned):
                    found.add((fixture, name, ordinal, f'pp_owned:{key}'))
            if call == 'start_of_job':
                job_open = True
            elif call == 'end_of_job':
                job_open = False
            elif call == 'tmatrix' and job_open:
                found.add((fixture, name, ordinal, 'tmatrix_inside_job'))
            elif call in MOTION_EVENTS and not job_open:
                found.add((fixture, name, ordinal, 'job_closed'))
            # The legacy harness never updates prev_command itself; only `set` does.
            prev_command = values.get('prev_command', prev_command)
            if call in RAPID_EVENTS and ordinal and prev_command != '@' + previous_event:
                found.add((fixture, name, ordinal, 'prev_command'))
            if call in SOLIDCAM_EVENTS:
                previous_event = call
    return found


class FixtureEventContractTests(unittest.TestCase):
    def setUp(self):
        self.pp_owned = set(declared_globals(pp_source()))

    def test_fixtures_follow_event_contract_or_are_justified(self):
        """INDEPENDENT: SolidCAM event-order evidence (3696aa2: tmatrix precedes
        start_of_job; @usr_rapid reads prev_command) and the GPP's own
        declarations (PP-owned variables are not CAM inputs). Every violation
        in the sequence fixtures carries a written reason; new violations need
        a fix or a reason, and fixed ones must leave ALLOWED."""
        found = contract_violations(fixture_sequences(), self.pp_owned)
        self.assertEqual(sorted(found - set(ALLOWED)), [], 'new contract violations need a fix or a reason')
        self.assertEqual(sorted(set(ALLOWED) - found), [], 'stale ALLOWED entries')

    def test_checker_rejects_impossible_sequences(self):
        """INDEPENDENT: self-check of the contract checker on a synthetic
        sequence that breaks every rule once."""
        bad = [('synthetic', 'bad', [
            {'call': 'end_of_job'},
            {'call': 'line_5x', 'set': {'zpos': 1}},                                       # job closed
            {'call': 'start_of_job'},
            {'call': 'move_5x', 'set': {'iWorkoffset': 56, 'prev_command': '@line_5x'}},  # PP-owned, stale
            {'call': 'tmatrix'},                                                          # inside a job
        ])]
        kinds = {item[3] for item in contract_violations(bad, self.pp_owned)}
        self.assertEqual(kinds, {'job_closed', 'pp_owned:iworkoffset', 'prev_command', 'tmatrix_inside_job'})

    def test_vmid_fallback_matches_vmid(self):
        """INDEPENDENT: Gmill_540v_4x.vmid <UserDefParams>: the defaults
        support.vericut uses for GPP copies without a VMID must equal the
        parsed VMID (names, types and default values)."""
        require_file(VMID)
        self.assertEqual(vmid_user_parameters(), VMID_FALLBACK)


# ----------------------------------------------------------------------------
# SolidCAM events this VMID delegates to the post.
# ----------------------------------------------------------------------------
# The stock engine raises UnsupportedGPPL('postprocessor stopped: <line>') for
# both `input` and `abort`; any other UnsupportedGPPL is a harness error.
STOPPED = re.compile(r'postprocessor stopped: ')


class TransformEventTests(unittest.TestCase):
    """The VMID delegates operation transformations to the post
    (<sub0 ... SoftwareTransform="0">, unchanged since ffd296c). Under the same
    setting the author's Mach3 template (ffd296c:mach3/4x/Mach3_4X_Y.gpp)
    implements @rotate as G68/G69 and @mirror as G51.1/G50.1; the Sinumerik
    equivalents are ROT/AROT and MIRROR/AMIRROR."""

    def frame_blocks_or_stop(self, procedure, **values):
        """NC blocks the event emits, or None when the post stops (input/abort)."""
        session = Session()
        try:
            return parse_blocks(session.ev(procedure, **values))
        except UnsupportedGPPL as exc:
            if STOPPED.search(str(exc)):
                return None
            raise

    @known_defect('PP-047', facet='rotate')
    def test_rotate_event_changes_the_frame_or_stops(self):
        """INDEPENDENT: a delegated transformation must change the controller
        frame (Sinumerik ROT/AROT with the 90 degree angle) or stop the post so
        the user knows the job cannot be posted; an empty @rotate machines the
        rotated copy at the original position. UNVERIFIED: that SolidCAM calls
        @rotate with an untransformed toolpath under this VMID (PP-047
        uncertain)."""
        blocks = self.frame_blocks_or_stop('rotate', rotate_cancel=False, angle=90)
        if blocks is None:
            return
        frames = [block.raw for block in blocks
                  if (block.has('ROT') or block.has('AROT')) and any(word.value == 90 for word in block.words)]
        self.assertTrue(frames, f'@rotate emitted {[block.raw for block in blocks]!r}')

    @known_defect('PP-047', facet='mirror')
    def test_mirror_event_changes_the_frame_or_stops(self):
        """INDEPENDENT: a delegated mirror must program MIRROR/AMIRROR or stop
        the post; an empty @mirror posts the mirrored copy unmirrored.
        UNVERIFIED: SolidCAM event delivery under SoftwareTransform="0"
        (PP-047 uncertain)."""
        blocks = self.frame_blocks_or_stop('mirror', mirror_type='mirror_x')
        if blocks is None:
            return
        frames = [block.raw for block in blocks if block.has('MIRROR') or block.has('AMIRROR')]
        self.assertTrue(frames, f'@mirror emitted {[block.raw for block in blocks]!r}')


class SolidCamEventCoverageTests(unittest.TestCase):
    """SolidCAM calls GPP procedures by name and, most likely, skips names the
    post does not define, so a missing event procedure drops the event
    silently. The event set comes from the author's own 4x template
    (ffd296c:mach3/4x/Mach3_4X_Y.gpp, a fork of teodoryantcheff/SolidCam-Mach3-
    Post), which uses the SolidCAM MCO variables (optional_stop,
    MCO_New_Line, MCO_CoordSysType, move_axis_*). round_comp, assign_axis and
    call_simple_proc are no-ops or subroutine-only there and not required."""

    EVENTS = {
        'halt_program': 'MCO "Halt program" (template: M0)',
        'machine_opt_stop': 'MCO optional stop (template: M1)',
        'mco_message': 'MCO operator message',
        'move_object': 'MCO axis move (template: G53/G0/G1)',
        'cool_flood': 'MCO flood coolant on/off',
        'cool_mist': 'MCO mist coolant on/off',
        'stop_tool': 'spindle stop event (template: M5)',
        'delay': 'dwell event (template: G4)',
        'dwell': 'dwell event (template: G4)',
        'drill4x_pnt': '4x drill point (template: re-runs @drill with the A position)',
        'rotate_to_plane': 'rotate the 4th axis to the next plane (template: G0 Z, G0 A)',
    }

    @known_defect('PP-048', facet='event-coverage')
    def test_every_event_of_the_authors_4x_template_is_handled(self):
        """INDEPENDENT: the event set the same author's SolidCAM 4x template
        handles; each must have a procedure (implementing the event or
        aborting). UNVERIFIED: that SolidCAM silently skips undefined
        procedures and delivers these events for this machine (PP-048
        uncertain)."""
        procedures = fresh_engine().procedures
        missing = sorted(f'@{name}: {meaning}' for name, meaning in self.EVENTS.items() if name not in procedures)
        self.assertEqual(missing, [])

    @known_defect('PP-048', facet='mco-halt', match='no @halt_program|posts no M0')
    def test_mco_halt_program_stops_the_machine(self):
        """INDEPENDENT: an MCO 'Halt program' (inserted to re-clamp or flip the
        part) must post a program stop; M0 is the Sinumerik program stop.
        UNVERIFIED: SolidCAM delivers @halt_program to this post (PP-048
        uncertain)."""
        session = Session()
        self.assertTrue('halt_program' in session.engine.procedures, 'no @halt_program: the MCO halt is not posted')
        blocks = parse_blocks(session.ev('halt_program'))
        self.assertTrue(any(block.has('M', 0) for block in blocks),
                        f'the MCO halt posts no M0: {[block.raw for block in blocks]}')


if __name__ == '__main__':
    unittest.main()
