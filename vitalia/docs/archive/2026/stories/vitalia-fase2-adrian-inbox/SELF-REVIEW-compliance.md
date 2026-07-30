# Self-review de cumplimiento — vitalia-fase2-adrian-inbox

> **Pedido de Chris (2026-06-04):** "vuelve a revisar el spec y tú mismo antes de entrar al auditor revisa el cumplimiento."
> Esto es **mi** auto-revisión honesta ANTES del `/auditor`. Confronta `01-spec.md` (AC-1..AC-13 + SC-1..SC-10 + RN-1..RN-14) con el código real + lo verificado LIVE en `dev-app.vitalialat.com`.
>
> **Veredicto: NO está listo para `/auditor`.** Mi build autónomo marcó `developed` en falso. La LISTA funciona; **todo lo que sigue al "clic en una conversación" (thread, modos, tools, activity, contacto, nudge, compliance) está sin verificar, y 3 caminos están ROTOS.**

## Cómo verifiqué

- Lectura de código (FE `features/adrian/components/inbox/` + BE `inbox/` + `crm/api/router.py` + `inbox_orchestrator.py`).
- Estado LIVE confirmado previamente en dev-app: la **lista** renderiza 2 conversaciones reales con nombres (Carlos Ramírez Ortega · Persistencia Verificada).
- **NO** pude ejercer el thread live: crashea al abrir (ver AC-3).

## Matriz AC (spec § Criterios de aceptación)

| AC | Qué pide | Estado | Evidencia / causa raíz |
|---|---|---|---|
| **AC-1** | Ruta `adrian/inbox` renderiza inbox real al 100% | ✅ **VERIFICADO LIVE** | Lista renderiza, layout flex 100% (fix v3→flex). Ruta registrada en `agent-catalog.ts:298`. |
| **AC-2** | Lista cross-canal + filtros + búsqueda + badges canal/modo + no-leído | 🟡 **PARCIAL-VERIFICADO** | Lista + channel badge + stage + help-flag + media-badge **verificados live** (2 convs). Filtros/búsqueda: código presente, **no ejercidos uno por uno**. |
| **AC-3** | Clic conv → thread carga + `?conv={id}` persiste + Valeria reacciona | ❌ **ROTO** | (1) `get_conversation_detail` devuelve `ConversationListItem` lean; el FE espera el compound `ConversationDetail` → `detail.messages` es `undefined` → `InboxThread` crashea en `detail.messages.length`. **El endpoint compound NUNCA se cableó** (los tickets asumieron "shipped 90%"; el orquestador `InboxOrchestrator` que lo arma no está conectado a ningún endpoint). (2) URL usa `?lead=` pero RN-14/AC-3 dicen `?conv={id}`. (3) `useValeriaReaccion` existe pero nunca dispara (el thread no abre). |
| **AC-4** | Toggle 3-modos cambia `agent_mode` + audit log; banner autonomía + "Tomar control" en `decide` | 🟠 **CÓDIGO PRESENTE · SIN VERIFICAR** | `ModeToggle` + `set_conversation_mode` (PATCH `/mode`, OCC) + `useModeToggle` existen. Banner/"Tomar control" sin confirmar en `ThreadHeader`. **No ejercido live** (thread no abre). |
| **AC-5** | Composer respeta modo (envía manual / draft-aprobable consulta / silenciado decide) | 🟠 **CÓDIGO PRESENTE · SIN VERIFICAR** | Composer + endpoint `/messages` presentes. Lógica de modo en composer **sin verificar live**. |
| **AC-6** | Tool-calls inline colapsables + Activity stream cronológico | 🟠 **CÓDIGO PRESENTE · SIN VERIFICAR** | `ToolCallCard` + `ActivityStream` (FE) + `ActivityEventService` (BE) presentes. **Sin verificar** (thread no abre · sin datos de tool-calls sembrados). |
| **AC-7** | Botón "Modo conversación" colapsa Valeria → 100% → restaura previo | 🟠 **CÓDIGO PRESENTE · SIN VERIFICAR LIVE** | `ConversationModeButton` consume `useShellStore` (RN-12 recuerda previo). **No ejercido live.** |
| **AC-8** | Nudge envía re-enganche 1:1 + Activity + audit | 🟠 **CÓDIGO PRESENTE · SIN VERIFICAR** | `NudgeButton` + `nudge_conversation` (POST `/nudge`) + `nudge_service.py` presentes. **No ejercido live.** |
| **AC-9** | ComplianceService bloquea PHI por canal no-encriptado + deriva a portal | ❌ **NO ENFORCED** | `phi_channel_policy.py` + tests existen (T-1 creó los archivos), **PERO el DI del router sigue inyectando `_NoOpComplianceService()`** (`router.py:266` y `:311`). La política existe pero **no está cableada en runtime** → outbound PHI NO se bloquea. T-1 quedó a medias. |
| **AC-10** | ContactSidebar identidad enmascarada + RBAC + tabs | ❌ **WIRING ROTO** | `ContactSidebar` (con `PiiMaskedSpan`+`RequireRole`) existe, pero `AdrianInboxView` le pasa `leadId={resolvedConvId}` + `patientId: resolvedConvId` (= el **id de conversación**, no el lead) → fetch del contacto incorrecto. |
| **AC-11** | Cross-tenant bloqueado (dual filter) + axe + Spanish neutro | 🟡 **PARCIAL** | Dual filter `tenant_id`+`clinic_id` presente en repos (cross-tenant → 404). **axe sin correr.** Spanish neutro OK en copy. |
| **AC-12** | Mobile: 3-pane colapsa a tabs (Conv·Thread·Detalles); Valeria a drawer | 🟠 **PARCIAL** | Fallback mobile presente pero es **single-panel** (thread O lista), **no las 3 tabs** que pide el spec. Valeria-drawer sin verificar. |
| **AC-13** | `features/inbox/` huérfano consolidado + eliminado; `adrian.inbox` en shell-routes | ✅ **VERIFICADO** | `features/inbox/` borrado (T-4). `adrian.inbox` registrado (`agent-catalog.ts:298`). |

## Matriz SC (spec § Gherkin · todos `playwright_required: true`)

| SC | Cubre | Estado e2e honesto |
|---|---|---|
| SC-1 happy (decide + tool-call + Valeria) | AC-3/6 | ❌ **SIN e2e real** (T-6 no hecho; tests existentes mockean el backend = falso verde, prohibido DoD #37) |
| SC-2 consulta (humano edita borrador) | AC-5 | ❌ sin e2e real |
| SC-3 adversarial (PHI no-encriptado) | AC-9 | ❌ sin e2e real · **+ compliance NoOp (no enforced)** |
| SC-4 edge (cambio modo concurrente, OCC) | RN-2/5 | ❌ sin e2e real |
| SC-5 full (colapsa Valeria 100%) | AC-7 | ❌ sin e2e real |
| SC-6 nudge | AC-8 | ❌ sin e2e real |
| SC-7 empty_state | AC-2 | 🟡 empty state **verificado live manual** (RBAC empty render limpio), sin e2e |
| SC-8 network_failure (thread cae) | AC-1 | ❌ sin e2e real |
| SC-9 a11y (teclado + axe) | AC-11 | ❌ sin e2e/axe real |
| SC-10 adversarial/i18n (cross-tenant + neutro) | RN-9/14 | ❌ sin e2e real (dual filter presente en BE, sin test live) |

**gherkin-matrix Phase D = todo MISSING para verificación live honesta.** Ningún SC tiene e2e contra backend real (sin mock). El gate DoD #37 NO se cumple.

## Lo que SÍ está hecho y verificado (no minimizar)

- T-3 (ruta + registro CONN + ChannelBadge) ✅ live.
- T-4 (consolidación + DELETE huérfano) ✅.
- Lista real cross-canal con nombres descifrados + RBAC operador (owner/recepción) ✅ live.
- 9 bugs live cazados+fixed que los unit-tests mockeados ocultaban (nuqs/path-crm/layout-v4/RBAC/list-stub/conv-shape/leads-path/leads-shape/name-wire).

## Gaps bloqueantes (orden de fix propuesto)

1. **[BLOCKER · AC-3/6] Detail compound endpoint.** Cablear el endpoint de detalle al compound `{conversation, lead, messages, action_receipts, tools_state}` que el FE espera (existe `InboxOrchestrator` que arma conv+messages+activity dual-filtered; falta lead + action_receipts + tools_state + DTO Pydantic + mapeo FE). Sin esto el thread crashea = inbox no-funcional.
2. **[BLOCKER · AC-10] ContactSidebar wiring.** Pasar el `lead_id`/`patient_id` reales (del detail compound), no el conv_id.
3. **[AC-3/RN-14] URL param** `?lead=` → `?conv=` (consistencia spec + deep-link).
4. **[AC-9] Wire compliance DI** NoOp→`PhiChannelPolicy` real en `_get_send_service`/`_get_proactive_service`.
5. **[datos] Seed messages** para las 2 convs sembradas (hoy sin mensajes → thread vacío aun arreglando el endpoint).
6. **[T-6 · DoD #37] e2e reales** (sin mock del backend) de SC-1..SC-10 + axe + visual goldens + demo-script.
7. Verificar LIVE cada AC-4/5/7/8/12 ejerciendo la acción real + leyendo logs.

## Veredicto

**NO listo para `/auditor`.** Estado real: lista funcional + verificada; **núcleo conversacional (thread→modos→tools→activity→contacto→nudge→compliance) sin verificar, con AC-3/AC-9/AC-10 rotos.** El `developed` autónomo fue prematuro. Recomiendo cerrar los blockers 1-5 + live-verify, luego T-6, antes de cualquier handoff.

---

## Progreso post-review (2026-06-04 · misma sesión)

Tras escribir la matriz, cerré los blockers de mayor impacto y verifiqué live en dev-app:

- **[BLOCKER #1 · AC-3/AC-6] RESUELTO + VERIFICADO LIVE.** Creé `ConversationDetailResponse` (compound `conversation+lead+messages+action_receipts+tools_state`) en `crm/application/dto/conversation_detail_dto.py` y cablé `GET /api/v1/crm/conversations/{id}` para armarlo (ConversationRepository + MessageRepository + LeadRepository decrypt). + `seed_inbox_messages.sql` (3+5 mensajes). **Verificado live dev-app:** el thread renderiza — Carlos Ramírez Ortega · WHATSAPP · 3-mode toggle (Adrián decide ✓ / consulta / Yo escribo) · "Pausar Adrián" (take-control) · "Dar empujón" (nudge) · los 3 mensajes. `GET /conversations/{id}` → 200 con payload completo (lead phone/email + messages). **0 console errors** (solo `favicon.ico` 500 pre-existente). El crash `'length'` desapareció.
- **[BLOCKER #2 · AC-10] FIX CODE-COMPLETE · re-verify interrumpido.** `AdrianInboxView` ahora arma el `contact` desde `detail.lead` (vía `useConversationDetail`, RQ dedup — sin request extra) en vez de pasar el conv_id. tsc limpio. La re-verificación live se cortó por **desconexión del Chrome MCP** (requiere touch+hard-reload por stale-bundle HMR). Pendiente confirmar phone/email/name/stage de Carlos en el panel.
- **Sigue PENDIENTE:** AC-9 (wire compliance DI NoOp→`PhiChannelPolicy`), AC-4/5/7/8 live, T-6 (e2e reales + axe + goldens + demo-script), `?lead=`→`?conv=` (cosmético, RN-14 satisfecho: es UUID sin PHI).

**Veredicto sin cambios: NO listo para `/auditor`.** El núcleo (thread) ya funciona live, pero falta compliance real + re-verify del contacto + verificación live del resto + T-6.
