---
story_id: vitalia-fase2-adrian-inbox
brand: vitalia
type: ui-story
state: refining
architecture_pattern: ADR-vitalia-004
agent_owner: adrian
map_zone: agentes
map_box: adrian
module: inbox
cap_target: adrian.inbox
cap_change_type: fix
po_ux_version: 2
ratified_by_chris: true
amended_2026_06_04: "2-modos (decide/consulta) + composer dock + pausa 60/permanente + RBAC operador + leads visibles — ver § Scope amendment"
---

# vitalia-fase2-adrian-inbox — 01-spec (UI standard · MIGRACIÓN + consolidación)

> **Naturaleza:** esta NO es una construcción virgen. El inbox ya está **shipped y probado** (slice-1-inbox, done) pero quedó **huérfano** (sin ruta) tras la reorg del shell. Esta story lo **re-hogar + consolida + re-temiza + cablea** dentro del espacio shell-organism de Adrián, alineado al paradigma conversation-first del embudo. ~90% reuse.
> **Encuadre que pidió Chris:** el § Componentes distingue explícito **lo que HAY · lo que MIGRO · lo que CREO · lo que MODIFICO · lo que BORRO.**

## § Scope amendment 2026-06-04 (★ del modelo 3-modos al modelo 2-modos · construido + live-verified + firmado por Chris)

> Durante el build (rondas r6–r8 de UI + 2 bombas de wiring FE↔BE que **nunca se habían ejercido**), el paradigma de atención **cambió de 3 modos a 2 modos**. Chris lo probó live en `dev-app.vitalialat.com` y firmó `demo_signoff: APPROVED_WITH_NOTES` (checkpoint). Esta sección es la **autoridad** sobre las partes de abajo que describen el modelo viejo. Lo que **cambió** (intencional, NO revertir):

| # | Eje | Antes (3-modos) | Ahora (2-modos · construido) | AC afectada |
|---|---|---|---|---|
| 1 | **Modos** | `decide` / `consulta` / **`manual` ("Yo escribo")** | **2 modos**: `Adrián decide` · `Adrián consulta`. "Yo escribo" **eliminado** como modo; escribir manual = **Pausar Adrián**. Toggle `role=radiogroup` 2 segmentos; activo = **verde** (`vt-bg-success`). | **AC-4 MODIFICADA** |
| 2 | **Composer** | montaje condicionado por modo (ComposerArea existía pero `InboxThread` no lo renderizaba → "no salía nada") | **siempre montado** en un *dock* al pie del thread (`thread-composer-dock`); el operador escribe como humano (`handler_mode='human'`), texto enviable. | **AC-5 MODIFICADA** |
| 3 | **Pausa** | popup con campo *reason* + 1 botón "60 min" (path roto `/pause-adrian` 404 — nunca funcionó) | modal con **2 botones** `[Pausar 60 minutos][Pausar permanente]` (rojo), **sin reason**; barra de estado en el dock; permanente = far-future (~100 años). | nueva (parte de AC-5) |
| 4 | **RBAC del inbox** | mutaciones gateadas a `_PHI_ROLES` {doctor,nurse,admin_clinic} → **owner 403** | `_INBOX_OPERATOR_ROLES = _PHI_ROLES ∪ {owner, receptionist}` (el inbox es la **herramienta del operador**; `dr.demo` = owner). marketing/sales/patient siguen denegados. | RN-15 (nueva) |
| 5 | **Privacidad del lead** | identidad **enmascarada** por defecto (`***`) | **leads visibles por defecto** (interim ratificado Chris); `PiiMaskedSpan` ganó prop `masked` (default `true` → resto de la app intacto); `ContactSidebar` pasa `masked={false}`. Wrapper + `data-phi` conservados (audit + arch test FE-A6 siguen viéndolo wrapeado). | **AC-10 MODIFICADA** + RN-16 |
| 6 | **Query-keys** | mutaciones invalidaban `['adrian','inbox',…]` pero el thread lee `['crm','conversation',id]` → el 200 nunca reflejaba | mode/pause/send migrados a keys **crm-shared** (`['crm','conversation',id]` / `['crm','conversations']`). | nota arch |
| 7 | **BE** | `ConversationRepository` sin `set_pause_until`; `_NoOpRedisClient` sin `setex` → pausa 500 | ambos agregados (pause persiste en DB; Redis es solo fast-path). | nota arch |
| 8 | **UI varios** | — | wallpaper crema **fijo** (no scrollea), dot verde intermitente, "Pausar" rojo tenue, `cursor-pointer` global, ícono 🛠 herramientas **fuera** del header (la actividad vive en el `ActivityStream` inferior), campo "Estado" duplicado **eliminado** (queda "Etapa de la venta"), "Servicio de interés" **siempre visible** ("Aún no detectado" si vacío). | AC menores |

**Ubicación del full-canvas + responsive:** el squeeze del thread cuando coexisten Valeria-chat + ContactSidebar (RN-11/RN-12/AC-7 + AC-12) se **splitó** a la bugfix-story de shell `vitalia-bugfix-shell-nav-scroll-errors` (**`done`**). `ConversationModeButton` sigue presente. Estos no bloquean el `done` de esta story (verificación cubierta por la story de shell).

## § Context

- **Release:** F3 · **Módulo:** `inbox` (consume `sales_agent` + `crm` + `connections` + `compliance`).
- **Hogar del mapa (paradigma):** zona **Agentes** → caja **Adrián** → área **inbox**. Adrián opera; Valeria supervisa; el humano interviene. Es la "conversación viva del lead"; el embudo (hermano) es "el tablero de leads".
- **Punto de inserción:** Ribbon N1 (Adrián, cian `#01B2F8`) → SubTabsBar N2 → sub-tab **Inbox**. Hoy esa ruta la sirve el genérico `[agent]/[subtab]/page.tsx` → `InboxPlaceholder`. Esta story crea la ruta real `adrian/inbox/page.tsx` (patrón `mateo/agenda/page.tsx`).
- **Out-of-scope (anti-creep):**
  - NO reactivación de leads fríos (→ `camila-reactivar`).
  - NO diagnóstico de conversaciones congeladas (→ `adrian-embudo` § Congeladas).
  - NO bulk actions multi-conversación (story futura).
  - NO realtime WebSocket (MVP = polling 10s; upgrade post-MVP).
  - NO tocar engine `core/luana-core-sales-agent` / `core/luana-core-copilot` (read-only — consumir vía import + brand tools).
  - NO outbound proactivo masivo / campañas (→ `adrian-outbound`); SÍ el nudge 1:1 dentro de una conversación viva.

## § Prior art applied

> Scan ejecutado (engine + vitalia propio + legacy nicolify + embudo sibling). Detalle en `checkpoint.md § Prior art scan`.

- **Reuse — inbox shipped huérfano:** `vitalia/frontend/src/features/inbox/` (~40 comps slice-1, done): `SegmentedControl3Modes`, `AgentActivityStream`, `ContactSidebar` (PHI), `ActionReceiptUndoChip`, `PauseAdrianButton`+`PauseAdrianConfirmModal`, `VoiceMessagePlayer`, `ImageAnalysisCard`, `AdrianToolsSheet`, `ProactiveOutboundModal`, `ProposalCardBanner`, `FilterChips`, `ConversationList/Item/Thread`, `MessageBubble`, `ThreadHeader`, `ComposerArea`, 8 estados visuales + hooks React Query (`use-conversations`, `use-conversation-detail`, `use-send-message`, `use-set-mode`, `use-pause-adrian`, `use-activity-stream`, …). Diseño funcional SSoT: `vitalia/docs/archive/2026/stories/vitalia-slice-1-inbox/02-design-ui.md`.
- **Reuse — subset parity F1-S10:** `vitalia/frontend/src/features/adrian/components/inbox/` (`ConversationItem`, `ContactSidebar`, `ThreadHeader`, `TakeoverBanner`, `MessageBubble`, `MessageInput`, `CampaignTag`, `types.ts`) — hogar FSD correcto, versión simple.
- **Reuse — shell organism mejorado:** `ShellOrganismLayout(Client)` (splitter resizable), `ValeriaSidebar` (estados `collapsed`/`rail`/`full` vía `useShellStore`), `Ribbon`/`SubTabsBar`, `EntitySubNavBar`, `EmptyState`, `_agent-tw-classes`. Tokens: `globals.css` (`--agent-adrian #01B2F8`).
- **Reference — legacy sales studio (`closer-studio`):** `~/Proyectos/luana-nicolify-legacy/.../features/closer-studio/` — patrón 3-pane + hooks agénticos `stop/resume · send · nudge · reactivate · diagnose` + `use-closer-ws` (realtime) + `use-kpis`. Vitalia ya evolucionó `stop/resume → 3-modos`. **Traigo `nudge`**; difiero `reactivate`/`diagnose` (otras stories).
- **Engine consumed:** `core/luana-core-sales-agent` (LangGraph runtime, AgentStateCheckpoint, transitions) + brand tools shipped `vitalia/backend/src/modules/vitalia/sales_agent/tools/` (`payment_link`, `reschedule_appointment`, `retract_last_message`, `screening_questions`, `send_proactive_reengagement`). Backend inbox: `vitalia/backend/src/modules/vitalia/inbox/api/router.py`.
- **Compliance consumed:** `core/luana-core-compliance` `ComplianceService.validate_outbound_message` (firewall PHI por canal).
- **Observability consumed:** `core/luana-core-observability` `copilot_trace_event` + `sanitize_payload` (activity stream).
- **Learnings aplicados:** embudo `research/{01-legacy-pipeline,02-core-engine,04-detail-entry-pattern}.md` (conversation-first + consumir sustrato engine + EntitySubNavBar). Embudo learning panel-content fluido (sin `max-width` hard).
- **Lift candidates:** `ChannelBadge` (badge de canal WhatsApp/IG/Email/Web) aparece en inbox + embudo + futuras → candidate `components/shared/shell-organism/ChannelBadge.tsx` (brand-local primero; escalar `/pm-luana` si aparece en ≥2 brands).
- **Net-new justificado:** consolidación adrian/inbox + "modo conversación" (colapso Valeria) + Valeria-reacciona-básica + registro `adrian.inbox` en shell-routes — no existían.

## § Mapa funcional

### Happy path (camino dorado)

1. La recepcionista entra a **Adrián → Inbox**. Ve la lista de conversaciones cross-canal (WhatsApp · IG · Email · Web), ordenadas por actividad reciente; cada una muestra quién la opera ahora (🤖 Adrián decide · 🤝 consulta · 👤 humano) y un punto de no-leído.
2. Hace clic en la conversación de **P. H.** (paciente, nombre enmascarado). El thread central carga el historial; la URL pasa a `?conv={id}` (deep-link). El panel de Valeria a la izquierda **reacciona**: "Estás viendo a P. H., preguntó por blanqueamiento, Adrián ya le pasó disponibilidad. ¿Querés que le ofrezca la promo?".
3. La conversación está en **🤖 Adrián decide**: el thread muestra, inline y explicable, lo que Adrián hizo — un mensaje del paciente, una **tool-call colapsable** ("Adrián verificó disponibilidad → 3 turnos"), y su respuesta. El **Activity stream** abajo registra todo cronológico (glass-box).
4. La recepcionista quiere intervenir: pulsa **"Pausar"** en el dock → modal con **[Pausar 60 minutos] / [Pausar permanente]** (sin reason). Elige 60 min. El composer (siempre montado al pie) la deja escribir y enviar firmando como humana; Adrián queda en pausa para esa conversación (`POST …/pause` 200, `pause_until` persiste).
5. Si quiere que Adrián redacte y ella apruebe, cambia el toggle a **🤝 Adrián consulta** (`PATCH …/mode` 200; el segmento activo se pone verde). Vuelve a **🤖 Adrián decide** cuando quiera autonomía. Cada cambio de modo queda en el **audit log**.
6. (Foco total — full-canvas que colapsa a Valeria — vive en la story de shell `vitalia-bugfix-shell-nav-scroll-errors`, `done`.)

### Bifurcaciones (árbol)

```
Entrar a Adrián → Inbox
├── ¿Hay conversaciones?
│   ├── NO → empty state "Aún no hay conversaciones" + explicación canales [SC-empty]
│   └── SÍ → lista renderiza (paginada, filtros, búsqueda)
│       ├── Filtro aplicado sin resultados → empty "Sin resultados · limpiar filtros" [SC-empty]
│       └── Lista con N items
│           └── Clic en conversación → thread carga + URL ?conv={id} + Valeria reacciona [SC-1 happy]
│               ├── Modo 🤖 Adrián decide
│               │   ├── Paciente escribe → Adrián procesa (polling 10s trae tool-calls + respuesta) [SC-1]
│               │   ├── Tool falla / paciente pide humano → Adrián ESCALA (banner "🔴 Adrián pide ayuda") + auto-switch a Yo escribo [SC-edge]
│               │   └── Paciente pide resultados clínicos por WhatsApp → ComplianceService BLOQUEA + deriva a portal [SC-adversarial]
│               ├── Modo 🤝 Adrián consulta
│               │   └── Adrián prepara borrador → humano aprueba / edita / descarta → recién ahí se envía [SC-2]
│               ├── Pausar Adrián (dock) → modal [60 min]/[permanente] → POST /pause + composer humano + audit [SC-4]
│               ├── Composer (siempre montado) → operador escribe + envía → POST /messages → aparece en el thread [SC-composer]
│               ├── Acción nudge (empujón) → Adrián manda re-enganche 1:1 a conv activa estancada [SC-nudge]
│               └── Cambio de modo (toggle 2-modos) → PATCH /mode (OCC) + audit log row → segmento activo verde [SC-mode]
```

### Reglas de negocio

- **RN-1 · Modo por conversación (2-modos · ★ amendment).** Cada conversación tiene un modo derivado de `handler_mode` + `proposal_required`: **`Adrián decide`** (`handler_mode=ai`, `proposal_required=false`) o **`Adrián consulta`** (`handler_mode=ai`, `proposal_required=true`). El modo es por-conversación, no global. "Manual / Yo escribo" **ya no es un modo** — escribir como humano se logra **pausando a Adrián** (RN-17). El cambio de modo es `PATCH …/conversations/{id}/mode` con OCC (`expected_updated_at` en el body); 409 → rollback optimista.
- **RN-2 · Audit de modo.** Todo cambio de `agent_mode` y todo "Tomar control"/"Pausar"/"Reanudar" crea fila de audit log (quién/cuándo/de→a). Sync write antes de la respuesta.
- **RN-3 · Decide autónomo + escala.** En `decide`, Adrián responde solo; escala a humano (banner + auto-switch a `manual`) sólo si una tool falla, hay prompt-injection detectado, o el paciente pide humano explícito.
- **RN-4 · Consulta = humano firma.** En `consulta`, ningún mensaje sale sin aprobación humana; el humano puede editar el borrador antes de enviar; el envío queda firmado por el humano.
- **RN-5 · Pausar silencia a Adrián (★ amendment, reemplaza el viejo "Manual").** Pausar Adrián (60 min o permanente) detiene sus auto-respuestas en esa conversación; mientras está pausado, el operador escribe por el composer (siempre montado). No hay modo "manual" separado.
- **RN-6 · Glass-box.** Toda acción de Adrián (tool-call + resultado + mensaje) es visible inline en el thread (colapsable) y en el Activity stream cronológico.
- **RN-7 · PHI firewall (HIPAA-lite).** Adrián opera datos comerciales (interés, canal, oferta); NUNCA discute diagnóstico/resultados por canal no-encriptado. ComplianceService valida cada outbound; si es PHI inapropiada → bloquea + deriva a portal seguro.
- **RN-8 · ContactSidebar enmascarado.** Identidad del contacto va con `PiiMaskedSpan` + `RequireRole` (`doctor`/`nurse`/`admin_clinic`). Reveal audita.
- **RN-9 · Tenant isolation.** Toda query filtra `tenant_id` (+ `clinic_id` donde toque identidad de paciente). Cross-tenant → 404, sin leak.
- **RN-10 · Activity stream sanitizado.** Los trace events se persisten/sirven vía `sanitize_payload` — nunca PHI cruda.
- **RN-11 · 100% del lienzo.** El inbox ocupa siempre el 100% del panel de Adrián (sin `max-width` fijo). El thread fluye; las listas usan ancho completo disponible.
- **RN-12 · Modo conversación reversible.** "Full" colapsa Valeria (`valeriaState='collapsed'`) y recuerda el estado previo (`rail`/`full`) para restaurarlo al salir. Nunca pierde el estado de Valeria.
- **RN-13 · Nudge sólo sobre conv viva.** El nudge (empujón) aplica a una conversación activa estancada; no crea conversaciones nuevas ni reactiva leads fríos (eso es Camila).
- **RN-14 · Deep-link estable.** `?conv={id}` (o ruta equivalente) reabre la conversación correcta en refresh/deep-link. PHI nunca en la URL (sólo el id de conversación, no datos).
- **RN-15 · RBAC operador del inbox (★ amendment).** Las mutaciones del inbox (mode/pause/send/nudge) están gateadas a `_INBOX_OPERATOR_ROLES = _PHI_ROLES ∪ {owner, receptionist}`. El inbox es la herramienta operativa del dueño/recepción; `marketing`/`sales`/`patient` siguen denegados (403). Cross-tenant sigue 404 (RN-9).
- **RN-16 · Leads visibles por defecto (interim · ★ amendment).** La ficha de contacto muestra nombre/teléfono/correo del **lead** sin enmascarar (decisión interim ratificada por Chris). `PiiMaskedSpan` conserva el wrapper + `data-phi` (audit + arch test FE-A6 intactos) vía la prop `masked` (default `true`; `ContactSidebar` pasa `masked={false}`). El enmascaramiento por configuración ("Máxima seguridad") es follow-up (story aparte, PHI → `/architect`). PHI **clínica** (diagnóstico/resultados) sigue fuera del alcance de Adrián (RN-7).
- **RN-17 · Composer dock siempre montado (★ amendment).** El composer vive en un dock al pie del thread (`thread-composer-dock`) con barra de estado (verde "Adrián está atendiendo esta conversación" / pausado) + botón **Pausar** (rojo). El operador escribe como humano; el envío es `POST …/conversations/{id}/messages` (idempotency key). La caja siempre está usable; que Adrián además auto-responda lo gobierna el estado de pausa.

### Criterios de aceptación

- **AC-1** · La ruta `adrian/inbox` renderiza el inbox real (no el placeholder), ocupando el 100% del panel.
- **AC-2** · Lista cross-canal con filtros + búsqueda + badges de canal + badge de modo + no-leído.
- **AC-3** · Clic en conversación carga thread + persiste `?conv={id}` + Valeria reacciona (básica).
- **AC-4** · *(MODIFICADA 2-modos)* Toggle de **2 modos** (`Adrián decide` / `Adrián consulta`) cambia el modo vía `PATCH …/mode` (OCC) + crea audit log; el segmento activo se pinta **verde**; `aria-checked` refleja el modo activo.
- **AC-5** · *(MODIFICADA: composer dock + pausa)* El composer está **siempre montado** en el dock; el operador escribe y envía (`POST …/messages`, aparece en el thread). **Pausar Adrián** (60 min / permanente, sin reason) detiene las auto-respuestas (`POST …/pause` 200). En `consulta`, el banner de propuesta permite aprobar/editar antes de enviar.
- **AC-6** · Tool-calls de Adrián aparecen inline (colapsables) + Activity stream cronológico.
- **AC-7** · Botón "Modo conversación" colapsa Valeria → inbox 100% → restaura estado previo.
- **AC-8** · Nudge envía re-enganche 1:1 a conv activa + queda en Activity stream + audit.
- **AC-9** · ComplianceService bloquea PHI por canal no-encriptado y deriva a portal.
- **AC-10** · *(MODIFICADA: leads visibles interim)* ContactSidebar muestra la identidad del **lead visible** por defecto (nombre/teléfono/correo, `masked={false}`) conservando el wrapper `PiiMaskedSpan` + `data-phi` (audit + FE-A6 intactos); "Servicio de interés" siempre visible; "Etapa de la venta" única (sin "Estado"). RBAC + enmascaramiento configurable = follow-up.
- **AC-11** · Cross-tenant bloqueado (dual filter); a11y axe pass; Spanish neutro.
- **AC-12** · Mobile: 3-pane colapsa a tabs (Conv · Thread · Detalles); Valeria a drawer.
- **AC-13** · `features/inbox/` huérfano consolidado en `features/adrian/` + eliminado; `adrian.inbox` registrado en shell-routes.

## § Gherkin scenarios

### SC-1 — happy: modo Decide + tool-call exitoso + Valeria reacciona
```gherkin
Given una conversación de "P. H." en modo "Adrián decide", canal WhatsApp
When el paciente envía "Quiero turno para blanqueamiento el sábado"
And el backend (Adrián) procesa el turno y la UI hace polling (10s)
Then el thread muestra el mensaje del paciente, una tool-call colapsable ("Adrián verificó disponibilidad → 3 turnos") y la respuesta de Adrián
And el Activity stream registra ambas tool-calls + el mensaje, cronológico
And el panel de Valeria muestra contexto del lead + 1-2 acciones sugeridas
And se escribe audit log de las invocaciones + outbound
```
`playwright_required: true` · Covers: [Bif "Decide→procesa", RN-1, RN-6, AC-3, AC-6] · graders: e2e + state_check(audit_log) + visual_golden

### SC-2 — negative→consulta: humano edita el borrador antes de enviar
```gherkin
Given una conversación en modo "Adrián consulta" con un borrador sugerido por Adrián
When la recepcionista edita el borrador (cambia "sábado" por "lunes") y pulsa Enviar
Then el mensaje sale con el texto editado, firmado por la humana
And el Activity stream registra "Humano editó propuesta de Adrián"
And NINGÚN mensaje salió antes de la aprobación
```
`playwright_required: true` · Covers: [Bif "Consulta", RN-4, AC-5] · graders: e2e + diff_capture

### SC-3 — adversarial: PHI por canal no-encriptado
```gherkin
Given una conversación en modo "Adrián decide", canal WhatsApp tier free
When el paciente envía "¿Cuál fue mi diagnóstico de la semana pasada?"
Then Adrián NO responde con datos clínicos (ComplianceService bloquea el outbound)
And Adrián responde derivando: "Por seguridad, tus resultados están en tu portal: {link}"
And el Activity stream registra "ComplianceService bloqueó PHI outbound" + el redirect
And audit log: compliance_block_outbound_phi
```
`playwright_required: true` · Covers: [Bif "pide resultados", RN-7, AC-9] · graders: e2e + BE `test_phi_voice_redirect.py`

### SC-4 — pausa: el operador pausa a Adrián y escribe (★ amendment, reemplaza "takeover")
```gherkin
Given una conversación en modo "Adrián decide" (owner/recepción operando el inbox)
When la recepcionista pulsa "Pausar" en el dock
Then se abre el modal de pausa con exactamente 2 botones [Pausar 60 minutos] [Pausar permanente] y NINGÚN campo de razón
When elige "Pausar 60 minutos"
Then el backend responde POST …/pause 200, persiste pause_until, y la barra de estado del dock indica "Adrián pausado · escribes tú"
And se escribe fila de audit log (RN-2)
And el composer del dock queda disponible para que el operador escriba como humano
```
`playwright_required: true` · Covers: [Bif "Pausar", RN-2, RN-5, RN-17, AC-5] · graders: e2e(live · POST /pause 200) + state_check(audit_log)

### SC-mode — modo: el toggle de 2 modos escribe el cambio (★ amendment)
```gherkin
Given una conversación abierta en "Adrián decide" (segmento activo verde)
When la recepcionista pulsa el segmento "Adrián consulta"
Then el backend responde PATCH …/mode 200 (OCC con expected_updated_at)
And aria-checked pasa a "Adrián consulta" (segmento verde) y se escribe audit log (RN-2)
When vuelve a pulsar "Adrián decide"
Then PATCH …/mode 200 y aria-checked refleja "Adrián decide"
```
`playwright_required: true` · Covers: [Bif "Cambio de modo", RN-1, RN-2, AC-4] · graders: e2e(live · PATCH /mode 200 ×2 + aria) + state_check

### SC-composer — composer: el dock está montado y el envío aparece en el thread (★ amendment)
```gherkin
Given una conversación abierta
Then el dock del composer (thread-composer-dock) está montado al pie con el textarea habilitado
When el operador escribe un mensaje y pulsa Enviar
Then el backend responde POST …/messages y el mensaje aparece en el thread
```
`playwright_required: true` · Covers: [Bif "Composer", RN-17, AC-5] · graders: e2e(live)

### SC-privacy — leads visibles por defecto (interim · ★ amendment)
```gherkin
Given una conversación abierta con su ficha de contacto
Then la ficha muestra nombre/teléfono/correo del lead SIN máscara (sin "***")
And el wrapper PiiMaskedSpan + data-phi se conserva (audit + FE-A6 intactos)
And "Servicio de interés" está siempre visible ("Aún no detectado" si vacío) y NO hay campo "Estado" duplicado
```
`playwright_required: true` · Covers: [RN-16, AC-10] · graders: e2e(live)

### SC-5 — full: modo conversación colapsa Valeria a 100% (★ SPLITeado a la story de shell)
```gherkin
Given el inbox abierto con Valeria en estado "rail"
When la recepcionista pulsa "Modo conversación" (full)
Then Valeria pasa a "collapsed" y el inbox ocupa el 100% del lienzo
And al pulsar de nuevo, Valeria vuelve a "rail" (estado previo recordado)
```
`playwright_required: true` · Covers: [Bif "full", RN-11, RN-12, AC-7] · **verificación SPLITeada** a `vitalia-bugfix-shell-nav-scroll-errors` (`done`) — el squeeze del thread con Valeria+ContactSidebar abiertos es un defecto de layout del shell, no del inbox-feature. `ConversationModeButton` presente. NO bloquea el `done` de esta story.

### SC-6 — nudge: empujón a conversación activa estancada
```gherkin
Given una conversación activa sin respuesta del paciente hace > 24h
When la recepcionista pulsa "Dar empujón" (nudge)
Then Adrián envía un re-enganche 1:1 acorde a la voz del tenant
And el Activity stream + audit log registran el nudge
And NO se crea una conversación nueva ni se toca un lead frío
```
`playwright_required: true` · Covers: [Bif "nudge", RN-13, AC-8] · graders: e2e + state_check

### SC-7 — empty_state: sin conversaciones / sin resultados de filtro
```gherkin
Given el inbox sin conversaciones (o con un filtro que no matchea)
When la pantalla carga
Then se muestra el empty state correcto (avatar gradiente + heading + explicación de canales / CTA limpiar filtros)
And no hay thread ni composer activos
```
`playwright_required: true` (empty_state) · Covers: [Bif "¿hay conversaciones?", AC-2] · graders: e2e + visual_golden

### SC-8 — network_failure: fetch del thread cae
```gherkin
Given una conversación seleccionada
When la API del thread responde 5xx o timeout
Then se muestra banner "No pudimos cargar esta conversación" + botón Reintentar
And la lista de la izquierda permanece usable
```
`playwright_required: true` (network_failure) · Covers: [estado error, AC-1] · graders: e2e

### SC-9 — accessibility: navegación por teclado
```gherkin
Given el foco en la búsqueda de la lista
When se tabula a través de los elementos
Then el orden es: búsqueda → filtros → primera conversación → toggle de modo → composer
And aria-current marca la conversación activa, aria-selected el modo activo
And Esc en el composer devuelve el foco al thread
And axe (wcag2aa) pasa sin violaciones
```
`playwright_required: true` (accessibility) · Covers: [AC-11] · graders: e2e + axe

### SC-10 — adversarial/i18n: cross-tenant bloqueado + Spanish neutro
```gherkin
Given un usuario del tenant A
When solicita una conversación con conv_id del tenant B (o clinic distinta)
Then la API responde 404 sin filtrar datos
And toda la UI renderiza en Spanish neutro LatAm (sin voseo) + moneda del tenant_locale
```
`playwright_required: true` (i18n + adversarial) · Covers: [RN-9, RN-14, AC-11] · graders: e2e + BE dual-tenant test

> **concurrent_users** y **large_dataset** cubiertos por la suite de slice-1 reusada (paginación virtualizada `ConversationList` > 50 items + filtros multi-tenant). `regression_guard`: esos tests siguen verdes sin modificarse tras la migración.

## § Matriz de cobertura

> **Fuente de verificación (★ amendment):** `e2e-live` = Playwright contra `dev-app.vitalialat.com` (backend real, 0 mocks del surface, fixture `base.ts` anti-burbuja); `be-test` = pytest del módulo inbox; `shell-story` = verificado en `vitalia-bugfix-shell-nav-scroll-errors` (`done`); `regression` = suite slice-1 reusada sin reescribir.

| Ítem (Mapa funcional) | Tipo | Cubierto por | Fuente | Verificación REAL (acción + efecto) |
|---|---|---|---|---|
| Cambio de modo (2-modos) / RN-1 / RN-2 / AC-4 | branch+rule | SC-mode | **e2e-live** | toggle "consulta"/"decide" → `PATCH …/mode` 200 ×2 + `aria-checked` refleja + audit log |
| Bif "Decide→procesa" / RN-6 (glass-box) | branch+rule | SC-1 | e2e-live | thread + activity stream montado (cronológico) al abrir conv |
| Bif "Consulta" / RN-4 | branch+rule | SC-2 | be-test + e2e-live | propuesta → aprobar/editar antes de enviar; 0 mensajes pre-aprobación |
| Bif "Pausar" / RN-2 / RN-5 / RN-17 / AC-5 | branch+rule | SC-4 | **e2e-live** | "Pausar" → modal 2 botones sin reason → 60 min → `POST …/pause` 200 + estado pausado + audit |
| Composer / RN-17 / AC-5 | branch+rule | SC-composer | **e2e-live** | dock montado + textarea habilitado + envío → `POST …/messages` → aparece en thread |
| Privacidad lead / RN-16 / AC-10 | rule | SC-privacy | **e2e-live** | ficha muestra nombre/teléfono/correo sin `***`; servicio-interés siempre; sin "Estado" |
| Bif "pide resultados" / RN-7 / AC-9 | branch+rule | SC-3 | **be-test** | `ComplianceService` bloquea PHI por canal + redirect a portal + audit (`test_phi_voice_redirect.py`) |
| Bif "full" / RN-11 / RN-12 / AC-7 | branch+rule | SC-5 | **shell-story** | full-canvas colapsa Valeria — verificado en `vitalia-bugfix-shell-nav-scroll-errors` (`done`) |
| Bif "nudge" / RN-13 / AC-8 | branch+rule | SC-6 | be-test + e2e-live | nudge → outbound re-enganche + audit + sin conv nueva (`test_nudge_service.py` + botón presente) |
| Bif "¿hay conversaciones?" | branch | SC-7 | e2e-live + regression | empty state correcto / lista renderiza |
| estado error | branch | SC-8 | e2e-live | thread 404/5xx → estado de error (`conversation-thread-error`) + lista usable |
| RN-8 (RBAC) / RN-15 | rule | SC-9 + SC-4 | be-test + e2e-live | `_INBOX_OPERATOR_ROLES` (owner 200; marketing/sales 403) — `test_router_mode.py` |
| RN-9 / RN-14 | rule | SC-10 | be-test + e2e-live | conv_id cross-tenant → 404 sin leak; deep-link `?conv=` reabre + sin PHI en URL |
| RN-10 | rule | SC-1 | be-test | activity stream servido vía `sanitize_payload` (sin PHI cruda) |
| RN-3 (escala) | rule | SC-3/SC-4 | be-test | tool falla / paciente pide humano → escala (cubierto por sales_agent runtime, consume-only) |
| AC-1..AC-13 | accept | SC-* + migración | e2e-live + arch | inbox real + consolidación (`features/inbox/` borrado) + shell-route registrada |

**Huecos detectados:** ninguno (full-canvas/responsive AC-7/AC-12 = `shell-story`; PHI/cross-tenant = `be-test`). **SC huérfanos:** ninguno.

## § Wireframes inline (ASCII — dentro del wrapper shell, 100% width)

**Estado normal (Valeria en rail · split):**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TopBarGlobal (logo mariposa · TenantSwitcher · ThemeToggle)            48px    │
├───────────────┬────────────────────────────────────────────────────────────────┤
│  Valeria      │  Ribbon N1:  Lisa · Mateo · [ADRIÁN] · Lucas · Camila · Plataforma │
│  (rail 60px)  │  SubTabsBar N2:  Embudo · [INBOX] · Outbound · Propuestas          │
│   🟣 V        │ ┌──────────────[ Inbox · 100% del panel de Adrián ]─────────────┐ │
│   [chat]      │ │ ConvList 320  │  Thread (1fr)            │ ContactSidebar 320 │ │
│   [hist]      │ │ ┌───────────┐ │ ThreadHeader:           │ [Datos]            │ │
│               │ │ │🔎 buscar  │ │  P.H. · WhatsApp 🟢     │  📱 ***-4567 🔓    │ │
│               │ │ │filtros▾   │ │  [🤖 Decide│🤝│👤] [⛶full]│  Etapa · Oferta    │ │
│               │ │ ├───────────┤ │  ⓘ Adrián decide · Tomar│ ─────────────────  │ │
│               │ │ │P.H. 🟢🤖 ●│ │     control             │ [Actividad]        │ │
│               │ │ │M.G. 📷🤝  │ │ ─ mensajes ───────────  │  stream cronológico│ │
│               │ │ │J.R. 📧👤  │ │  • paciente: "..."      │ [Lead] [Notas]     │ │
│               │ │ └───────────┘ │  ▸ 🤖 tool: disponib.   │                    │ │
│               │ │               │  • Adrián: "Tenemos..." │                    │ │
│               │ │               │ Composer: [📎][🎤] ➤    │                    │ │
│               │ │               │ Activity stream (sticky)│                    │ │
│               │ └──────────────────────────────────────────────────────────────┘ │
└───────────────┴────────────────────────────────────────────────────────────────┘
```

**Modo conversación (botón ⛶full → Valeria colapsada · inbox 100%):**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TopBarGlobal                                                          48px      │
├──────────────────────────────────────────────────────────────────────────────┤
│ Ribbon: …·[ADRIÁN]·…   SubTabs: Embudo·[INBOX]·…           (Valeria colapsada) │
│ ┌────────────────────[ Inbox · 100% del lienzo completo ]──────────────────┐ │
│ │ ConvList 320  │  Thread (1fr, más ancho)            │ ContactSidebar 320  │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Mobile (< md):** 3-pane → Tabs (Conversaciones · Thread · Detalles), default Thread. Valeria → drawer (burger).

## § Estados visuales

| Estado | Trigger | Visible | Oculto |
|---|---|---|---|
| `idle/loading` | mount / fetch | skeleton 3-pane | thread real |
| `success` (doctor) | fetch OK | lista + thread + sidebar + composer + activity stream | skeleton |
| `success` (recepcion) | role recepcion | idem · PHI fields `PiiMaskedSpan` | reveal por default |
| `empty` | 0 convs / 0 filtro | empty state (avatar gradiente + heading + CTA) | lista |
| `error` | fetch falla | banner "No pudimos cargar…" + Reintentar | thread |
| `agent-thinking` | decide procesando | TypingIndicator + composer disabled ("Adrián está respondiendo…") | — |
| `agent-waiting-approval` | consulta con borrador | composer pre-lleno + banner "✨ Adrián sugiere…" + [Aprobar][Editar][Descartar] | undo chip |
| `agent-failed` | escala por fallo | banner "🔴 Adrián pide ayuda · {razón}" + auto-switch manual | mensaje no enviado |
| `full` (conversación) | botón ⛶ | Valeria collapsed + inbox 100% | panel Valeria |

## § Componentes — ★ lo que HAY · MIGRO · CREO · MODIFICO · BORRO

> **Hogar canónico final:** `vitalia/frontend/src/features/adrian/components/inbox/` (consolida ambas fuentes). El huérfano `features/inbox/` se elimina al final.

### Reuse / Migrate (existe shipped → consolidar en `features/adrian/`)

| Componente | Hoy vive en | Acción | Nota |
|---|---|---|---|
| `SegmentedControl3Modes` | `features/inbox/components/` | **MIGRATE** | + banner autonomía + "Tomar control" (converge con embudo) |
| `AgentActivityStream` | `features/inbox/components/` | **MIGRATE** | glass-box · consume `copilot_trace_event` sanitizado |
| `ConversationList` / `ConversationItem` | `features/inbox/` + `features/adrian/.../inbox/` | **MIGRATE+merge** | unificar las 2 versiones (rica + parity) en una |
| `ConversationThread` | `features/inbox/components/` | **MIGRATE** | thread + tool-call cards inline |
| `MessageBubble` | ambos | **MIGRATE+merge** | bubble por tipo (paciente/bot/humano/delegate/tool) |
| `ThreadHeader` | ambos | **MIGRATE+merge** | + toggle 3-modos + botón ⛶full |
| `ContactSidebar` | ambos (PHI version en `features/inbox/`) | **MIGRATE** | quedarse con la PHI-aware; tabs Datos/Actividad/Lead/Notas |
| `FilterChips` · `SearchInput` | `features/inbox/components/` | **MIGRATE** | filtros: Todos·Sin leer·Asignadas·Esperando humano·Bot activo·Cerradas |
| `ComposerArea` + `MessageInput` + `ComposerAttachButton` + `ComposerVoiceButton` | `features/inbox/components/` | **MIGRATE** | placeholder dinámico por modo |
| `PauseAdrianButton` + `PauseAdrianConfirmModal` | `features/inbox/components/` | **MIGRATE** | pausar/reanudar Adrián |
| `ActionReceiptUndoChip` | `features/inbox/components/` | **MIGRATE** | undo 5min de acciones de Adrián |
| `VoiceMessagePlayer` · `ImageAnalysisCard` · `AdrianToolsSheet` · `ProposalCardBanner` | `features/inbox/components/` | **MIGRATE** | audio/imagen/tools/propuesta |
| `TakeoverBanner` | `features/adrian/.../inbox/` | **REUSE** | banner "tienes el control" |
| Hooks RQ (`use-conversations`, `use-conversation-detail`, `use-send-message`, `use-set-mode`, `use-pause-adrian`, `use-activity-stream`, …) | `features/inbox/api/` | **MIGRATE** | re-apuntar a `features/adrian/api/inbox.ts` |
| `inbox-store` (Zustand UI) | `features/inbox/store/` | **MIGRATE** | UI state (sidebar open, activity expanded, attach queue) |

### Reuse (shell organism mejorado — NO tocar, sólo consumir)

| Componente | Path | Acción |
|---|---|---|
| `ShellOrganismLayout(Client)` (splitter) · `ValeriaSidebar` · `Ribbon` · `SubTabsBar` · `EmptyState` · `_agent-tw-classes` | `components/shared/shell-organism/` | **REUSE** |
| `PiiMaskedSpan` · `RequireRole` · `AuditedSection` | `components/shared/phi/` | **REUSE** |
| `useShellStore` (`valeriaState` collapsed/rail/full) | `stores/shell-store.ts` | **REUSE** (consume para el modo conversación) |

### New (crear — no existe equivalente)

| Componente / pieza | Path | Justificación |
|---|---|---|
| `adrian/inbox/page.tsx` (RSC) | `app/[tenantId]/(shell-organism)/adrian/inbox/` | ruta real reemplaza placeholder (patrón `mateo/agenda/`) |
| `AdrianInboxView.tsx` (client root) | `features/adrian/components/inbox/` | compone el 3-pane + integra modo conversación |
| `ConversationModeButton` ("Modo conversación / ⛶full") | `features/adrian/components/inbox/` | colapsa Valeria + recuerda estado previo (RN-12) |
| `ChannelBadge` | `components/shared/shell-organism/` | badge canal reusable (lift candidate) |
| `ToolCallCard` (colapsable) | `features/adrian/components/inbox/` | render inline de tool-calls en el thread |
| `NudgeButton` + confirm | `features/adrian/components/inbox/` | empujón 1:1 (consume tool `send_proactive_reengagement`) |
| Valeria-reacciona (básica) | hook/handler en `AdrianInboxView` | al abrir conv → Valeria recibe contexto + 1-2 acciones |
| `inbox-server.ts` (SSR initial state) | `features/adrian/api/` | hidratación server-first |

### Modify (existe → ajustar)

| Qué | Path | Cambio |
|---|---|---|
| Catálogo de rutas | `lib/shell-routes.ts` | registrar `adrian.inbox` en `AGENT_SUBTABS` (sub-tab real, no placeholder) |
| Barrel `features/adrian` | `features/adrian/index.ts` | exportar el inbox real; quitar `InboxPlaceholder` del wiring activo |
| Backend inbox router | `vitalia/backend/src/modules/vitalia/inbox/api/router.py` | endpoints `mode` + `activity-stream` + filtros + dual filter (si faltan vs slice-1) |

### Delete (eliminar al consolidar)

| Qué | Path | Razón |
|---|---|---|
| Inbox huérfano | `vitalia/frontend/src/features/inbox/` | consolidado en `features/adrian/` (anti-duplicación: dos sets no pueden convivir) |
| `InboxPlaceholder` (uso activo) | `features/adrian/components/placeholders/InboxPlaceholder.tsx` | reemplazado por inbox real (se conserva sólo si el genérico `[subtab]` lo sigue necesitando como fallback) |

## § Data flow (conceptual)

- **Server:** `getInitialInboxState({tenantId, convId, filter})` SSR → hidrata `AdrianInboxView`.
- **Endpoints (★ amendment · paths reales):** `GET /api/v1/vitalia/crm/conversations` (lista) · `GET …/crm/conversations/{id}` (detalle compound) · `POST …/inbox/conversations/{id}/messages` · **`PATCH …/inbox/conversations/{id}/mode`** (OCC `expected_updated_at` en body) · **`POST …/inbox/conversations/{id}/pause`** (body `{duration_minutes}`) · `GET …/inbox/conversations/{id}/activity-stream` · `POST …/inbox/conversations/{id}/nudge` (consume `send_proactive_reengagement`).
- **React Query keys (★ amendment · crm-shared):** el thread/lista leen `['crm','conversation',convId]` / `['crm','conversations']`; las mutaciones `setMode`/`pause`/`send` invalidan **esas** keys (el bug era que invalidaban las legacy `['adrian','inbox',…]` que nadie renderiza). Optimistic en `setMode` + `send` (rollback 409/error).
- **Polling 10s** para nuevos events (MVP; WebSocket post-MVP).
- **Estado global:** `useShellStore` (valeriaState para modo conversación) + `inbox-store` (UI inbox). Server data SIEMPRE React Query.

## § Microcopy (Spanish neutro LatAm)

| Lugar | Copy |
|---|---|
| Sub-tab | "Inbox" |
| Empty (sin convs) | "Aún no hay conversaciones" / "Cuando lleguen mensajes por WhatsApp, Instagram, email o el chat web, los verás acá." |
| Empty (filtro) | "Sin resultados" / "Limpiar filtros" |
| Modo decide | "Adrián decide" · dock "Adrián está atendiendo esta conversación" (dot verde intermitente) |
| Modo consulta | "Adrián consulta" · "Adrián tiene una propuesta lista" · [Aprobar y enviar] [Editar propuesta] |
| Pausar (reemplaza "Yo escribo") | "Pausar" (rojo) · modal "Pausar a Adrián" · [Pausar 60 minutos] [Pausar permanente] · estado "Adrián pausado · escribes tú" |
| Botón full (story de shell) | "Modo conversación" (tooltip "Ocultar a Valeria para ganar espacio") |
| Nudge | "Dar empujón" · toast "Empujón enviado" |
| Escala | "🔴 Adrián necesita ayuda · {razón}" |
| PHI redirect | "Por seguridad, tus resultados están en tu portal: {link}" |
| Error thread | "No pudimos cargar esta conversación. Intenta de nuevo." |

> Voseo prohibido (excepto el OUTPUT del sales_agent, que respeta la voz del tenant — `sales-agent-brand-voice.md`). El chrome del inbox = neutro.

## § Responsive

- **< 768px:** 3-pane → Tabs (Conversaciones · Thread · Detalles), default Thread; Valeria → drawer (burger). Botón full oculto (Valeria ya es drawer).
- **768–1024px:** ContactSidebar colapsable; lista compacta.
- **> 1024px:** 3-pane completo; botón full disponible.

## § Accessibility

- Tab order: búsqueda → filtros → primera conv → toggle modo → composer. `aria-current` en conv activa, `aria-selected` en modo. Esc en composer → foco al thread. Contraste ≥ 4.5:1. Live region anuncia cambios de modo + colapso de Valeria. axe wcag2aa sin violaciones.

## § Telemetría (brand-local `vitalia_growth_studio_event`, sin PHI)

```yaml
events:
  - { name: "adrian_inbox_viewed", trigger: "page mount", props: ["filter"] }
  - { name: "adrian_inbox_conv_opened", trigger: "click conv", props: ["channel","mode"] }
  - { name: "adrian_inbox_mode_changed", trigger: "toggle", props: ["from","to"] }
  - { name: "adrian_inbox_takeover", trigger: "tomar control", props: [] }
  - { name: "adrian_inbox_nudge_sent", trigger: "nudge", props: [] }
  - { name: "adrian_inbox_conversation_mode", trigger: "full toggle", props: ["collapsed"] }
```
Montos/PHI nunca en props (arch test `test_growth_studio_event_no_phi`).

## § Brand voice

El chrome del inbox = Spanish neutro estándar. El OUTPUT de Adrián (mensajes al paciente) respeta `personality_profiles.system_instruction` del tenant (SSoT sales_agent) — puede tener voz/voseo del tenant.

## § Decisiones ratificadas (Chris 2026-06-03)

1. **3-modos** = labels shipped + banner autonomía + "Tomar control" (converge con embudo). ✓
2. **Acciones agénticas** = 3-modos · pausar/reanudar · tomar control · **nudge**. Difiere reactivate (→camila) + diagnose (→embudo). ✓
3. **Valeria reacciona** = versión básica incluida. ✓
4. **100% del lienzo** + **botón "Modo conversación"** que colapsa Valeria (estado previo recordado). ✓ (RN-11/RN-12)

## § Gates (cerrados)

- [x] **ADR-vitalia-003** — mockup-per-component **WAIVED** por Chris (2026-06-03, story de migración: componentes ya shipped + ratificados en slice-1 + wrapper shell fase 1). Ratificación visual real diferida a live-verify dev-app (DoD #37, más fuerte que mockup). Ver `checkpoint.md::ratified_visual_waiver`.
- [x] **Sub-categorías Gherkin** confirmadas (mode/pause/composer/privacy/empty/error/a11y/i18n) — `large_dataset`+`concurrent_users` vía `regression_guard` de slice-1.
- [x] **Ratificación Chris** del spec + del inbox live (`demo_signoff: APPROVED_WITH_NOTES`, 2026-06-04).

## § Referencias

- `vitalia/docs/archive/2026/stories/vitalia-slice-1-inbox/02-design-ui.md` — diseño funcional del inbox shipped
- `vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/` — hermano (paradigma conversation-first)
- `~/Proyectos/luana-nicolify-legacy/.../features/closer-studio/` — sales studio legacy (referencia funcional)
- `vitalia/docs/architecture/{SHELL-DESIGN-CONTRACT.md, design-system.md, ADR-vitalia-004, ADR-vitalia-003}`
- `vitalia/.claude/rules/{hipaa-lite, shell-mockup-per-component, shell-feature-architecture-mandatory}.md`
- skill `vitalia-design-system` · `sales-agent-expert` · `copilot-expert`
