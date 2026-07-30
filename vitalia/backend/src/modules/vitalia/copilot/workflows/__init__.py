# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Vitalia copilot workflows — registered via EP-4 in extensions.py.

Surface aggregation across Wave 2 (Story 11 T-workflow-1 treatment followup)
and Wave 4 (T-ag-workflows-1 Valeria wizard supervisor + extract_subagent).

Public surface — Treatment followup (Wave 2):
  - TreatmentFollowupState — workflow state TypedDict
  - build_treatment_followup_workflow — factory
  - handle_treatment_followup_tick — cron tick entry point
  - register_cron_handler — local registry decorator (lift-shared deferred)
  - get_workflow_cost_budget_usd — descriptor accessor for cost validators

Public surface — Wizard onboarding (Wave 4 — T-ag-workflows-1):
  - WizardOnboardingState — wizard supervisor state TypedDict
  - build_wizard_onboarding_graph — factory (LangGraph supervisor + deepagents
    extract_subagent; production checkpointer = luana_core_flows durable provider)
  - build_initial_state — initial state factory
  - build_extract_subagent_spec — deepagents SubAgent TypedDict
  - EXTRACT_SUBAGENT_NAME — public subagent name constant
  - compile_wizard_prompt + CompiledWizardPrompt + as_anthropic_system_blocks —
    5-slot cache-safe prompt compiler

Anti-duplication audit (per .claude/rules/anti-duplication.md):
  - Wave 2 surface: TreatmentFollowupWorkflow — see treatment_followup_workflow
    module docstring. No mirror risk.
  - Wave 4 surface: wizard state + supervisor graph + extract_subagent are
    brand-specific to Vitalia Valeria wizard onboarding. The engine
    `core/luana-core-copilot/` has no per-tenant onboarding wizard equivalent.
    If a second brand emerges with similar wizard surface, lift to engine via
    /pm-luana promotion proposal.
"""

# Wave 2 — treatment followup
from src.modules.vitalia.copilot.workflows.cron_handler import (
    get_registered_cron_handlers,
    handle_treatment_followup_tick,
    register_cron_handler,
)
from src.modules.vitalia.copilot.workflows.extract_subagent import (
    EXTRACT_SUBAGENT_NAME,
    build_extract_subagent_spec,
)
from src.modules.vitalia.copilot.workflows.module_registry_entry_helpers import (
    get_workflow_cost_budget_usd,
    get_workflow_observability_tags,
    get_workflow_trigger_event,
)
from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
    CheckpointerProtocol,
    TreatmentFollowupState,
    build_treatment_followup_workflow,
)

# Wave 4 — wizard supervisor + subagent
from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
    build_wizard_onboarding_graph,
)
from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
    WizardOnboardingState,
    build_initial_state,
)
from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
    CompiledWizardPrompt,
    as_anthropic_system_blocks,
    compile_wizard_prompt,
)

__all__ = [
    "EXTRACT_SUBAGENT_NAME",
    "CheckpointerProtocol",
    "CompiledWizardPrompt",
    "TreatmentFollowupState",
    "WizardOnboardingState",
    "as_anthropic_system_blocks",
    "build_extract_subagent_spec",
    "build_initial_state",
    "build_treatment_followup_workflow",
    "build_wizard_onboarding_graph",
    "compile_wizard_prompt",
    "get_registered_cron_handlers",
    "get_workflow_cost_budget_usd",
    "get_workflow_observability_tags",
    "get_workflow_trigger_event",
    "handle_treatment_followup_tick",
    "register_cron_handler",
]
