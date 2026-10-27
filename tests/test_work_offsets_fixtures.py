"""Work offsets (@home_number) and multiple fixtures (@Multiple_Fixtures) of Gmill_540v_4x.gpp.

Area C (tests/support/defects.py AREAS['C']).

Oracles
-------
* Siemens 828D settable zero offsets: G54..G57 (1st..4th) and G505..G599
  (5th..99th). G58/G59 are axial programmable offsets, G500 deactivates the
  settable offset, G1 is linear interpolation: none of them selects a fixture.
  The modal replay (support.modal) applies exactly these rules, so "the work
  offset in effect at a motion block" is read from the replayed state.
* Multiple fixtures (VMID part parameter iNumber_of_Fixtures > 1): every tool
  block is written to a TEMPFILE between '!!open file=F!!' and
  '!!close file=F!!' and replayed once per fixture with '!!copy file=F!!'.
  Copy i must machine fixture i (work offset G54, G55, ... in settable-offset
  order) at the rotary angle its block was programmed for; the copies may
  differ only in the work offset. The directive semantics are the only
  coherent reading of @Multiple_Fixtures (expand_fixture_copies below); how
  SolidCAM treats '!!delete file!!' for missing files is unknown (PP-035).
* c85f5f7 intent (DESIGN-006): the shipped @home_number maps every CoordSys to
  G54 (single origin). pp-weird-hunter-11 (a second CoordSys must not be G54)
  is REFUTED and not ported.

Multiple-fixture sessions use Session(header=True): @start_of_file enables
fixture mode. Known defects owned here: PP-014, PP-032, PP-033, PP-034
(next-tool-index, same-tool-offset, start-angle), PP-035; DESIGN-006 is
pinned with @covers. ReversionDetectionTests re-runs the regression checks on
focused in-memory mutants and requires an AssertionError from each.
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


def expand_fixture_copies(text):
    """Resolve the !!open/close/copy file!! directives of @Multiple_Fixtures.

    Blocks between '!!open file=F!!' and '!!close file=F!!' are written to F
    instead of the program; '!!copy file=F!!' inserts F's blocks at that point;
    '!!delete file!!' has no effect on the program. Returns
    [(block_text, origin)], origin (F, copy_number) for copied blocks, None
    for blocks of the main program.
    """
    files, capturing, program, copies = {}, None, [], {}
    for line in text.splitlines():
        block = line.strip()
        if not block:
            continue
        directive = DIRECTIVE.fullmatch(block)
        if directive:
            action, name = directive.groups()
            if action == 'open':
                capturing = name
                files[name] = []
            elif action == 'close':
                capturing = None
            elif action == 'copy':
                copies[name] = copies.get(name, 0) + 1
                program.extend((content, (name, copies[name])) for content in files.get(name, []))
            continue
        if capturing is not None:
            files[capturing].append(block)
        else:
            program.append((block, None))
    return program


def copied_motion(text):
    """[(block, file, copy number, work offset, A)] for every copied X/Y/Z motion block.

    Modal replay (support.modal) over the expanded program: work offset and A
    position in effect at each block.
    """
    program = expand_fixture_copies(text)
    states = replay([parse_block(block) for block, _ in program])
    return [(block.raw, origin[0], origin[1], state.work_offset, state.a)
            for (block, state), (_, origin) in zip(states, program)
            if origin is not None and block.axes]


def opened_files(text):
    return [match[1] for match in re.finditer(r'(?m)^!!open file=(.+?)!!\s*$', text)]


def two_tool_program(fixtures, second_tool_index=None, source=None):
    """Tool 1 at A0, optional tmatrix index before tool 2, tool 2, program end."""
    session = Session(source=source, header=True, vmid=dict(iNumber_of_Fixtures=fixtures))
    session.first_tool(tool=1, next_tool=2)
    session.cut(10, 20, 5, -3)
    session.next_tool(2, 2, tmatrix=second_tool_index, last_tool=True)
    session.cut(15, 25, 5, -2)
    session.ev('end_of_job')
    session.ev('end_program', last_tool=True)
    return session


def one_tool_two_faces_program(fixtures=2):
    """One tool: job 1 at A0, tmatrix index to A90, job 2 (same tool), program end."""
    session = Session(header=True, vmid=dict(iNumber_of_Fixtures=fixtures))
    session.first_tool(tool=1, next_tool=1, last_tool=True)
    session.cut(10, 20, 5, -3)
    session.same_tool_job(tmatrix=90, job_name='op2')
    session.cut(15, 25, 5, -2)
    session.ev('end_of_job')
    session.ev('end_program', last_tool=True)
    return session


def copy_offsets(rows, name):
    """{copy number: sorted offsets} for the copies of file `name`."""
    result = {}
    for _, file, number, offset, _ in rows:
        if file == name:
            result.setdefault(number, set()).add(offset)
    return {number: sorted(offsets) for number, offsets in sorted(result.items())}


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
# Multiple fixtures
# ---------------------------------------------------------------------------
class MultipleFixtureTests(unittest.TestCase):
    def _check_four_fixtures(self, source=None):
        session = two_tool_program(4, source=source)
        text = session.text()
        rows = copied_motion(text)
        files = opened_files(text)
        self.assertEqual(len(files), 2, text)
        for name in files:
            self.assertEqual(copy_offsets(rows, name), {1: [54], 2: [55], 3: [56], 4: [57]}, name)

    def test_four_fixtures_use_g54_to_g57(self):
        """INDEPENDENT: Siemens settable offsets G54..G57 are fixtures 1..4.

        With iNumber_of_Fixtures=4 every tool block (both TEMPFILEs) is
        replayed four times and copy i runs entirely in G(53+i) (modal replay
        over the expanded program).
        """
        self._check_four_fixtures()

    @known_defect('PP-033')
    def test_fifth_and_sixth_fixture_use_extended_settable_offsets(self):
        """INDEPENDENT: Siemens 828D: the settable offsets after G57 are G505,
        G506, ...; G58/G59 are axial programmable offsets that do not select a
        fixture (Siemens PG Fundamentals 'Axial zero offset G58/G59').

        The copy loop emits {cWo,(iWorkoffset-1)+i}, i.e. G58/G59 for copies
        5/6, so they rerun fixture 4's toolpath in G57 (double cut, fixtures 5
        and 6 unmachined).
        """
        session = two_tool_program(6)
        rows = copied_motion(session.text())
        name = opened_files(session.text())[0]
        offsets = copy_offsets(rows, name)
        if {number: offsets.get(number) for number in range(1, 5)} != {1: [54], 2: [55], 3: [56], 4: [57]}:
            raise RuntimeError(f'scenario precondition failed (copies 1-4 must be G54..G57): {offsets}')
        self.assertEqual(offsets,
                         {1: [54], 2: [55], 3: [56], 4: [57], 5: [505], 6: [506]},
                         '{fixture copy: offsets in effect}')

    def _check_fixture_mode_switch(self, source=None):
        for count, expected in ((0, False), (1, False), (2, True)):
            with self.subTest(fixtures=count):
                session = Session(source=source, header=True, vmid=dict(iNumber_of_Fixtures=count),
                                  blknum_exist=True)
                self.assertEqual(bool(session.state['bmultiplefixtures']), expected)
                # Copied TEMPFILEs would duplicate N numbers, so they are switched off.
                self.assertEqual(bool(session.state['blknum_exist']), not expected)

    def test_start_of_file_enables_fixture_mode_only_for_several_fixtures(self):
        """INDEPENDENT: VMID part parameter iNumber_of_Fixtures: fixture mode (and
        the copy loop) only makes sense for two or more fixtures; block
        numbers are switched off in fixture mode because each copy would
        repeat the TEMPFILE's N numbers."""
        self._check_fixture_mode_switch()

    @known_defect('PP-035')
    def test_end_of_file_deletes_only_created_tempfiles(self):
        """INDEPENDENT: cleanup should delete exactly the TEMPFILEs the program
        created; the expected names come from the '!!open file=' directives
        (R1-09 correction), so any correct fix flips this test.

        Tempfile numbering starts at 2001 (@usr_init_gmstates iTcnumber), but the
        delete loop runs TEMPFILE1..iTcnumber: 2000 directives for files that
        never existed.
        """
        session = two_tool_program(2)
        session.ev('end_of_file')
        text = session.text()
        opened = set(opened_files(text))
        deleted = {match[1] for match in re.finditer(r'(?m)^!!delete file=(.+?)!!\s*$', text)}
        if len(opened) != 2:
            raise RuntimeError(f'scenario precondition failed (two TEMPFILEs expected): {sorted(opened)}')
        extra = sorted(deleted - opened)
        self.assertEqual((sorted(opened - deleted), len(extra)), ([], 0),
                         f'(created but not deleted, deletes of never-created files), e.g. {extra[:3]}')


class MultipleFixtureIndexTests(unittest.TestCase):
    """iNumber_of_Fixtures > 1 together with 4x indexing (PP-034). Oracle: copy
    i of a tool block machines fixture i (G54, G55, ...) at the rotary angle
    the block was programmed for; copies differ only in the work offset."""

    def _check_harness(self, source=None):
        # The helper itself on a synthetic directive text.
        synthetic = '\n'.join(['G0 X1', '!!open file=F!!', 'X2', '!!close file=F!!', '!!copy file=F!!',
                               'G55', '!!copy file=F!!', '!!delete file=F!!', 'M30'])
        self.assertEqual(expand_fixture_copies(synthetic),
                         [('G0 X1', None), ('X2', ('F', 1)), ('G55', None), ('X2', ('F', 2)), ('M30', None)])
        # A real two-fixture program without indexing.
        session = two_tool_program(2, source=source)
        rows = copied_motion(session.text())
        name = opened_files(session.text())[0]
        self.assertEqual(copy_offsets(rows, name), {1: [54], 2: [55]}, session.text())
        self.assertEqual(sorted({a for _, file, _, _, a in rows if file == name}), [0.0], session.text())
        first = [block for block, file, number, _, _ in rows if file == name and number == 1]
        second = [block for block, file, number, _, _ in rows if file == name and number == 2]
        self.assertEqual(first, second, 'copies differ in their motion blocks')

    def test_harness_replays_a_tool_block_per_fixture(self):
        """INDEPENDENT: harness validation of expand_fixture_copies and the
        fixture contract (module docstring). Without indexing, tool 1's block is
        replayed twice: copy 1 in G54, copy 2 in G55, both at A0, with
        identical motion blocks."""
        self._check_harness()

    @known_defect('PP-034', facet='next-tool-index')
    def test_copies_run_at_the_rotary_angle_of_their_tool_block(self):
        """INDEPENDENT: fixture contract (class docstring): tool 1 is programmed
        at A0, so every copy of its block runs at A0.

        The next tool's deferred tmatrix index runs in @start_of_job before
        @usr_ct closes tool 1's TEMPFILE, so 'M1 / G75 / A=ACN(90)' becomes
        the end of tool 1's block and copy 2 machines tool 1's A0 toolpath on
        the part rotated to A90 (crash/gouge risk).
        """
        session = two_tool_program(2, second_tool_index=90)
        rows = copied_motion(session.text())
        name = opened_files(session.text())[0]
        wrong = [(number, block, a) for block, file, number, _, a in rows if file == name and a != 0]
        self.assertEqual(wrong, [], 'tool 1 is programmed at A0; (fixture copy, block, A) executed elsewhere')

    @known_defect('PP-034', facet='same-tool-offset')
    def test_fixture_copy_keeps_its_work_offset_after_a_same_tool_index(self):
        """INDEPENDENT: fixture contract: every block of copy i runs in G(53+i).

        An index inside a tool block re-emits G54 (start_of_job forces
        change(iWorkoffset) for the deferred index, 3696aa2), so the rest of
        copy 2 machines fixture 1 again.
        """
        session = one_tool_two_faces_program()
        rows = copied_motion(session.text())
        name = opened_files(session.text())[0]
        wrong = [(number, block, offset) for block, file, number, offset, _ in rows
                 if file == name and offset != 53 + number]
        self.assertEqual(wrong, [], "(fixture copy, block, active offset) outside the copy's fixture offset")

    @known_defect('PP-034', facet='start-angle')
    def test_fixture_copy_restores_the_starting_angle_of_its_tool_block(self):
        """INDEPENDENT: fixture contract: job 1 of the block is programmed at A0
        in every copy.

        The tool-change rapid with A=DC(0) is posted before '!!open file', so
        the block never re-establishes its start angle: after a same-tool
        index, copy 2 starts at the A90 copy 1 ended at.
        """
        session = one_tool_two_faces_program()
        rows = copied_motion(session.text())
        name = opened_files(session.text())[0]
        job1 = [(number, block, a) for block, file, number, _, a in rows
                if file == name and block in ('X10 Y20', 'G1 Z-3 F500')]
        if sorted({number for number, _, _ in job1}) != [1, 2]:
            raise RuntimeError(f'scenario precondition failed (job 1 blocks of both copies): {job1}')
        self.assertEqual([entry for entry in job1 if entry[2] != 0], [],
                         'job 1 of the block is programmed at A0; (copy, block, A) executed elsewhere')


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
    ('copy loop offsets shifted by one',
     [('{nb,cWo,((iWorkoffset-1)+i)}', '{nb,cWo,(iWorkoffset+i)}', 2)],
     MultipleFixtureTests, '_check_four_fixtures'),
    ('fixture mode enabled for a single fixture',
     [('    if iNumber_of_Fixtures > 1\n        bMultiplefixtures = true',
       '    if iNumber_of_Fixtures > 0\n        bMultiplefixtures = true', 1)],
     MultipleFixtureTests, '_check_fixture_mode_switch'),
    ('copy loop runs once',
     [('while i <= iNumber_of_Fixtures', 'while i <= 1', 2)],
     MultipleFixtureIndexTests, '_check_harness'),
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
