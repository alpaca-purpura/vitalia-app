---
story_id: vitalia-slice-1-marketing
brand: vitalia
generated: 2026-05-20
generator: /architect
---

# Guidelines — vitalia-slice-1-marketing

## 1. Files in scope (paths /dev-team can touch)

### Backend (builder-backend)

```
vitalia/backend/src/modules/vitalia/marketing/**                           ← NEW Slice 1 (all)
vitalia/backend/src/modules/vitalia/connections/meta_ads/**                ← NEW Slice 1
vitalia/backend/src/modules/vitalia/connections/google_ads/**              ← NEW Slice 1
vitalia/backend/src/modules/vitalia/extensions.py                          ← EDIT (add 2 register_channel_provider calls Meta + Google via EP-8)
vitalia/backend/tests/modules/vitalia/marketing/**                         ← NEW (test surfaces)
vitalia/backend/tests/modules/vitalia/connections/meta_ads/**              ← NEW
vitalia/backend/tests/modules/vitalia/connections/google_ads/**            ← NEW
vitalia/backend/tests/workers/test_marketing_crons.py                      ← NEW
vitalia/backend/tests/architecture/test_cron_envelope_consumed.py          ← NEW (arch fitness gate)
vitalia/backend/tests/architecture/test_compound_scope_repo_consumed.py    ← NEW (arch fitness gate)
```

### Frontend (builder-frontend)

```
vitalia/frontend/src/app/marketing/page.tsx                                ← NEW route
vitalia/frontend/src/features/marketing/**                                 ← NEW Slice 1
vitalia/frontend/src/features/marketing-shared/**                          ← NEW Slice 1 (cross-story types)
vitalia/frontend/src/components/shared/{marketing,lucas-recommendations,attribution,channels}/**  ← EDIT (promote scaffolds: replace stub bodies with real implementations consuming feature hooks)
vitalia/frontend/src/lib/zod-schemas/lucas-recommendation.ts               ← NEW
vitalia/frontend/src/lib/nuqs-parsers/marketing-parsers.ts                 ← NEW (re-export from feature)
vitalia/frontend/e2e/pages/marketing.page.ts                               ← NEW POM
vitalia/frontend/e2e/specs/smoke/marketing.smoke.spec.ts                   ← NEW
vitalia/frontend/e2e/specs/a11y/marketing.a11y.spec.ts                     ← NEW
vitalia/frontend/scripts/check-bowtie-bundle.mjs                           ← NEW perf budget script
```

### Out of scope (HARD BAN — escalate if needed)

```
core/luana-core-**                                                         ← READ-ONLY consultation
{nicolify,comunify,lupulo}/**                                              ← cross-brand pollution
vitalia/backend/src/modules/vitalia/agentic/lucas/**                       ← Already shipped; consumer-only access via service imports
vitalia/backend/src/modules/vitalia/{inbox,pipeline,agenda,fidelizacion,onboarding,iam,crm}/**  ← Other stories
vitalia/frontend/src/features/{inbox,pipeline,agenda,fidelizacion,onboarding,vitalia,dashboard,crm-shared}/**  ← Other stories (except marketing-shared which IS this story's)
.claude/{rules,skills}/                                                    ← Meta-paradigm change
docs/process/, docs/architecture/, docs/specs/                             ← Meta
vitalia/.claude/rules/, vitalia/.claude/skills/                            ← Brand overlay meta
```

## 2. Required patterns

### 2.1 Backend DDD Inside-Out

- Domain layer pure Python — no SQLAlchemy, no FastAPI imports in `domain/`
- Infrastructure implements domain interfaces — repos subclass `CompoundScopeRepositoryBase` (engine `core/luana-core-platform/repositories/compound_scope_repository.py`) with `scope_field="clinic_id"`
- Application services orchestrate via repos + adapters — NO direct DB queries in services
- API thin: routes call services, services return DTOs, DTOs serialise via `response_model=`

### 2.2 Tenant + Clinic dual filter (cardinal)

EVERY query touching PHI or tenant-scoped data uses `CompoundScopeRepositoryBase` dual filter:

```python
class LucasRecommendationRepository(CompoundScopeRepositoryBase[LucasRecommendationModel, UUID]):
    MODEL = LucasRecommendationModel
    def __init__(self, *, session: AsyncSession) -> None:
        super().__init__(session=session, scope_field="clinic_id")
```

Arch fitness `test_compound_scope_repo_consumed.py` enforces.

### 2.3 Cron envelope engine `@cron_envelope`

ALL marketing crons use engine decorator. NO brand-local mirror of `vitalia/_shared/workers/base.py::idempotent_cron` (deprecated post lift 2026-05-20):

```python
from luana_core_platform.workers.cron_envelope import cron_envelope

@cron_envelope("vitalia.cron.channel_metrics_sync_meta", ttl=14400)
async def channel_metrics_sync_meta(ctx: dict) -> None:
    ...
```

### 2.4 Migrations idempotent

Raw SQL `IF NOT EXISTS` per `.claude/rules/backend-migrations.md`. NO `op.create_table()`, NO `op.add_column()`, NO `sa.Enum(create_type=True)`.

```python
op.execute("CREATE TABLE IF NOT EXISTS vitalia_lucas_recommendations (...)")
op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_stage_status ON ...")
op.execute("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_source VARCHAR(64) NULL")
```

### 2.5 SQLAlchemy 2.0 + Pydantic v2

```python
# SA 2.0 ONLY
result = await session.execute(select(LucasRecommendationModel).where(...))
# NOT: session.query(LucasRecommendationModel)

# Pydantic v2 ONLY
class ApproveRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
# NOT: class Config: orm_mode = True
```

### 2.6 FastAPI `redirect_slashes=False` + headers

App-level only (already configured in `vitalia/backend/src/main.py`). EVERY route requires `Bearer JWT + X-Tenant-ID + X-Clinic-ID`. `response_model=` mandatory.

### 2.7 Audit log sync write pre-response

Per `vitalia/.claude/rules/hipaa-lite.md` — every PHI/sensitive mutation writes `vitalia_audit_log` SYNC before response, same transaction. Approve/reject/undo are sensitive (financial decision audit trail).

```python
async def approve(self, *, rec_id: UUID, user_id: UUID, tenant_id: UUID, clinic_id: UUID) -> LucasRecommendation:
    async with self._session.begin():
        rec = await self._repo.get_by_id(tenant_id=tenant_id, clinic_id=clinic_id, id=rec_id)
        rec.status = "approved"
        rec.approved_by_user_id = user_id
        rec.approved_at = utc_now()
        rec.undo_until = rec.approved_at + timedelta(minutes=5)
        await self._repo.save(rec)
        await self._audit_log_repo.record(
            tenant_id=tenant_id, clinic_id=clinic_id, user_id=user_id,
            action="lucas_recommendation_approved",
            resource_type="lucas_recommendation",
            resource_id=rec_id,
            payload_redacted=sanitize_payload({"rec_kind": rec.recommendation_kind}, compliance_level="hipaa_lite"),
        )
    await self._outbox_bus.publish(LucasRecommendationApproved(...))
    return rec
```

### 2.8 PgCrypto encrypt OAuth tokens

`vitalia_channel_sync_state.oauth_token_encrypted BYTEA` uses pgcrypto symmetric. KEK via `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py` (shipped infra-cross-cutting).

### 2.9 Outbox events bus

Domain events published via `from luana_core_events.outbox.adapter_bus import publish` (post 2026-04-29 default ON). NO `EventBus.publish` legacy.

### 2.10 Idempotency on writes

POST mutations (approve, reject, undo, sync) accept `Idempotency-Key` header. Engine `core/luana-core-idempotency/` validates uniqueness.

### 2.11 Spanish neutro LatAm strict

UI chrome strings live in `vitalia/frontend/src/features/marketing/copy.ts::MARKETING_COPY`. NO inline strings in `.tsx`. Arch fitness `test_no_voseo_in_copy.test.ts` enforce.

**Exception:** Lucas-generated `rec.title` + `rec.body` displayed verbatim (preserves tenant voice). Arch test scope is `copy.ts` files only.

### 2.12 Master data (UTC + timezone tenant + currency)

`DateTime(timezone=True)` mandatory. Store UTC. FE display via `useTenantLocale()`.

Monetary fields: `spend_cents BIGINT` + `currency CHAR(3)` (NOT just `spend_usd`). FE consumes `formatMoney(amount_cents / 100, currency)`. NEVER hardcode `'USD'`.

### 2.13 FSD-Lite frontend boundaries

- `features/marketing/` can import from: `features/marketing/`, `features/marketing-shared/`, `lib/`, `hooks/`, `components/shared/`
- Cross-feature import ONLY via Public API `index.ts` (e.g., `/pipeline` imports `marketing-shared` via `@/features/marketing-shared`)
- Server Components default — `"use client"` only at leaf nodes with hooks/event handlers

### 2.14 React Query patterns

`queryKey: ["marketing", resource, params]` namespace. `staleTime: 5 * 60 * 1000` (5min) — Lucas cron is daily, channels c/4h, so 5min cache fits. `invalidateQueries({ queryKey: ["marketing", ...] })` on mutation success.

### 2.15 Tokens-only CSS vars (no HEX literales)

All colors via CSS custom properties from `vitalia/frontend/src/app/globals.css` (per `vitalia/docs/architecture/design-system.md`). Arch fitness `test_no_hardcoded_colors.test.ts` enforce.

```tsx
// ✅ OK
className="vt-bg-surface vt-border"
style={{ backgroundColor: "var(--vitalia-cian-color)" }}

// ❌ BAN
className="bg-[#01B2F8]"
style={{ backgroundColor: "#01B2F8" }}
```

### 2.16 Graceful degradation (Meta + Google APIs)

Per `tessl__graceful-degradation`:
- 30s timeout per external API call
- Exponential backoff retry 3× on 5xx (1s, 2s, 4s)
- Circuit breaker per provider (5 consecutive failures → `status='error'` 1h cool-down)
- Soft-fail per tenant in cron — one tenant's Meta auth issue doesn't abort the cron for others
- UI degraded state: show `last_known` metrics with timestamp + warning badge, NEVER spinner indefinido

### 2.17 TDD mandatory

RED test before implementation. Per layer order BE: domain → infrastructure → application → API. FE: hook → component → store. E2E smoke before route impl.

## 3. Forbidden patterns

| ❌ Anti-pattern | Why | ✅ Correct |
|---|---|---|
| Mirror Lucas pattern in marketing module (`class LucasRecommendationsService` reimplementing growth setter) | Anti-duplication cross-module (`.claude/rules/anti-duplication.md`) | Consume existing `LucasOrchestratorService` via Python import |
| Hardcoded HEX colors in `.tsx` | Design system violation | CSS vars from `globals.css` |
| Inline UI strings in `.tsx` | Spanish neutro arch test | `MARKETING_COPY.namespace.key` |
| Voseo in UI chrome `copy.ts` | LatAm neutro strict | Tuteo (`tú`) — magic comment `<!-- voseo-allowed: NO -->` |
| Hardcoded currency `'USD'` | Master-data violation | DTO `currency: str \| None` + `formatMoney(amount, currency)` |
| `session.query(Model)` SA 1.x | SA 2.0 mandatory | `await session.execute(select(Model).where(...))` |
| Pydantic v1 `class Config:` | v2 mandatory | `model_config = ConfigDict(...)` |
| `op.create_table()` Alembic | Not idempotent | Raw SQL `IF NOT EXISTS` |
| `EventBus.publish` legacy | Post 2026-04-29 outbox cutover | `from luana_core_events.outbox.adapter_bus import publish` |
| Brand-local cron decorator (mirror `vitalia/_shared/workers/base.py::idempotent_cron`) | Engine lift 2026-05-20 — deprecated | `from luana_core_platform.workers.cron_envelope import cron_envelope` |
| Brand-local PHI repo base (mirror `vitalia/_shared/repositories/phi_repository.py::PhiRepositoryBase`) | Engine lift 2026-05-20 — deprecated | `from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase` |
| Cross-feature import without Public API | FSD boundaries error | Import via `@/features/X` (Public API barrel) |
| Cross-brand import (`from nicolify...`) | HARD BAN | Lift to engine via promotion proposal `/pm-luana` |
| Modify engine `core/luana-core-*/src/` | Read-only consultation | Escalate `/pm-luana` promotion proposal |
| Modify `vitalia/backend/src/modules/vitalia/agentic/lucas/**` | Already shipped 2026-05-18 | Consumer-only via service imports |
| PHI in URL query params (e.g., `?patient_dni=12345`) | hipaa-lite.md violation | POST body always for PHI lookups |
| PHI in logs without `sanitize_payload` | hipaa-lite.md | Wrap with `sanitize_payload(payload, compliance_level="hipaa_lite")` |
| PHI in UTM payload | this story scope | UTM payload IDs hash + channel slug + timestamp ONLY |
| Use `growth-studio` Nicolify components verbatim | Chris 2026-05-20 ratificó NO growth-studio | Build simple per `02-design-ui-mockup.html` SSoT |
| 4-tier progressive loading caches | Nicolify over-engineering | Single React Query fetch per resource + 5min staleTime |
| 13 hooks dispersed per channel | Nicolify over-engineering | 3-4 hooks per surface (`useChannelMetrics`, `useLucasRecommendations`, `useAttributionMatrix`, `useReferrals`) |
| 8 endpoints per channel | Nicolify over-engineering | 2 unified endpoints + polymorphic response |
| Wizard 8-step OAuth | Nicolify over-engineering | 3 pasos (selector → OAuth redirect → confirm) |
| `make e2e` / `make e2e-smoke` Docker | OOM risk | Native: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke` |
| `docker exec ruff/pytest/tsc/vitest` | Native-first rule | Native: `${WS}/.venv/bin/{ruff,pytest}` + `npx {tsc,vitest}` |
| Skip Storybook stories for components in scope | Slice 1 cement | Per `03-arch-fe.md § 7` — every NEW component has Storybook stories |
| Skip baseline visual regression (Chromatic) | Pixel-invariante mantenimiento Bowtie SVG | T-mk-fe-7 generates baselines + Chris approves pre-merge |
| Hardcoded role check (`if user.role == "marketing"`) | RBAC strict cement | `@require_role(["admin_clinic"])` decorator per hipaa-lite.md |
| Skip dual filter "porque single clinic" | hipaa-lite.md cardinal | ALWAYS dual filter — arch test enforce |
| Use `datetime.utcnow()` | Master-data | `utc_now()` from engine + `DateTime(timezone=True)` |

## 4. Skills + rules to load

### `/dev-team` MUST load these skills + rules during build:

| Trigger surface | Skill | Rule |
|---|---|---|
| `marketing/` backend module | `backend-expert` + `metrics-expert` | `backend-ddd.md`, `backend-quality.md`, `backend-migrations.md`, `tenant-isolation.md`, `architectural-fitness.md`, `anti-duplication.md`, `master-data.md`, `currency-handling.md`, `etl-extraction-contract.md` |
| `connections/{meta_ads,google_ads}/` adapters | `backend-expert` | idem above + Tessl rule `graceful-degradation` |
| `marketing/jobs/` cron jobs | `backend-expert` | idem + engine `cron_envelope` consumption pattern |
| FE `features/marketing/**` | `frontend-expert` | `frontend-fsd.md`, `frontend-quality.md`, `master-data.md`, `currency-handling.md`, `spanish-text.md` |
| E2E specs | `playwright-expert` | `e2e-testing.md` |
| Lucas read-only consumption | `sales-agent-expert` (read-only awareness) | `sales-agent-brand-voice.md`, `anti-duplication.md`, `auditor-downstream-regression.md` |
| Brand overlay | (brand `vitalia/.claude/rules/`) | `vitalia/.claude/rules/hipaa-lite.md`, `vitalia/.claude/rules/README.md` |

### Mandatory rule reads before commit:

- `.claude/rules/tdd-mandatory.md`
- `.claude/rules/anti-duplication.md`
- `.claude/rules/spanish-text.md`
- `.claude/rules/git-safety.md`
- `.claude/rules/parallel-safety.md`
- `vitalia/.claude/rules/hipaa-lite.md`
- `.claude/rules/auditor-downstream-regression.md` (for /auditor scope)

## 5. Anti-patterns specific to /marketing (vitalia-medical-vertical)

| ❌ Pattern | Why specific to vitalia/marketing |
|---|---|
| Use raw Meta/Google currency directly without `currency` field on DTO | Marketing serves LATAM tenants with mixed currencies — DTO must preserve source currency |
| Display `patient.name` in ReferralsWidget leaderboard | PHI exposure — leaderboard shows `referrer_patient_id_hash` only |
| Lucas recommendation includes diagnosis text | Medical guardrails — Lucas growth setter NEVER touches clinical data, only marketing analytics |
| Cross-link `/marketing` to `/inbox` with `patient_id` in URL | PHI in URL — use opaque session token or POST navigation |
| Approve Lucas recommendation that modifies budget without `admin_clinic` role check | RBAC strict — financial actions admin-only |
| Persist Meta OAuth token plaintext in JSON column | pgcrypto symmetric required (`oauth_token_encrypted BYTEA`) |
| 1 cron per channel (e.g., `meta_campaigns_sync_per_campaign`) | Nicolify mistake — collapse to 1 cron per provider per tenant batch |
| Lucas cron calls 30+ LLMs per tenant per day | Cost guard — 5 LLMs max per tenant per day (1 per stage) capped via BudgetGuard |
| Bowtie SVG hardcoded 5 stages slugs in TSX | Use enum `RecommendationStage` from types/ |
| Display `last_known` metrics without "stale" indicator when sync_status='error' | UX broken — show timestamp + warning explicit |

## 6. Story closure gate

Per `.claude/rules/story-closure-gate.md` — when `/dev-team` cierra all GREEN tickets:

1. State `developing → developed` + AUTO-HANDOFF a `/auditor` (default)
2. `/auditor` cierra APPROVED + AUTO-HANDOFF a `/pm-vitalia` merge
3. `/pm-vitalia` escribe `07-merge.md` (5 secciones) + capability update + archive
4. NO escape valve `defer_audit: true` requested for this story (proceed default)
5. WIP cap: this story is `developing ≤ 1` in worktree. Ola 2 parallel `/pipeline` is separate worktree.

## 7. Cross-story coordination

Update `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`:
- § 3 Marketing-shared types: confirm `LucasRecommendation` shape produced by this story (see FE arch § 11)
- § 5 Endpoints API: 10 marketing endpoints listed
- § 6 Domain events: 5 NEW marketing events (LucasRecommendationGenerated/Approved/Rejected/Undone/Expired · ChannelSyncSucceeded/Failed · ReferralConverted)

See `HANDOFF-cross-story-updates.md` for verbatim deltas.

## 8. References

- `03-arch.md`, `03-arch-be.md`, `03-arch-fe.md`, `03-arch-agentic.md` (this story)
- `vitalia/docs/architecture/design-system.md`
- `vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md`
- `vitalia/.claude/rules/hipaa-lite.md`
- `vitalia/config/brand.yaml`
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`
- Parent `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/05-guidelines.md` (heredados verbatim los anti-patterns universales)
