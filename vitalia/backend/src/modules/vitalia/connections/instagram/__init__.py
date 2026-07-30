# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Instagram Graph API connection adapter — vitalia connections module.

Provides retract_message_id via Meta Graph API DELETE with graceful degradation.
"""

from __future__ import annotations

# downstream-regression-na: brand-local vitalia connections instagram module
from src.modules.vitalia.connections.instagram.adapter import (
    InstagramAdapter,
    RetractResult,
)

__all__ = [
    "InstagramAdapter",
    "RetractResult",
]
