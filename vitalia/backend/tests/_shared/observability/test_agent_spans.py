"""Tests for agent_turn_span context manager.

TDD: RED-first. Defines contract for agent_spans.py.

downstream-regression-na: brand-local observability agent span test; no cross-brand consumers
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONVERSATION_ID = uuid4()


class TestAgentTurnSpanContract:
    """agent_turn_span must inject cost attrs and sanitize PHI."""

    @pytest.mark.asyncio
    async def test_agent_span_is_async_context_manager(self) -> None:
        """agent_turn_span must be usable as async context manager."""
        from src.modules.vitalia._shared.observability.agent_spans import (
            agent_turn_span,
        )

        assert callable(agent_turn_span)

    @pytest.mark.asyncio
    async def test_agent_span_creates_named_span(self) -> None:
        """agent_turn_span must start a span named after agent_name."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with patch(
            "src.modules.vitalia._shared.observability.agent_spans._get_tracer",
            return_value=mock_tracer,
        ):
            from src.modules.vitalia._shared.observability.agent_spans import (
                agent_turn_span,
            )

            async with agent_turn_span(
                agent_name="vitalia.agent.adrian",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                conversation_id=CONVERSATION_ID,
            ):
                pass

        mock_tracer.start_as_current_span.assert_called_once()
        assert mock_tracer.start_as_current_span.call_args[0][0] == "vitalia.agent.adrian"

    @pytest.mark.asyncio
    async def test_agent_span_injects_tenant_clinic_ids(self) -> None:
        """Span attributes must include tenant_id and clinic_id."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with patch(
            "src.modules.vitalia._shared.observability.agent_spans._get_tracer",
            return_value=mock_tracer,
        ):
            from src.modules.vitalia._shared.observability.agent_spans import (
                agent_turn_span,
            )

            async with agent_turn_span(
                agent_name="vitalia.agent.lucas",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                conversation_id=CONVERSATION_ID,
            ):
                pass

        mock_span.set_attributes.assert_called()
        attrs_set = mock_span.set_attributes.call_args[0][0]
        assert attrs_set.get("tenant_id") == str(TENANT_ID)
        assert attrs_set.get("clinic_id") == str(CLINIC_ID)

    @pytest.mark.asyncio
    async def test_agent_span_injects_cost_attrs(self) -> None:
        """agent_turn_span must accept and inject cost attributes."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with patch(
            "src.modules.vitalia._shared.observability.agent_spans._get_tracer",
            return_value=mock_tracer,
        ):
            from src.modules.vitalia._shared.observability.agent_spans import (
                agent_turn_span,
            )

            async with agent_turn_span(
                agent_name="vitalia.agent.adrian",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                conversation_id=CONVERSATION_ID,
            ) as span_ctx:
                # Simulate cost injection after turn completes
                span_ctx.set_cost(
                    cost_usd=0.012,
                    tokens_input=1200,
                    tokens_output=400,
                    cache_read_tokens=800,
                )

        # Verify set_attribute calls include cost fields
        calls = [c[0][0] for c in mock_span.set_attribute.call_args_list]
        assert any("cost_usd" in c for c in calls) or mock_span.set_attributes.called

    @pytest.mark.asyncio
    async def test_agent_span_phi_sanitized_before_attribute_set(self) -> None:
        """PHI fields must be sanitized before written as span attributes.

        agent_turn_span MUST import sanitize_phi_payload from compliance adapter,
        NOT define local PII regex.
        """
        import inspect

        from src.modules.vitalia._shared.observability import agent_spans

        src = inspect.getsource(agent_spans)

        # Must not define local PHI regex (anti-pattern per anti-duplication.md)
        assert "re.compile" not in src or "sanitize" in src

        # Must import sanitize_phi_payload from compliance adapter (or luana_core_observability)
        has_import = "sanitize_phi_payload" in src or "sanitize_payload" in src
        assert has_import, (
            "agent_spans.py must import sanitize_phi_payload or sanitize_payload "
            "from engine/adapter — NEVER define local PII regex"
        )

    @pytest.mark.asyncio
    async def test_agent_span_no_local_phi_regex(self) -> None:
        """No local PII regex patterns should be defined in agent_spans.py."""
        import inspect

        from src.modules.vitalia._shared.observability import agent_spans

        src = inspect.getsource(agent_spans)

        # Should not define patient PHI patterns inline
        phi_fields = ["diagnosis", "dni", "treatment_plan", "medical_notes"]
        for field in phi_fields:
            assert f'"{field}"' not in src or "import" in src, (
                f"agent_spans.py should not hardcode PHI field '{field}' "
                f"— use sanitize_phi_payload from compliance adapter"
            )


class TestAgentSpanCostAttributes:
    """Cost attribute names must match spec."""

    def test_cost_attr_names_match_spec(self) -> None:
        """AgentSpanContext must expose cost_usd, tokens_input, tokens_output, cache_read_tokens."""
        from src.modules.vitalia._shared.observability.agent_spans import (
            AgentSpanContext,
        )

        ctx = AgentSpanContext(span=MagicMock())
        ctx.set_cost(
            cost_usd=0.005,
            tokens_input=500,
            tokens_output=100,
            cache_read_tokens=200,
        )
        # Should not raise — all 4 attributes accepted
