"""Machine-definition readers: VMID user parameters, Vericut control (.ctl)
G-function whitelist, Vericut machine (.mch) and GcodeSim.ini.

All readers skip the calling test (unittest.SkipTest) when the file is absent,
except vmid_user_parameters(), which falls back to the defaults copied from
Gmill_540v_4x.vmid so session tests also run on bare scratch copies.
"""
import functools
import re
from pathlib import Path

from .paths import CTL, GCODESIM_INI, MCH, VMID, read_text, require_file

# Gmill_540v_4x.vmid <UserDefParams> defaults (ValueType 1 logical, 2 string,
# 3 numeric, 5 integer). Used only when the VMID is not next to the GPP.
VMID_FALLBACK = {
    'iWorkOffset_Method': 0, 'iNumber_of_Fixtures': 0, 'bLimit_3axis': False, 'sWorkpcDir': '',
    **{f'Message{i}': '' for i in range(1, 11)},
    'bStopM00': False, 'sStopMessage': '', 'iG187_P': 0, 'nG187_E': 0.0, 'M50': 0.0, 'M51': 0.0,
}


def vmid_text():
    return require_file(VMID)


@functools.lru_cache(maxsize=None)
def _vmid_parameters(path):
    text = read_text(path, 'latin-1')
    section = re.search(r'<UserDefParams\b.*?</UserDefParams>', text, re.S)
    result = {}
    for tag, attrs in re.findall(r'<(Param|ParamJobs)\s+([^>]*)/>', section[0] if section else ''):
        fields = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        if 'GppName' not in fields or 'ValueType' not in fields:
            continue
        kind, default = fields['ValueType'], fields.get('DefaultValue', fields.get('Value', ''))
        if kind == '1':
            value = default not in ('', '0')
        elif kind == '2':
            value = default
        elif kind == '5':
            value = int(float(default or 0))
        else:
            value = float(default or 0)
        result[fields['GppName']] = (value, 'job' if tag == 'ParamJobs' else 'machine', kind)
    return result


def vmid_user_parameters(with_scope=False):
    """User-defined machine/job parameters SolidCAM supplies, at their VMID defaults.

    Returns {GppName: value}; with_scope=True returns {GppName: (value, scope, ValueType)}.
    """
    if not Path(VMID).exists():
        if with_scope:
            raise FileNotFoundError(VMID)
        return dict(VMID_FALLBACK)
    parameters = _vmid_parameters(str(VMID))
    if with_scope:
        return dict(parameters)
    return {name: value for name, (value, _, _) in parameters.items()}


def ctl_text():
    return require_file(CTL, 'utf-8')


def mch_text():
    return require_file(MCH)


def gcodesim_ini_text():
    return require_file(GCODESIM_INI)


@functools.lru_cache(maxsize=None)
def _g_functions(text):
    defined = set()
    for value in re.findall(r'<Group Name="G" Type="word" [^>]*Range="([^"]+)"', text):
        for part in re.split(r'[,\s]+', value.strip()):
            if not part:
                continue
            low, _, high = part.partition('-')
            defined.update(range(int(float(low)), int(float(high or low)) + 1))
    return frozenset(defined)


def g_function_whitelist():
    """G-function numbers the repository's 828D Vericut control defines.

    Oracle source: vericut/sin840d_special.ctl <Group Name="G" Type="word" Range=...>.
    Skips the test when the control file is absent.
    """
    return _g_functions(ctl_text())
