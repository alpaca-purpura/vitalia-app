---
story_id: vitalia-fase2-adrian-canal-inbound
type: agentic-story
agent_owner: adrian
map_zone: agentes
map_box: adrian
module: sales_agent           # heart = trigger del runtime; cross-module connections (receivers) + inbox (feed)
capability: adrian.inbox      # EXTIENDE la cap del inbox (loop inbound la activa)
state: developing         # 2026-06-22: OLA-2 build RESUME tras audit (Chris eligió dir A). OLA-1 firmada (chris_verify.signoff persiste); la story mergea post-OLA-2 (slice_decision). PREV: developed/AWAIT_CHRIS_VERIFY (OLA-1 carril cero-engine T-BE-1/2/3+T-AG-1+T-FE-1 GREEN)
phase: OLA2_BUILT_AWAIT_CHRIS_G   # ★ GAP-1 (0fd45f31) + GAP-2/3 lift (5bd0dd1b, engine seams + brand wiring, tests+downstream×4 GREEN, live-verify orchestrator-level) BUILT. PENDIENTE: G de Chris (round-trip Telegram live: consulta→borrador+0-outbound · decide→reply+activity · tools share/match/payment) → R reconcile → /auditor (auditor-agentic, single pass post-OLA-2 per slice_decision) → merge. GAP-4/book + GAP-5/reschedule = dominio scheduling. autonomous_mode:false → NO auto-handoff. ⚠️ commit 9feb302c MISLABELED (race shared-index: contenido mateo T-BE-4 bajo subject de este lift; pushed → no rewrite; flag /pm-vitalia)
architecture_pattern: ADR-vitalia-004
last_modified: 2026-06-22
ratified_by_chris: true   # diseño v3 (02-design-agentic) + spec v6 (01-spec) ratificados Chris 2026-06-21
autonomous_mode: false    # agentic + PHI = stake-asimétrico; gate G (Chris-verify live Telegram) obligatorio
arch_verdict: BLOCKED-PARTIAL   # 03-arch.md § Engine-boundary escalations — ver next_action
engine_lift_phase1: graph-runs-ok__esc17-2.4a-FIXED__OLA2-share+match-LIVE__book-WIRED-blocked-esc19__run_async+esc18-FIXED   # ★ 2026-06-22 (b834b130) — Tier 2.4b: share_doctor_profile (b13c6455) + match_service_and_specialist (dd950beb) DONE+LIVE-VERIFIED. book_appointment WIRED (b834b130) + run_async cross-loop bridge FIXED (set_main_loop + main-loop submission, confirmado empírico) + ESC-18 FIXED (AppointmentModel.lead dead cross-registry relationship removida, engine). book "agenda" runtime BLOQUEADO en ESC-19 (ESCALADO a Chris): scheduling create-lane incompleta (ningún repo implementa create/create_clinic_map, mock-only) + DOS tablas appointment (engine `appointments` 0 rows = lo que el create-service escribe; brand `vitalia_appointments` 88 rows = lo que la grilla Mateo lee → escribir el engine table = isla anti-orphan). Decisión scheduling-domain, fuera de OLA-2. VitaliaSchedulerProvider diferido (Protocol event_slug no encaja doctor+slot). recomienda+comparte = tools REALES vivos (bar tool-exec del end-state CUMPLIDO). PREV:   # ★ 2026-06-22 — 2.4a (b13c6455) + 2.4b parcial: share_doctor_profile (b13c6455) + match_service_and_specialist (dd950beb) DONE+LIVE-VERIFIED (native-sync, real registry + real dev DB → URLs/recomendaciones reales). book_appointment + VitaliaSchedulerProvider SUB-PHASED + ESCALATADO a Chris (HIPAA write; requiere fix del cross-loop async-DB bridge — NullPool bridge engine o main-loop submission; el run_async actual fresh-loop+shared-pool revienta 'Future attached to a different loop' en el 2º async-DB call, confirmado empírico 2026-06-22; + patient/slot resolution + 4 deps del service + idempotencia + 409 race). recomienda+comparte = tools de marca REALES vivos (bar de tool-exec del end-state CUMPLIDO). PREV:   # ★ 2026-06-22 — ESC-17 RESUELTO (Tier 2.4a, b13c6455): brand registra adapters sync (state,db)->dict (structured_tool_adapter wrappea los 9 StructuredTools; share_doctor_profile native-sync = pilot). arch+execution tests GREEN; LIVE-VERIFIED: share_doctor_profile vía el merged registry REAL + DB dev real → URL real dra-ana-garcia-mendoza; screening (era TypeError) → error dict elegante; grafo corre end-to-end. NEXT 2.4b: VitaliaSchedulerProvider + match_service_and_specialist + book_appointment + goldens. Hallazgos: state["_db"] nunca se siembra (None en inbound; adapter hace su propia sesión) + los DI resolvers de los 9 tools nunca se cablearon a lifespan (degradan elegante; cablearlos = 2.4b). PREV:   # ★ 2026-06-22 (/pm-vitalia self-paced lift loop, wip/vitalia, SCOPE_GATE_SKIP in-hub): Tier 1 (ESC-7/8/13/15/16) DONE 44e1d4af — graph runs end-to-end; LIVE-VERIFIED via synthetic Telegram webhook: semantic_check→llm_call→processing_response_chunks (Adrián 4-chunk reply re: blanqueamiento dental), only the EXPECTED synthetic-chat sendMessage 400, zero unexpected traceback. Tier 2 seam DONE: 2.1 prompt advertises brand tools e43015ee · 2.2 scheduler per-tenant 3aff15af · 2.3 orphans 833fece3. ★ NEW BLOCKER ESC-17 (fe481dac): the EP-3 tool handler ABI is broken — engine dispatches tool_fn(state, db=...) (sync) but all 9 "real" vitalia handlers are async LangChain StructuredTools → screening_questions(state, db=None) raises TypeError 'StructuredTool' not callable → every brand tool errors on dispatch, never executes. So the CONVERSATIONAL round-trip works, but Adrián cannot yet USE a real brand tool (recommend/book/share). The "13 tools dispatchable" of 846388a6 was registry-presence, not ABI-callability (arch-green≠runtime, embudo). Fix = sub-phase 2.4a (brand sync (state,db)->dict adapters), builder-agentic flagship. Phase 2 / OLA-2 (book/match/share) gated behind 2.4a. SSoT: docs/architecture/luana-platform/sales-agent-multibrand-hexagonal-lift.md § ESC-17 + docs/learnings/2026-06-22-ep3-tool-handler-abi-mismatch.md.
reconciled: true          # ★ R done 2026-06-22 (/pm-vitalia self-paced loop): cap taxonomy confirmada (vitalia.sales_agent.honor-mode-bridge · agent_owner:adrian · functional_area:adrian.inbox · module:sales_agent OK) + 04-validators OLA-2 deferred tags refrescados (ESC-1/2/3 done → blocker real ESC-17). SLICE DECISION: OLA-1 queda en `developed`; auditor único POST-OLA-2 (no audit independiente de slice-1) — razón: (1) OLA-1+OLA-2 = misma story/módulo code:sales_agent → un solo audit final antes de done (story-closure-gate); (2) ESC-17 bloquea tool live-verify → audit OLA-1-only rebota determinista en LIVE_VERIFY_MISSING de los SC de tool; (3) los 64 commits de wip/vitalia están mezclados (shell DS + otros) → no hay slice-1→main limpio independiente. El merge a `done` es post-OLA-2 con auditor sobre la story completa.
reconcile_2026-06-22:
  reconciled_by: /pm-vitalia
  cap_taxonomy_confirmed: vitalia.sales_agent.honor-mode-bridge
  validators_deferred_refreshed: "V-FN-8/9/11/12 + V-ARCH-5 + goldens book-* → deferred reason ESC-17/Tier-2.4a (ESC-1/2/3 ya done)"
  slice_decision: "OLA-1 stays developed; single auditor pass after OLA-2 (rationale in `reconciled` note above)"
chris_verify:
  required: true
  signoff:                # ★ Chris firmó OLA-1 (carril texto inbound) — 2026-06-22
    by: Chris
    date: 2026-06-22
    result: SATISFIED_WITH_FOLLOWUPS   # OLA-1 texto satisfecho; el followup (OLA-2 tools) es un SLICE SEPARADO, no un defecto de OLA-1
    scope: OLA-1 (carril texto inbound — honor-mode · screening-gate · objection-trust · operator-instruction)
    basis: "grafo live-verified (webhook → Adrián responde, reply generado) + ratificación explícita de Chris ('Firmo'). El round-trip de TEXTO por @nicolify_dev_bot está operativo (tunnel 200, semantic_check→llm_call→processing_response_chunks)."
    notes: "NO cubre el demo de un tool de marca real — eso está gated por ESC-17/Tier 2.4a (ABI handler roto). El signoff es del carril texto OLA-1, que es funcional e independiente."
    open_items:
      - "ESC-17 / Tier 2.4a: ningún tool de marca ejecuta (ABI handler EP-3 roto) — sub-fase siguiente, builder-agentic flagship"
      - "OLA-2 (match/share/book) = slice 2, depende de 2.4a"
  rounds: []
dod_live_verified: partial   # agentic core (5 goldens) live vs Postgres real; loop Telegram round-trip = tu verify en G (needs bot dev + tunnel)
dod_evidence:
  - action: "5 goldens agentic ejercidos contra el grafo + Postgres real (T-AG-1)"
    observed: "honor-mode (decide/consulta/pausa) · screening-gate DERIVAR_EMERGENCIA → no bookea+escala · objection-trust → bio sin overpromise · ethical no-dark-patterns · operator-instruction steerea el siguiente turno (SC-8)"
    backend_log: "5/5 goldens GREEN, pass^k OK; sin PHI en trazas; tenant-scoped"
  - action: "set-instruction endpoint + honor-mode bridge ejercidos (integración) (T-BE-3)"
    observed: "instrucción persiste metadata_info + bridge resume_objective (HB-92 gap cerrado) · audit row · 0 outbound al lead"
    backend_log: "24/24 tests GREEN + audit_sync/response_model arch PASS"
pending_chris_G:
  - "loop Telegram round-trip real (SC-1): mensaje real → reply Adrián + fila conversación + trace + costo (needs bot dev nicolify_dev_bot + tunnel)"
  - "scheduling sweep/slot-marking live (SC-10) contra Postgres dev con migración 047/048 aplicada"
chris_decision_2026-06-21: "OLA 1 build-local-ya + OLA 2 lift-en-paralelo (ratificado Chris vía /architect). /dev-team builda carril cero-engine T-BE-1/2/3+T-AG-1+T-FE-1 → G → auditor → merge slice 1. T-LIFT-1 (ESC-1/2/3) → /pm-luana en worktree core efímero (lane paralela). T-AG-2/3/4/5 esperan el lift → slice 2."
channel_scope: telegram-first   # Chris 2026-06-04 — WhatsApp/IG = follow-up (sin API hoy)
gateway_improvement: out-of-scope   # mejora del LLM gateway = item /pm-luana aparte (toca engine)
parallel_safe: true
priority: high
estimated_dev_days: 4-6
dependencies:
  hard:
    - vitalia-fase2-adrian-inbox             # superficie + modo por-conversación que este loop respeta y nutre
    - vitalia-fase2-lisa-servicios           # ★ Chris 2026-06-05: el match servicio→especialista necesita el catálogo (Offer Studio) + link servicio↔doctor. Secuenciar PRIMERO.
  soft:
    - vitalia-fase2-adrian-embudo            # persistencia conversación + tablero leads
    - vitalia-fase2-lisa-doctores            # roster clínico (bio/specialty/disponibilidad) que el match presenta
blocks_hard: []
blocks_soft:
  - vitalia-fase2-adrian-outbound            # respuestas a outbound vuelven por este mismo loop
  - vitalia-fase2-camila-reactivar           # reactivación cierra el ciclo en el inbox
reuse_map_summary: >-
  CONSUME engine core/luana-core-sales-agent (runtime LangGraph: orchestrator/chat.py + graph.py +
  smart_debounce_runner.py — read-only, NUNCA recrear) · CONSUME extensión vitalia/.../sales_agent/
  (tools + 5 personas voz + prompts + state_overlay shipped) · CONSUME core/luana-core-channels
  (format_for_channel + intent_detector) + core/luana-core-compliance (firewall PHI outbound) ·
  REUSE adapters connections whatsapp/instagram (hoy solo OUTBOUND) — agregar INBOUND receiver ·
  NEW Telegram adapter (no existe) · EXTIEND inbox: el loop nutre activity stream + respeta modo
spawned_at: 2026-06-04
next_action: "★ AUDITORÍA PROFUNDA 2026-06-22 → RECONCILE-2026-06-22-doc-vs-reality.md (SSoT del estado real). autonomous-dispatch RESUELTO+promovido; R ya done (reconciled:true). VER known_gaps_2026-06-22. DECISIÓN CHRIS pendiente: (A) construir OLA-2 — cablear 6 DI resolvers (buildable ya, cero engine, alto valor) + /architect para consulta-mode (GAP-2) + activity-feed (GAP-3) → /dev-team; (B) mergear slice OLA-1 + parkear book (ESC-19/GAP-4 = decisión dominio scheduling). OJO: V-FN-1/V-FN-2 son must_pass con gap de cableado live (activity + consulta) → NO pasan /auditor hasta GAP-2/3. [GUÍA PREVIA, parcialmente ejecutada]: corré R (reconcile: reconciled:true + confirmá taxonomía de la cap sales_agent.honor-mode-bridge + marcá must_pass:false los validators de scope OLA-2 deferido) → AUTO-HANDOFF /auditor sobre el slice OLA-1 → si APPROVED, merge slice-1 (la story NO va a `done` global hasta OLA-2; respetá story-closure-gate + WIP cap). EN PARALELO, lift sales_agent (sub-fases): Tier 2.4a (ESC-17 ABI fix) → 2.4b (match/share/book) → governance → promote+sync. G parcialmente destrabado (2026-06-22 lift loop). El grafo CORRE y Adrián responde conversacionalmente (live-verified, synthetic webhook) → el round-trip Telegram de TEXTO ya es ejercible por Chris (demo-script.md) para firmar chris_verify.signoff sobre el carril OLA-1 (honor-mode/screening-gate/objection-trust/operator-instruction). PERO Adrián TODAVÍA no puede usar un tool de marca real (recommend/book/share) por ESC-17 (EP-3 handler ABI roto — ver engine_lift_phase1). NEXT (sub-fase 2.4a, builder-agentic flagship): arreglar el ABI → la marca registra adapters sync (state,db)->dict que extraen args del state + puentean al service async (footgun event-loop: nada de asyncio.run dentro del stack async). TDD: test de EJECUCIÓN que llama el handler como node_tool_executor + arch test (todo handler EP-3 es callable sync, no StructuredTool). Live-verify: forzar un dispatch real + leer el tool result en logs. LUEGO 2.4b: VitaliaSchedulerProvider + match/share/book (deps verificadas: doctor_model + ruta pública /d/[clinica-slug]/[doctor-slug] + offer_service_specialist_links + scheduling create-appointment) + goldens book-*. LUEGO governance (migraciones 049-pattern + seed can_use_platform_keys + uv lock fastembed) + promote core SHAs a main + sync-all + downstream ×4 → proposal migrated. Seam 2.1/2.2/2.3 ya en wip/vitalia (e43015ee/3aff15af/833fece3); ESC-17 capturado fe481dac."
last_artifact: T-FE-1-result.md
lift_E_promote_2026-06-22: "DONE — engine lift core SHAs cherry-picked to main b4155f2a (44e1d4af Tier1 + 64c0e3e1 seam + e43015ee 2.1 + 3aff15af 2.2 + 3d2f3cf8 uv.lock) + sync-all (comunify/nicolify synced). Downstream ×4: sales-agent net-new=0 + comunify arch 144 + nicolify arch 20 + vitalia live. Proposal 2026-06-22-sales-agent-multibrand-graph-runtime → state: migrated. DEFERRED: ESC-18 (entangled brand commit, no urgencia) · book/ESC-19 (escalado Chris) · autonomous-dispatch ✅ RESUELTO+promovido a main (d8c737c4+7a326124, 0→~1.0 dispatch live; HEAD a1a95e1e; proposal ya actualizado — el checkpoint lo listaba deferido = STALE corregido 2026-06-22 audit) · uv.lock downgrade Docker-validation (ci-parity deferred). LOOP END-STATE: lift promoted+migrated; items restantes = ver known_gaps_2026-06-22."

reconcile_audit_2026-06-22:
  by: /pm-vitalia
  doc: RECONCILE-2026-06-22-doc-vs-reality.md   # SSoT del estado real (3 auditorías read-only + git)
  verdict: "construido real y sólido; checkpoint subreportaba 2 gaps de cableado live + 1 nota stale (autonomous-dispatch)"
known_gaps_2026-06-22:   # ★ surfaced por auditoría profunda — NO estaban explícitos en el checkpoint
  - id: GAP-1-resolvers
    sev: high
    status: BUILT   # ★ 2026-06-22 commit 0fd45f31 (builder-agentic flagship)
    desc: "RESUELTO. Los 5 set_*_service_resolver cableados vía sales_agent/composition.py::wire_sales_agent_tool_resolvers() llamado en extensions.py::register_all (cada resolver abre AsyncSession main-loop-bound + UoW commit/rollback/close; tenant/clinic authoritative del state). book = native-sync sin resolver (ESC-19). TDD: execution test RED(5 fail)→GREEN(6) + arch guard test_ep3_resolvers_wired. 454 sales_agent+arch PASS, inbox regression 103 PASS, ruff clean. Live-verify vs dev Postgres: tool_resolvers_wired log fired; screening+retract reachan el service (retract corrió query real → not_retractable, NO resolver-error). Round-trip Telegram full = G de Chris."
  - id: GAP-2-consulta-mode
    sev: high
    status: BUILT   # ★ 2026-06-23 commit 5bd0dd1b — engine inbound_mode_seam.py (mode-resolver default DECIDE) + deliver_response CONSULTA branch (0 outbound + draft + WS, post-ainvoke cache-safe); vitalia inyecta HonorModeBridge + draft sink (adrian_draft_pending, sin body). 13 engine + tests brand GREEN. Live-verify dev Postgres: CONSULTA→draft row, 0 outbound. Telegram round-trip full = G de Chris.
    desc: "El loop inbound NO honra modo `consulta` (borrador/0-outbound). HonorModeBridge solo gate del endpoint operator-instruction; sin pre-send interceptor en el loop. decide+pausa(human) sí; consulta no. Rompe SC-2/V-FN-2 (must_pass) en live."
    buildable: engine-seam   # ★ routing 2026-06-22: NO brand-buildable. EP-13 pre_send es signature-only/unwired; ChatOrchestrator singleton hardcoded sin mode-resolver injection; engine handler_mode solo conoce `human`. SEAM: generalizar handle_human_mode→resolve_mode + draft_only en deliver_response (conversation_pipeline.py), brand inyecta HonorModeBridge. → /pm-luana promotion.
  - id: GAP-3-activity-feed
    sev: high
    status: BUILT   # ★ 2026-06-23 commit 5bd0dd1b — platform AgentTurnCompletedEvent (IDs+stage, CERO PHI) por el outbox adapter_bus existente; subscriber vitalia escribe vitalia_activity_events (adrian_turn, dual-filter, sanitizado). Emit+listener juntos (anti-orphan). Live-verify dev Postgres: DECIDE→activity row, sin PHI.
    desc: "El loop NO emite activity event al inbox ('nutre el inbox glass-box' del Goal). process_chat_flow escribe solo audit_log, nunca vitalia_activity_events. Rompe el '+activity' de SC-1/V-FN-1 (must_pass) en live."
    buildable: engine-seam   # ★ routing 2026-06-22: HYBRID. AuditEmitter sin brand-listener seam. SEAM additivo: emitir AgentTurnCompletedEvent (solo IDs+stage, sin PHI) por el outbox EventBus existente; el SUBSCRIBER que escribe vitalia_activity_events = brand puro. Land emit+listener juntos (anti-orphan). → /pm-luana promotion (mismo proposal que GAP-2: 2 seams, mismos 2 files engine).
  - id: GAP-4-book-esc19
    sev: blocked
    desc: "book runtime-bloqueado: dos tablas appointment (engine `appointments` write vs brand `vitalia_appointments` read=grilla Mateo) + AgendaGridRepositoryImpl sin create()/create_clinic_map(). Decisión dominio scheduling, escalada a Chris."
    buildable: chris-decision
  - id: GAP-5-reschedule-lane
    sev: medium
    desc: "★ descubierto en GAP-1 build (0fd45f31): reschedule_appointment YA reacha su service (resolver cableado), pero el lane scheduling `update_slot` es un stub fail-fast → el tool degrada elegante a fallback en español. Mismo dominio que GAP-4/book (scheduling create/update lane incompleto). Follow-up de scheduling, no de sales_agent."
    buildable: chris-decision   # dominio scheduling (coordinar vitalia-scheduling-mateo-review)

# Schema v2 migration (cement 2026-05-27)
release: F3
cap_target: adrian.inbox     # extiende la cap del inbox · posible derived cap adrian.canal-inbound (architect decide)
cap_change_type: extend      # new | fix | extend | derive
parent_story: null
---

# F3 vitalia-fase2-adrian-canal-inbound — checkpoint

## Goal

Cablear el **loop autónomo de atención por canal** de Adrián: que un mensaje entrante de WhatsApp / Instagram / Telegram dispare el runtime sales_agent y produzca una respuesta, **nutriendo el inbox en vivo** — tal como funcionaba el `sales_agent` legacy, pero re-hogarado al shell-organism actual y mejorado.

Pipeline objetivo:

```
webhook canal recibe mensaje
  → persiste en conversación (crm/inbox)
  → invoca grafo sales_agent (engine, vía import) RESPETANDO el modo por-conversación que fija el inbox
     (🤖 Adrián decide · 🤝 consulta · 👤 humano = NO responde)
  → firewall PHI compliance + format_for_channel
  → responde por el adapter del canal
  → emite activity event → el inbox lo muestra glass-box
```

## Naturaleza (★ leer antes de refinar)

**NO es construir el agente.** El cerebro YA EXISTE y se reutiliza al máximo:

| Pieza que YA EXISTE | Path | Cómo se usa |
|---|---|---|
| Runtime LangGraph (cerebro) | `core/luana-core-sales-agent/.../application/orchestrator/{chat.py,graph.py}` + `agents/sales/graph.py` + `smart_debounce_runner.py` | **CONSUMIR vía import. READ-ONLY.** Tocar = `/pm-luana` promotion gate |
| Extensión de marca vitalia | `vitalia/backend/src/modules/vitalia/sales_agent/` | tools (screening, payment_link, reschedule, reengagement, retract) + 5 personas voz + prompts + state_overlay — REUSE |
| Adapters canal (OUTBOUND) | `vitalia/.../connections/{whatsapp,instagram}/adapter.py` | REUSE para enviar; **falta el INBOUND receiver** |
| Format + intent + compliance | `core/luana-core-channels/format_for_channel.py` + `intent_detector.py` · `core/luana-core-compliance` | REUSE |
| Inbox (superficie + modo) | `vitalia/.../inbox/` (story `adrian-inbox`) | el loop **respeta el modo** y **nutre** el activity stream |

**Antecedente:** el loop fue **shipped en slice-1** (caps `sales_agent/inbox-handler-mode-occ` + `adrian-3-tools-mvp`, hoy `status: deprecated` / `slice-1-superseded`: *"Adrián atiende consultas en Instagram y WhatsApp"*). Se deprecó en la reorg del shell → quedó huérfano. Esta story lo **re-hogar + cablea + mejora**, NO lo inventa.

## Filosofía (Chris, 2026-06-04)

Reutilizar al máximo lo que ya existe, **mejorarlo**, y seguir haciendo de este sistema algo genial. Cero duplicación del engine. La historia está **conectada con las capabilities del inbox** → es modificadora → **lleva en su alcance las pruebas de regresión del inbox** (que nada de lo shipped del inbox se rompa al enchufar el loop).

## Anti-objetivos

- ❌ NO recrear el agente / grafo LangGraph — vive en `core/luana-core-sales-agent` (engine, `/pm-luana` para tocarlo)
- ❌ NO duplicar tools/personas/prompts — reusar la extensión `vitalia/.../sales_agent/` shipped
- ❌ NO reconstruir la UI del inbox — es `vitalia-fase2-adrian-inbox` (esta story la CONSUME + nutre)
- ❌ NO campañas/outbound masivo — eso es `adrian-outbound`
- ❌ NO reactivación de fríos — eso es `camila-reactivar`
- ❌ NO romper ninguna cap shipped del inbox (de ahí el regression scope obligatorio)

## Scope (preliminar — refina /po + /ux-agentico)

### § Inbound receivers (NEW — connections) · ★ TELEGRAM-FIRST (Chris 2026-06-04)
- **Telegram adapter NUEVO** (inbound + outbound — no existe en connections). **ÚNICO canal en scope.**
  Webhook receiver Telegram (setWebhook + recepción updates) → normalizar a `IncomingMessage`.
- ⏳ **Follow-up (FUERA de scope hasta tener API):** Webhook receiver WhatsApp Cloud API · Webhook
  receiver Instagram Messaging. Quedan como story posterior cuando Chris tenga la API real
  (no se construyen stubs no-verificables — Critical Rule #37).
- Normalización a un mensaje canónico → persiste conversación (reusar crm/inbox repos).

### § Trigger del runtime (sales_agent extension)
- Al persistir inbound, disparar el grafo (`orchestrator/chat.py`) con debounce (`smart_debounce_runner` — ráfagas).
- **Honrar el modo por-conversación** del inbox: 🤖 decide → responde · 🤝 consulta → propone sin enviar · 👤 humano / pausado → NO responde.
- Outbound vía adapter del canal tras firewall PHI + format_for_channel.

### § Feed del inbox (EXTEND inbox)
- Cada paso (mensaje, tool-call, respuesta) emite activity event que el inbox renderiza glass-box.
- Sin cambios de UI nuevos; integración con el activity stream shipped.

### § Regression scope (★ obligatorio — Chris)
- Suite de regresión de las caps del inbox: modos (set-mode + OCC), pause Adrián + undo 5min, send humano, nudge, proactive-outbound, activity stream, PHI channel policy.
- Gate: los tests del inbox shipped pasan SIN modificarse (regression_guard). Si cambian → revisión explícita.

## Dependencies map

### Hard
- `vitalia-fase2-adrian-inbox` — la superficie + el modo por-conversación que este loop respeta y nutre. **Debe aterrizar primero.**

### Soft
- `vitalia-fase2-adrian-embudo` — persistencia de conversación + tablero de leads.

### Esta historia desbloquea
- `adrian-outbound` (respuestas a campañas vuelven por este loop) · `camila-reactivar` (cierre del ciclo en el inbox).

## Prior art scan

> Ejecutado 2026-06-04 (`/pm-vitalia`). Detalle de paths en § Naturaleza arriba.

- **Engine cubre 100% del cerebro** → CONSUMIR import. `core/luana-core-sales-agent` runtime LangGraph + `core/luana-core-channels` + `core/luana-core-compliance`.
- **Extensión de marca shipped** → REUSE `vitalia/.../sales_agent/` (tools + personas + prompts).
- **Adapters connections** → REUSE outbound whatsapp/instagram; falta inbound receiver.
- **Telegram** → net-new adapter (no existe en vitalia ni se usa en engine channels más allá de base genérica).
- **Caps slice-1 deprecated** → re-home candidate (verificar código huérfano recuperable antes de fijar new vs extend).
- **Decisión:** `extend` (conecta/modifica inbox + reusa engine). Posible `derived cap` `adrian.canal-inbound` — lo decide `/architect`.

## ✅ Verificación pre-refinement — HECHA (2026-06-04, `00-research.md`)

- **Cerebro en engine** (`core/luana-core-sales-agent`: orchestrator/chat.py + smart_debounce + graph + handle_telegram_webhook) → CONSUMIR import, read-only.
- **Extensión `vitalia/.../sales_agent/` in-tree + registrada EP-3** (tools/personas/state_overlay/observability/lead_screening) → REUSE.
- **Loop NUNCA cableado** (`webhook_routes.py` = stubs "T-be-8 scope"; cero imports del orchestrator en vitalia) → falta **enchufar**, no rescatar borrado.
- → **`extend` confirmado.** Detalle: `00-research.md`.

## Decisiones Chris (2026-06-04, ratificadas vía /pm-vitalia)

1. **Telegram-first** — WhatsApp/IG = follow-up cuando haya API (no stubs no-verificables).
2. **Mejora del LLM gateway = item `/pm-luana` aparte** — esta story CONSUME el gateway tal cual (ya funciona); mejorarlo toca engine (promotion gate). Proposal SSoT `docs/promotion-protocol/proposals/2026-06-04-llm-gateway-chinese-first.md`.
3. **Refinar ya en paralelo** — spec/flujo avanzan (bucket docs); el BUILD espera a que dep hard `adrian-inbox` cierre.

## Decisión Chris 2026-06-05 — secuenciar servicios primero + match in-scope

Origen: Chris preguntó cómo Adrián entiende la necesidad del paciente + presenta al especialista disponible (match first + callbacks) si no hay servicios creados ni doctores cableados al agente. Investigación (`00-research-data-foundation.md` abajo). **Decisiones:**

1. **Secuenciar servicios PRIMERO** (no por capas). canal-inbound nace con el match completo. → dep hard NEW: `lisa-servicios` debe aterrizar antes del BUILD de canal-inbound.
2. **Servicios = Offer Studio (escalera de valor)** — ofertas con LadderSlot (lead-magnet/core/profit-maximizer), no catálogo plano. Es lo que `lisa-servicios` ya diseñó + lo que el `TenantKnowledgeBuilder` del engine ya lee.
3. **El match servicio→especialista pasa a IN-SCOPE de canal-inbound** (antes "layered/follow-up"). Mecánica: § Match servicio→especialista del spec + § en el design (tool brand-level `match_service_and_specialist`, NO toca engine).

**Cadena de bloqueo del match:** `lisa-servicios` (catálogo Offer Studio + link servicio↔doctor) → cablear doctores clínicos al conocimiento de Adrián (tool brand-level, NO el `team` de Brand Studio que ve hoy) → canal-inbound consume el match. **Gap a asignar hogar:** el "wire doctores+servicios → Adrián" (¿en lisa-servicios? ¿slice agentic propio? ¿dentro de canal-inbound?) — pendiente `/architect`/Chris.

## Scope-add ratificado Chris 2026-06-21 — `book_appointment` (cerrar el gap "agendar")

**Origen:** Chris retoma la story (deps reportadas cumplidas: staff + servicios construidos) y pide validar si Adrián ya puede "agendar reuniones" desde el loop. **Hallazgo (grep verbatim):**

- **Motor de agendar EXISTE + LIVE:** `BookingService.create_booking` (`vitalia/backend/src/modules/vitalia/application/services/booking_service.py:176`) con advisory locks · cap `booking/prepaid-booking-advisory-locks` (status live) · endpoint `api/routes.py:376`.
- **NO cableado a Adrián:** el grafo `sales_agent` (que el loop dispara) solo expone `screening_questions` · `send_payment_link` · `reschedule_appointment`. Ninguna **crea** turno. `reschedule` mueve uno existente; `send_payment_link` **requiere `appointment_id` ya existente** (no puede ser entrada). El `tool_groups: booking` de RN-3b está **hueco** del lado de Adrián.
- **Tool que SÍ agenda existe en OTRA surface:** `agentic/tools/appointment_reschedule_with_doctor.py` acción `propose_and_book` → `BookingService.create_booking`, pero cableada al agente `agentic`/copilot (cap `agentic.eval-goldens-slice-1`, Story 11), NO al grafo de Adrián.

**Decisión Chris:** el book va **dentro de canal-inbound** (dueña del runtime de Adrián + ya declara el `booking` group). 

**Fix (cero duplicación):** tool fina `book_appointment` en `sales_agent/tools/` que delega vía DI a `BookingService.create_booking` existente + bindeo al grafo de Adrián. Flujo prepago natural: `match_service_and_specialist` → `list_slots` → **`book_appointment` (hold)** → `send_payment_link` (seña) → confirma al pagar. `list_slots`/`propose_and_book` de `agentic/tools/` = referencia portable.

**A refinar (/po → /ux-agentico):** RN/AC/scenarios del paso agendar · fuente de slots disponibles por doctor (toca modelo disponibilidad de `lisa-doctores` — recurrencia/vista-mes cambiaron; ver story `vitalia-scheduling-mateo-review`) · guarda-por-modo (decide ejecuta el book · consulta deja propuesta sin holdear) · idempotencia del hold · qué pasa si el slot se ocupa entre propose y book (advisory lock 409).

## Dependencias — estado 2026-06-21

Chris reporta `lisa-servicios` + `adrian-inbox` **construidos** → BUILD desbloqueado. Verificar `state: done` de ambos en el handoff a `/architect` (no asumir). El match servicio→especialista (in-scope desde 2026-06-05) + el nuevo book comparten la fuente de datos doctores/servicios.

## Próximo paso

`/po` pliega `book_appointment` al `01-spec.md` (RN/AC/scenarios + guarda-por-modo) → `/ux-agentico` folda el paso al flujo turn-by-turn + state machine. Re-ratificar Chris → `refining → refined` → `/architect`.

## Referencias

- **Engine:** `core/luana-core-sales-agent/` (runtime · read-only)
- **Extensión marca:** `vitalia/backend/src/modules/vitalia/sales_agent/`
- **Inbox sibling:** `vitalia/docs/product/stories/vitalia-fase2-adrian-inbox/` (superficie + modo)
- **Caps shipped (deprecated):** `vitalia/docs/product/capabilities/sales_agent/{inbox-handler-mode-occ,adrian-3-tools-mvp}.yaml`
- **Slice-1 archived:** `vitalia/docs/archive/2026/stories/vitalia-slice-1-inbox/`
- **Rules:** `.claude/rules/anti-duplication.md` · `.claude/rules/anti-duplication-refining.md` · `.claude/rules/definition-of-done-live-verify.md` (regression scope) · `vitalia/.claude/rules/hipaa-lite.md` (firewall PHI por canal)

## Scope-add ratificado Chris 2026-06-11 (origen: delta doctores D3-B — /po-ux)

**Adrián consume el perfil del doctor para la venta.** Hoy NADA del doctor llega al sales_agent (verificado por grep — el "la consume el agente de ventas" del spec doctores era aspiracional). Esta story, como dueña del runtime Adrián, suma:
1. **Contexto de venta:** bio_public (Resumen/Formación/Enfoque) + especialidad + servicios del doctor asignado/preguntado entran al contexto del agente (slot/KB — architect decide mecanismo).
2. **Acción "compartir perfil del doctor":** cuando el lead pregunta por el doctor o se le informa quién lo atenderá, Adrián envía el **link de la página pública mobile-first del doctor** (página = scope de `vitalia-fase2-lisa-doctores` § D3-D — corrección Chris 2026-06-11; esta story consume la URL).
3. Solo doctores con "Visible en landing" ON son compartibles/citables.

El architect de esta story debe declarar el contrato con la página del doctor (URL pattern `/d/{clinica}/{doctor}` — D3-D doctores) + el slot de contexto. Registrado también en `vitalia-fase2-lisa-doctores/01-spec.md § Derivadas del delta`.
