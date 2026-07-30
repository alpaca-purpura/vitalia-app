"""Tests for NPSResponseRepository (TDD RED phase).

Verifica: herencia CompoundScopeRepositoryBase, dual filter, list_for_patient,
list_detractors_untagged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.fidelizacion.infrastructure.models.nps_response_model import (
    NPSResponseModel,
)
from src.modules.vitalia.fidelizacion.infrastructure.repositories.nps_response_repository import (
    NPSResponseRepository,
)


class TestNPSResponseRepositoryContract:
    """Contratos arquitectónicos (sin DB)."""

    def test_inherits_compound_scope_repository(self) -> None:
        assert issubclass(NPSResponseRepository, CompoundScopeRepositoryBase)

    def test_scope_field_is_clinic_id(self) -> None:
        import inspect

        source = inspect.getsource(NPSResponseRepository)
        assert "clinic_id" in source, "NPSResponseRepository must configure scope_field='clinic_id'"

    def test_model_class_defined(self) -> None:
        assert hasattr(NPSResponseRepository, "MODEL")
        assert NPSResponseRepository.MODEL is NPSResponseModel  # type: ignore[attr-defined]

    def test_has_required_methods(self) -> None:
        for method in ["get_by_id", "save", "list_for_patient", "list_detractors_untagged"]:
            assert hasattr(NPSResponseRepository, method), f"Missing method: {method}"


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
    """Guarda respuesta NPS y la recupera con dual filter."""
    repo = NPSResponseRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)

    nps = NPSResponseModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        score=9,
        band="promoter",
        source="post_appointment_sms",
        tagged_in_inbox=False,
        responded_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(nps)
    await db_session.flush()

    result = await repo.get_by_id(id=nps.id, tenant_id=tenant_id, scope_id=clinic_id)
    assert result is not None
    assert result.score == 9
    assert result.band == "promoter"


@pytest.mark.integration
async def test_cross_tenant_isolation(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """NPS de otro tenant retorna None."""
    repo = NPSResponseRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)
    other_tenant = uuid4()

    nps = NPSResponseModel(
        id=uuid4(),
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        score=3,
        band="detractor",
        source="sms",
        tagged_in_inbox=False,
        responded_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(nps)
    await db_session.flush()

    result = await repo.get_by_id(id=nps.id, tenant_id=other_tenant, scope_id=clinic_id)
    assert result is None


@pytest.mark.integration
async def test_list_detractors_untagged(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """Retorna solo detractores con tagged_in_inbox=False."""
    repo = NPSResponseRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)
    other_patient = uuid4()

    # detractor untagged, detractor tagged, promoter untagged
    for score, tagged in [(3, False), (2, True), (10, False)]:
        from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand

        db_session.add(
            NPSResponseModel(
                id=uuid4(),
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=patient_id if score != 10 else other_patient,
                score=score,
                band=NPSBand.from_score(score).value,
                source="sms",
                tagged_in_inbox=tagged,
                responded_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    await db_session.flush()

    results = await repo.list_detractors_untagged(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    assert len(results) == 1
    assert results[0].band == "detractor"
    assert results[0].tagged_in_inbox is False


@pytest.mark.integration
async def test_list_for_patient(
    db_session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
) -> None:
    """Retorna NPS del paciente específico."""
    repo = NPSResponseRepository(session=db_session, scope_field="clinic_id")
    now = datetime.now(timezone.utc)
    other_patient = uuid4()

    for pid, score in [(patient_id, 8), (patient_id, 9), (other_patient, 5)]:
        from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand

        db_session.add(
            NPSResponseModel(
                id=uuid4(),
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                patient_id=pid,
                score=score,
                band=NPSBand.from_score(score).value,
                source="sms",
                tagged_in_inbox=False,
                responded_at=now,
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
