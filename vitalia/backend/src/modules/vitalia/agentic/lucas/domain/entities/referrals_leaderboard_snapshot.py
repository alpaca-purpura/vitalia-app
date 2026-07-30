# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas domain entity — ReferralsLeaderboardSnapshot.

Pure Python domain entity. No SQLAlchemy, no FastAPI imports.

Stores referrals leaderboard data per period, per (tenant_id, clinic_id).

HIPAA-lite: top_referrers list contains referrer_id (UUID), rank, counts.
No patient names or identifiable PHI — referrer_id is a hash UUID.
Dual filter: every repository query uses BOTH tenant_id + clinic_id.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class ReferralsLeaderboardSnapshot:
    """Domain entity for a referrals leaderboard snapshot.

    One snapshot per (tenant_id, clinic_id, period_start) — uniqueness enforced
    by migration 019 unique partial index (WHERE deleted_at IS NULL).

    top_referrers: list of dicts {referrer_id: str (UUID), referral_count: int,
                                  converted_count: int, rank: int}.
    Referrer names MUST NOT be stored here — PHI risk. Use referrer_id only.
    """

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    period_start: dt.date
    period_end: dt.date
    top_referrers: list[dict[str, Any]]
    total_referrals: int
    total_converted: int
    computed_at: dt.datetime
    deleted_at: dt.datetime | None
