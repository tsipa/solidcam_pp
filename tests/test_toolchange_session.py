"""Tool-change and job-boundary session tests for Gmill_540v_4x.gpp (area A).

Scope: @change_tool, @usr_ct*, @usr_tc_init_gmstates, @usr_coolant*,
@usr_HSM_mode, @usr_StopM00_sametool/_difftool, @start_of_job and
@end_of_job, run in SolidCAM's event order through support.Session:

    start_program -> change_tool -> [tmatrix] -> start_of_job -> moves
    -> end_of_job -> change_tool -> start_of_job -> ... -> end_program

Change flags are cleared after initialisation (Session flags='clear'); the
persisting policy is only used by the PP-054 tests in test_session_program.py.
M00 paths need the VMID job parameter bStopM00 of the job that ends, passed to
@end_of_job (end=dict(bStopM00=True, ...)).

Assertions use parsed blocks (support.nc) and the modal replay (support.modal:
M9 switches every coolant channel off, M3/M4/M5 set the spindle state, T
selects and M6 loads a tool). Oracles: machining and controller rules (retract
Z before a tool change, spindle and coolant off before M06/M00, spindle on and
cutting edge D1 active before cutting, the 828D G-function set of the
repository's Vericut control), the PP's own option documentation in
@usr_ip_useroptions and commit intent. Orderings that are equally safe either
way are labelled CHARACTERIZATION (tc-14). Every passing guard has mutation
checks that must fail with AssertionError.
"""
import unittest

from support import (Segment, Session, assert_detected, covers, g_function_whitelist, index_of, known_defect,
                     last_index_of, mutate, parse_blocks)

SPINDLE_ACCEL_DOC = 500   # @init_post: spindle_accel = 500 ; rpm/s
NO_COOLANT = dict(flood_coolant=0, Mist_coolant=0, HP_Flood_coolant=0, LP_Flood_coolant=0,
                  through_ival_coolant=0, through_coolant_val=0, LP_Through_coolant=0,
                  Air_Blast_coolant=0, air_through_coolant=0)
TC_HOMING_CALL = ("            if sHomestrtc ne ''\n                sHomestr = sHomestrtc\n"
                  "                call @usr_prep_home_axis\n")
INDEX_HOMING = ("            if i4xIndexClearanceMode eq 0\n                if sHomestrrot ne ''\n"
                "                    sHomestr = sHomestrrot\n                    call @usr_prep_home_axis\n"
                "                endif\n                iMotionmode = 0\n                {nb,")
START_TOOL_AFTER_TC = ('            skipline = false\n            call @start_tool\n        endif\n    endif\n'
                       ';    bSkipxyrapid = true')


def listing(blocks):
    return '\n'.join(block.raw for block in blocks)


def m_code(*codes):
    return lambda block: any(block.has('M', code) for code in codes)


def t_word(number):
    return lambda block: block.has('T', number)


def z_homing(block):
    return 'Z' in block.homing_axes


def axis_motion(block):
    """Plain X/Y/Z or rotary words (G75 fixed-point blocks excluded)."""
    return block.is_motion


def any_axis_move(block):
    return block.is_motion or bool(block.homing_axes)


def z_word(block):
    return 'Z' in block.axes


def tool_in_effect(segment, index):
    selected = segment.find_last(lambda b: b.get('T') is not None, 0, index)
    return segment.blocks[selected].get('T') if selected >= 0 else None


def two_tool_change(source=None, options=None, spin=3000, **job):
    s = Session(source=source, options=options)
    s.first_tool()
    s.cut(10, 20, 5, -1)
    mark = s.mark()
    s.next_tool(2, 3, spin=spin, job_name='op2', **job)
    s.cut(30, 40, 5, -1)
    return s, mark


# ---------------------------------------------------------------------------
# Tool change sequence: cutting edge and work offset
# ---------------------------------------------------------------------------

class ToolChangeSequenceTests(unittest.TestCase):
    def tool_changes(self, source=None):
        """(label, Segment) for the first and the second tool change of one program."""
        s = Session(source=source)
        s.first_tool()
        s.cut(10, 20, 5, -1)
        mark = s.mark()
        s.next_tool(2, 3, job_name='op2')
        s.cut(30, 40, 5, -1)
        # Both segments are searched forward from their first M06.
        return [('first tool', Segment(s)), ('second tool', Segment(s, mark))]

    def assert_d1_before_motion(self, source=None):
        for label, seg in self.tool_changes(source):
            m06 = seg.find(m_code(6))
            self.assertGreaterEqual(m06, 0, f'{label}: no M06:\n{seg.shown}')
            edge = seg.find(lambda b: b.get('D') is not None, m06)
            self.assertGreater(edge, m06, f'{label}: no cutting edge selected after M06:\n{seg.shown}')
            self.assertEqual([word.raw for word in seg.blocks[edge].find('D')], ['D1'], seg.shown)
            motion = seg.find(any_axis_move, m06)
            self.assertGreater(motion, m06, seg.shown)
            self.assertLess(edge, motion, f'{label}: D1 must precede the first axis move after M06:\n{seg.shown}')

    def test_tool_change_activates_d1_before_first_motion(self):
        """INDEPENDENT: 420c4ab intent; on Sinumerik T/M06 loads the tool and D1 activates its edge.

        After M06 the first D word is exactly D1 and comes before any axis move
        (G75, X/Y/Z or A), for the first and for a later tool change.
        """
        self.assert_d1_before_motion()

    def test_d1_reversions_are_detected(self):
        """INDEPENDENT: removing D1 (420c4ab reverted) or moving it after the first rapid fails."""
        rapid = "            change(zpos) = false\n            skipline = true\n            call @usr_rapid\n"
        late = mutate("    {nb, 'D1 '}\n", '')
        late = mutate(rapid, rapid + "            {nb, 'D1 '}\n", source=late)
        sources = {'420c4ab reverted': mutate("    {nb, 'D1 '}\n", ''), 'D1 after the first rapid': late}
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.assert_d1_before_motion, source, label, 'cutting edge|D1')

    def assert_work_offset_reactivated(self, source=None):
        for label, seg in self.tool_changes(source):
            m06 = seg.find(m_code(6))
            positioning = seg.find(lambda b: bool(b.axes), m06)
            self.assertGreater(positioning, m06, seg.shown)
            offset = seg.find(lambda b: 54 in b.g, m06)
            self.assertTrue(m06 < offset < positioning,
                            f'{label}: work offset not re-activated after M06 before positioning:\n{seg.shown}')
            self.assertIn(0, seg.blocks[offset].g, f'{label}: the offset block must be a G0 rapid:\n{seg.shown}')
            self.assertEqual(seg.states[positioning].work_offset, 54, seg.shown)

    def test_tool_change_reactivates_work_offset_before_first_move(self):
        """INDEPENDENT: option doc 'bWorkoffsettc: True = Forces output of Work Offset at each Tool Change'.

        After T/M06 the first block that names a work offset carries G54 and
        comes before the first X/Y/Z positioning, at the first and a later tool
        change. The option itself is dead (tc-17: the offset is printed
        unconditionally), so its doc is the intent oracle at its shipped value
        True. CHARACTERIZATION: the offset shares its block with G0.
        """
        self.assert_work_offset_reactivated()

    def test_work_offset_reactivation_mutations_are_detected(self):
        """INDEPENDENT: deleting the tool-change rapid block or its offset word fails the guard."""
        block = "{nb,'G'iMotionmode:mcode_f ' ',['G'iMplane' '],'G'iAbsincmode ' ',cWo,iWorkoffset' '}"
        sources = {
            'tool-change rapid block deleted': mutate(block + '\n', ''),
            'offset dropped from the tool-change rapid': mutate(
                block, "{nb,'G'iMotionmode:mcode_f ' ',['G'iMplane' '],'G'iAbsincmode ' '}"),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.assert_work_offset_reactivated, source, label, 'work offset')


# ---------------------------------------------------------------------------
# Tool-change safety invariants
# ---------------------------------------------------------------------------

class ToolChangeSafetyTests(unittest.TestCase):
    def assert_order(self, seg, labelled):
        previous_label, previous = None, -1
        for label, index in labelled:
            self.assertGreaterEqual(index, 0, f'{label} missing in:\n{seg.shown}')
            self.assertGreater(index, previous, f'{label} must follow {previous_label} in:\n{seg.shown}')
            previous_label, previous = label, index

    # -- next tool change ---------------------------------------------------
    def check_next_tool_change(self, source=None, options=None):
        s, mark = two_tool_change(source, options)
        seg = Segment(s, mark)
        m06 = seg.find(m_code(6))
        self.assertGreaterEqual(m06, 0, seg.shown)
        home = seg.find_last(z_homing, 0, m06)
        self.assert_order(seg, [('G75 Z retract', home), ('T2', seg.find(t_word(2), home)), ('M06', m06),
                                ('D1', seg.find(lambda b: b.has('D', 1), m06)),
                                ('T3 preselect', seg.find(t_word(3), m06))])
        self.assertEqual(seg.find(lambda b: bool({'X', 'Y'} & (set(b.axes) | b.homing_axes)), 0, home), -1,
                         f'X/Y moved before the Z retract:\n{seg.shown}')
        self.assertEqual(seg.find(axis_motion, home + 1, m06), -1, f'axis motion between the retract and M06:\n{seg.shown}')
        self.assertEqual(tool_in_effect(seg, m06), 2, f'the T word in effect at M06 must be the new tool:\n{seg.shown}')
        at_change = seg.before(m06)
        self.assertEqual(at_change.spindle, 5, f'spindle still running at M06:\n{seg.shown}')
        self.assertEqual(sorted(at_change.coolant), [], f'coolant still on at M06:\n{seg.shown}')
        approach = seg.find(z_word, m06)
        cut = seg.first_feed(m06)
        self.assertTrue(m06 < approach <= cut, seg.shown)
        for index, label in ((approach, 'first Z approach'), (cut, 'first cut')):
            state = seg.states[index]
            self.assertEqual((state.spindle, state.speed), (3, 3000), f'spindle not on at S3000 at the {label}:\n{seg.shown}')
            # Flood is required at the first cut; already at the Z approach is
            # this PP's order (CHARACTERIZATION).
            self.assertEqual(sorted(state.coolant), [8], f'flood coolant not on at the {label}:\n{seg.shown}')
        # CHARACTERIZATION (tc-14): stop-then-retract and M1 between M5 and M06 are
        # this PP's order (retract-then-stop would be equally safe); the ramp dwell
        # is the PP's own spindle_accel policy (500 rpm/s), not machine physics.
        m5, m9, m1 = seg.find(m_code(5)), seg.find(m_code(9)), seg.find(m_code(1))
        self.assertTrue(0 <= m9 < home and 0 <= m5 < home, f'M9/M5 must precede the retract:\n{seg.shown}')
        self.assertTrue(m5 < m1 < m06, f'M01 (bOptstptc) must be between M5 and M06:\n{seg.shown}')
        speed = seg.find(lambda b: b.has('S', 3000), m06)
        self.assertGreaterEqual(seg.dwell(speed, approach), 3000 / SPINDLE_ACCEL_DOC,
                                f'spindle ramp dwell missing:\n{seg.shown}')

    def test_next_tool_change_stops_retracts_then_changes_then_restarts(self):
        """INDEPENDENT: tool-change safety (retract Z, change, restart) on the replayed modal state.

        Z retracts (G75 Z) before any X/Y travel and nothing moves between the
        retract and M06; T2 is the tool in effect at M06; D1 and the T3
        preselection follow M06; spindle (M5) and coolant (M9) are off at M06
        (option docs bSpinofftc/bCoolofftc); S3000 and M3 are in effect at the
        first Z approach and at the first cut, the requested flood M8 at the
        first cut. CHARACTERIZATION (tc-14): M5/M9 before G75 Z, M1 between M5
        and M06, M8 already at the Z approach and the S/500 s ramp dwell (the
        PP's spindle_accel policy).
        """
        self.check_next_tool_change()

    def test_next_tool_change_mutations_are_detected(self):
        """INDEPENDENT: tc-14 and weird-hunter tool-change mutants fail the guard."""
        both_homing = mutate("            sHomestrrot = sHomestrrotv\n            if sHomestrrot ne ''\n"
                             "                sHomestr = sHomestrrot\n                call @usr_prep_home_axis\n"
                             "            endif\n            ; {nb, 'HVH'}",
                             "            sHomestrrot = sHomestrrotv\n            ; {nb, 'HVH'}")
        both_homing = mutate("        else\n            if sHomestrtc ne ''\n                sHomestr = sHomestrtc\n"
                             "                call @usr_prep_home_axis\n            endif\n        endif",
                             "        else\n        endif", source=both_homing)
        sources = {
            'no tool-change homing': mutate(TC_HOMING_CALL, "            if sHomestrtc ne ''\n"
                                                            "                sHomestr = sHomestrtc\n"),
            'both tool-change homing calls removed (weird-hunter)': both_homing,
            'no M5 before M06': mutate("        if bSpinoffend\n            iSpindleDir = 5\n            {nb}\n"
                                       "            call @usr_spindle_mcode_output\n        endif\n        if bVertical",
                                       "        if bVertical"),
            'no M9 before M06': mutate("    if !bStopM00difftool\n        if bCooloffend and bCoolExist",
                                       "    if !bStopM00difftool\n        if false"),
            'no M01 between tools': mutate("        if bOptstptc\n            call @usr_optionalstop\n        endif\n"
                                           "    endif\n    if bTcseperation", "    endif\n    if bTcseperation"),
            'no spindle start after M06': mutate(START_TOOL_AFTER_TC, START_TOOL_AFTER_TC.replace(
                '            call @start_tool\n', '')),
            'no coolant after M06': mutate("            if bCoolExist\n                skipline = false\n"
                                           "                call @usr_coolant\n",
                                           "            if bCoolExist\n                skipline = false\n"),
            'preselect before M06': mutate("    {nb, 'T',tool_number,cTCcodes}\n    {nb, cTCcodep}",
                                           "    {nb, 'T',tool_number,cTCcodes}\n    {nb, 'T'next_tool_number' '}\n"
                                           "    {nb, cTCcodep}"),
            'short ramp dwell': mutate('(0.3+(sdiff/500))', '(0.3+(sdiff/5000))'),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.check_next_tool_change, source, label)

    # -- first tool change --------------------------------------------------
    def check_first_tool_change(self, source=None):
        s = Session(source=source)
        s.first_tool()
        s.cut(10, 20, 5, -1)
        seg = Segment(s)
        m06 = seg.find(m_code(6))
        home = seg.find(z_homing)
        self.assert_order(seg, [('G75 Z homing', home), ('T1', seg.find(t_word(1))), ('M06', m06),
                                ('D1', seg.find(lambda b: b.has('D', 1), m06)),
                                ('T2 preselect', seg.find(t_word(2), m06))])
        self.assertEqual(seg.find(axis_motion, 0, m06), -1, f'no motion before the first M06:\n{seg.shown}')
        self.assertEqual(seg.find(lambda b: bool({'X', 'Y'} & b.homing_axes), 0, home), -1,
                         f'X/Y homed before Z at program start:\n{seg.shown}')
        self.assertEqual(tool_in_effect(seg, m06), 1, f'the T word in effect at M06 must be T1:\n{seg.shown}')
        rotary = seg.find(lambda b: b.rotary('A') is not None, m06)
        self.assertGreater(rotary, m06, seg.shown)
        self.assertEqual(seg.blocks[rotary].rotary('A')[0], 'DC', f'first A output must be DC (ab853be):\n{seg.shown}')
        approach = seg.find(z_word, m06)
        self.assertGreater(approach, m06, f'no Z approach after M06:\n{seg.shown}')
        state = seg.states[approach]
        self.assertEqual((state.spindle, state.speed), (3, 8000), f'spindle on at S8000 before the approach:\n{seg.shown}')
        # CHARACTERIZATION: the PP's spindle_accel ramp policy (S/500 s).
        speed = seg.find(lambda b: b.has('S', 8000), m06)
        self.assertGreaterEqual(seg.dwell(speed, approach), 8000 / SPINDLE_ACCEL_DOC, f'ramp dwell missing:\n{seg.shown}')

    def test_first_tool_change_is_preceded_by_program_start_retract(self):
        """INDEPENDENT: program start safety and the first tool load.

        The program-start G75 Z precedes T1/M06 and nothing moves before M06;
        T1 is in effect at M06; D1 and the T2 preselection follow; the first A
        output is DC (ab853be: the A position is unknown at program start);
        spindle M3 at S8000 is on before the first Z approach. The S/500 s dwell
        is a CHARACTERIZATION of the PP's spindle_accel policy.
        """
        self.check_first_tool_change()

    def test_first_tool_change_mutations_are_detected(self):
        """INDEPENDENT: missing start homing, early preselect, no spindle start or no DC force fail."""
        sources = {
            'no start homing': mutate("    if sHomestrbegin ne ''\n        sHomestr = sHomestrbegin\n"
                                      "        call @usr_prep_home_axis\n    endif\nendp",
                                      "    if sHomestrbegin ne ''\n        sHomestr = sHomestrbegin\n    endif\nendp"),
            'preselect before M06': mutate("    {nb, 'T',tool_number,cTCcodes}\n    {nb, cTCcodep}",
                                           "    {nb, 'T',tool_number,cTCcodes}\n    {nb, 'T'next_tool_number' '}\n"
                                           "    {nb, cTCcodep}"),
            'no spindle start after M06': mutate(START_TOOL_AFTER_TC, START_TOOL_AFTER_TC.replace(
                '            call @start_tool\n', '')),
            'no initial DC force': mutate('    bR1forceOutput = true\n', '    bR1forceOutput = false\n'),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.check_first_tool_change, source, label)

    # -- preselection ---------------------------------------------------------
    def check_preselection(self, source=None):
        cases = {'default': ({}, {}, True), 'last tool': ({}, {'last_tool': True}, False),
                 'bToolPreselect off': ({'bToolPreselect': False}, {}, False)}
        found = {}
        for label, (options, job, _) in cases.items():
            s = Session(source=source, options=options)
            blocks = parse_blocks(s.first_tool(tool=4, next_tool=9, **job))
            m06 = index_of(blocks, m_code(6))
            found[label] = index_of(blocks, t_word(9), m06) > m06
        # No subTest: mutation checks need the AssertionError.
        self.assertEqual(found, {label: expected for label, (_, _, expected) in cases.items()})

    def test_tool_preselection_respects_last_tool_and_option(self):
        """INDEPENDENT: option doc 'bToolPreselect: True = Next tool is Preselected after tool change'.

        The next tool (T9) is preselected after M06 by default, not for the last
        tool (no next tool) and not with bToolPreselect=False.
        """
        self.check_preselection()

    def test_preselection_mutations_are_detected(self):
        """INDEPENDENT: preselection ignoring last_tool or the option fails the guard."""
        sources = {
            'preselect ignores last_tool': mutate("        if !last_tool\n            {nb, 'T'next_tool_number' '}",
                                                  "        if true\n            {nb, 'T'next_tool_number' '}"),
            'preselect ignores the option': mutate('    if bToolPreselect\n        if !last_tool',
                                                   '    if true\n        if !last_tool'),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.check_preselection, source, label)

    # -- M00 before a different tool ---------------------------------------------
    def check_m00_different_tool(self, source=None):
        s = Session(source=source)
        s.first_tool()
        s.cut(10, 20, 5, -1)
        mark = s.mark()
        s.next_tool(2, 3, end=dict(bStopM00=True, next_job_tool_number=2, sStopMessage='CHECK PART'),
                    bStopM00=False)
        seg = Segment(s, mark)
        stop, m06 = seg.find(m_code(0)), seg.find(m_code(6))
        self.assertTrue(0 <= stop < m06, f'M00 before the tool change missing:\n{seg.shown}')
        at_stop = seg.before(stop)
        self.assertEqual(at_stop.spindle, 5, f'spindle must stop before M00:\n{seg.shown}')
        self.assertEqual(sorted(at_stop.coolant), [], f'coolant must stop before M00:\n{seg.shown}')
        # tc-11 corrected invariant: a G75 Z after the last axis motion and before M06.
        program = s.blocks()
        offset = len(program) - len(seg.blocks)
        last_motion = last_index_of(program, axis_motion, 0, offset + m06)
        home = last_index_of(program, z_homing, 0, offset + m06)
        self.assertGreater(home, last_motion, f'G75 Z retract required between the last motion and M06:\n{seg.shown}')

    @covers('PP-056')
    def test_m00_with_different_tool_still_retracts_before_m06(self):
        """INDEPENDENT: safety, spindle/coolant off before an operator stop; Z retracted before M06.

        CHARACTERIZATION pin for PP-056: bStopM00difftool is set and cleared in
        the same @end_of_job, so the tool change after an M00 still runs its
        G75 retract (sHomestrstpdiff is '' by default). A naive "fix" that keeps
        the flag alive drops the only Z retract before M06; this guard (from
        tc-11, weird-hunter and pp-region-3) catches it. Invariant per the
        tc-11 correction: G75 Z after the last motion and before M06.
        """
        self.check_m00_different_tool()

    def test_m00_different_tool_mutations_are_detected(self):
        """INDEPENDENT: a live bStopM00difftool or no M5 before M00 fails the guard."""
        sources = {
            'bStopM00difftool kept alive': mutate('    bSkipxyrapid = false\n    bStopM00difftool = false\n'
                                                  '    iPworkoffset = iWorkoffset',
                                                  '    bSkipxyrapid = false\n    iPworkoffset = iWorkoffset'),
            'no M5 before the different-tool M00': mutate(
                "        call @usr_coolant_output\n    endif\n    iSpindleDir = 5\n    {nb}\n"
                "    call @usr_spindle_mcode_output\n    if sHomestrstpdiff",
                "        call @usr_coolant_output\n    endif\n    if sHomestrstpdiff"),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.check_m00_different_tool, source, label)

    # -- M00 between same-tool jobs ------------------------------------------------
    def check_m00_same_tool(self, source=None):
        s = Session(source=source)
        s.first_tool()
        s.cut(10, 20, 5, -1)
        mark = s.mark()
        s.same_tool_job(end=dict(bStopM00=True, next_job_tool_number=1, sStopMessage='CHECK PART'),
                        bStopM00=False, job_name='op2')
        s.cut(30, 40, 5, -1)
        seg = Segment(s, mark)
        stop = seg.find(m_code(0))
        self.assertGreaterEqual(stop, 0, f'M00 missing:\n{seg.shown}')
        at_stop = seg.before(stop)
        self.assertEqual(at_stop.spindle, 5, f'spindle not stopped before M00:\n{seg.shown}')
        self.assertEqual(sorted(at_stop.coolant), [], f'coolant not stopped before M00:\n{seg.shown}')
        motion = seg.find(axis_motion, stop)
        cut = seg.first_feed(stop)
        self.assertTrue(stop < motion <= cut, seg.shown)
        for index, label in ((motion, 'reposition'), (cut, 'first cut')):
            state = seg.states[index]
            self.assertEqual(state.spindle, 3, f'spindle not restarted before the {label}:\n{seg.shown}')
            self.assertEqual(state.speed, 8000, f'programmed S lost before the {label}:\n{seg.shown}')

    def test_m00_with_same_tool_stops_and_restarts_spindle_before_next_cut(self):
        """INDEPENDENT: operator safety, then no motion with a stopped spindle.

        Spindle (M5) and coolant (M9) are off when M00 starts; M3 is in effect
        again at the first reposition and at the first cut after M00, with the
        programmed S8000 still active (on Sinumerik S survives M5/M0, so no new S
        word is required; tc-03 correction).
        """
        self.check_m00_same_tool()

    def test_m00_same_tool_mutations_are_detected(self):
        """INDEPENDENT: no M5 before M00 or no restart after it fails the guard (pp-region-3, tc-14)."""
        sources = {
            'no M5 before the same-tool M00': mutate(
                "        call @usr_coolant_output\n    endif\n    iSpindleDir = 5\n    {nb}\n"
                "    call @usr_spindle_mcode_output\n    if sHomestrstpsame",
                "        call @usr_coolant_output\n    endif\n    if sHomestrstpsame"),
            'no spindle restart after M00': mutate('    call @m_feed_spin\n    call @usr_spindle_mcode_output\n'
                                                   '    change(xpos) = true',
                                                   '    call @m_feed_spin\n    change(xpos) = true'),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.check_m00_same_tool, source, label, 'not stopped|not restarted')

    # -- index pending at a tool change -----------------------------------------------
    def check_pending_index(self, source=None):
        s, mark = two_tool_change(source, tmatrix=90)
        seg = Segment(s, mark)
        rotations = [index for index, block in enumerate(seg.blocks)
                     if block.rotary('A') is not None and abs(block.rotary('A')[1] - 90) < 1e-9]
        self.assertEqual(len(rotations), 1, f'exactly one A90 index expected:\n{seg.shown}')
        # Order-independent (DESIGN-003 decides index before/after the change):
        # each event happens with Z at the fixed point and no Z move since.
        for label, event in (('A90 index', rotations[0]), ('M06', seg.find(m_code(6)))):
            home = seg.find_last(z_homing, 0, event)
            self.assertGreaterEqual(home, 0, f'G75 Z required before {label}:\n{seg.shown}')
            moved = [seg.blocks[index].raw for index in range(home + 1, event) if z_word(seg.blocks[index])]
            self.assertEqual(moved, [], f'Z moved between G75 Z and {label}:\n{seg.shown}')

    def test_tool_change_with_pending_index_retracts_before_rotation_and_m06(self):
        """INDEPENDENT: Z at the fixed point before both a table rotation and a tool change.

        Order-independent: whichever of the deferred A90 index and the tool
        change comes first (DESIGN-003), each one follows a G75 Z with no Z move
        in between.
        """
        self.check_pending_index()

    def test_pending_index_mutations_are_detected(self):
        """INDEPENDENT: an index without its G75 Z homing fails the guard."""
        assert_detected(self, self.check_pending_index,
               mutate(INDEX_HOMING, "            if i4xIndexClearanceMode eq 0\n                iMotionmode = 0\n"
                                    "                {nb,"), 'index without homing', 'A90 index')

    # -- coolant channels ---------------------------------------------------------------
    def check_coolant_channels(self, source=None):
        requests = [  # (job coolant parameters, ON codes of @usr_ip_useroptions / @usr_coolant)
            (dict(flood_coolant=1), [8]),
            (dict(Mist_coolant=1), [7]),
            (dict(flood_coolant=1, Air_Blast_coolant=1), [8, 50]),
            (dict(HP_Flood_coolant=1), [130]),
            (dict(), []),
            (dict(LP_Through_coolant=1), [51]),
            (dict(air_through_coolant=1), [92]),
            (dict(through_ival_coolant=1, through_coolant_val=40), [71]),
            (dict(Mist_coolant=2, flood_coolant=1), [8]),
        ]
        s = Session(source=source)
        marks = []
        for number, (flags, _) in enumerate(requests, 1):
            job = dict(NO_COOLANT, **flags)
            marks.append(s.mark())
            if number == 1:
                s.first_tool(**job)
            else:
                s.next_tool(number, number + 1, **job)
            s.cut(10 * number, 20, 5, -1)
        found = {}
        for number, mark in enumerate(marks, 1):
            seg = Segment(s, mark)
            m06 = seg.find(m_code(6))
            cut = seg.first_feed(m06)
            self.assertTrue(0 <= m06 < cut, f'tool {number}: no M06 followed by a cut:\n{seg.shown}')
            found[number] = sorted(seg.states[cut].coolant)
        # No subTest: the mutation checks need the AssertionError.
        self.assertEqual(found, {number: codes for number, (_, codes) in enumerate(requests, 1)},
                         'active coolant channels at the first cut of each tool')

    def test_coolant_channels_requested_per_tool_are_active_at_first_cut(self):
        """INDEPENDENT: the replayed coolant state at each tool's first cut equals the job's request.

        support.modal.replay: M9 switches every channel off (Sinumerik/Vericut
        'Coolant Off'), an ON code adds its channel. CHARACTERIZATION: the
        M-code per channel (option table @usr_ip_useroptions iCoolantM1ON..M8ON;
        40 bar -> 71 from @usr_coolant) and 'a value of 2 means off' (the PP's
        own 'eq 0 or eq 2' reading; SolidCAM's meaning of 2 is not verified).
        Tool 1 is a first job under the default flags='clear' policy; under
        flags='persist' it would cut dry (PP-054, ENGINE-001).
        """
        self.check_coolant_channels()

    def test_coolant_channel_mutations_are_detected(self):
        """INDEPENDENT: wrong flag value, a skipped channel, a wrong pressure code or no coolant fail."""
        sources = {
            'air blast flag value': mutate('    if Air_Blast_coolant eq 1\n', '    if Air_Blast_coolant eq 2\n'),
            'channel 7 never written': mutate("    if change(iCoolantM7)\n        {nb,['M'iCoolantM7:mcode_f' ']}\n",
                                              "    if false\n        {nb,['M'iCoolantM7:mcode_f' ']}\n"),
            '40 bar code': mutate('            iCoolantM5ON = 71\n', '            iCoolantM5ON = 72\n'),
            'no coolant after M06': mutate("            if bCoolExist\n                skipline = false\n"
                                           "                call @usr_coolant\n",
                                           "            if bCoolExist\n                skipline = false\n"),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.check_coolant_channels, source, label)

    # -- G-function whitelist -----------------------------------------------------------
    def check_g_functions(self, source=None):
        defined = g_function_whitelist()
        foreign = {}
        for label, options in (('default', {}), ('coolant+spindle after TC', {'bCoolspinaftertc': True}),
                               ('no M1, N numbers', {'bOptstptc': False, 'bNnumtc': True})):
            s = Session(source=source, options=options)
            s.first_tool()
            s.cut(10, 20, 5, -1)
            s.next_tool(2, 3, tmatrix=90)
            s.cut(30, 40, 5, -1)
            s.same_tool_job(job_name='op3')
            s.cut(50, 60, 5, -1)
            s.ev('end_of_job')
            s.ev('end_program', last_tool=True)
            codes = {code for block in s.blocks() for code in block.g}
            if codes - defined:
                foreign[label] = sorted(codes - defined)
        self.assertEqual(foreign, {}, 'G functions outside the 828D control definition')

    def test_default_program_uses_only_sinumerik_g_functions(self):
        """INDEPENDENT: every emitted G number is in the G ranges of vericut/sin840d_special.ctl.

        support.vericut.g_function_whitelist() reads the repository's 828D
        control (skips when it is absent). Three option sets, tool change,
        index, same-tool job and program end, with the VMID default job
        parameters iG187_P=0/nG187_E=0. Holds under the default flags='clear'
        policy; under flags='persist' the first job prints 'G187 P2' (PP-054
        g187-default, ENGINE-001).
        """
        self.check_g_functions()

    def test_g_function_mutations_are_detected(self):
        """INDEPENDENT: re-enabling the Fanuc G43 H height compensation fails the guard."""
        g_function_whitelist()  # skip early when the control file is absent
        sources = {
            'height compensation enabled (coolant+spindle path)': mutate(
                '            call @usr_rapid\n;\t    call @usr_heightcomp_on', '            call @usr_rapid\n\t    call @usr_heightcomp_on'),
            'height compensation in the default path': mutate(
                START_TOOL_AFTER_TC, START_TOOL_AFTER_TC.replace(
                    '            call @start_tool\n', '            call @start_tool\n            call @usr_heightcomp_on\n')),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.check_g_functions, source, label)


# ---------------------------------------------------------------------------
# Suspected PP defects (canonical tests)
# ---------------------------------------------------------------------------

def m00_same_tool_session():
    s = Session()
    s.first_tool()
    s.cut(10, 20, 5, -1)
    mark = s.mark()
    s.same_tool_job(end=dict(bStopM00=True, next_job_tool_number=1, sStopMessage='CHECK PART'),
                    bStopM00=False, job_name='op2')
    s.cut(30, 40, 5, -1)
    return s, Segment(s, mark)


NON_COOLANT_M = frozenset({0, 1, 2, 3, 4, 5, 6, 9, 30})   # stops, spindle, tool change, end, coolant off


def through_coolant_code(through_coolant_val):
    """M codes a first tool change emits after M06 for through-tool coolant only.

    Read from the emitted words (every M code except stops, spindle, M06, M9 and
    program end), not from the replay, whose coolant table is derived from the
    current PP and would not recognise a corrected code such as M70.
    """
    s = Session()
    blocks = parse_blocks(s.first_tool(**dict(NO_COOLANT, through_ival_coolant=1,
                                               through_coolant_val=through_coolant_val)))
    m06 = index_of(blocks, m_code(6))
    return sorted(code for block in blocks[m06 + 1:] for code in block.m if code not in NON_COOLANT_M)


class ToolChangeDefectTests(unittest.TestCase):
    @known_defect('PP-010', match='still on at M06')
    def test_tool_change_options_control_spindle_and_coolant_off(self):
        """INDEPENDENT: option docs 'bSpinofftc/bCoolofftc: True = Outputs Spindle/Coolant off between Tool Changes'.

        With bSpinofftc=bCoolofftc=True and the end-of-program flags
        bSpinoffend=bCooloffend=False, spindle and coolant must be off at M06
        (replayed state). The PP gates the tool-change M5/M9 with the
        end-of-program flags. A missing M06 is a precondition failure (match=).
        """
        s, mark = two_tool_change(options=dict(bSpinofftc=True, bSpinoffend=False, bCoolofftc=True, bCooloffend=False))
        seg = Segment(s, mark)
        m06 = seg.find(m_code(6))
        self.assertGreaterEqual(m06, 0, f'precondition: no M06 in the second tool change:\n{seg.shown}')
        at_change = seg.before(m06)
        self.assertEqual((at_change.spindle, sorted(at_change.coolant)), (5, []),
                         f'bSpinofftc/bCoolofftc=True but spindle/coolant still on at M06:\n{seg.shown}')

    @known_defect('PP-024', facet='coolant', match='coolant in effect when cutting resumes')
    def test_m00_same_tool_restores_coolant_before_next_cut(self):
        """INDEPENDENT: the job requests flood (flood_coolant=1) and M9 switches all coolant off.

        After an M00 between same-tool jobs (VMID job parameter bStopM00) the
        replayed coolant state at the next cut must again be flood (M8). A
        missing M00 or cut is a precondition failure (match=).
        """
        s, seg = m00_same_tool_session()
        stop = seg.find(m_code(0))
        cut = seg.first_feed(stop)
        self.assertTrue(0 <= stop < cut, f'precondition: M00 followed by a cut:\n{seg.shown}')
        self.assertEqual(sorted(seg.states[cut].coolant), [8],
                         f'coolant in effect when cutting resumes after M00:\n{seg.shown}')

    @known_defect('PP-024', facet='ramp-dwell', match='no spindle ramp dwell')
    def test_m00_same_tool_waits_for_spindle_ramp(self):
        """INDEPENDENT oracle: the PP's own spindle-acceleration policy, not machine physics.

        Every other spindle start of this PP dwells S/spindle_accel seconds
        (@init_post spindle_accel = 500 rpm/s; @usr_spindle_output). The restart
        after an M00 between same-tool jobs (S8000 from standstill) gets no
        dwell. Whether the 828D needs one at all is decided by MD35500
        SPIND_ON_SPEED_AT_IPO_START (tc-03 correction: low severity). A missing
        M00, restart or cut is a precondition failure (match=).
        """
        s, seg = m00_same_tool_session()
        stop = seg.find(m_code(0))
        self.assertGreaterEqual(stop, 0, f'precondition: no M00:\n{seg.shown}')
        restart = seg.find(m_code(3, 4), stop)
        cut = seg.first_feed(restart)
        self.assertTrue(stop < restart < cut, f'precondition: M3/M4 restart before the next cut:\n{seg.shown}')
        policy = 8000 / s.state['spindle_accel']
        self.assertGreaterEqual(seg.dwell(restart, cut), policy,
                                f'no spindle ramp dwell between the M3 restart and cutting:\n{seg.shown}')

    @known_defect('PP-025', match='coolant in effect at the first cut')
    def test_same_tool_job_applies_its_coolant_request(self):
        """INDEPENDENT: the per-operation coolant parameters, replayed with M9 = all channels off.

        UNVERIFIED: assumes SolidCAM expects the post to switch coolant between
        consecutive same-tool operations (settle with a trace of two same-tool
        jobs with different coolant). Cases: dry -> flood, and the channel switch
        mist -> flood from the tc-04 correction (an ON-then-M9 order would also
        leave coolant off). A missing cut is a precondition failure (match=).
        """
        problems = {}
        for label, first, second in (
                ('dry -> flood', dict(), dict(flood_coolant=1)),
                ('mist -> flood', dict(Mist_coolant=1), dict(flood_coolant=1))):
            s = Session()
            s.first_tool(**dict(NO_COOLANT, **first))
            s.cut(10, 20, 5, -1)
            mark = s.mark()
            s.same_tool_job(job_name='op2', **dict(NO_COOLANT, **second))
            s.cut(30, 40, 5, -1)
            seg = Segment(s, mark)
            cut = seg.first_feed()
            self.assertGreaterEqual(cut, 0, f'precondition: {label}: no cut in the second job:\n{seg.shown}')
            active = sorted(seg.states[cut].coolant)
            if active != [8]:
                problems[label] = active
        self.assertEqual(problems, {}, 'coolant in effect at the first cut of the second same-tool job')

    @known_defect('PP-027')
    def test_tool_change_does_not_depend_on_previous_tool_being_first(self):
        """INDEPENDENT: metamorphic symmetry, identical inputs give identical tool-change blocks.

        Tool 2 (after the first tool) and tool 3 (after tool 2) change with the
        same job data; after normalising the tool numbers the emitted blocks must
        be equal. The first-tool path leaves bSafetyprep=true, so tool 2 skips
        the full modal reset.
        """
        s = Session()
        s.first_tool()
        s.cut(10, 20, 5, -1, apos=30)
        changes = []
        for tool in (2, 3):
            mark = s.mark()
            s.next_tool(tool, tool + 1, job_name='opX')
            names = {f'T{tool}': 'Tcur', f'T{tool + 1}': 'Tnext'}
            changes.append([[names.get(word.raw, word.raw) for word in block.words] for block in s.blocks(mark)])
            s.cut(10, 20, 5, -1, apos=30)
        first = next((index for index, (two, three) in enumerate(zip(*changes)) if two != three),
                     None if len(changes[0]) == len(changes[1]) else min(map(len, changes)))
        self.assertIsNone(first, f'tool 2 and tool 3 tool-change blocks differ from block {first} on: '
                                 f'{changes[0][first or 0:]} vs {changes[1][first or 0:]}')

    @known_defect('PP-012')
    def test_hsm_job_parameters_emit_only_sinumerik_g_functions(self):
        """INDEPENDENT: the 828D G-function set of vericut/sin840d_special.ctl (no G187; 828D uses CYCLE832).

        VMID job parameters set explicitly (iG187_P=1, nG187_E=0.05), change
        flags cleared (flags='clear'): every emitted G number must be defined.
        """
        defined = g_function_whitelist()
        s = Session(flags='clear')
        s.first_tool(iG187_P=1, nG187_E=0.05)
        s.cut(10, 20, 5, -1)
        foreign = sorted({code for block in s.blocks() for code in block.g} - defined)
        self.assertEqual(foreign, [], f'non-828D G functions for HSM job parameters:\n{listing(s.blocks())}')

    @covers('PP-008')
    def test_through_coolant_pressure_codes_pin(self):
        """CHARACTERIZATION of the owner decision on PP-008 (accepted, not a defect): the
        @usr_coolant pressure table. 5/10/15 bar post M77/76/75 and 40/50/60/70 bar M71..74
        (30+10k bar -> 70+k, history-misc-14); 30 bar posts M7, the same code as the mist
        coolant iCoolantM2ON = 7. The machine has no through-spindle coolant, so the owner
        keeps M7 for 30 bar; the alternative was M70, the free code of the 70+k family.
        The 30 bar line is the literal `07` (ENGINE-006: rewritten by LegacyCompatEngine,
        native in the GPPL engine)."""
        codes = {pressure: through_coolant_code(pressure) for pressure in (5, 10, 15, 30, 40, 50, 60, 70)}
        self.assertEqual(codes, {5: [77], 10: [76], 15: [75], 30: [7], 40: [71], 50: [72], 60: [73], 70: [74]})
        self.assertEqual(Session().state['icoolantm2on'], 7, 'mist coolant code')

    @known_defect('PP-009', match='unlisted pressure after a 70 bar job')
    def test_through_coolant_code_does_not_leak_between_jobs(self):
        """INDEPENDENT: option doc 'iCoolantM5ON = 77 ; High Pressure Coolant Through Tool ON'.

        A per-job parameter must not depend on job order: a pressure outside the
        table (20 bar) gets the configured default M77, also after a job that
        used 70 bar (M74). @usr_coolant overwrites the option iCoolantM5ON.
        Leading-zero workaround (ENGINE-006) is the Session default. A missing
        M06 or cut is a precondition failure (match=).
        """
        default = Session().state['icoolantm5on']
        s = Session()
        s.first_tool(**dict(NO_COOLANT, through_ival_coolant=1, through_coolant_val=70))
        s.cut(10, 20, 5, -1)
        mark = s.mark()
        s.next_tool(2, 3, **dict(NO_COOLANT, through_ival_coolant=1, through_coolant_val=20))
        s.cut(30, 40, 5, -1)
        seg = Segment(s, mark)
        m06 = seg.find(m_code(6))
        cut = seg.first_feed(m06)
        self.assertTrue(0 <= m06 < cut, f'precondition: M06 followed by a cut:\n{seg.shown}')
        self.assertEqual(sorted(seg.states[cut].coolant), [default],
                         f'unlisted pressure after a 70 bar job:\n{seg.shown}')


if __name__ == '__main__':
    unittest.main()
