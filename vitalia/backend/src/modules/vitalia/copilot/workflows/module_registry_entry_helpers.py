# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Helpers exposing module_registry_entry data to workflow consumers + tests.

Story 11 T-workflow-1 — thin re-export layer to decouple test/import paths
from the descriptor file location (which lives one level up at
`modules/vitalia/copilot/module_registry_entry.py` per ticket files_in_scope).

Import lift-shared candidate: when @luana/core grows a real workflow
registry, these helpers move to that shared package and the local
implementation becomes a thin call-through.
"""

from __future__ import annotations

from src.modules.vitalia.copilot.module_registry_entry import (
    vitalia_treatment_followup_descriptor,
)


def get_workflow_cost_budget_usd() -> float:
    """Return TreatmentFollowupWorkflow cost ceiling per D0→D90 cycle (USD).

    Used by:
      - test_total_cost_budget (V-AE-7 acceptance A4)
      - cost_budget validators V-AE-14/15/16
      - workflow runtime alert when state.cost_accumulated_usd nears ceiling
    """
    return vitalia_treatment_followup_descriptor.cost_budget_per_workflow_run


def get_workflow_observability_tags() -> tuple[str, ...]:
    """Return observability tags applied to copilot_trace_event metadata."""
    return vitalia_treatment_followup_descriptor.observability_tags


def get_workflow_trigger_event() -> str:
    """Return event name that triggers workflow start."""
    return vitalia_treatment_followup_descriptor.trigger_event
