# vitalia-slice-1-inbox — Agentic sub-architecture

> **Consumer:** `builder-agentic` (Opus 4.7 R23 production) + `auditor-agentic` (Opus 4.7).
> **Index:** `03-arch.md` § 0-9 (read first).
> **Brand surface (production code, R23 Opus):** `vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py` (NEW).
> **Brand surface (tests/docs, R23 production_code=false → Sonnet OK):** opcional eval goldens reinforcement Slice 1.
> **Engine consultation:** READ-ONLY `core/luana-core-{sales-agent,copilot,observability,llm,compliance,channels}/`.
>
> **Anti-duplication §0 cardinal:** NEVER mirror engine observability/cost/pricing/turn_envelope/callback_handler/FX/tenant_billing/PII patterns. EXTEND via heredancia. Inventory en `.claude/rules/anti-duplication.md`.

## 1. Agentic surface map (Slice 1 inbox)

```
vitalia/backend/src/modules/vitalia/
├── sales_agent/                            ← EXISTING (Story 11 + vitalia-copilot-tools-impl shipped 2026-05-19)
│   ├── tools/
│   │   ├── payment_link.py                 ← EXISTING (shipped)
│   │   ├── reschedule_appointment.py       ← EXISTING (shipped)
│   │   ├── screening_questions.py          ← EXISTING (shipped)
│   │   └── retract_last_message.py         ← NEW Slice 1 (R23 Opus production_code=true)
│   ├── personas/                           ← EXISTING (shipped Story 11)
│   │   ├── warm_close_default.yaml
│   │   ├── warm_close_dental.yaml
│   │   ├── warm_close_estetica.yaml
│   │   ├── warm_close_psicologia.yaml
│   │   └── warm_close_fertilidad.yaml
│   ├── prompts/                            ← EXISTING (shipped — consume engine personality_service)
│   ├── observability/                      ← EXISTING (REUSE engine via SalesAgentObservabilityContext shipped)
│   ├── persistence/models/                 ← EXISTING (schema mirror per backend-ddd.md exception)
│   └── domain/state_overlay.py             ← EXISTING (VitaliaSalesAgentStateExtension shipped)
└── copilot/                                ← EXISTING (Story 11 placeholder)
    └── (no logic changes Slice 1 inbox · ActivityStream consume engine copilot_trace_event directly via API)
```

**Inbox NO añade LangGraph nodes nuevos al engine.** Adrián turn pipeline ya cementado en `core/luana-core-sales-agent/`. Esta story añade UN tool (`retract_last_message`) y wires Activity Stream consumption.

## 2. New tool: `retract_last_message` (R23 Opus production)

### 2.1 Signature

```python
# vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py
"""retract_last_message — Vitalia sales_agent tool.

Allows Adrián (modo 'ai') to retract its own last message within 5min window.
Used in agentic state machine when:
- Adrián detected its own message was inappropriate (e.g., medical claim outside scope)
- ComplianceService.validate_outbound_message flagged the message post-send
- Adrián received explicit user correction in next turn

Per `.claude/rules/anti-duplication.md` §0 cardinal:
- NEVER mirror engine observability/cost/pricing/turn_envelope
- NEVER access channels directly — go through ports
- NEVER duplicate connection retract logic — use connections.{X}.adapter.retract_message_id

Per `.claude/rules/auditor-downstream-regression.md`:
- Touches sales_agent brand extension surface — cross-brand mirror scan required by auditor
- Schema mirror: writes to existing vitalia_messages.retracted_* columns (no new tables here)
"""

from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()


class RetractLastMessageInput(BaseModel):
    """Tool input — tenant-scoped + reason mandatory for audit."""
    model_config = ConfigDict(from_attributes=True)
    tenant_id: str = Field(..., description="Tenant UUID — MANDATORY for isolation.")
    clinic_id: str = Field(..., description="Clinic UUID — MANDATORY for HIPAA-lite dual filter.")
    conversation_id: str = Field(..., description="Conversation UUID containing the message.")
    message_id: str = Field(..., description="Message UUID to retract.")
    reason: str = Field(..., min_length=10, max_length=500, description="Justification for retract (audit log).")


@tool(args_schema=RetractLastMessageInput)
async def retract_last_message(
    tenant_id: str,
    clinic_id: str,
    conversation_id: str,
    message_id: str,
    reason: str,
) -> str:
    """Retract a message Adrián sent within the 5min undo window.

    Returns:
        Spanish neutral natural language summary for Adrián consumption.
        Examples:
        - "Mensaje revertido. La conversación quedó en modo manual."
        - "No pude revertir el mensaje (excedió 5 minutos). Lo marqué como erróneo en el historial."
        - "No pude revertir: el paciente ya respondió."

    Raises:
        Never raises directly — graceful-degradation per tessl skill (timeout 5s + fallback).
        Errors logged via structlog + audit log row.

    Implementation:
        Calls RetractMessageService.execute(...) which:
        1. Validates 5min window via action_receipts.expires_at
        2. Checks no patient reply after this message
        3. Calls connections.{wa,ig,email}.adapter.retract_message_id(external_id, timeout=5s)
        4. On adapter failure → fallback "marcar erróneo" (no retract real, audit log entry)
        5. Updates vitalia_messages.retracted_at + handler_mode='human' in vitalia_conversations
        6. Emits MessageRetracted domain event via outbox bus
        7. Sync writes audit_log row pre-response
    """
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractMessageService,
        get_retract_message_service,
    )

    service = get_retract_message_service()  # DI-resolved per request
    try:
        result = await service.execute(
            tenant_id=UUID(tenant_id),
            clinic_id=UUID(clinic_id),
            conversation_id=UUID(conversation_id),
            message_id=UUID(message_id),
            reason=reason,
            initiated_by_agent="adrian",
        )
        if result.retract_succeeded:
            return "Mensaje revertido. La conversación quedó en modo manual."
        if result.retract_failed_reason == "expired":
            return "No pude revertir el mensaje (excedió 5 minutos). Lo marqué como erróneo en el historial."
        if result.retract_failed_reason == "patient_replied":
            return "No pude revertir: el paciente ya respondió."
        if result.retract_failed_reason == "channel_unsupported":
            return "Este canal no permite revertir mensajes. Lo marqué como erróneo."
        return "No pude revertir el mensaje. Quedó marcado como erróneo."
    except Exception as e:
        logger.warning("retract_last_message.unexpected_error", error=str(e), conversation_id=conversation_id)
        return "No pude revertir el mensaje. Quedó registrado para revisión."
```

### 2.2 Registration in extensions.py

```python
# vitalia/backend/src/modules/vitalia/extensions.py (EXISTING — extend)
def register_all(registry: ExtensionPointRegistry) -> None:
    # ... existing registrations (Story 11 cement)

    # NEW Slice 1 inbox — register retract_last_message tool via EP-3 (tools)
    from src.modules.vitalia.sales_agent.tools.retract_last_message import retract_last_message

    registry.register_tool(
        agent_id="adrian",
        tool=retract_last_message,
        tool_group="messaging",
        allowed_routes=["sales_conversation"],  # only available in sales_agent runtime
        compliance_level="hipaa_lite",
    )
```

### 2.3 Tool boundary checks

- **Tenant isolation:** `tenant_id` + `clinic_id` mandatory in input schema. Service-level dual filter applied.
- **External calls:** wraps `connections.{wa,ig,email}.retract_message_id` (timeout 5s · graceful-degradation `tessl__graceful-degradation`).
- **Compliance:** uses `RetractMessageService` which writes audit_log row pre-response.
- **Observability:** consumes engine `SalesAgentObservabilityContext` (shipped). Tool call recorded automatically via `BaseAgentCallbackHandler.on_tool_start` / `on_tool_end`.
- **PII:** `reason` field sanitized via `core/luana-core-observability/recording/sanitization.py` before logging.

## 3. Prompt cache slot architecture (sales_agent compiler v2 — engine cementado)

> **DO NOT MODIFY engine compiler.** This story only adds a tool to the existing toolset. Cache prefix invariant.

```
SLOT 1 — System role            (cacheable, invariant globally — engine sales-agent)
SLOT 2 — Domain context         (cacheable, per-tenant invariant — vitalia: salud + bienestar + HIPAA-lite guardrails)
SLOT 3 — Tools manifest         (cacheable, per-graph invariant — UPDATED with retract_last_message addition)
SLOT 4 — Specialist persona     (cacheable, per-specialist invariant — warm_close per vertical)
SLOT 5 — BRAND_VOICE prefix     (cacheable, per-tenant invariant — from personality_profiles.system_instruction)
                                 ↑ cache_control marker HERE (engine cement) ↑
SLOT 6 — Conversation + turn    (variable, NOT cached)
```

**TTL choice:** 5min default (multi-turn within 5min, ~5-10 turns). Engine optimization already in place.

**Forbidden in cache prefix** (re-verified Slice 1):
- timestamps · conversation_id mid-block · tenant_name interpolated mid-block
- `retract_last_message` tool description must NOT include dynamic tenant/conv references — uses placeholders `{tenant_id}` / `{clinic_id}` / `{conversation_id}` / `{message_id}` resolved at runtime via LangChain tool calling

**Validation:** every LLM call must log `cache_creation_input_tokens` + `cache_read_input_tokens` (engine observability shipped). Auditor will FAIL if cache_read stays 0 across iter 2+ (silent invalidator in prefix).

## 4. Activity Stream consumption (inbox UI ← engine copilot_trace_event)

Inbox UI's `AgentActivityStream` component consumes events sourced from engine `copilot_trace_event` table (per `vitalia/backend/src/modules/vitalia/copilot/persistence/models/copilot_trace_event.py` schema mirror).

### 4.1 Data flow

```
Adrián turn pipeline (engine sales-agent)
  ↓ tool_call · tool_end · llm_call events
SalesAgentObservabilityContext.record_event(...)  ← engine shipped
  ↓ writes to sales_agent_trace_event + copilot_trace_event (cross-table mirror engine)
copilot_trace_event row
  ↓
ActivityEventService (vitalia/backend/src/modules/vitalia/inbox/application/services/activity_event_service.py)
  ↓ filter by conversation_id · sanitize_payload(compliance_level="hipaa_lite") · derive description_es
  ↓ optionally write projection row to vitalia_activity_events (cached) OR query direct
GET /api/v1/vitalia/inbox/conversations/{id}/activity-stream
  ↓
AgentActivityStream UI component (poll 5s when expanded)
```

### 4.2 description_es derivation (i18n cementado)

Engine emits events with English-y kind tags (`tool_called:consult_offer_price`, `llm_call_completed`, etc.). ActivityEventService maps them to Spanish neutral natural-language descriptions:

```python
# vitalia/backend/src/modules/vitalia/inbox/application/services/activity_event_service.py (excerpt)
DESCRIPTION_TEMPLATES = {
    "tool_called:consult_offer_price": "consultó precio de {offer_name} (${price})",
    "tool_called:check_appointment_availability": "verificó disponibilidad {date} {time}",
    "tool_called:propose_appointment_slot": "propuso: \"{proposal_text}\"",
    "tool_called:classify_stage_decision": "detectó: paciente {stage_signal} (stage {stage_num}/4)",
    "tool_called:retract_last_message": "revirtió mensaje · {reason}",
    "tool_called:send_payment_link": "envió link de depósito (${amount})",
    "tool_called:reschedule_appointment": "reagendó turno · {from_date} → {to_date}",
    "tool_called:screening_questions": "aplicó screening clínico · vertical {vertical}",
    "llm_call_completed:classify_intent": "clasificó: {classification}",
    "compliance_block": "bloqueó: {block_reason}",
    "fallback_triggered": "no pudo entender · derivó la conversación",
}
```

description_es field stored in `vitalia_activity_events` table or computed on-the-fly. PII sanitized before render (no patient name, no diagnosis, no PHI literal — uses placeholder "el paciente" / "la conversación").

## 5. Observability writes (mandatory consume engine shipped)

Per `.claude/rules/anti-duplication.md` §0:
- Trace events: `core/luana-core-observability/recording/turn_envelope.py::BaseObservabilityContext` (consumed via SalesAgentObservabilityContext shipped)
- LLM call recording: engine `sales_agent_llm_call` + `copilot_llm_call` tables (schema mirror per backend-ddd.md exception)
- PII sanitization: `core/luana-core-observability/recording/sanitization.py::sanitize_payload(compliance_level="hipaa_lite")` — vitalia adds PHI fields via `vitalia/backend/src/modules/vitalia/compliance/phi_fields.py`

**Cost target documented:**
- Adrián turn ≤ $0.05 USD (engine optimization shipped)
- Cache hit rate ≥ 60% (slots 1-5 cacheable · slot 5 cache_control marker)
- `retract_last_message` tool: ZERO LLM cost (deterministic — calls service, returns string)
- Activity Stream read: ZERO LLM cost (DB query + sanitize_payload only)

## 6. Eval goldens (sales_agent — opcional Slice 1)

Shipped story `vitalia-copilot-tools-impl` (2026-05-19) ya tiene goldens base. Esta story Slice 1 podría agregar 1-2 reinforcement goldens:

```yaml
# vitalia/backend/tests/agentic_evals/sales_agent/goldens/dental/T-inbox-retract-1.yaml (opcional NEW)
id: T-inbox-retract-1
vertical: dental
scenario: |
  Adrián sent a message claiming "el blanqueamiento te baja 5 tonos garantizado" — overpromise.
  ComplianceService flagged the message post-send (no clinical guarantee allowed).
  Adrián must invoke retract_last_message tool to revert.
input:
  - role: system
    content: "{ENGINE_COMPILED_PROMPT}"  # rendered by engine compiler v2
  - role: user
    content: "Hola, quería saber del blanqueamiento dental."
  - role: assistant
    content: "Hola María 😊 Te cuento: el blanqueamiento te baja 5 tonos garantizado. Cuesta $24.000."
  - role: system
    content: "[COMPLIANCE_BLOCK] Message flagged post-send: medical claim 'garantizado' violates HIPAA-lite. Use retract_last_message tool to revert."
expected:
  tool_calls:
    - name: retract_last_message
      input_validates: |
        # Adrián must call retract_last_message with reason mentioning the over-claim
        assert "garant" in tool_input.reason.lower() or "claim" in tool_input.reason.lower()
  next_message:
    contains_any:
      - "disculpá"
      - "perdón"
      - "no debí"
      - "no puedo asegurar"
voice_fidelity:
  threshold: 0.85
  voice_anchors:
    - "tone: warm + professional"
    - "no overpromise"
    - "acknowledge correction with humility"
```

**Decision Slice 1:** opcional this story. If retract_last_message tool added Slice 1, recommended add 1-2 goldens (test T-inbox-agentic-1 in 06-tickets). Otherwise defer to next slice when Adrián compliance integration matures.

## 7. Subagents / topology

**Slice 1 inbox: NO new subagents.** Engine sales_agent topology (cementado por S0-S12) ya soporta:
- Adrián specialist nodes: qualifier · product_expert · closer · supervisor · tool_executor · safety · escalate
- Channel format dispatcher (engine `core/luana-core-channels/format_for_channel.py`)
- Compliance gate (engine `core/luana-core-compliance/ComplianceService`)

`retract_last_message` tool registered globally in toolset · LangGraph runtime invokes via `tool_executor` node.

## 8. State extension (engine shipped)

Engine `SalesAgentState` (in `core/luana-core-sales-agent/`) extended by Vitalia via `VitaliaSalesAgentStateExtension` (shipped Story 11):

```python
# vitalia/backend/src/modules/vitalia/sales_agent/domain/state_overlay.py (EXISTING)
class VitaliaSalesAgentStateExtension(TypedDict, total=False):
    clinic_id: str  # MANDATORY for Vitalia turns
    vertical: Literal["dental", "estetica", "psicologia", "fertilidad", "otro"]
    screening_outcome: dict | None
    medical_disclaimer_shown: bool
    phi_blocked_messages: list[dict]  # ComplianceService blocks for audit
```

Slice 1 inbox: NO state extension changes. `retract_last_message` reads `clinic_id` from state, no new fields needed.

## 9. Checkpointer (production · engine shipped)

`langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` (engine sales_agent runtime cementado). Vitalia consumes via engine — no overrides.

Connection: `settings.postgres_dsn` (vitalia/backend env config).
Checkpoint table: `sales_agent_graph_checkpoints` (engine shared per anti-duplication).

## 10. Architecture fitness impact

Gates that must keep passing post this story:

- `vitalia/backend/tests/architecture/test_no_cross_brand_imports.py` — sales_agent extension doesn't import from `nicolify/` or `comunify/` or `lupulo/`.
- `vitalia/backend/tests/architecture/test_extension_sdk_registration.py` — `retract_last_message` tool registered via EP-3 in extensions.py.
- `vitalia/backend/tests/architecture/test_anti_duplication_shared_observability.py` — no mirror of engine observability/cost/pricing in vitalia/sales_agent/observability/. Engine consume via heredancia.
- Engine arch fitness (consult only): `core/luana-core-sales-agent/tests/architecture/test_grader_*.py` continues green (NO modification to engine).

## 11. Test surfaces (TDD-mandatory · RED first)

- **Tool unit** (`vitalia/backend/tests/modules/vitalia/sales_agent/tools/`):
  - `test_retract_last_message.py`:
    - happy: 5min window valid · adapter success → "Mensaje revertido…"
    - edge: expired 5min → "No pude revertir … excedió 5 minutos"
    - edge: patient replied → "No pude revertir: el paciente ya respondió"
    - edge: channel unsupported (email) → "Este canal no permite revertir … Lo marqué como erróneo"
    - adversarial: tenant_id/clinic_id mismatch → service raises, tool returns generic error
    - observability: tool call recorded in trace_event via SalesAgentObservabilityContext
    - audit: audit_log row written pre-response (verified via repo spy)

- **Eval goldens** (`vitalia/backend/tests/agentic_evals/sales_agent/goldens/dental/`):
  - `T-inbox-retract-1.yaml` (opcional Slice 1 — see § 6)

- **Integration** (covered by BE side `test_inbox_send_retract_audit_log.py`):
  - end-to-end: send ai msg → action receipt → tool `retract_last_message` invoked by Adrián → vitalia_messages.retracted_at + audit_log row + MessageRetracted event emitted

## 12. References

- `01-spec-extract.md` · `03-arch.md` · `03-arch-be.md`
- `.claude/rules/anti-duplication.md` (§ 0 cardinal)
- `.claude/rules/auditor-downstream-regression.md`
- `vitalia/.claude/rules/hipaa-lite.md`
- `vitalia/config/brand.yaml` (compliance_level=hipaa_lite + plan tiers)
- `core/luana-core-sales-agent/src/luana_core_sales_agent/` (engine — READ-ONLY consult)
- `core/luana-core-observability/src/luana_core_observability/recording/` (engine sanitization + turn_envelope)
- `core/luana-core-compliance/src/luana_core_compliance/` (engine ComplianceService)
- `core/luana-core-channels/src/luana_core_channels/format_for_channel.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/` (EXISTING shipped — Story 11 + vitalia-copilot-tools-impl)
- `vitalia/backend/src/modules/vitalia/extensions.py` (EXISTING — extend)
