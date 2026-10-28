"""SolidCAM runtime model: system variables, per-event input contracts,
enumeration constants and PP->runtime control variables.

Provenance matters more than completeness here. Each contract entry was
inferred from what the 4x GPP reads inside the event procedure's call closure
(``analysis.event_contracts`` recomputes that from source and reports drift)
plus generic GPPL knowledge; none of it is copied from SolidCAM documentation.
A captured trace replaces inference: ``Session`` records which variables each
real event actually supplied.
"""

# --- event input contracts ----------------------------------------------------
# event -> variables SolidCAM is expected to (re)supply when it calls @event.
_MOTION = ('xpos', 'ypos', 'zpos', 'feed', 'feed_type', 'prev_command', 'next_command')
_ARC = _MOTION + ('xstart', 'ystart', 'zstart', 'xcenter', 'ycenter', 'zcenter',
                  'xcenter_rel', 'ycenter_rel', 'zcenter_rel', 'arc_size', 'arc_direction',
                  'arc_plane', 'radius')
_FIVE = _MOTION + ('apos', 'bpos', 'cpos', 'dir5a')
_COOLANT = ('flood_coolant', 'mist_coolant', 'hp_flood_coolant', 'lp_flood_coolant',
            'through_ival_coolant', 'through_coolant_val', 'lp_through_coolant',
            'air_blast_coolant', 'air_through_coolant')
_TRANSFORM = ('angle_4x_around_x', 'angle_4x_around_x_dir', 'x_angle_const_z', 'y_angle_const_z',
              'shift_x', 'shift_y', 'shift_z', 'rotate_angle_x', 'rotate_angle_y', 'rotate_angle_z')

EVENT_CONTRACTS = {
    'start_of_file': ('part_name', 'program_number', 'date', 'time', 'g_file_name', 'full_g_file_name',
                      'stock_x', 'stock_y', 'stock_z', 'stock_x_minus', 'stock_y_minus',
                      'stock_z_plus', 'stock_z_minus', 'target_z_minus', 'fourth_axis_used'),
    'def_tool': ('tool_number', 'tool_offset', 'tool_length', 'holder_name', 'tool_message',
                 'msg_mill_tool1', 'msg_mill_tool2', 'msg_mill_tool3', 'msg_mill_tool4',
                 'msg_mill_tool5', 'next_command'),
    'start_program': (),
    'change_tool': ('tool_number', 'first_tool', 'last_tool', 'next_tool_number', 'xnext', 'ynext',
                    'cnext', 'tool_start_plane', 'tool_direction', 'spin', 'd_drill_type',
                    'tool_message', 'tool_offset'),
    'start_of_job': ('job_name', 'job_type', 'msg', 'home_number', 'home_user_name', 'position',
                     'rot_axis_coord', 'x5_job', 'transform_type', 'tool_z_level', 'tool_start_plane',
                     'xnext', 'ynext', 'spin_rate', 'spin', 'tool_direction', 'd_drill_type',
                     'loop_level', 'loop_count', 'next_job_tool_number', 'apos', 'bpos', 'cpos',
                     'angle', 'shift_x', 'shift_y', 'shift_z', 'rotate_angle_x', 'rotate_angle_y',
                     'rotate_angle_z', 'wall_offset', 'floor_offset') + _COOLANT,
    'end_of_job': ('next_job_tool_number', 'tool_z_level', 'tool_start_plane'),
    'rapid_move': _MOTION,
    'line': _MOTION,
    'arc': _ARC, 'arc_zx': _ARC, 'arc_yz': _ARC,
    'move_5x': _FIVE, 'line_5x': _FIVE, 'move_4x': _FIVE, 'line_4x': _FIVE,
    'compensation': ('side', 'tool_side'),
    'machine_plane': ('machine_plane',),
    'tmatrix': _TRANSFORM,
    'fourth_axis': ('angle',),
    'drill': ('drill_type', 'drill_clearance_z', 'drill_upper_z', 'drill_lower_z', 'safety',
              'down_step', 'delay', 'feed', 'spin', 'xpos', 'ypos', 'zpos', 'd_drill_type'),
    'drill_point': ('xpos', 'ypos', 'zpos'),
    'end_drill': ('drill_type',),
    'm_feed_spin': ('spin', 'feed', 'tool_direction'),
    'start_tool': ('spin', 'tool_direction', 'd_drill_type'),
    'offset_change': ('tool_number',),
    'change_ref_point': ('home_number', 'xhome', 'yhome', 'zhome'),
    'call_proc': ('label', 'message', 'xnext', 'ynext', 'tool_start_plane'),
    'proc': ('label',),
    'end_proc': (),
    'loop': ('loop_level', 'loop_count'),
    'end_loop': ('loop_level',),
    'loop_matrix_info': (),
    'message': ('message',),
    'home_data': ('home_user_name', 'home_number', 'position', 'shift_x', 'shift_y', 'shift_z',
                  'y_angle_const_z'),
    'relative_mode': (), 'absolute_mode': (), 'rotate': (), 'mirror': (), 'job_plane': (),
    'chng_tool_cnext': (), 'rotary_info': (), 'tool_path_info': (), 'transform_info': (),
    'end_program': (), 'end_of_file': (),
}
LIFECYCLE = ('init_post', 'start_of_file', 'end_of_file')

# --- system variable types (for typed formats, replay type normalisation) ----
_TYPES = {
    'integer': ('tool_number', 'next_tool_number', 'next_job_tool_number', 'program_number',
                'home_number', 'position', 'loop_level', 'loop_count', 'label', 'rot_axis_coord',
                'transform_type', 'gcode', 'mcode', 'flood_coolant',
                'mist_coolant', 'hp_flood_coolant', 'lp_flood_coolant', 'through_ival_coolant',
                'through_coolant_val', 'lp_through_coolant', 'air_blast_coolant',
                'air_through_coolant', 'blknum', 'blknum_delta', 'blknum_max', 'num_user_procs',
                'clear_change_after_gen'),
    'logical': ('first_tool', 'last_tool', 'x5_job', 'fourth_axis_used', 'skipline', 'blknum_exist',
                'blknum_gen', 'remove_blanks', 'line_labels'),
    'string': ('part_name', 'date', 'time', 'g_file_name', 'full_g_file_name', 'job_name', 'job_type',
               'msg', 'message', 'home_user_name', 'tool_message', 'holder_name', 'msg_mill_tool1',
               'msg_mill_tool2', 'msg_mill_tool3', 'msg_mill_tool4', 'msg_mill_tool5',
               'prev_command', 'next_command', 'feed_type', 'dir5a', 'arc_direction', 'arc_plane',
               'machine_plane', 'side', 'tool_side', 'tool_direction', 'drill_type', 'd_drill_type',
               'angle_4x_around_x_dir', 'blknum_letter', 'end_block_text', 'numeric_def_f',
               'integer_def_f', 'gcode_f', 'mcode_f', 'xpos_f', 'ypos_f', 'zpos_f', 'apos_f',
               'feed_f', 'blknum_f'),
}
SYSTEM_TYPES = {name: kind for kind, names in _TYPES.items() for name in names}
for _names in EVENT_CONTRACTS.values():
    for _name in _names:
        SYSTEM_TYPES.setdefault(_name, 'numeric')

# PP -> runtime control variables and the value assumed when never assigned.
CONTROL_DEFAULTS = {
    'skipline': True, 'clear_change_after_gen': 0, 'blknum_exist': False, 'blknum_gen': False,
    'blknum': 1, 'blknum_delta': 1, 'blknum_max': 99999, 'blknum_letter': 'N',
    'remove_blanks': False, 'line_labels': False, 'num_user_procs': 0, 'end_block_text': '',
}
CONTROL_VARIABLES = set(CONTROL_DEFAULTS) | {'numeric_def_f', 'integer_def_f', 'gcode_f', 'mcode_f',
                                              'blknum_f'}
# Output formats SolidCAM defines itself (names: SolidCAM GPPTool Help, via the GPPL IDE catalog).
# Any other '<name>_f' format is a PP variable and needs a declaration (Analysis.classify).
SYSTEM_FORMATS = frozenset({'numeric_def_f', 'integer_def_f', 'gcode_f', 'mcode_f', 'xpos_f', 'ypos_f',
                            'zpos_f', 'apos_f', 'feed_f', 'blknum_f'})

# Enumeration constants: the value is the spelling SolidCAM prints in its trace.
# Observed in tests/fixtures/reference_multijob.trace.txt.xz: arc_plane:xy,
# machine_plane:xy, arc_direction/dir5a/tool_direction:cw|ccw, side:comp_left|
# comp_off, tool_side:comp_left. comp_right, zx/yz, G8x (VMID drill cycles),
# d_tapping and mirror_* are not in that trace (unverified).
CONSTANTS = {
    'xy': 'xy', 'zx': 'zx', 'yz': 'yz', 'cw': 'cw', 'ccw': 'ccw',
    'comp_left': 'comp_left', 'comp_right': 'comp_right', 'comp_off': 'comp_off',
    'd_tapping': 'd_tapping',
    'mirror_off': 'mirror_off', 'mirror_x': 'mirror_x', 'mirror_y': 'mirror_y', 'mirror_xy': 'mirror_xy',
}
CONSTANT_STATUS = {name: 'used-by-4x-gpp' for name in ('xy', 'zx', 'yz', 'cw', 'ccw', 'comp_left',
                                                      'comp_right', 'comp_off', 'd_tapping')}

# Format-valid stand-ins for strings redacted by trace.sanitize().
REDACTION_SUBSTITUTES = {
    'date': '01-JAN-2000', 'time': '12:00:00', 'part_name': 'PART', 'g_file_name': 'PART.MPF',
    'full_g_file_name': 'C:\\CAM\\PART.MPF', 'job_name': 'JOB', 'home_user_name': 'G54',
    'msg': '', 'message': '', 'tool_message': '', 'holder_name': 'HOLDER',
    'msg_mill_tool1': '', 'msg_mill_tool2': '', 'msg_mill_tool3': '', 'msg_mill_tool4': '',
    'msg_mill_tool5': '', 'job_type': 'profile', 'feed_type': 'feed_rate',
}
REDACTED = '<redacted>'

# CAM vocabulary that drives PP branches. trace.sanitize() redacts these (its
# allow-list only keeps cw/ccw/xy/yz/zx/...), which makes a sanitized capture
# un-replayable at the first compensation/drill/link event; replay refuses to
# guess them and session.sanitize_for_replay() keeps them.
REPLAY_ENUMS = ('feed_type', 'side', 'tool_side', 'drill_type', 'd_drill_type', 'job_type',
                'arc_direction', 'arc_plane', 'machine_plane', 'dir5a', 'tool_direction',
                'angle_4x_around_x_dir', 'prev_command', 'next_command')


def system_type(name):
    return SYSTEM_TYPES.get(name)


def is_known_system(name):
    return (name in SYSTEM_TYPES or name in CONTROL_VARIABLES or name.endswith('_f')
            or name in CONSTANTS)
