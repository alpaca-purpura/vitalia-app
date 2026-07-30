# vitalia-ux-discovery — Architecture (consolidated index)

> **Status:** ready package draft · architect run on **2026-05-17** (Opus 4.7) · spawned by `/architect vitalia` post v1 spec ratificada 2026-05-17.
>
> **State transition:** refined → ready (target — al cerrar este package).
>
> **Brand:** `vitalia` (Salud + Bienestar · HIPAA-lite · compliance_level=hipaa_lite).
>
> **Scope:** Slice 1 MVP — 6 rutas P1 (`/inbox` · `/pipeline` · `/agenda` · `/fidelizacion` · `/marketing` + Wizard Brand Studio onboarding agentic) + cross-cutting infra + 5 Extension SDK registries Vitalia + 11 tablas nuevas + 11 cron jobs + ~50 endpoints + agentic stack (Adrián sales_agent · Lucas growth setter · Valeria copilot · screening clínico).
>
> **Mega-story split recommendation:** see § 9. This story is too large for a single autonomous build (>10 tickets natural split). Recommended split into 7 sub-stories (6 ruta-scoped + 1 cross-cutting infra) — see 06-tickets.yaml § Recommendation.

## 0. Context summary

### Artifact map

| Surface | File | Owner builder | Auditor |
|---|---|---|---|
| Consolidated index | `03-arch.md` (this file) | — | — |
| Backend sub-arch (DDD + tables + endpoints + cron + Extension SDK registries) | `03-arch-be.md` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| Frontend sub-arch (FSD-Lite + 6 routes + components + Storybook + arch fitness) | `03-arch-fe.md` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| Agentic sub-arch (LangGraph state · supervisor · tools · cache slots · evals · medical guardrails) | `03-arch-agentic.md` | `builder-agentic` (Opus 4.7 R23 production) | `auditor-agentic` (Opus 4.7) |
| Validators ★ CRITICAL ★ | `04-validators.yaml` | — | — |
| Guidelines (patterns required/forbidden + files in scope + skills/rules) | `05-guidelines.md` | — | — |
| Tickets (atomic work units + DAG + blockers) | `06-tickets.yaml` | — | — |
| Engine lift candidates (Slice 2 promotion candidates retro doc for `/pm-luana`) | `delta-arch-notes.md` | — | `/pm-luana` |

### Surface → builder → auditor mapping (PM `/dev-team` consumes to spawn correct agents)

| Surface (paths) | Builder | Auditor | Model |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/{inbox,pipeline,agenda,fidelizacion,marketing,onboarding,connections,iam,crm,compliance}/{domain,application,api,infrastructure}/` | `builder-backend` | `auditor-backend` | Sonnet build · Opus audit |
| `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/{tools,extractors,workflows,kb,personas,goldens}/` | `builder-agentic` | `auditor-agentic` | **Opus 4.7 R23 production_code=true** |
| `vitalia/backend/src/modules/vitalia/extensions.py::register_all` (EP-1..EP-18 + 5 NEW EPs Vitalia) | `builder-agentic` (EP wiring is agentic-adjacent) | `auditor-agentic` | Opus 4.7 |
| `vitalia/frontend/src/features/{inbox,pipeline,agenda,fidelizacion,marketing,onboarding}/` + `vitalia/frontend/src/components/shared/{agents,phi,contact-sidebar,nps}/` | `builder-frontend` | `auditor-frontend` | Sonnet build · Opus audit |
| Schema mirror models en `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/persistence/models/` (DDL ripple from engine migration) | `builder-backend` (per `.claude/rules/backend-ddd.md` schema-mirror exception) | `auditor-backend` | Sonnet OK |
| Storybook stories (tests/docs sobre agentic UI) — `vitalia/frontend/src/**/*.stories.tsx` | `builder-frontend` (Storybook = docs sobre agentic, R23 production_code=false) | `auditor-frontend` | Sonnet OK |
| Eval goldens (`vitalia/backend/tests/agentic_evals/sales_agent/goldens/**`, `tests/agentic_evals/copilot/goldens/**`) | `builder-agentic` tests scope (R23 production_code=false) | `auditor-agentic` | Sonnet OK |

### Skills consulted (one-liner decisions taken)

- **`copilot-expert`** — Valeria copilot rail derecho 80px idle · brand-extension surface `vitalia/backend/src/modules/vitalia/copilot/` consume engine `core/luana-core-copilot/`. Wizard onboarding tools (`extract_tenant_context`, `confirm_slot`, `simulate_personality`, `complete_onboarding`) registrados vía EP-3. Observability via `copilot_trace_event` + `copilot_llm_call` standard tier Kimi/DeepSeek. **CRITICAL CONSULT (anti-duplication §0):** observability/cost/pricing/turn_envelope/callback_handler patterns viven en `core/luana-core-observability/` (cross-agent shared). NUNCA mirror per-brand. Decisión: vitalia consume engine via heredancia + brand extension overlay solo via `extensions.py::register_all`.
- **`sales-agent-expert`** — Adrián sales_agent closer · brand-extension surface `vitalia/backend/src/modules/vitalia/sales_agent/` consume engine `core/luana-core-sales-agent/`. **§3 NO se toca:** Closer Studio API+WS, SmartBufferService, OutputManager chunking, enrollment_*, agent_state_checkpoints, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup. Compiler v2 voz Adrián desde `personality_profiles.system_instruction` slot 5 cache stable (NO inject tenant_name mid-block). Eval goldens Vitalia 12 escenarios (3 dental + 3 estética + 3 psicología + 3 fertilidad) per persona Owner with voice_fidelity grader. Medical guardrails: `medical_safety_no_diagnosis`, `medical_safety_no_prescription`, `medical_disclaimer_required`, `prompt_injection_block` (per `vitalia/config/brand.yaml`). LiteLLM Proxy canonical (PI-12 S1 T-5 cement post 2026-05-06 — NO direct provider adapters).
- **`brand-expert`** — Wizard onboarding Slice 1 toca `core/luana-core-brand-studio/` engine voice infra: `style_analyzer` LangGraph agent + `personality_service.compile_partial/simulate` + `voice_fidelity/grader` + `brand_data_adapter` (extend Vitalia for medical vertical context). PersonalityProfile 3-pilar (dimensions + linguistic_patterns + sample_exchanges) — NO solo dimensions. Decisión: engine direct consume (no fork) — wizard llama endpoints engine vía port `shared/links/ports/brand_studio.py` (NEW lift candidate). Brand Studio enabled_sections per Slice 1: `[identity, contact, team, testimonials]` (per `vitalia/config/brand.yaml`).
- **`offer-expert`** — preset_pack `medical_services_v1` (per `vitalia/config/brand.yaml`). Slice 1 stub fields: `offers.{requires_multi_session, sessions_expected, gap_alert_days, maintenance_schedule, maintenance_custom_days}`. Field contract reactive — copilot lee runtime, no code change required cuando se agregan fields nuevos. NO modificar engine `core/luana-core-offer-studio/` directly — agregar fields como overrides en `vitalia/backend/src/modules/vitalia/offer/extensions.py` via Extension SDK EP-2.
- **`offer-type-preset-expert`** — `medical_services_v1` preset pack registrado en `vitalia/backend/src/modules/vitalia/offer/presets/medical_services_v1.py` via EP-2. NO modify engine catalog directamente. Si Slice 2 requiere preset adjustments — Chris ratifica + `_CATALOG_VERSION` bump engine via `/pm-luana` promotion.
- **`metrics-expert`** — `/marketing` consume engine `core/luana-core-analytics-engine/` (stage services SSoT). Brand-config en `vitalia/backend/src/modules/vitalia/analytics/extensions.py` registra `enabled_metrics` + `channel_groups` para salud LATAM. UTM tracking lead→origin para `AttributionMatrixWidget` Stage Reserva (4 origins: `sales_agent`, `walk_in`, `phone_manual`, `proactive_outbound`). Bowtie 5 stages mapeo a engine funnel_stage existing enum. NO crear stage_service mirror per-brand.
- **`backend-expert`** — DDD Inside-Out strict en cada módulo brand. Dual filter `tenant_id` + `clinic_id` cardinal (per `vitalia/.claude/rules/hipaa-lite.md`). Migrations idempotentes `IF NOT EXISTS` raw SQL. PHI columns encrypted via `pgcrypto`. Audit log sync write pre-response. Cross-module via ports (`shared/links/ports/...`), NUNCA cross-module import directo.
- **`frontend-expert`** — FSD-Lite per brand (`vitalia/frontend/src/{app,features,components,lib,hooks}/`). Server-First default (RSC), `"use client"` solo en nodos hoja con state/handlers. `fetchClient` auto-inyecta `X-Tenant-ID` (no hardcode). nuqs URL state SSoT. NO cross-feature import sin port `index.ts` (Public API). Tokens-only HEX literales en CSS variables (`vitalia/frontend/src/app/globals.css` per design-system.md § 4) — arch fitness `test_no_hardcoded_colors.ts` enforces.
- **`tessl__langgraph`** — LangGraph 2.0 patterns: `AsyncPostgresSaver` checkpointer (NO `MemorySaver`), 6 stream modes (`updates` for production UI, `messages` for token streaming chat UX), supervisor topology con `langgraph_supervisor.create_supervisor` para wizard onboarding multi-tool routing.
- **`tessl__deepagents`** — deepagents subagents via `task` tool con `SubAgentMiddleware.allowed_keys_to_subagent` / `allowed_keys_from_subagent` para isolación state. Aplicable a wizard onboarding (subagent: URL/doc extractor) — opcional Slice 1, defer Slice 2 si simpler ReAct alcanza.
- **`tessl__graceful-degradation`** — External calls (Whisper STT, Meta Ads API, Google Ads API, Nubefact PE, WhatsApp Business API, Mercado Pago) wrap timeout+fallback. Soft-fail patterns per provider.
- **`playwright-expert`** — E2E smoke per ruta P1 + wizard onboarding · Clerk auth fixture · POMs `vitalia/frontend/e2e/pages/`. Visual regression Playwright + Chromatic bowtie SVG pixel-invariante. Port 3002 vitalia frontend.

### CONTEXT-BRIEF source

Self-explored Path B (no Haiku context-builder pre-cocked CONTEXT-BRIEF.md found en story folder). Manually executed:
- Step 0: date capture 2026-05-17
- Step 0.5: workspace + brand resolved (`vitalia`)
- Step 1: read PRIORITY READ in order — `checkpoint.md` · `01-spec.md §Slice 1 cut + §Components mapping + §Handoff` · `design-system.md` · `hipaa-lite.md` · `brand.yaml` · existing `extensions.py` brand scaffold (Story 11 cement)
- Step 4 cross-module audit: engine `core/luana-core-*/` consultation (read-only) confirmed engine voice infra `core/luana-core-brand-studio/` exists + observability `core/luana-core-observability/` shared abstractions inventory matches `.claude/rules/anti-duplication.md` SSoT table

### capability YAML files affected (post-merge updates required per pm-redesign-2026-05 paradigma)

Story merge will trigger updates to:
- `vitalia/docs/product/capabilities/inbox/conversational-segmented.yaml` (NEW)
- `vitalia/docs/product/capabilities/pipeline/consultive-funnel-6stages.yaml` (NEW)
- `vitalia/docs/product/capabilities/agenda/4origins-3layers-cobro.yaml` (NEW)
- `vitalia/docs/product/capabilities/fidelizacion/4patterns-reengagement.yaml` (NEW)
- `vitalia/docs/product/capabilities/marketing/bowtie-5stages-lucas.yaml` (NEW)
- `vitalia/docs/product/capabilities/onboarding/wizard-agentic-voz-clonada.yaml` (NEW)
- `vitalia/docs/product/modules/{inbox,pipeline,agenda,fidelizacion,marketing,onboarding}.md` (NEW SSoT funcional viva)

### Architecture fitness gates that must keep passing

Engine + brand fitness suites:
- `core/luana-core-*/tests/architecture/` (engine packages — read-only consultation, no modifications)
- `vitalia/backend/tests/architecture/`:
  - `test_phi_dual_filter.py` — tenant_id+clinic_id dual filter cardinal
  - `test_no_cross_brand_imports.py` — anti-duplication enforce
  - `test_no_legacy_paths.py` — no `backend/src/shared/` (root) imports
  - `test_response_model_required.py` — PII allowlist per `hipaa-lite.md`
  - `test_migrations_idempotent.py` — `IF NOT EXISTS` raw SQL
  - `test_extension_sdk_registration.py` — vitalia extensions.py registers via EP only
  - `test_audit_log_sync_write.py` — PHI mutations write audit_log row pre-response (NEW Slice 1)
  - `test_pgcrypto_phi_columns.py` — PHI columns use pgcrypto symmetric encryption (NEW Slice 1)
- `vitalia/frontend/src/__tests__/architecture/`:
  - `test_no_hardcoded_colors.test.ts` — only design-system.md CSS vars allowed (HEX literales forbidden outside `globals.css`)
  - `test_no_hardcoded_strings.test.ts` — user-facing strings live in `<feature>/copy.ts` (NEW Slice 1)
  - `test_fsd_boundaries.test.ts` — boundaries error per `.claude/rules/frontend-fsd.md`
  - `test_no_cross_feature_imports.test.ts` — Public API via `index.ts` only
  - `test_server_first.test.ts` — RSC default, `"use client"` only on leaf nodes
  - `test_phi_pii_components_used.test.ts` — `<PiiMaskedSpan>`/`<RequireRole>`/`<AuditedSection>` used for all PHI surfaces (NEW Slice 1)
  - `test_no_voseo_in_copy.test.ts` — voseo glosario excluded from copy.ts files (NEW Slice 1)
  - `test_page_padding.test.ts` — design tokens consistency

Allowlist shrinkage expected: zero new allowlist entries — all violations fix-forward.

## 1. Top-level architecture (cross-surface contract)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          USER (Owner clínica P1 + P2)                            │
│                          Modo móvil + desktop                                    │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │ HTTPS + Clerk JWT + X-Tenant-ID + X-Clinic-ID
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   FRONTEND vitalia (Next.js 16 App Router · FSD-Lite)            │
│                   Port 3002 (dev) · Server-First RSC default                     │
│ ┌──────────────────────────────────────────────────────────────────────────────┐│
│ │  Shell — TopBar + Sidebar 240px + Main + Copilot rail 80px idle/460px chat   ││
│ │  ╔ Wizard onboarding (chat-LEFT 50/50) ──→ App daily (rail derecho) ╗         ││
│ │  Routes: /inbox · /pipeline · /agenda · /fidelizacion · /marketing            ││
│ │  URL state: nuqs SSoT (push inter-route, replace intra-state)                 ││
│ │  React Query (TanStack v5) data hooks · RHF+Zod forms · Tailwind v4 + Shadcn  ││
│ │  20+ NEW components Vitalia + REUSE ~30 Nicolify curados (fork+adapter tokens)││
│ └──────────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │ REST + SSE v2 streaming (chat) + Webhooks IN
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   BACKEND vitalia (FastAPI async · DDD Inside-Out)                │
│                   Port 8002 (dev) · uvicorn workers · redirect_slashes=False      │
│ ┌──────────────────────────────────────────────────────────────────────────────┐│
│ │  ~50 endpoints /api/v1/vitalia/{inbox,pipeline,agenda,fidelizacion,marketing,  ││
│ │  onboarding,connections,iam}/...                                              ││
│ │  11 cron jobs (ARQ workers) · 7+ services · 11 NEW tables                     ││
│ │  Dual filter tenant_id + clinic_id en TODA query PHI                          ││
│ │  Audit log sync write pre-response (vitalia.audit_log table)                  ││
│ │  pgcrypto encryption columns PHI sensitive                                    ││
│ │  Extension SDK registries (5 NEW Vitalia: payment_provider · fiscal_provider  ││
│ │     · appointment_origin · conversation_initiation · print_method)            ││
│ └──────────────────────────────────────────────────────────────────────────────┘│
└─┬─────────────────────────────────────────────────────────────────────────────┬─┘
  │                                                                             │
  │ AGENTIC LAYER (Opus 4.7 R23 production)                                     │
  ▼                                                                             ▼
┌─────────────────────────────┐                       ┌───────────────────────────────────┐
│ Engine core/luana-core-*    │                       │ External integrations             │
│ (READ-ONLY consultation)    │                       │ (graceful-degradation timeout+fb) │
│ ─ copilot                   │                       │ ─ WhatsApp Business API           │
│ ─ sales-agent               │                       │ ─ Meta Ads API                    │
│ ─ brand-studio (voice)      │                       │ ─ Google Ads API                  │
│ ─ observability (turn_env)  │                       │ ─ Whisper STT (audio IN)          │
│ ─ extension-sdk EP-1..18    │                       │ ─ Mercado Pago (depósito 30%)     │
│ ─ analytics-engine          │                       │ ─ Nubefact PE (fiscal Slice 1)    │
│ ─ scheduling                │                       │ ─ Clerk (auth)                    │
│ ─ idempotency               │                       │ ─ Sentry/OpenTelemetry            │
│ ─ events                    │                       │                                   │
│ ─ billing                   │                       │                                   │
│ ─ compliance                │                       │                                   │
└─────────────────────────────┘                       └───────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│           DATA LAYER · Postgres (port 5435 shared) + Qdrant + Redis              │
│   ─ 11 tablas NEW Vitalia + 8 column additions                                   │
│   ─ Qdrant collection `vitalia_marketing_kb` (per brand.yaml prefix)             │
│   ─ Redis db=1 (per brand.yaml infra.dev.redis_db)                              │
│   ─ vitalia_dev database (per brand.yaml infra.dev.database_name)                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Cross-cutting design principles (consumed by all 3 sub-archs)

### 2.1 Tenant + Clinic dual filter (cardinal — HIPAA-lite)

**Rule:** every query touching PHI MUST filter `Model.tenant_id == tenant_id AND Model.clinic_id == clinic_id`. No exceptions. Including `get_by_id`.

**Enforcement:**
- Arch fitness `test_phi_dual_filter.py` enforces grep pattern
- Repository abstract base `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py::PhiRepositoryBase` with mandatory `tenant_id + clinic_id` constructor params
- Every endpoint MUST resolve `clinic_id` from `X-Clinic-ID` header (middleware-injected from Clerk JWT claim `clinic_id` per Slice 1 single-clinic-per-user; multi-clinic switcher = Slice 2+)

### 2.2 Audit log sync write (PHI mutation/access)

**Rule:** every PHI read/write writes a row in `vitalia.audit_log` BEFORE response is sent. Sync, not fire-forget.

**Pattern:**
```python
# Inside application service (sync write pre-response)
async def get_patient_diagnosis(self, patient_id: UUID, ...) -> DiagnosisDTO:
    diagnosis = await self.repo.get_diagnosis(tenant_id, clinic_id, patient_id)  # dual filter
    await self.audit_log_repo.record(  # sync write — same transaction
        tenant_id=tenant_id, clinic_id=clinic_id,
        user_id=current_user.id,
        action="view_diagnosis", resource_type="patient.diagnosis",
        resource_id=patient_id,
        from_ip=request.client.host, user_agent=request.headers.get("user-agent"),
        payload_redacted={"patient_id_hash": hash_patient_id(patient_id)},  # sanitize PHI
    )
    return diagnosis  # response after audit row committed
```

### 2.3 PII sanitization in traces

**Rule:** `sanitize_payload(payload, compliance_level="hipaa_lite")` (from `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py`) MUST be applied BEFORE writing to any observability table (`copilot_trace_event`, `sales_agent_trace_event`, `copilot_llm_call`, `sales_agent_llm_call`).

**Implementation:** Vitalia adds NEW PHI field list to canonical PII patterns in `vitalia/backend/src/modules/vitalia/compliance/phi_fields.py` (per `hipaa-lite.md` § PHI fields). Adapter pattern wires this to engine sanitizer via Extension SDK EP-N (NEW lift candidate Slice 2 — for now, brand-specific list overrides default at runtime).

### 2.4 Encryption at-rest (pgcrypto)

**Columns encrypted via `pgcrypto` symmetric (KEK rotated annually):**
- `patient_medical_records.diagnosis`
- `patient_medical_records.treatment_plan`
- `patient_medical_records.medical_notes`
- `treatment_plans.notes` (NEW Slice 1)
- `re_engagement_events.payload_phi` (NEW Slice 1)
- `audit_log.payload_redacted` (NEW Slice 1 — even sanitized payload encrypted at rest as defense in depth)

KEK stored in Vault/cloud KMS — NOT in env vars, NOT in DB. App reads via `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py` (NEW Slice 1).

### 2.5 RBAC strict (medical roles)

**Roles allowed PHI:** `doctor`, `nurse`, `admin_clinic`. Other roles (marketing, sales) NEVER see PHI. Patient role `patient` sees only own data.

**Decorator pattern:**
```python
from vitalia.compliance.rbac import require_phi_access

@router.get("/patients/{patient_id}/diagnosis", response_model=DiagnosisResponse)
@require_phi_access(roles=["doctor", "nurse", "admin_clinic"])
async def get_diagnosis(...): ...
```

### 2.6 Channel guards (no PHI on non-encrypted channels)

`ComplianceService.validate_outbound_message(message, channel)` (from `core/luana-core-compliance/`) blocks PHI on:
- WhatsApp tier free (only Business API tier paid OK)
- SMS (any)
- Email plaintext (only portal-link email OK)

Vitalia channel adapters register via EP-8 with `compliance_level=hipaa_lite` flag — compliance gate auto-applies.

### 2.7 Currency policy (LatAm — NO hardcoded USD)

**Per `brand.yaml::booking.default_currency_per_country`:**
- AR → ARS · CL → CLP · MX → MXN · CO → COP · PE → PEN · BR → BRL · US → USD

DTOs with monetary fields include `currency: str | None = None`. FE consumes via `formatMoney(amount, currency)`. Source-of-truth: `tenants.location_country` (NEW column Slice 1) → resolves currency via `TenantLocale` VO from `core/luana-core-platform/`.

### 2.8 Spanish neutro LatAm strict

UI chrome `<feature>/copy.ts` files MUST follow `.claude/rules/spanish-text.md` (tuteo neutro, NO voseo, NO regionalismos). Arch fitness `test_no_voseo_in_copy.test.ts` enforces.

**Exception:** sales_agent Adrián output respects tenant voice configuration (`personality_profiles.system_instruction` per-tenant). If tenant AR configures voseo → Adrián replies voseo. This applies to OUTBOUND messages, NOT UI chrome.

### 2.9 Master data (UTC + timezone tenant)

`DateTime(timezone=True)` mandatory. Store UTC. Display via `useTenantLocale()` (FE) / `formatTenantDate*()` resolving from `tenants.timezone` (NEW column Slice 1) — defaults per country (AR=America/Argentina/Buenos_Aires, MX=America/Mexico_City, etc.).

### 2.10 Idempotency on writes

All POST/PUT routes with retry potential use idempotency keys:
- Pattern: `Idempotency-Key` header → `core/luana-core-idempotency/` checks `idempotency_keys` table
- Natural-key idempotency for payment: `(tenant_id, clinic_id, appointment_id, attempt_n)` partial unique index

### 2.11 No cross-brand mirror (anti-duplication)

Pattern detected in 2+ brands → STOP, escalate `/pm-luana` promotion proposal. NEVER mirror in `vitalia/backend/src/modules/vitalia/X/` if `nicolify/backend/src/modules/nicolify/X/` exists similar.

**Vitalia-specific patterns identified as lift candidates Slice 2** (documented in `delta-arch-notes.md`):
- `AttributionMatrixWidget` (4 origins) — lift to `core/luana-core-analytics-engine/`
- Agent identity primitives (`<AgentAvatar>`, `<AgentAttribution>`, `agentNameByRole`) — lift to `@luana/ui-kit`
- PHI wrappers (`<PiiMaskedSpan>`, `<RequireRole>`, `<AuditedSection>`) — lift to `core/luana-core-compliance/` (FE binding)
- `<ContactSidebar>` PHI-aware pattern — lift to `@luana/ui-kit`
- Lucas recommendations pattern — lift to `core/luana-core-sales-agent/`
- 5 Extension SDK registries (payment_provider · fiscal_provider · appointment_origin · conversation_initiation · print_method) — consolidate to engine EP-N

## 3. Existing systems audit (NO NEW LAYER rule per `.claude/rules/anti-duplication.md`)

### Source of evidence
- [x] CONTEXT-BRIEF.md not found in story folder — used Path B (self-run greps)
- [x] Self-run greps cross-module (core + 4 active brands)
- [x] Engine package read-only consultation

### Audit cross-module executed

```bash
# 1. Engine observability shared abstractions (SSoT per anti-duplication.md)
ls core/luana-core-observability/src/luana_core_observability/
# → recording/{turn_envelope,base_callback_handler,sanitization}.py
# → cost/{calculator,fx_resolver,pricing_resolver,cost_recorder}.py
# → persistence/{base_trace_event_repo,base_llm_call_repo,pricing_snapshot_repository,tenant_billing_config_repository}.py
# → channels/{format_for_channel,intent_detector}.py
# All CROSS-AGENT shared. Vitalia consume via heredancia.

# 2. Engine brand-studio voice infra (cementado spec § Components mapping)
ls core/luana-core-brand-studio/src/luana_core_brand_studio/application/
# → agents/style_analyzer/  (LangGraph agent)
# → services/{personality_service,brand_data_adapter}.py
# → voice_fidelity/{grader,golden}/
# Engine DIRECT consume — no fork. Wizard onboarding llama via port shared/links.

# 3. Engine analytics-engine
ls core/luana-core-analytics-engine/src/luana_core_analytics_engine/
# → stage_services/{constants,channel_registry,attraction_stage,conversion_stage,...}.py
# Brand opt-in via extensions.py registering enabled_metrics + channel_groups.

# 4. Engine extension-sdk registry
cat core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py
# → EP-1..EP-18 frozen post Story 9 cement. Vitalia consume 5 EP + introduces 5 NEW registries
#   (payment_provider, fiscal_provider, appointment_origin, conversation_initiation, print_method)
#   pero esto NO modifica el engine — son brand-specific dict keys montados en vitalia/extensions.py
#   via EP-3 (tools) / EP-4 (workflows) / EP-2 (presets) según corresponda.
#   FUTURE: Slice 2 lift to engine como EP nuevos (NEW core EP-19..EP-23 candidate).

# 5. Cross-brand mirror check (CRITICAL anti-duplication)
for B in nicolify comunify lupulo; do
  echo "=== $B ==="
  find ./$B/backend/src/modules/$B -path "*payment*" -name "*.py" 2>/dev/null | head
done
# → nicolify has nicolify/payment/ but DIFFERENT semantics (B2B agencies billing, not booking deposit)
# → No mirror risk Slice 1. Lift candidates Slice 2 documented in delta-arch-notes.md.
```

### Sistemas existentes encontrados

| Sistema | Path engine | Decision Vitalia |
|---|---|---|
| Observability cross-agent (turn_envelope, callback_handler, cost_recorder, sanitize_payload) | `core/luana-core-observability/` | **EXTEND via heredancia** — Vitalia copilot+sales_agent subclase los engines. Schema mirror tables (`copilot_trace_event`, `copilot_llm_call`, `sales_agent_trace_event`, `sales_agent_llm_call`) per brand backend per backend-ddd.md schema-mirror exception. |
| Brand voice infra (style_analyzer, personality_service, voice_fidelity, brand_data_adapter) | `core/luana-core-brand-studio/` | **EXTEND** — Vitalia wizard llama via port (NEW `shared/links/ports/brand_studio.py` lift candidate). brand_data_adapter Vitalia subclase para medical vertical context (URL scraping medical-aware, PII detection medical fields). |
| Analytics stage services + channel registry | `core/luana-core-analytics-engine/` | **EXTEND** — Vitalia `analytics/extensions.py` registra `enabled_metrics` (medical-relevant subset) + `channel_groups` (LATAM medical channels). NO mirror stage_services. |
| Extension SDK registry | `core/luana-core-extension-sdk/` | **CONSUME** via existing EP-1..EP-18. 5 NEW Vitalia registries son brand-specific dict structures montadas internamente, NO modifican engine. Slice 2 lift candidates documented. |
| Scheduling (booking + event_types) | `core/luana-core-scheduling/` (NEW post-multibrand-reorg) | **EXTEND** — Vitalia agenda módulo consume engine `Appointment` model + BookingPolicyDef per-brand via EP. 4 origins NEW (`sales_agent`, `walk_in`, `phone_manual`, `proactive_outbound`) son metadata column en `appointments.origin` Vitalia, NO modifican engine. |
| LLM router (LiteLLM Proxy canonical post 2026-05-06) | `core/luana-core-llm/src/luana_core_llm/providers/litellm.py` | **CONSUME direct** — no provider adapters mirror. Kimi/DeepSeek Standard tier wizard onboarding + Adrián. |
| Compliance gates (ComplianceService) | `core/luana-core-compliance/` | **EXTEND** — Vitalia `compliance_level=hipaa_lite` (per brand.yaml). Channel guards apply automatically. |
| Idempotency keys | `core/luana-core-idempotency/` | **CONSUME direct** — payment endpoints + reschedule endpoints use Idempotency-Key header. |
| Events outbox pattern | `core/luana-core-events/` | **CONSUME direct** — Vitalia emite DomainEvents (PatientCheckedIn, AppointmentRescheduled, NPSReceived, etc.) via outbox bus (post 2026-04-30 default True). |

### Decisión por sistema (EXTEND > REPLACE > NEW priority)

**ALL EXTEND** — zero NEW infrastructure layers proposed. Brand-extension only via Extension SDK. Zero engine modifications proposed. Cross-brand mirror risk: ZERO (Vitalia patterns are medical-specific, not yet repeatable in other brands until 2do brand opts in to medical preset pack — at that point promotion proposal triggered).

### Cross-brand mirror check resultado

**ZERO mirrors detected.** All Vitalia surfaces are brand-specific OR consume engine directly. Lift candidates Slice 2 documented in `delta-arch-notes.md` for `/pm-luana` retrospective.

## 4. Side stories blocker mitigation (per `06-tickets.yaml`)

Three paralleldependent stories MUST be `state=developed` or `shipped` BEFORE `/dev-team` picks dependent tickets from this story:

| Side story | Status | Dependent tickets (this story) |
|---|---|---|
| `vitalia-payment-adapter-mvp` | state=idea (Chris ratified 2026-05-17) | T-be-agenda-payment-mp · T-fe-agenda-payment-sheet · T-fe-pipeline-deposit-badge |
| `vitalia-copilot-tools-impl` | state=idea (Chris ratified 2026-05-17) | T-agentic-wizard-onboarding · T-agentic-valeria-tools · T-fe-onboarding-wizard |
| `vitalia-fiscal-emission-pe` | state=idea (Chris ratified 2026-05-17 NEW Slice 1) | T-be-agenda-fiscal-nubefact · T-fe-agenda-fiscal-toggle |

Tickets marked `blocked_by: [side-story-id]` in 06-tickets.yaml. `/dev-team` picks unblocked tickets first; blocked tickets enter queue only after side story `state >= developed`.

## 5. Performance budgets (Slice 1)

| Metric | Budget |
|---|---|
| LCP (Largest Contentful Paint) | < 2.5s |
| INP (Interaction to Next Paint) | < 200ms |
| CLS (Cumulative Layout Shift) | < 0.1 |
| Bowtie SVG bundle size | < 30KB gzipped (pixel-invariante mantenimiento) |
| Lucas recommendations card | lazy-load below fold |
| Wizard onboarding live preview | debounced 1.5s + throttle 5 calls/min/tenant |
| LLM cost per onboarding | $0.05-0.10 USD (Kimi/DeepSeek Standard tier) |
| LLM cost per Adrián turn | ≤ $0.05 USD |
| Cache hit rate (Adrián system prompt) | ≥ 60% (slot 1-5 cacheable cross-tenant + per-tenant) |

Validators per § 04-validators.yaml `visual` + `agentic_eval` categories.

## 6. Observability + tracing (Slice 1)

### OpenTelemetry tracing

NEW spans:
- `vitalia.cron.lucas_daily_analysis_sweep` (cron lucas recommendations)
- `vitalia.cron.multi_session_gap_sweep` (cron fidelización)
- `vitalia.cron.follow_up_due_sweep`
- `vitalia.cron.maintenance_due_sweep`
- `vitalia.cron.absence_sweep`
- `vitalia.cron.nps_post_treatment_sweep`
- `vitalia.cron.re_engagement_response_timeout_sweep`
- `vitalia.cron.channel_metrics_sync` (Meta + Google)
- `vitalia.cron.payment_timeout_sweep`
- `vitalia.cron.referrals_value_sync`
- `vitalia.cron.brand_studio_drafts_cleanup`
- `vitalia.adrian.turn` (sales_agent per-turn)
- `vitalia.valeria.turn` (copilot per-turn)
- `vitalia.wizard.extract_url`
- `vitalia.wizard.extract_doc`
- `vitalia.wizard.transcribe_audio` (Whisper)
- `vitalia.wizard.simulate_voice`
- `vitalia.wizard.complete`
- `vitalia.nubefact.submit_receipt`
- `vitalia.mp.create_payment` + `vitalia.mp.refund_payment`

### Sentry/observability alerts

- Cron job failure > 3 consecutive → page on-call
- Adrián cost per turn > $0.10 → warn (cost runaway detection)
- Wizard onboarding `simulate_personality` cache hit rate < 30% → warn (silent invalidator in prefix)
- Nubefact PE retry queue > 10 pending > 1h → page (fiscal compliance risk)
- WhatsApp Business API rate limit hit → throttle + degrade

## 7. Open questions deferred to /dev-team (NON-blocking per Chris ratification)

Per spec § Handoff /architect 12 puntos — resolutions cementadas:

| # | Question | Resolution (this arch) |
|---|---|---|
| 1 | Fork físico vs shared package Nicolify reuse | **Fork físico Slice 1** — Vitalia copies closer-studio + growth-studio components into `vitalia/frontend/src/features/{inbox,pipeline,marketing}/` with token adapter (HEX→Vitalia tokens) + PHI wrappers added. Shared package candidate Slice 2 when 2nd brand opts-in medical. ADR `vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md` (NEW ticket T-arch-1). |
| 2 | Promotion candidates lift to engine | Documented in `delta-arch-notes.md` — NOT addressed in Slice 1 tickets. `/pm-luana` retrospective post-Slice 1 ratifica lift roadmap. |
| 3 | Side stories blocker | Per § 4 above. |
| 4 | Backend Slice 1 additions confirmation | Per `03-arch-be.md` — 11 tables + ~50 endpoints + 11 cron jobs + 7+ services + 5 Extension SDK registries cemented. |
| 5 | Arquitectura buenas prácticas | Per § 2 cross-cutting + `05-guidelines.md` § Required patterns. |
| 6 | Tabla 13 anti-patterns Nicolify NO replicar | Per `05-guidelines.md` § Forbidden patterns. |
| 7 | Performance budget Slice 1 | Per § 5 + `04-validators.yaml::visual`. |
| 8 | Storybook obligatorio | T-fe-storybook-setup + per-component story tickets T-fe-{comp}-story. Per `06-tickets.yaml`. |
| 9 | Visual regression Playwright + Chromatic | Per `04-validators.yaml::visual`. |
| 10 | Observability OpenTelemetry | Per § 6 + T-be-observability-otel ticket. |
| 11 | A11y WCAG 2.1 AA | Per `04-validators.yaml::visual::a11y` + `05-guidelines.md` § A11y. |
| 12 | Spanish neutro verified pre-merge | Per `04-validators.yaml::non_functional::test_no_voseo_in_copy`. |

## 8. Mega-story SPLIT recommendation

> **Architect recommendation:** this is a Slice 1 MVP mega-story spanning 6 routes + cross-cutting infra. Natural split below produces 7 sub-stories each ≤ 10 tickets, allows parallel `/dev-team` execution post side-stories shipped, and aligns with state machine WIP caps (developing ≤ 3, ready ≤ 5).

### Recommended split (7 sub-stories)

| Sub-story | Scope | Tickets count (est) | Blocker dependencies |
|---|---|---|---|
| `vitalia-slice-1-infra-cross-cutting` | 11 tables migrations · Extension SDK registries · audit_log + pgcrypto + RBAC decorators · ADR shared-vs-fork · arch fitness tests · OpenTelemetry · Storybook setup · design-system globals.css | 8-10 | none (foundation) |
| `vitalia-slice-1-onboarding-wizard` | Wizard agentic conversacional · 4 tools Valeria · live preview voz Adrián real · brand_data_adapter extension · onboarding_progress + brand_studio_drafts tables | 7-8 | infra-cross-cutting · vitalia-copilot-tools-impl |
| `vitalia-slice-1-inbox` | /inbox segmented 3-modos · Audio IN Whisper · Image OUT asset library · Activity Stream sticky · Action Receipts · ProactiveOutboundModal · Tools Sheet | 8-9 | infra-cross-cutting |
| `vitalia-slice-1-pipeline` | /pipeline 6 stages venta consultiva ética · DnD + auto-progression · screening clínico Lucas · depósito 30% badge · 9 telemetry events | 7-8 | infra-cross-cutting · vitalia-payment-adapter-mvp · vitalia-copilot-tools-impl |
| `vitalia-slice-1-agenda` | /agenda Semana/Día/Mes · 4 origins · 3 capas cobranza · DnD reschedule · 5 cron jobs · WalkIn/PhoneManual drawers · ProactiveOutbound cross-link | 8-10 | infra-cross-cutting · vitalia-payment-adapter-mvp · vitalia-fiscal-emission-pe |
| `vitalia-slice-1-fidelizacion` | /fidelización 4 patrones re-engagement · NPS post-treatment auto · 5 templates Meta-approved · 6 cron jobs · treatment_plans + re_engagement_events tables | 7-8 | infra-cross-cutting |
| `vitalia-slice-1-marketing` | /marketing bowtie 5 stages · Lucas StageRecommendations · AttributionMatrixWidget · ReferralsWidget · Meta+Google sync simplified · 4 cron jobs · channel_sync_state + channel_metrics + referrals tables | 8-10 | infra-cross-cutting · vitalia-copilot-tools-impl (Lucas tools) |

**Total: ~53-63 tickets across 7 sub-stories.** Original single story = blow up to 53+ tickets → exceeds 10-ticket WIP cap. Split MANDATORY per `.claude/skills/architect/SKILL.md` rule.

**Recommended action for `/pm-vitalia`:**
1. Read this `03-arch.md` index + 3 sub-archs.
2. Split `vitalia-ux-discovery` into 7 sub-stories above, archive original as parent epic.
3. Spawn `/architect` per sub-story IF FE/BE/AGENTIC contracts inside each need further detail (this arch already covers 80%).
4. OR: skip per-sub-story architects and pass this consolidated arch + 06-tickets.yaml directly to `/dev-team` per sub-story.

This `06-tickets.yaml` provides the COMPLETE 53-63 ticket DAG grouped by sub-story label.

## 9. Referencias

- `01-spec.md` § Slice 1 cut · § Components mapping · § Handoff /architect · § Bitácora Batches 1-7
- `00-research.md` + `00-research-chat-layout.md` (research base)
- `vitalia/docs/architecture/design-system.md` (tokens + tipografía + agent attribution + PHI conventions)
- `vitalia/.claude/rules/hipaa-lite.md` (PHI compliance cardinal)
- `vitalia/.claude/rules/README.md` (overlay rules vitalia)
- `vitalia/config/brand.yaml` (feature flags + plan tiers + currencies + compliance_level)
- `vitalia/backend/src/modules/vitalia/extensions.py` (existing Story 11 cement EP-1..EP-18 scaffold)
- `core/luana-core-{copilot,sales-agent,brand-studio,observability,analytics-engine,scheduling,extension-sdk,compliance,events,idempotency,llm,billing,platform}/` (engine READ-ONLY consultation)
- `nicolify/frontend/src/features/{closer-studio,brand-studio,growth-studio,sales}/` (audit pre-fork componente por componente)
- `.claude/rules/{tenant-isolation,backend-ddd,frontend-fsd,architectural-fitness,anti-duplication,spanish-text,tdd-mandatory,master-data,currency-handling,auditor-downstream-regression,hotfix-repro-mandatory}.md`
- `docs/portfolio/PORTFOLIO.md` (vista master 11 universos)
- `docs/specs/templates/{03-arch,04-validators,05-guidelines,06-tickets}-template*` (templates ready package)

## 10. Research notes (DATE-AWARE — accessed 2026-05-17)

| Source | Version | Accessed | Key takeaway |
|---|---|---|---|
| LangGraph docs · supervisor pattern | langgraph 0.6+ | 2026-05-17 | `langgraph_supervisor.create_supervisor` for multi-tool wizard onboarding routing — accepts `members[]` + `output_mode="full_history"`. Stream modes `updates` (production UI) + `messages` (token streaming chat UX) — 6 modes available. |
| LangGraph checkpointer | langgraph 0.6+ | 2026-05-17 | `AsyncPostgresSaver` mandatory for production (NOT `MemorySaver` — tutorials only). Connection via `settings.postgres_dsn`. Checkpoint table per-module. |
| deepagents SubAgentMiddleware | 0.5.3+ | 2026-05-17 | `allowed_keys_to_subagent` / `allowed_keys_from_subagent` isolation for wizard onboarding subagents (URL extractor + doc parser). Optional Slice 1 — simpler ReAct may suffice. |
| Anthropic prompt caching | API 2024-10-22 ext | 2026-05-17 | Slot order: System role → Domain → Tools → Persona → BRAND_VOICE (cache_control marker) → Conversation (NOT cached). TTL: 5min default · 1h for batch eval. Break-even at 2 reads (5min) / 3 reads (1h). 1h write = 2× input price; cache read = 0.1×. Forbidden in cache prefix: timestamps, conversation IDs, tenant_name interpolated mid-block. |
| Next.js 16 App Router parallel routes | 16.x | 2026-05-17 | URL state nuqs SSoT pattern · `useSearchParams` + `useRouter().push/replace` · push for inter-route nav, replace for intra-state (filter/selected ID). Server Components default — `"use client"` solo en nodos hoja. |
| Pydantic v2 ConfigDict | 2.10+ | 2026-05-17 | `model_config = ConfigDict(from_attributes=True)` mandatory (no inner `class Config`). Explicit types, no `Any`. |
| SQLAlchemy 2.0 async | 2.0.30+ | 2026-05-17 | `mapped_column()` syntax · `select(Model).where(...)` · async-first · NEVER `Column()` or `session.query()`. |
| FastAPI redirect_slashes | 0.115+ | 2026-05-17 | `FastAPI(redirect_slashes=False)` mandatory — default `True` returns 307 on POST which Next.js drops body. App-level only. |
| Mercado Pago API · LATAM booking deposit | API v1 2025 | 2026-05-17 | Tokenized recurring + onboard via OAuth — deposit % via webhook · refund flow synchronous · 30% deposit pattern standard LATAM clinics (validated via Cero.ai + DentaLink). |
| Nubefact PE API REST | API 2025 | 2026-05-17 | Boleta + factura emit · CDR response · retry queue mandatory (Nubefact rate-limited 100req/h free tier). Secrets vault for token storage. |
| WhatsApp Business API templates | Cloud API 2025 | 2026-05-17 | UTILITY templates (transactional) NO opt-in required · MARKETING templates require explicit opt-in checkbox. Throttle 1 reminder per pattern per 7d compliance. |
| OpenTelemetry Python | otel 1.30+ | 2026-05-17 | `tracer.start_as_current_span("vitalia.cron.X")` instrumentation cron + agent turns. Sentry integration via otel adapter. |
| Playwright + Chromatic visual regression | Playwright 1.50 · Chromatic | 2026-05-17 | Bowtie SVG pixel-invariante mantenimiento — snapshot per breakpoint (mobile 768 · tablet 1024 · desktop 1440). |
| WCAG 2.1 AA | WAI-ARIA 1.2 | 2026-05-17 | Contrast ratios validated cross-tokens. Bowtie SVG with title+aria-labelledby. Keyboard nav Lucas cards. |

**Knowledge cutoff disclosure:** Topics LangGraph 0.6+ stream modes, deepagents 0.5.3+, LiteLLM Proxy canonical (post 2026-05-06 commit) — researched live on 2026-05-17 via internal codebase greps and skill knowledge bases. Opus 4.7 cutoff is Jan 2026; post-cutoff topics (PI-12 S1 T-5 LiteLLM canonicalization 2026-05-06, multibrand reorg 2026-05-15) verified via current codebase state.

---

**Next sub-archs:** read `03-arch-be.md`, `03-arch-fe.md`, `03-arch-agentic.md` for surface-specific contracts. Each cross-references this index.
