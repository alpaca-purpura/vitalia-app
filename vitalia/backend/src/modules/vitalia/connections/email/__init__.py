# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Email connection adapter — vitalia connections module.

Email channel does NOT support real message retraction.
Raises ChannelRetractUnsupportedError (caught by RetractMessageService
which applies 'marcar como erróneo' fallback via flag + UI strike-through).
"""

from __future__ import annotations

# downstream-regression-na: brand-local vitalia connections email module
from src.modules.vitalia.connections.email.adapter import (
    ChannelRetractUnsupportedError,
    EmailAdapter,
)

__all__ = [
    "EmailAdapter",
    "ChannelRetractUnsupportedError",
]
