# VERICUT control initialization

`sin840d_special.ctl` loads `sin840d_special.def` from beside the control file.
Deploy both files together and reload the control/project (reset simulation) so
that VERICUT reads the new initialization.

The DEF is a local copy of the installed VERICUT 9.6.1 `library/sin840d.def`.
Its only changes are `$MC_TRAFO_TYPE_1`, `_2` and `_3`: `1` becomes `0`.
This configuration uses posted XYZ/A motion without TRAORI. The generic library
initialization advertises three transformations but leaves their input-axis
arrays zeroed. Library CYCLE832 then evaluates
`$MC_AXCONF_CHANAX_NAME_TAB[$MC_TRAFO_AXES_IN_n[3]-1]` with index -1, followed by
AXNAME and IS_ROT_AX errors. Disabling the unconfigured transformations avoids
that branch while retaining the real CYCLE832 implementation.

The installed CGTech library files and the postprocessor are unchanged. This is
not a TRAORI configuration: if TRAORI is introduced, configure its actual axis
mapping rather than re-enabling the generic placeholder transformation types.
After a VERICUT upgrade, compare the vendor DEF against this copy before adopting
new library initialization. Static file/XML checks passed. The user confirmed
that the previously failing program runs with this fix in VERICUT.
