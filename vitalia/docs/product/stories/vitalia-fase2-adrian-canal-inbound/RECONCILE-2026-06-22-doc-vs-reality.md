# Reconcile — doc vs reality (sales_agent loop) · 2026-06-22

> **Owner:** `/pm-vitalia`. **Trigger:** Chris pidió auditoría profunda checkpoint-vs-código tras avance paralelo (lift loop). **Método:** 3 auditorías read-only paralelas (brand `sales_agent` · engine ABI/bridge · loop+telegram+booking) + verificación git de SHAs/proposal. **Verdict global:** lo construido es **real y sólido** (no humo); el checkpoint **subreporta 2 gaps de cableado live** y tiene **1 nota stale** (autonomous-dispatch). Este doc es el SSoT del estado real.

## TL;DR

- ✅ **El grafo corre live por Telegram** (webhook real → Adrián responde). OLA-1 (texto) firmada por Chris.
- ✅ **Autonomous-dispatch RESUELTO + promovido a main** (0 → ~1.0). El checkpoint aún lo listaba como deferido (F-path) → **stale, corregido**.
- ✅ **share/match = reales + live** (native sync, DB real, URL `/d/{clinica}/{doctor}` real).
- 🟡 **6 de 9 tools dispatchan pero erroran** — sus DI resolvers nunca se cablearon al lifespan (degradan a error-dict). Solo los 3 native-sync (share/match/book) ejecutan lógica real.
- ❌ **`book_appointment` runtime-bloqueado (ESC-19)** — create-lane de scheduling no existe + dos tablas appointment (isla anti-orphan). Escalado a Chris (decisión de dominio scheduling).
- ❌ **2 objetivos core del spec NO cableados al loop live:** (1) modo `consulta` (borrador, 0 outbound) no se intercepta; (2) el loop **no emite activity event** al inbox ("nutre el inbox glass-box" = no cumplido en runtime).

## 1 · Matriz de tools (reality)

| Tool | Tipo | Servicio real | Dispatch live | Ejecuta lógica real | Estado |
|---|---|---|---|---|---|
| `share_doctor_profile` | native sync `(state,db)->dict` | read `VitaliaDoctorModel`/`ClinicModel` | ✅ | ✅ | **LIVE** |
| `match_service_and_specialist` | native sync | read `ProductModel`+`OfferServiceSpecialistLinkModel`+doctores | ✅ | ✅ | **LIVE** |
| `book_appointment` | sync → `run_async` bridge → `CreateAppointmentService` | scheduling create-lane | ✅ (dispatcha) | ❌ AttributeError (`repo.create` no existe) | **WIRED, ESC-19 blocked** |
| `screening_questions` | async StructuredTool + adapter | `ScreeningQuestionsService` | ✅ | ❌ resolver no cableado → error-dict | **resolver-unwired** |
| `send_payment_link` | async + adapter | `PaymentLinkService` | ✅ | ❌ resolver no cableado | **resolver-unwired** |
| `reschedule_appointment` | async + adapter | `RescheduleAppointmentService` | ✅ | ❌ resolver no cableado | **resolver-unwired** |
| `send_proactive_reengagement` | async + adapter | `ProactiveOutboundService` | ✅ | ❌ resolver no cableado | **resolver-unwired** |
| `retract_last_message` | async + adapter | `RetractMessageService` | ✅ | ❌ resolver no cableado | **resolver-unwired** |

> 9 tools brand registrados (5 async-wrapped + share/match/book native) + 4 wizard = 13 dispatchable (claim CONFIRMADO, era registry-presence). **Pero "dispatch ~1.0" ≠ "tool funciona":** la métrica `sales_agent.tool_dispatched` cuenta la emisión del call; el éxito de datos depende del resolver. Por eso share/match (sin resolver) brillan y los 6 wrapped erroran hasta cablear `set_*_service_resolver` en `register_all`.

## 2 · Mecanismo ESC-17 / bridge async (CONFIRMADO real)

- Engine ABI sync: `node_tool_executor` → `tool_fn(state, db=state["_db"])` (`core/luana-core-sales-agent/.../agents/sales/nodes.py:505`).
- Brand adapter: `structured_tool_adapter` (`vitalia/.../sales_agent/tool_bridge.py:123`) wrappea las StructuredTools async → sync `(state,db)->dict`. Arch test `test_ep3_handlers_sync_callable.py` lo enforza.
- Cross-loop bridge: `run_async` → `run_coroutine_threadsafe(coro, _main_loop)` con `set_main_loop(get_running_loop())` en lifespan (`vitalia/.../main.py:75`). Mata el "Future attached to a different loop".
- ESC-18: relación muerta `LeadModel.appointments` (string-stub a clase no registrada) removida del engine (`core/luana-core-platform/.../crm.py:213-221`).
- Engine boundary respetado: cambios en `core/` cubiertos por proposal `2026-06-22-sales-agent-multibrand-graph-runtime` (state: **migrated**).
- ⚠️ `state["_db"]` siempre None en inbound (engine nunca lo siembra) → cada tool abre su propia `Session(get_engine())`. Degrada bien pero el param `db=` del ABI está muerto; share/match abren sesión sync fuera del UoW de request (tenant-scoped, sin PHI — patrón a vigilar).

## 3 · Loop wiring (reality)

| Pieza | Estado | Evidencia |
|---|---|---|
| Webhook Telegram (secret + dedup `update_id` + tenant-resolve) | ✅ REAL | `connections/telegram/api/router.py:165-277` (mig 047) |
| Persist + invoke orchestrator + debounce | ✅ REAL | `chat.py:139-180` → buffer → `smart_debounce` → `process_chat_flow` |
| Modo `decide` → responde | ✅ | grafo corre |
| Modo `human`/pausa → NO responde | ✅ | engine `ConversationPipeline.handle_human_mode` (`conversation_pipeline.py:128-150`) |
| Modo `consulta` → borrador, 0 outbound | ❌ **NO cableado** | `HonorModeBridge` solo lo consume `operator_instruction_service.py`, **no** el loop inbound. Sin pre-send interceptor en `extensions.py` |
| Emitir activity event al inbox (glass-box) | ❌ **NO emitido** | `process_chat_flow`/pipeline escriben solo `audit_log`, nunca `vitalia_activity_events` (esos salen de operator-instruction/send/nudge) |
| `setWebhook` registration | ⚪ out-of-band (operacional, no en código prod) |

## 4 · Booking ESC-19 (CONFIRMADO bloqueo legítimo)

- Dos tablas: engine `appointments` (`core/luana-core-scheduling/.../appointment_model.py`) que escribiría el create-service · brand `vitalia_appointments` (sin ORM, raw SQL en `agenda_grid_repository_impl.py:99`) que **lee** la grilla de Mateo. Escribir el engine table = isla anti-orphan (la grilla no lo ve).
- `AgendaGridRepositoryImpl` no implementa `create()`/`create_clinic_map()` → `CreateAppointmentService.create_appointment` haría `AttributeError` → atrapado → "No pude crear el turno por un problema técnico".
- `VitaliaSchedulerProvider` = **no existe** (solo en docs); el Protocol engine `SchedulerProvider` es event_slug-céntrico, no doctor+slot.
- **Veredicto:** book es decisión de **dominio scheduling** (unificar tabla + implementar create-lane), bien escalada a Chris. Fuera de OLA-2 puro.

## 5 · Drift checkpoint → acción

| # | Claim del checkpoint | Reality | Acción doc |
|---|---|---|---|
| D1 | autonomous-dispatch DEFERIDO (F-path: "LLM no despacha solo") | RESUELTO + promovido a main (`d8c737c4`+`7a326124`, 0→~1.0) | ✏️ checkpoint corregido + proposal ya current |
| D2 | "share/match LIVE, book wired-blocked" | CONFIRMADO | sin cambio |
| D3 | (implícito) tools de marca ejecutables | solo 3 de 9 ejecutan; 6 con resolver no cableado | ✏️ checkpoint known-gaps + validators |
| D4 | "honra el modo por-conversación" (Goal/pipeline) | solo decide+pausa; `consulta` NO interceptado | ✏️ checkpoint known-gaps + V-FN-2 flag |
| D5 | "nutre el inbox glass-box" (Goal/pipeline + V-FN-1 "+activity") | loop NO emite activity event | ✏️ checkpoint known-gaps + V-FN-1 flag |
| D6 | V-FN-8 deferred reason = "ESC-17/Tier-2.4a (ABI handler roto)" | ESC-17 resuelto; blocker real = DI resolvers no cableados | ✏️ V-FN-8 deferred reason actualizado |

## 6 · Trabajo restante a `done` (priorizado)

**Buildable ya (cero engine, brand-local):**
1. **Cablear los 6 DI resolvers** en `register_all` (`set_screening/payment/reschedule/reengagement/retract_service_resolver`). Sin esto, autonomous-dispatch luce verde pero los tools erroran. **Alto valor, bajo riesgo.**
2. **Activity-feed emit** desde el loop — el objetivo "nutre el inbox". Necesita hook desde `process_chat_flow` (engine) → evento brand. Probable EP/event-bus → **/architect** decide si brand-local vía EP o requiere seam engine.
3. **Consulta-mode interception** — pre-send gate que respete `HonorModeBridge` en el loop. Mismo punto: el send vive en engine → **/architect** (¿EP pre-send brand o seam engine?).

**Bloqueado / decisión Chris:**
4. **book ESC-19** — unificar tabla appointment + create-lane scheduling. Dominio scheduling (ver `vitalia-scheduling-mateo-review`). No avanza sin decisión.

**Verde ya:** OLA-1 texto (firmado) · share/match live · ESC-17/18 + bridge + lift migrated.

## Referencias

- Checkpoint: `checkpoint.md` (§ frontmatter `engine_lift_phase1` / `lift_E_promote` corregidos + `known_gaps_2026-06-22`)
- Validators: `04-validators.yaml` (V-FN-1/2 flags + V-FN-8 reason)
- Proposal engine: `docs/promotion-protocol/proposals/2026-06-22-sales-agent-multibrand-graph-runtime.md` (migrated)
- Learnings: `docs/learnings/2026-06-22-{ep3-tool-handler-abi-mismatch,tools-advertised-executable-not-dispatched,engine-reuse-must-be-exercised-live}.md`
- Engine ABI: `core/luana-core-sales-agent/.../agents/sales/nodes.py:505` · bridge `vitalia/.../sales_agent/tool_bridge.py`
