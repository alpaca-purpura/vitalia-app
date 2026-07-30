# cap: clinics.lisa.doctores
"""DNI race condition test — SC-5: unique constraint → 409 Conflict.

Tests that duplicate DNI within same tenant raises 409 (not 500).
The unique constraint is on (tenant_id, dni_hash).
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_duplicate_dni_raises_409() -> None:
    """SC-5: Creating doctor with duplicate DNI → raises DniConflictError."""
    from src.modules.vitalia.clinics.application.doctor_service import (
        DniConflictError,
        DoctorService,
    )

    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()

    # Simulate existing doctor with same DNI hash found
    existing_doctor = AsyncMock()
    existing_doctor.id = uuid4()

    mock_repo = AsyncMock()
    mock_repo.get_by_dni_hash.return_value = existing_doctor  # DNI already exists

    audit_repo = AsyncMock()
    mock_emitter = AsyncMock()

    service = DoctorService(
        doctor_repo=mock_repo,
        audit_repo=audit_repo,
        emitter=mock_emitter,
    )

    with pytest.raises(DniConflictError):
        await service.create_doctor(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            first_name="Ana",
            last_name="García",
            dni="12345678",
            email="ana@clinica.com",
            phone=None,
            specialty="Odontología",
            credential="12345",
            credential_country="PE",
            years_experience=5,
            languages=["es"],
        )
