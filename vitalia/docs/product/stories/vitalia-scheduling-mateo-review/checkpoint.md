---
story_id: vitalia-scheduling-mateo-review
type: bugfix                                       # review/rename lite — repro-first, sin diseño nuevo (ADR-011)
architecture_pattern: ADR-vitalia-004
module: scheduling                                 # bucket code:scheduling

release: F2

cap_target: scheduling.mateo-agenda                # destino canónico del rename (hoy el YAML aún es valeria-agenda.yaml)
cap_change_type: fix                               # rename + correctness; refining puede subir a extend si aparece gap de integración
parent_story: null

state: idea
phase_workflow: IDEA
last_artifact: checkpoint.md
last_modified: 2026-06-21
next_action: "BUGFIX repro-first. ✅ FIXED+verified: D9, D2-D6, D7, D13(favicon), D8(rename + cap-doctor SANO). Restan (producto/diseño — esperan visión de Chris): D10 (Pacientes = directorio nuevo) · D11 (Nueva cita: dropdowns médico/servicio) · D12 (vista semana: grilla con eje/leyenda/resumen). Opcional técnico: D1 (alinear DTO BE a camelCase y retirar el shim FE)."
ratified_by_chris: false
spawned_at: 2026-06-21
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: null
autonomous_mode: false

# Zona/caja del mapa (paradigm-arquitectura · derivada de SYSTEM-MAP.yaml)
zone: agentes
box: mateo
functional_area: mateo.agenda
---

# Review — Agenda de Mateo: rename Valeria→Mateo coherente + re-validación contra modelos cambiados

## Intake-handshake (origen: pedido de Chris, 2026-06-21)

Chris notó dos cosas sobre el módulo `scheduling` / la agenda:
1. La capability **`scheduling/valeria-agenda`** "dice Valeria pero es Mateo".
2. Desde que se construyó la agenda (2026-05-27) **cambiaron varios modelos** que impactan
   agendamiento → no está claro si lo desarrollado **sigue vigente**.

### Dónde vive (zona/caja)

ZONA **Agentes** → caja **Mateo** (Operar / Mi Día) → área **`mateo.agenda`**.
Derivado de `vitalia/docs/architecture/SYSTEM-MAP.yaml` (v2.0, 2026-05-30): Valeria pasó a ser
**supervisora transversal** (sidebar, runtime en motor-agentico — NO caja de valor en el Ribbon);
las functional_areas de valor (agenda, bookings, pacientes) **se trasladaron a Mateo**.

### Qué ya existe (prior-art en el intake — no es net-new)

La agenda YA está shipped (`status: live`) y la migración Valeria→Mateo está **~80% hecha en código,
stale en el doc**:

| Superficie | Estado | Detalle |
|---|---|---|
| Ruta app | ✅ **Mateo** | `app/[tenantId]/(shell-organism)/mateo/agenda/` · todos los redirects van a `/{t}/mateo/agenda` |
| Feature dir FE | ✅ **Mateo** | `features/mateo/**` (api, store, hooks, components/agenda) |
| Backend módulo | ✅ neutral | `scheduling/` (no agent-named) |
| SYSTEM-MAP | ✅ **Mateo** | box `mateo` con `functional_areas: [agenda, …]`; Valeria = supervisora |
| `agent_owner` del cap | ✅ **mateo** | + `functional_area: mateo.agenda` |
| **cap id/slug/archivo** | ❌ **Valeria** | `capability_id: vitalia.scheduling.valeria-agenda` · `valeria-agenda.yaml` |
| **dev_preview.route del cap** | ❌ **stale** | dice `/valeria/agenda` — el código sirve `/mateo/agenda` |
| **componente FE** | ❌ **Valeria** | `ValeriaAgendaView.tsx` (+ `.test.tsx`) dentro de `features/mateo/` |
| **mocks de test** | ❌ **stale** | `usePathname → /…/valeria/agenda` en `ValeriaAgendaView.test.tsx`, `AgendaHeader.test.tsx`, `AgendaPresetFilters.test.tsx` |
| **`_code-index.json`** | ❌ **mixto** | casi todo `scheduling.valeria-agenda`, pero `telemetry_router.py → scheduling.mateo-agenda` (dangling: no hay YAML `mateo-agenda`) |
| checkpoints/refs | ❌ **mixto** | el bugfix hermano ya usa `cap_target: scheduling.mateo-agenda` ⇒ `mateo-agenda` es el id **intencionado**; el YAML nunca se renombró |

→ Decisión de ubicación: **NO es net-new**. Es (A) cerrar un rename a medias + (B) review de vigencia.
El rename es **código-acoplado** (renombrar el componente + mocks + regen de índices) ⇒ NO es una
edición de doc suelta: se hace dentro de esta story con el código junto, así pasan los gates
deterministas (cap-doctor / cross_check_3) y se live-verifica. Hacer solo el doc dejaría el cap
desincronizado de `ValeriaAgendaView.tsx`.

## Naturaleza: BUGFIX (repro-first · sin diseño nuevo)

Confirmado con Chris (2026-06-21): **no se crea funcionalidad nueva — se corrige lo construido.**
Bugfix lite (ADR-011): cada defecto nace de un **repro**, se fixea, se **live-verifica** (DoD #37). NO pasa
por `/po-ux` (no hay UI nueva que diseñar) ni por ready-package pesado de `/architect`. Ceremonia de diseño
mínima; rigor de verificación **completo** (es funcional). `cap_change_type: fix`.

## Defectos detectados (repro-first · backlog del bugfix)

Todos salieron de la live-verify contra el stack real tras sembrar data (`seed_demo_activity.py`). La agenda
estaba "verde" por DB vacía + mocks MSW camelCase — con data real, rota end-to-end.

| # | Defecto | Repro | Estado |
|---|---|---|---|
| **D1** | Contrato FE↔BE roto: BE snake_case + enums de engine vs FE camelCase + unions EN → grid en blanco con data real | `GET grid` 200 con 56 slots pero UI vacía (pre-shim); `start_time` vs `startTime` | **mitigado** por shim `normalize-agenda.ts` (band-aid). Fix propio: alinear el DTO BE a camelCase |
| **D2** | `SlotPaymentStatus` NO derivado server-side — BE manda `payment_status` crudo de engine ("succeeded"/"not_initiated"), no el color que el dominio (`slot_payment_status.py`) promete | response `payment_status:"succeeded"` (debería ser pagado/deposito/sin_pago/no_show) | ✅ **FIXED + live-verified** (CASE en grid+detail repo → pagado/deposito/sin_pago/no_show; las 4 estados aparecen) |
| **D3** | `doctor_label: "—"` — no resuelve el nombre del doctor pese a `doctor_id` válido | grid slot `doctor_label:"—"` con doctor real | ✅ **FIXED + live-verified** (JOIN `vitalia_doctors` en grid+detail → "Ana Garcia Mendoza") |
| **D4** | `service_label: "Consulta"` genérico | grid slot `service_label:"Consulta"` | ✅ **FIXED + live-verified** (clinic_map.service_label, populado en seed/create → "Limpieza dental profunda"/"Botox facial"/"Ácido hialurónico") |
| **D5** | `patient_name_masked: "—"` — el masking no produce iniciales (el nombre decrypta OK con la KEK) | decrypt→"María Fernanda López", grid→"—" | ✅ **FIXED + live-verified** (decrypt `pgp_sym_decrypt(:kek)` + `_phi_mask.mask_name` en Python → "M. López"; raw stripped, PHI-safe) |
| **D6** | Balance no refleja pagos — `balance_due_cents` = precio completo aún en pagadas; `balance_paid_cents:null` pese a 72 pagos | appt pagada full → due=80000 paid=null | ✅ **FIXED + live-verified** (balance_due/paid_cents desde `va.amount_pending/paid` → due=0 paid=80000; drawer "Saldo pendiente: MXN 0") |
| **D7** | CANCELLED se muestran en el grid (¿filtrar o mostrar distinto?) | grid semana futura devuelve 8 CANCELLED | ✅ **FIXED + verified** (decisión: cancelada = slot libre → `va.status <> 'CANCELLED'` en el grid; detalle por id sigue accesible; futura 32→24) |
| **D8** | Naming drift Valeria→Mateo: cap `valeria-agenda` (id/slug/archivo) + `ValeriaAgendaView.tsx` + 3 mocks + `dev_preview.route /valeria/agenda` aunque la app sirve `/mateo/agenda` | `capability_id: …valeria-agenda` con `agent_owner: mateo` | ✅ **FIXED + cap-doctor SANO** (33 headers + componente `MateoAgendaView` + mocks + cap `mateo-agenda.yaml` + 6 cross-cap refs + regen índice · 0 deriva; FE 412 + BE scheduling verdes; agent-catalog legacy-test intacto) |
| **D9** 🔴 | **Detalle del turno 500** — clic en cualquier slot → `GET /appointments/{id}` 500. `AppointmentDetailDTO.model_validate` falta `doctor_label` + `payments.0.payment_id` (dict trae `id`) + `payments.0.amount_cents` (trae `amount`). Bloquea detalle→cobrar-saldo→fiscal | drawer → "API error 500"; traceback `agenda_router.py:456` | ✅ **FIXED + live-verified 2026-06-21** |
| **D10** | Sub-tab "Pacientes" = placeholder ("próximamente, Fase 2") — sin directorio de pacientes pese a 28 en DB | `/mateo/pacientes` → "Pacientes — próximamente" | abierto (live-QA) |
| **D11** | "Nueva cita": médico = textbox de UUID a mano · servicio = texto libre · hora de fin manual (debería ser dropdowns + autocalc) | form walk-in: "ID del médico" textbox | abierto (live-QA · UX) |
| **D12** | Vista "Semana" = lista apilada por día, sin eje horario; columnas desbordan; sin leyenda de colores ni resumen del día | screenshot grilla | abierto (live-QA · producto) |
| **D13** | Higiene: `/favicon.ico` 500 (Clerk middleware matcher) · warning `auth() sin clerkMiddleware` · grid 500 transitorio · Valeria chat mock contradice datos ("8 turnos hoy" con día vacío) | console + logs FE | ✅ **FIXED (favicon)** — `public/favicon.ico` (brand ico) → 200; el warning Clerk se va con él (causa: favicon→`[tenantId]`). **Console limpia, 0 errores.** Resto = nits cosméticos (logo aspect-ratio, css-preload) + Valeria chat mock (skeleton F1) → no tocados |

> **Catálogo completo del recorrido live (L1-L22, con evidencia + lectura de producto): `LIVE-QA-2026-06-21.md`.**
> Prioridad de negocio: **D9 primero** (desbloquea cobro/fiscal) → D2-D6/L2-L6 (que la grilla diga la verdad:
> paciente·doctor·servicio·pago) → D10/D11/D12 (directorio + create usable + grilla con eje).

**D8 detalle del rename** (coherencia, código-acoplado): cap `valeria-agenda`→`mateo-agenda` (`capability_id`/`slug`/
archivo vía `make`/resolver — NUNCA hand-author, HB-51 + `user_facing_name` + `dev_preview` + `access` + `scenarios`),
componente `ValeriaAgendaView.tsx`(+`.test.tsx`)→`Mateo…`, mocks `usePathname /valeria/agenda`→`/mateo/agenda`
(⚠️ no romper `agent-catalog.test.ts:272` extractAgentFromPath legacy), regen índices code↔cap, reconciliar dangling
`scheduling.mateo-agenda`, `make cap-doctor` = 0 deriva.

> El **alcance verdadero** (qué deps cambiaron y por qué rompieron) se ancla en los modelos tocados desde 2026-05-27:
> `lisa-doctores delta v3` (recurrencia/vista-mes/occurrences/Google/Doctoralia), `lisa-servicios`, `iam roles-DB`,
> `crm pgcrypto PHI`. Cada defecto se mapea a su causa al confirmar el repro.

## Notas de scope
- Brand-local vitalia (cap doc + `features/mateo` FE + `scheduling` BE). No toca core ni otras marcas.
- Si algún helper de actor-headers requiriera lift a `@luana/*` → escalar `/pm-luana`.
