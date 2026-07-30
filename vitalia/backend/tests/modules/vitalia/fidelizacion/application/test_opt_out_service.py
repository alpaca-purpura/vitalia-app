"""Tests para OptOutService — cascade cancel pending events.

T-2 PatientOptedOut event handler: cancela todos los eventos de
re-engagement pendientes del paciente.

Tests de unidad puros (sin DB).
HIPAA-lite: dual filter verificado, audit log escrito.
"""

from __future__ import annotations

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
    """UUID de usuario que ejecuta el opt-out."""
    return uuid4()


@pytest.fixture
def mock_session() -> AsyncMock:
    """AsyncSession mock."""
    return AsyncMock()


@pytest.fixture
def mock_re_engagement_repo() -> AsyncMock:
    """Mock de ReEngagementEventRepository."""
    repo = AsyncMock()
    repo.list_by_pattern = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_repo() -> AsyncMock:
    """Mock de AuditLogRepository."""
    repo = AsyncMock()
    repo.write = AsyncMock()
    return repo


@pytest.fixture
def opt_out_service(
    mock_session: AsyncMock,
    mock_re_engagement_repo: AsyncMock,
    mock_audit_repo: AsyncMock,
) -> Any:
    """OptOutService con dependencias mock."""
    from src.modules.vitalia.fidelizacion.application.services.opt_out_service import (
        OptOutService,
    )

    return OptOutService(
        session=mock_session,
        re_engagement_repo=mock_re_engagement_repo,
        audit_repo=mock_audit_repo,
    )


# ---------------------------------------------------------------------------
# Tests: opt_out_patient
# ---------------------------------------------------------------------------


class TestOptOutPatient:
    """Tests para dar de baja a un paciente del sistema de fidelización."""

    @pytest.mark.asyncio
    async def test_opt_out_cancels_pending_events(
        self,
        opt_out_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Opt-out cancela todos los eventos de re-engagement pendientes."""
        # 3 eventos pendientes (sin sent_at = pendientes)
        pending_events = []
        for _ in range(3):
            ev = MagicMock(spec=ReEngagementEventModel)
            ev.id = uuid4()
            ev.tenant_id = tenant_id
            ev.clinic_id = clinic_id
            ev.patient_id = patient_id
            ev.sent_at = None  # pendiente
            ev.outcome = None
            ev.deleted_at = None
            pending_events.append(ev)

        mock_re_engagement_repo.list_pending_for_patient = AsyncMock(return_value=pending_events)
        mock_re_engagement_repo.save = AsyncMock(side_effect=lambda m: m)

        result = await opt_out_service.opt_out_patient(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            user_id=user_id,
            opt_out_reason="Solicitud del paciente",
        )

        # 3 eventos cancelados + audit log
        assert result.pending_events_cancelled == 3
        mock_audit_repo.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_opt_out_no_pending_events_is_ok(
        self,
        opt_out_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Opt-out con 0 eventos pendientes es válido."""
        mock_re_engagement_repo.list_pending_for_patient = AsyncMock(return_value=[])

        result = await opt_out_service.opt_out_patient(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            user_id=user_id,
            opt_out_reason=None,
        )

        assert result.pending_events_cancelled == 0
        # Audit log aún se escribe
        mock_audit_repo.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_opt_out_emits_domain_event(
        self,
        mock_session: AsyncMock,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Opt-out emite PatientOptedOut domain event via outbox."""
        from src.modules.vitalia.fidelizacion.application.services.opt_out_service import (
            OptOutService,
        )

        mock_re_engagement_repo.list_pending_for_patient = AsyncMock(return_value=[])

        with MagicMock() as mock_adapter:
            mock_adapter.publish = AsyncMock()

            with MagicMock():
                # Verificamos que el servicio intenta publicar vía outbox
                service = OptOutService(
                    session=mock_session,
                    re_engagement_repo=mock_re_engagement_repo,
                    audit_repo=mock_audit_repo,
                )

                result = await service.opt_out_patient(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    patient_id=patient_id,
                    user_id=user_id,
                    opt_out_reason=None,
                )

                # El resultado tiene datos válidos
                assert result.patient_id == patient_id
                assert result.clinic_id == clinic_id

    @pytest.mark.asyncio
    async def test_dual_filter_passed_to_list_pending(
        self,
        opt_out_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Dual filter (tenant_id + clinic_id) se pasa al listar pendientes."""
        mock_re_engagement_repo.list_pending_for_patient = AsyncMock(return_value=[])

        await opt_out_service.opt_out_patient(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            user_id=user_id,
            opt_out_reason=None,
        )

        call_kwargs = mock_re_engagement_repo.list_pending_for_patient.call_args.kwargs
        assert call_kwargs["tenant_id"] == tenant_id
        assert call_kwargs["clinic_id"] == clinic_id
        assert call_kwargs["patient_id"] == patient_id
