"""CAMDBG readouts of the post (post-writer option trace_level 5, usr_camdbg_*).

trace_level 5 runs trace "all":5 and writes '; CAMDBG <event> name:value' comment lines with
event inputs the SolidCAM trace omits (date, time, the arc start point, the rotary positions of
the first job, prev_command, next_command), prints as a name (coolant 'no_action',
rot_axis_coord 'axis4_no', the drill type constant D_Tapping) or prints with fewer decimals than
the post computes with (arc centre and arc_size: 3 to 5). pp_tests/tools/input_trace.py promotes
them into the recorded input fixture; tests_engine/test_input_trace.py checks that round trip. An
NC written at trace_level 5 is for analysis only (the trace records go into the NC file;
test_gpp_static.StaticSourceTests keeps trace_level 0 in the shipped post).
"""
import json
import unittest
from collections import Counter

from pp_tests.gppl.session import Session, resolve_policies
from program_session import Program, require_nc_stream
from support import assert_detected, mutate
from support.paths import ROOT, VMID, pp_source
from support.session import HEADER_DEFAULTS

SESSIONS = ROOT / 'tests_engine' / 'fixtures'
SESSION_NAMES = ('synthetic_session', 'options_session', 'machine_variants_session', 'oracle_session',
                 'cycle832_session')
TOOL = dict(tool_number=1, tool_offset=1, tool_message='', holder_name='H', tool_length=20,
            **{f'msg_mill_tool{index}': '' for index in range(1, 6)})
XY_ARC = dict(xpos=0, ypos=10.123456789012, zpos=50, xstart=10.123456789012, ystart=0, zstart=50,
              xcenter_rel=-10.123456789012, ycenter_rel=0, zcenter_rel=0, arc_size=90, arc_direction='ccw',
              arc_plane='xy')
YZ_ARC = dict(xpos=0, ypos=0, zpos=60, xstart=0, ystart=10, zstart=50, xcenter_rel=0, ycenter_rel=-10,
              zcenter_rel=0, arc_size=90, arc_direction='ccw', arc_plane='yz')


def readouts(blocks):
    return [block for block in blocks if block.startswith('; CAMDBG')]


def program_readouts(source=None, trace_level=5):
    """One readout list per event of a short program."""
    p = Program(source=source, options={'trace_level': trace_level})
    result = [readouts(p.ev('start_of_file', **dict(HEADER_DEFAULTS, date='27-OCT-2026', time='17:57:04'))),
              readouts(p.ev('def_tool', **TOOL, next_command='@def_tool')),
              readouts(p.start(tool=1, next_tool=2, apos=90, mist_coolant=2)),
              readouts(p.ev('rapid_move', xpos=10, ypos=10, zpos=50)),
              readouts(p.ev('move_5x', xpos=10, ypos=10, zpos=50, apos=100, dir5a='ccw', prev_command='@line_5x')),
              readouts(p.ev('move_4x', xpos=10, ypos=10, zpos=50, apos=110, dir5a='ccw')),
              readouts(p.ev('arc', **XY_ARC)),
              readouts(p.ev('arc_yz', **YZ_ARC))]
    return result


def replay_lines(name, trace_level, source=None):
    session = json.loads((SESSIONS / f'{name}.json').read_text(encoding='utf-8'))
    meta = session.get('session', {})
    replay = Session(source or pp_source(), vmid=VMID, policies=resolve_policies('session', {}, meta))
    report = replay.replay(session['events'], overrides={**meta.get('overrides', {}), 'trace_level': trace_level},
                           user_params=meta.get('user_params'), stop_on_error=True, synthesize_commands=True)
    if report.errors:
        raise AssertionError(f'{name}: {report.errors}')
    return report.nc_text.splitlines(), Counter(event['name'] for event in session['events'])


class ReadoutTests(unittest.TestCase):
    def setUp(self):
        require_nc_stream()   # the legacy engine has no string functions (usr_US_date)

    def test_each_event_reads_out_its_inputs(self):
        """INDEPENDENT: the readouts name their SolidCAM event (the extractor attaches a readout
        only to the event whose trace record it follows) and print numbers with 9 decimals
        (nCamDbg_f '5.9'): an arc's end is the start rotated about the centre by arc_size and
        must hit the CAM end to 0.001 (usr_arc_math), which 3-decimal arc_size misses. The
        engine resolves the constant D_Tapping to its name; SolidCAM prints its number."""
        self.assertEqual(program_readouts(), [
            ['; CAMDBG start_of_file date:27-OCT-2026 time:17:57:04 d_tapping_value:d_tapping'],
            ['; CAMDBG def_tool next_command:@def_tool'],
            ['; CAMDBG start_of_job angle:0 cpos:0 apos:90 bpos:0 d_drill_type:-1 rot_axis_coord_value:0',
             '; CAMDBG start_of_job flood_coolant_value:1 mist_coolant_value:2 hp_flood_coolant_value:0 '
             'lp_flood_coolant_value:0',
             '; CAMDBG start_of_job through_ival_coolant_value:0 lp_through_coolant_value:0 '
             'air_blast_coolant_value:0 air_through_coolant_value:0 through_coolant_val:0'],
            [],
            ['; CAMDBG move_5x prev_command:@line_5x'],
            ['; CAMDBG move_4x prev_command:@move_5x'],
            ['; CAMDBG arc xstart:10.123456789 ystart:0 zstart:50',
             '; CAMDBG arc xcenter_rel:-10.123456789 ycenter_rel:0 zcenter_rel:0 arc_size:90'],
            ['; CAMDBG arc_yz xstart:0 ystart:10 zstart:50',
             '; CAMDBG arc_yz xcenter_rel:0 ycenter_rel:-10 zcenter_rel:0 arc_size:90'],
        ])

    def test_trace_level_0_writes_no_readout(self):
        """INDEPENDENT: the shipped post (trace_level 0) writes the NC for the machine."""
        self.assertEqual(program_readouts(trace_level=0), [[]] * 8)

    def test_readouts_keep_the_change_flags(self):
        """INDEPENDENT: printing a variable clears its change flag (clear_change_after_gen 1), and
        the post tests change(apos) and change(bpos) in usr_line_4x; the readouts print copies."""
        p = Program(options={'trace_level': 5})
        names = ('angle', 'cpos', 'apos', 'bpos', 'd_drill_type', 'rot_axis_coord', 'flood_coolant', 'xstart',
                 'ystart', 'zstart', 'xcenter_rel', 'ycenter_rel', 'zcenter_rel', 'arc_size')
        p.engine.changed.update({name: True for name in names})
        p.engine.call('usr_camdbg_start_of_job')
        p.engine.call('usr_camdbg_arc')
        self.assertEqual({name: p.engine.changed[name] for name in names}, {name: True for name in names})

    def test_readout_mutations_are_detected(self):
        """INDEPENDENT: mutation self-check of the event name, the copies and the gate."""
        mutants = {
            'arc_yz named arc': ("        sDbg1 = 'arc_yz'\n", "        sDbg1 = 'arc'\n"),
            'gate at trace_level 0': ('    if trace_level >= 5\n        sDbg1 = next_command\n',
                                      '    if trace_level >= 0\n        sDbg1 = next_command\n'),
            'printed without a copy': ("' apos:',nDbg3:nCamDbg_f", "' apos:',apos:nCamDbg_f"),
        }
        checks = {'arc_yz named arc': self.check_readouts, 'gate at trace_level 0': self.check_trace_level_0,
                  'printed without a copy': self.check_flags}
        for label, (old, new) in mutants.items():
            with self.subTest(mutant=label):
                assert_detected(self, checks[label], mutate(old, new), label)

    def check_readouts(self, source):
        self.assertEqual(program_readouts(source)[7][0], '; CAMDBG arc_yz xstart:0 ystart:10 zstart:50')

    def check_trace_level_0(self, source):
        self.assertEqual(program_readouts(source, trace_level=0), [[]] * 8)

    def check_flags(self, source):
        p = Program(source=source, options={'trace_level': 5})
        p.engine.changed['apos'] = True
        p.engine.call('usr_camdbg_start_of_job')
        self.assertTrue(p.engine.changed['apos'])


class SessionReadoutTests(unittest.TestCase):
    def check_session(self, name, source=None):
        plain, _ = replay_lines(name, 0, source)
        traced, events = replay_lines(name, 5, source)
        self.assertEqual([line for line in traced if not line.startswith('; CAMDBG')], plain)
        counts = Counter(line.split()[2] for line in traced if line.startswith('; CAMDBG'))
        expected = Counter({'start_of_file': events['start_of_file'], 'def_tool': events['def_tool'],
                            'start_of_job': 3 * events['start_of_job'], 'move_4x': events['move_4x'],
                            'move_5x': events['move_5x'], 'arc': 2 * events['arc'], 'arc_yz': 2 * events['arc_yz']})
        self.assertEqual(counts, +expected, name)

    def check_sessions(self, source=None):
        for name in SESSION_NAMES:   # mutant runs: the first AssertionError propagates
            self.check_session(name, source)

    def test_readouts_leave_the_nc_lines_and_follow_the_cam_events(self):
        """INDEPENDENT: at trace_level 5 the NC minus the readouts is line for line the NC of
        trace_level 0 (a readout opens its own lines where no block waits to be joined), and
        each SolidCAM event reads out once. prev_command is read out on the 4x/5x rapids, the
        only rapids whose CAM link test reads it (usr_rapid_cam_link); the rapids the post makes
        itself (start_of_job, usr_StopM00_sametool, drill) read out nothing."""
        for name in SESSION_NAMES:
            with self.subTest(session=name):
                self.check_session(name)

    def test_readout_in_the_shared_rapid_is_detected(self):
        """INDEPENDENT: mutation self-check; the move readout in usr_rapid would print for every
        rapid, also the post's own and the 3-axis ones."""
        moved = mutate('    call @usr_camdbg_move((5))\n', '')
        mutant = mutate('\n@usr_rapid\n', '\n@usr_rapid\n    call @usr_camdbg_move((5))\n', source=moved)
        assert_detected(self, self.check_sessions, mutant, 'readout in usr_rapid')


if __name__ == '__main__':
    unittest.main()
