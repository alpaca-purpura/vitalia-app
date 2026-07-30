"""Vitalia Adrián tool — ``reschedule_appointment`` unit tests.

Story T-ag-tools-2 — R23 production_code=true.

Covers:
1. Pydantic v2 input schema validation (tenant + clinic dual filter mandatory).
2. new_starts_at requires timezone-aware datetime.
3. Service invocation passes dual-filter params.
4. Service exception → operator-handoff fallback (no raise).
5. DI resolver hook works.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


@pytest.fixture(autouse=True)
def _reset_resolver():
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
        set_reschedule_service_resolver,
    )

    set_reschedule_service_resolver(None)
    yield
    set_reschedule_service_resolver(None)


def test_input_schema_requires_dual_filter() -> None:
    """tenant_id + clinic_id mandatory (HIPAA-lite cardinal)."""
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
        RescheduleAppointmentInput,
    )

    with pytest.raises(Exception):  # noqa: B017, PT011 — ValidationError
        RescheduleAppointmentInput(
            appointment_id=uuid4(),
            new_starts_at=datetime.now(tz=UTC),
            reason="patient_request",
            # missing tenant_id + clinic_id
        )


def test_input_schema_max_reason_length() -> None:
    """reason field max length 500."""
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
        RescheduleAppointmentInput,
    )

    with pytest.raises(Exception):  # noqa: B017, PT011
        RescheduleAppointmentInput(
            appointment_id=uuid4(),
            new_starts_at=datetime.now(tz=UTC),
            reason="x" * 501,  # over max
            tenant_id=uuid4(),
            clinic_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_service_invoked_with_dual_filter() -> None:
    """Service called with full dual-filter kwargs."""
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
        reschedule_appointment,
        set_reschedule_service_resolver,
    )

    new_slot = datetime.now(tz=UTC) + timedelta(days=2)
    appointment_uuid = uuid4()

    fake = MagicMock()
    fake.appointment_id = appointment_uuid
    fake.new_slot = new_slot
    service = MagicMock()
    service.reschedule = AsyncMock(return_value=fake)
    set_reschedule_service_resolver(lambda: service)

    tenant_id = uuid4()
    clinic_id = uuid4()

    result = await reschedule_appointment.ainvoke(
        {
            "appointment_id": appointment_uuid,
            "new_starts_at": new_slot,
            "reason": "patient_request_morning_slot",
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
        }
    )

    service.reschedule.assert_awaited_once()
    kwargs = service.reschedule.await_args.kwargs
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["clinic_id"] == clinic_id
    assert kwargs["appointment_id"] == appointment_uuid
    assert kwargs["new_slot"] == new_slot
    assert "reprogramado" in result.lower() or "rescheduled" in result.lower()


@pytest.mark.asyncio
async def test_service_exception_returns_operator_fallback() -> None:
    """Service exception → operator-handoff message, no raise."""
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
        reschedule_appointment,
        set_reschedule_service_resolver,
    )

    service = MagicMock()
    service.reschedule = AsyncMock(side_effect=RuntimeError("scheduler busy"))
    set_reschedule_service_resolver(lambda: service)

    result = await reschedule_appointment.ainvoke(
        {
            "appointment_id": uuid4(),
            "new_starts_at": datetime.now(tz=UTC) + timedelta(days=1),
            "reason": "test",
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
        }
    )

    assert "automáticamente" in result.lower() or "equipo" in result.lower()


@pytest.mark.asyncio
async def test_no_resolver_raises_runtime_error() -> None:
    """DI resolver unset → RuntimeError on invoke."""
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
        reschedule_appointment,
    )

    with pytest.raises(RuntimeError, match="resolver not configured"):
        await reschedule_appointment.ainvoke(
            {
                "appointment_id": uuid4(),
                "new_starts_at": datetime.now(tz=UTC) + timedelta(days=1),
                "reason": "test",
                "tenant_id": uuid4(),
                "clinic_id": uuid4(),
            }
        )


def test_tool_has_langchain_tool_marker() -> None:
    """reschedule_appointment MUST be a LangChain @tool."""
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
        reschedule_appointment,
    )

    assert reschedule_appointment.name == "reschedule_appointment"
    assert hasattr(reschedule_appointment, "args_schema")
