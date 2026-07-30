# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent state overlay (TypedDict extension).

Story T-ag-tools-2 — R23 production_code=true.

Per 03-arch-agentic.md § 2.2 + 02-design-agentic.md § 2.2:
Adrián consumes engine ``core/luana-core-sales-agent/`` LangGraph DIRECTLY.
NO parallel graph in vitalia (§3 NO se toca per sales-agent-expert).

This module defines the brand-specific state keys that vitalia writes into the
engine's runtime state dict. The engine ``AgentState`` is a ``TypedDict`` and the
live state object is a plain ``dict`` — brands EXTEND it by composition (writing
these keys / nesting them under ``metadata_info``), NOT via any engine registration
API. There is intentionally NO ``engine.register_state_extension()`` and NO change to
the engine ``AgentState`` TypedDict (ratified contract — multibrand-graph-runtime
proposal §4: "CERO cambio al AgentState TypedDict — las keys de marca viven en
overlay/metadata_info"). This TypedDict is the brand-side **type contract** that gives
vitalia code type-safety when it reads/writes those keys; the engine never imports it.

Keys added (Adrián 3-tools MVP):
- ``clinic_id`` — MANDATORY for Vitalia turns (HIPAA-lite dual filter)
- ``vertical`` — domain-routing hint (dental/estetica/psicologia/fertilidad/otro)
- ``screening_outcome`` — populated post screening_questions tool call
- ``medical_disclaimer_shown`` — track whether disclaimer footer was emitted
- ``phi_blocked_messages`` — list of compliance blocks for audit trail
- ``compliance_level`` — always "hipaa_lite" for vitalia tenants

Booking keys added (T-AG-1 — canal-inbound, 02-design-agentic § 6 + 03-arch-agentic § 1.1):
- ``recommended_doctor_id`` — set by match_service_and_specialist (post-lift tool)
- ``recommended_service_offer_id`` — the matched service Offer
- ``candidate_slots`` — get_available_slots cached for reasoning-based slot mapping.
  ★ VOLATILE per-turn signal (lives in slot 8 of compose, post CACHE_BOUNDARY) —
  it MUST NEVER enter a cacheable prompt prefix (a forbidden cacheable-prefix
  element: it changes every turn, so it would be a silent cache invalidator).
- ``doctor_profile_shared_at`` — audit/glass-box of share_doctor_profile (post-lift)

The engine ``scheduled_meetings`` (agent_state_checkpoint_model.py) already models
the booked turn (tracking, status, appointment_id, scheduled_at, reminders) — these
overlay keys REFERENCE it, they do NOT duplicate it. The engine AgentState TypedDict
and MeetingEntry are NOT extended here (engine read-only; doctor_id/service_id on a
meeting are post-lift decisions, NOT this brand overlay's concern).

Reducer for ``phi_blocked_messages`` uses ``operator.add`` so parallel branches
(if engine supervisor fans out via Send) accumulate audit entries safely.

Anti-duplication audit (Step 0 GATE pre-write):
- No engine sales_agent state class to subclass — engine state is a TypedDict
  that brands extend via composition, NOT inheritance (LangGraph 2.0 pattern).
- This module declares ONLY the brand-specific keys; engine state remains
  the source of truth for all base keys (messages, tenant_id, etc.).
- ``operator.add`` is stdlib, NOT a custom reducer. No reducer mirror.

downstream-regression-na: brand-local state schema declaration only — no
engine modification, no cross-brand consumers.
"""

from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Any, Literal, TypedDict
from uuid import UUID

# Vitalia clinical verticals (cardinal SSoT — matches screening_questions_by_vertical.yaml).
VitaliaVertical = Literal["dental", "estetica", "psicologia", "fertilidad", "otro"]

# Compliance level enum (hipaa-lite only for vitalia).
VitaliaComplianceLevel = Literal["hipaa_lite"]


class VitaliaSalesAgentStateExtension(TypedDict, total=False):
    """Brand-specific state keys for vitalia Adrián sales_agent.

    These keys are written into the engine's runtime state ``dict`` by the inbound
    adapter + brand tools (directly or under ``metadata_info``) — there is NO engine
    registration step and NO change to the engine ``AgentState`` TypedDict (ratified
    contract §4). This TypedDict only documents + type-checks the brand keys.

    All fields are ``total=False`` (optional) to allow gradual population
    during the conversation lifecycle.

    Per .claude/rules/tenant-isolation.md + hipaa-lite.md cardinal:
    ``clinic_id`` MUST be populated by the inbound webhook adapter BEFORE
    the first LLM call. Engine state schema is the source for ``tenant_id``
    and ``lead_id``; vitalia adds ``clinic_id`` as the dual-filter second
    component for PHI queries.
    """

    # HIPAA-lite dual filter (cardinal)
    clinic_id: UUID

    # Domain routing hint
    vertical: VitaliaVertical

    # Screening outcome (populated post screening_questions tool call)
    # Shape: {"event_id": UUID, "outcome": str, "reasoning": str|None, "questions_asked": list[str]}
    screening_outcome: dict[str, Any] | None

    # Disclaimer footer tracker
    medical_disclaimer_shown: bool

    # PHI block audit accumulator — parallel-safe via operator.add reducer
    phi_blocked_messages: Annotated[list[dict[str, Any]], operator.add]

    # Compliance level (constant per brand — always "hipaa_lite")
    compliance_level: VitaliaComplianceLevel

    # ── Booking keys (T-AG-1 — canal-inbound, total=False) ──
    # Set by match_service_and_specialist (post-lift). The matched primary doctor.
    recommended_doctor_id: UUID | None

    # The matched service Offer for which the doctor was recommended.
    recommended_service_offer_id: UUID | None

    # get_available_slots cached for reasoning-based slot mapping.
    # ★ VOLATILE per-turn signal (compose slot 8, post CACHE_BOUNDARY).
    # NEVER promote into the cacheable prefix — it is a silent cache invalidator.
    candidate_slots: list[dict[str, Any]] | None

    # Audit/glass-box timestamp of share_doctor_profile (post-lift tool).
    doctor_profile_shared_at: datetime | None


__all__ = [
    "VitaliaComplianceLevel",
    "VitaliaSalesAgentStateExtension",
    "VitaliaVertical",
]
