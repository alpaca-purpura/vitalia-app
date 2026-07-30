# cap: __shared__
# story-origin: TBD
"""ARQ cron job: reactivation_45d — 45-day patient reactivation.

Schedule: every 6h
Span: vitalia.cron.reactivation_45d
Owner module: fidelizacion

Scaffold — real logic implemented in vitalia-slice-1-fidelizacion story T-fidelizacion-reactivacion.

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def reactivation_45d(ctx: dict) -> None:
    """Detect and contact patients absent for 45+ days to drive reactivation.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-fidelizacion story (T-fidelizacion-reactivacion).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = (
        "reactivation_45d not yet implemented. "
        "Implemented in vitalia-slice-1-fidelizacion story T-fidelizacion-reactivacion."
    )
    raise NotImplementedError(msg)
