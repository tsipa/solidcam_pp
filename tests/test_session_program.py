"""Program-level session tests for Gmill_540v_4x.gpp (area A, sentinel file).

Scope: @start_program, @end_program/@end_of_file, the @start_of_file header,
the @def_tool tool list with its WORKPIECE blank, the state @init_post leaves
for a first job, whole-program safety invariants of a two-job session, the
homing-string parser (@usr_prep_home_axis/@usr_home_axis) and the first-job
outcome under the persisting change-flag policy (PP-054, ENGINE-001).

Every program is built with support.Session from the GPP's own @init_post
(flags='clear' unless a test says otherwise) and checked on parsed NC blocks
(support.nc) or on the modal replay (support.modal). Each passing guard proves
it guards something: an in-memory mutation of the GPP (support.mutation) must
make it fail with AssertionError.

Oracles: Sinumerik 828D programming semantics (';' comment, M30/M2 program
end, G75 fixed-point approach, G90/G91 modal, G53 block-wise), machining
safety (coolant and spindle off and Z retracted before X/Y travel), the PP's
own option documentation in @usr_ip_useroptions, the VMID PrecisionDef and the
commit messages of the guarded fixes. Whitespace of the rendered blocks is only
a CHARACTERIZATION of how the engine renders nb/nl (TSR-16).
"""
import re
import unittest

from support import (Session, assert_detected, g_function_whitelist, index_of, known_defect, mutate,
                     parse_blocks, replay, state_before)


def listing(blocks):
    return '\n'.join(block.raw for block in blocks)


def homed_axes(block):
    """Axes a block moves: plain X/Y/Z words plus G75 X1=/Y1=/Z1= targets."""
    return set(block.axes) | block.homing_axes


# ---------------------------------------------------------------------------
# Program end
# ---------------------------------------------------------------------------

END_ANCHOR_M30 = "        {nb, 'M30'}\n        {nl}\n"
END_ANCHOR_M2 = "        {nb, 'M2'}\n        {nl}\n"


class ProgramEndTests(unittest.TestCase):
    """@end_program/@end_of_file after a one-job program (shipped options)."""

    def program_end(self, source=None, **options):
        s = Session(source=source, options=options)
        s.first_tool()
        s.cut(10, 20, 5, -1)
        s.ev('end_of_job')
        mark = s.mark()
        s.ev('end_program', last_tool=True)
        s.ev('end_of_file')
        return s, mark

    def assert_program_end(self, source=None, end_code=30, **options):
        s, mark = self.program_end(source, iProgendmode={30: 1, 2: 2}[end_code], **options)
        text, blocks = s.text(mark), s.blocks(mark)
        shown = listing(blocks)
        program = s.blocks()
        replayed = replay(program)
        ends = [index for index, block in enumerate(program) if block.m in ([30], [2])]
        # Sinumerik: exactly one program end, and it is the last block.
        self.assertEqual(ends, [len(program) - 1], f'program end must be the single last block:\n{shown}')
        self.assertEqual(program[-1].m, [end_code], shown)
        self.assertEqual([word.raw for word in program[-1].words], [f'M{end_code}'],
                         f'the program end block must be exactly M{end_code}:\n{shown}')
        # Safety at program end: coolant and spindle off, Z at the fixed point before X/Y.
        at_end = replayed[-1][1]
        self.assertEqual(at_end.coolant, frozenset(), f'coolant still on at program end:\n{shown}')
        self.assertEqual(at_end.spindle, 5, f'spindle not stopped at program end:\n{shown}')
        self.assertEqual(at_end.homed, frozenset('XYZ'), f'X/Y/Z not at the fixed point at program end:\n{shown}')
        z_home = index_of(blocks, lambda b: b.homing_axes == {'Z'})
        xy_home = index_of(blocks, lambda b: {'X', 'Y'} <= b.homing_axes)
        self.assertGreaterEqual(z_home, 0, f'no G75 Z retract before program end:\n{shown}')
        self.assertLess(z_home, xy_home, f'Z must reach the fixed point before X/Y travel:\n{shown}')
        self.assertEqual(index_of(blocks, lambda b: bool({'X', 'Y'} & homed_axes(b)), 0, z_home), -1,
                         f'X/Y moved before the Z retract:\n{shown}')
        # CHARACTERIZATION (tc-14, R1-03): this PP stops coolant and spindle before
        # the final retract; retract-then-stop would be equally safe.
        for code in (9, 5):
            stop = index_of(blocks, lambda b, c=code: b.has('M', c))
            self.assertTrue(0 <= stop < z_home, f'M{code} must precede the final retract:\n{shown}')
        # CHARACTERIZATION of the engine's nb/nl rendering (TSR-16): 961facc
        # terminates the program end block with a line feed, a03b38e removed the
        # trailing blank after the end code.
        lines = text.split('\n')
        self.assertEqual(lines[-1], '', f'last block not terminated by a line feed (961facc): {text!r}')
        self.assertEqual(lines[-2], f'M{end_code}', f'trailing blank after M{end_code} (a03b38e): {text!r}')
        return blocks

    def test_end_program_sequence(self):
        """INDEPENDENT: Sinumerik program end plus end-of-program safety.

        M30 is the single last block and exactly 'M30'; coolant (M9) and spindle
        (M5) are off and Z reaches the G75 fixed point before X/Y (replayed modal
        state at M30: no coolant, M5, X/Y/Z homed). CHARACTERIZATION: M9/M5
        come before the G75 Z retract (tc-14/R1-03: retract-then-stop is equally
        safe). The whitespace part (line feed after M30, 961facc; no trailing
        blank, a03b38e) is a CHARACTERIZATION of how the engine renders nb/nl
        (TSR-16).
        """
        self.assert_program_end()

    def test_optional_stop_before_program_end(self):
        """INDEPENDENT: option doc 'bOptstpend: True = Outputs Optional Stop at end of program'."""
        blocks = self.assert_program_end(bOptstpend=True)
        self.assertEqual([block.m for block in blocks[-2:]], [[1], [30]], listing(blocks))
        s, mark = self.program_end()
        self.assertEqual(index_of(s.blocks(mark), lambda b: b.has('M', 1)), -1,
                         'bOptstpend=False (shipped) must not stop before M30')

    def test_m2_program_end_option(self):
        """INDEPENDENT: option doc 'iProgendmode: 1=M30, 2=M2'.

        Same end-of-program safety as M30; no M30 anywhere. The whitespace part
        is a CHARACTERIZATION of the engine's nb/nl rendering (TSR-16).
        """
        blocks = self.assert_program_end(end_code=2)
        self.assertEqual(index_of(blocks, lambda b: b.has('M', 30)), -1, listing(blocks))

    def test_program_end_regressions_are_detected(self):
        """INDEPENDENT: reverting 961facc/a03b38e or dropping a safety step fails the guard."""
        sources = {
            '961facc reverted (M30)': (mutate(END_ANCHOR_M30, "        {nb, 'M30'}\n"), 30),
            '961facc reverted (M2)': (mutate(END_ANCHOR_M2, "        {nb, 'M2'}\n"), 2),
            'a03b38e reverted (M30)': (mutate("{nb, 'M30'}", "{nb, 'M30 '}"), 30),
            'a03b38e reverted (M2)': (mutate("{nb, 'M2'}", "{nb, 'M2 '}"), 2),
            'XY homed before Z': (mutate("sHomestrend           = '8::G75 Z1=0. ;8::G75 Y1=0 X1=0'",
                                         "sHomestrend           = '8::G75 Y1=0 X1=0;8::G75 Z1=0. '"), 30),
            'no end homing': (mutate("    if sHomestrend ne ''\n        sHomestr = sHomestrend\n        call @usr_prep_home_axis\n",
                                     "    if sHomestrend ne ''\n        sHomestr = sHomestrend\n"), 30),
            'spindle not stopped': (mutate('bSpinoffend\t\t\t\t\t= true', 'bSpinoffend\t\t\t\t\t= false'), 30),
            'coolant not stopped': (mutate('bCooloffend\t\t\t\t\t= true', 'bCooloffend\t\t\t\t\t= false'), 30),
        }
        for label, (source, code) in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, lambda src, c=code: self.assert_program_end(src, end_code=c), source, label)


# ---------------------------------------------------------------------------
# Program start
# ---------------------------------------------------------------------------

class ProgramStartTests(unittest.TestCase):
    def assert_start_homing(self, source=None):
        s = Session(source=source)
        blocks = parse_blocks(s.ev('start_program'))
        shown = listing(blocks)
        # Z must reach the fixed point before any X/Y travel; G75 uses machine axes.
        self.assertEqual([block.homing_axes for block in blocks], [{'Z'}, {'X', 'Y'}],
                         f'start of program must home Z alone, then X/Y:\n{shown}')
        self.assertTrue(all(75 in block.g and not block.axes for block in blocks), shown)

    def test_start_program_homes_z_before_xy(self):
        """INDEPENDENT: machining safety, Z retracts before X/Y travel at program start.

        Sinumerik G75 Z1=0 / X1=0 Y1=0 approach the fixed point with machine axes;
        Z must move alone first.
        """
        self.assert_start_homing()

    def test_start_homing_regressions_are_detected(self):
        """INDEPENDENT: swapped, emptied or uncalled start homing fails the guard."""
        anchor = "sHomestrbegin         = '8::G75 Z1=0. ;8::G75 Y1=0 X1=0'"
        sources = {
            'XY before Z': mutate(anchor, "sHomestrbegin         = '8::G75 Y1=0 X1=0;8::G75 Z1=0. '"),
            'empty start homing': mutate(anchor, "sHomestrbegin         = ''"),
            'start homing not called': mutate(
                "    if sHomestrbegin ne ''\n        sHomestr = sHomestrbegin\n        call @usr_prep_home_axis\n",
                "    if sHomestrbegin ne ''\n        sHomestr = sHomestrbegin\n"),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.assert_start_homing, source, label)


# ---------------------------------------------------------------------------
# Tool list and WORKPIECE blank
# ---------------------------------------------------------------------------

TOOL_LIST_STOCK = dict(stock_x=100, stock_y=30, stock_z=20, stock_x_minus=25, stock_y_minus=-7,
                       stock_z_plus=8, stock_z_minus=-12, target_z_minus=-10)
NO_TOOL_MESSAGES = {f'msg_mill_tool{index}': '' for index in range(1, 6)}
TOOL_COMMENT = re.compile(r'(?:TOOL (?P<number>\d+) - DIA (?P<dia>[-\d.]+)|T(?P<tnumber>\d+)-(?P<message>.*?))'
                          r' \| HOLDER: (?P<holder>.*) \| STICKOUT: (?P<stickout>[-\d.]+) mm')
LIST_TOOLS = [
    dict(tool_number=3, tool_offset=5, tool_message='', holder_name='BT40 ER32', tool_length=45.25),
    dict(tool_number=12, tool_offset=3, tool_message='FINISH EM6', holder_name='SHRINK 6', tool_length=30,
         msg_mill_tool1='CHECK RUNOUT', msg_mill_tool3='NEW INSERTS'),
]
SIMPLE_TOOLS = [dict(tool_number=n, tool_offset=1, tool_message='', holder_name='H', tool_length=20)
                for n in (1, 2, 3)]
WORKPIECE_797FC88 = (
    ("' - DIA '(tool_offset*2),' | HOLDER: ',holder_name,' | STICKOUT: ',tool_length:'5.3',' mm',cCe }",
     "' - DIA '(tool_offset*2),cCe }"),
    ("'-' tool_message,' | HOLDER: ',holder_name,' | STICKOUT: ',tool_length:'5.3',' mm',cCe}",
     "'-' tool_message,cCe}"),
)


def tool_list(tools, source=None, fourth_axis_used=True, during_tool_change=False, **options):
    """Tool list as SolidCAM delivers it: one @def_tool per tool, then @start_program.

    during_tool_change=True delivers the @def_tool events after a @change_tool,
    so the PP's own @change_tool sets its bTlchg flag (no injected PP state).
    That event order is the template's stated intent ('Use bTlchg to use
    different message for tool_change'); whether SolidCAM ever produces it is
    UNVERIFIED.
    """
    s = Session(source=source, options=options, fourth_axis_used=fourth_axis_used, **TOOL_LIST_STOCK)
    if during_tool_change:
        s.ev('change_tool', first_tool=True, tool_number=tools[0]['tool_number'],
             next_tool_number=tools[0]['tool_number'])
    last = '@start_of_job' if during_tool_change else '@start_program'
    for ordinal, tool in enumerate(tools):
        values = dict(NO_TOOL_MESSAGES, **tool)
        values['next_command'] = '@def_tool' if ordinal + 1 < len(tools) else last
        s.ev('def_tool', **values)
    return s


def workpiece_blocks(blocks):
    return [block for block in blocks if block.words and block.words[0].address == 'WORKPIECE']


class ToolListTests(unittest.TestCase):
    def assert_tool_comment(self, block, tool):
        """Sinumerik comment carrying number, diameter or message, holder and stickout (797fc88)."""
        self.assertEqual(block.code, '', f'tool list entry must be a pure comment: {block.raw!r}')
        match = TOOL_COMMENT.fullmatch(block.comment or '')
        self.assertIsNotNone(match, f'tool list comment lacks holder/stickout (797fc88): {block.raw!r}')
        if tool['tool_message']:
            self.assertEqual((int(match['tnumber']), match['message']), (tool['tool_number'], tool['tool_message']))
        else:
            self.assertEqual(int(match['number']), tool['tool_number'])
            self.assertEqual(float(match['dia']), 2 * tool['tool_offset'], 'DIA is twice the tool radius')
        self.assertEqual(match['holder'], tool['holder_name'])
        self.assertAlmostEqual(float(match['stickout']), tool['tool_length'], delta=0.0005,
                               msg='stickout is the tool length (0.001 mm output)')

    def assert_tool_lines(self, source=None):
        s = tool_list(LIST_TOOLS, source)
        blocks = s.blocks()
        self.assertGreaterEqual(len(blocks), 4, listing(blocks))
        self.assert_tool_comment(blocks[0], LIST_TOOLS[0])
        self.assert_tool_comment(blocks[1], LIST_TOOLS[1])
        self.assertEqual([(b.code, b.comment) for b in blocks[2:4]],
                         [('', '---CHECK RUNOUT'), ('', '---NEW INSERTS')], listing(blocks))
        return blocks

    def test_tool_list_lines(self):
        """INDEPENDENT: 797fc88 intent (tool list comments carry holder name and stickout).

        Each entry is a Sinumerik ';' comment; DIA is twice tool_offset, STICKOUT
        is tool_length (float compare, 0.001 mm output). The ' | HOLDER: ' /
        ' | STICKOUT: ' separators and the '---' prefix of the tool message lines
        are a CHARACTERIZATION of the shipped format.
        """
        self.assert_tool_lines()

    def assert_trailer(self, source=None):
        blocks = self.assert_tool_lines(source)
        trailer = blocks[4:]
        shown = listing(blocks)
        self.assertEqual(len(trailer), 2, shown)
        self.assertEqual(trailer[0].find('MSG')[0].args, (' Loading Zeropoints ',), shown)
        pieces = workpiece_blocks(blocks)
        self.assertEqual(len(pieces), 1, f'the last tool entry must emit exactly one WORKPIECE (115bd14):\n{shown}')
        self.assertIs(pieces[0], blocks[-1], shown)
        # CHARACTERIZATION: the known-good rotary-axis blank of @usr_workpiece_stock
        # ("RECTANGLE" clamped on A; Par7 = stock_x, Par8 = -stock_x, Par9/10 = stock_y/z).
        self.assertEqual(pieces[0].words[0].args, ('', '"A"', '', '"RECTANGLE"', '0', '0', '100', '-100', '30', '20'))
        with_stop = tool_list(SIMPLE_TOOLS, source, bOptstpbegin=True).blocks()
        self.assertEqual([b.m for b in with_stop[3:4]], [[1]], listing(with_stop))
        self.assertEqual(len(workpiece_blocks(with_stop)), 1, listing(with_stop))
        self.assertIs(workpiece_blocks(with_stop)[0], with_stop[-1], listing(with_stop))
        during = tool_list(SIMPLE_TOOLS, source, during_tool_change=True).blocks()
        self.assertEqual([b.raw for b in during if b.find('MSG') or workpiece_blocks([b])], [],
                         f'trailer emitted for a @def_tool during a tool change:\n{listing(during)}')
        box = tool_list(SIMPLE_TOOLS[:1], source, fourth_axis_used=False).blocks()
        pieces = workpiece_blocks(box)
        self.assertEqual(len(pieces), 1, listing(box))
        args = pieces[0].words[0].args
        self.assertEqual(args[:5], ('', '', '', '"BOX"', '0'), listing(box))
        z0, z1, zb, x0, y0, x1, y1 = (float(value) for value in args[5:])
        stock = TOOL_LIST_STOCK
        self.assertEqual((z0, z0 + z1, z0 + zb), (stock['stock_z_plus'], stock['stock_z_minus'], stock['target_z_minus']),
                         f'BOX Z extents (Par5=0: Z1/ZB incremental from Z0):\n{listing(box)}')
        self.assertEqual((x0, y0, x1, y1), (stock['stock_x_minus'], stock['stock_y_minus'], stock['stock_x'], stock['stock_y']),
                         f'BOX X/Y origin and sizes:\n{listing(box)}')

    def test_tool_list_trailer_once_after_last_tool(self):
        """INDEPENDENT: 115bd14 intent, one WORKPIECE blank after the whole tool list.

        Middle entries emit no trailer; the last one emits MSG(" Loading
        Zeropoints ") and exactly one WORKPIECE call. bOptstpbegin ('Outputs
        Optional Stop at beginning of program') puts M1 before the trailer; a
        @def_tool after @change_tool (bTlchg set by the PP; event order
        UNVERIFIED, see tool_list) emits no trailer. Non-4x stock
        uses Siemens "BOX": with Par5=0 the Z1/ZB/X1/Y1 sizes are incremental
        (Siemens WORKPIECE doc cited in @usr_workpiece_stock), so the blank must
        reproduce the stock extents. The RECTANGLE argument list is a
        CHARACTERIZATION of the known-good rotary blank.
        """
        self.assert_trailer()

    def test_tool_list_reversion_797fc88_is_detected(self):
        """INDEPENDENT: reverting 797fc88 (no holder/stickout) fails the tool-line guard."""
        source = None
        for old, new in WORKPIECE_797FC88:
            source = mutate(old, new, source=source)
        assert_detected(self, self.assert_tool_lines, source, '797fc88 reverted', match='797fc88')

    def test_workpiece_reversion_115bd14_is_detected(self):
        """INDEPENDENT: no WORKPIECE (115bd14 reverted), a trailer per tool or during a tool change, or absolute BOX Z1 fails."""
        sources = {
            '115bd14 reverted': (mutate('            call @usr_workpiece_stock\n', ''), None),
            'trailer after every tool': (mutate("        if next_command ne '@def_tool' and bTlchg eq false\n",
                                                "        if bTlchg eq false\n"), None),
            'trailer during a tool change': (mutate("        if next_command ne '@def_tool' and bTlchg eq false\n",
                                                    "        if next_command ne '@def_tool'\n"), 'during a tool change'),
            'BOX Z1 absolute': (mutate('    nStockZ1 = stock_z_minus - stock_z_plus\n', '    nStockZ1 = stock_z_minus\n'),
                                'BOX Z extents'),
        }
        for label, (source, match) in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.assert_trailer, source, label, match)


# ---------------------------------------------------------------------------
# Header (@start_of_file)
# ---------------------------------------------------------------------------

def header_blocks(source=None, **cam):
    return parse_blocks(Session(source=source, header=True, **cam).header_text)


class ProgramHeaderTests(unittest.TestCase):
    def assert_header(self, source=None):
        s = Session(source=source, header=True, part_name='BRACKET-OP1-',
                    vmid=dict(Message1='CLAMP ON A', Message3='CHECK Z0'))
        blocks = parse_blocks(s.header_text)
        self.assertTrue(all(block.code == '' for block in blocks), f'header lines must be comments:\n{s.header_text}')
        self.assertEqual([block.comment for block in blocks], [
            '%_N_BRACKET_OP1__MPF',          # '-' is not allowed in Sinumerik names: replaced by '_'
            '$PATH=/_N_WKS_DIR/_N_WPD',
            'Oct-26-2026-2:41:00PM',         # 26-Oct-2026 14:41:00 in US order, 12-hour clock
            'CLAMP ON A',
            'CHECK Z0',
        ])
        self.assertEqual(s.state['scamfilepath'], 'C:\\cam\\', 'CAM part folder = full path minus file name')

    def test_header_lines(self):
        """INDEPENDENT: Sinumerik file header conventions and the PP's own procedure docs.

        ';%_N_<name>_MPF' with '-' replaced by '_' (Sinumerik program names use
        letters, digits and '_'), ';$PATH=/_N_WKS_DIR/_N_WPD', the date converted
        to US order and the time to a 12-hour clock (@usr_US_date 'Converts
        Europe Date format to US format', @usr_US_time 'Converts Military time to
        12hr format'), then the non-empty VMID Message1..10 lines; all are ';'
        comments. HEADER_DEFAULTS: date 26-Oct-2026, time 14:41:00.
        CHARACTERIZATION: the '-' separators of the date/time line and the
        '$PATH=/_N_WKS_DIR/_N_WPD' literal the PP prints for an empty sWorkpcDir
        (no Siemens rule defines a nameless workpiece directory). Runs with the
        GpplCompatEngine right()/tostr() workaround (ENGINE-007, Session default).
        """
        self.assert_header()

    def assert_workpiece_directory(self, source=None):
        blocks = header_blocks(source, vmid=dict(sWorkpcDir='FIXTURES'))
        self.assertIn('$PATH=/_N_WKS_DIR/_N_FIXTURES_WPD', [block.comment for block in blocks])

    def test_workpiece_directory_comment(self):
        """INDEPENDENT: Sinumerik workpiece directory path for the VMID parameter sWorkpcDir."""
        self.assert_workpiece_directory()

    def assert_clock(self, source=None):
        cases = (('00:07:09', '12:07:09AM'), ('01:00:00', '1:00:00AM'), ('11:59:59', '11:59:59AM'),
                 ('12:00:00', '12:00:00PM'), ('13:05:33', '1:05:33PM'), ('23:59:59', '11:59:59PM'))
        # No subTest: the mutation check needs the AssertionError to propagate.
        rendered = {clock: header_blocks(source, time=clock)[2].comment for clock, _ in cases}
        self.assertEqual(rendered, {clock: f'Oct-26-2026-{expected}' for clock, expected in cases})

    def test_12_hour_clock_boundaries(self):
        """INDEPENDENT: 12-hour clock convention (00:xx is 12 AM, 12:xx is 12 PM).

        Needs the tostr() workaround of GpplCompatEngine (ENGINE-007).
        """
        self.assert_clock()

    def test_header_regressions_are_detected(self):
        """INDEPENDENT: mutated name, path, date and clock conversions fail the header guards."""
        cases = {
            'program name keeps "-"': (self.assert_header, mutate(
                "    name2 = instr(part_name,'-')\n    while", "    name2 = 0\n    while")),
            'no _MPF suffix': (self.assert_header, mutate("{part_name'_MPF' }", "{part_name'.MPF' }")),
            'European date order': (self.assert_header, mutate(
                "sUS_date = substr(date,(iInt1+1),3) + '-' + substr(date,1,(iInt1-1)) + '-' + right(date,4)",
                "sUS_date = substr(date,1,(iInt1-1)) + '-' + substr(date,(iInt1+1),3) + '-' + right(date,4)")),
            'workpiece directory dropped': (self.assert_workpiece_directory, mutate(
                "'$PATH=/_N_WKS_DIR/_N_'sWorkpcDir '_WPD'", "'$PATH=/_N_WKS_DIR/_N_WPD'")),
            'midnight hour 0': (self.assert_clock, mutate(
                "        if iHr_Mil_int < 1\n            iHour = 12", "        if iHr_Mil_int < 1\n            iHour = 0")),
            'noon is AM': (self.assert_clock, mutate('    if iHr_Mil_int < 12\n', '    if iHr_Mil_int < 13\n')),
        }
        for label, (check, source) in cases.items():
            with self.subTest(mutant=label):
                assert_detected(self, check, source, label)


# ---------------------------------------------------------------------------
# Option invariants
# ---------------------------------------------------------------------------

class OptionGuardTests(unittest.TestCase):
    def assert_shared_off_code(self, source=None):
        state = Session(source=source).state
        codes = {index: state[f'icoolantm{index}off'] for index in range(1, 9)}
        self.assertEqual(set(codes.values()), {codes[1]},
                         f'coolant OFF codes differ, only channel 1 is ever switched off: {codes}')

    def test_coolant_off_codes_are_shared(self):
        """INDEPENDENT: code-path invariant (R1-12).

        @end_program and @usr_ct_before_notfirsttool flag only change(iCoolantM1)
        for output, so only iCoolantM1OFF is ever written. Every channel's OFF
        code must therefore equal it, or that channel stays on through the tool
        change and past M30.
        """
        self.assert_shared_off_code()
        assert_detected(self, self.assert_shared_off_code, mutate('iCoolantM5OFF\t\t\t\t= 9', 'iCoolantM5OFF\t\t\t\t= 79'),
               'distinct through-coolant OFF code')


# ---------------------------------------------------------------------------
# Session state from @init_post
# ---------------------------------------------------------------------------

FIRST_RAPID = dict(xpos=12.34567, ypos=-23.45678, zpos=5.43215, apos=-12.3456)
# A = (-apos) * iR1dir (iR1dir=-1), +360 for iR1posControl=1: -12.3456 + 360.
EXPECTED_A = 347.6544
LINE_X = 20.98765
XY_TOL = 0.000005 + 1e-9      # VMID MovementPrecision="5": half of 0.00001 mm
CONTROL_TOL = 0.0005 + 1e-9   # 828D input resolution 0.001 mm / 0.001 deg (VMID RotaryAxisPrecision)


class InitPostSessionTests(unittest.TestCase):
    def run_session(self, source=None):
        s = Session(source=source, tool_start_plane=50, tool_z_level=40)
        s.first_tool(tool=3, next_tool=4, spin=3000)
        start = s.blocks()
        mark = s.mark()
        s.ev('move_5x', ('xpos', 'ypos', 'zpos', 'apos'), **FIRST_RAPID)
        rapid = s.blocks(mark)
        mark = s.mark()
        s.ev('line_5x', ('xpos',), xpos=LINE_X, feed_type='feed_cut')
        return start, rapid, s.blocks(mark)

    def assert_session(self, source=None):
        start, rapid, line = self.run_session(source)
        shown = listing(start + rapid + line)
        rotary = [block.rotary('A') for block in start + rapid if block.rotary('A') is not None]
        self.assertTrue(rotary, f'no A word before the first cutting move:\n{shown}')
        self.assertEqual(rotary[0][0], 'DC', f'first A word of the program must be DC (ad2537a):\n{shown}')
        for axis, tolerance in (('X', XY_TOL), ('Y', XY_TOL), ('Z', CONTROL_TOL)):
            values = [block.axes[axis] for block in rapid if axis in block.axes]
            self.assertEqual(len(values), 1, f'{axis} words in the first rapid:\n{shown}')
            self.assertAlmostEqual(values[0], FIRST_RAPID[axis.lower() + 'pos'], delta=tolerance,
                                   msg=f'{axis} rounded coarser than the output resolution:\n{shown}')
        cut_x = [block.axes['X'] for block in line if 'X' in block.axes]
        self.assertEqual(len(cut_x), 1, shown)
        self.assertAlmostEqual(cut_x[0], LINE_X, delta=XY_TOL, msg=f'cutting X rounded too coarsely:\n{shown}')
        a_words = [block.rotary('A') for block in rapid if block.rotary('A') is not None]
        self.assertEqual(len(a_words), 1, shown)
        self.assertAlmostEqual(a_words[0][1], EXPECTED_A, delta=CONTROL_TOL,
                               msg=f'A rounded coarser than 0.001 deg:\n{shown}')
        self.assertEqual([block.raw for block in rapid + line if 17 in block.g], [],
                         f'unchanged modal G17 restated:\n{shown}')

    def test_session_from_init_post(self):
        """INDEPENDENT: output resolution and the initial A=DC from the GPP's own @init_post.

        X/Y keep VMID MovementPrecision=5 (half an increment tolerance); Z and A
        keep the 828D input resolution of 0.001 mm / 0.001 deg (VMID
        RotaryAxisPrecision) - Z's 4-decimal format is PP-006 (area D) and is not
        pinned here. Commit ab853be (bR1forceOutput initialised in @init_post):
        the first A word of a program is DC because the actual A position is
        unknown (the ad2537a branch order needs a non-zero first angle and is
        guarded by the indexed two-job test). Geometry: A = -apos * iR1dir
        (+360). Modal G17 is not restated (clear_change_after_gen contract).
        """
        self.assert_session()

    def test_init_post_mutations_are_detected(self):
        """INDEPENDENT: coarse formats, no initial DC force and no flag clearing fail the guard."""
        sources = {
            'xpos_f coarse': mutate("xpos_f          = '8.5'", "xpos_f          = '8.2'"),
            'zpos_f coarse (usr_rapid/usr_ct)': mutate("zpos_f = '5.4'", "zpos_f = '5.2'", count=3),
            'nR1pos_f integer': mutate("nR1pos_f        = '7.3'", "nR1pos_f        = '7.0'"),
            'no initial DC': mutate('    bR1forceOutput = true\n', '    bR1forceOutput = false\n'),
            'flags never cleared': mutate('clear_change_after_gen = 1', 'clear_change_after_gen = 0'),
        }
        for label, source in sources.items():
            with self.subTest(mutant=label):
                assert_detected(self, self.assert_session, source, label)


# ---------------------------------------------------------------------------
# Whole-program invariants of a realistic two-job session
# ---------------------------------------------------------------------------

def two_job_program(source=None):
    """Two indexed 4x jobs with different tools (event order: GPP @change_tool comment, 3696aa2)."""
    s = Session(source=source)
    s.first_tool(tmatrix=45)
    s.cut(10, 20, 5, -1.5, feed=250)
    s.next_tool(2, 3, tmatrix=90, last_tool=True, spin=8000, job_name='op2')
    s.cut(11, 21, 6, -2, feed=300)
    s.ev('end_of_job')
    s.ev('end_program')
    s.ev('end_of_file')
    return s.text()


class RealisticSessionTests(unittest.TestCase):
    def check_two_job_safety(self, text):
        blocks = parse_blocks(text)
        replayed = replay(blocks)
        shown = listing(blocks)
        for index, (block, state) in enumerate(replayed):
            if block.rotary('A') is not None and not block.axes:
                # c03e1b4: the motion mode is unknown after a control reset; an index
                # block without G0 in effect alarms 'Feedrate not programmed'.
                self.assertEqual(state.motion, 0, f'rotary index block without effective G0: {block.raw!r}\n{shown}')
                self.assertIn('Z', state_before(replayed, index).homed,
                              f'rotary index without preceding Z homing: {block.raw!r}\n{shown}')
        first_rotary = next((block.rotary('A') for block in blocks if block.rotary('A') is not None), None)
        self.assertIsNotNone(first_rotary, f'no A word in an indexed 4x program:\n{shown}')
        self.assertEqual(first_rotary[0], 'DC', f'first A position must be DC (ab853be/ad2537a):\n{shown}')
        changes = [index for index, block in enumerate(blocks) if block.has('M', 6)]
        self.assertEqual(len(changes), 2, shown)
        for change in changes:
            cut = next((index for index in range(change, len(blocks))
                        if blocks[index].is_motion and replayed[index][1].motion in (1, 2, 3)), -1)
            self.assertGreater(cut, change, f'no feed move after M06:\n{shown}')
            window = blocks[change:cut]
            self.assertTrue(any(b.has('D', 1) for b in window), f'tool offset D1 must be selected before cutting:\n{shown}')
            self.assertIn(replayed[cut][1].spindle, (3, 4), f'spindle must be started before the first feed move:\n{shown}')
            self.assertTrue(any(b.get('S') for b in window), f'speed must be programmed before the first feed:\n{shown}')
        self.assertEqual(blocks[-1].m, [30], shown)
        # CHARACTERIZATION of the engine's nl rendering (TSR-16): 961facc.
        self.assertTrue(text.endswith('\n'), 'last NC block must be terminated by a line feed (961facc)')

    def test_two_job_session_safety_properties(self):
        """INDEPENDENT: Sinumerik semantics and machining safety over a whole program.

        Every rotary index block runs with G0 in effect (c03e1b4) after a Z
        homing with no Z move since; the first A position is DC (ab853be/ad2537a);
        after each M06, D1, a spindle start and an S word precede the first feed
        move; the program ends with M30. The final line feed (961facc) is a
        CHARACTERIZATION of the engine's nl rendering (TSR-16).
        """
        self.check_two_job_safety(two_job_program())

    def test_two_job_session_mutations_are_detected(self):
        """INDEPENDENT: historical reversions and safety mutations fail the two-job invariant."""
        cases = {
            'c03e1b4 reverted (no G0 on the first index)':
                (mutate('of file\n\tiMotionmode = 9999', 'of file\n\tiMotionmode = 0'), 'without effective G0'),
            '961facc reverted (no final line feed)': (mutate(END_ANCHOR_M30, "        {nb, 'M30'}\n"), 'line feed'),
            'no spindle start after the tool change': (mutate(
                '            skipline = false\n            call @start_tool\n        endif\n    endif\n;    bSkipxyrapid',
                '            skipline = false\n        endif\n    endif\n;    bSkipxyrapid'), 'spindle must be started'),
            'no homing before an index': (mutate(
                "            if i4xIndexClearanceMode eq 0\n                if sHomestrrot ne ''\n"
                "                    sHomestr = sHomestrrot\n                    call @usr_prep_home_axis\n"
                "                endif\n                iMotionmode = 0\n                {nb,",
                "            if i4xIndexClearanceMode eq 0\n                iMotionmode = 0\n                {nb,"),
                'without preceding Z homing'),
            'no initial DC force': (mutate('    bR1forceOutput = true\n', '    bR1forceOutput = false\n'), 'must be DC'),
            'D1 removed (420c4ab reverted)': (mutate("    {nb, 'D1 '}\n", ''), 'D1'),
        }
        for label, (source, match) in cases.items():
            with self.subTest(mutant=label):
                assert_detected(self, lambda src: self.check_two_job_safety(two_job_program(src)), source, label, match)


# ---------------------------------------------------------------------------
# Homing strings (@usr_prep_home_axis / @usr_home_axis)
# ---------------------------------------------------------------------------

SHIPPED_HOMING = '8::G75 Z1=0. ;8::G75 Y1=0 X1=0'
HOMING_MODES = {mode: f'{mode}::Z0;{mode}::X0 Y0' for mode in range(1, 8)}
HOMING_MODES[8] = SHIPPED_HOMING
HOMING_TARGET = dict(xpos=30, ypos=40, zpos=5)


def homing_session(homing, source=None, options=None, **cam):
    """Mid-job homing (one cut done), then one absolute rapid to HOMING_TARGET.

    STRUCTURAL: @usr_prep_home_axis is a PP procedure, not a SolidCAM event. It
    is driven directly with a homing string of the shape the sHomestr* user
    options hold (the PP calls it from @start_program, the tool change, the
    rotary rapid and @end_program). The following rapid gets SolidCAM's real
    previous event ('@line_5x', the retract of the cut), not the procedure name.
    """
    s = Session(source=source, options=options, **cam)
    s.first_tool()
    s.cut(10, 20, 5, -1)
    before = s.mark()
    s.ev('usr_prep_home_axis', sHomestr=homing)
    after = s.mark()
    s.ev('move_5x', ('xpos', 'ypos', 'zpos'), prev_command='@line_5x', **HOMING_TARGET)
    return s, before, after


class HomingStringTests(unittest.TestCase):
    def check_homing_modes(self, source=None, modes=tuple(HOMING_MODES)):
        for mode in modes:
            s, before, after = homing_session(HOMING_MODES[mode], source)
            program = s.blocks()
            homing = s.blocks(before)[:len(s.blocks(before)) - len(s.blocks(after))]
            shown = f'mode {mode}:\n' + listing(s.blocks(before))
            # Z first, no X/Y before Z: the first homing block moves Z alone.
            axes = [homed_axes(block) for block in homing]
            self.assertTrue(axes, shown)
            self.assertEqual(axes[0], {'Z'}, f'the first homing block must move Z alone:\n{shown}')
            self.assertTrue(any({'X', 'Y'} <= moved for moved in axes[1:]), f'X/Y homing line missing:\n{shown}')
            # G91 must not leak: the next rapid programs the absolute target with G90 in effect.
            position = len(program) - len(s.blocks(after))
            state = replay(program)[position][1]
            self.assertEqual(state.distance, 90, f'G91 leaks after homing:\n{shown}')
            targets = {axis: value for block in program[position:] for axis, value in block.axes.items()}
            self.assertEqual(targets, dict(X=30, Y=40, Z=5), f'rapid after homing misses its target:\n{shown}')
            if mode in (3, 4):
                # Doc @usr_ip_useroptions: 3 = G53 Non-Modal, 4 = G53 Modal.
                self.assertTrue(all(53 in block.g for block in homing), f'G53 homing not in machine coordinates:\n{shown}')
                rapid = program[position]
                self.assertNotIn(53, rapid.g, f'G53 leaks into the positioning block:\n{shown}')
                offsets = [code for code in rapid.g if 54 <= code <= 57 or 505 <= code <= 599]
                # CHARACTERIZATION: after block-wise G53 (mode 3) re-outputting G54 would be equally valid.
                self.assertEqual(offsets, [54] if mode == 4 else [],
                                 f'mode {mode}: work offset re-output after G53 homing:\n{shown}')

    def test_homing_modes(self):
        """INDEPENDENT: invariants of the documented homing modes 1..8 (@usr_ip_useroptions).

        Kept invariants only (the G28/G30 block texts of modes 1/2/5/6 are ISO
        dialect and not certified): Z is homed alone before any X/Y; after the
        homing the next absolute rapid runs in G90 (modes 2/6 switch to G91 for
        the homing block; a leaked G91 runs absolute targets incrementally) and
        reaches its target; modes 3/4 home in machine coordinates (G53 is
        block-wise on Sinumerik). CHARACTERIZATION of the PP's choice: only mode 4
        ('G53 Modal') re-outputs the active work offset; for mode 3 a re-output G54
        after the block-wise G53 would be equally valid on Sinumerik, so its absence
        is pinned, not required. Mode 7's offset handling is PP-042 and not asserted.
        STRUCTURAL guard of the parser and the mode table: the homing procedure
        is driven directly (see homing_session).
        """
        self.check_homing_modes()

    def test_homing_mode_mutations_are_detected(self):
        """INDEPENDENT: the pp-region-4 homing mutants and two parser mutants fail the guard."""
        cases = {
            'mode 2 G91 leaks': ((2,), mutate(
                "        { sHomeline}\n        iAbsincmode = 90\n        change(iAbsincmode) = true\n    endif\n    if iHomingmode eq 3",
                "        { sHomeline}\n    endif\n    if iHomingmode eq 3"), 'G91 leaks'),
            'mode 6 G91 leaks': ((6,), mutate(
                "        { sHomeline}\n        iAbsincmode = 90\n        change(iAbsincmode) = true\n    endif\n    if iHomingmode eq 7",
                "        { sHomeline}\n    endif\n    if iHomingmode eq 7"), 'G91 leaks'),
            'mode 3 forces the work offset': ((3,), mutate(
                '        if iHomingmode eq 3\n            change(iWorkOffset) = false',
                '        if iHomingmode eq 30\n            change(iWorkOffset) = false'), 're-output'),
            'G53 work offset not restored': ((3, 4), mutate('        iWorkOffset = sav_iWorkOffset\n', ''),
                                             'G53 homing|re-output'),
            'homing line separator ignored': ((8,), mutate("p1 = instr(s1,';')", 'p1 = 0'), 'X/Y homing line missing'),
            'mode 8 homing line joins the previous block': ((8,), mutate(
                '        {nb,cHomep,sHomeline}', '        {cHomep,sHomeline}'), 'Z alone'),
        }
        for label, (modes, source, match) in cases.items():
            with self.subTest(mutant=label):
                assert_detected(self, lambda src, m=modes: self.check_homing_modes(src, m), source, label, match)

    @known_defect('PP-040', match='homing lines merged|in a comment')
    def test_homing_lines_without_prep_string(self):
        """INDEPENDENT: homing format doc '[integer:][Prepstr :][AxisStr1 ;][AxisStrN]'.

        Prepstr is optional, and ';' starts a comment on Sinumerik. A
        two-line definition without the prep colon must still give a Z block
        and a separate X/Y block, with nothing hidden in a comment. STRUCTURAL:
        the homing procedure is driven directly (see homing_session). No
        homing output at all, or a first block that does not home Z, is a
        precondition failure (match=).
        """
        s, before, after = homing_session('8:G75 Z1=0. ;8:G75 Y1=0 X1=0')
        homing = parse_blocks(s.log[before][1])
        shown = listing(homing)
        self.assertTrue(homing and homing[0].homing_axes == {'Z'},
                        f'precondition: the first homing block homes Z:\n{shown}')
        self.assertEqual([block.homing_axes for block in homing], [{'Z'}, {'X', 'Y'}],
                         f'homing lines merged:\n{shown}')
        self.assertEqual([block.comment for block in homing if block.comment is not None], [],
                         f'homing text ends up in a comment:\n{shown}')

    @known_defect('PP-041', match='G53 homing left machine coordinates')
    def test_g53_homing_stays_in_machine_coordinates_for_every_offset_mode(self):
        """INDEPENDENT: homing mode doc (3/4 = G53, machine coordinates) for every iWorkOffsetmode.

        The work-offset style option ('1=G54, 2=E1, 3=G54.1 P1') must not turn
        the G53 machine-coordinate homing into a motion in work coordinates
        (with iWorkOffsetmode=2 the PP prints cWo+0, i.e. 'G0 Z0'). The oracle
        is one block carrying G53; a G0 next to the G53 is valid Sinumerik and
        allowed. STRUCTURAL: the homing procedure is driven directly with G54
        active (see homing_session). The shipped iWorkOffsetmode=1 must give the
        G53 block (precondition, not a reproduction: match=).
        """
        failures = []
        for mode in (3, 4):
            for offset_mode in (1, 2, 3):
                s = Session(options=dict(iWorkOffsetmode=offset_mode))
                blocks = parse_blocks(s.ev('usr_prep_home_axis', sHomestr=f'{mode}::Z0', iWorkoffset=54))
                if len(blocks) != 1 or 53 not in blocks[0].g:
                    failures.append((mode, offset_mode, [block.raw for block in blocks]))
        self.assertEqual([failure for failure in failures if failure[1] == 1], [],
                         'precondition: G53 homing with the shipped iWorkOffsetmode=1')
        self.assertEqual(failures, [], 'G53 homing left machine coordinates')

    @known_defect('PP-042', match='after mode-7 homing')
    def test_homing_mode_7_keeps_the_active_work_offset(self):
        """INDEPENDENT: Sinumerik G54..G57/G505.. are modal; homing must not change the active offset.

        With G55 active (iWorkOffset_Method=1, CoordSys '55'), a homing defined
        with mode 7 ('G90 G54') must leave G55 in effect for the next
        positioning move (or restore it). Mode 7 hard-codes G54 and never
        re-outputs the active offset. STRUCTURAL: the homing procedure is
        driven directly (see homing_session).
        """
        s, before, after = homing_session('7::Z0;7::X0 Y0', vmid=dict(iWorkOffset_Method=1), home_user_name='55')
        program = s.blocks()
        replayed = replay(program)
        homing_start = len(program) - len(s.blocks(before))
        self.assertEqual(state_before(replayed, homing_start).work_offset, 55,
                         f'precondition: G55 active before the homing:\n{listing(program)}')
        position = len(program) - len(s.blocks(after))
        self.assertEqual(replayed[position][1].work_offset, 55,
                         f'work offset in effect after mode-7 homing:\n{listing(s.blocks(before))}')


# ---------------------------------------------------------------------------
# First job under the persisting change-flag policy (ENGINE-001)
# ---------------------------------------------------------------------------

def persisting_first_job():
    s = Session(flags='persist')
    s.first_tool(flood_coolant=1)
    s.cut(10, 20, 5, -1)
    return s


class FirstJobPersistingFlagTests(unittest.TestCase):
    @known_defect('PP-054', facet='coolant-burst', match='coolant in effect at the first cut')
    def test_flood_coolant_is_not_cancelled_before_the_first_cut(self):
        """INDEPENDENT: M9 switches every coolant channel off on the 828D (modal replay).

        The job requests flood coolant (flood_coolant=1, all other channels 0),
        so flood (M8) must be active at the first feed move. UNVERIFIED: only
        under Session(flags='persist'), i.e. if SolidCAM keeps the change flags
        raised by the @usr_init_gmstates assignments (ENGINE-001); then
        @usr_coolant_output prints M8 followed by seven M9. The clear policy
        prints only M8. An engine-semantics probe (pp-weird-hunter-06), not a
        confirmed PP bug. The unemulated skipline switch (ENGINE-002) that
        @usr_coolant_output sets is also involved (history-misc-15), but joining
        the blocks would still put M9 after M8, so the replayed result does not
        depend on it. A missing first cut is a precondition failure, not a
        reproduction (match=).
        """
        s = persisting_first_job()
        blocks = s.blocks()
        replayed = replay(blocks)
        cut = index_of(blocks, lambda b: b.is_motion and 1 in b.g)
        self.assertGreater(cut, 0, f'precondition: no feed move in the first job:\n{listing(blocks)}')
        self.assertEqual(sorted(replayed[cut][1].coolant), [8],
                         f'coolant in effect at the first cut:\n{listing(blocks[:cut + 1])}')

    @known_defect('PP-054', facet='g187-default')
    def test_no_fanuc_g187_in_a_default_program(self):
        """INDEPENDENT: the 828D G-function set of the repository's Vericut control (no G187).

        With the VMID default job parameters (iG187_P=0, nG187_E=0) a first job
        must emit only Sinumerik G functions. UNVERIFIED: only under
        Session(flags='persist') (ENGINE-001): @usr_init_gmstates assigns
        iG187_P_gpp = 2 and, if that flag persists, @usr_HSM_mode prints
        'G187 P2'. The clear policy prints nothing.
        """
        defined = g_function_whitelist()
        blocks = persisting_first_job().blocks()
        foreign = sorted({code for block in blocks for code in block.g if code not in defined})
        self.assertEqual(foreign, [], f'non-828D G functions in a default first job:\n{listing(blocks)}')


if __name__ == '__main__':
    unittest.main()
