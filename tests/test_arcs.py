"""@usr_arc / @usr_arc_math / @usr_arc_check (dc916d7) on the hand-authored
vectors of fixtures/ambiguous_arcs.json (legacy bare-engine harness).

Scope after the area-D port:
* XY (G17) and YZ (G19) only. Every ZX arc stops the post since 5408e5c (PP-003,
  fixed): tests/test_zx_arc_guard.py and
  tests/test_arc_compensation_plane.py::test_zx_arc_stops_the_post.
* Incremental I/J/K only: the other arc modes (iArcmode 1/3/4, PP-022) were
  removed in the refactor (tests/test_arc_compensation_plane.py).
* Compensation is unchanged, so no G40/G41/G42 may appear in an arc block (TRC
  in a G2/G3 block was PP-020; b999f65 stops the post instead); the old forced
  change(iDiametercomp) is gone. The harness state includes iCompActive (the
  TRC state last posted, 264be29) and iFeedMode (9f48a3a), which the fixed post
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
  almost_full_circle, full_circle_*) exercise the @usr_arc_math rotation for
  any angle. With the VMID setting SupportGrt180degArcs="0" SolidCAM is
  expected to split such arcs before the post sees them (meaning of the VMID
  flag UNVERIFIED), so these cases guard the math, not a reachable input.
"""
import json
import unittest

from pp_tests.engine import UnsupportedGPPL
from support import FIXTURES, arc_sweep_degrees, covers, fresh_engine, parse_blocks

FIXTURE = json.loads((FIXTURES / 'ambiguous_arcs.json').read_text())
# plane: (axes in the PP's (u, v, w) order, G code, SolidCAM event). For G17 and G19
# the PP order equals the DIN abscissa/ordinate order used by arc_sweep_degrees.
PLANES = [('xy', ('x', 'y', 'z'), 17, 'arc'), ('yz', ('y', 'z', 'x'), 19, 'arc_yz')]
CENTER_WORDS = {'x': 'I', 'y': 'J', 'z': 'K'}
# Coordinates use the @init_post format '8.5': rounding error at most 5e-6 mm.
COORDINATE_TOLERANCE = 0.51e-5


def arc_engine(case, plane, axes):
    """Bare engine in the mid-job state an arc event sees."""
    engine = fresh_engine()
    engine.set(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz', arc_direction=case['direction'],
               arc_plane=plane, arc_size=case['size'], radius=10, bFeedoutput=False,
               iFeedMode=94, iDiametercomp=40, iCompActive=40, cWo='G', iWorkoffset=54, iAbsincmode=90, feed=100,
               mcode_f='2.0(p)', clear_change_after_gen=1, xpos_f='8.5', ypos_f='8.5', zpos_f='8.5',
               bCycle832Auto=False, iCycle832Want=0, nCycle832WantTol=0, iCycle832Mode=0, nCycle832Tol=0)
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
    def test_ambiguous_arcs_all_planes_and_modes(self):
        """INDEPENDENT: XY (G17) and YZ (G19) with incremental I/J/K. End points come
        from the fixture geometry (rotation of start-center by +-arc_size); the control
        must sweep arc_size for the written block (DIN 66025 / Siemens 828D, checked with
        support.nc.arc_sweep_degrees); I/J/K are incremental from the start point; the
        helical orthogonal end point is the CAD value; with compensation unchanged no
        G40/G41/G42 appears in the arc block. Scope (module docstring): no ZX (PP-003), no
        modes 1/3/4 (PP-022). STRUCTURAL parts (module docstring): the exact modal G list
        comes from the forced change flags, and change(nRapidfeed) is the @usr_arc
        contract that re-arms 'F nRapidfeed' for the next feed-emulated rapid
        (bSyncdrapid=false; usr_ip_useroptions documents nRapidfeed as the G1 rapid
        feed)."""
        for case in FIXTURE['cases']:
            if 'error' in case:
                continue
            for plane, axes, plane_code, procedure in PLANES:
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
                    self.assertEqual(len(blocks), 1, blocks)
                    block = blocks[0]
                    self.assertEqual(block.g, [motion, plane_code, 54, 90], block.raw)
                    self.assertEqual(set(block.g) & {40, 41, 42}, set(), f'TRC word in arc block: {block.raw!r}')
                    self.assertEqual(set(block.axes), {'X', 'Y', 'Z'}, block.raw)
                    for axis in 'xyz':
                        self.assertAlmostEqual(block.get(axis.upper()), engine.state[axis + 'pos'],
                                               delta=COORDINATE_TOLERANCE, msg=block.raw)
                    self.assertEqual(block.get('F'), 100, block.raw)
                    start = {u.upper(): case['start'][0], v.upper(): case['start'][1], w.upper(): 2}
                    sweep = arc_sweep_degrees(plane, start, block)
                    self.assertAlmostEqual(sweep, case['size'] % 360, delta=0.01, msg=block.raw)
                    words = {word.address: (word.mode, word.value) for word in block.words
                             if word.address in ('I', 'J', 'K', 'R', 'CR')}
                    expected = {CENTER_WORDS[axis]: (None, case['center'][index] - case['start'][index])
                                for index, axis in enumerate((u, v))}
                    self.assertEqual(words, expected, block.raw)
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
        pin the engine model."""
        for case in FIXTURE['cases']:
            if 'error' not in case:
                continue
            for plane, axes, _, procedure in PLANES:
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
