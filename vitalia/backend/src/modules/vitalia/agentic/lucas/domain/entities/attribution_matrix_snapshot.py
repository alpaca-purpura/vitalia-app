# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas domain entity — AttributionMatrixSnapshot.

Pure Python domain entity. No SQLAlchemy, no FastAPI imports.

Stores analytics attribution data per period, per (tenant_id, clinic_id).
Currency is ISO-4217 from tenant locale — NEVER hardcoded.

HIPAA-lite: no PHI fields. Pure analytics data.
Dual filter: every repository query uses BOTH tenant_id + clinic_id.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass
class AttributionMatrixSnapshot:
    """Domain entity for an attribution matrix snapshot.

    One snapshot per (tenant_id, clinic_id, period_start) — uniqueness enforced
    by migration 018 unique partial index (WHERE deleted_at IS NULL).

    currency: ISO-4217 from tenant locale. Never default 'USD'.
    See .claude/rules/currency-handling.md.
    """

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    period_start: dt.date
    period_end: dt.date
    channel_breakdown: dict[str, Any]
    total_attributed_revenue: Decimal
    currency: str | None  # ISO-4217 from tenant locale; None until locale resolved
    computed_at: dt.datetime
    deleted_at: dt.datetime | None
