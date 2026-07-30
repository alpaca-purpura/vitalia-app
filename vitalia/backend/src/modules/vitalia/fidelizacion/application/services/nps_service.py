# cap: patients.nps-tracking
# story-origin: TBD
"""NPSService — registro y resumen de encuestas NPS.

submit: Almacena respuesta NPS del paciente con PHI cifrado (comment pgcrypto).
summary: Agrega estadísticas NPS por tenant+clínica+periodo (sin PHI per-patient).

HIPAA-lite:
  - comment (texto libre paciente) cifrado BYTEA vía pgcrypto en DB.
  - Audit log sync write al registrar respuesta NPS.
  - Dual filter tenant_id + clinic_id en todas las queries.
  - summary() retorna stats agregadas (sin PHI per-patient).

downstream-regression-na: brand-local application service vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.fidelizacion.application.dtos.nps_dtos import (
    NPSResponseResponse,
    NPSSummaryResponse,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand
from src.modules.vitalia.fidelizacion.infrastructure.models.nps_response_model import (
    NPSResponseModel,
)

# Outbox adapter_bus — module-level import with test fallback
try:
    from luana_core_events.outbox.application.event_bus_adapter import (  # type: ignore[import]
        adapter_bus,
    )
except (ImportError, Exception):  # pragma: no cover
    from unittest.mock import AsyncMock as _AsyncMock  # noqa: PLC0415

    class _FallbackBus:  # type: ignore[no-redef]
        """Fallback bus for test environments."""

        publish = _AsyncMock()

    adapter_bus = _FallbackBus()

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia._shared.repositories.audit_log_repository import (
        AuditLogRepository,
    )
    from src.modules.vitalia.fidelizacion.infrastructure.repositories.nps_response_repository import (
        NPSResponseRepository,
    )

logger = structlog.get_logger(__name__)


class NPSService:
    """Servicio de gestión de encuestas NPS para fidelización vitalia.

    Maneja el ciclo completo NPS: recepción de respuesta, almacenamiento
    PHI-safe y generación de reportes agregados.
    """

    def __init__(
        self,
        *,
        session: "AsyncSession",
        nps_repo: "NPSResponseRepository",
        audit_repo: "AuditLogRepository",
    ) -> None:
        """Inicializa el servicio con repos inyectados.

        Args:
            session: AsyncSession compartido.
            nps_repo: Repo de respuestas NPS.
            audit_repo: Repo de audit log HIPAA-lite (sync write).
        """
        self._session = session
        self._nps_repo = nps_repo
        self._audit_repo = audit_repo

    async def submit(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        score: int,
        comment_plain: str | None,
        appointment_id: UUID | None,
        responded_via: str,
        user_id: UUID,
    ) -> NPSResponseResponse:
        """Registra una respuesta NPS del paciente.

        El campo comment_plain se cifra vía pgcrypto en DB (BYTEA).
        La API responde sin el comment (PHI excluido de response).
        Audit log escrito sync antes de retornar.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica (dual filter HIPAA-lite).
            patient_id: UUID del paciente.
            score: Puntuación NPS (0-10).
            comment_plain: Comentario libre del paciente (PHI — se cifra).
            appointment_id: UUID de la cita relacionada (opcional).
            responded_via: Canal de respuesta (ej. "whatsapp").
            user_id: UUID del usuario que registra (para audit log).

        Returns:
            NPSResponseResponse con datos del registro (sin PHI comment).
        """
        from src.modules.vitalia._shared.repositories.audit_log_repository import (
            AuditLogEntry,
        )
        from src.modules.vitalia.fidelizacion.domain.events.events import NPSScoreCollected

        now = datetime.now(UTC)
        response_id = uuid4()
        band = NPSBand.from_score(score)

        # Cifrado PHI: comment_plain → bytes.
        # Migration 025 habilita pgcrypto symmetric encryption en nps_responses.comment
        # mediante un trigger BEFORE INSERT/UPDATE que aplica pgp_sym_encrypt().
        # La capa de aplicación pasa el texto en bytes; la DB lo almacena cifrado.
        # El trigger usa current_setting('app.encryption_key') como KEK.
        # KEK rotation: anual per hipaa-lite.md § Encryption at rest.
        comment_bytes: bytes | None = comment_plain.encode("utf-8") if comment_plain else None

        model = NPSResponseModel(
            id=response_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            score=score,
            band=band.value,
            comment=comment_bytes,
            appointment_id=appointment_id,
            source=responded_via,
            responded_at=now,
            tagged_in_inbox=False,
            created_at=now,
            updated_at=now,
        )

        saved = await self._nps_repo.save(model)

        # Audit log HIPAA-lite sync write mandatorio
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="submit_nps_response",
            resource_type="nps_response",
            resource_id=response_id,
            payload_redacted=b"",  # comment PHI excluido del audit log
        )
        await self._audit_repo.write(audit_entry)

        # Emitir NPSScoreCollected event via outbox
        domain_event = NPSScoreCollected.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            nps_response_id=response_id,
            score=score,
            band=band.value,
            appointment_id=appointment_id,
        )
        try:
            await adapter_bus.publish(domain_event, session=self._session)
        except Exception as exc:
            logger.warning(
                "nps_event_publish_failed",
                response_id=str(response_id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )

        logger.info(
            "nps_response_submitted",
            response_id=str(response_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            patient_id=str(patient_id),
            score=score,
            band=band.value,
        )

        return NPSResponseResponse(
            id=saved.id,
            tenant_id=saved.tenant_id,
            clinic_id=saved.clinic_id,
            patient_id=saved.patient_id,
            score=saved.score,
            band=NPSBand(saved.band),
            appointment_id=saved.appointment_id,
            responded_via=saved.source,
            responded_at=saved.responded_at,
            tagged_in_inbox=saved.tagged_in_inbox,
            created_at=saved.created_at,
        )

    async def summary(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: datetime,
        period_end: datetime,
        all_responses: list[Any],
    ) -> NPSSummaryResponse:
        """Genera resumen NPS agregado para un periodo.

        NO incluye PHI per-patient. Solo estadísticas agregadas.
        Usado para dashboards y reportes de clínica.

        HIPAA-lite: retorna solo stats anónimas — no comment, no patient name.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            period_start: Inicio del periodo de análisis.
            period_end: Fin del periodo de análisis.
            all_responses: Lista de NPSResponseModel para el periodo.

        Returns:
            NPSSummaryResponse con estadísticas NPS (sin PHI).
        """
        total = len(all_responses)

        if total == 0:
            detractors_untagged = await self._nps_repo.list_detractors_untagged(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                limit=1,
            )
            return NPSSummaryResponse(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                period_start=period_start,
                period_end=period_end,
                total_responses=0,
                promoters=0,
                passives=0,
                detractors=0,
                nps_score=0.0,
                detractors_untagged=len(detractors_untagged),
            )

        promoters = sum(1 for r in all_responses if r.band == NPSBand.PROMOTER.value)
        passives = sum(1 for r in all_responses if r.band == NPSBand.PASSIVE.value)
        detractors = sum(1 for r in all_responses if r.band == NPSBand.DETRACTOR.value)

        # NPS standard formula: (promoters - detractors) / total * 100
        nps_score = round((promoters - detractors) / total * 100, 2)

        detractors_untagged_list = await self._nps_repo.list_detractors_untagged(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            limit=200,
        )

        return NPSSummaryResponse(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            total_responses=total,
            promoters=promoters,
            passives=passives,
            detractors=detractors,
            nps_score=nps_score,
            detractors_untagged=len(detractors_untagged_list),
        )
