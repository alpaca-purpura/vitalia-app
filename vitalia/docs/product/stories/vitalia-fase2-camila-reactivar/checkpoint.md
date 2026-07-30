---
story_id: vitalia-fase2-camila-reactivar
type: ui-story
agent_owner: camila
map_zone: agentes
map_box: camila
module: reengagement
capability: camila.reactivar
state: idea
architecture_pattern: ADR-vitalia-004
last_modified: 2026-05-30
ratified_by_chris: false
parallel_safe: true
priority: high
estimated_dev_days: 4-5
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-camila-voz                # triggers SSoT alimentan listas dinámicas
    - vitalia-fase2-valeria-pacientes         # cohortes consultan last_visit / nps
blocks_hard: []
blocks_soft: []
reuse_map_summary: "REUSE sales_agent reengagement_tool shipped · REUSE fidelización engine · REUSE F2-S5 outbound campaigns wizard pattern · audience PACIENTES EXISTENTES (no leads — territorio Adrián) · NEW 5 listas dinámicas + recovery flow wizard"
spawned_at: 2026-05-22
next_action: "/po-ux refinar 01-spec.md con wireframes listas + recovery wizard"

# Schema v2 migration (cement 2026-05-27)
release: F7   # release ID · ver releases/
cap_target: camila.reactivar   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F2-S12 vitalia-fase2-camila-reactivar — checkpoint

## Goal

Sub-tab Reactivar de Camila: **audience = pacientes existentes post-revenue** (churn defense · NOT leads pre-paciente que es Adrián territory). 5 listas dinámicas pre-definidas + recovery flow wizard.

5 listas dinámicas:
1. `sin-actividad-60-90-180d` — Pacientes con last_visit > N días
2. `fin-tratamiento-sin-recall` — Treatment marked complete pero no follow-up
3. `mantenimiento-por-vencer` — Treatments recurrentes (cleaning · checkup) próximos
4. `propuesta-sin-firmar` — Propuesta sent > 7d no firma (consume F2-S6 trigger)
5. `detractor-nps-pendiente` — NPS detractor sin plan recuperación activa (consume F2-S11)

## Notas a considerar — diagnóstico fidelización re-engagement (2026-06-18)

> **Contexto, NO mandato.** Inyectado por /pm-vitalia tras diagnóstico LIVE de HB-82 (`docs/process/harness-backlog.md` = SSoT del análisis + los 9 gaps restantes). La story contenedor que originó esto fue BORRADA (Chris, 2026-06-18); el detalle re-engagement vive acá. El refinamiento decide qué tomar; nada acá obliga el diseño. **Regla anti-código-muerto:** lo que el rediseño NO reuse, BORRARLO en la misma story (no dejar el scaffold huérfano acumulándose).

**Notas (cosas que ya existen y conviene mirar antes de refinar):**

- **El motor BE de re-engagement ya está construido, cableado y vivo** — `vitalia/backend/src/modules/vitalia/fidelizacion/` (router `main.py:81`, `prefix=/api/v1/vitalia/fidelizacion`). 10 rutas live (openapi-verificado): `POST /re-engagement/{pause,mark-external,mark-no-continue,manual-call,send-proactive}` + `GET /re-engagement/patterns` + `GET /summary` + `GET /activity-stream` + `POST nps/submit` + `GET nps/summary`. Servicios (`re_engagement_service · manual_call_service · proactive_outbound_service · pause_patient_service · opt_out_service`) + repos + models + 3 workers + DTOs (`application/dtos/re_engagement_dtos.py`).
  - 💡 A considerar: el módulo se llama **`fidelizacion`**, no `reengagement`. Los Deliverables de abajo listan `modules/vitalia/reengagement/...` NEW → posible mirror si se crea aparte. Vale evaluar CONSUMIR `fidelizacion` existente. Lo que falta BE serían las 5 queries de listas dinámicas.

- **Existe un FE de las 5 mutations, pero es scaffold huérfano** (OCULTA — nunca cableado, contrato imaginado): `vitalia/frontend/src/features/fidelizacion/` (FidelizacionLayout + tabs Absence/FollowUp/Maintenance/MultiSession/NPSResumen + ReEngagementCard + ReEngagementContactSidebar + modales PausePatientModal/ManualCallLoggedModal/ConfirmTemplateModal/SuggestSlotsModal + 10 hooks + store + Storybook). Cero ruta/nav lo monta. Cap `fidelizacion.re-engagement` = `planned`; hooks tagueados a cap `patients.nps-tracking` (DEPRECATED). Origen: slice viejo `vitalia-slice-1-fidelizacion`.
  - 💡 A considerar: la IA del scaffold (tabs) ≠ la IA de reactivar (5 listas) → probable rediseño de estructura. Los modales + ReEngagementCard + ContactSidebar podrían ser salvables (wirean las 5 mutations); los 10 hooks tienen URL+body+headers imaginados (candidatos a reemplazar). **El refinamiento decide qué cosechar.**
  - 🧹 **Si NO se reusa:** borrar `features/fidelizacion/` (+ Storybook + store + hooks) en esta story, eliminar la cap deprecada `patients.nps-tracking`, y dropear las entradas de `KNOWN_CONTRACT_GAPS` que correspondan. No dejar el huérfano vivo.

- **Contrato BE real de las 5 mutations** (referencia si se reusan/reconstruyen · todos POST a `…/fidelizacion/re-engagement/`):
  - Headers (los 3, hoy faltan en el scaffold): `X-Clinic-ID` (`useClinicId`) + `X-User-ID` + `X-User-Role` (`useActorHeaders`) — patrón canónico `features/mateo/api/notify.ts`. Sin ellos → 422.
  - Body snake_case, `patient_id`+`clinic_id` SIEMPRE en body (no en path):
    - `pause`: `{patient_id, clinic_id, pause_until(datetime), pause_reason?, paused_by_user_id?}`
    - `mark-external`: `{patient_id, clinic_id, event_id?, comment?, converted_to_appointment_id?, recorded_by_user_id?}`
    - `mark-no-continue`: `{patient_id, clinic_id, event_id?, reason?, recorded_by_user_id?}`
    - `manual-call` (201): `{patient_id, clinic_id, outcome(ReEngagementOutcome), notes_plain?, called_by_user_id(req), converted_to_appointment_id?}`
    - `send-proactive`: `{patient_id, clinic_id, patient_phone, patient_name, template_id, pattern, channel="whatsapp", idempotency_key?, throttle_days}`

- **2 decisiones de diseño (si se construye la pieza)** — recomendación /pm-vitalia, no vinculante:
  1. `manual-call` — outcome de la llamada (reached/voicemail/no_answer) ≠ `ReEngagementOutcome` clínico {sent,responded,rescheduled,declined,not_responsive,opted_out,failed_sending}. Sugerencia: enum telefónico propio `call_result {reached,voicemail,no_answer}` + `call_duration_seconds` + `outcome` clínico OPCIONAL (no sobrecargar el enum clínico — mapearlo es lossy).
  2. `send-proactive` — exige `patient_phone`+`patient_name` (PHI) que el FE no tiene. Sugerencia: que el BE los resuelva por `patient_id`+`clinic_id` (sacar del DTO `ProactiveReminderRequest`; hipaa-lite — no PHI en el wire desde el cliente).

- **Reads de la misma feature huérfana:** `GET summary` (BE `items`/snake vs FE `events`/camel) · `GET activity-stream` · NPS: BE tiene `nps/summary`+`nps/submit`; el FE inventó `nps/responses` (no existe). La lista `detractor-nps-pendiente` consumiría el NPS real (`nps/summary`). Mismo criterio anti-código-muerto: lo que no se use, se borra.

## Anti-objetivos

- NO mezclar con audience leads (Adrián territory · per Punto 1 paradigma 2026-05-21)
- NO duplicar campaign wizard de F2-S5 — REUSE component + adapt audience
- NO implementar custom audience builder (5 dinámicas suficiente MVP · story future para custom)
- NO tocar engine

## Scope verbatim

### § 1 — Page + 5 listas

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/camila/reactivar/page.tsx`:

`<CamilaReactivarView>` con cards row top (cada card = una lista dinámica):
- Card title + ícono
- Count live "23 pacientes"
- "Ver pacientes" CTA → drawer lista paginated

### § 2 — `ListaDinamicaCard`

`vitalia/frontend/src/features/camila/components/reactivar/ListaDinamicaCard.tsx`:

Card UI:
- Header: nombre lista + ícono + count
- Stats tiny (% del total · trend last 30d)
- CTA "Crear campaña recovery" → reusar F2-S5 wizard con audience pre-cargado

### § 3 — Recovery flow wizard

`vitalia/frontend/src/features/camila/components/reactivar/RecoveryWizard.tsx`:

REUSE F2-S5 `NewCampaignWizard` pero:
- Step 1 audience locked (pre-cargado por lista source)
- Step 2 templates específicos recovery (subset filtered):
  - `recall_seis_meses` (HSM utility) — "Hola P. tu última visita fue hace 6m..."
  - `mantenimiento_vence` — "Tu mantenimiento dental vence en 30 días"
  - `propuesta_recordatorio` — "Aún puedes firmar tu propuesta · X días restantes"
  - `detractor_recovery` — "Lamentamos lo que pasó · ¿podemos charlar?"
- Step 3 schedule + opt-out compliance idéntico

### § 4 — Lista drawer detalle

Drawer lista paginated:
- Tabla pacientes (PHI masked)
- Columns: Patient · Last visit · Status (e.g., "fin tratamiento 45d" · "propuesta pending 8d")
- Acción individual: Enviar mensaje · Marcar como contactado · Excluir lista
- Bulk action: "Crear campaña para todos" → wizard

### § 5 — Métricas overview

Header `<ReactivarMetrics>`:
- Total pacientes activos
- Total pacientes inactive (any lista)
- Campaigns recovery activas (M2M)
- Conversion rate recovery (revisits / sent last 30d)

### § 6 — HIPAA-lite voice

Per `hipaa-lite.md`:
- Recovery mensajes NUNCA mencionan diagnóstico · solo "tratamiento" generico
- Channel guards aplican (no PHI por WhatsApp free)

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Page renderiza 5 cards listas dinámicas |
| AC-2 | Counts live per lista |
| AC-3 | Click card → drawer lista paginated |
| AC-4 | Recovery wizard con audience pre-cargado |
| AC-5 | Templates recovery filtered correctly |
| AC-6 | Audit log per campaign create + per send |
| AC-7 | Bulk action "Crear campaña" funciona |
| AC-8 | Métricas header live |
| AC-9 | Visual goldens × 6 (overview · drawer · wizard × 2 themes) |
| AC-10 | a11y axe pass |
| AC-11 | Cross-tenant + opt-out enforce |
| AC-12 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: lista dormant 90d + recovery

**Given:** Tenant tiene 50 pacientes con last_visit > 90d

**When:**
1. Click card "Sin actividad 90d"
2. Drawer lista carga 50 pacientes (paginated 20/page)
3. Click "Crear campaña recovery"
4. Wizard pre-cargado audience=50 · template recall_seis_meses
5. Schedule inmediato · submit

**Then:**
- Campaign created con audience = 50
- Worker queue sends
- Audit log
- Stats card "Sin actividad 90d" update (algunos contacted → excluded)

### Scenario 2 — edge: lista vacía

**Given:** Tenant sin pacientes propuesta-sin-firmar

**When:** Page carga

**Then:**
- Card "Propuesta sin firmar" muestra count 0 · CTA disabled
- Tooltip "Sin pacientes en esta cohorte"

### Scenario 3 — adversarial: bulk action sin permission

**Given:** Role `marketing_assistant` (no campaign create perm)

**When:** Click bulk action

**Then:** UI bloquea button · backend 403 if API hit · audit `unauthorized_attempt`

### Scenario 4 — keyboard-a11y

Tab → traverse cards · Enter → drawer · Esc → cierra. aria-live counts update.

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/camila/reactivar/page.tsx` | MODIFY |
| `vitalia/frontend/src/features/camila/components/reactivar/CamilaReactivarView.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/reactivar/ListaDinamicaCard.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/reactivar/ListaDrawer.tsx` | NEW |
| `vitalia/frontend/src/features/camila/components/reactivar/RecoveryWizard.tsx` | REUSE F2-S5 NewCampaignWizard + adapt audience locked |
| `vitalia/frontend/src/features/camila/components/reactivar/ReactivarMetrics.tsx` | NEW |
| `vitalia/frontend/src/features/camila/api/reactivar.ts` | NEW |
| `vitalia/frontend/src/features/camila/types/lista.types.ts` | NEW |
| `vitalia/backend/src/modules/vitalia/reengagement/api/reactivar_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/reengagement/application/listas_dinamicas_service.py` | NEW (5 queries) |
| `vitalia/frontend/e2e/shell-organism/camila-reactivar-flow.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/reactivar/{view}-{light\|dark}.png` (×6) | NEW |
| `vitalia/backend/tests/modules/vitalia/reengagement/test_listas_queries.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/reengagement/test_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| `core/luana-core-sales-agent` reengagement_tool | Engine reengagement | CONSUME via API |
| Vitalia shipped — fidelización engine | NPS + campaign worker | REUSE |
| F2-S5 `NewCampaignWizard` | Wizard 3-pasos | REUSE 100% + audience locked variant |
| F2-S11 voz triggers | Trigger SSoT alimenta listas | CONSUME via shared signals service |
| F2-S6 propuestas | "propuesta-sin-firmar" cohorte | CONSUME proposal status |
| Shadcn primitives | `Card` · `Drawer` · `Table` · `Tabs` | reuse |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-camila-voz` — triggers SSoT
- `vitalia-fase2-valeria-pacientes` — cohorte queries
- `vitalia-fase2-adrian-propuestas` — propuesta-sin-firmar trigger
- `vitalia-fase2-adrian-outbound` — wizard reused

### Esta historia desbloquea
- ninguna directa (es endpoint operativo)

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Listas dinámicas queries lentas grandes tenants | Media | Medio | Materialized views + refresh background hourly |
| Wizard reuse rompe si F2-S5 cambia | Media | Bajo | Contract test compartido |
| Opt-out gap entre listas y wizard | Baja | Crítico | F2-S5 opt-out filter aplica automatic |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 6
3. Backend tests listas + cross-tenant + opt-out pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `camila.reactivar` registrada

## Próximo paso post-done

- F2-S13 multiplicar consume cohorte promotores

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § camila.reactivar (5 listas dinámicas)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **F2-S5 wizard:** REUSE pattern
