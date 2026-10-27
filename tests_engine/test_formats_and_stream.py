"""Format engine (legacy and extended grammars) and NC output stream semantics."""
import unittest

import support  # noqa: F401  (skips this module under GPPL_ENGINE=legacy)
from pp_tests.engine import Engine, UnsupportedGPPL
from pp_tests.gppl.formats import parse_format as _parse, render_number
from pp_tests.gppl.policies import Policies

COMPAT = Policies()


def parse_format(text):
    return _parse(text, 'extended')


class FormatTests(unittest.TestCase):
    def test_parse_grammar(self):
        spec = parse_format('<(>+05.3(*-2P)<)>')
        self.assertEqual((spec.prefix, spec.suffix, spec.plus, spec.zero_pad, spec.int_digits,
                          spec.dec_digits, spec.scale, spec.flags),
                         ('(', ')', True, True, 5, 3, -2.0, frozenset({'p'})))
        self.assertEqual(parse_format('5.3/2').scale, 0.5)
        for bad in ('5', 'x.3', '5.3(q)', '5.3(*)', '', '5.3)', '5.3()', ' 5.3', '5.3 '):
            with self.subTest(bad=bad), self.assertRaises(UnsupportedGPPL):
                parse_format(bad)

    def test_legacy_grammar_is_exactly_the_legacy_regex(self):
        for text in ('8.5', '5.0(p)', '4.4(P)', '12.3'):
            with self.subTest(text=text):
                _parse(text, 'legacy')
        _parse('03.0', 'legacy')                     # the legacy regex accepts (and ignores) zero padding
        self.assertEqual(render_number(1.5, _parse('99.0', 'legacy'), COMPAT), '2')   # integer digits ignored
        with self.assertRaisesRegex(UnsupportedGPPL, 'more than 30 digits'):
            _parse('5.' + '3' * 31, 'legacy')
        for text in ('+8.5', '5.0(n)', '5.4(*-1)', '<(>5.3<)>', ' 5.3', '5.3 ', '5.3()'):
            with self.subTest(text=text), self.assertRaisesRegex(UnsupportedGPPL, 'unsupported numeric format'):
                _parse(text, 'legacy')

    def test_every_format_literal_in_the_pp_family(self):
        for text in ('8.5', '5.0(p)', '2.0(p)', '7.3', '5.3', '4.4(P)', '+8.5', '5.4', '5.1',
                     '5.0(n)', '5.4(*-1)', '<(>5.3<)>', '7.0(*1000P)', '5.3/1', '4.3(p)'):
            with self.subTest(text=text):
                parse_format(text)

    def test_legacy_rendering(self):
        cases = [(132, '8.5', '132'), (15.83333, '5.4', '15.8333'), (636.62, '4.4(P)', '636.62'),
                 (0, '2.0(p)', '0'), (-0.0001, '5.3', '0'), (8, '2.0(p)', '8'), (-90, '7.3', '-90'),
                 (2.5, '5.0(p)', '2')]
        for value, text, expected in cases:
            with self.subTest(value=value, text=text):
                self.assertEqual(render_number(value, parse_format(text), COMPAT), expected)
        self.assertEqual(render_number(1.23456, None, COMPAT), '1.235')

    def test_scale_sign_and_decoration(self):
        self.assertEqual(render_number(10, parse_format('5.4(*-1)'), COMPAT), '-10')
        self.assertEqual(render_number(3, parse_format('+8.5'), COMPAT), '+3')
        self.assertEqual(render_number(-3, parse_format('+8.5'), COMPAT), '-3')
        self.assertEqual(render_number(0, parse_format('+8.5'), COMPAT), '0')
        self.assertEqual(render_number(0, parse_format('+8.5'), COMPAT.with_(plus_zero='plus')), '+0')
        self.assertEqual(render_number(7, parse_format('03.0'), COMPAT), '007')

    def test_point_and_digit_policies(self):
        keep = COMPAT.with_(trailing_zeros='keep')
        self.assertEqual(render_number(12.5, parse_format('8.3'), keep), '12.500')
        point = COMPAT.with_(flag_p='keep_point')
        self.assertEqual(render_number(1000, parse_format('4.4(P)'), point), '1000.')
        self.assertEqual(render_number(1000, parse_format('4.4'), point), '1000')
        nopoint = COMPAT.with_(trailing_zeros='keep', flag_n='no_point')
        self.assertEqual(render_number(5, parse_format('5.0(n)'), nopoint), '5')

    def test_rounding_policy(self):
        self.assertEqual(render_number(0.125, parse_format('5.2'), COMPAT), '0.12')        # binary/half-even
        self.assertEqual(render_number(0.125, parse_format('5.2'), COMPAT.with_(rounding='half_away')), '0.13')
        self.assertEqual(render_number(-0.125, parse_format('5.2'), COMPAT.with_(rounding='half_away')), '-0.13')

    def test_typed_default_formats(self):
        engine = Engine("@t\nglobal integer i\nglobal numeric n\ni = 2\nn = 1.234567\n{i, ' ', n, ' ', (n*2)}\nendp")
        engine.call('t')
        self.assertEqual(engine.output[-1], '2 1.235 2.469')          # legacy fallback (3 decimals)
        engine = Engine("@t\nglobal integer i\nglobal numeric n\ni = 2\nn = 1.234567\n{i, ' ', n, ' ', (n*2)}\nendp",
                        policies=COMPAT.with_(typed_default_formats='on'))
        engine.set(numeric_def_f='8.5', integer_def_f='5.0(p)')
        engine.call('t')
        self.assertEqual(engine.output[-1], '2 1.23457 2.46913')
        engine = Engine('@t\nglobal numeric n\nn = 1.5\n{n}\nendp')                # v1 default: ignore *_def_f
        engine.set(numeric_def_f='8.5')
        engine.call('t')
        self.assertEqual(engine.output[-1], '1.5')


class OutputStreamTests(unittest.TestCase):
    def emit(self, body, policies=None, changed=None, **state):
        engine = Engine('@t\n' + body + '\nendp', policies=policies)
        engine.set(**state)
        engine.changed.update(changed or {})
        engine.call('t')
        engine.stream.finish()
        return engine

    def test_fragments_unchanged_and_lines_built(self):
        engine = self.emit("{'A'}\n{' B'}\n{nb,'C'}\n{nl,'D'}")
        self.assertEqual(engine.output, ['A', ' B', '\nC', '\nD'])
        self.assertEqual(engine.nc_lines(), ['A B', 'C', 'D'])

    def test_skipline_false_joins_the_next_nb_once(self):
        engine = self.emit("{nb,'G43 H1 '}\nskipline = false\n{nb,'Z50.'}\n{nb,'M8'}")
        self.assertEqual(engine.nc_lines(), ['G43 H1 Z50.', 'M8'])
        self.assertIs(engine.state['skipline'], False)          # PP-visible value untouched
        engine = self.emit("{nb,'A'}\nskipline = false\n{nb,'B'}\nskipline = false\n{nb,'C'}\n{nb,'D'}")
        self.assertEqual(engine.nc_lines(), ['ABC', 'D'])         # each assignment arms one join
        engine = self.emit("{nb,'G43 H1 '}\nskipline = false\n{nb,'Z50.'}",
                           policies=Policies(skipline='ignore'))
        self.assertEqual(engine.nc_lines(), ['G43 H1 ', 'Z50.'])

    def test_skipline_does_not_affect_nl(self):
        engine = self.emit("{nb,'A'}\nskipline = false\n{nl,'B'}\n{nb,'C'}")
        self.assertEqual(engine.nc_lines(), ['A', 'BC'])

    def test_block_numbers_and_block_text(self):
        engine = self.emit("{nb,'G0'}\n{nb,['X'x]}\n{nb,'M30'}\n{nl,'%'}", blknum_exist=True, blknum=10,
                           blknum_delta=5, blknum_f='5.0(p)', end_block_text=' ;', x=1, changed={'x': False})
        self.assertEqual(engine.nc_lines(), ['N10 G0 ;', 'N15 M30 ;', '% ;'])
        self.assertEqual(engine.state['blknum'], 20)

    def test_block_number_wraps_at_max(self):
        engine = self.emit("{nb,'A'}\n{nb,'B'}", blknum_exist=True, blknum=99990, blknum_delta=10, blknum_max=99995)
        self.assertEqual(engine.nc_lines(), ['N99990 A', 'N10 B'])

    def test_empty_lines_policy_and_remove_blanks(self):
        self.assertEqual(self.emit("{nb}\n{nb,'A'}").nc_lines(), ['A'])
        self.assertEqual(self.emit("{nb}\n{nb,'A'}", policies=Policies(empty_lines='keep')).nc_lines(), ['', 'A'])
        self.assertEqual(self.emit("{nb,'G0 X1 Y2'}", remove_blanks=True).nc_lines(), ['G0X1Y2'])

    def test_provenance(self):
        engine = Engine("@t\ncall @u\nendp\n@u\n{nb,'X'}\nendp")
        engine.call('t')
        line = engine.stream.all_lines()[0]
        self.assertEqual((line.origin, line.stack), (('u', 5), ('t', 'u')))
        self.assertIn('@u:5', engine.stream.annotated())


if __name__ == '__main__':
    unittest.main()
