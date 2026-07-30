# vitalia-slice-1-fidelizacion — Agentic sub-architecture

> **Consumer:** `builder-agentic` (Opus 4.7 R23 production) + `auditor-agentic` (Opus 4.7).
> **Index:** `03-arch.md` § 0-9 (read first).
> **Brand surface (agentic this story):** `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_re_engagement_recommendation.py` (NEW) + `vitalia/backend/src/modules/vitalia/sales_agent/tools/send_proactive_reengagement.py` (NEW wrapper) + eval goldens.
> **Engine consultation (READ-ONLY):** `core/luana-core-{copilot,sales-agent,observability,llm,billing,compliance}/`.

> **R23 cost-routing:** all `production_code: true` tickets MUST use Opus 4.7. Eval goldens + tests = `production_code: false` → Sonnet OK.
>
> **Anti-duplication §0 cardinal:** NEVER mirror engine observability/cost/pricing/turn_envelope/callback_handler/FX/tenant_billing/PII patterns. EXTEND via heredancia o escalate LIFT-TO-SHARED via `/pm-luana` if not yet shared. Inventory en `.claude/rules/anti-duplication.md`.

## 1. Agentic surfaces (esta story)

```
vitalia/backend/src/modules/vitalia/sales_agent/
├── tools/
│   ├── send_proactive_reengagement.py      ← NEW Slice 1 (THIS story) wrapper around existing send_template_confirmation
│   └── (existing tools cementadas en story side `vitalia-copilot-tools-impl`)
├── personas/
│   └── (cementadas Story 11 — voz Adrián consume `personality_profiles.system_instruction` slot 5)
├── goldens/
│   └── reengagement/                       ← NEW Slice 1 (THIS story) 4 eval scenarios
│       ├── happy_multi_session.yaml        ← Patrón 1 send + paciente reagenda
│       ├── happy_follow_up.yaml            ← Patrón 2 send
│       ├── happy_maintenance.yaml          ← Patrón 3 send
│       └── absence_optin_guard.yaml        ← Patrón 4 sin opt-in → tool refuse send
└── observability/
    └── (REUSE engine — NO mirror per anti-duplication §0)

vitalia/backend/src/modules/vitalia/agentic/lucas/
├── tools/
│   └── compute_re_engagement_recommendation.py  ← NEW Slice 1 (THIS story) Lucas tool
└── goldens/
    └── re_engagement_recommendation/        ← NEW Slice 1 (THIS story) 3 eval scenarios
        ├── high_value_dental_critico.yaml   ← Lucas detecta cluster ortodoncia abandon
        ├── psicologia_safety_referral.yaml  ← Lucas recommends derivar emergencia detector
        └── estetica_maintenance_segment.yaml ← Lucas suggests segment campaign maintenance
```

## 2. Tools (NEW Slice 1 — this story)

### 2.1 `send_proactive_reengagement` (Adrián tool wrapper)

```python
# vitalia/backend/src/modules/vitalia/sales_agent/tools/send_proactive_reengagement.py
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Literal

class SendProactiveReEngagementInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: UUID
    clinic_id: UUID                                  # CARDINAL dual filter
    patient_id: UUID
    pattern: Literal["multi_session", "follow_up", "maintenance", "absence", "nps"]
    template_id: str                                 # e.g., "recordatorio_proxima_sesion"
    slot_values: dict                                # variables substitution
    re_engagement_event_id: UUID                     # link back for outcome update
    trigger_source: str                              # cron name or "manual"
    triggered_by_user_id: UUID                       # operator who confirmed (or system for nps)

@tool
async def send_proactive_reengagement(
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    pattern: str,
    template_id: str,
    slot_values: dict,
    re_engagement_event_id: UUID,
    trigger_source: str,
    triggered_by_user_id: UUID,
) -> str:
    """Send proactive WhatsApp template to patient as re-engagement reminder.
    
    Wraps existing send_template_confirmation tool with re-engagement context.
    Honors throttle (7d per pattern), opt-in (MARKETING templates), opt-out flag,
    compliance channel guard, and updates re_engagement_events.outcome.
    """
    # 1. Resolve services (DI per agent runtime)
    proactive_service = current_app.deps.get(ProactiveOutboundService)
    
    # 2. Delegate to service (handles dual filter + throttle + compliance + audit + Adrián dispatch + persist + emit event)
    response = await proactive_service.send_proactive_reminder(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        user_id=triggered_by_user_id,
        request=SendProactiveRequest(
            template_id=template_id, pattern=pattern,
            slot_values=slot_values, trigger_source=trigger_source,
        ),
        idempotency_key=f"proactive::{tenant_id}::{re_engagement_event_id}",
    )
    
    return f"Sent {pattern} reminder to patient {patient_id} via {template_id}. Outcome: {response.status}. Event id: {response.re_engagement_event_id}."
```

**Tenant-scoped:** YES + dual filter clinic_id.
**External calls:** YES — WhatsApp Business API (templates Meta-approved) wrap timeout 10s + fallback "marcar conversación pendiente revisar". Per `tessl__graceful-degradation`.
**Async:** YES.
**Calls SERVICES (never raw repos):** YES — delegates to `ProactiveOutboundService`.

### 2.2 `compute_re_engagement_recommendation` (Lucas tool)

```python
# vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_re_engagement_recommendation.py
from langchain_core.tools import tool
from pydantic import BaseModel
from uuid import UUID
from typing import Literal

class ComputeReEngagementRecommendationInput(BaseModel):
    tenant_id: UUID
    clinic_id: UUID
    period: Literal["7d", "30d", "90d"] = "30d"

@tool
async def compute_re_engagement_recommendation(
    tenant_id: UUID,
    clinic_id: UUID,
    period: str = "30d",
) -> dict:
    """Compute Lucas recommendation for re-engagement opportunities.
    
    Reads vitalia_re_engagement_events aggregates (per pattern, per outcome, per period),
    detects clusters (e.g., '3 abandonos ortodoncia comparten doctor X'),
    and returns actionable recommendation for Owner.
    
    Output shape:
    {
        "tenant_id": "...",
        "clinic_id": "...",
        "stage": "fidelizacion",
        "recommendations": [
            {
                "title": "Detectamos 3 ortodoncias abandonadas con Dr. Mendoza este mes",
                "body_markdown": "...",
                "severity": "warning",
                "suggested_actions": [
                    {"label": "Ver pacientes", "href": "/fidelización?tab=multisession&doctor=mendoza"},
                ],
                "rationale_json": {...},
            }
        ]
    }
    """
    lucas_service = current_app.deps.get(LucasReEngagementService)
    
    # 1. Aggregate query (DB analytics — no LLM call here)
    aggregates = await lucas_service.aggregate_patterns(
        tenant_id=tenant_id, clinic_id=clinic_id, period=period
    )
    
    # 2. Detect clusters (Python deterministic — no LLM)
    clusters = lucas_service.detect_clusters(aggregates)
    
    # 3. If clusters found → LLM single call to phrase recommendation (Kimi reasoning short prompt)
    if clusters:
        recommendations = await lucas_service.generate_recommendations(
            tenant_id=tenant_id, clinic_id=clinic_id,
            clusters=clusters, period=period,
        )
    else:
        recommendations = []
    
    return {
        "tenant_id": str(tenant_id),
        "clinic_id": str(clinic_id),
        "stage": "fidelizacion",
        "recommendations": recommendations,
    }
```

**Tenant-scoped:** YES + dual filter.
**External calls:** YES — single LLM call (Kimi reasoning) per recommendation cluster. Cost ≤ $0.05/invocation. Cache invariant key `(tenant, clinic, period, cluster_signature)` with 1h TTL — Lucas tool re-invocation within 1h hits cache.
**Async:** YES.

## 3. Agentic state (no NEW StateGraph esta story)

Esta story NO crea NEW LangGraph. Adrián consume engine `core/luana-core-sales-agent/` runtime directly. Lucas tool es simple ReAct (1 tool DB aggregate + 1 LLM call) — no needs supervisor topology. NO `WizardOnboardingState` (wizard vive en story side `vitalia-copilot-tools-impl`).

State management:
- Adrián turns: consume engine `SalesAgentState` (no extension overlay esta story — `clinic_id` ya en extension Story 11)
- Lucas tool: stateless invocation (no graph state — pure tool call wrapping aggregate + LLM)

## 4. Prompt cache slot architecture

### 4.1 Adrián cache (re-engagement template send)

Re-engagement template send NO requires LLM call runtime (template Meta-approved + variables substitution via personality compiler — deterministic). Cache prefix Adrián slot 1-5 N/A para envío template.

Cache aplica al **fallback ReAct** cuando paciente responde y Adrián entra conversación normal (turn flow). Slot architecture engine-canonical:

```
SLOT 1 — System role           (cacheable, invariant globally) — engine
SLOT 2 — Domain context        (cacheable, per-domain — medical_vertical Vitalia) — Story 11
SLOT 3 — Tools manifest        (cacheable, per-graph invariant)
SLOT 4 — MEDICAL_SAFETY_RAILS  (cacheable, per-brand) — Story 11
SLOT 5 — BRAND_VOICE prefix    (cacheable, per-tenant — `personality_profiles.system_instruction`)
                                ↑ cache_control marker HERE ↑
SLOT 6 — Conversation + turn   (variable, NOT cached)
```

TTL 5min default Adrián per-conversation. Cache hit rate target ≥ 60%.

### 4.2 Lucas cache

Lucas reasoning call (re-engagement recommendation) consumes engine LangGraph harness shared. Cache slot:

```
SLOT 1 — System role + Lucas role + Vitalia medical context (cacheable)
SLOT 2 — Recommendation rubric + JSON output schema (cacheable, per-graph)
                                ↑ cache_control marker HERE ↑
SLOT 3 — Aggregate data injection + period + clusters (variable per invocation)
```

TTL 1h (Lucas recommendation reused across multiple Owner views within hour). Break-even at 3 reads.

### 4.3 Validation (mandatory observability)

Every LLM call (Lucas) MUST log:
- `cache_creation_input_tokens`
- `cache_read_input_tokens`
- `provider` (LiteLLM canonical)
- `model` (kimi-k2.6 for Lucas reasoning, default per brand.yaml)
- `cost_usd` (via engine `cost_recorder.pop_cost(litellm_call_id)`)

If `cache_read_input_tokens` stays 0 across invocations 2+ → silent invalidator in prefix (auditor FAIL).

**Cost target:**
- Lucas re-engagement recommendation ≤ $0.05 USD per invocation
- Adrián response after re-engagement template (fallback ReAct turn) ≤ $0.05 USD

## 5. Checkpointer (production — MANDATORY)

Esta story NO crea NEW LangGraph + NO crea NEW checkpoint table.
- Adrián consumes engine `agent_state_checkpoints` (NO mirror per `sales-agent-expert::§3`)
- Lucas tool stateless (no checkpoint)

NEVER `MemorySaver`.

## 6. Stream modes (SSE v2)

Lucas `compute_re_engagement_recommendation` tool runs **internamente** invocado por Owner navegando `/marketing` Stage Adopción (Slice 2) o `/fidelización` activity footer (Slice 1 minimal — Lucas insights NOT in /fidelización Slice 1 UI yet, defer Slice 2).

Slice 1 scope: Lucas tool callable on-demand but UI surface delayed Slice 2. No SSE stream needed.

Adrián proactive_outbound template send: NO streaming UI (template fire-and-update DB).

## 7. Observability writes (mandatory)

Per `.claude/rules/copilot-observability.md` + `auditor-downstream-regression.md` § A:

### 7.1 Trace events

- `sales_agent_trace_event` recorder (engine + schema mirror Vitalia per `backend-ddd.md` exception)
- Adrián `send_proactive_reengagement` tool emits: `turn_start`, `tool_call`, `tool_result`, `turn_end`
- Lucas `compute_re_engagement_recommendation` emits: `turn_start`, `tool_call` (aggregate query), `llm_call`, `tool_result`, `turn_end`
- Best-effort try/except per `copilot-observability.md`
- PII sanitized via `sanitize_payload(payload, compliance_level="hipaa_lite")`

### 7.2 LLM call recording

- `copilot_llm_call` (Lucas) + `sales_agent_llm_call` (Adrián if entering ReAct fallback post-response)
- Columns: `(tenant_id, conversation_id, node_name, model, provider, input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens, duration_ms, cost_usd, litellm_call_id)`
- Per PI-12 S1 T-1 cost canonicalization (2026-05-02): `cost_usd` via `pop_cost(litellm_call_id)` from CustomLogger bridge

### 7.3 Trace anti-duplication §0

Vitalia subclase engine `BaseAgentCallbackHandler` — implements ONLY `_persist_llm_call_row` + `_persist_trace_event_row` for sales_agent / Lucas. NO mirror engine recording/cost/pricing.

## 8. Eval goldens (Slice 1)

### 8.1 Adrián re-engagement goldens (4 scenarios)

Located: `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/`

**Per scenario YAML schema (cementado Story B PI-12 evals foundation 2026-05-08):**

```yaml
golden_id: vitalia_reengagement_multi_session_happy
brand: vitalia
agent: sales_agent
persona_archetype: warm_close_dental
language: es
locale: es_MX
voseo: false
scenario_type: re_engagement_proactive
expected_termination_reason: tool_completed_success
expected_tools_invoked: [send_proactive_reengagement]
forbidden_tools: [send_payment_link]  # not part of re-engagement flow
context:
  tenant_id: <fixture_sanare_mx_uuid>
  clinic_id: <fixture_sanare_clinic_uuid>
  patient_id: <fixture_patient_m_rodriguez_uuid>
  re_engagement_event_id: <fixture_event_uuid>
  pattern: multi_session
  template_id: recordatorio_proxima_sesion
  slot_values:
    patient_name: "M. Rodríguez"
    offer_label: "Ortodoncia"
    sessions_completed: 4
    sessions_expected: 12
    slot_1_date: "21 May 10:00"
    slot_2_date: "22 May 14:00"
    slot_3_date: "23 May 11:00"
  trigger_source: "cron multi_session_gap_sweep"
  triggered_by_user_id: <fixture_dr_demo_user_uuid>
expected_tool_call_args:
  send_proactive_reengagement:
    pattern: multi_session
    template_id: recordatorio_proxima_sesion
expected_observability:
  cost_bucket: evals_only
  cache_read_min: 0  # first invocation
  llm_calls_max: 0  # template send NO LLM call
```

Scenarios:
1. `happy_multi_session.yaml` — Patrón 1 send + patient reschedules within 24h (multi-turn simulator)
2. `happy_follow_up.yaml` — Patrón 2 send
3. `happy_maintenance.yaml` — Patrón 3 send
4. `absence_optin_guard.yaml` — Patrón 4 absence pattern: patient.marketing_opt_in=false → tool refuses send + returns `Outcome=opted_out` reason explanation

### 8.2 Lucas re-engagement recommendation goldens (3 scenarios)

Located: `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/`

```yaml
golden_id: lucas_reengagement_high_value_dental_cluster
brand: vitalia
agent: lucas
language: es
scenario_type: stage_recommendation
context:
  tenant_id: <fixture_sanare_mx_uuid>
  clinic_id: <fixture_sanare_clinic_uuid>
  period: 30d
  seed_re_engagement_events:
    - { pattern: multi_session, doctor_id: <dr_mendoza>, count: 3 }  # cluster
    - { pattern: maintenance, doctor_id: <dra_lopez>, count: 1 }
expected_output_shape:
  recommendations:
    - severity: warning
      title_contains: ["Dr. Mendoza", "ortodoncias", "abandonadas"]
      suggested_actions:
        - label_contains: "Ver pacientes"
          href_contains: "/fidelización"
expected_observability:
  cost_bucket: evals_only
  cache_read_min: 0
  cache_creation_min: 1  # first cache write
  llm_calls_max: 1  # single reasoning call
  cost_usd_max: 0.05
```

Scenarios:
1. `high_value_dental_critico.yaml` — Cluster detection ortodoncia × doctor abandono
2. `psicologia_safety_referral.yaml` — Lucas recommends derivar (medical_safety_no_diagnosis guard not triggered — Lucas is meta-recommendation, no doctor advice)
3. `estetica_maintenance_segment.yaml` — Maintenance cadencia segment opportunity

### 8.3 Voice fidelity grader (Adrián)

For each Adrián scenario, voice fidelity grader compares output vs `PersonalityProfile.system_instruction` voice anchors. Threshold: `grader_score >= 0.85`.

Drift detection: if grader_score < 0.85 across 3+ scenarios → escalate `auditor-agentic` + investigate prompt drift en `personality_compiler` or templates.

### 8.4 Trials threshold

Per checkpoint § 06-tickets agentic_eval: 4 patrones × 3 trials each = 12 trials Adrián. 3 Lucas scenarios × 3 trials = 9. Threshold ≥ 0.66 (2/3 trials per scenario must pass).

## 9. RAG / Qdrant

NOT used esta story. Lucas re-engagement recommendation is aggregate-based reasoning (no KB search). Slice 2+ Lucas Insights cluster patterns con KB curado.

## 10. Skill decisions referenced

- **`copilot-expert`** § Anti-duplication §0 cardinal — observability/cost/pricing patterns viven en engine `core/luana-core-observability/`. Vitalia consume direct/heredancia. NUNCA mirror per-brand.
- **`sales-agent-expert`** § 3 NO se toca — Closer Studio, SmartBufferService, OutputManager chunking, agent_state_checkpoints. Adrián compiler v2 slot 5 BRAND_VOICE from `personality_profiles.system_instruction`. Channel registry shared via `register_channel` (engine canonical post lift Story 11).
- **`sales-agent-expert`** § Surfaces compartidas — `BaseAgentCallbackHandler` template method · DRY threshold 2 consumers (sales + copilot) · subclass implementa solo `_persist_llm_call_row` + `_persist_trace_event_row`.
- **`tessl__langgraph`** — Lucas simple ReAct alcanza. No supervisor needed (1 tool aggregate + 1 LLM reasoning call).
- **`tessl__graceful-degradation`** — WhatsApp Business API send template: timeout 10s + fallback "marcar conversación pendiente revisar" + retry queue persistente.
- **`backend-expert`** — Service injection pattern: tool delegates to `ProactiveOutboundService` (handles dual filter + throttle + compliance + audit + emit event).

## 11. Test surfaces (TDD-mandatory)

| Layer | Test file pattern | RED first |
|---|---|---|
| Tool unit (Adrián send_proactive_reengagement) | `vitalia/backend/tests/modules/vitalia/sales_agent/tools/test_send_proactive_reengagement.py` | YES |
| Tool unit (Lucas compute) | `vitalia/backend/tests/modules/vitalia/agentic/lucas/tools/test_compute_re_engagement_recommendation.py` | YES |
| Eval goldens Adrián | `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/test_*.py` | NO (validation only — goldens YAML schema enforced via arch test) |
| Eval goldens Lucas | `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/test_*.py` | NO |
| Voice fidelity Adrián | `vitalia/backend/tests/agentic_evals/sales_agent/test_voice_fidelity_reengagement.py` | YES (smoke with Sanaré tenant fixture) |
| Observability invariants | `vitalia/backend/tests/architecture/test_eval_simulator_observability_invariants.py` (engine existing) — verify cost_bucket=evals_only for goldens runs | YES already exists |
| Cost recorder cleanup | `vitalia/backend/tests/modules/vitalia/{copilot,sales_agent}/observability/test_callback_handler.py` (existing) | downstream regression scope per `.claude/rules/auditor-downstream-regression.md` § A — must run when touching engine cost_recorder. This story does NOT touch engine. |

## 12. Architectural fitness impact (agentic-specific)

Allowlists:
- `test_no_legacy_eventbus_mock_when_outbox_on.py` (engine cross-brand) — outbox emit `ReEngagementTriggered` + `NPSScoreCollected` MUST use `adapter_bus.publish()` not legacy `EventBus.publish` (post 2026-04-30 default flip)
- `test_personas_yaml_completeness.py` (engine) — no impact (no personas modification)
- `test_simulator_no_mirrors_shared.py` (engine) — verify no mirror of engine simulator schema in brand goldens

Zero new allowlist entries — fix-forward.

## 13. R23 ticket production_code flagging

| Ticket | production_code | Owner pool | Justification |
|---|---|---|---|
| T-fidelizacion-agentic-1 `send_proactive_reengagement` tool | true (AGENTIC runtime) | Opus 4.7 ONLY | per R23 |
| T-fidelizacion-agentic-2 Lucas `compute_re_engagement_recommendation` tool | true (AGENTIC runtime) | Opus 4.7 ONLY | per R23 |
| T-fidelizacion-agentic-3 Adrián eval goldens (4 YAML files + grader smoke) | false (tests on agentic) | Sonnet OK | per R23 docs+tests carve-out |
| T-fidelizacion-agentic-4 Lucas eval goldens (3 YAML files + harness) | false | Sonnet OK | idem |
| T-fidelizacion-agentic-5 Voice fidelity grader smoke tests | false | Sonnet OK | idem |
| T-fidelizacion-agentic-6 PII patterns add re-engagement template variable PHI markers (if needed) | false (docs/config) | Sonnet OK | idem |

## 14. References

- `.claude/rules/anti-duplication.md` (cardinal — observability shared abstractions)
- `.claude/rules/copilot-observability.md`
- `.claude/rules/auditor-downstream-regression.md` § A engine observability + § E brand sales_agent extensions
- `.claude/rules/sales-agent-brand-voice.md` (slot 5 cache prefix)
- `vitalia/.claude/rules/hipaa-lite.md` (PHI sanitization en traces + channel guard)
- `core/luana-core-sales-agent/src/luana_core_sales_agent/runtime/` (engine consume)
- `core/luana-core-observability/src/luana_core_observability/recording/{sanitize_payload, base_callback_handler}.py`
- `core/luana-core-compliance/src/luana_core_compliance/ComplianceService` (channel guard)
- `vitalia/backend/src/modules/vitalia/extensions.py` (existing EP-13 guardrails: medical_safety_no_diagnosis, medical_safety_no_prescription, medical_disclaimer_required, prompt_injection_block — Story 11 cement)
