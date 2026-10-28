"""Arcs, tool radius compensation and plane modality of Gmill_540v_4x.gpp
(@usr_arc, @usr_arc_math, @usr_arc_check, @compensation, @machine_plane,
@relative_mode/@absolute_mode).

Area D. Tests drive a SolidCAM-like Session after the first tool change, put
the tool at the arc start with a feed move and judge the emitted G2/G3 block
the way a Sinumerik 828D executes it:
* support.nc.arc_sweep_degrees is the DIN 66025 / Siemens sweep oracle: G17
  is X/Y viewed from +Z, G18 is Z/X viewed from +Y (abscissa Z, ordinate X),
  G19 is Y/Z viewed from +X; I/J/K are incremental unless written I=AC(..);
* plane (G17/G18/G19) and TRC (G40/G41/G42) states come from support.modal.replay.

ZX (G18) orientation was registered as PP-003. The owner's fix (5408e5c) stops
the post with a POST ERROR on every ZX arc until SolidCAM's arc_direction
convention is verified, so the arc guards below run in XY and YZ, and the former
PP-003 test checks that a ZX arc stops the post (the abort mechanics are in
tests/test_zx_arc_guard.py). The template's other arc modes (absolute plain
I/J, R word; PP-022) were removed.

TRC: PP-019, PP-020 and PP-021 are fixed (b999f65, 264be29, 88695c9, 9767011);
their former canonical tests are regression guards (@covers).

Event order caveat: every PP-019/PP-020 test assumes SolidCAM delivers
@compensation directly before the rapid/arc it names. That order is UNVERIFIED
(no captured trace contains a compensation event).
"""
import json
import math
import unittest

from pp_tests.engine import UnsupportedGPPL
from support import (DRILL_DEFAULTS, FIXTURES, Session, arc_center, arc_sweep_degrees, assert_detected,
                     covers, mutate, parse_blocks, replay, state_before)

# plane: (abscissa, ordinate, applicate, SolidCAM event, G code), DIN 66025 / Siemens 828D.
PLANES = {
    'xy': ('X', 'Y', 'Z', 'arc', 17),
    'zx': ('Z', 'X', 'Y', 'arc_zx', 18),
    'yz': ('Y', 'Z', 'X', 'arc_yz', 19),
}
CENTER_WORDS = {'X': 'I', 'Y': 'J', 'Z': 'K'}
# Coarsest coordinate format in effect after the first tool change is zpos_f '5.4'
# (PP-006): rounding moves a written coordinate by at most 5e-5 mm.
COORDINATE_TOLERANCE = 5.1e-5
# 5e-5 mm on a 10 mm radius is 3e-4 deg; 0.01 deg separates rounding from a wrong arc.
SWEEP_TOLERANCE = 0.01


_JOB_TEMPLATES = {}


def job_session(source=None, options=None, **cam):
    """Session after the program start and the first tool change (tool 1).

    Built once per (source, options, cam) and forked, because the arc guards and
    their mutant runs need hundreds of identical job starts.
    """
    key = (source, tuple(sorted((options or {}).items())), tuple(sorted(cam.items())))
    template = _JOB_TEMPLATES.get(key)
    if template is None:
        template = Session(source=source, options=options, **cam)
        template.first_tool()
        _JOB_TEMPLATES[key] = template
    return template.fork()


def raw(pairs):
    return [block.raw for block, _ in pairs]


def position(session, point):
    """Feed move to point {'X','Y','Z'} (all three flagged)."""
    session.ev('line_5x', ('xpos', 'ypos', 'zpos', 'feed'), feed=200, feed_type='feed_rate',
               xpos=point['X'], ypos=point['Y'], zpos=point['Z'])


def emit_arc(session, plane, direction, size, start, center, end):
    """Deliver one SolidCAM arc event from start around center to the CAD end point.

    start/center/end are {'X','Y','Z'}; the tool must already be at start. The axes
    whose end differs from start are flagged as changed. Returns the event mark.
    """
    abscissa, ordinate, _, event_name, _ = PLANES[plane]
    values = dict(arc_plane=plane, arc_direction=direction, arc_size=size,
                  radius=math.hypot(start[abscissa] - center[abscissa], start[ordinate] - center[ordinate]))
    for axis in 'XYZ':
        key = axis.lower()
        values.update({key + 'start': start[axis], key + 'center': center[axis],
                       key + 'center_rel': center[axis] - start[axis], key + 'pos': end[axis]})
    changed = [axis.lower() + 'pos' for axis in 'XYZ' if end[axis] != start[axis]]
    mark = session.mark()
    session.ev(event_name, changed, **values)
    return mark


def emit_valid_arc(testcase, session, *args):
    """emit_arc for an arc the oracle considers valid, in a REGRESSION test: a PP stop
    ('POST ERROR', e.g. 'ARC end mismatch') becomes an AssertionError, so a reverted arc
    check is reported as a failure, not as an engine error. Known-defect tests keep
    emit_arc: there a setup stop must stay an error and never count as a reproduction."""
    try:
        return emit_arc(session, *args)
    except UnsupportedGPPL as exc:
        if 'POST ERROR' in str(exc):
            testcase.fail(f'the PP stopped on a valid arc: {exc}')
        raise


def arc_result(testcase, session, mark):
    """(G2/G3 block, modal state before it, modal state after it) of the arc event."""
    replayed = replay(session.text())
    first = len(replayed) - len(parse_blocks(session.text(mark)))
    last = len(replayed) - len(parse_blocks(session.text(mark + 1)))
    arcs = [index for index in range(first, last) if set(replayed[index][0].g) & {2, 3}]
    testcase.assertEqual(len(arcs), 1, f'expected one G2/G3 block: {raw(replayed[first:last])}')
    index = arcs[0]
    return replayed[index][0], state_before(replayed, index), replayed[index][1]


def in_plane(plane, pair, applicate):
    """{'X','Y','Z'} point from (abscissa, ordinate) and the applicate value."""
    abscissa, ordinate, normal = PLANES[plane][:3]
    return {abscissa: pair[0], ordinate: pair[1], normal: applicate}


class ArcSweepConventionTests(unittest.TestCase):
    """Convention-independent G2/G3 check (pp-weird-hunter-02, history-misc-04).

    For each CAM label and size both candidate CAD end points are fed; the PP must
    accept exactly one (dc916d7 end-point check) and the control must sweep the
    CAM arc_size for the block it writes, whatever label convention SolidCAM uses.
    """

    CENTER = {'X': 3.0, 'Y': -2.0, 'Z': 1.0}

    def accepted_arc(self, plane, direction, size, source=None):
        abscissa, ordinate = PLANES[plane][:2]
        start = dict(self.CENTER)
        start[abscissa] += 10
        accepted = []
        for sign in (1, -1):
            end = dict(self.CENTER)
            end[abscissa] += 10 * math.cos(math.radians(sign * size))
            end[ordinate] += 10 * math.sin(math.radians(sign * size))
            session = job_session(source)
            position(session, start)
            try:
                mark = emit_arc(session, plane, direction, size, start, self.CENTER, end)
            except UnsupportedGPPL as exc:
                if 'ARC end mismatch' not in str(exc):
                    raise
                continue
            accepted.append(arc_result(self, session, mark))
        self.assertEqual(len(accepted), 1, f'{plane} {direction} {size}: expected exactly one accepted end point')
        return accepted[0]

    def sweep_errors(self, planes, source=None):
        errors = []
        for plane in planes:
            for direction in ('ccw', 'cw'):
                for size in (45, 90, 135):
                    block, before, _ = self.accepted_arc(plane, direction, size, source)
                    sweep = arc_sweep_degrees(plane, before.xyz(), block)
                    if abs(sweep - size) > SWEEP_TOLERANCE:
                        errors.append(f'{plane} {direction} {size}: control sweeps {sweep:.3f} deg for {block.raw!r}')
        return errors

    def test_pin_xy_yz_arcs_sweep_cam_angle_on_control(self):
        """INDEPENDENT: DIN 66025 / Siemens 828D circle direction (G17 viewed from +Z, G19
        from +X): for XY and YZ arcs of 45/90/135 deg, both labels, the block the PP
        writes must sweep exactly the CAM arc_size on the control."""
        errors = self.sweep_errors(('xy', 'yz'))
        self.assertEqual(errors, [])

    def test_pin_xy_yz_arc_sweep_detects_mutation(self):
        """INDEPENDENT: swapping G3/G2 for the CCW label in @usr_arc_math must make the XY/YZ
        sweep check fail with AssertionError."""
        mutant = mutate('    if arc_direction eq CCW then\n        iMotionmode = 3\n    else\n        iMotionmode = 2',
                        '    if arc_direction eq CCW then\n        iMotionmode = 2\n    else\n        iMotionmode = 3')
        assert_detected(self, lambda source: self.assertEqual(self.sweep_errors(('xy', 'yz'), source), []),
                        mutant, 'G2/G3 swapped')

    @covers('PP-003')
    def test_zx_arc_stops_the_post(self):
        """INDEPENDENT: DIN 66025 / Sinumerik G18 is viewed from +Y with Z as abscissa and X
        as ordinate, so G3 turns Z->X, while @usr_arc_math rotates X->Z for a positive
        angle; which end point SolidCAM sends for a CCW label is UNVERIFIED (VMID
        ArcDirectionBy="0"). Owner decision (5408e5c, PP-003): until that is verified a ZX
        arc must not be posted at all. For both labels, three sizes and both candidate CAD
        end points the post must stop with the ZX POST ERROR and no G2/G3 or G18 block may
        reach the NC program. Regression guard of PP-003; the input/abort mechanics are
        tests/test_zx_arc_guard.py."""
        abscissa, ordinate = PLANES['zx'][:2]
        start = dict(self.CENTER)
        start[abscissa] += 10
        for direction in ('ccw', 'cw'):
            for size in (45, 90, 135):
                for sign in (1, -1):
                    end = dict(self.CENTER)
                    end[abscissa] += 10 * math.cos(math.radians(sign * size))
                    end[ordinate] += 10 * math.sin(math.radians(sign * size))
                    label = f'zx {direction} {size} end {sign:+d}'
                    with self.subTest(label):
                        session = job_session()
                        position(session, start)
                        first = len(session.engine.output)
                        with self.assertRaisesRegex(UnsupportedGPPL, 'POST ERROR: ZX arc direction is unverified',
                                                    msg=label):
                            emit_arc(session, 'zx', direction, size, start, self.CENTER, end)
                        written = parse_blocks(''.join(session.engine.output[first:]))
                        self.assertEqual([block.raw for block in written if set(block.g) & {2, 3, 18}], [], label)


# Off-axis vectors (TSR-07: every fixture case starts on the +abscissa axis, so the
# ordinate terms of the rotation were untested). (abscissa, ordinate) in DIN order.
# Semicircles end at 2*center - start for either direction, so they run in all three
# planes; quarter arcs only where the PP rotation sense is DIN-verified (G17, G19).
OFF_AXIS_CASES = [
    dict(name='semicircle_off_axis_ccw', size=180, direction='ccw', start=(6, 8), center=(0, 0), end=(-6, -8)),
    dict(name='semicircle_off_axis_cw', size=180, direction='cw', start=(6, 8), center=(0, 0), end=(-6, -8)),
    dict(name='semicircle_offset_center_ccw', size=180, direction='ccw', start=(5, 1), center=(2, 5), end=(-1, 9)),
    dict(name='semicircle_offset_center_cw', size=180, direction='cw', start=(5, 1), center=(2, 5), end=(-1, 9)),
    dict(name='quarter_off_axis_ccw', size=90, direction='ccw', start=(6, 8), center=(0, 0), end=(-8, 6),
         planes=('xy', 'yz')),
    dict(name='quarter_off_axis_cw', size=90, direction='cw', start=(6, 8), center=(0, 0), end=(8, -6),
         planes=('xy', 'yz')),
    dict(name='quarter_offset_center_ccw', size=90, direction='ccw', start=(5, 1), center=(2, 5), end=(6, 8),
         planes=('xy', 'yz')),
    # A CAD end point off the circle in the NEGATIVE direction of each in-plane axis aborts too.
    dict(name='negative_abscissa_mismatch_aborts', size=180, direction='ccw', start=(6, 8), center=(0, 0),
         end=(-6, -8), cad_delta=(-0.0011, 0), error=True),
    dict(name='negative_ordinate_mismatch_aborts', size=180, direction='ccw', start=(6, 8), center=(0, 0),
         end=(-6, -8), cad_delta=(0, -0.0011), error=True),
    dict(name='negative_roundoff_is_corrected', size=180, direction='cw', start=(6, 8), center=(0, 0),
         end=(-6, -8), cad_delta=(-0.0009, -0.0009)),
]


def fixture_cases():
    """fixtures/ambiguous_arcs.json cases as XY/YZ arc cases (ZX orientation is PP-003)."""
    fixture = json.loads((FIXTURES / 'ambiguous_arcs.json').read_text())
    return [dict(case, planes=('xy', 'yz')) for case in fixture['cases']]


class ArcGuardTests(unittest.TestCase):
    """dc916d7 ('Arcs must be handled mathematically in post') regression guards."""

    def assert_arc_case(self, case, plane, source=None):
        abscissa, ordinate, normal, _, code = PLANES[plane]
        delta = case.get('cad_delta', (0, 0))
        start = in_plane(plane, case['start'], 2)
        center = in_plane(plane, case['center'], 2)
        true_end = in_plane(plane, case['end'], -7)   # helical: the applicate end comes from CAD
        cad_end = in_plane(plane, (case['end'][0] + delta[0], case['end'][1] + delta[1]), -7)
        label = f"{case['name']} {plane}"
        session = job_session(source)
        position(session, start)
        if case.get('error'):
            error = case['error'] if isinstance(case['error'], str) else 'ARC end mismatch'
            with self.assertRaisesRegex(UnsupportedGPPL, 'POST ERROR: ' + error, msg=label):
                emit_arc(session, plane, case['direction'], case['size'], start, center, cad_end)
            return
        try:
            mark = emit_arc(session, plane, case['direction'], case['size'], start, center, cad_end)
        except UnsupportedGPPL as exc:
            if 'POST ERROR' in str(exc):
                self.fail(f'{label}: the PP aborted an arc whose CAD end point is on the circle: {exc}')
            raise
        block, before, after = arc_result(self, session, mark)
        self.assertEqual(after.plane, code, f'{label}: plane active at {block.raw!r}')
        sweep = arc_sweep_degrees(plane, before.xyz(), block)
        self.assertAlmostEqual(sweep, case['size'] % 360, delta=SWEEP_TOLERANCE, msg=f'{label}: {block.raw!r}')
        self.assertIn(3 if case['direction'] == 'ccw' else 2, block.g, f'{label}: {block.raw!r}')
        for axis in 'XYZ':
            self.assertAlmostEqual(after.xyz()[axis], true_end[axis], delta=COORDINATE_TOLERANCE,
                                   msg=f'{label} {axis}: {block.raw!r}')
        words = {word.address: (word.mode, word.value) for word in block.words
                 if word.address in ('I', 'J', 'K', 'R', 'CR')}
        expected = {CENTER_WORDS[axis]: (None, center[axis] - start[axis]) for axis in (abscissa, ordinate)}
        self.assertEqual(words, expected, f'{label}: incremental centre words expected in {block.raw!r}')

    def run_cases(self, cases, source=None, subtests=True):
        # XY and YZ only: every ZX arc stops the post since 5408e5c (test_zx_arc_stops_the_post).
        for case in cases:
            for plane in case.get('planes', ('xy', 'yz')):
                if not subtests:   # mutant runs: the first AssertionError propagates
                    self.assert_arc_case(case, plane, source)
                    continue
                with self.subTest(case=case['name'], plane=plane):
                    self.assert_arc_case(case, plane, source)

    @covers('ENGINE-009')
    def test_off_axis_center_words_and_negative_mismatch(self):
        """INDEPENDENT: geometry and Sinumerik words, in XY (G17) and YZ (G19); ZX arcs stop
        the post since 5408e5c (test_zx_arc_stops_the_post). A semicircle ends at
        2*center - start for either direction; quarter arcs rotate +abscissa -> +ordinate
        for CCW (DIN 66025); I/J/K are the centre relative to the start point (incremental,
        iArcmode=2); dc916d7 aborts on a CAD end point more than 0.001 off the circle in
        either direction of any axis and writes the corrected end point within tolerance.
        Starts lie off the abscissa (absorbs the TSR off-axis test). The abort is observed
        as the engine exception at the GPPL `input` line (ENGINE-009)."""
        self.run_cases(OFF_AXIS_CASES)

    # ZX mutants (dc916d7's ZX K-word revert, ZX K sign, ZX orthogonal axis) are gone:
    # since 5408e5c the ZX output and rotation lines run only after the ZX stop, so
    # they are unreachable and no behaviour test can see them.
    MUTANTS = {
        'no_end_point_commit': ('    xpos = calculated_xpos\n    ypos = calculated_ypos\n    zpos = calculated_zpos\n', ''),
        'no_mismatch_check': ('    call @usr_arc_check(dx, dy, dz)\n', ''),
        'xy_rotation_flipped': ('        rx = vx * c - vy * s\n        ry = vx * s + vy * c\n',
                                '        rx = vx * c + vy * s\n        ry = -vx * s + vy * c\n'),
        'yz_rotation_flipped': ('        ry = vy * c - vz * s\n        rz = vy * s + vz * c\n',
                                '        ry = vy * c + vz * s\n        rz = -vy * s + vz * c\n'),
        'xy_ordinate_term_sign': ('        ry = vx * s + vy * c\n', '        ry = vx * s - vy * c\n'),
        'center_y_sign': ('    cy = ystart + ycenter_rel\n', '    cy = ystart - ycenter_rel\n'),
        'center_z_sign': ('    cz = zstart + zcenter_rel\n', '    cz = zstart - zcenter_rel\n'),
        'cw_sign_dropped': ('        angle_deg = -angle_deg\n', '        angle_deg = angle_deg\n'),
        'xy_orthogonal_from_start': ('        calculated_zpos = zpos\n', '        calculated_zpos = zstart\n'),
        'yz_orthogonal_from_start': ('        calculated_xpos = xpos\n', '        calculated_xpos = xstart\n'),
        'dx_signed_reversed': ('dx = abs(calculated_xpos - xpos)', 'dx = (xpos - calculated_xpos)'),
        'dy_signed_reversed': ('dy = abs(calculated_ypos - ypos)', 'dy = (ypos - calculated_ypos)'),
        'dz_signed_reversed': ('dz = abs(calculated_zpos - zpos)', 'dz = (zpos - calculated_zpos)'),
        'xy_j_rel_sign': ("{'I'xcenter_rel ' ', 'J'ycenter_rel ' '}", "{'I'xcenter_rel ' ', 'J'(-ycenter_rel) ' '}"),
        'yz_k_rel_sign': ("{'J'ycenter_rel ' ', 'K'zcenter_rel ' '}", "{'J'ycenter_rel ' ', 'K'(-zcenter_rel) ' '}"),
        'check_or_to_and': ('if dx gt tolerance or dy gt tolerance or dz gt tolerance then',
                            'if dx gt tolerance and dy gt tolerance and dz gt tolerance then'),
        'no_chord_check': ('    call @usr_arc_chord_check(du, dv)\n', ''),
        'yz_chord_in_xy': ('    if iMplane eq 19 then\n        du = calculated_ypos - ystart\n',
                           '    if false then\n        du = calculated_ypos - ystart\n'),
        'chord_limit_looser': ('du * du + dv * dv < 0.00000001', 'du * du + dv * dv < 0.000000001'),
        'chord_limit_tighter': ('du * du + dv * dv < 0.00000001', 'du * du + dv * dv < 0.0000001'),
        'full_circle_not_exempt': ('    if arc_size < 360 and du * du', '    if du * du'),
    }

    def test_arc_math_mutants_are_detected_by_assertions(self):
        """INDEPENDENT: every in-memory mutant of @usr_arc_math/@usr_arc/@usr_arc_check below
        (dc916d7 reverts, rotation/sign/centre/orthogonal-axis/tolerance mutants) must make
        one of the geometric oracles above raise AssertionError, never an interpreter
        error. ZX mutants are absent: the ZX lines are unreachable behind the ZX stop."""
        cases = OFF_AXIS_CASES + fixture_cases()
        for name, (old, new) in self.MUTANTS.items():
            with self.subTest(mutant=name):
                assert_detected(self, lambda source: self.run_cases(cases, source, subtests=False),
                                mutate(old, new), name)

    def check_configured_arc_mode(self, source=None):
        session = job_session(source)
        case = OFF_AXIS_CASES[6]   # quarter, start (5, 1), center (2, 5)
        start, center = in_plane('xy', case['start'], 2), in_plane('xy', case['center'], 2)
        position(session, start)
        mark = emit_valid_arc(self, session, 'xy', case['direction'], case['size'], start, center,
                              in_plane('xy', case['end'], 2))
        block, before, _ = arc_result(self, session, mark)
        self.assertEqual([word.raw for word in block.words if word.address in ('R', 'CR')], [], block.raw)
        self.assertEqual({word.address: (word.mode, word.value) for word in block.words
                          if word.address in ('I', 'J', 'K')},
                         {'I': (None, -3), 'J': (None, 4)}, block.raw)
        self.assertEqual(arc_center('xy', before.xyz(), block), (2, 5), block.raw)

    def test_configured_arc_mode_emits_sinumerik_incremental_ijk(self):
        """INDEPENDENT: Sinumerik 828D reads plain I/J/K as incremental centre offsets
        (absolute needs I=AC(..)) and writes the radius as CR= (R is an arithmetic
        parameter). @usr_arc must produce incremental I/J
        and no radius word (absorbs efc test_configured_arc_mode_is_sinumerik_incremental_ijk)."""
        self.check_configured_arc_mode()

    def test_non_sinumerik_arc_words_are_detected(self):
        """INDEPENDENT: @usr_arc writing the absolute centre as plain I/J (the removed
        iArcmode 1) or an R word (the removed modes 3/4) must make the configured-mode check
        fail with AssertionError."""
        xy_centre = "        {'I'xcenter_rel ' ', 'J'ycenter_rel ' '}\n"
        mutants = {'absolute I/J': "        {'I'xcenter ' ', 'J'ycenter ' '}\n",
                   'R word': "        {'I'xcenter_rel ' ', 'J'ycenter_rel ' ', 'R'radius ' '}\n"}
        for label, words in mutants.items():
            with self.subTest(label):
                assert_detected(self, self.check_configured_arc_mode, mutate(xy_centre, words), label)

    def test_configured_output_precision_keeps_end_point_on_circle(self):
        """INDEPENDENT: dc916d7 raised XYZ output to 5 decimals so emitted arc end points lie
        on the circle (VMID MovementPrecision=5). After @init_post a 30 deg XY arc must end
        on the circle of its start point within 1e-5 mm (5-decimal rounding of X/Y bounds the
        radial error by about 0.71e-5 mm)."""
        session = job_session()
        start = {'X': 10, 'Y': 0, 'Z': 0}
        end = {'X': 10 * math.cos(math.radians(30)), 'Y': 5.0, 'Z': 0}
        position(session, start)
        mark = emit_valid_arc(self, session, 'xy', 'ccw', 30, start, {'X': 0, 'Y': 0, 'Z': 0}, end)
        block, before, after = arc_result(self, session, mark)
        cx, cy = arc_center('xy', before.xyz(), block)
        radial_error = abs(math.hypot(after.xyz()['X'] - cx, after.xyz()['Y'] - cy)
                           - math.hypot(before.xyz()['X'] - cx, before.xyz()['Y'] - cy))
        self.assertLessEqual(radial_error, 1e-5, block.raw)


class RemovedArcModeTests(unittest.TestCase):
    """The template's arc modes 1, 3 and 4 (absolute centre as plain I/J, R word) are removed (PP-022).

    Oracle: Siemens 828D programming manual (plain I/J/K are incremental from the start point, an
    absolute centre needs I=AC(..), the radius word is CR=, a bare R is an arithmetic parameter); the
    machine's Vericut control (sin840d_special.ctl) defines 'CR=' as 'CIRCLES: Circle radius'.
    """

    START, CENTER = {'X': 12, 'Y': 23, 'Z': -2}, {'X': 2, 'Y': 23, 'Z': -2}

    def arc_block(self, mode, size):
        session = job_session(options=dict(iArcmode=mode))
        angle = math.radians(size)
        end = {'X': 2 + 10 * math.cos(angle), 'Y': 23 + 10 * math.sin(angle), 'Z': -2}
        position(session, self.START)
        mark = emit_arc(session, 'xy', 'ccw', size, self.START, self.CENTER, end)
        block, before, _ = arc_result(self, session, mark)
        return block, before

    @covers('PP-022')
    def test_leftover_arc_mode_setting_posts_the_sinumerik_centre(self):
        """INDEPENDENT: the Sinumerik centre and radius rules above. A leftover iArcmode 1, 3 or 4
        setting (the removed modes printed the absolute centre as plain I/J, also for full circles,
        and R for the radius) must give the control the CAM centre (2, 23) for a 90 deg arc and a
        full circle, with no R or CR word. Regression guard of all three PP-022 facets."""
        problems = {}
        for mode in (1, 3, 4):
            for size in (90, 360):
                block, before = self.arc_block(mode, size)
                radius = [word.raw for word in block.words if word.address in ('R', 'CR')]
                if arc_center('xy', before.xyz(), block) != (2, 23) or radius:
                    problems[(mode, size)] = block.raw
        self.assertEqual(problems, {}, 'arc words are not the Sinumerik incremental centre')


def compensated_job(source=None):
    """Tool 1 positioned at X12 Y13 Z-2 (in the material, G1, no compensation yet)."""
    session = job_session(source)
    session.ev('move_5x', ('xpos', 'ypos', 'zpos'), xpos=12, ypos=13, zpos=5)
    session.ev('line_5x', ('zpos', 'feed'), zpos=-2, feed=300, feed_type='feed_rate')
    return session


def xy_arc(session, start, center_x, size=90):
    """CCW XY arc from start {'X','Y'} around (center_x, start Y) at Z-2."""
    begin = {'X': start[0], 'Y': start[1], 'Z': -2}
    radius = start[0] - center_x
    angle = math.radians(size)
    end = {'X': center_x + radius * math.cos(angle), 'Y': start[1] + radius * math.sin(angle), 'Z': -2}
    return emit_arc(session, 'xy', 'ccw', size, begin, {'X': center_x, 'Y': start[1], 'Z': -2}, end)


TRC_ON_ARC_STOP = 'POST ERROR: Cutter compensation change on an arc'


def post_error_stop(exc):
    """True for a deliberate fail-safe POST ERROR stop (accepted for a TRC change before a rapid).

    'ARC end mismatch' is excluded: the arcs of these scenarios are geometrically valid,
    so that stop is an arc-math regression and must surface as an error.
    """
    message = str(exc)
    return 'POST ERROR' in message and 'ARC end mismatch' not in message


def stopped_arc(testcase, session, start, center_x):
    """Deliver an XY arc that must stop the post with the TRC-on-arc POST ERROR (b999f65).

    Returns the blocks the post wrote for the arc event before it stopped.
    """
    first = len(session.engine.output)
    with testcase.assertRaisesRegex(UnsupportedGPPL, TRC_ON_ARC_STOP):
        xy_arc(session, start, center_x)
    return parse_blocks(''.join(session.engine.output[first:]))


class CompensationTests(unittest.TestCase):
    """Tool radius compensation (TRC) selection and placement."""

    def test_compensation_sides_select_g41_g42_g40_on_linear_moves(self):
        """INDEPENDENT: ISO 6983 / Sinumerik: tool left of the contour = G41, right = G42,
        off = G40; a change written on the following G1 move is a valid linear
        selection/deselection block (TSR SmallBranchRegressions, left was never called)."""
        session = compensated_job()
        for side, y, code in (('comp_left', 20, 41), ('comp_right', 25, 42), ('comp_off', 30, 40), ('comp_left', 35, 41)):
            session.ev('compensation', side=side)
            self.assertEqual(session.state['idiametercomp'], code, side)
            mark = session.mark()
            session.ev('line', ('ypos',), ypos=y)
            pairs = session.event_replay(mark)
            self.assertEqual(len(pairs), 1, raw(pairs))
            block, state = pairs[0]
            self.assertIn(code, block.g, f'{side}: {block.raw!r}')
            self.assertEqual((state.trc, state.motion), (code, 1), f'{side}: {block.raw!r}')

    @covers('PP-020')
    def test_compensation_not_activated_in_circular_block(self):
        """INDEPENDENT: Sinumerik 828D selects TRC (G41/G42) only in a G0/G1 block; G41/G42
        in a G2/G3 block raises alarm 10753. Owner decision (b999f65): a compensation change
        delivered right before an arc stops the post with a POST ERROR ('use a linear
        lead-in/lead-out'), so no circular block may carry G41/G42 and nothing of the arc
        reaches the NC program. Regression guard of PP-020 facet activation. UNVERIFIED
        event order: assumes SolidCAM delivers @compensation directly before an @arc
        lead-in (VMID CompensationNeedFirstLine="0"; 2aa6df0 removed the @usr_line
        lookahead)."""
        session = compensated_job()
        session.ev('compensation', side='comp_left')
        written = stopped_arc(self, session, (12, 13), 2)
        self.assertEqual([block.raw for block in written if set(block.g) & {2, 3, 41, 42}], [],
                         'arc or TRC block written before the stop')

    @covers('PP-020')
    def test_compensation_not_deactivated_in_circular_block(self):
        """INDEPENDENT: Sinumerik 828D deselects TRC (G40) only in a G0/G1 block; G40 in a
        G2/G3 block raises alarm 10754. Scenario: the arc lead-out case behind 2aa6df0 (G41
        active, @compensation off, then the lead-out @arc). Owner decision (b999f65): the
        post stops with a POST ERROR instead of writing G40 into the arc. Regression guard
        of PP-020 facet deactivation. UNVERIFIED event order: assumes SolidCAM delivers
        @compensation(off) directly before the lead-out arc."""
        session = compensated_job()
        session.ev('compensation', side='comp_left')
        session.ev('line', ('ypos',), ypos=23)
        session.ev('compensation', side='comp_off')
        written = stopped_arc(self, session, (12, 23), 2)
        self.assertEqual([block.raw for block in written if set(block.g) & {2, 3, 40}], [],
                         'arc or G40 block written before the stop')

    @covers('PP-019')
    def test_compensation_off_emitted_on_following_rapid(self):
        """INDEPENDENT: TRC is modal and the GPP comment in @usr_line says 'CAM emits
        @compensation before the move where it must become active', so a G40 delivered
        before a retract rapid must be in effect at the end of that rapid. Sinumerik 828D
        deselects TRC with G40 only in a G0/G1 block that programs an axis of the working
        plane (Siemens programming manual, TRC selection/deselection), so the G40 block must
        carry X or Y, and no X/Y motion after the COMP_OFF may run under G41. Before b999f65
        the G40 waited for the next feed move; 264be29 waited for the next X/Y block; 2f5b759
        writes 'G0 G40 X.. Y.. Z50' on the Z-only retract. Regression guard of PP-019 facet
        off-before-rapid. UNVERIFIED event order: assumes SolidCAM emits @compensation(off)
        immediately before the rapid (e.g. lead-out 'None')."""
        session = compensated_job()
        session.ev('compensation', side='comp_left')
        session.ev('line', ('ypos',), ypos=23)
        session.ev('line', ('xpos',), xpos=40)
        session.ev('compensation', side='comp_off')
        mark = session.mark()
        session.ev('rapid_move', ('zpos',), zpos=50)
        retract = session.mark()
        session.ev('rapid_move', ('xpos', 'ypos'), xpos=0, ypos=0)
        pairs = session.replay_tail(mark)
        retract_pairs = pairs[:len(pairs) - len(session.blocks(retract))]
        self.assertTrue(retract_pairs, 'retract rapid emitted nothing')
        self.assertEqual(retract_pairs[-1][1].trc, 40, f'retract rapid still under TRC, G40 deferred: {raw(pairs)}')
        deselect = [block for block, _ in pairs if 40 in block.g]
        self.assertTrue(deselect and {'X', 'Y'} & set(deselect[0].axes),
                        f'G40 block without a working-plane axis: {raw(pairs)}')
        self.assertEqual([state.trc for block, state in pairs if {'X', 'Y'} & set(block.axes)],
                         [40] * sum(1 for block, _ in pairs if {'X', 'Y'} & set(block.axes)),
                         f'X/Y motion under TRC after the COMP_OFF: {raw(pairs)}')

    @covers('PP-019')
    def test_compensation_on_emitted_on_following_rapid(self):
        """INDEPENDENT: same modal TRC rule for selection: G41 delivered before an approach
        rapid must be active at the end of that rapid (the approach is the activation move;
        Sinumerik allows G41 in G0). Deferring it makes the first cutting move the
        activation move. Regression guard of PP-019 facet on-before-rapid (fixed in
        b999f65: rapids carry the pending TRC word). UNVERIFIED event order: assumes
        SolidCAM emits @compensation(left) immediately before the approach rapid. A POST
        ERROR stop is accepted."""
        session = job_session()
        session.ev('move_5x', ('xpos', 'ypos', 'zpos'), xpos=12, ypos=13, zpos=50)
        session.ev('compensation', side='comp_left')
        mark = session.mark()
        try:
            session.ev('rapid_move', ('xpos', 'ypos'), xpos=0, ypos=0)
        except UnsupportedGPPL as exc:
            if post_error_stop(exc):
                return
            raise
        pairs = session.event_replay(mark)
        self.assertTrue(pairs, 'approach rapid emitted nothing')
        self.assertEqual(pairs[-1][1].trc, 41, f'TRC activation deferred to the next feed move: {raw(pairs)}')

    @covers('PP-019')
    def test_compensation_off_before_retract_reaches_controller_before_next_tool_cuts(self):
        """INDEPENDENT: Sinumerik TRC (G41/G42) is modal and survives T/M06 (the new D1
        radius is simply applied); before b999f65 the tool-change safety block 'G17 G64 G90'
        had no G40 and @usr_tc_init_gmstates only assumed G40. So G40 delivered before the
        retract rapid must reach the control before the next tool cuts. Regression guard of
        PP-019 facet across-tool-change (fixed in b999f65: 'G17 G40 G64 G90'). UNVERIFIED
        event order: assumes @compensation(off) before the retract rapid and no line/arc
        between that rapid and @end_of_job."""
        session = compensated_job()
        session.ev('compensation', side='comp_left')
        session.ev('line', ('xpos',), xpos=20)
        session.ev('line', ('ypos',), ypos=40)
        session.ev('compensation', side='comp_off')
        try:
            session.ev('rapid_move', ('zpos',), zpos=50)
        except UnsupportedGPPL as exc:
            if post_error_stop(exc):
                return
            raise
        session.next_tool(2, 3)
        session.ev('rapid_move', ('xpos', 'ypos', 'zpos'), xpos=10, ypos=20, zpos=5)
        mark = session.mark()
        session.ev('line', ('zpos', 'feed'), zpos=-3, feed=300)
        pairs = session.event_replay(mark)
        self.assertTrue(pairs, 'cutting move of tool 2 emitted nothing')
        block, state = pairs[-1]
        self.assertEqual(state.trc, 40, f'tool 2 cuts {block.raw!r} with G{state.trc} still modal: '
                                        f'{[b.raw for b in parse_blocks(session.text())]}')


class PlaneModeTests(unittest.TestCase):
    """Machine plane and absolute/incremental mode events."""

    def test_machine_plane_event_selects_din_plane_codes(self):
        """INDEPENDENT: DIN 66025 / Siemens 828D plane selection: XY = G17, ZX = G18,
        YZ = G19; the next linear block must make the plane active on the control."""
        session = compensated_job()
        for x, (plane, code) in enumerate((('zx', 18), ('yz', 19), ('xy', 17)), start=20):
            session.ev('machine_plane', machine_plane=plane)
            self.assertEqual(session.state['implane'], code, plane)
            mark = session.mark()
            session.ev('line', ('xpos',), xpos=x)
            pairs = session.event_replay(mark)
            self.assertEqual([state.plane for _, state in pairs], [code], f'{plane}: {raw(pairs)}')

    def test_relative_and_absolute_mode_events_select_g91_g90(self):
        """INDEPENDENT: DIN 66025 / Siemens 828D: @relative_mode selects incremental
        dimensions (G91), @absolute_mode absolute (G90); the next linear block must make the
        mode active on the control."""
        session = compensated_job()
        for event_name, x, code in (('relative_mode', 5, 91), ('absolute_mode', 30, 90)):
            session.ev(event_name)
            mark = session.mark()
            session.ev('line', ('xpos',), xpos=x)
            pairs = session.event_replay(mark)
            self.assertEqual([state.distance for _, state in pairs], [code], f'{event_name}: {raw(pairs)}')


class PlaneModalityTests(unittest.TestCase):
    """A G19 set by a YZ arc and the next same-tool job (PP-021, fixed in 88695c9).

    YZ (G19) is used because ZX arcs stop the post (PP-003); @usr_arc_math sets
    the modal plane. Caveat (verifier): @machine_plane is also a SolidCAM event;
    if SolidCAM called it at every job start the symptom would disappear. These
    tests deliver no @machine_plane event between the jobs; before 88695c9 the
    GPP called @machine_plane itself only on the tool-change path
    (@usr_tc_init_gmstates).
    """

    def after_yz_arc_job(self, source=None):
        session = compensated_job(source)
        start = {'X': 12, 'Y': 13, 'Z': -2}
        emit_arc(session, 'yz', 'ccw', 90, start, {'X': 12, 'Y': 3, 'Z': -2}, {'X': 12, 'Y': 3, 'Z': 8})
        session.ev('line_5x', ('zpos',), zpos=50, feed_type='feed_rate')
        session.same_tool_job(job_name='op2')
        return session

    @covers('PP-021')
    def test_xy_compensation_after_yz_arc_runs_in_g17(self):
        """INDEPENDENT: on a VMC an XY profile needs G17; Sinumerik TRC acts in the active
        plane (with G19 the radius offset would be applied in Y/Z). Only a tool change calls
        @machine_plane, so G19 from the previous job's YZ arc is still modal when the next
        same-tool job selects G41. Regression guard of PP-021 facet trc (fixed in 88695c9 and
        9767011: @start_of_job and the G41 block select the job plane). UNVERIFIED event
        semantics: assumes SolidCAM does not deliver @machine_plane at every job start
        (class docstring)."""
        session = self.after_yz_arc_job()
        session.ev('move_5x', ('xpos', 'ypos', 'zpos'), xpos=0, ypos=-10, zpos=5)
        session.ev('line', ('zpos', 'feed'), zpos=-2, feed=300)
        session.ev('compensation', side='comp_left')
        session.ev('line', ('ypos',), ypos=0)
        replayed = replay(session.text())
        selections = [(block.raw, state.plane) for block, state in replayed if 41 in block.g]
        self.assertEqual(len(selections), 1, [block.raw for block, _ in replayed])
        self.assertEqual(selections[0][1], 17, f'TRC selected in plane G{selections[0][1]}: {selections[0][0]!r}')

    @covers('PP-021')
    def test_drill_cycle_after_yz_arc_runs_in_g17(self):
        """INDEPENDENT: Sinumerik CYCLE81 drills along the applicate of the active plane (X in
        G19); a spindle-axis drill job on a VMC needs G17 when the modal cycle is called.
        Before 88695c9 @drill did not reset the plane left by the previous job's YZ arc.
        Regression guard of PP-021 facet drill-cycle. UNVERIFIED event semantics: assumes
        SolidCAM does not deliver @machine_plane at every job start (class docstring)."""
        self.check_drill_cycle_after_yz_arc()

    def check_drill_cycle_after_yz_arc(self, source=None):
        session = self.after_yz_arc_job(source)
        session.ev('drill', ('xpos', 'ypos', 'zpos'), xpos=30, ypos=40, zpos=30, drill_type='g81', **DRILL_DEFAULTS)
        replayed = replay(session.text())
        calls = [(block.raw, state.plane) for block, state in replayed
                 if block.cycle is not None and block.find('MCALL')]
        self.assertEqual(len(calls), 1, [block.raw for block, _ in replayed])
        self.assertEqual(calls[0][1], 17, f'modal drill cycle called in plane G{calls[0][1]}: {calls[0][0]!r}')

    def test_88695c9_reversion_is_detected(self):
        """INDEPENDENT: negative validation of the PP-021 drill-cycle guard. Reverting
        88695c9 in memory (no plane restore in @start_of_job) must make
        check_drill_cycle_after_yz_arc fail with AssertionError. The TRC guard is not
        used here: a later follow-up also selects the job plane in the G41 block."""
        anchor = ('    call @home_number\n'
                  "    ; Arcs in YZ/ZX leave iMplane at 19/18; restore the job's machining plane for its first motion block.\n"
                  '    call @usr_job_plane\n')
        mutant = mutate(anchor, '    call @home_number\n')
        assert_detected(self, self.check_drill_cycle_after_yz_arc, mutant, '88695c9 reverted', match='plane G19')


if __name__ == '__main__':
    unittest.main()
