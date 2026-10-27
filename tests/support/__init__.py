"""Shared test support for the Gmill_540v_4x.gpp suite (no tests in here).

Modules
  paths         ROOT, PP (PP_TEST_SOURCE), VMID, CTL, MCH, GCODESIM_INI, FIXTURES,
                pp_source(), require_file()
  defects       REGISTRY (PP-/ENGINE-/DESIGN- entries with location and per-facet
                confidence), AREAS (exclusive file ownership), OBSERVATIONS
  findings      render() of tests/PP_FINDINGS.md from the registry and the markers
                (python -m pp_tests.tools.findings --write)
  markers       @known_defect(id, facet=, match=), @covers(*ids), strict_mode()
                (PP_STRICT_KNOWN_DEFECTS=1)
  engines       ENGINE_NAME ('gppl' or 'legacy' with GPPL_ENGINE=legacy), fresh_engine(),
                adopt_state(), fork_engine(), nc_text(), GpplCompatEngine (documented
                ENGINE-xxx workarounds on the active engine), LegacyCompatEngine, WORKAROUNDS
  legacy        rotary_engine(), motion_engine(), history_engine() (legacy presets)
  session       Session (realistic SolidCAM event sessions, 'clear'/'persist' flag
                policy; replay_tail(), event_replay(), segment(), fork()), Segment,
                event(), AUTO, CAM_CONSTANTS, CAM_JOB_DEFAULTS, DRILL_DEFAULTS, SOLIDCAM_EVENTS
  nc            parse_blocks(), parse_block(), Block, Word, block_texts(), index_of(),
                last_index_of(), arc_center(), arc_sweep_degrees()
  modal         replay(), step(), state_before(), ModalState, DEFAULT_COOLANT_ON,
                SETTABLE_OFFSETS
  vericut       vmid_user_parameters(), g_function_whitelist(), ctl_text(), mch_text(),
                gcodesim_ini_text(), vmid_text(), VMID_FALLBACK
  mutation      mutate(), assert_detected(match=), StaleAnchor, UnrelatedKill
"""
from .paths import (CTL, FIXTURES, GCODESIM_INI, MACH3_PP, MCH, PP, ROOT, VERICUT, VMID,
                    pp_source, require_file)
from .defects import AREAS, REGISTRY, Defect
from .markers import STRICT_ENV, covers, known_defect, run_unmarked, strict_mode
from .engines import (ENGINE_NAME, LEGACY, WORKAROUNDS, GpplCompatEngine, LegacyCompatEngine, adopt_state,
                      fork_engine, fresh_engine, nc_text)
from .legacy import history_engine, motion_engine, rotary_engine
from .nc import (Block, Word, arc_center, arc_sweep_degrees, block_texts, index_of, last_index_of,
                 parse_block, parse_blocks)
from .modal import DEFAULT_COOLANT_ON, SETTABLE_OFFSETS, ModalState, replay, state_before
from .session import (AUTO, CAM_CONSTANTS, CAM_JOB_DEFAULTS, DRILL_DEFAULTS, MOTION_FLAGS,
                      SOLIDCAM_EVENTS, Segment, Session, event)
from .vericut import g_function_whitelist, vmid_user_parameters
from .mutation import StaleAnchor, UnrelatedKill, assert_detected, mutate
