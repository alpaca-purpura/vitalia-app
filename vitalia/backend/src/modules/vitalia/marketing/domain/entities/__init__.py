# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""Marketing domain entities for vitalia brand."""

from __future__ import annotations

from src.modules.vitalia.marketing.domain.entities.channel_metric import ChannelMetric
from src.modules.vitalia.marketing.domain.entities.channel_sync_state import ChannelSyncState
from src.modules.vitalia.marketing.domain.entities.lucas_recommendation import LucasRecommendation
from src.modules.vitalia.marketing.domain.entities.referral import Referral

__all__ = [
    "ChannelMetric",
    "ChannelSyncState",
    "LucasRecommendation",
    "Referral",
]
