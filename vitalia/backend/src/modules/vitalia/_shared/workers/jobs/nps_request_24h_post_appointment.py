# cap: patients.nps-tracking
# story-origin: TBD
"""ARQ cron job: nps_request_24h_post_appointment — 24h post-appointment NPS request.

Schedule: every 1h
Span: vitalia.cron.nps_request_24h_post_appointment
Owner module: fidelizacion

Scaffold — real logic implemented in vitalia-slice-1-fidelizacion story T-fidelizacion-nps.

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def nps_request_24h_post_appointment(ctx: dict) -> None:
    """Send NPS survey requests to patients 24h after appointment completion.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-fidelizacion story (T-fidelizacion-nps).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = (
        "nps_request_24h_post_appointment not yet implemented. "
        "Implemented in vitalia-slice-1-fidelizacion story T-fidelizacion-nps."
    )
    raise NotImplementedError(msg)
