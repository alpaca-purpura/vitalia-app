"""Tests para ManualCallService — registrar llamadas manuales.

Tests de unidad puros (sin DB).
HIPAA-lite: dual filter verificado, audit log escrito.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
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
    """UUID del médico/admin que realizó la llamada."""
    return uuid4()


@pytest.fixture
def mock_session() -> AsyncMock:
    """AsyncSession mock."""
    return AsyncMock()


@pytest.fixture
def mock_re_engagement_repo() -> AsyncMock:
    """Mock de ReEngagementEventRepository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_repo() -> AsyncMock:
    """Mock de AuditLogRepository."""
    repo = AsyncMock()
    repo.write = AsyncMock()
    return repo


@pytest.fixture
def manual_call_service(
    mock_session: AsyncMock,
    mock_re_engagement_repo: AsyncMock,
    mock_audit_repo: AsyncMock,
) -> Any:
    """ManualCallService con dependencias mock."""
    from src.modules.vitalia.fidelizacion.application.services.manual_call_service import (
        ManualCallService,
    )

    return ManualCallService(
        session=mock_session,
        re_engagement_repo=mock_re_engagement_repo,
        audit_repo=mock_audit_repo,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestManualCallRecord:
    """Tests para registrar llamadas manuales."""

    @pytest.mark.asyncio
    async def test_record_call_creates_event_and_audit(
        self,
        manual_call_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Registro de llamada crea evento y escribe audit log."""
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.outcome = ReEngagementOutcome.RESCHEDULED.value
        saved_model.sent_at = datetime.now(UTC)
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        result = await manual_call_service.record_call(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            outcome=ReEngagementOutcome.RESCHEDULED,
            notes_plain=None,
            called_by_user_id=user_id,
            converted_to_appointment_id=None,
        )

        mock_re_engagement_repo.save.assert_called_once()
        mock_audit_repo.write.assert_called_once()
        assert result.outcome == ReEngagementOutcome.RESCHEDULED

    @pytest.mark.asyncio
    async def test_record_call_with_conversion(
        self,
        manual_call_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Llamada que resulta en cita reagendada."""
        appointment_id = uuid4()
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.outcome = ReEngagementOutcome.RESPONDED.value
        saved_model.sent_at = datetime.now(UTC)
        saved_model.converted_to_appointment_id = appointment_id
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        result = await manual_call_service.record_call(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            outcome=ReEngagementOutcome.RESPONDED,
            notes_plain=None,
            called_by_user_id=user_id,
            converted_to_appointment_id=appointment_id,
        )

        assert result.outcome == ReEngagementOutcome.RESPONDED

    @pytest.mark.asyncio
    async def test_record_call_dual_filter_on_model(
        self,
        manual_call_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Modelo guardado tiene tenant_id + clinic_id correcto."""
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.outcome = ReEngagementOutcome.NOT_RESPONSIVE.value
        saved_model.sent_at = datetime.now(UTC)
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        await manual_call_service.record_call(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            outcome=ReEngagementOutcome.NOT_RESPONSIVE,
            notes_plain=None,
            called_by_user_id=user_id,
            converted_to_appointment_id=None,
        )

        call_args = mock_re_engagement_repo.save.call_args
        model_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("model")
        assert model_arg.tenant_id == tenant_id
        assert model_arg.clinic_id == clinic_id
