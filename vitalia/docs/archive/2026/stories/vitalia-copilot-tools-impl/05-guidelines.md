# vitalia-copilot-tools-impl — Guidelines

> **Owner:** /architect Opus 4.7 · 2026-05-18
> **Consumer:** /dev-team builders + /auditor reviewers
> **Surface:** `vitalia/backend/src/modules/vitalia/{copilot,sales_agent,agentic,compliance}/` + `vitalia/backend/tests/`
> **Engine boundary:** READ-ONLY `core/luana-core-*/`

This file enumerates: (1) patterns REQUIRED, (2) patterns FORBIDDEN, (3) files in scope (NEW vs MODIFIED), (4) skills + rules to load per surface, (5) anti-patterns consolidated from 02-design § 4.5 + 03-arch-agentic § 16.

## 1. Patterns REQUIRED

### 1.1 DDD Inside-Out per `.claude/rules/backend-ddd.md`

- `domain/` pure Python — no framework deps. Entities + value objects + enums + ports (abstract base classes).
- `infrastructure/` implements ports + SA 2.0 models + adapters + repositories.
- `application/services/` orchestrate business logic — single transaction boundary per service method (`async with self.uow.begin():`).
- `api/` thin FastAPI routes — `response_model=` on every route, Bearer + X-Tenant-ID headers required.
- NO cross-module imports inside vitalia (except `vitalia/copilot/` is infra-like per backend-ddd.md). Use `core/luana-core-platform/links/` ports for cross-module shared.

### 1.2 SQLAlchemy 2.0 ONLY

```python
# REQUIRED
result = await session.execute(select(LeadScreeningEventModel).where(
    LeadScreeningEventModel.tenant_id == tenant_id,
    LeadScreeningEventModel.clinic_id == clinic_id,
    LeadScreeningEventModel.deleted_at.is_(None),
))
events = result.scalars().all()
```

### 1.3 Pydantic v2 with `model_config = ConfigDict(from_attributes=True)`

NEVER inner `class Config`. Every DTO with monetary fields includes `currency: str | None`.

### 1.4 FastAPI app config

`FastAPI(redirect_slashes=False)` at app level (parent T-arch-1 cement) — NEVER `True` (POST 307 drops body in Next.js). Arch test enforces.

### 1.5 Tenant + clinic dual filter (HIPAA-lite cardinal)

PHI-touching tables (`lead_screening_events`, `appointments`, `patient_*`, `medical_*`, `treatment_*`):

```python
.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id, Model.deleted_at.is_(None))
```

Repository methods ALL include `tenant_id: UUID` + `clinic_id: UUID` REQUIRED parameters (incl. `get_by_id`).

### 1.6 Soft delete `deleted_at` always

NEVER hard delete. Every table has `deleted_at: TIMESTAMPTZ NULL`.

### 1.7 Idempotent migrations

Raw SQL `IF NOT EXISTS` only. NEVER `op.create_table()` / `sa.Enum(create_type=True)` (broken SA 2.0.27 per `.claude/rules/backend-migrations.md`).

### 1.8 Master data + currency

- `DateTime(timezone=True)` always, store UTC via `utc_now()` helper.
- NEVER `datetime.utcnow()` (deprecated naive).
- Monetary DTOs include `currency: str | None`.
- ETL keeps source currency (Lucas analytics preserves channel-original).
- Lucas cron schedule consumes `TenantLocationContract.timezone` (Fase A engine lift).

### 1.9 PII / PHI sanitization (mandatory)

Every write to observability tables (`*_trace_event`, `*_llm_call`, `lead_screening_events`, `audit_log_vitalia`) MUST pre-process payload via:

```python
from luana_core_observability.recording.sanitization import sanitize_payload
sanitized = sanitize_payload(payload, compliance_level="hipaa_lite")
```

PHI field list SSoT: `vitalia/backend/src/modules/vitalia/compliance/phi_fields.py` (existing).

### 1.10 Audit log SYNC write (pre-response, never async fire-forget)

```python
async with self.uow.begin():
    # ... business logic ...
    await self.audit_log_repo.write_sync(
        tenant_id=tenant_id, user_id=user_id, action="...",
        resource_type="...", resource_id=..., payload_redacted=sanitize_payload(...),
    )
# response returned AFTER audit_log committed
```

Arch fitness gate `test_audit_log_sync_write.py` enforces.

### 1.11 LangGraph patterns

- TypedDict state schemas with `tenant_id: str` MANDATORY in every state.
- `iterations: int` key + max-iter guard (`if state["iterations"] > 25: return END` for wizard; bounded by stage list for Lucas).
- Conditional edges total — every branch reaches `END` or named node.
- Production checkpointer MANDATORY: `AsyncPostgresSaver.from_conn_string(settings.postgres_dsn)`. NEVER `MemorySaver`.
- Stream modes: `updates` (per-node deltas) + `messages` (token-by-token).
- NO `from __future__ import annotations` in `*/orchestrator/graph.py` (breaks LangGraph runtime introspection).

### 1.12 deepagents subagent isolation

```python
SubAgentMiddleware(
    allowed_keys_to_subagent={"extraction_subagent_input", "tenant_id"},
    allowed_keys_from_subagent={"extraction_subagent_output"},
)
```

Subagent `tools=[explicit_list]` — NEVER inherit parent toolset.

### 1.13 Tools (LangChain @tool)

- `@tool` decorator with Pydantic `args_schema` REQUIRED.
- `async def`.
- Call SERVICES (never raw repos directly).
- `tenant_id: UUID` (+ `clinic_id: UUID` for PHI-touching) REQUIRED in input schema.
- Return type: `str` (summary) for non-DTO tools, structured DTO for query/computation tools.
- Wrap external API calls with `asyncio.timeout(N)` + fallback per `tessl__graceful-degradation`.

### 1.14 Prompt cache slot architecture (Anthropic prompt caching)

Per `claude-api`:
- Slot order: invariants first, variables last. Cache marker before variable slot.
- TTL 5min default per-conversation; 1h batch (eval runners).
- Log `cache_creation_input_tokens` + `cache_read_input_tokens` per LLM call (validator catches silent invalidators).

### 1.15 LLM router LiteLLM canonical

- Use `LiteLLMService` from `core/luana-core-llm/src/luana_core_llm/providers/litellm.py`.
- Models: `kimi-k2.6` (main reasoning) + `deepseek-v4-flash` (nano classifier).
- Tier pricing >200k tokens: split at `TIER_THRESHOLD = 200_000`.
- Cost via `cost_recorder.pop_cost(litellm_call_id)` (NO `calculate_cost()` runtime).

### 1.16 Observability subclass pattern (anti-duplication §0)

```python
from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler

class VitaliaCopilotCallbackHandler(BaseAgentCallbackHandler):
    async def _persist_llm_call_row(self, payload: dict) -> None:
        sanitized = sanitize_payload(payload, compliance_level="hipaa_lite")
        try:
            await self.llm_call_repo.create(sanitized)
        except Exception as exc:
            structlog.get_logger().warning("vitalia.copilot.observability.llm_call_persist_failed", error=str(exc))
    async def _persist_trace_event_row(self, payload: dict) -> None:
        # idem
```

ONLY 2 method overrides. NEVER duplicate plumbing.

### 1.17 Engine consumption (READ-ONLY)

All engine consumption via Python imports `from luana_core_{pkg} import ...`. NEVER modify `core/luana-core-*/src/`.

### 1.18 Extension SDK registration (extend existing extensions.py)

This story REPLACES placeholders in existing `vitalia/backend/src/modules/vitalia/extensions.py::register_all` for:
- EP-3 (sales_agent_tool_register): 3 NEW Adrián tools + 4 NEW Valeria tools
- EP-4 (copilot_workflow_register): wizard_onboarding_graph
- EP-13 (sales_agent_guardrail_register): 4 real guardrail callables
- EP-N (placeholder Lucas extension — TBD per Slice 2 SDK extension proposal if needed)

NEVER add new EPs in this story. If new EP needed → escalate `/pm-luana`.

### 1.19 TDD obligatorio per `.claude/rules/tdd-mandatory.md`

For EACH layer in EACH ticket: RED test first → GREEN impl → REFACTOR. Order: domain → infrastructure → application → API.

Default flag flips: ZERO in this story (cross-cutting concern § 3.10 in 03-arch.md).

### 1.20 Spanish neutro tuteo (UI chrome)

Per `.claude/rules/spanish-text.md`: Valeria responses + Lucas card output text + error responses use tuteo (`tú/puedes/tienes/configura`). NO voseo.

**Exception:** Adrián sales_agent output respects tenant voice (compiled from `personality_profiles.system_instruction`). If tenant configures voseo, Adrián voseaa. Slot 5 `BRAND_VOICE` per-tenant invariant.

### 1.21 Conventional Commits + git safety

- `feat(vitalia-copilot): ...` `feat(vitalia-sales-agent): ...` `feat(vitalia-agentic-lucas): ...` `feat(vitalia-compliance): ...` `test(vitalia-...): ...` `chore(vitalia-migrations): ...`
- Per `.claude/rules/git-safety.md`: NO `git pull`, NO `--force`, NO `git add .` / `-A`. Stage by exact filename.
- Per `.claude/rules/git-haiku-delegation.md`: multi-file commit+push → delegate to Haiku sub-agent.

## 2. Patterns FORBIDDEN (consolidated from design § 4.5 + arch § 16)

Engine + framework:
- ❌ Modify `core/luana-core-*/src/` (engine boundary cardinal — requires `/pm-luana` promotion proposal)
- ❌ Migrar StateGraph a deepagents wholesale (deepagents only for subagent isolation in wizard extractor)
- ❌ Eliminar Closer Studio + WS + SmartBufferService + OutputManager + follow_up_engine + frozen_detection (sales-agent §3 NO se toca)
- ❌ Subagents deepagents en sales_agent (Adrián consume engine supervisor — NO parallel graph)
- ❌ Importar `copilot/` desde `sales_agent/` (o viceversa) — both consume `core/luana-core-*/`
- ❌ Tocar `PromptVersionModel`
- ❌ `from __future__ import annotations` en `*/orchestrator/graph.py`

LLM router + providers:
- ❌ Direct provider adapters bypass LiteLLM Proxy (legacy removed PI-12 S1 T-4 2026-05-06)
- ❌ Hardcodear model wire-name strings en specialists — use `LLM_ROLE_BY_SITE` SSoT engine
- ❌ DeepSeek aliases retired (`deepseek-chat`, `deepseek-reasoner`) — use `deepseek-v4-flash` / `deepseek-v4-pro`
- ❌ Tier pricing >200k tokens sin resolver — Kimi K2.6 split en `TIER_THRESHOLD = 200_000`

Channels:
- ❌ Hardcodear canales literales en código — use `get_channel_format(channel_type)` from engine
- ❌ Bypass channel registry shared

Observability + cost:
- ❌ Crear archivo nuevo en `modules/{copilot,sales_agent}/observability/recording/<X>.py` o `cost/<X>.py` o `pricing/<X>.py` — first check `.claude/rules/anti-duplication.md` inventory · EXTEND engine subclass
- ❌ Duplicar plumbing del `BaseAgentCallbackHandler` shared (only overrides agent-specific)
- ❌ Mirror `turn_envelope.py` / `callback_handler.py` / `FXResolver` / `PricingResolver` / `tenant_billing_config_repository` / `sanitization`
- ❌ `calculate_cost()` runtime (cost_usd via `pop_cost(litellm_call_id)` PI-12 S1 T-1 canonical)
- ❌ Bypass `sanitize_payload(compliance_level="hipaa_lite")` en writes a observability tables

Cache slots:
- ❌ Inyectar `{tenant_name}` mid-block cache prefix slot 5 (use slot boundary)
- ❌ Hardcoding tenant_name interpolated mid-block en cache prefix (silent invalidator)
- ❌ Timestamps en slots 1-5 cacheable (silent invalidator)
- ❌ Conversation_id en slots 1-5 cacheable (silent invalidator)
- ❌ Voice rewriter LLM pass post-generation (per `sales-agent-brand-voice.md § No-skip creep guard`)
- ❌ Brand voice summary table mirror LLM-distilled
- ❌ Fine-tuning per tenant
- ❌ Hardcoding voz en `agent_identity.j2` o specialists

Tenant + clinic isolation:
- ❌ Skip `tenant_id` filter en any query
- ❌ Skip `clinic_id` dual filter en PHI queries
- ❌ PII en logs sin `sanitize_payload(compliance_level="hipaa_lite")`
- ❌ Async fire-forget audit_log writes (must be sync pre-response per `hipaa-lite.md`)
- ❌ PHI en URLs (GET query params) — use POST body siempre

LangGraph + checkpointer:
- ❌ `MemorySaver` (tutorials only) — production MUST `AsyncPostgresSaver`
- ❌ Conversation >25 iterations (max-iter guard violation wizard)
- ❌ Tool dispatch sin Pydantic input schema
- ❌ Repo queries from tools directly (must go through service layer)

Evals:
- ❌ Skip eval goldens for new vertical (every vertical needs ≥3 goldens before ship)
- ❌ Skip channel guards for "trusted" channels (HIPAA-lite cardinal applies always)
- ❌ Spawn Lucas via chat (per Q2 default cron-only Slice 1)
- ❌ Lucas recommendations without confidence score
- ❌ Cross-brand tool import (each brand has own tools, NO cross-brand reuse — lift to engine via `/pm-luana`)

Frontend (cross-reference — FE lives in sub-stories):
- ❌ Hardcode 'USD' fallback in monetary FE (use `data.currency ?? parentData.currency`)
- ❌ Hardcoded timezone or `toLocaleDateString()` (use `useTenantLocale()` + `formatTenantDate*()`)
- ❌ Voseo in UI chrome strings (sales_agent output exempt)

Git safety:
- ❌ `git pull` (any form)
- ❌ `git push --force` / `--force-with-lease`
- ❌ `git revert` without approval
- ❌ `git add .` / `-A` / `-u`
- ❌ `git commit --no-verify`

## 3. Files in scope

### 3.1 NEW files (this story owns)

| Path | Type | Purpose |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/copilot/domain/entities/onboarding_draft.py` | Python | Domain entity |
| `vitalia/backend/src/modules/vitalia/copilot/domain/entities/wizard_slot.py` | Python | Value object |
| `vitalia/backend/src/modules/vitalia/copilot/domain/enums/wizard_state.py` | Python | StrEnum |
| `vitalia/backend/src/modules/vitalia/copilot/domain/ports/personality_service_port.py` | Python | Abstract port |
| `vitalia/backend/src/modules/vitalia/copilot/infrastructure/repositories/{onboarding_draft,onboarding_progress}_repository.py` | Python | Repos |
| `vitalia/backend/src/modules/vitalia/copilot/infrastructure/adapters/{personality_service,website_scraper,document_extractor,whisper_stt}_adapter.py` | Python | External integrations |
| `vitalia/backend/src/modules/vitalia/copilot/application/services/{onboarding_draft,extract_tenant_context,simulate_personality,complete_onboarding}_service.py` | Python | App services |
| `vitalia/backend/src/modules/vitalia/copilot/api/dtos/{extract,confirm_slot,simulate,complete}_dto.py` | Python | Pydantic v2 |
| `vitalia/backend/src/modules/vitalia/copilot/api/routes/{wizard_onboarding,lucas_cron_trigger}_routes.py` | Python | FastAPI |
| `vitalia/backend/src/modules/vitalia/copilot/persistence/models/{copilot_trace_event,copilot_llm_call}.py` | Python | Schema mirror SA 2.0 |
| `vitalia/backend/src/modules/vitalia/copilot/tools/{extract_tenant_context,confirm_slot,simulate_personality,complete_onboarding}.py` | Python | LangChain @tool |
| `vitalia/backend/src/modules/vitalia/copilot/workflows/{wizard_onboarding_state,wizard_onboarding_graph,extract_subagent,extract_subagent_tools}.py` | Python | LangGraph + deepagents |
| `vitalia/backend/src/modules/vitalia/copilot/prompts/{valeria_persona,wizard_role_vitalia,extractor_subagent}.md` | Markdown | Slot prompts |
| `vitalia/backend/src/modules/vitalia/copilot/observability/recording/{callback_handler,turn_envelope}.py` | Python | Anti-duplication subclasses |
| `vitalia/backend/src/modules/vitalia/sales_agent/domain/entities/lead_screening_event.py` | Python | Domain entity |
| `vitalia/backend/src/modules/vitalia/sales_agent/domain/enums/screening_outcome.py` | Python | StrEnum |
| `vitalia/backend/src/modules/vitalia/sales_agent/infrastructure/repositories/lead_screening_event_repository.py` | Python | Repo |
| `vitalia/backend/src/modules/vitalia/sales_agent/infrastructure/adapters/{mercadopago,whatsapp_business}_adapter.py` | Python | External integrations |
| `vitalia/backend/src/modules/vitalia/sales_agent/application/services/{screening_questions,payment_link,reschedule_appointment}_service.py` | Python | App services |
| `vitalia/backend/src/modules/vitalia/sales_agent/persistence/models/{sales_agent_trace_event,sales_agent_llm_call,lead_screening_event}.py` | Python | Schema mirror SA 2.0 |
| `vitalia/backend/src/modules/vitalia/sales_agent/tools/{send_payment_link,reschedule_appointment,screening_questions}.py` | Python | LangChain @tool |
| `vitalia/backend/src/modules/vitalia/sales_agent/workflows/vitalia_state_overlay.py` | Python | State extension overlay |
| `vitalia/backend/src/modules/vitalia/sales_agent/personas/{warm_close_default,warm_close_dental,warm_close_estetica,warm_close_psicologia,warm_close_fertilidad}.yaml` | YAML | Personas (data, `production_code=false` Sonnet OK) |
| `vitalia/backend/src/modules/vitalia/sales_agent/prompts/{medical_vertical,medical_safety_rails}.md` | Markdown | Slot 2 + Slot 4 |
| `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/{callback_handler,turn_envelope}.py` | Python | Anti-duplication subclasses |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/domain/entities/{stage_recommendation,attribution_matrix_snapshot,referrals_leaderboard_snapshot}.py` | Python | Domain entities |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/domain/enums/stage.py` | Python | StrEnum |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/infrastructure/repositories/{stage_recommendation,attribution_matrix_snapshot,referrals_leaderboard_snapshot}_repository.py` | Python | Repos |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/infrastructure/adapters/analytics_engine_query_adapter.py` | Python | Port to luana_core_analytics_engine |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/{lucas_stage_recommendation,lucas_attribution,lucas_referrals}_service.py` | Python | App services |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/persistence/models/{stage_recommendation,attribution_matrix_snapshot,referrals_leaderboard_snapshot}.py` | Python | Schema mirror SA 2.0 |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/{compute_stage_recommendation,compute_attribution_matrix,compute_referrals_leaderboard}.py` | Python | LangChain @tool |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/{lucas_analysis_state,lucas_daily_analysis_graph}.py` | Python | LangGraph ReAct |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/personas/lucas_growth_setter.yaml` | YAML | Persona (Sonnet OK) |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/prompts/{lucas_growth_setter_role,lucas_stage_reasoning_frame}.md` | Markdown | Slot prompts |
| `vitalia/backend/src/modules/vitalia/agentic/screening/screening_questions_by_vertical.yaml` | YAML | SSoT screening (Sonnet OK data) |
| `vitalia/backend/src/modules/vitalia/persistence/migrations/{017_lead_screening_events,018_attribution_matrix_snapshots,019_referrals_leaderboard_snapshots,020_langgraph_checkpoint_tables,021_screening_outcome_enum_check}.py` | Python | Idempotent migrations |
| `vitalia/backend/tests/architecture/{test_no_observability_mirror_copilot,test_no_observability_mirror_sales_agent,test_lucas_cron_tz_aware,test_screening_yaml_completeness}.py` | Python | Arch fitness gates NEW |
| `vitalia/backend/tests/unit/modules/vitalia/{copilot,sales_agent,agentic/lucas}/...` | Python | Unit tests per layer |
| `vitalia/backend/tests/integration/modules/vitalia/{copilot,sales_agent}/...` | Python | Integration tests |
| `vitalia/backend/tests/agentic_evals/sales_agent/goldens/{dental,estetica,psicologia,fertilidad}/*.yaml` (12) | YAML | Goldens (Sonnet OK) |
| `vitalia/backend/tests/agentic_evals/sales_agent/personas/*.yaml` (12) | YAML | Personas (Sonnet OK) |
| `vitalia/backend/tests/agentic_evals/sales_agent/test_pass_k_evaluation.py` + `test_voice_fidelity_vitalia.py` + `test_medical_guardrails.py` | Python | Runners |
| `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/{happy,negative,edge_browser_close,adversarial}.yaml` | YAML | Goldens (Sonnet OK) |
| `vitalia/backend/tests/agentic_evals/copilot/wizard_personas/*.yaml` (4) | YAML | Personas (Sonnet OK) |
| `vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py` | Python | Runner |
| `vitalia/backend/tests/agentic_evals/agentic/lucas/test_lucas_smoke.py` | Python | Smoke runner |
| `vitalia/backend/tests/agentic_evals/cache/test_vitalia_cache_hit_rate.py` | Python | Cache validation |
| `vitalia/backend/tests/agentic_evals/cost_budget/test_vitalia_cost_budget.py` | Python | Budget caps |

### 3.2 MODIFIED files

| Path | What changes |
|---|---|
| `vitalia/backend/src/modules/vitalia/extensions.py` | EXTEND existing `register_all` — replace placeholders with real tool callables (EP-3 wires 7 NEW tools: 4 Valeria + 3 Adrián), copilot workflow (EP-4 wires wizard_onboarding_graph), real medical guardrails (EP-13 wires 4 real callables). Lucas tools may be invoked via cron worker direct import (NOT EP — internal). |
| `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_safety_no_diagnosis.py` | REPLACE placeholder with real diagnosis term regex + LLM nano classifier |
| `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_safety_no_prescription.py` | REPLACE placeholder |
| `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_disclaimer_required.py` | REPLACE placeholder |
| `vitalia/backend/src/modules/vitalia/compliance/guardrails/prompt_injection_block_reuse.py` | REPLACE placeholder |
| `vitalia/backend/tests/architecture/__init__.py` | Append imports for 4 NEW arch fitness gate test modules |
| `vitalia/docs/product/modules/copilot.md` | Document 4 NEW Valeria tools + wizard supervisor topology |
| `vitalia/docs/product/modules/sales_agent.md` | Document 3 NEW Adrián tools subset MVP + Slot 4 MEDICAL_SAFETY_RAILS NEW + deferred Slice 2 tools |
| `vitalia/docs/product/modules/agentic.md` (NEW or EXTEND) | Document Lucas cron analysis + 3 tools |
| `vitalia/docs/product/modules/compliance.md` | Document 4 medical guardrails real impl + EP-13 wiring |

### 3.3 NOT TOUCHED (engine — READ-ONLY consult)

- `core/luana-core-copilot/src/luana_core_copilot/` — engine
- `core/luana-core-sales-agent/src/luana_core_sales_agent/` — engine (§3 NO se toca)
- `core/luana-core-observability/src/luana_core_observability/` — engine (anti-duplication §0)
- `core/luana-core-brand-studio/src/luana_core_brand_studio/` — engine
- `core/luana-core-llm/src/luana_core_llm/` — engine
- `core/luana-core-billing/src/luana_core_billing/` — engine
- `core/luana-core-compliance/src/luana_core_compliance/` — engine
- `core/luana-core-channels/src/luana_core_channels/` — engine
- `core/luana-core-platform/src/luana_core_platform/` — engine (incl. `TenantLocationContract` Fase A)
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/` — engine
- `core/luana-core-events/src/luana_core_events/` — engine
- `core/luana-core-analytics-engine/src/luana_core_analytics_engine/` — engine

## 4. Skills + rules to load per surface

### 4.1 builder-agentic (Opus 4.7 R23 production_code=true)

**Skills (mandatory):**
- `copilot-expert` (Valeria wizard surface)
- `sales-agent-expert` (Adrián surface)
- `brand-expert` (wizard personality_service integration)
- `tessl__langgraph` (supervisor + ReAct + AsyncPostgresSaver + stream modes)
- `tessl__deepagents` (SubAgentMiddleware sandbox)
- `tessl__graceful-degradation` (external tool wrappers)
- `claude-api` (prompt caching slot validation)
- `metrics-expert` (Lucas analytics queries — invoked when touching Lucas)

**Rules (load on demand):**
- `.claude/rules/anti-duplication.md` — § Inventario + § Multibrand awareness (CARDINAL)
- `.claude/rules/copilot-resilience.md` — debugging copilot
- `.claude/rules/copilot-observability.md` — recording layer
- `.claude/rules/sales-agent-brand-voice.md` — SSoT voice
- `vitalia/.claude/rules/hipaa-lite.md` — CARDINAL dual filter + PHI + channel guards + medical guardrails (REUSE existing scaffold)
- `.claude/rules/tenant-isolation.md` — root cardinal
- `.claude/rules/tdd-mandatory.md` — RED first per layer
- `.claude/rules/anti-default-flip-audit.md` — N/A this story (no flips)
- `.claude/rules/spanish-text.md` — UI chrome tuteo (Valeria + Lucas only)
- `.claude/rules/auditor-downstream-regression.md` — downstream test paths surface map

### 4.2 builder-backend (Sonnet/qwen-opencode default; Opus only for arch fitness test files in edge cases)

**Skills:**
- `backend-expert` (DDD Inside-Out, arch fitness, migrations, master-data, currency-handling)
- `tessl__fastapi` (response_model PII allowlist)
- `tessl__pytest-api-testing`

**Rules (load on demand):**
- `.claude/rules/backend-ddd.md` — Inside-Out + schema-mirror exception
- `.claude/rules/backend-migrations.md` — idempotent raw SQL
- `.claude/rules/backend-quality.md` — ruff + arch fitness gates
- `.claude/rules/master-data.md` — UTC + tenant locale
- `.claude/rules/currency-handling.md` — DTO currency field
- `.claude/rules/architectural-fitness.md` — ratchet shrink-only
- `.claude/rules/tenant-isolation.md` — root cardinal
- `.claude/rules/tdd-mandatory.md`
- `vitalia/.claude/rules/hipaa-lite.md` — CARDINAL

### 4.3 auditor-agentic (Opus 4.7)

Same skills + rules as builder-agentic + additionally:
- `.claude/rules/auditor-downstream-regression.md` (SSoT scope mapping; references doc `.claude/rules/references/auditor-downstream-targets.md`)

### 4.4 auditor-backend (Opus 4.7)

Same skills + rules as builder-backend + additionally:
- `.claude/rules/auditor-downstream-regression.md`

## 5. Cross-cutting consistency (anti-pattern detection)

If builder discovers a pattern that emerges reusable cross-brand (e.g., screening_questions infra for Lupulo dietary screening) → **STOP** and:

1. Document discovery in `vitalia/docs/learnings/2026-MM-DD-{topic}.md` with `promotable: candidate`.
2. Open `/pm-luana` promotion proposal at `docs/promotion-protocol/proposals/2026-MM-DD-{topic}.md` (state=draft).
3. Block PR until proposal accepted + migrated.

Builder NEVER modifies engine without ratified proposal.

## 6. Hot-fix repro (N/A this story — feature build, not hot-fix)

Per `.claude/rules/hotfix-repro-mandatory.md`: this story is a feature build, NOT a hot-fix. `repro_verified` field N/A in tickets.

## 7. Process metrics emission (per `dev-team` + `auditor` skill)

`/dev-team` + `/auditor` emit metrics via `scripts/emit_process_metric.py` per `docs/process/metrics/README.md`:
- ticket_completion_time
- iterations_per_ticket
- agentic_eval_pass_rate
- cost_per_tenant_session
