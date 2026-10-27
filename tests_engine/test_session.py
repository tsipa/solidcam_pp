"""Full-session replay: init_post .. end_of_file through the real GPP."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from pp_tests.gppl.__main__ import main as cli
from pp_tests.gppl.calltrace import CallTrace
from pp_tests.gppl.coverage import Coverage, load_for
from pp_tests.gppl.errors import MissingInput
from pp_tests.gppl.session import (Session, compare_with_trace, load_events, replay_file,
                                   sanitize_for_replay)
from pp_tests.trace import parse_trace, sanitize
from pp_tests.file_commands import assemble_files
from support import FIXTURES, PP, ROOT, SESSIONS, VMID, lines_matching, require_vmid, source, statement_kinds_from_text

MAIN = FIXTURES / 'synthetic_session.json'
ORACLE = FIXTURES / 'oracle_session.json'


def main_replay(**policy):
    return replay_file(PP, MAIN, vmid=VMID, **policy)


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli([str(arg) for arg in args])
    return code, out.getvalue(), json.loads(err.getvalue())


class SessionReplayTests(unittest.TestCase):
    def setUp(self):
        require_vmid(self)

    def test_synthetic_full_session(self):
        session, report = main_replay()
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(all(event.called for event in report.events))
        lines = [line.rstrip() for line in assemble_files(report.nc_text).splitlines()]
        self.assertEqual(lines[:9], [
            ';%_N_DEMO_PART_1_MPF', ';$PATH=/_N_WKS_DIR/_N_WPD', ';Oct-26-2026-2:05:33PM',
            ';SYNTHETIC REPLAY', ';TOOL 1 - DIA 10 | HOLDER: BT40-ER32 | STICKOUT: 45 mm',
            ';T2-DRILL 6 | HOLDER: BT40-ER25 | STICKOUT: 60.5 mm', ';---HSS', 'MSG(" Loading Zeropoints ")',
            'WORKPIECE(,"A",,"BOX",0,0,-30,-25,0,0,100,60)'])
        expected_in_order = ['G75 Z1=0.', 'T1', 'M06', 'D1', 'T2', 'MSG("F_CONTOUR")', 'X10 Y20', 'Z5',
                             'G1 G41 Y30 Z-5 F600', 'X40', 'G2 X50 Y20 I0 J-10', 'G1 Y0', 'G0 Z50', 'G40 X50 Y0',
                             'M9', 'M5', 'M1', 'T2', 'MSG("D_PECK")', 'X25 Y15', 'MCALL CYCLE83 (30,0,2,-20,,,4,4,,0.5,1,1)',
                             'X45', 'MCALL', 'G54 A=ACN(90)', 'MSG("F_SIDE_A90")', 'M0', ';CHECK PART',
                             'MSG("F_5X")', 'G0 A=ACN(100)', 'G1 G93 Z5 A=ACP(110) F19.769', 'G94 Z30 F300',
                             'G0 A=ACN(120)',
                             'A=ACN(135)', 'M30']
        position = 0
        for token in expected_in_order:
            found = next((i for i in range(position, len(lines)) if lines[i] == token), None)
            self.assertIsNotNone(found, f'{token!r} missing/out of order after line {position}')
            position = found + 1
        self.assertEqual(lines[-1], 'M30')
        rotation = lines.index('G0 A=ACN(120)')
        self.assertEqual(lines[rotation - 1], 'G94 Z30 F300')   # CAM-link retract authorises the rotary rapid

    def test_inline_per_event_oracles(self):
        _, report = replay_file(PP, ORACLE, vmid=VMID)
        self.assertTrue(report.ok, (report.errors, report.failures))
        self.assertIn('ARC end mismatch', str(report.events[-1].error))      # expected error, replay continued
        _, flipped = replay_file(PP, ORACLE, vmid=VMID, change_on_equal_assign='clear')
        self.assertEqual(flipped.failures, [
            "event #6 @start_of_job: 0 line(s) start with 'M9', expected 7",
            "event #11 @arc: blocks ['G2 I0 J-10'] != ['G2 X50 Y20 I0 J-10']"])
        _, flipped = replay_file(PP, ORACLE, vmid=VMID, event_flag_reset='globals_after_event')
        self.assertIn("event #9 @line: blocks ['G1 Y30 Z-5 F600'] != ['G1 G41 Y30 Z-5 F600']", flipped.failures)

    def test_gppl_policy_reaches_fixture_replays(self):
        code = ('import sys; from pp_tests.gppl.session import replay_file; '
                's, r = replay_file(sys.argv[1], sys.argv[2], vmid=sys.argv[3]); print(len(r.failures))')
        env = dict(os.environ, GPPL_POLICY='change_on_equal_assign=clear')
        out = subprocess.run([sys.executable, '-c', code, str(PP), str(ORACLE), str(VMID)], cwd=ROOT,
                             env=env, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), '2', out.stderr)

    def test_trace_log_round_trips_through_trace_py(self):
        session, report = main_replay()
        parsed = parse_trace(report.trace_text)
        self.assertEqual([e.name for e in parsed], [e.name for e in report.events])
        for want, got in zip(parsed, report.events):
            with self.subTest(event=got.index, name=got.name):
                for key, value in got.params.items():
                    self.assertEqual(want.parameters[key], value)
                numeric = {k: v for k, v in got.flags.items()
                           if isinstance(got.params[k], (int, float)) and not isinstance(got.params[k], bool)}
                self.assertEqual(want.changed, numeric)
                self.assertEqual(want.output, [line.rstrip() for line in got.nc])

    def test_replaying_a_parsed_trace_reproduces_the_nc_and_diffs_clean(self):
        events, extension, recorded = load_events(MAIN)
        self.assertIsNone(recorded)
        _, original = main_replay()
        trace = parse_trace(original.trace_text)
        again = Session.from_paths(PP, vmid=VMID)
        replay = again.replay(trace, user_params=extension['user_params'], synthesize_commands=False)
        self.assertEqual(replay.nc_text, original.nc_text)
        self.assertEqual(compare_with_trace(trace, replay), [])

    def test_trace_diff_pinpoints_a_source_regression(self):
        _, original = main_replay()
        trace = parse_trace(original.trace_text)
        mutant = source().replace("{nb, 'D1 '}", "{nb, 'D2 '}", 1)
        replay = Session(mutant, vmid=VMID).replay(trace, user_params=load_events(MAIN)[1]['user_params'])
        self.assertEqual(compare_with_trace(trace, replay), ['event 5 @start_of_job: line 4: D1 vs D2',
                                                             'event 16 @start_of_job: line 9: D1 vs D2'])

    def test_cli_replays_a_raw_trace_with_tolerance(self):
        _, original = main_replay()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'session.trace.txt'
            path.write_text(original.trace_text, encoding='utf-8')
            code, _, summary = run_cli('replay', PP, path, '--vmid', VMID)
            # user parameter Message1 is not part of a trace, so the header comment is the only difference
            self.assertEqual((code, summary['trace_diff']),
                             (3, ["event 0 @start_of_file: line 3: expected ';SYNTHETIC REPLAY', got None"]))
            nudged = original.trace_text.replace('> X10 Y20', '> X10.0004 Y20', 1)
            self.assertNotEqual(nudged, original.trace_text)
            path.write_text(nudged, encoding='utf-8')
            _, _, loose = run_cli('replay', PP, path, '--vmid', VMID)
            _, _, tight = run_cli('replay', PP, path, '--vmid', VMID, '--tolerance', '0.0001')
            self.assertEqual(len(loose['trace_diff']), 1)
            self.assertEqual(len(tight['trace_diff']), 2)
            self.assertIn('X10.0004 vs X10', tight['trace_diff'][1])

    def test_cli_replays_captures_that_start_with_init_post(self):
        """`python -m pp_tests capture` output starts with init_post; replay must not
        start the session twice (the session-emulator prototype crashed here)."""
        _, original = main_replay()
        with tempfile.TemporaryDirectory() as tmp:
            trace_path, capture = Path(tmp) / 't.txt', Path(tmp) / 'capture.json'
            trace_path.write_text(original.trace_text, encoding='utf-8')
            out = subprocess.run([sys.executable, '-m', 'pp_tests', 'capture', str(trace_path), str(capture)],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(json.loads(capture.read_text())['events'][0]['name'], 'init_post')
            code, _, summary = run_cli('replay', PP, capture, '--vmid', VMID)
            self.assertEqual(code, 2)                       # sanitize() redacted d_drill_type: refused, no crash
            self.assertIn('d_drill_type was redacted', summary['errors'][0])
            safe = Path(tmp) / 'safe.json'
            safe.write_text(json.dumps({'schema': 1, 'events': sanitize_for_replay(parse_trace(original.trace_text))}))
            code, nc, summary = run_cli('replay', PP, safe, '--vmid', VMID)
            self.assertEqual((code, summary['errors']), (0, []))
            self.assertTrue(assemble_files(nc).rstrip().endswith('M30'))

    def test_replay_of_sanitized_capture(self):
        _, original = main_replay()
        recorded = parse_trace(original.trace_text)
        captured = sanitize(recorded)                       # pp_tests/trace.py, unchanged
        self.assertEqual(captured[1]['parameters']['part_name'], '<redacted>')
        report = Session.from_paths(PP, vmid=VMID).replay(captured)
        self.assertEqual(len(report.errors), 1)              # first redacted CAM enum stops replay
        self.assertIn('d_drill_type was redacted by trace.sanitize()', str(report.errors[0]))
        safe = sanitize_for_replay(recorded)
        report = Session.from_paths(PP, vmid=VMID).replay(safe)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.events[1].substitutions['date'], '01-Jan-2000')
        self.assertIn(';Jan-01-2000-12:00:00PM', report.nc_text)

        def body(text):
            return [line for line in text.splitlines()
                    if line.startswith(('G', 'X', 'Y', 'Z', 'A=', 'M')) and not line.startswith('MSG')]
        self.assertEqual(body(report.nc_text), body(original.nc_text))

    def test_contract_warnings_and_missing_inputs(self):
        session = Session.from_paths(PP, vmid=VMID)
        session.start()
        with self.assertRaises(MissingInput):
            session.event('start_of_file', {'program_number': 1})
        record = session.events[-1]
        self.assertTrue({'part_name', 'date', 'time'} <= set(record.contract_warnings))
        self.assertIsNotNone(record.error)

    def test_events_without_procedure_are_recorded(self):
        session = Session.from_paths(PP, vmid=VMID)
        record = session.event('cool_flood', {'flood_coolant': 1})
        self.assertFalse(record.called)
        self.assertIn('no procedure in PP', session.recorder.text())

    def test_calltrace_explains_who_emitted_an_nc_word(self):
        trace = CallTrace()
        _, report = replay_file(PP, MAIN, vmid=VMID, tracer=trace)
        self.assertTrue(report.ok)
        chains = trace.emitted_by('M9')
        self.assertEqual(len(chains), 10)
        outer, origin, text = chains[0]
        self.assertEqual(outer[0], '@start_of_job')
        self.assertEqual(origin, ('usr_coolant_output', lines_matching(r"'M'iCoolantM2:mcode_f", start='@usr_coolant_output')[0]))
        self.assertTrue(all('<-@' in entry for entry in outer[1:]))
        self.assertIn('@usr_coolant_output', trace.render())

    def test_cli_annotate_and_emitted_by(self):
        code, out, summary = run_cli('replay', PP, MAIN, '--vmid', VMID, '--annotate', '--emitted-by', 'G41')
        self.assertEqual(code, 0)
        self.assertIn(f"@usr_ct_toolchange:{lines_matching(r'cTCcodes', start='@usr_ct_toolchange')[0]}", out)
        self.assertEqual(summary['errors'], [])
        self.assertEqual(len(summary['emitted_by']), 1)
        self.assertEqual(summary['emitted_by'][0]['chain'][0], '@line')


class CoverageTests(unittest.TestCase):
    def test_sessions_execute_almost_the_whole_gpp(self):
        require_vmid(self)
        total = Coverage()
        program = None
        for name in SESSIONS:
            session, report = replay_file(PP, FIXTURES / f'{name}.json', vmid=VMID)
            self.assertTrue(report.ok, (name, report.errors, report.failures))
            total.merge(session.engine.coverage)
            program = session.engine.program
        summary = total.summary(program)
        self.assertEqual(summary['total'], sum(statement_kinds_from_text().values()))
        self.assertGreaterEqual(summary['percent'], 87.0)    # ZX arc math after its stop, new POST ERROR paths
        never = {name for name, count, hit, _ in summary['rows'] if count and not hit}
        # arc_zx: no session has a ZX arc since a ZX arc stops the post (5408e5c);
        # test_replay_findings.test_zx_arc_stops_the_session runs it. The unsupported events stop the post
        # (tests/test_unsupported_features.py). usr_line_homed_return: a feed move right after a post homing,
        # which only the removed subprogram session recorded (tests/test_post_homing_reposition.py runs it).
        unsupported = {'call_proc', 'proc', 'end_proc', 'loop', 'end_loop', 'change_ref_point', 'usr_unsupported_event'}
        self.assertEqual(never, {'arc_zx', 'usr_line_homed_return'} | unsupported)
        self.assertIn('Branch gaps', total.markdown(program))

    def test_coverage_file_merges_across_processes_and_ignores_mutants(self):
        """GPPL_COVERAGE_OUT: suite + one CLI process per session accumulate in one
        file, keyed by source digest (in-memory mutants are kept apart)."""
        require_vmid(self)
        with tempfile.TemporaryDirectory() as tmp:
            cov = Path(tmp) / 'cov.json'
            env = dict(os.environ, GPPL_COVERAGE_OUT=str(cov))
            env.pop('GPPL_POLICY', None)
            subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=ROOT, env=env,
                           capture_output=True, check=True)
            program = Session.from_paths(PP).engine.program
            suite = load_for(program, cov).summary(program)
            data = json.loads(cov.read_text())
            self.assertGreater(len(data['programs']), 1)                        # mutants recorded apart
            self.assertGreaterEqual(suite['percent'], 40.0)
            # A process that runs only a mutant must add nothing to the real program's coverage.
            mutant_cov = Path(tmp) / 'mutant.json'
            code = ('from pathlib import Path; from pp_tests.engine import Engine; '
                    f'src = Path({str(PP)!r}).read_text(encoding="utf-8-sig"); '
                    'Engine(src.replace("nLastPathZ = zpos", "nLastPathZ = zpos + 1", 1)).call("usr_ip_useroptions")')
            subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=dict(env, GPPL_COVERAGE_OUT=str(mutant_cov)),
                           capture_output=True, check=True)
            self.assertTrue(mutant_cov.exists())
            self.assertEqual(load_for(program, mutant_cov).summary(program)['hit'], 0)
            for name in SESSIONS:
                subprocess.run([sys.executable, '-m', 'pp_tests.gppl', 'replay', str(PP),
                                str(FIXTURES / f'{name}.json'), '--vmid', str(VMID)],
                               cwd=ROOT, env=env, capture_output=True, check=True)
            merged = load_for(program, cov).summary(program)
            self.assertGreaterEqual(merged['percent'], 93.0)
            out = Path(tmp) / 'cov.md'
            text = subprocess.run([sys.executable, '-m', 'pp_tests.gppl', 'coverage', str(PP), str(cov), str(out),
                                   '--vmid', str(VMID)], cwd=ROOT, capture_output=True, text=True, check=True).stdout
            self.assertIn(f"{merged['hit']}/{sum(statement_kinds_from_text().values())}", text)
            self.assertIn('never executed: dead under the shipped configuration', out.read_text())


class SemanticsProbeTests(unittest.TestCase):
    """The same stream under competing change-flag hypotheses. The GPP author relies
    on four behaviours: arcs print their end point, @compensation's G41 reaches the
    next move, the first tool gets M8 without M9 right after it, and no G187 (not a
    Sinumerik code) appears. Only 'clear_user' satisfies all four."""

    def probe(self, **policy):
        session, report = replay_file(PP, MAIN, vmid=VMID, **policy)
        self.assertTrue(report.ok, report.errors)
        by_index = {event.index: event for event in report.events}
        first_tool = [line.strip() for line in by_index[6].nc]
        return {'m9_after_first_m8': sum(1 for line in first_tool if line.startswith('M9')),
                'g187': any('G187' in line for line in report.nc_text.splitlines()),
                'arc_end': any('X50 Y20' in line for line in by_index[11].nc),
                'g41': any('G41' in line for line in by_index[9].nc)}

    def test_hypotheses(self):
        require_vmid(self)
        self.assertEqual(self.probe(), {'m9_after_first_m8': 7, 'g187': True, 'arc_end': True, 'g41': True})
        self.assertEqual(self.probe(change_on_equal_assign='clear'),
                         {'m9_after_first_m8': 0, 'g187': False, 'arc_end': False, 'g41': True})
        self.assertEqual(self.probe(event_flag_reset='globals_after_event'),
                         {'m9_after_first_m8': 0, 'g187': False, 'arc_end': True, 'g41': False})
        self.assertEqual(self.probe(change_on_equal_assign='clear_user'),
                         {'m9_after_first_m8': 0, 'g187': False, 'arc_end': True, 'g41': True})


if __name__ == '__main__':
    unittest.main()
