# vitalia-copilot-tools-impl — Architecture (consolidated index)

> **Architect:** /architect Opus 4.7
> **Run date:** 2026-05-18
> **Brand:** vitalia
> **Story type:** AGENTIC + BE (single-shot full-stack — no FE component lives here; FE cards consume via sub-stories `vitalia-slice-1-{marketing,pipeline,onboarding-wizard,agenda}`)
> **Parent context (read-only cross-ref):**
> - `../vitalia-ux-discovery/01-spec.md § Batch 7` (wizard onboarding agentic spec)
> - `../vitalia-ux-discovery/03-arch-agentic.md` (12 tools tables + slot architectures + checkpointer + stream modes + observability + 4 medical guardrails + 12+4 goldens + LiteLLM canonical)
> - `02-design-agentic.md v1.0 RATIFIED Chris 2026-05-17`
> **Engine boundary cardinal:** NO engine modify in this story. `core/luana-core-{copilot,sales-agent,observability,brand-studio,llm,billing,compliance,extension-sdk,events,channels,platform}/` are READ-ONLY consult. Fase A engine lift (`TenantLocationContract` + `OfferAdherenceContract`, commit `5ca6101`) is `state: migrated` — consume Protocols, do not modify.

## 0. Context Summary

### 0.1 Modules touched (brand extension overlay)

```
vitalia/backend/src/modules/vitalia/
├── copilot/
│   ├── tools/                     ← 4 NEW (Valeria wizard)
│   ├── workflows/                 ← 1 NEW (LangGraph supervisor wizard onboarding graph)
│   ├── prompts/                   ← 2 NEW (valeria_persona.md + extractor_subagent.md)
│   ├── observability/recording/   ← VitaliaCopilotCallbackHandler subclass (anti-duplication §0)
│   ├── persistence/models/        ← schema mirror only (per backend-ddd schema-mirror exception)
│   └── application/services/      ← OnboardingDraftService + SimulatePersonalityService + ExtractTenantContextService + CompleteOnboardingService
├── sales_agent/
│   ├── tools/                     ← 3 NEW (Adrián subset MVP per Q1: send_payment_link + reschedule_appointment + screening_questions)
│   ├── personas/                  ← 5 YAML (warm_close_default + 4 verticals: dental/estetica/psicologia/fertilidad)
│   ├── prompts/                   ← 2 NEW (medical_safety_rails.md SLOT 4 + medical_vertical.md SLOT 2)
│   ├── observability/recording/   ← VitaliaSalesAgentCallbackHandler subclass
│   ├── persistence/models/        ← schema mirror only
│   └── application/services/      ← ScreeningQuestionsService + PaymentLinkService + RescheduleAppointmentService
├── agentic/
│   ├── lucas/
│   │   ├── tools/                 ← 3 NEW (compute_stage_recommendation + compute_attribution_matrix + compute_referrals_leaderboard)
│   │   ├── workflows/             ← 1 NEW (lucas_daily_analysis_graph.py — cron-triggered ReAct)
│   │   ├── personas/              ← lucas_growth_setter.yaml
│   │   └── application/services/  ← LucasStageRecommendationService + LucasAttributionService + LucasReferralsService
│   └── screening/                 ← screening_questions_by_vertical.yaml (SSoT screening per vertical, 4 verticals)
├── compliance/                    ← ChannelGuard service + MedicalGuardrail check functions (EP-13 callables, READ existing scaffold)
└── extensions.py                  ← EXTEND existing register_all (no new EP wiring beyond placeholders→real)
```

### 0.2 Surface → builder → auditor mapping

| Surface | Builder | Auditor | Skills invoked |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/copilot/{tools,workflows,prompts,observability}/` | **builder-agentic** (Opus 4.7 R23 production_code=true) | **auditor-agentic** (Opus 4.7) | copilot-expert · tessl__langgraph · tessl__deepagents · tessl__graceful-degradation · claude-api · brand-expert |
| `vitalia/backend/src/modules/vitalia/sales_agent/{tools,personas,prompts,observability}/` | **builder-agentic** (Opus 4.7 R23 production_code=true) | **auditor-agentic** (Opus 4.7) | sales-agent-expert · tessl__langgraph · tessl__graceful-degradation · claude-api · brand-expert |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/{tools,workflows,personas}/` + `agentic/screening/` | **builder-agentic** (Opus 4.7 R23 production_code=true — Lucas reasoning prompts agentic) | **auditor-agentic** (Opus 4.7) | tessl__langgraph · metrics-expert (analytics queries) · claude-api · brand-expert |
| `vitalia/backend/src/modules/vitalia/{copilot,sales_agent,agentic/lucas}/application/services/` | **builder-backend** (Sonnet/qwen-opencode default) — pure service orchestration | **auditor-backend** (Opus 4.7) | backend-expert · tessl__fastapi · tessl__pytest-api-testing |
| `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/persistence/models/` (schema mirror exception) | **builder-backend** (Sonnet OK per backend-ddd schema-mirror exception) | **auditor-backend** | backend-expert |
| Migrations idempotent (new tables `lead_screening_events`, `vitalia_wizard_onboarding_checkpoints`, `vitalia_lucas_analysis_checkpoints`, `attribution_matrix_snapshots`, `referrals_leaderboard_snapshots`) | **builder-backend** (Sonnet) | **auditor-backend** | backend-expert |
| Goldens YAML (16 total: 12 Adrián + 4 wizard) + personas YAML (12 personas Adrián + 4 wizard personas + lucas_growth_setter.yaml) | **builder-agentic** (Sonnet OK — `production_code=false`, data/docs about agentic per R23) | **auditor-agentic** | sales-agent-expert · brand-expert |
| Architecture fitness tests (new gates: `test_no_observability_mirror_copilot.py`, `test_no_observability_mirror_sales_agent.py`, `test_lucas_cron_tz_aware.py`, `test_screening_yaml_completeness.py`) | **builder-backend** (Sonnet test code) | **auditor-backend** | backend-expert |

### 0.3 Skills consulted (with one-liner decision)

- **copilot-expert** → Valeria wizard tools register via EP-3; observability via engine `BaseAgentCallbackHandler` subclass (NO mirror); LangGraph supervisor topology with `extract_subagent` via `deepagents.task` sandbox.
- **sales-agent-expert** → Adrián consumes engine LangGraph directly via brand extension overlay; **§3 NO TOCAR** Closer Studio + SmartBufferService + OutputManager preserved; subset MVP 3 tools (send_payment_link + reschedule_appointment + screening_questions); compiler v2 slot architecture (slot 4 `MEDICAL_SAFETY_RAILS` NEW + slot 5 `BRAND_VOICE` from `personality_profiles.system_instruction`).
- **brand-expert** → wizard `complete_onboarding` calls engine `personality_service.compile_full` (3-pilar: dimensions + linguistic_patterns + sample_exchanges); `simulate_personality` calls engine `personality_service.simulate` (single-call NANO scenario render).
- **tessl__langgraph** → `AsyncPostgresSaver` MANDATORY (NO MemorySaver); 6 stream modes — wizard emits `updates` + `messages`; supervisor topology for wizard; ReAct for Lucas cron.
- **tessl__deepagents** → `SubAgentMiddleware.allowed_keys_to_subagent={"extraction_subagent_input","tenant_id"}` + `allowed_keys_from_subagent={"extraction_subagent_output"}` sandbox isolation for `extract_subagent` (wizard).
- **tessl__graceful-degradation** → all external tool calls (Whisper STT, MercadoPago, WhatsApp Business API, website_scraper) wrap `asyncio.timeout` + fallback (per § 1.6 error recovery matrix).
- **claude-api** → prompt cache slot 1-5 cacheable + slot 6 variable; TTL 5min default (active session) / 1h batch (goldens runner); validate `cache_creation_input_tokens` + `cache_read_input_tokens` per LLM call; cache hit rate ≥ 60% post-deploy.
- **backend-expert** → SQLAlchemy 2.0 `mapped_column()` only; Pydantic v2 `ConfigDict(from_attributes=True)`; `response_model=` mandatory on every route; raw SQL idempotent migrations `IF NOT EXISTS`; SoftDelete `deleted_at`; tenant + clinic dual filter cardinal.
- **metrics-expert** → Lucas attribution + referrals queries go through `core/luana-core-analytics-engine/` SSoT (consume `ChannelRegistry` + `STAGE_CHANNEL_MAP` — never duplicate); analytics reads pure DB no LLM.
- **offer-expert** → screening questions per vertical reference `offer_studio.preset_pack: medical_services_v1` for vertical→treatment matching when screening_questions tool fires.

### 0.4 CONTEXT-BRIEF source

No `CONTEXT-BRIEF.md` present (story sub-spawned; small surface; Haiku context-builder skipped). Architect ran direct reads of priority files 1-10 from caller prompt + scanned existing scaffold under `vitalia/backend/src/modules/vitalia/{copilot,sales_agent,agentic}/`. Existing systems audit (§ Existing Systems Audit below) ran greps cross-brand + engine to verify NO mirrors required and NO cross-brand pattern leak.

### 0.5 capability YAML + modules MD updates required (post 2026-05 paradigma)

- `vitalia/docs/product/modules/copilot.md` — § Tools (Valeria) extend section with 4 NEW tools + reference to wizard supervisor topology.
- `vitalia/docs/product/modules/sales_agent.md` — § Tools (Adrián) add 3 NEW tools subset MVP + clarify deferred (`send_template_confirmation`, `retract_last_message` → Slice 2); § Slot architecture add `MEDICAL_SAFETY_RAILS` slot 4.
- `vitalia/docs/product/modules/agentic.md` (NEW or extend) — § Lucas cron analysis + 3 tools.
- `vitalia/docs/product/capabilities/{copilot,sales_agent,agentic}/{wizard-onboarding,closer-screening,lucas-daily-analysis}.yaml` — emit/promote capability rows post-merge (handled by /pm-vitalia merge step).
- `vitalia/docs/product/modules/compliance.md` — § Medical guardrails reference EP-13 real implementations + Slot 4 prompt MD.

### 0.6 Architecture gates that must keep passing

- `vitalia/backend/tests/architecture/test_phi_dual_filter.py` (cardinal tenant_id + clinic_id)
- `vitalia/backend/tests/architecture/test_no_cross_brand_imports.py`
- `vitalia/backend/tests/architecture/test_extension_sdk_registration.py`
- `vitalia/backend/tests/architecture/test_audit_log_sync_write.py`
- `vitalia/backend/tests/architecture/test_no_legacy_paths.py`
- `vitalia/backend/tests/architecture/test_response_model_required.py`
- `vitalia/backend/tests/architecture/test_ddd_inside_out_boundaries.py`
- `vitalia/backend/tests/architecture/test_extraction_orchestrator_inheritance.py`
- `vitalia/backend/tests/architecture/test_vitalia_no_pii_in_cacheable_slots.py`
- `vitalia/backend/tests/architecture/test_vitalia_slot_4_safety_markers_present.py`
- `vitalia/backend/tests/architecture/test_vitalia_cost_bucket_invariant.py`
- `vitalia/backend/tests/architecture/test_vitalia_no_query_without_tenant_filter.py`
- `vitalia/backend/tests/architecture/test_vitalia_personas_yaml_completeness.py`
- **NEW (this story adds)** `test_no_observability_mirror_copilot.py` — assert Vitalia copilot callback handler subclasses `luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler`.
- **NEW** `test_no_observability_mirror_sales_agent.py` — same for sales_agent overlay.
- **NEW** `test_lucas_cron_tz_aware.py` — assert Lucas cron schedule consumes `TenantLocationContract.timezone` from `luana_core_platform.contracts`.
- **NEW** `test_screening_yaml_completeness.py` — 4 verticals × ≥2 questions each in `agentic/screening/screening_questions_by_vertical.yaml`.

Allowlists shrink expected (none new). Engine consult READ-ONLY — gate `be_arch_fitness_engine_consult_readonly` (from parent ready package) detects accidental engine mutation.

## 1. Existing Systems Audit (NO-NEW-LAYER rule, anti-duplication §0)

### 1.1 Source of evidence

- [x] Self-run greps Path B (no CONTEXT-BRIEF.md present)
- [ ] CONTEXT-BRIEF § 7 + § 8

### 1.2 Audit cross-module ejecutado

```bash
WS=/home/chalreme/Proyectos/luana-platform
BRAND=vitalia

# Search engine packages for existing abstractions we'd mirror
grep -rn "BaseAgentCallbackHandler\|BaseObservabilityContext\|FXResolver\|PricingResolver\|sanitize_payload" \
  ${WS}/core/luana-core-observability/src/ ${WS}/core/luana-core-copilot/src/ ${WS}/core/luana-core-sales-agent/src/ | head

# Cross-brand mirror scan for tools we'll create
for tool in extract_tenant_context confirm_slot simulate_personality complete_onboarding \
            send_payment_link reschedule_appointment screening_questions \
            compute_stage_recommendation compute_attribution_matrix compute_referrals_leaderboard; do
  echo "=== $tool ==="
  find ${WS}/{nicolify,comunify,lupulo}/backend/src -name "${tool}.py" 2>/dev/null
done

# Channel format dispatcher (per anti-duplication.md inventory)
grep -rn "get_channel_format\|CHANNEL_FORMATS\|register_channel" ${WS}/core/luana-core-channels/src/ ${WS}/core/luana-core-observability/src/

# LLM router canonical
grep -rn "class LiteLLMService\|class LLMRouter" ${WS}/core/luana-core-llm/src/

# Cost recorder pop_cost canonical
grep -rn "def pop_cost\|class CostRecorder" ${WS}/core/luana-core-observability/src/

# Compliance service channel guards
grep -rn "ComplianceService\|validate_outbound_message" ${WS}/core/luana-core-compliance/src/
```

### 1.3 Sistemas existentes encontrados

| Sistema | Path | Estado | Decision |
|---|---|---|---|
| Callback handler base class | `core/luana-core-observability/src/luana_core_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler` | active | **EXTEND** — Vitalia subclasses with `_persist_llm_call_row` + `_persist_trace_event_row` only (per `anti-duplication.md § Inventario`). |
| Turn envelope | `core/luana-core-observability/src/luana_core_observability/recording/turn_envelope.py::BaseObservabilityContext` | active | **EXTEND** — `VitaliaCopilotObservabilityContext(BaseObservabilityContext)` + sales-agent equivalent. NO mirror. |
| FX resolver | `core/luana-core-observability/src/luana_core_observability/cost/fx_resolver.py::FXResolver` | active | **CONSUME** via `FXResolver.default()` factory. |
| Pricing resolver | `core/luana-core-observability/src/luana_core_observability/cost/pricing_resolver.py` | active | **CONSUME** via engine. |
| Cost recorder canonical (PI-12 S1 T-1) | `core/luana-core-observability/src/luana_core_observability/cost/cost_recorder.py::pop_cost` | active | **CONSUME** — `cost_usd` via `pop_cost(litellm_call_id)` (NO `calculate_cost()` runtime). |
| LiteLLM canonical service | `core/luana-core-llm/src/luana_core_llm/providers/litellm.py::LiteLLMService` | active (legacy adapters removed PI-12 S1 T-4) | **CONSUME** as only LLM dispatch path. NO direct provider adapters. |
| Channel format dispatcher | `core/luana-core-channels/src/luana_core_channels/format_for_channel.py::get_channel_format` | active | **CONSUME** for Adrián outbound. |
| PII sanitization | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py::sanitize_payload` | active | **CONSUME** with `compliance_level="hipaa_lite"` (per `vitalia/.claude/rules/hipaa-lite.md`). |
| Compliance ChannelGuard | `core/luana-core-compliance/src/luana_core_compliance/` (`ComplianceService.validate_outbound_message`) | active | **CONSUME** — Adrián catches `BlockedChannelError` per § 4.1 channel guards table. |
| BudgetGuard + RateLimiter | `core/luana-core-billing/src/luana_core_billing/` | active | **CONSUME** — Lucas cron + Adrián pre-LLM-call gating (per PR-2 cementado). |
| Personality service (3-pilar engine compiler) | `core/luana-core-brand-studio/src/luana_core_brand_studio/application/personality_service.py` (`compile_partial`, `compile_full`, `simulate`) | active | **CONSUME** — Valeria wizard calls `simulate` + `compile_full`. |
| Voice fidelity grader | `core/luana-core-brand-studio/src/luana_core_brand_studio/application/voice_fidelity/grader.py` | active | **CONSUME** for golden tests. |
| AsyncPostgresSaver checkpointer | `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` | active (library) | **CONSUME** for wizard + Lucas. Adrián consumes engine `agent_state_checkpoints`. |
| deepagents SubAgentMiddleware | `deepagents` library | active | **CONSUME** for wizard `extract_subagent` sandbox. |
| Extension SDK EP-3 (sales_agent_tool_register) | `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py` | active | **CONSUME** via `vitalia/backend/src/modules/vitalia/extensions.py` (existing register_all). |
| Extension SDK EP-4 (copilot_workflow_register) | idem | active | **CONSUME** via existing `register_all`. |
| Extension SDK EP-13 (sales_agent_guardrail_register) | idem | active | **CONSUME** via existing `register_all` (placeholders→real callables in this story). |
| LangGraph checkpoint table prefix Vitalia | NEW (`vitalia_wizard_onboarding_checkpoints` + `vitalia_lucas_analysis_checkpoints`) | none yet | **NEW** — declared in migrations T-be-migrations-1; brand-scoped tables for AsyncPostgresSaver. |
| Lucas stage recommendation persistence | `lucas_recommendations` table already declared in parent T-infra-1 migration 009 | exists (parent story) | **CONSUME** existing table; this story populates rows. |
| Attribution + referrals snapshots | NEW (`attribution_matrix_snapshots` + `referrals_leaderboard_snapshots`) | none yet | **NEW** — declared in migration T-be-migrations-1 in this story (NOT in parent). |
| Lead screening events | NEW (`lead_screening_events`) | none yet | **NEW** — declared in migration T-be-migrations-1. |
| Onboarding draft repo | `brand_studio_drafts` + `onboarding_progress` tables already declared parent T-infra-1 | exists (parent story) | **CONSUME** existing tables; this story populates via services. |
| Screening questions YAML SSoT | `vitalia/backend/src/modules/vitalia/agentic/screening/screening_questions_by_vertical.yaml` | none yet | **NEW** in this story. |

### 1.4 Cross-brand mirror scan results

Cross-brand grep for proposed tool basenames in `{nicolify,comunify,lupulo}/backend/src` returned **zero matches** for: `extract_tenant_context`, `confirm_slot`, `simulate_personality`, `complete_onboarding`, `send_payment_link`, `reschedule_appointment`, `screening_questions`, `compute_stage_recommendation`, `compute_attribution_matrix`, `compute_referrals_leaderboard`. → No cross-brand mirror conflict. If during Slice 2 a 2nd brand (e.g., Lupulo restaurants screening dietary contraindications) needs `screening_questions` analog → **STOP, escalate `/pm-luana`** promotion proposal in `docs/promotion-protocol/proposals/` to lift to `core/luana-core-sales-agent/` (e.g., generic `vertical_screening_protocol` extension point).

### 1.5 Decisión por sistema (summary)

- **EXTEND (default for shared abstractions):** BaseAgentCallbackHandler · BaseObservabilityContext · FXResolver (via `.default()`) · PricingResolver · cost_recorder pop_cost · LiteLLMService · channel_format · sanitize_payload · ComplianceService · BudgetGuard · personality_service · voice_fidelity grader · AsyncPostgresSaver · SubAgentMiddleware · EP-3/EP-4/EP-13 registries.
- **NEW (brand-specific extensions, no overlap):** 11 tool implementations · wizard supervisor LangGraph + Lucas ReAct graph · 5 personas YAML Adrián · `valeria_persona.md` + `lucas_growth_setter.yaml` · `medical_safety_rails.md` (slot 4 MD) · `medical_vertical.md` (slot 2 MD) · `extractor_subagent.md` · `screening_questions_by_vertical.yaml` (4 verticals × 2-4 questions) · 16 goldens YAML · 5 brand-scoped tables (lead_screening_events, vitalia_wizard_onboarding_checkpoints, vitalia_lucas_analysis_checkpoints, attribution_matrix_snapshots, referrals_leaderboard_snapshots).

## 2. Sub-arch index (split by surface)

| File | Surface | Owner |
|---|---|---|
| **`03-arch-be.md`** | Backend DDD layers (domain/infra/application/api) · migrations · schema mirror persistence · application services · API routes (`/api/v1/vitalia/onboarding/*` + screening + lucas cron triggers) · audit_log integration · PHI dual-filter repos | builder-backend / auditor-backend |
| **`03-arch-agentic.md`** | LangGraph supervisor topology (wizard) + ReAct (Lucas) · deepagents SubAgentMiddleware · 11 tool implementations · 4 slot architectures (Adrián 6-slot + Valeria 5-slot + Lucas 3-slot + screening optional cache) · observability subclasses (anti-duplication §0) · 4 medical guardrails real impl · 16 goldens YAML · cost+latency budgets · evals pass^k policy | builder-agentic / auditor-agentic |

Both sub-arch docs share these cross-cutting principles (consumed by both builders/auditors):

## 3. Cross-cutting principles (apply to both BE and AGENTIC builders)

### 3.1 Tenant + clinic dual filter (HIPAA-lite cardinal)

Per `vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo`:

- **Every** repository method takes `tenant_id: UUID` AND `clinic_id: UUID` as REQUIRED parameters when PHI-touching (`patient_*`, `medical_*`, `treatment_*`, `appointment_*`, `lead_screening_events`).
- Query body: `.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)` — never one without the other.
- For non-PHI tables (e.g., `lucas_recommendations`, `attribution_matrix_snapshots`): `tenant_id` cardinal, `clinic_id` optional but PRESENT in schema for future-proofing.
- Tool input Pydantic schemas: PHI-touching tools (screening_questions, send_payment_link, reschedule_appointment) include both `tenant_id: UUID` + `clinic_id: UUID` as required fields.
- Arch fitness: `vitalia/backend/tests/architecture/test_phi_dual_filter.py` already enforces; this story keeps it green.

### 3.2 Currency handling (per `.claude/rules/currency-handling.md` + master-data.md)

- Lucas tools that compute money figures (`compute_stage_recommendation` may surface CAC/CPL targets) MUST read tenant currency from `tenant.default_currency` (which itself derives from `tenants.location` country code per Fase A `TenantLocationContract`).
- Lucas `RecommendationDTO.supporting_data` includes `currency: str | None` when monetary; FE displays via `formatMoney(amount, currency)`.
- `send_payment_link` reads `appointment.currency` (already persisted per parent Slice 1 booking flow) — MercadoPago preference call passes that currency, no hardcoded `'USD'`.
- ETL keeps source currency (Lucas attribution matrix from analytics ETL preserves channel-original currency per `metrics-expert::§ETL Extraction Contract`).

### 3.3 Master data (UTC store + tenant locale display)

- All `*_starts_at`, `*_at`, `created_at`, `updated_at`, `deleted_at` columns: `DateTime(timezone=True)`, store UTC via `utc_now()` helper (NEVER `datetime.utcnow()`).
- Lucas cron schedule resolves tenant local TZ via `TenantLocationContract.timezone` (Fase A engine lift, commit `5ca6101`). Cron daily at 06:00 LOCAL tenant TZ. Implementation: APScheduler with per-tenant trigger `CronTrigger(hour=6, minute=0, timezone=tenant.timezone)`.
- Wizard `onboarding_progress.last_slot_completed_at` UTC; resume email shows tenant-local time via `formatTenantDate*()` (FE side, sub-story).

### 3.4 PII / PHI sanitization (per `vitalia/.claude/rules/hipaa-lite.md`)

- Every write to `copilot_trace_event`, `copilot_llm_call`, `sales_agent_trace_event`, `sales_agent_llm_call`, `lead_screening_events`, `audit_log_vitalia` MUST pre-process payload via `sanitize_payload(payload, compliance_level="hipaa_lite")` from `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py`.
- PHI field list SSoT: `vitalia/backend/src/modules/vitalia/compliance/phi_fields.py` (already declared in parent T-infra-3). This story does NOT extend the list (no new PHI fields introduced).
- Wizard `extract_tenant_context` doc/audio uploads: scan with `sanitize_payload` BEFORE persisting `extraction_subagent_output` — if PII detected (DNI/passport accidentally in doc), mask + trigger `PII_DETECTED_BLOCK` state (per § 1.6 design § Error recovery matrix).
- Audit log writes: **synchronous** (pre-response, not async fire-forget) — already encoded in arch fitness `test_audit_log_sync_write.py`.

### 3.5 Spanish neutro LatAm (per `.claude/rules/spanish-text.md`)

- UI chrome (Valeria responses + Lucas card text + error responses) uses **tuteo** (`tú/puedes/tienes/configura`). NO voseo (`vos/podés/tenés/configurá`).
- Valeria persona prompt MD (slot 4) explicitly cements tuteo per § 1.5 voice constraints.
- Lucas persona prompt explicitly cements tuteo profesional analytics per § 3.5 voice constraints.
- **Exception:** Adrián sales_agent OUTPUT respects tenant voice (compiled from `personality_profiles.system_instruction` — if tenant AR-Buenos Aires configures voseo, Adrián voseaa). Slot 5 `BRAND_VOICE` prefix per-tenant invariant.

### 3.6 Channel guards enforcement points (HIPAA-lite cardinal)

Per `vitalia/.claude/rules/hipaa-lite.md § Voice patterns sales_agent` + design § 4.1:

- Enforcement layer: `core/luana-core-compliance/src/luana_core_compliance/ComplianceService.validate_outbound_message(message, channel)` — Vitalia tools (`send_payment_link`, `reschedule_appointment`, Adrián's reply generation) MUST call `validate_outbound_message` BEFORE any send.
- Returns `BlockedChannelError` if PHI in message + channel non-encrypted (WhatsApp tier free, SMS, Telegram, Email plain).
- Adrián catches BlockedChannelError → derives to portal: `"Por seguridad, los resultados los podés ver en tu portal: {portal_link}"` (per § 4.1 channel guards table).
- Per `vitalia/config/brand.yaml` `payment_gateways`: WhatsApp Business API tier paid only for PHI-sensitive comms; default tier check via tenant config column `tenants.whatsapp_tier`.

### 3.7 Medical guardrails enforcement points (4 guardrails per § 4.2)

Real implementations land in `vitalia/backend/src/modules/vitalia/compliance/guardrails/` (existing scaffold has placeholders per Story 11 `T-guards-1..3`):

| Guardrail | Trigger detection | File |
|---|---|---|
| `medical_safety_no_diagnosis` | Regex match diagnosis terms (gingivitis, periodontitis, depresión clínica, etc.) + LLM nano classifier confirm | `compliance/guardrails/medical_safety_no_diagnosis.py` (existing scaffold) — implement real check |
| `medical_safety_no_prescription` | Regex match medication+dosage + prescription verb (recetá, tomar, dosis) | `compliance/guardrails/medical_safety_no_prescription.py` |
| `medical_disclaimer_required` | Regex match medical info terms → append disclaimer footer if not already present | `compliance/guardrails/medical_disclaimer_required.py` |
| `prompt_injection_block` | Pattern regex (`ignora tus instrucciones`, `forget previous`, etc.) + LLM nano classifier | `compliance/guardrails/prompt_injection_block_reuse.py` (reuses engine pattern) |

Wired via EP-13 in existing `extensions.py::register_all` (currently registered as scaffold callables; this story replaces with real implementations).

### 3.8 Engine consumption (READ-ONLY)

- NO file under `core/luana-core-*/src/` is created/modified in this story.
- All consumption via Python imports `luana_core_*` (per `pyproject.toml` workspace).
- If during builder phase a new pattern emerges reusable cross-brand → **STOP** and escalate `/pm-luana` promotion proposal in `docs/promotion-protocol/proposals/2026-MM-DD-{topic}.md` (state=draft). PR BLOCKED until proposal accepted+migrated. Builder-agentic / builder-backend MUST refuse to modify engine without ratification.

### 3.9 R23 cost-routing

- **AGENTIC tickets `production_code=true` → Opus 4.7** (state machine implementations, tool implementations consuming LLM router, slot prompts MD, observability subclasses, eval runners). NO Sonnet/qwen-opencode.
- **AGENTIC tickets `production_code=false` → Sonnet OK** (goldens YAML data, personas YAML, screening_questions_by_vertical.yaml, tests/docs about agentic).
- **BE tickets `production_code=true` → Sonnet/qwen-opencode default** (application services, repos, migrations, schema-mirror persistence models).
- **BE tickets `production_code=false` → Sonnet/qwen-opencode default** (tests, docs).

### 3.10 Default flag flips audit

**ZERO flag flips proposed.** This story does not flip any `USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, `ENABLE_*` flags. If Slice 2 adds a flag flip (e.g., toggle deepagents subagent on/off) → `.claude/rules/anti-default-flip-audit.md` 4-step audit obligatory. Tests/CONTRACT section 9.5 marked `[x] No aplica — CONTRACT no flipea defaults side-effect`.

## 4. Migration Notes (consolidated reference)

Idempotent raw SQL `IF NOT EXISTS`. New tables declared this story:

- `lead_screening_events` (tenant_id, clinic_id, lead_id, vertical, questions_asked JSONB, response_text TEXT, outcome ENUM, evaluated_at TIMESTAMPTZ, created_at, deleted_at)
- `attribution_matrix_snapshots` (tenant_id, clinic_id, period VARCHAR(7) (YYYY-MM), origin_breakdown JSONB, created_at)
- `referrals_leaderboard_snapshots` (tenant_id, clinic_id, period, top_referrers JSONB, created_at)
- `vitalia_wizard_onboarding_checkpoints` (LangGraph AsyncPostgresSaver schema — auto-managed by library; declare via `await checkpointer.setup()` in startup, but with table_prefix='vitalia_wizard_onboarding_')
- `vitalia_lucas_analysis_checkpoints` (idem with table_prefix='vitalia_lucas_analysis_')

Detail in `03-arch-be.md § 9 Migrations`. Test pre-prod clone DB workflow per `.claude/rules/backend-migrations.md`:

```bash
# Clone DB workflow
docker exec luana-vitalia-postgres-dev psql -U postgres -c "CREATE DATABASE vitalia_migration_test"
docker exec luana-vitalia-postgres-dev pg_dump -U postgres vitalia_dev -s | docker exec -i luana-vitalia-postgres-dev psql -U postgres vitalia_migration_test
docker exec -t luana-vitalia-backend-dev bash -c "cd /app && DATABASE_URL=postgresql+asyncpg://postgres@postgres:5432/vitalia_migration_test alembic stamp head && alembic upgrade head"
# Verify idempotent re-run
docker exec -t luana-vitalia-backend-dev bash -c "cd /app && DATABASE_URL=postgresql+asyncpg://postgres@postgres:5432/vitalia_migration_test alembic upgrade head"  # should be no-op, no errors
docker exec luana-vitalia-postgres-dev psql -U postgres -c "DROP DATABASE vitalia_migration_test"
```

## 5. Test Surfaces (TDD-mandatory, RED first per layer)

| Layer | Test file pattern | RED first | Surface owner |
|---|---|---|---|
| Domain entities | `vitalia/backend/tests/unit/modules/vitalia/{copilot,sales_agent,agentic/lucas}/domain/test_*.py` | YES | builder-backend |
| Application services | `vitalia/backend/tests/unit/modules/vitalia/{copilot,sales_agent,agentic/lucas}/application/services/test_*.py` | YES | builder-backend |
| Repositories (dual filter) | `vitalia/backend/tests/unit/modules/vitalia/{copilot,sales_agent}/infrastructure/repositories/test_*.py` | YES | builder-backend |
| API routes | `vitalia/backend/tests/integration/modules/vitalia/{copilot,sales_agent}/api/test_*.py` | YES | builder-backend |
| Tool unit tests | `vitalia/backend/tests/unit/modules/vitalia/{copilot,sales_agent,agentic/lucas}/tools/test_*.py` | YES | builder-agentic |
| Workflow integration | `vitalia/backend/tests/integration/modules/vitalia/copilot/workflows/test_wizard_onboarding_graph.py` + `.../agentic/lucas/workflows/test_lucas_daily_analysis_graph.py` | YES | builder-agentic |
| Goldens (12 Adrián + 4 wizard) | `vitalia/backend/tests/agentic_evals/{sales_agent,copilot}/goldens/.../{golden_name}.yaml` + runner harness | NO (data, not code) | builder-agentic (production_code=false) |
| Personas (12 Adrián + 4 wizard + 1 Lucas) | `vitalia/backend/tests/agentic_evals/sales_agent/personas/*.yaml` + `vitalia/backend/src/modules/vitalia/agentic/lucas/personas/lucas_growth_setter.yaml` | NO (data) | builder-agentic (production_code=false) |
| Voice fidelity grader smoke | `vitalia/backend/tests/agentic_evals/sales_agent/test_voice_fidelity_vitalia.py` | YES | builder-agentic |
| Medical guardrails | `vitalia/backend/tests/agentic_evals/sales_agent/test_medical_guardrails.py` | YES | builder-agentic |
| Channel guards | `vitalia/backend/tests/unit/modules/vitalia/sales_agent/test_channel_guards.py` | YES | builder-agentic |
| Cost canonicalization (PI-12 S1 T-1) | `vitalia/backend/tests/unit/modules/vitalia/{copilot,sales_agent}/observability/test_callback_handler.py` (fixtures need `litellm_call_id`) | YES | builder-backend (schema-mirror exception) |
| Architecture fitness NEW gates | `vitalia/backend/tests/architecture/test_no_observability_mirror_{copilot,sales_agent}.py` + `test_lucas_cron_tz_aware.py` + `test_screening_yaml_completeness.py` | YES | builder-backend (arch fitness test code Sonnet OK) |
| Migrations smoke | `vitalia/backend/tests/migrations/test_slice1_migrations.py` (extend existing) | NO (smoke) | builder-backend |

## 6. Research Notes (DATE-AWARE — Step 0 captured 2026-05-18)

> **Knowledge cutoff disclosure:** Opus 4.7 cutoff is Jan 2026. For LangGraph 2.0, deepagents, Anthropic prompt caching post-cutoff state — no live WebSearch was required for this story because (a) all canonical patterns are already cemented in skills referenced (sales-agent-expert, copilot-expert, tessl__langgraph, tessl__deepagents, claude-api), (b) the post-PI-12 S1 LiteLLM canonical migration (2026-05-06) is documented in skill bodies, (c) the engine layer (`core/luana-core-*/`) is READ-ONLY for this story — no novel infrastructure patterns introduced.

If during builder-agentic implementation a novel pattern is required (e.g., new deepagents `SubAgentMiddleware` config not in tile), invoke `mcp__tessl__query_library_docs("deepagents", question)` at build time (per Q4 default ratified Chris 2026-05-17 — Tessl MCP load-time SSoT).

## 7. Open Questions for PM (none — all 7 questions ratified Chris 2026-05-17 single G6 batched round)

Q1-Q4 + D1-D3 all resolved per `02-design-agentic.md § 0.2`:
- Q1 ✅ Subset MVP 3 tools Adrián (send_payment_link + reschedule_appointment + screening_questions); `send_template_confirmation` + `retract_last_message` deferred Slice 2.
- Q2 ✅ Lucas cron-only Slice 1; chat-invokable Lucas deferred Slice 3.
- Q3 ✅ Hardcoded YAML goldens Slice 1; plugin EP-registry deferred Slice 2.
- Q4 ✅ Tessl MCP load-time + offline fallback `.tessl/tiles/`.
- D1 ✅ Slot 4 MEDICAL_SAFETY_RAILS arch+design ratify only (cemented in this 03-arch + 02-design + 03-arch-agentic).
- D2 ✅ Lucas cron TZ-aware via `TenantLocationContract.timezone` (Fase A engine lift accepted/migrated).
- D3 ✅ `screening_questions` belongs to Adrián (sales_agent). Lucas is analytics cron-only. Naming canonical documented inline.

If during build a new ambiguity surfaces → /dev-team escalates to /pm-vitalia via checkpoint.md `state: blocked` with single sharp question. Builder NEVER assumes.

