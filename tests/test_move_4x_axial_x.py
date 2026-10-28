"""@move_4x posts the CAM X: on this machine A rotates around X, so X is the axial coordinate.

Oracle (INDEPENDENT): VMID axis A has VecX=1 (rotation around X). Zeroing X only makes sense for a
rotary axis along Y, where X is the wrapped coordinate; here it would send the rapid to X0 and the
following @line_4x would feed diagonally from X0 to the real X.
"""
import re
import unittest

from test_post_homing_reposition import Session


class Move4xAxialXTests(unittest.TestCase):
    def test_changed_x_is_posted(self):
        session = Session()
        output = session.step('move_4x', ['xpos', 'zpos'], xpos=50, zpos=40, prev_command='@line_4x')
        self.assertEqual(output, ['G0 X50 Z40'])
        self.assertEqual(session.engine.state['xpos'], 50)

    def test_following_line_starts_from_the_posted_x(self):
        # SolidCAM resends X50 on the line; its flag is a value compare against the GPPL variable
        # (assumed GPPL semantics). Zeroing X in @move_4x made that X50 a change: a diagonal G1.
        session = Session()
        session.step('move_4x', ['xpos'], xpos=50, prev_command='@line_4x')
        changed = ['zpos'] + (['xpos'] if session.engine.state['xpos'] != 50 else [])
        output = session.step('line_4x', changed, xpos=50, zpos=2, feed_type='feed_rate')
        self.assertFalse(re.search(r'\bX', ' '.join(output)), output)

    def test_vmid_rotary_axis_is_around_x(self):
        from test_offline import ROOT
        vmid = (ROOT / 'siemens_sinumerik_828d/noname_vmc500_4x/Gmill_540v_4x.vmid').read_text(encoding='latin-1')
        axis = re.search(r'<Axis [^>]*Name="A"[^>]*>', vmid).group(0)
        self.assertIn('VecX="1"', axis)
        self.assertIn('VecY="0"', axis)


if __name__ == '__main__':
    unittest.main()
