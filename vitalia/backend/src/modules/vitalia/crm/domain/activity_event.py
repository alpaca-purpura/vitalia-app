# cap: crm.crm-consent-optout
# story-origin: TBD
"""ActivityEvent domain entity — UI-tuned projection of copilot_trace_event.

Domain layer — pure Python dataclass, no ORM imports.

Per 03-arch-be.md § 3.3: ActivityEvent is a curated projection for ActivityStream UI.
NOT a mirror of copilot_trace_event — it's a brand-local read-isolation layer.
Per hipaa-lite.md: PHI dual-filter (tenant_id + clinic_id) mandatory.
Per spanish-text.md: description_es uses Spanish neutro LatAm (no voseo).

SC-01 ActivityStream: 8 last events showing what Adrián did (consultó precio,
verificó disponibilidad, propuso turno, clasificó interés, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

# downstream-regression-na: brand-local vitalia CRM domain entity

AgentId = Literal["adrian", "valeria", "lucas", "system"]

# Exported constants for tests and arch fitness checks
VALID_AGENT_IDS: frozenset[str] = frozenset({"adrian", "valeria", "lucas", "system"})


@dataclass
class ActivityEvent:
    """ActivityEvent domain entity — PHI dual-filter.

    PHI obligations (hipaa-lite.md § Regla cardinal):
    1. tenant_id + clinic_id dual filter mandatory on every query.
    2. payload_sanitized: PII must be redacted before storing/returning.
       Service calls sanitize_payload(compliance_level='hipaa_lite') before write.
    3. description_es: never include raw PHI (patient names, diagnosis, etc.).
       Use placeholder references like 'el paciente' or offer names only.

    ActivityStream UI contract (SC-01, 01-spec § 8):
    - 8 last events visible in collapsed/expanded ActivityStream.
    - Poll interval: 5s when expanded.
    - format: '{timestamp} · {description_es}'
    - description_es uses 3rd person narrated form for activity logging.
      (Not tuteo/voseo — this is event narration, not user-addressed copy.)

    Anti-duplication (anti-duplication.md):
    - source_trace_event_id: optional FK to copilot_trace_event engine table.
    - ActivityEventService may fallback to direct copilot_trace_event query
      if this projection is empty.
    - NEVER reimplementing turn_envelope or cost_recorder locally.
    """

    # Identity (PHI dual-filter keys)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID

    # Relations
    conversation_id: UUID
    source_trace_event_id: UUID | None  # FK to copilot_trace_event if available

    # Event classification
    event_kind: str  # 'consulto_precio' | 'verifico_agenda' | 'propuso_turno' | etc.
    description_es: str  # "Consultó precio de Blanqueamiento Premium ($24.000)"

    # Agent attribution
    agent_id: str  # AgentId literal: 'adrian' | 'valeria' | 'lucas' | 'system'

    # Timeline
    occurred_at: datetime

    # Debugging payload (PII-sanitized — NEVER render raw in UI)
    payload_sanitized: dict = field(default_factory=dict)  # type: ignore[assignment]

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
