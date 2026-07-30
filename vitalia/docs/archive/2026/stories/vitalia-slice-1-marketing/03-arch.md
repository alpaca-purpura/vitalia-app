---
story_id: vitalia-slice-1-marketing
parent: vitalia-ux-discovery (archived 2026-05-20)
architect_run_on: 2026-05-20
architect_model: claude-opus-4-7
brand: vitalia
compliance_level: hipaa_lite
ola: 2
ready_package_version: v1.0
---

# Architecture — vitalia-slice-1-marketing (consolidated index)

> Build NUEVO simple. NO growth-studio reuse (Chris 2026-05-20). 5 surfaces: Bowtie SVG · Lucas Stage Recommendations · AttributionMatrix · ReferralsWidget · Channels viewport read-only.

## 0. Context Summary

### PR + story metadata

- Brand: `vitalia`
- Story: `vitalia-slice-1-marketing`
- Ola: 2 (paralela con `vitalia-slice-1-pipeline`)
- Side-dependencies: NONE (all pre-flight gates GREEN — `vitalia-copilot-tools-impl` already shipped 2026-05-18, Lucas tools live)
- Engine extensions migrated (2026-05-20): `core/luana-core-platform.workers.cron_envelope` + `core/luana-core-platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` (v0.4.0)

### Artifact map

| Surface | File | Owner builder | Auditor |
|---|---|---|---|
| Consolidated index | `03-arch.md` (this file) | — | — |
| Backend sub-arch | `03-arch-be.md` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| Frontend sub-arch | `03-arch-fe.md` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| Agentic sub-arch (consumer-only — minimal) | `03-arch-agentic.md` | `builder-agentic` (Opus R23) audit only | `auditor-agentic` (Opus) |
| Validators ★ CRITICAL ★ | `04-validators.yaml` | — | — |
| Guidelines | `05-guidelines.md` | — | — |
| Tickets DAG | `06-tickets.yaml` | — | — |
| Cross-story handoff updates | `HANDOFF-cross-story-updates.md` | — | — |

### Surface → builder → auditor mapping (PM `/dev-team` consumes to spawn correct agents)

| Surface (paths) | Builder | Auditor | Model |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/marketing/{domain,application,api,infrastructure}/` | `builder-backend` | `auditor-backend` | Sonnet build · Opus audit |
| `vitalia/backend/src/modules/vitalia/connections/{meta_ads,google_ads}/` (adapters OAuth + sync) | `builder-backend` | `auditor-backend` | Sonnet · Opus |
| `vitalia/backend/src/modules/vitalia/analytics/extensions.py` (registry enabled_metrics + channel_groups extension) | `builder-backend` | `auditor-backend` | Sonnet · Opus |
| `vitalia/backend/tests/modules/vitalia/marketing/**` + `tests/workers/test_marketing_crons.py` | `builder-backend` | `auditor-backend` | Sonnet · Opus |
| `vitalia/frontend/src/features/marketing/**` + `features/marketing-shared/types.ts` | `builder-frontend` | `auditor-frontend` | Sonnet · Opus |
| `vitalia/frontend/src/app/marketing/page.tsx` route | `builder-frontend` | `auditor-frontend` | Sonnet · Opus |
| `vitalia/frontend/e2e/{pages,specs}/marketing*` | `builder-frontend` | `auditor-frontend` | Sonnet · Opus |
| Lucas tools (READ-ONLY consumption — NO modify) `vitalia/backend/src/modules/vitalia/agentic/lucas/**` | (none — consumer-only) | `auditor-agentic` (sanity verify no agentic surface contracted) | Opus audit |

**Skills consulted (one-liner decisions):**

- `metrics-expert` — Bowtie 5 stages mapeo a engine funnel_stage existing enum. NO mirror stage_service per-brand. Vitalia analytics extensions registra `enabled_metrics` (medical subset) + `channel_groups` (LATAM medical).
- `backend-expert` — DDD Inside-Out. Dual filter `tenant_id + clinic_id` via `CompoundScopeRepositoryBase`. Migrations idempotentes raw SQL. Audit log sync write. Pgcrypto encrypt `oauth_token_encrypted`.
- `frontend-expert` — FSD-Lite `features/marketing/`. Server Components default. nuqs URL state SSoT. Tokens-only CSS vars (no HEX literales). Build simple — no growth-studio.
- `sales-agent-expert` — Lucas tools R23 production ya shipped. Marketing surface es CONSUMER ONLY. No agentic surface contracted en este story (NO new prompts, NO new tools).
- `tessl__graceful-degradation` — External calls (Meta, Google) wrap timeout + fallback. Cron retry exponential backoff. Soft-fail per provider isolated.

**capability YAML files affected (post-merge updates):**
- `vitalia/docs/product/capabilities/marketing/bowtie-5stages-lucas.yaml` (NEW)
- `vitalia/docs/product/modules/marketing.md` (NEW)

**Architecture fitness gates that must keep passing:**

Engine + brand fitness suites (allowlist shrinks only):
- `vitalia/backend/tests/architecture/test_phi_dual_filter.py` — tenant + clinic dual filter cardinal
- `vitalia/backend/tests/architecture/test_no_cross_brand_imports.py` — anti-duplication
- `vitalia/backend/tests/architecture/test_no_legacy_paths.py` — no `backend/src/shared/` (root) imports
- `vitalia/backend/tests/architecture/test_response_model_required.py` — `response_model=` mandatory
- `vitalia/backend/tests/architecture/test_migrations_idempotent.py` — `IF NOT EXISTS` raw SQL
- `vitalia/backend/tests/architecture/test_audit_log_sync_write.py` — PHI mutations write audit_log pre-response
- `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py` — encryption columns use pgcrypto
- `vitalia/backend/tests/architecture/test_extension_sdk_registration.py` — vitalia extensions register via EP only
- `vitalia/backend/tests/architecture/test_cron_envelope_consumed.py` (NEW Slice 1) — all `marketing/jobs/*.py` use engine `@cron_envelope`, no brand-local mirror
- `vitalia/backend/tests/architecture/test_compound_scope_repo_consumed.py` (NEW Slice 1) — all `marketing/infrastructure/repositories/*.py` subclass engine `CompoundScopeRepositoryBase`
- `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_colors.test.ts` — only CSS vars
- `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_strings.test.ts` — user strings in copy.ts
- `vitalia/frontend/src/__tests__/architecture/test_fsd_boundaries.test.ts` — boundaries error
- `vitalia/frontend/src/__tests__/architecture/test_no_cross_feature_imports.test.ts` — Public API only
- `vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts` — RSC default
- `vitalia/frontend/src/__tests__/architecture/test_no_voseo_in_copy.test.ts` — Spanish neutro

## 1. Top-level architecture (cross-surface contract)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ User (Owner clínica P1 + Admin P2 + Recepción)                                │
│ HTTPS + Clerk JWT + X-Tenant-ID + X-Clinic-ID                                 │
└────────────────────────┬─────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Frontend vitalia (Next.js 16 App Router · FSD-Lite)                           │
│ Port 3002 (dev)                                                                │
│   features/marketing/                                                          │
│     ├ MarketingLayout · MarketingBowtieSVG · StageDispatcher                  │
│     ├ AttractionStage · QualificationStage · ReservationStage                 │
│     │  · AdoptionStage · ExpansionStage                                        │
│     ├ LucasStageRecommendationsCard ★ · LucasRecommendationDetailModal         │
│     │  · LucasApprovalModal                                                    │
│     ├ AttributionMatrixWidget · ReferralsWidget · ChannelBreakdownRow          │
│     │  · ChannelDetailSidebar · ChannelConnectionWizard                        │
│     └ store/marketing-store.ts · copy.ts · types/ · api/ hooks                 │
│   features/marketing-shared/types.ts (cross-story consumption /pipeline)       │
└────────────────────────┬─────────────────────────────────────────────────────┘
                          ▼ REST + Idempotency-Key headers
┌──────────────────────────────────────────────────────────────────────────────┐
│ Backend vitalia (FastAPI async · DDD Inside-Out)                              │
│ Port 8002 (dev) · redirect_slashes=False                                       │
│   modules/vitalia/marketing/                                                   │
│     ├ domain/entities: ChannelSyncState · ChannelMetric · LucasRecommendation │
│     │  · Referral                                                              │
│     ├ infrastructure/repositories: subclass CompoundScopeRepositoryBase       │
│     │  scope_field="clinic_id"                                                 │
│     ├ application/services: MarketingService · AttributionService             │
│     │  · ReferralsService · LucasRecommendationsService (proxy a Lucas svc)   │
│     ├ api: 10 endpoints /api/v1/vitalia/marketing/...                          │
│     ├ persistence/migrations: 4 NEW tables + 3 utm columns                    │
│     └ jobs/: 4 cron jobs decorados @cron_envelope                              │
│   modules/vitalia/connections/{meta_ads,google_ads}/                          │
│     └ adapter.py (OAuth wizard 3 pasos + sync simplificado)                   │
│   modules/vitalia/agentic/lucas/  (READ-ONLY consumption — Lucas ya shipped)  │
│     └ services/* invoked by cron lucas_daily_analysis_sweep                   │
└──────┬─────────────────────────────────────────┬──────────────────────────────┘
        │ Engine consume (READ-ONLY)              │ External (graceful degradation)
        ▼                                          ▼
┌────────────────────────────────┐  ┌─────────────────────────────────────────┐
│ core/luana-core-*              │  │ Meta Marketing API (1 call/tenant 4h)   │
│   platform.workers.cron_env    │  │ Google Ads API (1 call/tenant 4h)       │
│   platform.repositories.       │  │ Sentry/OpenTelemetry                    │
│     compound_scope_repository  │  │                                          │
│   analytics-engine.stage_svc   │  │                                          │
│   extension-sdk EP-7,EP-8      │  │                                          │
│   events.outbox                │  │                                          │
│   idempotency                  │  │                                          │
│   observability.sanitize       │  │                                          │
└────────────────────────────────┘  └─────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Data layer · Postgres 5435 + Redis 1                                          │
│   Tablas NEW vitalia: 4 (channel_sync_state · channel_metrics ·               │
│                              lucas_recommendations · referrals)                │
│   Column additions: vitalia_appointments.{utm_source,utm_campaign,utm_medium} │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 2. Cross-cutting design principles (consumed by all 3 sub-archs)

### 2.1 Tenant + Clinic dual filter via `CompoundScopeRepositoryBase`

**Engine extension (v0.4.0 — migrated 2026-05-20):**

```python
# In all marketing repositories:
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from vitalia.modules.vitalia.marketing.infrastructure.models.channel_sync_state_model import (
    ChannelSyncStateModel,
)

class ChannelSyncStateRepository(CompoundScopeRepositoryBase[ChannelSyncStateModel, UUID]):
    MODEL = ChannelSyncStateModel

    def __init__(self, *, session: AsyncSession) -> None:
        super().__init__(session=session, scope_field="clinic_id")
```

Engine enforce dual filter automático per `tenant_id` + `clinic_id`. Arch fitness `test_compound_scope_repo_consumed.py` valida que TODOS los marketing repos subclasen `CompoundScopeRepositoryBase` con `scope_field="clinic_id"`.

### 2.2 Cron envelope engine `@cron_envelope`

**Engine extension (v0.4.0):**

```python
# In all marketing/jobs/*.py:
from luana_core_platform.workers.cron_envelope import cron_envelope

@cron_envelope("vitalia.cron.lucas_daily_analysis_sweep", ttl=86400)
async def lucas_daily_analysis_sweep(ctx: dict) -> None:
    """Daily 06:00 UTC sweep — Lucas regenerates recommendations per stage."""
    ...
```

Engine envelope wires idempotency + OTel span + structlog audit + Sentry capture (graceful degradation per dependency). Arch fitness `test_cron_envelope_consumed.py` valida que TODOS los marketing crons usan `@cron_envelope`, NO brand-local mirror de `vitalia/_shared/workers/base.py::idempotent_cron` (deprecated post engine lift).

### 2.3 PII sanitization in traces + audit_log payload

`sanitize_payload(payload, compliance_level="hipaa_lite")` from `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` aplicado pre-write a `vitalia_audit_log.payload_redacted`. UTM payloads NUNCA contienen PHI (no patient.name, no patient.dni, solo IDs hash + channel slug + timestamp).

### 2.4 Encryption at-rest (pgcrypto) — campos sensible

- `vitalia_channel_sync_state.oauth_token_encrypted BYTEA` (symmetric pgcrypto · KEK rotada anualmente)
- `vitalia_audit_log.payload_redacted BYTEA` (defense in depth aunque ya sanitized)

KEK via `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py` (heredado infra-cross-cutting story Slice 1 — ya shipped).

### 2.5 RBAC strict (marketing-relevant roles)

| Role | Marketing permissions |
|---|---|
| `admin_clinic` | Full — connect/disconnect channels, approve/reject Lucas recommendations, view all metrics |
| `marketing` (Slice 2 future role) | View metrics + Lucas recommendations · NO approve budget changes |
| `doctor`, `nurse` | View bowtie summary only · NO Lucas approvals · NO channel sync controls |
| `recepcion` | View bowtie summary only |
| `patient` | NO ACCESS — 403 |

Decorator `@require_role(["admin_clinic"])` en aprobar/rechazar/undo + connect/disconnect endpoints.

### 2.6 Currency policy

`vitalia_channel_metrics.spend_cents BIGINT` + `currency CHAR(3)`. Preserve API source currency (Meta Ads API returns spend en account currency). FE consume `formatMoney(amount_cents / 100, currency)`. DTO incluye `currency: str | None`.

### 2.7 Spanish neutro LatAm strict

UI chrome `vitalia/frontend/src/features/marketing/copy.ts` MUST follow `.claude/rules/spanish-text.md`. Arch fitness `test_no_voseo_in_copy.test.ts` enforce.

### 2.8 Master data (UTC + timezone tenant)

`DateTime(timezone=True)` mandatory. Store UTC. Display via `useTenantLocale()` resolving from `tenants.timezone`.

### 2.9 Idempotency on writes

POST `/marketing/recommendations/{id}/{approve,reject,undo}` + POST `/marketing/channels/{provider}/sync` require `Idempotency-Key` header → engine `core/luana-core-idempotency/` checks `idempotency_keys` table. Pattern natural key for approve: `(tenant_id, clinic_id, recommendation_id, action)` partial unique idx.

### 2.10 No cross-brand mirror (anti-duplication audit)

Cross-brand grep executed:

```bash
WS=/home/chalreme/Proyectos/luana-vitalia
# Channel sync pattern
grep -rln "channel_sync_state\|ChannelSyncState" ${WS}/core/luana-core-*/src/ ${WS}/{nicolify,comunify,lupulo}/backend/src/ 2>/dev/null
# Referrals pattern
grep -rln "referrals.*leaderboard\|ReferralCode" ${WS}/core/luana-core-*/src/ ${WS}/{nicolify,comunify,lupulo}/backend/src/ 2>/dev/null
```

Result: ZERO mirrors detected. ChannelSyncState pattern is vitalia-medical-specific Slice 1; lift to engine candidate Slice 2 when 2nd brand opta-in medical channel sync. Referrals pattern likewise.

**Anti-duplication shared abstractions consumed (per `.claude/rules/anti-duplication.md`):**
- `sanitize_payload` from `core/luana-core-observability/recording/sanitization.py`
- `cron_envelope` from `core/luana-core-platform/workers/cron_envelope.py` (migrated 2026-05-20)
- `CompoundScopeRepositoryBase` from `core/luana-core-platform/repositories/compound_scope_repository.py` (migrated 2026-05-20)
- Outbox bus from `core/luana-core-events/outbox/adapter_bus.py` (publish `LucasRecommendationGenerated`, `LucasRecommendationApproved`, `ChannelSyncSucceeded`, `ChannelSyncFailed`, `ReferralConverted`)
- Idempotency keys from `core/luana-core-idempotency/`
- Analytics adapter from existing `vitalia/backend/src/modules/vitalia/agentic/lucas/infrastructure/adapters/analytics_engine_query_adapter.py` (consumes engine `core/luana-core-analytics-engine/` READ-ONLY)

## 3. Existing systems audit (NO NEW LAYER per anti-duplication.md)

### Source of evidence

- [x] CONTEXT-BRIEF.md absent — used Path B (self-run greps + engine package read)
- [x] Lucas services already shipped 2026-05-18 — consumed READ-ONLY
- [x] Engine extensions migrated 2026-05-20 (cron_envelope + CompoundScopeRepositoryBase) — consumed via import
- [x] Cross-brand mirror check executed — ZERO mirrors

### Sistemas existentes encontrados

| Sistema | Path canónico | Decisión Vitalia marketing |
|---|---|---|
| Cron envelope decorator | `core/luana-core-platform/workers/cron_envelope.py` (v0.4.0) | **CONSUME via import** — NO mirror `vitalia/_shared/workers/base.py::idempotent_cron` (deprecated) |
| Dual-scope repository base | `core/luana-core-platform/repositories/compound_scope_repository.py` (v0.4.0) | **EXTEND via subclass** with `scope_field="clinic_id"` |
| Analytics stage services + ChannelRegistry | `core/luana-core-analytics-engine/` | **CONSUME via existing `AnalyticsEngineQueryAdapter`** (Lucas already wires) |
| Observability sanitization | `core/luana-core-observability/recording/sanitization.py` | **CONSUME via import** |
| Outbox events bus | `core/luana-core-events/outbox/adapter_bus.py` | **CONSUME via import** (post 2026-04-29 default ON) |
| Idempotency keys | `core/luana-core-idempotency/` | **CONSUME via header Idempotency-Key** |
| Lucas growth setter services + tools | `vitalia/backend/src/modules/vitalia/agentic/lucas/` (shipped 2026-05-18) | **CONSUME via service layer** — Marketing's `LucasRecommendationsService` proxies to `LucasOrchestratorService` |
| Compliance gates | `core/luana-core-compliance/` | **CONSUME** — channel guards block PHI on WhatsApp free / SMS / plaintext email |
| Tenant locale VO | `core/luana-core-platform/domain/locale.py::TenantLocale` | **CONSUME** for currency + timezone |

### Decisión por sistema (EXTEND > REPLACE > NEW priority)

**ALL CONSUME / EXTEND** — zero NEW infrastructure layers proposed. Brand-extension only. Zero engine modifications proposed.

**Cross-brand mirror risk:** ZERO — vitalia-medical-specific surfaces only (channel_sync_state, referrals, lucas recommendations stored brand-local). Slice 2 lift candidates documented (lucas patterns + channel_sync_state).

## 4. Performance budgets (Slice 1 — heredados parent)

| Metric | Budget |
|---|---|
| LCP (Largest Contentful Paint) | < 2.5s |
| INP (Interaction to Next Paint) | < 200ms |
| CLS (Cumulative Layout Shift) | < 0.1 |
| Bowtie SVG bundle size | < 30KB gzipped (pixel-invariante mantenimiento) |
| Lucas cards | lazy-load below fold via intersection observer |
| LLM cost per Lucas daily sweep (per tenant) | ≤ $0.10 USD (Lucas calls Kimi K2.6 Standard tier · daily aggregation) |

Validators per `04-validators.yaml::visual` + `04-validators.yaml::non_functional`.

## 5. Observability + tracing

### OpenTelemetry tracing (NEW spans)

- `vitalia.cron.channel_metrics_sync_meta` (cron every 4h)
- `vitalia.cron.channel_metrics_sync_google` (cron every 4h)
- `vitalia.cron.lucas_daily_analysis_sweep` (cron 06:00 UTC)
- `vitalia.cron.referrals_value_sync` (cron daily 10:00 UTC)
- `vitalia.marketing.bowtie_summary` (request handler)
- `vitalia.marketing.stage_detail` (request handler)
- `vitalia.marketing.channel_detail` (request handler)
- `vitalia.marketing.approve_recommendation` (mutation)
- `vitalia.marketing.sync_channel` (manual trigger)

### Sentry/observability alerts

- Cron `channel_metrics_sync_*` falla > 3 consecutive (24h window) → page on-call
- Lucas daily sweep falla → warn (Lucas already silent-fails — re-runs next day)
- Meta API rate limit hit → throttle + degrade UI to last_known
- Google API rate limit hit → idem

### Activity feed footer template

"Lucas analizó {leads_analyzed} leads · sistema sync c/4h · última {last_sync_relative}"

Fed by `GET /api/v1/vitalia/marketing/bowtie/summary` response field `last_sync_at` from `ChannelSyncState`.

## 6. Open Questions (deferred to /dev-team — non-blocking)

| # | Question | Resolution |
|---|---|---|
| 1 | UTM columns en `vitalia_appointments` ya existen? | /dev-team VERIFY via grep ANTES T-mk-be-1. If absent, brand-local migration OK (no engine touch since `vitalia_appointments` puede ser brand table local). |
| 2 | Lucas LLM tool call cost guard (BudgetGuard) | Per `sales-agent-expert::Budget + Outbound Gating` — Lucas calls go through `BudgetGuard.check(agent_kind="sales_agent")` consume SA pool. Already wired in `LucasOrchestratorService`. /dev-team CONFIRM by reading existing service code. |
| 3 | Meta + Google OAuth scopes Slice 1 | Meta: `ads_read, ads_management` (sync only Slice 1, NO budget changes). Google: `https://www.googleapis.com/auth/adwords` read-only scope. Documented in `03-arch-be.md § OAuth Wizard`. |
| 4 | Visual regression baselines initial commit | T-mk-fe-7 generates baselines via Playwright `--update-snapshots` flag. Chris approves baselines pre-merge. |

## 7. Engine gaps (escalate `/pm-luana` — NOT in scope)

Architectural review found ZERO engine gaps requiring promotion proposal for Slice 1 of this story.

Slice 2 lift candidates (documented `HANDOFF-cross-story-updates.md`):
- Lucas recommendations pattern (when 2nd brand opta-in growth agent)
- Channel sync state pattern (when 2nd brand opta-in ad channels)
- Referrals pattern (when 2nd brand opta-in referral leaderboard)

## 8. Surface details — read sub-archs

- BE: `03-arch-be.md` (entities, tables, repos, services, API routes, DTOs, migrations, cron jobs, OAuth adapters)
- FE: `03-arch-fe.md` (FSD layout, components, TS types, nuqs URL state, React Query hooks, Zod schemas, Storybook, arch tests, performance)
- Agentic: `03-arch-agentic.md` (consumer-only surface — NO new tools/personas/goldens · existing Lucas tools R23-verified)

## 9. References

- Parent `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/{01-spec.md § §§ Ruta /marketing, 03-arch*, 06-tickets.yaml T-marketing-1..8}`
- `vitalia/docs/architecture/design-system.md` (tokens + tipografía + agent attribution)
- `vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md` (fork físico Slice 1 — ratified)
- `vitalia/.claude/rules/hipaa-lite.md` (PHI compliance overlay)
- `vitalia/config/brand.yaml` (compliance_level=hipaa_lite, feature flags)
- `vitalia/backend/src/modules/vitalia/extensions.py` (EP-1..EP-18 mount existing)
- `vitalia/backend/src/modules/vitalia/agentic/lucas/` (Lucas tools + services shipped 2026-05-18)
- `core/luana-core-platform/{workers/cron_envelope.py, repositories/compound_scope_repository.py}` (engine v0.4.0)
- `core/luana-core-{analytics-engine,extension-sdk,observability,events,idempotency,compliance,scheduling,llm,billing}/` READ-ONLY consultation
- `.claude/rules/{tenant-isolation,backend-ddd,frontend-fsd,architectural-fitness,anti-duplication,spanish-text,tdd-mandatory,master-data,currency-handling,auditor-downstream-regression}.md`
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` (cross-story contracts)

## 10. Research notes (DATE-AWARE — accessed 2026-05-20)

| Source | Version | Accessed | Key takeaway |
|---|---|---|---|
| FastAPI redirect_slashes | 0.115+ | 2026-05-20 | `FastAPI(redirect_slashes=False)` mandatory. App-level only. |
| SQLAlchemy 2.0 async | 2.0.30+ | 2026-05-20 | `mapped_column()` syntax · `select(Model).where(...)` · async-first. |
| Pydantic v2 | 2.10+ | 2026-05-20 | `ConfigDict(from_attributes=True)` mandatory. |
| Next.js 16 App Router | 16.x | 2026-05-20 | URL state nuqs SSoT. Server Components default. |
| Meta Marketing API | v18.0 (current as of 2026-05) | 2026-05-20 | `GET /act_{ad_account_id}/insights?level=campaign&fields=spend,impressions,clicks,actions,date_start,date_stop&time_range=...` — 1 call per tenant. Rate limit 200 req/h tier free, exponential backoff mandatory. |
| Google Ads API | v15 (current as of 2026-05) | 2026-05-20 | `customers.googleAds.search` with GAQL — 1 call per tenant. Bidirectional pagination. |
| OpenTelemetry Python | otel 1.30+ | 2026-05-20 | `tracer.start_as_current_span("vitalia.cron.X")` instrumentation. |
| pgcrypto | Postgres 16 | 2026-05-20 | `pgp_sym_encrypt(data, key)` for symmetric encrypt at-rest. KEK via Vault/KMS, not env. |
| Playwright + Chromatic visual regression | Playwright 1.50 · Chromatic | 2026-05-20 | Snapshot per breakpoint (mobile 768 · tablet 1024 · desktop 1440). Diff threshold 0.1%. |
| WCAG 2.1 AA | WAI-ARIA 1.2 | 2026-05-20 | Bowtie SVG with `<title>` + role="img". Keyboard nav Lucas cards. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff is Jan 2026. Post-cutoff topics (multibrand reorg 2026-05-15, engine cron_envelope + CompoundScopeRepositoryBase lift 2026-05-20) verified via current codebase state grep. Lucas services shipped 2026-05-18 verified via `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/`.

---

**Next sub-archs:** read `03-arch-be.md`, `03-arch-fe.md`, `03-arch-agentic.md` for surface-specific contracts.
