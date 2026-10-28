"""Input trace extraction preserves CAM data while removing post output."""
import gzip
import tempfile
import unittest
from pathlib import Path

from pp_tests.tools.input_trace import extract
from pp_tests.trace import parse_trace


class InputTraceTests(unittest.TestCase):
    def test_input_values_and_format_survive_identity_changes(self):
        raw = (b"(1)@start_of_file ==> part_name:'PRIVATE_PART'\r\n"
               b"                    ..> full_g_file_name:'Z:\\private\\sample.mpf'\r\n"
               b"(2)@usr_header ==> GENERATED_HEADER\r\n"
               b"                      > G54 A=DC(90)\r\n"
               b"(1)@start_of_job ==> job_name:'rough-one' original_job_name:'rough_one'\r\n"
               b"                    ..> job_type:'spiral_pocket' index_job:3\r\n"
               b"(1)@line_5x ==> xpos:12.34500T apos:-90.00000F feed:600.000\r\n"
               b"(2)@usr_line ==> G1 X12.345 A=ACN(270) F600\r\n"
               b"                    ..> internal_only:99\r\n"
               b"(1)@end_of_file ==> no parameters\r\n")
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'source.mpf', Path(tmp) / 'reference.trace.txt.gz'
            source.write_bytes(raw)
            manifest = extract(source, destination, forbidden=['private', 'rough'])
            result = gzip.decompress(destination.read_bytes())
            events = parse_trace(result.decode())
            self.assertEqual([e.name for e in events], ['start_of_file', 'start_of_job', 'line_5x', 'end_of_file'])
            self.assertTrue(all(not event.output for event in events))
            self.assertEqual(events[1].parameters['job_name'], 'operation_001')
            self.assertEqual(events[1].parameters['original_job_name'], 'operation_001')
            self.assertEqual(events[1].parameters['job_type'], 'spiral_pocket')
            self.assertEqual(events[2].changed, {'xpos': True, 'apos': False})
            self.assertIn(b'xpos:12.34500T apos:-90.00000F feed:600.000\r\n', result)
            self.assertNotIn(b'internal_only', result)
            self.assertEqual(source.read_bytes(), raw)
            first = destination.read_bytes()
            self.assertEqual(extract(source, destination), manifest)
            self.assertEqual(destination.read_bytes(), first)

    def test_forbidden_identity_fails_without_leaving_an_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'source.mpf', Path(tmp) / 'output.gz'
            source.write_bytes(b"(1)@def_tool ==> tool_message:'private_reference'\n")
            with self.assertRaisesRegex(ValueError, 'forbidden identity'):
                extract(source, destination, forbidden=['private'])
            self.assertFalse(destination.exists())
