# cap: __shared__
# story-origin: TBD
"""ARQ cron job: maintenance_90d — 90-day treatment maintenance reminder.

Schedule: every 12h
Span: vitalia.cron.maintenance_90d
Owner module: fidelizacion

Scaffold — real logic implemented in vitalia-slice-1-fidelizacion story
or vitalia-copilot-tools-impl (T-fidelizacion-maintenance).

downstream-regression-na: brand-local cron scaffold; no cross-brand consumers
"""

from __future__ import annotations


async def maintenance_90d(ctx: dict) -> None:
    """Detect patients due for maintenance treatment at 90-day intervals.

    Scaffold: raises NotImplementedError until implemented in
    vitalia-slice-1-fidelizacion story (T-fidelizacion-maintenance).

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, etc.)
    """
    msg = (
        "maintenance_90d not yet implemented. "
        "Implemented in vitalia-slice-1-fidelizacion story T-fidelizacion-maintenance."
    )
    raise NotImplementedError(msg)
