"""Legacy-compatible harness engines (rotary_engine, motion_engine, history_engine).

Byte-for-byte the presets of the original tests/test_offline.py,
tests/test_motion.py and tests/test_history_regressions.py helpers, built on
the cached parse (fresh_engine) instead of re-reading and re-parsing the GPP.
The original modules re-export these names, so `from test_offline import
rotary_engine` keeps working.

These are mid-job harnesses with hand-copied state (formats, modal values,
every change flag False). They never run @init_post, so they cannot see
defects in initial state or formats (e.g. zpos_f='8.5' here hides PP-006).
New tests should prefer support.session.Session; these remain for the legacy
fixtures and their area owners.
"""
from pp_tests.engine import Engine

from .engines import adopt_state, fresh_engine


def rotary_engine(source=None, **overrides):
    engine = fresh_engine(source)
    # Explicit CAM/environment defaults for isolated rotary procedure tests.
    engine.set(angle_4x_around_x=0, angle=0, cpos=0, apos=0, bpos=0,
               x_angle_const_z=0, iR1dir=-1, iR2dir=1,
               nPR1postemp=0, nPR1pos=0, nPR2pos=0, bLimit_3axis=False,
               bR1forceOutput=False, bR1useDir5a=True, dir5a='cw',
               angle_4x_around_x_dir='cw', cw='cw', ccw='ccw', cR1='A')
    engine.set(**overrides)
    return engine


def motion_engine(source=None):
    engine = rotary_engine(source)
    engine.call('usr_ip_useroptions')
    engine.set(X5_job=True, bJobPositioned=True, bCamLinkRetract=False, bPostHomed=False, bClimbZValid=False,
               machine_plane='xy', xy='xy', zx='zx', yz='yz',
               iFeedMode=94, bFeedPrevValid=True, nFeedPrevX=12, nFeedPrevY=23, nFeedPrevZ=10,
               nFeedPrevA=0, nFeedPrevR1=0, nInvFeed_f='5.3',
               bIndexClearancePending=False, bTlchg=False, bFirstRapid=False,
               bFirstMove=False, bFirstMovetlch=False, bVertical=False,
               bFirstVert=False, bSkipxyrapid=False, bFeedoutput=False,
               nLastPathZ=10, nLastPathWorkoffset=54, iWorkoffset=54,
               iPworkoffset=54, iMplane=17, iAbsincmode=90, iDiametercomp=40, iCompActive=40,
               iMotionmode=1, xpos=12, ypos=23, zpos=10, feed=100,
               tool_start_plane=35, tool_z_level=35, nPtool_z_level=35,
               nPtool_start_plane=35, prev_command='@line_5x',
               feed_type='feed_cut', job_type='contour', bStopM00=False,
               iWorkOffset_Method=0, rotate_angle_x=0, rotate_angle_y=0,
               rotate_angle_z=0, shift_x=0, shift_y=0, shift_z=0, position=1,
               rot_axis_coord=0, bSubs=False, bPrintloop=False, transform_type=0,
               job_name='fixture_operation', iG187_P=2, nG187_E=0,
               iG187_P_gpp=2, nG187_E_gpp=0,
               bStopM00difftool=False, bTmatrixIndexPending=False,
               sHomestrrot=engine.state['shomestrroth'],
               mcode_f='2.0(p)', clear_change_after_gen=1,
               xpos_f='8.5', ypos_f='8.5', zpos_f='8.5')
    engine.changed.clear()
    engine.changed.update({key: False for key in engine.state})
    engine.changed.update({key: False for key in ('apos', 'bpos', 'nrapidfeed')})
    engine.output.clear()
    return engine


def history_engine(source=None):
    engine = motion_engine()
    if source is not None:
        engine = adopt_state(engine, source, Engine)
    engine.set(COMP_LEFT='left', COMP_RIGHT='right', COMP_OFF='off',
               tool_number=7, last_tool=False, next_tool_number=8,
               drill_clearance_z=30, drill_upper_z=12, drill_lower_z=-15,
               safety=2, down_step=3, delay=0.25,
               G81='g81', G82='g82', G83='g83', G84='g84', G86='g86')
    return engine
