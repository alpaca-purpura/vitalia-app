"""Vitalia Adrián tool — ``send_payment_link`` unit tests.

Story T-ag-tools-2 — R23 production_code=true.

Covers:
1. Pydantic v2 input schema validation (tenant + clinic dual filter mandatory).
2. deposit_percent bounded 1-100.
3. Service invocation passes all dual-filter params.
4. BlockedChannelError exception → portal-redirect message (graceful).
5. Generic service exception → operator-handoff fallback message.
6. DI resolver hook works.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


@pytest.fixture(autouse=True)
def _reset_resolver():
    from src.modules.vitalia.sales_agent.tools.payment_link import (
        set_payment_link_service_resolver,
    )

    set_payment_link_service_resolver(None)
    yield
    set_payment_link_service_resolver(None)


def test_input_schema_requires_dual_filter() -> None:
    """tenant_id + clinic_id mandatory (HIPAA-lite cardinal)."""
    from src.modules.vitalia.sales_agent.tools.payment_link import (
        SendPaymentLinkInput,
    )

    with pytest.raises(Exception):  # noqa: B017, PT011 — ValidationError
        SendPaymentLinkInput(
            lead_id=uuid4(),
            appointment_id=uuid4(),
            deposit_percent=30,
            channel="whatsapp_business_encrypted",
            # missing tenant_id + clinic_id
        )


def test_input_schema_rejects_out_of_range_deposit() -> None:
    """deposit_percent must be 1-100."""
    from src.modules.vitalia.sales_agent.tools.payment_link import (
        SendPaymentLinkInput,
    )

    with pytest.raises(Exception):  # noqa: B017, PT011
        SendPaymentLinkInput(
            lead_id=uuid4(),
            appointment_id=uuid4(),
            deposit_percent=0,  # too low
            channel="x",
            tenant_id=uuid4(),
            clinic_id=uuid4(),
        )

    with pytest.raises(Exception):  # noqa: B017, PT011
        SendPaymentLinkInput(
            lead_id=uuid4(),
            appointment_id=uuid4(),
            deposit_percent=101,  # too high
            channel="x",
            tenant_id=uuid4(),
            clinic_id=uuid4(),
        )


def test_input_schema_default_deposit_30() -> None:
    """30% is typical deposit but caller MUST provide explicitly (not defaulted)."""
    from src.modules.vitalia.sales_agent.tools.payment_link import (
        SendPaymentLinkInput,
    )

    data = SendPaymentLinkInput(
        lead_id=uuid4(),
        appointment_id=uuid4(),
        deposit_percent=30,
        channel="whatsapp_business_encrypted",
        tenant_id=uuid4(),
        clinic_id=uuid4(),
    )
    assert data.deposit_percent == 30
    assert data.amount == 0.0  # default
    assert data.currency == "ARS"  # default


@pytest.mark.asyncio
async def test_service_invoked_with_dual_filter_and_optional_args() -> None:
    """Service called with full kwargs including dual filter."""
    from src.modules.vitalia.sales_agent.tools.payment_link import (
        send_payment_link,
        set_payment_link_service_resolver,
    )

    class FakeResult:
        channel = "whatsapp_business_encrypted"
        init_point = "https://mp.example/checkout/123"
        preference_id = "MP-123"

    service = MagicMock()
    service.send_payment_link = AsyncMock(return_value=FakeResult())
    set_payment_link_service_resolver(lambda: service)

    appointment_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()

    result = await send_payment_link.ainvoke(
        {
            "lead_id": uuid4(),
            "appointment_id": appointment_id,
            "deposit_percent": 30,
            "channel": "whatsapp_business_encrypted",
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "amount": 50000.0,
            "to_phone": "+541112345678",
            "currency": "ARS",
        }
    )

    service.send_payment_link.assert_awaited_once()
    kwargs = service.send_payment_link.await_args.kwargs
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["clinic_id"] == clinic_id
    assert kwargs["appointment_id"] == appointment_id
    assert kwargs["deposit_percent"] == 30
    assert "checkout" in result.lower() or "MP-123" in result


@pytest.mark.asyncio
async def test_blocked_channel_error_returns_portal_redirect() -> None:
    """BlockedChannelError → human-friendly portal-redirect message."""
    from src.modules.vitalia.compliance.application.compliance_service_adapter import (
        BlockedChannelError,
    )
    from src.modules.vitalia.sales_agent.tools.payment_link import (
        send_payment_link,
        set_payment_link_service_resolver,
    )

    service = MagicMock()
    service.send_payment_link = AsyncMock(side_effect=BlockedChannelError(channel="whatsapp_free"))
    set_payment_link_service_resolver(lambda: service)

    result = await send_payment_link.ainvoke(
        {
            "lead_id": uuid4(),
            "appointment_id": uuid4(),
            "deposit_percent": 30,
            "channel": "whatsapp_free",
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
        }
    )

    assert "bloqueado" in result.lower() or "canal" in result.lower()


@pytest.mark.asyncio
async def test_generic_exception_returns_operator_fallback() -> None:
    """Generic exception → operator-handoff message, no raise."""
    from src.modules.vitalia.sales_agent.tools.payment_link import (
        send_payment_link,
        set_payment_link_service_resolver,
    )

    service = MagicMock()
    service.send_payment_link = AsyncMock(side_effect=RuntimeError("MP API down"))
    set_payment_link_service_resolver(lambda: service)

    result = await send_payment_link.ainvoke(
        {
            "lead_id": uuid4(),
            "appointment_id": uuid4(),
            "deposit_percent": 30,
            "channel": "whatsapp_business_encrypted",
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
        }
    )

    assert "técnico" in result.lower() or "equipo" in result.lower()


@pytest.mark.asyncio
async def test_no_resolver_raises_runtime_error() -> None:
    """DI resolver unset → RuntimeError."""
    from src.modules.vitalia.sales_agent.tools.payment_link import send_payment_link

    with pytest.raises(RuntimeError, match="resolver not configured"):
        await send_payment_link.ainvoke(
            {
                "lead_id": uuid4(),
                "appointment_id": uuid4(),
                "deposit_percent": 30,
                "channel": "whatsapp_business_encrypted",
                "tenant_id": uuid4(),
                "clinic_id": uuid4(),
            }
        )


def test_tool_has_langchain_tool_marker() -> None:
    """send_payment_link MUST be a LangChain @tool."""
    from src.modules.vitalia.sales_agent.tools.payment_link import send_payment_link

    assert send_payment_link.name == "send_payment_link"
    assert hasattr(send_payment_link, "args_schema")
