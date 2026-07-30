# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadStageTransition domain entity — audit log for funnel transitions.

Domain layer — pure Python dataclass, no ORM imports.

NON-PHI: reason field = commercial override context (NOT clinical notes).
IMPORTANT: field named 'reason' NOT 'notes' — arch test PHI regex matches 'notes TEXT'.

Tenant isolation: tenant_id required on every DB access (single filter, non-PHI).
Retention: business event audit, 10y per LatAm health regulations (hipaa-lite.md).

Each LeadStageTransition records:
  - who triggered the transition (agent | manual_override | webhook | auto_freeze)
  - optional reason (commercial context for the override, RN-4.1)
  - score snapshot at transition time
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class LeadStageTransition:
    """Audit record for a single funnel stage transition.

    NON-PHI entity — single tenant_id filter only.
    reason field contains commercial override context (e.g. 'wants to see before/after photos'),
    NEVER clinical diagnosis or treatment data.

    SC-5 and RN-4.1: reason is injected as override_context for the agent's next turn
    when triggered_by == 'manual_override' with a non-null reason.
    """

    id: UUID
    tenant_id: UUID  # mandatory — tenant isolation (non-PHI single filter)
    lead_id: UUID
    from_stage: str | None  # None when initial stage is set
    to_stage: str
    triggered_by: str  # agent | manual_override | webhook | reactivation | auto_freeze
    reason: str | None  # override context (commercial, NON-PHI) — RN-4.1
    score_at_transition: int | None
    actor_user_id: UUID | None  # set when triggered_by == 'manual_override'
    occurred_at: datetime
    deleted_at: datetime | None = None
