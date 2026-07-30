# cap: patients.nps-tracking
# story-origin: TBD
"""Worker cron: nps_post_treatment_sweep.

Dispara encuesta NPS para pacientes que completaron un tratamiento
recientemente y aún no recibieron survey.

Schedule: 15 * * * * (horario en el minuto :15)

HIPAA-lite: sin PHI en logs. Dual filter tenant_id + clinic_id.
            patient_id se pasa como UUID opaco (no datos clínicos).

downstream-regression-na: brand-local worker vitalia fidelización
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import structlog
from luana_core_platform.workers.cron_envelope import cron_envelope

logger = structlog.get_logger(__name__)

_NPS_TEMPLATE_ID = "nps_post_treatment_01"
_SYSTEM_USER_ID = uuid4()  # sentinel para operaciones automáticas (no PHI)


@cron_envelope("vitalia.cron.nps_post_treatment_sweep", ttl=300, enable_sentry=True)
async def nps_post_treatment_sweep_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Cron sweep horario para NPS post-tratamiento.

    Procesa la lista de citas/appointments elegibles para NPS. Cada entrada
    en eligible_appointments debe contener tenant_id, clinic_id, patient_id
    y treatment_plan_id.

    Args:
        ctx: Contexto ARQ con:
            - re_engagement_service: ReEngagementService instanciado.
            - tenant_clinic_pairs: list[tuple[UUID, UUID]] pares (tenant, clinic).
            - eligible_appointments: list[dict] con keys:
                tenant_id, clinic_id, patient_id, treatment_plan_id.

    Returns:
        dict con total_nps_triggered.
    """
    service = ctx["re_engagement_service"]
    eligible_appointments: list[dict[str, Any]] = ctx.get("eligible_appointments", [])

    total_triggered = 0
    sweep_results: list[dict[str, Any]] = []

    for appointment in eligible_appointments:
        tenant_id: UUID = appointment["tenant_id"]
        clinic_id: UUID = appointment["clinic_id"]
        patient_id: UUID = appointment["patient_id"]
        treatment_plan_id: UUID = appointment["treatment_plan_id"]

        log = logger.bind(
            cron="nps_post_treatment_sweep",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

        try:
            await service.trigger_nps_post_treatment(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=patient_id,
                treatment_plan_id=treatment_plan_id,
                template_id=_NPS_TEMPLATE_ID,
                user_id=_SYSTEM_USER_ID,
            )

            total_triggered += 1
            sweep_results.append(
                {
                    "tenant_id": str(tenant_id),
                    "clinic_id": str(clinic_id),
                    "triggered": True,
                }
            )

        except Exception:
            log.exception("nps_post_treatment_sweep.trigger_error")
            raise

    # Si no hay appointments, iteramos pairs solo para loguear actividad
    if not eligible_appointments:
        tenant_clinic_pairs: list[tuple[UUID, UUID]] = ctx.get("tenant_clinic_pairs", [])
        for tenant_id, clinic_id in tenant_clinic_pairs:
            sweep_results.append(
                {
                    "tenant_id": str(tenant_id),
                    "clinic_id": str(clinic_id),
                    "triggered": 0,
                }
            )

    logger.info(
        "nps_post_treatment_sweep.done",
        appointments_processed=len(eligible_appointments),
        total_nps_triggered=total_triggered,
    )

    return {
        "sweeps": sweep_results,
        "total_nps_triggered": total_triggered,
    }
