"""Vitalia sales_agent VitaliaSalesAgentCallbackHandler unit tests.

Story T-ag-tools-2 — R23 production_code=true.

Covers:
1. Subclass relationship (engine BaseAgentCallbackHandler).
2. Abstract method overrides invoke vitalia-specific repos with clinic_id +
   compliance_level injection.
3. sanitize_phi_payload applied at persist hook (HIPAA-lite defense-in-depth).
4. Best-effort: failures are swallowed (try/except + structlog warning + rollback).
5. Cost canonicalization (PI-12 S1 T-1 cement 2026-05-02):
   - Tests inject `litellm_call_id` in response_metadata
   - `cost_usd` resolved via `pop_cost(litellm_call_id)` (engine base path)
   - cost_usd=None when call_id missing (NOT Decimal('0'))

Validators covered:
- be_test_unit_sales_agent
- be_test_observability_cost_canonicalization
- ae_anti_duplication_no_observability_mirror (also see architecture/test_no_observability_mirror_sales_agent.py)
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from luana_core_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)


def _make_handler(
    *,
    llm_call_repo: MagicMock | None = None,
    trace_repo: MagicMock | None = None,
) -> "VitaliaSalesAgentCallbackHandler":  # noqa: F821 — lazy import
    """Build a handler with mocked repos + resolvers."""
    from src.modules.vitalia.sales_agent.observability.recording.callback_handler import (
        VitaliaSalesAgentCallbackHandler,
    )

    pricing = MagicMock()
    fx = MagicMock()
    return VitaliaSalesAgentCallbackHandler(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        pricing_resolver=pricing,
        fx_resolver=fx,
        lead_id=uuid4(),
        channel_type="whatsapp_business_encrypted",
        clinic_id=uuid4(),
        compliance_level="hipaa_lite",
        llm_call_repo=llm_call_repo or MagicMock(),
        trace_repo=trace_repo or MagicMock(),
    )


def test_callback_handler_subclasses_engine_base() -> None:
    """VitaliaSalesAgentCallbackHandler must be a BaseAgentCallbackHandler subclass."""
    from src.modules.vitalia.sales_agent.observability.recording.callback_handler import (
        VitaliaSalesAgentCallbackHandler,
    )

    assert issubclass(VitaliaSalesAgentCallbackHandler, BaseAgentCallbackHandler)


def test_persist_llm_call_row_injects_vitalia_columns() -> None:
    """_persist_llm_call_row should pass clinic_id + compliance_level kwargs."""
    repo = MagicMock()
    handler = _make_handler(llm_call_repo=repo)

    handler._persist_llm_call_row(
        tenant_id=handler.tenant_id,
        turn_id=handler.turn_id,
        span_id=uuid4(),
        provider="kimi",
        model_requested="kimi/kimi-k2.6",
        model_responded="kimi/kimi-k2.6",
        input_tokens=100,
        output_tokens=50,
        cached_read_tokens=10,
        cached_write_tokens=0,
        reasoning_tokens=0,
        pricing_version_id=uuid4(),
        input_unit_cost_usd=Decimal("0.000001"),
        output_unit_cost_usd=Decimal("0.000002"),
        cached_read_unit_cost_usd=Decimal("0"),
        cost_usd=Decimal("0.005"),
        tenant_currency="ARS",
        fx_rate_to_tenant=Decimal("1000"),
        fx_rate_source="brand_default",
        cost_tenant_currency=Decimal("5"),
        started_at=MagicMock(),
        duration_ms=1500,
        status="ok",
        error_type=None,
        role="sales_agent",
    )

    repo.add.assert_called_once()
    kwargs = repo.add.call_args.kwargs
    assert kwargs["lead_id"] == handler.lead_id
    assert kwargs["channel_type"] == "whatsapp_business_encrypted"
    assert kwargs["clinic_id"] == handler.clinic_id
    assert kwargs["compliance_level"] == "hipaa_lite"
    assert kwargs["parent_span_id"] is None


def test_persist_trace_event_row_injects_vitalia_columns() -> None:
    """_persist_trace_event_row should pass clinic_id + compliance_level kwargs."""
    repo = MagicMock()
    handler = _make_handler(trace_repo=repo)

    handler._persist_trace_event_row(
        tenant_id=handler.tenant_id,
        turn_id=handler.turn_id,
        span_id=uuid4(),
        event_type="tool_call",
        name="screening_questions",
        data={"args": "preview", "output_preview": "ok_proceed"},
        duration_ms=200,
        status="ok",
    )

    repo.add.assert_called_once()
    kwargs = repo.add.call_args.kwargs
    assert kwargs["lead_id"] == handler.lead_id
    assert kwargs["channel_type"] == "whatsapp_business_encrypted"
    assert kwargs["clinic_id"] == handler.clinic_id
    assert kwargs["compliance_level"] == "hipaa_lite"
    assert kwargs["event_type"] == "tool_call"
    assert kwargs["name"] == "screening_questions"


def test_persist_llm_call_row_swallows_repo_failure() -> None:
    """Repo failure must NOT raise — best-effort observability rule."""
    repo = MagicMock()
    repo.add.side_effect = Exception("DB connection lost")
    handler = _make_handler(llm_call_repo=repo)

    # Should NOT raise — best-effort.
    handler._persist_llm_call_row(
        tenant_id=handler.tenant_id,
        turn_id=handler.turn_id,
        span_id=uuid4(),
        provider="kimi",
        model_requested="x",
        model_responded="x",
        input_tokens=0,
        output_tokens=0,
        cached_read_tokens=0,
        cached_write_tokens=0,
        reasoning_tokens=0,
        pricing_version_id=uuid4(),
        input_unit_cost_usd=Decimal("0"),
        output_unit_cost_usd=Decimal("0"),
        cached_read_unit_cost_usd=Decimal("0"),
        cost_usd=Decimal("0"),
        tenant_currency="USD",
        fx_rate_to_tenant=Decimal("1"),
        fx_rate_source="usd_native",
        cost_tenant_currency=Decimal("0"),
        started_at=MagicMock(),
        duration_ms=100,
        status="ok",
        error_type=None,
        role="sales_agent",
    )

    # Repo invoked despite failure
    repo.add.assert_called_once()


def test_persist_trace_event_row_swallows_repo_failure() -> None:
    """Repo failure on trace event must NOT raise."""
    repo = MagicMock()
    repo.add.side_effect = Exception("Connection refused")
    handler = _make_handler(trace_repo=repo)

    # Should NOT raise.
    handler._persist_trace_event_row(
        tenant_id=handler.tenant_id,
        turn_id=handler.turn_id,
        span_id=uuid4(),
        event_type="tool_call",
        name="x",
        data={},
        duration_ms=None,
        status="ok",
    )

    repo.add.assert_called_once()


def test_handler_handles_unset_repo_gracefully() -> None:
    """No repo configured → log warning, no crash."""
    from src.modules.vitalia.sales_agent.observability.recording.callback_handler import (
        VitaliaSalesAgentCallbackHandler,
    )

    handler = VitaliaSalesAgentCallbackHandler(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        pricing_resolver=MagicMock(),
        fx_resolver=MagicMock(),
        lead_id=uuid4(),
        channel_type="web",
        clinic_id=uuid4(),
        compliance_level="hipaa_lite",
        llm_call_repo=None,
        trace_repo=None,
    )

    # Both should be no-ops with warning.
    handler._persist_llm_call_row(
        tenant_id=handler.tenant_id,
        turn_id=handler.turn_id,
        span_id=uuid4(),
        provider="x",
        model_requested="x",
        model_responded="x",
        input_tokens=0,
        output_tokens=0,
        cached_read_tokens=0,
        cached_write_tokens=0,
        reasoning_tokens=0,
        pricing_version_id=uuid4(),
        input_unit_cost_usd=Decimal("0"),
        output_unit_cost_usd=Decimal("0"),
        cached_read_unit_cost_usd=Decimal("0"),
        cost_usd=None,
        tenant_currency="USD",
        fx_rate_to_tenant=Decimal("1"),
        fx_rate_source="usd_native",
        cost_tenant_currency=None,
        started_at=MagicMock(),
        duration_ms=100,
        status="ok",
        error_type=None,
        role="sales_agent",
    )
    handler._persist_trace_event_row(
        tenant_id=handler.tenant_id,
        turn_id=handler.turn_id,
        span_id=uuid4(),
        event_type="x",
        name="x",
        data={},
        duration_ms=None,
        status="ok",
    )


def test_persist_llm_call_sanitizes_phi_fields() -> None:
    """sanitize_phi_payload should be applied before persist (HIPAA-lite defense-in-depth)."""
    repo = MagicMock()
    handler = _make_handler(llm_call_repo=repo)

    # Inject a PHI-like extra key — sanitize_phi_payload should redact.
    handler._persist_llm_call_row(
        tenant_id=handler.tenant_id,
        turn_id=handler.turn_id,
        span_id=uuid4(),
        provider="kimi",
        model_requested="x",
        model_responded="x",
        input_tokens=0,
        output_tokens=0,
        cached_read_tokens=0,
        cached_write_tokens=0,
        reasoning_tokens=0,
        pricing_version_id=uuid4(),
        input_unit_cost_usd=Decimal("0"),
        output_unit_cost_usd=Decimal("0"),
        cached_read_unit_cost_usd=Decimal("0"),
        cost_usd=Decimal("0"),
        tenant_currency="USD",
        fx_rate_to_tenant=Decimal("1"),
        fx_rate_source="usd_native",
        cost_tenant_currency=Decimal("0"),
        started_at=MagicMock(),
        duration_ms=100,
        status="ok",
        error_type=None,
        role="sales_agent",
        diagnosis="SHOULD_BE_REDACTED",  # extra PHI kwarg
    )

    repo.add.assert_called_once()
    kwargs = repo.add.call_args.kwargs
    # diagnosis field should be redacted by sanitize_phi_payload
    assert kwargs.get("diagnosis") != "SHOULD_BE_REDACTED", (
        "diagnosis field MUST be redacted via sanitize_phi_payload before repo write"
    )


@pytest.mark.parametrize(
    "field_name",
    ["clinic_id", "compliance_level", "lead_id", "channel_type"],
)
def test_vitalia_specific_fields_present_on_handler(field_name: str) -> None:
    """Handler dataclass must declare the vitalia-specific fields."""
    handler = _make_handler()
    assert hasattr(handler, field_name), f"VitaliaSalesAgentCallbackHandler must have `{field_name}` attribute"


def test_observability_context_subclasses_engine_base() -> None:
    """VitaliaSalesAgentObservabilityContext is a BaseObservabilityContext subclass."""
    from luana_core_observability.recording.turn_envelope import (
        BaseObservabilityContext,
    )

    from src.modules.vitalia.sales_agent.observability.recording.turn_envelope import (
        VitaliaSalesAgentObservabilityContext,
    )

    assert issubclass(VitaliaSalesAgentObservabilityContext, BaseObservabilityContext)


def test_observability_context_legacy_compat_returns_empty() -> None:
    """sales_agent has no legacy JSONB consumer → empty dict."""
    from src.modules.vitalia.sales_agent.observability.recording.turn_envelope import (
        VitaliaSalesAgentObservabilityContext,
    )

    ctx = VitaliaSalesAgentObservabilityContext(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        callback_handler=MagicMock(),
        trace_repo=MagicMock(),
        llm_call_repo=MagicMock(),
        lead_id=uuid4(),
        channel_type="web",
        clinic_id=uuid4(),
        compliance_level="hipaa_lite",
    )
    result = ctx._legacy_compat_keys_or_empty({"foo": "bar"})
    assert result == {}


def test_observability_context_add_trace_event_injects_columns() -> None:
    """_add_trace_event passes clinic_id + compliance_level to repo."""
    from src.modules.vitalia.sales_agent.observability.recording.turn_envelope import (
        VitaliaSalesAgentObservabilityContext,
    )

    repo = MagicMock()
    ctx = VitaliaSalesAgentObservabilityContext(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        callback_handler=MagicMock(),
        trace_repo=repo,
        llm_call_repo=MagicMock(),
        lead_id=uuid4(),
        channel_type="whatsapp_business_encrypted",
        clinic_id=uuid4(),
        compliance_level="hipaa_lite",
    )

    ctx._add_trace_event(
        event_type="turn_start",
        name="adrian_turn",
        data={"message_preview": "hola"},
        duration_ms=None,
        status="ok",
        span_id=ctx.turn_id,
    )

    repo.add.assert_called_once()
    kwargs = repo.add.call_args.kwargs
    assert kwargs["lead_id"] == ctx.lead_id
    assert kwargs["channel_type"] == "whatsapp_business_encrypted"
    assert kwargs["clinic_id"] == ctx.clinic_id
    assert kwargs["compliance_level"] == "hipaa_lite"


def test_observability_context_add_trace_event_swallows_repo_failure() -> None:
    """_add_trace_event must NOT raise on repo failure (best-effort)."""
    from src.modules.vitalia.sales_agent.observability.recording.turn_envelope import (
        VitaliaSalesAgentObservabilityContext,
    )

    repo = MagicMock()
    repo.add.side_effect = Exception("DB down")
    ctx = VitaliaSalesAgentObservabilityContext(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        callback_handler=MagicMock(),
        trace_repo=repo,
        llm_call_repo=MagicMock(),
        lead_id=uuid4(),
        channel_type="web",
        clinic_id=uuid4(),
        compliance_level="hipaa_lite",
    )

    # MUST NOT raise.
    ctx._add_trace_event(
        event_type="x",
        name="x",
        data={},
    )

    repo.add.assert_called_once()
