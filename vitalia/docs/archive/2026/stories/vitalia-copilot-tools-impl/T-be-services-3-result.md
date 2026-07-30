---
ticket: T-be-services-3
story: vitalia-copilot-tools-impl
state: pushed
pushed_at: 2026-05-18
push_commit_sha: 476a7558d87737e6d54e7631d03e22580eeedd9d
builder: claude-sonnet-4-6
---

# T-be-services-3 — Result

## Summary

Lucas growth setter backend services + TZ-aware cron implemented per 03-arch-be.md § 1 + § 8.6+8.7.
Full DDD Inside-Out stack: domain entities → infrastructure repos + adapter → application services → cron + API route.

## Test Results

- **Lucas unit + arch tests:** 86 passed, 0 failed
- **Full vitalia suite:** 1410 passed, 58 skipped (skips = Postgres integration markers, expected without live DB)
- **Architecture fitness:** 226 passed, 0 failed
- **Lint (ruff check):** 0 errors
- **Format (ruff format):** 0 files to reformat

## Files

### New — Lucas module (`vitalia/backend/src/modules/vitalia/agentic/lucas/`) — 30 files, ~1746 LOC

**Domain (pure Python, no framework imports):**
- `domain/entities/stage_recommendation.py` — StageRecommendation entity (funnel stage + AI reasoning + budget status)
- `domain/entities/attribution_matrix_snapshot.py` — AttributionMatrixSnapshot (channel breakdown + Decimal revenue)
- `domain/entities/referrals_leaderboard_snapshot.py` — ReferralsLeaderboardSnapshot (top_referrers list)
- `domain/enums/stage.py` — LucasStage enum (attraction/capture/nurture/opportunity/retention)
- `domain/interfaces/` — repository ABC interfaces (all methods take tenant_id + clinic_id dual filter)

**Infrastructure:**
- `persistence/models/stage_recommendation.py` — SA 2.0 model (Mapped[], DateTime(timezone=True))
- `persistence/models/attribution_matrix_snapshot.py` — SA 2.0 model with JSONB channel_breakdown
- `persistence/models/referrals_leaderboard_snapshot.py` — SA 2.0 model with JSONB top_referrers
- `infrastructure/repositories/stage_recommendation_repository.py` — async, tenant+clinic dual filter
- `infrastructure/repositories/attribution_matrix_snapshot_repository.py` — async, dual filter
- `infrastructure/repositories/referrals_leaderboard_snapshot_repository.py` — async, dual filter
- `infrastructure/adapters/analytics_engine_query_adapter.py` — port to `luana_core_analytics_engine` ChannelRegistry + STAGE_CHANNEL_MAP (NO _GROUP_MAP mirror per analytics-metrics.md)
- `infrastructure/cron/lucas_cron_scheduler.py` — APScheduler CronTrigger(hour=6, timezone=tenant.timezone), TenantLocationContract from luana_core_platform (Fase A engine lift D2)

**Application:**
- `application/services/lucas_stage_recommendation_service.py` — orchestrates Kimi LLM per stage, BudgetGuard pre-check, status='skipped_budget' when exceeded
- `application/services/lucas_attribution_service.py` — pure DB analytics via engine ChannelRegistry (no LLM)
- `application/services/lucas_referrals_service.py` — pure DB analytics, top referrers + conversion
- `application/dtos/recommendation_dto.py` — Pydantic v2 response DTOs (ConfigDict(from_attributes=True))

### New — Lucas cron route + worker

- `vitalia/backend/src/modules/vitalia/copilot/api/routes/lucas_cron_trigger_routes.py` — Bearer LUCAS_CRON_SECRET + X-Tenant-ID, response_model= mandatory, 116 LOC
- `vitalia/backend/src/modules/vitalia/_shared/workers/jobs/lucas_weekly_recommendations.py` — real impl (was scaffold), @idempotent_cron + cron_span OTel, 242 LOC

### New — Tests (12 files, ~899 LOC)

- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/domain/test_lucas_domain_entities.py`
- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/application/services/test_lucas_services.py` (covers all 3 services)
- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/infrastructure/repositories/test_lucas_repositories.py`
- `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/infrastructure/cron/test_lucas_cron_scheduler.py`
- `vitalia/backend/tests/architecture/test_lucas_cron_tz_aware.py` — arch gate D2 (TenantLocationContract from engine, no hardcoded UTC)

### Modified (format + test update)

- `vitalia/backend/tests/workers/test_jobs.py` — updated to remove `lucas_weekly_recommendations` from scaffold NotImplementedError checks (now implemented)
- All other modified infrastructure/models/repos/tests: `ruff format` auto-fixes only (spacing, line length normalization) — zero logic changes
- `vitalia/pyproject.toml` + `uv.lock` — `apscheduler>=3.10` dependency added for APScheduler CronTrigger

## Key architectural decisions enforced

- Tenant + clinic **dual filter** on all repository queries (HIPAA-lite per `.claude/rules/hipaa-lite.md`)
- `TenantLocationContract.timezone` consumed from `luana_core_platform` engine (D2 ratified) — zero hardcoded UTC
- `AnalyticsEngineQueryAdapter` reads `luana_core_analytics_engine.ChannelRegistry.STAGE_CHANNEL_MAP` — NO local _GROUP_MAP mirror (analytics-metrics.md compliant)
- `BudgetGuard.check()` pre-LLM call in `LucasStageRecommendationService` — sets `status='skipped_budget'` if exceeded
- All SA 2.0 models use `Mapped[T]` + `mapped_column()` + `DateTime(timezone=True)` — zero legacy `Column()`
- All response DTOs have `ConfigDict(from_attributes=True)` — zero `Any` types

## Story progress

4/10 tickets pushed: T-be-migrations-1, T-be-services-1, T-be-services-2, T-be-services-3.
Remaining: T-ag-tools-{1,2,3} (Wave 3, Opus 4.7 R23), T-ag-workflows-{1,2} (Wave 4, Opus 4.7 R23), T-ag-evals-1 (Wave 5).
