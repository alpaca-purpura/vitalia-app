# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Vitalia copilot tools — LangChain @tool surfaces for the wizard supervisor.

Per .claude/rules/anti-duplication.md (cross-brand mirror scan) — these tools
are vitalia-specific brand extensions. If a sibling tool pattern emerges in
{nicolify, comunify, lupulo} → lift to engine via /pm-vitalia proposal first
(NEVER mirror cross-brand).

Tool inventory:
  - ``extract_tenant_context`` — wraps ExtractTenantContextService
  - ``confirm_slot`` — wraps OnboardingDraftService.update_slot
  - ``simulate_personality`` — wraps SimulatePersonalityService (throttle + cache)
  - ``complete_onboarding`` — wraps CompleteOnboardingService

All tools are LangChain ``@tool`` decorated, async, with Pydantic v2
``args_schema``. They call SERVICES (never raw repos). ``tenant_id: UUID``
mandatory in every input schema (HIPAA-lite tenant isolation cardinal).

Registered via Extension SDK EP-3 in ``vitalia/backend/src/modules/vitalia/extensions.py``.
"""

from __future__ import annotations

from src.modules.vitalia.copilot.tools.complete_onboarding import (
    CompleteOnboardingInput,
    complete_onboarding,
)
from src.modules.vitalia.copilot.tools.confirm_slot import (
    ConfirmSlotInput,
    confirm_slot,
)
from src.modules.vitalia.copilot.tools.extract_tenant_context import (
    ExtractTenantContextInput,
    extract_tenant_context,
)
from src.modules.vitalia.copilot.tools.simulate_personality import (
    SimulatePersonalityInput,
    simulate_personality,
)

__all__ = [
    "CompleteOnboardingInput",
    "ConfirmSlotInput",
    "ExtractTenantContextInput",
    "SimulatePersonalityInput",
    "complete_onboarding",
    "confirm_slot",
    "extract_tenant_context",
    "simulate_personality",
]
