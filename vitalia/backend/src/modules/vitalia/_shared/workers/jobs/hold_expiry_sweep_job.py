# cap: scheduling.mateo-agenda
"""ARQ cron job: hold_expiry_sweep_job — release expired appointment holds.

Schedule: every 5 minutes (configurable in ARQ worker settings).
Span: vitalia.cron.hold_expiry_sweep
Owner module: scheduling

Iterates all active tenants → runs HoldExpirySweepService.sweep_expired().
Idempotent: safe to run multiple times with same parameters.

Per 03-arch § 7 (HoldExpirySweepService) + vitalia-fase2-adrian-canal-inbound T-BE-2.

downstream-regression-na: brand-local cron (no cross-brand consumers).
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()


async def hold_expiry_sweep_job(ctx: dict) -> None:
    """Release expired appointment holds across all tenants.

    ARQ worker context provides db session factory and tenant list.

    Idempotent: HoldExpirySweepService.sweep_expired() returns 0 for already-cleared holds.

    Args:
        ctx: ARQ worker context dict (contains job_id, redis, session_factory, tenant_ids).
    """
    # Defensive: handle missing ctx gracefully for testability
    session_factory = ctx.get("session_factory")
    tenant_ids: list[str] = ctx.get("tenant_ids", [])

    if not session_factory or not tenant_ids:
        logger.warning(
            "hold_expiry_sweep_job_skipped",
            reason="no session_factory or tenant_ids in ctx",
        )
        return

    from src.modules.vitalia._shared.workers.jobs._sweep_factory import build_sweep_service  # noqa: PLC0415

    now = datetime.now(timezone.utc)
    total_released = 0

    for tenant_id_str in tenant_ids:
        async with session_factory() as session:
            service = build_sweep_service(session=session)
            from uuid import UUID  # noqa: PLC0415

            try:
                released = await service.sweep_expired(
                    tenant_id=UUID(tenant_id_str),
                    now=now,
                )
                total_released += released
            except Exception:  # noqa: BLE001
                logger.exception(
                    "hold_expiry_sweep_tenant_failed",
                    tenant_id=tenant_id_str,
                )

    logger.info(
        "hold_expiry_sweep_job_complete",
        total_released=total_released,
        tenant_count=len(tenant_ids),
    )
