"""Whole recorded SolidCAM programs through the post: tests/fixtures/recorded_cam_001..005.

Each recording is SolidCAM's own input for a real program (native trace, tests/fixtures/README.md).
support/recorded.py decompresses it in memory and replays every event through the tested GPP with
the session API, stopping at the first error. Per recording:

* posts_to_end_of_file (INDEPENDENT): the replay reaches @end_of_file without an error and nothing
  says POST ERROR. recorded_cam_004 does not today: its first job is face milling, which sends no
  wall_offset (PP-063, open; this is its canonical test).
* nc_matches_pin (CHARACTERIZATION): the replay ends where expected (at @end_of_file, or exactly at
  the stop of an open registry entry, support.recorded.KNOWN_STOPS), no POST ERROR, and the sha256
  of its normalized NC equals the pin in tests/fixtures/recorded_cam_nc_pins.json. A mismatch
  shows the first differing lines; regenerate the pins with
  python -m pp_tests.tools.recorded_pins --write [NAME ...] when the change is intended.

recorded_cam_001 (155k events: about 60 s and 2 GB) runs only with PP_RECORDED_ALL=1; the other
four take about 20 s. The replays run on the GPPL engine (pp_tests/gppl/session.py), so
GPPL_ENGINE=legacy skips them. reference_multijob is not replayed: recorded_cam_001 is the same
program recorded again with arc_size at 9 decimals (tests/fixtures/README.md).
"""
import os
import re
import unittest

from support import REGISTRY, known_defect
from support import recorded
from support.engines import ENGINE_NAME

ALL_ENV = 'PP_RECORDED_ALL'
SLOW = {'recorded_cam_001': '155k events, about 60 s and 2 GB'}


def replay_of(name):
    if ENGINE_NAME != 'gppl':
        raise unittest.SkipTest('the recorded replays run on the GPPL engine (pp_tests/gppl/session.py) only')
    if name in SLOW and os.environ.get(ALL_ENV) != '1':
        raise unittest.SkipTest(f'{name} ({SLOW[name]}) runs with {ALL_ENV}=1')
    return recorded.replay(name)


def describe(errors):
    return '; '.join(f'event {index} @{event} ({job} {job_type}): {message}'
                     for index, event, job, job_type, message in errors)


class RecordedReplayTests(unittest.TestCase):
    def assert_posts_to_end_of_file(self, name):
        result = replay_of(name)
        if result.errors:
            self.fail(f'{name} stopped: {describe(result.errors)}')
        self.assertEqual(result.last_event, 'end_of_file', name)
        self.assertEqual(result.post_errors, (), name)

    def assert_nc_matches_pin(self, name):
        result = replay_of(name)
        self.assertEqual(result.post_errors, (), name)
        stop = recorded.KNOWN_STOPS.get(name)
        if stop is None:
            self.assertEqual((result.errors, result.last_event), ((), 'end_of_file'),
                             f'{name} stopped: {describe(result.errors)}')
        else:
            defect_id, event, pattern = stop
            status = REGISTRY[defect_id].status
            self.assertEqual(status, 'open', f'{defect_id} is {status}: remove {name} from support.recorded.'
                                             'KNOWN_STOPS and regenerate its pin')
            self.assertEqual(len(result.errors), 1,
                             f'{name} must stop at {defect_id} (open), not: {describe(result.errors) or "no stop"}')
            _, stopped_at, _, _, message = result.errors[0]
            self.assertTrue(stopped_at == event and re.search(pattern, message),
                            f'{name} must stop at {defect_id} (@{event}: /{pattern}/), not: {describe(result.errors)}')
        pins = recorded.load_pins()
        self.assertIn(name, pins, f'no pin for {name}; run {recorded.REGENERATE} {name}')
        pin = pins[name]
        if recorded.make_pin(result)['sha256'] != pin['sha256']:
            self.fail(recorded.mismatch_message(name, pin, result))

    def test_recorded_cam_001_posts_to_end_of_file(self):
        """INDEPENDENT: SolidCAM's input of a real program (31 operations; the reference_multijob program
        recorded again) must post to @end_of_file without a POST ERROR."""
        self.assert_posts_to_end_of_file('recorded_cam_001')

    def test_recorded_cam_002_posts_to_end_of_file(self):
        """INDEPENDENT: SolidCAM's input of a real program must post to @end_of_file without a POST ERROR."""
        self.assert_posts_to_end_of_file('recorded_cam_002')

    def test_recorded_cam_003_posts_to_end_of_file(self):
        """INDEPENDENT: SolidCAM's input of a real program (drill jobs: G81, G83) must post to @end_of_file
        without a POST ERROR."""
        self.assert_posts_to_end_of_file('recorded_cam_003')

    @known_defect('PP-063', match="missing variable 'wall_offset'")
    def test_recorded_cam_004_posts_to_end_of_file(self):
        """INDEPENDENT: SolidCAM's input of a real program must post to @end_of_file without a POST ERROR.
        Its face_milling jobs send no wall_offset/floor_offset (operation_001, the first job, and 002, 009,
        011), so their CYCLE832 type cannot come from them: today @usr_smoothing reads wall_offset and the
        replay stops at the first job."""
        self.assert_posts_to_end_of_file('recorded_cam_004')

    def test_recorded_cam_005_posts_to_end_of_file(self):
        """INDEPENDENT: SolidCAM's input of a real program must post to @end_of_file without a POST ERROR."""
        self.assert_posts_to_end_of_file('recorded_cam_005')

    def test_recorded_cam_001_nc_matches_pin(self):
        """CHARACTERIZATION: the NC of recorded_cam_001 is the pinned one."""
        self.assert_nc_matches_pin('recorded_cam_001')

    def test_recorded_cam_002_nc_matches_pin(self):
        """CHARACTERIZATION: the NC of recorded_cam_002 is the pinned one."""
        self.assert_nc_matches_pin('recorded_cam_002')

    def test_recorded_cam_003_nc_matches_pin(self):
        """CHARACTERIZATION: the NC of recorded_cam_003 is the pinned one."""
        self.assert_nc_matches_pin('recorded_cam_003')

    def test_recorded_cam_004_nc_matches_pin(self):
        """CHARACTERIZATION: the NC of recorded_cam_004 up to its PP-063 stop is the pinned one."""
        self.assert_nc_matches_pin('recorded_cam_004')

    def test_recorded_cam_005_nc_matches_pin(self):
        """CHARACTERIZATION: the NC of recorded_cam_005 is the pinned one."""
        self.assert_nc_matches_pin('recorded_cam_005')


if __name__ == '__main__':
    unittest.main()
