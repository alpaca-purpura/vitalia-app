"""Unit tests — extract_tenant_context LangChain @tool.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
  - args_schema is Pydantic v2 with required fields (draft_id, tenant_id) + optional (url, text_content)
  - decorator metadata: name="extract_tenant_context"
  - calls injected service.extract(...) with the right kwargs
  - returns a summary string mentioning the source list + draft id
  - error path returns "Error extracting ..." string (best-effort, never raises out)
  - tenant_id flows through to the service (HIPAA-lite isolation cardinal)
  - factory wiring raises RuntimeError when not configured
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.vitalia.copilot.tools.extract_tenant_context import (
    ExtractTenantContextInput,
    extract_tenant_context,
    set_extract_tenant_context_service_factory,
)

# Get the actual module (not the @tool-decorated object shadowing the name in
# tools/__init__.py). sys.modules[...] returns the module object reliably.
ext_mod = sys.modules["src.modules.vitalia.copilot.tools.extract_tenant_context"]

TENANT_ID = uuid4()
DRAFT_ID = uuid4()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_draft_stub(extracted_slot_count: int = 2) -> Any:
    """Return a stub draft with N extracted slots (confidence > 0, source='extracted')."""
    from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

    slots: dict[str, WizardSlot] = {}
    for i in range(extracted_slot_count):
        slot_id = f"tenant.field_{i}"
        slots[slot_id] = WizardSlot(
            slot_id=slot_id,
            value=f"value_{i}",
            confidence=0.85,
            confirmed_at=None,
            source="extracted",
        )

    class _Draft:
        def __init__(self) -> None:
            self.id = DRAFT_ID
            self.slots_required = slots
            self.slots_optional: dict[str, WizardSlot] = {}

    return _Draft()


@pytest.fixture(autouse=True)
def _reset_factory() -> None:
    """Reset module-level factory between tests."""
    ext_mod._service_factory = None
    yield
    ext_mod._service_factory = None


class TestExtractTenantContextInputSchema:
    """Pydantic v2 args_schema."""

    def test_input_schema_required_fields(self) -> None:
        """draft_id + tenant_id are required."""
        with pytest.raises(ValidationError):
            ExtractTenantContextInput(url="https://example.com")  # type: ignore[call-arg]

    def test_input_schema_optional_fields(self) -> None:
        """url + text_content default to None."""
        payload = ExtractTenantContextInput(draft_id=DRAFT_ID, tenant_id=TENANT_ID)
        assert payload.url is None
        assert payload.text_content is None

    def test_input_schema_accepts_url_only(self) -> None:
        payload = ExtractTenantContextInput(draft_id=DRAFT_ID, tenant_id=TENANT_ID, url="https://clinic.example")
        assert payload.url == "https://clinic.example"

    def test_input_schema_strips_whitespace(self) -> None:
        """Per ConfigDict(str_strip_whitespace=True)."""
        payload = ExtractTenantContextInput(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            url="  https://clinic.example  ",
        )
        assert payload.url == "https://clinic.example"


class TestExtractTenantContextToolMetadata:
    """LangChain @tool metadata."""

    def test_tool_name_is_canonical(self) -> None:
        """Tool registered with the exact LangChain name 'extract_tenant_context'."""
        assert extract_tenant_context.name == "extract_tenant_context"

    def test_tool_args_schema_matches_pydantic(self) -> None:
        """@tool decorator wired the Pydantic args_schema."""
        assert extract_tenant_context.args_schema is ExtractTenantContextInput

    def test_tool_is_async(self) -> None:
        """Tool function is async (coroutine)."""
        import asyncio

        assert asyncio.iscoroutinefunction(extract_tenant_context.coroutine)


class TestExtractTenantContextHandlerBehavior:
    """Async handler delegates to the injected service."""

    @pytest.mark.asyncio
    async def test_handler_calls_service_with_kwargs(self) -> None:
        """Tool invokes service.extract(draft_id=, tenant_id=, url=, text_content=)."""
        draft = _make_draft_stub(extracted_slot_count=2)
        mock_service = AsyncMock()
        mock_service.extract = AsyncMock(return_value=draft)
        set_extract_tenant_context_service_factory(lambda: mock_service)

        result = await extract_tenant_context.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "url": "https://clinic.example",
                "text_content": None,
            }
        )

        assert isinstance(result, str)
        mock_service.extract.assert_awaited_once_with(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            url="https://clinic.example",
            text_content=None,
        )

    @pytest.mark.asyncio
    async def test_handler_returns_summary_with_extracted_count(self) -> None:
        draft = _make_draft_stub(extracted_slot_count=3)
        mock_service = AsyncMock()
        mock_service.extract = AsyncMock(return_value=draft)
        set_extract_tenant_context_service_factory(lambda: mock_service)

        result = await extract_tenant_context.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "url": "https://clinic.example",
                "text_content": "additional brief",
            }
        )

        assert "Extracted 3 slot" in result
        assert "url + text" in result
        assert str(DRAFT_ID) in result

    @pytest.mark.asyncio
    async def test_handler_passes_tenant_id_for_isolation(self) -> None:
        """HIPAA-lite cardinal — tenant_id flows to service untouched."""
        draft = _make_draft_stub()
        mock_service = AsyncMock()
        mock_service.extract = AsyncMock(return_value=draft)
        set_extract_tenant_context_service_factory(lambda: mock_service)

        await extract_tenant_context.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "url": "https://clinic.example",
            }
        )

        kwargs = mock_service.extract.await_args.kwargs
        assert kwargs["tenant_id"] == TENANT_ID

    @pytest.mark.asyncio
    async def test_handler_handles_service_exception_best_effort(self) -> None:
        """Service raises → tool returns error string, never raises out."""
        mock_service = AsyncMock()
        mock_service.extract = AsyncMock(side_effect=RuntimeError("scraper timed out"))
        set_extract_tenant_context_service_factory(lambda: mock_service)

        result = await extract_tenant_context.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "url": "https://clinic.example",
            }
        )

        assert "Error" in result
        assert "RuntimeError" in result

    @pytest.mark.asyncio
    async def test_handler_with_no_sources_returns_zero_summary(self) -> None:
        """Both url + text_content None → 'from none'."""
        draft = _make_draft_stub(extracted_slot_count=0)
        mock_service = AsyncMock()
        mock_service.extract = AsyncMock(return_value=draft)
        set_extract_tenant_context_service_factory(lambda: mock_service)

        result = await extract_tenant_context.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
            }
        )

        assert "Extracted 0 slot" in result
        assert "from none" in result


class TestServiceFactoryWiring:
    """Module-level service factory hook."""

    @pytest.mark.asyncio
    async def test_unwired_factory_raises_runtime_error_on_get(self) -> None:
        """get_extract_tenant_context_service() raises if no factory set."""
        from src.modules.vitalia.copilot.tools.extract_tenant_context import (
            get_extract_tenant_context_service,
        )

        with pytest.raises(RuntimeError, match="factory not wired"):
            get_extract_tenant_context_service()
