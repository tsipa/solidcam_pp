"""Arcs, tool radius compensation and plane modality of Gmill_540v_4x.gpp
(@usr_arc, @usr_arc_math, @usr_arc_check, @compensation, @machine_plane,
@relative_mode/@absolute_mode).

Area D. Tests drive a SolidCAM-like Session after the first tool change, put
the tool at the arc start with a feed move and judge the emitted G2/G3 block
the way a Sinumerik 828D executes it:
* support.nc.arc_path_error is the DIN 66025 / Siemens oracle: G17 is X/Y
  viewed from +Z; the post writes the end point and the opening angle AR=
  (PGsl 03/2013 9.6.4) and the control derives the centre, so the oracle
  compares the arc the control runs with the CAM arc; an arc above 180 deg is
  two blocks of half the angle;
* plane and TRC (G40/G41/G42) states come from support.modal.replay.

XY (G17) arcs only. ZX (G18) orientation was registered as PP-003; the owner's
fix (5408e5c) stopped the post on every ZX arc. Since the machine test of
2026-10-28 every YZ and ZX arc and every YZ/ZX machining plane stops the post:
the machine has SD42940 $SC_TOOL_LENGTH_CONST = 0, so G18/G19 move the tool
length compensation from Z to Y/X ('G19 G3 Y-10 Z55 AR=90' drove Z down by
about the tool length). The arc guards below run in XY, and the former PP-003
test checks that a ZX arc stops the post (the abort mechanics are in
tests/test_side_plane_guard.py). The YZ/ZX output code behind the stops was
deleted 2026-10-28, and the PP-021 guards (G19 left modal by a YZ arc into the
next job) with it. The template's other arc modes (absolute plain I/J, R
word; PP-022) were removed.

TRC: PP-019, PP-020 and PP-021 are fixed (b999f65, 0cfd586, 88695c9, 7aeae99);
their former canonical tests are regression guards (@covers).

Event order caveat: every PP-019/PP-020 test assumes SolidCAM delivers
@compensation directly before the rapid/arc it names. That order is UNVERIFIED
(no captured trace contains a compensation event).
"""
import json
import math
import os
import unittest
from unittest import mock

from pp_tests.engine import UnsupportedGPPL
from program_session import Program, require_nc_stream
from support import (FIXTURES, Session, arc_center, arc_path_error, assert_detected, covers, mutate, parse_blocks,
                     replay, state_before)

# plane: (abscissa, ordinate, applicate, SolidCAM event, G code), DIN 66025 / Siemens 828D.
# ZX only feeds the stop guard (test_zx_arc_stops_the_post): YZ and ZX arcs stop the post.
PLANES = {
    'xy': ('X', 'Y', 'Z', 'arc', 17),
    'zx': ('Z', 'X', 'Y', 'arc_zx', 18),
}
# Coarsest coordinate format in effect after the first tool change is zpos_f '5.4'
# (PP-006): rounding moves a written coordinate by at most 5e-5 mm.
COORDINATE_TOLERANCE = 5.1e-5
# The arc the control runs through rounded end points: an end moves by up to 0.71e-5 mm in XY
# ('8.5'); the AR= bulge error is below 1e-6 here.
PATH_TOLERANCE = 1.0e-4


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


def arc_blocks(testcase, session, mark):
    """[(block, state before, state after)] of the AR= arc blocks of the arc event; an arc
    above 180 deg is two, and its second half carries no G2/G3 word (modal)."""
    replayed = replay(session.text())
    first = len(replayed) - len(parse_blocks(session.text(mark)))
    last = len(replayed) - len(parse_blocks(session.text(mark + 1)))
    arcs = [index for index in range(first, last)
            if replayed[index][1].motion in (2, 3) and replayed[index][0].has('AR')]
    testcase.assertTrue(arcs, f'no AR= arc block: {raw(replayed[first:last])}')
    return [(replayed[index][0], state_before(replayed, index), replayed[index][1]) for index in arcs]


def path_errors(plane, center, sweep, arcs):
    """arc_path_error of each block against its share of the CAM arc (sweep / blocks, positive
    counter-clockwise); a block the control cannot run (AR= outside 0..360, an end on the
    start) counts as infinitely far off."""
    abscissa, ordinate = PLANES[plane][:2]
    errors = []
    for block, before, after in arcs:
        try:
            errors.append(arc_path_error(plane, before.xyz(), block, (center[abscissa], center[ordinate]),
                                         sweep / len(arcs), after.motion))
        except ValueError:
            errors.append(math.inf)
    return errors


def rotated(point, center, degrees):
    """(abscissa, ordinate) of point turned about center by degrees (positive counter-clockwise)."""
    angle = math.radians(degrees)
    du, dv = point[0] - center[0], point[1] - center[1]
    return (center[0] + du * math.cos(angle) - dv * math.sin(angle),
            center[1] + du * math.sin(angle) + dv * math.cos(angle))


def in_plane(plane, pair, applicate):
    """{'X','Y','Z'} point from (abscissa, ordinate) and the applicate value."""
    abscissa, ordinate, normal = PLANES[plane][:3]
    return {abscissa: pair[0], ordinate: pair[1], normal: applicate}


class ArcSweepConventionTests(unittest.TestCase):
    """Convention-independent G2/G3 check (pp-weird-hunter-02, history-misc-04).

    For each CAM label and size both candidate CAD end points are fed; the PP must
    accept exactly one (dc916d7 end-point check) and the control must run the CAM arc
    for the block it writes, whatever label convention SolidCAM uses.
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
            abscissa, ordinate = PLANES[plane][:2]
            for direction in ('ccw', 'cw'):
                for size in (45, 90, 135):
                    block, before, after = self.accepted_arc(plane, direction, size, source)
                    # The CAM arc ends at the accepted end point: turned by +size or -size.
                    center = (self.CENTER[abscissa], self.CENTER[ordinate])
                    end = (after.xyz()[abscissa], after.xyz()[ordinate])
                    start = (before.xyz()[abscissa], before.xyz()[ordinate])
                    sweep = min((sign * size for sign in (1, -1)),
                                key=lambda turn: math.dist(end, rotated(start, center, turn)))
                    error = arc_path_error(plane, before.xyz(), block, center, sweep)
                    if error > PATH_TOLERANCE:
                        errors.append(f'{plane} {direction} {size}: the control runs off the CAM arc by {error:.4f} '
                                      f'for {block.raw!r}')
        return errors

    def test_pin_xy_arcs_sweep_cam_angle_on_control(self):
        """INDEPENDENT: DIN 66025 / Siemens 828D circle direction (G17 viewed from +Z) and
        PGsl 03/2013 9.6.4 (end point and AR=): for XY arcs of 45/90/135 deg, both labels,
        the block the PP writes must make the control run the CAM arc (the start turned
        about the CAM centre by arc_size in the label's sense). YZ and ZX arcs stop the
        post."""
        errors = self.sweep_errors(('xy',))
        self.assertEqual(errors, [])

    def test_pin_xy_arc_sweep_detects_mutation(self):
        """INDEPENDENT: swapping G3/G2 for the CCW label in @usr_arc_math must make the XY
        sweep check fail with AssertionError."""
        mutant = mutate('    if arc_direction eq CCW then\n        iMotionmode = 3\n    else\n        iMotionmode = 2',
                        '    if arc_direction eq CCW then\n        iMotionmode = 2\n    else\n        iMotionmode = 3')
        assert_detected(self, lambda source: self.assertEqual(self.sweep_errors(('xy',), source), []),
                        mutant, 'G2/G3 swapped')

    @covers('PP-003')
    def test_zx_arc_stops_the_post(self):
        """INDEPENDENT: DIN 66025 / Sinumerik G18 is viewed from +Y with Z as abscissa and X
        as ordinate, so G3 turns Z->X, while @usr_arc_math rotates X->Z for a positive
        angle; which end point SolidCAM sends for a CCW label is UNVERIFIED (VMID
        ArcDirectionBy="0"). Owner decision (5408e5c, PP-003): a ZX arc must not be posted
        at all. Since the machine test of 2026-10-28 one stop covers YZ and ZX arcs: with
        SD42940 $SC_TOOL_LENGTH_CONST = 0 (backups/NOLOG.ard) G18/G19 move the tool length
        compensation from Z to Y/X. For both labels, three sizes and both candidate CAD end
        points the post must stop with the YZ/ZX arc POST ERROR and no G2/G3 or G18 block
        may reach the NC program. Regression guard of PP-003; the input/abort mechanics are
        tests/test_side_plane_guard.py."""
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
                        with self.assertRaisesRegex(UnsupportedGPPL, 'POST ERROR: YZ/ZX arc: G18/G19 would move the '
                                                    'tool length compensation off Z', msg=label):
                            emit_arc(session, 'zx', direction, size, start, self.CENTER, end)
                        written = parse_blocks(''.join(session.engine.output[first:]))
                        self.assertEqual([block.raw for block in written if set(block.g) & {2, 3, 18}], [], label)


# Off-axis vectors (TSR-07: every fixture case starts on the +abscissa axis, so the
# ordinate terms of the rotation were untested). (abscissa, ordinate) in DIN order, XY
# (G17) only: YZ and ZX arcs stop the post.
OFF_AXIS_CASES = [
    dict(name='semicircle_off_axis_ccw', size=180, direction='ccw', start=(6, 8), center=(0, 0), end=(-6, -8)),
    dict(name='semicircle_off_axis_cw', size=180, direction='cw', start=(6, 8), center=(0, 0), end=(-6, -8)),
    dict(name='semicircle_offset_center_ccw', size=180, direction='ccw', start=(5, 1), center=(2, 5), end=(-1, 9)),
    dict(name='semicircle_offset_center_cw', size=180, direction='cw', start=(5, 1), center=(2, 5), end=(-1, 9)),
    dict(name='quarter_off_axis_ccw', size=90, direction='ccw', start=(6, 8), center=(0, 0), end=(-8, 6)),
    dict(name='quarter_off_axis_cw', size=90, direction='cw', start=(6, 8), center=(0, 0), end=(8, -6)),
    dict(name='quarter_offset_center_ccw', size=90, direction='ccw', start=(5, 1), center=(2, 5), end=(6, 8)),
    # Above 180 deg (two halves): the start off the abscissa exercises both terms of the halfway rotation.
    dict(name='major_off_axis_ccw', size=270, direction='ccw', start=(6, 8), center=(0, 0), end=(8, -6)),
    dict(name='major_off_axis_cw', size=270, direction='cw', start=(6, 8), center=(0, 0), end=(-8, 6)),
    dict(name='major_offset_center_ccw', size=270, direction='ccw', start=(5, 1), center=(2, 5), end=(-2, 2)),
    # A CAD end point off the circle in the NEGATIVE direction of each in-plane axis aborts too.
    dict(name='negative_abscissa_mismatch_aborts', size=180, direction='ccw', start=(6, 8), center=(0, 0),
         end=(-6, -8), cad_delta=(-0.0011, 0), error=True),
    dict(name='negative_ordinate_mismatch_aborts', size=180, direction='ccw', start=(6, 8), center=(0, 0),
         end=(-6, -8), cad_delta=(0, -0.0011), error=True),
    dict(name='negative_roundoff_is_corrected', size=180, direction='cw', start=(6, 8), center=(0, 0),
         end=(-6, -8), cad_delta=(-0.0009, -0.0009)),
]


def fixture_cases():
    """fixtures/ambiguous_arcs.json cases as XY arc cases (YZ and ZX arcs stop the post)."""
    fixture = json.loads((FIXTURES / 'ambiguous_arcs.json').read_text())
    return [dict(case, planes=tuple(case.get('planes', ('xy',)))) for case in fixture['cases']]


class ArcGuardTests(unittest.TestCase):
    """dc916d7 ('Arcs must be handled mathematically in post') regression guards."""

    def assert_arc_case(self, case, plane, source=None):
        normal, code = PLANES[plane][2], PLANES[plane][4]
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
        arcs = arc_blocks(self, session, mark)
        written = [block.raw for block, _, _ in arcs]
        self.assertEqual(len(arcs), 2 if case['size'] > 180 else 1, f'{label}: {written}')
        self.assertIn(3 if case['direction'] == 'ccw' else 2, arcs[0][0].g, f'{label}: {written}')
        for block, _, after in arcs:
            self.assertEqual(after.plane, code, f'{label}: plane active at {block.raw!r}')
            self.assertEqual([word.raw for word in block.words if word.address in ('I', 'J', 'K', 'R', 'CR')], [],
                             f'{label}: centre or radius word with AR= in {block.raw!r}')
        sweep = case['size'] if case['direction'] == 'ccw' else -case['size']
        errors = path_errors(plane, center, sweep, arcs)
        self.assertLessEqual(max(errors), PATH_TOLERANCE, f'{label}: {written} runs off the CAM arc by {errors}')
        if len(arcs) == 2:   # a helix rises half its lead in each half
            self.assertAlmostEqual(arcs[0][2].xyz()[normal], (start[normal] + true_end[normal]) / 2,
                                   delta=COORDINATE_TOLERANCE, msg=f'{label}: {written}')
        for axis in 'XYZ':
            self.assertAlmostEqual(arcs[-1][2].xyz()[axis], true_end[axis], delta=COORDINATE_TOLERANCE,
                                   msg=f'{label} {axis}: {written}')

    def run_cases(self, cases, source=None, subtests=True):
        # XY only: every YZ and ZX arc stops the post (test_zx_arc_stops_the_post).
        for case in cases:
            for plane in case.get('planes', ('xy',)):
                if not subtests:   # mutant runs: the first AssertionError propagates
                    self.assert_arc_case(case, plane, source)
                    continue
                with self.subTest(case=case['name'], plane=plane):
                    self.assert_arc_case(case, plane, source)

    @covers('ENGINE-009')
    def test_off_axis_arcs_and_negative_mismatch(self):
        """INDEPENDENT: geometry and Sinumerik words in XY (G17); YZ and ZX arcs stop the post
        (test_zx_arc_stops_the_post). A semicircle ends at 2*center - start for either
        direction; quarter arcs rotate +abscissa -> +ordinate
        for CCW (DIN 66025); the block carries the end point and AR= and no centre or radius
        word (PGsl 03/2013 9.6.4), and the arc the control derives from it follows the CAM
        arc; above 180 deg it is two halves, a helix rising half its lead in each; dc916d7
        aborts on a CAD end point more than 0.001 off the circle in either direction of any
        axis and writes the recomputed end point within tolerance (a CAD end off by more than the
        rounding of the inputs; ArcEndPointTests keeps one within it). Starts lie off the
        abscissa (absorbs the TSR off-axis test). The abort is observed as the engine
        exception at the GPPL `input` line (ENGINE-009)."""
        self.run_cases(OFF_AXIS_CASES)

    # YZ and ZX mutants (dc916d7's ZX K-word revert, ZX K sign, the YZ/ZX rotation, orthogonal
    # axis, chord, Z resolution and halfway point) went with the YZ/ZX code behind the arc stop
    # (deleted 2026-10-28), and center_z_sign with the Z centre it read. dz_signed_reversed is
    # gone too: dz is 0 for an XY arc, whose Z end comes from CAD.
    MUTANTS = {
        'no_end_point_commit': ('        xpos = calculated_xpos\n        ypos = calculated_ypos\n        zpos = calculated_zpos\n',
                                ''),
        'no_mismatch_check': ('    call @usr_arc_check(dx, dy, dz)\n', ''),
        'xy_rotation_flipped': ('    rx = vx * c - vy * s\n    ry = vx * s + vy * c\n',
                                '    rx = vx * c + vy * s\n    ry = -vx * s + vy * c\n'),
        'xy_ordinate_term_sign': ('    ry = vx * s + vy * c\n', '    ry = vx * s - vy * c\n'),
        'center_y_sign': ('    cy = ystart + ycenter_rel\n', '    cy = ystart - ycenter_rel\n'),
        'cw_sign_dropped': ('        angle_deg = -angle_deg\n', '        angle_deg = angle_deg\n'),
        'xy_orthogonal_from_start': ('    calculated_zpos = zpos\n', '    calculated_zpos = zstart\n'),
        'dx_signed_reversed': ('dx = abs(calculated_xpos - xpos)', 'dx = (xpos - calculated_xpos)'),
        'dy_signed_reversed': ('dy = abs(calculated_ypos - ypos)', 'dy = (ypos - calculated_ypos)'),
        'ar_complement': ("'AR='arc_size:nArcAR_f", "'AR='(360 - arc_size):nArcAR_f"),
        'halves_above_360': ('    if arc_size > 180.000005 then\n        ; First half',
                             '    if arc_size > 360 then\n        ; First half'),
        'mid_at_full_angle': ('        c = cos(angle_deg / 2)\n        s = sin(angle_deg / 2)\n',
                              '        c = cos(angle_deg)\n        s = sin(angle_deg)\n'),
        'xy_mid_normal_at_end': ('        nArcMidZ = (zstart + calculated_zpos) / 2\n',
                                 '        nArcMidZ = calculated_zpos\n'),
        'second_half_full_angle': ("        {'AR='nArcAR:nArcAR_f ' '}\n", "        {'AR='arc_size:nArcAR_f ' '}\n"),
        'no_angle_check': ('    call @usr_arc_angle_check\n', ''),
        'angle_limit_looser': ('arc_size > 360.000005', 'arc_size > 361'),
        'check_or_to_and': ('if dx gt tolerance or dy gt tolerance or dz gt tolerance then',
                            'if dx gt tolerance and dy gt tolerance and dz gt tolerance then'),
        'no_chord_check': ('    call @usr_arc_chord_check(du, dv)\n', ''),
        'chord_limit_looser': ('du * du + dv * dv < 0.00000001', 'du * du + dv * dv < 0.000000001'),
        'chord_limit_tighter': ('du * du + dv * dv < 0.00000001', 'du * du + dv * dv < 0.0000001'),
        'halves_not_exempt': ('    if arc_size <= 180.000005 and du * du', '    if du * du'),
        'mid_xy_ordinate_sign': ('        nArcMidX = cx + vx * c - vy * s\n',
                                 '        nArcMidX = cx + vx * c + vy * s\n'),
    }

    def test_arc_math_mutants_are_detected_by_assertions(self):
        """INDEPENDENT: every in-memory mutant of @usr_arc_math/@usr_arc/@usr_arc_check below
        (dc916d7 reverts, rotation/sign/centre/orthogonal-axis/tolerance mutants, the AR=
        word, the halves and the angle/chord stops) must make one of the geometric oracles
        above raise AssertionError, never an interpreter error. YZ/ZX mutants are absent:
        those lines are unreachable behind the YZ/ZX arc stop."""
        cases = OFF_AXIS_CASES + fixture_cases()
        for name, (old, new) in self.MUTANTS.items():
            with self.subTest(mutant=name):
                assert_detected(self, lambda source: self.run_cases(cases, source, subtests=False),
                                mutate(old, new), name)

    def check_arc_words(self, source=None):
        session = job_session(source)
        case = OFF_AXIS_CASES[6]   # quarter, start (5, 1), center (2, 5)
        start, center = in_plane('xy', case['start'], 2), in_plane('xy', case['center'], 2)
        position(session, start)
        mark = emit_valid_arc(self, session, 'xy', case['direction'], case['size'], start, center,
                              in_plane('xy', case['end'], 2))
        block, before, _ = arc_result(self, session, mark)
        self.assertEqual([word.raw for word in block.words if word.address in ('I', 'J', 'K', 'R', 'CR')], [],
                         block.raw)
        self.assertEqual((block.get('X'), block.get('Y'), block.get('AR')), (6, 8, 90), block.raw)
        cx, cy = arc_center('xy', before.xyz(), block)
        self.assertLessEqual(math.dist((cx, cy), (2, 5)), 1e-9, block.raw)

    def test_arc_block_writes_end_point_and_opening_angle(self):
        """INDEPENDENT: PGsl 03/2013 9.6.4: 'G2/G3 X... Y... Z... AR=' gives the end point and
        the opening angle, and the control derives the centre (here (2, 5)); the radius word
        of a Sinumerik is CR= (R is an arithmetic parameter). @usr_arc must write X/Y and
        AR= and no centre or radius word, which would over-determine the circle."""
        self.check_arc_words()

    def test_other_arc_words_are_detected(self):
        """INDEPENDENT: @usr_arc writing centre words next to AR= or an R word instead of
        AR= must make the arc-word check fail with AssertionError."""
        words = "'AR='arc_size:nArcAR_f ' '"
        mutants = {'centre words': "'I'xcenter_rel ' ', 'J'ycenter_rel ' ', 'AR='arc_size:nArcAR_f ' '",
                   'R word': "'R'radius ' '"}
        for label, replacement in mutants.items():
            with self.subTest(label):
                assert_detected(self, self.check_arc_words, mutate(words, replacement), label)

    def test_configured_output_precision_keeps_the_arc_on_the_cam_arc(self):
        """INDEPENDENT: dc916d7 raised XYZ output to 5 decimals (VMID MovementPrecision=5).
        After @init_post the arc the control runs for a 30 deg XY arc through its written end
        point and AR= must stay within 1e-5 mm of the CAM arc (5-decimal rounding moves the
        end by at most 0.71e-5 mm; the 5-decimal AR= moves the middle by chord * 2e-8)."""
        session = job_session()
        start = {'X': 10, 'Y': 0, 'Z': 0}
        end = {'X': 10 * math.cos(math.radians(30)), 'Y': 5.0, 'Z': 0}
        position(session, start)
        mark = emit_valid_arc(self, session, 'xy', 'ccw', 30, start, {'X': 0, 'Y': 0, 'Z': 0}, end)
        block, before, _ = arc_result(self, session, mark)
        self.assertLessEqual(arc_path_error('xy', before.xyz(), block, (0, 0), 30), 1e-5, block.raw)


class ArcEndWordTests(unittest.TestCase):
    """Both end words of the arc plane in every AR= block (@usr_arc_point)."""

    # A CAM end 0.0005 off in X: beyond the input rounding, so @usr_arc_math assigns the recomputed end.
    AMBIGUOUS_X = -10.0005

    def semicircle(self, source=None, zpos=-1, xpos=-10):
        require_nc_stream()
        with mock.patch.dict(os.environ, GPPL_POLICY='change_on_equal_assign=clear'):
            program = Program(source=source)
            program.start()
            program.ev('rapid_move', xpos=10, ypos=0, zpos=5)
            program.ev('line', zpos=-1, feed=200)
            return program.ev('arc', xpos=xpos, ypos=0, zpos=zpos, xstart=10, ystart=0, zstart=-1, xcenter_rel=-10,
                              ycenter_rel=0, zcenter_rel=0, arc_size=180, arc_direction='ccw', arc_plane='xy',
                              feed=200)

    def test_ar_block_keeps_both_plane_words_when_an_equal_assignment_clears_the_flag(self):
        """INDEPENDENT: PGsl 03/2013 9.6.4: AR= with the end point; a missing end word keeps the
        start coordinate, and an end on the start leaves the centre undefined. Whether an equal
        assignment clears a change flag is UNVERIFIED (policy change_on_equal_assign). The CAM end
        of a semicircle back to its start Y comes without the Y flag, and when @usr_arc_math
        replaces an ambiguous end it does so by such an assignment (Y = 0, the CAM value), so the
        block must carry X and Y whatever the flags say."""
        self.assertEqual(self.semicircle(), ['G3 X-10 Y0 AR=180'])
        self.assertEqual(self.semicircle(xpos=self.AMBIGUOUS_X), ['G3 X-10 Y0 AR=180'])

    def test_helix_keeps_its_normal_axis_when_an_equal_assignment_clears_the_flag(self):
        """INDEPENDENT: a helical arc ends at the CAM Z (here -2 from a start at -1); replacing an
        ambiguous end assigns Z its own value, which may clear the Z flag, and an arc block
        without Z runs flat."""
        self.assertEqual(self.semicircle(zpos=-2), ['G3 X-10 Y0 Z-2 AR=180'])
        self.assertEqual(self.semicircle(zpos=-2, xpos=self.AMBIGUOUS_X), ['G3 X-10 Y0 Z-2 AR=180'])

    def test_modal_end_words_are_detected(self):
        """INDEPENDENT: mutation self-check; modal plane words in @usr_arc_point drop X, and
        without the helix check the helix Z is dropped (XY; YZ and ZX arcs stop the post)."""
        checks = [
            ("    {'X'xpos ' ','Y'ypos ' ',['Z'zpos ' ']}\n", "    {['X'xpos ' '],['Y'ypos ' '],['Z'zpos ' ']}\n",
             lambda source: self.assertEqual(self.semicircle(source), ['G3 X-10 Y0 AR=180']), 'modal X/Y'),
            ('    if zpos ne zstart then\n        change(zpos) = true\n    endif\n', '',
             lambda source: self.assertEqual(self.semicircle(source, zpos=-2, xpos=self.AMBIGUOUS_X),
                                             ['G3 X-10 Y0 Z-2 AR=180']),
             'helix Z by flag'),
        ]
        for old, new, check, label in checks:
            with self.subTest(label):
                assert_detected(self, check, mutate(old, new), label)


class ArcLimitTests(unittest.TestCase):
    """The AR= format and the stops that keep an AR= block defined, with the post's real formats."""

    def arc(self, source=None, start=(10, 0), center=(0, 0), size=90.0, plane='xy', applicate=14, end_delta=(0, 0)):
        """One CCW arc of size degrees from start about center after the program start (real formats);
        end_delta moves the CAM end point off the exact end."""
        require_nc_stream()
        program = Program(source=source)
        program.start()
        abscissa, ordinate, normal, event, _ = PLANES[plane]
        su, sv = start
        cu, cv = center
        eu, ev = rotated(start, center, size)
        eu, ev = eu + end_delta[0], ev + end_delta[1]
        point = {abscissa: su, ordinate: sv, normal: applicate}
        program.ev('rapid_move', xpos=point['X'], ypos=point['Y'], zpos=5)
        program.ev('line', zpos=point['Z'], feed=200)
        values = {abscissa.lower() + 'pos': eu, ordinate.lower() + 'pos': ev, normal.lower() + 'pos': applicate,
                  abscissa.lower() + 'start': su, ordinate.lower() + 'start': sv, normal.lower() + 'start': applicate,
                  abscissa.lower() + 'center_rel': cu - su, ordinate.lower() + 'center_rel': cv - sv,
                  normal.lower() + 'center_rel': 0}
        return program.ev(event, arc_size=size, arc_direction='ccw', arc_plane=plane, feed=200, **values)

    def test_ar_prints_the_control_angle_resolution(self):
        """INDEPENDENT: INT_INCR_PER_DEG 100000 (MD10210 in backups/NOLOG.ard): the control reads an
        angle to 0.00001 deg, so AR= carries 5 decimals (a 37.123456 deg arc prints AR=37.12346, a
        0.0004 deg arc AR=0.0004, not AR=0)."""
        self.assertEqual(self.arc(size=37.123456), ['G3 X7.97337 Y6.03534 AR=37.12346'])
        self.assertEqual(self.arc(start=(100, 0), size=0.0004), ['G3 X100 Y0.0007 AR=0.0004'])

    def test_angle_that_prints_as_zero_stops(self):
        """INDEPENDENT: PGsl 03/2013 9.6.4 (AR= above 0): a 0.000004 deg arc prints AR=0 with 5
        decimals. On radius 2000 (VMID MaxArcRadius) its chord, 0.00014 mm, passes the chord
        stop, so @usr_arc_angle_check must stop the post."""
        with self.assertRaisesRegex(UnsupportedGPPL, 'POST ERROR: ARC opening angle outside AR='):
            self.arc(start=(2000, 0), size=0.000004)

    def test_coarser_ar_format_is_detected(self):
        """INDEPENDENT: mutation self-check of the 5-decimal pin; a coarser nArcAR_f would print
        AR=0 above the 0.000005 deg limit of @usr_arc_angle_check."""
        coarse = mutate("    nArcAR_f        = '3.5'\n", "    nArcAR_f        = '3.4'\n")
        assert_detected(self, lambda source: self.assertEqual(self.arc(source, size=37.123456),
                                                              ['G3 X7.97337 Y6.03534 AR=37.12346']), coarse, '3.4')


class ArcEndPointTests(unittest.TestCase):
    """The end point an XY arc block prints: SolidCAM's when the arc is unambiguous (owner 2026-10-28).

    Unambiguous: the end recomputed from the start, the centre and arc_size agrees with the CAM end up
    to the rounding of those inputs, 0.00003 mm per axis plus radius * 0.000005 deg. Beyond that, up to
    the 0.001 stop, the recomputed end replaces the CAM end (dc916d7, ArcGuardTests roundoff cases).
    """

    arc = ArcLimitTests.arc

    def assert_unambiguous_kept(self, source=None):
        self.assertEqual(self.arc(source, end_delta=(0.00002, 0.00002)), ['G3 X0.00002 Y10.00002 AR=90'])
        self.assertEqual(self.arc(source, start=(2000, 0), size=0.01, end_delta=(0, 0.00015)),
                         ['G3 X1999.99997 Y0.34922 AR=0.01'])

    def assert_ambiguous_recomputed(self, source=None):
        self.assertEqual(self.arc(source, end_delta=(0.00004, 0)), ['G3 X0 Y10 AR=90'])
        self.assertEqual(self.arc(source, end_delta=(0, -0.00004)), ['G3 X0 Y10 AR=90'])
        self.assertEqual(self.arc(source, start=(2000, 0), size=0.01, end_delta=(0, 0.00025)),
                         ['G3 X1999.99997 Y0.34907 AR=0.01'])

    def test_unambiguous_arc_keeps_the_cam_end_point(self):
        """INDEPENDENT: owner 2026-10-28 ('take the end from SolidCAM if the arc is unambiguous'):
        with AR= the control derives the centre from the end point, so the CAM end prints as sent.
        On radius 2000 (VMID MaxArcRadius) the 5-decimal arc_size alone turns the end by up to
        0.00017 mm, so a CAM end 0.00015 mm off the exact end is still unambiguous."""
        self.assert_unambiguous_kept()

    def test_ambiguous_arc_takes_the_recomputed_end_point(self):
        """INDEPENDENT: dc916d7: a CAM end off by more than the input rounding in any axis, up to the
        0.001 stop, gives way to the end recomputed from the start, the centre and arc_size."""
        self.assert_ambiguous_recomputed()

    def test_end_point_choice_mutants_are_detected(self):
        """INDEPENDENT: mutation self-check of the end point choice in @usr_arc_math."""
        tolerance = '    nEndTol = 0.00003 + (abs(vx) + abs(vy)) * 0.0000000873\n'
        mutants = {
            'always_recomputed': (tolerance, '    nEndTol = 0\n', self.assert_unambiguous_kept),
            'never_recomputed': (tolerance, '    nEndTol = 1\n', self.assert_ambiguous_recomputed),
            'no_radius_term': (tolerance, '    nEndTol = 0.00003\n', self.assert_unambiguous_kept),
            'or_to_and': ('    if dx > nEndTol or dy > nEndTol or dz > nEndTol\n',
                          '    if dx > nEndTol and dy > nEndTol and dz > nEndTol\n', self.assert_ambiguous_recomputed),
        }
        for label, (old, new, check) in mutants.items():
            with self.subTest(label):
                assert_detected(self, check, mutate(old, new), label)


class RemovedArcModeTests(unittest.TestCase):
    """The template's arc modes 1, 3 and 4 (absolute centre as plain I/J, R word) are removed (PP-022).

    Oracle: Siemens 828D programming manual (plain I/J/K are incremental from the start point, an
    absolute centre needs I=AC(..), the radius word is CR=, a bare R is an arithmetic parameter); the
    machine's Vericut control (sin840d_special.ctl) defines 'CR=' as 'CIRCLES: Circle radius'.
    """

    START, CENTER = {'X': 12, 'Y': 23, 'Z': -2}, {'X': 2, 'Y': 23, 'Z': -2}

    def arc_blocks(self, mode, size):
        session = job_session(options=dict(iArcmode=mode))
        angle = math.radians(size)
        end = {'X': 2 + 10 * math.cos(angle), 'Y': 23 + 10 * math.sin(angle), 'Z': -2}
        position(session, self.START)
        mark = emit_arc(session, 'xy', 'ccw', size, self.START, self.CENTER, end)
        return arc_blocks(self, session, mark)

    @covers('PP-022')
    def test_leftover_arc_mode_setting_posts_the_sinumerik_centre(self):
        """INDEPENDENT: the Sinumerik centre and radius rules above. A leftover iArcmode 1, 3 or 4
        setting (the removed modes printed the absolute centre as plain I/J, also for full circles,
        and R for the radius) must make the control run the CAM arc about (2, 23) for a 90 deg arc
        and a full circle (two halves, PGsl 03/2013 9.6.4), with no R or CR word. Regression guard
        of all three PP-022 facets."""
        problems = {}
        for mode in (1, 3, 4):
            for size in (90, 360):
                arcs = self.arc_blocks(mode, size)
                radius = [word.raw for block, _, _ in arcs for word in block.words if word.address in ('R', 'CR')]
                if max(path_errors('xy', self.CENTER, size, arcs)) > PATH_TOLERANCE or radius:
                    problems[(mode, size)] = [block.raw for block, _, _ in arcs]
        self.assertEqual(problems, {}, 'the control does not run the CAM arc')


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
        the G40 waited for the next feed move; 0cfd586 waited for the next X/Y block; 6f6f6ce
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

    def test_machine_plane_xy_event_selects_g17(self):
        """INDEPENDENT: DIN 66025 / Siemens 828D plane selection: XY = G17; the next linear
        block must make the plane active on the control. YZ and ZX machining planes stop the
        post (SD42940 = 0 on this machine)."""
        session = compensated_job()
        session.ev('machine_plane', machine_plane='xy')
        self.assertEqual(session.state['implane'], 17)
        mark = session.mark()
        session.ev('line', ('xpos',), xpos=20)
        pairs = session.event_replay(mark)
        self.assertEqual([state.plane for _, state in pairs], [17], raw(pairs))

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


if __name__ == '__main__':
    unittest.main()
