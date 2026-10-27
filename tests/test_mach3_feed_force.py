"""Mach3 4x post: feed-rate force from 6efcad8 ("Feed rate force for mach3").

The Mach3 post lives in the (usually uninitialised) submodule mach3/4x. These
tests skip unless the post is available, via the submodule checkout or
MACH3_PP_SOURCE=<path to Mach3_4X_Y.gpp> (support.paths.MACH3_PP), e.g. a copy
extracted with `git show 6efcad8:mach3/4x/Mach3_4X_Y.gpp`. An initialised
submodule pins the current SolidCam-Mach3-Post fork, not 6efcad8, so its
outcome there is not known in advance.

6efcad8 records that Mach3 "forgets" a changed feed and crashes into the
stock unless the feed is re-stated; the remedy emits a standalone
`G1 F<feed>` block before the motion block of a feed move.
"""
import re
import unittest

from support import fresh_engine, known_defect
from support.paths import MACH3_PP, read_text

EVENTS = [
    ('line', dict(feed=1000, xpos=10)),
    ('line', dict(feed=200, xpos=20)),
    ('line', dict(feed=200, ypos=5)),
    ('line_4x', dict(feed=300, cpos=90)),
    ('line', dict(feed=300, xpos=30)),
    ('line', dict(feed=1500, zpos=-2)),
]
MOTION = re.compile(r'(?<![A-Z])[XYZA][+-]?(?:\d|\.\d)')
STANDALONE_FEED = re.compile(r'G1 F([\d.]+)')


def run_events(events):
    """[(procedure, cam_feed, blocks)] for each event; SolidCAM flags a value as
    changed when it differs from the previous event's value."""
    engine = fresh_engine(read_text(MACH3_PP))
    engine.set(use_sc_feeds=False, original_feed=0, arc_direction='ccw', ccw='ccw', cw='cw', arc_size=90,
               radius=10, xcenter_rel=-10, ycenter_rel=0)
    engine.set(feed=0, xpos=0, ypos=0, zpos=0, cpos=0, apos=0, gcode=0, clear_change_after_gen=1,
               feed_f='4.3(p)', xpos_f='5.3', ypos_f='5.3', zpos_f='5.3', apos_f='5.3')
    engine.changed.update({key: False for key in ('feed', 'xpos', 'ypos', 'zpos', 'cpos', 'apos', 'gcode')})
    trace = []
    for procedure, values in events:
        for key in ('xpos', 'ypos', 'zpos', 'cpos', 'apos', 'feed'):
            engine.changed[key] = False
        for key, value in values.items():
            engine.changed[key] = engine.state[key] != value
            engine.state[key] = value
        engine.output.clear()
        engine.call(procedure)
        trace.append((procedure, values['feed'],
                      [b.strip() for b in ''.join(engine.output).splitlines() if b.strip()]))
    return trace


def feed_restatement_problems(events, procedures=None):
    """Feed changes that are not re-stated in a standalone G1 F block before
    their single motion block, as (procedure, feed, problem, blocks); only
    events of `procedures` are judged (default: all)."""
    problems = []
    previous = 0
    for procedure, feed, blocks in run_events(events):
        changed, previous = feed != previous, feed
        if procedures is not None and procedure not in procedures:
            continue
        motion = [index for index, block in enumerate(blocks) if MOTION.search(block)]
        if len(motion) != 1:
            problems.append((procedure, feed, 'expected exactly one motion block', blocks))
            continue
        if not changed:
            continue
        standalone = [index for index, block in enumerate(blocks) if STANDALONE_FEED.fullmatch(block)]
        if not standalone:
            problems.append((procedure, feed, 'feed change not restated in its own G1 block', blocks))
        elif float(STANDALONE_FEED.fullmatch(blocks[standalone[0]])[1]) != feed:
            problems.append((procedure, feed, 'restated feed differs from the CAM feed', blocks))
        elif standalone[0] > motion[0]:
            problems.append((procedure, feed, 'restated feed follows the motion block', blocks))
    return problems


@unittest.skipUnless(MACH3_PP.is_file(), f'Mach3 post not available ({MACH3_PP}); set MACH3_PP_SOURCE')
class Mach3FeedForceTests(unittest.TestCase):
    def test_feed_change_is_restated_in_separate_g1_block(self):
        """INDEPENDENT: the remedy recorded in 6efcad8: every feed change on
        @line/@line_4x is stated in a standalone 'G1 F<feed>' block that
        precedes the (single) motion block. The pre-6efcad8 post (ffd296c)
        carries the feed inline ('X20 F200') and fails."""
        self.assertEqual(feed_restatement_problems(EVENTS), [])

    @known_defect('PP-058')
    def test_line_5x_and_arc_feed_changes_are_restated_too(self):
        """INDEPENDENT: 6efcad8's own failure analysis (Mach3 forgets a changed
        feed unless it is re-stated) applies to every feed move; the remedy was
        added to @line, @line_4x and @move_object only, so @line_5x
        ('X20 A15 F250') and @arc ('G3 ... F600') still carry the changed feed
        inline. UNVERIFIED: no recorded Mach3 run shows the failure on these
        events, and the submodule may pin a different post version (PP-058
        uncertain). Only the @line_5x and @arc events are judged; the leading
        @line sets the previous feed and belongs to the regression test above."""
        self.assertEqual(feed_restatement_problems([
            ('line', dict(feed=1000, xpos=10)),
            ('line_5x', dict(feed=250, xpos=20, apos=15)),
            ('arc', dict(feed=600, xpos=30, ypos=10)),
        ], procedures=('line_5x', 'arc')), [])


if __name__ == '__main__':
    unittest.main()
