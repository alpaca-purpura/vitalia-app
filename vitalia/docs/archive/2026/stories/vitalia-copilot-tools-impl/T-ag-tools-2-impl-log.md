---
ticket: T-ag-tools-2
story: vitalia-copilot-tools-impl
brand: vitalia
state: developing
builder: claude-opus-4-7
production_code: true
r23_compliant: true
started_at: 2026-05-18
---

# T-ag-tools-2 — IMPL-LOG

> Adrián 3 tools subset MVP + Slot 4 MEDICAL_SAFETY_RAILS prompt + Slot 2 medical_vertical
> + observability subclass + 4 medical guardrails real impl + 5 personas YAML + state overlay.

## Step 0 — Date capture (R23 anchor)

`date -u +%Y-%m-%d` → **2026-05-18** (matches CLAUDE.md currentDate).
Underlying knowledge cutoff Jan 2026; state-of-the-art validation anchored on canonical docs URLs cited below.

## Skills Consulted (Step 0 GATE)

### `copilot-expert` (invoked)
**Reason:** ticket touches `vitalia/backend/src/modules/vitalia/{sales_agent,compliance}/` — agentic surfaces.
**Decision captured:** anti-duplication §0 cardinal applies. Observability/cost/pricing/turn_envelope/callback-handler patterns live in `core/luana-core-observability/` engine. NEVER mirror. EXTEND via subclass. Engine `BaseAgentCallbackHandler` + `BaseObservabilityContext` are abstract; vitalia subclass implements only `_persist_llm_call_row` + `_persist_trace_event_row` for callback handler + `_add_trace_event` + `_aggregate_totals` + `_legacy_compat_keys_or_empty` for context. Also: SSE v2 protocol applies for any streaming (none in this ticket).

### `sales-agent-expert` (invoked)
**Reason:** ticket creates `sales_agent/tools/` + prompts + personas + state overlay.
**Decision captured:**
- §0 anti-duplication: same as copilot-expert (callback handler + turn_envelope subclass pattern from engine `core/luana-core-sales-agent/src/luana_core_sales_agent/observability/recording/{callback_handler,turn_envelope}.py`).
- §3 NO se toca: engine sales_agent `OutputManager` chunking + Closer Studio + SmartBufferService preserved. Vitalia consumes engine LangGraph directly; brand state overlay registered via `register_state_extension()` API (read-only consume).
- Slot 5 BRAND_VOICE per-tenant (NOT in scope this ticket — comes from `personality_profiles.system_instruction`).
- Slot 4 MEDICAL_SAFETY_RAILS already EXISTS at `vitalia/backend/src/modules/vitalia/agentic/prompts/slot_4_medical_safety_rails.j2` (Story 11 T-prompts-1 cement). I create a SISTER MD at the ticket-prescribed path that re-emits the same canonical content (anti-duplication: load via shared loader, no inline duplication of regex/policy strings).
- Voice fidelity respects tenant voice — voseo OK if tenant configures.
- Channel format dispatch via engine `format_for_channel` (NEVER hardcode channel literals).

### `tessl__langgraph` (NOT invoked this ticket)
**Reason for skip:** T-ag-tools-2 does not modify LangGraph state/edges/nodes/graph compile. State **overlay** (`VitaliaSalesAgentStateExtension`) is a TypedDict definition only — registered via engine `register_state_extension()` (consumed, NOT modified). LangGraph supervisor topology + nodes live in T-ag-workflows-1 (Valeria) and engine (Adrián). Skipping is safe per ticket scope.

### `tessl__graceful-degradation` (invoked)
**Reason:** tools call services that wrap external adapters (MercadoPago, WhatsApp, LLM). Skill anchored via existing services (`payment_link_service.py` already has try/except; `screening_questions_service.py` graceful-degrades LLM parse errors).
**Decision captured:** tools themselves wrap service calls in try/except with structlog warning + best-effort observability writes. Tool-level network/timeout failures already handled by the wrapped service (which uses `asyncio.wait_for` patterns with retry-backoff inside adapters). Per `tessl__graceful-degradation` rule 1+2: every external call has a fallback path. Tool surface adds NO additional external calls — pure service wrapper.

### `tessl__pytest-api-testing` (invoked)
**Reason:** test surface includes async tool unit tests + observability callback handler unit test. Existing test patterns in `vitalia/backend/tests/unit/modules/vitalia/sales_agent/application/services/` (T-be-services-2 result) use `pytest.mark.asyncio` + AsyncMock fixtures. I mirror that pattern.
**Decision captured:** AsyncMock for service dependencies, `pytest.mark.asyncio` for async tests, factory fixtures for tool input DTOs. No live DB needed (tools call mocked service interfaces; observability persistence injected as protocol mock).

### `claude-api` (invoked)
**Reason:** prompts include cache slot architecture; ticket explicitly tracks `cache_creation_input_tokens` + `cache_read_input_tokens` per LLM call for silent invalidator detection.
**Decision captured:** slot 4 MEDICAL_SAFETY_RAILS MUST stay byte-equal across turns (no timestamps / conversation_id / random IDs / tenant_name mid-block). Existing `agentic/prompts/slot_4_medical_safety_rails.j2` is the canonical content. My `sales_agent/prompts/medical_safety_rails.md` is a thin re-export pointer (anti-duplication §0 LIFT-TO-SHARED variant). TTL 5min default for per-turn; 1h for batch eval.

## Step 0.5 — Default flip detection

NO default flag flip in this ticket. Verified: no edit to `core/luana-core-platform/src/luana_core_platform/config.py` defaults (engine read-only). No flip audit needed.

## Cross-module audit (NO-NEW-LAYER, per anti-duplication.md)

**Existing engine abstractions reused (NOT mirrored):**

| Pattern | Engine canonical path | How vitalia consumes |
|---|---|---|
| Callback handler base | `luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler` | `VitaliaSalesAgentCallbackHandler(BaseAgentCallbackHandler)` subclass |
| Turn envelope base | `luana_core_observability.recording.turn_envelope.BaseObservabilityContext` | `VitaliaSalesAgentObservabilityContext(BaseObservabilityContext)` subclass |
| PII sanitization | `luana_core_observability.recording.sanitization.sanitize_payload` | Imported, NEVER re-implemented |
| Compliance service | `luana_core_compliance.ComplianceService` | Wrapped via `VitaliaComplianceAdapter` (Story 11 existing) |
| Engine sales_agent callback | `luana_core_sales_agent.observability.recording.callback_handler.SalesAgentCallbackHandler` | Inheritance chain (NOT direct subclass — vitalia goes one level up to BaseAgentCallbackHandler with vitalia-specific repo mirror) |
| Engine sales_agent context | `luana_core_sales_agent.observability.recording.turn_envelope.SalesAgentObservabilityContext` | Same — vitalia inherits BaseObservabilityContext directly with vitalia mirror repo |
| FXResolver / PricingResolver | `luana_core_observability.cost.*` | Injected via factory at runtime (constructor params) — NEVER re-implemented |
| Slot 4 prompt | `vitalia/backend/src/modules/vitalia/agentic/prompts/slot_4_medical_safety_rails.j2` | NEW `sales_agent/prompts/medical_safety_rails.md` is a thin wrapper that loads same canonical content (no duplication of regex/policy strings) |
| Existing medical guardrails | `vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_{diagnosis,prescription}.py` (Story 11) | NEW `compliance/guardrails/*.py` re-export shims (delegate to agentic/ canonical impl — no logic duplication) |

**NO new abstraction layer introduced.** All new files either:
- Subclass engine base (callback handler, turn envelope)
- Wrap existing services (tools)
- Re-export canonical impl (slot 4 prompt MD, medical guardrails)
- Define new domain TypedDict (state overlay — no engine equivalent)
- Define new safety guardrails (disclaimer_required, prompt_injection_block_reuse — NEW, no engine equivalent)

## Cross-brand mirror scan

```bash
for OTHER in nicolify comunify lupulo; do
  find ${WS}/$OTHER/backend/src -name "callback_handler.py" -o -name "turn_envelope.py" -o -name "medical_safety_*.py" 2>/dev/null
done
```
Result: no matches in nicolify/comunify/lupulo for medical_safety_*, callback_handler.py, turn_envelope.py. Vitalia is the only brand creating these surfaces (medical vertical). NO cross-brand mirror risk.

## Engine boundary verification

```bash
git diff main..HEAD -- 'core/luana-core-*/src/**' 2>/dev/null
```
Result: 0 modifications to engine src/. Vitalia ticket touches only `vitalia/backend/` paths.

## Files created (T-ag-tools-2)

### Adrián 3 tools subset MVP
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/screening_questions.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/payment_link.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/reschedule_appointment.py`

### Slot prompts MD
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/medical_safety_rails.md` (Slot 4 — delegates to agentic/prompts/slot_4_medical_safety_rails.j2 canonical)
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/medical_vertical.md` (Slot 2 — NEW)
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/adrian_persona_base.md` (Slot 5 base persona — brand default, tenant overrides)

### 5 personas YAML (sales_agent production personas — distinct from rubric eval personas)
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_default.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_dental.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_estetica.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_psicologia.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_fertilidad.yaml`

### Medical guardrails service (4 guardrails real impl per ticket scope)
- `vitalia/backend/src/modules/vitalia/sales_agent/application/services/medical_guardrails_service.py`

### Medical guardrail callables at compliance/guardrails (re-export / new impl)
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_safety_no_diagnosis.py` (re-export agentic/)
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_safety_no_prescription.py` (re-export agentic/)
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_disclaimer_required.py` (NEW)
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/prompt_injection_block_reuse.py` (NEW)

### State overlay
- `vitalia/backend/src/modules/vitalia/sales_agent/domain/state_overlay.py`

### Observability subclasses (anti-duplication §0)
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/callback_handler.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/turn_envelope.py`

### Extension SDK wire (EDIT existing)
- `vitalia/backend/src/modules/vitalia/extensions.py` — EP-3 replace 3 placeholders (or add 3 new tool defs for Adrián MVP); EP-13 replace 4 placeholders with real callables.

### Tests (NEW)
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/tools/test_screening_questions.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/tools/test_payment_link.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/tools/test_reschedule_appointment.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/services/test_medical_guardrails_service.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/observability/test_callback_handler.py`
- `vitalia/backend/tests/architecture/test_no_observability_mirror_sales_agent.py`
- `vitalia/backend/tests/agentic_evals/sales_agent/test_medical_guardrails.py` (★ adversarial cases)

## State-of-the-art validation (Step 0 date 2026-05-18)

Anchored on canonical official docs (these never go obsolete):
- LangGraph: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` — for state overlay TypedDict patterns.
- deepagents: `https://docs.langchain.com/oss/python/deepagents/overview` — NOT used this ticket (Valeria uses, not Adrián).
- Anthropic prompt caching: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` — Slot 4 cacheable invariant (no timestamps / conversation_id / random IDs).

Engine canonical contracts (READ-ONLY, current cement as of 2026-05-18):
- `BaseAgentCallbackHandler` abstract methods: `_persist_llm_call_row(**kwargs)` + `_persist_trace_event_row(**kwargs)` accepting `**agent_specific` for `lead_id` + `channel_type`.
- `BaseObservabilityContext` abstract methods: `_add_trace_event` + `_aggregate_totals` + `_legacy_compat_keys_or_empty`.
- LiteLLM canonical cost path: `cost_recorder.pop_cost(litellm_call_id)` (PI-12 S1 T-1 cement 2026-05-02). Tests inject `litellm_call_id` in `response_metadata`.

## Notes

- §3 NO se toca: NO modify of engine sales_agent OutputManager / Closer Studio / SmartBufferService / follow_up_engine / agent_state_checkpoints.
- Engine boundary: NO modify of `core/luana-core-*/src/`. Read-only consume.
- Cache prefix safety: medical_safety_rails.md and medical_vertical.md contain NO timestamps / conversation_id / random IDs / tenant_name interpolated mid-block. LLM-side substitution markers `{doctor_specialty}` etc. are OK (model fills at generation time).
- 5 personas YAML are PRODUCTION personality archetype configs (consumed by sales_agent compiler v2 slot 5 BRAND_VOICE when tenant.personality_profile_id points to a brand default). Distinct from `docs/specs/personas/archetype-aware/patient-*.yaml` (rubric eval personas — Story 11).
- Anti-duplication enforced: medical_safety_no_diagnosis + medical_safety_no_prescription canonical impls live at `agentic/guardrails/` (Story 11 cement). NEW `compliance/guardrails/*` files are re-export shims (mostly delegate to canonical via `from … import *` or named re-exports) — keeps EP-13 wire pointing to a `compliance/`-domain callable while preserving SSoT at `agentic/`.
