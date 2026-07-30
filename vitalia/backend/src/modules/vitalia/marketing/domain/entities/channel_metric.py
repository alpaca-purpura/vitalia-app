# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""ChannelMetric domain entity — immutable daily metric snapshot per channel.

Per HIPAA-lite: NO PHI stored here. UTM fields contain campaign attribution
data only (no patient identifiers).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from src.modules.vitalia.marketing.domain.enums import ProviderSlug


@dataclass
class ChannelMetric:
    """Daily performance metrics snapshot for a clinic's ad channel.

    Uniquely identified by (tenant_id, clinic_id, provider, channel_slug,
    campaign_id, metric_date) per arch spec §2.2.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    clinic_id: uuid.UUID
    provider: ProviderSlug
    channel_slug: str
    metric_date: date
    currency: str
    created_at: datetime

    # Metrics
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend_cents: int = 0

    # Campaign attribution
    campaign_id: str | None = None
    campaign_name: str | None = None

    # Raw payload for audit/debugging (no PHI)
    raw_payload: dict[str, Any] | None = None

    @property
    def ctr(self) -> float | None:
        """Click-through rate (clicks / impressions), or None if no impressions."""
        if self.impressions == 0:
            return None
        return self.clicks / self.impressions

    @property
    def cpc_cents(self) -> int | None:
        """Cost per click in cents, or None if no clicks."""
        if self.clicks == 0:
            return None
        return self.spend_cents // self.clicks
