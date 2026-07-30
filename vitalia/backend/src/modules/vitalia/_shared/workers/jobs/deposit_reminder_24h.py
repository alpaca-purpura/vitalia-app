# cap: __shared__
# story-origin: TBD
"""ARQ cron job: deposit_reminder_24h — 24h pre-appointment deposit reminder.

Schedule: every 1h
Span: vitalia.cron.deposit_reminder_24h
Owner module: agenda

Scaffold — real logic implemented in vitalia-slice-1-agenda story T-agenda-deposit.

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def deposit_reminder_24h(ctx: dict) -> None:
    """Remind patients to pay their deposit 24h before their appointment.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-agenda story (T-agenda-deposit).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = "deposit_reminder_24h not yet implemented. Implemented in vitalia-slice-1-agenda story T-agenda-deposit."
    raise NotImplementedError(msg)
