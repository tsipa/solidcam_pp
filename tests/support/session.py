"""Realistic SolidCAM-like sessions and the CAM event step helper.

Session build order (documented change-flag policy)
---------------------------------------------------
1. CAM_CONSTANTS are set (SolidCAM enum constants the GPP compares against).
2. @init_post runs (it calls @usr_ip_useroptions and @usr_ip_postwriteroptions).
3. `options` overrides post options (e.g. i4xIndexClearanceMode=1). Values the
   GPP derives from options inside @init_post are NOT recomputed.
4. VMID user parameters are set at their VMID defaults, then `vmid` overrides.
5. CAM_JOB_DEFAULTS, then `cam` overrides, are set (CAM system variables).
6. header=False (default): @usr_init_gmstates runs and bStartFile=true is set,
   i.e. the state-changing part of @start_of_file without the header text.
   header=True: the real @start_of_file runs (needs HEADER_DEFAULTS; with
   iNumber_of_Fixtures > 1 it is mandatory: @start_of_file stops the post,
   multiple fixtures are not supported).
7. Change flags:
   flags='clear'   (default) every flag is cleared after initialisation, the
                   convention of the legacy harness. A first job therefore only
                   prints what its own events change.
   flags='persist' flags raised by the initialisation assignments stay pending
                   (stock-engine rule: a value-changing assignment raises the
                   flag). Whether SolidCAM keeps them is UNVERIFIED (ENGINE-001);
                   results that differ between the policies are engine-policy
                   dependent and must cite ENGINE-001 / PP-054.
   Every state key without a flag gets False (the engine requires explicit
   flags for modal [..] groups).
8. start=True additionally delivers @start_program.

Event step policy (event() and Session.ev())
--------------------------------------------
* values are assigned first (engine.set, which never touches change flags);
* the CAM motion flags in MOTION_FLAGS are reset to False, then every name in
  `changed` is set True (changed=AUTO marks the passed values whose value
  differs from the previous state instead); other flags keep their value;
* every state key without a flag gets False;
* Session.ev() also sets prev_command to '@<previous event>' unless the caller
  passes prev_command (track_prev_command=True; SolidCAM supplies the previous
  command name; the GPP compares it against '@line_5x' etc.).

Inspection helpers: text(), blocks(), replay(), replay_tail(since),
event_replay(mark), segment(mark) -> Segment, fork() (cheap copy of a built
session, e.g. a cached post-tool-change state).
"""
import copy

from .engines import GpplCompatEngine, fork_engine, fresh_engine
from .modal import replay, state_before
from .nc import index_of, last_index_of, parse_blocks
from .vericut import vmid_user_parameters

# drill_type SolidCAM sends for each drill cycle: its Gmill_540v_4x.vmid DrillType, the value of the
# constants G81..G86 (recorded_cam_003/005: drill_type:0 for G81, 2 for G83). d_drill_type is a number
# too: -1 in a milling job, D_Tapping 3 (CAMDBG d_tapping_value) in a tapping job.
DRILL_TYPE = dict(G81=0, G82=1, G83=2, G84=3, G86=4)
D_TAPPING = 3

# SolidCAM enum constants (names lower-cased by the engine; cw == CW).
CAM_CONSTANTS = dict(
    XY='xy', ZX='zx', YZ='yz', CW='cw', CCW='ccw', machine_plane='xy',
    COMP_LEFT='comp_left', COMP_RIGHT='comp_right', COMP_OFF='comp_off',
    **DRILL_TYPE, D_Tapping=D_TAPPING,
    MIRROR_OFF='mirror_off', MIRROR_X='mirror_x', MIRROR_Y='mirror_y', MIRROR_XY='mirror_xy',
)

# Representative CAM system variables for a first 4x contour job with tool 1.
# Synthetic values (not from a trace); every test that depends on one of them
# should pass it explicitly.
CAM_JOB_DEFAULTS = dict(
    first_tool=True, last_tool=False, tool_number=1, next_tool_number=2, next_job_tool_number=2,
    job_name='op1', msg='', tool_direction='cw', d_drill_type=-1, spin=8000, spin_rate=8000,
    flood_coolant=1, Mist_coolant=0, HP_Flood_coolant=0, LP_Flood_coolant=0,
    through_ival_coolant=0, through_coolant_val=0, LP_Through_coolant=0, Air_Blast_coolant=0,
    air_through_coolant=0, xnext=10, ynext=20, cnext=0, tool_start_plane=35, tool_z_level=35,
    angle_4x_around_x=0, angle_4x_around_x_dir='cw', angle=0, cpos=0, apos=0, bpos=0,
    x_angle_const_z=0, dir5a='cw', X5_job=True, job_type='profile', wall_offset=0, floor_offset=0,
    feed_type='feed_rate',
    prev_command='', next_command='', rotate_angle_x=0, rotate_angle_y=0, rotate_angle_z=0,
    shift_x=0, shift_y=0, shift_z=0, position=1, home_number=1, home_user_name='',
    rot_axis_coord=0, transform_type=0, loop_level=0, loop_count=0, bPrintloop=False,
    xpos=0, ypos=0, zpos=0, feed=500, tool_offset=1, side='comp_off', tool_side='comp_off',
)

# CAM inputs of a drilling job (@drill/@drill_point/@end_drill); pass them to
# the @drill event, e.g. s.ev('drill', ('xpos', 'ypos'), drill_type=DRILL_TYPE['G83'], **DRILL_DEFAULTS).
DRILL_DEFAULTS = dict(
    drill_clearance_z=30, drill_upper_z=12, drill_lower_z=-15, safety=2, down_step=3,
    delay=0.25, Step_Down=0, VarRetract=0,
)

# Inputs @start_of_file needs for its header (header=True).
HEADER_DEFAULTS = dict(
    part_name='P1', g_file_name='P1.mpf', full_g_file_name='C:\\cam\\P1.mpf',
    program_number=1, date='26-Oct-2026', time='14:41:00', remark='', tool_message='',
)

MOTION_FLAGS = ('xpos', 'ypos', 'zpos', 'apos', 'bpos', 'cpos', 'feed', 'spin')

# SolidCAM sends wall_offset and floor_offset with start_of_job only for the operation types that have
# them (recorded traces 001-005 and the reference trace: every milling operation but face_milling and
# thread, never drilling or 4x morphing). The post resets them between jobs (@usr_allowance_reset), so
# the drivers send them again at each start_of_job: the job's own values, else the last ones sent.
# NOT_SENT as a value sends nothing (an operation without an allowance).
ALLOWANCE_KEYS = ('wall_offset', 'floor_offset')


class _NotSent:
    def __repr__(self):
        return 'NOT_SENT'


NOT_SENT = _NotSent()


def sends_allowance(job_type):
    return job_type not in ('face_milling', 'thread', '4x_morph_between_curves') and 'drill' not in job_type


def with_allowance(event_name, values, job_type, sent):
    """values of one event as SolidCAM sends them; `sent` keeps the allowance last sent."""
    values = dict(values)
    for key in ALLOWANCE_KEYS:
        if values.get(key) is NOT_SENT:
            del values[key]
        elif key in values:
            sent[key] = values[key]
        elif event_name == 'start_of_job' and sends_allowance(job_type):
            values[key] = sent[key]
    return values


class _Auto:
    def __repr__(self):
        return 'AUTO'


AUTO = _Auto()

# SolidCAM procedures that are CAM events (called by SolidCAM, not by the GPP).
SOLIDCAM_EVENTS = frozenset({
    'init_post', 'start_of_file', 'def_tool', 'start_program', 'change_tool', 'tmatrix',
    'start_of_job', 'end_of_job', 'rapid_move', 'line', 'arc', 'arc_zx', 'arc_yz',
    'move_5x', 'line_5x', 'move_4x', 'line_4x', 'drill', 'drill_point', 'end_drill',
    'compensation', 'fourth_axis', 'machine_plane', 'home_number', 'message',
    'end_program', 'end_of_file', 'home_data', 'call_proc', 'proc', 'end_proc',
    'loop', 'end_loop', 'offset_change', 'm_feed_spin', 'start_tool', 'relative_mode',
    'absolute_mode', 'job_plane', 'rotate', 'mirror', 'change_ref_point',
})


def _fill_flags(engine):
    for key in list(engine.state):
        engine.changed.setdefault(key, False)


def event(engine, procedure, changed=(), **values):
    """Deliver one CAM event to engine and return the NC text it emitted."""
    previous = {key.lower(): engine.state.get(key.lower(), object()) for key in values}
    engine.set(**values)
    for key in MOTION_FLAGS:
        engine.changed[key] = False
    if changed is AUTO:
        for key, old in previous.items():
            engine.changed[key] = old != engine.state[key]
    else:
        if isinstance(changed, str):
            raise TypeError('changed must be a sequence of names or AUTO, not a string')
        for key in changed:
            engine.changed[key.lower()] = True
    _fill_flags(engine)
    start = len(engine.output)
    engine.call(procedure)
    return ''.join(engine.output[start:])


class Session:
    """One NC program built from SolidCAM-like events (see module docstring)."""

    def __init__(self, *, flags='clear', source=None, engine_class=GpplCompatEngine,
                 engine_options=None, options=None, vmid=None, header=False, start=False,
                 track_prev_command=True, **cam):
        if flags not in ('clear', 'persist'):
            raise ValueError(f"flags must be 'clear' or 'persist', not {flags!r}")
        engine = fresh_engine(source, engine_class, **(engine_options or {}))
        engine.set(**CAM_CONSTANTS)
        engine.call('init_post')
        engine.set(**(options or {}))
        parameters = vmid_user_parameters()
        parameters.update(vmid or {})
        engine.set(**parameters)
        job = dict(CAM_JOB_DEFAULTS)
        if header:
            job.update(HEADER_DEFAULTS)
        job.update(cam)
        self.allowance = {key: job[key] for key in ALLOWANCE_KEYS}
        engine.set(**job)
        _fill_flags(engine)
        for key in MOTION_FLAGS:
            engine.changed[key] = False
        if header:
            engine.call('start_of_file')
        else:
            if engine.state.get('inumber_of_fixtures', 0) > 1:
                raise ValueError('iNumber_of_Fixtures > 1 needs header=True (@start_of_file stops the post on it)')
            engine.call('usr_init_gmstates')
            engine.set(bStartFile=True)
        if flags == 'clear':
            for key in list(engine.changed):
                engine.changed[key] = False
        _fill_flags(engine)
        self.engine = engine
        self.flags = flags
        self.track_prev_command = track_prev_command
        self.header_text = ''.join(engine.output)
        engine.output.clear()
        self.log = []
        self._previous = None
        if start:
            self.ev('start_program')

    # -- events -----------------------------------------------------------
    def ev(self, procedure, changed=(), **values):
        """Deliver one event (policy in the module docstring); return its NC text."""
        name = procedure.lstrip('@').lower()
        if self.track_prev_command and 'prev_command' not in values and self._previous:
            values['prev_command'] = '@' + self._previous
        job_type = values.get('job_type', self.engine.state.get('job_type'))
        values = with_allowance(name, values, job_type, self.allowance)
        text = event(self.engine, name, changed, **values)
        self.log.append((name, text))
        self._previous = name
        return text

    def mark(self):
        """Position in the event log, for text(since=...)."""
        return len(self.log)

    def text(self, since=0):
        return ''.join(text for _, text in self.log[since:])

    def blocks(self, since=0):
        return parse_blocks(self.text(since))

    def replay(self, since=0):
        """Modal replay [(block, state_after)] of the program text from event `since`."""
        return replay(self.text(since))

    def replay_tail(self, since):
        """Whole-program modal replay restricted to the blocks emitted since event `since`.

        The states carry everything programmed before `since` (offset, A, motion).
        Raises RuntimeError when the first event text after `since` continues
        the previous block, because the tail could then not be split exactly.
        """
        text = self.text(since)
        if text and not text.startswith('\n'):
            raise RuntimeError(f'events since mark continue a block; cannot split the replay: {text[:40]!r}')
        full = self.replay()
        return full[len(full) - len(parse_blocks(text)):]

    def event_replay(self, mark, replayed=None):
        """[(block, modal state after it)] of the blocks emitted by event number `mark`.

        replayed: an existing whole-program replay to reuse (default: a fresh one).
        """
        replayed = self.replay() if replayed is None else replayed
        first = len(replayed) - len(parse_blocks(self.text(mark)))
        last = len(replayed) - len(parse_blocks(self.text(mark + 1)))
        return replayed[first:last]

    def segment(self, mark=0):
        """Segment of the blocks emitted since `mark` (see Segment)."""
        return Segment(self, mark)

    def fork(self):
        """Independent copy (state, change flags, output, event log).

        The parsed program stays shared (support.engines.fork_engine); state
        values are scalars, so shallow dict copies are independent.
        """
        clone = copy.copy(self)
        clone.engine, clone.log = fork_engine(self.engine), list(self.log)
        clone.allowance = dict(self.allowance)
        return clone

    @property
    def state(self):
        return self.engine.state

    # -- typical SolidCAM event groups -------------------------------------
    def first_tool(self, tool=1, next_tool=2, tmatrix=None, **job):
        """start_program, change_tool (first tool), optional tmatrix, start_of_job."""
        self.ev('start_program')
        self.ev('change_tool', first_tool=True, tool_number=tool, next_tool_number=next_tool,
                next_job_tool_number=next_tool, **job)
        if tmatrix is not None:
            self.ev('tmatrix', angle_4x_around_x=tmatrix)
        return self.ev('start_of_job', ('spin',))

    def next_tool(self, tool, next_tool, tmatrix=None, end=None, **job):
        """end_of_job, change_tool (not first), optional tmatrix, start_of_job."""
        self.ev('end_of_job', **(end or {}))
        self.ev('change_tool', first_tool=False, tool_number=tool, next_tool_number=next_tool,
                next_job_tool_number=next_tool, **job)
        if tmatrix is not None:
            self.ev('tmatrix', angle_4x_around_x=tmatrix)
        return self.ev('start_of_job', ('spin',))

    def same_tool_job(self, end=None, tmatrix=None, **job):
        """end_of_job, optional tmatrix, start_of_job without a tool change."""
        self.ev('end_of_job', **(end or {}))
        if tmatrix is not None:
            self.ev('tmatrix', angle_4x_around_x=tmatrix)
        return self.ev('start_of_job', **job)

    def cut(self, x, y, zclear, depth, apos=None, feed=None):
        """First rapid of a job (move_5x), plunge, one cut, retract (line_5x).

        The plunge flags feed as changed (first feed move of the job; SolidCAM
        flags the feed of the first cutting move). feed=None keeps the current
        CAM feed value.
        """
        values, changed = dict(xpos=x, ypos=y, zpos=zclear), ['xpos', 'ypos', 'zpos']
        if apos is not None:
            values['apos'] = apos
            changed.append('apos')
        self.ev('move_5x', changed, **values)
        plunge = dict(zpos=depth, feed_type='feed_rate')
        if feed is not None:
            plunge['feed'] = feed
        self.ev('line_5x', ('zpos', 'feed'), **plunge)
        self.ev('line_5x', ('xpos',), xpos=x + 5, feed_type='feed_rate')
        self.ev('line_5x', ('zpos',), zpos=zclear, feed_type='feed_rate')


class Segment:
    """Blocks emitted since a Session mark, with modal states from the whole-program replay.

    .blocks         parsed blocks emitted since the mark
    .states         ModalState after each of those blocks (whole-program replay,
                    so everything programmed before the mark is in effect)
    .before_first   ModalState in effect when the first block starts
    .shown          the blocks as text (for assertion messages)
    """

    def __init__(self, session, mark=0):
        program = session.blocks()
        replayed = replay(program)
        offset = len(program) - len(session.blocks(mark))
        self.blocks = program[offset:]
        self.states = [state for _, state in replayed[offset:]]
        self.before_first = state_before(replayed, offset)
        self.shown = '\n'.join(block.raw for block in self.blocks)

    def before(self, index):
        """Modal state in effect when block `index` starts (a negative index is an error)."""
        if index < 0:
            raise IndexError(f'block index {index}: the searched block was not found')
        return self.states[index - 1] if index > 0 else self.before_first

    def find(self, predicate, start=0, end=None):
        return index_of(self.blocks, predicate, start, end)

    def find_last(self, predicate, start=0, end=None):
        return last_index_of(self.blocks, predicate, start, end)

    def first_feed(self, start=0):
        """First block with axis motion while G1/G2/G3 is in effect (-1 if none)."""
        return next((index for index in range(start, len(self.blocks))
                     if self.blocks[index].is_motion and self.states[index].motion in (1, 2, 3)), -1)

    def dwell(self, start, end):
        """Seconds of G4 F<s> dwell in blocks [start, end)."""
        return sum(block.get('F', 0) for block in self.blocks[start:end] if 4 in block.g)
