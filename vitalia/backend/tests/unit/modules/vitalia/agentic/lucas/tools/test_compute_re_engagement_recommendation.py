"""Unit tests — `compute_re_engagement_recommendation` (Lucas tool, T-10 Slice 1).

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- Pydantic input schema (period Literal "7d"|"30d"|"90d", tenant+clinic UUIDs, top_n)
- Handler delegates to LucasReEngagementService (aggregate → cluster → LLM)
- Tenant boundary: PermissionError on tenant_id mismatch with ctx_tenant_id
- Output schema: list[recommendation] with pattern/priority/action/rationale
- Best-effort trace_event emission (NEVER breaks tool turn — R23)
- Trace event payload sanitized (no PHI), recommendation_text omitted
- Empty recommendations when no clusters (cost guard validated)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

TENANT_ID: UUID = uuid4()
CLINIC_ID: UUID = uuid4()


def _make_locale(currency: str = "MXN", timezone: str = "America/Mexico_City") -> MagicMock:
    locale = MagicMock()
    locale.currency = currency
    locale.timezone = timezone
    return locale


def _make_service_response(
    recs: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Build a fake LucasReEngagementService that returns recommendations via run()."""
    service = MagicMock()
    service.run = AsyncMock(return_value=recs or [])
    return service


# ─── Pydantic input schema validation ────────────────────────────────────


class TestComputeReEngagementRecommendationInput:
    """Validate input Pydantic schema."""

    def test_valid_input_accepted(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
        )

        input = ComputeReEngagementRecommendationInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period="30d",
            top_n=5,
        )
        assert input.period == "30d"
        assert input.top_n == 5

    def test_period_default_30d(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
        )

        input = ComputeReEngagementRecommendationInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
        )
        assert input.period == "30d"
        assert input.top_n == 5

    def test_invalid_period_rejected(self) -> None:
        """period must be 7d|30d|90d Literal."""
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
        )

        for bad_period in ["15d", "1d", "1y", "month", "2026-05"]:
            with pytest.raises(ValidationError):
                ComputeReEngagementRecommendationInput(
                    tenant_id=TENANT_ID,
                    clinic_id=CLINIC_ID,
                    period=bad_period,  # type: ignore[arg-type]
                )

    def test_top_n_must_be_positive(self) -> None:
        """top_n must be >= 1."""
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
        )

        with pytest.raises(ValidationError):
            ComputeReEngagementRecommendationInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                top_n=0,
            )

    def test_extra_field_forbidden(self) -> None:
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
        )

        with pytest.raises(ValidationError):
            ComputeReEngagementRecommendationInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                injected="evil",  # type: ignore[call-arg]
            )


# ─── Handler — happy path + service delegation ───────────────────────────


class TestComputeReEngagementRecommendationHandler:
    """Tool handler behaviour."""

    @pytest.mark.asyncio
    async def test_happy_path_delegates_to_service(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        recs = [
            {
                "pattern": "multi_session",
                "priority": "high",
                "action": "Reactiva con plantilla recordatorio_proxima_sesion",
                "expected_impact_pct": 25,
                "rationale": "3 abandonos comparten patron multi_session",
            }
        ]
        service = _make_service_response(recs)

        result = await compute_re_engagement_recommendation(
            ComputeReEngagementRecommendationInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="30d",
                top_n=5,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        # Service called with correct kwargs
        service.run.assert_awaited_once()
        kwargs = service.run.await_args.kwargs
        assert kwargs["tenant_id"] == TENANT_ID
        assert kwargs["clinic_id"] == CLINIC_ID
        assert kwargs["period_days"] == 30
        assert kwargs["top_n"] == 5

        # Output shape per caller spec
        assert "recommendations" in result
        assert len(result["recommendations"]) == 1
        rec = result["recommendations"][0]
        assert rec["pattern"] == "multi_session"
        assert rec["priority"] == "high"
        assert "action" in rec
        assert "rationale" in rec

    @pytest.mark.asyncio
    async def test_period_7d_maps_to_7_days(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        service = _make_service_response()
        await compute_re_engagement_recommendation(
            ComputeReEngagementRecommendationInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="7d",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )
        assert service.run.await_args.kwargs["period_days"] == 7

    @pytest.mark.asyncio
    async def test_period_90d_maps_to_90_days(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        service = _make_service_response()
        await compute_re_engagement_recommendation(
            ComputeReEngagementRecommendationInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="90d",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )
        assert service.run.await_args.kwargs["period_days"] == 90

    @pytest.mark.asyncio
    async def test_empty_recommendations_returned_when_no_clusters(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        service = _make_service_response([])

        result = await compute_re_engagement_recommendation(
            ComputeReEngagementRecommendationInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )
        assert result["recommendations"] == []


# ─── Tenant boundary — security ──────────────────────────────────────────


class TestTenantBoundary:
    """Defensive `tenant_id` mismatch guard — HIPAA-lite."""

    @pytest.mark.asyncio
    async def test_cross_tenant_raises_permission_error(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        attacker_tenant = uuid4()
        service = _make_service_response()

        with pytest.raises(PermissionError):
            await compute_re_engagement_recommendation(
                ComputeReEngagementRecommendationInput(
                    tenant_id=attacker_tenant,
                    clinic_id=CLINIC_ID,
                ),
                ctx_tenant_id=TENANT_ID,  # mismatch
                service=service,
                locale=_make_locale(),
            )
        # Service MUST NOT be called when boundary check fails
        service.run.assert_not_awaited()


# ─── Observability — best-effort trace_event ─────────────────────────────


class TestTraceEventEmission:
    """Best-effort trace event per R23 — NEVER breaks tool turn."""

    @pytest.mark.asyncio
    async def test_trace_event_emitted_when_repo_supplied(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        recs = [
            {
                "pattern": "multi_session",
                "priority": "high",
                "action": "x",
                "expected_impact_pct": 25,
                "rationale": "y",
            }
        ]
        service = _make_service_response(recs)
        repo = MagicMock()
        repo.add = MagicMock()
        turn_id = uuid4()
        span_id = uuid4()

        result = await compute_re_engagement_recommendation(
            ComputeReEngagementRecommendationInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="30d",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=repo,
            turn_id=turn_id,
            span_id=span_id,
        )

        assert len(result["recommendations"]) == 1
        repo.add.assert_called_once()
        kwargs = repo.add.call_args.kwargs
        assert kwargs["event_type"] == "tool.compute_re_engagement_recommendation.completed"
        assert kwargs["name"] == "compute_re_engagement_recommendation"
        assert kwargs["tenant_id"] == TENANT_ID
        assert kwargs["turn_id"] == turn_id
        assert kwargs["span_id"] == span_id

        # Audit log per caller spec: log aggregate count, NOT bodies
        data = kwargs["data"]
        assert data["period"] == "30d"
        assert data["clinic_id"] == str(CLINIC_ID)
        assert data["recommendations_count"] == 1
        # PHI defense-in-depth: NEVER log recommendation_text/action/rationale bodies
        assert "action" not in data
        assert "rationale" not in data
        assert "body" not in data
        assert "recommendation_text" not in data

    @pytest.mark.asyncio
    async def test_trace_event_skipped_when_repo_none(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        service = _make_service_response()
        result = await compute_re_engagement_recommendation(
            ComputeReEngagementRecommendationInput(tenant_id=TENANT_ID, clinic_id=CLINIC_ID),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=None,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_trace_event_repo_failure_does_not_break_turn(self) -> None:
        """Repo failure MUST NOT propagate — best-effort per R23."""
        from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
            ComputeReEngagementRecommendationInput,
            compute_re_engagement_recommendation,
        )

        service = _make_service_response()
        repo = MagicMock()
        repo.add = MagicMock(side_effect=RuntimeError("trace store down"))

        # MUST NOT raise
        result = await compute_re_engagement_recommendation(
            ComputeReEngagementRecommendationInput(tenant_id=TENANT_ID, clinic_id=CLINIC_ID),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=repo,
            turn_id=uuid4(),
            span_id=uuid4(),
        )
        assert result is not None
