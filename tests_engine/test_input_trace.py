"""Input trace extraction preserves CAM data while removing post output."""
import gzip
import lzma
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

    def test_diagnostics_supply_missing_values_in_the_correct_event(self):
        raw = (b"(1)@start_of_file ==> part_name:'PART'\r\n"
               b"(2)@usr_header ==> \r\n"
               b"   aftercodes         > ; CAMDBG start_of_file date:27-OCT-2026 time:17:57:04\r\n"
               b"(1)@start_of_job ==> job_name:'rough'\r\n"
               b"                      > ; CAMDBG start_of_job angle:0. cpos:0. apos:0. bpos:0.\r\n"
               b"                      > ; CAMDBG start_of_job d_drill_type:-1\r\n"
               b"(1)@arc ==> xpos:15.000T xstart:12.000F\r\n"
               b"                      > ; CAMDBG arc xstart:99. ystart:5.25 zcenter_rel:0.\r\n"
               b"(2)@usr_arc ==> G2 X15\r\n")
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'source.mpf', Path(tmp) / 'reference.trace.txt.xz'
            source.write_bytes(raw)
            manifest = extract(source, destination)
            result = lzma.decompress(destination.read_bytes())
            events = parse_trace(result.decode())
            self.assertEqual(events[0].parameters['date'], '27-OCT-2026')
            self.assertEqual(events[0].parameters['time'], '17:57:04')
            self.assertEqual(events[1].parameters['d_drill_type'], -1)
            self.assertEqual(events[1].parameters['apos'], 0)
            self.assertEqual(events[2].parameters['xstart'], 12)
            self.assertFalse(events[2].changed['xstart'])
            self.assertEqual(events[2].parameters['ystart'], 5.25)
            self.assertEqual(events[2].parameters['zcenter_rel'], 0)
            self.assertNotIn(b'CAMDBG', result)
            self.assertTrue(all(not event.output for event in events))
            self.assertEqual(manifest['diagnostic_lines_read'], 4)
            self.assertNotIn('xstart', manifest['parameters_from_diagnostics'])
            self.assertEqual(manifest['compression'], 'xz')
            first = destination.read_bytes()
            extract(source, destination)
            self.assertEqual(destination.read_bytes(), first)

    def test_diagnostic_cannot_be_attached_to_an_unrelated_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'source.mpf', Path(tmp) / 'output.xz'
            source.write_bytes(b'(1)@line ==> xpos:1\n'
                               b'                      > ; CAMDBG arc xstart:0.\n')
            with self.assertRaisesRegex(ValueError, 'current public event'):
                extract(source, destination)
            self.assertFalse(destination.exists())
