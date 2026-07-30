# cap: fidelizacion.re-engagement
# story-origin: TBD
"""ManualCallService — registrar llamadas telefónicas manuales.

Permite al equipo clínico registrar el resultado de llamadas realizadas
manualmente a pacientes fuera del flujo automatizado.

Registra un evento de re-engagement con trigger_source="manual_call"
y el outcome correspondiente (SCHEDULED, CONVERTED, NO_ANSWER, etc.).

HIPAA-lite:
  - Dual filter tenant_id + clinic_id.
  - Audit log sync write mandatorio al registrar llamada.
  - notes_plain cifrado (BYTEA pgcrypto) si se provee.

downstream-regression-na: brand-local application service vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ManualCallResponse,
)
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
    from src.modules.vitalia.fidelizacion.infrastructure.repositories.re_engagement_event_repository import (
        ReEngagementEventRepository,
    )

logger = structlog.get_logger(__name__)


class ManualCallService:
    """Servicio de registro de llamadas manuales a pacientes.

    El equipo clínico registra calls realizadas fuera del sistema automatizado.
    El call se persiste como ReEngagementEvent con trigger_source="manual_call".
    """

    def __init__(
        self,
        *,
        session: "AsyncSession",
        re_engagement_repo: "ReEngagementEventRepository",
        audit_repo: "AuditLogRepository",
    ) -> None:
        """Inicializa el servicio con repos inyectados.

        Args:
            session: AsyncSession compartido.
            re_engagement_repo: Repo de eventos de re-engagement.
            audit_repo: Repo de audit log HIPAA-lite.
        """
        self._session = session
        self._re_engagement_repo = re_engagement_repo
        self._audit_repo = audit_repo

    async def record_call(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        outcome: ReEngagementOutcome,
        notes_plain: str | None,
        called_by_user_id: UUID,
        converted_to_appointment_id: UUID | None = None,
    ) -> ManualCallResponse:
        """Registra una llamada manual y su resultado.

        Persiste como ReEngagementEvent tipo FOLLOW_UP (por default)
        con trigger_source="manual_call" y outcome inmediato.

        HIPAA-lite:
          - notes_plain almacenado como PHI (payload_phi BYTEA pgcrypto).
          - Audit log sync write mandatorio.
          - Dual filter tenant_id + clinic_id en modelo.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_id: UUID del paciente.
            outcome: Resultado de la llamada.
            notes_plain: Notas de la llamada (PHI — cifrado BYTEA).
            called_by_user_id: UUID del usuario que realizó la llamada.
            converted_to_appointment_id: UUID del turno si convirtió.

        Returns:
            ManualCallResponse con datos del registro.
        """
        from src.modules.vitalia._shared.repositories.audit_log_repository import (
            AuditLogEntry,
        )

        now = datetime.now(UTC)
        event_id = uuid4()

        # notes_plain = PHI → cifrado como BYTEA (payload_phi)
        notes_bytes: bytes | None = notes_plain.encode("utf-8") if notes_plain else None

        model = ReEngagementEventModel(
            id=event_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=ReEngagementPattern.FOLLOW_UP.value,
            trigger_source="manual_call",
            trigger_at=now,
            sent_at=now,
            response_at=now,
            outcome=outcome.value,
            converted_to_appointment_id=converted_to_appointment_id,
            payload_phi=notes_bytes,  # PHI cifrado en DB via pgcrypto
            created_at=now,
            updated_at=now,
        )

        saved = await self._re_engagement_repo.save(model)

        # Audit log HIPAA-lite sync write mandatorio
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=called_by_user_id,
            action="record_manual_call",
            resource_type="re_engagement_event",
            resource_id=event_id,
            payload_redacted=b"",  # notes_plain excluidas del audit log (PHI)
        )
        await self._audit_repo.write(audit_entry)

        logger.info(
            "manual_call_recorded",
            event_id=str(event_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            patient_id=str(patient_id),
            outcome=outcome.value,
        )

        return ManualCallResponse(
            event_id=saved.id,
            patient_id=patient_id,
            outcome=outcome,
            recorded_at=now,
        )
