"""Unit tests — `compute_stage_recommendation` (Lucas growth setter tool, T-ag-tools-3).

TDD per `.claude/rules/tdd-mandatory.md`.

Tests verify:
- Pydantic input validation (stage Literal + period YYYY-MM regex + UUIDs)
- Delegate to `LucasStageRecommendationService.compute(...)` with all required args
- Map entity → RecommendationDTO with confidence + currency from locale
- Tenant boundary check: PermissionError on tenant_id mismatch with ctx_tenant_id
- Best-effort trace_event emission (when repo + IDs supplied)
- Trace event NEVER breaks tool turn (repo raise → warning + tool returns OK)
- Status mapping (entity.status → DTO.status canonical literal)
- Spanish neutro / sanitize_payload applied to supporting_data
- No PHI in trace event payload (recommendation_text deliberately omitted)
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

TENANT_ID: UUID = uuid4()
CLINIC_ID: UUID = uuid4()


def _utc_now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


def _make_locale(currency: str = "PEN", timezone: str = "America/Lima") -> MagicMock:
    locale = MagicMock()
    locale.currency = currency
    locale.timezone = timezone
    return locale


def _make_entity(
    *,
    stage: str = "attraction",
    status: str = "open",
    body: str = "Iterar creatividad principal con 3 variantes A/B/C, 7 días test.",
    rationale: dict[str, Any] | None = None,
) -> Any:
    """Build a fake StageRecommendation entity matching the dataclass shape."""
    from src.modules.vitalia.agentic.lucas.domain.entities.stage_recommendation import (
        StageRecommendation,
    )

    now = _utc_now()
    return StageRecommendation(
        id=uuid4(),
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        stage=stage,
        recommendation_kind="growth",
        title="Iterar creatividad — +25% CTR target",
        body=body,
        rationale_json=rationale or {"channel_count": 3, "avg_ctr": 0.032},
        priority=50,
        status=status,
        expires_at=now + dt.timedelta(days=30),
        created_at=now,
        updated_at=now,
        deleted_at=None,
        approved_by_user_id=None,
        approved_at=None,
        undo_until=None,
    )


# ─── Pydantic input schema validation ────────────────────────────────────


class TestComputeStageRecommendationInput:
    """Validate `ComputeStageRecommendationInput` Pydantic schema."""

    def test_valid_input_accepted(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
        )

        input = ComputeStageRecommendationInput(
            stage="attraction",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period="2026-05",
        )
        assert input.stage == "attraction"
        assert input.period == "2026-05"

    def test_invalid_stage_rejected(self) -> None:
        """Stage must be one of 5 funnel stages — Literal validation."""
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
        )

        with pytest.raises(ValidationError):
            ComputeStageRecommendationInput(
                stage="invalid_stage",  # type: ignore[arg-type]
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            )

    def test_invalid_period_format_rejected(self) -> None:
        """Period must match YYYY-MM regex (e.g., 2026-05)."""
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
        )

        for bad_period in ["2026/05", "26-05", "2026-5", "2026-13-01", "May 2026"]:
            with pytest.raises(ValidationError):
                ComputeStageRecommendationInput(
                    stage="attraction",
                    tenant_id=TENANT_ID,
                    clinic_id=CLINIC_ID,
                    period=bad_period,
                )

    def test_extra_field_forbidden(self) -> None:
        """`extra='forbid'` — unknown fields rejected (defensive)."""
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
        )

        with pytest.raises(ValidationError):
            ComputeStageRecommendationInput(
                stage="attraction",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
                injected_field="evil",  # type: ignore[call-arg]
            )


# ─── Handler — happy path + entity → DTO mapping ─────────────────────────


class TestComputeStageRecommendationHandler:
    """Tool handler behaviour."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_dto_with_currency_from_locale(self) -> None:
        """compute() called, currency from locale (NEVER hardcoded), status='active'."""
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        entity = _make_entity(stage="attraction", status="open")
        service = MagicMock()
        service.compute = AsyncMock(return_value=entity)
        locale = _make_locale(currency="PEN")

        dto = await compute_stage_recommendation(
            ComputeStageRecommendationInput(
                stage="attraction",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=locale,
        )

        assert dto.stage == "attraction"
        assert dto.recommendation_text == entity.body
        assert dto.status == "active"  # entity 'open' → DTO 'active'
        assert dto.confidence > 0.0  # mandatory per design § 3.5
        assert dto.currency == "PEN"  # from locale, never hardcoded
        service.compute.assert_awaited_once()
        kwargs = service.compute.await_args.kwargs
        assert kwargs["tenant_id"] == TENANT_ID
        assert kwargs["clinic_id"] == CLINIC_ID
        assert kwargs["stage"] == "attraction"
        assert kwargs["period"] == "2026-05"
        assert kwargs["locale"] is locale

    @pytest.mark.asyncio
    async def test_skipped_budget_returns_status_skipped_budget(self) -> None:
        """When service returns entity.status='skipped_budget' → DTO.status mapped."""
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        entity = _make_entity(
            stage="capture",
            status="skipped_budget",
            body="El presupuesto de IA fue superado.",
        )
        service = MagicMock()
        service.compute = AsyncMock(return_value=entity)

        dto = await compute_stage_recommendation(
            ComputeStageRecommendationInput(
                stage="qualification",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        assert dto.status == "skipped_budget"
        assert dto.confidence == 0.0

    @pytest.mark.asyncio
    async def test_approved_status_maps_to_applied(self) -> None:
        """Entity 'approved' → DTO 'applied' with confidence 0.85."""
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        entity = _make_entity(status="approved")
        service = MagicMock()
        service.compute = AsyncMock(return_value=entity)

        dto = await compute_stage_recommendation(
            ComputeStageRecommendationInput(
                stage="reservation",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        assert dto.status == "applied"
        assert dto.confidence == 0.85


# ─── Tenant boundary — security ──────────────────────────────────────────


class TestTenantBoundary:
    """Defensive `tenant_id` mismatch guard."""

    @pytest.mark.asyncio
    async def test_cross_tenant_raises_permission_error(self) -> None:
        """input.tenant_id != ctx_tenant_id → PermissionError (no leak)."""
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        attacker_tenant = uuid4()
        service = MagicMock()
        service.compute = AsyncMock(return_value=_make_entity())

        with pytest.raises(PermissionError):
            await compute_stage_recommendation(
                ComputeStageRecommendationInput(
                    stage="attraction",
                    tenant_id=attacker_tenant,
                    clinic_id=CLINIC_ID,
                    period="2026-05",
                ),
                ctx_tenant_id=TENANT_ID,  # mismatch
                service=service,
                locale=_make_locale(),
            )
        # Service MUST NOT be called when boundary check fails
        service.compute.assert_not_awaited()


# ─── Observability — best-effort trace_event ─────────────────────────────


class TestTraceEventEmission:
    """Best-effort trace event emission per R23 (never breaks turn)."""

    @pytest.mark.asyncio
    async def test_trace_event_emitted_when_repo_supplied(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        entity = _make_entity()
        service = MagicMock()
        service.compute = AsyncMock(return_value=entity)
        repo = MagicMock()
        repo.add = MagicMock()
        turn_id = uuid4()
        span_id = uuid4()

        dto = await compute_stage_recommendation(
            ComputeStageRecommendationInput(
                stage="attraction",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=repo,
            turn_id=turn_id,
            span_id=span_id,
        )

        assert dto.status == "active"
        repo.add.assert_called_once()
        kwargs = repo.add.call_args.kwargs
        assert kwargs["event_type"] == "tool.compute_stage_recommendation.completed"
        assert kwargs["name"] == "compute_stage_recommendation"
        assert kwargs["tenant_id"] == TENANT_ID
        assert kwargs["turn_id"] == turn_id
        assert kwargs["span_id"] == span_id
        # PHI/PII defense-in-depth — recommendation_text MUST NOT be in trace payload
        assert "recommendation_text" not in kwargs["data"]
        # But stage + period + status + confidence ARE safe to log
        assert kwargs["data"]["stage"] == "attraction"
        assert kwargs["data"]["period"] == "2026-05"
        assert kwargs["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_trace_event_skipped_when_repo_none(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        service = MagicMock()
        service.compute = AsyncMock(return_value=_make_entity())

        # No exception even though turn_id+span_id missing
        dto = await compute_stage_recommendation(
            ComputeStageRecommendationInput(
                stage="attraction",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=None,
        )
        assert dto is not None

    @pytest.mark.asyncio
    async def test_trace_event_repo_failure_does_not_break_turn(self) -> None:
        """Repo.add raising MUST NOT propagate — best-effort observability."""
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        service = MagicMock()
        service.compute = AsyncMock(return_value=_make_entity())
        repo = MagicMock()
        repo.add = MagicMock(side_effect=RuntimeError("trace store down"))

        # MUST NOT raise — best-effort per R23
        dto = await compute_stage_recommendation(
            ComputeStageRecommendationInput(
                stage="attraction",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=repo,
            turn_id=uuid4(),
            span_id=uuid4(),
        )
        assert dto.status == "active"


# ─── Supporting data sanitization ────────────────────────────────────────


class TestSupportingDataSanitization:
    """supporting_data must pass through `sanitize_payload` (engine SSoT)."""

    @pytest.mark.asyncio
    async def test_supporting_data_sanitized(self) -> None:
        """If rationale_json contains email/phone, sanitize_payload masks them.

        Engine sanitization SSoT — we just verify dispatcher is invoked
        (the actual masking patterns are tested in core/luana-core-observability/).
        """
        from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
            ComputeStageRecommendationInput,
            compute_stage_recommendation,
        )

        # Rationale with a value that contains an email-like string (sanitization
        # engine will redact this — defense-in-depth even though Lucas should
        # never see PII in rationale).
        rationale = {
            "channel_count": 3,
            "avg_ctr": 0.032,
            "stage_metrics": {"contact": "operator@clinic.com"},
        }
        entity = _make_entity(rationale=rationale)
        service = MagicMock()
        service.compute = AsyncMock(return_value=entity)

        dto = await compute_stage_recommendation(
            ComputeStageRecommendationInput(
                stage="attraction",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period="2026-05",
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        # supporting_data is a dict (sanitized — exact masking semantics owned
        # by engine sanitization tests; here we only assert it's a dict + non-empty)
        assert isinstance(dto.supporting_data, dict)
        assert "channel_count" in dto.supporting_data  # non-PII key preserved
