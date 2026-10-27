"""Indexing, tmatrix and the CAM-link state machine of Gmill_540v_4x.gpp.

Area C sentinel (tests/support/defects.py AREAS['C']).

Oracles
-------
* Rotation safety, the contract of d5952a2/37ab3b9 (usr_rapid comment,
  tests/CAM_LINK_POSTMORTEM.md): A may rotate only after G75 Z homing, or
  inside a contiguous CAM link that began with a confirmed straight upward Z
  feed_link retract in the same job and index context. Every index or job
  boundary revokes the authorization and re-arms the index clearance.
* Sinumerik 828D modal semantics through support.modal.replay: G0/G1 are modal
  (group 1, a block without a group-1 word inherits the previous motion);
  G54..G57 and G505..G599 are the settable work offsets (group 8).
* Commit intent: c03e1b4 (explicit G0 on the first index, 'Feedrate not
  programmed' otherwise), 92e2b23 (M1 before an index), 8d6b044 (the tmatrix
  index comes from angle_4x_around_x), 3696aa2 (deferred tmatrix index with a
  resolved work offset), e574716/719e946 (fourth_axis indexes with the default
  options and does not count the angle twice).
* PP header option documentation: i4xIndexMode (0 simple rotation, 1 new work
  offset per index position, 2 trig macro) and i4xIndexClearanceMode
  (0 Z homing, 1 Z tool Z level, 2 Z tool start plane).

Scenarios are realistic sessions (support.session.Session: @init_post, VMID
defaults, SolidCAM event order, prev_command tracking). Inputs are synthetic;
expected values never come from copying current output, except in the
CHARACTERIZATION pins of open DESIGN questions (@covers).

Known defects owned here (one canonical test per facet): PP-005, PP-015,
PP-016, PP-017, PP-018, PP-038 (abort, syntax), PP-039, PP-044 (index-boundary,
syntax), PP-053. Work offsets and multiple fixtures (PP-014, PP-032..PP-035,
DESIGN-006) live in test_work_offsets_fixtures.py; DESIGN-004 is pinned by
test_motion.py::test_actual_shit2_contiguous_link.

Several state-machine tests inject one state bit or deliver an event outside
its normal SolidCAM context (CamLinkGuardTests, the boundary and initial-state
tests, the lone @tmatrix case of test_index_clearance_survives_xyz_only_rapids
and the bare @drill_point of
test_untracked_motion_event_between_retract_and_rapid_requires_homing). They
are structural pins and say so: normal event order makes some guards
redundant, and only direct setup proves that each documented precondition
blocks on its own.

ReversionDetectionTests re-runs the regression checks against focused
in-memory mutants of the GPP and requires an AssertionError from each.
"""
import re
import textwrap
import unittest

from pp_tests.engine import UnsupportedGPPL

from support import (DRILL_DEFAULTS, SETTABLE_OFFSETS, Session, assert_detected, covers, index_of,
                     known_defect, last_index_of, mutate, parse_blocks, replay)


# ---------------------------------------------------------------------------
# Block predicates and session builders
# ---------------------------------------------------------------------------
def is_rotation(block):
    return block.rotary('A') is not None


def is_home_z(block):
    return 'Z' in block.homing_axes


def is_optional_stop(block):
    return 1 in block.m


def rotations(blocks):
    """[(mode, value)] of every A word, in order."""
    return [block.rotary('A') for block in blocks if is_rotation(block)]


def job_session(source=None, **options):
    """First job of a program after one cut (A never rotated in this job)."""
    session = Session(source=source, options=options or None)
    session.first_tool()
    session.cut(10, 20, 5, -1)
    return session


def rotated_job(source=None, **options):
    """Mid-job state: one homed rotation to A5, back at the part, plunged to Z-1.

    The index clearance of the job is discharged (bIndexClearancePending
    false), the job is positioned and the last path Z is -1.
    """
    session = job_session(source, **options)
    session.ev('move_5x', ['apos'], apos=5)
    session.ev('move_5x', ['xpos', 'ypos', 'zpos'], xpos=10, ypos=20, zpos=5)
    session.ev('line_5x', ['zpos', 'feed'], zpos=-1, feed_type='feed_cut')
    return session


def rotated_4x_job(source=None):
    """Like rotated_job, but the rotation comes from a 4x event (cpos=5, apos 0)."""
    session = job_session(source)
    session.ev('move_4x', ['cpos'], cpos=5)
    session.ev('line_4x', ['zpos', 'feed'], zpos=-1, feed_type='feed_cut')
    return session


def link_retract(session, z=20, call='line_5x', **values):
    """A CAM feed_link straight up in Z (the d5952a2 'confirmed retract')."""
    return session.ev(call, ['zpos'], zpos=z, feed_type='feed_link', **values)


def rotate(session, a=10):
    """A rotary-only rapid (move_5x); prev_command is tracked by the Session."""
    return session.ev('move_5x', ['apos'], apos=a)


class LinkOracle:
    def assert_rotation_after_homing(self, text, context=''):
        blocks = parse_blocks(text)
        rotation = index_of(blocks, is_rotation)
        self.assertGreaterEqual(rotation, 0, f'no rotary output {context}: {text!r}')
        self.assertGreaterEqual(last_index_of(blocks, is_home_z, 0, rotation), 0,
                                f'A rotated without Z homing {context}: {text!r}')

    def assert_rotation_without_homing(self, text, expected, context=''):
        blocks = parse_blocks(text)
        self.assertEqual(rotations(blocks), [expected], f'{context}: {text!r}')
        self.assertEqual([block.raw for block in blocks if 75 in block.g], [],
                         f'unwanted homing inside a confirmed CAM link {context}: {text!r}')


# ---------------------------------------------------------------------------
# Index history: c03e1b4, 92e2b23, 8d6b044, 3696aa2
# ---------------------------------------------------------------------------
class IndexHistoryTests(LinkOracle, unittest.TestCase):
    def _check_first_program_index(self, source=None):
        session = Session(source=source)
        session.first_tool(tmatrix=45.125)
        replayed = session.replay()
        blocks = [block for block, _ in replayed]
        rotation = index_of(blocks, is_rotation)
        self.assertGreaterEqual(rotation, 0, session.text())
        state = replayed[rotation][1]
        self.assertEqual(state.motion, 0, f'first index is not a G0 move (c03e1b4): {blocks[rotation].raw!r}')
        self.assertEqual(state.work_offset, 54, f'first index is not in G54 (3696aa2): {blocks[rotation].raw!r}')
        self.assertEqual(blocks[rotation].rotary('A'), ('DC', 45.125), blocks[rotation].raw)
        self.assertGreaterEqual(index_of(blocks, is_optional_stop, 0, rotation), 0,
                                f'no M1 before the first index (92e2b23): {session.text()!r}')
        sentinels = [word.raw for block in blocks for word in block.words if word.value == 9999]
        self.assertEqual(sentinels, [], 'modal 9999 sentinel leaked into the NC output')

    def test_first_program_index_is_explicit_rapid_with_resolved_offset(self):
        """INDEPENDENT: c03e1b4, 3696aa2 and 92e2b23 on a real program start.

        c03e1b4: the first index block was 'G54 A45.' without G0 and the 828D
        stopped with 'Feedrate not programmed'; Sinumerik keeps G0/G1 modal, so
        the motion in effect at the index block must be an explicit G0 (the
        9999 motion sentinel of @usr_init_gmstates forces it). Its format half
        ('7.3') matches VMID RotaryAxisPrecision=0.001: A=DC(45.125) exactly.
        The first A output of a program is DC (position unknown, ab853be).
        3696aa2: the deferred index block states G54, never the 9999 sentinel.
        92e2b23: an optional stop M1 precedes the rotation.
        Absorbs test-suite-review test_first_index_move_is_an_explicit_rapid_with_work_offset.
        """
        self._check_first_program_index()

    def _check_index_after_feed_moves(self, source=None):
        cases = [(index_mode, offset, clearance, retract, approach)
                 for index_mode, offset in ((0, 54), (1, 55))
                 for clearance, retract, approach in ((0, None, None), (1, 45, 38), (2, 40, 36))]
        for index_mode, offset, clearance, retract, approach in cases:
            with self.subTest(index_mode=index_mode, clearance=clearance):
                session = Session(source=source, options=dict(i4xIndexMode=index_mode,
                                                              i4xIndexClearanceMode=clearance))
                # Clearance level above the start level in both jobs (the PP warns
                # otherwise); distinct values identify which job's level is used.
                session.first_tool(tool_z_level=45, tool_start_plane=40)
                session.cut(10, 20, 5, -1)
                self.assertEqual(session.state['imotionmode'], 1, 'precondition: modal G1 after cutting')
                mark = session.mark()
                session.same_tool_job(tmatrix=90, position=2, tool_z_level=38, tool_start_plane=36)
                text = session.text(mark)
                # Replay only the index sequence: G0 and the offset must be
                # programmed by the index itself, not inherited.
                replayed = replay(text)
                blocks = [block for block, _ in replayed]
                rotation = index_of(blocks, is_rotation)
                self.assertGreaterEqual(rotation, 0, text)
                self.assertEqual(len(rotations(blocks)), 1, text)
                self.assertEqual(blocks[rotation].axes, {}, f'index block also moves X/Y/Z: {text!r}')
                state = replayed[rotation][1]
                self.assertEqual(state.motion, 0, f'index inherits the modal feed motion: {text!r}')
                self.assertEqual(state.work_offset, offset, f'work offset not stated for the index: {text!r}')
                stop = index_of(blocks, is_optional_stop, 0, rotation)
                self.assertGreaterEqual(stop, 0, f'no M1 before the index (92e2b23): {text!r}')
                for block, after in replayed:
                    if 'Z' in block.axes:
                        self.assertEqual(after.motion, 0, f'clearance move {block.raw!r} is not rapid: {text!r}')
                if clearance == 0:
                    self.assertGreaterEqual(last_index_of(blocks, is_home_z, stop, rotation), 0,
                                            f'A rotated without Z homing: {text!r}')
                else:
                    self.assertTrue(0 < rotation < len(blocks) - 1, f'no retract/approach around the index: {text!r}')
                    self.assertEqual(blocks[rotation - 1].axes.get('Z'), retract, text)
                    self.assertEqual(blocks[rotation + 1].axes.get('Z'), approach, text)

    def test_index_after_feed_moves_is_rapid_and_states_work_offset(self):
        """INDEPENDENT: c03e1b4 root cause and the index option documentation.

        After cutting, the modal motion is G1, so every index variant must
        program G0 itself before A, in a block of its own (no X/Y/Z), with
        exactly one A word, and rapid clearance moves. The work offset is stated
        for the index: G55 for index position 2 in i4xIndexMode=1 (one offset
        per position); in mode 0 the G54 is a pin of 3696aa2's stated intent
        ('force' the offset), not a safety property. M1 precedes the rotation
        (92e2b23; checked with index_of >= 0, so a missing M1 fails). Clearance
        modes: 0 homes Z before A; 1/2 retract to the finished job's tool Z
        level / start plane and approach at the new job's level.
        Absorbs test-suite-review MotionModeRegressions.test_index_rotation_is_its_own_rapid_block.
        """
        self._check_index_after_feed_moves()

    def _check_tmatrix_index_angle(self, source=None):
        # CAM inputs of the pre-8d6b044 formula, chosen to reproduce its -360.
        session = Session(source=source, y_angle_const_z=-180, dev_angle_z=-180)
        session.first_tool()
        session.cut(10, 20, 5, -1)
        mark = session.mark()
        session.same_tool_job(tmatrix=180)
        found = [value for _, value in rotations(session.blocks(mark))]
        self.assertEqual(found, [180.0], session.text(mark))
        self.assertEqual(session.state['nr1pos'], 180)

    def test_tmatrix_index_uses_angle_4x_around_x(self):
        """INDEPENDENT: 8d6b044 commit message.

        A 180-degree indexed CoordSys must rotate to A180. The old source
        (-y_angle_const_z - dev_angle_z) collapsed it to -360, A never moved and
        the job ran on the A0 face; those inputs are supplied as distractors.
        """
        self._check_tmatrix_index_angle()

    def _check_index_between_jobs(self, source=None):
        for tool in (None, 2):
            with self.subTest(tool_change=tool is not None):
                session = job_session(source)
                mark = session.mark()
                if tool is None:
                    session.same_tool_job(tmatrix=90)
                else:
                    session.next_tool(tool, tool + 1, tmatrix=90)
                session.cut(30, 40, 5, -1)
                text = session.text(mark)
                blocks = session.blocks(mark)
                rotation = index_of(blocks, lambda block: block.rotary('A') is not None
                                    and block.rotary('A')[1] == 90)
                self.assertGreaterEqual(rotation, 0, text)
                self.assertEqual([value for _, value in rotations(blocks)], [90.0], f'exactly one A90 index:\n{text}')
                home = last_index_of(blocks, is_home_z, 0, rotation)
                stop = last_index_of(blocks, is_optional_stop, 0, rotation)
                first_xy = index_of(blocks, lambda block: 'X' in block.axes or 'Y' in block.axes)
                self.assertGreaterEqual(stop, 0, f'M1 required before the A90 index:\n{text}')
                self.assertTrue(0 <= home < rotation < first_xy, f'G75 Z, A90, then XY:\n{text}')
                self.assertEqual([block.raw for block in blocks[home + 1:rotation] if 'Z' in block.axes], [],
                                 f'Z moves between the homing and the rotation:\n{text}')

    def test_index_between_jobs_has_optional_stop_and_retract_before_rotation(self):
        """INDEPENDENT: 92e2b23 (optional stop before 4th-axis index moves) and
        index clearance mode 0 (Z homing before the rotation).

        For a same-tool and a tool-change job boundary with a tmatrix index:
        exactly one A90 word (tc-12), M1 and G75 Z come before it, no Z move
        lowers the tool in between, and the part is approached in XY only after
        the rotation.
        """
        self._check_index_between_jobs()


# ---------------------------------------------------------------------------
# First index of a program (known defects)
# ---------------------------------------------------------------------------
class FirstIndexClearanceTests(unittest.TestCase):
    """The first tmatrix index runs in the first @start_of_job, before the first
    tool change, before any @end_of_job stored nPtool_z_level /
    nPtool_start_plane and before @usr_rapid assigned sHomestrrot."""

    @known_defect('PP-015')
    def test_first_index_tool_level_clearance_never_plunges_to_z0(self):
        """INDEPENDENT: PP header definition of i4xIndexClearanceMode 1/2
        (retract to the tool Z level / tool start plane before the rotation)
        and the tool-change order of a program start.

        Merged tc-02 oracle with the verifier's correction: on the first job the
        deferred index runs before 'T1 M06 D1', while the previous program's
        tool and length offset are still active, so no Z word may be programmed
        before the first M06 (G75 Z1= homing is allowed; a 'Z60' with an
        unknown tool length is not a clearance). In addition, between program
        start and the first rotation no Z move goes below the job's clearance
        level, and when A rotates Z is either homed (G75, modal replay 'homed')
        or at least at that level. Z0 (part zero, often the rotary centreline)
        is neither. Currently the retract uses the not yet assigned nPtool_*
        (0): 'G0 G54 Z0', A=DC(90), then the new level, all before M06. A fix
        that only substitutes the job's level still programs Z before M06 and
        keeps this test red (tc-02 correction).
        """
        problems = {}
        for clearance, level in ((1, 60), (2, 50)):
            session = Session(options=dict(i4xIndexClearanceMode=clearance))
            session.first_tool(tmatrix=90, tool_z_level=60, tool_start_plane=50)
            replayed = session.replay()
            blocks = [block for block, _ in replayed]
            rotation = index_of(blocks, is_rotation)
            tool_load = index_of(blocks, lambda block: 6 in block.m)
            if rotation < 0 or tool_load < 0:
                raise RuntimeError(f'scenario precondition failed (no index or no M06): {session.text()!r}')
            before_tool_load = [block.raw for block in blocks[:tool_load] if 'Z' in block.axes]
            low = [block.raw for block in blocks[:rotation] if block.axes.get('Z', level) < level]
            at_rotation = replayed[rotation][1]
            z_at_rotation = 'homed' if 'Z' in at_rotation.homed else at_rotation.position[2]
            if before_tool_load or low or (z_at_rotation != 'homed'
                                           and (z_at_rotation is None or z_at_rotation < level)):
                problems[clearance] = dict(z_before_first_m06=before_tool_load, below_clearance=low,
                                           z_at_rotation=z_at_rotation)
        self.assertEqual(problems, {}, 'first index: Z programmed with the previous tool or A rotated '
                                       'below the job clearance')

    @known_defect('PP-053', match='no Z homing of its own')
    def test_first_index_in_z_homing_mode_homes_z(self):
        """INDEPENDENT: PP header '0=Z-Homing' for i4xIndexClearanceMode: every
        index homes Z after its optional stop, as all later indexes do
        ('M1 / G75 Z1=0. / G75 Y1=0 X1=0 / A').

        The first index of a program has no G75 because sHomestrrot is still
        empty; it relies on @start_program having homed earlier (safe in
        practice, low severity).
        """
        session = Session()
        session.first_tool(tmatrix=90)
        blocks = session.blocks()
        rotation = index_of(blocks, is_rotation)
        stop = last_index_of(blocks, is_optional_stop, 0, rotation)
        if rotation < 0 or stop < 0:
            raise RuntimeError(f'scenario precondition failed (index or M1 missing): {session.text()!r}')
        self.assertGreaterEqual(last_index_of(blocks, is_home_z, stop, rotation), 0,
                                f'the first index has no Z homing of its own: {session.text()!r}')


# ---------------------------------------------------------------------------
# Index work offset modes (known defects) and fourth_axis indexing
# ---------------------------------------------------------------------------
class IndexWorkOffsetModeTests(unittest.TestCase):
    @known_defect('PP-016')
    def test_same_index_position_keeps_new_workoffset(self):
        """INDEPENDENT: PP header i4xIndexMode '1=New WorkOffset' and the
        usr_4x_index formula iWorkoffset = base + (position-1): index position
        2 is machined in G55 whether or not A moves in this job.

        Job 2 indexes to CoordSys position 2 (A90, G55). Job 3 stays at position
        2: @home_number resets the offset to G54 and the index adds position-1
        only when A changes, so job 3 runs in G54, the A0 position's offset.
        Scenario assumption (the registry's settle evidence): SolidCAM reports
        'position' 2 for both operations on that CoordSys.
        """
        session = Session(options=dict(i4xIndexMode=1))
        session.first_tool()
        session.cut(10, 20, 5, -1)
        session.same_tool_job(tmatrix=90, position=2)
        session.cut(20, 30, 5, -1)
        job3 = session.mark()
        session.same_tool_job(position=2)
        session.cut(20, 30, 5, -1)
        moves = [(block.raw, state.work_offset, state.a) for block, state in session.replay_tail(job3)
                 if block.axes]
        if not moves or any(a != 90 for _, _, a in moves):
            raise RuntimeError(f'scenario precondition failed (job 3 must cut at A90): {moves}')
        self.assertEqual(sorted({offset for _, offset, _ in moves}), [55],
                         f'job 3 at index position 2 (A90): (block, offset, A) = {moves}')

    @known_defect('PP-017')
    def test_new_workoffset_mode_maps_position_to_offset(self):
        """INDEPENDENT: PP header i4xIndexMode '1=New WorkOffset' (one settable
        offset per index position, G54 + position - 1).

        Two successive @fourth_axis indexes (positions 2 and 3) must machine in
        G55 and then G56. usr_4x_index adds position-1 to the already shifted
        offset, giving 54 -> 55 -> 57.
        """
        session = Session(options=dict(i4xIndexMode=1))
        session.first_tool()
        session.cut(10, 20, 5, -1)
        found = []
        for angle, position in ((90, 2), (180, 3)):
            session.ev('fourth_axis', angle=angle)
            mark = session.mark()
            session.cut(10, 20, 5, -1)
            moves = [state for block, state in session.replay_tail(mark) if block.axes]
            if not moves or {state.a for state in moves} != {angle}:
                raise RuntimeError(f'scenario precondition failed (cut not at A{angle}): {session.text(mark)!r}')
            found.append((position, angle, sorted({state.work_offset for state in moves})))
        self.assertEqual(found, [(2, 90, [55]), (3, 180, [56])],
                         '(index position, A, offsets of the following cut)')


class FourthAxisIndexTests(LinkOracle, unittest.TestCase):
    def _check_default_indexing(self, source=None):
        session = job_session(source)
        text = session.ev('fourth_axis', angle=90, angle_4x_around_x_dir='ccw')
        blocks = parse_blocks(text)
        self.assertEqual(rotations(blocks), [('ACP', 90.0)], text)
        self.assert_rotation_after_homing(text)
        self.assertEqual(session.state['iworkoffset'], 54)
        other = [code for block in blocks for code in block.g if code in SETTABLE_OFFSETS and code != 54]
        self.assertEqual(other, [], f'default indexing changed the work offset: {text!r}')

    def test_default_indexing_is_simple_rotation(self):
        """INDEPENDENT: e574716 shipped defaults (i4xIndexMode 0 'Simple
        Rotation', i4xIndexClearanceMode 0 'Z-Homing'), read from @init_post.

        A @fourth_axis index to 90 with direction 'ccw' rotates A=ACP(90)
        after G75 Z and stays in G54 (no per-position offset). The ACP mode is
        a CHARACTERIZATION of the PP's bff5ed0 direction mapping (direction
        source: DESIGN-005, area B); the value, the homing and G54 are the
        independent part.
        """
        self._check_default_indexing()

    def _check_fourth_axis_single_word(self, source=None):
        cases = [(90, 123, 'ccw', ('ACP', 90.0)), (-90, 45, 'cw', ('ACN', 270.0)), (270, 0, 'ccw', ('ACP', 270.0))]
        for angle, stale_apos, direction, expected in cases:
            with self.subTest(angle=angle):
                session = job_session(source)
                text = session.ev('fourth_axis', angle=angle, apos=stale_apos, angle_4x_around_x_dir=direction,
                                  opposite_z_angle_const_y=0)
                self.assertEqual(rotations(parse_blocks(text)), [expected], text)
                self.assertEqual(session.state['apos'], 0)

    def test_fourth_axis_emits_single_index_word(self):
        """INDEPENDENT: e574716 (@fourth_axis calls the index) and 719e946 (the
        angle is not also copied into apos, a stale apos is cleared).

        One A word per index at the transform angle in the positive modulo
        range (-90 -> 270); apos is 0 afterwards. The ACN/ACP mode is a
        CHARACTERIZATION of the PP's own mapping since bff5ed0 (direction from
        angle_4x_around_x_dir, cw -> ACN, ccw -> ACP; DESIGN-005, area B).
        """
        self._check_fourth_axis_single_word()

    def _check_fourth_axis_return_to_zero(self, source=None):
        session = job_session(source, i4xIndexMode=1)
        first = session.ev('fourth_axis', angle=90)
        self.assertEqual(session.state['position'], 2)
        replayed = replay(first)
        rotation = index_of([block for block, _ in replayed], is_rotation)
        self.assertGreaterEqual(rotation, 0, first)
        self.assertEqual(replayed[rotation][1].work_offset, 55, f'position 2 not on G55: {first!r}')
        session.cut(10, 20, 5, -1)
        session.same_tool_job()                  # @home_number of the next job (G54)
        back = session.ev('fourth_axis', angle=0)
        self.assertEqual(session.state['position'], 1)
        self.assertEqual([value for _, value in rotations(parse_blocks(back))], [0.0], back)
        self.assert_rotation_after_homing(back)
        self.assertEqual(session.state['iworkoffset'], 54, f'angle 0 not on the base offset: {back!r}')

    def test_fourth_axis_return_to_zero(self):
        """INDEPENDENT: @fourth_axis contract and the i4xIndexMode 1 option doc.

        An index to angle 90 is position 2 (G55 with one offset per position);
        an index back to angle 0 is position 1 again: A0, Z homing first, base
        offset G54. Absorbs test-suite-review test_fourth_axis_is_an_indexing_boundary
        (position bookkeeping; the link revocation is in CamLinkBoundaryTests).
        The 'position' counter itself is PP-internal state; whether SolidCAM
        also sets 'position' around @fourth_axis is unverified
        (pp3-fourth-axis-position), so G55/G54 at the motion is the observable
        contract.
        """
        self._check_fourth_axis_return_to_zero()

    @known_defect('PP-038', facet='abort')
    def test_trig_macro_mode_unchanged_angle_does_not_abort(self):
        """INDEPENDENT: an index whose angle does not change needs no output and
        must not stop the post (pre-bff5ed0 behaviour of the same branch).

        With i4xIndexMode=2 the trig-macro branch runs outside
        'if change(nR1pos)' and calls usr_r1_output without a selected
        direction: 'POST ERROR: A-axis output direction mode ...'.
        """
        session = job_session(i4xIndexMode=2)       # A is at 0 after the first tool change
        try:
            session.same_tool_job(tmatrix=0)
        except UnsupportedGPPL as stopped:
            if 'POST ERROR' in str(stopped):
                self.fail(f'unchanged index angle stops the post: {stopped}')
            raise

    @known_defect('PP-038', facet='syntax')
    def test_trig_macro_mode_emits_sinumerik_code(self):
        """INDEPENDENT: Sinumerik 828D Siemens-mode syntax: no G65 macro call and
        no #-variables; G112 is polar-pole programming, not a work offset.

        i4xIndexMode=2 emits 'G65P777 ...' and 'G0 G112 A=...' for an index.
        """
        session = job_session(i4xIndexMode=2)
        mark = session.mark()
        session.same_tool_job(tmatrix=90)
        blocks = session.blocks(mark)
        fanuc = [word.raw for block in blocks for word in block.words
                 if re.match(r'G65(?!\d)', word.raw) or '#' in word.raw
                 or (word.address == 'G' and word.value in (65, 112))]
        self.assertEqual(fanuc, [], session.text(mark))

    @known_defect('PP-039')
    def test_index_clearance_warning_is_a_comment(self):
        """INDEPENDENT: Sinumerik syntax: free text in a part program must be a
        comment (';...') or an operator message (MSG("...")).

        i4xIndexClearanceMode=1 with tool_z_level below tool_start_plane writes
        '{nl,'WARNING!! ...'}' as a bare block (828D syntax alarm). The
        preceding Print runs through the GpplCompatEngine Print workaround
        (ENGINE-008, Session default).
        """
        session = job_session(i4xIndexClearanceMode=1)
        mark = session.mark()
        session.same_tool_job(tmatrix=90, tool_z_level=20, tool_start_plane=35)
        bare = [block.raw for block in session.blocks(mark) if 'WARNING' in block.code
                and not block.code.startswith('MSG(')]
        self.assertEqual(bare, [], session.text(mark))

    @known_defect('PP-005')
    def test_tmatrix_index_ignores_previous_job_apos(self):
        """INDEPENDENT: geometry: the A position of a tmatrix-indexed job is the
        CoordSys rotation alone (angle_4x_around_x = 90 -> A90).

        UNVERIFIED: depends on SolidCAM keeping the last apos of a simultaneous
        job (here apos=10) into the next job's @tmatrix/@start_of_job; the PP
        itself zeroes apos at tool changes, which suggests it does. The index
        currently sums the stale apos: A=ACN(100).
        """
        session = job_session()
        session.ev('line_5x', ['apos'], apos=10, dir5a='ccw', feed_type='feed_cut')
        mark = session.mark()
        session.same_tool_job(tmatrix=90)
        found = [value for _, value in rotations(session.blocks(mark))]
        if len(found) != 1:
            raise RuntimeError(f'scenario precondition failed (exactly one index expected): {session.text(mark)!r}')
        self.assertEqual(found, [90.0], session.text(mark))


# ---------------------------------------------------------------------------
# CAM-link authorization state machine (d5952a2 / 37ab3b9 / f1803b4)
# ---------------------------------------------------------------------------
class CamLinkBoundaryTests(LinkOracle, unittest.TestCase):
    def _check_initial_state(self, source=None):
        session = Session(source=source)
        state = session.state
        self.assertTrue(state['bindexclearancepending'], 'first rotation must home')
        self.assertFalse(state['bcamlinkretract'])
        self.assertFalse(state['bjobpositioned'])
        self.assertFalse(state['btmatrixindexpending'])
        self.assertNotIn(state['iworkoffset'], SETTABLE_OFFSETS, 'offset must start as a sentinel')
        self.assertNotIn(state['nlastpathworkoffset'], SETTABLE_OFFSETS)
        session.ev('home_number')
        self.assertTrue(session.engine.changed['iworkoffset'], 'the first G54 must be output')

    def test_initial_state_requires_clearance(self):
        """INDEPENDENT: d5952a2 contract plus 3696aa2: a program starts with the
        index clearance armed, no CAM-link authorization, no positioned job and
        a work-offset sentinel that makes the first G54 an output change.

        State pin of @usr_init_gmstates (structural: start_of_job and
        change_tool re-arm the same bits in normal event order). Absorbs
        pp-region-1-setup test_initial_state_forces_first_offset_and_blocks_cam_links.
        """
        self._check_initial_state()

    def _check_boundaries(self, source=None):
        cases = {
            'change_tool': (dict(first_tool=False, tool_number=2, next_tool_number=3), True),
            'start_of_job': ({}, True),
            'end_of_job': ({}, True),
            'tmatrix': (dict(angle_4x_around_x=0), False),
            'fourth_axis': (dict(angle=0), False),
        }
        for event, (values, job_boundary) in cases.items():
            with self.subTest(event=event):
                session = rotated_job(source)
                link_retract(session)
                self.assertTrue(session.state['bcamlinkretract'], 'precondition: confirmed retract')
                # Same work offset as the finished job (what end_of_job records), so a
                # lone start_of_job emits no offset-change rapid.
                session.engine.set(iPworkoffset=session.state['iworkoffset'])
                session.ev(event, **values)
                self.assertFalse(session.state['bcamlinkretract'], f'{event} keeps the CAM-link authorization')
                self.assertTrue(session.state['bindexclearancepending'], f'{event} does not re-arm the clearance')
                if job_boundary:
                    self.assertFalse(session.state['bjobpositioned'], f'{event} keeps the job positioned')

    def test_every_index_or_job_boundary_revokes_link(self):
        """INDEPENDENT: d5952a2/37ab3b9: the authorization lasts 'until a feed
        move or an indexing boundary resets it'.

        Each boundary event revokes it on its own (not relying on the
        end_of_job that usually precedes) and re-arms the index clearance; job
        boundaries also clear the positioned flag. Absorbs test-suite-review
        LinkTrackingRegressions.test_fourth_axis_is_an_indexing_boundary.
        """
        self._check_boundaries()

    def _check_drill_rapid(self, source=None):
        session = rotated_job(source)
        link_retract(session)
        self.assertTrue(session.state['bcamlinkretract'], 'precondition: confirmed retract')
        session.ev('drill', ['xpos', 'ypos'], drill_type='g81', xpos=30, ypos=40, **DRILL_DEFAULTS)
        self.assertFalse(session.state['bcamlinkretract'], 'a drill positioning rapid keeps the link authorization')

    def test_drill_rapid_revokes_link(self):
        """INDEPENDENT: d5952a2: only rapids of the 5x/4x link chain keep the
        authorization; the positioning rapid of a drill cycle is not part of
        the CAM link and must revoke it (flag-level check). Structural: the
        @drill follows the link retract directly; in SolidCAM a drill cycle
        starts its own job, whose @start_of_job already revokes."""
        self._check_drill_rapid()


class CamLinkTransitionTests(LinkOracle, unittest.TestCase):
    BOUNDARIES = {
        'tmatrix': (('tmatrix', {}),),
        'job_boundary': (('end_of_job', {}), ('start_of_job', {})),
        'fourth_axis': (('fourth_axis', dict(angle=90)),),
    }

    def _check_index_boundary_clearance(self, source=None):
        for boundary, events in self.BOUNDARIES.items():
            with self.subTest(boundary=boundary):
                session = rotated_job(source)
                for event, values in events:
                    session.ev(event, **values)
                # XYZ-only rapid (no rotation), cut, then a textbook CAM retract.
                session.ev('move_5x', ['xpos', 'ypos'], xpos=40, ypos=50)
                session.ev('line_5x', ['zpos'], zpos=-2, feed_type='feed_cut')
                link_retract(session, z=30)
                self.assert_rotation_after_homing(rotate(session), boundary)

    def test_index_clearance_survives_xyz_only_rapids(self):
        """INDEPENDENT: d5952a2 'Preserve index clearance while skipping homing
        on confirmed CAM links'.

        After a tmatrix, a job boundary or a @fourth_axis index, the first
        rotation homes Z even if the CAM later shows a straight feed_link
        retract; XYZ-only rapids do not discharge that obligation. The
        'tmatrix' case delivers @tmatrix alone mid-job (structural: SolidCAM
        always follows it with @start_of_job, which re-arms too) to prove that
        @tmatrix re-arms on its own. Absorbs
        pp-region-3-motion IndexClearanceGuardTests
        (test_index_boundary_clearance_survives_straight_cam_retract and its
        two mutation tests, now in ReversionDetectionTests).
        """
        self._check_index_boundary_clearance()

    def _check_descending_or_zero_length(self, source=None):
        scenarios = {
            'after_rapid_climb': [('move_5x', ['zpos'], dict(zpos=50)),
                                  ('line_5x', ['zpos'], dict(zpos=30, feed_type='feed_link'))],
            'after_feed_climb': [('line_5x', ['zpos'], dict(zpos=50, feed_type='feed_cut')),
                                 ('line_5x', ['zpos'], dict(zpos=30, feed_type='feed_link'))],
            'zero_length': [('line_5x', ['feed'], dict(feed=200, feed_type='feed_link'))],
        }
        for name, events in scenarios.items():
            with self.subTest(scenario=name):
                session = rotated_job(source)
                for call, changed, values in events:
                    session.ev(call, changed, **values)
                self.assertFalse(session.state['bcamlinkretract'], name)
                self.assert_rotation_after_homing(rotate(session), name)

    def test_descending_or_zero_length_link_never_authorizes(self):
        """INDEPENDENT: geometry: only an upward Z move is a retract.

        Z tracking must follow rapids and upward cutting moves, not only links:
        a feed_link descending from a rapid climb or a feed climb, or a link
        without Z motion, never authorizes the next rotation. Absorbs
        test-suite-review LinkTrackingRegressions
        (test_descending_link_after_rapid_climb_does_not_bypass_homing,
        test_descending_link_after_feed_climb_does_not_bypass_homing).
        """
        self._check_descending_or_zero_length()

    def _check_non_straight_link(self, source=None):
        for axis, value in (('xpos', 15), ('ypos', 30), ('apos', 8), ('bpos', 5)):
            with self.subTest(axis=axis):
                session = rotated_job(source)
                session.ev('line_5x', ['zpos', axis], zpos=20, feed_type='feed_link', **{axis: value})
                self.assertFalse(session.state['bcamlinkretract'], axis)
                self.assert_rotation_after_homing(rotate(session, a=12), axis)

    def test_non_straight_link_never_authorizes(self):
        """INDEPENDENT: usr_rapid contract 'a CAM-tagged, straight Z retract':
        any X, Y, A or B motion in the link block disqualifies it."""
        self._check_non_straight_link()

    def _check_untracked_motion_event(self, source=None):
        session = rotated_job(source)
        link_retract(session)
        self.assertTrue(session.state['bcamlinkretract'], 'precondition: confirmed retract')
        moved = parse_blocks(session.ev('drill_point', ['zpos'], zpos=-5))
        self.assertEqual([block.axes.get('Z') for block in moved], [-5.0], 'precondition: drill_point moves Z')
        self.assert_rotation_after_homing(rotate(session))

    def test_untracked_motion_event_between_retract_and_rapid_requires_homing(self):
        """INDEPENDENT: d5952a2 prev_command whitelist (only @line_5x/@line_4x/
        @move_5x/@move_4x continue a link).

        @drill_point moves Z without updating the link tracking; the rapid after
        it must not reuse the earlier retract confirmation. Structural pin:
        SolidCAM sends @drill_point only inside a @drill cycle, whose own
        positioning rapid already revokes the link (test_drill_rapid_revokes_link);
        the bare @drill_point isolates the prev_command whitelist.
        """
        self._check_untracked_motion_event()

    ARCS = {
        # Start X10 Y20 Z20 after the retract; centre offset -10 on the plane's
        # first axis, CCW 90; the end point is the DIN G19 rotation (Y->Z). ZX is
        # not used: since 5408e5c every ZX arc stops the post (PP-003,
        # tests/test_zx_arc_guard.py), so there is no link state after it.
        'arc_yz': dict(arc_plane='yz', xcenter_rel=0, ycenter_rel=-10, zcenter_rel=0,
                       xcenter=10, ycenter=10, zcenter=20, xpos=10, ypos=10, zpos=30),
    }

    def _check_arc_in_any_plane(self, source=None):
        for call, values in self.ARCS.items():
            with self.subTest(call=call):
                session = rotated_job(source)
                link_retract(session, z=20)
                self.assertTrue(session.state['bcamlinkretract'], 'precondition: confirmed retract')
                session.ev(call, ['xpos', 'ypos', 'zpos'], arc_direction='ccw', arc_size=90,
                           xstart=10, ystart=20, zstart=20, radius=10, **values)
                self.assertFalse(session.state['bcamlinkretract'], f'{call} keeps the link authorization')
                self.assertEqual(session.state['nlastpathz'], 30, f'{call} endpoint Z not tracked')
                link_retract(session, z=25)            # descends from the arc endpoint Z30
                self.assert_rotation_after_homing(rotate(session), call)

    def test_arc_in_any_plane_revokes_and_tracks_endpoint(self):
        """INDEPENDENT: f1803b4 (tests/ARC_LINK_FINDING.md) generalised to YZ:
        a completed arc revokes the link and records its endpoint Z, so a later
        feed_link that descends from the arc endpoint does not authorize the
        rotation. The XY helix case is test_arc_link_boundary.py; ZX arcs stop
        the post since 5408e5c. The event mixture (a YZ arc inside a 5x job) is
        synthetic; its reachability in a SolidCAM job is not established
        (ARC_LINK_FINDING.md)."""
        self._check_arc_in_any_plane()

    def _check_straight_4x_link(self, source=None):
        session = rotated_4x_job(source)
        link_retract(session, call='line_4x')
        self.assertTrue(session.state['bcamlinkretract'], 'straight 4x link not confirmed')
        self.assert_rotation_without_homing(session.ev('move_4x', ['cpos'], cpos=10), ('ACN', 10.0))

    @covers('PP-018')
    def test_straight_4x_link_keeps_authorization(self):
        """INDEPENDENT: d5952a2 whitelists @line_4x/@move_4x as link events and
        SolidCAM 4x events carry the rotary position in cpos (the author's
        Mach3_4X_Y.gpp writes ' A'cpos): a straight 4x feed_link retract
        authorizes the following rotary move_4x without G75.

        Reachability is UNVERIFIED (X5_job true during SolidCAM 4x events, see
        PP-018); this is the passing companion of the PP-018 canonical test.
        """
        self._check_straight_4x_link()

    @known_defect('PP-018', match='accepted as a straight retract|A rotated without Z homing')
    def test_rotary_4x_link_is_not_a_straight_retract(self):
        """INDEPENDENT: usr_rapid contract 'a CAM-tagged, straight Z retract':
        the 4x link block itself rotates A (A=ACN(8)), so it is not straight
        and the next rotation must home.

        UNVERIFIED: whether SolidCAM 4x feed links carry the rotation in cpos
        with X5_job true (settle with a '@line_4x':5 trace). usr_line checks
        apos/bpos but not cpos.
        """
        session = rotated_4x_job()
        session.ev('line_4x', ['zpos', 'cpos'], zpos=20, cpos=8, feed_type='feed_link')
        self.assertFalse(session.state['bcamlinkretract'], 'rotating 4x link accepted as a straight retract')
        self.assert_rotation_after_homing(session.ev('move_4x', ['cpos'], cpos=10))


class CamLinkGuardTests(LinkOracle, unittest.TestCase):
    """Defence in depth: each documented precondition of the d5952a2 link
    authorization blocks on its own, even if another state bit was left stale
    by a future edit. Structural pins (one injected state bit each)."""

    def _check_rapid_preconditions(self, source=None):
        blockers = {
            'index_clearance_pending': ('move_5x', dict(bIndexClearancePending=True)),
            'tool_change_pending': ('move_5x', dict(bTlchg=True)),
            'first_rapid_of_job': ('move_5x', dict(bFirstRapid=True)),
            'job_not_positioned': ('move_5x', dict(bJobPositioned=False)),
            'not_a_5x_job': ('move_5x', dict(X5_job=False)),
            'offset_changed_since_retract': ('move_5x', dict(nLastPathWorkoffset=55)),
            # rapid_move (3-axis event) runs usr_rapid with bR1useDir5a false.
            'three_axis_rapid_event': ('rapid_move', {}),
        }
        for name, (call, state) in blockers.items():
            with self.subTest(blocker=name):
                session = rotated_job(source)
                link_retract(session)
                self.assertTrue(session.state['bcamlinkretract'], 'precondition: confirmed retract')
                session.engine.set(**state)
                self.assert_rotation_after_homing(session.ev(call, ['apos'], apos=10), name)

    def test_each_rapid_precondition_blocks_authorization(self):
        """INDEPENDENT: the d5952a2 usr_rapid preconditions (5x/4x event, 5x job,
        positioned job, no pending index clearance, no pending tool change, not
        the first rapid of a job, unchanged work offset): each one alone forces
        G75 Z before the rotation."""
        self._check_rapid_preconditions()

    def _check_retract_preconditions(self, source=None):
        blockers = {
            'index_clearance_pending': ('line_5x', dict(bIndexClearancePending=True)),
            'job_not_positioned': ('line_5x', dict(bJobPositioned=False)),
            'not_a_5x_job': ('line_5x', dict(X5_job=False)),
            # @line (3-axis event) runs usr_line with bR1useDir5a false.
            'three_axis_line_event': ('line', {}),
            'offset_changed_since_last_move': ('line_5x', dict(nLastPathWorkoffset=55)),
        }
        for name, (call, state) in blockers.items():
            with self.subTest(blocker=name):
                session = rotated_job(source)
                session.engine.set(**state)
                link_retract(session, call=call)
                self.assertFalse(session.state['bcamlinkretract'], name)

    def test_each_retract_precondition_blocks_authorization(self):
        """INDEPENDENT: the d5952a2 usr_line preconditions (5x/4x event, 5x job,
        positioned job, no pending index clearance, unchanged work offset):
        each one alone prevents a feed_link from confirming a retract."""
        self._check_retract_preconditions()


# ---------------------------------------------------------------------------
# @call_proc (known defect, two facets)
# ---------------------------------------------------------------------------
class SubroutineIndexTests(unittest.TestCase):
    def call_proc_after_link(self):
        session = rotated_job()
        link_retract(session)
        # Subroutine call to an indexed CoordSys (apos 0: the CoordSys angle alone).
        text = session.ev('call_proc', label=100, angle_4x_around_x=90, apos=0)
        if rotations(parse_blocks(text)) == []:
            raise RuntimeError(f'scenario precondition failed (call_proc did not index): {text!r}')
        return session, text

    @known_defect('PP-044', facet='index-boundary')
    def test_call_proc_index_is_an_index_boundary(self):
        """INDEPENDENT (state consistency): @call_proc indexes A through
        usr_4x_index, so like @fourth_axis/@tmatrix it must revoke the CAM-link
        authorization and re-arm the index clearance.

        Not a demonstrated safety bug: the next rapid homes anyway because
        '@call_proc' is not in the prev_command whitelist.
        """
        session, _ = self.call_proc_after_link()
        self.assertEqual((session.state['bcamlinkretract'], session.state['bindexclearancepending']),
                         (False, True), '(link authorization, index clearance pending) after @call_proc')

    @known_defect('PP-044', facet='syntax')
    def test_call_proc_emits_sinumerik_syntax(self):
        """INDEPENDENT: Sinumerik 828D subprogram calls use the program name (or
        CALL/L<n>); M98/H are plain auxiliary functions in Siemens mode, so the
        subprogram is never called. The rotary word must be A, not the literal
        variable name 'cR1' ('G54 cR190').
        """
        _, text = self.call_proc_after_link()
        fanuc = [word.raw for block in parse_blocks(text) for word in block.words
                 if (word.address == 'M' and word.value == 98) or word.address == 'H' or word.raw.startswith('cR1')]
        self.assertEqual(fanuc, [], text)


# ---------------------------------------------------------------------------
# DESIGN pins (owner decisions; @covers only)
# ---------------------------------------------------------------------------
class DesignPinTests(LinkOracle, unittest.TestCase):
    def _check_link_trust(self, source=None):
        # (a) a 0.001 mm feed_link Z step confirms the retract.
        session = rotated_job(source)                        # last path Z = -1
        link_retract(session, z=-0.999)
        self.assertTrue(session.state['bcamlinkretract'], '0.001 mm feed_link step')
        self.assert_rotation_without_homing(rotate(session), ('ACN', 10.0), 'after a 0.001 mm retract')
        # (b) a rapid that descends inside the confirmed link keeps the authorization.
        session = rotated_job(source)
        link_retract(session, z=20)
        descent = parse_blocks(session.ev('move_5x', ['xpos', 'zpos'], xpos=40, zpos=2))
        self.assertEqual([block.axes for block in descent], [{'X': 40.0, 'Z': 2.0}])
        self.assertTrue(session.state['bcamlinkretract'], 'descending link rapid')
        self.assert_rotation_without_homing(rotate(session), ('ACN', 10.0), 'at Z2 after a descending rapid')

    @covers('DESIGN-001')
    def test_cam_link_trusts_any_positive_z_step_and_descending_rapids(self):
        """CHARACTERIZATION of DESIGN-001 (open owner decision; current behaviour).

        The retract height is not checked, only zpos > nLastPathZ: a 0.001 mm
        feed_link step authorizes an unhomed rotation; and 37ab3b9 keeps the
        authorization for the whole contiguous rapid chain, so after a retract
        to Z20 a link rapid down to Z2 still lets A rotate without G75.
        Alternatives: require a minimum retract height (e.g. the job's
        tool_z_level), revoke when a link rapid descends below the confirmed
        retract Z, or keep trusting the collision-checked CAM chain (current).
        Merges pp-weird-hunter test_pin_any_positive_feed_link_z_step_authorizes_unhomed_rotation
        and history-indexing-link-10 (descending rapid).
        """
        self._check_link_trust()

    def _check_index_before_tool_change(self, source=None):
        session = job_session(source)
        mark = session.mark()
        session.next_tool(2, 3, tmatrix=90)
        replayed = session.replay_tail(mark)
        blocks = [block for block, _ in replayed]
        text = session.text(mark)
        rotation = index_of(blocks, is_rotation)
        spindle_off = index_of(blocks, lambda block: 5 in block.m)
        tool_change = index_of(blocks, lambda block: 6 in block.m)
        self.assertTrue(0 <= rotation < spindle_off < tool_change, text)
        state = replayed[rotation][1]
        self.assertEqual((state.spindle, state.tool), (3, 1), 'old tool spinning at the rotation')
        self.assertEqual(len([block for block in blocks if is_optional_stop(block)]), 2, text)
        self.assertEqual(len([block for block in blocks if is_home_z(block)]), 2, text)

    @covers('DESIGN-003')
    def test_deferred_tmatrix_index_runs_before_tool_change(self):
        """CHARACTERIZATION of DESIGN-003 (open owner decision; current behaviour).

        @start_of_job runs the deferred tmatrix index before usr_ct: the table
        rotates with the previous tool still spinning (M3, coolant on), then the
        tool change follows with its own M5/M9, homing and M1, i.e. two M1 and
        two G75 Z for one transition (Z is homed before the rotation, so it is
        safe). Alternative: run the index after the tool change (also removes
        the PP-015/PP-034 couplings). From pp-weird-hunter
        test_pin_tmatrix_index_runs_before_tool_change.
        """
        self._check_index_before_tool_change()


# ---------------------------------------------------------------------------
# Negative validation: focused reversions must fail with AssertionError
# ---------------------------------------------------------------------------
_INDEX_BLOCK = ('    if bTmatrixIndexPending\n        change(cWo) = true\n        change(iWorkoffset) = true\n'
                '        call @usr_4x_index\n        bTmatrixIndexPending = false\n    endif\n')
# 88695c9 put the job-plane restore between @home_number and the deferred index.
_JOB_PLANE = ("    ; Arcs in YZ/ZX leave iMplane at 19/18; restore the job's machining plane for its first motion block.\n"
              '    call @usr_job_plane\n')

# (label, [(old, new), ...], holder class, check method)
REVERSIONS = [
    ('rotary format precision reduced (c03e1b4 format half)',
     [("    nR1pos_f        = '7.3'", "    nR1pos_f        = '7.1'")],
     IndexHistoryTests, '_check_first_program_index'),
    ('c03e1b4: motion mode initialised to 0',
     [('\tiMotionmode = 9999\n    nLlabel', '\tiMotionmode = 0\n    nLlabel')],
     IndexHistoryTests, '_check_first_program_index'),
    ('3696aa2: index before home_number',
     [('    call @home_number\n' + _JOB_PLANE + _INDEX_BLOCK, _JOB_PLANE + _INDEX_BLOCK + '    call @home_number\n')],
     IndexHistoryTests, '_check_first_program_index'),
    ('3696aa2: work offset not forced for the deferred index',
     [('        change(cWo) = true\n        change(iWorkoffset) = true\n        call @usr_4x_index',
       '        call @usr_4x_index')],
     IndexHistoryTests, '_check_index_after_feed_moves'),
    ('c03e1b4: index mode 0 does not force G0',
     [('    iMotionmode = 0\n    if i4xIndexClearanceMode eq 0\n        call @usr_home_rot\n',
       '    if i4xIndexClearanceMode eq 0\n        call @usr_home_rot\n')],
     IndexHistoryTests, '_check_index_after_feed_moves'),
    ('92e2b23: no optional stop before the index (after feed moves)',
     [('        call @usr_optionalstop\n        if i4xIndexMode eq 0 or i4xIndexMode eq 1\n',
       '        if i4xIndexMode eq 0 or i4xIndexMode eq 1\n')],
     IndexHistoryTests, '_check_index_after_feed_moves'),
    ('92e2b23: no optional stop before the index (between jobs)',
     [('        call @usr_optionalstop\n        if i4xIndexMode eq 0 or i4xIndexMode eq 1\n',
       '        if i4xIndexMode eq 0 or i4xIndexMode eq 1\n')],
     IndexHistoryTests, '_check_index_between_jobs'),
    ('index mode 0 does not home before the rotation',
     [("    if i4xIndexClearanceMode eq 0\n        call @usr_home_rot\n    endif\n", '')],
     IndexHistoryTests, '_check_index_between_jobs'),
    ('8d6b044: old tmatrix formula',
     [('\tnR1postmatrix = (-angle_4x_around_x) * iR1dir',
       '\tnR1postmatrix = (-y_angle_const_z - dev_angle_z) * iR1dir')],
     IndexHistoryTests, '_check_tmatrix_index_angle'),
    ('e574716: default index mode 1 (new work offset)',
     [('    i4xIndexMode          = 0 ', '    i4xIndexMode          = 1 ')],
     FourthAxisIndexTests, '_check_default_indexing'),
    ('e574716: default index clearance mode 3 (no branch)',
     [('    i4xIndexClearanceMode = 0 ', '    i4xIndexClearanceMode = 3 ')],
     FourthAxisIndexTests, '_check_default_indexing'),
    ('e574716: fourth_axis does not index',
     [('        apos = 0\n\t\tcall @usr_4x_index\n', '        apos = 0\n')],
     FourthAxisIndexTests, '_check_fourth_axis_single_word'),
    ('719e946: fourth_axis copies the angle into apos',
     [('        apos = 0\n\t\tcall @usr_4x_index',
       '        apos = angle -opposite_z_angle_const_y\n\t\tcall @usr_4x_index')],
     FourthAxisIndexTests, '_check_fourth_axis_single_word'),
    ('719e946: fourth_axis keeps a stale apos',
     [('        apos = 0\n\t\tcall @usr_4x_index', '\t\tcall @usr_4x_index')],
     FourthAxisIndexTests, '_check_fourth_axis_single_word'),
    ('fourth_axis angle 0 does not reset the index position',
     [('    if angle eq 0\n        position = 1', '    if false\n        position = 1')],
     FourthAxisIndexTests, '_check_fourth_axis_return_to_zero'),
    ('initial index clearance not armed',
     [('    bIndexClearancePending = true\n    bCamLinkRetract = false\n    bJobPositioned = false\n'
       '    bPostHomed = false\n',
       '    bIndexClearancePending = false\n    bCamLinkRetract = false\n    bJobPositioned = false\n'
       '    bPostHomed = false\n')],
     CamLinkBoundaryTests, '_check_initial_state'),
    ('change_tool keeps the link',
     [('@change_tool\n    bIndexClearancePending = true\n    bCamLinkRetract = false\n    bJobPositioned = false\n',
       '@change_tool\n')],
     CamLinkBoundaryTests, '_check_boundaries'),
    ('start_of_job keeps the link',
     [('@start_of_job\n    bIndexClearancePending = true\n    bCamLinkRetract = false\n    bJobPositioned = false\n',
       '@start_of_job\n')],
     CamLinkBoundaryTests, '_check_boundaries'),
    ('end_of_job keeps the link',
     [('@end_of_job\n    call @usr_feedmode_94\n    bIndexClearancePending = true\n    bCamLinkRetract = false\n'
       '    bJobPositioned = false\n',
       '@end_of_job\n    call @usr_feedmode_94\n')],
     CamLinkBoundaryTests, '_check_boundaries'),
    ('tmatrix keeps the link',
     [('    bCamLinkRetract = false\n    bTmatrixIndexPending = true\nendp', '    bTmatrixIndexPending = true\nendp')],
     CamLinkBoundaryTests, '_check_boundaries'),
    ('fourth_axis keeps the link',
     [('@fourth_axis\n    bIndexClearancePending = true\n    bCamLinkRetract = false\n', '@fourth_axis\n')],
     CamLinkBoundaryTests, '_check_boundaries'),
    ('an unconfirmed rapid keeps a previous link confirmation',
     [('    ; Used up here; usr_rapid_done renews it while the link goes on.\n    bCamLinkRetract = false\n',
       '')],
     CamLinkBoundaryTests, '_check_drill_rapid'),
    ('any XYZ rapid discharges the index clearance',
     [('    if bRapidRotaryChanged\n        bIndexClearancePending = false\n    endif\n',
       '    bIndexClearancePending = false\n')],
     CamLinkTransitionTests, '_check_index_boundary_clearance'),
    ('pending-clearance guards removed from usr_line and usr_rapid',
     [('if X5_job and bR1useDir5a and bJobPositioned and !bIndexClearancePending',
       'if X5_job and bR1useDir5a and bJobPositioned'),
      ('if !bIndexClearancePending and !bTlchg and !bFirstRapid', 'if !bTlchg and !bFirstRapid')],
     CamLinkTransitionTests, '_check_index_boundary_clearance'),
    ('fourth_axis does not re-arm the index clearance',
     [('@fourth_axis\n    bIndexClearancePending = true\n', '@fourth_axis\n')],
     CamLinkTransitionTests, '_check_index_boundary_clearance'),
    ('rapids do not track Z',
     [('    bJobPositioned = true\n    nLastPathZ = zpos\n', '    bJobPositioned = true\n')],
     CamLinkTransitionTests, '_check_descending_or_zero_length'),
    ('feed moves do not track Z',
     [('    nLastPathZ = zpos\n    nLastPathWorkoffset = iWorkoffset\n    bClimbZValid = true\n'
       '    ; Handle output for line movement (G01)',
       '    nLastPathWorkoffset = iWorkoffset\n    bClimbZValid = true\n    ; Handle output for line movement (G01)')],
     CamLinkTransitionTests, '_check_descending_or_zero_length'),
    ('zero-length link accepted',
     [("feed_type eq 'feed_link' and zpos gt nLastPathZ", "feed_type eq 'feed_link' and zpos ge nLastPathZ")],
     CamLinkTransitionTests, '_check_descending_or_zero_length'),
    ('X motion allowed in a link',
     [('!change(xpos) and !change(ypos) and !change(apos)', '!change(ypos) and !change(apos)')],
     CamLinkTransitionTests, '_check_non_straight_link'),
    ('Y motion allowed in a link',
     [('!change(xpos) and !change(ypos) and !change(apos)', '!change(xpos) and !change(apos)')],
     CamLinkTransitionTests, '_check_non_straight_link'),
    ('A motion allowed in a link',
     [('!change(ypos) and !change(apos) and !change(bpos)', '!change(ypos) and !change(bpos)')],
     CamLinkTransitionTests, '_check_non_straight_link'),
    ('B motion allowed in a link',
     [('!change(apos) and !change(bpos)', '!change(apos)')],
     CamLinkTransitionTests, '_check_non_straight_link'),
    ('prev_command ignored',
     [("            if prev_command eq '@line_5x' or prev_command eq '@line_4x' or "
       "prev_command eq '@move_5x' or prev_command eq '@move_4x'", '            if true')],
     CamLinkTransitionTests, '_check_untracked_motion_event'),
    ('arc keeps the link authorization',
     [('    bCamLinkRetract = false\n    nLastPathZ = zpos\n    nLastPathWorkoffset = iWorkoffset\n'
       '    bClimbZValid = true\n    if bFeedoutput',
       '    nLastPathZ = zpos\n    nLastPathWorkoffset = iWorkoffset\n    bClimbZValid = true\n    if bFeedoutput')],
     CamLinkTransitionTests, '_check_arc_in_any_plane'),
    ('arc does not track its endpoint Z',
     [('    bCamLinkRetract = false\n    nLastPathZ = zpos\n    nLastPathWorkoffset = iWorkoffset\n'
       '    bClimbZValid = true\n    if bFeedoutput',
       '    bCamLinkRetract = false\n    nLastPathWorkoffset = iWorkoffset\n    bClimbZValid = true\n    if bFeedoutput')],
     CamLinkTransitionTests, '_check_arc_in_any_plane'),
    ('4x events not whitelisted',
     [("prev_command eq '@line_5x' or prev_command eq '@line_4x' or "
       "prev_command eq '@move_5x' or prev_command eq '@move_4x'",
       "prev_command eq '@line_5x' or prev_command eq '@move_5x'")],
     CamLinkTransitionTests, '_check_straight_4x_link'),
    ('usr_rapid: X5_job guard removed',
     [('if X5_job and bR1useDir5a and bJobPositioned and bCamLinkRetract',
       'if bR1useDir5a and bJobPositioned and bCamLinkRetract')],
     CamLinkGuardTests, '_check_rapid_preconditions'),
    ('usr_rapid: bR1useDir5a guard removed',
     [('if X5_job and bR1useDir5a and bJobPositioned and bCamLinkRetract',
       'if X5_job and bJobPositioned and bCamLinkRetract')],
     CamLinkGuardTests, '_check_rapid_preconditions'),
    ('usr_rapid: bJobPositioned guard removed',
     [('if X5_job and bR1useDir5a and bJobPositioned and bCamLinkRetract',
       'if X5_job and bR1useDir5a and bCamLinkRetract')],
     CamLinkGuardTests, '_check_rapid_preconditions'),
    ('usr_rapid: pending clearance guard removed',
     [('if !bIndexClearancePending and !bTlchg and !bFirstRapid', 'if !bTlchg and !bFirstRapid')],
     CamLinkGuardTests, '_check_rapid_preconditions'),
    ('usr_rapid: tool change guard removed',
     [('if !bIndexClearancePending and !bTlchg and !bFirstRapid', 'if !bIndexClearancePending and !bFirstRapid')],
     CamLinkGuardTests, '_check_rapid_preconditions'),
    ('usr_rapid: first rapid guard removed',
     [('if !bIndexClearancePending and !bTlchg and !bFirstRapid', 'if !bIndexClearancePending and !bTlchg')],
     CamLinkGuardTests, '_check_rapid_preconditions'),
    ('usr_rapid: work offset guard removed',
     [(' and !bFirstRapid and nLastPathWorkoffset eq iWorkoffset\n', ' and !bFirstRapid\n')],
     CamLinkGuardTests, '_check_rapid_preconditions'),
    ('usr_line: X5_job guard removed',
     [('if X5_job and bR1useDir5a and bJobPositioned and !bIndexClearancePending',
       'if bR1useDir5a and bJobPositioned and !bIndexClearancePending')],
     CamLinkGuardTests, '_check_retract_preconditions'),
    ('usr_line: bR1useDir5a guard removed',
     [('if X5_job and bR1useDir5a and bJobPositioned and !bIndexClearancePending',
       'if X5_job and bJobPositioned and !bIndexClearancePending')],
     CamLinkGuardTests, '_check_retract_preconditions'),
    ('usr_line: bJobPositioned guard removed',
     [('if X5_job and bR1useDir5a and bJobPositioned and !bIndexClearancePending',
       'if X5_job and bR1useDir5a and !bIndexClearancePending')],
     CamLinkGuardTests, '_check_retract_preconditions'),
    ('usr_line: pending clearance guard removed',
     [('if X5_job and bR1useDir5a and bJobPositioned and !bIndexClearancePending',
       'if X5_job and bR1useDir5a and bJobPositioned')],
     CamLinkGuardTests, '_check_retract_preconditions'),
    ('usr_line: work offset guard removed',
     [(' and !bIndexClearancePending and nLastPathWorkoffset eq iWorkoffset\n', ' and !bIndexClearancePending\n')],
     CamLinkGuardTests, '_check_retract_preconditions'),
    # Policy changes the DESIGN pins must notice.
    ('DESIGN-001 alternative: retract must reach the tool Z level',
     [("feed_type eq 'feed_link' and zpos gt nLastPathZ",
       "feed_type eq 'feed_link' and zpos gt nLastPathZ and zpos ge tool_z_level")],
     DesignPinTests, '_check_link_trust'),
    ('DESIGN-001 alternative: a descending link rapid revokes',
     [('    if bCamLinkRapid\n        bCamLinkRetract = true',
       '    if bCamLinkRapid and zpos ge nLastPathZ\n        bCamLinkRetract = true')],
     DesignPinTests, '_check_link_trust'),
    ('DESIGN-003 alternative: index after the tool change',
     [('    call @home_number\n' + _JOB_PLANE + _INDEX_BLOCK, '    call @home_number\n' + _JOB_PLANE),
      ('            call @usr_ct\n            bTlchg = false\n',
       '            call @usr_ct\n' + textwrap.indent(_INDEX_BLOCK, '        ') + '            bTlchg = false\n')],
     DesignPinTests, '_check_index_before_tool_change'),
]


class ReversionDetectionTests(unittest.TestCase):
    def test_focused_reversions_fail_with_assertion(self):
        """INDEPENDENT: negative validation. Each focused reversion of a fixed
        behaviour (or alternative of a DESIGN policy) is applied in memory and
        its guarding check must fail with AssertionError; an interpreter error
        propagates as a test error and a surviving mutant fails this test.
        A stale anchor raises StaleAnchor (support.mutation)."""
        for label, edits, holder, check in REVERSIONS:
            with self.subTest(reversion=label):
                mutant = None
                for old, new in edits:
                    mutant = mutate(old, new, source=mutant)
                # A fresh, not running instance: its subTest blocks re-raise.
                assert_detected(self, getattr(holder(), check), mutant, label)


if __name__ == '__main__':
    unittest.main()
