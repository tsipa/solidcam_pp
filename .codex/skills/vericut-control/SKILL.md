---
name: vericut-control
description: Work safely with CGTech VERICUT Siemens control files, especially `sin840d_special.ctl`, CDC/G41/G42 behavior, NC simulation debug, Vericut project syncing, and VMC PP Vericut assets. Use this skill whenever Codex edits, debugs, compares, syncs, or reasons about VERICUT control/project files or VERICUT simulation behavior.
---

# Vericut Control

## Core Paths

- Use `%PP_REPO%` for the local checkout of this repository. If it is unset, infer it from the current working directory or ask only if it cannot be inferred.
- Use `%VERICUT_WORKDIR%` for the active Vericut project/files directory. If it is unset, infer it from user context or ask only if it cannot be inferred.
- Repo Vericut destination relative to `%PP_REPO%`: `siemens_sinumerik_828d\noname_vmc500_4x\vericut`
- Main Siemens control overlay currently under investigation: `sin840d_special.ctl`
- Keep `%VERICUT_WORKDIR%\sin840d_special.ctl` and `%PP_REPO%\siemens_sinumerik_828d\noname_vmc500_4x\vericut\sin840d_special.ctl` identical after edits unless the user explicitly asks otherwise.

## Operating Rules

- Treat SolidCAM PP cutter compensation output as trusted unless the user explicitly asks to change PP behavior. For cutter compensation simulation issues, investigate Vericut control behavior first.
- When updating Vericut files, compare the working Vericut directory against the repo `vericut` directory and copy only changed/new intended project files.
- If setup is not 1, Vericut work offset `G54` / offset 54 should map to CSYS 2. To inspect the reference mapping, run a Vericut simulation on the default setup.
- Avoid keeping speculative CDC behavior changes unless the user confirms the tested behavior is correct. Do not leave behind experimental `CutterCompSuspend`, `CutterCompOnOffSwitches`, same-side `Already left/right compensation` no-op branches, or reordered direct `G40/G41/G42` groups after a failed test.

## Vericut Debug Safety

Vericut `ConditionMacro` branches can intercept normal handling. A debug-only branch can make Vericut log the line and skip the real motion or CDC macro.

Use this rule: if a debug condition matches an axis or CDC command, the same condition must also call the real macro that would have run without debug.

Safe axis debug pattern:

```xml
<ConditionMacro Description="CDC debug X left">
  <CondVariable Logical="and" Name="$P_GG[7]" Range="2"/>
  <Macro Name="LoggerMessage" Scan="no" AfterMotion="no">
    <Override Type="text" Value="CDC DBG: going to run X{$}; left comp; corrector {#$P_TOOLR}mm"/>
  </Macro>
  <Macro Name="XAxisMotion" Scan="no" AfterMotion="no">
  </Macro>
</ConditionMacro>
```

Use the corresponding real macro for each axis:

- `X` -> `XAxisMotion`
- `Y` -> `YAxisMotion`
- `Z` -> `ZAxisMotion`

Safe cutter compensation debug pattern:

```xml
<Group Name="G" Type="word" Description="CUTTER COMPENSATION: Tool radius compensation left of contour" Range="41" Field="0">
  <ConditionMacro Description="">
    <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
      <Override Type="value" Value="2" Units="0"/>
    </Variable>
    <Macro Name="LoggerMessage" Scan="no" AfterMotion="no">
      <Override Type="text" Value="CDC DBG: G41 left comp; corrector {#$P_TOOLR}mm"/>
    </Macro>
    <Macro Name="CutterCompLeft" Scan="no" AfterMotion="no">
    </Macro>
  </ConditionMacro>
</Group>
```

For `G42`, use the same pattern immediately before `CutterCompRight`.

## CDC Notes Learned

- VERICUT library controls generally implement CDC directly as `G41 -> CutterCompLeft`, `G42 -> CutterCompRight`, `G40 -> CutterCompOff`.
- Heidenhain library controls use `CutterCompSuspend` for an explicit suspend command such as `M98`; do not assume it is valid for normal `G41 <-> G42` transitions.
- Moving direct `G40/G41/G42` groups before axis motion changes same-block behavior. Restore original ordering if the test fails.
- `CutterCompOnOffSwitches` can change CDC turn-on/off behavior globally. Do not keep it after failed CDC tests.

## Validation Checklist

- Search for failed-test leftovers:

```powershell
Select-String -Path "$env:VERICUT_WORKDIR\sin840d_special.ctl" -Pattern 'Already|CutterCompOnOffSwitches|CutterCompSuspend|CDC DBG'
```

- Compare working and repo control files:

```powershell
$repoCtl = Join-Path $env:PP_REPO 'siemens_sinumerik_828d\noname_vmc500_4x\vericut\sin840d_special.ctl'
$workCtl = Join-Path $env:VERICUT_WORKDIR 'sin840d_special.ctl'
Compare-Object (Get-Content -LiteralPath $workCtl) (Get-Content -LiteralPath $repoCtl)
```

- Run repo diff check:

```powershell
git -C $env:PP_REPO diff --check -- siemens_sinumerik_828d/noname_vmc500_4x/vericut/sin840d_special.ctl
```
