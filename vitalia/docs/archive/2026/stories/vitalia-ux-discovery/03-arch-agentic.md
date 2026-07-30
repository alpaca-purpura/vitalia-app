# vitalia-ux-discovery — Agentic sub-architecture

> **Consumer:** `builder-agentic` (Opus 4.7 R23 production) + `auditor-agentic` (Opus 4.7).
> **Index:** `03-arch.md` § 0-10 (read first).
> **Brand surface:** `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/{tools,extractors,workflows,kb,personas,goldens}/` + `vitalia/backend/src/modules/vitalia/agentic/`.
> **Engine consultation:** READ-ONLY `core/luana-core-{copilot,sales-agent,brand-studio,observability,llm,billing,compliance}/`.

> **R23 cost-routing:** all `production_code: true` tickets MUST use Opus 4.7 (NO Sonnet/opencode). Tests + goldens + docs about agentic = `production_code: false` → Sonnet OK.
>
> **Anti-duplication §0 cardinal:** NEVER mirror engine observability/cost/pricing/turn_envelope/callback_handler/FX/tenant_billing/PII patterns. EXTEND via heredancia or escalate LIFT-TO-SHARED via `/pm-luana` if not yet shared. Inventory en `.claude/rules/anti-duplication.md`.

## 1. Agentic surface map

```
vitalia/backend/src/modules/vitalia/
├── copilot/                                ← Valeria (rail derecho + wizard onboarding)
│   ├── extractors/
│   │   ├── medical_kb_extractor.py        ← (existing Story 11 placeholder)
│   │   └── dental_history_extractor.py    ← (existing placeholder)
│   ├── tools/
│   │   ├── extract_tenant_context.py      ← NEW Slice 1 (wizard tool — depends side story)
│   │   ├── confirm_slot.py                ← NEW Slice 1
│   │   ├── simulate_personality.py        ← NEW Slice 1 (wrapper engine personality_service.simulate)
│   │   └── complete_onboarding.py         ← NEW Slice 1 (commit draft + activate)
│   ├── workflows/
│   │   ├── wizard_onboarding_graph.py     ← NEW Slice 1 (LangGraph supervisor topology)
│   │   └── treatment_followup_workflow.py ← (existing Story 11 stub)
│   ├── kb/
│   │   ├── medical_kb_dental/             ← markdown chunks (T-kb-1)
│   │   ├── medical_kb_psychology/         ← (T-kb-2)
│   │   └── medical_kb_psychiatry/         ← (T-kb-3)
│   ├── observability/
│   │   └── (REUSE engine — NO mirror per anti-duplication §0)
│   ├── persistence/
│   │   └── models/                         ← Schema mirror tables ONLY (per backend-ddd.md schema-mirror exception)
│   │       ├── copilot_trace_event.py     ← mirror engine schema (no logic)
│   │       └── copilot_llm_call.py        ← mirror engine schema (no logic)
│   └── prompts/
│       └── valeria_persona.md              ← Slot 4 specialist persona
├── sales_agent/                            ← Adrián (closer)
│   ├── tools/
│   │   ├── send_template_confirmation.py  ← NEW Slice 1
│   │   ├── send_payment_link.py           ← NEW Slice 1
│   │   ├── reschedule_appointment.py      ← NEW Slice 1
│   │   ├── retract_last_message.py        ← NEW Slice 1 (5min undo support)
│   │   └── screening_questions.py         ← NEW Slice 1 (Lucas screening clínico per vertical)
│   ├── personas/
│   │   ├── warm_close_default.yaml         ← default (per brand.yaml)
│   │   ├── warm_close_dental.yaml
│   │   ├── warm_close_estetica.yaml
│   │   ├── warm_close_psicologia.yaml
│   │   └── warm_close_fertilidad.yaml
│   ├── goldens/
│   │   ├── dental/                         ← 3 escenarios
│   │   ├── estetica/                       ← 3 escenarios
│   │   ├── psicologia/                     ← 3 escenarios
│   │   └── fertilidad/                     ← 3 escenarios (total 12 goldens per persona Owner)
│   ├── prompts/
│   │   └── adrian_persona_compiler.py      ← consume engine personality_service
│   ├── observability/
│   │   └── (REUSE engine)
│   └── persistence/
│       └── models/                         ← Schema mirror tables ONLY
│           ├── sales_agent_trace_event.py
│           └── sales_agent_llm_call.py
└── agentic/                                ← Brand-wide agentic shared (Lucas growth setter)
    ├── lucas/
    │   ├── tools/
    │   │   ├── compute_stage_recommendation.py     ← NEW Slice 1
    │   │   ├── compute_attribution_matrix.py       ← NEW Slice 1
    │   │   └── compute_referrals_leaderboard.py    ← NEW Slice 1
    │   ├── workflows/
    │   │   └── lucas_daily_analysis_graph.py       ← cron-triggered LangGraph
    │   └── personas/
    │       └── lucas_growth_setter.yaml
    └── screening/
        └── screening_questions_by_vertical.yaml    ← SSoT screening per vertical (dental/estética/psicología/fertilidad)
```

## 2. Agentic state schemas (TypedDict per `tessl__langgraph`)

### 2.1 Wizard onboarding state (`WizardOnboardingState`)

```python
# vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_onboarding_state.py
from typing import TypedDict, Annotated, Literal
from operator import add
from langgraph.graph.message import add_messages

class WizardSlot(TypedDict):
    slot_id: str
    value: str | dict | None
    confidence: float  # 0.0-1.0
    confirmed_at: str | None  # ISO datetime

class WizardOnboardingState(TypedDict):
    # Tenant isolation (CARDINAL)
    tenant_id: str
    user_id: str
    clinic_id: str | None  # may not exist yet — onboarding creates it
    
    # Conversation
    messages: Annotated[list, add_messages]
    iterations: int  # max-iter guard (cap 25 per copilot-resilience)
    
    # Slots
    slots_required_confirmed: dict[str, WizardSlot]  # tenant.name, tenant.vertical, tenant.location
    slots_optional_confirmed: dict[str, WizardSlot]  # brand.tone_default, offer[0]
    slots_pending: list[str]  # slot_ids awaiting extraction or confirmation
    bonus_extracted: dict[str, WizardSlot]  # NLU bonus (team, values, differentiators, contact, offer_catalog_full)
    
    # Mode
    mode: Literal["libre", "guiado"] | None
    
    # Live preview
    voice_profile_partial: dict | None  # compiled by personality_service
    voice_samples: list[dict]  # [{slot_relevant, scenario, sample_text, generated_at}]
    landing_preview_url: str | None
    
    # Subagent isolation (deepagents)
    extraction_subagent_input: dict | None  # passed via allowed_keys_to_subagent
    extraction_subagent_output: dict | None  # returned via allowed_keys_from_subagent
    
    # Compliance
    pii_detected_in_doc: bool
    consent_voice_activation: bool  # explicit consent before final compile
    
    # Errors
    last_error: dict | None
    task_complete: bool
```

### 2.2 Adrián sales_agent state (consumes engine — extension overlay)

Engine state schema lives in `core/luana-core-sales-agent/`. Vitalia EXTENDS via additional keys:

```python
class VitaliaSalesAgentStateExtension(TypedDict, total=False):
    # Vitalia-specific overlay (merged with engine SalesAgentState via reducer)
    clinic_id: str  # MANDATORY for Vitalia turns
    vertical: Literal["dental", "estetica", "psicologia", "fertilidad", "otro"]
    screening_outcome: dict | None  # Lucas screening per vertical
    medical_disclaimer_shown: bool  # guardrail tracker
    phi_blocked_messages: list[dict]  # ComplianceService blocks for audit
```

### 2.3 Lucas growth setter state (cron-triggered)

```python
class LucasAnalysisState(TypedDict):
    tenant_id: str
    clinic_id: str
    analysis_date: str  # YYYY-MM-DD
    stages_to_analyze: list[Literal["attraction", "qualification", "reservation", "adoption", "expansion"]]
    
    # Per-stage outputs
    stage_recommendations: Annotated[list[dict], add]  # accumulator
    attribution_matrix: dict | None
    referrals_leaderboard: list[dict] | None
    
    iterations: int
    task_complete: bool
```

## 3. Topology (supervisor pattern for wizard onboarding)

Per `tessl__langgraph` + `tessl__deepagents`:

### 3.1 Wizard onboarding graph (supervisor topology)

```python
# vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_onboarding_graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

def build_wizard_onboarding_graph(settings: Settings):
    """Wizard onboarding supervisor topology:
    
    [START] → supervisor
                ↓ route based on state
              ┌─→ extract_subagent (URL/doc/audio via deepagents.task)
              │
              ├─→ slot_question_router (Valeria asks next slot natural)
              │
              ├─→ live_preview_router (debounced simulate_personality)
              │
              ├─→ completion_router (final commit)
              │
              └─→ END (task_complete=True OR iterations > 25)
    """
    graph = StateGraph(WizardOnboardingState)
    
    graph.add_node("supervisor", route_supervisor)
    graph.add_node("extract_subagent", extract_subagent_node)  # deepagents.task subagent
    graph.add_node("slot_question_router", slot_question_node)
    graph.add_node("live_preview_router", live_preview_node)
    graph.add_node("completion_router", completion_node)
    
    # Conditional edges (every branch reaches END or named node)
    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        decide_next_node,
        {
            "extract": "extract_subagent",
            "ask_slot": "slot_question_router",
            "preview": "live_preview_router",
            "complete": "completion_router",
            "end": END,
        },
    )
    graph.add_edge("extract_subagent", "supervisor")  # return to supervisor after subagent
    graph.add_edge("slot_question_router", "supervisor")
    graph.add_edge("live_preview_router", "supervisor")
    graph.add_edge("completion_router", END)
    
    # Production checkpointer (MANDATORY — NEVER MemorySaver)
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.postgres_dsn)
    return graph.compile(checkpointer=checkpointer)
```

**Max-iter guard:** `if state["iterations"] > 25: return END` per `copilot-resilience.md` `COPILOT_RECURSION_LIMIT`.

### 3.2 deepagents subagent (extract_subagent)

Per `tessl__deepagents`:

```python
from deepagents import SubAgentMiddleware

extract_subagent = create_subagent(
    name="vitalia_wizard_extractor",
    tools=[
        # Sandbox — explicit tools (NO inherit parent)
        scrape_website_tool,
        parse_document_tool,
        transcribe_audio_tool,
    ],
    middleware=SubAgentMiddleware(
        allowed_keys_to_subagent={"extraction_subagent_input", "tenant_id"},
        allowed_keys_from_subagent={"extraction_subagent_output"},
    ),
    instructions=open("prompts/extractor_subagent.md").read(),
)
```

### 3.3 Adrián sales_agent (consume engine — no parallel graph)

Adrián consumes engine `core/luana-core-sales-agent/` LangGraph directly via brand extension overlay. NO parallel graph in `vitalia/`. Brand-specific tools registered via EP-3 from `extensions.py`.

### 3.4 Lucas daily analysis (cron-triggered subgraph)

Simple ReAct agent (no supervisor) — single role compute recommendations per stage.

## 4. Tools (Slice 1 NEW)

### 4.1 Valeria copilot tools (wizard onboarding — side story `vitalia-copilot-tools-impl`)

| Tool | Path | Input schema | Returns | Tenant-scoped | External calls |
|---|---|---|---|---|---|
| `extract_tenant_context` | `vitalia/backend/src/modules/vitalia/copilot/tools/extract_tenant_context.py` | `ExtractInput(urls, doc_uploads, audio_uploads, tenant_id, user_id)` | `ExtractResponse` (slots + confidence) | YES | YES — `website_scraper` + `document_extractor` + Whisper STT (timeout+fallback per `tessl__graceful-degradation`) |
| `confirm_slot` | `.../confirm_slot.py` | `ConfirmSlotInput(slot_id, value, tenant_id, user_id)` | `ConfirmSlotResponse` | YES | none (DB write only) |
| `simulate_personality` | `.../simulate_personality.py` | `SimulateInput(profile_partial, scenario, tenant_id)` | `SimulateResponse` (sample text) | YES | YES — wraps engine `personality_service.simulate` + LLM call Kimi/DeepSeek (throttle 5/min/tenant + cache) |
| `complete_onboarding` | `.../complete_onboarding.py` | `CompleteInput(draft_id, tenant_id, user_id)` | `CompleteResponse` | YES | YES — engine `personality_service.compile_full` + BrandStudio commit |

All tools `@tool` decorated, async, call SERVICES (never raw repos), `tenant_id` mandatory.

### 4.2 Adrián sales_agent tools (Slice 1 NEW)

| Tool | Path | Input schema | Returns | Tenant-scoped | External calls |
|---|---|---|---|---|---|
| `send_template_confirmation` | `vitalia/backend/src/modules/vitalia/sales_agent/tools/send_template_confirmation.py` | `SendTemplateInput(template_id, slot_values, conv_id, tenant_id, clinic_id)` | `str` (summary) | YES + dual filter | YES — WhatsApp Business API (timeout+fallback) |
| `send_payment_link` | `.../send_payment_link.py` | `SendPaymentLinkInput(appointment_id, deposit_percent, tenant_id, clinic_id)` | `str` | YES + dual filter | YES — Mercado Pago API + WhatsApp Business API (timeout+fallback) |
| `reschedule_appointment` | `.../reschedule_appointment.py` | `RescheduleInput(appointment_id, new_starts_at, reason, tenant_id, clinic_id)` | `str` | YES + dual filter | none (DB) |
| `retract_last_message` | `.../retract_last_message.py` | `RetractInput(message_id, conv_id, tenant_id, clinic_id)` | `str` | YES + dual filter | YES — WhatsApp/IG retract API + fallback "marcar erróneo" |
| `screening_questions` | `.../screening_questions.py` | `ScreeningInput(lead_id, vertical, tenant_id, clinic_id)` | `ScreeningOutcome` (ok | derivado) | YES + dual filter | YES — LLM call (1-2 questions per vertical via personality compiled) |

### 4.3 Lucas growth setter tools (cron-triggered)

| Tool | Path | Input schema | Returns | Tenant-scoped | External calls |
|---|---|---|---|---|---|
| `compute_stage_recommendation` | `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_stage_recommendation.py` | `ComputeInput(stage, tenant_id, clinic_id, period)` | `RecommendationDTO` | YES + dual filter | YES — LLM call (Kimi reasoning prompt) |
| `compute_attribution_matrix` | `.../compute_attribution_matrix.py` | `MatrixInput(tenant_id, clinic_id, period)` | `MatrixDTO` (4 origins) | YES + dual filter | none (DB analytics) |
| `compute_referrals_leaderboard` | `.../compute_referrals_leaderboard.py` | `LeaderboardInput(tenant_id, clinic_id, period, limit=5)` | `LeaderboardDTO` | YES + dual filter | none (DB) |

## 5. Prompt cache slot architecture (Anthropic prompt caching)

Per `sales-agent-expert::§Decisiones cross-fase no obvias` + `claude-api`:

### 5.1 Adrián sales_agent compiler v2 slots (canonical layout — engine governs, brand provides slot 5 + slot 4 specialist)

```
SLOT 1 — System role            (cacheable, invariant globally) — engine
SLOT 2 — Domain context         (cacheable, per-domain — medical_vertical Vitalia)
SLOT 3 — Tools manifest         (cacheable, per-graph invariant)
SLOT 4 — MEDICAL_SAFETY_RAILS   (cacheable, per-brand — medical guardrails Vitalia) ★ NEW Slice 1
SLOT 5 — BRAND_VOICE prefix     (cacheable, per-tenant invariant — from personality_profiles.system_instruction)
                                 ↑ cache_control marker HERE ↑
SLOT 6 — Conversation + turn    (variable, NOT cached)
```

**Forbidden in cache prefix (slot 1-5):**
- Timestamps
- Conversation IDs
- Turn counters
- Random IDs
- `{tenant_name}` interpolated mid-block — use slot boundary instead (per `.claude/rules/sales-agent-brand-voice.md`)

### 5.2 TTL choice

- **5min default** for Adrián per-conversation (multi-turn within 5 min, ~5-10 turns)
- **1h** (`"ttl": "1h"`) for batch eval (each prefix reused dozens) — used by goldens runner

**Decision rule:** break-even at 2 reads (5min) / 3 reads (1h). 1h write = 2× input price; cache read = 0.1×.

### 5.3 Wizard onboarding cache slots

Wizard turns ~10-15 total per onboarding session (10-20 min). 5min TTL works for active session.

```
SLOT 1 — System role            (cacheable)
SLOT 2 — Wizard role + Vitalia onboarding context (cacheable, per-brand)
SLOT 3 — Tools manifest (extract, confirm_slot, simulate_personality, complete) (cacheable)
SLOT 4 — Valeria persona prompt (cacheable, per-brand)
                                 ↑ cache_control marker HERE ↑
SLOT 5 — Conversation + current slots state + user turn (variable, NOT cached)
```

### 5.4 Validation

Every LLM call MUST log:
- `cache_creation_input_tokens`
- `cache_read_input_tokens`
- `provider` (LiteLLM canonical post 2026-05-06)
- `model` (kimi-k2.6 / deepseek-v4-flash for wizard; specialist roles for Adrián)
- `cost_usd` (resolved via engine `cost_recorder.pop_cost(litellm_call_id)`)

If `cache_read_input_tokens` stays 0 across iter 2+ → silent invalidator in prefix (auditor will FAIL).

**Cost target:**
- Wizard onboarding ≤ $0.10 USD total ($0.05-0.10 range per spec)
- Adrián per turn ≤ $0.05 USD
- Cache hit rate ≥ 60% post-deploy

## 6. Checkpointer (production — MANDATORY)

Per `tessl__langgraph`:

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

checkpointer = AsyncPostgresSaver.from_conn_string(settings.postgres_dsn)
```

**Checkpoint tables (declared in migrations — table prefixes ratchet per Vitalia):**
- `vitalia_wizard_onboarding_checkpoints` (LangGraph supervisor wizard)
- `vitalia_lucas_analysis_checkpoints` (LangGraph daily analysis)
- Adrián consumes engine `agent_state_checkpoints` table (NO mirror per `sales-agent-expert::§3 NO se toca`)

NEVER `MemorySaver` — that's for tutorials.

## 7. Stream modes (SSE v2 protocol)

Per `copilot-expert::§SSE v2 protocol`:

Wizard onboarding API `/api/v1/vitalia/onboarding/start` + `/extract` + `/confirm-slot` emit:
- `status` (state: streaming|done)
- `message_start` (msg_id)
- `block_start` / `block_delta` / `block_end` / `block_append` (cards: `slot_confirmed`, `voice_preview`, `landing_preview`, `error`)
- `tool_start` / `tool_result`
- `ui_action` (legacy compat — minimal)
- `message_end`
- `done` | `error`

Frontend `WizardChatThread` consumes via `EventSource` (Next.js 16 supports native).

## 8. Observability writes (mandatory)

Per `.claude/rules/copilot-observability.md` + `auditor-downstream-regression.md` § A:

### 8.1 Trace events

`copilot_trace_event` recorder (existing engine — schema-mirrored to Vitalia per `backend-ddd.md` exception):
- Wizard: emits `turn_start`, `extract_url`, `extract_doc`, `simulate_voice`, `confirm_slot`, `complete`, `turn_end`
- Best-effort `try/except` wrapping per `copilot-observability.md`
- PII sanitized via `sanitize_payload(payload, compliance_level="hipaa_lite")` per `hipaa-lite.md` § PII sanitization

### 8.2 LLM call recording

`copilot_llm_call` (engine schema mirror — `(tenant_id, conversation_id, node_name, model, provider, input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens, duration_ms, cost_usd, litellm_call_id)`).

Per PI-12 S1 T-1 cost canonicalization (2026-05-02): `cost_usd` via `pop_cost(litellm_call_id)` from CustomLogger bridge (NO `calculate_cost()` runtime). Test fixtures MUST include `litellm_call_id` in `response_metadata`.

### 8.3 Trace event recorder anti-duplication §0

Vitalia subclasses engine `BaseAgentCallbackHandler` (from `core/luana-core-observability/src/luana_core_observability/recording/base_callback_handler.py`) — implements ONLY `_persist_llm_call_row` + `_persist_trace_event_row`:

```python
# vitalia/backend/src/modules/vitalia/copilot/observability/recording/callback_handler.py
from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler

class VitaliaCopilotCallbackHandler(BaseAgentCallbackHandler):
    async def _persist_llm_call_row(self, payload: dict) -> None:
        # Inherits sanitize_payload(compliance_level="hipaa_lite") + try/except + rollback from base
        await self.llm_call_repo.create(payload)
    
    async def _persist_trace_event_row(self, payload: dict) -> None:
        await self.trace_event_repo.create(payload)
```

NEVER duplicate `BaseAgentCallbackHandler` logic in `vitalia/` — extend only.

## 9. Eval goldens (Slice 1 obligatorios)

Per `.claude/rules/tdd-mandatory.md` + `sales-agent-expert::§Tech debt`:

### 9.1 Adrián sales_agent goldens (12 escenarios)

`vitalia/backend/tests/agentic_evals/sales_agent/goldens/`:

| Vertical | Escenarios (3) | persona |
|---|---|---|
| dental | (1) lead consulta + warm_close + screening + reservation 30% deposit, (2) objection price + handle warmth + close, (3) PHI request via WA → derivar portal seguro | `warm_close_dental.yaml` |
| estetica | (1) lead curioso + screening contraindication tattoo + derivar a doctor, (2) high-ticket package + value stack, (3) maintenance follow-up post-treatment | `warm_close_estetica.yaml` |
| psicologia | (1) lead crisis + safety guard + derivar emergencia (no cierra venta), (2) primer encuentro online + booking, (3) re-engagement follow-up médico | `warm_close_psicologia.yaml` |
| fertilidad | (1) consulta sensible + warmth + booking deposit, (2) couple inquiry + screening + nutrition pre-FIV, (3) cycle reschedule via WA | `warm_close_fertilidad.yaml` |

Each golden:
- Input conversation context
- Expected tool calls trajectory
- Expected voice_fidelity score ≥ 0.85
- Expected medical guardrails (`no_diagnosis`, `no_prescription`, `medical_disclaimer_required`) enforce
- Expected channel guards (PHI WhatsApp free → blocked / derive portal)

### 9.2 Eval runner

`pass^k` evaluation per `04-validators.yaml::agentic_eval`:
- k=3 trials per golden
- `per_trial_threshold = 0.66` (≥2/3 dimensions pass)
- `pass_k_threshold = 0.5` (≥50% of goldens pass k=3)

### 9.3 Voice fidelity grader

Vitalia leverages engine `voice_fidelity/grader` from `core/luana-core-brand-studio/application/voice_fidelity/grader.py`. Anchors per-tenant `personality_profile.system_instruction`.

### 9.4 Wizard onboarding goldens (4 escenarios — Batch 7 cementado)

`vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/`:
- happy: URL adjunto + 5 slots confirmed entra inbox
- negative: texto incompleto, required missing → Valeria pregunta
- edge: browser close mid-wizard → autosave resume
- adversarial: URL maliciosa + PII en doc + cross-tenant inference + XSS sanitize

## 10. Medical guardrails (per `vitalia/config/brand.yaml::guardrails`)

Per `.claude/rules/copilot-resilience.md` + `vitalia/.claude/rules/hipaa-lite.md`:

| Guardrail | Trigger | Action |
|---|---|---|
| `medical_safety_no_diagnosis` | Adrián / Valeria output contains diagnosis terms (regex + LLM classifier) | Block + replace with disclaimer "Información de referencia. Consultá con tu doctor." |
| `medical_safety_no_prescription` | Output contains medication dosage/name + prescription verb | Block + replace |
| `medical_disclaimer_required` | Output contains medical info terms | Append disclaimer footer |
| `prompt_injection_block` | User input contains prompt injection signature | Strip + warn user |

Implementation: registered via EP-13 (existing Story 11 scaffold has placeholders — T-guards-1..3 implement real check functions).

## 11. Channel guards (PHI on non-encrypted channels)

Per `hipaa-lite.md` § Compliance gates + `core/luana-core-compliance/ComplianceService.validate_outbound_message`:

- WhatsApp tier free → PHI blocked → reply "Por seguridad, los resultados los podés ver en tu portal: {link}"
- SMS → PHI blocked
- Email plaintext → PHI blocked (only portal-link emails OK)

Tool `screening_questions` per vertical filters out PHI-requiring questions on free WhatsApp.

## 12. LLM router (LiteLLM Proxy canonical post 2026-05-06)

Per `core/luana-core-llm/src/luana_core_llm/providers/litellm.py`:

Vitalia consumes:
- **Wizard onboarding:** kimi-k2.6 (Standard tier) / deepseek-v4-flash for cost optimization
- **Adrián sales_agent:** specialist roles per `SPECIALIST_TO_ROLE` from engine (kimi-k2.6 main, deepseek-v4-flash for nano classifier)
- **Lucas growth setter:** kimi-k2.6 (reasoning model)
- **Valeria copilot rail (daily ops):** kimi-k2.6 main + deepseek-v4-flash nano (intent classifier)

NEVER direct provider adapters (legacy, removed PI-12 S1 T-4 2026-05-06). LiteLLM Proxy single path.

## 13. Skill decisions referenced (per `03-arch.md § 0`)

- **`copilot-expert`:** Valeria 80px rail · wizard tools via EP-3 · observability via engine subclass (NO mirror) · post-2026-04-30 outbox pattern default True · LiteLLM canonical
- **`sales-agent-expert`:** Adrián consume engine direct · §3 NO toca · compiler v2 slots · 12 goldens · LiteLLM canonical
- **`brand-expert`:** wizard llama engine voice infra via port · 3-pilar personality · `personality_service.compile_partial` + `simulate` durante wizard
- **`tessl__langgraph`:** supervisor topology + `AsyncPostgresSaver` + 6 stream modes (`updates` + `messages` for UI)
- **`tessl__deepagents`:** `SubAgentMiddleware` isolation for wizard extractor subagent
- **`tessl__graceful-degradation`:** all external tool calls (Whisper, MP, Nubefact, WhatsApp, Meta Ads, Google Ads) wrap timeout+fallback
- **`claude-api`:** prompt cache slot 1-5 cacheable, slot 6 variable. TTL 5min default · 1h batch eval

## 14. Test surfaces (TDD-mandatory)

Per `.claude/rules/tdd-mandatory.md`:

| Layer | Test file pattern | RED first | Builder | Audit owner |
|---|---|---|---|---|
| Tool unit tests | `vitalia/backend/tests/modules/vitalia/{copilot,sales_agent}/tools/test_*.py` | YES | builder-agentic (production_code=true) | auditor-agentic |
| Workflow integration | `vitalia/backend/tests/modules/vitalia/copilot/workflows/test_wizard_onboarding_graph.py` | YES | builder-agentic | auditor-agentic |
| Goldens (12 Adrián + 4 wizard) | `vitalia/backend/tests/agentic_evals/{sales_agent,copilot}/goldens/...` | NO (data, not code) | builder-agentic (tests/docs about agentic, production_code=FALSE → Sonnet OK) | auditor-agentic |
| Voice fidelity grader | `vitalia/backend/tests/agentic_evals/sales_agent/test_voice_fidelity_vitalia.py` | YES | builder-agentic (production_code=false test wrapper) | auditor-agentic |
| Medical guardrails | `vitalia/backend/tests/agentic_evals/sales_agent/test_medical_guardrails.py` | YES | builder-agentic | auditor-agentic |
| Channel guards | `vitalia/backend/tests/modules/vitalia/sales_agent/test_channel_guards.py` | YES | builder-agentic | auditor-agentic |
| Cost canonicalization (per PI-12 S1 T-1) | `vitalia/backend/tests/modules/vitalia/{copilot,sales_agent}/observability/test_callback_handler.py` | YES (fixtures need `litellm_call_id`) | builder-backend (schema mirror exception) | auditor-backend |
| Anti-duplication mirror scan | `vitalia/backend/tests/architecture/test_no_observability_mirror.py` | YES | builder-agentic (arch fitness) | auditor-agentic |
| Cache hit rate validation | smoke test post-deploy `verify_cache_hit_rate.py` | NO (smoke) | n/a | auditor-agentic |

## 15. Cross-cutting concerns (agentic-specific)

- **R23 cost-routing:** production_code=true → Opus 4.7 (build + audit). Tests/docs/goldens about agentic → Sonnet OK.
- **§3 NO TOCAR:** Adrián engine surfaces (Closer Studio, SmartBufferService, OutputManager, etc.) per `sales-agent-expert::§3`. Brand extension ONLY via `vitalia/backend/src/modules/vitalia/sales_agent/{tools,personas,goldens}/`.
- **No cross-module imports from `copilot/` to `sales_agent/` (or vice versa).** Both consume `core/luana-core-*/` engine.
- **Spanish neutro UI chrome.** Adrián OUTPUT respects tenant voice (`personality_profiles.system_instruction`) — voseo OK if tenant AR configures.
- **PII sanitization MANDATORY** before writing observability rows. Vitalia adds NEW PHI fields per `phi_fields.py`.
- **Default flag flips: ZERO Slice 1.** No `USE_*_PATTERN_*` flips proposed. If Slice 2 needs flip → `.claude/rules/anti-default-flip-audit.md` 4-step audit obligatory.
- **Schema-mirror exception:** builder-backend MAY touch `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/persistence/models/` for engine migration schema mirror ONLY (per `backend-ddd.md` Schema-mirror exception, origen R5 2026-05-05).

## 16. Anti-patterns prohibited (per `sales-agent-expert::§Anti-patterns` + `copilot-resilience.md`)

- ❌ Migrar StateGraph a deepagents wholesale (deepagents only for subagent isolation in wizard extractor)
- ❌ Eliminar Closer Studio + WS + SmartBufferService + OutputManager + follow_up_engine
- ❌ Hardcodear model wire-name strings en specialists — use `LLM_ROLE_BY_SITE` SSoT from engine
- ❌ Hardcodear canales literales — use `get_channel_format(channel_type)` from `core/luana-core-channels/`
- ❌ Importar `copilot/` desde `sales_agent/` (o viceversa) — both consume `core/luana-core-*/`
- ❌ Tocar `PromptVersionModel`
- ❌ `from __future__ import annotations` en `*/orchestrator/graph.py` (rompe LangGraph runtime introspection)
- ❌ Bypass `sanitize_payload(compliance_level="hipaa_lite")` en writes a observability tables
- ❌ Duplicar plumbing del `BaseAgentCallbackHandler` shared (only overrides agent-specific)
- ❌ Bypass channel registry shared
- ❌ Aliases DeepSeek retired Jul 24 2026 (`deepseek-chat`, `deepseek-reasoner`) — use `deepseek-v4-flash` / `deepseek-v4-pro`
- ❌ Tier pricing >200k tokens sin resolver — Kimi K2.6 declare `input_cost_per_token_above_200k_tokens` (calculator split `TIER_THRESHOLD = 200_000`)
- ❌ `MemorySaver` (tutorials only) — production MUST `AsyncPostgresSaver`
- ❌ Inyectar `{tenant_name}` mid-block cache prefix slot 5 (use slot boundary)
- ❌ Crear archivo nuevo en `modules/{copilot,sales_agent}/observability/recording/<X>.py` o `cost/<X>.py` o `pricing/<X>.py` — first check `.claude/rules/anti-duplication.md` inventory. EXTEND engine subclass.
