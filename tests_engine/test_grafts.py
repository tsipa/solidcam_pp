"""Behaviour grafted from the runner-up designs and the judges' findings:
recursion hardening, strict loading, rollback switch, no shared mutable state,
legacy-equal defaults where the session-emulator prototype silently differed,
lexer strictness, coverage keyed by source digest, call tracing."""
import dataclasses
import os
import re
import subprocess
import sys
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from pp_tests.gppl import legacy
from pp_tests.gppl import nodes as N
from pp_tests.gppl.calltrace import CallTrace
from pp_tests.gppl.coverage import Coverage, CoverageStore
from pp_tests.gppl.errors import GPPLSyntaxError
from pp_tests.gppl.policies import Policies
from pp_tests.gppl.program import load_program
from support import PP, ROOT, SESSION, first_statement_line, source


def nested_ifs(depth):
    return '@t\nx = 0\n' + 'if true\n' * depth + 'x = 1\n' + 'endif\n' * depth + 'endp'


class RecursionHardeningTests(unittest.TestCase):
    def test_deep_block_nesting_runs_without_python_recursion(self):
        engine = Engine(nested_ifs(600))
        engine.call('t')
        self.assertEqual(engine.state['x'], 1)
        legacy_engine = legacy.Engine(nested_ifs(600))
        legacy_engine.call('t')
        self.assertEqual(legacy_engine.state['x'], 1)

    def test_full_call_depth_inside_nested_blocks(self):
        """62 nested calls, each inside 12 ifs and a while: the 64-call limit is the
        only depth limit (the parser-first and incremental prototypes hit Python's)."""
        body = 'if true\n' * 12 + 'i = 0\nwhile i < 1\ni = i + 1\nif n gt 0\ncall @r(n - 1)\nendif\nendw\n' + 'endif\n' * 12
        src = '@r(numeric n)\nlocal numeric i\n' + body + 'hits = hits + 1\nendp'
        engine = Engine(src)
        engine.set(hits=0)
        engine.call('r', [61])
        self.assertEqual(engine.state['hits'], 62)
        with self.assertRaisesRegex(UnsupportedGPPL, 'call depth exceeded'):
            Engine(src).call('r', [70])

    def test_pathological_expressions_are_located_syntax_errors(self):
        cases = {'parens': '(' * 150 + '1' + ')' * 150, 'sum': ' + '.join(['1'] * 3000),
                 'unary': '-' * 1500 + '1', 'not': 'not ' * 500 + 'true'}
        for name, text in cases.items():
            with self.subTest(case=name):
                with self.assertRaisesRegex(GPPLSyntaxError, 'nested deeper than 100 levels'):
                    Engine('').expression(text)
                src = f'@ok\ny = 1\nendp\n@never\nx = {text}\nendp'
                engine = Engine(src)                                  # a never-called procedure cannot block load
                engine.call('ok')
                self.assertEqual([(d.code, d.line) for d in engine.diagnostics], [('E-SYNTAX', 5)])
                with self.assertRaisesRegex(UnsupportedGPPL, 'nested deeper'):
                    engine.call('never')
        self.assertEqual(Engine('').expression(' + '.join(['1'] * 99)), 99)
        self.assertEqual(Engine('', policies=Policies(max_expr_depth=400)).expression('(' * 150 + '1' + ')' * 150), 1)

    def test_deep_modal_nesting_in_output(self):
        src = '@t\n{' + '[' * 400 + "'X'x" + ']' * 400 + '}\nendp'
        engine = Engine(src)
        self.assertEqual([d.code for d in engine.diagnostics], ['E-SYNTAX'])


class StrictLoadTests(unittest.TestCase):
    STRICT = Policies(load_errors='raise')

    def test_strict_load_rejects_every_static_error(self):
        cases = {'missing procedure': '@t\nif false\ncall @nope\nendif\nendp',
                 'arity': '@t\ncall @u(1, 2)\nendp\n@u(numeric a)\nendp',
                 'syntax in dead code': '@t\nif false\nx = 0x10\nendif\nendp',
                 'structure': '@t\nwhile true\nendp',
                 'outside code': '@t\nendp\nx = 1',
                 'missing endp': '@a\nx = 1\n@t\nendp',
                 'policy-rejected construct': "@t\nif false\nPrint 'x'\nendif\nendp"}
        for name, src in cases.items():
            with self.subTest(case=name):
                Engine(src)                                           # lazy default: loads
                with self.assertRaisesRegex(UnsupportedGPPL, 'GPP validation failed'):
                    Engine(src, policies=self.STRICT)
        Engine("@t\nif false\nPrint 'x'\nendif\nendp", policies=SESSION.with_(load_errors='raise'))


class LegacyEqualDefaultsTests(unittest.TestCase):
    """Defaults where the session-emulator prototype silently differed from legacy."""

    def test_format_extensions_are_rejected_under_compat(self):
        for fmt in ('+8.5', '5.0(n)', '5.3()', ' 5.3', '5.3 '):
            with self.subTest(fmt=fmt):
                for engine_class in (legacy.Engine, Engine):
                    engine = engine_class("@t\n{x:f}\nendp")
                    engine.set(x=3.5, f=fmt)
                    with self.assertRaisesRegex(Exception, 'unsupported numeric format'):
                        engine.call('t')

    def test_format_on_a_string_value_is_accepted_like_legacy(self):
        for engine_class in (legacy.Engine, Engine):
            engine = engine_class("@t\n{'abc':'5.3'}\nendp")
            engine.call('t')
            self.assertEqual(engine.output, ['abc'])

    def test_trace_and_print_and_ne_operator(self):
        for src in ("@t\ntrace \"all\":5\nendp", "@t\nPrint 'x'\nendp"):
            with self.subTest(src=src):
                with self.assertRaisesRegex(legacy.UnsupportedGPPL, 'unsupported statement'):
                    legacy.Engine(src).call('t')
                with self.assertRaisesRegex(UnsupportedGPPL, 'unsupported statement'):
                    Engine(src).call('t')
        with self.assertRaises(UnsupportedGPPL):
            Engine('').expression('1 <> 2')

    def test_global_declaration_under_a_local_does_not_leak(self):
        cases = [('@a(numeric v)\nglobal numeric v\nendp', [5]),
                 ('@a\nlocal numeric v\nglobal numeric v\nendp', []),
                 ('@a\nlocal numeric v\ncall @b\nendp\n@b\nglobal numeric v\nendp', [])]
        for src, args in cases:
            with self.subTest(src=src):
                old, new = legacy.Engine(src), Engine(src)
                old.call('a', args)
                new.call('a', args)
                self.assertEqual(new.state, old.state)
                self.assertEqual(new.state, {})

    def test_if_and_while_without_space_report_clearly(self):
        for src, message in (('@t\nif(x)\ny = 1\nendif\nendp', "'if(' needs a space"),
                             ('@t\nwhile(x)\nendw\nendp', "'while(' needs a space"),
                             ('@t\ncall@u\nendp\n@u\nendp', "write 'call @name"),
                             ('@t\ncall @u (1)\nendp\n@u(numeric a)\nendp', "no space before '('")):
            with self.subTest(src=src):
                engine = Engine(src)
                self.assertNotIn('E-STRUCT', [d.code for d in engine.diagnostics])   # blocks still match
                with self.assertRaisesRegex(UnsupportedGPPL, re.escape(message)):
                    engine.call('t')
        with self.assertRaisesRegex(UnsupportedGPPL, 'invalid procedure at line 1'):
            Engine('@test (numeric a)\nendp')                                         # legacy: fatal

    def test_ascii_only_numbers_and_identifiers(self):
        for text in ('٣', '٣ + 1', 'xé', '1٣'):
            with self.subTest(text=text), self.assertRaises(UnsupportedGPPL):
                Engine('').expression(text)

    def test_tonum_returns_float_like_legacy(self):
        for text in ('tonum(1)', "tonum('7')", 'tonum(true)'):
            with self.subTest(text=text):
                self.assertEqual(repr(Engine('').expression(text)), repr(legacy.Engine('').expression(text)))


class SharedStateTests(unittest.TestCase):
    def test_engines_from_one_source_share_only_immutable_ir(self):
        a, b = Engine.from_path(PP), Engine.from_path(PP)
        self.assertIs(a.program, b.program)
        del a.procedures['tmatrix']
        a.procedures['usr_arc'].clear()
        self.assertIn('tmatrix', b.procedures)
        self.assertTrue(b.procedures['usr_arc'])
        a.diagnostics.append('junk')
        self.assertNotIn('junk', b.diagnostics)
        b.call('tmatrix')                                             # execution uses the IR, not the view

    def test_ir_nodes_are_frozen(self):
        program = load_program(source())
        stmt = program.procedures['tmatrix'].body[0]
        self.assertIsInstance(stmt, N.Assign)
        self.assertEqual((stmt.span.line, stmt.target), (first_statement_line('tmatrix'), 'bindexclearancepending'))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            stmt.target = 'x'
        self.assertIsInstance(program.procedures['tmatrix'].code[0], N.Instr)

    def test_rollback_switch_selects_the_legacy_engine(self):
        code = 'import pp_tests.engine as e; print(e.Engine.__module__)'
        for value, module in (('legacy', 'pp_tests.gppl.legacy'), ('', 'pp_tests.gppl.runtime')):
            env = dict(os.environ, GPPL_ENGINE=value)
            out = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(out.stdout.strip(), module, out.stderr)


class CoverageAndTraceTests(unittest.TestCase):
    def test_coverage_store_keys_by_source_digest(self):
        store = CoverageStore()
        real = load_program(source())
        mutant = load_program(source().replace('nR1pos5x = (-apos) * iR1dir', 'nR1pos5x = (apos) * iR1dir', 1))
        self.assertIsNot(store.for_program(real), store.for_program(mutant))
        self.assertIs(store.for_program(real), store.for_program(load_program(source())))

    def test_statement_and_branch_counting(self):
        coverage = Coverage()
        engine = Engine('@t\nif x\ny = 1\nelse\ny = 2\nendif\nendp', coverage=coverage)
        engine.set(x=True)
        engine.call('t')
        self.assertEqual(coverage.lines['t'], {2, 3})
        self.assertEqual(coverage.branches[('t', 2)], {True})
        summary = coverage.summary(engine.program)
        self.assertEqual((summary['hit'], summary['total'], summary['branch_outcomes_seen']), (2, 3, 1))

    def test_calltrace_records_calls_outputs_and_assignments(self):
        trace = CallTrace(record_assignments=True)
        engine = Engine("@a\ncall @b(2)\nendp\n@b(numeric n)\nx = n\n{'G75 X'x}\nendp", tracer=trace)
        engine.call('a')
        self.assertEqual(trace.calls(), ['a', 'b'])
        self.assertEqual(trace.emitted_by('G75'), [(['@a', '@b<-@a:2'], ('b', 6), 'G75 X2')])
        self.assertIn('L5 x = 2', trace.render())


if __name__ == '__main__':
    unittest.main()
