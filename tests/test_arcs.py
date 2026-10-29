"""@usr_arc / @usr_arc_math / @usr_arc_check (dc916d7) on the hand-authored
vectors of fixtures/ambiguous_arcs.json (legacy bare-engine harness).

Scope after the area-D port:
* XY (G17) only. Every YZ and ZX arc stops the post: ZX since 5408e5c (PP-003,
  fixed), both since the machine test of 2026-10-28 (SD42940 = 0, so G18/G19
  move the tool length compensation off Z): tests/test_side_plane_guard.py and
  tests/test_arc_compensation_plane.py::test_zx_arc_stops_the_post.
* End point and opening angle AR= (PGsl 03/2013 9.6.4): no centre word. The
  control derives the centre, so support.nc.arc_path_error compares the arc it
  runs with the fixture arc. An arc above 180 deg is two blocks of AR=size/2
  through the point halfway (the centre from the chord is ill-conditioned there
  and AR= has no full circle).
* Compensation is unchanged, so no G40/G41/G42 may appear in an arc block (TRC
  in a G2/G3 block was PP-020; b999f65 stops the post instead); the old forced
  change(iDiametercomp) is gone. The harness state includes iCompActive (the
  TRC state last posted, 0cfd586) and iFeedMode (9f48a3a), which the fixed post
  reads.
* The CAD-mismatch abort is judged through the engine, which stops at the GPPL
  `input` line (ENGINE-009): real SolidCAM continues after `input`, writes the
  'POST ERROR ...' text and then stops at `abort`.

STRUCTURAL GUARDS (states a real session does not produce, stated on purpose):
* arc_engine() hand-sets the mid-job state and forces the change flags of
  every modal word except TRC, so each arc block carries the full modal
  context (G2/G3, plane, G54, G90, F). In a real session most of these words
  are modal and absent; the block layout asserted here is a property of the
  forced flags, not of a SolidCAM program.
* Fixture arcs above 180 deg (major_*, just_above_semicircle,
  almost_full_circle*, full_circle_*) exercise the @usr_arc_math rotation and
  the halves for any angle. With the VMID setting SupportGrt180degArcs="0"
  SolidCAM splits such arcs before the post sees them (the reference trace of
  2026-10-27 has none above 180), so these cases guard the math, not a
  reachable input.
"""
import json
import unittest

from pp_tests.engine import UnsupportedGPPL
from support import FIXTURES, arc_path_error, covers, fresh_engine, parse_blocks

FIXTURE = json.loads((FIXTURES / 'ambiguous_arcs.json').read_text())
# plane: (axes in the PP's (u, v, w) order, G code, SolidCAM event). For G17 the PP
# order equals the DIN abscissa/ordinate order used by arc_path_error. XY only: YZ and
# ZX arcs stop the post.
PLANES = [('xy', ('x', 'y', 'z'), 17, 'arc')]
# Coordinates use the @init_post format '8.5': rounding error at most 5e-6 mm.
COORDINATE_TOLERANCE = 0.51e-5
# The arc the control runs through rounded end points: both ends move by up to 0.71e-5 mm.
PATH_TOLERANCE = 1.5e-5


def case_planes(case):
    """PLANES entries of a fixture case ('planes' limits it; default xy)."""
    return [entry for entry in PLANES if entry[0] in case.get('planes', ('xy',))]


def arc_engine(case, plane, axes):
    """Bare engine in the mid-job state an arc event sees."""
    engine = fresh_engine()
    engine.set(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz', arc_direction=case['direction'],
               arc_plane=plane, arc_size=case['size'], radius=10, bFeedoutput=False,
               iFeedMode=94, iDiametercomp=40, iCompActive=40, cWo='G', iWorkoffset=54, iAbsincmode=90, feed=100,
               mcode_f='2.0(p)', clear_change_after_gen=1, xpos_f='8.5', ypos_f='8.5', zpos_f='8.5', nArcAR_f='3.5',
               bCycle832Auto=False, iCycle832Want=0, nCycle832WantTol=0, iCycle832Mode=0, nCycle832Tol=0, trace_level=0)
    u, v, w = axes
    delta = case.get('cad_delta', [0, 0])
    engine.set(**{u + 'start': case['start'][0], v + 'start': case['start'][1], w + 'start': 2,
                  u + 'center': case['center'][0], v + 'center': case['center'][1], w + 'center': 2,
                  u + 'center_rel': case['center'][0] - case['start'][0],
                  v + 'center_rel': case['center'][1] - case['start'][1], w + 'center_rel': 0,
                  u + 'pos': case['end'][0] + delta[0], v + 'pos': case['end'][1] + delta[1], w + 'pos': -7})
    # Every modal word except TRC is forced so the block shows the full modal context.
    engine.changed.update({key: True for key in ('imotionmode', 'implane', 'cwo', 'iworkoffset',
                                                  'iabsincmode', 'xpos', 'ypos', 'zpos', 'feed')})
    engine.changed['idiametercomp'] = False
    return engine


def call_valid_arc(testcase, engine, procedure, arguments=()):
    """Run an arc the oracle considers valid; a PP stop becomes an AssertionError."""
    try:
        engine.call(procedure, arguments)
    except UnsupportedGPPL as exc:
        if 'POST ERROR' in str(exc):
            testcase.fail(f'the PP stopped on a valid arc: {exc}')
        raise


class ArcTests(unittest.TestCase):
    def test_ambiguous_xy_arcs_all_modes(self):
        """INDEPENDENT: XY (G17). End points come from the fixture geometry (rotation of
        start-center by +-arc_size); the arc the control runs for the written blocks (PGsl
        03/2013 9.6.4: end point and opening angle AR=, centre derived; G17 viewed from +Z,
        checked with support.nc.arc_path_error) must follow the fixture arc; an arc above
        180 deg is two blocks of AR=size/2 through the point halfway; no centre or radius
        word is written; the helical orthogonal end point is the CAD value; with
        compensation unchanged no G40/G41/G42 appears. Scope (module docstring): no YZ or
        ZX arcs. STRUCTURAL parts (module docstring): the exact modal G list comes from the
        forced change flags, and change(nRapidfeed) is the @usr_arc contract that re-arms
        'F nRapidfeed' for the next feed-emulated rapid (bSyncdrapid=false;
        usr_ip_useroptions documents nRapidfeed as the G1 rapid feed)."""
        for case in FIXTURE['cases']:
            if 'error' in case:
                continue
            for plane, axes, plane_code, procedure in case_planes(case):
                with self.subTest(case=case['name'], plane=plane):
                    engine = arc_engine(case, plane, axes)
                    call_valid_arc(self, engine, procedure)
                    u, v, w = axes
                    self.assertAlmostEqual(engine.state[u + 'pos'], case['end'][0], places=8)
                    self.assertAlmostEqual(engine.state[v + 'pos'], case['end'][1], places=8)
                    self.assertEqual(engine.state[w + 'pos'], -7)  # helical orthogonal endpoint
                    self.assertEqual(engine.state['implane'], plane_code)
                    motion = 3 if case['direction'] == 'ccw' else 2
                    self.assertEqual(engine.state['imotionmode'], motion)
                    blocks = parse_blocks(''.join(engine.output))
                    halves = case['size'] > 180
                    self.assertEqual(len(blocks), 2 if halves else 1, [block.raw for block in blocks])
                    self.assertEqual(blocks[0].g, [motion, plane_code, 54, 90], blocks[0].raw)
                    self.assertEqual(set(blocks[0].axes), {'X', 'Y', 'Z'}, blocks[0].raw)
                    self.assertEqual(blocks[0].get('F'), 100, blocks[0].raw)
                    point = {u.upper(): case['start'][0], v.upper(): case['start'][1], w.upper(): 2}
                    center = tuple(case['center'])
                    for index, block in enumerate(blocks):
                        self.assertEqual(set(block.g) & {40, 41, 42}, set(), f'TRC word in arc block: {block.raw!r}')
                        self.assertEqual([word.raw for word in block.words if word.address in ('I', 'J', 'K', 'R', 'CR')],
                                         [], block.raw)
                        self.assertAlmostEqual(block.get('AR'), case['size'] / len(blocks), delta=0.51e-5, msg=block.raw)
                        sweep = (1 if motion == 3 else -1) * case['size'] / len(blocks)
                        self.assertLessEqual(arc_path_error(plane, point, block, center, sweep, motion), PATH_TOLERANCE,
                                             block.raw)
                        if index:
                            self.assertEqual((block.g, block.get('F')), ([], None), block.raw)
                        point = {axis: block.get(axis, point[axis]) for axis in 'XYZ'}
                    if halves:   # the helix rises half its lead in each half
                        self.assertAlmostEqual(blocks[0].get(w.upper()), (2 - 7) / 2, delta=COORDINATE_TOLERANCE)
                    for axis in 'xyz':
                        self.assertAlmostEqual(point[axis.upper()], engine.state[axis + 'pos'],
                                               delta=COORDINATE_TOLERANCE, msg=blocks[-1].raw)
                    self.assertTrue(engine.changed['nrapidfeed'])

    @covers('ENGINE-009')
    def test_cad_mismatch_stops_before_the_arc_block(self):
        """INDEPENDENT: dc916d7 ('Arcs must be handled mathematically in post'): a CAD end
        point more than 0.001 off the circle stops the post with 'POST ERROR: ARC end
        mismatch' BEFORE the arc is written, so no motion block (G2/G3 or an axis word)
        reaches the NC program. The stop is observed as the engine exception raised at the
        GPPL `input` line (ENGINE-009). Real SolidCAM continues after `input`, writes the
        'POST ERROR ...' text and stops at `abort`; that text block is deliberately not
        asserted (neither its presence nor the engine's empty output), so the test does not
        pin the engine model. The tiny-chord cases (below 0.0001 mm) stop the same way with
        'POST ERROR: ARC chord too short' (usr_arc_chord_check): with the end point and AR= the
        control derives the centre from the chord (PGsl 03/2013 9.6.4), and an end point that
        rounds onto the start leaves it undefined. An opening angle that prints as AR=0 or
        exceeds a full circle stops with 'POST ERROR: ARC opening angle outside AR=' (9.6.4: 0
        to 360)."""
        for case in FIXTURE['cases']:
            if 'error' not in case:
                continue
            for plane, axes, _, procedure in case_planes(case):
                with self.subTest(case=case['name'], plane=plane):
                    engine = arc_engine(case, plane, axes)
                    with self.assertRaisesRegex(UnsupportedGPPL, 'POST ERROR: ' + case['error']):
                        engine.call(procedure)
                    written = [block.raw for block in parse_blocks(''.join(engine.output))
                               if block.is_motion or set(block.g) & {2, 3}]
                    self.assertEqual(written, [], 'arc written before the mismatch stop')

    @covers('ENGINE-009')
    def test_exact_mismatch_tolerance_each_axis(self):
        """INDEPENDENT: dc916d7 accepts a CAD end point up to 0.001 off the computed one on
        every axis and stops above it ('POST ERROR: ARC end mismatch'). The stop is observed
        as the engine exception raised at the GPPL `input` line (ENGINE-009). UNVERIFIED:
        the tolerance_cases edge 0.001000001 aborts only under an exact float compare of
        'dx gt tolerance', the same unverified GPPL numeric-compare semantic as PP-046."""
        for case in FIXTURE['tolerance_cases']:
            for axis in range(3):
                with self.subTest(case=case, axis=axis):
                    engine = fresh_engine()
                    values = [0, 0, 0]
                    values[axis] = case['delta']
                    if case['abort']:
                        with self.assertRaisesRegex(UnsupportedGPPL, 'POST ERROR: ARC end mismatch'):
                            engine.call('usr_arc_check', values)
                    else:
                        call_valid_arc(self, engine, 'usr_arc_check', values)


if __name__ == '__main__':
    unittest.main()
