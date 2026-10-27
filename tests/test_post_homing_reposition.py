"""After a homing inserted by the post, X, Y and Z are programmed again before cutting.

Oracle (INDEPENDENT): 'G75 Y1=0 X1=0' leaves X/Y at the machine fixed point and 'G75 Z1=0.' leaves
Z at the top. The axes stay there until they are programmed again, so the next positioning move
must output X, Y and Z even when the CAM values did not change (SolidCAM flags only changed values).
"""
import re
import unittest

from pp_tests.engine import Engine
from program_session import Program, require_nc_stream
from test_motion import motion_engine
from test_offline import PP

HOME_XY = 'G75 Y1=0 X1=0'


def blocks(text):
    return [block.strip() for block in text.splitlines() if block.strip()]


def words(block):
    return dict(re.findall(r'\b([XYZ])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', block))


class Session:
    def __init__(self, source=None):
        engine = motion_engine()
        if source is not None:
            candidate = Engine(source)
            candidate.set(**engine.state)
            candidate.changed.update(engine.changed)
            engine = candidate
        self.engine = engine

    def step(self, call, changed=(), **values):
        self.engine.set(**values)
        for key in ('xpos', 'ypos', 'zpos', 'apos', 'bpos', 'feed'):
            self.engine.changed[key] = False
        self.engine.changed.update({key.lower(): True for key in changed})
        self.engine.output.clear()
        self.engine.call(call)
        return blocks(''.join(self.engine.output))


def axes_after_homing(output):
    """X/Y/Z values programmed after the last XY homing block, in order of appearance."""
    index = max(i for i, block in enumerate(output) if block == HOME_XY)
    seen = []
    for block in output[index + 1:]:
        for axis, value in re.findall(r'\b([XYZ])([+-]?(?:\d+(?:\.\d*)?|\.\d+))', block):
            seen.append((axis, float(value)))
    return seen


class PostHomingRepositionTests(unittest.TestCase):
    def rotate_only_scenario(self, source=None):
        session = Session(source)
        session.step('move_5x', ['zpos'], zpos=50, prev_command='@line_5x')
        rotation = session.step('move_5x', ['apos'], apos=90, prev_command='@move_5x')
        approach = session.step('move_5x', ['zpos'], zpos=10, prev_command='@move_5x')
        return rotation, approach

    def assert_xy_restored_before_descent(self, rotation, approach):
        """X/Y are programmed in an earlier block than the first Z that leaves the homed height."""
        self.assertIn(HOME_XY, rotation)
        after = rotation[rotation.index(HOME_XY) + 1:] + approach
        descent = [i for i, block in enumerate(after) if 'Z' in words(block)]
        self.assertTrue(descent, f'Z never programmed after homing: {after}')
        before = {}
        for block in after[:descent[0]]:
            before.update(words(block))
        self.assertEqual((before.get('X'), before.get('Y')), ('12', '23'),
                         f'X/Y not reprogrammed in a block before the descent: {after}')

    def test_rotation_homing_reprograms_unchanged_xy(self):
        rotation, approach = self.rotate_only_scenario()
        self.assert_xy_restored_before_descent(rotation, approach)
        self.assertEqual(axes_after_homing(rotation)[-1], ('Z', 50.0), 'Z must be programmed after homing')

    def test_index_between_jobs_reprograms_unchanged_y(self):
        session = Session()
        session.engine.set(bR1forceOutput=True)
        session.step('end_of_job')
        session.step('tmatrix', angle_4x_around_x=90)
        index = session.step('start_of_job')
        self.assertIn(HOME_XY, index)
        first = session.step('move_5x', ['xpos', 'zpos'], xpos=15, zpos=20)
        xy = [words(block) for block in first if 'X' in words(block) or 'Y' in words(block)]
        self.assertTrue(xy, first)
        self.assertEqual((xy[0].get('X'), xy[0].get('Y')), ('15', '23'), first)
        self.assertIn('Z20', first)

    def test_without_homing_unchanged_axes_stay_modal(self):
        session = Session()
        session.step('move_5x', ['zpos'], zpos=50, prev_command='@line_5x')
        self.assertEqual(session.step('move_5x', ['zpos'], zpos=40, prev_command='@move_5x'), ['Z40'])

    def test_removing_the_homing_marker_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = '    bPostHomed = true\n'
        self.assertEqual(source.count(anchor), 1, 'homing marker moved; review this test')
        rotation, approach = self.rotate_only_scenario(source.replace(anchor, '', 1))
        with self.assertRaises(AssertionError):
            self.assert_xy_restored_before_descent(rotation, approach)


class PostHomingProgramTests(unittest.TestCase):
    """Whole programs: tool-change homing, M00, subprograms, a feed move right after homing."""

    def two_tools(self, source=None, **options):
        program = Program(options=options, source=source)
        program.start()
        program.ev('move_5x', xpos=10, ypos=20, zpos=50)
        program.ev('line_5x', zpos=-1, feed=200)
        program.ev('move_5x', zpos=50)
        program.ev('end_of_job')
        program.ev('change_tool', tool_number=2, next_tool_number=3, first_tool=False, tool_start_plane=60)
        program.ev('start_of_job', job_name='op2')
        return program

    def test_first_rapid_after_tool_change_reprograms_unchanged_xy(self):
        # The next tool starts over the same XY: SolidCAM flags only Z, the axes stand at G75.
        program = self.two_tools()
        self.assertEqual(program.ev('move_5x', xpos=10, ypos=20, zpos=60), ['X10 Y20', 'Z60'])

    def test_reposition_is_forced_only_once(self):
        program = self.two_tools()
        program.ev('move_5x', xpos=10, ypos=20, zpos=60)
        self.assertEqual(program.ev('move_5x', zpos=40), ['Z40'])
        self.assertEqual(program.ev('move_5x', xpos=120, ypos=90, zpos=50), ['X120 Y90 Z50'])

    def test_feed_move_after_index_homing_returns_in_rapid_then_feeds_in_z(self):
        program = Program()
        program.start()
        program.ev('move_5x', xpos=30, ypos=10, zpos=5)
        program.ev('line_5x', zpos=-2, feed=200)
        program.ev('end_of_job')
        program.ev('tmatrix', angle_4x_around_x=90)
        program.engine.state['btmatrixindexpending'] = True
        self.assertIn(HOME_XY, program.ev('start_of_job', job_name='op2'))
        self.assertEqual(program.ev('line_5x', xpos=40, ypos=15, zpos=-1, feed=200), ['G0 X40 Y15', 'G1 Z-1'])
        self.assertEqual(program.ev('line_5x', xpos=50), ['X50'])

    def test_m00_return_keeps_z_at_home_and_next_job_programs_it(self):
        # M00 with homing (non-default sHomestrstpsame): the return is XY only; the next job comes down.
        program = Program(options=dict(sHomestrstpsame='8::G75 Z1=0. ;8::G75 Y1=0 X1=0'),
                          cam=dict(bStopM00=True, next_job_tool_number=1))
        program.start()
        program.ev('move_5x', xpos=30, ypos=10, zpos=5)
        program.ev('line_5x', zpos=-2, feed=200)
        stop = program.ev('end_of_job')
        self.assertEqual(stop[-3:], ['M0', 'M3', 'G0 X30 Y10'], stop)
        program.ev('start_of_job', job_name='op2')
        self.assertEqual(program.ev('move_5x', xpos=60, ypos=20, zpos=40), ['X60 Y20', 'Z40'])

    def test_subprogram_job_start_keeps_its_own_order(self):
        # bSubs (non-default): X/Y, spindle, then Z once, exactly as before the homing fix.
        program = Program(options=dict(bSubs=True))
        program.ev('start_program')
        program.engine.state['btlchg'] = False
        program.ev('call_proc', label=1, xnext=12, ynext=23)
        program.ev('proc', label=1)
        output = program.ev('start_of_job', job_name='op1', xnext=12, ynext=23, zpos=35, force=dict(zpos=True))
        self.assertEqual(output, ['MSG("op1")', 'G0 G90 X12 Y23 M3', 'S3000', 'G04 F6.3', 'M8', 'Z35'])

    def test_subprogram_tool_change_rapid_keeps_the_reposition(self):
        # The tool-change rapid programs no X/Y: after the start homing, X/Y must come before Z.
        program = Program(options=dict(bSubs=True, sHomestrroth='', sHomestrrotv=''))
        self.assertIn(HOME_XY, program.ev('start_program'))
        program.engine.state.update(btlchg=True, br1forceoutput=False, nr1pos=0, npr1pos=0)
        output = program.ev('start_of_job', job_name='op1', xnext=40, ynext=10, zpos=50, force=dict(zpos=True))
        self.assertEqual(output[-2:], ['X40 Y10', 'Z50'], output)

    def test_file_start_clears_a_stale_homing_mark(self):
        program = Program()
        program.engine.state['bposthomed'] = True
        program.engine.call('usr_init_gmstates')
        self.assertIs(program.engine.state['bposthomed'], False)

    def test_tool_change_branch_must_not_consume_the_reposition(self):
        source = PP.read_text(encoding='utf-8-sig')
        anchor = '    bTlchg = false\n    bClimbZValid = false\n'
        self.assertEqual(source.count(anchor), 1, 'tool-change rapid branch changed; review this test')
        program = self.two_tools(source.replace(anchor, anchor + '    bPostHomed = false\n', 1))
        self.assertEqual(program.ev('move_5x', xpos=10, ypos=20, zpos=60), ['Z60'])


class PostHomingSkiplineTests(unittest.TestCase):
    """The XY/Z split relies on `skipline = true` before the Z block: check the joined NC lines."""

    def rotation_after_cutting(self, source=None):
        require_nc_stream()
        program = Program(source=source)
        program.start()
        program.ev('move_5x', xpos=10, ypos=20, zpos=50)
        program.ev('line_5x', xpos=15, feed=200)
        program.ev('move_5x', apos=30, xpos=50, ypos=60, zpos=3, prev_command='@line_5x')
        nc = program.nc()
        last_homing = len(nc) - 1 - nc[::-1].index(HOME_XY)
        return nc[last_homing + 1:]

    def test_xy_and_z_are_separate_nc_lines(self):
        self.assertEqual(self.rotation_after_cutting()[1:3], ['X50 Y60', 'Z3'])

    def test_skipline_false_before_z_would_join_the_lines(self):
        require_nc_stream()
        source = PP.read_text(encoding='utf-8-sig')
        pattern = re.compile(r"(if bFirstMove or bPostHomed\n\s*if !bFirstMove\n(?:\s*;[^\n]*\n)*"
                             r"\s*call @usr_emulated_rapid_feed\n\s*endif\n\s*skipline = )true")
        self.assertEqual(len(pattern.findall(source)), 1, 'post-homing split changed; review this test')
        broken = pattern.sub(r"\1false", source, count=1)
        self.assertIn('X50 Y60 Z3', self.rotation_after_cutting(broken))


class PostHomingApproachOrderTests(unittest.TestCase):
    """Oracle (INDEPENDENT): the move back from the homing position is post-generated, not CAM-planned
    or collision-checked; traverse XY at the homed Z first, then plunge in Z (same order the post
    already uses for the first move of a job)."""

    def test_rotation_after_cutting_returns_xy_then_z(self):
        session = Session()
        session.step('line_5x', ['xpos'], xpos=15, feed_type='feed_cut')
        output = session.step('move_5x', ['apos', 'xpos', 'ypos', 'zpos'], apos=30, xpos=50, ypos=60, zpos=3,
                              prev_command='@line_5x')
        self.assertEqual(output, ['G75 Z1=0.', HOME_XY, 'G0 A=ACN(30)', 'X50 Y60', 'Z3'])

    def test_rotate_only_returns_xy_then_z(self):
        rotation, _ = PostHomingRepositionTests().rotate_only_scenario()
        self.assertEqual(rotation, ['G75 Z1=0.', HOME_XY, 'G0 A=ACN(90)', 'X12 Y23', 'Z50'])

    def test_rapid_without_homing_keeps_xyz_in_one_block(self):
        session = Session()
        output = session.step('move_5x', ['xpos', 'ypos', 'zpos'], xpos=40, ypos=30, zpos=20,
                              prev_command='@line_5x')
        self.assertEqual(output, ['G0 X40 Y30 Z20'])

    def test_removing_the_split_is_detected(self):
        source = PP.read_text(encoding='utf-8-sig')
        pattern = re.compile(r"if bFirstMove or bPostHomed\n")
        self.assertEqual(len(pattern.findall(source)), 1, 'post-homing split changed; review this test')
        broken = pattern.sub("if bFirstMove\n", source, count=1)
        session = Session(broken)
        session.step('line_5x', ['xpos'], xpos=15, feed_type='feed_cut')
        output = session.step('move_5x', ['apos', 'xpos', 'ypos', 'zpos'], apos=30, xpos=50, ypos=60, zpos=3,
                              prev_command='@line_5x')
        self.assertIn('X50 Y60 Z3', output)


EMULATED_RAPIDS = dict(options=dict(bSyncdrapid=False), cam=dict(job_type='3-d model'))


def without_emulated_feed_calls(source):
    """Remove the rapid feed of the FIRST block of a split rapid (climb, homed XY return); the
    optional F at the end of @usr_rapid_xyz stays."""
    pattern = re.compile(r'\n[ \t]*call @usr_emulated_rapid_feed(?=\n)')
    for name in ('usr_rapid_climb_then_xy', 'usr_rapid_xy_then_z'):
        start = source.index(f'\n@{name}\n')
        end = source.index('\nendp\n', start)
        body = source[start:end]
        if len(pattern.findall(body)) != 1:
            raise AssertionError('emulated rapid feed calls changed; review this test')
        source = source[:start] + pattern.sub('', body) + source[end:]
    return source


class PostHomingEmulatedRapidFeedTests(unittest.TestCase):
    """Oracle (INDEPENDENT): with feed-emulated rapids (bSyncdrapid=false, '3-d model' job) the post
    writes G1 for a rapid and must give it nRapidfeed (F650); F is modal, so the first block of the
    split return carries F650 and the Z block after it inherits it. Before 3e0c345 the return was one
    diagonal block 'X50 Y60 Z3 F650'."""

    def return_after_rotation(self, source=None):
        require_nc_stream()
        program = Program(source=source, **EMULATED_RAPIDS)
        program.start()
        program.ev('move_5x', xpos=10, ypos=20, zpos=50)
        program.ev('line_5x', xpos=15, feed=200)
        program.ev('move_5x', apos=30, xpos=50, ypos=60, zpos=3, prev_command='@line_5x')
        nc = program.nc()
        last_homing = len(nc) - 1 - nc[::-1].index(HOME_XY)
        return nc[last_homing + 2:]

    def test_xy_return_after_homing_moves_at_rapid_feed(self):
        self.assertEqual(self.return_after_rotation(), ['X50 Y60 F650', 'Z3'])

    def test_missing_feed_on_the_xy_return_is_detected(self):
        broken = without_emulated_feed_calls(PP.read_text(encoding='utf-8-sig'))
        self.assertEqual(self.return_after_rotation(broken), ['X50 Y60', 'Z3 F650'])

    def test_synchronised_rapids_get_no_feed(self):
        require_nc_stream()
        program = Program()
        program.start()
        program.ev('move_5x', xpos=10, ypos=20, zpos=50)
        program.ev('line_5x', xpos=15, feed=200)
        program.ev('move_5x', apos=30, xpos=50, ypos=60, zpos=3, prev_command='@line_5x')
        self.assertEqual(program.nc()[-2:], ['X50 Y60', 'Z3'])


if __name__ == '__main__':
    unittest.main()
