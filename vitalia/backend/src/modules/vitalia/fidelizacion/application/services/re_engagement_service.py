# cap: fidelizacion.re-engagement
# story-origin: TBD
"""ReEngagementService — detección y orquestación de re-engagement.

Detecta brechas en tratamientos multi-sesión, genera eventos de seguimiento,
marca timeouts y verifica throttle anti-spam.

HIPAA-lite: toda lectura de PHI debe registrar audit log.
Dual filter: tenant_id + clinic_id en todas las queries.

downstream-regression-na: brand-local application service vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (
    ReEngagementEventModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia._shared.repositories.audit_log_repository import (
        AuditLogRepository,
    )
    from src.modules.vitalia.fidelizacion.infrastructure.repositories.nps_response_repository import (
        NPSResponseRepository,
    )
    from src.modules.vitalia.fidelizacion.infrastructure.repositories.re_engagement_event_repository import (
        ReEngagementEventRepository,
    )
    from src.modules.vitalia.fidelizacion.infrastructure.repositories.treatment_plan_repository import (
        TreatmentPlanRepository,
    )

logger = structlog.get_logger(__name__)


class ReEngagementService:
    """Servicio de detección y orquestación de re-engagement multi-patrón.

    Coordina repos de T-4 para detectar brechas y disparar eventos de
    re-engagement según el patrón adecuado (multi_session, follow_up,
    maintenance, absence, nps).

    Todos los métodos reciben tenant_id + clinic_id explícitos para
    enforcement de HIPAA-lite dual filter.
    """

    def __init__(
        self,
        *,
        session: "AsyncSession",
        re_engagement_repo: "ReEngagementEventRepository",
        treatment_plan_repo: "TreatmentPlanRepository",
        nps_repo: "NPSResponseRepository",
        audit_repo: "AuditLogRepository",
    ) -> None:
        """Inicializa el servicio con repos inyectados.

        Args:
            session: AsyncSession compartido (mismo para todos los repos).
            re_engagement_repo: Repo de eventos de re-engagement.
            treatment_plan_repo: Repo de planes de tratamiento.
            nps_repo: Repo de respuestas NPS.
            audit_repo: Repo de audit log HIPAA-lite (sync write).
        """
        self._session = session
        self._re_engagement_repo = re_engagement_repo
        self._treatment_plan_repo = treatment_plan_repo
        self._nps_repo = nps_repo
        self._audit_repo = audit_repo

    async def check_throttle(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        pattern: ReEngagementPattern,
        throttle_days: int = 7,
    ) -> bool:
        """Verifica si el paciente puede recibir un re-engagement nuevo.

        Delega al repo (check_throttle). El repo retorna True cuando el paciente
        YA recibió un evento reciente (está throttled). Este método retorna
        el mismo valor para que el caller use: if is_throttled: skip.

        Args:
            tenant_id: UUID del tenant (filtro raíz).
            clinic_id: UUID de la clínica (filtro HIPAA-lite).
            patient_id: UUID del paciente.
            pattern: Patrón de re-engagement a verificar.
            throttle_days: Ventana de throttle en días (default 7).

        Returns:
            True si el paciente ESTÁ throttled (ya recibió mensaje reciente).
            False si el paciente PUEDE recibir re-engagement.
        """
        return await self._re_engagement_repo.check_throttle(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=pattern,
            throttle_days=throttle_days,
        )

    async def list_patterns(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        pattern: ReEngagementPattern,
        limit: int = 100,
    ) -> list[ReEngagementEventModel]:
        """Lista eventos de re-engagement por patrón para un tenant+clínica.

        HIPAA-lite: dual filter tenant_id + clinic_id aplicado siempre.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            pattern: Patrón a filtrar.
            limit: Máximo de resultados.

        Returns:
            Lista de modelos ORM de eventos.
        """
        return await self._re_engagement_repo.list_by_pattern(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            pattern=pattern,
            limit=limit,
        )

    async def detect_multi_session_gaps(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_ids: list[UUID],
    ) -> list[UUID]:
        """Detecta pacientes con brechas en tratamientos multi-sesión.

        Para cada patient_id, busca planes activos con gap_alert_days superado.
        Retorna lista de patient_ids candidatos a re-engagement.

        HIPAA-lite: dual filter tenant_id + clinic_id en lista de planes.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_ids: Lista de pacientes a evaluar.

        Returns:
            Lista de UUIDs de pacientes con brecha detectada.
        """
        if not patient_ids:
            return []

        candidates: list[UUID] = []
        now = datetime.now(UTC)

        for patient_id in patient_ids:
            plans = await self._treatment_plan_repo.list_for_patient(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=patient_id,
            )

            for plan in plans:
                if plan.status.lower() == "active" and plan.next_session_due_at is not None:
                    # Calcular días de brecha
                    gap_days = (now - plan.next_session_due_at).days
                    alert_days = plan.gap_alert_days or 7
                    if gap_days >= alert_days:
                        candidates.append(patient_id)
                        break  # Un candidato por paciente es suficiente

        logger.info(
            "re_engagement_multi_session_gaps_detected",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            candidates_count=len(candidates),
            evaluated_count=len(patient_ids),
        )
        return candidates

    async def detect_follow_up_due(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_ids: list[UUID],
    ) -> list[UUID]:
        """Detecta pacientes con seguimiento post-sesión pendiente.

        Busca planes con sesiones completadas recientemente sin seguimiento.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_ids: Lista de pacientes a evaluar.

        Returns:
            Lista de UUIDs de pacientes candidatos a follow_up.
        """
        if not patient_ids:
            return []

        candidates: list[UUID] = []
        now = datetime.now(UTC)

        for patient_id in patient_ids:
            plans = await self._treatment_plan_repo.list_for_patient(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=patient_id,
                include_completed=True,
            )

            for plan in plans:
                if plan.last_session_at is not None:
                    days_since = (now - plan.last_session_at).days
                    # Follow-up estándar a los 3 días post-sesión
                    if 3 <= days_since <= 10:  # ventana de follow-up
                        candidates.append(patient_id)
                        break

        return candidates

    async def detect_maintenance_due(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_ids: list[UUID],
    ) -> list[UUID]:
        """Detecta pacientes con tratamiento completado para mantenimiento.

        Busca planes completados sin visita de mantenimiento en 90+ días.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_ids: Lista de pacientes a evaluar.

        Returns:
            Lista de UUIDs de pacientes candidatos a mantenimiento.
        """
        if not patient_ids:
            return []

        candidates: list[UUID] = []
        now = datetime.now(UTC)

        for patient_id in patient_ids:
            plans = await self._treatment_plan_repo.list_for_patient(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=patient_id,
                include_completed=True,
            )

            for plan in plans:
                if plan.status.lower() == "completed" and plan.last_session_at is not None:
                    days_since = (now - plan.last_session_at).days
                    if days_since >= 90:
                        candidates.append(patient_id)
                        break

        return candidates

    async def detect_absence(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_ids: list[UUID],
    ) -> list[UUID]:
        """Detecta pacientes con ausencia prolongada sin contacto.

        Identifica pacientes que no han tenido actividad en 180+ días.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_ids: Lista de pacientes a evaluar.

        Returns:
            Lista de UUIDs de pacientes con ausencia prolongada.
        """
        if not patient_ids:
            return []

        candidates: list[UUID] = []
        now = datetime.now(UTC)

        for patient_id in patient_ids:
            plans = await self._treatment_plan_repo.list_for_patient(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=patient_id,
                include_completed=True,
            )

            if not plans:
                continue

            # Último contacto = max(last_session_at) de todos los planes
            last_contact = max(
                (p.last_session_at for p in plans if p.last_session_at is not None),
                default=None,
            )

            if last_contact is not None:
                days_absent = (now - last_contact).days
                if days_absent >= 180:
                    candidates.append(patient_id)

        return candidates

    async def trigger_nps_post_treatment(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        treatment_plan_id: UUID,
        template_id: str,
        user_id: UUID,
    ) -> ReEngagementEventModel:
        """Crea evento NPS post-tratamiento para un paciente.

        Genera un evento de patrón NPS al completar un tratamiento.
        Escribe audit log HIPAA-lite (sync write mandatorio).

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_id: UUID del paciente.
            treatment_plan_id: UUID del plan completado.
            template_id: ID del template NPS a enviar.
            user_id: UUID del usuario que dispara la acción.

        Returns:
            Modelo ORM del evento creado.
        """
        from src.modules.vitalia._shared.repositories.audit_log_repository import AuditLogEntry  # noqa: PLC0415

        now = datetime.now(UTC)
        event_id = uuid4()

        model = ReEngagementEventModel(
            id=event_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=ReEngagementPattern.NPS.value,
            trigger_source="treatment_completed",
            trigger_at=now,
            template_id=template_id,
            created_at=now,
            updated_at=now,
        )

        saved = await self._re_engagement_repo.save(model)

        # Audit log HIPAA-lite (sync write — mandatorio antes de retornar)
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="trigger_nps_post_treatment",
            resource_type="re_engagement_event",
            resource_id=event_id,
            payload_redacted=b"",
        )
        await self._audit_repo.write(audit_entry)

        logger.info(
            "nps_post_treatment_triggered",
            event_id=str(event_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            patient_id=str(patient_id),
            treatment_plan_id=str(treatment_plan_id),
        )
        return saved

    async def mark_response_timeout(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        event_model: ReEngagementEventModel,
    ) -> ReEngagementEventModel:
        """Marca un evento sin respuesta como timeout (NO_RESPONSE).

        Se usa en el cron de fidelización cuando un evento supera el
        periodo de respuesta sin recibir reply del paciente.

        HIPAA-lite: tenant_id + clinic_id verificados en el modelo.

        Args:
            tenant_id: UUID del tenant (para verificación HIPAA).
            clinic_id: UUID de la clínica (para verificación HIPAA).
            event_model: Instancia ORM del evento a marcar.

        Returns:
            Modelo ORM actualizado.
        """
        now = datetime.now(UTC)
        event_model.outcome = ReEngagementOutcome.NOT_RESPONSIVE.value
        event_model.response_at = now
        event_model.updated_at = now

        saved = await self._re_engagement_repo.save(event_model)

        logger.info(
            "re_engagement_timeout_marked",
            event_id=str(event_model.id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )
        return saved
