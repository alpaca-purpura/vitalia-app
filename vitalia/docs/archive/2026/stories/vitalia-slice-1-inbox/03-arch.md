# vitalia-slice-1-inbox — Architecture (consolidated index)

> **Status:** ready package draft post replan 2026-05-20 (Chris ratified).
> **Architect run on:** 2026-05-20.
> **Brand:** `vitalia` (Salud + Bienestar · HIPAA-lite · `compliance_level=hipaa_lite`).
> **Scope:** `/inbox` route Slice 1 (Batch 2 cementado): segmented 3-modos + 6 filtros venta consultiva ética + audio IN Whisper STT + imagen IN stub + composer attach + Tools Sheet read-only + Activity Stream sticky + Action Receipts undo 5min + proactive outbound modal.

## 0. Context summary

### Artifact map

| Surface | File | Owner builder | Auditor |
|---|---|---|---|
| Consolidated index | `03-arch.md` (this) | — | — |
| Backend sub-arch | `03-arch-be.md` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| Frontend sub-arch | `03-arch-fe.md` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| Agentic sub-arch | `03-arch-agentic.md` | `builder-agentic` (Opus R23 production) | `auditor-agentic` (Opus) |
| Spec extract | `01-spec-extract.md` | — | — |
| Design UI breakdown | `02-design-ui.md` (+ `02-design-ui-mockup.html` SSoT) | — | — |
| Validators ★ CRITICAL ★ | `04-validators.yaml` | — | — |
| Guidelines | `05-guidelines.md` | — | — |
| Tickets | `06-tickets.yaml` | — | — |
| HANDOFF cross-story | `HANDOFF-cross-story-updates.md` | — | — |

### Surface → builder → auditor mapping

| Surface (paths) | Builder | Auditor | Model |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/inbox/{domain,application,api,infrastructure}/` | `builder-backend` | `auditor-backend` | Sonnet build · Opus audit |
| `vitalia/backend/src/modules/vitalia/crm/{domain,application,api,infrastructure}/` (EXTEND existing scaffold) | `builder-backend` | `auditor-backend` | Sonnet build · Opus audit |
| `vitalia/backend/src/modules/vitalia/connections/{whatsapp,instagram,email,whisper}/` (extend retract + Whisper adapter) | `builder-backend` | `auditor-backend` | Sonnet build · Opus audit |
| `vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py` (NEW) | `builder-agentic` (Opus R23 production) | `auditor-agentic` | Opus 4.7 |
| `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_{dental,estetica,psicologia,fertilidad}.yaml` (extend if not present from shipped story) | `builder-agentic` | `auditor-agentic` | Opus 4.7 |
| `vitalia/backend/src/modules/vitalia/copilot/persistence/models/copilot_trace_event.py` (schema mirror per backend-ddd.md schema-mirror exception) | `builder-backend` | `auditor-backend` | Sonnet OK |
| `vitalia/frontend/src/features/inbox/**` | `builder-frontend` | `auditor-frontend` | Sonnet build · Opus audit |
| `vitalia/frontend/src/features/crm-shared/` + `vitalia/frontend/src/lib/zod-schemas/{lead,conversation}.ts` (NEW shared cross-story) | `builder-frontend` | `auditor-frontend` | Sonnet build · Opus audit |
| `vitalia/frontend/src/features/inbox/**/*.stories.tsx` (Storybook) | `builder-frontend` (R23 production_code=false) | `auditor-frontend` | Sonnet OK |
| `vitalia/frontend/e2e/specs/smoke/inbox.smoke.spec.ts` + `e2e/pages/inbox.page.ts` POM | `builder-frontend` (R23 production_code=false) | `auditor-frontend` | Sonnet OK |
| Eval goldens (`vitalia/backend/tests/agentic_evals/sales_agent/goldens/dental/*.yaml`) — opcional Slice 1 si parent goldens shipped | `builder-agentic` tests scope | `auditor-agentic` | Sonnet OK |

### Skills consulted (decisiones tomadas — pointer-first)

- **`copilot-expert`** — Activity Stream consume `copilot_trace_event` engine (filter by `conversation_id`). Story `vitalia-copilot-tools-impl` shipped 2026-05-19 ya tiene tools instrumentadas → API debería estar disponible. Si gap detectado, escalate `/pm-luana` lift `GET copilot_trace_event by conversation_id` a engine. NUNCA mirror per-brand observability (anti-duplication §0).
- **`sales-agent-expert`** — Adrián compiler v2: voz desde `personality_profiles.system_instruction` slot 5 cache stable. `retract_last_message` tool NUEVO consume `connections.{whatsapp,instagram}.retract_message_id` adapter. §3 NO se toca: Closer Studio API+WS, SmartBufferService, OutputManager chunking, tool_call_dedup, model_pricing_snapshot. Medical guardrails `medical_safety_no_diagnosis` + `medical_safety_no_prescription` aplicados via ComplianceService (engine `core/luana-core-compliance/`).
- **`backend-expert`** — DDD Inside-Out strict. Dual filter `tenant_id` + `clinic_id` cardinal (per `vitalia/.claude/rules/hipaa-lite.md`). Repositorios consumen `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` con `scope_field="clinic_id"`. Lead repo SIN dual filter (Lead NO es PHI per existing `vitalia/backend/src/modules/vitalia/crm/domain/lead.py`). Audit log sync write pre-response. Conversation table mira `vitalia_conversations`. Migrations idempotentes raw SQL `IF NOT EXISTS`.
- **`frontend-expert`** — FSD-Lite. Server-First (RSC default · `"use client"` solo nodos hoja). `fetchClient` auto-inject `X-Tenant-ID` + `X-Clinic-ID`. nuqs URL state SSoT. NO cross-feature import sin Public API. Tokens-only HEX en CSS vars `globals.css` (arch fitness `test_no_hardcoded_colors`). Reuso: fork físico desde `nicolify/frontend/src/features/{crm-hub,closer-studio,copilot}/` con retoken.
- **`metrics-expert`** — NO toca analytics ETL. Activity Stream del inbox NO es analytics canal — es trace-event sourced.
- **`brand-expert`** — Voice style chip `🟢 Estilo: consultivo · sin presión` consume `brand_personality.archetype` + reads `personality_profiles.system_instruction`. Read-only Slice 1. CTA "Configurar →" link a wizard (Story 11 wizard onboarding ya shipped).
- **`tessl__langgraph`** — Adrián turn ya implementado en `core/luana-core-sales-agent/`. Inbox NO añade nodos LangGraph nuevos. Stream modes: SSE v2 `block_append` para action receipts + activity stream events (NO `text_chunk` legacy).
- **`tessl__graceful-degradation`** — Whisper STT timeout 30s · fallback "no se entendió bien" (per SC-02). WhatsApp Cloud Media API + IG Graph timeout 15s. Retract endpoint timeout 5s con fallback "marcar como erróneo".
- **`playwright-expert`** — E2E smoke `vitalia/frontend/e2e/specs/smoke/inbox.smoke.spec.ts` + POM `e2e/pages/inbox.page.ts`. Clerk auth fixture (dr.demo · recepcion · admin pre-seedeados). Port 3002 dev. Storage state `vitalia/frontend/playwright/.clerk/user.json`.

### CONTEXT-BRIEF source

Self-explored Path B (no Haiku context-builder pre-cocked CONTEXT-BRIEF.md). Steps ejecutados:
- Step 0: date capture 2026-05-20
- Step 0.5: `git rev-parse --show-toplevel` → `/home/chalreme/Proyectos/luana-vitalia` · branch `wip/vitalia`
- Step 1: read in order — parent archived `01-spec.md` § Ruta /inbox + `03-arch*.md` + `06-tickets.yaml` § inbox section · HANDOFF cross-story doc · vitalia config `brand.yaml` · CRM existing scaffold · sales_agent shipped tools · core CRM engine
- Step 3 cross-module audit: engine `core/luana-core-{platform,crm,channels,observability}/` (ALL EXTEND, ZERO mirror)
- Cross-brand mirror scan: nicolify/closer-studio + nicolify/crm-hub + nicolify/copilot — REUSE adapter (fork físico Slice 1) ratified parent ADR-vitalia-001-shared-vs-fork.md

### capability YAML files affected (post-merge updates required per pm-redesign-2026-05)

Story merge will trigger updates to:
- `vitalia/docs/product/capabilities/inbox/conversational-segmented.yaml` (NEW — status: live)
- `vitalia/docs/product/modules/inbox.md` (NEW — SSoT funcional viva)
- `vitalia/docs/product/capabilities/inbox/multimedia-audio-image.yaml` (NEW — status: live for audio · stub for image)
- `vitalia/docs/product/capabilities/inbox/tools-sheet-read-only.yaml` (NEW — status: live)
- `vitalia/docs/product/capabilities/inbox/activity-stream-transparency.yaml` (NEW — status: live)
- `vitalia/docs/product/capabilities/inbox/action-receipts-undo.yaml` (NEW — status: live)
- `vitalia/docs/product/capabilities/inbox/proactive-outbound.yaml` (NEW — status: live)

### Architecture fitness gates que MUST keep passing

Existing arch gates (cementados Story 11 + slice-1-infra):
- `vitalia/backend/tests/architecture/`:
  - `test_phi_dual_filter.py` — tenant_id+clinic_id dual filter cardinal
  - `test_no_cross_brand_imports.py` — anti-duplication enforce
  - `test_response_model_required.py` — PII allowlist per `hipaa-lite.md`
  - `test_migrations_idempotent.py` — `IF NOT EXISTS` raw SQL
  - `test_extension_sdk_registration.py` — extensions.py registers via EP only
  - `test_audit_log_sync_write.py` — PHI mutations write audit_log row pre-response
  - `test_compound_scope_repository_consumed.py` — repos heredan engine `CompoundScopeRepositoryBase`
- `vitalia/frontend/src/__tests__/architecture/`:
  - `test_no_hardcoded_colors.test.ts` — only CSS vars from globals.css
  - `test_fsd_boundaries.test.ts`
  - `test_no_cross_feature_imports.test.ts`
  - `test_server_first.test.ts`
  - `test_phi_pii_components_used.test.ts`
  - `test_no_voseo_in_copy.test.ts`

NEW arch gates (Slice 1 inbox-specific):
- `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_strings_inbox.test.ts` — grep `features/inbox/.*\.tsx` por strings hardcoded > 3 chars (allowlist whitelisted en arch test)

Allowlist shrinkage expected: zero new entries — todas las violaciones fix-forward.

## 1. Top-level architecture (cross-surface contract)

```
User (Owner P1 + P2) ─ HTTPS + Clerk JWT + X-Tenant-ID + X-Clinic-ID
  │
  ▼
FRONTEND vitalia (Next.js 16 App Router · FSD-Lite) port 3002
  Shell · Sidebar 240px · TopBar · Main · Copilot rail 80px idle
  /inbox route:
    InboxLayout · ConvList 320px · Thread (flex) · ContactSidebar 280 toggle
    URL state: nuqs SSoT (replace intra-state, push inter-route P1)
    React Query + RHF+Zod + Tailwind + Shadcn
  │ REST + Webhooks IN (WhatsApp/IG/email)
  ▼
BACKEND vitalia (FastAPI async · DDD Inside-Out) port 8002
  Routes /api/v1/vitalia/{inbox,crm,connections,iam}/...
  Dual filter tenant_id + clinic_id en TODA query PHI
  Audit log sync write pre-response
  Extension SDK already mounted (Story 11)
  │
  ▼ AGENTIC (Adrián engine ya shipped)
core/luana-core-sales-agent/ · core/luana-core-copilot/ · core/luana-core-observability/
External: Whisper STT · WhatsApp Cloud Media · IG Graph · email MIME
  │
  ▼
Postgres (shared 5435 · DB vitalia_dev) · Redis db=1 · Qdrant `vitalia_marketing_kb`
```

## 2. Cross-cutting design principles (consumed by all 3 sub-archs)

Heredados del parent — referencia rápida:

1. **Tenant + Clinic dual filter** cardinal HIPAA-lite (`vitalia/.claude/rules/hipaa-lite.md`)
2. **Audit log sync write** pre-response · `vitalia.audit_log` table
3. **PII sanitization in traces** via `core/luana-core-observability/recording/sanitization.py` (NEVER mirror)
4. **Encryption at-rest** via `pgcrypto` (KEK rotada anualmente · `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py`)
5. **RBAC strict** medical roles · `@require_phi_access(roles=["doctor","nurse","admin_clinic"])`
6. **Channel guards** ComplianceService bloquea PHI por canales no-encriptados
7. **Currency policy LatAm** — `currency: str | None` en monetary DTOs · NO hardcoded USD
8. **Spanish neutro LatAm strict** UI chrome (arch fitness `test_no_voseo_in_copy.test.ts`) · sales_agent voice exemption
9. **Master data UTC + timezone tenant** · `DateTime(timezone=True)` mandatory
10. **Idempotency on writes** · `Idempotency-Key` header → `core/luana-core-idempotency/`
11. **No cross-brand mirror** (anti-duplication) · pattern repetido 2 brands → STOP, escalate `/pm-luana` lift

## 3. Existing systems audit (NO NEW LAYER per `.claude/rules/anti-duplication.md`)

### Source of evidence
- [x] Self-run greps (Path B fallback — no CONTEXT-BRIEF.md found)
- [x] Engine package read-only consultation
- [x] Cross-brand mirror scan ∀ otra brand activa

### Audit cross-module executed

```bash
WS=$(git rev-parse --show-toplevel)

# 1. Engine consultation (CRM + channels + observability + compound_scope + cron_envelope)
ls ${WS}/core/luana-core-crm/src/luana_core_crm/{domain,application,api}/
ls ${WS}/core/luana-core-channels/src/luana_core_channels/
ls ${WS}/core/luana-core-observability/src/luana_core_observability/{recording,cost,persistence,channels}/
ls ${WS}/core/luana-core-platform/src/luana_core_platform/{repositories,workers}/

# 2. Vitalia existing crm scaffold (Story 11 cement) — EXTEND
find ${WS}/vitalia/backend/src/modules/vitalia/crm -type f -name "*.py"
# → lead.py + patient.py domain + lead_repository.py + patient_repository.py + services + dto + router.py
# Conclusion: EXTEND existing crm scaffold. Add conversation.py + message.py + activity_event.py + action_receipt.py to crm/domain (or new inbox/ submodule per scope).

# 3. Sales_agent shipped tools (vitalia-copilot-tools-impl) — REUSE
find ${WS}/vitalia/backend/src/modules/vitalia/sales_agent/tools -name "*.py"
# → payment_link.py, reschedule_appointment.py, screening_questions.py
# NEW Slice 1: retract_last_message.py (consume connections.{whatsapp,instagram}.retract_message_id)

# 4. Cross-brand mirror scan (CRITICAL)
for OB in nicolify comunify lupulo; do
  find ${WS}/$OB/backend/src/modules/$OB -name "inbox" -type d 2>/dev/null
  find ${WS}/$OB/frontend/src/features/{crm-hub,closer-studio,copilot} -type d 2>/dev/null | head
done
# → nicolify/frontend/src/features/{crm-hub,closer-studio,copilot} EXIST — fork físico Slice 1 ratificado ADR-vitalia-001
# → backend NO mirror — vitalia inbox tables son brand-local (vitalia_conversations, etc.)
```

### Sistemas existentes encontrados — decisión por sistema (EXTEND > REPLACE > NEW)

| Sistema | Path | Decision |
|---|---|---|
| Engine `luana_core_crm` (lead, customer, scoring) | `core/luana-core-crm/src/luana_core_crm/domain/{lead,customer}.py` | **CONSULT only Slice 1** — vitalia CRM mantiene su propio Lead (ya cementado, NO PHI per existing) + nueva Conversation/Message en vitalia. Engine domain entities serán LIFTed Slice 2 cuando 2do brand opt-in (lift candidate documented). |
| Engine `luana_core_channels` (format_for_channel, intent_detector) | `core/luana-core-channels/src/luana_core_channels/` | **CONSUME direct** — used for outbound message format dispatch + intent_detector (WA quick replies, IG buttons). Adapter Whisper STT NEW vive en `vitalia/backend/src/modules/vitalia/connections/whisper/` per existing scaffold pattern (no engine modify). |
| Engine `luana_core_observability` (turn_envelope, callback_handler, sanitization, cost_recorder) | `core/luana-core-observability/src/luana_core_observability/` | **EXTEND via heredancia** (NEVER mirror) — Activity Stream consume `copilot_trace_event` filter by conversation_id. Sales_agent ya consume engine recording vía SalesAgentObservabilityContext shipped. |
| Engine `luana_core_platform.repositories.CompoundScopeRepositoryBase` | `core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py` | **CONSUME direct** — inbox repos heredan con `scope_field="clinic_id"` (PHI conversations + messages + activity_events + action_receipts). Replaces local `vitalia/_shared/repositories/phi_repository.PhiRepositoryBase` (migrated per HANDOFF § 2 pre-flight gate). |
| Engine `luana_core_platform.workers.cron_envelope` | `core/luana-core-platform/src/luana_core_platform/workers/cron_envelope.py` | **CONSUME direct** — IF inbox introduces crons (`cleanup_expired_action_receipts_5min_sweep` opcional Slice 1). |
| Engine `luana_core_sales_agent` runtime (Adrián turn pipeline) | `core/luana-core-sales-agent/` | **CONSUME direct** — Adrián tools registered via `vitalia/backend/src/modules/vitalia/extensions.py::register_all` (Story 11). Inbox no toca engine. |
| Engine `luana_core_compliance.ComplianceService` (channel guards + medical guardrails) | `core/luana-core-compliance/` | **CONSUME direct** — bloquea PHI por WhatsApp tier free + SMS + email plaintext. Medical guardrails configurados en `vitalia/config/brand.yaml::compliance_level=hipaa_lite`. |
| Nicolify `closer-studio/components/inbox/` FE | `nicolify/frontend/src/features/closer-studio/components/inbox/` | **REUSE adapter (fork físico Slice 1)** — copy components into `vitalia/frontend/src/features/inbox/components/` with token adapter (Tailwind classes amber→vitalia-azul-marino, violeta→vitalia-purpura) + PHI wrappers added. Shared package candidate Slice 2 cuando 2do brand opt-in. ADR-vitalia-001 cementa decisión. |
| Nicolify `crm-hub/` FE | `nicolify/frontend/src/features/crm-hub/` | **REUSE adapter parcial** — components ContactDetailContent + LifecycleStageChip + ContactFiltersPanel sirven como referencia para ContactSidebar PHI-aware + FilterChips Vitalia. |
| Nicolify `copilot/components/composer/VoiceOverlay.tsx` | `nicolify/frontend/src/features/copilot/components/composer/` | **REUSE direct** for composer voice record button (MediaRecorder API) — copy file into `vitalia/frontend/src/features/inbox/components/ComposerVoiceButton.tsx` with vitalia retoken. |

### Decision summary

**ALL EXTEND or CONSUME — zero NEW infrastructure layers.** Cross-brand mirror risk: zero backend (vitalia tables son brand-local · NO replicar nicolify backend). FE fork físico ratificado ADR-vitalia-001 (Slice 2 lift candidate).

## 4. Side stories blockers

**NONE.** Esta sub-story es auto-contenida (per checkpoint `blocker_dependencies: []`). Side stories que Olas 2+3 dependen (`vitalia-payment-adapter-mvp`, `vitalia-fiscal-emission-pe`) NO afectan a inbox Slice 1.

Pre-flight gates (heredados de HANDOFF § 2):
- Clerk testing token + webhook secret configurado
- 3 test users seedeados (dr.demo · recepcion · admin)
- 3 tenants fixture (Aurora AR · Mindful CL · Sanaré MX) — tests usan Sanaré MX
- Playwright storage state generado
- Smoke 23 specs GREEN local + live
- Promotion proposal `2026-05-20-core-platform-extensions-slice-1` migrated (CompoundScopeRepositoryBase + cron_envelope)

## 5. Performance budgets (Slice 1)

| Metric | Budget |
|---|---|
| LCP `/inbox` | < 2.5s |
| INP | < 200ms |
| CLS | < 0.1 |
| ConversationList | virtualized si > 50 items |
| ActivityStream | poll 5s when expanded, NO polling collapsed |
| Whisper STT timeout | 30s · fallback "no se entendió bien" + auto-switch handler_mode=human |
| Retract endpoint timeout | 5s · fallback "marcar como erróneo" + audit log |
| LLM cost Adrián per turn | ≤ $0.05 USD (engine ya optimizado) |
| Cache hit rate Adrián system prompt | ≥ 60% (slots 1-5 cacheable cross-tenant + per-tenant) |

## 6. Observability + tracing

OpenTelemetry spans NEW Slice 1 (additive — engine spans ya emitidos por Adrián+observability shipped):

- `vitalia.inbox.list_conversations` (API endpoint)
- `vitalia.inbox.send_message` (incluye dual-write trace_event + audit_log)
- `vitalia.inbox.retract_message` (consume `connections.{X}.retract_message_id`)
- `vitalia.inbox.transcribe_audio` (Whisper STT wrapper · timeout 30s)
- `vitalia.inbox.set_mode` (mode change · invalida React Query)
- `vitalia.inbox.pause_adrian` (60min pause)
- `vitalia.inbox.activity_stream_read` (query copilot_trace_event filter by conv_id)
- `vitalia.inbox.proactive_outbound_send`

Sentry alerts:
- Whisper STT failure rate > 30% / 5min → warn
- Retract endpoint failure rate > 10% / 5min → page (compliance risk)
- WhatsApp Cloud API rate limit hit → throttle + degrade
- Activity Stream read p95 > 800ms → warn (DB query indexing issue)

## 7. Open questions (resolutions cementadas)

| # | Question | Resolution (this arch) |
|---|---|---|
| 1 | Fork físico vs shared package | Fork físico Slice 1 — ratificado parent ADR-vitalia-001-shared-vs-fork.md. Shared package candidate Slice 2 cuando 2do brand opt-in medical. |
| 2 | Engine CRM lift Lead/Conversation | Slice 2 retro — vitalia mantiene su Lead local (ya cementado). Engine `luana_core_crm.domain.lead` queda como engine SSoT pero NO consumido directly Slice 1 (DDD purity). |
| 3 | Activity Stream API exposure | T-inbox-be-{n} ticket añade endpoint `GET /api/v1/vitalia/inbox/conversations/{id}/activity-stream` que consume `copilot_trace_event` filter by conversation_id. Si engine API gap detectado, escalate `/pm-luana` lift Slice 2. |
| 4 | Whisper STT location (brand vs engine) | Brand-local `vitalia/backend/src/modules/vitalia/connections/whisper/adapter.py`. Lift candidate Slice 2 cuando 2do brand opt-in audio IN (likely fitflow voice notes, comunify creator audio messages). |
| 5 | ProactiveOutboundModal templates source | 5 templates Meta-approved hardcoded en `vitalia/backend/src/modules/vitalia/inbox/application/services/proactive_outbound_service.py` Slice 1. Templates registry → Slice 2 (lift `core/luana-core-channels/templates/`). |
| 6 | Concurrent edit conflict resolution (SC-03) | Optimistic Concurrency Control via `updated_at` timestamp + `If-Match` header on POST mode + revert endpoints. 409 Conflict returned para mutation perdedora. Cliente refresca via React Query invalidate. |

## 8. Research notes (DATE-AWARE — accessed 2026-05-20)

| Source | Version | Accessed | Key takeaway |
|---|---|---|---|
| LangGraph 2.0 stream modes | langgraph 0.6+ | 2026-05-20 | Engine Adrián ya shipped — inbox solo emite SSE v2 `block_append` para action receipts. NO `text_chunk` legacy (per Sales Agent S8 cement). |
| Anthropic prompt caching slot architecture | API 2024-10-22 ext | 2026-05-20 | Engine sales-agent compiler v2 cementado (Sales Agent S3 + S11A). Slot order: System role → Domain → Tools → Persona → BRAND_VOICE (cache_control marker) → Conversation (NOT cached). Inbox NO modifica prompt cache (engine territory). |
| Next.js 16 App Router parallel routes | 16.x | 2026-05-20 | nuqs SSoT URL state · `useSearchParams` + `useRouter().push/replace`. Server Components default — `"use client"` solo nodos hoja con state/handlers. |
| nuqs URL state parsers | nuqs latest | 2026-05-20 | `parseAsString` + `parseAsStringEnum` + `parseAsBoolean` type-safe. `history: 'replace'` para sub-state intra-route. `useQueryStates(SCHEMA, { history: 'replace' })` para multi-param atomic update. |
| Pydantic v2 ConfigDict | 2.10+ | 2026-05-20 | `model_config = ConfigDict(from_attributes=True)` mandatory. No inner `class Config`. Explicit types. |
| SQLAlchemy 2.0 async + mapped_column | 2.0.30+ | 2026-05-20 | `mapped_column()` syntax · `select(Model).where(...)` · async-first · `AsyncSession`. NEVER `Column()` or `session.query()`. |
| Whisper STT (OpenAI API) | API 2025-04 | 2026-05-20 | `audio/transcriptions` endpoint · `response_format=verbose_json` retorna `confidence` per segment. Confidence aggregate < 0.5 → trigger fallback "no se entendió". Cost ~$0.006/min. |
| WhatsApp Cloud API · retract message | Cloud API 2025 | 2026-05-20 | `DELETE /v18.0/{phone-number-id}/messages/{message_id}` dentro 5min window. 6+ min → API returns 400. Fallback: marcar como erróneo en audit log sin retract real (mantiene compliance trail). |
| Meta IG Graph · retract DM | Graph API 2025 | 2026-05-20 | IG retract similar 5min window. Algunos canales (email) NO soportan retract — UI muestra "marcar como erróneo" directo. |
| Playwright + Chromatic | Playwright 1.50+ · Chromatic | 2026-05-20 | E2E smoke `--project=smoke` filtra specs `.smoke.spec.ts`. Storage state Clerk via auth.fixture. Chromatic snapshot per breakpoint (mobile 768 · tablet 1024 · desktop 1440). |
| WCAG 2.1 AA | WAI-ARIA 1.2 | 2026-05-20 | Segmented control = radiogroup pattern · aria-live polite para countdown · keyboard nav Tab order. |

**Knowledge cutoff disclosure:** Topics shipped post-cutoff Jan 2026 — multibrand reorg 2026-05-15, vitalia-copilot-tools-impl 2026-05-19, slice-1-infra-cross-cutting 2026-05-18 — verificados vía codebase greps al day-of (2026-05-20).

## 9. Referencias

- `01-spec-extract.md` (recorte parent /inbox)
- `02-design-ui.md` + `02-design-ui-mockup.html` (SSoT visual)
- `03-arch-be.md` · `03-arch-fe.md` · `03-arch-agentic.md` (sub-archs)
- `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/01-spec.md` (mega-spec parent)
- `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/03-arch*.md` (mega-arq parent)
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` (HANDOFF cross-story)
- `vitalia/.claude/rules/hipaa-lite.md`
- `vitalia/config/brand.yaml` (compliance_level=hipaa_lite + feature flags)
- `core/luana-core-{crm,channels,observability,platform,sales-agent,copilot,compliance}/src/` (engine READ-ONLY)
- `nicolify/frontend/src/features/{crm-hub,closer-studio,copilot}/` (REUSE adapter source)
- `.claude/rules/{tenant-isolation,backend-ddd,frontend-fsd,architectural-fitness,anti-duplication,spanish-text,tdd-mandatory,master-data,currency-handling,auditor-downstream-regression,hotfix-repro-mandatory,story-closure-gate}.md`

---

**Next sub-archs:** `03-arch-be.md`, `03-arch-fe.md`, `03-arch-agentic.md`.
