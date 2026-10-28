"""Read the parts of a SolidCAM .vmid that feed the GPP runtime.

* UserDefParams/MachineParams   -> global user variables (e.g. iNumber_of_Fixtures)
* UserDefParams/MillParamsJobs  -> per-job user variables (e.g. bStopM00)
* MillDrilCycles/DrillCycle     -> drill-cycle names (G81..), their DrillType and CycleParams
* PrecisionDef, WorkingStyle    -> recorded for reports only

The file is untrusted input: DOCTYPE/ENTITY declarations are refused before
parsing (no entity expansion), and only attributes are read.
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

VALUE_TYPES = {'1': 'logical', '2': 'string', '3': 'numeric', '5': 'integer'}


@dataclass
class UserParam:
    name: str
    vtype: str
    value: object
    group: str


@dataclass
class VmidConfig:
    machine_params: dict = field(default_factory=dict)
    job_params: dict = field(default_factory=dict)
    drill_cycles: dict = field(default_factory=dict)   # name -> {param: UserParam}
    drill_types: dict = field(default_factory=dict)    # name -> DrillType (int)
    precision: dict = field(default_factory=dict)
    working_style: dict = field(default_factory=dict)

    def all_params(self):
        merged = dict(self.machine_params)
        merged.update(self.job_params)
        for params in self.drill_cycles.values():
            merged.update(params)
        return merged

    def constants(self):
        """Drill-cycle names as constants of their DrillType: SolidCAM sends drill_type as that number
        (recorded_cam_003/005: drill_type:0 with drill_cycle_name:'G81', drill_type:2 with 'G83').
        A cycle without a DrillType attribute defines no constant."""
        return {name.lower(): number for name, number in self.drill_types.items()}


def _value(vtype, raw):
    if vtype == 'logical':
        return raw.strip() not in ('', '0', 'false', 'False')
    if vtype == 'integer':
        return int(float(raw or 0))
    if vtype == 'numeric':
        return float(raw or 0)
    return raw


def _param(element, group):
    vtype = VALUE_TYPES.get(element.get('ValueType', ''), 'string')
    name = element.get('GppName', '').lower()
    return UserParam(name, vtype, _value(vtype, element.get('Value', '')), group)


def parse_vmid(text):
    if re.search(r'<!DOCTYPE|<!ENTITY', text, re.I):
        raise ValueError('refusing VMID with DOCTYPE/ENTITY declarations')
    root = ET.fromstring(text)
    config = VmidConfig()
    for group_tag, target in (('MachineParams', config.machine_params), ('MillParamsJobs', config.job_params)):
        for group in root.iter(group_tag):
            for element in group:
                if element.get('GppName'):
                    param = _param(element, group_tag)
                    target[param.name] = param
    for cycle in root.iter('DrillCycle'):
        name = cycle.get('GppName')
        if not name:
            continue
        params = {}
        for element in cycle.iter('Param'):
            if element.get('GppName'):
                param = _param(element, f'DrillCycle:{name}')
                params[param.name] = param
        config.drill_cycles[name] = params
        drill_type = cycle.get('DrillType', '').strip()
        if re.fullmatch(r'-?\d+', drill_type):
            config.drill_types[name] = int(drill_type)
    for element in root.iter('PrecisionDef'):
        config.precision = dict(element.attrib)
    for element in root.iter('WorkingStyle'):
        config.working_style = {key: value for key, value in element.attrib.items()
                                if key in ('HomeDataAtStart', 'AtStartSetAllAxesToHomeRef',
                                           'AtEndSetAllAxesToHomeRef', 'SafetyDist', 'StartComment')}
    return config


def load_vmid(path):
    raw = Path(path).read_bytes()
    text = raw.decode('latin-1')
    return parse_vmid(text)
