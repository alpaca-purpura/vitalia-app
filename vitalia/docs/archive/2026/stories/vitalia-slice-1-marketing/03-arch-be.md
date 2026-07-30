---
story_id: vitalia-slice-1-marketing
sub_arch: backend
brand: vitalia
compliance_level: hipaa_lite
builder: builder-backend (Sonnet)
auditor: auditor-backend (Opus)
production_code: false
---

# Backend sub-arch — vitalia-slice-1-marketing

> Brand-extension only: `vitalia/backend/src/modules/vitalia/{marketing,connections,analytics}/`. Engine consultation READ-ONLY. Zero engine modifications.

## 1. Module structure (DDD Inside-Out)

```
vitalia/backend/src/modules/vitalia/
├── marketing/                                  ← NEW Slice 1
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── channel_sync_state.py          ← ChannelSyncState
│   │   │   ├── channel_metric.py              ← ChannelMetric
│   │   │   ├── lucas_recommendation.py        ← LucasRecommendation
│   │   │   └── referral.py                    ← Referral
│   │   ├── enums.py                           ← ProviderSlug, SyncStatus, RecommendationStatus, ReferralStatus, BowtieStage
│   │   └── events.py                          ← LucasRecommendationGenerated, LucasRecommendationApproved, ChannelSyncSucceeded, ChannelSyncFailed, ReferralConverted
│   ├── infrastructure/
│   │   ├── models/
│   │   │   ├── channel_sync_state_model.py    ← SQLAlchemy 2.0 mapped_column
│   │   │   ├── channel_metric_model.py
│   │   │   ├── lucas_recommendation_model.py
│   │   │   └── referral_model.py
│   │   ├── repositories/                      ← All subclass CompoundScopeRepositoryBase
│   │   │   ├── channel_sync_state_repository.py
│   │   │   ├── channel_metric_repository.py
│   │   │   ├── lucas_recommendation_repository.py
│   │   │   └── referral_repository.py
│   │   └── adapters/                          ← (no adapters here — provider adapters live in connections/)
│   ├── application/
│   │   ├── services/
│   │   │   ├── marketing_service.py           ← bowtie summary, stage detail, channel detail
│   │   │   ├── attribution_service.py         ← UTM tracking lead→origin matrix (4 origins)
│   │   │   ├── referrals_service.py           ← codes + leaderboard + conv tracking (proxies LucasReferralsService)
│   │   │   └── lucas_recommendations_service.py  ← orchestration (proxies LucasOrchestratorService cron-triggered)
│   │   └── dtos/
│   │       ├── bowtie_summary_dto.py
│   │       ├── stage_detail_dto.py
│   │       ├── channel_detail_dto.py
│   │       ├── lucas_recommendation_dto.py
│   │       ├── attribution_matrix_dto.py
│   │       └── referrals_dto.py
│   ├── api/
│   │   ├── routes.py                          ← FastAPI router /api/v1/vitalia/marketing
│   │   └── deps.py                            ← role decorators, idempotency dep
│   ├── persistence/
│   │   └── migrations/
│   │       ├── 050_slice1_marketing_channel_sync_state.py
│   │       ├── 051_slice1_marketing_channel_metrics.py
│   │       ├── 052_slice1_marketing_lucas_recommendations.py
│   │       ├── 053_slice1_marketing_referrals.py
│   │       └── 054_slice1_marketing_appointments_utm_columns.py
│   └── jobs/                                  ← ARQ cron jobs
│       ├── channel_metrics_sync_meta.py
│       ├── channel_metrics_sync_google.py
│       ├── lucas_daily_analysis_sweep.py
│       └── referrals_value_sync.py
└── connections/                                ← Slice 1 brand-extension adapters
    ├── meta_ads/
    │   └── adapter.py                          ← OAuth wizard 3 pasos + metrics pull
    └── google_ads/
        └── adapter.py                          ← idem
```

## 2. Tables (Slice 1 brand-local · idempotent migrations `IF NOT EXISTS`)

### 2.1 `vitalia_channel_sync_state` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_channel_sync_state (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  provider VARCHAR(32) NOT NULL,                    -- meta_ads | google_ads
  last_sync_at TIMESTAMPTZ NULL,
  last_success_at TIMESTAMPTZ NULL,
  last_error TEXT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'idle',       -- idle | running | error | disconnected
  oauth_token_encrypted BYTEA NULL,                 -- pgcrypto symmetric, KEK rotated annually
  account_id VARCHAR(128) NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_sync_state_tenant_provider
  ON vitalia_channel_sync_state (tenant_id, clinic_id, provider)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_channel_sync_state_status
  ON vitalia_channel_sync_state (tenant_id, clinic_id, status);
```

### 2.2 `vitalia_channel_metrics` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_channel_metrics (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  provider VARCHAR(32) NOT NULL,
  channel_slug VARCHAR(64) NOT NULL,
  campaign_id VARCHAR(128) NULL,
  campaign_name VARCHAR(256) NULL,
  metric_date DATE NOT NULL,
  impressions BIGINT NULL,
  clicks BIGINT NULL,
  conversions BIGINT NULL,
  spend_cents BIGINT NULL,
  currency CHAR(3) NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_metrics_unique
  ON vitalia_channel_metrics (tenant_id, clinic_id, provider, channel_slug, campaign_id, metric_date);
CREATE INDEX IF NOT EXISTS ix_vitalia_channel_metrics_date
  ON vitalia_channel_metrics (tenant_id, clinic_id, metric_date DESC);
```

### 2.3 `vitalia_lucas_recommendations` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_lucas_recommendations (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  stage VARCHAR(32) NOT NULL,                       -- attraction | qualification | reservation | adoption | expansion
  recommendation_kind VARCHAR(64) NOT NULL,         -- e.g., meta_campaign_scale, ig_organic_post_gap, walkin_audit_source, ...
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  rationale_json JSONB NOT NULL DEFAULT '{}',       -- data analysis + projection + previous_rejection_reason (feedback loop)
  action_payload_json JSONB NULL,                   -- e.g., {"endpoint": "meta_ads/campaigns/X/budget", "amount": 1400} — Slice 1 stored, NOT executed
  priority INT NOT NULL DEFAULT 50,
  confidence_pct INT NULL,                          -- 0-100
  projected_impact_text TEXT NULL,                  -- e.g., "+12 leads/mes · ROI 4.2x"
  status VARCHAR(16) NOT NULL DEFAULT 'open',       -- open | approved | rejected | expired | undone
  approved_by_user_id UUID NULL,
  approved_at TIMESTAMPTZ NULL,
  rejected_by_user_id UUID NULL,
  rejected_at TIMESTAMPTZ NULL,
  reject_reason VARCHAR(64) NULL,                   -- not_priority | already_doing | data_wrong | too_risky | other
  undo_until TIMESTAMPTZ NULL,                      -- 5min window post approve
  expires_at TIMESTAMPTZ NOT NULL,                  -- default created_at + 7 days
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_stage_status
  ON vitalia_lucas_recommendations (tenant_id, clinic_id, stage, status, priority DESC)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_undo_window
  ON vitalia_lucas_recommendations (undo_until)
  WHERE undo_until IS NOT NULL;
```

### 2.4 `vitalia_referrals` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_referrals (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  referrer_patient_id UUID NOT NULL,
  referred_patient_id UUID NULL,
  referral_code VARCHAR(16) NOT NULL,               -- 6-12 chars alfanum unique per tenant+clinic
  shared_at TIMESTAMPTZ NULL,
  signed_up_at TIMESTAMPTZ NULL,
  converted_at TIMESTAMPTZ NULL,
  conversion_value_cents BIGINT NULL,
  currency CHAR(3) NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'open',       -- open | shared | signed_up | converted | expired
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_referrals_code
  ON vitalia_referrals (tenant_id, clinic_id, referral_code)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_referrals_referrer
  ON vitalia_referrals (tenant_id, clinic_id, referrer_patient_id, status)
  WHERE deleted_at IS NULL;
```

### 2.5 `vitalia_appointments` UTM columns (brand-local table — no engine touch Slice 1)

```sql
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_source VARCHAR(64) NULL;
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(128) NULL;
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_medium VARCHAR(64) NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_utm
  ON vitalia_appointments (tenant_id, clinic_id, utm_source, utm_campaign)
  WHERE utm_source IS NOT NULL;
```

**Note:** /dev-team VERIFY `vitalia_appointments` is brand-local table (not engine `appointments`). If engine table → escalate `/pm-luana` for promotion proposal. Brand-local table OK to add columns directly.

## 3. Pydantic v2 DTOs

```python
# vitalia/backend/src/modules/vitalia/marketing/application/dtos/lucas_recommendation_dto.py
from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class LucasRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    stage: str  # attraction | qualification | reservation | adoption | expansion
    recommendation_kind: str
    title: str
    body: str
    rationale_json: dict[str, Any]
    action_payload_json: dict[str, Any] | None = None
    priority: int
    confidence_pct: int | None = None
    projected_impact_text: str | None = None
    status: str
    approved_by_user_id: UUID | None = None
    approved_at: datetime | None = None
    undo_until: datetime | None = None
    expires_at: datetime
    created_at: datetime


class ApproveRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Idempotency-Key header carried separately
    # No body fields required Slice 1


class RejectRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(..., pattern=r"^(not_priority|already_doing|data_wrong|too_risky|other)$")


class BowtieSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_start: datetime
    period_end: datetime
    stages: list["BowtieStageDTO"]
    overall_conversion_pct: float
    overall_roi_x: float | None = None
    overall_ltv_cents: int | None = None
    currency: str | None = None
    last_sync_at: datetime | None = None


class BowtieStageDTO(BaseModel):
    slug: str
    label: str
    count: int
    primary_kpi_value: float | None = None
    primary_kpi_label: str | None = None


class ChannelMetricDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    channel_slug: str
    metric_date: datetime
    impressions: int | None = None
    clicks: int | None = None
    conversions: int | None = None
    spend_cents: int | None = None
    currency: str | None = None


class AttributionMatrixResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_start: datetime
    period_end: datetime
    origins: list["AttributionOriginRow"]
    totals: "AttributionOriginRow"
    top_insight_text: str | None = None
    currency: str | None = None


class AttributionOriginRow(BaseModel):
    origin: str  # sales_agent | walk_in | phone_manual | proactive_outbound | total
    leads: int
    qualified: int
    conv_listo: int
    reservations: int
    adoption: int
    value_cents: int


class ReferralsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_start: datetime
    period_end: datetime
    referrals_count: int
    conv_rate: float
    avg_ltv_per_referrer_cents: int | None = None
    top_referrers: list["ReferrerLeaderboardRow"]
    currency: str | None = None


class ReferrerLeaderboardRow(BaseModel):
    referrer_patient_id_hash: str  # NEVER patient name — hash only
    referrals_count: int
    total_value_cents: int


class OAuthConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    redirect_uri: str
    state_token: str  # CSRF guard


class OAuthConnectResponse(BaseModel):
    authorize_url: str  # Frontend redirects user here


class SyncResponse(BaseModel):
    triggered: bool
    sync_state_id: UUID
    status: str
```

## 4. API routes (10 endpoints)

Router prefix `/api/v1/vitalia/marketing`. All routes require `Bearer JWT + X-Tenant-ID + X-Clinic-ID`. `redirect_slashes=False` app-level. `response_model=` mandatory on every endpoint.

| Method | Path | Role | Request | response_model | Idempotency |
|---|---|---|---|---|---|
| GET | `/bowtie/summary` | doctor/nurse/admin_clinic/recepcion | query `period=7d\|30d\|90d` | `BowtieSummaryResponse` | — |
| GET | `/stage/{stage_slug}` | doctor/nurse/admin_clinic/recepcion | path `attraction\|qualification\|reservation\|adoption\|expansion`; query `period` | `StageDetailResponse` | — |
| GET | `/channels/{provider}` | admin_clinic | path `meta_ads\|google_ads`; query `period` | `ChannelDetailResponse` | — |
| POST | `/channels/{provider}/connect` | admin_clinic | `OAuthConnectRequest` | `OAuthConnectResponse` | — (CSRF state_token) |
| POST | `/channels/{provider}/sync` | admin_clinic | — | `SyncResponse` | `Idempotency-Key` header |
| GET | `/recommendations` | doctor/nurse/admin_clinic/recepcion | query `stage`, `status`, `limit` | `list[LucasRecommendationResponse]` | — |
| POST | `/recommendations/{rec_id}/approve` | admin_clinic | `ApproveRecommendationRequest` | `LucasRecommendationResponse` | `Idempotency-Key` header (natural key `(tenant, clinic, rec_id, "approve")`) |
| POST | `/recommendations/{rec_id}/reject` | admin_clinic | `RejectRecommendationRequest` | `LucasRecommendationResponse` | `Idempotency-Key` |
| POST | `/recommendations/{rec_id}/undo` | admin_clinic | — | `LucasRecommendationResponse` | `Idempotency-Key`; window check `undo_until > now` |
| GET | `/attribution-matrix` | admin_clinic | query `period` | `AttributionMatrixResponse` | — |
| GET | `/referrals` | admin_clinic | query `period`, `leaderboard_limit` | `ReferralsResponse` | — |

10 endpoints total (matches parent arch).

## 5. Repositories (subclass `CompoundScopeRepositoryBase`)

```python
# vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/lucas_recommendation_repository.py
from __future__ import annotations
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from vitalia.modules.vitalia.marketing.infrastructure.models.lucas_recommendation_model import (
    LucasRecommendationModel,
)


class LucasRecommendationRepository(CompoundScopeRepositoryBase[LucasRecommendationModel, UUID]):
    MODEL = LucasRecommendationModel

    def __init__(self, *, session: AsyncSession) -> None:
        super().__init__(session=session, scope_field="clinic_id")

    # Custom queries added here (all dual-filter inherited from base)
    async def list_open_by_stage(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: str,
        limit: int = 3,
    ) -> list[LucasRecommendationModel]:
        ...

    async def list_pending_undo_expired(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[LucasRecommendationModel]:
        # Cron sweep helper to expire undo_until past
        ...
```

All 4 marketing repos follow the same pattern. Arch fitness `test_compound_scope_repo_consumed.py` enforce.

## 6. Application services

```python
# vitalia/backend/src/modules/vitalia/marketing/application/services/marketing_service.py
class MarketingService:
    """Orchestrator for bowtie summary + stage detail + channel detail.

    Reads:
      - channel_metric_repository (channel performance)
      - channel_sync_state_repository (last_sync_at status)
      - LucasAttributionService (existing — reused from agentic/lucas/)
      - LucasReferralsService (existing — reused)
      - LucasOrchestratorService (cron-triggered, recommendations read-only here)

    Writes: none (writes happen in cron jobs + approve/reject/undo handlers)
    """
    ...


# vitalia/backend/src/modules/vitalia/marketing/application/services/lucas_recommendations_service.py
class LucasRecommendationsService:
    """API-facing service.

    Proxies CRUD on lucas_recommendation_repository.

    approve(rec_id, user_id, idempotency_key):
      - Reads rec via repo
      - Sets status='approved', approved_by_user_id, approved_at, undo_until = approved_at + 5min
      - Writes audit_log row SYNC before commit (per hipaa-lite.md)
      - Publishes LucasRecommendationApproved event via outbox
      - Returns rec DTO

    reject(rec_id, user_id, reason, idempotency_key):
      - Sets status='rejected', rejected_by_user_id, rejected_at, reject_reason
      - rationale_json.previous_rejection_reason updated for feedback loop next cron
      - audit_log + outbox event LucasRecommendationRejected

    undo(rec_id, user_id, idempotency_key):
      - Validates undo_until > now() (5min window)
      - Sets status='undone', clears approved_at, approved_by_user_id, undo_until
      - audit_log + outbox event LucasRecommendationUndone
      - Slice 1: status undo only (Slice 2: also reverses Meta API call if action executed)
    """
    ...
```

`AttributionService` and `ReferralsService` are thin wrappers around existing Lucas services (`LucasAttributionService`, `LucasReferralsService`). They read snapshots persisted by Lucas daily cron — NO recompute on request (cache pattern).

## 7. Domain events (engine outbox bus consume)

| Event | When | Consumer |
|---|---|---|
| `LucasRecommendationGenerated` | Cron `lucas_daily_analysis_sweep` produces rec | FE optional toast notification + telemetry |
| `LucasRecommendationApproved` | User approves rec | FE invalidate React Query cache · Slice 2 wires Meta API call |
| `LucasRecommendationRejected` | User rejects rec | FE invalidate cache · telemetry |
| `LucasRecommendationUndone` | User undoes within 5min | FE re-show card if still pending |
| `LucasRecommendationExpired` | undo_until passed without action | telemetry only |
| `ChannelSyncSucceeded` | Cron metrics_sync completes OK | FE invalidate React Query cache |
| `ChannelSyncFailed` | Cron fails for a provider | Sentry alert + FE shows degraded state |
| `ReferralCodeGenerated` | New patient activates account → referral_code created | telemetry |
| `ReferralConverted` | Referred patient completes treatment | LucasReferralsService recomputes leaderboard next cron |

All events: `from luana_core_events.outbox.adapter_bus import publish` (default `USE_OUTBOX_PATTERN_*=True` since 2026-04-29).

## 8. Cron jobs (4 total — all decorated `@cron_envelope`)

### 8.1 `channel_metrics_sync_meta` — every 4h per tenant

```python
# vitalia/backend/src/modules/vitalia/marketing/jobs/channel_metrics_sync_meta.py
from luana_core_platform.workers.cron_envelope import cron_envelope

@cron_envelope("vitalia.cron.channel_metrics_sync_meta", ttl=14400)  # 4h
async def channel_metrics_sync_meta(ctx: dict) -> None:
    """Pull Meta Marketing API metrics per tenant+clinic with active Meta channel.

    Steps:
      1. Query channel_sync_state WHERE provider='meta_ads' AND enabled=TRUE AND status != 'disconnected'
      2. For each row: decrypt oauth_token, call Meta API
         GET /act_{account_id}/insights?level=campaign&fields=spend,impressions,clicks,actions,date_start,date_stop&time_range=last_30_days
      3. Upsert vitalia_channel_metrics rows (ON CONFLICT update via SQL — natural key uq_vitalia_channel_metrics_unique)
      4. Update sync_state.last_sync_at + last_success_at + status='idle'
      5. On error: status='error', last_error=str(exc), publish ChannelSyncFailed
      6. On success: publish ChannelSyncSucceeded

    Soft-fail per tenant — one tenant's Meta auth issue doesn't abort the cron.
    """
    ...
```

### 8.2 `channel_metrics_sync_google` — every 4h per tenant

Same pattern as Meta but Google Ads API via `customers.googleAds.search` GAQL.

### 8.3 `lucas_daily_analysis_sweep` — daily 06:00 UTC

```python
# vitalia/backend/src/modules/vitalia/marketing/jobs/lucas_daily_analysis_sweep.py
from luana_core_platform.workers.cron_envelope import cron_envelope

@cron_envelope("vitalia.cron.lucas_daily_analysis_sweep", ttl=86400)  # 24h
async def lucas_daily_analysis_sweep(ctx: dict) -> None:
    """Daily 06:00 UTC — Lucas regenerates recommendations per stage per tenant+clinic.

    Steps:
      1. For each tenant+clinic in active set:
         - Expire `vitalia_lucas_recommendations.status='open'` rows older than expires_at
         - Invoke LucasOrchestratorService.run_daily_sweep(tenant_id, clinic_id):
           * Compute attribution matrix via LucasAttributionService (pure DB)
           * Compute referrals leaderboard via LucasReferralsService (pure DB)
           * Call compute_stage_recommendation tool per stage (LLM-backed Lucas growth setter persona)
             - BudgetGuard.check(agent_kind="sales_agent", estimated_cost_usd=$0.02 per stage)
             - 5 stages × LLM call = 5 calls per tenant per day (cost capped)
         - Persist new vitalia_lucas_recommendations rows (status='open', expires_at=now+7d)
         - Skip recommendations matching previous_rejection_reason within 30d cooldown
      2. Publish LucasRecommendationGenerated events
    """
    ...
```

### 8.4 `referrals_value_sync` — daily 10:00 UTC

```python
@cron_envelope("vitalia.cron.referrals_value_sync", ttl=86400)
async def referrals_value_sync(ctx: dict) -> None:
    """Daily 10:00 UTC — refresh referral conversion values per referrer.

    Steps:
      1. For each referral WHERE status IN ('signed_up', 'converted'):
         - Query vitalia_appointments for referred_patient_id treatments completed since shared_at
         - Sum conversion_value_cents from completed appointments
         - Update referrals.converted_at + conversion_value_cents if changed
         - Publish ReferralConverted event if status transitions to 'converted'
    """
    ...
```

## 9. OAuth wizard adapters (`connections/{meta_ads,google_ads}/adapter.py`)

```python
# vitalia/backend/src/modules/vitalia/connections/meta_ads/adapter.py
class MetaAdsAdapter:
    """Meta Marketing API adapter — Slice 1 read-only (no budget changes).

    OAuth scopes Slice 1: `ads_read`, `ads_management` (read-only for now)
    """
    async def oauth_authorize_url(self, *, tenant_id: UUID, clinic_id: UUID, redirect_uri: str, state_token: str) -> str:
        """Step 1: return Meta authorize URL for user redirect."""
        ...

    async def oauth_callback(self, *, code: str, state_token: str) -> str:
        """Step 2: exchange code for token, encrypt via pgcrypto, persist channel_sync_state."""
        ...

    async def list_ad_accounts(self, *, oauth_token: str) -> list[dict]:
        """Step 3 helper: list ad_accounts for picker before final confirm."""
        ...

    async def fetch_insights(self, *, oauth_token: str, ad_account_id: str, since: date, until: date) -> list[dict]:
        """Cron pull — 1 API call per tenant per 4h."""
        ...
```

Similar pattern for `GoogleAdsAdapter` (GAQL `customers.googleAds.search` + offline access scope).

External calls wrapped per `tessl__graceful-degradation`:
- 30s timeout per call
- Exponential backoff retry 3× on 5xx
- Circuit breaker per tenant (5 consecutive failures → flag `status='error'` 1h cool-down)

Register adapters via Extension SDK EP-8 (channel_provider) in `vitalia/backend/src/modules/vitalia/extensions.py::register_all`. NO modifications to engine SDK — just additions to brand `extensions.py` (extends existing pattern from Story 11).

## 10. Test surfaces (TDD-mandatory RED first)

| Layer | Test path | Coverage |
|---|---|---|
| Domain entities | `vitalia/backend/tests/modules/vitalia/marketing/domain/` | Entity invariants, enums, events emission semantics |
| Infrastructure repos | `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/` | Dual filter enforce (`test_dual_filter_*`), upsert ON CONFLICT, pgcrypto encrypt roundtrip |
| Application services | `vitalia/backend/tests/modules/vitalia/marketing/application/services/` | MarketingService bowtie summary aggregation, approve/reject/undo state transitions, idempotency dedup, audit_log sync write, outbox events publish |
| API routes | `vitalia/backend/tests/modules/vitalia/marketing/api/` | All 10 endpoints — auth headers required, role gating, response_model schema, error paths (403 unauthorized, 404 not found, 409 idempotency conflict, 410 undo window expired) |
| Cron jobs | `vitalia/backend/tests/workers/test_marketing_crons.py` | 4 cron jobs — soft-fail per tenant, exponential backoff, outbox events publish, structlog audit logged |
| OAuth adapters | `vitalia/backend/tests/modules/vitalia/connections/{meta_ads,google_ads}/` | OAuth flow happy path + token encrypt + circuit breaker + rate-limit handling |
| Architecture fitness | `vitalia/backend/tests/architecture/` | All gates listed in `03-arch.md § 0` |

## 11. Migration order (sequential)

1. T-mk-be-1 migration 050: `vitalia_channel_sync_state`
2. T-mk-be-1 migration 051: `vitalia_channel_metrics`
3. T-mk-be-1 migration 052: `vitalia_lucas_recommendations`
4. T-mk-be-1 migration 053: `vitalia_referrals`
5. T-mk-be-1 migration 054: `vitalia_appointments` utm columns (idempotent ALTER ... ADD COLUMN IF NOT EXISTS)

All migrations idempotent raw SQL `IF NOT EXISTS`. Test pre-prod via clone DB workflow (per `.claude/rules/backend-migrations.md`):

```bash
docker exec visionarias_postgres createdb -U postgres vitalia_migration_test
docker exec visionarias_postgres pg_dump -U postgres -s vitalia_dev | docker exec -i visionarias_postgres psql -U postgres vitalia_migration_test
docker exec visionarias_postgres alembic -c vitalia/alembic.ini stamp head
docker exec visionarias_postgres alembic -c vitalia/alembic.ini upgrade head
docker exec visionarias_postgres dropdb -U postgres vitalia_migration_test
```

## 12. Wiring in `vitalia/backend/src/modules/vitalia/extensions.py`

Register the meta_ads + google_ads adapters via EP-8 (channel_provider). Register Lucas recommendation cron config via EP-N (NEW Slice 1 — brand-local dict, not engine modification):

```python
# Inside register_all(registry):
from vitalia.modules.vitalia.connections.meta_ads.adapter import MetaAdsAdapter
from vitalia.modules.vitalia.connections.google_ads.adapter import GoogleAdsAdapter

# EP-8 channel_provider
registry.register_channel_provider("meta_ads", MetaAdsAdapter(...))
registry.register_channel_provider("google_ads", GoogleAdsAdapter(...))

# Marketing crons registered via ARQ scheduler config (not engine EP — ARQ-specific)
# See vitalia/backend/src/modules/vitalia/marketing/jobs/__init__.py
```

## 13. Tests audit (default flip — N/A)

CONTRACT does NOT flip any feature flag default in this story. Marked `[x] No aplica — CONTRACT no flipea defaults side-effect`.

## 14. References

- `core/luana-core-platform/{workers/cron_envelope.py, repositories/compound_scope_repository.py}` (engine v0.4.0)
- `core/luana-core-{analytics-engine,extension-sdk,observability,events,idempotency,compliance,llm,billing}/` READ-ONLY
- `vitalia/backend/src/modules/vitalia/agentic/lucas/` (Lucas services shipped 2026-05-18)
- `vitalia/backend/src/modules/vitalia/extensions.py` (EP-1..EP-18 mount existing)
- `.claude/rules/{backend-ddd,backend-migrations,backend-quality,tenant-isolation,architectural-fitness,anti-duplication,master-data,currency-handling}.md`
- `vitalia/.claude/rules/hipaa-lite.md`
- Parent `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/03-arch-be.md` (sections 2.6-2.9, 3.5, services, jobs — heredados verbatim where applicable)
