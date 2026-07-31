# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""WizardOnboardingState — TypedDict state schema for Valeria wizard supervisor.

Per 03-arch-agentic.md § 2.1 + 05-guidelines.md § 1.11 LangGraph patterns:

- ``tenant_id`` MANDATORY (tenant-isolation cardinal — every state carries it).
- ``iterations: int`` for max-iter guard (cap 25 per copilot-resilience
  ``COPILOT_RECURSION_LIMIT``).
- Slot machinery (required / optional / pending / bonus) for the wizard
  conversation contract.
- deepagents subagent bridge (``extraction_subagent_input`` →
  ``extraction_subagent_output``) — orchestrator/sandbox isolation surface.
- Compliance flags + completion guard for honest trace recorder.

Anti-duplication audit (per `.claude/rules/anti-duplication.md` § Inventario):

  - This state is **brand-specific to Vitalia Valeria wizard onboarding**. It
    does NOT mirror any existing engine state — the wizard supervisor is brand
    extension (the engine copilot has no per-tenant onboarding wizard). Other
    brands (nicolify, comunify, lupulo) do not have an analogous concept.
  - If a SECOND brand emerges with a similar wizard surface, this state class
    should be lifted to engine `core/luana-core-copilot/` per
    `/pm-vitalia` promotion proposal. Cross-brand mirror prohibited.

Tenant isolation:
  ``tenant_id`` is REQUIRED in every initial state. Checkpointer thread_id
  composes ``(tenant_id, draft_id)`` to keep wizard sessions isolated per
  tenant across multitenant traffic.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages

# ════════════════════════════════════════════════════════════════════════════
# Slot value object
# ════════════════════════════════════════════════════════════════════════════


class WizardSlotDict(TypedDict):
    """Slot value carried inside the wizard state.

    Note: this is a TypedDict view used by the LangGraph state — the domain
    entity lives in ``src.modules.vitalia.copilot.domain.entities.wizard_slot``.
    Both have the same field shape on purpose (the API layer converts at the
    boundary). DO NOT add behavior here.
    """

    slot_id: str
    value: Any  # str | dict | None — TypedDict tolerates Any for free-form
    confidence: float
    confirmed_at: Optional[str]  # ISO 8601 datetime when user confirmed
    source: Literal["extracted", "user_text", "user_correction"]


# ════════════════════════════════════════════════════════════════════════════
# WizardOnboardingState (LangGraph state schema)
# ════════════════════════════════════════════════════════════════════════════


class WizardOnboardingState(TypedDict, total=False):
    """LangGraph supervisor state for Valeria wizard onboarding.

    ``total=False`` — nodes return only the keys they modify (LangGraph
    convention). Initial state factory ``build_initial_state`` seeds the full
    surface with safe defaults.

    Required slot list comes from ``REQUIRED_SLOT_IDS`` (cement constant).
    """

    # Tenant isolation (CARDINAL)
    tenant_id: str
    user_id: str
    clinic_id: Optional[str]  # may not exist yet — onboarding creates it

    # Conversation
    messages: Annotated[list, add_messages]
    iterations: int  # max-iter guard (cap 25)

    # Slots
    slots_required_confirmed: dict[str, WizardSlotDict]
    slots_optional_confirmed: dict[str, WizardSlotDict]
    slots_pending: list[str]
    bonus_extracted: dict[str, WizardSlotDict]

    # Mode
    mode: Optional[Literal["libre", "guiado"]]

    # Live preview
    voice_profile_partial: Optional[dict]
    voice_samples: Annotated[list[dict], add]
    landing_preview_url: Optional[str]

    # Subagent bridge (deepagents sandbox)
    extraction_subagent_input: Optional[dict]
    extraction_subagent_output: Optional[dict]

    # Compliance
    pii_detected_in_doc: bool
    consent_voice_activation: bool

    # Errors + termination
    last_error: Optional[dict]
    task_complete: bool


# ════════════════════════════════════════════════════════════════════════════
# Cement constants
# ════════════════════════════════════════════════════════════════════════════

REQUIRED_SLOT_IDS: tuple[str, ...] = (
    "tenant.name",
    "tenant.vertical",
    "tenant.location",
)
"""Required wizard slots — cement per 03-arch-agentic § 2.1 + design § 1.2."""

OPTIONAL_SLOT_IDS: tuple[str, ...] = ("brand.tone_default",)
"""Optional wizard slots (cosmetic at completion time)."""


MAX_ITERATIONS: int = 25
"""Max supervisor iterations before forced END (copilot-resilience cap)."""


# ════════════════════════════════════════════════════════════════════════════
# Pure helpers (used by supervisor router)
# ════════════════════════════════════════════════════════════════════════════


def required_all_confirmed(state: dict[str, Any]) -> bool:
    """Return True iff every REQUIRED_SLOT_IDS has a confirmed entry.

    A slot counts as confirmed if it exists in
    ``state["slots_required_confirmed"]`` and its value is not None.
    Confidence threshold is NOT enforced here — the supervisor is responsible
    for asking for confirmation before promoting an extracted value to
    confirmed.

    Pure function: callable from router branches AND from completion router.
    """
    confirmed = state.get("slots_required_confirmed", {}) or {}
    if not isinstance(confirmed, dict):
        return False
    for slot_id in REQUIRED_SLOT_IDS:
        slot = confirmed.get(slot_id)
        if slot is None:
            return False
        value = slot.get("value") if isinstance(slot, dict) else None
        if value is None:
            return False
    return True


def has_pending_extraction(state: dict[str, Any]) -> bool:
    """Return True iff state has subagent input set but no output yet."""
    return state.get("extraction_subagent_input") is not None and state.get("extraction_subagent_output") is None


def build_initial_state(
    *,
    tenant_id: str,
    user_id: str,
    clinic_id: Optional[str],
) -> WizardOnboardingState:
    """Construct a fresh WizardOnboardingState with safe defaults.

    Called by the orchestrator/composition root when starting a new wizard
    session. All required keys present so total=False does not surprise
    downstream nodes.
    """
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "clinic_id": clinic_id,
        "messages": [],
        "iterations": 0,
        "slots_required_confirmed": {},
        "slots_optional_confirmed": {},
        "slots_pending": list(REQUIRED_SLOT_IDS),
        "bonus_extracted": {},
        "mode": None,
        "voice_profile_partial": None,
        "voice_samples": [],
        "landing_preview_url": None,
        "extraction_subagent_input": None,
        "extraction_subagent_output": None,
        "pii_detected_in_doc": False,
        "consent_voice_activation": False,
        "last_error": None,
        "task_complete": False,
    }


__all__ = [
    "MAX_ITERATIONS",
    "OPTIONAL_SLOT_IDS",
    "REQUIRED_SLOT_IDS",
    "WizardOnboardingState",
    "WizardSlotDict",
    "build_initial_state",
    "has_pending_extraction",
    "required_all_confirmed",
]
