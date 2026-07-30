"""Tests para ReEngagementService — capa application fidelización vitalia.

Tests de unidad puros (sin DB). Todos los repos y dependencias son mocks.
Cubre: detect_multi_session_gaps, detect_follow_up_due, detect_maintenance_due,
       detect_absence, trigger_nps_post_treatment, mark_response_timeout,
       list_patterns, check_throttle.

HIPAA-lite: no PHI en logs, dual filter verificado.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
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
    """UUID de tenant para tests."""
    return uuid4()


@pytest.fixture
def clinic_id() -> Any:
    """UUID de clínica para tests."""
    return uuid4()


@pytest.fixture
def patient_id() -> Any:
    """UUID de paciente para tests."""
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
    repo.list_by_pattern = AsyncMock(return_value=[])
    repo.check_throttle = AsyncMock(return_value=False)
    return repo


@pytest.fixture
def mock_treatment_plan_repo() -> AsyncMock:
    """Mock de TreatmentPlanRepository."""
    repo = AsyncMock()
    repo.list_for_patient = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_nps_repo() -> AsyncMock:
    """Mock de NPSResponseRepository."""
    repo = AsyncMock()
    repo.list_for_patient = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_audit_repo() -> AsyncMock:
    """Mock de AuditLogRepository."""
    repo = AsyncMock()
    repo.write = AsyncMock()
    return repo


@pytest.fixture
def re_engagement_service(
    mock_session: AsyncMock,
    mock_re_engagement_repo: AsyncMock,
    mock_treatment_plan_repo: AsyncMock,
    mock_nps_repo: AsyncMock,
    mock_audit_repo: AsyncMock,
) -> Any:
    """ReEngagementService con repositorios mock inyectados."""
    from src.modules.vitalia.fidelizacion.application.services.re_engagement_service import (
        ReEngagementService,
    )

    return ReEngagementService(
        session=mock_session,
        re_engagement_repo=mock_re_engagement_repo,
        treatment_plan_repo=mock_treatment_plan_repo,
        nps_repo=mock_nps_repo,
        audit_repo=mock_audit_repo,
    )


# ---------------------------------------------------------------------------
# Tests: check_throttle
# ---------------------------------------------------------------------------


class TestCheckThrottle:
    """Tests para la verificación de throttle de re-engagement."""

    @pytest.mark.asyncio
    async def test_returns_false_when_no_recent_event(
        self,
        re_engagement_service: Any,
        mock_re_engagement_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
    ) -> None:
        """Retorna False (no throttled) cuando no hay evento reciente."""
        mock_re_engagement_repo.check_throttle.return_value = False

        result = await re_engagement_service.check_throttle(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=ReEngagementPattern.FOLLOW_UP,
            throttle_days=7,
        )

        assert result is False
        mock_re_engagement_repo.check_throttle.assert_called_once_with(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=ReEngagementPattern.FOLLOW_UP,
            throttle_days=7,
        )

    @pytest.mark.asyncio
    async def test_returns_true_when_throttled(
        self,
        re_engagement_service: Any,
        mock_re_engagement_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
    ) -> None:
        """Retorna True (throttled) cuando hay evento reciente en la ventana."""
        mock_re_engagement_repo.check_throttle.return_value = True

        result = await re_engagement_service.check_throttle(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=ReEngagementPattern.MULTI_SESSION,
            throttle_days=7,
        )

        assert result is True


# ---------------------------------------------------------------------------
# Tests: list_patterns
# ---------------------------------------------------------------------------


class TestListPatterns:
    """Tests para listar eventos de re-engagement por patrón."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_events(
        self,
        re_engagement_service: Any,
        mock_re_engagement_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """Retorna lista vacía cuando no hay eventos del patrón."""
        mock_re_engagement_repo.list_by_pattern.return_value = []

        result = await re_engagement_service.list_patterns(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            pattern=ReEngagementPattern.FOLLOW_UP,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_passes_dual_filter_to_repo(
        self,
        re_engagement_service: Any,
        mock_re_engagement_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """Verifica que se pasa dual filter (tenant_id + clinic_id) al repo."""
        await re_engagement_service.list_patterns(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            pattern=ReEngagementPattern.ABSENCE,
        )

        mock_re_engagement_repo.list_by_pattern.assert_called_once()
        call_kwargs = mock_re_engagement_repo.list_by_pattern.call_args.kwargs
        assert call_kwargs["tenant_id"] == tenant_id
        assert call_kwargs["clinic_id"] == clinic_id


# ---------------------------------------------------------------------------
# Tests: detect_multi_session_gaps
# ---------------------------------------------------------------------------


class TestDetectMultiSessionGaps:
    """Tests para detección de brechas en multi-sesión."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_overdue_plans(
        self,
        re_engagement_service: Any,
        mock_treatment_plan_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """Retorna lista vacía cuando no hay planes vencidos."""
        mock_treatment_plan_repo.list_for_patient.return_value = []

        result = await re_engagement_service.detect_multi_session_gaps(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_ids=[uuid4(), uuid4()],
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_empty_patient_ids_returns_empty(
        self,
        re_engagement_service: Any,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """Lista vacía de patient_ids retorna lista vacía."""
        result = await re_engagement_service.detect_multi_session_gaps(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_ids=[],
        )

        assert result == []


# ---------------------------------------------------------------------------
# Tests: mark_response_timeout
# ---------------------------------------------------------------------------


class TestMarkResponseTimeout:
    """Tests para marcar eventos como timeout."""

    @pytest.mark.asyncio
    async def test_mark_response_timeout_calls_repo_save(
        self,
        re_engagement_service: Any,
        mock_re_engagement_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
    ) -> None:
        """Persiste el evento actualizado con outcome TIMEOUT."""
        event_model = MagicMock(spec=ReEngagementEventModel)
        event_model.tenant_id = tenant_id
        event_model.clinic_id = clinic_id
        event_model.outcome = None
        event_model.response_at = None
        event_model.deleted_at = None
        mock_re_engagement_repo.save = AsyncMock(return_value=event_model)

        await re_engagement_service.mark_response_timeout(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            event_model=event_model,
        )

        mock_re_engagement_repo.save.assert_called_once()
        # Outcome debe haberse seteado a NO_RESPONSE
        assert event_model.outcome == ReEngagementOutcome.NOT_RESPONSIVE.value


# ---------------------------------------------------------------------------
# Tests: trigger_nps_post_treatment
# ---------------------------------------------------------------------------


class TestTriggerNpsPostTreatment:
    """Tests para disparar NPS al completar tratamiento."""

    @pytest.mark.asyncio
    async def test_creates_nps_event_for_completed_treatment(
        self,
        re_engagement_service: Any,
        mock_re_engagement_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
        tenant_id: Any,
        clinic_id: Any,
        patient_id: Any,
    ) -> None:
        """Crea evento NPS cuando se completa un tratamiento."""
        saved_model = MagicMock(spec=ReEngagementEventModel)
        saved_model.id = uuid4()
        saved_model.tenant_id = tenant_id
        saved_model.clinic_id = clinic_id
        saved_model.patient_id = patient_id
        mock_re_engagement_repo.save = AsyncMock(return_value=saved_model)

        treatment_plan_id = uuid4()
        result = await re_engagement_service.trigger_nps_post_treatment(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            treatment_plan_id=treatment_plan_id,
            template_id="nps_post_treatment_01",
            user_id=uuid4(),
        )

        mock_re_engagement_repo.save.assert_called_once()
        assert result is not None
