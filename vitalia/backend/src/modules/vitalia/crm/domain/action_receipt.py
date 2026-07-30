# cap: crm.crm-consent-optout
# story-origin: TBD
"""ActionReceipt domain entity — 5min undo window for AI messages.

Domain layer — pure Python dataclass, no ORM imports.

Per 03-arch-be.md § 3.4: ActionReceipt tracks the 5min undo window per message.
Per hipaa-lite.md: PHI dual-filter (tenant_id + clinic_id) mandatory.

SC-01 Action Receipts: each AI-sent message gets a receipt with 5min countdown.
SC-03 OCC: updated_at present for state change tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

# downstream-regression-na: brand-local vitalia CRM domain entity

RetractReason = Literal["user_undo", "expired", "patient_replied"] | None

# Exported constants for tests and arch fitness checks
VALID_RETRACT_REASONS: frozenset[str] = frozenset({"user_undo", "expired", "patient_replied"})

# 5-minute undo window per spec (SC-01, 01-spec § 9)
ACTION_RECEIPT_WINDOW_MINUTES: int = 5


@dataclass
class ActionReceipt:
    """ActionReceipt domain entity — PHI dual-filter.

    PHI obligations (hipaa-lite.md § Regla cardinal):
    1. tenant_id + clinic_id dual filter mandatory on every query.
    2. Audit log row written when retraction attempted (success or failure).

    State machine (SC-01, 01-spec § 9):
    - ACTIVE:   retracted_at=None, expires_at=future
    - RETRACTED_SUCCESS: retracted_at=<ts>, retract_succeeded=True
    - RETRACTED_FALLBACK: retracted_at=<ts>, retract_succeeded=False
      (email / WA API failure → 'marcar erróneo')
    - EXPIRED:  retracted_at=<ts>, retract_reason='expired'
    - INVALIDATED: retract_reason='patient_replied' (patient replied before undo)

    WA retract window: messages older than 5 minutes cannot be retracted via API.
    IG retract window: same 5 minutes.
    Email: retract NOT supported → always fallback (retract_succeeded=False).
    """

    # Identity (PHI dual-filter keys)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID

    # Relations
    message_id: UUID
    conversation_id: UUID

    # Expiry window (5min from message sent_at)
    expires_at: datetime

    # Retraction state
    retracted_at: datetime | None
    retract_succeeded: bool | None  # None=not attempted, True=OK, False=fallback
    retract_reason: str | None  # RetractReason literal

    # Timestamps
    created_at: datetime
    updated_at: datetime  # for OCC state tracking
