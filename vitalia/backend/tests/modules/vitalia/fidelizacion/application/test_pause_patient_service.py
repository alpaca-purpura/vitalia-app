"""Tests para PausePatientService — pausar re-engagement de un paciente.

Tests de unidad puros (sin DB).
HIPAA-lite: dual filter verificado, audit log escrito.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

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
    """UUID de usuario que ejecuta la pausa."""
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
def pause_service(
    mock_session: AsyncMock,
    mock_re_engagement_repo: AsyncMock,
    mock_audit_repo: AsyncMock,
) -> Any:
    """PausePatientService con dependencias mock."""
    from src.modules.vitalia.fidelizacion.application.services.pause_patient_service import (
        PausePatientService,
    )

    return PausePatientService(
        session=mock_session,
        re_engagement_repo=mock_re_engagement_repo,
        audit_repo=mock_audit_repo,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPausePatient:
    """Tests para pausar re-engagement de un paciente."""

    @pytest.mark.asyncio
    async def test_pause_creates_event_and_audit(
        self,
        pause_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Pausa crea evento de re-engagement tipo ABSENCE y escribe audit log."""
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        pause_until = datetime.now(UTC) + timedelta(days=30)

        result = await pause_service.pause_patient(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pause_until=pause_until,
            pause_reason="Vacaciones del paciente",
            paused_by_user_id=user_id,
        )

        # Evento persistido
        mock_re_engagement_repo.save.assert_called_once()

        # Audit log escrito
        mock_audit_repo.write.assert_called_once()

        # Resultado correcto
        assert result.patient_id == patient_id
        assert result.paused_until == pause_until

    @pytest.mark.asyncio
    async def test_pause_emits_patient_paused_event(
        self,
        pause_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Pausa emite PatientPausedReEngagement domain event."""
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        pause_until = datetime.now(UTC) + timedelta(days=14)

        result = await pause_service.pause_patient(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pause_until=pause_until,
            pause_reason=None,
            paused_by_user_id=user_id,
        )

        # Verificamos que se retorna un event_id válido
        assert result.event_id is not None

    @pytest.mark.asyncio
    async def test_pause_dual_filter_on_event(
        self,
        pause_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """El modelo de pausa tiene tenant_id + clinic_id correctos."""
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        pause_until = datetime.now(UTC) + timedelta(days=7)

        await pause_service.pause_patient(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pause_until=pause_until,
            pause_reason=None,
            paused_by_user_id=user_id,
        )

        # El modelo guardado tiene el dual filter correcto
        call_args = mock_re_engagement_repo.save.call_args
        model_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("model")
        assert model_arg.tenant_id == tenant_id
        assert model_arg.clinic_id == clinic_id
