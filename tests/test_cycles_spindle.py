"""Drill cycles and spindle output of Gmill_540v_4x.gpp.

Covered procedures: @drill (CYCLE81/82/83/84/86), @drill_point, @end_drill (bare
MCALL cancel, G94 after tapping), @start_tool, @m_feed_spin, @usr_spindle_output
and @usr_spindle_mcode_output (M3/M4, S, ramp dwell).

Oracles
  Siemens 840D sl / 828D cycle signatures (positional parameters):
    CYCLE81(RTP,RFP,SDIS,DP,DPR)
    CYCLE82(RTP,RFP,SDIS,DP,DPR,DTB)
    CYCLE83(RTP,RFP,SDIS,DP,DPR,FDEP,FDPR,DAM,DTB,DTS,FRF,VARI)
    CYCLE84(RTP,RFP,SDIS,DP,DPR,DTB,SDAC,MPIT,PIT,POSS,SST,SST1,_AXN,_PTAB,_TECHNO,
            _VARI,_DAM,_VRT)
    CYCLE86(RTP,RFP,SDIS,DP,DPR,DTB,SDIR,RPA,RPO,RPAP,POSS)
  The control rapids to RFP+SDIS and feeds from there; DP is the absolute final
  depth; an empty or zero DPR means "not programmed", so DP is used. FDPR is the
  first drilling depth relative to RFP. SolidCAM's drill_upper_z is the
  feed-start plane (the Fanuc R plane), drill_clearance_z the retract plane
  (RTP) and drill_lower_z the hole bottom (DP).
  MCALL CYCLExx(...) is modal: the cycle runs after every following block with
  path motion until a bare MCALL cancels it.
  CYCLE84: PIT is the pitch in mm/rev (F [mm/min] / S [rpm]); its sign selects
  the thread hand (negative = left-hand, spindle CCW). The machine's Vericut
  control agrees (vericut/sin840d_special.ctl, condition macro "Direction of
  rotation after end of cycle CYCLE84": PIT < 0 -> ActiveSpindleDir CCW).
  CYCLE86: SDIR 3/4 is the spindle direction the cycle switches on (M3/M4).
  Spindle: M3 = CW, M4 = CCW. M3/M4 starts the spindle at the S that is active
  in that block, so S must be programmed in or before it. A ramp of dS rpm at an
  acceleration of a rpm/s takes dS/a seconds.

Harness
  Every test runs a support.session.Session, so @init_post formats apply
  (SPIN:INTEGER_DEF_F renders like the post; the legacy history_engine has no
  integer_def_f). Drilling inputs are DRILL_DEFAULTS (clearance 30, upper 12,
  lower -15, safety 2, down_step 3, delay 0.25) unless a test overrides them.
  Feed/spin pairs are chosen so that FEED/SPIN is exact in three decimals,
  because the unformatted PIT uses the engine's default of three decimals
  (ENGINE-003).
  ENGINE-004: the CYCLE84 line used the literal ',0,''' that the engine rendered
  with a stray apostrophe before SST. The @drill rewrite writes ',0,', so every
  reading of the literal gives the same quote-free list.
  Guards are check_*(tc, source=None) functions without subTest, so a mutated GPP
  (support.mutation.mutate) fails them with AssertionError (MutationKillTests).
  Structural sequences: the cycle-geometry, continuity and tapping guards deliver
  many @drill/@end_drill pairs in one job, without job boundaries or drill points.
  SolidCAM sends one cycle type per job, but the cycle line @drill prints depends
  only on that event's inputs (F is printed unconditionally, and @rapid_move gets
  no changed position). The modal-cancel guard uses real job boundaries.
"""
import re
import unittest

from pp_tests.engine import UnsupportedGPPL

from support import (DRILL_DEFAULTS, Session, assert_detected, block_texts, covers, index_of,
                     known_defect, last_index_of, mutate, parse_blocks, pp_source, replay,
                     state_before)

SIGNATURES = {
    81: 'RTP RFP SDIS DP DPR'.split(),
    82: 'RTP RFP SDIS DP DPR DTB'.split(),
    83: 'RTP RFP SDIS DP DPR FDEP FDPR DAM DTB DTS FRF VARI'.split(),
    84: 'RTP RFP SDIS DP DPR DTB SDAC MPIT PIT POSS SST SST1 _AXN _PTAB _TECHNO _VARI _DAM _VRT'.split(),
    86: 'RTP RFP SDIS DP DPR DTB SDIR RPA RPO RPAP POSS'.split(),
}
DRILL_TYPES = (('g81', 81), ('g82', 82), ('g83', 83), ('g84', 84), ('g86', 86))
# drill_upper_z: above the safety distance, between 0 and safety, the Z0 boundary
# (the PP branches on drill_upper_z > 0) and below Z0.
UPPER_LEVELS = (12, 1, 0, -2)
HOLE = dict(xpos=10, ypos=20, zpos=30)

# bea8c62 "Fix Sinumerik drill cycle parameters", positive branch; one shared CYCLE8x head since the
# @drill rewrite, so reverting it reverts every cycle, CYCLE84 included.
G84_FIX = "{' (',rtp,','rfp,','sdis,',',dp,','}"
G84_BEFORE_BEA8C62 = "{' (',rtp,',,'sdis,',',dp,',',rfp}"


# --------------------------------------------------------------------------- helpers

def number(field):
    """Numeric value of a cycle argument; '' (not programmed) reads as 0.

    A non-numeric field is malformed NC that the control rejects, so it fails the
    test with AssertionError instead of ValueError (verifier corrections to
    pp-region-4-cycles-rotary-21 and engine-impl-critic-06).
    """
    if field == '':
        return 0.0
    try:
        return float(field)
    except ValueError:
        raise AssertionError(f'non-numeric cycle argument {field!r}') from None


def drilling_session(source=None):
    """Session after the first tool change, positioned over the first hole."""
    session = Session(source=source)
    session.first_tool()
    session.ev('move_5x', ('xpos', 'ypos', 'zpos'), **HOLE)
    return session


def drill(session, drill_type, **inputs):
    """Deliver @drill at the current hole, then @end_drill; return the @drill blocks.

    Defaults: DRILL_DEFAULTS, feed 150 mm/min, spin 100 rpm, a CW tool.
    """
    values = dict(DRILL_DEFAULTS, drill_type=drill_type, feed=150, spin=100, tool_direction='cw', **HOLE)
    values.update(inputs)
    blocks = parse_blocks(session.ev('drill', (), **values))
    session.ev('end_drill')
    return blocks


def cycle_arguments(tc, blocks, cycle, where=''):
    """Raw argument list of the single 'MCALL CYCLE<cycle> (..)' block."""
    calls = [block for block in blocks if block.has('MCALL')]
    tc.assertEqual(len(calls), 1, f'{where}: expected one MCALL block in {[b.raw for b in blocks]}')
    call = calls[0].cycle
    tc.assertIsNotNone(call, f'{where}: MCALL without a cycle argument list: {calls[0].raw!r}')
    tc.assertEqual(call[0], f'CYCLE{cycle}', where)
    return list(call[1])


def assert_plain_arguments(tc, fields, where=''):
    quoted = [field for field in fields if "'" in field or '"' in field]
    tc.assertEqual(quoted, [], f'{where}: quote character inside cycle arguments: {fields}')


def named(tc, fields, cycle, where=''):
    """{parameter name: raw field} by the Siemens signature (missing trailing fields = '')."""
    names = SIGNATURES[cycle]
    tc.assertLessEqual(len(fields), len(names), f'{where}: too many CYCLE{cycle} parameters: {fields}')
    return dict(zip(names, fields + [''] * (len(names) - len(fields))))


def cycle_parameters(tc, session, drill_type, cycle, where='', **inputs):
    """Run one drill job and return its CYCLE parameters by name."""
    fields = cycle_arguments(tc, drill(session, drill_type, **inputs), cycle, where)
    assert_plain_arguments(tc, fields, where)
    return named(tc, fields, cycle, where), fields


def assert_feed_start_geometry(tc, values, upper, where=''):
    """RTP = clearance, DP = lower level, DPR unused, feed starts at drill_upper_z."""
    tc.assertEqual(number(values['RTP']), DRILL_DEFAULTS['drill_clearance_z'], where)
    tc.assertEqual(number(values['DP']), DRILL_DEFAULTS['drill_lower_z'], where)
    tc.assertEqual(number(values['DPR']), 0, f'{where}: DPR must be empty or 0 so DP is used')
    tc.assertGreaterEqual(number(values['SDIS']), 0, where)
    # Inputs are integers or 0.001 steps and the post prints 3 decimals: 1e-6 absorbs float noise only.
    tc.assertAlmostEqual(number(values['RFP']) + number(values['SDIS']), upper, delta=1e-6,
                         msg=f'{where}: feed start RFP+SDIS must equal drill_upper_z')


def first_peck_depth(values):
    """Absolute Z of the first CYCLE83 peck: RFP - FDPR (FDEP if FDPR is not programmed)."""
    if values['FDPR'] != '':
        return number(values['RFP']) - number(values['FDPR'])
    return number(values['FDEP'])


def spindle_codes(blocks):
    return [code for block in blocks for code in block.m if code in (3, 4, 5)]


def speeds(blocks):
    return [block.get('S') for block in blocks if block.get('S') is not None]


def dwell_seconds(blocks):
    """Total G4 dwell; F inside a G4 block is the dwell time in seconds."""
    return sum(block.get('F', 0.0) for block in blocks if 4 in block.g)


# --------------------------------------------------------------------------- guards

def check_cycle_geometry(tc, source=None):
    """Every cycle in both drill_upper_z branches: Siemens geometry plus cycle extras."""
    session = drilling_session(source)
    feeds = []
    for drill_type, cycle in DRILL_TYPES:
        for upper in UPPER_LEVELS:
            where = f'CYCLE{cycle} drill_upper_z={upper}'
            feed = (150, 120)[len(feeds) % 2]      # alternate, so a stale F is visible
            feeds.append((where, feed))
            values, _ = cycle_parameters(tc, session, drill_type, cycle, where, drill_upper_z=upper, feed=feed)
            assert_feed_start_geometry(tc, values, upper, where)
            if cycle == 82:
                tc.assertEqual(number(values['DTB']), DRILL_DEFAULTS['delay'], where)
            if cycle == 83:
                down_step = DRILL_DEFAULTS['down_step']
                tc.assertEqual(number(values['DAM']), down_step, f'{where}: DAM = down_step')
                tc.assertEqual(values['VARI'], '1', f'{where}: VARI 1 = swarf removal (e4af180)')
                # The first peck is one down_step below either the feed-start plane or the
                # reference surface (upper - safety); which one is intended is open (PP-055).
                references = (upper - down_step, upper - DRILL_DEFAULTS['safety'] - down_step)
                peck = first_peck_depth(values)
                tc.assertTrue(any(abs(peck - reference) < 1e-6 for reference in references),
                              f'{where}: first peck Z{peck} not one down_step below {references}')
            if cycle == 86:
                tc.assertEqual(values['SDIR'], '3', f'{where}: CW tool -> SDIR 3 (M3)')
    # The cycle feed must be the job's F when the MCALL block runs (modal F).
    replayed = replay(session.text())
    calls = [index for index, (block, _) in enumerate(replayed) if block.has('MCALL') and block.cycle]
    tc.assertEqual(len(calls), len(feeds))
    for index, (where, feed) in zip(calls, feeds):
        tc.assertEqual(state_before(replayed, index).feed, feed, f'{where}: F at the MCALL block')


def check_drill_continuity(tc, source=None):
    """RTP/DP/DPR and RFP+SDIS are continuous across drill_upper_z = 0 for every cycle."""
    session = drilling_session(source)
    for drill_type, cycle in DRILL_TYPES:
        sides = {}
        for upper in (0.001, -0.001):
            where = f'CYCLE{cycle} drill_upper_z={upper}'
            values, _ = cycle_parameters(tc, session, drill_type, cycle, where, drill_upper_z=upper)
            tc.assertAlmostEqual(number(values['RFP']) + number(values['SDIS']), upper, delta=1e-6, msg=where)
            sides[upper] = tuple(number(values[name]) for name in ('RTP', 'DP', 'DPR'))
        tc.assertEqual(sides[0.001], sides[-0.001], f'CYCLE{cycle}: RTP/DP/DPR differ across Z0')


TAPPING_CASES = (
    # drill_upper_z, Step_Down, VarRetract, expected (_VARI, _DAM, _VRT)
    (12, 0, 0, []),
    (12, 2.5, 0, ['1', '2.5', '2.5']),
    (12, 2.5, 0.7, ['1', '2.5', '0.7']),
    (-2, 0, 0, []),
    (-2, 2.5, 0, ['1', '2.5', '2.5']),
    (-2, 2.5, 0.7, ['1', '2.5', '0.7']),
)


def check_tapping_fields(tc, source=None):
    """CYCLE84 for a CW tap, feed 150 mm/min at S100 (pitch 1.5 mm)."""
    session = drilling_session(source)
    for upper, step_down, retract, tail in TAPPING_CASES:
        where = f'CYCLE84 drill_upper_z={upper} Step_Down={step_down} VarRetract={retract}'
        values, fields = cycle_parameters(tc, session, 'g84', 84, where, drill_upper_z=upper,
                                          Step_Down=step_down, VarRetract=retract, feed=150, spin=100)
        assert_feed_start_geometry(tc, values, upper, where)
        # INDEPENDENT (Siemens CYCLE84):
        tc.assertEqual(number(values['PIT']), 1.5, f'{where}: PIT = F/S = 150/100 mm/rev, right-hand')
        tc.assertEqual(values['MPIT'], '', f'{where}: pitch is given by PIT only')
        tc.assertEqual(number(values['SST']), 100, f'{where}: SST = tapping speed = S')
        tc.assertIn(values['SDAC'], ('3', '5'), f'{where}: a CW tap must not turn M4 after the cycle')
        tc.assertEqual((values['_AXN'], values['_PTAB']), ('', ''), where)
        if step_down:
            tc.assertIn(number(values['_VARI']), (1, 2), f'{where}: _VARI 1/2 = machining with infeed steps')
            tc.assertEqual(number(values['_DAM']), step_down, f'{where}: _DAM = infeed per step')
            if retract:
                tc.assertEqual(number(values['_VRT']), retract, f'{where}: _VRT = retract amount')
        else:
            tc.assertEqual(number(values['_VARI']), 0, f'{where}: single pass (_VARI empty or 0)')
        # CHARACTERIZATION (PP choices, not Siemens requirements):
        tc.assertEqual(values['SDAC'], '3', f'{where}: spindle keeps M3 after the cycle (5 = stop is also valid)')
        tc.assertEqual(number(values['SST1']), 200, f'{where}: retract at 2 x SST')
        tc.assertEqual(values['_TECHNO'], '1221', where)
        tc.assertEqual((number(values['DTB']), number(values['POSS'])), (0, 0), where)
        tc.assertEqual(fields[15:], tail, f'{where}: exact tail: none for a single pass, else _VARI 1 '
                                          '(chip breaking) and _VRT falling back to Step_Down')


def check_modal_cycle_cancel(tc, source=None):
    """MCALL cycle runs at the holes and is cancelled before the next positioning.

    One drilling job per cycle type, separated by end_of_job/start_of_job (same
    tool: structural, @drill/@end_drill never read the tool).
    """
    session = Session(source=source)
    session.first_tool()
    jobs = []
    for index, (drill_type, cycle) in enumerate(DRILL_TYPES):
        x0 = 10 + 100 * index                       # unique coordinates per job
        if index:
            session.same_tool_job(job_name=f'drill_{drill_type}')
        session.ev('move_5x', ('xpos', 'ypos', 'zpos'), xpos=x0, ypos=20, zpos=30)
        start = session.mark()
        session.ev('drill', (), **dict(DRILL_DEFAULTS, drill_type=drill_type, feed=150, spin=100,
                                       tool_direction='cw', xpos=x0, ypos=20, zpos=30))
        session.ev('drill_point', (), xpos=x0, ypos=20)                  # first hole (see PP-030)
        session.ev('drill_point', ('xpos', 'ypos'), xpos=x0 + 20, ypos=25)
        cancel = session.ev('end_drill')
        session.ev('move_5x', ('xpos',), xpos=x0 + 40)
        jobs.append((drill_type, cycle, x0, session.text(start), cancel))
    replayed = replay(session.text())
    blocks = [block for block, _ in replayed]
    for drill_type, cycle, x0, job_text, cancel in jobs:
        where = f'{drill_type} job at X{x0}'
        calls = [b for b in parse_blocks(job_text) if b.cycle and b.cycle[0] == f'CYCLE{cycle}']
        tc.assertEqual(len(calls), 1, f'{where}: one MCALL CYCLE{cycle} per job')
        hole = index_of(blocks, lambda b: b.axes == {'X': x0 + 20, 'Y': 25})
        tc.assertNotEqual(hole, -1, f'{where}: hole X{x0 + 20} Y25 not programmed as one block')
        tc.assertEqual(state_before(replayed, hole).mcall, f'CYCLE{cycle}', f'{where}: cycle not active at the hole')
        after = index_of(blocks, lambda b: b.axes == {'X': x0 + 40}, hole)
        tc.assertNotEqual(after, -1, f'{where}: positioning move X{x0 + 40} missing')
        tc.assertIsNone(state_before(replayed, after).mcall, f'{where}: modal cycle still active at X{x0 + 40}')
        # Exact @end_drill blocks: one bare MCALL; G94 after tapping is a CHARACTERIZATION
        # (the Vericut ctl switches G331/G332 to feed per revolution).
        tc.assertEqual(block_texts(cancel), ['MCALL'] + (['G94'] if drill_type == 'g84' else []), where)


def check_spindle_start(tc, source=None):
    """M3/M4 by tool direction with S; no spindle start for tapping tools; S changes."""
    for direction, code in (('cw', 3), ('ccw', 4)):
        session = Session(source=source)
        blocks = parse_blocks(session.ev('start_tool', tool_direction=direction, spin=1000))
        tc.assertEqual(spindle_codes(blocks), [code], f'start_tool {direction}: {[b.raw for b in blocks]}')
        tc.assertEqual(speeds(blocks), [1000], f'start_tool {direction}')
        # A mid-job speed change (CAM @m_feed_spin) programs only the new S.
        tc.assertEqual(block_texts(session.ev('m_feed_spin', ('spin',), tool_direction=direction, spin=1200)),
                       ['S1200'], f'm_feed_spin {direction}')
        tc.assertEqual(block_texts(session.ev('m_feed_spin', (), tool_direction=direction, spin=1200)), [],
                       f'm_feed_spin {direction} without a speed change')
    # CYCLE84 runs the spindle itself (SST); the tool start must not start it.
    session = Session(source=source)
    blocks = parse_blocks(session.ev('start_tool', tool_direction='cw', spin=1000, d_drill_type='d_tapping'))
    tc.assertEqual((spindle_codes(blocks), speeds(blocks)), ([], []), f'tapping tool: {[b.raw for b in blocks]}')
    # Restart after an M0 between two jobs of the same tool (VMID bStopM00): @m_feed_spin
    # sets the direction that the restart block prints.
    for direction, code in (('cw', 3), ('ccw', 4)):
        session = Session(source=source, tool_direction=direction)
        session.first_tool(next_tool=1)
        session.cut(10, 20, 5, -1)
        mark = session.mark()
        session.ev('end_of_job', bStopM00=True, next_job_tool_number=1)
        blocks = session.blocks(mark)
        stop = index_of(blocks, lambda b: 0 in b.m)
        tc.assertNotEqual(stop, -1, f'no M0 between same-tool jobs: {[b.raw for b in blocks]}')
        tc.assertEqual(spindle_codes(blocks[stop:]), [code], f'restart after M0, {direction} tool')


def check_spindle_acceleration_dwell(tc, source=None):
    """A speed change above one second of ramp gets a dwell of at least dS/spindle_accel.

    spindle_accel is the post's declared acceleration (@init_post 'spindle_accel =
    500 ; rpm/s'). Whether the 828D needs a dwell at all depends on MD35500
    (tc-03/tc-09 corrections); the oracle is the ramp time at the declared value.
    """
    for previous, target in ((0, 1000), (900, 1000), (8000, 3000)):
        session = Session(source=source)
        if previous:
            session.ev('start_tool', tool_direction='cw', spin=previous)
            text = session.ev('m_feed_spin', ('spin',), spin=target)
        else:
            text = session.ev('start_tool', tool_direction='cw', spin=target)
        accel = session.state['spindle_accel']
        dwell = dwell_seconds(parse_blocks(text))
        where = f'S{previous} -> S{target} at {accel} rpm/s: {text!r}'
        if abs(target - previous) > accel:
            tc.assertGreaterEqual(dwell, abs(target - previous) / accel, where)   # INDEPENDENT: ramp time
        else:
            tc.assertEqual(dwell, 0, where)          # CHARACTERIZATION: no dwell below 1 s of ramp


# --------------------------------------------------------------------------- tests

class DrillCycleGeometryTests(unittest.TestCase):
    def test_feed_start_plane_and_depth_in_every_cycle_and_branch(self):
        """INDEPENDENT: Siemens CYCLE81/82/83/84/86 signatures and SolidCAM drill levels.

        CYCLE81..86 at drill_upper_z 12, 1, 0 and -2 (both branches of the PP's
        drill_upper_z > 0 test): RTP = drill_clearance_z, DP = drill_lower_z, DPR
        empty or 0, RFP+SDIS = drill_upper_z (bea8c62), SDIS >= 0, and the job's F is
        modal at the MCALL block. CYCLE82 DTB = delay. CYCLE83 DAM = down_step, VARI 1
        (swarf removal, e4af180), and the first peck one down_step below the feed
        start or the reference surface (which one is PP-055). CYCLE86 SDIR 3 for a
        CW tool.
        """
        check_cycle_geometry(self)

    def test_pin_effective_cycle_geometry_is_continuous_across_z0(self):
        """INDEPENDENT: Siemens CYCLE8x semantics give the same hole on both sides of Z0.

        The PP writes two layouts (RFP=upper-safety, SDIS=safety above Z0; RFP=upper,
        SDIS empty, DPR 0 at or below). At drill_upper_z = +/-0.001 the feed start
        RFP+SDIS must follow drill_upper_z and RTP/DP/DPR must be identical.
        """
        check_drill_continuity(self)

    def test_pin_drill_continuity_detects_mutation(self):
        """INDEPENDENT: the continuity guard kills an RFP shift in the Z0 branch of the shared
        CYCLE8x head."""
        mutant = mutate("{' (',rtp,','drill_upper_z,',,',dp,',','0.'}", "{' (',rtp,','rfp,',,',dp,',','0.'}")
        assert_detected(self, lambda source: check_drill_continuity(self, source), mutant,
                        'RFP = upper - safety in the drill_upper_z <= 0 branch')

    def test_cycle83_documentation_matches_output(self):
        """INDEPENDENT: Siemens CYCLE83 signature and the e4af180/1710187 commit intent.

        e4af180 documents the CYCLE83 parameter list in a GPP comment and states
        "DTB empty/0, DTS 0.5 sec, FRF 1, VARI 1"; 1710187 reduced DTS to 0.5. The
        signature comment must match the Siemens signature, and the stated values
        must match both the emitted output and the commit intent (DTS 0.5).
        """
        source = pp_source()
        match = re.search(r';\s*CYCLE83\(([^)]*)\)', source)
        self.assertIsNotNone(match, 'CYCLE83 signature comment (e4af180) is missing')
        self.assertEqual(match.group(1).split(','), SIGNATURES[83])
        claims = re.search(r';[^\n]*DTB\s+empty/0,\s*DTS\s+([\d.]+)\s*sec,\s*FRF\s+(\d+),\s*VARI\s+(\d+)', source)
        self.assertIsNotNone(claims, 'CYCLE83 "DTB empty/0, DTS .. sec, FRF .., VARI .." comment (e4af180) is missing')
        self.assertEqual(float(claims[1]), 0.5, 'documented DTS differs from 1710187 (0.5 s)')
        session = drilling_session()
        for upper in (12, -2):
            where = f'CYCLE83 drill_upper_z={upper}'
            values, _ = cycle_parameters(self, session, 'g83', 83, where, drill_upper_z=upper)
            self.assertEqual(number(values['DTB']), 0, where)
            self.assertEqual(number(values['DTS']), float(claims[1]), f'{where}: DTS differs from the comment')
            self.assertEqual((values['FRF'], values['VARI']), (claims[2], claims[3]),
                             f'{where}: FRF/VARI differ from the comment')
            self.assertEqual((values['FRF'], values['VARI']), ('1', '1'), f'{where}: FRF 1, VARI 1 (swarf removal)')

    @known_defect('PP-055', match='first peck')
    def test_cycle83_first_peck_is_continuous_across_z0(self):
        """INDEPENDENT: Siemens CYCLE83, FDPR is the first drilling depth relative to RFP.

        Two holes whose feed-start planes differ by 0.002 mm (drill_upper_z +0.001
        and -0.001) must get first pecks that differ by 0.002 mm. Above Z0 the PP
        writes RFP = upper - safety, at or below Z0 RFP = upper, and FDPR = down_step
        in both branches, so the first peck jumps by SDIS (-4.999 vs -3.001).
        Tolerance 0.001: one output step of the 3-decimal RFP.
        """
        session = drilling_session()
        pecks = {}
        for upper in (0.001, -0.001):
            values, _ = cycle_parameters(self, session, 'g83', 83, f'drill_upper_z={upper}', drill_upper_z=upper)
            pecks[upper] = first_peck_depth(values)
        self.assertAlmostEqual(pecks[0.001] - pecks[-0.001], 0.002, delta=0.001,
                               msg=f'first peck depth jumps across Z0: {pecks}')


class RigidTappingTests(unittest.TestCase):
    @covers('ENGINE-004')
    def test_cycle84_rigid_tapping_fields(self):
        """INDEPENDENT + CHARACTERIZATION: CYCLE84 rigid tapping for a CW tap.

        INDEPENDENT (Siemens CYCLE84): geometry as for every cycle, PIT = F/S = 1.5
        mm/rev (positive = right-hand), MPIT empty, SST = S, SDAC 3 or 5 (never M4
        after a right-hand tap), _AXN/_PTAB empty, _VARI empty/0 (single pass)
        without a step down, otherwise _VARI 1/2 with _DAM = Step_Down and _VRT =
        VarRetract when given.
        CHARACTERIZATION (PP choices): SDAC 3, SST1 = 2 x SST, _TECHNO 1221, DTB 0,
        POSS 0, the exact tail (nothing for a single pass), _VARI 1 (chip breaking
        rather than chip removal) and _VRT = Step_Down when VarRetract is 0
        (history-misc-05 correction: a PP fallback, not Siemens).
        """
        check_tapping_fields(self)

    def test_bea8c62_cycle84_reversion_is_detected(self):
        """INDEPENDENT: reverting the bea8c62 CYCLE84 hunk alone must fail the tapping guard.

        Before bea8c62 the positive branch wrote (RTP,,SDIS,DP,RFP,...): RFP empty,
        so the cycle rapids to SDIS instead of drill_upper_z, and DPR = rfp.
        """
        mutant = mutate(G84_FIX, G84_BEFORE_BEA8C62)
        assert_detected(self, lambda source: check_tapping_fields(self, source), mutant,
                        'bea8c62 CYCLE84 hunk reverted')

    @covers('PP-028')
    def test_left_hand_tap_uses_negative_pitch(self):
        """INDEPENDENT: Siemens CYCLE84, the sign of PIT selects the thread hand.

        A CCW (left-hand) tap needs PIT < 0; the machine's Vericut control maps
        PIT < 0 to ActiveSpindleDir CCW. Before a38f158 @drill never read
        tool_direction, so PIT = FEED/SPIN > 0 drove a left-hand tap as right-hand.
        Regression guard of PP-028 (fixed in a38f158); SDAC 4 for the left-hand tap
        is checked by tests/test_tapping_direction.py. If the pitch moves to MPIT,
        the sign of MPIT is used instead.
        """
        self.check_left_hand_tap()

    def check_left_hand_tap(self, source=None):
        session = drilling_session(source)
        values, _ = cycle_parameters(self, session, 'g84', 84, 'CCW tap', tool_direction='ccw', feed=150, spin=100)
        pitch = number(values['PIT']) if values['PIT'] != '' else number(values['MPIT'])
        self.assertLess(pitch, 0, f'thread hand: CCW tap programmed with pitch {pitch} (right-hand)')
        if values['PIT'] != '':
            self.assertEqual(abs(pitch), 1.5, '|PIT| must stay F/S = 1.5 mm/rev')

    def test_a38f158_reversion_is_detected(self):
        """INDEPENDENT: negative validation of the PP-028 guard. Reverting a38f158 in
        memory (every G84 tap takes the right-hand CYCLE84 line, whatever tool_direction)
        must make check_left_hand_tap fail with AssertionError."""
        anchor = "        if tool_direction eq CW then\n            {',0.,3,,',(FEED/SPIN)}"
        mutant = mutate(anchor, anchor.replace('if tool_direction eq CW then', 'if true then'))
        assert_detected(self, self.check_left_hand_tap, mutant, 'a38f158 reverted')

    @covers('ENGINE-004')
    def test_cycle84_arguments_are_numeric_and_ordered(self):
        """INDEPENDENT: Siemens CYCLE84 arguments are numeric or empty; a quote is a syntax error.

        The old line used ',0,''' (the engine lexed '' inside a literal as an escaped
        quote, so SST read "'500"); the @drill rewrite writes ',0,', so no literal
        reading can put a quote there. Regression guard of ENGINE-004.
        Fields: RTP 30, RFP 10, SDIS 2, DP -15, DPR empty, SDAC 3, PIT 625/500 = 1.25,
        POSS 0, SST 500, SST1 1000.
        """
        session = drilling_session()
        fields = cycle_arguments(self, drill(session, 'g84', feed=625, spin=500), 84)
        expected = {0: 30, 1: 10, 2: 2, 3: -15, 6: 3, 8: 1.25, 9: 0, 11: 1000}
        self.assertEqual({index: number(fields[index]) for index in expected}, expected, fields)
        self.assertEqual(fields[4], '', 'DPR must be empty when RFP/SDIS are used')
        quoted = [field for field in fields if "'" in field or '"' in field]
        self.assertEqual(quoted, [], f'quote character inside CYCLE84 arguments: {fields}')
        self.assertEqual(number(fields[10]), 500, 'SST')


class BoringCycleTests(unittest.TestCase):
    def test_right_hand_boring_tool_runs_m3(self):
        """INDEPENDENT: Siemens CYCLE86 SDIR 3 = M3 for a CW boring tool."""
        values, _ = cycle_parameters(self, drilling_session(), 'g86', 86, 'CW boring', tool_direction='cw')
        self.assertEqual(values['SDIR'], '3')

    @known_defect('PP-029', match='SDIR')
    def test_left_hand_boring_tool_runs_m4(self):
        """INDEPENDENT: Siemens CYCLE86 SDIR is the spindle direction (3 = M3, 4 = M4).

        A CCW boring tool must get SDIR 4, as @start_tool and @m_feed_spin map
        tool_direction CCW to M4; @drill hard-codes 3.
        """
        values, _ = cycle_parameters(self, drilling_session(), 'g86', 86, 'CCW boring', tool_direction='ccw')
        self.assertEqual(values['SDIR'], '4', 'SDIR for a CCW boring tool')


class ModalCycleTests(unittest.TestCase):
    def test_modal_cycle_is_cancelled_before_the_next_positioning(self):
        """INDEPENDENT: Sinumerik MCALL modal call; CHARACTERIZATION: G94 after tapping.

        One program with one drilling job per cycle (real end_of_job/start_of_job
        between them): one MCALL CYCLExx per job, the cycle is active at the hole
        block (X and Y both programmed, so dropping Y is visible), @end_drill prints
        exactly one bare MCALL, and the next positioning move runs without the modal
        cycle (otherwise every later move drills). @end_drill also restores G94
        after CYCLE84 (pin).
        """
        check_modal_cycle_cancel(self)

    @known_defect('PP-030', match='first hole')
    def test_first_drill_point_is_a_motion_block(self):
        """INDEPENDENT: Sinumerik runs an MCALL cycle only after a block with path motion.

        UNVERIFIED assumption: SolidCAM positions the tool over the first hole before
        @drill and does not flag X/Y as changed at the first @drill_point. Then
        @drill_point prints an empty block and the first hole is not drilled. The
        cycles were proven on the machine (bea8c62), which argues against it; a
        SolidCAM drilling trace or a Vericut run of a posted 2-hole job settles it.
        """
        session = drilling_session()
        session.ev('drill', (), **dict(DRILL_DEFAULTS, drill_type='g81', feed=150, spin=100, **HOLE))
        first = parse_blocks(session.ev('drill_point', (), xpos=HOLE['xpos'], ypos=HOLE['ypos']))
        self.assertTrue(any(block.is_motion for block in first),
                        f'first hole has no motion block after MCALL: {[b.raw for b in first]}')

    @known_defect('PP-031', match='argument list|stale cycle')
    def test_unknown_drill_type_is_rejected(self):
        """INDEPENDENT: a cycle call needs its parameter list and must be the requested cycle.

        After a G81 job, a drill_type the PP does not implement (g85, Siemens CYCLE85)
        must either stop the post (abort) or emit CYCLE85 with arguments. The PP
        prints the stale 'MCALL CYCLE81' without arguments (RTP=RFP=DP=0).
        Structural: the shipped VMID offers only the five implemented cycles
        (registry reachability), so SolidCAM cannot send g85 today.
        ENGINE-009: the engine stops at `input` as well as at `abort`, but in GPPL
        `input` only prompts and generation continues (engine-impl-critic-01
        correction). A stop therefore counts only if @drill contains an abort.
        """
        session = drilling_session()
        drill(session, 'g81')
        try:
            blocks = drill(session, 'g85')
        except UnsupportedGPPL as exc:
            if 'postprocessor stopped' not in str(exc):
                raise
            body = re.search(r'(?ms)^@drill\b.*?^endp\b', pp_source())
            self.assertTrue(body and re.search(r'(?im)^[ \t]*abort\b', body[0]),
                            f'stale cycle: @drill prompts without abort, so SolidCAM continues ({exc})')
            return
        calls = [block for block in blocks if block.has('MCALL')]
        self.assertTrue(calls, 'the g85 job was dropped without a cycle call or a stop')
        for block in calls:
            self.assertIsNotNone(block.cycle, f'MCALL without an argument list: {block.raw!r}')
            self.assertEqual(block.cycle[0], 'CYCLE85', f'stale cycle called for g85: {block.raw!r}')


class SpindleTests(unittest.TestCase):
    def test_spindle_start(self):
        """INDEPENDENT: Sinumerik M3 = CW, M4 = CCW; CYCLE84 owns the spindle when tapping.

        @start_tool prints M3/M4 by tool_direction and S; a tapping tool
        (d_drill_type D_Tapping) gets no M3/M4/M5 and no S (CYCLE84 SST starts it);
        @m_feed_spin programs only the new S (no dwell for a 200 rpm change is the
        PP's one-second threshold, CHARACTERIZATION); the restart after an M0
        between two same-tool jobs (VMID bStopM00) uses the tool's direction.
        """
        check_spindle_start(self)

    def test_spindle_acceleration_dwell(self):
        """INDEPENDENT: ramp time = dS / spindle_accel; CHARACTERIZATION: no dwell below 1 s.

        S0->S1000 and S8000->S3000 at the post's declared spindle_accel (@init_post,
        500 rpm/s) need a G4 of at least 2 s and 10 s; S900->S1000 gets none (PP
        threshold: one second of ramp). Whether the 828D needs a dwell at all is an
        MD35500 question (tc-03/tc-09 corrections).
        """
        check_spindle_acceleration_dwell(self)

    @known_defect('PP-011', match='active S')
    def test_spindle_speed_programmed_with_or_before_start(self):
        """INDEPENDENT: Sinumerik M3/M4 starts the spindle at the S active in that block.

        Second tool after a tool running S12000, with the post option
        bCoolspinaftertc = true (coolant and spindle directly after the tool
        change): the new tool's S1000 must be programmed in or before the M3 block.
        @start_tool runs with skipline = true, @usr_spindle_mcode_output prints M3
        without nb (it joins the MSG block) and S follows in a new block, so in
        single-block prove-out the new tool spins up to S12000.
        This path reproduces under either skipline semantics. On the default path
        (bCoolspinaftertc = false) @usr_ct_after sets skipline = false right before
        @start_tool, evidently to join S to the M3 block. Only the stock engine,
        which has no skipline joining (ENGINE-002), puts S in the next block there;
        with the GpplCompatEngine skipline emulation it prints
        'G0 G17 G90 G54 M8 M3 S1000'. The default path therefore depends on
        UNVERIFIED skipline semantics (ENGINE-002, efc-05) and is not used here.
        """
        session = Session(options=dict(bCoolspinaftertc=True))
        session.first_tool(spin=12000, spin_rate=12000)
        session.cut(10, 20, 5, -1)
        session.next_tool(2, 3, spin=1000, spin_rate=1000)
        replayed = replay(session.text())
        blocks = [block for block, _ in replayed]
        tool_change = last_index_of(blocks, lambda b: 6 in b.m)
        start = index_of(blocks, lambda b: bool(set(b.m) & {3, 4}), tool_change)
        self.assertNotEqual(start, -1, 'no spindle start after the second tool change')
        self.assertEqual(replayed[start][1].speed, 1000,
                         f'active S at the spindle start block {replayed[start][0].raw!r}')

    @known_defect('PP-026', match='dwell')
    def test_spindle_dwell_uses_configured_acceleration(self):
        """INDEPENDENT: ramp time = dS / acceleration, with the post's own spindle_accel.

        With spindle_accel = 250 rpm/s the first tool's start to S8000 needs at least
        8000/250 = 32 s; @usr_spindle_output gates the dwell with spindle_accel but
        computes it with the literal 500 (0.3 + 8000/500 = 16.3 s). Latent: the shipped
        spindle_accel is 500.
        """
        session = Session(options=dict(spindle_accel=250))
        blocks = parse_blocks(session.first_tool(spin=8000, spin_rate=8000))
        speed = index_of(blocks, lambda b: b.get('S') == 8000)
        self.assertNotEqual(speed, -1, [b.raw for b in blocks])
        self.assertGreaterEqual(dwell_seconds(blocks[speed:]), 8000 / 250,
                                f'dwell after S8000 at 250 rpm/s: {[b.raw for b in blocks[speed:]]}')


# --------------------------------------------------------------------------- mutation kills

GUARDS = {
    'cycle_geometry': check_cycle_geometry,
    'drill_continuity': check_drill_continuity,
    'tapping_fields': check_tapping_fields,
    'modal_cycle_cancel': check_modal_cycle_cancel,
    'spindle_start': check_spindle_start,
    'spindle_acceleration_dwell': check_spindle_acceleration_dwell,
}

# (name, guard, old, new, occurrences of old). Each must fail its guard with AssertionError.
MUTATIONS = (
    ('end_drill_no_mcall_cancel', 'modal_cycle_cancel', "        {nb, 'MCALL '}\n", '', 1),
    # Killed only under the default 'clear' flag policy. With 'persist' the init
    # assignment's flag stays raised and the mutant is equivalent (ENGINE-001;
    # TSR-15 verifier: the iDrillmode flag is never consumed).
    ('end_drill_mode_never_changes', 'modal_cycle_cancel', '    iDrillmode = 80\n', '    iDrillmode = 9999\n', 1),
    ('end_drill_no_g94_after_tap', 'modal_cycle_cancel',
     "    if drill_type eq G84\n        {nb, 'G94'}\n",
     "    if drill_type eq G84\n    endif\n    if false\n        {nb, 'G94'}\n", 1),
    ('drill_point_drops_y', 'modal_cycle_cancel',
     "{nb,['X'xpos ' '], ['Y'ypos ' '], ['Z'zpos ' ']}", "{nb,['X'xpos ' '], ['Z'zpos ' ']}", 1),
    ('cycle_feed_not_programmed', 'cycle_geometry', "    {nb,' F'feed }\n", '', 1),
    ('nonpositive_rfp_shifted', 'cycle_geometry',
     "        {' (',rtp,','drill_upper_z,',,',dp,',','0.'}\n", "        {' (',rtp,','rfp,',,',dp,',','0.'}\n", 1),
    ('cycle86_spindle_mode_lost', 'cycle_geometry', "        {',,3'}\n", "        {',,'}\n", 1),
    ('cycle84_variable_retract_ignored', 'tapping_fields',
     "{',1,'Step_Down:feed_f ',' VarRetract:feed_f}", "{',1,'Step_Down:feed_f ',' Step_Down:feed_f}", 1),
    ('tapping_tool_starts_spindle', 'spindle_start',
     '    if d_drill_type ne D_Tapping\n', "    if d_drill_type ne 'never'\n", 1),
    ('start_tool_direction_swapped', 'spindle_start',
     '(SST).\n    if tool_direction eq CW then\n'
     '        iSpindleDir = 3\n    else\n        iSpindleDir = 4',
     '(SST).\n    if tool_direction eq CW then\n'
     '        iSpindleDir = 4\n    else\n        iSpindleDir = 3', 1),
    ('m_feed_spin_direction_swapped', 'spindle_start',
     '@m_feed_spin\n    ; Handle output for spindle change\n    if tool_direction eq CW then\n        iSpindleDir = 3',
     '@m_feed_spin\n    ; Handle output for spindle change\n    if tool_direction eq CW then\n        iSpindleDir = 4', 1),
    ('spindle_dwell_threshold_inverted', 'spindle_acceleration_dwell',
     '    if sdiff > spindle_accel\n', '    if sdiff < spindle_accel\n', 1),
)


class MutationKillTests(unittest.TestCase):
    @covers('ENGINE-001')
    def test_guards_detect_mutations(self):
        """INDEPENDENT: every drill/spindle guard fails with AssertionError on its mutation.

        Mutants are built in memory with support.mutation.mutate (a missing anchor
        raises StaleAnchor); errors other than AssertionError propagate.
        ENGINE-001: end_drill_mode_never_changes is killed only under the Session's
        default 'clear' flag policy (see its table comment).
        """
        for name, guard, old, new, count in MUTATIONS:
            with self.subTest(mutation=name):
                mutant = mutate(old, new, count=count)
                assert_detected(self, lambda source, check=GUARDS[guard]: check(self, source), mutant, name)

    def test_guards_pass_on_current_source_through_the_mutation_path(self):
        """INDEPENDENT: the guards pass on the unmodified GPP passed as an explicit source."""
        source = pp_source()
        for name, check in GUARDS.items():
            with self.subTest(guard=name):
                check(self, source)


if __name__ == '__main__':
    unittest.main()
