"""Tests para ProactiveOutboundService — SC-01, SC-02 y SC-03 del T-5.

Gherkin coverage:
  SC-01: test_send_proactive_reminder_full_flow (MARKETING template + opt-in)
  SC-02: test_send_proactive_blocks_marketing_no_optin (MARKETING template sin opt-in)
  SC-03: test_utility_template_passes_without_marketing_opt_in (UTILITY template)

Audit iter 2 fix F1: step 2 ahora consulta WHATSAPP_TEMPLATE_REGISTRY.requires_marketing_opt_in.
Templates UTILITY (recordatorio_proxima_sesion, recordatorio_control_doctor,
nps_post_tratamiento) no requieren opt-in.
Templates MARKETING (invitacion_mantenimiento, re_engagement_ausencia) requieren opt-in.

Tests de unidad puros (sin DB). Todos los repos y dependencias son mocks.
HIPAA-lite: audit log escrito, compliance gate aplicado, sin PHI en logs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (
    ReEngagementEventModel,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant_id() -> Any:
    """UUID de tenant."""
    return uuid4()


@pytest.fixture
def clinic_id() -> Any:
    """UUID de clínica."""
    return uuid4()


@pytest.fixture
def patient_id() -> Any:
    """UUID de paciente."""
    return uuid4()


@pytest.fixture
def user_id() -> Any:
    """UUID de usuario que dispara la acción."""
    return uuid4()


@pytest.fixture
def mock_session() -> AsyncMock:
    """AsyncSession mock."""
    return AsyncMock()


@pytest.fixture
def mock_re_engagement_repo() -> AsyncMock:
    """Mock de ReEngagementEventRepository."""
    repo = AsyncMock()
    repo.check_throttle = AsyncMock(return_value=False)
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_repo() -> AsyncMock:
    """Mock de AuditLogRepository."""
    repo = AsyncMock()
    repo.write = AsyncMock()
    return repo


@pytest.fixture
def mock_compliance_service() -> AsyncMock:
    """Mock de ComplianceService — permite el mensaje por default."""
    service = AsyncMock()
    check_result = MagicMock()
    check_result.allowed = True
    check_result.block_reason = None
    service.check = AsyncMock(return_value=check_result)
    return service


@pytest.fixture
def mock_patient_opt_in() -> MagicMock:
    """Mock de Patient con opt_out=False y marketing_opt_in=True."""
    patient = MagicMock()
    patient.opt_out = False
    patient.marketing_opt_in = True
    return patient


@pytest.fixture
def mock_patient_no_optin() -> MagicMock:
    """Mock de Patient con marketing_opt_in=False (debe bloquear MARKETING)."""
    patient = MagicMock()
    patient.opt_out = False
    patient.marketing_opt_in = False
    return patient


@pytest.fixture
def proactive_service(
    mock_session: AsyncMock,
    mock_re_engagement_repo: AsyncMock,
    mock_audit_repo: AsyncMock,
    mock_compliance_service: AsyncMock,
) -> Any:
    """ProactiveOutboundService con dependencias mock inyectadas."""
    from src.modules.vitalia.fidelizacion.application.services.proactive_outbound_service import (
        ProactiveOutboundService,
    )

    return ProactiveOutboundService(
        session=mock_session,
        re_engagement_repo=mock_re_engagement_repo,
        audit_repo=mock_audit_repo,
        compliance_service=mock_compliance_service,
    )


# ---------------------------------------------------------------------------
# SC-01: Flujo completo exitoso
# ---------------------------------------------------------------------------


class TestSendProactiveReminderFullFlow:
    """SC-01: Reminder proactivo con flujo completo exitoso."""

    @pytest.mark.asyncio
    async def test_send_proactive_reminder_full_flow(
        self,
        proactive_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        mock_compliance_service: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """SC-01: Reminder enviado exitosamente cuando paciente permite marketing.

        Given: tenant_id, clinic_id, patient_id con opt_out=False, marketing_opt_in=True
        When: send_proactive_reminder con template MARKETING, channel=whatsapp
        Then: audit_log escrito, compliance_service verificado, evento persistido
        """
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.sent_at = datetime.now(UTC)
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        # No throttled
        mock_re_engagement_repo.check_throttle.return_value = False

        # Compliance allows
        check_result = MagicMock()
        check_result.allowed = True
        check_result.block_reason = None
        mock_compliance_service.check = AsyncMock(return_value=check_result)

        # SC-01: template MARKETING + marketing_opt_in=True → pasa completo
        result = await proactive_service.send_proactive_reminder(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            patient_phone="+5491112345678",
            patient_name="Ana García",
            template_id="invitacion_mantenimiento",  # MARKETING template (requires opt-in)
            pattern=ReEngagementPattern.MULTI_SESSION,
            channel="whatsapp",
            marketing_opt_in=True,
            opt_out=False,
            user_id=user_id,
        )

        # Audit log escrito (HIPAA-lite mandatorio)
        mock_audit_repo.write.assert_called_once()

        # Compliance verificado
        mock_compliance_service.check.assert_called_once()

        # Evento persistido
        mock_re_engagement_repo.save.assert_called_once()

        # Resultado no bloqueado
        assert result.throttled is False
        assert result.blocked_reason is None

    @pytest.mark.asyncio
    async def test_send_proactive_reminder_throttled_skips_send(
        self,
        proactive_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        mock_compliance_service: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Cuando paciente está throttled, no se envía el mensaje."""
        # Throttled = True (ya recibió mensaje reciente)
        mock_re_engagement_repo.check_throttle.return_value = True

        result = await proactive_service.send_proactive_reminder(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            patient_phone="+5491112345678",
            patient_name="Ana García",
            template_id="invitacion_mantenimiento",  # MARKETING template — valid slug
            pattern=ReEngagementPattern.MULTI_SESSION,
            channel="whatsapp",
            marketing_opt_in=True,
            opt_out=False,
            user_id=user_id,
        )

        # No debe enviar ni persistir evento
        mock_re_engagement_repo.save.assert_not_called()
        assert result.throttled is True


# ---------------------------------------------------------------------------
# SC-02: Bloqueo por marketing_opt_in=False
# ---------------------------------------------------------------------------


class TestSendProactiveBlocksMarketingNoOptin:
    """SC-02: Bloqueo cuando paciente no tiene marketing_opt_in=True."""

    @pytest.mark.asyncio
    async def test_send_proactive_blocks_marketing_no_optin(
        self,
        proactive_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """SC-02: No se envía reminder de MARKETING si marketing_opt_in=False.

        Given: paciente con marketing_opt_in=False
        When: send_proactive_reminder con template MARKETING
        Then: resultado bloqueado, audit_log NO escrito (blocking antes PHI access),
              event NO persistido
        """
        # No throttled
        mock_re_engagement_repo.check_throttle.return_value = False

        # SC-02: template MARKETING + marketing_opt_in=False → bloqueado
        result = await proactive_service.send_proactive_reminder(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            patient_phone="+5491112345678",
            patient_name="Ana García",
            template_id="invitacion_mantenimiento",  # MARKETING — requires_marketing_opt_in=True
            pattern=ReEngagementPattern.MULTI_SESSION,
            channel="whatsapp",
            marketing_opt_in=False,  # <-- No opt-in → bloqueado para MARKETING
            opt_out=False,
            user_id=user_id,
        )

        # Evento NO debe persistirse
        mock_re_engagement_repo.save.assert_not_called()

        # Resultado bloqueado por falta de opt-in para template MARKETING
        assert result.blocked_reason == "marketing_opt_in_required"

    @pytest.mark.asyncio
    async def test_send_proactive_blocks_opted_out_patient(
        self,
        proactive_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Paciente con opt_out=True es bloqueado siempre (antes de consultar template)."""
        mock_re_engagement_repo.check_throttle.return_value = False

        result = await proactive_service.send_proactive_reminder(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            patient_phone="+5491112345678",
            patient_name="Ana García",
            template_id="recordatorio_proxima_sesion",  # UTILITY — valid slug
            pattern=ReEngagementPattern.FOLLOW_UP,
            channel="whatsapp",
            marketing_opt_in=True,
            opt_out=True,  # <-- Opted out → bloqueado en paso 1 (antes de registry check)
            user_id=user_id,
        )

        mock_re_engagement_repo.save.assert_not_called()
        assert result.blocked_reason == "patient_opted_out"

    @pytest.mark.asyncio
    async def test_utility_template_passes_without_marketing_opt_in(
        self,
        proactive_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        mock_compliance_service: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """SC-03: Template UTILITY no requiere marketing_opt_in.

        Given: paciente con marketing_opt_in=False
        When: send_proactive_reminder con template UTILITY (recordatorio_proxima_sesion)
        Then: mensaje enviado (no bloqueado por marketing_opt_in)

        Audit iter 2 fix F1 — regresión previa: el servicio bloqueaba UTILITY
        incorrectamente cuando marketing_opt_in=False.
        """
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.sent_at = datetime.now(UTC)
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)
        mock_re_engagement_repo.check_throttle.return_value = False

        check_result = MagicMock()
        check_result.allowed = True
        check_result.block_reason = None
        mock_compliance_service.check = AsyncMock(return_value=check_result)

        result = await proactive_service.send_proactive_reminder(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            patient_phone="+5491112345678",
            patient_name="Ana García",
            template_id="recordatorio_proxima_sesion",  # UTILITY — requires_marketing_opt_in=False
            pattern=ReEngagementPattern.FOLLOW_UP,
            channel="whatsapp",
            marketing_opt_in=False,  # Sin opt-in marketing — UTILITY no lo requiere
            opt_out=False,
            user_id=user_id,
        )

        # UTILITY debe pasar sin marketing_opt_in
        assert result.status == "sent"
        assert result.blocked_reason is None
        mock_re_engagement_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_compliance_block_prevents_send(
        self,
        mock_session: AsyncMock,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Bloque de ComplianceService impide el envío."""
        from src.modules.vitalia.fidelizacion.application.services.proactive_outbound_service import (
            ProactiveOutboundService,
        )

        mock_compliance_blocked = AsyncMock()
        check_result = MagicMock()
        check_result.allowed = False
        check_result.block_reason = "channel_not_encrypted"
        mock_compliance_blocked.check = AsyncMock(return_value=check_result)

        service = ProactiveOutboundService(
            session=mock_session,
            re_engagement_repo=mock_re_engagement_repo,
            audit_repo=mock_audit_repo,
            compliance_service=mock_compliance_blocked,
        )

        mock_re_engagement_repo.check_throttle.return_value = False

        result = await service.send_proactive_reminder(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            patient_phone="+5491112345678",
            patient_name="Ana García",
            template_id="invitacion_mantenimiento",  # valid MARKETING slug
            pattern=ReEngagementPattern.MULTI_SESSION,
            channel="whatsapp",
            marketing_opt_in=True,
            opt_out=False,
            user_id=user_id,
        )

        mock_re_engagement_repo.save.assert_not_called()
        assert result.blocked_reason is not None
