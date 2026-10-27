"""Cross-file contract between the GPP, the SolidCAM VMID and the Vericut files.

The revert matrix only covers commits that touch the GPP, so fixes made in
the machine definition (5c0271d, f88de47, c85f5f7, dc916d7, the .ctl half of
8966d35) had no guard. These are static checks; the oracle of each one is
the commit that introduced the setting, or the GPP behaviour the setting must
agree with. The files are read through support.vericut / support.paths, which
skip the test with a reason when a scratch copy lacks them (the VMID is
looked up next to PP_TEST_SOURCE first, the Vericut files in the repository
machine directory).
"""
import configparser
import html
import re
import unittest

from support import assert_detected, covers, fresh_engine, known_defect, mutate, parse_blocks
from support.vericut import ctl_text, gcodesim_ini_text, mch_text, vmid_text

HOMING_OPTIONS = ('shomestrbegin', 'shomestrtc', 'shomestrend', 'shomestrrotv', 'shomestrroth')


def attribute(text, name):
    return re.findall(r'\b' + re.escape(name) + r'="([^"]*)"', text)


def decimals(descriptor):
    """Decimal places of a GPPL/Vericut numeric format ('8.5', '+8.5', '5.0(p)',
    and the literal-wrapped '<(>5.3<)>' of older GPP revisions). An unparseable
    format fails the calling test with AssertionError instead of a TypeError,
    so a historical revision is reported as a failed pin, not a harness error."""
    match = re.fullmatch(r'(?:<[^>]*>)?[+]?\d+\.(\d+)(?:\((?:[pPnN]|\*[-+]?[\d.]+)\))*(?:<[^>]*>)?', descriptor)
    if match is None:
        raise AssertionError(f'unparseable numeric format {descriptor!r}')
    return int(match[1])


def init_state(source=None):
    engine = fresh_engine(source)
    engine.call('init_post')
    return engine.state


def gpp_code():
    """All executable GPP statements (comments removed by the engine parser)."""
    return '\n'.join(line for lines in fresh_engine().procedures.values() for _, line in lines)


class MachineDefinitionPins(unittest.TestCase):
    def test_5x_callbacks_are_in_part_coordinates(self):
        """INDEPENDENT: 5c0271d 'Sim 5x G-code reference set to part coordinates
        so generated 5-axis callbacks no longer include the machine setup
        offset'. The GPP prints move_5x/line_5x coordinates unchanged, so a
        VMID that reverts to machine coordinates shifts every 4x/5x move."""
        self.assertEqual(attribute(vmid_text(), 'OutputGcodePartCoordinate'), ['1'])

    def test_vericut_a_axis_link_matches_post_rotary_direction(self):
        """INDEPENDENT: 5c0271d 'link the A-axis to -X, matching the corrected
        rotary direction'. The GPP side of that direction is iR1dir = -1
        (@usr_r1pos_calc); flipping either side alone makes Vericut rotate the
        part opposite to the controller."""
        links = re.findall(r'<Link\s+Axis="([^"]+)"[^>]*Register="A"', mch_text())
        self.assertEqual(links, ['-X'])
        self.assertEqual(init_state()['ir1dir'], -1)

    def test_vericut_absolute_rotary_direction_mode(self):
        """INDEPENDENT: 8966d35 changed two .ctl modals; the direction rule for
        an undirected A position (A=DC) is the half not pinned elsewhere:
        shortest distance, 180 degrees CCW (the 828D DC rule)."""
        direction = re.findall(r'<MacroModal Name="mmABSOLUTE_ROTARY_DIRECTION"\s+Value="([^"]+)"', ctl_text())
        self.assertEqual(direction, ['mmSHORTEST_DISTANCE180CCW'])

    def test_vericut_models_a_as_modulo_axis(self):
        """INDEPENDENT: 8966d35 switched the Vericut A axis from linear to
        modulo 360 (the 828D A axis is a modulo axis)."""
        rotary_type = re.findall(r'<MacroModal Name="mmA_AXIS_ROTARY_TYPE"\s+Value="([^"]+)"', ctl_text())
        self.assertEqual(rotary_type, ['mmABSOLUTE_360'])

    def test_rotary_output_precision_matches_vmid(self):
        """CHARACTERIZATION (pin of the dc916d7 pairing): dc916d7 set VMID
        RotaryAxisPrecision 0.002 -> 0.001 so that SolidCAM simulation rounds A
        like the 3-decimal NC output (nR1pos_f). The equality is inferred from
        that commit, not stated (before it the pair was 0.002 vs 3 decimals);
        history-misc-03 correction: label such pairings a pin."""
        values = attribute(vmid_text(), 'RotaryAxisPrecision')
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(float(values[0]), 10 ** -decimals(init_state()['nr1pos_f']))

    def test_vmid_movement_precision_matches_output_decimals(self):
        """CHARACTERIZATION (pin of the dc916d7 pairing, history-misc-03
        correction): dc916d7 raised the XYZ output to 5 decimals together with
        VMID MovementPrecision 4 -> 5. The equality of the two is an inference
        (before dc916d7 the pair was 3 decimals vs 4), pinned for the formats
        @init_post sets (the later zpos_f switch to '5.4' at the first rapid is
        PP-006, not checked here)."""
        match = re.search(r'MovementPrecision="(\d+)"', vmid_text())
        self.assertIsNotNone(match)
        state = init_state()
        self.assertEqual({key: decimals(state[key]) for key in ('xpos_f', 'ypos_f', 'zpos_f')},
                         dict.fromkeys(('xpos_f', 'ypos_f', 'zpos_f'), int(match[1])))

    def test_vericut_ij_words_keep_post_precision(self):
        """INDEPENDENT: commit intent of f88de47 ('use 8.5 metric formatting for
        I and J macro call words'): @usr_arc prints the XY centre words I/J
        with numeric_def_f, so the Vericut control must read them with the same
        number of decimals. Reverting f88de47 (I/J back to 5.3) fails here. K
        is the separate known defect PP-051 (test below)."""
        ctl = ctl_text()
        precision = decimals(init_state()['numeric_def_f'])
        formats = {}
        for word in ('I', 'J'):
            match = re.search(r'<Word Name="' + word + r'" Type="[^"]+">\s*<Value [^>]*MetricFormat="([^"]*)"', ctl)
            self.assertIsNotNone(match, f'{word} word missing from the Vericut control')
            formats[word] = decimals(match[1])
        self.assertEqual(formats, {'I': precision, 'J': precision})


class MachineDefinitionKnownDefects(unittest.TestCase):
    @known_defect('PP-050')
    def test_vericut_mac_table_matches_post_work_offsets(self):
        """INDEPENDENT: c85f5f7 'Map additional Vericut MAC setups to G54'. The
        GPP maps every CoordSys position to G54 (@home_number with
        iWorkOffset_Method = 0; deliberate single-origin design, DESIGN-006),
        so the Vericut MAC table must give that offset for every MAC up to the
        highest one it lists; MAC 4 is missing."""
        parser = configparser.ConfigParser()
        parser.read_string(gcodesim_ini_text())
        table = {int(key): int(value) for key, value in parser['MAC'].items()}
        expected = {}
        for position in range(1, max(table) + 1):
            engine = fresh_engine()
            engine.call('usr_ip_useroptions')
            engine.set(iWorkOffset_Method=0, position=position, home_user_name='', rotate_angle_x=0,
                       rotate_angle_y=0, rotate_angle_z=0, shift_x=0, shift_y=0, shift_z=0)
            engine.call('home_number')
            expected[position] = engine.state['iworkoffset']
        self.assertEqual(table, expected)

    @known_defect('PP-051', match='MetricFormat precision')
    def test_vericut_arc_center_words_keep_post_precision(self):
        """INDEPENDENT: f88de47 'use 8.5 metric formatting for I and J macro call
        words' to match the post's numeric_def_f; @usr_arc prints K (ZX and YZ
        arcs) from the same numeric_def_f and the VMID enables those planes
        (SupportArcsZX_YZ="1"), so K needs the same precision. UNVERIFIED:
        whether Vericut's K MetricFormat changes the simulated arc for a word
        written with a decimal point (PP-051 uncertain)."""
        if attribute(vmid_text(), 'SupportArcsZX_YZ') != ['1']:
            self.skipTest('ZX/YZ arcs disabled in the VMID; K is never printed')
        ctl = ctl_text()
        precision = decimals(init_state()['numeric_def_f'])
        formats = {}
        for word in ('I', 'J', 'K'):
            match = re.search(r'<Word Name="' + word + r'" Type="[^"]+">\s*<Value [^>]*MetricFormat="([^"]*)"', ctl)
            self.assertIsNotNone(match, f'precondition: no {word} word format in the Vericut control')
            formats[word] = decimals(match[1])
        self.assertEqual(formats, {'I': precision, 'J': precision, 'K': precision},
                         'Vericut arc centre word MetricFormat precision differs from numeric_def_f')

    @known_defect('PP-052', match='never read by the GPP')
    def test_every_vmid_user_parameter_is_read_by_the_post(self):
        """INDEPENDENT: a VMID user parameter appears in the SolidCAM job/part
        dialog; if the GPP never reads it the user's setting is silently
        ignored. M50 and M51 match the air-blast (iCoolantM7ON = 50) and
        low-pressure through-tool (iCoolantM6ON = 51) codes, so they read as
        coolant switches, but no GPP statement uses them."""
        names = re.findall(r'<(?:Param|ParamJobs) GppName="([^"]+)"', vmid_text())
        self.assertTrue(names, 'precondition: no VMID user parameters found')
        code = gpp_code()
        unused = [name for name in names if not re.search(r'\b' + re.escape(name) + r'\b', code, re.I)]
        self.assertEqual(unused, [], 'VMID user parameters never read by the GPP')


class ConfigurationGuards(unittest.TestCase):
    """VMID settings that keep dormant non-Sinumerik PP paths unreachable."""

    def test_vmid_offers_only_parameterized_drill_cycles(self):
        """INDEPENDENT: @drill parameterises only CYCLE81/82/83/84/86; any other
        drill type falls through to a stale 'MCALL CYCLE<gcode>' without
        arguments (PP-031). The VMID must offer exactly these cycles."""
        names = set(re.findall(r'<DrillCycle GppName="([^"]+)"', vmid_text()))
        self.assertEqual(names, {'G81', 'G82', 'G83', 'G84', 'G86'})

    @covers('PP-044', 'PP-057')
    def test_vmid_keeps_subroutines_and_loops_disabled(self):
        """INDEPENDENT: @call_proc/@proc/@end_proc/@loop/@end_loop and the
        bPrintloop block of @start_of_job emit Fanuc code (M98 H, M99, #
        variables, WHILE [..]) and the literal text 'cR1' (PP-044, PP-057);
        the VMID ProceduresDef must keep GenProc, DrillProc and LoopExist off."""
        definition = re.search(r'<ProceduresDef [^>]*>', vmid_text())
        self.assertIsNotNone(definition)
        self.assertEqual({name: attribute(definition[0], name) for name in ('GenProc', 'DrillProc', 'LoopExist')},
                         {'GenProc': ['0'], 'DrillProc': ['0'], 'LoopExist': ['0']})


class HomingDefinitionTests(unittest.TestCase):
    def check_homing(self, source=None):
        """Every shipped homing definition retracts Z alone first, then X/Y, in
        G75 blocks Vericut knows (NCSubstitution inputs of the control). Only
        the G75 blocks are matched against the control, so a non-homing block a
        future fix emits after the Z retract (e.g. an X/Y re-programming for
        PP-001) does not trip this pin."""
        inputs = {html.unescape(value) for value in re.findall(r'<Substitution Input="([^"]*)"', ctl_text())}
        options = init_state(source)
        for name in HOMING_OPTIONS:
            modes = [line.split(':', 1)[0].strip() for line in options[name].split(';')]
            self.assertEqual(modes, ['8'] * len(modes), f'{name}: every line uses homing mode 8 (G75 fixed point)')
            engine = fresh_engine(source)
            engine.call('usr_ip_useroptions')
            engine.set(sHomestr=engine.state[name], iWorkoffset=54, cWo='G', iAbsincmode=90, iCompActive=40)
            engine.call('usr_prep_home_axis')
            blocks = parse_blocks(''.join(engine.output))
            self.assertGreaterEqual(len(blocks), 2, name)
            self.assertEqual([block.homing_axes for block in blocks][:1], [{'Z'}],
                             f'{name}: Z must retract alone first: {[block.raw for block in blocks]}')
            self.assertIn({'X', 'Y'}, [block.homing_axes for block in blocks[1:]], f'{name}: no X/Y homing')
            for block in blocks:
                if 75 in block.g:
                    self.assertIn(block.raw, inputs, f'{name}: {block.raw!r} is not a Vericut NCSubstitution input')

    def test_homing_retracts_z_first_and_matches_vericut_substitutions(self):
        """INDEPENDENT: machining safety (retract Z before any lateral move to
        the machine fixed point) and the Vericut control: only the G75 blocks
        listed as NCSubstitution inputs are simulated as homing moves (G75
        Z1=0. -> G53 G0 Z410, G75 Y1=0 X1=0 -> G53 G0 X-480 Y180)."""
        self.check_homing()

    def test_homing_pin_detects_mutation(self):
        """INDEPENDENT: mutation self-check; XY before Z, and a Z block Vericut
        does not substitute ('Z1=0' without the point), must fail the pin."""
        mutants = {
            'tool change homes XY first': ("sHomestrtc            = '8::G75 Z1=0. ;8::G75 Y1=0 X1=0'",
                                           "sHomestrtc            = '8::G75 Y1=0 X1=0 ;8::G75 Z1=0.'"),
            'rotation homing block unknown to Vericut': (
                "sHomestrroth          = '8::G75 Z1=0. ;8::G75 Y1=0 X1=0'",
                "sHomestrroth          = '8::G75 Z1=0 ;8::G75 Y1=0 X1=0'"),
        }
        for label, (old, new) in mutants.items():
            assert_detected(self, self.check_homing, mutate(old, new), label)


if __name__ == '__main__':
    unittest.main()
