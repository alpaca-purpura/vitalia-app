# cap: treatments.treatment-followup-workflow
# story-origin: TBD
"""ARQ cron job: followup_24h — 24h post-conversation follow-up.

Schedule: every 1h
Span: vitalia.cron.followup_24h
Owner module: fidelizacion

Scaffold — real logic implemented in vitalia-slice-1-fidelizacion story T-fidelizacion-N.

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def followup_24h(ctx: dict) -> None:
    """Send 24h post-conversation follow-up messages to patients.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-fidelizacion story (T-fidelizacion-followup).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = "followup_24h not yet implemented. Implemented in vitalia-slice-1-fidelizacion story T-fidelizacion-followup."
    raise NotImplementedError(msg)
