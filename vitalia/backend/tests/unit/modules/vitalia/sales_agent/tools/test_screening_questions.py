"""Vitalia Adrián tool — ``screening_questions`` unit tests.

Story T-ag-tools-2 — R23 production_code=true.

Covers:
1. Tool signature + Pydantic v2 input schema validation.
2. tenant_id + clinic_id mandatory (HIPAA-lite cardinal).
3. First turn (lead_response=None) returns questions; no LLM call.
4. Subsequent turn invokes service.screen with all dual-filter params.
5. Service exception → graceful degradation (no raise from tool).
6. DI resolver hook can be set + cleared.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest


@pytest.fixture(autouse=True)
def _reset_resolver():
    """Reset the screening service DI resolver between tests."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        set_screening_service_resolver,
    )

    set_screening_service_resolver(None)
    yield
    set_screening_service_resolver(None)


def test_tool_input_schema_requires_dual_filter() -> None:
    """tenant_id + clinic_id MUST be required fields (HIPAA-lite cardinal)."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        ScreeningQuestionsInput,
    )

    with pytest.raises(Exception):  # noqa: B017, PT011 — Pydantic ValidationError
        ScreeningQuestionsInput(
            lead_id=uuid4(),
            vertical="dental",
            # missing tenant_id + clinic_id
        )


def test_tool_input_schema_accepts_required_fields() -> None:
    """Valid input parses correctly."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        ScreeningQuestionsInput,
    )

    data = ScreeningQuestionsInput(
        lead_id=uuid4(),
        vertical="dental",
        tenant_id=uuid4(),
        clinic_id=uuid4(),
    )
    assert data.vertical == "dental"
    assert data.lead_response is None
    assert data.user_id is None


def test_tool_input_schema_rejects_extras() -> None:
    """extra='forbid' must reject unknown fields."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        ScreeningQuestionsInput,
    )

    with pytest.raises(Exception):  # noqa: B017, PT011 — Pydantic ValidationError
        ScreeningQuestionsInput(
            lead_id=uuid4(),
            vertical="dental",
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            unexpected_field="x",
        )


@pytest.mark.asyncio
async def test_first_turn_returns_questions_no_llm_call() -> None:
    """When lead_response=None, return question list + outcome=awaiting_response."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        screening_questions,
        set_screening_service_resolver,
    )

    service = MagicMock()
    service.load_questions_for_vertical.return_value = [
        "¿Has tenido sensibilidad dental previa?",
        "¿Estás embarazada?",
    ]
    service.screen = AsyncMock()  # should NOT be called
    set_screening_service_resolver(lambda: service)

    result = await screening_questions.ainvoke(
        {
            "lead_id": uuid4(),
            "vertical": "dental",
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_response": None,
        }
    )

    assert "awaiting_response" in result
    assert "sensibilidad" in result
    service.screen.assert_not_called()


@pytest.mark.asyncio
async def test_second_turn_invokes_screen_with_dual_filter() -> None:
    """When lead_response present, service.screen invoked with tenant + clinic."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        screening_questions,
        set_screening_service_resolver,
    )

    class FakeResult:
        outcome = "ok_proceed"
        reasoning = "no contraindications"

    service = MagicMock()
    service.screen = AsyncMock(return_value=FakeResult())
    set_screening_service_resolver(lambda: service)

    lead_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()

    result = await screening_questions.ainvoke(
        {
            "lead_id": lead_id,
            "vertical": "dental",
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "lead_response": "No, ninguna sensibilidad. No embarazo.",
        }
    )

    service.screen.assert_awaited_once()
    kwargs = service.screen.await_args.kwargs
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["clinic_id"] == clinic_id
    assert kwargs["lead_id"] == lead_id
    assert "ok_proceed" in result


@pytest.mark.asyncio
async def test_service_exception_graceful_degradation() -> None:
    """Service exception MUST NOT raise from tool — graceful fallback message."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        screening_questions,
        set_screening_service_resolver,
    )

    service = MagicMock()
    service.screen = AsyncMock(side_effect=Exception("LLM timeout"))
    set_screening_service_resolver(lambda: service)

    result = await screening_questions.ainvoke(
        {
            "lead_id": uuid4(),
            "vertical": "dental",
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_response": "alguna respuesta",
        }
    )

    assert "Error técnico" in result or "técnico" in result.lower()


@pytest.mark.asyncio
async def test_no_resolver_set_raises_runtime_error() -> None:
    """If DI resolver not configured, tool raises RuntimeError on use."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        screening_questions,
    )

    with pytest.raises(RuntimeError, match="resolver not configured"):
        await screening_questions.ainvoke(
            {
                "lead_id": uuid4(),
                "vertical": "dental",
                "tenant_id": uuid4(),
                "clinic_id": uuid4(),
                "lead_response": "alguna respuesta",
            }
        )


def test_tool_has_langchain_tool_marker() -> None:
    """screening_questions must be wrapped in LangChain @tool decorator."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        screening_questions,
    )

    assert hasattr(screening_questions, "name")
    assert screening_questions.name == "screening_questions"
    assert hasattr(screening_questions, "args_schema")


@pytest.mark.asyncio
async def test_unknown_vertical_returns_fallback() -> None:
    """Unknown vertical → empty questions → graceful fallback string."""
    from src.modules.vitalia.sales_agent.tools.screening_questions import (
        screening_questions,
        set_screening_service_resolver,
    )

    service = MagicMock()
    service.load_questions_for_vertical.return_value = []
    set_screening_service_resolver(lambda: service)

    result = await screening_questions.ainvoke(
        {
            "lead_id": uuid4(),
            "vertical": "otro",
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_response": None,
        }
    )

    # Either fallback message or graceful continuation hint.
    assert isinstance(result, str)
    assert len(result) > 0


def _typecheck_uuid_kwargs(kwargs: dict[str, object]) -> None:
    """Helper — asserts dual-filter UUIDs present + UUID-typed."""
    assert isinstance(kwargs["tenant_id"], UUID)
    assert isinstance(kwargs["clinic_id"], UUID)
