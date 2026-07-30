# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas growth setter — StageEnum.

Funnel stages consumed by analytics engine (STAGE_CHANNEL_MAP) and
Lucas stage recommendation service.

Source of truth: luana_core_analytics_engine channel_registry STAGE_CHANNEL_MAP.
Values MUST match the keys of that mapping exactly.
"""

from __future__ import annotations

from enum import Enum


class StageEnum(str, Enum):
    """Funnel stages for Lucas analytics recommendations.

    Values align with STAGE_CHANNEL_MAP keys in the analytics engine.
    DO NOT add stages here without a corresponding entry in the engine map.
    """

    ATTRACTION = "attraction"
    CAPTURE = "capture"
    NURTURE = "nurture"
    OPPORTUNITY = "opportunity"
    RETENTION = "retention"
