# 02 · Core engine — qué hay HOY para un pipeline agent-operated

> Fuente: `core/luana-core-{crm,sales-agent,platform}` en el workspace actual + comparación con legacy. Investigado por agente Explore (read-only).

## ★ Titular: la maquinaria agéntica del pipeline YA ESTÁ en core (no se perdió en el reorg)

`core/luana-core-sales-agent/.../closer_studio/` está **completo en el core actual, byte-idéntico al legacy** (155 archivos py iguales; diff cero en `command_service.py`, `kpi_service.py`, `query_service.py`). El reorg multimarca **NO removió** capacidades — solo levantó modelos compartidos a `luana_core_platform`. **Lo que falta es que vitalia construya ENCIMA.**

## Contrato del pipeline engine (hoy)

- **`LifecycleStage`** (platform enums): `SUBSCRIBER | LEAD | MQL | SQL | OPPORTUNITY | CUSTOMER | EVANGELIST | CHURNED` (score-driven, marketing bowtie).
- **`FunnelStage`** (crm enums): `S1_Rapport | S2_Discovery | S3_Gap | S4_Pitch | S5_Anchoring | S6_Closing | DOWNSELL_EXIT` (conversación).
- **Scoring** (`crm/domain/scoring.py`): 3 dimensiones (engagement / intent / fit), pesos por evento (`form_submitted=5`, `meeting_requested=10`, `pricing_viewed=4`, …), thresholds `LEAD≥10 / MQL≥40 / SQL≥70`, decay 5%/día.
- **`lifecycle_transitions`** (tabla audit): `from_stage, to_stage, reason, triggered_by (scoring_rule|sale_event|manual|decay|reactivation), score_at_transition, metadata(JSONB), occurred_at`.
- **API pipeline** (`crm/api/pipeline.py`): `GET /pipeline` (lista plana, `min_score` declarado pero NO aplicado — stub) · `PUT /pipeline/{id}/stage` (override manual + audit, `triggered_by=manual`) · `GET /pipeline/{id}/transitions` (historial).

## ★ Sustrato agent-operating (sales-agent · closer-studio)

**`AgentStateCheckpointModel`** = el vehículo donde el agente escribe el estado del pipeline por conversación:
- `current_stage` (String, default "rapport") — posición funnel **que el agente mueve cada turno**
- `lead_score` (Integer) · `buying_signals` (JSONB) · `objection_history` (JSONB) · `qualification_answers` (JSONB)
- `handler_mode` ("ai"/"human") · `frozen_at` · `frozen_reason` · `frozen_diagnosis`
- `scheduled_meetings` (JSONB, booking) · `payment_state` (JSONB, pago)

**Closer Studio endpoints** (presentes en core actual): stop / resume / send_message(direct\|instruction) / nudge / reactivate / diagnose / kpis / frozen. **Diagnose** genera análisis IA desde checkpoint (score, stage, signals, objections).

**TOOL_REGISTRY sales-agent**: `send_payment_link, check_schedule, recommend_product, escalate_to_human` (+ enrollment/scheduling/payment registries). NO hay tool explícito "mover lead a etapa N" — la transición es side-effect del progreso conversacional en los nodos LangGraph.

**Workers**: `follow_up_engine`, `frozen_detection`, `appointment_reminder_engine`, `payment_reminder_engine`, `verify_pending_bookings`, `verify_pending_payments` — todos presentes.

**copilot_provider**: CRM expone solo `lead_count` read-only (DataAccessProvider). Sales-agent provider es metadata-only. El agente NO escribe CRM lifecycle vía copilot — mueve `current_stage` del checkpoint.

## Eventos de dominio (EventBus, outbox activo)

`sale_completed→CUSTOMER`, `churn_detected→CHURNED`, `lead_captured→audit`, `appointment_booked→journey_event(meeting_booked)+score`, `appointment_completed`, `appointment_no_show`. Emite `PaymentLinkCreatedEvent`, `PaymentReceivedEvent`, `BookingLinkCreatedEvent`, `AccessGrantedEvent`.

## Vitalia CRM brand-module hoy (qué falta)

`vitalia/crm/domain/lead.py::Lead` (non-PHI): `id, tenant_id, name, email, phone, source, status(new|contacted|qualified|lost|converted), notes, deleted_at`. **Falta TODO**: sin `stage` enum (solo el flat `status` de 5 valores), sin audit de transiciones, sin scoring, sin linkage a checkpoint del agente, sin endpoint de board agregado.

Endpoints vitalia crm: `GET/POST/PATCH /leads`, `GET /leads/{id}`, `GET/PATCH /patients/{id}` (PHI gated), `GET /conversations` (stub empty Slice 1).

**EP-15 ya inyecta** `LifecycleStageDef(stage_id="vitalia:pending_consent", after="lead", before="booking")` — única customización de funnel hecha (precedente del patrón Extension SDK para etapas vitalia-local).

## Boundary REUSE vs BUILD (para embudo vitalia dental agent-operated)

| REUSE del engine | BUILD brand-local (vitalia) |
|---|---|
| Sustrato closer-studio (stop/resume/nudge/diagnose/kpis) | **Vocabulario de 6 etapas dentales** (vía Extension SDK, como EP-15) |
| `AgentStateCheckpointModel.current_stage` como superficie de lectura/escritura del agente | Mapeo `current_stage` → etapas dentales + prompts/especialistas vitalia (intake/asesor/confirmador) |
| Patrón `lifecycle_transitions` (schema audit) | Tabla `vitalia_funnel_transitions` (mismo schema) si se quiere audit por etapa vitalia |
| `force_stage()` / `PUT /pipeline/{id}/stage` para override manual | **Endpoint de board agregado** (`GET .../board` agrupado por etapa — engine devuelve lista plana) |
| EventBus `AppointmentEvent`, `PaymentReceivedEvent`, `SaleCompletedEvent` | **Agent tool** `move_to_stage(stage)` vitalia (no existe en engine) |
| Workers follow_up / frozen_detection / reminders | `copilot data_access` para conteos por etapa vitalia |
| Scoring (pesos engagement/intent — `message_sent`, `meeting_requested`) | PHI firewall: lead=interés (non-PHI), clínico fuera del embudo |

## Legacy vs actual: delta = CERO

Sales-agent y CRM son byte-idénticos entre legacy y actual. Closer Studio presente en ambos. Nada se perdió. El "gap" es que el brand-module vitalia nunca construyó sobre el sustrato.

## Implicancia para la decisión B (batch 1)

La decisión B ratificada ("stage machine vitalia-local, NO consumir engine") se tomó con lectura incompleta (solo `api/pipeline.py` + crm Lead). El sustrato agent-operating real (closer-studio + checkpoint + handler_mode + frozen/diagnose + transitions + workers) es **vertical-agnóstico** salvo labels + prompts. **Recomendación revisada: CONSUMIR el sustrato agéntico del engine + vocabulario/prompts dentales vitalia-local (Extension SDK).** No recrear el runtime; no co-optar el LifecycleStage marketing. Ver `00-propuesta-embudo-agentico.md`.

`02-core-engine.md` (persistido por orquestador desde digest del Explore read-only)
