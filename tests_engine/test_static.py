"""Whole-file load/validation of the real GPP (and other GPPs from the repo history)."""
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from pp_tests.engine import Engine, UnsupportedGPPL, uncomment
from pp_tests.gppl.__main__ import main as cli
from pp_tests.gppl.analysis import Analysis
from pp_tests.gppl.policies import Policies
from pp_tests.gppl.program import load_program
from pp_tests.gppl.vmid import load_vmid, parse_vmid
from support import COMPAT, PP, QUOTE_DOUBLING, SESSION, VMID, declared_global_count, first_statement_line, lines_matching, require_vmid, source, statement_kinds_from_text


class WholeGppTests(unittest.TestCase):
    def setUp(self):
        require_vmid(self)
        self.program = load_program(source())
        self.analysis = Analysis(self.program, load_vmid(VMID), SESSION)
        self.diagnostics = self.analysis.run()

    def test_entire_gpp_loads_without_errors_under_the_session_policy(self):
        summary = self.analysis.summary()
        kinds = statement_kinds_from_text()
        self.assertEqual((summary['procedures'], summary['statements'], summary['globals_declared'],
                          summary['entry_points']),
                         (len(lines_matching(r'^@\w+')), sum(kinds.values()), declared_global_count(), 46))
        self.assertEqual(summary['statement_kinds'], kinds)
        self.assertEqual([d for d in self.diagnostics if d.severity == 'error'], [])
        self.program.validate(strict=True, policies=SESSION)
        Engine(source(), policies=SESSION.with_(load_errors='raise'))
        self.assertEqual(sum(1 for p in self.program.procedures.values() if p.error), 0)
        warnings = sorted((d.code, d.line) for d in self.diagnostics if d.severity == 'warning')
        self.assertEqual(warnings, [('W-QUOTE-DOUBLING', line) for line in lines_matching(QUOTE_DOUBLING)])

    def test_compat_policy_lists_exactly_what_the_legacy_engine_would_reject(self):
        errors = sorted((d.code, d.line) for d in self.program.errors(COMPAT))
        expected = sorted(lines_matching(r"'5\.0\(n\)'") + lines_matching(r'^\s*print\b'))
        self.assertEqual(len(expected), 4)                     # 3x '5.0(n)', 1x Print (usr_4x_index_rotate)
        self.assertEqual(errors, [('E-POLICY', line) for line in expected])
        format_vars = sorted(d.line for d in self.program.policy_diagnostics(COMPAT) if d.code == 'W-FORMAT-POLICY')
        self.assertEqual(format_vars, lines_matching(r"=\s*'\+8\.5'"))           # newshift_*_f = '+8.5'
        with self.assertRaisesRegex(UnsupportedGPPL, 'GPP validation failed'):
            Engine(source(), policies=Policies(load_errors='raise'))

    def test_every_identifier_resolves(self):
        unknown = [str(d) for d in self.diagnostics if d.code == 'W-UNKNOWN-IDENT']
        self.assertEqual(unknown, [])
        bare = Analysis(self.program).run()           # without the VMID its user params are unknown
        names = {d.message.split("'")[1] for d in bare if d.code == 'W-UNKNOWN-IDENT'}
        self.assertTrue({'inumber_of_fixtures', 'blimit_3axis', 'bstopm00', 'step_down'} <= names)

    def test_dead_code_and_shipped_configuration(self):
        unreachable = {d.proc for d in self.diagnostics if d.code == 'I-UNREACHABLE'}
        self.assertEqual(unreachable, set())                       # usr_heightcomp_on/off deleted (refactor)
        config_dead_procs = {d.proc for d in self.diagnostics if d.code == 'I-CONFIG-DEAD-PROC'}
        # usr_soj_subs: the bSubs branch of start_of_job (R13 moved its 22 statements there).
        self.assertEqual(config_dead_procs, {'usr_trig_macro_call', 'usr_trig_macro_output', 'usr_soj_subs'})
        branches = [d for d in self.diagnostics if d.code == 'I-CONFIG-DEAD']
        # 37 before the review fixes + the iR1posControl eq 3 block split out of 'eq 1 or eq 3' (6228b3d).
        # Dead statements 147 before the fixes: +3 that block, +2 bSubs branch (ed07c3f, review round 2),
        # +2 index mode 0 clearance Z tracking (fc664ce), +4 index mode 1 clearance Z tracking and
        # +2 trig-macro resets (review round 2). +1 branch / +2 statements: @usr_emulated_rapid_feed
        # (bSyncdrapid=false only). -1 branch / -3 statements: refactor B4 deleted the first iR1posControl
        # eq 3 block, which the second one fully overwrote. -1 branch / -2 statements: refactor B7 deleted
        # the never-taken bSkipxyrapid else branch in usr_rapid. -1 branch / -3 statements: round 2 split
        # usr_rapid into stages; the two head-homing copies became usr_head_home and the motion-mode
        # if/else lost its nested job_type test. -1 statement: R2 deleted the dead bSkipxyrapid writes
        # (one in the bSubs branch, hence 22 statements there). -1 branch / -5 statements: R4 moved the
        # duplicated safety block (its dead bNnumtc branch) and the M5 copies into helpers. +3 branches /
        # -35 statements: R5 folded the six index copies (modes 0/1 x clearance 0/1/2) into one
        # usr_4x_index_rotate with smaller per-clearance branches. -21 statements: R13 moved the bSubs
        # branch body into usr_soj_subs (a dead procedure; its statements are not counted here).
        # -3 branches / -5 statements: the fixup round moved the "homing string not ''" test into
        # usr_prep_home_axis; the call-site tests of sHomestrstpsame/stpdiff/endsub ('' as shipped) were
        # dead branches, and the trig-macro index homing gained its 'sHomestr = sHomestrrot' (+1).
        # -1 statement: the always-true 'if !bSubs' in the dead bCoolspinaftertc branch of usr_ct_after.
        self.assertEqual(len(branches), 35)
        self.assertEqual(self.analysis.summary()['statements_dead_under_shipped_configuration'], 86)
        subs_line = lines_matching(r'^\s*if bSubs\s*$', start='@start_of_job')
        subs = [d for d in branches if d.proc == 'start_of_job' and d.line == subs_line[0]]
        option = lines_matching(r'^\s*bSubs\s*=')[0]
        self.assertIn(f'bsubs=False (L{option})', subs[0].message)
        self.assertIn('1 statement(s)', subs[0].message)         # call @usr_soj_subs
        # The dead bSubs code itself: + reposition handling (ed07c3f, review round 2).
        self.assertEqual(len(list(self.program.procedures['usr_soj_subs'].statements())), 22)

    def test_policy_sensitive_sites(self):
        codes = {}
        for d in self.diagnostics:
            codes.setdefault(d.code, []).append(d.line)
        self.assertEqual(codes['W-QUOTE-DOUBLING'], lines_matching(QUOTE_DOUBLING))
        integer_tonum = lines_matching(r'^\s*(iWorkoffset|macnum)\s*=\s*tonum\(')
        self.assertEqual(sorted(set(codes['I-POLICY-INTEGER'])), integer_tonum)
        self.assertIn(integer_tonum[0], codes['I-POLICY-TONUM'])
        self.assertEqual(sorted(codes['I-POLICY-STMT']), lines_matching(r'^\s*(input|print)\b'))

    def test_event_contracts_include_change_flags(self):
        contracts = self.analysis.event_contracts()
        self.assertEqual(set(contracts['start_of_file']['inferred']) & {'part_name', 'date', 'time'},
                         {'part_name', 'date', 'time'})
        self.assertEqual(contracts['start_of_file']['inferred']['inumber_of_fixtures'], 'vmid-param')
        # gcode is assigned only inside 'if drill_type eq G8x' branches: definite-assignment
        # analysis reports it as an input of @drill.
        self.assertEqual(contracts['drill']['inferred']['gcode'], 'system')
        self.assertNotIn('rtp', contracts['drill']['inferred'])            # locals never count
        self.assertNotIn('xpos', contracts['change_tool']['inferred'])
        self.assertIn('stock_x', contracts['def_tool']['persisted_from_earlier_events'])
        self.assertEqual(contracts['move_4x']['flags'], ['xpos', 'ypos', 'zpos'])
        self.assertEqual(contracts['arc']['flags'], ['feed', 'xpos', 'ypos', 'zpos'])

    def test_cam_interface_inventory(self):
        interface = self.analysis.interface()
        self.assertEqual(len(interface['entry_points']), 46)
        for name in ('tool_number', 'arc_size', 'date', 'time', 'home_user_name'):
            self.assertIn(name, interface['cam_inputs'])
        self.assertEqual(interface['cam_inputs']['inumber_of_fixtures'], 'vmid-param')
        for name in ('xpos', 'spin', 'shift_y', 'msg', 'part_name'):
            self.assertIn(name, interface['cam_inputs_modified_by_gpp'])
        self.assertEqual(interface['flag_inputs'], ['apos', 'bpos', 'feed', 'message', 'spin', 'xpos', 'ypos', 'zpos'])
        for name in ('clear_change_after_gen', 'skipline', 'numeric_def_f', 'blknum_exist'):
            self.assertIn(name, interface['runtime_switches_written_never_read'])

    def test_vmid_runtime_inputs(self):
        vmid = load_vmid(VMID)
        self.assertEqual(vmid.machine_params['inumber_of_fixtures'].vtype, 'integer')
        self.assertIs(vmid.job_params['bstopm00'].value, False)
        self.assertEqual(sorted(vmid.drill_cycles), ['G81', 'G82', 'G83', 'G84', 'G86'])
        self.assertEqual(sorted(vmid.drill_cycles['G84']), ['step_down', 'varretract'])
        with self.assertRaises(ValueError):
            parse_vmid('<!DOCTYPE x [<!ENTITY a "b">]><Machine/>')

    def test_broken_statements_are_reported_up_front_and_raised_lazily(self):
        program = load_program('@ok\nx = 1\nendp\n@bad\nexec something\nif (\nendif\nendp')
        codes = sorted((d.code, d.line) for d in program.diagnostics)
        self.assertEqual(codes, [('E-SYNTAX', 5), ('E-SYNTAX', 6)])
        Engine('@ok\nx = 1\nendp\n@bad\nexec something\nendp').call('ok')    # unexecuted: allowed
        with self.assertRaises(UnsupportedGPPL):
            program.validate(strict=True)

    def test_cli_validate_contracts_interface(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli(['validate', str(PP), '--vmid', str(VMID), '--strict', '--json']), 0)
        self.assertEqual(json.loads(out.getvalue())['summary']['statements'], sum(statement_kinds_from_text().values()))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli(['validate', str(PP), '--vmid', str(VMID), '--strict', '--policy', 'compat']), 1)
        for command in ('contracts', 'interface'):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cli([command, str(PP), '--vmid', str(VMID)]), 0)
            self.assertTrue(json.loads(out.getvalue()))

    def test_legacy_helpers_kept(self):
        engine = Engine.from_path(PP)
        self.assertEqual(engine.procedures['tmatrix'][0], (first_statement_line('tmatrix'), 'bIndexClearancePending = true'))
        self.assertEqual(engine.arguments['usr_arc_check'], ['dx', 'dy', 'dz'])
        self.assertEqual(uncomment("x = 'a;b' ; c"), "x = 'a;b'")


class CorpusTests(unittest.TestCase):
    """Other GPPs from the repository history (extract with `git show`, then set
    GPPL_CORPUS=<dir>): active(), trace, input in @init_post, '7.0(*1000P)', 'not'."""

    def test_corpus_parses(self):
        corpus = os.environ.get('GPPL_CORPUS')
        if not corpus or not Path(corpus).is_dir():
            raise unittest.SkipTest('set GPPL_CORPUS to a directory of .gpp files')
        files = sorted(Path(corpus).glob('*.gpp'))
        self.assertTrue(files)
        for path in files:
            with self.subTest(gpp=path.name):
                program = load_program(path.read_text(encoding='utf-8-sig', errors='replace'))
                errors = [str(d) for d in program.errors(SESSION)]
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
