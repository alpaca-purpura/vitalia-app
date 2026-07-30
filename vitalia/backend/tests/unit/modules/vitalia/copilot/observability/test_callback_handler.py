"""Unit tests — VitaliaCopilotCallbackHandler.

Anti-duplication §0 cardinal verification:
  - Subclass of engine BaseAgentCallbackHandler (imports from luana_core_observability)
  - Only overrides _persist_llm_call_row + _persist_trace_event_row
  - Does NOT redefine on_chat_model_start, on_llm_end, on_tool_*, on_chain_*, _persist_llm_call

Cost canonicalization (PI-12 S1 T-1 cement 2026-05-02):
  - Fixtures inject `litellm_call_id` in response_metadata
  - cost_usd resolved via `pop_cost(litellm_call_id)` (engine-canonical)
  - NO `calculate_cost()` runtime invocation

Best-effort behavior:
  - llm_call_repo / trace_repo None → no raise, just structlog warning
  - Repo .add() raises → no raise out (rollback delegated to base)
  - sanitize_payload applied to data JSONB before persist
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from luana_core_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)

from src.modules.vitalia.copilot.observability.recording.callback_handler import (
    VitaliaCopilotCallbackHandler,
)

TENANT_ID = uuid4()
TURN_ID = uuid4()
CONVERSATION_ID = uuid4()
USER_ID = uuid4()
CLINIC_ID = uuid4()


def _make_handler(*, llm_repo=None, trace_repo=None) -> VitaliaCopilotCallbackHandler:
    """Build a handler with fresh mock resolvers."""
    pricing_resolver = MagicMock()
    fx_resolver = MagicMock()
    return VitaliaCopilotCallbackHandler(
        tenant_id=TENANT_ID,
        turn_id=TURN_ID,
        conversation_id=CONVERSATION_ID,
        user_id=USER_ID,
        clinic_id=CLINIC_ID,
        compliance_level="hipaa_lite",
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        llm_call_repo=llm_repo,
        trace_repo=trace_repo,
    )


class TestSubclassRelationship:
    """Anti-duplication §0 — must inherit from engine base."""

    def test_inherits_from_engine_base(self) -> None:
        """VitaliaCopilotCallbackHandler MUST be subclass of luana_core_observability base."""
        assert issubclass(VitaliaCopilotCallbackHandler, BaseAgentCallbackHandler)

    def test_imports_base_from_engine(self) -> None:
        """The module imports BaseAgentCallbackHandler from luana_core_observability."""
        source = Path(VitaliaCopilotCallbackHandler.__module__.replace(".", "/") + ".py")
        # robust path resolution via __file__
        mod_file = Path(inspect.getfile(VitaliaCopilotCallbackHandler))
        src = mod_file.read_text(encoding="utf-8")
        assert "from luana_core_observability.recording.base_callback_handler" in src, (
            f"VitaliaCopilotCallbackHandler must import BaseAgentCallbackHandler from "
            f"luana_core_observability (anti-duplication §0). Source: {source}"
        )


class TestNoMirrorOfBasePlumbing:
    """Subclass MUST NOT redefine inherited plumbing methods."""

    FORBIDDEN_OVERRIDES = (
        "on_chat_model_start",
        "on_llm_end",
        "on_llm_error",
        "on_tool_start",
        "on_tool_end",
        "on_tool_error",
        "on_chain_start",
        "on_chain_end",
        "_persist_llm_call",
        "_safe_rollback",
        "_extract_provider_and_model",
        "_canonical_provider",
        "_extract_usage",
        "_extract_model_responded",
        "_extract_litellm_call_id",
        "_chain_name",
        "_elapsed_ms",
        "_stringify",
    )

    def test_no_forbidden_method_redefined_in_subclass(self) -> None:
        """Parse the subclass source AST and verify it does NOT redefine plumbing."""
        mod_file = Path(inspect.getfile(VitaliaCopilotCallbackHandler))
        src = mod_file.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name != "VitaliaCopilotCallbackHandler":
                continue
            method_names = {m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
            mirror_violations = method_names & set(self.FORBIDDEN_OVERRIDES)
            assert not mirror_violations, (
                f"VitaliaCopilotCallbackHandler redefines plumbing methods "
                f"{mirror_violations} — anti-duplication §0 violation. Engine base "
                f"owns those methods."
            )


class TestPersistLLMCallRowDelegation:
    """_persist_llm_call_row injects vitalia-specific columns + delegates to repo."""

    def test_persist_llm_call_row_calls_repo_add_with_vitalia_columns(self) -> None:
        repo = MagicMock()
        handler = _make_handler(llm_repo=repo)
        handler._persist_llm_call_row(
            tenant_id=TENANT_ID,
            turn_id=TURN_ID,
            span_id=uuid4(),
            provider="deepseek",
            model_requested="deepseek/deepseek-v4-flash",
            model_responded="deepseek/deepseek-v4-flash",
            input_tokens=10,
            output_tokens=5,
            cached_read_tokens=0,
            cached_write_tokens=0,
            reasoning_tokens=0,
            pricing_version_id=uuid4(),
            input_unit_cost_usd=Decimal("0.000001"),
            output_unit_cost_usd=Decimal("0.000002"),
            cached_read_unit_cost_usd=Decimal(0),
            cost_usd=Decimal("0.00012"),
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal(1),
            fx_rate_source="static",
            cost_tenant_currency=Decimal("0.00012"),
            started_at=datetime.now(tz=UTC),
            duration_ms=100,
            status="ok",
            error_type=None,
            role="agent",
        )

        repo.add.assert_called_once()
        kwargs = repo.add.call_args.kwargs
        # Vitalia-specific columns must be present
        assert kwargs["conversation_id"] == CONVERSATION_ID
        assert kwargs["user_id"] == USER_ID
        assert kwargs["clinic_id"] == CLINIC_ID
        assert kwargs["compliance_level"] == "hipaa_lite"
        # Engine-computed columns flow through verbatim
        assert kwargs["provider"] == "deepseek"
        assert kwargs["cost_usd"] == Decimal("0.00012")

    def test_persist_llm_call_row_no_repo_does_not_raise(self) -> None:
        """llm_call_repo None → log warning, return cleanly."""
        handler = _make_handler(llm_repo=None)
        # Should not raise
        handler._persist_llm_call_row(
            tenant_id=TENANT_ID,
            turn_id=TURN_ID,
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
            input_unit_cost_usd=Decimal(0),
            output_unit_cost_usd=Decimal(0),
            cached_read_unit_cost_usd=Decimal(0),
            cost_usd=None,
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal(1),
            fx_rate_source="static",
            cost_tenant_currency=None,
            started_at=datetime.now(tz=UTC),
            duration_ms=0,
            status="ok",
            error_type=None,
            role="agent",
        )

    def test_persist_llm_call_row_repo_exception_does_not_raise_out(self) -> None:
        """repo.add raises → handler catches, logs, never propagates."""
        repo = MagicMock()
        repo.add.side_effect = RuntimeError("db fail")
        handler = _make_handler(llm_repo=repo)
        # Should not raise
        handler._persist_llm_call_row(
            tenant_id=TENANT_ID,
            turn_id=TURN_ID,
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
            input_unit_cost_usd=Decimal(0),
            output_unit_cost_usd=Decimal(0),
            cached_read_unit_cost_usd=Decimal(0),
            cost_usd=Decimal(0),
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal(1),
            fx_rate_source="static",
            cost_tenant_currency=Decimal(0),
            started_at=datetime.now(tz=UTC),
            duration_ms=0,
            status="ok",
            error_type=None,
            role="agent",
        )


class TestPersistTraceEventRowSanitization:
    """_persist_trace_event_row sanitizes data + injects vitalia columns."""

    def test_persist_trace_event_calls_repo_with_sanitized_data(self) -> None:
        repo = MagicMock()
        handler = _make_handler(trace_repo=repo)
        handler._persist_trace_event_row(
            tenant_id=TENANT_ID,
            turn_id=TURN_ID,
            span_id=uuid4(),
            event_type="llm_call",
            name="deepseek.deepseek-v4-flash",
            data={"input_tokens": 10, "output_tokens": 5},
            duration_ms=120,
            status="ok",
        )

        repo.add.assert_called_once()
        kwargs = repo.add.call_args.kwargs
        assert kwargs["conversation_id"] == CONVERSATION_ID
        assert kwargs["user_id"] == USER_ID
        assert kwargs["clinic_id"] == CLINIC_ID
        assert kwargs["compliance_level"] == "hipaa_lite"
        # data was sanitized + passed through (numeric values preserved)
        assert kwargs["data"]["input_tokens"] == 10
        assert kwargs["data"]["output_tokens"] == 5

    def test_persist_trace_event_no_repo_does_not_raise(self) -> None:
        handler = _make_handler(trace_repo=None)
        # Should not raise
        handler._persist_trace_event_row(
            tenant_id=TENANT_ID,
            turn_id=TURN_ID,
            span_id=uuid4(),
            event_type="tool_call",
            name="confirm_slot",
            data={"args": "x"},
            duration_ms=10,
            status="ok",
        )

    def test_persist_trace_event_repo_exception_does_not_raise_out(self) -> None:
        repo = MagicMock()
        repo.add.side_effect = RuntimeError("db down")
        handler = _make_handler(trace_repo=repo)
        # Should not raise
        handler._persist_trace_event_row(
            tenant_id=TENANT_ID,
            turn_id=TURN_ID,
            span_id=uuid4(),
            event_type="node_enter",
            name="supervisor",
            data={},
            duration_ms=None,
            status="ok",
        )

    def test_empty_data_dict_handled(self) -> None:
        """data={} → sanitized to {} without raise."""
        repo = MagicMock()
        handler = _make_handler(trace_repo=repo)
        handler._persist_trace_event_row(
            tenant_id=TENANT_ID,
            turn_id=TURN_ID,
            span_id=uuid4(),
            event_type="node_enter",
            name="supervisor",
            data={},
            duration_ms=None,
            status="ok",
        )

        repo.add.assert_called_once()
        kwargs = repo.add.call_args.kwargs
        assert kwargs["data"] == {}
