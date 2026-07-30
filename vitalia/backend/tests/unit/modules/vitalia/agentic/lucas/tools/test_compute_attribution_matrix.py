"""Unit tests — `compute_attribution_matrix` (Lucas growth setter tool, T-ag-tools-3).

TDD per `.claude/rules/tdd-mandatory.md`.

Tests verify:
- Pydantic input validation (UUIDs + period_start/period_end dates)
- Delegate to `LucasAttributionService.compute_attribution(...)` with required args
- Map entity → MatrixDTO with currency fallback to locale.currency
- Tenant boundary check: PermissionError on tenant mismatch
- Best-effort trace_event emission
- Total revenue serialised as string (Decimal → str via field_serializer)
- Pure DB tool — no BudgetGuard, no LLM call expected (verified by absence)
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

TENANT_ID: UUID = uuid4()
CLINIC_ID: UUID = uuid4()
PERIOD_START = dt.date(2026, 5, 1)
PERIOD_END = dt.date(2026, 5, 31)


def _make_locale(currency: str = "PEN") -> MagicMock:
    locale = MagicMock()
    locale.currency = currency
    locale.timezone = "America/Lima"
    return locale


def _make_attribution_entity(
    *,
    channel_breakdown: dict[str, Any] | None = None,
    total: Decimal | None = None,
    currency: str | None = "PEN",
) -> Any:
    from src.modules.vitalia.agentic.lucas.domain.entities.attribution_matrix_snapshot import (
        AttributionMatrixSnapshot,
    )

    return AttributionMatrixSnapshot(
        id=uuid4(),
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        channel_breakdown=channel_breakdown or {"meta_ads": 1500.0, "google_ads": 800.0},
        total_attributed_revenue=total if total is not None else Decimal("2300.00"),
        currency=currency,
        computed_at=dt.datetime.now(tz=dt.timezone.utc),
        deleted_at=None,
    )


# ─── Pydantic input schema validation ────────────────────────────────────


class TestComputeAttributionMatrixInput:
    """Validate input schema."""

    def test_valid_input_accepted(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
        )

        input = ComputeAttributionMatrixInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=PERIOD_START,
            period_end=PERIOD_END,
        )
        assert input.period_start == PERIOD_START
        assert input.period_end == PERIOD_END

    def test_extra_field_forbidden(self) -> None:
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
        )

        with pytest.raises(ValidationError):
            ComputeAttributionMatrixInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                unauthorized_field="evil",  # type: ignore[call-arg]
            )


# ─── Handler — happy path + currency fallback ────────────────────────────


class TestComputeAttributionMatrixHandler:
    """Tool handler behaviour."""

    @pytest.mark.asyncio
    async def test_happy_path_uses_entity_currency(self) -> None:
        """When entity.currency set, DTO uses it (not locale fallback)."""
        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
            compute_attribution_matrix,
        )

        entity = _make_attribution_entity(currency="PEN")
        service = MagicMock()
        service.compute_attribution = AsyncMock(return_value=entity)
        locale = _make_locale(currency="USD")  # locale differs from entity

        dto = await compute_attribution_matrix(
            ComputeAttributionMatrixInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=locale,
        )

        assert dto.currency == "PEN"  # entity currency wins
        assert dto.total_attributed_revenue == Decimal("2300.00")
        assert dto.channel_breakdown == {"meta_ads": 1500.0, "google_ads": 800.0}
        service.compute_attribution.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_locale_currency_when_entity_currency_none(self) -> None:
        """When entity.currency is None, fall back to locale.currency."""
        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
            compute_attribution_matrix,
        )

        entity = _make_attribution_entity(currency=None)
        service = MagicMock()
        service.compute_attribution = AsyncMock(return_value=entity)
        locale = _make_locale(currency="MXN")

        dto = await compute_attribution_matrix(
            ComputeAttributionMatrixInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=locale,
        )

        assert dto.currency == "MXN"

    @pytest.mark.asyncio
    async def test_total_revenue_serialised_as_string(self) -> None:
        """Decimal serialiser converts to string for JSON safety."""
        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
            compute_attribution_matrix,
        )

        entity = _make_attribution_entity(total=Decimal("99999.99"))
        service = MagicMock()
        service.compute_attribution = AsyncMock(return_value=entity)

        dto = await compute_attribution_matrix(
            ComputeAttributionMatrixInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        # internal value preserved as Decimal
        assert dto.total_attributed_revenue == Decimal("99999.99")
        # serialised form is string
        dumped = dto.model_dump()
        assert dumped["total_attributed_revenue"] == "99999.99"


# ─── Tenant boundary ─────────────────────────────────────────────────────


class TestTenantBoundary:
    @pytest.mark.asyncio
    async def test_cross_tenant_raises_permission_error(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
            compute_attribution_matrix,
        )

        service = MagicMock()
        service.compute_attribution = AsyncMock(return_value=_make_attribution_entity())

        with pytest.raises(PermissionError):
            await compute_attribution_matrix(
                ComputeAttributionMatrixInput(
                    tenant_id=uuid4(),  # attacker tenant
                    clinic_id=CLINIC_ID,
                    period_start=PERIOD_START,
                    period_end=PERIOD_END,
                ),
                ctx_tenant_id=TENANT_ID,
                service=service,
                locale=_make_locale(),
            )
        service.compute_attribution.assert_not_awaited()


# ─── Observability — trace event ─────────────────────────────────────────


class TestTraceEventEmission:
    @pytest.mark.asyncio
    async def test_trace_event_emitted(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
            compute_attribution_matrix,
        )

        entity = _make_attribution_entity()
        service = MagicMock()
        service.compute_attribution = AsyncMock(return_value=entity)
        repo = MagicMock()
        repo.add = MagicMock()

        await compute_attribution_matrix(
            ComputeAttributionMatrixInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=repo,
            turn_id=uuid4(),
            span_id=uuid4(),
        )

        repo.add.assert_called_once()
        kwargs = repo.add.call_args.kwargs
        assert kwargs["event_type"] == "tool.compute_attribution_matrix.completed"
        assert kwargs["data"]["channel_count"] == 2
        assert kwargs["data"]["currency"] == "PEN"
        assert kwargs["data"]["total_attributed_revenue"] == "2300.00"

    @pytest.mark.asyncio
    async def test_trace_event_failure_does_not_break_turn(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
            ComputeAttributionMatrixInput,
            compute_attribution_matrix,
        )

        service = MagicMock()
        service.compute_attribution = AsyncMock(return_value=_make_attribution_entity())
        repo = MagicMock()
        repo.add = MagicMock(side_effect=RuntimeError("trace store down"))

        dto = await compute_attribution_matrix(
            ComputeAttributionMatrixInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
            trace_event_repo=repo,
            turn_id=uuid4(),
            span_id=uuid4(),
        )
        # MUST return DTO even though trace failed
        assert dto.currency == "PEN"
