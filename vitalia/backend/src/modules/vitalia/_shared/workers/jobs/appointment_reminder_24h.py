# cap: __shared__
# story-origin: TBD
"""ARQ cron job: appointment_reminder_24h — 24h pre-appointment reminder.

Schedule: every 1h
Span: vitalia.cron.appointment_reminder_24h
Owner module: agenda

Scaffold — real logic implemented in vitalia-slice-1-agenda story T-agenda-reminder.

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def appointment_reminder_24h(ctx: dict) -> None:
    """Send appointment reminders to patients 24h before their scheduled time.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-agenda story (T-agenda-reminder).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = "appointment_reminder_24h not yet implemented. Implemented in vitalia-slice-1-agenda story T-agenda-reminder."
    raise NotImplementedError(msg)
