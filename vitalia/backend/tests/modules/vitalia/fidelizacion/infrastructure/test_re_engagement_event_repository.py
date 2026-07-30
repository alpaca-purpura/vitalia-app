"""Tests for ReEngagementEventRepository (TDD RED phase).

Incluye: cross-tenant isolation (gherkin SC-02), throttle check, list_by_pattern.
Markers: integration (requieren Postgres).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (
    ReEngagementEventModel,
)
from src.modules.vitalia.fidelizacion.infrastructure.repositories.re_engagement_event_repository import (
    ReEngagementEventRepository,
)

# ────────────────────────────────────────────────────────────────
# Architecture contract (no DB needed)
# ────────────────────────────────────────────────────────────────


class TestReEngagementEventRepositoryContract:
    """Re test a nivel unitario — herencia + atributos del engine."""

    def test_inherits_compound_scope_repository(self) -> None:
        assert issubclass(ReEngagementEventRepository, CompoundScopeRepositoryBase)

    def test_scope_field_is_clinic_id(self, db_session: AsyncSession | None = None) -> None:
        """scope_field debe ser 'clinic_id' — verificado via inspect source o instancia."""
        import inspect

        source = inspect.getsource(ReEngagementEventRepository)
        assert "clinic_id" in source, "ReEngagementEventRepository must configure scope_field='clinic_id'"

    def test_model_class_defined(self) -> None:
        """MODEL class attribute requerida por CompoundScopeRepositoryBase."""
        assert hasattr(ReEngagementEventRepository, "MODEL")
        assert ReEngagementEventRepository.MODEL is ReEngagementEventModel  # type: ignore[attr-defined]

    def test_has_required_methods(self) -> None:
        for method in ["get_by_id", "list_by_pattern", "save", "check_throttle"]:
            assert hasattr(ReEngagementEventRepository, method), f"Missing method: {method}"


# ────────────────────────────────────────────────────────────────
# Integration tests (require Postgres — marker integration)
# ────────────────────────────────────────────────────────────────


@pytest.fixture()
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture()
def clinic_id() -> UUID:
    return uuid4()


@pytest.fixture()
def patient_id() -> UUID:
    return uuid4()


@pytest.fixture()
def other_tenant_id() -> UUID:
    return uuid4()


@pytest.fixture()
def other_clinic_id() -> UUID:
    return uuid4()


@pytest.mark.integration
async def test_save_and_get_by_id(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """Guarda un evento y lo recupera por ID con dual filter."""
    repo = ReEngagementEventRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    event = ReEngagementEventModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        pattern="multi_session",
        trigger_source="cron_fidelizacion",
        trigger_at=now,
        retry_count=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(event)
    await db_session.flush()

    result = await repo.get_by_id(id=event.id, tenant_id=tenant_id, scope_id=clinic_id)
    assert result is not None
    assert result.id == event.id


@pytest.mark.integration
async def test_cross_tenant_query_returns_404(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    other_tenant_id: UUID,
) -> None:
    """SC-02: Solicitud con tenant_id_A + clinic_id ajeno retorna None (no leak).

    Gherkin: Given an existing re_engagement_event for tenant_A/clinic_A
             When queried with tenant_B (different tenant)
             Then the result is None (no cross-tenant data leak)
    """
    repo = ReEngagementEventRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    event = ReEngagementEventModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        pattern="follow_up",
        trigger_source="cron_fidelizacion",
        trigger_at=now,
        retry_count=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(event)
    await db_session.flush()

    # Query with different tenant_id — must return None
    result = await repo.get_by_id(id=event.id, tenant_id=other_tenant_id, scope_id=clinic_id)
    assert result is None, "Cross-tenant query MUST return None (no data leak)"


@pytest.mark.integration
async def test_cross_clinic_query_returns_none(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    other_clinic_id: UUID,
) -> None:
    """SC-04: Solicitud con clinic_id_X siendo user de clinic_id_Y → None.

    HIPAA-lite: dual filter tenant_id + clinic_id.
    """
    repo = ReEngagementEventRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    event = ReEngagementEventModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        pattern="maintenance",
        trigger_source="cron_fidelizacion",
        trigger_at=now,
        retry_count=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(event)
    await db_session.flush()

    result = await repo.get_by_id(id=event.id, tenant_id=tenant_id, scope_id=other_clinic_id)
    assert result is None, "Cross-clinic query MUST return None (HIPAA-lite dual filter)"


@pytest.mark.integration
async def test_list_by_pattern(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """list_by_pattern retorna solo eventos del tenant/clinic/pattern dados."""
    repo = ReEngagementEventRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    # Create 2 matching events + 1 different pattern
    for pattern in ["multi_session", "multi_session", "follow_up"]:
        db_session.add(
            ReEngagementEventModel(
                id=uuid4(),
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=patient_id,
                pattern=pattern,
                trigger_source="cron",
                trigger_at=now,
                retry_count=0,
                created_at=now,
                updated_at=now,
            )
        )
    await db_session.flush()

    results = await repo.list_by_pattern(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        pattern=ReEngagementPattern.MULTI_SESSION,
    )
    assert len(results) == 2
    for r in results:
        assert r.pattern == ReEngagementPattern.MULTI_SESSION


@pytest.mark.integration
async def test_check_throttle_within_days(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """check_throttle retorna True si ya se envió dentro del periodo throttle."""
    repo = ReEngagementEventRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    # Evento enviado hace 2 días
    db_session.add(
        ReEngagementEventModel(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern="multi_session",
            trigger_source="cron",
            trigger_at=now - timedelta(days=2),
            sent_at=now - timedelta(days=2),
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
    )
    await db_session.flush()

    # Throttle de 7 días — debe retornar True (ya enviado dentro del periodo)
    throttled = await repo.check_throttle(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        pattern=ReEngagementPattern.MULTI_SESSION,
        throttle_days=7,
    )
    assert throttled is True


@pytest.mark.integration
async def test_check_throttle_outside_days(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """check_throttle retorna False si el último envío fue antes del periodo."""
    repo = ReEngagementEventRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    # Evento enviado hace 10 días (fuera del throttle de 7)
    db_session.add(
        ReEngagementEventModel(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern="follow_up",
            trigger_source="cron",
            trigger_at=now - timedelta(days=10),
            sent_at=now - timedelta(days=10),
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
    )
    await db_session.flush()

    throttled = await repo.check_throttle(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        pattern=ReEngagementPattern.FOLLOW_UP,
        throttle_days=7,
    )
    assert throttled is False


@pytest.mark.integration
async def test_soft_delete_excluded_from_queries(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """Registros con deleted_at no se retornan en queries normales."""
    repo = ReEngagementEventRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    event = ReEngagementEventModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        pattern="absence",
        trigger_source="cron",
        trigger_at=now,
        deleted_at=now,  # soft-deleted
        retry_count=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(event)
    await db_session.flush()

    result = await repo.get_by_id(id=event.id, tenant_id=tenant_id, scope_id=clinic_id)
    assert result is None, "Soft-deleted records must be excluded from queries"
