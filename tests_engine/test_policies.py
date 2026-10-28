"""Every semantics policy is observable, validated, and its default equals the
legacy behaviour (or, for string_index, a loud error instead of a Python
artefact)."""
import os
import subprocess
import sys
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from pp_tests.gppl import legacy
from pp_tests.gppl.errors import MissingInput, PostAbort, PostprocessorStopped
from pp_tests.gppl.policies import CHOICES, LEGACY_VALUES, PRESETS, Policies
from support import PP, ROOT


def engine(src, **policy):
    return Engine(src, policies=Policies(**policy))


class PolicyTests(unittest.TestCase):
    def test_choices_are_validated_and_default_first(self):
        with self.assertRaises(ValueError):
            Policies(tonum='lenient')
        with self.assertRaises(ValueError):
            Policies(max_steps=-1)
        for name, allowed in CHOICES.items():
            self.assertEqual(getattr(Policies(), name), allowed[0], name)
        self.assertEqual(LEGACY_VALUES, {'string_index': 'python'})          # the only non-legacy default

    def test_gppl_policy_environment_syntax(self):
        self.assertEqual(Policies.from_env(''), Policies())
        self.assertEqual(Policies.from_env('session,tonum=atof,max_steps=5'),
                         Policies.session(tonum='atof', max_steps=5))
        self.assertEqual(Policies.from_env('tonum=atof', base='session'), Policies.session(tonum='atof'))
        self.assertEqual(Policies.from_env('best_guess'), Policies.best_guess())
        for bad in ('nope', 'session,nope=1', 'session,tonum=lenient', 'session,tonum'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Policies.from_env(bad)

    def test_gppl_policy_reaches_engines_created_by_unchanged_tests(self):
        code = ('from pp_tests.engine import Engine; e = Engine(""); '
                'print(e.policies.tonum, e.policies.format_grammar)')
        env = dict(os.environ, GPPL_POLICY='session,tonum=atof')
        out = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(out.stdout.split(), ['atof', 'extended'], out.stderr)

    def test_presets(self):
        session = Policies.session()
        self.assertEqual(session.differences(), {
            'declared_flag': 'false', 'constants': 'registry', 'typed_default_formats': 'on',
            'logical_default': 'false', 'format_grammar': 'extended', 'print_stmt': 'console',
            'trace_stmt': 'ignore'})
        guess = Policies.best_guess()
        self.assertEqual(set(guess.differences(session)), {'tonum', 'input_stmt', 'change_on_equal_assign',
                                                           'quote_escape', 'string_escapes', 'string_index'})
        self.assertEqual(set(PRESETS), {'compat', 'session', 'best_guess'})

    def test_integer_assignment(self):
        src = '@t\nglobal integer i\ni = 2.7\nj = -2.5\nendp'
        for policy, expected in (('keep', 2.7), ('truncate', 2), ('round_half_away', 3)):
            e = engine(src, integer_assign=policy)
            e.call('t')
            with self.subTest(policy=policy):
                self.assertEqual(e.state['i'], expected)
                self.assertEqual(e.state['j'], -2.5)          # undeclared: not integer-typed

    def test_typed_assignment(self):
        e = engine("@t\nglobal string s\ns = 5\nendp", typed_assign='coerce')
        with self.assertRaisesRegex(UnsupportedGPPL, 'non-string'):
            e.call('t')
        e = engine("@t\nglobal logical b\nb = 2\nendp", typed_assign='coerce')
        e.call('t')
        self.assertIs(e.state['b'], True)

    def test_change_on_equal_assignment(self):
        src = '@t\nx = 1\nendp'
        for policy, flag in {'keep': True, 'clear': False, 'set': True}.items():
            e = engine(src, change_on_equal_assign=policy)
            e.set(x=1)
            e.changed['x'] = True
            e.call('t')
            with self.subTest(policy=policy):
                self.assertIs(e.changed['x'], flag)
        e = engine('@t\nx = 1\nxpos = 5\nendp', change_on_equal_assign='clear_user')
        e.set(x=1, xpos=5)
        e.changed.update(x=True, xpos=True)
        e.call('t')
        self.assertEqual((e.changed['x'], e.changed['xpos']), (False, True))   # user vs SolidCAM variable

    def test_declared_flag_and_missing_flag(self):
        src = '@t\nglobal numeric n\nn = 0\ny = change(n)\nendp'
        with self.assertRaisesRegex(MissingInput, r'change\(n\) was not supplied'):
            engine(src).call('t')
        e = engine(src, declared_flag='false')
        e.call('t')
        self.assertIs(e.state['y'], False)
        e = engine('@t\ny = change(q)\nendp', missing_change_flag='false')
        e.call('t')
        self.assertIs(e.state['y'], False)

    def test_modal_missing_flag(self):
        src = "@t\n{['X'x]}\nendp"
        e = engine(src)
        e.set(x=1)
        with self.assertRaisesRegex(UnsupportedGPPL, 'modal output requires explicit change flags'):
            e.call('t')
        e = engine(src, modal_missing_flag='unchanged')
        e.set(x=1)
        e.call('t')
        self.assertEqual(e.output, [''])

    def test_substr_start_lies_inside_the_string(self):
        # GPPTool Help (via the GPPL IDE catalog): 1 <= start <= strlen; the legacy engine sliced.
        self.assertEqual(engine('').expression("substr('abc', 3, 5)"), 'c')
        for text in ("substr('abc', 4, 1)", "substr('', 1, 0)"):
            with self.subTest(text=text), self.assertRaisesRegex(UnsupportedGPPL, 'string_index'):
                engine('').expression(text)
        for policy in ('python', 'clamp'):
            self.assertEqual(engine('', string_index=policy).expression("substr('abc', 4, 1)"), '')
        self.assertEqual(legacy.Engine('').expression("substr('abc', 4, 1)"), '')

    def test_string_and_mixed_comparison(self):
        self.assertFalse(engine('').expression("'CW' eq 'cw'"))
        self.assertTrue(engine('', string_compare='case_insensitive').expression("'CW' eq 'cw'"))
        self.assertFalse(engine('').expression("'a' eq 1"))
        self.assertEqual(legacy.Engine('').expression("'a' eq 1"), False)
        with self.assertRaises(UnsupportedGPPL):
            engine('', mixed_compare='error').expression("'a' eq 1")
        with self.assertRaises(UnsupportedGPPL):
            engine('').expression("'a' lt 1")

    def test_tonum(self):
        with self.assertRaises(UnsupportedGPPL):
            engine('').expression("tonum('G5')")
        e = engine('', tonum='atof')
        self.assertEqual((e.expression("tonum('G5')"), e.expression("tonum('12abc')"), e.expression("tonum('')")),
                         (0, 12.0, 0))

    def test_modulo(self):
        self.assertEqual(engine('').expression('0 - 7 % 3'), 0 - 7 % 3)
        self.assertEqual(engine('').expression('(0 - 7) % 3'), legacy.Engine('').expression('(0 - 7) % 3'))
        self.assertEqual(engine('', modulo='truncate').expression('(0 - 7) % 3'), -1)
        self.assertEqual(engine('', modulo='truncate').expression('7.5 % 2'), 1.5)
        with self.assertRaisesRegex(UnsupportedGPPL, 'division by zero'):
            engine('', modulo='truncate').expression('1 % 0')

    def test_constants(self):
        with self.assertRaises(MissingInput):
            engine('').expression('CW')                        # legacy: strict, must be supplied
        self.assertEqual(engine('', constants='registry').expression('CW'), 'cw')
        self.assertEqual(engine('', constants='registry').expression('COMP_LEFT'), 'comp_left')
        e = engine('', constants='registry')
        e.set(cw='clockwise')                                  # supplied value wins over constant
        self.assertEqual(e.expression('cw'), 'clockwise')

    def test_local_scoping(self):
        src = '@a\nlocal numeric v\nv = 3\ncall @b\nendp\n@b\nr = v\nendp'
        e = engine(src)
        e.call('a')
        self.assertEqual(e.state['r'], 3)                      # legacy: callee sees caller locals
        with self.assertRaises(MissingInput):
            engine(src, local_scoping='lexical').call('a')

    def test_undeclared_assignment(self):
        engine('@t\nresult = 1\nendp').call('t')
        with self.assertRaisesRegex(UnsupportedGPPL, 'undeclared'):
            engine('@t\nresult = 1\nendp', undeclared_assign='error').call('t')
        engine('@t\nglobal numeric result\nresult = 1\nxpos = 2\nendp', undeclared_assign='error').call('t')

    def test_logical_default_and_output(self):
        e = engine('@t\nglobal logical b\n{b}\nendp')
        e.call('t')
        self.assertEqual((e.state['b'], e.output), (0, ['0']))          # legacy: logical declared as 0
        e = engine('@t\nglobal logical b\n{b}\nendp', logical_default='false')
        e.call('t')
        self.assertEqual((e.state['b'], e.output), (False, ['False']))
        e = engine('@t\nglobal logical b\n{b}\nendp', logical_default='false', logical_output='numeric')
        e.call('t')
        self.assertEqual(e.output, ['0'])

    def test_quote_and_backslash_escapes(self):
        src = "@t\nx = 'can''t'\ny = 'a\\nb'\nendp"
        e = engine(src)
        e.call('t')
        self.assertEqual((e.state['x'], e.state['y']), ("can't", 'a\\nb'))
        with self.assertRaises(UnsupportedGPPL):                 # 'can' 't' : adjacent literals
            engine(src, quote_escape='none', string_escapes='c').call('t')
        e = engine("@t\ny = 'a\\r\\nb'\nendp", quote_escape='none', string_escapes='c')
        e.call('t')
        self.assertEqual(e.state['y'], 'a\r\nb')

    def test_print_trace_and_input_statements(self):
        src = "@t\nPrint 'hello ', x\ntrace \"all\":5\nendp"
        with self.assertRaisesRegex(UnsupportedGPPL, 'print_stmt=error'):
            engine(src).call('t')
        self.assertIn('unsupported statement', str(_legacy_error(src)))   # compat == legacy
        e = engine(src, print_stmt='console', trace_stmt='ignore')
        e.set(x=5)
        e.call('t')
        self.assertEqual((e.console, e.output), ([('print', 'hello 5')], []))
        e = engine(src, print_stmt='console')
        e.set(x=5)
        with self.assertRaisesRegex(UnsupportedGPPL, 'trace_stmt=error'):
            e.call('t')
        src = "@t\nlocal numeric v\ninput 'Value?' v\nr = v\n{'POST ERROR v=', v}\nabort\nendp"
        with self.assertRaisesRegex(PostprocessorStopped, 'postprocessor stopped: input'):
            engine(src).call('t')
        e = engine(src, input_stmt='scripted')
        e.scripted_inputs.append(4)
        with self.assertRaisesRegex(PostAbort, "postprocessor stopped: abort .*POST ERROR v=4"):
            e.call('t')
        self.assertEqual((e.state['r'], e.console), (4, [('input', 'Value?')]))

    def test_format_grammar(self):
        src = "@t\n{'X'x:'+8.5', ' T'tostr(n:'5.0(n)'), ' A'x:'<(>5.3<)>', ' P'd:'7.0(*1000P)'}\nendp"
        e = engine(src)
        e.set(x=5, n=2001, d=0.25)
        with self.assertRaisesRegex(UnsupportedGPPL, r"unsupported numeric format: \+8\.5 \(accepted under"):
            e.call('t')
        self.assertEqual(len([d for d in e.diagnostics if d.code == 'E-POLICY']), 4)
        e = engine(src, format_grammar='extended')
        e.set(x=5, n=2001, d=0.25)
        e.call('t')
        self.assertEqual(e.output, ['X+5 T2001 A(5) P250'])
        e = engine("@t\n{'abc':'zz', s:'5.3'}\nendp")             # formats apply to numbers only (legacy)
        e.set(s='text')
        e.call('t')
        self.assertEqual(e.output, ['abctext'])

    def test_real_arc_mismatch_under_scripted_input_writes_the_error_then_aborts(self):
        e = Engine.from_path(PP, policies=Policies(input_stmt='scripted'))
        with self.assertRaisesRegex(PostAbort, 'ARC end mismatch') as caught:
            e.call('usr_arc_check', [0.002, 0, 0])
        self.assertIn('POST ERROR: ARC end mismatch. tolerance=0.001 dX=0.002', e.nc_lines()[-1])
        self.assertEqual(caught.exception.gppl_stack[0][0], 'usr_arc_check')

    def test_step_depth_and_load_limits(self):
        with self.assertRaisesRegex(UnsupportedGPPL, 'step limit'):
            engine('@t\nwhile true\nx = 1\nendw\nendp', max_steps=50).call('t')
        with self.assertRaisesRegex(UnsupportedGPPL, 'depth'):
            engine('@t\ncall @t\nendp', max_depth=5).call('t')
        with self.assertRaisesRegex(UnsupportedGPPL, 'call to undefined procedure @nope'):
            engine('@t\nif false\ncall @nope\nendif\nendp', load_errors='raise')
        with self.assertRaisesRegex(UnsupportedGPPL, 'takes 1 argument'):
            engine('@t\ncall @u\nendp\n@u(numeric a)\nendp', load_errors='raise')
        engine('@t\nif false\ncall @nope\nendif\nendp').call('t')          # lazy (default): runs


def _legacy_error(src):
    try:
        legacy.Engine(src).call('t')
    except Exception as exc:                    # noqa: BLE001
        return exc
    return None


if __name__ == '__main__':
    unittest.main()
