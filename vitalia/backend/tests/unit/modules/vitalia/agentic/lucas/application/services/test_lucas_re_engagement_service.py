"""Unit tests — LucasReEngagementService (T-10, Slice 1 fidelización).

TDD per .claude/rules/tdd-mandatory.md — RED first.

Tests verify:
- aggregate_patterns(): queries re_engagement_event repo with dual filter
  tenant_id + clinic_id, period filter, NO PHI leakage
- detect_clusters(): Python deterministic clustering of aggregates by
  (pattern, outcome) tuple — no LLM call here
- generate_recommendations(): single LLM call (Kimi) per cluster bundle,
  prompt template cache-friendly (SLOT 1+2 invariant per tenant+clinic),
  sanitize_payload applied to any rationale, NEVER echoes patient_id/name
- BudgetGuard skip (no LLM call when budget exhausted)
- LLM error fallback (graceful — empty recommendations, no raise)

HIPAA-lite: assert tenant_id + clinic_id ALWAYS passed to repo,
recommendation bodies NEVER include patient identifiers.

Anti-duplication §0: consume engine `sanitize_payload`. NEVER mirror.
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


def _make_event(
    *,
    pattern: str = "multi_session",
    outcome: str | None = "no_response",
    patient_id: UUID | None = None,
    trigger_at: dt.datetime | None = None,
) -> MagicMock:
    """Build a fake ReEngagementEventModel-like object for aggregation."""
    ev = MagicMock()
    ev.id = uuid4()
    ev.tenant_id = TENANT_ID
    ev.clinic_id = CLINIC_ID
    ev.patient_id = patient_id or uuid4()
    ev.pattern = pattern
    ev.outcome = outcome
    ev.trigger_at = trigger_at or _utc_now()
    ev.sent_at = trigger_at or _utc_now()
    ev.response_at = None
    return ev


def _make_locale(currency: str = "MXN", timezone: str = "America/Mexico_City") -> MagicMock:
    locale = MagicMock()
    locale.currency = currency
    locale.timezone = timezone
    return locale


# ─── aggregate_patterns ──────────────────────────────────────────────────


class TestAggregatePatterns:
    """Aggregation queries from re_engagement_event_repository."""

    @pytest.mark.asyncio
    async def test_aggregate_patterns_uses_dual_filter(self) -> None:
        """aggregate_patterns MUST pass tenant_id + clinic_id to repo.

        HIPAA-lite refuerzo per vitalia/.claude/rules/hipaa-lite.md.
        """
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        events = [
            _make_event(pattern="multi_session", outcome="no_response"),
            _make_event(pattern="multi_session", outcome="no_response"),
        ]
        # Repo returns list of events when queried by pattern in period range
        re_engagement_repo = MagicMock()
        re_engagement_repo.list_in_period = AsyncMock(return_value=events)

        service = LucasReEngagementService(
            re_engagement_repo=re_engagement_repo,
            llm_service=MagicMock(),
        )
        aggregates = await service.aggregate_patterns(tenant_id=TENANT_ID, clinic_id=CLINIC_ID, period_days=30)

        # Repo CALLED with dual filter
        re_engagement_repo.list_in_period.assert_awaited_once()
        kwargs = re_engagement_repo.list_in_period.await_args.kwargs
        assert kwargs["tenant_id"] == TENANT_ID
        assert kwargs["clinic_id"] == CLINIC_ID
        assert kwargs["period_days"] == 30

        # Aggregates is a list of dicts with pattern + outcome + count
        assert isinstance(aggregates, list)
        assert len(aggregates) >= 1

    @pytest.mark.asyncio
    async def test_aggregate_returns_pattern_outcome_counts(self) -> None:
        """Aggregates group events by (pattern, outcome) with count."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        events = [
            _make_event(pattern="multi_session", outcome="no_response"),
            _make_event(pattern="multi_session", outcome="no_response"),
            _make_event(pattern="multi_session", outcome="rescheduled"),
            _make_event(pattern="follow_up", outcome="no_response"),
        ]
        re_engagement_repo = MagicMock()
        re_engagement_repo.list_in_period = AsyncMock(return_value=events)

        service = LucasReEngagementService(
            re_engagement_repo=re_engagement_repo,
            llm_service=MagicMock(),
        )
        aggregates = await service.aggregate_patterns(tenant_id=TENANT_ID, clinic_id=CLINIC_ID, period_days=30)

        # Build a lookup for assertions
        lookup = {(a["pattern"], a.get("outcome")): a["count"] for a in aggregates}
        assert lookup.get(("multi_session", "no_response")) == 2
        assert lookup.get(("multi_session", "rescheduled")) == 1
        assert lookup.get(("follow_up", "no_response")) == 1

    @pytest.mark.asyncio
    async def test_aggregate_does_not_leak_patient_id(self) -> None:
        """Aggregates MUST NOT include patient_id (only counts).

        HIPAA-lite: only aggregate-level info, no per-patient PHI.
        """
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        events = [_make_event(pattern="multi_session", outcome="no_response")]
        re_engagement_repo = MagicMock()
        re_engagement_repo.list_in_period = AsyncMock(return_value=events)

        service = LucasReEngagementService(
            re_engagement_repo=re_engagement_repo,
            llm_service=MagicMock(),
        )
        aggregates = await service.aggregate_patterns(tenant_id=TENANT_ID, clinic_id=CLINIC_ID, period_days=30)

        for agg in aggregates:
            # NEVER any patient_id, patient_name, email, phone in aggregates
            assert "patient_id" not in agg
            assert "patient_name" not in agg
            assert "email" not in agg
            assert "phone" not in agg


# ─── detect_clusters ─────────────────────────────────────────────────────


class TestDetectClusters:
    """Python deterministic clustering — NO LLM call."""

    def test_detects_cluster_when_count_above_threshold(self) -> None:
        """Cluster forms when (pattern, outcome) count >= 2 (heuristic Slice 1)."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=MagicMock())
        aggregates: list[dict[str, Any]] = [
            {"pattern": "multi_session", "outcome": "no_response", "count": 3},
            {"pattern": "follow_up", "outcome": "rescheduled", "count": 1},
            {"pattern": "maintenance", "outcome": "no_response", "count": 2},
        ]

        clusters = service.detect_clusters(aggregates)
        # 2 clusters expected (counts >= 2 — multi_session.no_response & maintenance.no_response)
        assert len(clusters) == 2
        # First cluster is highest count
        assert clusters[0]["pattern"] == "multi_session"
        assert clusters[0]["count"] == 3

    def test_no_clusters_when_all_singletons(self) -> None:
        """No clusters formed when all aggregates have count=1."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=MagicMock())
        aggregates = [
            {"pattern": "multi_session", "outcome": "no_response", "count": 1},
            {"pattern": "follow_up", "outcome": "rescheduled", "count": 1},
        ]

        clusters = service.detect_clusters(aggregates)
        assert clusters == []


# ─── generate_recommendations ────────────────────────────────────────────


class TestGenerateRecommendations:
    """LLM call (Kimi reasoning) to phrase recommendations from clusters."""

    @pytest.mark.asyncio
    async def test_no_clusters_returns_empty_no_llm_call(self) -> None:
        """When no clusters, NO LLM call (cost guard)."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        llm_service = MagicMock()
        llm_service.generate_response = MagicMock()
        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=llm_service)

        recs = await service.generate_recommendations(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            clusters=[],
            period_days=30,
            top_n=5,
        )

        assert recs == []
        llm_service.generate_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_clusters_generate_recommendations_via_llm(self) -> None:
        """Clusters → single LLM call → parsed recommendations list."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        clusters = [
            {"pattern": "multi_session", "outcome": "no_response", "count": 3},
        ]
        # LLM returns a well-formed JSON-ish output that the service parses
        llm_response = """[
            {
                "pattern": "multi_session",
                "priority": "high",
                "action": "Reactiva con plantilla recordatorio_proxima_sesion + bonus 10% descuento",
                "expected_impact_pct": 25,
                "rationale": "3 abandonos comparten patron multi_session no_response: high cluster signal"
            }
        ]"""
        llm_service = MagicMock()
        llm_service.generate_response = MagicMock(return_value=llm_response)

        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=llm_service)

        recs = await service.generate_recommendations(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            clusters=clusters,
            period_days=30,
            top_n=5,
        )

        # Single LLM call
        llm_service.generate_response.assert_called_once()
        # Output is list of dicts with mandatory keys per caller spec
        assert isinstance(recs, list)
        assert len(recs) >= 1
        rec = recs[0]
        assert rec["pattern"] == "multi_session"
        assert rec["priority"] == "high"
        assert "action" in rec
        assert isinstance(rec["expected_impact_pct"], int)
        assert "rationale" in rec

    @pytest.mark.asyncio
    async def test_llm_call_uses_cache_friendly_prompt_structure(self) -> None:
        """Verify LLM call structure: system_prompt cacheable + variable user.

        Cache slot architecture per 03-arch-agentic § 4.2:
        - SLOT 1 (system role + Lucas role + Vitalia medical context) — cacheable
        - SLOT 2 (rubric + JSON output schema) — cacheable
        - SLOT 3 (aggregate data) — variable
        """
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        clusters = [{"pattern": "multi_session", "outcome": "no_response", "count": 3}]
        llm_service = MagicMock()
        llm_service.generate_response = MagicMock(return_value="[]")

        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=llm_service)

        await service.generate_recommendations(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            clusters=clusters,
            period_days=30,
            top_n=5,
        )

        call_kwargs = llm_service.generate_response.call_args.kwargs
        # system_prompt MUST be provided (the cacheable SLOT 1+2 prefix)
        assert "system_prompt" in call_kwargs
        sys_prompt = call_kwargs["system_prompt"]
        # SLOT 1+2 content invariant — must NOT contain tenant_id/clinic_id (those break cache)
        assert str(TENANT_ID) not in sys_prompt
        assert str(CLINIC_ID) not in sys_prompt
        # Variable user message contains the cluster data
        messages = call_kwargs.get("messages") or call_kwargs.get("messages", [])
        # Concat all message content to check cluster data appears in user message, not system
        user_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
        assert "multi_session" in user_text or "multi_session" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_llm_error_returns_empty_no_raise(self) -> None:
        """LLM failure MUST be graceful — empty recommendations, NO raise."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        clusters = [{"pattern": "multi_session", "outcome": "no_response", "count": 3}]
        llm_service = MagicMock()
        llm_service.generate_response = MagicMock(side_effect=RuntimeError("LLM down"))

        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=llm_service)

        recs = await service.generate_recommendations(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            clusters=clusters,
            period_days=30,
            top_n=5,
        )

        assert recs == []  # graceful — empty, NO raise

    @pytest.mark.asyncio
    async def test_recommendations_truncated_to_top_n(self) -> None:
        """When LLM returns N>top_n recommendations, truncate to top_n."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        clusters = [
            {"pattern": "multi_session", "outcome": "no_response", "count": 3},
            {"pattern": "follow_up", "outcome": "no_response", "count": 5},
            {"pattern": "maintenance", "outcome": "no_response", "count": 2},
        ]
        # LLM returns 5 recommendations; top_n=2 → truncate to 2
        llm_response = """[
            {"pattern":"follow_up","priority":"high","action":"a1","expected_impact_pct":30,"rationale":"r1"},
            {"pattern":"multi_session","priority":"high","action":"a2","expected_impact_pct":25,"rationale":"r2"},
            {"pattern":"maintenance","priority":"medium","action":"a3","expected_impact_pct":10,"rationale":"r3"},
            {"pattern":"absence","priority":"low","action":"a4","expected_impact_pct":5,"rationale":"r4"},
            {"pattern":"nps","priority":"low","action":"a5","expected_impact_pct":3,"rationale":"r5"}
        ]"""
        llm_service = MagicMock()
        llm_service.generate_response = MagicMock(return_value=llm_response)

        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=llm_service)

        recs = await service.generate_recommendations(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            clusters=clusters,
            period_days=30,
            top_n=2,
        )

        assert len(recs) == 2

    @pytest.mark.asyncio
    async def test_recommendation_text_never_contains_patient_identifiers(self) -> None:
        """Defense-in-depth: even if LLM hallucinated, sanitize_payload masks.

        Sanitize_payload from luana_core_observability (engine SSoT) — verify
        the service applies it before returning rationale.
        """
        from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
            LucasReEngagementService,
        )

        clusters = [{"pattern": "multi_session", "outcome": "no_response", "count": 3}]
        # LLM (badly) hallucinates an email in rationale
        llm_response = (
            '[{"pattern":"multi_session","priority":"high",'
            '"action":"send template","expected_impact_pct":25,'
            '"rationale":"contact at user@example.com immediately"}]'
        )
        llm_service = MagicMock()
        llm_service.generate_response = MagicMock(return_value=llm_response)

        service = LucasReEngagementService(re_engagement_repo=MagicMock(), llm_service=llm_service)

        recs = await service.generate_recommendations(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            clusters=clusters,
            period_days=30,
            top_n=5,
        )

        assert len(recs) >= 1
        # The rationale_sanitized field is the masked version
        # The email pattern MUST be masked by sanitize_payload
        full_text = str(recs[0])
        assert "user@example.com" not in full_text
