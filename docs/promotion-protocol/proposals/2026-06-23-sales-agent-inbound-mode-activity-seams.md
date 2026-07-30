---
slug: sales-agent-inbound-mode-activity-seams
state: accepted              # Chris ratificó 2026-06-23 (dir A → lift /pm-luana in-hub, skip 1). Migrated cuando el grafo ejerza ambos seams live + downstream ×4 green.
date: 2026-06-23
ratified_by: Chris
ratified_basis: "Audit profundo canal-inbound (RECONCILE-2026-06-22) surface 2 gaps de cableado live (GAP-2 consulta-gate · GAP-3 activity-emit); routing confirmó que NINGUNO es brand-buildable (EP-13 pre_send signature-only/unwired · ChatOrchestrator singleton sin mode-resolver injection · AuditEmitter sin brand-listener). Chris eligió dir A (construir OLA-2) → lift /pm-luana in-hub + SCOPE_GATE_SKIP=1."
target_package: core/luana-core-sales-agent
semver_impact: minor          # 2 seams ADITIVOS, backward-compatible (default = comportamiento actual; brand opt-in)
origin_story: vitalia/docs/product/stories/vitalia-fase2-adrian-canal-inbound
origin_analysis: vitalia/docs/product/stories/vitalia-fase2-adrian-canal-inbound/RECONCILE-2026-06-22-doc-vs-reality.md
prior_proposal: 2026-06-22-sales-agent-multibrand-graph-runtime   # migrated · cerrado · esto es follow-up nuevo
in_hub: true                  # wip/vitalia, SCOPE_GATE_SKIP=1 (ratificado Chris · mismo patrón que Tier 2.1/2.2/2.3 + ESC-17)
downstream_consumers: [vitalia, comunify, nicolify, lupulo]
---

# Promotion proposal — sales_agent inbound loop: mode-resolver + activity-emit seams

## Problema

El loop inbound del `sales_agent` (engine `core/luana-core-sales-agent/.../application/orchestrator/chat.py` → `process_chat_flow` → `conversation_pipeline.py` → `deliver_response`) corre end-to-end y Adrián responde, pero **2 objetivos core del spec de canal-inbound NO están cableados al runtime** porque el engine no expone el seam:

1. **GAP-2 — modo `consulta` no honrado.** El loop solo intercepta `handler_mode == "human"` (`conversation_pipeline.py::handle_human_mode`). El engine no conoce `consulta`/`proposal_required` (es concepto brand). No hay punto de inyección de un mode-resolver ni un pre-send hook (EP-13 `pre_send_check` es signature-only — `dispatch_guardrail` lanza `NotImplementedError`, nunca se invoca). → SC-2/V-FN-2 (must_pass) imposible de cumplir live.
2. **GAP-3 — el loop no emite activity event al inbox.** `process_chat_flow` escribe solo `audit_log`; `AuditEmitter` emite WS + `LeadCapturedEvent` pero ningún evento por-turno que un brand pueda consumir para escribir `vitalia_activity_events`. → el "+activity" de SC-1/V-FN-1 (must_pass) + el objetivo "nutre el inbox glass-box" no se cumplen live.

Ambos requieren editar el engine (boundary `/pm-luana`). Son **aditivos** (cero cambio de comportamiento para quien no opta).

## Seam 1 — mode-resolver + draft_only (GAP-2)

**Contrato (additivo, backward-compatible):**

- `conversation_pipeline.py`: generalizar la rama de modo. Hoy `handle_human_mode(checkpoint)` branchea solo en `handler_mode == "human"`. Introducir un **mode-resolver opcional inyectable** que devuelva `DECIDE | CONSULTA | PAUSA` a partir del estado de conversación. Default (sin resolver registrado) = comportamiento actual EXACTO (`human` → skip AI; resto → responde). El brand inyecta su `HonorModeBridge` ya construido (`vitalia/.../sales_agent/application/services/honor_mode_bridge.py`) como ese resolver.
- `deliver_response`: añadir un **`draft_only` path**. Cuando el modo resuelto = `CONSULTA`, en vez de `OutputManager.process_response` (outbound real): log + WS (al inbox) + **0 outbound al canal** + persistir el texto como borrador (el brand decide dónde — store de drafts/activity brand bajo dual filter tenant+clinic, NUNCA en logs del engine).
- **Cache-safety:** el resolver/draft branch corre **POST `agent_app.ainvoke`** (CONSULTA igual consume tokens por diseño — el agente razona, luego se decide enviar o no). Interceptar SOLO en `deliver_response`. NO gatear antes de `invoke_agent_with_typing` para CONSULTA (solo PAUSA corta pre-grafo, que `handle_human_mode` ya hace). Prompt-cache slots + ejecución del grafo intactos.
- **Inyección:** el seam debe ser registrable por brand SIN que el engine importe nada brand (hexagonal: engine = puerto, brand = adapter). Default None → comportamiento actual.

## Seam 2 — AgentTurnCompletedEvent (GAP-3)

**Contrato (additivo, backward-compatible):**

- Nuevo evento de dominio liviano `AgentTurnCompletedEvent { tenant_id, lead_id, conversation_id, role, funnel_stage, occurred_at }` — **SOLO IDs + stage, CERO PHI / CERO bodies de mensaje** (HIPAA-lite). Emitido por el **outbox `EventBus` existente** (`luana_core_events`, ya usado en `audit_emitter.py`) en cada turno inbound (en `AuditEmitter` o `deliver_response`).
- El **subscriber que escribe `vitalia_activity_events` = brand puro** (reusa el `ActivityRepoPort` de `operator_instruction_service`). Brands sin subscriber ignoran el evento → cero cambio de comportamiento.
- **Anti-orphan (CONN):** land engine-emit + brand-listener JUNTOS. Un emit sin consumer = isla.

## Brand follow-up (vitalia, post-lift · NO es engine)

1. Registrar `HonorModeBridge` como mode-resolver del seam 1 + un draft-writer brand (consulta → borrador en activity/draft store, dual filter).
2. Subscriber `AgentTurnCompletedEvent` → escribe `vitalia_activity_events` (description_es genérico + sanitize, dual filter tenant+clinic).
3. Live-verify (Rule #37): mensaje real Telegram en `consulta` → 0 outbound + borrador + activity row; en `decide` → reply + activity row. Leer logs + confirmar filas.

## Semver + migración

- **minor** en `core/luana-core-sales-agent` (2 puntos de extensión opcionales + 1 tipo de evento nuevo). Sin breaking. Sin migración de schema en engine (el `vitalia_activity_events` ya existe brand-side; los drafts usan store brand existente o uno nuevo brand-local).

## Downstream regression (×4)

- `core/luana-core-sales-agent/tests/` verdes sin tocarse (seam con default None = comportamiento idéntico).
- arch + suite de cada brand consumer (vitalia/comunify/nicolify/lupulo) — el seam default-off no cambia su runtime. vitalia ejerce el seam (único opt-in inicial).
- Engine-edit detection (auditor rule 14): ambos seams aditivos (param opcional default-actual + evento nuevo) → blast radius mínimo.

## Verificación (bar runtime, NO arch-verde)

`migrated` SOLO cuando: (a) suite engine + ×4 brands green; (b) vitalia ejerce AMBOS seams live (consulta → 0 outbound + borrador + activity; decide → reply + activity) contra Postgres dev real + logs leídos; (c) cero PHI en el payload del evento (verificado en trazas).

## Estado

- `accepted` 2026-06-23 (Chris). In-hub wip/vitalia, SCOPE_GATE_SKIP=1.
- **Build LANDED** 2026-06-23 commit `5bd0dd1b` (builder-agentic flagship): engine `inbound_mode_seam.py` + `events.py::AgentTurnCompletedEvent` + `conversation_pipeline.py` CONSULTA branch + `audit_emitter.py` emit + vitalia `inbound_seam_adapter.py` + composition wiring. 13 engine + 13 brand tests RED→GREEN; downstream ×4 GREEN (comunify 144 · nicolify 20 · engine observability 36 + platform events 19); seam default-off = byte-idéntico. Live-verify vs `vitalia_dev` real: DECIDE→activity row · CONSULTA→draft row (0 body, 0 outbound) · sin PHI.
- ⚠️ Race shared-index: commit `9feb302c` quedó MISLABELED (contenido del parallel session mateo T-BE-4 bajo el subject de este lift). PUSHED → NO rewrite (git-safety). Contenido intacto; flag a /pm-vitalia para repointar el SHA del mateo checkpoint.
- **PENDIENTE para `migrated`:** (a) G de Chris — round-trip Telegram live ejerciendo ambos seams (el bar §Verificación lo exige); (b) /auditor (auditor-agentic) single pass post-OLA-2. Recién con ambos → `migrated`.
