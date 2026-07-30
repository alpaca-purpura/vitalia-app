# cap: __shared__
# story-origin: TBD
"""ARQ cron job: appointment_reminder_2h — 2h pre-appointment reminder.

Schedule: every 15min
Span: vitalia.cron.appointment_reminder_2h
Owner module: agenda

Scaffold — real logic implemented in vitalia-slice-1-agenda story T-agenda-reminder-2h.

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def appointment_reminder_2h(ctx: dict) -> None:
    """Send urgent appointment reminders to patients 2h before their scheduled time.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-agenda story (T-agenda-reminder-2h).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = (
        "appointment_reminder_2h not yet implemented. Implemented in vitalia-slice-1-agenda story T-agenda-reminder-2h."
    )
    raise NotImplementedError(msg)
