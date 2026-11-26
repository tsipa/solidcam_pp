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
from pp_tests.gppl.errors import PostAbort
from program_session import Program
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
            session.ev('line_5x', changed, feed_type='feed_rate', **values)
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
        mutant = mutate('    iMotionmode = 1\n    ; A rotating G1 block',
                        '    ; A rotating G1 block')
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
        # The refactored @usr_rapid no longer reads bFirstRapid after the head check: revive the old
        # 'if bTlchg or bFirstRapid' tool-change branch (with its reset) together with the deletion.
        mutant = mutate('        bFirstRapid = false\n    endif\n    ; The A output clears',
                        '    endif\n    ; The A output clears')
        mutant = mutate('    if bTlchg\n        call @usr_rapid_tc_block\n',
                        '    if bTlchg or bFirstRapid\n        bFirstRapid = false\n'
                        '        call @usr_rapid_tc_block\n', source=mutant)
        assert_detected(self, self.check_descending_first_rapid, mutant, 'bFirstRapid kept live')

    def check_link_rotation_in_same_tool_job(self, source=None):
        # Same-tool job 2: homed first rotation (index boundary), cut, straight feed_link retract, then a
        # rotary rapid of the same CAM link: no homing before it (d5952a2).
        session = first_job(source)
        session.cut(10, 20, 5, -1)
        session.same_tool_job(job_name='op2')
        session.ev('move_5x', ['apos'], apos=5, dir5a='ccw')
        session.ev('move_5x', XYZ, xpos=10, ypos=20, zpos=5)
        session.ev('line_5x', ['zpos', 'feed'], zpos=-1, feed_type='feed_rate')
        session.ev('line_5x', ['zpos'], zpos=20, feed_type='feed_link')
        blocks = parse_blocks(session.ev('move_5x', ['apos'], apos=10))
        self.assertEqual([block.rotary('A') for block in blocks if block.rotary('A')], [('ACP', 10.0)],
                         [block.raw for block in blocks])
        self.assertEqual([block.raw for block in blocks if 75 in block.g], [],
                         f'homing inside a confirmed CAM link of a same-tool job: {[b.raw for b in blocks]}')

    def test_first_rapid_flag_is_cleared_by_the_first_rapid(self):
        """INDEPENDENT: deleting the real 'bFirstRapid = false' of @usr_rapid (one edit) keeps every
        later rapid of a same-tool job a 'first rapid', so a rotary rapid inside a confirmed CAM link
        (d5952a2) is homed. The CAM-link guard (no G75, one A=ACP(10)) must fail with AssertionError."""
        self.check_link_rotation_in_same_tool_job()
        mutant = mutate('            call @usr_prep_home_axis\n        endif\n        bFirstRapid = false\n    endif\n',
                        '            call @usr_prep_home_axis\n        endif\n    endif\n')
        assert_detected(self, self.check_link_rotation_in_same_tool_job, mutant, 'bFirstRapid never cleared')

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
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=300, feed_type='feed_rate')
        session.ev('line_5x', ('ypos',), ypos=-5, feed_type='feed_rate')
        session.ev('move_5x', ('zpos',), zpos=50)
        session.ev('move_5x', ('apos', 'ypos', 'zpos'), apos=90, ypos=0, zpos=40)
        session.ev('move_5x', ('zpos',), zpos=10)
        session.ev('line_5x', ('zpos',), zpos=-1, feed_type='feed_rate')
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
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=300, feed_type='feed_rate')
        replayed, first = program_replay(session, mark)
        reason = xy_lost_after_homing(replayed, first)
        if reason:
            self.fail(reason)


# @usr_rapid: 3e0c345 put Z in its own block when the rapid returns from post-inserted homing.
HOMED_RETURN_SPLIT = "        if bFirstMove or bPostHomed\n"


class ApproachAfterHomingTests(unittest.TestCase):
    """Approach after the G75 homing of a non-link rotary rapid (DESIGN-002)."""

    def first_link_of_job(self, source=None):
        session = first_job(source)
        session.cut(10, 20, 50, -1)
        session.same_tool_job(job_name='op2')
        session.ev('move_5x', XYZ, xpos=40, ypos=50, zpos=30)
        session.ev('line_5x', ('zpos', 'feed'), zpos=2, feed=300, feed_type='feed_rate')
        session.ev('line_5x', ('xpos',), xpos=80, feed_type='feed_rate')
        session.ev('line_5x', ('zpos',), zpos=30, feed_type='feed_link')
        mark = session.mark()
        session.ev('move_5x', ('apos',) + XYZ, apos=45, xpos=40, ypos=10, zpos=8)
        return session, mark, {'X': 40, 'Y': 10, 'Z': 8}

    def after_cutting_retract(self, source=None):
        session = first_job(source)
        session.cut(10, 20, 50, -1)
        session.ev('line_5x', ('zpos',), zpos=20, feed_type='feed_rate')
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
        mutant = mutate(HOMED_RETURN_SPLIT, "        if bFirstMove\n")
        for name in ('first_link_of_job', 'after_cutting_retract'):
            assert_detected(self, lambda source: self.check_homed_return(name, source), mutant,
                            f'3e0c345 reverted ({name})', match='not A, XY, Z')


class RapidWithoutMotionTests(unittest.TestCase):
    """A rapid whose axes do not move (SolidCAM sends the position again) adds nothing to the block
    before it. Oracle (INDEPENDENT): Sinumerik executes block by block; a G0 or a second F appended
    to a G1 block changes how that block moves (one G function of a group per block, the cut keeps
    its feed), and MSG("...") must be the only statement of its block."""

    NO_JOIN = ("    ; A rapid without axis motion prints only its pending modal words, in a block of their own: joined\n"
               "    ; to the current line they would turn a G1 block into G0 ('G1 Z-1 F200 G0').\n")
    JOINED = ("    if !change(nR1pos) and !change(xpos) and !change(ypos) and !change(zpos)\n"
              "        skipline = false\n    endif\n")

    @staticmethod
    def program(source=None, emulated=False, **options):
        if emulated:
            options['bSyncdrapid'] = False
        program = Program(source=source, options=options or None)
        program.start(job_type='3-d model' if emulated else 'profile')
        return program

    def check_lines(self, lines):
        for line in (raw.strip() for raw in lines):
            words = line.split()
            motion = [word for word in words if word in ('G0', 'G1', 'G2', 'G3')]
            feeds = [word for word in words if word.startswith('F')]
            self.assertLessEqual(len(motion), 1, f'two motion G codes in one block: {line!r}')
            self.assertLessEqual(len(feeds), 1, f'two feed words in one block: {line!r}')
            if line.startswith('MSG('):
                self.assertTrue(line.endswith(')'), f'MSG block carries more: {line!r}')
            if words and words[0] in ('M0', 'M1'):
                self.assertEqual(line, words[0], f'stop block carries more: {line!r}')

    def check_after_cut(self, source=None, emulated=False):
        program = self.program(source, emulated)
        program.ev('move_5x', xpos=10, ypos=10, zpos=5)
        cut = program.ev('line_5x', zpos=-1, feed=200, feed_type='feed_rate')
        program.ev('move_5x', xpos=10, ypos=10, zpos=-1)
        program.ev('line_5x', xpos=20, feed=200, feed_type='feed_rate')
        self.check_lines(program.nc())
        self.assertIn(cut[-1].strip(), [raw.strip() for raw in program.nc()])

    def check_after_job_comment(self, source=None, **options):
        # bOptstpjob (default on) puts an M1 between the MSG block and the rapid; off, they meet.
        program = self.program(source, **options)
        program.ev('move_5x', xpos=10, ypos=10, zpos=5)
        program.ev('line_5x', zpos=-1, feed=200, feed_type='feed_rate')
        program.ev('line_5x', zpos=5, feed=200, feed_type='feed_rate')
        program.ev('end_of_job', next_job_tool_number=1)
        program.ev('start_of_job', job_name='op2')
        program.ev('move_5x', xpos=10, ypos=10, zpos=5)
        self.check_lines(program.nc())

    @covers('PP-059')
    def test_rapid_without_motion_leaves_the_cut_alone(self):
        """INDEPENDENT: one motion G code per block; the plunge stays a G1 block."""
        self.check_after_cut()

    @covers('PP-059')
    def test_emulated_rapid_without_motion_leaves_the_cut_feed_alone(self):
        """INDEPENDENT: the plunge keeps its cutting feed; F<nRapidfeed> does not join it."""
        self.check_after_cut(emulated=True)

    @covers('PP-059')
    def test_rapid_without_motion_leaves_the_job_comment_alone(self):
        """INDEPENDENT: Sinumerik MSG("...") stands alone in its block; so does the M1 after it."""
        for stop in (True, False):
            with self.subTest(bOptstpjob=stop):
                self.check_after_job_comment(bOptstpjob=stop)

    def test_joining_the_rapid_to_the_current_line_is_detected(self):
        """INDEPENDENT: mutation self-check; the old join (skipline = false) fails each check."""
        mutant = mutate(self.NO_JOIN, self.JOINED)
        assert_detected(self, self.check_after_cut, mutant, 'G0 joined to the cut', match='two motion')
        assert_detected(self, lambda source: self.check_after_cut(source, emulated=True), mutant,
                        'F650 joined to the cut', match='two feed')
        assert_detected(self, lambda source: self.check_after_job_comment(source, bOptstpjob=False), mutant,
                        'G0 joined to MSG', match='MSG block')
        assert_detected(self, self.check_after_job_comment, mutant, 'G0 joined to the job M1', match='stop block')


class FeedEmulatedRapidTests(unittest.TestCase):
    """bSyncdrapid=false on '3-d model' jobs emulates rapids as G1 F<nRapidfeed>."""

    @staticmethod
    def emulated_session(source=None):
        return first_job(source, options=dict(bSyncdrapid=False), job_type='3-d model')

    def check_feed_restored(self, cut, source=None):
        session = self.emulated_session(source)
        session.ev('move_5x', XYZ, xpos=10, ypos=23, zpos=50)
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=100, feed_type='feed_rate')
        session.ev('line_5x', ('xpos',), xpos=12, feed_type='feed_rate')
        rapid = session.mark()
        session.ev('move_5x', ('zpos',), zpos=40)
        after = session.mark()
        if cut == 'line':
            session.ev('line_5x', ('zpos',), zpos=5, feed_type='feed_rate')
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
                        '    if change(iDiametercomp)',
                        '    if bFeedoutput\n        bFeedoutput  = false\n    endif\n    if change(iDiametercomp)')
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
        session.ev('line_5x', ('zpos', 'feed'), zpos=-1, feed=100, feed_type='feed_rate')
        session.ev('line_5x', ('xpos',), xpos=12, feed_type='feed_rate')
        session.ev('line_5x', ('zpos',), zpos=20, feed_type='feed_rate')
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

    @covers('PP-006')
    def test_z_keeps_coordinate_precision_after_first_rapid(self):
        """INDEPENDENT: commit dc916d7 raised the coordinate formats to 8.5 together with VMID
        MovementPrecision 4 -> 5 so that arc end points are written consistently; Z must be
        rounded to 5 decimals like X. The program's first rapid (tool-change positioning,
        bFirstVert branch of @usr_rapid) set zpos_f='5.4' before PP-006 was fixed, so the
        cutting moves of job 1 printed Z with 4 decimals (the real shit2 trace: Z15.8333 next
        to X192.14583)."""
        session = first_job()
        session.ev('move_5x', XYZ, xpos=1, ypos=2, zpos=30)
        mark = session.mark()
        session.ev('line_5x', ('xpos', 'zpos', 'feed'), xpos=1.234567, zpos=1.234567, feed=300,
                   feed_type='feed_rate')
        block = parse_blocks(session.text(mark))[0]
        self.assertAlmostEqual(block.get('X'), 1.23457, delta=1e-9, msg=block.raw)
        self.assertAlmostEqual(block.get('Z'), 1.23457, delta=1e-9,
                               msg=f'Z has {decimals_of(block, "Z")} decimals, X {decimals_of(block, "X")}: {block.raw!r}')

    @covers('PP-006')
    def test_z_keeps_coordinate_precision_after_tool_change(self):
        """INDEPENDENT: same dc916d7 / VMID MovementPrecision=5 oracle after a NON-FIRST tool
        change: before PP-006 was fixed the tool change did not restore the coordinate format
        (and @usr_ct_before_notfirsttool re-applied zpos_f='5.4' whenever bVertical/bFirstVert
        was set), so the first move of tool 2 printed Z with 4 decimals."""
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


def link_session(source=None, options=None):
    """Same-tool job 2 after a homed first rotation, a cut at X10 Y0 and a straight feed_link retract
    to Z50: the 4x/5x rapids that follow ride that confirmed CAM link (d5952a2). A stands at 5."""
    session = first_job(source, options)
    session.cut(10, 0, 5, -1)
    session.same_tool_job(job_name='op2')
    session.ev('move_5x', ['apos'], apos=5, dir5a='ccw')
    session.ev('move_5x', XYZ, xpos=10, ypos=0, zpos=5)
    session.ev('line_5x', ['zpos', 'feed'], zpos=-1, feed_type='feed_rate')
    session.ev('line_5x', ['zpos'], zpos=50, feed_type='feed_link')
    return session


def link_steps(session, steps, next_after, dir5a='ccw'):
    """CAM link rapids (move_5x) to each (xpos, apos); each names the next one as next_command, the
    last one next_after. Returns their NC text."""
    text = ''
    for index, (x, a) in enumerate(steps):
        following = '@move_5x' if index < len(steps) - 1 else next_after
        text += session.ev('move_5x', ['xpos', 'apos'], xpos=x, apos=a, dir5a=dir5a, next_command=following)
    return text


def a_words(blocks):
    return [block.rotary('A') for block in blocks if block.rotary('A')]


class LinkMergeTests(unittest.TestCase):
    """CAM-link rapids that turn A along one straight line at constant Y/Z (option bLinkMerge).

    Machine 2026-11-25: CAM split a 91.8 deg link at Z73 into 32 rapids (X -0.246 mm, A -2.869 deg
    each); posted as alternating G0 A / G0 X blocks, every G0 block ends at a stop (MD20550
    EXACT_POS_MODE 3) and A stops between them, and the machine jerked through the link. With MD20730
    G0_LINEAR_MODE 1 one G0 X A block runs the same straight line in X and A. The run is held while
    CAM's next_command is another 4x/5x rapid and printed with its last step, or before the first
    event that does not continue it."""

    STEPS = [(11, 8), (12, 11), (13, 14), (14, 17)]  # X +1 per 3 deg: one straight line from X10 A5

    def check_merge_before_a_feed_move(self, source=None):
        session = link_session(source)
        mark = session.mark()
        link_steps(session, self.STEPS, '@line_5x')
        session.ev('line_5x', ['zpos', 'feed'], zpos=40, feed=300, feed_type='feed_rate', next_command='')
        blocks = session.blocks(mark)
        self.assertEqual(a_words(blocks), [('ACP', 17.0)], [b.raw for b in blocks])
        merged = next(block for block in blocks if block.rotary('A'))
        self.assertEqual(merged.get('X'), 14, merged.raw)
        self.assertIn(0, merged.g, merged.raw)
        self.assertEqual([b.raw for b in blocks if 'X' in b.axes and not b.rotary('A')], [],
                         [b.raw for b in blocks])

    def test_one_block_when_a_feed_move_follows(self):
        """INDEPENDENT: four link rapids on one straight line in X and A (X +1 mm per 3 deg) go out as
        one G0 X14 A=ACP(17) block, printed with the last one (its next_command is a feed move); no
        separate A or X block remains."""
        self.check_merge_before_a_feed_move()

    def check_merge_before_a_rapid_down(self, source=None):
        session = link_session(source)
        mark = session.mark()
        link_steps(session, self.STEPS, '@move_5x')
        session.ev('move_5x', ['zpos'], zpos=10, next_command='@line_5x')
        blocks = session.blocks(mark)
        self.assertEqual([b.raw for b in blocks], ['G0 X14 A=ACP(17)', 'Z10'])

    def test_one_block_when_a_rapid_down_follows(self):
        """INDEPENDENT: the recorded link of the 2026-11-25 program ends with a 4x/5x rapid down in Z
        (its next_command is a 4x/5x rapid too): the held run is printed first in that rapid, as one
        block, before its Z block."""
        self.check_merge_before_a_rapid_down()

    def check_off_line_step_splits(self, source=None):
        session = link_session(source)
        mark = session.mark()
        link_steps(session, [(11, 8), (12, 11), (13.1, 14), (14.2, 17)], '@line_5x')
        blocks = session.blocks(mark)
        self.assertEqual([b.raw for b in blocks], ['G0 X12 A=ACP(11)', 'G0 X14.2 A=ACP(17)'])

    def test_a_step_off_the_line_starts_a_new_block(self):
        """INDEPENDENT: one block may only take points of one straight line (else it cuts the corner
        CAM planned): a step 0.1 mm off the line of the run ends it (one block to its last point) and
        starts the next run."""
        self.check_off_line_step_splits()

    def check_plain_output(self, source=None, options=None, steps=None):
        """Two link rapids (xpos, apos, zpos or None); the NC of both."""
        session = link_session(source, options)
        mark = session.mark()
        for index, (x, a, z) in enumerate(steps or [(11, 8, None), (12, 11, None)]):
            changed, values = ['xpos', 'apos'], dict(xpos=x, apos=a)
            if z is not None:
                changed.append('zpos')
                values['zpos'] = z
            session.ev('move_5x', changed, dir5a='ccw', next_command='@move_5x' if index == 0 else '@line_5x',
                       **values)
        return [b.raw for b in session.blocks(mark)]

    RISING = [(11, 8, 60), (12, 11, 70)]

    def test_no_merge_without_the_option_or_off_a_constant_height(self):
        """INDEPENDENT: with bLinkMerge false, and for steps that also change Z (CAM's link is then not
        a straight line in X and A alone), every step keeps its G0 A block and X block."""
        self.assertEqual(self.check_plain_output(options=dict(bLinkMerge=False)),
                         ['G0 A=ACP(8)', 'X11', 'G0 A=ACP(11)', 'X12'])
        self.assertEqual(self.check_plain_output(steps=self.RISING),
                         ['G0 A=ACP(8)', 'X11 Z60', 'G0 A=ACP(11)', 'X12 Z70'])

    def check_last_step_keeps_the_run_x(self, source=None):
        # X drifts by 0.002 mm per step within the line tolerance; CAM does not flag X on the last
        # step (same X as the step before), but the run moved X since its start.
        session = link_session(source)
        mark = session.mark()
        session.ev('move_5x', ['xpos', 'apos'], xpos=10.002, apos=8, dir5a='ccw', next_command='@move_5x')
        session.ev('move_5x', ['xpos', 'apos'], xpos=10.004, apos=11, dir5a='ccw', next_command='@move_5x')
        session.ev('move_5x', ['apos'], xpos=10.004, apos=14, dir5a='ccw', next_command='@line_5x')
        self.assertEqual([b.raw for b in session.blocks(mark)], ['G0 X10.004 A=ACP(14)'])

    def test_the_last_block_carries_the_x_of_the_run(self):
        """INDEPENDENT: the held steps printed no X, so the one block must carry the run's X also when
        CAM flags no X change on the last step (it flags only what changes at its own precision)."""
        self.check_last_step_keeps_the_run_x()

    def check_single_and_half_turns(self, source=None):
        # One held step followed by a rapid down: its plain A and X blocks.
        session = link_session(source)
        mark = session.mark()
        link_steps(session, [(11, 8)], '@move_5x')
        session.ev('move_5x', ['zpos'], zpos=10, next_command='')
        self.assertEqual([b.raw for b in session.blocks(mark)], ['G0 A=ACP(8)', 'X11', 'Z10'])
        # Two steps of 179.5 deg would make 359 deg in one block: each goes on its own.
        session = link_session(source)
        mark = session.mark()
        link_steps(session, [(11, 184.5), (12, 364)], '@line_5x')
        self.assertEqual(a_words(session.blocks(mark)), [('ACP', 184.5), ('ACP', 4.0)])
        # The other direction ends the run, also back along the same line (merged, the ACN word would
        # turn from A5 to A6.5 the long way, 358.5 deg).
        session = link_session(source)
        mark = session.mark()
        session.ev('move_5x', ['xpos', 'apos'], xpos=11, apos=8, dir5a='ccw', next_command='@move_5x')
        session.ev('move_5x', ['xpos', 'apos'], xpos=10.5, apos=6.5, dir5a='cw', next_command='@line_5x')
        self.assertEqual(a_words(session.blocks(mark)), [('ACP', 8.0), ('ACN', 6.5)])

    def test_single_steps_long_turns_and_reversals_stay_apart(self):
        """INDEPENDENT: a run of one step keeps the plain output; a modulo axis turns less than one
        revolution per ACP/ACN word, so a run stops before 359 deg; a step that turns the other way
        cannot share the word of the run."""
        self.check_single_and_half_turns()

    def check_safety_net(self, source=None):
        session = link_session(source)
        mark = session.mark()
        # CAM names another 4x/5x rapid after the last step, but a feed move comes.
        link_steps(session, self.STEPS, '@move_5x')
        session.ev('line_5x', ['zpos', 'feed'], zpos=40, feed=300, feed_type='feed_rate', next_command='')
        raws = [b.raw for b in session.blocks(mark)]
        self.assertEqual(raws[0], 'G0 X14 A=ACP(17)', raws)
        self.assertTrue(raws[1].startswith('G1') and 'Z40' in raws[1], raws)

    def test_a_held_run_is_printed_before_the_next_move_in_any_case(self):
        """INDEPENDENT: a held point must never be lost or follow a later move: when the event after
        the last step is not the 4x/5x rapid CAM's next_command named, the next motion event prints
        the run first (here a feed move)."""
        self.check_safety_net()

    def check_safety_net_arc(self, source=None):
        session = link_session(source)
        mark = session.mark()
        link_steps(session, self.STEPS, '@move_5x')
        emit_xy_arc(session, (14, 0, 50), (14, 5), 90)
        raws = [b.raw for b in session.blocks(mark)]
        self.assertEqual(raws[0], 'G0 X14 A=ACP(17)', raws)
        self.assertTrue(raws[1].startswith(('G2', 'G3', 'G1')), raws)

    def check_safety_net_job_end(self, source=None):
        session = link_session(source)
        mark = session.mark()
        link_steps(session, self.STEPS, '@move_5x')
        session.same_tool_job(job_name='op3')
        raws = [b.raw for b in session.blocks(mark)]
        self.assertIn('G0 X14 A=ACP(17)', raws)
        self.assertLess(raws.index('G0 X14 A=ACP(17)'), raws.index('MSG("op3")'), raws)

    def check_safety_net_relative(self, source=None):
        session = link_session(source)
        mark = session.mark()
        link_steps(session, self.STEPS, '@move_5x')
        session.ev('relative_mode')
        session.ev('line_5x', ['zpos', 'feed'], zpos=-5, feed=300, feed_type='feed_rate', next_command='')
        blocks = session.blocks(mark)
        merged = next(block for block in blocks if block.rotary('A'))
        self.assertNotIn(91, merged.g, [b.raw for b in blocks])
        self.assertIn(91, blocks[-1].g, [b.raw for b in blocks])

    def test_the_safety_net_covers_arcs_job_ends_and_g91(self):
        """INDEPENDENT: with a next_command that named a 4x/5x rapid, the held run still goes out before
        an arc and before the next job (not after its message and M1), and in the G90 it was held in
        when a G91 came in between (the end point X14 is absolute)."""
        self.check_safety_net_arc()
        self.check_safety_net_job_end()
        self.check_safety_net_relative()

    BROKEN_FLUSH = ('    if bLinkHold\n        iMode = iMotionmode\n', '    if false\n        iMode = iMotionmode\n')

    def check_lost_run_stops_the_post(self, source, close):
        session = link_session(source)
        link_steps(session, self.STEPS, '@move_5x')
        with self.assertRaises(PostAbort) as caught:
            close(session)
        self.assertIn('held CAM-link rapid was not posted', str(caught.exception))

    def test_a_run_still_held_at_an_end_stops_the_post(self):
        """INDEPENDENT: second line of defence. If the flush ever failed, a job, program or file end
        must stop the post (POST ERROR) instead of writing a program without the held rapid. Without
        that check the broken flush loses the run silently at the job end."""
        broken = mutate(*self.BROKEN_FLUSH)
        closes = {'end_of_job': lambda s: s.ev('end_of_job'),
                  'end_program': lambda s: s.ev('end_program'),
                  'end_of_file': lambda s: s.ev('end_of_file')}
        for label, close in closes.items():
            with self.subTest(event=label):
                self.check_lost_run_stops_the_post(broken, close)
        no_check = mutate('    call @usr_link_flush\n    call @usr_link_none_held\n    bBoundaryStop = false\n',
                          '    call @usr_link_flush\n    bBoundaryStop = false\n', source=broken)
        assert_detected(self, lambda source: self.check_lost_run_stops_the_post(source, closes['end_of_job']),
                        no_check, 'no check at the job end')

    def check_y_motion_stays_apart(self, source=None):
        session = link_session(source)
        mark = session.mark()
        session.ev('move_5x', ['xpos', 'ypos', 'apos'], xpos=11, ypos=1, apos=8, dir5a='ccw', next_command='@move_5x')
        session.ev('move_5x', ['xpos', 'ypos', 'apos'], xpos=12, ypos=2, apos=11, dir5a='ccw',
                   next_command='@line_5x')
        self.assertEqual([b.raw for b in session.blocks(mark)], ['G0 A=ACP(8)', 'X11 Y1', 'G0 A=ACP(11)', 'X12 Y2'])

    def test_no_merge_when_y_moves(self):
        """INDEPENDENT: the one block carries X and A only: steps that move Y keep their own blocks."""
        self.check_y_motion_stays_apart()

    def test_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the link merge."""
        mutants = {
            'no line check': (('                    if abs(xpos - nLinkX0 - nLinkDX * nT / nLinkDT) <= 0.005\n',
                               '                    if true\n'), self.check_off_line_step_splits),
            'no turn limit': (('                if abs(nT) < 359\n', '                if true\n'),
                              self.check_single_and_half_turns),
            'no direction check': (('            if iR1dirMode eq iLinkDir\n', '            if true\n'),
                                   self.check_single_and_half_turns),
            'no flush before a feed move': (('    local logical bInverseBlock\n    call @usr_link_flush\n',
                                             '    local logical bInverseBlock\n'), self.check_safety_net),
            'no flush at the end of a job': (('    call @usr_link_flush\n    call @usr_link_none_held\n    bBoundaryStop = false\n',
                                              '    bBoundaryStop = false\n'), self.check_safety_net_job_end),
            'run printed in the current G91': (('        iAbsincmode = iLinkAbs\n', ''), self.check_safety_net_relative),
            'Y ignored': (('if bFeedPrevValid and !change(ypos) and !change(zpos)', 'if bFeedPrevValid and !change(zpos)'),
                          self.check_y_motion_stays_apart),
            'held run lost at a rapid down': (('        if !bGoesOn\n            call @usr_link_flush\n',
                                               '        if false\n            call @usr_link_flush\n'),
                                              self.check_merge_before_a_rapid_down),
            'merged block without X': (("[cWo,iWorkoffset' '],['G'iAbsincmode ' '],'X',nLinkX:xpos_f,' '}\n",
                                        "[cWo,iWorkoffset' '],['G'iAbsincmode ' ']}\n"),
                                       self.check_merge_before_a_rapid_down),
            'last step without the run X': (("    if abs(xpos - nLinkX0) >= 0.000005\n        change(xpos) = true\n",
                                             "    if false\n        change(xpos) = true\n"),
                                            self.check_last_step_keeps_the_run_x),
        }
        feed_flush = '    ; A held CAM-link run goes out before a call of this feed move (usr_link_flush).\n    call @usr_link_flush\n'
        for label, ((old, new), check) in mutants.items():
            with self.subTest(mutant=label):
                mutant = mutate(old, new)
                if label == 'no flush before a feed move':
                    mutant = mutate(feed_flush, '', source=mutant)
                if label == 'Y ignored':
                    mutant = mutate('abs(ypos - nFeedPrevY) < 0.000005 and abs(zpos', 'abs(zpos', source=mutant)
                assert_detected(self, check, mutant, label)
        with self.subTest(mutant='no flush before an arc'):
            mutant = mutate(feed_flush, '')
            mutant = mutate('    local numeric nArcAR nArcEndX nArcEndY nArcEndZ\n    call @usr_link_flush\n',
                            '    local numeric nArcAR nArcEndX nArcEndY nArcEndZ\n', source=mutant)
            assert_detected(self, self.check_safety_net_arc, mutant, 'no flush before an arc')

    def test_z_change_and_option_mutants_are_detected(self):
        """INDEPENDENT: mutation self-check of the step conditions (constant Z, the option)."""
        def plain_z(source):
            self.assertEqual(self.check_plain_output(source, steps=self.RISING),
                             ['G0 A=ACP(8)', 'X11 Z60', 'G0 A=ACP(11)', 'X12 Z70'])

        def plain_option(source):
            self.assertEqual(self.check_plain_output(source, options=dict(bLinkMerge=False)),
                             ['G0 A=ACP(8)', 'X11', 'G0 A=ACP(11)', 'X12'])
        for label, (old, new), check in (
                ('Z ignored', ('if bFeedPrevValid and !change(ypos) and !change(zpos) and !change(iDiametercomp)',
                               'if bFeedPrevValid and !change(ypos) and !change(iDiametercomp)'), plain_z),
                ('option ignored', ('    if bLinkMerge and bCamLinkRapid and', '    if bCamLinkRapid and'),
                 plain_option)):
            with self.subTest(mutant=label):
                mutant = mutate(old, new)
                if label == 'Z ignored':
                    mutant = mutate('abs(ypos - nFeedPrevY) < 0.000005 and abs(zpos - nFeedPrevZ) < 0.000005',
                                    'abs(ypos - nFeedPrevY) < 0.000005', source=mutant)
                assert_detected(self, check, mutant, label)


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
        Regression guard of PP-049 (fixed in 9f48a3a/1bdfecc; the F values are checked by
        tests/test_inverse_time_feed.py)."""
        session = first_job()
        self.assertEqual(session.state['i4xfeedmode'], 1, 'the shipped option no longer selects inverse time')
        session.ev('move_5x', XYZ, xpos=10, ypos=0, zpos=50)
        session.ev('line_5x', ('zpos', 'feed'), zpos=20, feed=200, feed_type='feed_rate')
        mark = session.mark()
        session.ev('line_4x', ('apos', 'feed'), apos=30, feed=200, feed_type='feed_rate', dir5a='ccw')
        session.ev('line_4x', ('xpos', 'apos'), xpos=22, apos=60, feed_type='feed_rate', dir5a='ccw')
        replayed, first = program_replay(session, mark)
        missing = [block.raw for block, state in replayed[first:]
                   if block.rotary('A') is not None and state.motion == 1 and state.feed_mode != 93]
        self.assertTrue(raw(replayed, first), 'no rotary feed blocks emitted')
        if missing:
            self.fail(f'rotary feed blocks posted without inverse-time mode (G93): {missing}')


class ChangeRefPointTests(unittest.TestCase):
    """@change_ref_point ('Not Supported in this template')."""

    @covers('PP-045')
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
