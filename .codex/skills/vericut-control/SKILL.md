---
name: vericut-control
description: "Work safely with CGTech VERICUT project assets and control files: `.vcproject`, `.mch`, `.ctl`, `.spf`, `.ini`, tool libraries, project syncing, local/repo comparisons, and simulation/debug investigation. Use this skill whenever Codex edits, debugs, compares, syncs, or reasons about VERICUT files or VERICUT simulation behavior."
---

# Vericut Control

## Core Paths

- Use `%PP_REPO%` for the local checkout of this repository. If it is unset, infer it from the current working directory.
- Use `%VERICUT_WORKDIR%` for the active Vericut project/files directory. If it is unset, infer it from user context.
- Repo Vericut destination relative to `%PP_REPO%`: `siemens_sinumerik_828d\noname_vmc500_4x\vericut`
- Keep working Vericut files and repo Vericut files synchronized when the same file is intentionally changed in both places.

## Workflow

1. Identify the active Vericut file first: project (`.vcproject`), machine (`.mch`), control (`.ctl`), subprogram/cycle (`.spf`), config (`.ini`), or tooling data.
2. Compare the working Vericut directory against the repo Vericut directory before editing when both copies exist.
3. Make the smallest change that tests the current hypothesis.
4. Keep unrelated Vericut experiments out of commits. If a test fails, remove that test change before moving to the next hypothesis.
5. Before committing, show or inspect the exact diff and confirm only intended files are staged.

Useful PowerShell patterns:

```powershell
$repo = $env:PP_REPO
$work = $env:VERICUT_WORKDIR
$repoVericut = Join-Path $repo 'siemens_sinumerik_828d\noname_vmc500_4x\vericut'
Compare-Object (Get-Content -LiteralPath (Join-Path $work 'file.name')) (Get-Content -LiteralPath (Join-Path $repoVericut 'file.name'))
```

```powershell
Select-String -Path (Join-Path $work 'unnamed.vcproject') -Pattern 'Collision|Tolerance|NearMiss|ShankStockDist|GcodeSim|Work Offsets' -Context 2,2
```

## Debugging Control Files

Vericut `ConditionMacro` branches can intercept normal handling. A debug-only branch can log a match and prevent the real macro from running.

When adding debug to an existing control path, preserve the original behavior in the same matching branch:

```xml
<ConditionMacro Description="debug X motion">
  <CondVariable Logical="and" Name="$P_GG[7]" Range="2"/>
  <Macro Name="LoggerMessage" Scan="no" AfterMotion="no">
    <Override Type="text" Value="DBG: X{$}; state {#$P_GG[7]}"/>
  </Macro>
  <Macro Name="XAxisMotion" Scan="no" AfterMotion="no">
  </Macro>
</ConditionMacro>
```

General rule: if the debug condition matches a command that normally moves, changes state, loads data, or calls a Vericut macro, the debug branch must also call the same real macro or explicitly document why it is intentionally suppressing it.

Common real motion macros:

- `X` -> `XAxisMotion`
- `Y` -> `YAxisMotion`
- `Z` -> `ZAxisMotion`

For non-axis commands, insert `LoggerMessage` next to the existing real macro when possible instead of creating a competing condition branch.

## Validation

- Compare working and repo copies for files that should match.
- Run `git diff --check` on changed repo files.
- Use `git diff --cached --name-only` and `git diff --cached` before committing.
- Prefer committing Vericut asset/config changes separately from postprocessor logic changes unless the user explicitly asks for one combined commit.
