# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Worker cron: re_engagement_response_timeout_sweep.

Marca como NOT_RESPONSIVE los eventos de re-engagement que llevan
7+ días sin respuesta del paciente.

Schedule: 0 9 * * * (diario 09:00 UTC)

HIPAA-lite: sin PHI en logs. Dual filter tenant_id + clinic_id.

downstream-regression-na: brand-local worker vitalia fidelización
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.workers.cron_envelope import cron_envelope

logger = structlog.get_logger(__name__)


@cron_envelope(
    "vitalia.cron.re_engagement_response_timeout_sweep",
    ttl=300,
    enable_sentry=True,
)
async def re_engagement_response_timeout_sweep_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Cron sweep diario para timeouts de respuesta a re-engagement.

    Procesa la lista de eventos que ya superaron el timeout de 7 días sin
    respuesta. Invoca mark_response_timeout para cada uno.

    Args:
        ctx: Contexto ARQ con:
            - re_engagement_service: ReEngagementService instanciado.
            - tenant_clinic_pairs: list[tuple[UUID, UUID]] pares (tenant, clinic).
            - timed_out_events: list[ReEngagementEventModel] eventos a marcar.

    Returns:
        dict con total_marked_timeout.
    """
    service = ctx["re_engagement_service"]
    timed_out_events: list[Any] = ctx.get("timed_out_events", [])

    total_marked = 0
    sweep_results: list[dict[str, Any]] = []

    for event_model in timed_out_events:
        tenant_id: UUID = event_model.tenant_id
        clinic_id: UUID = event_model.clinic_id

        log = logger.bind(
            cron="re_engagement_response_timeout_sweep",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

        try:
            await service.mark_response_timeout(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                event_model=event_model,
            )

            total_marked += 1
            sweep_results.append(
                {
                    "tenant_id": str(tenant_id),
                    "clinic_id": str(clinic_id),
                    "marked_timeout": True,
                }
            )

        except Exception:
            log.exception("re_engagement_response_timeout_sweep.mark_error")
            raise

    # Si no hay eventos, iteramos pairs para loguear actividad
    if not timed_out_events:
        tenant_clinic_pairs: list[tuple[UUID, UUID]] = ctx.get("tenant_clinic_pairs", [])
        for tenant_id, clinic_id in tenant_clinic_pairs:
            sweep_results.append(
                {
                    "tenant_id": str(tenant_id),
                    "clinic_id": str(clinic_id),
                    "marked_timeout": 0,
                }
            )

    logger.info(
        "re_engagement_response_timeout_sweep.done",
        events_processed=len(timed_out_events),
        total_marked_timeout=total_marked,
    )

    return {
        "sweeps": sweep_results,
        "total_marked_timeout": total_marked,
    }
