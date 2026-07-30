---
story_id: vitalia-fase2-adrian-canal-inbound
brand: vitalia
doc: 03-arch
arch_version: 1
schema_version: v4.1
architect_run_on: 2026-06-21
architecture_pattern: ADR-vitalia-004
adr_004_compliance: partial-with-rationale   # FE composer = sub-tab EXTEND (not new sub-tab); rationale § Architecture Decisions
consumes: 01-spec.md (v6) · 02-design-agentic.md (v3)
cap_target: adrian.inbox
cap_change_type: extend
verdict: BLOCKED-PARTIAL    # brand-local surfaces buildable NOW; core agentic value (book/match via graph) requires /pm-luana lift — see § Engine-boundary escalations
autonomous_mode: false     # agentic + PHI = stake-asimétrico; gate G (Chris-verify live Telegram) mandatory
sota_reviewed: 2026-06-21
---

# 03-arch — canal-inbound (Adrián) · contrato técnico

> **Lectura de un párrafo:** El diseño v3 es excelente y su norte (montar sobre el engine, no rediseñar)
> es correcto. **Pero la auditoría de código (prior-art re-scan, § Prior art audit) descubre tres muros
> de engine-boundary que el diseño asumió resueltos y NO lo están:** (1) el resolver de scheduler del
> engine hardcodea `"internal"` e ignora `tenant_id`; (2) el `TOOL_REGISTRY` del engine es un dict de
> módulo que NO mergea tools de marca (EP-3); (3) `STAGE_TOOL_SCOPE` es un dict de engine hardcodeado.
> Sin un **lift `/pm-luana`** que abra esos tres hooks, los tools NUEVOS de Adrián
> (`book_appointment`, `match_service_and_specialist`, `share_doctor_profile`) **no se pueden cablear al
> grafo** sin editar `core/luana-core-sales-agent/src/`. Lo que **SÍ es brand-local y buildable hoy**: el
> canal Telegram (receiver+route+honor-modo+set-instruction), la plomería de `scheduling`
> (marcar `availability_slot` + hold-TTL + sweep), y el composer FE en modo-instrucción. Este arch entrega
> el ready package para esas superficies + escala el muro agentic a `/pm-luana`.

---

## § 0 · Context Summary

- **PR / story:** `vitalia-fase2-adrian-canal-inbound` (F3, agentic-story, `extend`, cap `adrian.inbox`).
- **Architect run on:** 2026-06-21.
- **Módulos tocados:** `connections/telegram` (NEW, BE), `scheduling` (EXTEND, BE), `sales_agent` (EXTEND, agentic),
  `inbox`/`adrian` FE (EXTEND composer), `api/webhook_routes.py` (replace stubs, BE).
- **CONTEXT-BRIEF source:** ausente (story sin brief Haiku) → **self-ran greps Path B** (prior-art re-scan
  ejecutado verbatim, § Prior art audit + § Existing systems audit).

### Surface → builder → auditor mapping (PM usa para spawnear los agentes correctos)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/.../sales_agent/{tools,domain,application,prompts,personas,goldens}/` (agentic prod) | **`builder-agentic`** (flagship) | **`auditor-agentic`** (flagship) |
| `vitalia/.../connections/telegram/` + `vitalia/.../api/webhook_routes.py` + `vitalia/.../scheduling/` (BE) | **`builder-backend`** (workhorse) | **`auditor-backend`** (flagship) |
| `vitalia/frontend/src/features/{adrian,inbox}/...` (FE composer instrucción) | **`builder-frontend`** (workhorse) | **`auditor-frontend`** (flagship) |
| `core/luana-core-sales-agent/src/**` (3 hooks: scheduler routing + extension-tool merge + stage-scope) | **`/pm-luana` promotion gate** (NOT a builder) | n/a → escalate |

### Skills consultados (decisión tomada de cada uno)

- **`sales-agent-expert`**: §3 protected surfaces (orchestrator, debounce, OutputManager, follow_up_engine,
  `tool_call_dedup`) — NO tocar; el book MONTA sobre el grafo, no lo reescribe. Anti-dup cardinal §0:
  observability/cost/channel viven en engine, consumir vía import. **Hallazgo crítico:** el `TOOL_REGISTRY`
  del engine (`application/agents/sales/tools.py:107`) es un dict hardcodeado que NO mergea EP-3 → tools de
  marca no dispatchan por el grafo hoy.
- **`copilot-expert`**: "verificá que algo existe (grep + schema + registry) antes de declarar que falta" —
  aplicado: cada anchor del diseño v3 §2 fue grepeado. Best-effort observability (try/except + structlog).
- **`backend-expert`**: `create_appointment_service` ya existe (async, dual-persist appointment+clinic_map +
  audit sync); el gap real = no marca `has_confirmed_appointment`. Migrations idempotentes raw SQL.
- **`frontend-expert`**: composer del inbox = EXTEND (reusar `MessageInput` legacy effectiveMode pattern),
  no nuevo componente. Live-verify via `chrome-devtools-verify`.
- **LangGraph canonical docs (WebSearch 2026-06-21):** supervisor StateGraph es el patrón del engine
  (validado). `langgraph>=0.2` pin del engine es viejo pero estable; NO bumpear (engine = `/pm-luana`).

### capability YAML files affected (post-merge, paradigma post 2026-05)

- `vitalia/docs/product/capabilities/inbox/adrian-inbox.yaml` (cap_target, `extend`) — agregar scenarios
  del loop inbound + honor-modo + booking + § access + § business_rules v3.2.
- **Posible derived cap `adrian.canal-inbound`** (cap_change_type=`derive`): el loop inbound autónomo +
  book es funcionalmente distinto del inbox (UI). **Decisión architect:** crear cap derivada
  `sales_agent.adrian-canal-inbound` (área `adrian.inbox`) con `make new-cap` — el loop es un trigger del
  runtime, no de la UI; merece caja propia en el cockpit. Ver § 13. (Gate 5b lo exige si new-cap.)

### Architecture gates que deben seguir verdes

- `vitalia/backend/tests/architecture/test_phi_dual_filter.py` (dual filter tenant+clinic).
- `vitalia/backend/tests/architecture/test_audit_log_sync_write.py` (audit sync pre-response).
- `vitalia/backend/tests/architecture/test_response_model_required.py` (response_model en cada route).
- `vitalia/backend/tests/architecture/test_growth_studio_event_no_phi.py`.
- `core/luana-core-sales-agent/tests/architecture/` (NO modificar — engine read-only).
- `vitalia/backend/tests/architecture/` DDD boundaries + anti-mirror cross-brand.

---

## § Prior art audit (re-scan verbatim — anchors del diseño v3 §2 verificados contra código real)

> Ejecutado 2026-06-21 (self-run, Path B). Cada anchor del diseño v3 fue grepeado. **EXISTE** = el path:line
> está y el contrato coincide. **GAP** = el anchor existe pero el contrato NO permite lo que el diseño asumió
> (→ § Engine-boundary escalations).

| Anchor (diseño v3) | Verificación real | Veredicto |
|---|---|---|
| Orchestrator `handle_telegram_webhook` (per-tenant token + adapter + debounce) | `core/.../orchestrator/chat.py:93-128` — **resuelve token vía `get_channel_credentials` + `create_telegram_adapter` (platform port) + debounce**. Ya wired end-to-end. | ✅ EXISTE (mejor de lo esperado — BE chico) |
| `create_telegram_adapter` platform port | `core/luana-core-platform/.../links/ports/channel_adapter.py:19` | ✅ EXISTE |
| `get_channel_credentials` (per-tenant token) | `core/luana-core-platform/.../links/ports/calendar.py:19` | ✅ EXISTE |
| `BaseChannel` + `normalize_payload` | `core/luana-core-platform/.../infrastructure/channels/base.py:12,23` | ✅ EXISTE (template del adapter Telegram) |
| `handle_human_mode` (honor-modo) | `core/.../orchestrator/conversation_pipeline.py:128-149` — **solo honra `handler_mode=='human'`** (skip AI). NO modela "consulta" (draft) ni "pausa" nativamente. | ⚠️ PARCIAL (bridge brand) |
| Supervisor + qualifier/product_expert/closer + signal_accumulator | `core/.../application/agents/sales/nodes.py` (paths reales = `application/agents/sales/`, no `agents/sales/`) | ✅ EXISTE |
| `objection_history` + Aikido + rutas `objection_*` + `tenant_route_overlay` | `agent_state_checkpoint_model.py:34` + `tenant_route_overlay.py` (per-tenant LIVE hook) | ✅ EXISTE |
| `SchedulerProvider` Protocol + `register_scheduler_provider` + `SCHEDULER_PROVIDERS` | `core/.../tools/scheduling/providers.py:148,425,430` — registry existe | ⚠️ GAP (ver abajo) |
| `scheduler_provider_for_tenant` (routing per-tenant) | `providers.py:439-449` — **hardcodea `SCHEDULER_PROVIDERS["internal"]`, ignora `tenant_id`** (`_ = tenant_id # reserved`). | 🔴 GAP-1 (engine edit) |
| `get_available_slots`/`create_booking_link`/`verify_booking_status` tools (vía provider) | `tools.py:123,179,240` llaman `scheduler_provider_for_tenant(db, tenant_id)` → siempre "internal" | ⚠️ GAP (heredan GAP-1) |
| `scheduled_meetings` JSONB + `MeetingEntry` + `MeetingStateService` | `agent_state_checkpoint_model.py:69` + `meeting_state_service.py:57` — **`MeetingEntry` es `@dataclass(frozen, slots=True)` SIN `doctor_id`/`service_id`** | ⚠️ GAP-4 (overlay brand evita engine) |
| Workers `verify_pending_bookings`/`appointment_reminder_engine`/`follow_up_engine`/`frozen_detection` | `workers/*.py` — `verify_pending_bookings` reconcilia hold→expired vía `provider.verify_booking_status()` | ✅ EXISTE (hold-TTL gratis SI el provider expone expiry) |
| `STAGE_TOOL_SCOPE` + `get_tools_for_stage` | `registry.py:56-110` — **dict hardcodeado de engine**; filtra estricto `ALWAYS_AVAILABLE \| stage_set` | 🔴 GAP-3 (engine edit para tool names nuevos) |
| Engine `TOOL_REGISTRY` (dispatch del grafo) | `application/agents/sales/tools.py:107` — **dict de módulo hardcodeado; NO mergea EP-3**. `nodes.py:402` hace `TOOL_REGISTRY.get(name)` directo. NO existe `class ToolRegistry.register_tool_from_extension` (el `_SalesAgentToolRegistryAdapter` lo exige y falla `NotImplementedError`). | 🔴 GAP-2 (engine edit / lift) |
| `AgentState` (runtime state) | `application/orchestrator/state.py:8` — **`TypedDict` cerrado, sin extensión**. `register_state_extension` NO existe. Las keys de marca (clinic_id, screening) fluyen por `lead_data`/`tenant_config` dicts, NO como top-level. | ⚠️ GAP-5 (overlay brand evita engine) |
| Brand `state_overlay.py` (`VitaliaSalesAgentStateExtension`) | `vitalia/.../sales_agent/domain/state_overlay.py:50-92` — TypedDict total=False; **NO está cableado a `AgentState` del engine** (no hay merge mechanism) | ✅ EXISTE (pero su composición al runtime = GAP-5) |
| Brand tools (`screening_questions`, `payment_link`, `reschedule_appointment`, ...) | `vitalia/.../sales_agent/tools/*.py` registrados EP-3 en `extensions.py` — **pero NO en engine `TOOL_REGISTRY`** → no dispatchan por el grafo hoy | 🔴 hereda GAP-2 |
| `override_context_wire` (operator instructions) | `vitalia/.../sales_agent/application/services/override_context_wire.py:89` — `set_override_context` → `metadata_info[override_context]` JSONB (key real = `override_context`, NO `operator_instructions`) | ✅ EXISTE (EXTEND: usar key existente o agregar `operator_instructions` en el mismo JSONB) |
| `ComplianceService.validate_outbound_message` | `core/luana-core-compliance/.../compliance_service.py:41` | ✅ EXISTE |
| `offer_service_specialist_links` (link servicio↔doctor) | `vitalia/.../offer/.../offer_service_specialist_link_model.py:19` (`tenant_id/offer_id/doctor_id`, migr 045) | ✅ EXISTE (live) |
| `availability_slots` + `has_confirmed_appointment` | `vitalia/.../clinics/.../availability_slot_model.py` + `availability_projection_service.py:77` | ✅ EXISTE (live) |
| `create_appointment_service` (`origin=proactivo_adrian`) | `vitalia/.../scheduling/.../create_appointment_service.py:76` — async, dual-persist + audit; **NO marca `has_confirmed_appointment`** | ✅ EXISTE + GAP (cerrar el marcado del slot) |
| `AppointmentOrigin.PROACTIVO_ADRIAN` | `vitalia/.../scheduling/domain/appointment_origin.py:30` | ✅ EXISTE |
| Doctor public page `/d/{clinica-slug}/{doctor-slug}` | `vitalia/frontend/src/app/d/[clinica-slug]/[doctor-slug]/page.tsx` + `public_doctor_serializer.py` | ✅ EXISTE (URL para `share_doctor_profile`) |
| `BookingService`/`vitalia_bookings` | cap `booking/prepaid-booking-advisory-locks.yaml:5` **`status: deprecated`** | ✅ confirmado DEPRECATED — NO usar (anti-isla) |

**Conclusión de la auditoría:** el diseño v3 acierta en el 90% del *concepto*, pero su afirmación operativa
"todo se consume por APIs existentes, cero engine" **no se sostiene en 3 puntos duros** (GAP-1/2/3). El loop
nunca se cableó, así que estos muros nunca se ejercieron. Los GAP-4/5 SÍ tienen workaround brand-local
(overlay). Los GAP-1/2/3 obligan a tocar engine → **STOP-flag `/pm-luana`** (§ Engine-boundary escalations).

---

## § Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — fallback, no había CONTEXT-BRIEF)

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Engine sales_agent runtime (supervisor+especialistas+rutas+objeciones+señales) | `core/luana-core-sales-agent/src/.../application/{orchestrator,agents/sales}` | active | **CONSUME vía import** (read-only) |
| Subsistema agendamiento S8 (SchedulerProvider+tools+scheduled_meetings+workers) | `core/.../application/tools/scheduling/` + `workers/` | active | **CONSUME el patrón**; provider de marca + (GAP-1/2/3 → lift) |
| Lane scheduling VIVO (agenda Mateo) | `vitalia/.../scheduling/` (`create_appointment_service`, `availability_slots`) | live | **EXTEND** (marcar slot + hold-TTL) |
| `BookingService`/`vitalia_bookings` | `vitalia/.../application/services/booking_service.py` | **deprecated** | **NUNCA usar** (referencia de patrón advisory-lock/hold solamente) |
| Brand sales_agent extension (tools+personas+state_overlay+observability) | `vitalia/.../sales_agent/` | live (parcial) | **EXTEND** (+3 tools, +overlay keys) |
| Inbox honor-modo + PHI policy + activity stream | `vitalia/.../inbox/` (cap `adrian-inbox`) | live | **CONSUME + HONRAR** (regression_guard); EXTEND composer |
| `override_context_wire` (operator instruction) | `vitalia/.../sales_agent/application/services/override_context_wire.py` | live | **REUSE + EXTEND** (key JSONB) |
| Connections adapters (whatsapp/instagram outbound + email/google_ads/payment) | `vitalia/.../connections/` | live | **PATRÓN** para el adapter Telegram NEW |
| Doctor public page + serializer | `vitalia/frontend/src/app/d/...` + `clinics/.../public_doctor_serializer.py` | live | **CONSUME** (URL para share_doctor_profile) |

### Decisión por sistema
- **Telegram inbound channel (path: connections/whatsapp,instagram)**: **NEW adapter** `connections/telegram/`
  + **REUSE** engine `handle_telegram_webhook` (ya wired). Justificación: Telegram no existe en connections;
  el patrón adapter sí. NO net-new layer — implementa `BaseChannel` del engine.
- **Scheduling slot-marking + hold-TTL (path: scheduling/)**: **EXTEND** `create_appointment_service` +
  NEW sweep job. Justificación: el lane vivo no marca slot ni tiene hold; cerrar el gap aquí evita isla.
  NUNCA `BookingService` deprecado.
- **VitaliaSchedulerProvider (path: sales_agent/)**: **NEW provider** (impl `SchedulerProvider` Protocol) +
  registro vía `register_scheduler_provider`. **PERO** su routing requiere GAP-1 (engine) → § escalations.
- **Cross-brand mirror check:** ✅ ninguno — Telegram inbound + scheduler provider vitalia son brand-local;
  no replican patrón de otra brand. (nicolify reseteada; comunify sin sales_agent médico.)

**Sin NEW layer redundante.** Todo es EXTEND o consume del engine. El único "NEW" agentic real
(VitaliaSchedulerProvider + 3 tools) cae sobre el muro engine-boundary, no sobre duplicación.

---

## § Engine-boundary escalations (★ STOP-flag → `/pm-luana` promotion gate)

> **Estas son las razones del verdict `BLOCKED-PARTIAL`.** Tres hooks del engine `core/luana-core-sales-agent`
> están cerrados; sin abrirlos, el valor agentic central (el agente AGENDA/MATCHEA por el grafo) no se cablea
> sin editar `core/luana-core-sales-agent/src/`. **NO se genera ticket de builder para estos** — van a
> `/pm-luana`. Cada uno trae el path:line del muro + el cambio mínimo propuesto + por qué es lift y no
> brand-local.

### ESC-1 — `scheduler_provider_for_tenant` ignora `tenant_id` (hardcodea "internal")
- **Muro:** `core/.../application/tools/scheduling/providers.py:439-449` →
  `klass = SCHEDULER_PROVIDERS["internal"]; _ = tenant_id`.
- **Por qué bloquea:** los tools `get_available_slots`/`create_booking_link` (vivos, en stage scope) resuelven
  el provider por aquí. Registrar `VitaliaSchedulerProvider` vía `register_scheduler_provider` (que SÍ existe)
  NO sirve: el resolver nunca lo elige. El docstring lo dice: *"When tenant config grows a `scheduler_provider`
  column … branch here"*.
- **Cambio mínimo (lift):** que `scheduler_provider_for_tenant` lea un campo per-tenant
  (`tenant_config.scheduler_provider` o `connections`) y branchee a `SCHEDULER_PROVIDERS[choice]`. ~10 LOC +
  arch test. Engine-wide (beneficia toda brand con scheduler propio) → lift legítimo.
- **Por qué NO brand-local:** el resolver vive en engine y es el único punto que los tools consultan; no hay
  override per-tenant ni hook de marca.

### ESC-2 — `TOOL_REGISTRY` del engine no mergea tools de marca (EP-3)
- **Muro:** `core/.../application/agents/sales/tools.py:107` (dict de módulo hardcodeado) + `nodes.py:402`
  (`TOOL_REGISTRY.get(name)` directo). El `_SalesAgentToolRegistryAdapter`
  (`core/luana-core-extension-sdk/.../_adapters.py:58-83`) exige un `class ToolRegistry.register_tool_from_extension`
  que **NO EXISTE** en el engine → `raise NotImplementedError`.
- **Por qué bloquea:** los 3 tools NUEVOS de Adrián (`book_appointment`, `match_service_and_specialist`,
  `share_doctor_profile`) registrados EP-3 nunca llegan al `TOOL_REGISTRY` que el grafo dispatcha. Hoy los
  tools de marca SHIPPED (`reschedule_appointment`, `screening_questions`) tampoco dispatchan (el loop nunca
  corrió → nunca se notó).
- **Cambio mínimo (lift):** el engine `TOOL_REGISTRY` debe ser un registry mutable que mergee tools EP-3 al
  runtime (implementar `register_tool_from_extension` que el adapter ya espera), y `get_tools_for_stage`/
  `nodes.py` deben consultarlo. ~30-50 LOC + arch test "extension tool dispatchable".
- **Por qué NO brand-local:** el dispatch (`nodes.py`) y el registry viven en engine; la marca no puede
  inyectar sin un hook del engine. **Era el diseño intencional de EP-3 (Stories 11-13 "wiring real adapters")
  pero quedó sin terminar** — el adapter existe, el surface del engine que consume falta.

### ESC-3 — `STAGE_TOOL_SCOPE` hardcodeado: tool names nuevos no surfacean
- **Muro:** `core/.../application/tools/registry.py:56-110` — dict de engine; `get_tools_for_stage` filtra
  estricto `ALWAYS_AVAILABLE | STAGE_TOOL_SCOPE[stage]`. Los nombres `book_appointment`/`match_service_and_specialist`/
  `share_doctor_profile` no están en ningún stage → el LLM nunca los ve.
- **Por qué bloquea:** aunque ESC-2 se resuelva, un tool de marca con nombre nuevo no aparece en el toolset
  del especialista sin estar en algún `STAGE_TOOL_SCOPE`.
- **Cambio mínimo (lift):** que la registración EP-3 acepte un `stage_scope` y `get_tools_for_stage` mergee
  los stage-scopes de extensión. ~15 LOC + arch test. (Acoplado a ESC-2.)
- **Por qué NO brand-local:** mismo motivo — el gating vive en engine.

### Mitigación parcial sin lift (lo que el architect SÍ puede salvar hoy)
- **Reusar nombres de engine que YA están en scope:** el match/doctor/slots se puede expresar **sin tools
  nuevos** apoyándose en los tools de engine ya scoped: `get_available_slots` (discovery/presentation/closing)
  consume `VitaliaSchedulerProvider` → resuelve slots reales **una vez ESC-1 esté hecho**; `create_booking_link`
  (presentation/closing) crea el hold; `send_payment_link` (closing) la seña; `recommend_product`
  (ALWAYS_AVAILABLE) + el `agent_identity` (slot 4 vía `TenantKnowledgeBuilder`, que lee Offer+team) cubre
  parte del "recomendar". **Pero el MATCH al doctor clínico (no oferta) y el share_doctor_profile (URL pública)
  no tienen tool de engine equivalente** → siguen necesitando ESC-2/ESC-3. Y `get_available_slots`/
  `create_booking_link` siguen necesitando ESC-1 para tocar el lane vitalia.
- **Net:** ESC-1 es el muro inescapable (sin él, ni siquiera los tools de engine tocan el lane vivo de
  vitalia). ESC-2+ESC-3 son el muro de los tools nuevos (match/share). **Los tres deben ir a `/pm-luana`
  juntos** como un lift cohesivo "abrir el engine sales_agent a scheduler+tools+stage per-brand".

### Lo que NO está bloqueado (buildable brand-local hoy — ready package abajo)
- Receiver webhook Telegram + adapter de marca + ruta FastAPI (reemplaza stubs) → consume el `handle_telegram_webhook`
  YA wired del engine. **Cero engine.**
- Honor-modo bridge (decide/consulta/pausa) sobre el `handler_mode` + `proposal_required` + `pause_until` del
  inbox shipped. **Cero engine.**
- Endpoint set-instruction (operator instruction) sobre `override_context_wire` shipped. **Cero engine.**
- Plomería scheduling: marcar `availability_slot.has_confirmed_appointment` en `create_appointment_service` +
  status hold-pendiente-pago + TTL/sweep job + param config Adrián per-tenant. **Cero engine** (todo en
  `vitalia/.../scheduling/` + `clinics/`).
- FE composer modo-instrucción. **Cero engine.**

> **Recomendación de secuenciamiento al PM:** mergear el lift `/pm-luana` (ESC-1/2/3) ANTES del BUILD de los
> tickets agentic T-AG-* (book/match/share). Los tickets BE/FE (canal, scheduling, composer) NO dependen del
> lift y pueden arrancar ya. El ready package marca esa frontera en el DAG (§ 06-tickets).

---

## § Integration design (CONN — anti-isla · nada llega a `done` como isla)

### Reachability path (Telegram → grafo → outbound + agenda Mateo)

```
Paciente (Telegram) → setWebhook(secret_token) del bot per-tenant
  → POST /api/v1/connections/telegram/webhook (NEW route, vitalia)  [valida X-Telegram-Bot-Api-Secret-Token]
  → resuelve tenant dueño del bot (per-tenant token en connections)
  → orchestrator.handle_telegram_webhook(payload, bg, tenant_id, db)  [engine VIVO — consume]
     → normalize → buffer → smart_debounce → grafo sales_agent
        → honor-modo BRIDGE (decide=corre+envía · consulta=corre+borrador · pausa=skip)
        → [una vez lift ESC-1/2/3] match→slots→book_appointment → VitaliaSchedulerProvider
             → scheduling/create_appointment_service(origin=proactivo_adrian)
                → marca availability_slot.has_confirmed_appointment=True
                → APARECE en la agenda de Mateo (cap scheduling.mateo-agenda, badge origin)
             → append scheduled_meetings(status=hold, appointment_id)
        → send_payment_link (seña) → ComplianceService.validate_outbound_message → format_for_channel(telegram)
  → outbound por adapter Telegram (decide) | banner propuesta inbox (consulta) | silencio (pausa)
  → activity event sanitizado → inbox glass-box (cap adrian-inbox)
```

### Consumers (≥1 real por superficie)
- Telegram webhook route → consumido por **Telegram (setWebhook)** + el orchestrator engine.
- `book_appointment`/`VitaliaSchedulerProvider` → consumido por **el grafo** (tool_executor) + **la agenda de
  Mateo** lee el appointment creado (origin badge).
- Honor-modo bridge → consumido por **el inbox** (set_mode_service shipped fija el modo; el bridge lo lee).
- Set-instruction endpoint → consumido por **el composer FE** (modo-instrucción) → el supervisor lo honra.
- Sweep hold-TTL → consumido por **el lead** (slot liberado re-ofrecido) + **activity stream**.

### Registration points (dónde el runtime lo descubre)
- **setWebhook** del bot per-tenant (config connections) → Telegram entrega al route.
- **`include_router`** de la ruta Telegram en `vitalia/backend/src/main.py` (FastAPI app).
- **`register_scheduler_provider(VitaliaSchedulerProvider)`** en `extensions.py::register_all` (+ requiere
  ESC-1 para routing).
- **EP-3 `sales_agent_tool_register`** de los 3 tools nuevos en `extensions.py` (+ requiere ESC-2/ESC-3).
- **Nav/cap:** home cap `adrian.inbox` (+ derived `adrian.canal-inbound`); el loop activa la caja en vivo.

### Home cap
- `adrian.inbox` (cap_target) + posible derived `sales_agent.adrian-canal-inbound` (área `adrian.inbox`).

---

## § 1 · Domain Entities / state (EXTEND brand overlay — GAP-5 workaround)

> El `AgentState` del engine es un TypedDict cerrado (no extensible). Las keys de booking NO van como
> top-level state (eso sería editar engine). Van en el **overlay brand `VitaliaSalesAgentStateExtension`**
> (ya existe, total=False) + se transportan por `lead_data`/`metadata_info` JSONB en el checkpoint. El
> `scheduled_meetings` del engine se REUSA (referencia el appointment); `doctor_id`/`service_id` que el
> `MeetingEntry` frozen no tiene → van en el overlay/`metadata_info`, NO se extiende `MeetingEntry` (eso sería
> engine, GAP-4).

```python
# vitalia/.../sales_agent/domain/state_overlay.py — EXTEND VitaliaSalesAgentStateExtension (TypedDict total=False)
# EXISTENTES (no tocar): clinic_id, vertical, screening_outcome, medical_disclaimer_shown,
#                        phi_blocked_messages, compliance_level
# NEW (booking — opcionales):
recommended_doctor_id: UUID | None          # match_service_and_specialist → doctor recomendado
recommended_service_offer_id: UUID | None    # offer matcheado (para el book + payment)
candidate_slots: list[dict[str, Any]] | None # get_available_slots cacheado para el mapeo por razonamiento
doctor_profile_shared_at: datetime | None    # share_doctor_profile (audit/glass-box)
# el hold/booking VIVE en el engine scheduled_meetings (referencia, NO duplicar)
```

**Tenant isolation:** `clinic_id` (dual-filter con `tenant_id`) ya está en el overlay y es mandatorio antes
del primer LLM call (lo popula el adapter inbound). Toda query de booking/slots filtra `tenant_id + clinic_id`.

---

## § 2 · SQLAlchemy 2.0 Models (BE — scheduling plomería, EXTEND)

> No hay tabla nueva del lado agentic (el estado vive en JSONB del checkpoint engine + overlay). Lo único en
> SQLA es el **status hold + TTL** sobre el appointment del lane vivo. Decisión: NO columna nueva en la tabla
> engine `appointments` (eso es engine). El hold-status + expiry viven en el **brand-local
> `vitalia_appointment_clinic_map`** (ya existe, brand-local) → agregar columnas idempotentes.

```python
# vitalia/.../scheduling/persistence/models/appointment_clinic_map_model.py — EXTEND (brand-local)
# NEW columns (idempotent migration raw SQL):
hold_status: Mapped[str | None] = mapped_column(String(24), nullable=True)        # None|hold_pending_payment|confirmed|expired
hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # UTC
hold_created_by_agent: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
# Index para el sweep:
# ix_clinic_map_hold_expiry  ON (tenant_id, hold_status, hold_expires_at)  WHERE hold_status='hold_pending_payment'
```

`availability_slots.has_confirmed_appointment` (existe en `clinics`) se setea `True` al crear el turno.
`DateTime(timezone=True)` siempre; store UTC; display via tenant locale.

---

## § 3 · Pydantic v2 DTOs

```python
# vitalia/.../connections/telegram/api/dtos.py
class TelegramWebhookAck(BaseModel):                  # response_model del webhook
    model_config = ConfigDict(from_attributes=True)
    ok: bool

# vitalia/.../sales_agent/api/dtos.py  (set-instruction)
class SetOperatorInstructionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    conversation_id: UUID
    instruction: str                                   # texto comercial, sanitizado (NON-PHI)

class SetOperatorInstructionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    conversation_id: UUID
    instruction_active: bool
    updated_at: datetime
```

No `Any` en superficie pública. El payload Telegram crudo es `dict` interno (normalizado por el adapter), no DTO.

---

## § 4 · API Routes

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/connections/telegram/webhook` | secret_token header (NO Bearer — es Telegram) | raw Telegram update (dict) | `TelegramWebhookAck` | Receiver inbound: valida `X-Telegram-Bot-Api-Secret-Token` + `update_id` idempotente → `orchestrator.handle_telegram_webhook`. Reemplaza stubs `webhook_routes.py`. |
| POST | `/api/v1/adrian/conversations/{conversation_id}/instruction` | Bearer + X-Tenant-ID | `SetOperatorInstructionRequest` | `SetOperatorInstructionResponse` | Set/clear operator instruction (override_context_wire). Solo en `decide`. |

- `FastAPI(redirect_slashes=False)` (ya enforced).
- El webhook **NO** lleva Bearer/X-Tenant-ID (Telegram no los manda); su auth = el `secret_token` + la
  resolución del tenant por bot. El set-instruction SÍ (Bearer + X-Tenant-ID).
- **Idempotencia (RN-9):** dedup por `update_id` (Telegram reentrega). Tabla/set de dedup brand-local con TTL.

---

## § 5 · TypeScript Types (Frontend — composer instrucción)

```typescript
// vitalia/frontend/src/features/adrian/types/operator-instruction.ts
export interface SetOperatorInstructionRequest {
  conversationId: string;   // UUID
  instruction: string;      // NON-PHI, comercial
}
export interface SetOperatorInstructionResponse {
  conversationId: string;
  instructionActive: boolean;
  updatedAt: string;        // ISO 8601
}
// effectiveMode pattern (reusa MessageInput legacy):
export type ComposerMode = 'instruction' | 'direct';
// handlerMode==='human' (pausado) → 'direct' (mensaje al lead) · else (decide) → 'instruction'
```

camelCase FE ↔ snake_case BE; datetimes ISO string.

---

## § 6 · Repository Interfaces (async, tenant+clinic scoped)

```python
# vitalia/.../scheduling/application/ports/  (EXTEND existing scheduling repo port)
class SchedulingHoldPort(ABC):
    @abstractmethod
    async def mark_slot_confirmed(self, *, tenant_id: UUID, clinic_id: UUID, slot_id: UUID, confirmed: bool) -> None: ...
    @abstractmethod
    async def set_hold(self, *, tenant_id: UUID, clinic_id: UUID, appointment_id: UUID,
                       status: str, expires_at: datetime) -> None: ...
    @abstractmethod
    async def list_expired_holds(self, *, tenant_id: UUID, now: datetime) -> list[UUID]: ...   # para el sweep
```

Toda firma recibe `tenant_id` + `clinic_id` (dual-filter PHI). `get_available_slots` (lectura de slots libres)
filtra `has_confirmed_appointment=False` + doctores del servicio matcheado.

---

## § 7 · Application Services

- **`TelegramInboundService`** (BE): valida secret + idempotencia `update_id` → delega a engine orchestrator.
  NO reimplementa normalize/debounce (engine).
- **`HonorModeBridge`** (BE/agentic frontier): lee `handler_mode`+`proposal_required`+`pause_until` (inbox
  shipped) → mapea a comportamiento (decide=envía · consulta=borrador no-send · pausa=skip). Es el punto donde
  el resultado del grafo se entrega o se retiene.
- **`SchedulingHoldService`** (BE): al crear turno proactivo_adrian → `mark_slot_confirmed(True)` +
  `set_hold(hold_pending_payment, now+TTL)`. TTL = `tenant_config.adrian_hold_ttl_minutes` (default 30).
  Audit sync + growth event.
- **`HoldExpirySweepService`** (BE worker): job periódico → `list_expired_holds` → cancela turno + libera slot
  (`mark_slot_confirmed(False)`) + emite activity al inbox. **Idempotente.** Coordina con
  `verify_pending_bookings` del engine (no duplicar la reconciliación; el sweep brand cubre el lado del lane
  vivo que el engine no ve).
- **`OperatorInstructionService`** (agentic): reusa `override_context_wire.set_override_context` →
  `metadata_info[operator_instructions]` (o el `override_context` existente) + audit row + activity NON-PHI.
- **Tools agentic (BLOQUEADOS por ESC-2/3 hasta lift):** `VitaliaSchedulerProvider`,
  `match_service_and_specialist`, `share_doctor_profile`, `book_appointment` (tool fina → provider).

**Transaction boundaries:** el create del turno + slot-marking + hold = una transacción (anti doble-booking).
Advisory-lock / unique constraint sobre `(doctor_id, slot)` → el segundo create recibe 409 (RN-22). El audit
es sync pre-response (hipaa-lite). Idempotencia del book por natural key `(patient, doctor, slot)`.

---

## § 8 · Agentic Surfaces

> Owner: `builder-agentic` (flagship). Auditor: `auditor-agentic` (flagship). **Patrones SOTA as of
> 2026-06-21.** Detalle completo: `03-arch-agentic.md`. **★ Estas superficies dependen del lift `/pm-luana`
> (ESC-1/2/3) para los tools NUEVOS.** Lo brand-local agentic SIN lift = el overlay de estado + persona/playbook
> tuning + eval goldens + operator-instruction wiring.

- **LangGraph state:** REUSE `AgentState` (engine) + overlay brand (§1). `tenant_id`+`clinic_id` mandatorios.
- **Topology:** REUSE supervisor StateGraph del engine (qualifier/product_expert/closer + signal_accumulator +
  tool_executor + escalation). NO rediseñar.
- **Tools:** REUSE engine (`get_available_slots`/`create_booking_link`/`send_payment_link`/`verify_booking_status`/
  `escalate_to_human`/`recommend_product`) + brand vivos (`screening_questions`/`reschedule_appointment` —
  **nota: hoy no dispatchan, ESC-2**) + NEW (`book_appointment`/`match_service_and_specialist`/
  `share_doctor_profile` — **BLOQUEADOS ESC-2/3**). Selección de slot = razonamiento (bar no-`if`s).
- **Prompt cache slots:** REUSE `compose.py` (slots 1-5 cacheable, 6-9 volátiles). **★ SOTA 2026-06-21: el
  default TTL de Anthropic bajó a 5min (marzo 2026); los slots 1h deben declarar `"ttl": "1h"` explícito.**
  Operator instruction = SLOT volátil (post cache-boundary), nunca cacheable. Forbidden en prefix: timestamps,
  conversation_id, chat_id, turn_counter, texto de instrucción, candidate_slots.
- **Checkpointer:** REUSE engine (AsyncPostgresSaver / `agent_state_checkpoints` — el engine ya lo maneja).
- **Observability:** REUSE `SalesAgentCallbackHandler` (subclasea base engine) → `sanitize_payload(compliance_level="hipaa_lite")`
  en CADA write. Cost target: ≥60% cache_read + presupuesto SA pool (BudgetGuard).
- **Eval goldens:** ver `03-arch-agentic.md` § goldens (honor-mode, screening-gate, book-happy, book-no-isla,
  book-consulta, book-race, hold-expira, objection-trust, ethical no-dark-patterns).
- **Dedup reschedule (decisión architect):** existen `reschedule_appointment` (brand, hoy no dispatcha) +
  `appointment_reschedule_with_doctor` (agentic, EP-3 `_not_implemented_yet`). **Decisión: cablear el rico
  `propose_and_book`/`list_slots` de `agentic/tools/appointment_reschedule_with_doctor.py` como base del
  `book_appointment` (tiene cuerpo + schema), DEPRECAR el path duplicado.** NO dejar dos rutas vivas. (Requiere
  lift ESC-2 igual.)

---

## § 9 · Migration Notes

```sql
-- vitalia/.../scheduling — idempotent raw SQL (backend-migrations.md)
ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS hold_status VARCHAR(24);
ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS hold_expires_at TIMESTAMPTZ;
ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS hold_created_by_agent BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_clinic_map_hold_expiry
  ON vitalia_appointment_clinic_map (tenant_id, hold_status, hold_expires_at)
  WHERE hold_status = 'hold_pending_payment';
-- Telegram update_id dedup (idempotencia RN-9):
CREATE TABLE IF NOT EXISTS vitalia_telegram_update_dedup (
  tenant_id UUID NOT NULL, update_id BIGINT NOT NULL, seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, update_id));
```

Test pre-prod: clone DB workflow (backend-migrations.md). `tenant_config.adrian_hold_ttl_minutes` = config
JSONB, sin migración. NUNCA `sa.Enum(create_type=True)` / `op.create_table()`.

---

## § 9.5 · Tests audit (default flip) — **No aplica**
- [x] No aplica — 03-arch.md NO flipea defaults side-effect. (No se toca `USE_OUTBOX_PATTERN_*` ni provider
  routing por flag. El honor-modo bridge es comportamiento per-conversación, no un default flag global.)

---

## § 10 · File Structure (NEW vs MODIFIED)

```
# AGENTIC (builder-agentic) — ⚠️ tools nuevos BLOQUEADOS ESC-2/3
vitalia/backend/src/modules/vitalia/sales_agent/
  domain/state_overlay.py                         MODIFIED (+ booking keys)
  tools/match_service_and_specialist.py           NEW  ⚠️ requiere lift ESC-2/3
  tools/share_doctor_profile.py                   NEW  ⚠️ requiere lift ESC-2/3
  tools/book_appointment.py                        NEW  ⚠️ requiere lift ESC-2/3
  infrastructure/scheduler/vitalia_scheduler_provider.py  NEW  ⚠️ requiere lift ESC-1
  application/services/operator_instruction_service.py    NEW (reusa override_context_wire) — buildable
  prompts/ (tuning persona descubrimiento)         MODIFIED — buildable (cero engine)
  personas/warm_close_*.yaml                        MODIFIED (tune) — buildable
  goldens/                                           NEW — buildable
# BE (builder-backend) — buildable hoy
vitalia/backend/src/modules/vitalia/connections/telegram/
  adapter.py                                        NEW (implementa BaseChannel)
  api/router.py                                     NEW (webhook route + secret validation + dedup)
  api/dtos.py                                        NEW
vitalia/backend/src/modules/vitalia/api/webhook_routes.py   MODIFIED (replace T-be-8 stubs → real dispatch)
vitalia/backend/src/modules/vitalia/scheduling/
  application/services/create_appointment_service.py  MODIFIED (mark slot + hold status)
  application/services/scheduling_hold_service.py      NEW
  application/services/hold_expiry_sweep_service.py     NEW (worker)
  application/ports/scheduling_hold_port.py            NEW
  persistence/models/appointment_clinic_map_model.py   MODIFIED (+ hold columns)
  persistence/migrations/                              NEW (idempotent)
vitalia/backend/src/main.py                          MODIFIED (include_router telegram)
vitalia/backend/src/modules/vitalia/extensions.py    MODIFIED (register_scheduler_provider + EP-3 — ⚠️ lift-gated)
# FE (builder-frontend) — buildable hoy
vitalia/frontend/src/features/adrian/
  components/inbox/composer/ (instruction mode)      MODIFIED (EXTEND MessageInput effectiveMode)
  api/operator-instruction.ts                         NEW
  hooks/use-operator-instruction.ts                   NEW
  types/operator-instruction.ts                        NEW
# ENGINE — ⚠️ NO EDITAR (lift /pm-luana): providers.py, registry.py, agents/sales/tools.py
```

---

## § 11 · Cross-Cutting Concerns

- **Tenant isolation + clinic dual-filter (HIPAA-lite):** toda query booking/slots/conversación filtra
  `tenant_id + clinic_id`. El `clinic_id` se popula en el overlay ANTES del primer LLM call (adapter inbound).
  Arch test `test_phi_dual_filter.py`.
- **PHI firewall:** `ComplianceService.validate_outbound_message` en cada outbound Telegram (canal no-encriptado);
  PHI → deriva a portal. `sanitize_payload(compliance_level="hipaa_lite")` en cada write a trace/activity.
  Telegram NUNCA en `localStorage`; instrucción del operador = NON-PHI comercial.
- **Currency:** la seña (`send_payment_link`) lleva la moneda del servicio (offer) — NUNCA hardcode `'USD'`;
  `currency_override` ya existe en clinic_map.
- **Master data:** `DateTime(timezone=True)` UTC store; TTL del hold en UTC; display tenant locale.
- **Spanish neutro:** UI strings + schemas neutro; **output del agente Adrián respeta la voz del tenant**
  (sales_agent = voseo OK si tenant AR; `personality_profiles`).
- **Native-first:** lint/tests host (`${WS}/.venv/bin/{ruff,pytest}`, `npx tsc/vitest/playwright`). NUNCA docker exec.
- **Audit:** audit_log sync write pre-response en booking + set-instruction + PHI block (hipaa-lite).

---

## § 12 · Architecture Fitness Impact

- Gates que corren (gate-runner): `test_phi_dual_filter`, `test_audit_log_sync_write`,
  `test_response_model_required`, `test_growth_studio_event_no_phi`, DDD boundaries, anti-mirror cross-brand,
  `test_no_phi_in_url_params` (FE). Engine arch tests (`core/.../tests/architecture/`) deben seguir verdes
  **sin tocarse** (read-only).
- **Allowlist:** ninguna nueva. La regla de no editar engine se enforza por boundary (los tickets agentic
  T-AG-* quedan `BLOCKED` hasta el lift; no se commitea edición de `core/`).
- **NEW arch test recomendado (post-lift, en engine, por `/pm-luana`):** `test_extension_tool_dispatchable.py`
  + `test_scheduler_provider_per_tenant.py` (cierran ESC-1/2/3 con dientes).

---

## § 13 · capability YAML + modules updates (post-merge)

- **Crear cap derivada** `sales_agent.adrian-canal-inbound` vía `make new-cap BRAND=vitalia MODULE=sales_agent
  SLUG=adrian-canal-inbound AREA=adrian.inbox` (gate 5b la exige si new-cap; el loop inbound = trigger del
  runtime, caja propia). Poblar scenarios SC-1..SC-12 + access + business_rules v3.2.
- **EXTEND** `inbox/adrian-inbox.yaml`: scenario "loop inbound activa la caja" + honor-modo + instrucción operador.
- `vitalia/docs/product/modules/sales_agent.md` (si existe narrativa) — agregar el loop + el book proactivo.
- Header `# cap: sales_agent.adrian-canal-inbound` en archivos nuevos (líneas 1-3).

---

## § 14 · Test Surfaces (TDD RED-first) — Test Construction Plan

- **BE (DDD layers):** domain (hold status VO) → infrastructure (clinic_map columns + dedup repo) →
  application (`SchedulingHoldService`, `HoldExpirySweepService`, `TelegramInboundService`, `HonorModeBridge`) →
  API/E2E (webhook security `test_telegram_webhook_security.py` SC-5 + tenant isolation
  `test_telegram_tenant_isolation.py` SC-6 + hold expiry `test_hold_expiry_sweep.py` SC-10).
- **FE (Vitest):** hook `use-operator-instruction` → composer effectiveMode component (SC-8) → store.
- **E2E (Playwright):** smoke del composer instrucción (no nueva ruta — extiende inbox).
- **Agentic (eval goldens — post-lift):** honor-mode (decide/consulta/pausa), screening-gate (DERIVAR_EMERGENCIA
  → NO bookea), book-happy (slot por razonamiento), book-no-isla (agenda Mateo + slot marcado), book-consulta,
  book-race (409 → re-propone), hold-expira, objection-trust (share_doctor_profile), ethical (no dark patterns).
  `trials_per_scenario: 3, per_trial_pass_threshold: 0.66, pass_k_threshold: 0.5`.
- **Regression (regression_guard):** la suite del inbox shipped corre verde SIN tocarse (modos/pausa/send/nudge/
  activity/PHI/tenant/deep-link). EXCEPCIÓN coordinada: composer en `decide` se EXTIENDE (RN-14/15) — cambio
  intencional sobre superficie firmada.
- **Live-verify (DoD #37, funcional):** enviar mensaje real por Telegram (bot dev, tenant ≠ Chris) → leer
  reply + logs BE + filas DB (conversación, scheduling_appointment origin=proactivo_adrian, availability_slot
  marcado, trace, costo). CERO "GET 200".

---

## § 15 · Research Notes (date-aware — accessed 2026-06-21)

- **LangGraph supervisor production pattern** — `https://docs.langchain.com/oss/python/langgraph/workflows-agents`
  + WebSearch (lifetideshub/eastondev/gheware) accessed 2026-06-21. Takeaway: supervisor StateGraph + worker
  nodes con tools scoped = el patrón del engine sales_agent (validado). `create_supervisor` (high-level) vs
  StateGraph (low-level) — el engine usa StateGraph. **Por qué este patrón:** ya está construido + en prod
  (Uber/Klarna/LinkedIn usan LangGraph). Topic mostly pre-cutoff; verificado live.
- **Anthropic prompt caching TTL** — `https://platform.claude.com/docs/en/build-with-claude/prompt-caching`
  accessed 2026-06-21. **★ Crítico (post mi cutoff de ene-2026 — researched live):** el default TTL bajó de
  1h a 5min el 6-mar-2026. Los slots cacheables 1h del engine (slots 1-5 en `compose.py`) **deben declarar
  `"cache_control": {"type": "ephemeral", "ttl": "1h"}` explícito** o degradan a 5min → cache miss en
  conversaciones de venta largas (>5min entre turnos). 1h fue diseñado exactamente para multi-agent/sales.
  Hasta 4 breakpoints; ponerlos al final de bloques estáticos. **Por qué importa acá:** una conversación de
  agendamiento dental tiene gaps de minutos entre turnos → el 1h explícito sostiene el ≥60% cache-read target.
  **Acción para el architect del engine (no esta story):** verificar que `compose.py` declare `ttl:1h` en el
  cache marker; si no, es un item de tuning del engine (`/pm-luana`, no brand).
- **LangGraph version pin** — engine pinea `langgraph>=0.2` (`pyproject.toml:11`). Viejo pero estable; **NO
  bumpear desde esta story** (engine = `/pm-luana`). Verificado contra el pin real.

---

## § 16 · Open Questions for PM

1. **★ DECISIÓN MAYOR (Chris/`/pm-luana`):** ¿se aprueba el lift `/pm-luana` ESC-1/2/3 (abrir scheduler
   per-tenant + extension-tool merge + stage-scope per-brand en `core/luana-core-sales-agent`) ANTES del BUILD
   agentic? **Sin él, los tools `book_appointment`/`match`/`share` NO se pueden cablear sin editar engine.** Mi
   recomendación: SÍ — es un lift cohesivo (~80 LOC + 2 arch tests) que beneficia toda brand con sales_agent
   propio, y completa el wiring EP-3 que quedó a medias (Stories 11-13 "wiring real adapters" nunca terminó).
   El gate `/pm-luana` puede correr en paralelo al BUILD de los tickets BE/FE (que NO lo necesitan).
2. **cap derivada:** ¿OK crear `sales_agent.adrian-canal-inbound` (derived) o mantenemos todo en `adrian.inbox`?
   Recomiendo derivada (el loop es caja propia en el cockpit).
3. **`tuning.py` (umbrales stage/fatiga/score) es engine.** Si querés tunear para contexto médico (cerrar a
   score más bajo, fatiga a 2 preguntas), ¿per-tenant config (brand-local) o lift `/pm-luana`? Recomiendo
   per-tenant config (no editar engine).
4. **Slot-marking gap (RN-26):** ¿cerramos el marcado de `availability_slot` acá (canal-inbound lo necesita
   sí o sí) o vive en `vitalia-scheduling-mateo-review`? Recomiendo cerrarlo acá + que mateo-review lo verifique.
5. **Deps duras `state: done`:** `lisa-servicios` + `adrian-inbox` confirmados archivados (= done). `lisa-doctores`
   también done. El BUILD agentic igual espera el lift ESC-1/2/3.
