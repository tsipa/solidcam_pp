"""SolidCAM rejects variable names that collide with GPPL functions."""
import unittest

from pp_tests.gppl.builtins import RESERVED_FUNCTION_NAMES
from pp_tests.gppl.errors import UnsupportedGPPL
from pp_tests.gppl.policies import Policies
from pp_tests.gppl.runtime import Engine


class ReservedFunctionNameTests(unittest.TestCase):
    def test_declarations_and_assignments_reject_function_names(self):
        for name in sorted(RESERVED_FUNCTION_NAMES):
            for spelling in (name, name.upper()):
                for statement in (f'local numeric value, {spelling}',
                                  f'global numeric {spelling}', f'{spelling} = 1'):
                    with self.subTest(statement=statement):
                        # The offending procedure is never called. Strict load
                        # must catch the error even in unreachable code.
                        source = f'@main\nendp\n@unused\n{statement}\nendp'
                        with self.assertRaisesRegex(UnsupportedGPPL, 'reserved GPPL function name'):
                            Engine(source, policies=Policies(load_errors='raise'))

    def test_function_names_are_rejected_as_parameters(self):
        for name in ('dist', 'DIST', 'sin'):
            with self.subTest(name=name):
                with self.assertRaisesRegex(UnsupportedGPPL, 'reserved GPPL function name'):
                    Engine(f'@unused(numeric {name})\nendp')

    def test_prefixed_names_and_real_function_calls_remain_valid(self):
        engine = Engine('@main\nlocal numeric nDist nSin\nnDist = 3\n'
                        'nSin = sin(90)\nresult = nDist + nSin\nendp',
                        policies=Policies(load_errors='raise'))
        engine.call('main')
        self.assertEqual(engine.state['result'], 4)


if __name__ == '__main__':
    unittest.main()
