# cap: __shared__
# story-origin: TBD
"""ARQ cron job: channel_sync_state_15min — Channel sync state refresh.

Schedule: every 15min
Span: vitalia.cron.channel_sync_state_15min
Owner module: inbox

Scaffold — real logic implemented in vitalia-slice-1-inbox story T-inbox-sync.

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def channel_sync_state_15min(ctx: dict) -> None:
    """Refresh channel sync state for all connected providers (Meta Ads, Google Ads).

    Updates vitalia_channel_sync_state table with latest sync status.
    Triggers re-sync if status is 'error' or last_success_at is stale.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-inbox story (T-inbox-sync).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = "channel_sync_state_15min not yet implemented. Implemented in vitalia-slice-1-inbox story T-inbox-sync."
    raise NotImplementedError(msg)
