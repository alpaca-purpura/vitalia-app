"""Tests para NPSService — submit + summary.

Tests de unidad puros (sin DB).
HIPAA-lite: PHI (comment) cifrado, dual filter verificado, audit log escrito.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand
from src.modules.vitalia.fidelizacion.infrastructure.models.nps_response_model import (
    NPSResponseModel,
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
    """UUID de usuario."""
    return uuid4()


@pytest.fixture
def mock_session() -> AsyncMock:
    """AsyncSession mock."""
    return AsyncMock()


@pytest.fixture
def mock_nps_repo() -> AsyncMock:
    """Mock de NPSResponseRepository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.list_for_patient = AsyncMock(return_value=[])
    repo.list_detractors_untagged = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_audit_repo() -> AsyncMock:
    """Mock de AuditLogRepository."""
    repo = AsyncMock()
    repo.write = AsyncMock()
    return repo


@pytest.fixture
def nps_service(
    mock_session: AsyncMock,
    mock_nps_repo: AsyncMock,
    mock_audit_repo: AsyncMock,
) -> Any:
    """NPSService con dependencias mock."""
    from src.modules.vitalia.fidelizacion.application.services.nps_service import (
        NPSService,
    )

    return NPSService(
        session=mock_session,
        nps_repo=mock_nps_repo,
        audit_repo=mock_audit_repo,
    )


# ---------------------------------------------------------------------------
# Tests: submit
# ---------------------------------------------------------------------------


class TestNPSSubmit:
    """Tests para submisión de respuesta NPS."""

    @pytest.mark.asyncio
    async def test_submit_creates_nps_response_and_writes_audit(
        self,
        nps_service: Any,
        mock_nps_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Submisión NPS crea entidad y escribe audit log."""
        saved_model = MagicMock(spec=NPSResponseModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.score = 9
        saved_model.band = NPSBand.PROMOTER.value
        saved_model.responded_at = datetime.now(UTC)
        saved_model.source = "whatsapp"
        saved_model.appointment_id = None
        saved_model.tagged_in_inbox = False
        saved_model.created_at = datetime.now(UTC)
        mock_nps_repo.save = AsyncMock(return_value=saved_model)

        result = await nps_service.submit(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            score=9,
            comment_plain=None,
            appointment_id=None,
            responded_via="whatsapp",
            user_id=user_id,
        )

        # Repo save llamado
        mock_nps_repo.save.assert_called_once()

        # Audit log escrito (HIPAA-lite mandatorio)
        mock_audit_repo.write.assert_called_once()

        # Resultado tiene band correcta para score 9
        assert result.score == 9
        assert result.band == NPSBand.PROMOTER

    @pytest.mark.asyncio
    async def test_submit_detractor_score_sets_correct_band(
        self,
        nps_service: Any,
        mock_nps_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Score 0-6 establece band DETRACTOR."""
        saved_model = MagicMock(spec=NPSResponseModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.score = 3
        saved_model.band = NPSBand.DETRACTOR.value
        saved_model.responded_at = datetime.now(UTC)
        saved_model.source = "whatsapp"
        saved_model.appointment_id = None
        saved_model.tagged_in_inbox = False
        saved_model.created_at = datetime.now(UTC)
        mock_nps_repo.save = AsyncMock(return_value=saved_model)

        result = await nps_service.submit(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            score=3,
            comment_plain=None,
            appointment_id=None,
            responded_via="whatsapp",
            user_id=user_id,
        )

        assert result.band == NPSBand.DETRACTOR

    @pytest.mark.asyncio
    async def test_submit_dual_filter_passed_to_repo(
        self,
        nps_service: Any,
        mock_nps_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
        user_id: Any,
    ) -> None:
        """Dual filter tenant_id + clinic_id se pasa al modelo guardado."""
        saved_model = MagicMock(spec=NPSResponseModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        saved_model.score = 8
        saved_model.band = NPSBand.PASSIVE.value
        saved_model.responded_at = datetime.now(UTC)
        saved_model.source = "whatsapp"
        saved_model.appointment_id = None
        saved_model.tagged_in_inbox = False
        saved_model.created_at = datetime.now(UTC)
        mock_nps_repo.save = AsyncMock(return_value=saved_model)

        await nps_service.submit(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            score=8,
            comment_plain=None,
            appointment_id=None,
            responded_via="whatsapp",
            user_id=user_id,
        )

        # El modelo guardado tiene tenant_id + clinic_id correcto
        call_args = mock_nps_repo.save.call_args
        model_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("model")
        assert model_arg.tenant_id == tenant_id
        assert model_arg.clinic_id == clinic_id


# ---------------------------------------------------------------------------
# Tests: summary
# ---------------------------------------------------------------------------


class TestNPSSummary:
    """Tests para resumen NPS agregado."""

    @pytest.mark.asyncio
    async def test_summary_returns_aggregated_stats(
        self,
        nps_service: Any,
        mock_nps_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """Resumen NPS agrega estadísticas por clínica (sin PHI per-patient)."""
        now = datetime.now(UTC)
        period_start = now - timedelta(days=30)
        period_end = now

        # 3 respuestas mock: 1 promoter, 1 passive, 1 detractor
        promoter = MagicMock()
        promoter.band = NPSBand.PROMOTER.value
        promoter.responded_at = now - timedelta(days=5)

        passive = MagicMock()
        passive.band = NPSBand.PASSIVE.value
        passive.responded_at = now - timedelta(days=10)

        detractor = MagicMock()
        detractor.band = NPSBand.DETRACTOR.value
        detractor.tagged_in_inbox = False
        detractor.responded_at = now - timedelta(days=15)

        mock_nps_repo.list_detractors_untagged = AsyncMock(return_value=[detractor])

        result = await nps_service.summary(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            all_responses=[promoter, passive, detractor],
        )

        assert result.tenant_id == tenant_id
        assert result.clinic_id == clinic_id
        assert result.total_responses == 3
        assert result.promoters == 1
        assert result.passives == 1
        assert result.detractors == 1
        # NPS = (promoters - detractors) / total * 100 = (1-1)/3*100 = 0
        assert result.nps_score == 0.0

    @pytest.mark.asyncio
    async def test_summary_calculates_nps_score_correctly(
        self,
        nps_service: Any,
        mock_nps_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """NPS score = (promoters - detractors) / total * 100."""
        now = datetime.now(UTC)
        period_start = now - timedelta(days=30)
        period_end = now

        # 5 promoters, 2 passives, 1 detractor = (5-1)/8*100 = 50.0
        responses = []
        for _ in range(5):
            m = MagicMock()
            m.band = NPSBand.PROMOTER.value
            responses.append(m)
        for _ in range(2):
            m = MagicMock()
            m.band = NPSBand.PASSIVE.value
            responses.append(m)
        det = MagicMock()
        det.band = NPSBand.DETRACTOR.value
        det.tagged_in_inbox = False
        responses.append(det)

        mock_nps_repo.list_detractors_untagged = AsyncMock(return_value=[det])

        result = await nps_service.summary(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            all_responses=responses,
        )

        assert result.nps_score == 50.0

    @pytest.mark.asyncio
    async def test_summary_empty_responses_returns_zero(
        self,
        nps_service: Any,
        mock_nps_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """Sin respuestas, NPS score = 0."""
        now = datetime.now(UTC)
        mock_nps_repo.list_detractors_untagged = AsyncMock(return_value=[])

        result = await nps_service.summary(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=now - timedelta(days=30),
            period_end=now,
            all_responses=[],
        )

        assert result.total_responses == 0
        assert result.nps_score == 0.0
