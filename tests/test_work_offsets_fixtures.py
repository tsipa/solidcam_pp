"""Work offsets (@home_number) of Gmill_540v_4x.gpp.

Area C (tests/support/defects.py AREAS['C']).

Oracles
-------
* Siemens 828D settable zero offsets: G54..G57 (1st..4th) and G505..G599
  (5th..99th). G58/G59 are axial programmable offsets, G500 deactivates the
  settable offset, G1 is linear interpolation: none of them selects a fixture.
  The modal replay (support.modal) applies exactly these rules, so "the work
  offset in effect at a motion block" is read from the replayed state.
* c85f5f7 intent (DESIGN-006): the shipped @home_number maps every CoordSys to
  G54 (single origin). pp-weird-hunter-11 (a second CoordSys must not be G54)
  is REFUTED and not ported.
* Multiple fixtures (iNumber_of_Fixtures > 1) stop the post since the template
  feature was removed (owner decision 2026-10-27): test_unsupported_features.py.

Known defects owned here: PP-014, PP-032; DESIGN-006 is pinned with @covers.
ReversionDetectionTests re-runs the regression checks on focused in-memory
mutants and requires an AssertionError from each.
"""
import re
import unittest

from pp_tests.engine import UnsupportedGPPL

from support import (SETTABLE_OFFSETS, Session, assert_detected, covers, known_defect, mutate, parse_block,
                     replay)

# SETTABLE_OFFSETS (support.modal): Siemens 828D settable work offsets G54..G57
# (1st..4th) and G505..G599 (5th..99th); G58/G59 are axial offsets.
DIRECTIVE = re.compile(r'!!(open|close|copy|delete) file=(.+?)!!')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def motion_offsets(session, since=0):
    """Sorted work offsets in effect at the X/Y/Z motion blocks emitted since `since`.

    The replay covers the whole program, so offsets programmed earlier count.
    """
    replayed = session.replay()
    tail = len(session.blocks(since))
    return sorted({state.work_offset for block, state in replayed[len(replayed) - tail:] if block.axes})


def first_job_offsets(vmid=None, source=None, **job):
    """Offsets in effect at the motion blocks of a first job (incl. the tool-change rapid)."""
    session = Session(source=source, vmid=vmid)
    session.first_tool(**job)
    session.cut(10, 20, 5, -1)
    return motion_offsets(session)


# ---------------------------------------------------------------------------
# @home_number
# ---------------------------------------------------------------------------
class WorkOffsetTests(unittest.TestCase):
    def _check_shipped_g54(self, source=None):
        self.assertEqual(first_job_offsets(source=source, position=1), [54])

    def test_shipped_method_selects_g54(self):
        """INDEPENDENT: shipped iWorkOffset_Method=0 (VMID default) with
        iWorkOffsetmode=1 maps CoordSys position 1 to the first settable offset
        G54; every motion of the first job runs in G54."""
        self._check_shipped_g54()

    @covers('DESIGN-006')
    def test_shipped_method_ignores_coordsys_position(self):
        """CHARACTERIZATION of DESIGN-006 (single origin, c85f5f7 intent).

        A second CoordSys (position 2 with its own shift, MAC CoordSys number
        home_number=2) still runs in G54: the MAC CoordSys number is ignored and
        the template's newshift_x/y/z / ORGXYZ were computed but never output (deleted in the
        fixup round).
        Alternatives: map the MAC number to G(53+home_number) as standard
        SolidCAM templates do, or output the shift (TRANS); the owner must
        confirm that all CoordSys share one origin. The refuted
        pp-weird-hunter-11 expectation (G55) is deliberately not asserted.
        """
        self.assertEqual(first_job_offsets(position=2, shift_x=150, shift_y=-40, home_number=2), [54])

    def _check_user_defined_numbers(self, source=None):
        for name, expected in (('54', 54), ('57', 57), ('505', 505), ('599', 599)):
            with self.subTest(home_user_name=name):
                self.assertEqual(first_job_offsets(vmid=dict(iWorkOffset_Method=1), source=source,
                                                   home_user_name=name), [expected])

    def test_user_defined_numbers_map_to_settable_offsets(self):
        """INDEPENDENT: VMID iWorkOffset_Method=1 takes the offset number from the
        CoordSys user name; valid Siemens settable offsets (G54, G57, G505,
        G599) are used unchanged for the whole job."""
        self._check_user_defined_numbers()

    @known_defect('PP-032')
    def test_user_defined_offset_must_be_a_settable_offset(self):
        """INDEPENDENT: Siemens 828D settable offsets are G54..G57 and
        G505..G599; with iWorkOffset_Method=1 any other operator entry must stop
        the post instead of being emitted as the work offset.

        Currently '1' becomes G1 (linear interpolation), '500' G500 (settable
        offsets off) and '58' an axial programmable offset; the job then runs
        in whatever frame was active.
        """
        problems = {}
        for name in ('1', '500', '58'):
            try:
                offsets = first_job_offsets(vmid=dict(iWorkOffset_Method=1), home_user_name=name)
            except UnsupportedGPPL as stopped:
                if 'postprocessor stopped' not in str(stopped):
                    raise
                continue
            if not offsets or not set(offsets) <= SETTABLE_OFFSETS:
                problems[name] = offsets
        self.assertEqual(problems, {}, 'home_user_name -> offsets in effect at the motion blocks '
                                       '(None = no settable offset selected)')


class SameToolWorkOffsetChangeTests(unittest.TestCase):
    @known_defect('PP-014', match='without a machine-Z retract')
    def test_new_work_offset_is_entered_from_a_machine_z_retract(self):
        """INDEPENDENT: machining rule: the previous job's clearance height,
        measured in another fixture's offset, says nothing about the new
        fixture, so the tool must retract in machine coordinates (G75 Z, SUPA or
        G53 with Z) before the first XY traverse in a new work offset.

        VMID iWorkOffset_Method=1 for the whole program (a machine parameter,
        constant during a program); one tool; job 1 on CoordSys '54' ends 5 mm
        above fixture 1; job 2 is on CoordSys '55'. The PP posts
        'G0 G17 G90 G55' and traverses 'X100 Y100' at job 1's machine Z.
        """
        session = Session(X5_job=False, vmid=dict(iWorkOffset_Method=1), home_user_name='54')
        session.first_tool(tool=1, next_tool=1, last_tool=True)
        session.ev('rapid_move', ('xpos', 'ypos', 'zpos'), xpos=10, ypos=20, zpos=5)
        session.ev('line', ('zpos', 'feed'), zpos=-3)
        session.ev('line', ('xpos',), xpos=60)
        session.ev('rapid_move', ('zpos',), zpos=5)           # job 1 ends 5 mm above fixture 1
        session.ev('end_of_job')
        if 54 not in {state.work_offset for block, state in session.replay() if block.axes}:
            raise RuntimeError(f'scenario precondition failed (job 1 not in G54): {session.text()!r}')
        mark = session.mark()
        session.engine.set(home_user_name='55')               # CoordSys of job 2 (SolidCAM job data)
        session.ev('start_of_job', job_name='op2')
        session.ev('rapid_move', ('xpos', 'ypos', 'zpos'), xpos=100, ypos=100, zpos=50)
        blocks = session.blocks(mark)
        text = session.text(mark)
        offset = next((index for index, block in enumerate(blocks) if 55 in block.g), None)
        first_xy = next((index for index, block in enumerate(blocks) if {'X', 'Y'} & set(block.axes)), None)
        if offset is None or first_xy is None:
            raise RuntimeError(f'scenario precondition failed (no G55 or no XY move): {text!r}')
        retract = [block.raw for block in blocks[:first_xy]
                   if 'Z' in block.homing_axes or ((53 in block.g or block.has('SUPA')) and 'Z' in block.axes)]
        self.assertTrue(retract, f'XY traverse in G55 without a machine-Z retract: {text!r}')


# ---------------------------------------------------------------------------
# Negative validation
# ---------------------------------------------------------------------------
# (label, [(old, new, count), ...], holder class, check method)
REVERSIONS = [
    ('shipped method maps CoordSys to G55',
     [('        if iWorkOffsetmode eq 1\n            iWorkoffset = 54\n',
       '        if iWorkOffsetmode eq 1\n            iWorkoffset = 55\n', 1)],
     WorkOffsetTests, '_check_shipped_g54'),
    ('user-defined offset number shifted',
     [('    else\n        iWorkoffset = tonum(home_user_name)\n    endif',
       '    else\n        iWorkoffset = tonum(home_user_name) + 1\n    endif', 1)],
     WorkOffsetTests, '_check_user_defined_numbers'),
]


class ReversionDetectionTests(unittest.TestCase):
    def test_focused_reversions_fail_with_assertion(self):
        """INDEPENDENT: negative validation. Each focused mutation of a guarded
        behaviour is applied in memory and its check must fail with
        AssertionError (interpreter errors propagate; survivors fail)."""
        for label, edits, holder, check in REVERSIONS:
            with self.subTest(reversion=label):
                mutant = None
                for old, new, count in edits:
                    mutant = mutate(old, new, source=mutant, count=count)
                assert_detected(self, getattr(holder(), check), mutant, label)


if __name__ == '__main__':
    unittest.main()
