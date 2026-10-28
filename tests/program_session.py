"""Whole-program driver for tests: init_post, user options, then SolidCAM-like events.

Each event writes its values into the SolidCAM variables. A motion variable (xpos, ypos, zpos, apos,
bpos, cpos, feed, spin) is flagged changed when the delivered value differs from the last value
SolidCAM delivered (the post's own assignments do not count); `force` overrides single flags.
Declared globals start at GPPL defaults (0, '', false) with the change flag false.

Engine conveniences, the same for every PP version: `Print` is a recorded no-op and zero-padded
integer literals (`07`) are read as numbers.
"""
import re
import unittest

from pp_tests.engine import Engine
from test_offline import PP

# The default engine (pp_tests.gppl) joins NC lines on a one-shot skipline and runs `input` and
# `abort` as separate statements; GPPL_ENGINE=legacy does neither, so tests of those skip there.
ENGINE_HAS_NC_STREAM = hasattr(Engine, 'nc_lines')


def require_nc_stream():
    if not ENGINE_HAS_NC_STREAM:
        raise unittest.SkipTest('needs the default GPPL engine (skipline joining, input/abort)')


def scripted_input_policies():
    """`input` answers 0 and continues, so a following `abort` is what stops the post."""
    from pp_tests.gppl.policies import Policies
    return Policies(input_stmt='scripted')


def post_abort_error():
    from pp_tests.gppl.errors import PostAbort
    return PostAbort

MOTION_KEYS = ('xpos', 'ypos', 'zpos', 'apos', 'bpos', 'cpos', 'feed', 'spin')

CONSTANTS = dict(cw='cw', ccw='ccw', xy='xy', zx='zx', yz='yz',
                 comp_left='comp_left', comp_right='comp_right', comp_off='comp_off',
                 g81='g81', g82='g82', g83='g83', g84='g84', g86='g86', d_tapping='d_tapping')

VMID = dict(iworkoffset_method=0, inumber_of_fixtures=0, blimit_3axis=False, sworkpcdir='',
            bstopm00=False, sstopmessage='', ig187_p=0, ng187_e=0.0, m50=0.0, m51=0.0,
            **{f'message{i}': '' for i in range(1, 11)})

CAM = dict(
    machine_plane='xy', first_tool=True, last_tool=False, tool_number=1, next_tool_number=2,
    next_job_tool_number=2, xnext=0, ynext=0, cnext=0, tool_start_plane=50, tool_z_level=50,
    job_name='op1', msg='', home_user_name='', home_number=1, position=1, rot_axis_coord=0,
    x5_job=True, job_type='profile', wall_offset=0, floor_offset=0, transform_type=0, loop_level=0,
    loop_count=0,
    rotate_angle_x=0, rotate_angle_y=0, rotate_angle_z=0, shift_x=0, shift_y=0, shift_z=0,
    angle_4x_around_x=0, angle_4x_around_x_dir='ccw', angle=0, cpos=0, apos=0, bpos=0,
    x_angle_const_z=0, dir5a='ccw', spin=3000, spin_rate=3000, tool_direction='cw',
    d_drill_type=-1, flood_coolant=1, mist_coolant=0, hp_flood_coolant=0, lp_flood_coolant=0,
    through_ival_coolant=0, through_coolant_val=0, lp_through_coolant=0, air_blast_coolant=0,
    air_through_coolant=0, xpos=0, ypos=0, zpos=0, feed=100, prev_command='@start_program',
    feed_type='feed_rate', tool_offset=5, side='comp_off', tool_side='comp_off', next_command='',
    tool_message='', message='', bprintloop=False,
    arc_plane='xy', arc_direction='ccw', arc_size=90, radius=10, xstart=0, ystart=0, zstart=0,
    xcenter=0, ycenter=0, zcenter=0, xcenter_rel=0, ycenter_rel=0, zcenter_rel=0,
    drill_type='g81', drill_clearance_z=10, drill_upper_z=0, drill_lower_z=-10, safety=2,
    delay=0, down_step=1, step_down=0, varretract=0, gcode=0,
)


def program_source(source=None):
    text = PP.read_text(encoding='utf-8-sig') if source is None else source
    return re.sub(r'(?im)^([ \t]*)print[ \t]+(.+)$', r'\1gppl_print_log = \2', text)


def declared_globals(text):
    result = {}
    for raw in text.splitlines():
        line = raw.split(';', 1)[0].strip()
        match = re.fullmatch(r'global\s+(numeric|integer|logical|string)\s+(.+)', line, re.I)
        if match:
            kind = match[1].lower()
            for name in match[2].replace(',', ' ').split():
                result[name.lower()] = '' if kind == 'string' else (False if kind == 'logical' else 0)
    return result


class ProgramEngine(Engine):
    def expression(self, value):
        chunks = re.split(r'''('(?:[^']|'')*'|"(?:[^"]|"")*")''', value)
        for index in range(0, len(chunks), 2):
            chunks[index] = re.sub(r'(?<![\w.])0+(?=\d)', '', chunks[index])
        return super().expression(''.join(chunks))


class Program:
    """One NC program. `options` override user options after init_post, `cam` the CAM defaults."""

    def __init__(self, options=None, cam=None, source=None, policies=None):
        text = program_source(source)
        engine = ProgramEngine(text) if policies is None else ProgramEngine(text, policies=policies)
        for name, value in declared_globals(text).items():
            engine.state[name] = value
        engine.state.update(CONSTANTS)
        engine.call('init_post')
        engine.state.update({k.lower(): v for k, v in (options or {}).items()})
        engine.state.update(VMID)
        engine.state.update(CAM)
        engine.state.update({k.lower(): v for k, v in (cam or {}).items()})
        for name in list(engine.state):
            engine.changed.setdefault(name, False)
        engine.call('usr_init_gmstates')
        for name in list(engine.changed):
            engine.changed[name] = False
        engine.output.clear()
        self.engine = engine
        self.cam_last = {k: engine.state.get(k) for k in MOTION_KEYS}
        self.prev = '@start_of_file'

    def ev(self, name, force=None, **values):
        """Deliver one event; return its NC blocks (stripped, empty blocks dropped)."""
        engine = self.engine
        values = {k.lower(): v for k, v in values.items()}
        flags = {key: key in values and values[key] != self.cam_last.get(key) for key in MOTION_KEYS}
        flags.update({k.lower(): v for k, v in (force or {}).items()})
        values.setdefault('prev_command', self.prev)
        engine.state.update(values)
        for key in MOTION_KEYS:
            engine.changed[key] = flags[key]
            if key in values:
                self.cam_last[key] = values[key]
        for key in values:
            engine.changed.setdefault(key, False)
        start = len(engine.output)
        engine.call(name)
        self.prev = '@' + name
        return [block.strip() for block in ''.join(engine.output[start:]).splitlines() if block.strip()]

    def nc(self):
        """The whole NC program as the control reads it (skipline joining applied)."""
        return [line.strip() for line in self.engine.nc_lines() if line.strip()]

    def start(self, tool=1, next_tool=2, **cam):
        """start_program, then the first tool change and start_of_job of tool `tool`."""
        blocks = self.ev('start_program')
        blocks += self.ev('change_tool', tool_number=tool, next_tool_number=next_tool, **cam)
        blocks += self.ev('start_of_job', job_name='op1')
        return blocks
