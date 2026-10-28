"""Input trace extraction preserves CAM data while removing post output."""
import gzip
import lzma
import math
import tempfile
import unittest
from pathlib import Path

from pp_tests.gppl.session import Session, load_events, resolve_policies
from pp_tests.tools.input_trace import extract
from pp_tests.trace import parse_trace

from support import FIXTURES, PP, VMID, require_vmid


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

    def extract_bytes(self, raw):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'source.mpf', Path(tmp) / 'reference.trace.txt.xz'
            source.write_bytes(raw)
            manifest = extract(source, destination)
            result = lzma.decompress(destination.read_bytes())
        return manifest, result, parse_trace(result.decode())

    def test_diagnostic_restates_an_agreeing_native_number_with_more_decimals(self):
        """The 828D post prints arc_size and the centre with 9 decimals (usr_camdbg_arc); the trace
        prints 3 to 5. An agreeing readout respells the native number and keeps its flag; a
        disagreeing one or one with fewer decimals leaves the native value."""
        raw = (b"(1)@arc ==> xpos:15.00000T arc_size:45.000 xcenter_rel:3.63419T zstart:19.28000\r\n"
               b"                    ..> ycenter_rel:-3.65556\r\n"
               b"(2)@usr_camdbg_arc ==> \r\n"
               b"                      > ; CAMDBG arc xstart:31.6890612345 ystart:43.1396512345 zstart:19.28\r\n"
               b"                      > ; CAMDBG arc xcenter_rel:3.6341923456 ycenter_rel:-3.6555598765 "
               b"zcenter_rel:0 arc_size:44.9995000001\r\n"
               b"(1)@arc_yz ==> arc_size:90.000\r\n"
               b"                      > ; CAMDBG arc_yz arc_size:90.0012345678\r\n")
        manifest, result, events = self.extract_bytes(raw)
        arc, arc_yz = events[0].parameters, events[1].parameters
        self.assertEqual((arc['xcenter_rel'], arc['ycenter_rel'], arc['arc_size']),
                         (3.6341923456, -3.6555598765, 44.9995000001))
        self.assertTrue(events[0].changed['xcenter_rel'])
        self.assertEqual((arc['xstart'], arc['ystart'], arc['zcenter_rel'], arc['zstart']),
                         (31.6890612345, 43.1396512345, 0, 19.28))
        self.assertIn(b'zstart:19.28000\r\n', result)
        self.assertEqual(arc_yz['arc_size'], 90)                     # 0.0012 off the native 90.000
        self.assertEqual(manifest['parameters_upgraded_from_diagnostics'],
                         {'arc_size': 1, 'xcenter_rel': 1, 'ycenter_rel': 1})
        self.assertEqual(manifest['diagnostics_kept_native'], {'arc_size': 1, 'zstart': 1})
        self.assertEqual(manifest['parameters_from_diagnostics'], {'xstart': 1, 'ystart': 1, 'zcenter_rel': 1})

    def test_command_names_are_strings_and_enum_numbers_must_be_numeric(self):
        raw = (b"(1)@def_tool ==> tool_number:1\n"
               b"                      > ; CAMDBG def_tool next_command:@def_tool\n"
               b"(1)@rapid_move ==> xpos:1.000T\n"
               b"                      > ; CAMDBG rapid_move prev_command:\n"
               b"(1)@start_of_job ==> flood_coolant:no_action\n"
               b"                      > ; CAMDBG start_of_job flood_coolant_value:2 rot_axis_coord_value:0\n")
        _, _, events = self.extract_bytes(raw)
        self.assertEqual(events[0].parameters['next_command'], '@def_tool')
        self.assertEqual(events[1].parameters['prev_command'], '')
        self.assertEqual((events[2].parameters['flood_coolant'], events[2].parameters['flood_coolant_value'],
                          events[2].parameters['rot_axis_coord_value']), ('no_action', 2, 0))
        with self.assertRaisesRegex(ValueError, 'nonnumeric diagnostic value'):
            self.extract_bytes(b"(1)@start_of_job ==> flood_coolant:no_action\n"
                               b"                      > ; CAMDBG start_of_job flood_coolant_value:no_action\n")

    def test_post_readouts_round_trip_through_the_extractor(self):
        """The post's CAMDBG lines (trace_level 5) in a trace of the shape SolidCAM writes (the
        engine's TraceRecorder, numbers with 3 decimals; one arc with a fractional centre and
        arc_size): every readout is allow-listed and attached to its event, the arc geometry and
        arc_size come back with 9 decimals. The
        engine resolves the constant D_Tapping to its name, the number being what the readout
        records, so the test gives it one."""
        require_vmid(self)
        events, extension, _ = load_events(FIXTURES / 'synthetic_session.json')
        arc = next(event['parameters'] for event in events if event['name'] == 'arc')
        arc.update(xcenter_rel=0.1234567891, ycenter_rel=-9.8765432109, arc_size=33.3333333333, arc_direction='cw')
        angle = math.radians(-arc['arc_size'])
        vx, vy = -arc['xcenter_rel'], -arc['ycenter_rel']
        arc.update(xcenter=arc['xstart'] + arc['xcenter_rel'], ycenter=arc['ystart'] + arc['ycenter_rel'])
        arc.update(xpos=arc['xcenter'] + vx * math.cos(angle) - vy * math.sin(angle),
                   ypos=arc['ycenter'] + vx * math.sin(angle) + vy * math.cos(angle))
        session = Session.from_paths(PP, vmid=VMID, policies=resolve_policies('session', {}, extension),
                                     number_style='3dp')
        report = session.replay(events, overrides={**extension.get('overrides', {}), 'trace_level': 5},
                                user_params=extension.get('user_params'), stop_on_error=True,
                                synthesize_commands=True)
        self.assertEqual(report.errors, [])
        trace = report.trace_text.encode()
        self.assertEqual(trace.count(b' d_tapping_value:d_tapping'), 1)
        trace = trace.replace(b' d_tapping_value:d_tapping', b' d_tapping_value:3')
        self.assertIn(b'> ; CAMDBG arc xstart:', trace)
        manifest, _, recorded = self.extract_bytes(trace)
        self.assertGreater(manifest['diagnostic_lines_read'], 0)
        self.assertEqual(manifest['parameters_upgraded_from_diagnostics'],
                         {'arc_size': 1, 'xcenter_rel': 1, 'ycenter_rel': 1})
        recorded = [event for event in recorded if event.name != 'init_post']
        self.assertEqual([event.name for event in recorded], [event['name'] for event in events])
        arcs = [(event, original['parameters']) for event, original in zip(recorded, events) if event.name == 'arc']
        self.assertTrue(arcs)
        for event, original in arcs:
            for key in ('xstart', 'ystart', 'xcenter_rel', 'ycenter_rel', 'arc_size'):
                self.assertAlmostEqual(event.parameters[key], original[key], places=8, msg=key)
