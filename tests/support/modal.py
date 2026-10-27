"""Modal state replay over emitted NC blocks (Sinumerik 828D semantics).

Use it for oracles of the form "the state in effect at block N must be ...",
e.g. coolant active at the first cut, plane at a TRC activation, work offset at
each motion. Rules (Siemens 828D programming manual, group numbers in brackets):
  motion  G0/G1/G2/G3 (group 1); a CYCLExx/MCALL does not change it
  plane   G17/G18/G19 (group 6)
  trc     G40/G41/G42 (group 7)
  offset  G54..G57, G505..G599, G500 (group 8); G53 is block-wise and ignored
  dist    G90/G91 (group 14); a G90/G91 in a block applies to its own axis words
  feed_mode G93/G94/G95 (group 15); None means the power-on default G94
  feed    F in a block without G4 (F in a G4 block is the dwell time)
  spindle M3/M4/M5 and S
  coolant every M in coolant_on is added to the active set; M9 clears all
  tool    T selects (tool_selected), M6 loads it (tool)
  rotary  A=ACP/ACN/DC(v), A=IC(v) (relative) or A<v> sets the A position
  homing  G75 X1=0/Y1=0/Z1=0: the axis is at its reference point and its
          workpiece position is unknown until an X/Y/Z word programs it again
  mcall   MCALL CYCLExx(...) makes the cycle modal; a bare MCALL cancels it
"""
import dataclasses
from dataclasses import dataclass

from .nc import parse_blocks

# M codes that switch a coolant channel on in Gmill_540v_4x.gpp
# (@usr_ip_useroptions iCoolantM1ON..M8ON and the through-coolant pressure
# table in @usr_coolant: 77, 76, 75, 07, 71..74). M9 is the shared off code.
DEFAULT_COOLANT_ON = frozenset({7, 8, 50, 51, 71, 72, 73, 74, 75, 76, 77, 92, 130})
COOLANT_OFF = 9
# Siemens settable zero offsets: G54..G57 and G505..G599. G500 deactivates the
# settable offset; G58/G59 are axial (additive) offsets, not settable frames.
SETTABLE_OFFSETS = frozenset(range(54, 58)) | frozenset(range(505, 600))
WORK_OFFSETS = SETTABLE_OFFSETS | {500}


@dataclass(frozen=True)
class ModalState:
    motion: int = None
    plane: int = None
    trc: int = None
    work_offset: int = None
    distance: int = None
    feed_mode: int = None                  # G93/G94/G95 (group 15); None = power-on G94
    feed: float = None
    spindle: int = None
    speed: float = None
    coolant: frozenset = frozenset()
    tool_selected: float = None
    tool: float = None
    a: float = None
    a_mode: str = None
    position: tuple = (None, None, None)   # last programmed X, Y, Z (None = unknown)
    homed: frozenset = frozenset()         # axes at reference after G75, not re-programmed
    mcall: str = None

    def xyz(self):
        return dict(zip('XYZ', self.position))


def step(state, block, coolant_on=DEFAULT_COOLANT_ON):
    """State after executing one parsed block."""
    changes = {}
    g_codes = block.g
    for code in g_codes:
        if code in (0, 1, 2, 3):
            changes['motion'] = code
        elif code in (17, 18, 19):
            changes['plane'] = code
        elif code in (40, 41, 42):
            changes['trc'] = code
        elif code in WORK_OFFSETS:
            changes['work_offset'] = code
        elif code in (90, 91):
            changes['distance'] = code
        elif code in (93, 94, 95):
            changes['feed_mode'] = code
    # A G90/G91 written in a block already applies to that block's axis words
    # (Sinumerik: the distance-mode G functions are modal and take effect in
    # their own block).
    distance = changes.get('distance', state.distance)
    if 4 not in g_codes and block.get('F') is not None:
        changes['feed'] = block.get('F')
    if block.get('S') is not None:
        changes['speed'] = block.get('S')
    coolant = set(state.coolant)
    for code in block.m:
        if code in (3, 4, 5):
            changes['spindle'] = code
        elif code == COOLANT_OFF:
            coolant.clear()
        elif code in coolant_on:
            coolant.add(code)
        elif code == 6:
            changes['tool'] = changes.get('tool_selected', state.tool_selected)
    changes['coolant'] = frozenset(coolant)
    if block.get('T') is not None:
        changes['tool_selected'] = block.get('T')
    rotary = block.rotary('A')
    if rotary is not None:
        mode, value = rotary
        if mode == 'IC' and state.a is not None:
            value = state.a + value
        changes['a'], changes['a_mode'] = value, mode
    position, homed = list(state.position), set(state.homed)
    homing = block.homing_axes
    for index, axis in enumerate('XYZ'):
        if axis in homing:
            position[index] = None
            homed.add(axis)
    if not homing:
        for axis, value in block.axes.items():
            index = 'XYZ'.index(axis)
            if distance == 91 and position[index] is not None:
                value = position[index] + value
            position[index] = value
            homed.discard(axis)
    changes['position'], changes['homed'] = tuple(position), frozenset(homed)
    for word in block.words:
        if word.address == 'MCALL':
            cycle = block.cycle
            changes['mcall'] = cycle[0] if cycle else None
    return dataclasses.replace(state, **changes)


def replay(blocks, initial=None, coolant_on=DEFAULT_COOLANT_ON):
    """[(block, state_after_block)] for NC text or parsed blocks."""
    if isinstance(blocks, str):
        blocks = parse_blocks(blocks)
    state = initial or ModalState()
    result = []
    for block in blocks:
        state = step(state, block, coolant_on)
        result.append((block, state))
    return result


def state_before(replayed, index, initial=None):
    """Modal state in effect when block `index` of a replay starts."""
    return replayed[index - 1][1] if index > 0 else (initial or ModalState())
