"""Rotary (A axis) output of Gmill_540v_4x.gpp.

Scope (area B): the position calculation @usr_r1pos_calc, the direction choice
@usr_r1_select_dir, the output @usr_r1_output, and the rotary parts of the CAM
events that call them (@move_5x/@line_5x, @move_4x/@line_4x, @fourth_axis,
@tmatrix, the tool-change rapid), the bLimit_3axis machine parameter and
@home_data.

Oracles used below (each test names the one it relies on):
* Sinumerik 828D modulo rotary axis. A=DC(v) is an absolute move along the
  shortest path, A=ACP(v) an absolute move in the positive direction, A=ACN(v)
  an absolute move in the negative direction. At exactly 180 deg the DC
  direction is the control's tie-break rule, which need not match the CAM
  direction (verifier correction to history-rotary-04). The program range of
  DC/ACP/ACN is 0 <= v < 360 (alarm 16830 otherwise); whether 360 itself is
  accepted is uncertain (correction to history-rotary-07); 6228b3d posts 0
  instead (PP-002 facets whole-turn and rounding, fixed). The A axis is
  modulo: commit 8966d35 says so, and Vericut models it as mmABSOLUTE_360.
* The post cannot know the machine A position at program start, so the first A
  word must be DC (commits ab853be, ad2537a). After that every A move needs an
  explicit direction (bff5ed0).
* Recorded SolidCAM data (tests/fixtures/shit2_contiguous_link.json): apos
  0 -> 3.035 arrives with dir5a='ccw' and is posted as A=ACP(3.035). So 'ccw'
  means increasing apos, and with the shipped iR1dir=-1 the machine A is +apos.
  This backs the dir5a mapping only. The same cw->ACN / ccw->ACP mapping for
  angle_4x_around_x_dir (index moves) is bff5ed0's design; no recorded data
  shows what that input means, so tests that rely on it pin commit intent
  (corrections to history-rotary-03 and pp-region-4-cycles-rotary-09).
* The machine angle is (-angle) * iR1dir summed over the CoordSys (tmatrix),
  4x-transform, cpos and apos contributions (GPP @usr_r1pos_calc). Only the
  apos sign is backed by recorded data (the shit2 and slide fixtures exercise
  apos alone); the equal sign of the other three contributions is the GPP's
  convention, so expected values that depend on it are CHARACTERIZATION.
  Option docs: GPP @usr_ip_useroptions, L165-173.
* VMID: A turns about X (VecX=1), RotaryAxisPrecision=0.001; nR1pos_f '7.3'.
* Z must be retracted while A turns: every A word below is checked to execute
  with Z at its G75 reference point and not programmed since (modal replay).

Known defects use the shared @known_defect marker (tests/support/markers.py)
and design questions use @covers pins. Defects fixed by the owner's GPP
commits (PP-002 whole-turn/rounding in 6228b3d, PP-007 in ca63502) keep their
former canonical tests as regression guards (FixedRotaryDefectGuards, @covers).
Regression guards take an optional GPP source;
RotaryRegressionTests.test_reversions_are_detected applies each reverted fix or
mutation in memory and requires an AssertionError.
"""
import random
import unittest

from pp_tests.engine import UnsupportedGPPL
from support import (AUTO, GpplCompatEngine, Session, adopt_state, assert_detected, covers, event,
                     index_of, known_defect, motion_engine, mutate, parse_blocks, replay,
                     rotary_engine, state_before)

# Half of the 0.001 deg output resolution (VMID RotaryAxisPrecision, nR1pos_f '7.3').
RESOLUTION = 0.0005


# --------------------------------------------------------------------------- helpers

def rotary_words(text):
    """[(mode, value)] of every A word in NC text, in block order.

    mode is 'ACP', 'ACN', 'DC' or None for a plain 'A90' word.
    """
    return [block.rotary('A') for block in parse_blocks(text) if block.rotary('A') is not None]


def output_of(engine):
    return ''.join(engine.output)


def homed_before_first_rotary(text):
    """True if the first A word of text turns A with Z retracted.

    Modal replay (support.modal): Z was sent to its reference point by a G75
    Z1= block and has not been programmed since, neither before nor in the A
    block. A G75 somewhere earlier followed by a Z move does not count.
    """
    replayed = replay(text)
    blocks = [block for block, _ in replayed]
    first = index_of(blocks, lambda block: block.rotary('A') is not None)
    if first < 0:
        return False
    return 'Z' in state_before(replayed, first).homed and 'Z' not in blocks[first].axes


def congruent(value, expected):
    """value and expected denote the same modulo-360 position within the resolution."""
    return abs((value - expected + 180) % 360 - 180) <= RESOLUTION


def five_x_job(session, apos, direction='ccw'):
    """First rapid at the job angle, plunge, retract (SolidCAM 5x/4x simultaneous job)."""
    session.ev('move_5x', ('xpos', 'ypos', 'zpos', 'apos'), xpos=12, ypos=23, zpos=35,
               apos=apos, dir5a=direction)
    session.ev('line_5x', ('zpos', 'feed'), zpos=-2, feed_type='feed_cut')
    session.ev('line_5x', ('zpos',), zpos=35, feed_type='feed_cut')


def r1_output(engine):
    """Run @usr_r1pos_calc + @usr_r1_output on a rotary_engine and return the A words."""
    engine.output.clear()
    engine.call('usr_r1pos_calc')
    engine.call('usr_r1_output')
    return rotary_words(output_of(engine))


# --------------------------------------------------------------------------- checks

class RotaryChecks:
    """Guards shared by the tests and by the reversion table (source=None: tested GPP)."""

    def assert_stops_with_post_error(self, engine, run, context=''):
        """run() must stop the post with its POST ERROR guard.

        The stock engine stops at `input` (the exception carries the prompt); with
        GPPL semantics `input` continues, the POST ERROR line is printed and `abort`
        stops (ENGINE-009). Either way 'POST ERROR' is in the stop message or output.
        """
        start = len(engine.output)
        with self.assertRaises(UnsupportedGPPL, msg=context) as stop:
            run()
        self.assertIn('POST ERROR', str(stop.exception) + ''.join(engine.output[start:]), context)

    # ab853be + ad2537a (+ the efc initial-DC session check and the TSR A=DC check)
    def check_program_start_forces_dc(self, source=None):
        session = Session(source=source)
        session.first_tool()
        start = session.text()
        words = rotary_words(start)
        self.assertTrue(words, f'no A word at the first tool change: {start!r}')
        self.assertEqual(words[0], ('DC', 0.0), f'first A word of the program must be DC: {start!r}')
        self.assertTrue(homed_before_first_rotary(start), start)
        self.assertFalse(session.state['br1forceoutput'])
        # Afterwards the A position is known: every move carries an explicit direction.
        five_x_job(session, 0)
        mark = session.mark()
        session.ev('move_5x', ('apos', 'zpos'), apos=90, dir5a='ccw', zpos=20)
        session.ev('line_5x', ('apos', 'xpos'), apos=80, dir5a='cw', xpos=30)
        self.assertEqual(rotary_words(session.text(mark)), [('ACP', 90.0), ('ACN', 80.0)],
                         session.text(mark))
        # A changed first target (CoordSys index at program start) with a known index
        # direction is still DC, not a direction guessed from an unknown start. (The
        # value 45.125 follows the GPP's CoordSys sign convention, see the module
        # docstring; the mode DC is what this guard is about.)
        session = Session(source=source, angle_4x_around_x_dir='cw')
        session.first_tool(tmatrix=45.125)
        self.assertEqual(rotary_words(session.text()), [('DC', 45.125)], session.text())
        self.assertTrue(homed_before_first_rotary(session.text()), session.text())

    # bff5ed0: the tool-change rapid branch
    def check_toolchange_rapid_emits_changed_a(self, source=None):
        for direction, mode in (('ccw', 'ACP'), ('cw', 'ACN')):
            engine = motion_engine(source)
            engine.set(bTlchg=True, bR1forceOutput=False, nPR1pos=0, bFirstMove=True,
                       bJobPositioned=False, bIndexClearancePending=True)
            text = event(engine, 'move_5x', ('apos', 'xpos', 'ypos', 'zpos'), apos=90,
                         dir5a=direction, xpos=12, ypos=23, zpos=40)
            # One A word with an explicit direction (a plain 'A90' would be (None, 90.0)).
            self.assertEqual(rotary_words(text), [(mode, 90.0)], text)
            blocks = parse_blocks(text)
            rotary = index_of(blocks, lambda block: block.rotary('A') is not None)
            self.assertIn(0, blocks[rotary].g, text)
            self.assertTrue(homed_before_first_rotary(text), text)
            # The following cut at the same angle neither repeats nor needs the rotation.
            text = event(engine, 'line_5x', ('xpos', 'zpos'), xpos=15, zpos=5)
            self.assertEqual(rotary_words(text), [], text)

    # bff5ed0: index moves take their direction from the index, never from a stale dir5a
    def check_index_direction_ignores_stale_dir5a(self, source=None):
        for index_dir, stale_dir5a, mode in (('ccw', 'cw', 'ACP'), ('cw', 'ccw', 'ACN')):
            engine = motion_engine(source)
            engine.set(bR1forceOutput=False, opposite_z_angle_const_y=0)
            cut = event(engine, 'line_5x', ('apos',), apos=10, dir5a=stale_dir5a)
            self.assertEqual(len(rotary_words(cut)), 1, cut)
            event(engine, 'end_of_job')   # the 5x job ends; the next job starts with an index
            text = event(engine, 'fourth_axis', angle=90, angle_4x_around_x_dir=index_dir)
            self.assertEqual(rotary_words(text), [(mode, 90.0)], (index_dir, text))
            self.assertTrue(homed_before_first_rotary(text), text)
        # tmatrix index between jobs (apos back at 0 for the indexed job)
        engine = motion_engine(source)
        engine.set(bR1forceOutput=False)
        event(engine, 'line_5x', ('apos',), apos=10, dir5a='ccw')
        event(engine, 'end_of_job')
        event(engine, 'tmatrix', angle_4x_around_x=90, apos=0)
        text = event(engine, 'start_of_job', angle_4x_around_x_dir='cw')
        self.assertEqual(rotary_words(text), [('ACN', 90.0)], text)
        self.assertTrue(homed_before_first_rotary(text), text)

    # 8966d35 contract, guaranteed since bff5ed0
    def check_half_turn_moves_have_explicit_direction(self, source=None):
        cases = [
            ('move_5x', 0, 180, 'ccw', ('ACP', 180.0)),
            ('move_5x', 0, 180, 'cw', ('ACN', 180.0)),
            ('line_5x', 10, 190, 'ccw', ('ACP', 190.0)),
            ('line_5x', 350, -190, 'cw', ('ACN', 170.0)),  # crosses 0: -190 deg is position 170
            ('line_5x', 90, -90, 'cw', ('ACN', 270.0)),
        ]
        for procedure, previous, apos, direction, expected in cases:
            engine = motion_engine(source)
            engine.set(bR1forceOutput=False, nPR1pos=previous)
            text = event(engine, procedure, ('apos',), apos=apos, dir5a=direction)
            self.assertEqual(rotary_words(text), [expected], (procedure, previous, apos, direction, text))
        engine = motion_engine(source)
        engine.set(bR1forceOutput=False, bR1useDir5a=False, nPR1pos=0, opposite_z_angle_const_y=0)
        text = event(engine, 'fourth_axis', angle=180, angle_4x_around_x_dir='cw')
        self.assertEqual(rotary_words(text), [('ACN', 180.0)], text)
        # Without a known direction a half turn must stop the post, never be emitted.
        for direction in ('', 'none'):
            engine = motion_engine(source)
            engine.set(bR1forceOutput=False, nPR1pos=0)
            self.assert_stops_with_post_error(
                engine, lambda: event(engine, 'line_5x', ('apos',), apos=180, dir5a=direction), repr(direction))

    # bff5ed0: 4x events select ACP/ACN from dir5a and restore bR1useDir5a
    def check_4x_events_take_direction_from_dir5a(self, source=None):
        for procedure in ('line_4x', 'move_4x'):
            for dir5a, index_dir, mode in (('ccw', 'cw', 'ACP'), ('cw', 'ccw', 'ACN')):
                engine = motion_engine(source)
                # Outside the 4x/5x wrappers the post keeps bR1useDir5a false.
                engine.set(bR1useDir5a=False, bR1forceOutput=False)
                text = event(engine, procedure, ('cpos',), cpos=30, dir5a=dir5a,
                             angle_4x_around_x_dir=index_dir)
                self.assertEqual(rotary_words(text), [(mode, 30.0)], f'{procedure} dir5a={dir5a}: {text!r}')
                self.assertFalse(engine.state['br1usedir5a'], f'{procedure} must restore bR1useDir5a=false')

    # 77c03c6: @home_data must not write settable frames
    def check_home_data_writes_no_frames(self, source=None):
        session = Session(source=source)
        text = session.ev('home_data', home_user_name='P2', position=2, home_number=2,
                          shift_x=10, shift_y=-5, shift_z=3, y_angle_const_z=30)
        frame_words = [word.raw for block in parse_blocks(text) for word in block.words
                       if word.raw.startswith('$P_') or word.address in ('CTRANS', 'TRANS', 'ATRANS', 'ROT', 'AROT')]
        self.assertEqual(frame_words, [], text)

    # properties (test-suite-review) ------------------------------------------
    def check_contributions_compose_modulo_360(self, source=None):
        rng = random.Random(1729)
        mismatches = []
        samples = 0
        for _ in range(120):
            parts = [round(rng.uniform(-90, 90), 3) for _ in range(4)]
            total = sum(parts)
            if abs(total) < 0.01 or abs(abs(total) - 360) < 0.01:
                continue  # near-zero sums and whole turns: FixedRotaryDefectGuards (PP-002, fixed)
            samples += 1
            transform, angle, cpos, apos = parts
            engine = rotary_engine(source, angle_4x_around_x=transform, angle=angle, cpos=cpos,
                                   apos=apos, bR1forceOutput=True)
            words = r1_output(engine)
            expected = total % 360
            if abs(engine.state['nr1pos'] - expected) > 1e-9:
                mismatches.append(f'{parts}: nR1pos {engine.state["nr1pos"]} != {expected}')
            elif len(words) != 1 or words[0][0] != 'DC' or abs(words[0][1] - round(expected, 3)) > 1e-6:
                mismatches.append(f'{parts}: emitted {words}, expected DC({round(expected, 3)})')
        self.assertGreater(samples, 100)
        self.assertEqual(mismatches, [])

    def check_signed_travel_equals_cam_step(self, source=None):
        rng = random.Random(42)
        engine = motion_engine(source)
        engine.set(apos=0, nPR1pos=0)
        current, cam, steps, mismatches = 0.0, 0.0, 0, []
        for step_number in range(200):
            step = round(rng.choice([-1, 1]) * rng.uniform(0.5, 120), 3)
            if abs(cam + step) >= 359 or abs(cam + step) < 0.01:
                continue  # stay inside one turn (whole turns: FixedRotaryDefectGuards)
            cam = round(cam + step, 3)
            steps += 1
            text = event(engine, 'line_5x', ('apos',), apos=cam, dir5a='ccw' if step > 0 else 'cw')
            words = rotary_words(text)
            if len(words) != 1 or words[0][0] not in ('ACP', 'ACN'):
                mismatches.append(f'step {step_number}: {text!r}')
                continue
            mode, target = words[0]
            travel = (target - current) % 360 if mode == 'ACP' else -((current - target) % 360)
            if not 0 <= target < 360 or abs(travel - step) > 1e-6:
                mismatches.append(f'step {step_number}: CAM step {step} posted as {mode}({target}) from {current}')
            current = target
        self.assertGreater(steps, 150)
        self.assertEqual(mismatches, [])

    def check_unchanged_position_is_not_reemitted(self, source=None):
        engine = motion_engine(source)
        sequence = [(10, 'ccw', 1), (10, 'ccw', 0), (-5, 'cw', 1), (-5, 'cw', 0)]
        counts = []
        for number, (apos, direction, _) in enumerate(sequence):
            # AUTO: SolidCAM flags exactly the inputs whose value changed (apos only on
            # the 1st and 3rd step, X on every step).
            text = event(engine, 'line_5x', AUTO, xpos=20 + number, apos=apos, dir5a=direction)
            counts.append(len(rotary_words(text)))
        self.assertEqual(counts, [expected for _, _, expected in sequence])

    # design pins -------------------------------------------------------------
    def check_toolchange_zeroes_cam_apos(self, source=None):
        def two_tools():
            session = Session(source=source)
            session.first_tool()
            five_x_job(session, 37)
            session.next_tool(2, 3)
            five_x_job(session, 37)
            return session

        session = two_tools()
        mark = session.mark()
        session.next_tool(3, 4)
        toolchange = session.text(mark)
        self.assertEqual(rotary_words(toolchange), [('ACN', 0.0)], toolchange)
        self.assertEqual(session.state['apos'], 0)
        self.assertTrue(homed_before_first_rotary(toolchange), toolchange)
        mark = session.mark()
        five_x_job(session, 37)
        rewind = session.text(mark)
        self.assertEqual(rotary_words(rewind), [('ACP', 37.0)], rewind)
        self.assertTrue(homed_before_first_rotary(rewind), rewind)
        # The unwind direction comes from angle_4x_around_x_dir: neither cw nor ccw stops the post.
        session = two_tools()
        self.assert_stops_with_post_error(
            session.engine, lambda: session.next_tool(3, 4, angle_4x_around_x_dir=''), 'empty index direction')

    def check_secondary_rotation_adds_no_extra_rotation(self, source=None):
        for setup in ({'x_angle_const_z': 90}, {'bpos': 90}):
            # Both flags reach the vertical-head branch (HVV, zpos_f); only bTlchg also
            # reaches the tool-change G0 block, because @usr_rapid clears bFirstRapid
            # first (correction to history-rotary-06).
            for first in ('bFirstRapid', 'bTlchg'):
                # GpplCompatEngine renders the historical '5.4(*-1)' Z format (ENGINE-018),
                # so a re-enabled Z inversion shows up as wrong Z values.
                engine = adopt_state(motion_engine(), source, GpplCompatEngine)
                engine.set(bFirstVert=True, bFirstMove=True, bJobPositioned=False,
                           bIndexClearancePending=True, bR1forceOutput=True, **{first: True}, **setup)
                text = event(engine, 'move_5x', ('xpos', 'ypos', 'zpos'), xpos=12, ypos=23, zpos=34, apos=0)
                text += event(engine, 'move_5x', ('zpos',), zpos=5)
                text += event(engine, 'line_5x', ('xpos', 'zpos'), xpos=15, zpos=-3)
                blocks = parse_blocks(text)
                extra = [word.raw for block in blocks for word in block.words
                         if word.address in ('B', 'HVV', 'HVH', 'ROT', 'AROT')]
                self.assertEqual(extra, [], (setup, first, text))
                z_values = [block.axes['Z'] for block in blocks if 'Z' in block.axes]
                self.assertEqual(z_values[-2:], [5.0, -3.0], (setup, first, text))
                self.assertNotIn('*', engine.state['zpos_f'], (setup, first))


# --------------------------------------------------------------------------- regression guards

# Focused semantic undos of fixes (commit) and mutations of guarded rules:
# (label, commit or 'mutation', check method, [(old, new, count)]).
REVERSIONS = [
    ('init_post no longer arms the DC output', 'ab853be', 'check_program_start_forces_dc', [
        ('    bR1forceOutput = true\n', '    bR1forceOutput = false\n', 1)]),
    ('direction selected before the initial DC force', 'ad2537a', 'check_program_start_forces_dc', [
        ('    if bR1forceOutput\n        iR1dirMode = 3\n    else\n        if change(nR1pos)\n'
         '            call @usr_r1_select_dir\n        endif\n    endif\n',
         '    if change(nR1pos)\n        call @usr_r1_select_dir\n    else\n        if bR1forceOutput\n'
         '            iR1dirMode = 3\n        endif\n    endif\n', 1)]),
    ('tool-change rapid emits plain A<pos>', 'bff5ed0', 'check_toolchange_rapid_emits_changed_a', [
        ("    if change(nR1pos) or bR1forceOutput\n        call @usr_r1_output\n",
         "    if change(nR1pos) or bR1forceOutput\n        {cR1,nR1pos ' '}\n", 1)]),
    ('tool-change rapid drops a changed A', 'bff5ed0', 'check_toolchange_rapid_emits_changed_a', [
        ("    if change(nR1pos) or bR1forceOutput\n        call @usr_r1_output\n",
         "    if change(nR1pos) or bR1forceOutput\n        iR1dirMode = 0\n", 1)]),
    ('index direction words swapped', 'bff5ed0', 'check_index_direction_ignores_stale_dir5a', [
        ('        if angle_4x_around_x_dir eq cw\n            iR1dirMode = 1\n        else\n'
         '            if angle_4x_around_x_dir eq ccw\n                iR1dirMode = 2',
         '        if angle_4x_around_x_dir eq cw\n            iR1dirMode = 2\n        else\n'
         '            if angle_4x_around_x_dir eq ccw\n                iR1dirMode = 1', 1)]),
    ('index moves use dir5a', 'bff5ed0', 'check_index_direction_ignores_stale_dir5a', [
        ('    if bR1useDir5a\n        if dir5a eq cw', '    if true\n        if dir5a eq cw', 1)]),
    ('4x/5x wrappers do not reset bR1useDir5a', 'bff5ed0', 'check_index_direction_ignores_stale_dir5a', [
        ('    bR1useDir5a = false\n', '', 4)]),
    # Synthetic: the real 8966d35^ emitted a plain A180, not DC (correction to history-rotary-04).
    ('directed moves become shortest-path DC (8966d35 contract)', 'mutation',
     'check_half_turn_moves_have_explicit_direction', [
        ('    if bR1useDir5a\n        if dir5a eq cw\n            iR1dirMode = 1',
         '    iR1dirMode = 3\n    if false\n        if dir5a eq cw\n            iR1dirMode = 1', 1),
        ('        if angle_4x_around_x_dir eq cw\n            iR1dirMode = 1\n        else\n'
         '            if angle_4x_around_x_dir eq ccw\n                iR1dirMode = 2\n            endif\n        endif\n',
         '', 1)]),
    ('unknown dir5a defaults to ACP', 'bff5ed0', 'check_half_turn_moves_have_explicit_direction', [
        ('            if dir5a eq ccw\n                iR1dirMode = 2\n            endif\n',
         '            iR1dirMode = 2\n', 1)]),
    ('line_4x does not select dir5a', 'mutation', 'check_4x_events_take_direction_from_dir5a', [
        ('    bR1useDir5a = true\n    call @usr_line\n    bR1useDir5a = false\nendp\n\n@chng_tool_cnext',
         '    call @usr_line\n    bR1useDir5a = false\nendp\n\n@chng_tool_cnext', 1)]),
    ('move_4x does not select dir5a', 'mutation', 'check_4x_events_take_direction_from_dir5a', [
        ('    bR1useDir5a = true\n    call @usr_rapid\n    bR1useDir5a = false\nendp\n\n@line_4x',
         '    call @usr_rapid\n    bR1useDir5a = false\nendp\n\n@line_4x', 1)]),
    ('line_4x leaks bR1useDir5a=true', 'mutation', 'check_4x_events_take_direction_from_dir5a', [
        ('    bR1useDir5a = true\n    call @usr_line\n    bR1useDir5a = false\nendp\n\n@chng_tool_cnext',
         '    bR1useDir5a = true\n    call @usr_line\nendp\n\n@chng_tool_cnext', 1)]),
    # The commented-out template block was deleted (fixup round): inject its four output statements
    # (signs folded into the plain shift values) into the now empty @home_data.
    ('CTRANS frame writes re-enabled', '77c03c6', 'check_home_data_writes_no_frames', [
        ("    ; offset comes from @home_number; no frame (CTRANS) is written.\nendp\n",
         "    ; offset comes from @home_number; no frame (CTRANS) is written.\n"
         "    {nl,'$P_UIFR['(position + home_number + 2)']= CTRANS( X,'shift_x:'5.3'}\n"
         "    {', Y,'shift_y:'5.3'}\n"
         "    {', Z,'shift_z:'5.3'}\n"
         "    {', B,0',')',cCb,'G',(position + home_number + 502)}\n"
         "endp\n", 1)]),
    ('HVV head macro re-enabled', '77c03c6', 'check_secondary_rotation_adds_no_extra_rotation', [
        ('            call @usr_head_home_select\n            bVertical = true\n',
         "            call @usr_head_home_select\n            {nb, 'HVV'}\n            bVertical = true\n", 1)]),
    ('Z inversion re-enabled', '77c03c6', 'check_secondary_rotation_adds_no_extra_rotation', [
        ('            call @usr_head_home_select\n            bVertical = true\n',
         "            call @usr_head_home_select\n            zpos_f = '5.4(*-1)'\n            bVertical = true\n", 1)]),
    ('tool change keeps the CAM apos', 'mutation', 'check_toolchange_zeroes_cam_apos', [
        ('            change(nRapidfeed) = true\n            apos = 0\n', '            change(nRapidfeed) = true\n', 1)]),
    ('4x-transform angle sign flipped', 'mutation', 'check_contributions_compose_modulo_360', [
        ('    nR1postransform = (-angle) * iR1dir', '    nR1postransform = (angle) * iR1dir', 1)]),
    ('cpos contribution dropped', 'mutation', 'check_contributions_compose_modulo_360', [
        ('    nR1poscpos = (-cpos) * iR1dir', '    nR1poscpos = 0', 1)]),
    ('dir5a words swapped', 'mutation', 'check_signed_travel_equals_cam_step', [
        ('        if dir5a eq cw\n            iR1dirMode = 1', '        if dir5a eq cw\n            iR1dirMode = 2', 1)]),
    ('unchanged position re-emitted', 'mutation', 'check_unchanged_position_is_not_reemitted', [
        ('    if nPR1pos ne nR1pos\n        change(nR1pos) = TRUE\n', '    if true\n        change(nR1pos) = TRUE\n', 1)]),
]


class RotaryRegressionTests(RotaryChecks, unittest.TestCase):
    def test_program_start_forces_dc(self):
        """INDEPENDENT: the post cannot know the machine A position at program start
        (previous program, manual jog), so the first A word must be the absolute
        shortest-path A=DC(..) (ab853be, ad2537a); also for a CoordSys index at
        program start whose direction is known. Afterwards every move carries ACP/ACN.
        Runs a Session from @init_post, because the legacy presets pin
        bR1forceOutput=False."""
        self.check_program_start_forces_dc()

    def test_toolchange_rapid_emits_changed_a(self):
        """INDEPENDENT: bff5ed0 'Force explicit A-axis direction output': a changed
        A in the tool-change rapid is a G0 ACP/ACN word executed with Z retracted,
        never a plain 'A90' (a plain position on a modulo axis takes the shortest
        path, so the CAM direction is lost). dir5a 'ccw' = ACP (recorded shit2 data).
        STRUCTURAL guard: the bTlchg branch of @usr_rapid is driven directly through
        @move_5x. On HEAD SolidCAM reaches that branch from @start_of_job via
        @usr_ct_after (e.g. the third tool change after a 5x job, see the DESIGN-005
        pin), where the direction comes from angle_4x_around_x_dir instead."""
        self.check_toolchange_rapid_emits_changed_a()

    def test_index_direction_ignores_stale_dir5a(self):
        """INDEPENDENT (commit intent, bff5ed0) for the direction SOURCE: @fourth_axis
        and tmatrix indexes take ACP/ACN from angle_4x_around_x_dir, never from the
        dir5a left over by the previous 5x job. CHARACTERIZATION for the mapping
        itself: cw -> ACN / ccw -> ACP for angle_4x_around_x_dir is bff5ed0's design
        (a consistency pin with the dir5a mapping); no recorded data shows what that
        input means (corrections to history-rotary-03, pp-region-4-cycles-rotary-09).
        The expected 90 follows the GPP sign convention for the CoordSys/transform
        angle. Canonical index-direction test."""
        self.check_index_direction_ignores_stale_dir5a()

    def test_half_turn_moves_have_explicit_direction(self):
        """INDEPENDENT: 8966d35 'Guard ambiguous A-axis modulo moves' and bff5ed0:
        at exactly 180 deg the direction of a DC move is the control's tie-break
        rule, which need not match the CAM direction, so half turns carry ACP/ACN
        (dir5a mapping: recorded shit2 data; the @fourth_axis case relies on the
        bff5ed0 angle_4x_around_x_dir mapping, a commit-intent pin). A half turn
        without a known direction stops the post (POST ERROR) instead of guessing;
        that part is a structural guard, because whether SolidCAM ever sends a dir5a
        other than cw/ccw on a changed A is unverified."""
        self.check_half_turn_moves_have_explicit_direction()

    def test_4x_events_take_direction_from_dir5a(self):
        """INDEPENDENT: bff5ed0 made the 4x/5x events select ACP/ACN from dir5a
        (ccw = ACP, recorded shit2 data) and restore bR1useDir5a=false. The rotary
        input of @move_4x/@line_4x is cpos (the Mach3 sibling template prints
        A=cpos there). UNVERIFIED reachability: whether SolidCAM emits 4x events for
        this VMID (the PP-007 settle question) and whether it populates dir5a in them (correction to
        pp-region-4-cycles-rotary-03); this guards the GPP rule itself."""
        self.check_4x_events_take_direction_from_dir5a()

    def test_home_data_writes_no_frames(self):
        """INDEPENDENT: 77c03c6 removed the settable-frame writes ($P_UIFR[..] =
        CTRANS(..)) from @home_data; c85f5f7 maps every CoordSys to one origin
        (DESIGN-006), so @home_data must not write frames."""
        self.check_home_data_writes_no_frames()

    def test_reversions_are_detected(self):
        """INDEPENDENT: each entry of REVERSIONS reverts one fix (commit intent) or
        mutates one guarded rule in memory; its guard must fail with AssertionError.
        Interpreter errors propagate (support.mutation.assert_detected)."""
        for label, commit, check, edits in REVERSIONS:
            with self.subTest(reversion=label, commit=commit):
                mutant = None
                for old, new, count in edits:
                    mutant = mutate(old, new, source=mutant, count=count)
                assert_detected(self, getattr(self, check), mutant, f'{commit}: {label}')


class RotaryPropertyTests(RotaryChecks, unittest.TestCase):
    def test_all_four_contributions_compose_modulo_360(self):
        """INDEPENDENT for the reduction: modulo arithmetic and the 828D range put
        the summed angle into [0, 360) and the '7.3' format rounds it to 0.001; the
        forced output is one DC word. CHARACTERIZATION for the composition: with
        iR1dir=-1 the GPP adds the CoordSys, 4x-transform, cpos and apos angles with
        the same sign (@usr_r1pos_calc); only the apos sign is backed by recorded
        data. Procedure-level property: SolidCAM may never send all four non-zero
        together. 120 seeded samples, near-zero sums and whole turns excluded (they
        are FixedRotaryDefectGuards cases)."""
        self.check_contributions_compose_modulo_360()

    def test_signed_travel_equals_cam_step_along_a_random_walk(self):
        """INDEPENDENT: Sinumerik ACP travels +, ACN travels - on a modulo axis, so
        the signed travel from the previous position is (target-current) mod 360
        for ACP and -((current-target) mod 360) for ACN; it must equal the CAM step
        (dir5a 'ccw' accompanies increasing apos, recorded shit2 data). 200-step
        seeded walk inside one turn (whole turns: FixedRotaryDefectGuards)."""
        self.check_signed_travel_equals_cam_step()

    def test_unchanged_position_is_not_reemitted(self):
        """INDEPENDENT: geometry and the GPP change rule (change(nR1pos) against the
        previously programmed position): a repeated A target needs no A word, a
        changed one exactly one. Sub-resolution changes are PP-046 and not used here."""
        self.check_unchanged_position_is_not_reemitted()


class RotaryDirectionTests(unittest.TestCase):
    def assert_direction_matches_machine_motion(self, ir1dir):
        # SolidCAM 'ccw' = increasing apos (shit2); machine A = -apos * iR1dir.
        engine = rotary_engine(iR1dir=ir1dir, dir5a='ccw', apos=0)
        engine.call('usr_r1pos_calc')
        engine.set(apos=3.035)
        words = r1_output(engine)
        self.assertEqual(len(words), 1, output_of(engine))
        mode, value = words[0]
        machine_delta = -3.035 * ir1dir
        self.assertTrue(congruent(value, machine_delta), f'iR1dir={ir1dir}: {output_of(engine)!r}')
        self.assertEqual(mode, 'ACP' if machine_delta > 0 else 'ACN',
                         f'iR1dir={ir1dir}: a {machine_delta:+} deg machine move posted as {output_of(engine)!r}')

    def test_direction_matches_machine_motion_default_sign(self):
        """INDEPENDENT: geometry and recorded shit2 data. With the shipped iR1dir=-1
        a +3.035 deg CAM step (dir5a 'ccw') is a +3.035 deg machine move, so it is
        posted as A=ACP(3.035)."""
        self.assert_direction_matches_machine_motion(-1)

    @known_defect('PP-004')
    def test_direction_matches_machine_motion_reversed_sign(self):
        """INDEPENDENT: geometry. iR1dir=+1 ('1=+CCW', GPP L165) makes the machine A
        -apos, so a +3.035 deg CAM step (dir5a 'ccw') is a -3.035 deg machine move
        and must be posted as ACN(356.965). The post keeps ccw -> ACP and turns the
        3 deg move into a 357 deg revolution."""
        self.assert_direction_matches_machine_motion(1)


class RotaryDesignPins(RotaryChecks, unittest.TestCase):
    @covers('DESIGN-005')
    def test_pin_toolchange_zeroes_cam_apos_and_round_trips_a(self):
        """CHARACTERIZATION of DESIGN-005 (owner policy open). From the third tool
        change on, @usr_tc_init_gmstates sets the CAM inputs apos/bpos/cpos to 0
        (the second tool change skips that branch, see PP-027). Between two 5x jobs
        at A37 the tool-change rapid unwinds to A=ACN(0), the first move of the next
        job homes again and rewinds to A=ACP(37). The unwind takes its direction
        from angle_4x_around_x_dir, so a value other than cw/ccw stops the post.
        Alternatives for the owner: keep A at the job angle across the tool change
        (no unwind), or unwind with a direction that cannot abort. This pins the
        current behaviour, not a desired one. UNVERIFIED inputs: the session keeps
        the last CAM apos (37) through @end_of_job/@change_tool/@start_of_job (apos
        carry-over between jobs, the PP-005 assumption; without it the zeroing is a
        no-op, although the unwind to 0 still happens), and whether SolidCAM ever
        sends an angle_4x_around_x_dir other than cw/ccw at a tool change."""
        self.check_toolchange_zeroes_cam_apos()

    @covers('DESIGN-007')
    def test_secondary_rotation_adds_no_extra_rotation(self):
        """CHARACTERIZATION of DESIGN-007 (owner policy open). A non-zero secondary
        rotation (x_angle_const_z or bpos) on this X/Y/Z/A machine is silently
        ignored: no B word, no head-swivel macro (HVV/HVH/ROT), Z not inverted
        (77c03c6 X-flip fix), and the post does not stop; only the old vertical-head
        toggle remains (extra homing, Y in the tool-change block). Alternatives:
        abort with POST ERROR like the A-axis guards do for unrepresentable output,
        or keep ignoring it. STRUCTURAL state: SolidCAM should not send a secondary
        rotation for this 4-axis VMID, and the first-rapid/tool-change flags are set
        by hand. The 'no HVV' and 'Z sign kept' parts are the 77c03c6 regression
        guards (INDEPENDENT: commit intent and CAM Z sign); 'does not stop' is the
        characterization part (history-rotary-13 correction)."""
        self.check_secondary_rotation_adds_no_extra_rotation()


# @usr_r1_range: 6228b3d replaced the one-step adjustment with a wrap into [0, 360) and added
# the snap of values that print as 360.000 (or -0.000) to 0.
R1_MODE1_WRAP = """    while nR1pos < 0
        nShift = nShift + 360
        nR1pos = nR1postemp + nShift
    endw
    while nR1pos >= 360
        nShift = nShift - 360
        nR1pos = nR1postemp + nShift
    endw
"""
R1_MODE1_BEFORE_6228B3D = """    if nR1postemp < 0 and nR1postemp > -360
        nR1pos = nR1postemp + 360
    endif
"""
R1_SNAP_TO_ZERO = """    ; 360.000 and -0.000 with nR1pos_f '7.3' (sums of angles carry float noise) are the position 0.
    if nR1pos >= 359.9995 or nR1pos < 0.0005
        nR1pos = 0
    endif
"""


class FixedRotaryDefectGuards(unittest.TestCase):
    """Former canonical tests of rotary defects the owner's commits fixed."""

    @covers('PP-002')
    def test_emitted_a_positions_are_valid_modulo_positions(self):
        """INDEPENDENT: Siemens 828D modulo rotary axis: DC/ACP/ACN accept only
        0 <= A < 360 (alarm 16830). The A axis is modulo (8966d35, Vericut
        mmABSOLUTE_360). Inputs whose machine angle is clearly outside the range
        (apos -360, 400, -400, 720; CoordSys + apos = 400; CoordSys -360, the tmatrix
        case of the registry; CoordSys + transform = 390) must post the angle reduced
        modulo 360, both for the forced DC and for a directed move. Before 6228b3d
        iR1posControl=1 added 360 only on (-360, 0), so all of them passed through.
        Regression guard of PP-002 facet whole-turn (fixed in 6228b3d)."""
        self.check_whole_turn_positions()

    def check_whole_turn_positions(self, source=None):
        cases = [dict(apos=-360), dict(apos=400), dict(apos=-400), dict(apos=720),
                 dict(angle_4x_around_x=300, apos=100), dict(angle_4x_around_x=-360),
                 dict(angle_4x_around_x=270, angle=120)]
        bad = []
        for inputs in cases:
            machine = sum(inputs.values())   # iR1dir=-1: machine A = sum of the CAM angles
            for output in (dict(bR1forceOutput=True), dict(dir5a='ccw', nPR1pos=123.4)):
                words = r1_output(rotary_engine(source, **inputs, **output))
                if len(words) != 1 or not 0 <= words[0][1] < 360 or not congruent(words[0][1], machine):
                    bad.append(f'{inputs}: {words}')
        if bad:
            self.fail('A positions outside the modulo range 0 <= A < 360: ' + '; '.join(bad))

    @covers('PP-002')
    def test_directed_a_positions_stay_in_modulo_range(self):
        """INDEPENDENT: Siemens modulo-axis program range 0 <= A < 360 (alarm 16830).
        Covers every input that posted exactly 'A=..(360)' before 6228b3d. (1) A tiny
        negative angle (CAD/transform noise -1e-9, or -0.0004 below the 0.001
        resolution) denotes position 0, but iR1posControl=1 added 360 and the '7.3'
        format rounded 359.9996.. to 360. (2) An exact whole-turn sum (apos 360,
        CoordSys 270 + transform 90) passed through as 360. 6228b3d posts both as 0.
        UNVERIFIED, two assumptions: GPPL semantics the engine emulates with Python (the
        exact float compare and round-to-nearest of '7.3'), and the exclusive upper
        bound: whether the 828D rejects 360 itself is uncertain (correction to
        history-rotary-07). Forced DC and directed output are both checked. Regression
        guard of PP-002 facet rounding (fixed in 6228b3d; float noise: 9c89feb)."""
        self.check_rounded_whole_turns()

    def check_rounded_whole_turns(self, source=None):
        cases = [dict(apos=-0.0004), dict(apos=-1e-9), dict(apos=360),
                 dict(angle_4x_around_x=270, angle=90)]
        bad = []
        for inputs in cases:
            machine = sum(inputs.values())   # iR1dir=-1: machine A = sum of the CAM angles
            for output in (dict(bR1forceOutput=True), dict(nPR1pos=123)):
                words = r1_output(rotary_engine(source, **inputs, **output))
                if len(words) != 1 or not 0 <= words[0][1] < 360 or not congruent(words[0][1], machine):
                    bad.append(f'{inputs}: {words}')
        if bad:
            self.fail('inputs post A=..(360), outside 0 <= A < 360: ' + '; '.join(bad))

    def test_6228b3d_reversion_is_detected(self):
        """INDEPENDENT: negative validation of both PP-002 guards. Reverting 6228b3d in
        memory (mode 1 adds 360 only on (-360, 0) and nothing snaps a printed 360.000
        to 0) must make each check fail with AssertionError."""
        wrap = mutate(R1_MODE1_WRAP, R1_MODE1_BEFORE_6228B3D)
        mutant = mutate(R1_SNAP_TO_ZERO, '', source=wrap)
        assert_detected(self, self.check_whole_turn_positions, mutant, '6228b3d reverted (whole-turn)',
                        match='outside the modulo range')
        assert_detected(self, self.check_rounded_whole_turns, mutant, '6228b3d reverted (rounding)',
                        match=r'A=\.\.\(360\)')

    @covers('PP-007')
    def test_move_4x_preserves_axial_x(self):
        """INDEPENDENT: VMID kinematics: A turns about X (VecX=1), so X is the axial
        coordinate and a rotation never replaces it; @line_4x and the Mach3 sibling
        @move_4x print X unchanged. Before ca63502 @move_4x posted any changed X as X0.
        UNVERIFIED: whether SolidCAM emits @move_4x for this VMID at all (every recorded
        rotary move arrives as @move_5x/@line_5x). Regression guard of PP-007 (fixed in
        ca63502; the follow-up line is tests/test_move_4x_axial_x.py)."""
        engine = motion_engine()
        text = event(engine, 'move_4x', ('xpos', 'zpos'), xpos=50, zpos=40)
        x_values = [block.axes['X'] for block in parse_blocks(text) if 'X' in block.axes]
        self.assertEqual(x_values, [50.0], text)
        self.assertEqual(engine.state['xpos'], 50)


class KnownRotaryDefects(unittest.TestCase):
    @covers('PP-002')
    def test_negative_position_control_posts_valid_modulo_positions(self):
        """INDEPENDENT: Siemens modulo-axis program range 0 <= A < 360 (alarm 16830)
        holds whatever the post option. iR1posControl=2 ('Negative') printed
        A=ACN(-270) for a 90 deg target and iR1posControl=0 ('SolidCAM Direct') a
        negative CAM angle as is (A=ACN(-90)); the option is gone, so a leftover
        setting must change nothing. Regression guard of PP-002 facet negative-mode."""
        bad = []
        for control, apos in ((2, 90), (2, 10), (0, -90)):
            words = r1_output(rotary_engine(iR1posControl=control, apos=apos, nPR1pos=123))
            if len(words) != 1 or not 0 <= words[0][1] < 360 or not congruent(words[0][1], apos):
                bad.append(f'iR1posControl={control} apos={apos}: {words}')
        if bad:
            self.fail('non-default position control posts negative directed positions: ' + '; '.join(bad))

    @covers('PP-037')
    def test_shortest_distance_mode_keeps_target_angle(self):
        """INDEPENDENT: a direction strategy may change the direction word, never the
        target position: each posted value must denote apos modulo 360. The removed
        'Shortest Distance' mode (iR1posControl=3) posted A100 -> A30 as ACP(-30); a
        leftover setting must change nothing. Regression guard of PP-037."""
        engine = rotary_engine(iR1posControl=3, dir5a='ccw')
        bad = []
        for apos in (100, 30):
            engine.set(apos=apos)
            words = r1_output(engine)
            if len(words) != 1 or not congruent(words[0][1], apos):
                bad.append(f'apos={apos}: {words}')
        if bad:
            self.fail('shortest-distance mode changes the target: ' + '; '.join(bad))

    @known_defect('PP-036')
    def test_limit_3axis_never_outputs_rotary(self):
        """INDEPENDENT: meaning of the VMID machine parameter bLimit_3axis ('limit to
        3 axes'); the GPP itself suppresses rotary changes and the 4x trig/MAC paths
        when it is set (@usr_r1pos_calc, @usr_ct_after, @start_of_job). A program
        posted with bLimit_3axis=1 must contain no A word; the forced initial DC
        (ab853be) still prints A=DC(0) at the first tool change."""
        session = Session(vmid={'bLimit_3axis': True})
        session.first_tool()
        five_x_job(session, 30)
        self.assertEqual(rotary_words(session.text()), [], session.text())

    @covers('PP-043')
    def test_home_data_does_not_modify_cam_inputs(self):
        """INDEPENDENT: SolidCAM system variables are inputs; a postprocessor must not
        overwrite them. @home_data (run at program start, VMID HomeDataAtStart="1")
        replaced a negative shift_y by its absolute value when position != 1, for the
        removed trig macro only. Regression guard of PP-043."""
        session = Session()
        session.ev('home_data', home_user_name='P2', position=2, home_number=1,
                   shift_x=10, shift_y=-5, shift_z=3, y_angle_const_z=0)
        state = session.state
        self.assertEqual((state['shift_x'], state['shift_y'], state['shift_z']), (10, -5, 3))

    @known_defect('PP-046')
    def test_sub_resolution_rotary_change_does_not_home(self):
        """INDEPENDENT: VMID RotaryAxisPrecision=0.001 and nR1pos_f '7.3': a target
        that formats to the current A (270) is no rotation, so the rapid needs no
        G75 clearance and no A word. The exact compare 'nPR1pos ne nR1pos' turns a
        1e-9 difference into G75 Z + XY homing plus a no-op A=ACN(270). UNVERIFIED:
        GPPL numeric compare semantics (exact or tolerance/format based)."""
        engine = motion_engine()
        engine.set(nPR1pos=270, nPR1postemp=-90, apos=-90)   # A already at 270
        text = event(engine, 'move_5x', ('xpos',), apos=-90 - 1e-9, xpos=50)
        blocks = parse_blocks(text)
        self.assertEqual([block.raw for block in blocks if 75 in block.g or block.rotary('A')], [], text)


if __name__ == '__main__':
    unittest.main()
