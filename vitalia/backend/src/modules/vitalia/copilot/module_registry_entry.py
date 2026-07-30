# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Vitalia copilot module registry entry — TreatmentFollowupWorkflow descriptor.

Story 11 T-workflow-1 (R23 Opus 4.7 production AGENTIC code).

Per 02-design-agentic.md § 8.1 + 03-arch-agentic.md § 6.5.

Anti-duplication audit (per .claude/rules/anti-duplication.md):
  - `luana_core_copilot.domain.module_registry.ModuleDescriptor` exists but
    is a COPILOT DATA INTROSPECTION descriptor (model_class + read_fn for
    tenant data queries), NOT a workflow registry. The arch doc § 6.5 uses
    a different schema (workflow_slug + cron_schedule_rules + cost_budget).
  - Resolution: this file declares a vitalia-LOCAL `WorkflowDescriptor`
    dataclass capturing the workflow registration metadata per § 6.5.
    Runtime EP-4 wiring (`registry.copilot_workflow_register(WorkflowDef)`)
    already happened in T-extensions-1 with empty steps tuple — that
    placeholder remains the canonical entry; this file documents the
    descriptor shape per design intent.
  - Lift-shared candidate: when @luana/core grows a real workflow registry
    (post-Story 14+ if 2nd vertical workflow appears per D3 staging), this
    descriptor lifts to shared with NO-NEW-LAYER discipline.

Decisions honored:
  D3  — TreatmentFollowupWorkflow inherits StateGraph directly (no shared base
        BaseWorkflowOrchestrator). Descriptor here documents the workflow
        identity + cron rules + observability tags + cost budget.
  D7  — compliance_level=hipaa_lite (eligible_clinic_types limited to
        dental/psychology/psychiatry; wellness deferred Q7 ratified).
  D10 — RedisSaver checkpointer cross-brand (state_persister="redis_saver"
        documented; runtime swap via `treatment_followup_workflow.build_*`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# ════════════════════════════════════════════════════════════════════════════
# Cron rule schema (lift-shared candidate when @luana/core scheduling lands)
# ════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class CronRule:
    """Cron tick scheduling rule per workflow milestone.

    Future: lift to @luana/core/scheduling when shared cron primitive lands
    (per cron_handler.py anti-duplication audit).
    """

    milestone: Literal["D5", "D14", "D90"]
    offset_days: int  # days from procedure_date
    hour_local: int  # tenant local TZ hour (0-23)


# ════════════════════════════════════════════════════════════════════════════
# Workflow descriptor (vitalia-local)
# ════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class WorkflowDescriptor:
    """TreatmentFollowupWorkflow registration metadata.

    Mirrors arch doc § 6.5 fields. Consumed by:
      - cron_handler.py for scheduling derivation
      - extensions.py future re-registration with `WorkflowDef.steps` populated
      - observability tagging (copilot_trace_event metadata)
      - cost-budget enforcement (validators V-AE-7 + V-AE-14/15/16)
    """

    workflow_slug: str
    workflow_class: str
    version: str
    eligible_tenants_filter: dict[str, str]
    eligible_clinic_types: tuple[str, ...]
    not_eligible_clinic_types: tuple[str, ...]
    trigger_event: str
    cron_schedule_rules: tuple[CronRule, ...]
    state_persister: Literal["memory_saver", "redis_saver", "postgres_saver"]
    observability_tags: tuple[str, ...]
    cost_budget_per_workflow_run: float  # USD ceiling per complete D0→D90 cycle


# ════════════════════════════════════════════════════════════════════════════
# Vitalia TreatmentFollowupWorkflow descriptor instance
# ════════════════════════════════════════════════════════════════════════════


vitalia_treatment_followup_descriptor = WorkflowDescriptor(
    workflow_slug="vitalia.treatment_followup",
    workflow_class="TreatmentFollowupWorkflow",
    version="v1",
    eligible_tenants_filter={"brand_slug": "vitalia"},
    eligible_clinic_types=("dental", "psychology", "psychiatry"),
    not_eligible_clinic_types=("wellness",),  # Q7 ratified — defer Story 11.bis
    trigger_event="ProcedureCompleted",  # or BookingConfirmed for psychology/psychiatry
    cron_schedule_rules=(
        CronRule(milestone="D5", offset_days=5, hour_local=8),
        CronRule(milestone="D14", offset_days=14, hour_local=8),
        CronRule(milestone="D90", offset_days=90, hour_local=8),
    ),
    state_persister="redis_saver",  # D10 ratified target; current MemorySaver until package install
    observability_tags=("workflow=treatment_followup", "vertical=medical"),
    cost_budget_per_workflow_run=0.25,  # USD ceiling per complete D0→D90 cycle (V-AE-7 + A4)
)
