"""Behaviour of the *current GPP* that full-session replay makes visible.

These are characterisation tests: they pin what the PP does today under the
stated policies so DESIGN.md's findings are reproducible. They are hypotheses
about real machine output until a captured SolidCAM trace confirms them; a PP fix
should flip the corresponding assertion deliberately.
"""
import json
import tempfile
import unittest
from pathlib import Path

from pp_tests.gppl.policies import Policies
from pp_tests.gppl.session import Session, replay_file
from support import FIXTURES, PP, VMID, require_vmid, source


# options_session had this ZX arc as event 8; since 5408e5c a ZX arc stops the post, so the fixture
# reaches the same point with a line and test_zx_arc_stops_the_session puts the arc back.
ZX_ARC_EVENT = {'name': 'arc_zx', 'parameters': {
    'xpos': -40, 'ypos': 0, 'zpos': -5, 'xstart': -50, 'ystart': 0, 'zstart': 5, 'xcenter': -50, 'ycenter': 0,
    'zcenter': -5, 'xcenter_rel': 0, 'ycenter_rel': 0, 'zcenter_rel': -10, 'arc_size': 90, 'arc_direction': 'cw',
    'arc_plane': 'zx', 'radius': 10, 'feed': 500, 'feed_type': 'feed_cut'}}


def replay(name, **policy):
    session, report = replay_file(PP, FIXTURES / f'{name}.json', vmid=VMID, **policy)
    assert report.ok, report.errors
    return session, report


def nc(report):
    return [line.rstrip() for line in report.nc_text.splitlines()]


class ReplayFindings(unittest.TestCase):
    def setUp(self):
        require_vmid(self)

    def test_first_hole_is_not_repositioned_after_mcall(self):
        """Sinumerik MCALL runs the cycle after each *following* positioning block. The
        drill position is reached before 'MCALL CYCLE83', and @drill_point for that same
        hole emits nothing (unchanged XY), so the first hole gets no cycle call."""
        _, report = replay('synthetic_session')
        events = {event.index: event for event in report.events}
        self.assertEqual([line.strip() for line in events[18].nc][:2], ['X25 Y15', 'Z30'])
        self.assertEqual(events[19].name, 'drill_point')
        self.assertEqual(events[19].nc, [])                     # first hole: no block after MCALL
        self.assertEqual([line.strip() for line in events[20].nc], ['X45'])

    def test_coolant_is_not_restored_after_same_tool_m00(self):
        _, report = replay('synthetic_session')
        lines = nc(report)
        stop = lines.index('M0')
        tail = lines[stop:lines.index('M30')]
        self.assertIn('G1 G93 Z5 A=ACP(110) F19.769', tail)        # cutting continues ...
        self.assertFalse([line for line in tail if line.startswith('M8')])   # ... without M8

    def test_multiple_fixtures_delete_loop_counts_from_one_to_2002(self):
        """iTcnumber starts at 2001 (usr_init_gmstates) but the end-of-file delete loop
        runs i = 1..iTcnumber: 2002 delete markers for 2 temp files."""
        _, report = replay('fixtures_subs_session')
        deletes = [line for line in nc(report) if line.startswith('!!delete file=')]
        self.assertEqual(len(deletes), 2002)
        self.assertEqual(deletes[0], '!!delete file=E:\\WORK\\TEMPFILE1!!')
        opened = [line for line in nc(report) if line.startswith('!!open file=')]
        self.assertEqual(opened, ['!!open file=E:\\WORK\\TEMPFILE2001!!', '!!open file=E:\\WORK\\TEMPFILE2002!!'])

    def test_index_warning_is_written_as_an_uncommented_nc_block(self):
        session, report = replay('machine_variants_session', tonum='atof')
        warning = [line for line in nc(report) if 'WARNING' in line]
        self.assertEqual(warning[0], 'WARNING!! Tool Z Level is below Tool Start Plane in CoordSys')
        self.assertIn(('print', 'WARNING!! Tool Z Level is below Tool Start Plane in CoordSys'),
                      session.engine.console)

    def test_cycle84_apostrophe_depends_on_quote_lexing(self):
        _, report = replay('options_session')
        cycle = [line for line in nc(report) if 'CYCLE84' in line][0]
        self.assertIn(",0,'500,1000", cycle)                  # doubled-quote escape (v1 rule)
        _, report = replay('options_session', quote_escape='none')
        cycle = [line for line in nc(report) if 'CYCLE84' in line][0]
        self.assertIn(',0,500,1000', cycle)
        self.assertNotIn("'", cycle)

    def test_m00_with_tool_change_repeats_coolant_and_spindle_off(self):
        """usr_StopM00_difftool sets bStopM00difftool, but end_of_job clears it on the
        next line, so usr_ct_before_notfirsttool emits M9/M5 again after M0."""
        _, report = replay('options_session')
        lines = [line.split(' ', 1)[1] if line.startswith('N') else line for line in nc(report)]
        stop = lines.index('M0')
        self.assertEqual(lines[stop + 2:stop + 4], ['M9', 'M5'])

    def test_call_proc_emits_literal_cr1(self):
        _, report = replay('fixtures_subs_session')
        self.assertIn('G54 cR10', nc(report))
        self.assertIn("{nb,cWo,iWorkoffset' ','cR1',nR1pos}", source())

    def test_subs_mode_leaks_the_9999_sentinel(self):
        # iDiametercomp keeps its 9999 start value in subs mode; since b999f65 the TRC word rides on the
        # first XY rapid instead of the first feed move.
        _, report = replay('subs_session')
        self.assertIn('G9999 X1 Y2', nc(report))

    def test_zx_arc_stops_the_session(self):
        events = json.loads((FIXTURES / 'options_session.json').read_text())
        index = next(i for i, event in enumerate(events['events']) if event['name'] == 'line'
                     and event['parameters'].get('zpos') == -5)
        events['events'][index] = ZX_ARC_EVENT
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'zx.json'
            path.write_text(json.dumps(events))
            _, report = replay_file(PP, path, vmid=VMID)
        self.assertFalse(report.ok)
        self.assertIn('ZX arc direction is unverified', str(report.errors))

    def test_message_split_needs_c_escapes_and_crlf(self):
        """usr_ct_after splits msg at instr(msg,'\\n') and uses poz1-2 / poz1+1: correct
        only if '\\n' is one LF character and SolidCAM separates lines with CR LF."""
        def first_tool_comments(policy, message):
            session = Session.from_paths(PP, vmid=VMID, policies=policy)
            session.start()
            engine = session.engine
            engine.set(msg=message, i4xIndexMode=0, bCoolspinaftertc=False, bsubs=True)
            engine.call('usr_ct_after')
            return [line for line in engine.nc_lines() if line.startswith(';')]
        literal = first_tool_comments(Policies.session(), 'LINE ONE\\nLINE TWO')
        self.assertEqual(literal, [';LINE ON', ';nLINE TWO'])
        c_style = first_tool_comments(Policies.session(string_escapes='c'), 'LINE ONE\r\nLINE TWO')
        self.assertEqual(c_style, [';LINE ONE', ';LINE TWO'])


if __name__ == '__main__':
    unittest.main()
