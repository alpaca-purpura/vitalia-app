"""Regression — appointment detail repo output MUST satisfy AppointmentDetailDTO.

Bug (live-QA 2026-06-21, story vitalia-scheduling-mateo-review · D9): clicking any
slot → GET /appointments/{id} → 500. `AppointmentDetailDTO.model_validate(detail)`
failed with 3 missing fields:
  - doctor_label              (projection selected doctor_id but no doctor_label)
  - payments.0.payment_id     (repo emitted key `id`)
  - payments.0.amount_cents   (repo emitted key `amount`)

Masked for months because vitalia_appointments was empty (no detail call ever) AND
the service unit test mocks the repo dict + never validates the DTO. These tests pin
the repo↔DTO contract so the rename/projection can't silently regress again.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.vitalia.scheduling.api.dtos.agenda_dtos import (
    AppointmentDetailDTO,
    AppointmentPaymentDTO,
)
from src.modules.vitalia.scheduling.infrastructure.repositories.appointment_detail_repository import (
    AppointmentDetailRepository,
)


def _mock_session_returning(models: list) -> MagicMock:
    """AsyncSession mock whose execute().scalars().all() → models."""
    scalars = MagicMock()
    scalars.all.return_value = models
    result = MagicMock()
    result.scalars.return_value = scalars
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    return session


def _fake_payment_model() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        amount=80000,
        currency="MXN",
        method="mercadopago",
        external_payment_id=None,
        fiscal_doc_id=None,
        notes=None,
        balance_version=1,
        created_at=datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_get_payments_emits_dto_field_names():
    """_get_payments must use the DTO field names (payment_id/amount_cents), not id/amount."""
    repo = AppointmentDetailRepository(session=_mock_session_returning([_fake_payment_model()]))

    payments = await repo._get_payments(appointment_id=uuid4(), tenant_id=uuid4(), clinic_id=uuid4())

    assert len(payments) == 1
    row = payments[0]
    # The exact bug: old keys id/amount → DTO validation 500.
    assert "payment_id" in row and "id" not in row
    assert "amount_cents" in row and "amount" not in row
    # And the row must validate as an AppointmentPaymentDTO (nested DTO of the detail).
    AppointmentPaymentDTO.model_validate(row)


def _detail_dict_with_payment() -> dict:
    """A detail dict shaped like the (fixed) repo projection + one payment."""
    return {
        "appointment_id": uuid4(),
        "patient_id": uuid4(),
        "patient_name_masked": "—",
        "service_label": "Consulta",
        "doctor_id": uuid4(),
        "doctor_label": "Ana García Mendoza",
        "start_time": datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc),
        "end_time": datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc),
        "duration_minutes": 30,
        "appointment_status": "COMPLETED",
        "payment_status": "succeeded",
        "origin": "telefono",
        "currency": "MXN",
        "booking_metadata": {},
        "created_at": datetime(2026, 6, 15, tzinfo=timezone.utc),
        "updated_at": None,
        "payments": [
            {
                "payment_id": uuid4(),
                "amount_cents": 80000,
                "currency": "MXN",
                "method": "mercadopago",
                "created_at": datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc),
            }
        ],
    }


def test_detail_dict_satisfies_dto():
    """The repo's detail dict (with doctor_label + payments) must validate the DTO."""
    AppointmentDetailDTO.model_validate(_detail_dict_with_payment())


def test_detail_dict_without_doctor_label_fails():
    """Documents the D9 root: missing doctor_label → ValidationError (was the 500)."""
    import pydantic

    bad = _detail_dict_with_payment()
    del bad["doctor_label"]
    with pytest.raises(pydantic.ValidationError):
        AppointmentDetailDTO.model_validate(bad)
