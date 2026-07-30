# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadActivity domain entity — micro-log attributed timeline.

Domain layer — pure Python dataclass, no ORM imports.

NON-PHI micro-log: commercial/funnel events only.
NEVER store clinical data (diagnosis, treatments, lab results).
RN-2 firewall: Lead activity = marketing/commercial timeline.

Distinct from crm/domain/activity_event.py which is PHI dual-filter inbox events.
LeadActivity is non-PHI, single tenant_id filter, commercial context only.

actor: who generated this activity
  - 'agent' — Adrián (sales agent AI)
  - 'human' — operator manual action
  - 'lead' — inbound action from the lead itself
  - 'system' — auto-freeze, cron, webhook

kind: what type of activity
  - 'message' — inbound/outbound message
  - 'stage_move' — funnel stage transition
  - 'info_sent' — info/brochure/price list sent
  - 'deposit' — deposit/payment received
  - 'note' — internal note added by operator
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class LeadActivity:
    """Single attributed activity in the lead commercial timeline.

    NON-PHI — single tenant_id filter only.
    description_es: Spanish neutro LatAm, 3rd person, NEVER clinical data.

    Example: "Adrián envió la lista de precios de implantes." (OK)
    Example: "El paciente tiene periodontitis grado II." (FORBIDDEN — clinical)
    """

    id: UUID
    tenant_id: UUID  # mandatory — tenant isolation (non-PHI single filter)
    lead_id: UUID
    actor: str  # agent | human | lead | system
    kind: str  # message | stage_move | info_sent | deposit | note
    description_es: str  # Spanish neutro, 3rd person, NON-PHI
    occurred_at: datetime
    deleted_at: datetime | None = None
