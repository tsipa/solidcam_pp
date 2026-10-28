"""Read public GPPL trace events; omit nested implementation trace calls."""
import re
from dataclasses import dataclass, field

from .gppl.sysvars import D_DRILL_TYPES

HEADER = re.compile(r'^\((\d+)\)@(\w+)\s*==>\s*(.*)$')
# SolidCAM prints VMID job parameters as 'name : value' with the string value unquoted, so an empty
# string leaves nothing before the next 'name :' ('sStopMessage :   iG187_P : 0') or the line end:
# a value is never a name followed by blanks and ':'. A value may contain ':' ('CHECK:PART').
PARAM = re.compile(r"(\w+)\s*:\s*('(?:[^']|'')*'|(?!\w+\s+:)[^\s]+)?")


@dataclass
class Event:
    name: str
    parameters: dict = field(default_factory=dict)
    changed: dict = field(default_factory=dict)
    output: list = field(default_factory=list)


def parameters(text, event):
    for match in PARAM.finditer(text):
        key, token = match.groups()
        key = key.lower()
        if token is None:
            value = ''
        elif token.startswith("'"):
            value = token[1:-1].replace("''", "'")
        else:
            number = re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([TF]?)', token)
            if number:
                value = float(number[1])
                if number[2]:
                    event.changed[key] = number[2] == 'T'
            elif token.lower() in ('true', 'false'):
                value = token.lower() == 'true'
            elif key == 'd_drill_type' and token.lower() in D_DRILL_TYPES:
                # @drill prints the number SolidCAM sends by its constant name (D_Drilling, D_Peck).
                value = float(D_DRILL_TYPES[token.lower()])
            else:
                value = token
        event.parameters[key] = value


def parse_trace(text):
    events = []
    current = None
    external_parameters = False
    for line in text.splitlines():
        header = HEADER.match(line)
        if header:
            depth, name, rest = header.groups()
            # Level zero and one are CAM events. Level >=2 are PP calls.
            external_parameters = int(depth) <= 1
            if external_parameters:
                current = Event(name.lower())
                events.append(current)
                parameters(rest, current)
            elif current and rest.strip():
                # Internal calls often emit their first NC fragment right after ==>.
                current.output.append(rest.rstrip())
            continue
        if current and '..>' in line and external_parameters:
            parameters(line.split('..>', 1)[1], current)
        elif current:
            output = re.match(r'^.{22}> ?(.*)$', line)
            if output:
                current.output.append(output[1].rstrip())
    if not events:
        raise ValueError('No GPPL trace events found; plain NC cannot recover CAM inputs')
    return events


def sanitize(events):
    """Remove all string payloads from portable input fixtures; preserve enums."""
    result = []
    identifiers = {'cw', 'ccw', 'xy', 'yz', 'zx', 'true', 'false', 'yes', 'no', 'no_action',
                   'comp_left', 'comp_right', 'comp_off'}
    for event in events:
        values = {key: (value if not isinstance(value, str) or value.lower() in identifiers
                        else '<redacted>') for key, value in event.parameters.items()}
        result.append({'name': event.name, 'parameters': values, 'changed': event.changed})
    return result
