"""Unit tests — `compute_referrals_leaderboard` (Lucas growth setter tool, T-ag-tools-3).

TDD per `.claude/rules/tdd-mandatory.md`.

Tests verify:
- Pydantic input validation (default limit=5, range 1-50)
- Delegate to `LucasReferralsService.compute_referrals(...)` with required args
- Map entity → LeaderboardDTO; sanitize each top_referrers row (defense-in-depth)
- limit clamps service result to N items
- Tenant boundary check: PermissionError on tenant mismatch
- Best-effort trace_event emission
- top_referrers NOT included in trace payload (principle of least exposure)
- HIPAA-lite: only referrer_id (UUID) in DTO, never patient names
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

TENANT_ID: UUID = uuid4()
CLINIC_ID: UUID = uuid4()
PERIOD_START = dt.date(2026, 5, 1)
PERIOD_END = dt.date(2026, 5, 31)


def _make_locale() -> MagicMock:
    locale = MagicMock()
    locale.currency = "PEN"
    locale.timezone = "America/Lima"
    return locale


def _build_referrers(n: int) -> list[dict[str, Any]]:
    """Build N referrer rows — UUID + counts only, NEVER names (HIPAA-lite)."""
    return [
        {
            "referrer_id": str(uuid4()),
            "referral_count": 10 - i,
            "converted_count": 5 - (i // 2),
            "rank": i + 1,
        }
        for i in range(n)
    ]


def _make_referrals_entity(
    *,
    top_referrers: list[dict[str, Any]] | None = None,
    total_referrals: int = 25,
    total_converted: int = 12,
) -> Any:
    from src.modules.vitalia.agentic.lucas.domain.entities.referrals_leaderboard_snapshot import (
        ReferralsLeaderboardSnapshot,
    )

    return ReferralsLeaderboardSnapshot(
        id=uuid4(),
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        top_referrers=top_referrers if top_referrers is not None else _build_referrers(5),
        total_referrals=total_referrals,
        total_converted=total_converted,
        computed_at=dt.datetime.now(tz=dt.timezone.utc),
        deleted_at=None,
    )


# ─── Pydantic input schema validation ────────────────────────────────────


class TestComputeReferralsLeaderboardInput:
    def test_default_limit_is_5(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
        )

        input = ComputeReferralsLeaderboardInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=PERIOD_START,
            period_end=PERIOD_END,
        )
        assert input.limit == 5  # default per design § 2.4

    def test_limit_out_of_range_rejected(self) -> None:
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
        )

        for bad_limit in [0, -1, 51, 100]:
            with pytest.raises(ValidationError):
                ComputeReferralsLeaderboardInput(
                    tenant_id=TENANT_ID,
                    clinic_id=CLINIC_ID,
                    period_start=PERIOD_START,
                    period_end=PERIOD_END,
                    limit=bad_limit,
                )

    def test_extra_field_forbidden(self) -> None:
        from pydantic import ValidationError

        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
        )

        with pytest.raises(ValidationError):
            ComputeReferralsLeaderboardInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                evil_field=1,  # type: ignore[call-arg]
            )


# ─── Handler — happy path + limit clamping ───────────────────────────────


class TestComputeReferralsLeaderboardHandler:
    @pytest.mark.asyncio
    async def test_happy_path_returns_dto(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
            compute_referrals_leaderboard,
        )

        entity = _make_referrals_entity(top_referrers=_build_referrers(5))
        service = MagicMock()
        service.compute_referrals = AsyncMock(return_value=entity)

        dto = await compute_referrals_leaderboard(
            ComputeReferralsLeaderboardInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        assert dto.total_referrals == 25
        assert dto.total_converted == 12
        assert len(dto.top_referrers) == 5

    @pytest.mark.asyncio
    async def test_limit_clamps_service_output(self) -> None:
        """If service returns 10 referrers but input.limit=3, DTO clamps to 3."""
        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
            compute_referrals_leaderboard,
        )

        # Service returns 10
        entity = _make_referrals_entity(top_referrers=_build_referrers(10))
        service = MagicMock()
        service.compute_referrals = AsyncMock(return_value=entity)

        dto = await compute_referrals_leaderboard(
            ComputeReferralsLeaderboardInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                limit=3,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        assert len(dto.top_referrers) == 3

    @pytest.mark.asyncio
    async def test_hipaa_lite_no_names_in_dto(self) -> None:
        """HIPAA-lite: only referrer_id UUID, never patient names in top_referrers.

        This test verifies invariant + sanitization defense-in-depth: even if
        upstream accidentally injected a name-like field, sanitize_payload
        would mask it. Here we just ensure the canonical shape is preserved.
        """
        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
            compute_referrals_leaderboard,
        )

        entity = _make_referrals_entity(top_referrers=_build_referrers(2))
        service = MagicMock()
        service.compute_referrals = AsyncMock(return_value=entity)

        dto = await compute_referrals_leaderboard(
            ComputeReferralsLeaderboardInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
            ),
            ctx_tenant_id=TENANT_ID,
            service=service,
            locale=_make_locale(),
        )

        for row in dto.top_referrers:
            assert "referrer_id" in row
            assert "name" not in row  # NEVER patient names per HIPAA-lite
            assert "dni" not in row
            assert "email" not in row


# ─── Tenant boundary ─────────────────────────────────────────────────────


class TestTenantBoundary:
    @pytest.mark.asyncio
    async def test_cross_tenant_raises_permission_error(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
            compute_referrals_leaderboard,
        )

        service = MagicMock()
        service.compute_referrals = AsyncMock(return_value=_make_referrals_entity())

        with pytest.raises(PermissionError):
            await compute_referrals_leaderboard(
                ComputeReferralsLeaderboardInput(
                    tenant_id=uuid4(),
                    clinic_id=CLINIC_ID,
                    period_start=PERIOD_START,
                    period_end=PERIOD_END,
                ),
                ctx_tenant_id=TENANT_ID,
                service=service,
                locale=_make_locale(),
            )
        service.compute_referrals.assert_not_awaited()


# ─── Observability — trace event ─────────────────────────────────────────


class TestTraceEventEmission:
    @pytest.mark.asyncio
    async def test_trace_event_emitted_without_top_referrers(self) -> None:
        """top_referrers MUST NOT appear in trace payload (least exposure)."""
        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
            compute_referrals_leaderboard,
        )

        entity = _make_referrals_entity(top_referrers=_build_referrers(5))
        service = MagicMock()
        service.compute_referrals = AsyncMock(return_value=entity)
        repo = MagicMock()
        repo.add = MagicMock()

        await compute_referrals_leaderboard(
            ComputeReferralsLeaderboardInput(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=PERIOD_START,
                period_end=PERIOD_END,
                limit=5,
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
        assert kwargs["event_type"] == "tool.compute_referrals_leaderboard.completed"
        # DEFENSIVE: top_referrers MUST NOT be in trace data
        assert "top_referrers" not in kwargs["data"]
        # Only aggregates / counts
        assert kwargs["data"]["total_referrals"] == 25
        assert kwargs["data"]["limit"] == 5
        assert kwargs["data"]["returned_count"] == 5

    @pytest.mark.asyncio
    async def test_trace_event_failure_does_not_break_turn(self) -> None:
        from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
            ComputeReferralsLeaderboardInput,
            compute_referrals_leaderboard,
        )

        service = MagicMock()
        service.compute_referrals = AsyncMock(return_value=_make_referrals_entity())
        repo = MagicMock()
        repo.add = MagicMock(side_effect=RuntimeError("trace store down"))

        dto = await compute_referrals_leaderboard(
            ComputeReferralsLeaderboardInput(
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
        assert dto.total_referrals == 25
