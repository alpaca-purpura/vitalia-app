"""Tests for TreatmentPlanRepository (TDD RED phase).

Verifica: herencia CompoundScopeRepositoryBase, dual filter, CRUD básico.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.fidelizacion.infrastructure.models.treatment_plan_model import (
    TreatmentPlanModel,
)
from src.modules.vitalia.fidelizacion.infrastructure.repositories.treatment_plan_repository import (
    TreatmentPlanRepository,
)


class TestTreatmentPlanRepositoryContract:
    """Contratos arquitectónicos (sin DB)."""

    def test_inherits_compound_scope_repository(self) -> None:
        assert issubclass(TreatmentPlanRepository, CompoundScopeRepositoryBase)

    def test_scope_field_is_clinic_id(self) -> None:
        import inspect

        source = inspect.getsource(TreatmentPlanRepository)
        assert "clinic_id" in source, "TreatmentPlanRepository must configure scope_field='clinic_id'"

    def test_model_class_defined(self) -> None:
        assert hasattr(TreatmentPlanRepository, "MODEL")
        assert TreatmentPlanRepository.MODEL is TreatmentPlanModel  # type: ignore[attr-defined]

    def test_has_required_methods(self) -> None:
        for method in ["get_by_id", "save", "list_for_patient"]:
            assert hasattr(TreatmentPlanRepository, method), f"Missing method: {method}"


@pytest.fixture()
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture()
def clinic_id() -> UUID:
    return uuid4()


@pytest.fixture()
def patient_id() -> UUID:
    return uuid4()


@pytest.mark.integration
async def test_save_and_get_by_id(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """Guarda plan de tratamiento y lo recupera con dual filter."""
    repo = TreatmentPlanRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    plan = TreatmentPlanModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        sessions_total=6,
        sessions_completed=0,
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(plan)
    await db_session.flush()

    result = await repo.get_by_id(id=plan.id, tenant_id=tenant_id, scope_id=clinic_id)
    assert result is not None
    assert result.sessions_total == 6
    assert result.status == "active"


@pytest.mark.integration
async def test_cross_tenant_isolation(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """Cross-tenant query retorna None (no leak PHI)."""
    repo = TreatmentPlanRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)
    other_tenant = uuid4()

    plan = TreatmentPlanModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        sessions_total=3,
        sessions_completed=1,
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add(plan)
    await db_session.flush()

    result = await repo.get_by_id(id=plan.id, tenant_id=other_tenant, scope_id=clinic_id)
    assert result is None


@pytest.mark.integration
async def test_list_for_patient(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """list_for_patient retorna solo planes activos del paciente en la clínica."""
    repo = TreatmentPlanRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)
    other_patient = uuid4()

    # Two plans for our patient, one for other patient
    for pid, sessions in [(patient_id, 4), (patient_id, 6), (other_patient, 2)]:
        db_session.add(
            TreatmentPlanModel(
                id=uuid4(),
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=pid,
                sessions_total=sessions,
                sessions_completed=0,
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
    await db_session.flush()

    results = await repo.list_for_patient(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
    )
    assert len(results) == 2
    for r in results:
        assert r.patient_id == patient_id


@pytest.mark.integration
async def test_soft_deleted_excluded(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """Planes con deleted_at no se retornan."""
    repo = TreatmentPlanRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    plan = TreatmentPlanModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        sessions_total=3,
        sessions_completed=3,
        status="completed",
        deleted_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(plan)
    await db_session.flush()

    result = await repo.get_by_id(id=plan.id, tenant_id=tenant_id, scope_id=clinic_id)
    assert result is None
