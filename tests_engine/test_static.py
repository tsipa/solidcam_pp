"""Whole-file load/validation of the real GPP (and other GPPs from the repo history)."""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from pp_tests.engine import Engine, UnsupportedGPPL, uncomment
from pp_tests.gppl.__main__ import main as cli
from pp_tests.gppl import sysvars
from pp_tests.gppl.analysis import Analysis, entry_points
from pp_tests.gppl.builtins import RESERVED_FUNCTION_NAMES
from pp_tests.gppl.policies import Policies
from pp_tests.gppl.program import SYNTAX_WORDS, load_program
from pp_tests.gppl.vmid import load_vmid, parse_vmid
from support import COMPAT, PP, SESSION, VMID, declared_global_count, first_statement_line, lines_matching, require_vmid, source, statement_kinds_from_text


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
                         (len(lines_matching(r'^@\w+')), sum(kinds.values()), declared_global_count(), 59))
        self.assertEqual(summary['statement_kinds'], kinds)
        self.assertEqual([d for d in self.diagnostics if d.severity == 'error'], [])
        self.program.validate(strict=True, policies=SESSION)
        Engine(source(), policies=SESSION.with_(load_errors='raise'))
        self.assertEqual(sum(1 for p in self.program.procedures.values() if p.error), 0)
        warnings = sorted((d.code, d.line) for d in self.diagnostics if d.severity == 'warning')
        # The only warnings were W-QUOTE-DOUBLING on the CYCLE84 ',0,''' idiom, gone with the @drill rewrite.
        self.assertEqual(warnings, [])

    def test_compat_policy_lists_exactly_what_the_legacy_engine_would_reject(self):
        errors = sorted((d.code, d.line) for d in self.program.errors(COMPAT))
        expected = sorted(lines_matching(r"'5\.0\(n\)'") + lines_matching(r'^\s*(print|trace)\b'))
        # The 24 POST ERROR prints (print + abort replaced input + abort), the index clearance Print
        # (usr_4x_index_rotate) and the trace_level trace (usr_ip_postwriteroptions); the '5.0(n)'
        # formats went with the fixture files
        self.assertEqual(len(expected), 26)
        self.assertEqual(errors, [('E-POLICY', line) for line in expected])
        format_vars = sorted(d.line for d in self.program.policy_diagnostics(COMPAT) if d.code == 'W-FORMAT-POLICY')
        # The only policy-sensitive formats were newshift_*_f = '+8.5', deleted with the dead
        # @home_data code (fixup round): none are left.
        self.assertEqual(format_vars, lines_matching(r"=\s*'\+8\.5'"))
        self.assertEqual(format_vars, [])
        with self.assertRaisesRegex(UnsupportedGPPL, 'GPP validation failed'):
            Engine(source(), policies=Policies(load_errors='raise'))

    def test_every_identifier_resolves(self):
        unknown = [str(d) for d in self.diagnostics if d.code == 'W-UNKNOWN-IDENT']
        self.assertEqual(unknown, [])
        # Every assigned name is declared, a VMID parameter or a SolidCAM variable (the IDE reports an
        # undeclared one, GPPL2007). Only SolidCAM's own formats are exempt, not every '*_f' name.
        undeclared = [str(d) for d in self.diagnostics if d.code == 'W-UNDECLARED-WRITE']
        self.assertEqual(undeclared, [])
        mutant = re.sub(r'(?im)^(\s*global\s+string\s.*?)\s+nArcAR_f\b', r'\1', source(), count=1)
        self.assertNotEqual(mutant, source())
        found = {d.message.split("'")[1] for d in Analysis(load_program(mutant), load_vmid(VMID), SESSION).run()
                 if d.code == 'W-UNDECLARED-WRITE'}
        self.assertEqual(found, {'narcar_f'})
        bare = Analysis(self.program).run()           # without the VMID its user params are unknown
        names = {d.message.split("'")[1] for d in bare if d.code == 'W-UNKNOWN-IDENT'}
        self.assertTrue({'inumber_of_fixtures', 'blimit_3axis', 'bstopm00', 'step_down'} <= names)

    def test_dead_code_and_shipped_configuration(self):
        unreachable = {d.proc for d in self.diagnostics if d.code == 'I-UNREACHABLE'}
        self.assertEqual(unreachable, set())
        config_dead_procs = {d.proc for d in self.diagnostics if d.code == 'I-CONFIG-DEAD-PROC'}
        self.assertEqual(config_dead_procs, set())       # the bSubs and trig-macro procedures are deleted
        branches = [d for d in self.diagnostics if d.code == 'I-CONFIG-DEAD']
        # Branches the shipped user options never take: 33 branches / 80 statements at 058b0e9, fewer
        # with each removal of template options for other controls (+2: the G40 before an index in
        # clearance modes 1/2, the iR1dir stop; +1 the job-parameter stop with bCycle832 off; the G04
        # spindle dwell with bSpinDwell off is gone, WAITS with bSpinWait on is live). +6 / +44: the trace
        # gate and the five CAMDBG readout gates, dead at the shipped trace_level 0 since trace_level is a
        # declared post-writer option instead of a runtime control variable. -5 statements: the four
        # option stops of usr_check_options and the job-parameter stop with bCycle832 off lost the dead
        # store 'dummy_var = 0' before their input (now a print).
        self.assertEqual(len(branches), 31)
        self.assertEqual(self.analysis.summary()['statements_dead_under_shipped_configuration'], 98)
        gates = sorted(d.line for d in branches if 'trace_level=0' in d.message)
        self.assertEqual(gates, lines_matching(r'^\s*if trace_level\s*(>|>=)\s*[05]\s*$'))
        self.assertEqual(len(gates), 6)
        # The stops on an unsupported i4xIndexMode, i4xIndexClearanceMode or i4xFeedMode are among them: they run
        # only on a wrong setting.
        guard = lines_matching(r'^\s*if i4xIndexMode ne 0 and i4xIndexMode ne 1\s*$', start='@usr_check_options')
        stop = [d for d in branches if d.proc == 'usr_check_options' and d.line == guard[0]]
        option = lines_matching(r'^\s*i4xIndexMode\s*=')[0]
        self.assertIn(f'i4xindexmode=0 (L{option})', stop[0].message)

    def test_policy_sensitive_sites(self):
        codes = {}
        for d in self.diagnostics:
            codes.setdefault(d.code, []).append(d.line)
        self.assertNotIn('W-QUOTE-DOUBLING', codes)
        integer_tonum = lines_matching(r'^\s*(iWorkoffset|macnum|iHomingmode)\s*=\s*tonum\(')
        self.assertEqual(sorted(set(codes['I-POLICY-INTEGER'])), integer_tonum)
        self.assertIn(integer_tonum[0], codes['I-POLICY-TONUM'])
        self.assertEqual(sorted(codes['I-POLICY-STMT']), lines_matching(r'^\s*(input|print|trace)\b'))

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
        # X/Y of an XY arc and Y/Z of a YZ arc print whatever their flags (usr_arc_point).
        self.assertEqual(contracts['arc']['flags'], ['feed', 'xpos', 'zpos'])

    def test_cam_interface_inventory(self):
        interface = self.analysis.interface()
        # 47 implemented or ignored events (@home_number is also a PP call target), plus the 12 motion
        # events that stop the post (usr_unsupported_motion_event).
        self.assertEqual(len(interface['entry_points']), 59)
        for name in ('tool_number', 'arc_size', 'date', 'time', 'home_user_name'):
            self.assertIn(name, interface['cam_inputs'])
        self.assertEqual(interface['cam_inputs']['inumber_of_fixtures'], 'vmid-param')
        for name in ('xpos', 'msg', 'part_name'):
            self.assertIn(name, interface['cam_inputs_modified_by_gpp'])
        self.assertNotIn('shift_y', interface['cam_inputs_modified_by_gpp'])     # PP-043
        self.assertEqual(interface['flag_inputs'], ['apos', 'bpos', 'feed', 'spin', 'xpos', 'ypos', 'zpos'])
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


def ide_keywords(grammar):
    """Identifier-like literals of the lexer rules of the reference GPPL.g4 ('Name // type N : body ;'
    lines whose body is quoted literals, alternatives separated by '|'). Read at test time, never copied."""
    words = set()
    text = Path(grammar).read_text(encoding='utf-8')
    for match in re.finditer(r'^\w+\s*//\s*type\s+\d+\s*:\s*(.*?)\s*;\s*$', text, re.M):
        for alternative in match.group(1).replace('(', ' ').replace(')', ' ').split('|'):
            pieces = re.findall(r"'((?:[^'\\]|\\.)*)'(?:/i)?|(\S+)", alternative)
            word = ''.join(literal for literal, _ in pieces).lower()
            if not any(other for _, other in pieces) and re.fullmatch(r'[a-z][a-z0-9_]*', word):
                words.add(word)
    return words


class IdeGrammarTests(unittest.TestCase):
    """The post against the GPPL IDE's grammar, its keywords and its undeclared-name check (not in the
    repository; the engine accepts forms the IDE grammar rejects, e.g. '%', a bare numeric function in an
    output block, 'if 1'). Set GPPL_IDE_REFERENCE=<dir> with GPPL.g4, raw/ (the IDE catalogs) and
    work/gppl_check.py."""

    def check(self, gpp):
        reference = Path(os.environ.get('GPPL_IDE_REFERENCE', '')).resolve()
        result = subprocess.run([sys.executable, '-I', str(reference / 'work' / 'gppl_check.py'),
                                 str(reference / 'GPPL.g4'), str(Path(gpp).resolve()), str(VMID.resolve()),
                                 str(reference / 'raw')], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def test_post_is_accepted_by_the_ide_grammar(self):
        reference = os.environ.get('GPPL_IDE_REFERENCE')
        if not reference or not (Path(reference) / 'work' / 'gppl_check.py').is_file():
            raise unittest.SkipTest('set GPPL_IDE_REFERENCE to the GPPL IDE reference directory')
        require_vmid(self)
        lines = self.check(PP)
        self.assertIn('per-line findings: 0', [line.strip() for line in lines])
        self.assertIn('whole-file rule post accepts: True', [line.strip() for line in lines])
        self.assertEqual([line for line in lines if line.startswith('SEM ')], [])
        # Self-check: the state before 690774d (trace_level never declared) gives a SEM line.
        mutant = re.sub(r'(?im)^(\s*global\s+integer\s.*?)\s+trace_level\b', r'\1', source(), count=1)
        self.assertNotEqual(mutant, source())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / PP.name
            path.write_text(mutant, encoding='utf-8')
            sem = [line for line in self.check(path) if line.startswith('SEM ')]
        self.assertEqual(len(sem), 1)
        self.assertIn("'trace_level'", sem[0])

    def test_no_variable_is_named_like_an_ide_keyword(self):
        """W-KEYWORD-NAME with the IDE grammar's keywords instead of the engine's syntax words: function
        words the engine does not implement (mod, round, int, inc, space, ...) are keywords there."""
        reference = os.environ.get('GPPL_IDE_REFERENCE')
        if not reference or not (Path(reference) / 'GPPL.g4').is_file():
            raise unittest.SkipTest('set GPPL_IDE_REFERENCE to the GPPL IDE reference directory')
        require_vmid(self)
        words = ide_keywords(Path(reference) / 'GPPL.g4')
        # The lint's default words and the function names the loader rejects are all IDE keywords.
        self.assertLessEqual(SYNTAX_WORDS | RESERVED_FUNCTION_NAMES, words)

        def found(text):
            analysis = Analysis(load_program(text), load_vmid(VMID), SESSION, keywords=words)
            return [d.message.split("'")[1] for d in analysis.run() if d.code == 'W-KEYWORD-NAME']

        self.assertEqual(found(source()), [])
        local, setting = '    local numeric nDbg1\n', '    remove_blanks = FALSE\n'
        for word, old, new in (('mod', local, '    local numeric nDbg1 mod\n'),
                               ('inc', local, local + '    local integer inc\n'),
                               ('round', setting, setting + '    round = 1\n')):
            with self.subTest(mutant=word):
                self.assertEqual(source().count(old), 1)
                self.assertEqual(found(source().replace(old, new)), [word])


class SolidCamCatalogTests(unittest.TestCase):
    """Names against SolidCAM's system-variable list (SolidCAM GPPTool Help, via the GPPL IDE catalog;
    not in the repository). Set GPPL_SOLIDCAM_CATALOG=<solidcam-system-variables.json>: a JSON object
    whose 'variables' lists {'name', 'type', ...}; only names and types are read. The procedure list is
    the sibling solidcam-system-procedures.json ('procedures' keyed '@name'); only its keys are read."""

    # SYSTEM_TYPES entries typed differently by the catalog. The enumerations are strings in the engine
    # because SolidCAM's trace prints their names (arc_plane:xy, side:comp_left); the catalog types them
    # integer (dir5a numeric). gcode/mcode: integer vs numeric; transform_type: integer vs logical;
    # angle_4x_around_x_dir, clear_change_after_gen, line_labels: catalog type 'unknown'.
    TYPE_DIVERGENCES = {'arc_direction', 'arc_plane', 'd_drill_type', 'drill_type', 'machine_plane', 'side',
                        'tool_direction', 'tool_side', 'dir5a', 'angle_4x_around_x_dir', 'gcode', 'mcode',
                        'transform_type', 'clear_change_after_gen', 'line_labels'}
    # date and time are GPPL built-in functions there; delay is this VMID's DELAY job parameter.
    NOT_IN_CATALOG = {'date', 'time', 'delay'}

    def setUp(self):
        path = os.environ.get('GPPL_SOLIDCAM_CATALOG')
        if not path or not Path(path).is_file():
            raise unittest.SkipTest('set GPPL_SOLIDCAM_CATALOG to the SolidCAM system-variable catalog JSON')
        require_vmid(self)
        variables = json.loads(Path(path).read_text(encoding='utf-8-sig'))['variables']
        self.catalog = {entry['name'].lower(): entry['type'] for entry in variables}

    def analysis(self, text):
        return Analysis(load_program(text), load_vmid(VMID), SESSION)

    def unresolved(self, text):
        """Names read or written that are not declared, VMID names or catalog variables."""
        analysis = self.analysis(text)
        known = (analysis.pp_globals | set(analysis.vmid_params) | set(analysis.vmid_constants)
                 | set(self.catalog) | {'date', 'time'})
        names = set()
        for fact in analysis.facts.values():
            used = set(fact.reads) | set(fact.flag_reads) | set(fact.writes) | set(fact.flag_writes)
            names |= used - fact.locals - fact.params - known
        return names

    def reused(self, text):
        """Post globals, locals and parameters that carry a SolidCAM variable name."""
        analysis = self.analysis(text)
        names = {(None, name) for name in analysis.pp_globals}
        for proc, fact in analysis.facts.items():
            names |= {(proc, name) for name in fact.locals | fact.params}
        return sorted((proc, name) for proc, name in names if name in self.catalog)

    def test_every_identifier_is_declared_a_vmid_name_or_a_solidcam_variable(self):
        self.assertEqual(self.unresolved(source()), set())
        # The state before 690774d: trace_level assigned and read, never declared.
        mutant = re.sub(r'(?im)^(\s*global\s+integer\s.*?)\s+trace_level\b', r'\1', source(), count=1)
        self.assertNotEqual(mutant, source())
        self.assertEqual(self.unresolved(mutant), {'trace_level'})

    def test_no_post_variable_reuses_a_solidcam_name(self):
        self.assertEqual(self.reused(source()), [])
        mutant = re.sub(r'(?m)^(\s*local\s+numeric\s.*)$', r'\1 tool_feed', source(), count=1)
        self.assertEqual([name for _, name in self.reused(mutant)], ['tool_feed'])

    def test_engine_registry_differs_from_the_catalog_only_where_pinned(self):
        types = sysvars.SYSTEM_TYPES
        self.assertEqual({name for name in types if name not in self.catalog}, self.NOT_IN_CATALOG)
        self.assertEqual({name for name in types if name in self.catalog and self.catalog[name] != types[name]},
                         self.TYPE_DIVERGENCES)
        names = set(sysvars.CONSTANTS) | sysvars.CONTROL_VARIABLES | sysvars.SYSTEM_FORMATS
        self.assertEqual(names - set(self.catalog), set())

    def undeclared_events(self, text, procedures):
        """SolidCAM procedures the post defines that the analysis does not take for entry points."""
        program = load_program(text)
        return (set(program.procedures) & procedures) - set(entry_points(program))

    def test_every_solidcam_procedure_the_post_defines_is_an_entry_point(self):
        variables = Path(os.environ['GPPL_SOLIDCAM_CATALOG'])
        path = variables.with_name(variables.name.replace('solidcam-system-variables', 'solidcam-system-procedures'))
        if path == variables or not path.is_file():
            raise unittest.SkipTest(f'no SolidCAM procedure catalog next to the variable catalog ({path.name})')
        procedures = {name.lstrip('@').lower() for name in
                      json.loads(path.read_text(encoding='utf-8-sig'))['procedures']}
        self.assertEqual((set(sysvars.EVENT_CONTRACTS) | set(sysvars.LIFECYCLE)) - procedures, set())
        # @home_number was missing from EVENT_CONTRACTS: its inputs were never reported.
        self.assertEqual(self.undeclared_events(source(), procedures), set())
        mutant = source() + '\n@stop_tool\nendp\n'
        self.assertEqual(self.undeclared_events(mutant, procedures), {'stop_tool'})


if __name__ == '__main__':
    unittest.main()


class CallArgumentSyntaxTests(unittest.TestCase):
    def test_constants_and_expressions_require_parentheses(self):
        for argument in ('1', '-1', 'x+7', '(x)+7'):
            with self.subTest(argument=argument):
                program = load_program('@main\ncall @user(' + argument + ')\nendp\n@user(integer value)\nendp')
                self.assertTrue(program.errors())

    def test_variable_reference_and_parenthesized_values_are_valid(self):
        for argument in ('x', '(1)', '(-1)', '(x+7)', '((x)+7)'):
            with self.subTest(argument=argument):
                program = load_program('@main\ncall @user(' + argument + ')\nendp\n@user(integer value)\nendp')
                self.assertFalse(program.errors())
