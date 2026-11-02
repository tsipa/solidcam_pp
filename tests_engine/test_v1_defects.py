"""One test per defect of the original engine that the GPPL engine fixed.

Each test checks the fixed behaviour of the GPPL engine. Each also reproduced
the defect on the original engine until that engine (pp_tests/gppl/legacy.py)
was removed; the docstrings and comments record what it did.
"""
import unittest

from pp_tests.engine import Engine, UnsupportedGPPL
from pp_tests.gppl.policies import Policies
from pp_tests.gppl.session import Session
from support import PP, SESSION, VMID, require_vmid, source


def run(src, policies=None, **state):
    engine = Engine(src, policies=policies)
    engine.set(**state)
    engine.call('t')
    return engine


class V1DefectTests(unittest.TestCase):
    def test_leading_zero_integer_literal(self):
        """The GPP has 'iCoolantM5ON = 07' (through-coolant 30 bar)."""
        self.assertEqual(run('@t\nx = 07\nendp').state['x'], 7)
        self.assertIn('iCoolantM5ON = 07', source())

    def test_python_only_syntax_is_rejected(self):
        """The original engine evaluated these with Python: 16, 1000, 2j, True, 'abab', 'ab', '5!'."""
        for text in ('0x10', '1_000', '2j', '1 < 2 < 3', "'ab' * 2", "'a' 'b'", "'%s!' % 5"):
            with self.subTest(text=text), self.assertRaises(UnsupportedGPPL):
                Engine('').expression(text)
        # The reason, which the golden fixture does not keep for its 15 string repetitions.
        for text in ("'ab' * 2", "2 * 'ab'"):
            with self.subTest(text=text), self.assertRaisesRegex(UnsupportedGPPL, r"arithmetic '\*' on non-numbers"):
                Engine('').expression(text)
        for text in ('2 ** 3', '[1]', '1 if 1 else 2', 'lambda: 1', '٣', '1 <> 2'):
            with self.subTest(text=text), self.assertRaises(UnsupportedGPPL):
                Engine('').expression(text)
        self.assertEqual(Engine('').expression('1e3'), 1000.0)          # the original engine accepted it: kept

    def test_python_keywords_are_valid_gppl_identifiers(self):
        """The original engine parsed with Python, so 'in + 1' was an error."""
        engine = Engine('@t\nfrom = 2\nclass = from * 3\nendp')
        engine.set(**{'in': 1})
        self.assertEqual(engine.expression('in + 1'), 2)
        engine.call('t')
        self.assertEqual(engine.state['class'], 6)

    def test_negative_string_indexes_no_longer_wrap(self):
        """The original engine used Python slicing: left('abc',-1)='ab', substr(s,0,3)=''
        and substr('2026',1,0-1)='202' (reachable from @usr_US_date)."""
        for text in ("left('abc', -1)", "substr('abcdef', 0, 3)", "substr('2026', 1, 0-1)", "right('abc', -2)"):
            with self.subTest(text=text), self.assertRaisesRegex(UnsupportedGPPL, 'string_index'):
                Engine('').expression(text)
        python = Engine('', policies=Policies(string_index='python'))
        self.assertEqual(python.expression("left('abc', -1)"), 'ab')         # the original engine's value, opt-in
        clamp = Engine('', policies=Policies(string_index='clamp'))
        self.assertEqual((clamp.expression("left('abc', -1)"), clamp.expression("substr('abcdef', 0, 3)")),
                         ('', 'ab'))

    def test_tonum_does_not_accept_python_float_spellings(self):
        """The original engine's tonum was Python's float(): it accepted these and returned a float."""
        for text in ("tonum('nan')", "tonum('1_000')", "tonum('infinity')"):
            with self.subTest(text=text):
                with self.assertRaises(UnsupportedGPPL):
                    Engine('').expression(text)
        engine = Engine('')
        self.assertEqual(engine.expression("tonum(' 12.5 ')"), 12.5)
        self.assertEqual(repr(engine.expression('tonum(1)')), '1.0')

    def test_no_raw_python_exceptions(self):
        """The original engine raised ZeroDivisionError, AttributeError, TypeError and a non-GPPL
        error for a bad parameter list."""
        for text in ('1/0', "tonum('G5')", "instr(5, 'x')", 'strlen(3)', "-'a'"):
            with self.subTest(text=text), self.assertRaises(UnsupportedGPPL):
                Engine('').expression(text)
        with self.assertRaises(UnsupportedGPPL):
            run("@t\nx = instr(5, 'x')\nendp")
        with self.assertRaisesRegex(UnsupportedGPPL, 'format must be a string'):
            run('@t\n{x:f}\nendp', x=1, f=3)
        with self.assertRaisesRegex(UnsupportedGPPL, 'parameter must be'):
            Engine('@f(numeric)\nendp')

    def test_modal_groups_track_real_variables_only(self):
        """The original engine counted function names and identifiers inside string literals as
        modal-group variables ({['X'(abs(xpos))]} failed on 'abs'; {[('X' + s)]} printed X1)."""
        src = "@t\n{['X'(abs(xpos))]}\n{'Y'(abs(xpos))}\nendp"
        engine = Engine(src)
        engine.set(xpos=-2, clear_change_after_gen=1)
        engine.changed['xpos'] = True
        engine.call('t')
        self.assertEqual(engine.output, ['X2', 'Y2'])
        self.assertNotIn('abs', engine.changed)
        src = "@t\n{[('X' + s)]}\nendp"
        engine = Engine(src)
        engine.set(s='1', x=0)
        engine.changed.update(s=False, x=True)
        engine.call('t')
        self.assertEqual(engine.output, [''])

    def test_call_arguments_are_parsed_not_split_on_commas(self):
        src = ("@t\ncall @p(('a,b'))\ncall @q((left('abc',2)), (3))\ncall @r()\nendp\n"
               "@p(string s)\nx=s\nendp\n@q(string s, numeric n)\ny=s\nz=n\nendp\n@r\nw=1\nendp")
        engine = run(src)                                       # the original engine split on the commas
        self.assertEqual((engine.state['x'], engine.state['y'], engine.state['z'], engine.state['w']),
                         ('a,b', 'ab', 3, 1))

    def test_local_redeclarations_do_not_leak(self):
        cases = [('@t\nlocal integer i\ni=5\nlocal integer i\nendp', {'i': 1}, (), {'i': 1}),
                 ('@t(numeric i)\nlocal integer i\ni=5\nendp', {'i': 1}, (2,), {'i': 1}),
                 ('@t\ni=0\nwhile i<2\nlocal numeric y\ny=5\ni=i+1\nendw\nendp', {'y': 8}, (), {'y': 8, 'i': 2})]
        for src, state, args, expected in cases:
            with self.subTest(src=src):
                new = Engine(src)                               # the original engine lost the outer value
                new.set(**state)
                new.call('t', list(args))
                self.assertEqual(new.state, expected)

    def test_numeric_assignment_target_is_rejected(self):
        """The original engine stored the value under the name '5'."""
        with self.assertRaisesRegex(UnsupportedGPPL, 'unsupported statement'):
            run('@t\n5 = x\nendp', x=1)

    def test_doubled_double_quote_is_consistent(self):
        """The original engine printed 'ab' but assigned 'a"b'."""
        new = run('@t\n{"a""b"}\nx="a""b"\nendp')
        self.assertEqual((new.output, new.state['x']), (['a"b'], 'a"b'))

    def test_structure_errors_are_located_and_raised_before_side_effects(self):
        """The original engine failed with 'list index out of range' on a stray else, failed on an
        unclosed if only after its output and assignments, and ran a mis-nested while/if."""
        with self.assertRaisesRegex(UnsupportedGPPL, 'else without if'):
            run('@t\nelse\nendp')
        new = Engine("@t\n{'X'}\nif true\nx=1\nendp")
        with self.assertRaisesRegex(UnsupportedGPPL, 'unclosed if'):
            new.call('t')
        self.assertEqual((new.output, new.state), ([], {}))
        self.assertTrue(any(d.code == 'E-STRUCT' for d in new.diagnostics))
        src = '@test\ni=0\nwhile i<1\nif true\ni=i+1\nendw\nendif\nendp'
        with self.assertRaisesRegex(UnsupportedGPPL, r'endw inside if \(unclosed if at line 4\)'):
            Engine(src).call('test')

    def test_code_outside_procedures_and_missing_endp_are_reported(self):
        """The original engine dropped code outside procedures without a word."""
        src = "@test\nx=1\nendp\nx=2\n{'never'}\nendp\n@a\ny=1\n@b\nendp"
        codes = [d.code for d in Engine(src).diagnostics]
        self.assertEqual(codes, ['W-OUTSIDE', 'W-OUTSIDE', 'W-ENDP', 'W-MISSING-ENDP'])
        with self.assertRaisesRegex(UnsupportedGPPL, 'statement outside any procedure'):
            Engine(src, policies=Policies(load_errors='raise'))

    def test_unexecuted_unsupported_code_is_reported_at_load(self):
        src = '@ok\nx = 1\nendp\n@bad\nif false\nexec rm -rf\nendif\nendp'
        engine = Engine(src)                                                       # the original engine never saw it
        engine.call('ok')                                                          # still allowed
        self.assertEqual([(d.code, d.line) for d in engine.diagnostics], [('E-SYNTAX', 6)])

    def test_errors_carry_one_gppl_call_chain(self):
        """The original engine re-wrapped the message at every frame ('@a:2: @b:5: @c:8: ...')."""
        src = '@a\ncall @b\nendp\n@b\ncall @c\nendp\n@c\nx = missing\nendp'
        with self.assertRaises(UnsupportedGPPL) as caught:
            Engine(src).call('a')
        self.assertEqual(caught.exception.gppl_stack, [('c', 8), ('b', 5), ('a', 2)])
        self.assertIn("@c:8: missing variable 'missing'", str(caught.exception))
        self.assertIn('[call chain: @b:5 <- @a:2]', str(caught.exception))

    def test_constructs_the_gpp_needs(self):
        """right(), tostr(x:'fmt') and Print are used by start_of_file and usr_4x_index;
        the original engine had none of them, so those procedures could never run."""
        engine = Engine('')
        self.assertEqual(engine.expression("right('abcd', 2)"), 'cd')
        self.assertEqual(engine.expression("tostr(3:'5.0(p)') + ':05'"), '3:05')
        engine = Engine.from_path(PP)
        engine.set(date='26-Oct-2026', time='14:05:33')
        engine.call('usr_us_date')
        engine.call('usr_us_time')
        self.assertEqual((engine.state['sus_date'], engine.state['sus_time']), ('Oct-26-2026', '2:05:33PM'))

    def test_real_gpp_print_path_runs_under_session_policy(self):
        def index_engine(policies):
            engine = Engine.from_path(PP, policies=policies)
            engine.call('usr_ip_useroptions')
            engine.set(angle_4x_around_x=90, angle=0, cpos=0, apos=0, bpos=0, x_angle_const_z=0,
                       nPR1postemp=0, nPR1camcpos=0, nPR1camapos=0, bR1StepReset=False, nPR1pos=0, nPR2pos=0,
                       bLimit_3axis=False, bR1forceOutput=True,
                       i4xIndexClearanceMode=1, tool_z_level=10, tool_start_plane=40, nPtool_z_level=10,
                       iMplane=17, cWo='G', iWorkoffset=54, iAbsincmode=90, iMotionmode=1, position=1,
                       iCompActive=40, bR1useDir5a=False, bStopSinceMotion=False, iCycle832Mode=0,
                       mcode_f='2.0(p)', clear_change_after_gen=1)
            engine.changed.update({k: False for k in engine.state})
            return engine
        with self.assertRaisesRegex(UnsupportedGPPL, 'print_stmt=error'):
            index_engine(None).call('usr_4x_index')                    # compat, as the original engine: unsupported
        engine = index_engine(SESSION)
        engine.call('usr_4x_index')
        self.assertEqual(engine.console[0][0], 'print')
        self.assertIn('WARNING!! Tool Z Level', ''.join(engine.output))

    def test_whole_session_runs_through_the_real_gpp(self):
        require_vmid(self)
        session = Session.from_paths(PP, vmid=VMID)
        session.start()
        session.event('start_of_file', dict(part_name='P', program_number=1, date='01-Jan-2026',
                                            time='08:00:00', g_file_name='P.MPF', full_g_file_name='P.MPF'))
        session.event('end_program')
        session.event('end_of_file')
        self.assertEqual(session.finish().splitlines()[0], ';%_N_P_MPF')


if __name__ == '__main__':
    unittest.main()
