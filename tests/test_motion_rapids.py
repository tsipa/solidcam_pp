"""Rapids and approach order, homing restore, feed-emulated rapids, Z output
precision and the rotary feed mode of Gmill_540v_4x.gpp (@usr_rapid,
@usr_line, @move_5x/@line_5x/@line_4x, @change_ref_point).

Area D sentinel (tests/support/defects.py AREAS['D']). Every test drives a
SolidCAM-like Session (tests/support/session.py: @init_post, VMID defaults,
the real first tool change) and asserts on parsed blocks (support.nc) and on
the Sinumerik modal state replayed over the whole program (support.modal), so
'X15' never matches 'X150' and a modal G0/G1/F/TRC state is judged the way the
control executes it.

Each test docstring states its oracle: INDEPENDENT (Sinumerik 828D semantics,
machining practice, the PP's own option documentation, commit intent) or
CHARACTERIZATION (an intentional current behaviour; here only the DESIGN-002
approach policy). Suspected PP defects are @known_defect tests that assert the
correct behaviour; this suite never edits the GPP. Defects fixed by the owner's
GPP commits (PP-001, PP-013, PP-049; DESIGN-002 decided) keep their former
canonical tests as regression guards marked @covers.

Modelling assumptions shared by these tests
* SolidCAM flags only the coordinates that change in an event (the real shit2
  trace flags line_5x with zpos/feed only). support.session.event() therefore
  resets the CAM motion flags (xpos ypos zpos apos bpos cpos feed spin) at every
  event. A PP fix that sets change(xpos)=true at homing time and relies on that
  flag surviving into a LATER event whose CAM X is unchanged is rejected by this
  harness. Whether SolidCAM keeps such a PP-set flag is part of PP-001's settle
  evidence; the PP-001 tests demand that X/Y are re-programmed within the event
  that homes them or by the PP's own state (345cb49 uses a global 'homed' flag,
  bPostHomed).
* The first feed move of a job flags feed as changed (Session.cut convention).
"""
import math
import unittest

from pp_tests.engine import UnsupportedGPPL
from support import (Session, assert_detected, covers, known_defect, mutate, parse_blocks, replay,
                     state_before)

# CAM rapid feed emulation: usr_ip_useroptions 'nRapidfeed = 650. ;Set your value for
# Max Feed in G1 (Used with Non-Sync'd Rapid Moves)'.
RAPID_FEED_EMULATED = 650
XYZ = ('xpos', 'ypos', 'zpos')


def first_job(source=None, options=None, **cam):
    """Session after the program start and the first tool change (tool 1, job 'op1')."""
    session = Session(source=source, options=options, **cam)
    session.first_tool()
    return session


def program_replay(session, since):
    """(whole-program modal replay, index of the first block emitted at/after event `since`).

    The whole program is replayed so modal G0/G1, F, plane and TRC come from the
    real preceding blocks. Counting from the end also handles an event whose
    first fragment continues the previous block.
    """
    replayed = replay(session.text())
    return replayed, len(replayed) - len(parse_blocks(session.text(since)))


def raw(replayed, first=0):
    return [block.raw for block, _ in replayed[first:]]


def emit_xy_arc(session, start, center, size, direction='ccw'):
    """Deliver one XY @arc event from `start` (current position) around `center`."""
    angle = math.radians(size if direction == 'ccw' else -size)
    vx, vy = start[0] - center[0], start[1] - center[1]
    end = (center[0] + vx * math.cos(angle) - vy * math.sin(angle),
           center[1] + vx * math.sin(angle) + vy * math.cos(angle), start[2])
    values = dict(arc_plane='xy', arc_direction=direction, arc_size=size, radius=math.hypot(vx, vy),
                  xstart=start[0], ystart=start[1], zstart=start[2],
                  xcenter=center[0], ycenter=center[1], zcenter=start[2],
                  xcenter_rel=center[0] - start[0], ycenter_rel=center[1] - start[1], zcenter_rel=0,
                  xpos=end[0], ypos=end[1], zpos=end[2])
    return session.ev('arc', ('xpos', 'ypos'), **values)


class MotionModeTests(unittest.TestCase):
    """G0/G1 modality of the first feed moves after a rapid (TSR-01)."""

    FEEDS = ((('zpos', 'feed'), dict(zpos=-2, feed=500), {'Z': -2}, 500),
             (('xpos', 'ypos'), dict(xpos=15, ypos=-7.5), {'X': 15, 'Y': -7.5}, 500),
             (('xpos', 'feed'), dict(xpos=1.5, feed=250), {'X': 1.5}, 250))

    def check_feed_moves_after_rapid(self, source=None):
        session = first_job(source)
        session.ev('move_5x', XYZ, xpos=40, ypos=50, zpos=5)
        marks = []
        for changed, values, _, _ in self.FEEDS:
            marks.append(session.mark())
            session.ev('line_5x', changed, feed_type='feed_cut', **values)
        replayed = replay(session.text())
        for mark, (_, _, axes, feed) in zip(marks, self.FEEDS):
            moves = session.event_replay(mark, replayed)
            self.assertEqual(len(moves), 1, f'one block per feed event expected: {raw(replayed)}')
            block, state = moves[0]
            self.assertEqual(block.axes, axes, f'exact axis words: {block.raw!r}')
            self.assertEqual(state.motion, 1, f'feed move {block.raw!r} executes in G{state.motion}: '
                                              f'{raw(replayed)}')
            self.assertEqual(state.feed, feed, f'modal feed after {block.raw!r}')

    def test_feed_move_after_rapid_emits_g1(self):
        """INDEPENDENT: Sinumerik G0/G1 belong to modal group 1, so a feed move after a
        G0 without G1 runs at rapid traverse (TSR-01). The plunge after the job's first
        rapid must execute in G1 at the CAM feed, and following moves keep G1 and their
        exact words (X15 must not be satisfied by X150)."""
        self.check_feed_moves_after_rapid()

    def test_dropping_g1_after_rapid_is_detected(self):
        """INDEPENDENT: deleting 'iMotionmode = 1' in @usr_line (TSR-01 mutant, survived the
        original suite) must fail the modal-G1 check with AssertionError."""
        mutant = mutate('    iMotionmode = 1\n    ; ---- 4x\n    ; A rotating G1 block',
                        '    ; ---- 4x\n    ; A rotating G1 block')
        assert_detected(self, self.check_feed_moves_after_rapid, mutant, 'usr_line without iMotionmode = 1')


def second_job_first_rapid(previous_z, target, source=None):
    """Job 1 ends at Z previous_z; same-tool job 2 (same A, same offset) starts with a rapid."""
    session = first_job(source)
    session.cut(10, 20, previous_z, -1)
    session.same_tool_job(job_name='op2')
    mark = session.mark()
    session.ev('move_5x', XYZ, xpos=target[0], ypos=target[1], zpos=target[2])
    return session, mark


def first_index(replayed, first, predicate):
    return next((index for index in range(first, len(replayed)) if predicate(replayed[index][1])), -1)


class FirstRapidTests(unittest.TestCase):
    """First rapid of a same-tool job (@start_of_job sets bFirstRapid, no retract)."""

    def check_descending_first_rapid(self, source=None):
        session, mark = second_job_first_rapid(50, (100, 60, 5), source)
        replayed, first = program_replay(session, mark)
        xy = first_index(replayed, first, lambda state: state.position[:2] == (100, 60))
        down = first_index(replayed, first, lambda state: state.position[2] == 5)
        self.assertGreaterEqual(xy, 0, f'XY target X100 Y60 missing: {raw(replayed, first)}')
        self.assertGreaterEqual(down, 0, f'Z target Z5 missing: {raw(replayed, first)}')
        at_xy = replayed[xy][1]
        self.assertTrue('Z' in at_xy.homed or (at_xy.position[2] is not None and at_xy.position[2] >= 50),
                        f'descending first rapid plunges while traversing: {raw(replayed, first)}')
        self.assertLess(xy, down, f'descending first rapid moved Z before XY: {raw(replayed, first)}')

    def test_first_rapid_of_same_tool_job_reaches_xy_before_descending(self):
        """INDEPENDENT: a rapid approach going DOWN traverses X/Y at the current height and
        descends last (machining practice; the GPP applies it to the first move of a job,
        bFirstMove). The CAM target must be reached, i.e. the tool-change branch of
        @usr_rapid, which writes no X/Y, must not swallow it. Only the descending case is
        asserted, so the PP-013 order of an ASCENDING first rapid is not pinned."""
        self.check_descending_first_rapid()

    def test_live_first_rapid_in_toolchange_branch_is_detected(self):
        """INDEPENDENT: removing 'bFirstRapid = false' (@usr_rapid, after the HVH block) makes
        the first rapid enter the tool-change branch, which drops the X/Y target; the
        guard must fail with AssertionError (pp3-dead-branches mutant)."""
        mutant = mutate('        bFirstRapid = false\n    endif\n    bRapidRotaryChanged',
                        '    endif\n    bRapidRotaryChanged')
        assert_detected(self, self.check_descending_first_rapid, mutant, 'bFirstRapid kept live')

    @covers('PP-013')
    def test_same_tool_job_climbs_before_xy_traverse(self):
        """INDEPENDENT: a rapid going UP must climb before it traverses (machining practice:
        the XY traverse happens at the higher of the two heights). Job 1 ends at Z5, the
        same-tool job 2 starts with a rapid to X100 Y100 Z50; nothing retracts between
        same-tool, same-offset, same-A jobs, so the XY traverse must start at Z >= 50 or
        after a Z homing. Regression guard of PP-013 (fixed in 49f8b80; before it the
        bFirstMove branch of @usr_rapid always wrote XY before Z)."""
        session, mark = second_job_first_rapid(5, (100, 100, 50))
        replayed, first = program_replay(session, mark)
        xy = first_index(replayed, first, lambda state: state.position[:2] == (100, 100))
        self.assertGreaterEqual(xy, 0, f'XY target missing: {raw(replayed, first)}')
        before = state_before(replayed, xy)
        climbed = 'Z' in before.homed or (before.position[2] is not None and before.position[2] >= 50)
        self.assertTrue(climbed, f'XY traverse from Z{before.position[2]} before climbing to Z50: '
                                 f'{raw(replayed, first)}')


def xy_lost_after_homing(replayed, first):
    """Reason string if X/Y stay at the G75 fixed point when the tool descends or cuts.

    After the last 'G75 ... X1=0 Y1=0' at or after `first`, every block that programs
    Z (leaving the Z reference point) or cuts (G1/G2/G3 motion) must leave X and Y
    re-programmed (Sinumerik G75: the axes sit at the fixed point until programmed
    again under G90). Returns None when no X/Y homing occurs (nothing to restore).
    """
    homings = [index for index in range(first, len(replayed)) if {'X', 'Y'} <= replayed[index][0].homing_axes]
    if not homings:
        return None
    for index in range(homings[-1] + 1, len(replayed)):
        block, state = replayed[index]
        cuts = block.is_motion and state.motion in (1, 2, 3)
        if 'Z' in block.axes or cuts:
            lost = sorted({'X', 'Y'} & state.homed)
            if lost:
                return f'{lost} still at the G75 fixed point at {block.raw!r}: {raw(replayed, first)}'
            return None
    return None


class HomingRestoreTests(unittest.TestCase):
    """PP-inserted G75 Y1=0 X1=0 homing (every default sHomestr*) and X/Y restore."""

    @covers('PP-001')
    def test_xy_reestablished_after_homing_in_rotary_rapid(self):
        """INDEPENDENT: Sinumerik G75 X1=0 Y1=0 moves X/Y to the machine fixed point; under
        G90 an axis that is not programmed again stays there. Realistic trigger (TSR-04
        verifier probe): A turns about X, so a non-link rotary rapid keeps the CAM X.
        Sequence: cut at X12, rapid retract Z50, rotary rapid A90 with a new Y and Z40 (X
        unchanged, not flagged), approach Z10, plunge. X12 must be re-programmed before the
        tool leaves the Z reference. Modelling assumption (module docstring): CAM motion
        flags are reset per event, so a sticky change(xpos)=true set at homing time is not
        accepted as a fix by this harness. Regression guard of PP-001 facet rotary-rapid
        (fixed in 345cb49)."""
        session = first_job()
        mark = session.mark()
        session.ev('move_5x', XYZ, xpos=12, ypos=23, zpos=50)
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=300, feed_type='feed_cut')
        session.ev('line_5x', ('ypos',), ypos=-5, feed_type='feed_cut')
        session.ev('move_5x', ('zpos',), zpos=50)
        session.ev('move_5x', ('apos', 'ypos', 'zpos'), apos=90, ypos=0, zpos=40)
        session.ev('move_5x', ('zpos',), zpos=10)
        session.ev('line_5x', ('zpos',), zpos=-1, feed_type='feed_cut')
        replayed, first = program_replay(session, mark)
        reason = xy_lost_after_homing(replayed, first)
        if reason:
            self.fail(reason)

    @covers('PP-001')
    def test_y_reestablished_after_job_start_index_homing(self):
        """INDEPENDENT: same G75 rule at a job boundary. Realistic same-Y scenario (TSR-04
        verifier): both jobs work on the rotary centreline Y0; job 2 is indexed by @tmatrix
        (A90, homed by @usr_4x_index in @start_of_job) and its first rapid changes only X
        and Z, so SolidCAM does not flag Y (assumption: SolidCAM flags only changed
        coordinates, module docstring). Y0 must be re-programmed before the tool descends.
        Regression guard of PP-001 facet index (fixed in 345cb49)."""
        session = first_job()
        session.cut(10, 0, 50, -1)
        mark = session.mark()
        session.same_tool_job(tmatrix=90, job_name='op2')
        session.ev('move_5x', ('xpos', 'zpos'), xpos=30, zpos=20)
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=300, feed_type='feed_cut')
        replayed, first = program_replay(session, mark)
        reason = xy_lost_after_homing(replayed, first)
        if reason:
            self.fail(reason)


# @usr_rapid: 3e0c345 put Z in its own block when the rapid returns from post-inserted homing.
HOMED_RETURN_SPLIT = """                        if bHomedReposition
                            ; Coming from the homing position: traverse XY at the homed Z, then plunge in Z.
                            call @usr_emulated_rapid_feed
                            skipline = true
                            {nb,'Z'zpos ' ' }
                            skipline = true
                        else
                            {'Z'zpos ' ' }
                        endif
"""


class ApproachAfterHomingTests(unittest.TestCase):
    """Approach after the G75 homing of a non-link rotary rapid (DESIGN-002)."""

    def first_link_of_job(self, source=None):
        session = first_job(source)
        session.cut(10, 20, 50, -1)
        session.same_tool_job(job_name='op2')
        session.ev('move_5x', XYZ, xpos=40, ypos=50, zpos=30)
        session.ev('line_5x', ('zpos', 'feed'), zpos=2, feed=300, feed_type='feed_cut')
        session.ev('line_5x', ('xpos',), xpos=80, feed_type='feed_cut')
        session.ev('line_5x', ('zpos',), zpos=30, feed_type='feed_link')
        mark = session.mark()
        session.ev('move_5x', ('apos',) + XYZ, apos=45, xpos=40, ypos=10, zpos=8)
        return session, mark, {'X': 40, 'Y': 10, 'Z': 8}

    def after_cutting_retract(self, source=None):
        session = first_job(source)
        session.cut(10, 20, 50, -1)
        session.ev('line_5x', ('zpos',), zpos=20, feed_type='feed_cut')
        mark = session.mark()
        session.ev('move_5x', ('apos',) + XYZ, apos=10, xpos=50, ypos=60, zpos=5)
        return session, mark, {'X': 50, 'Y': 60, 'Z': 5}

    @covers('DESIGN-002')
    def test_homed_rotary_rapid_returns_xy_then_z(self):
        """CHARACTERIZATION of the owner decision on DESIGN-002 (3e0c345): after
        'G75 Z1=0.', 'G75 Y1=0 X1=0' and the A rotation, @usr_rapid traverses X/Y at the
        homed Z in one G0 block and then descends Z in its own block (as the first move of a
        job does), instead of the former single diagonal 'X.. Y.. Z..' block from the fixed
        point, which was safe only with linear G0 interpolation (MD20730 G0_LINEAR_MODE /
        RTLION) and a target Z above every obstacle. Scenarios: the first rotary link of a
        job (index clearance pending) and a rotary rapid after a cutting retract. The stale
        @usr_rapid comment 'XYZ not allowed together on a single line' is not used as an
        oracle (the shit2 fixture expects XYZ links on one line)."""
        for name in ('first_link_of_job', 'after_cutting_retract'):
            with self.subTest(scenario=name):
                self.check_homed_return(name)

    def check_homed_return(self, scenario, source=None):
        session, mark, target = getattr(self, scenario)(source)
        blocks = parse_blocks(session.text(mark))
        shown = [b.raw for b in blocks]
        homing = [index for index, block in enumerate(blocks) if {'X', 'Y'} <= block.homing_axes]
        self.assertEqual(len(homing), 1, shown)
        after = blocks[homing[0] + 1:]
        self.assertEqual(len(after), 3, f'return after homing is not A, XY, Z: {shown}')
        self.assertIsNotNone(after[0].rotary('A'), shown)
        self.assertEqual(after[0].axes, {}, shown)
        self.assertEqual(after[1].axes, {'X': target['X'], 'Y': target['Y']}, shown)
        self.assertEqual(after[2].axes, {'Z': target['Z']}, shown)

    def test_3e0c345_reversion_is_detected(self):
        """INDEPENDENT: negative validation of the DESIGN-002 pin. Reverting 3e0c345 in
        memory (Z stays on the X/Y block after post-inserted homing) must make
        check_homed_return fail with AssertionError in both scenarios."""
        mutant = mutate(HOMED_RETURN_SPLIT, "                        {'Z'zpos ' ' }\n")
        for name in ('first_link_of_job', 'after_cutting_retract'):
            assert_detected(self, lambda source: self.check_homed_return(name, source), mutant,
                            f'3e0c345 reverted ({name})', match='not A, XY, Z')


class FeedEmulatedRapidTests(unittest.TestCase):
    """bSyncdrapid=false on '3-d model' jobs emulates rapids as G1 F<nRapidfeed>."""

    @staticmethod
    def emulated_session(source=None):
        return first_job(source, options=dict(bSyncdrapid=False), job_type='3-d model')

    def check_feed_restored(self, cut, source=None):
        session = self.emulated_session(source)
        session.ev('move_5x', XYZ, xpos=10, ypos=23, zpos=50)
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=100, feed_type='feed_cut')
        session.ev('line_5x', ('xpos',), xpos=12, feed_type='feed_cut')
        rapid = session.mark()
        session.ev('move_5x', ('zpos',), zpos=40)
        after = session.mark()
        if cut == 'line':
            session.ev('line_5x', ('zpos',), zpos=5, feed_type='feed_cut')
        else:
            try:
                emit_xy_arc(session, (12, 23, 40), (2, 23, 40), 90)
            except UnsupportedGPPL as exc:   # a PP stop on this valid arc is a failure, not an error
                if 'POST ERROR' in str(exc):
                    self.fail(f'the PP stopped on a valid arc: {exc}')
                raise
        replayed, _ = program_replay(session, rapid)
        _, cut_first = program_replay(session, after)
        rapid_state = replayed[cut_first - 1][1]
        self.assertEqual((rapid_state.motion, rapid_state.feed), (1, RAPID_FEED_EMULATED),
                         f'emulated rapid is not G1 F{RAPID_FEED_EMULATED}: {raw(replayed)}')
        self.assertEqual(replayed[-1][1].feed, 100,
                         f'{cut}: cutting feed not restored after the G1 F650 rapid: {raw(replayed, cut_first - 1)}')

    def test_cut_after_feed_emulated_rapid_restores_feed(self):
        """INDEPENDENT: usr_ip_useroptions documents nRapidfeed as 'Max Feed in G1 (Used with
        Non-Sync'd Rapid Moves)'; F is modal on Sinumerik, so the next cutting move must
        re-establish its own feed (F100) even when the CAM feed value did not change,
        otherwise it cuts at F650 (pp3-feed-restore-coverage)."""
        for cut in ('line', 'arc'):
            with self.subTest(cut=cut):
                self.check_feed_restored(cut)

    def test_line_feed_restore_removal_is_detected(self):
        """INDEPENDENT: deleting change(feed)=true from the bFeedoutput branch of @usr_line
        must fail the line case with AssertionError."""
        mutant = mutate('    if bFeedoutput\n        change(feed) = true\n        bFeedoutput  = false\n    endif\n'
                        ';    if change(iFeedType)',
                        '    if bFeedoutput\n        bFeedoutput  = false\n    endif\n;    if change(iFeedType)')
        assert_detected(self, lambda source: self.check_feed_restored('line', source), mutant,
                        '@usr_line feed restore removed')

    def test_arc_feed_restore_removal_is_detected(self):
        """INDEPENDENT: deleting change(feed)=true from the bFeedoutput branch of @usr_arc
        must fail the arc case with AssertionError."""
        mutant = mutate('    nLastPathWorkoffset = iWorkoffset\n    bClimbZValid = true\n    if bFeedoutput\n'
                        '        change(feed) = true\n',
                        '    nLastPathWorkoffset = iWorkoffset\n    bClimbZValid = true\n    if bFeedoutput\n')
        assert_detected(self, lambda source: self.check_feed_restored('arc', source), mutant,
                        '@usr_arc feed restore removed')

    @known_defect('PP-023')
    def test_every_g1_block_of_emulated_rapid_moves_at_rapid_feed(self):
        """INDEPENDENT: every G1 block the post writes for a rapid must move at nRapidfeed
        (usr_ip_useroptions: 'Max Feed in G1 (Used with Non-Sync'd Rapid Moves)'); F is
        modal, so a G1 rapid block without F inherits the cutting feed, or has no feed at
        all at program start ('feedrate not programmed', cf. c03e1b4). G75 blocks are not
        motion blocks here (fixed-point approach at rapid). Checked for every rapid of a
        program: the tool-change positioning, the job's first move and a non-link rotary
        rapid after a cutting retract. Policy note: 'G1 G17 G90 G54 A=DC(0)', the first-move
        'X10 Y23' and the rotary 'G1 A=ACN(10)' fail under both Session flag policies (the
        split return after the homing carries F650 on 'X50 Y60'); the first-move 'Z50'
        lacks F only under flags='clear' (with 'persist' the pending init_post
        change(nRapidfeed) prints 'Z50 F650'), so that item depends on ENGINE-001 and is not
        needed for the failure."""
        session = self.emulated_session()
        session.ev('move_5x', XYZ, xpos=10, ypos=23, zpos=50)
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=100, feed_type='feed_cut')
        session.ev('line_5x', ('xpos',), xpos=12, feed_type='feed_cut')
        session.ev('line_5x', ('zpos',), zpos=20, feed_type='feed_cut')
        session.ev('move_5x', ('apos',) + XYZ, apos=10, xpos=50, ypos=60, zpos=30)
        problems = []
        replayed = replay(session.text())
        for mark, (name, _) in enumerate(session.log):
            if name not in ('start_of_job', 'move_5x', 'rapid_move'):
                continue
            for block, state in session.event_replay(mark, replayed):
                if block.is_motion and state.motion == 1 and state.feed != RAPID_FEED_EMULATED:
                    problems.append(f'@{name}: {block.raw!r} runs at F{state.feed}')
        if problems:
            self.fail(f'emulated rapid blocks not at F{RAPID_FEED_EMULATED}: {"; ".join(problems)} in {raw(replayed)}')


def decimals_of(block, address):
    word = block.find(address)[0]
    return len(word.raw.split('.', 1)[1]) if '.' in word.raw else 0


class ZPrecisionTests(unittest.TestCase):
    """Coordinate output precision after dc916d7 (xpos_f/ypos_f/zpos_f '8.5', VMID
    MovementPrecision=5)."""

    @known_defect('PP-006', facet='first-rapid', match='Z has')
    def test_z_keeps_coordinate_precision_after_first_rapid(self):
        """INDEPENDENT: commit dc916d7 raised the coordinate formats to 8.5 together with VMID
        MovementPrecision 4 -> 5 so that arc end points are written consistently; Z must be
        rounded to 5 decimals like X. The program's first rapid (tool-change positioning,
        bFirstVert branch of @usr_rapid) sets zpos_f='5.4', so the cutting moves of job 1
        print Z with 4 decimals (also visible in the real shit2 trace: Z15.8333 next to
        X192.14583)."""
        session = first_job()
        session.ev('move_5x', XYZ, xpos=1, ypos=2, zpos=30)
        mark = session.mark()
        session.ev('line_5x', ('xpos', 'zpos', 'feed'), xpos=1.234567, zpos=1.234567, feed=300,
                   feed_type='feed_cut')
        block = parse_blocks(session.text(mark))[0]
        self.assertAlmostEqual(block.get('X'), 1.23457, delta=1e-9, msg=block.raw)
        self.assertAlmostEqual(block.get('Z'), 1.23457, delta=1e-9,
                               msg=f'Z has {decimals_of(block, "Z")} decimals, X {decimals_of(block, "X")}: {block.raw!r}')

    @known_defect('PP-006', facet='tool-change', match='Z has')
    def test_z_keeps_coordinate_precision_after_tool_change(self):
        """INDEPENDENT: same dc916d7 / VMID MovementPrecision=5 oracle after a NON-FIRST tool
        change: the tool change does not restore the coordinate format (and
        @usr_ct_before_notfirsttool re-applies zpos_f='5.4' whenever bVertical/bFirstVert
        is set), so the first move of tool 2 prints Z with 4 decimals."""
        session = first_job()
        session.cut(10, 20, 50, -1)
        session.next_tool(2, 3)
        mark = session.mark()
        session.ev('move_5x', XYZ, xpos=1.23456, ypos=2.34567, zpos=30.45678)
        blocks = parse_blocks(session.text(mark))
        z_block = next(block for block in blocks if 'Z' in block.axes)
        self.assertEqual(blocks[0].axes, {'X': 1.23456, 'Y': 2.34567}, [b.raw for b in blocks])
        self.assertAlmostEqual(z_block.get('Z'), 30.45678, delta=1e-9,
                               msg=f'Z has {decimals_of(z_block, "Z")} decimals: {[b.raw for b in blocks]}')


class RotaryFeedModeTests(unittest.TestCase):
    """Feed of simultaneous rotary moves (@line_4x/@line_5x with an A word)."""

    @covers('PP-049')
    def test_rotary_feed_moves_use_the_documented_inverse_time_mode(self):
        """INDEPENDENT: usr_ip_useroptions documents i4xFeedMode=1 as 'Inverse Time
        FeedRate' (Sinumerik G93). Under G94 a block that moves only A reads F as deg/min,
        and in an X+A block F is the path feed of the linear axes only, so the mm/min CAM
        feed is wrong by a geometry-dependent factor (critic-04). Every G1 block with an A
        word must therefore run under G93. UNVERIFIED: assumes SolidCAM passes a linear
        mm/min feed to @line_4x/@line_5x and the machine keeps the default FGROUP/FGREF.
        Regression guard of PP-049 (fixed in 9f48a3a/f0ffada; the F values are checked by
        tests/test_inverse_time_feed.py)."""
        session = first_job()
        self.assertEqual(session.state['i4xfeedmode'], 1, 'the shipped option no longer selects inverse time')
        session.ev('move_5x', XYZ, xpos=10, ypos=0, zpos=50)
        session.ev('line_5x', ('zpos', 'feed'), zpos=20, feed=200, feed_type='feed_cut')
        mark = session.mark()
        session.ev('line_4x', ('apos', 'feed'), apos=30, feed=200, feed_type='feed_cut')
        session.ev('line_4x', ('xpos', 'apos'), xpos=22, apos=60, feed_type='feed_cut')
        replayed, first = program_replay(session, mark)
        missing = [block.raw for block, state in replayed[first:]
                   if block.rotary('A') is not None and state.motion == 1 and state.feed_mode != 93]
        self.assertTrue(raw(replayed, first), 'no rotary feed blocks emitted')
        if missing:
            self.fail(f'rotary feed blocks posted without inverse-time mode (G93): {missing}')


class ChangeRefPointTests(unittest.TestCase):
    """@change_ref_point ('Not Supported in this template')."""

    @known_defect('PP-045')
    def test_change_ref_point_emits_no_fanuc_data_setting(self):
        """INDEPENDENT: Sinumerik 828D (Siemens mode) has no G10 L2 data setting; work offsets
        are written via $P_UIFR or shifted with TRANS/ATRANS, and in ISO dialect
        'G91 G10 L2' would shift the offset incrementally. The procedure says 'Not
        Supported' yet writes 'G91 G10 L2 P.. X Y Z'. A POST ERROR stop is accepted as the
        fail-safe alternative."""
        session = first_job()
        mark = session.mark()
        try:
            session.ev('change_ref_point', home_number=2, xhome=10, yhome=20, zhome=30)
        except UnsupportedGPPL as exc:
            if 'POST ERROR' in str(exc):
                return
            raise
        blocks = parse_blocks(session.text(mark))
        self.assertEqual([block.raw for block in blocks if 10 in block.g], [],
                         f'Fanuc G10 data setting in the NC program: {[b.raw for b in blocks]}')


if __name__ == '__main__':
    unittest.main()
