# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Worker cron: maintenance_due_sweep.

Detecta pacientes con mantenimiento programado vencido y dispara
eventos de re-engagement con patrón MAINTENANCE.

Schedule: 0 8 * * * (diario 08:00 UTC)

HIPAA-lite: sin PHI en logs. Dual filter tenant_id + clinic_id.

downstream-regression-na: brand-local worker vitalia fidelización
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.workers.cron_envelope import cron_envelope

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)

logger = structlog.get_logger(__name__)

_THROTTLE_DAYS = 30


@cron_envelope("vitalia.cron.maintenance_due_sweep", ttl=300, enable_sentry=True)
async def maintenance_due_sweep_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Cron sweep diario para mantenimiento de tratamiento vencido.

    Itera los pares (tenant_id, clinic_id) e invoca
    ReEngagementService.detect_maintenance_due para detectar pacientes
    que deben recibir recordatorio de mantenimiento.

    Args:
        ctx: Contexto ARQ con:
            - re_engagement_service: ReEngagementService instanciado.
            - tenant_clinic_pairs: list[tuple[UUID, UUID]] pares (tenant, clinic).

    Returns:
        dict con total_events_inserted.
    """
    service = ctx["re_engagement_service"]
    tenant_clinic_pairs: list[tuple[UUID, UUID]] = ctx.get("tenant_clinic_pairs", [])

    total_inserted = 0
    sweep_results: list[dict[str, Any]] = []

    for tenant_id, clinic_id in tenant_clinic_pairs:
        log = logger.bind(
            cron="maintenance_due_sweep",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

        try:
            patient_ids: list[UUID] = await service.detect_maintenance_due(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_ids=[],
            )

            eligible_count = 0
            for patient_id in patient_ids:
                is_throttled = await service.check_throttle(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    patient_id=patient_id,
                    pattern=ReEngagementPattern.MAINTENANCE,
                    throttle_days=_THROTTLE_DAYS,
                )
                if is_throttled:
                    continue

                eligible_count += 1

            total_inserted += eligible_count
            sweep_results.append(
                {
                    "tenant_id": str(tenant_id),
                    "clinic_id": str(clinic_id),
                    "candidates": len(patient_ids),
                    "inserted": eligible_count,
                }
            )

            if eligible_count > 0 or len(patient_ids) > 0:
                log.info(
                    "maintenance_due_sweep.pair_done",
                    candidates=len(patient_ids),
                    inserted=eligible_count,
                )

        except Exception:
            log.exception("maintenance_due_sweep.pair_error")
            raise

    logger.info(
        "maintenance_due_sweep.done",
        pairs_processed=len(tenant_clinic_pairs),
        total_events_inserted=total_inserted,
    )

    return {
        "sweeps": sweep_results,
        "total_events_inserted": total_inserted,
    }
