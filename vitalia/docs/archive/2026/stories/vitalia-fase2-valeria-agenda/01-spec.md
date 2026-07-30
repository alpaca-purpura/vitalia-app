---
story_id: vitalia-fase2-valeria-agenda
brand: vitalia
outcome: vitalia-mvp-ui-foundation
phase: fase-2
type: ui-story
agent_owner: valeria
module: scheduling
capability_target: scheduling/valeria-agenda
state: refining
po_ux_version: 1
ratified_by_chris: false
ratified_visual_by_chris: false                  # gate bloqueante shell-mockup-per-component.md
last_updated: 2026-05-26
sub_categories_coverage:                         # ★ v4.1 gate /po-ux refined
  happy: covered
  negative: covered
  edge: covered
  adversarial: covered
  race_condition: covered
  concurrent_users: covered
  network_failure: covered
  empty_state: covered
  large_dataset: covered
  accessibility: covered
  i18n: covered
---

# F2-S1 — vitalia-fase2-valeria-agenda · 01-spec UNIFICADO

## § Context

### Outcome + por qué

- **Outcome:** `vitalia-mvp-ui-foundation` (contenedor maestro Fase 1 + Fase 2 shell-organism agéntico).
- **Posición journey:** primer sub-tab del agente **Valeria** (control operativo del día). Reemplaza el empty-state F1-S10 con feature real.
- **Valor end-to-end:** Valeria (agendamiento) + Adrián (ventas) + Camila (post-cita) cierran loop **reservas pre-pagadas → cobranza inline → seguimiento NPS**. Sin Agenda Fase 2, el shell agéntico es decorativo.

### Refactor target

Migra capability `vitalia-slice-1-agenda` (mockup HTML existente en `vitalia/docs/archive/2026/stories/vitalia-slice-1-agenda/02-design-ui-mockup.html`, calendar shell + drawer draft). NO se rehacen modelos BE — se consumen `core/luana-core-scheduling/` + bridges brand-local en `vitalia/backend/src/modules/vitalia/scheduling/` (a CREAR — módulo brand-extension nuevo bajo DDD Inside-Out, NO mirror de engine).

### Out-of-scope explícito (anti-creep)

- ❌ Booking público externo (flujo cliente — outcome separado)
- ❌ Editor recurrencias avanzadas (solo recurrencia simple día-de-semana)
- ❌ Google Calendar / iCal sync (F2-S21 `config-conexiones`)
- ❌ Waiting-list feature (parking story)
- ❌ Tocar `core/luana-core-*/` directamente (read-only desde brand)
- ❌ Multi-tenant simultaneous edit (resuelto via tenant switcher hard redirect F1-S3)
- ❌ Editor templates WhatsApp inline (templates predefinidos backend — admin UI vive en F2-S22 `config-avanzado`)

### Service-deps blockers (BE → /dev-team gate)

| Story | State actual | Bloquea |
|---|---|---|
| `vitalia-payment-adapter-mvp` | `refined` | Endpoint `/api/payments/charge` (Stripe/MP/efectivo) |
| `vitalia-fiscal-emission-pe` | `refining` | Endpoint `/api/fiscal/emit` (Nubefact PE — boleta/factura) |

**/architect** puede arrancar (`refined → ready`) sin que estas estén `done`, pero **/dev-team** REFUSE pickup hasta ambas en `developed` mínimo (gate hard documentado en `06-tickets.yaml`).

---

## § Gherkin scenarios (4 base + 7 sub-categorías mandatory)

### SC-1 · happy — cobro saldo end-to-end (★ corazón valor F2-S1)

**Given:**
- Tenant PE `clinica-sonrisa-pe` activo (locale `es-PE`, currency `PEN`)
- Usuario rol `valeria_assistant` autenticado (Clerk session)
- Slot existente: paciente `P. Hernández` (DNI masked `12.***.***`), servicio `Limpieza dental`, saldo pendiente PEN 80, status `🟡 depósito`
- `vitalia-payment-adapter-mvp` shipped + `vitalia-fiscal-emission-pe` shipped
- ComplianceService activo perfil `hipaa_lite`

**When:**
1. Usuario click slot en `WeekCalendar`
2. `AppointmentDrawer` abre (side=right, ancho usuario localStorage o 440px default)
3. Acordeón `Pago / saldo` expandido por default → click `Cobrar saldo` → `CobrarSaldoSubform` aparece inline
4. Selecciona `method=tarjeta`, `emit_invoice=true`, `fiscal_doc_type=boleta` (default tenant PE), `currency=PEN` (tenant default), `notes="cobro normal"`
5. Click `Cobrar PEN 80`

**Then:**
- POST `/api/v1/payments/charge` retorna 200 con `payment_id`
- POST `/api/v1/fiscal/emit` retorna 200 con `boleta_url`
- `<Toast>` success "Cobro PEN 80 + boleta emitida" con link `Ver comprobante` → abre PDF en nueva pestaña
- Slot border-status cambia 🟡 depósito → 🟢 pagado (React Query invalidate `['agenda','grid',{tenantId,view,date}]`)
- `audit_log` row creado: `{user_id, tenant_id, clinic_id, action: 'charge', resource_type: 'appointment_payment', resource_id: <payment_id>, payload_redacted: {amount: 80, method: 'tarjeta', currency: 'PEN'}}`
- NO PHI en log (DNI paciente NO aparece, solo `patient_id` UUID hash)
- Telemetry `charge_succeeded` event emitted (props: tenant_id, clinic_id, payment_method, amount_bucket: '50-100', currency, fiscal_doc_emitted: true)

**playwright_required:** `true`

**Graders:**
- e2e: `vitalia/frontend/e2e/shell-organism/valeria-agenda-cobro.spec.ts`
- visual_state: `e2e/__screenshots__/agenda/drawer-cobrar-saldo-success-light.png`
- backend: `vitalia/backend/tests/modules/vitalia/scheduling/test_drawer_charge_flow.py::test_happy_path_pe_boleta`
- state_check: db `SELECT count(*) FROM audit_log WHERE action='charge' AND resource_id=$payment_id` expect 1
- axe: `wcag2aa` (subform + toast)

---

### SC-2 · negative — payment-adapter caído (503 timeout)

**Given:**
- `vitalia-payment-adapter-mvp` retorna 503 (Stripe API timeout simulado vía MSW mock)
- Slot mismo SC-1 con saldo PEN 80

**When:** Usuario completa subform + click `Cobrar PEN 80`

**Then:**
- `<Alert variant="destructive">` "No pudimos procesar el cobro. Intentalo de nuevo en unos segundos." (Spanish neutro)
- Botón `Reintentar` disponible (re-submit form con misma data)
- NO comprobante fiscal emitido (transacción NO commit — saga abortada antes de POST `/fiscal/emit`)
- Sentry capture sin PHI: `{payment_attempt_id, error_code: 'PAYMENT_ADAPTER_503', tenant_id, clinic_id}` (NO DNI, NO nombre)
- Slot border-status NO cambia
- Telemetry `charge_failed` event (props: error_code, retry_count: 0)

**playwright_required:** `true`

**Graders:**
- e2e: `valeria-agenda-cobro.spec.ts::test_payment_adapter_503`
- visual_state: `e2e/__screenshots__/agenda/drawer-cobrar-saldo-error-light.png`
- backend: `test_drawer_charge_flow.py::test_payment_503_no_fiscal_emit`
- axe: contrast ratio en `<Alert>`

---

### SC-3 · edge — tenant switch durante drawer abierto

**Given:**
- Usuario tiene `AppointmentDrawer` abierto para slot de tenant A (`clinica-sonrisa-pe`)
- Subform `CobrarSaldoSubform` parcialmente llenado (method=tarjeta, no submit)

**When:** Click `TenantSwitcher` (F1-S3) → selecciona tenant B (`aurora-spa-mx`)

**Then:**
- TenantSwitcher dispara **hard redirect** a `/{tenant-B-slug}/valeria/agenda` (per F1-S3 pattern)
- Drawer cierra automático (state local feature reset)
- `localStorage.x-tenant-id` actualizado
- React Query cache invalidado `queryClient.clear()`
- Agenda re-fetchea con tenant B (currency MXN, dates en `America/Mexico_City`)
- NO leak datos tenant A en UI (zero re-render con stale data)
- Form data del subform NO persiste cross-tenant (zustand store local feature reset)

**playwright_required:** `true`

**Graders:**
- e2e: `vitalia/frontend/e2e/shell-organism/valeria-agenda-tenant-switch.spec.ts`
- state_check: localStorage `x-tenant-id` equals tenant B slug post-switch
- visual: dashboard tenant B muestra MXN currency en chips/drawer

---

### SC-4 · adversarial — PHI en URL bloqueado + cross-clinic query bloqueada

**Given:**
- Usuario adversarial autenticado como `staff` de `clinic_A` en tenant `T1`
- Conoce `appointment_id` de `clinic_B` (mismo tenant) via guess UUID

**When:**
1. `GET /{T1}/valeria/agenda?patient_dni=12345678` (PHI en URL)
2. `GET /api/v1/scheduling/appointments/{appointment_id_of_clinic_B}` (cross-clinic query)

**Then:**
- **(1)** Server-side filter ignora `patient_dni` query param (whitelist explícita: `view`, `date`, `preset_filter`, `clinic_id`). Audit log row `suspicious_request` creado SIN contenido DNI. Response agenda completa sin filtro PHI. NO 500. NO leak.
- **(2)** Endpoint aplica **dual filter** `WHERE tenant_id=$T1 AND clinic_id=$clinic_A` per `hipaa-lite.md`. Appointment de `clinic_B` retorna 404 (NO 403 — evita leak existencia). Audit log row `cross_clinic_attempt` creado.

**playwright_required:** `false` (backend tests son suficientes — adversarial flow NO necesita Playwright)

**Graders:**
- backend: `vitalia/backend/tests/modules/vitalia/scheduling/test_phi_url_protection.py`
- backend: `test_dual_filter_clinic_isolation.py`
- arch_fitness: `tests/architecture/test_phi_dual_filter.py` (ya existe per overlay HIPAA)

---

### SC-5 · race_condition — 2 staff cobrando mismo slot simultáneo

**Given:**
- Staff A y Staff B (mismo tenant + clinic) ven slot con saldo PEN 80
- Ambos abren `AppointmentDrawer` para mismo `appointment_id`

**When:**
1. Staff A submit `CobrarSaldoSubform` → POST `/charge` → backend procesa
2. ANTES de que Staff A reciba respuesta, Staff B también submit charge mismo slot

**Then:**
- Backend usa optimistic lock en `appointment.balance_version` (incremented atomic via SQLA `with_for_update()`)
- Staff A request gana (commit primero, returns 200)
- Staff B recibe **409 Conflict** `{error_code: 'BALANCE_ALREADY_CHARGED', latest_state: <slot_state>}`
- FE Staff B: `<Alert>` "Este saldo ya fue cobrado por otro usuario hace unos segundos. Refrescando agenda…" → auto-invalidate React Query + cierra subform
- Audit log SOLO de Staff A `action: 'charge'` (no audit log Staff B porque NO se ejecutó cobro)
- NO double charge cliente (idempotency garantizada backend)

**playwright_required:** `false` (multi-user concurrency es backend integration test + frontend mock)

**Graders:**
- backend: `test_drawer_charge_flow.py::test_concurrent_charge_optimistic_lock`
- vitest: `vitalia/frontend/src/features/valeria/components/agenda/__tests__/CobrarSaldoSubform.test.tsx::test_handles_409_conflict`

---

### SC-6 · concurrent_users — 2 staff misma clínica viewing agenda (polling 30s)

**Given:**
- Staff A viendo `WeekCalendar` (view=semana, polling activo 30s)
- Staff B en otra pestaña/dispositivo cancela un appointment

**When:** Pasan ≥30s (próximo polling tick de Staff A)

**Then:**
- Staff A `useQuery(['agenda','grid',...])` con `refetchInterval=30_000` ejecuta refetch
- Slot del appointment cancelado se re-renderiza con status `Cancelado` (border-color update + tooltip "Cancelado por Staff B · 14:32")
- Indicator header "Actualizado hace 0s" se resetea (mostraba "Actualizado hace 28s" antes del refetch)
- Si Staff A tenía `AppointmentDrawer` abierto para ese mismo slot → drawer permanece pero muestra `<Banner>` "Este turno fue actualizado por otro usuario. ¿Recargar datos?" con botón `Recargar`
- NO interrupción operativa (Staff A puede seguir viendo otros slots)

**playwright_required:** `true`

**Graders:**
- e2e: `valeria-agenda-concurrent-users.spec.ts` (2 contexts Playwright + simulan cambio)
- visual_state: `e2e/__screenshots__/agenda/drawer-stale-banner-light.png`

---

### SC-7 · network_failure — fetch grid timeout

**Given:**
- Backend `/api/v1/scheduling/agenda/grid` simula timeout (10s sin respuesta)
- Usuario en `WeekCalendar`

**When:** Page mount fetch + retry React Query (3 attempts default + exponential backoff)

**Then:**
- Loading skeleton renderiza primeros 5s (`<SkeletonCalendar>` placeholder grid)
- Después de 3 retries fallidos → `<EmptyState variant="error">` "No pudimos cargar tu agenda. Verificá tu conexión." + botón `Reintentar` (manual)
- NO crash blanco
- Botón Reintentar resetea `useQuery` (refetch fresh)
- Sentry capture `{error: 'AGENDA_GRID_TIMEOUT', tenant_id, clinic_id}` sin PHI

**playwright_required:** `true`

**Graders:**
- e2e: `valeria-agenda-network.spec.ts::test_grid_timeout_retry_empty_state`
- visual_state: `e2e/__screenshots__/agenda/empty-state-network-error-light.png`

---

### SC-8 · empty_state — día sin slots

**Given:**
- Tenant + clinic activos
- View=día, fecha=domingo (clinic cerrada, 0 appointments)

**When:** Usuario navega a vista día domingo

**Then:**
- `DayCalendar` renderiza grid horario completo (8:00-22:00) pero VACÍO (sin slots)
- Overlay `<EmptyState>` central: ilustración (Lucide `CalendarOff`) + heading "No hay turnos este día" + body "Tomate un café o creá una cita walk-in." + CTA `+ Crear cita`
- Chips preset siguen activos (usuario puede filtrar otro día)
- NO error, NO loading infinito

**playwright_required:** `true`

**Graders:**
- e2e: `valeria-agenda-empty.spec.ts::test_empty_day_renders_empty_state`
- visual_state: `e2e/__screenshots__/agenda/empty-state-day-light.png`

---

### SC-9 · large_dataset — clinic con 200+ slots/día (virtualización)

**Given:**
- Tenant `mega-clinic-ar` con 240 appointments en single día (clinic con 12 doctores × 20 slots/c)
- View=día

**When:** Usuario navega a vista día

**Then:**
- `DayCalendar` virtualizado con `react-window` (FixedSizeList)
- Render inicial < 100ms (solo slots visibles en viewport, ~15 slots)
- Scroll smooth (60fps medido vía Lighthouse perf)
- View=mes consume endpoint **agregado** `/api/v1/scheduling/agenda/aggregates?month=...` que devuelve `[{date, total_slots, status_breakdown}]` — **NO bulk load** 3000+ slots individuales
- Click día en MonthCalendar navega a DayCalendar (URL params `?view=dia&date=YYYY-MM-DD`)

**playwright_required:** `true`

**Graders:**
- e2e: `valeria-agenda-large-dataset.spec.ts::test_day_240_slots_renders_under_100ms`
- vitest: `AgendaCalendar.test.tsx::test_uses_react_window_for_day_view`
- perf: Lighthouse score `performance ≥ 90` en page agenda con seed 240 slots

---

### SC-10 · accessibility — keyboard nav + screen reader

**Given:** Foco en primer slot del día (`WeekCalendar`, Lunes 9:00)

**When:**
1. `Tab` → siguiente slot (orden visual columnar: Lun9, Lun10, Lun11... → Mar9...)
2. `Enter` → abre `AppointmentDrawer`
3. Focus traps dentro del drawer (Tab cycle: Cerrar → Ver ficha (disabled) → acciones turno → subform fields → footer acciones avanzadas → Cerrar)
4. `Esc` → cierra drawer + devuelve focus al slot trigger
5. `Shift+Tab` desde primer slot → focus pasa al botón `+ Crear cita` (header)

**Then:**
- Cada slot recibe **focus visible** (`focus-visible:ring-2 focus-visible:ring-primary`)
- `<AgendaSlot>` ARIA: `role="button"`, `aria-haspopup="dialog"`, `aria-label="Slot 9:00 Lunes · P. Hernández · Limpieza dental · estado pagado"` (PHI masked, NO DNI completo)
- `<Sheet>` (drawer) ARIA: `role="dialog"`, `aria-modal="true"`, `aria-labelledby="appointment-drawer-title"`, focus trap activo
- `<CobrarSaldoSubform>` inputs todos con `<Label htmlFor>` asociados
- Screen reader anuncia cambios live: `<div aria-live="polite">` para toast notifications
- Contrast ratio ≥ 4.5:1 textos, ≥ 3:1 UI components (verificable axe)

**playwright_required:** `true`

**Graders:**
- e2e: `valeria-agenda-keyboard.spec.ts`
- axe: `wcag2aa` en calendar + drawer + subform (3 checkpoints)

---

### SC-11 · i18n — multi-currency tenant + per-transaction override

**Given:**
- Tenant `clinica-aurora-ar` (default currency ARS)
- Slot con paciente argentino: amount ARS 12.000
- **OTRO** slot mismo tenant con paciente turista USA: `currency_override="USD"` en appointment metadata (amount USD 50)

**When:**
1. Click slot paciente AR → `CobrarSaldoSubform` muestra amount `$ 12.000` (currency=ARS, locale es-AR thousand separator)
2. Click slot paciente turista → subform muestra amount `US$ 50` con `<Select>` currency showing `[ARS (default tenant), USD (override)]` selected USD por default

**Then:**
- Subform `useTenantLocale()` provee tenant default + chequea `appointment.currency_override` para preseed select
- Format: `formatTenantMoney(amount, currency, locale)` from `@/lib/format`
- POST `/charge` body incluye `currency` campo explícito (no infiere)
- Backend audit log `payload_redacted.currency` recordado
- Fiscal emit aplica tax rules per currency country (ARS → IVA AR, USD → exempt o IVA per config tenant)
- Spanish neutro LatAm en labels (NO "Importe", USAR "Monto"; NO "Comprobante", USAR "Comprobante")

**playwright_required:** `true`

**Graders:**
- e2e: `valeria-agenda-i18n.spec.ts::test_currency_per_transaction_override`
- vitest: `CobrarSaldoSubform.test.tsx::test_renders_tenant_default_and_override_currency_select`
- visual: `e2e/__screenshots__/agenda/subform-currency-ars.png` + `subform-currency-usd-override.png`

---

### Sub-categorías N/A (justificadas)

- **prompt_injection** — `not_applicable_reason: "Story es UI standard con form fields tipados (no free-text LLM). Subform `notes` es textarea max 500 chars, sanitizada server-side."`

---

## § Wireframes inline (referencia mockups/)

Mockups HTML obligatorios per `vitalia/.claude/rules/shell-mockup-per-component.md` — ratificados por Chris ANTES de transition `refining → refined`.

**Path:** `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/`

| # | File | Componente | Ratificado |
|---|---|---|---|
| 0 | `agenda-cockpit-grid.html` | TOC navegable + 8 vistas inline (mini-previews) | ⏳ pending |
| 1 | `agenda-day.html` | DayCalendar (timeline 24h × N doctores) con slots realistas LatAm | ⏳ |
| 2 | `agenda-week.html` | WeekCalendar (grid 7d × 9-21h) — vista default | ⏳ |
| 3 | `agenda-month.html` | MonthCalendar (grid mensual con dots-load + click día → dia) | ⏳ |
| 4 | `slot-states-matrix.html` | 4 estados pago × 3 orígenes + 4 interactive states = 16 cells | ⏳ |
| 5 | `appointment-drawer.html` | Drawer abierto (440px ancho) con 5 acordeones (Turno+Pago expandidos · resto collapsed) | ⏳ |
| 6 | `cobrar-saldo-subform.html` | Subform expandido con 4 currency variants (PEN · ARS · USD override · MXN) + states loading/success/error | ⏳ |
| 7 | `preset-filters.html` | 5 chips single-select + estado activo + hover | ⏳ |
| 8 | `crear-cita-dropdown.html` | DropdownMenu 3 opciones (Walk-in · Teléfono · Desde paciente — autocomplete) | ⏳ |
| 9 | `mobile-drawer-fullscreen.html` | Mobile <768px: DayCalendar + bottom-sheet drawer 95vh + chip carousel + FAB Crear cita | ⏳ |

### ASCII layout overview (desktop semana default)

```
┌──────────────────────────────────────────────────────────────────────┐
│ TopBar (F1-S2) · TenantSwitcher (F1-S3) · ThemeToggle               │
├──────────────────────────────────────────────────────────────────────┤
│ Ribbon (F1-S7) · [Valeria · Adrián · Lisa · Camila · Lucas · ⚙]    │
├──────────────────────────────────────────────────────────────────────┤
│ SubTabsBar (F1-S8) · [Agenda · Pacientes · Mensajes · Reportes]    │
├──────────────────────────────────────────────────────────────────────┤
│ AgendaHeader · [Día|Semana|Mes] · DatePicker · "Actualizado hace 12s"·🔄│
├──────────────────────────────────────────────────────────────────────┤
│ AgendaPresetFilters · [📅 Hoy] [⏰ Por confirmar] [↩️ Re-agendar] [🚫 No-shows] [💰 Saldos pendientes]│
├──────────────────────────────────────────────────────────────────────┤
│         ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐                 │
│  09:00  │ Lun │ Mar │ Mié │ Jue │ Vie │ Sáb │ Dom │  + Crear cita ▾│
│  10:00  │ 🟢  │     │ 🟡  │ 🔴  │     │     │     │                 │
│  11:00  │     │ ⚫   │     │ 🟢  │ 🟡  │     │     │                 │
│  12:00  │ 🟢👤│     │     │     │     │     │     │                 │
│  ...    │     │     │     │     │     │     │     │                 │
│  21:00  │     │     │     │     │     │     │     │                 │
│         └─────┴─────┴─────┴─────┴─────┴─────┴─────┘                 │
└──────────────────────────────────────────────────────────────────────┘
        │
        ▼  click slot
┌───────────────────────────┐
│ AppointmentDrawer (440px)│
│ ┌─────────────────────┐  │
│ │ [Avatar] P.Hernández│✕│
│ │ DNI: 12.***.***     │  │
│ │ [Ver ficha ▸ próx.] │  │  ← disabled tooltip
│ ├─────────────────────┤  │
│ │ ▼ TURNO             │  │
│ │ Lun 26 · 09:00-09:30│  │
│ │ Dr. García · Limpieza│ │
│ │ [Reagendar][Cancelar│  │  ← Cancelar+Noshow → Dialog
│ │ [✓Completado][🚫No-show│ │
│ ├─────────────────────┤  │
│ │ ▼ PAGO / SALDO      │  │
│ │ 🟡 Depósito PEN 40/120│ │
│ │ Saldo: PEN 80       │  │
│ │ [Cobrar saldo ▾]    │  │
│ │   └─ Subform inline │  │
│ ├─────────────────────┤  │
│ │ ▸ HISTÓRICO PAGOS   │  │  ← collapsed default
│ ├─────────────────────┤  │
│ │ ▸ NOTAS INTERNAS    │  │  ← collapsed
│ ├─────────────────────┤  │
│ │ ▸ ACCIONES AVANZADAS│  │  ← collapsed
│ └─────────────────────┘  │
└───────────────────────────┘
```

---

## § Estados visuales (por screen)

### AgendaCalendar (día/semana/mes)

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `idle` | Page mount pre-fetch | `<SkeletonCalendar>` placeholder grid | Slots, drawer |
| `loading` | Refetch (cada 30s) | Slots actuales + spinner mini header | — |
| `success` | Data fetched | Slots + chips filters + crear-cita button | Skeleton, empty |
| `success_filtered` | Chip preset active | Slots filtrados + chip activo highlighted | Slots fuera filtro |
| `empty_day` | 0 slots día | `<EmptyState variant="empty">` con CTA crear cita | Slots |
| `empty_filtered` | Chip filter retorna 0 | `<EmptyState variant="filtered">` "Ningún turno coincide" + botón Limpiar filtros | Slots |
| `error` | Fetch falló (3 retries) | `<EmptyState variant="error">` con `Reintentar` | Slots, chips |

### AppointmentDrawer

| Estado | Trigger | Visibles | Ocultos |
|---|---|---|---|
| `closed` | Default | — | Drawer |
| `open_loading` | Click slot + fetch detail | Drawer + skeleton sections | Acordeones |
| `open_loaded` | Detail fetched | Header + Turno + Pago expandidos + 3 acordeones collapsed | Skeleton |
| `open_stale` | Polling detectó cambio remoto | Banner amarillo "Actualizado por otro usuario" + botón Recargar | — |
| `closing` | Esc o click X | Drawer animation slide-out | — |

### CobrarSaldoSubform

| Estado | Trigger | Visibles | Ocultos |
|---|---|---|---|
| `collapsed` | Default within Pago section | Botón `Cobrar saldo ▾` | Form fields |
| `expanded` | Click botón | Form fields (amount/method/emit_invoice/doc_type/notes) + submit | — |
| `submitting` | Click submit | Form disabled + spinner btn "Procesando…" | — |
| `success` | Charge + emit OK | Toast green + slot status update + form reset/collapse | — |
| `error_payment` | Charge fail | `<Alert variant="destructive">` + Reintentar | Form re-enabled |
| `error_fiscal` | Charge OK pero emit fail | `<Alert variant="warning">` "Cobro OK, comprobante pendiente — reintentar emisión" + botón `Reintentar emisión` | — |
| `conflict_409` | Concurrent charge same slot | `<Alert>` "Ya fue cobrado…" + auto-collapse subform + invalidate query | — |

---

## § Componentes (reuse > new)

### Shadcn primitives (instalar pendientes)

| Componente | Status | Path post-install |
|---|---|---|
| `Sheet` | NEW install | `vitalia/frontend/src/components/ui/sheet.tsx` |
| `Accordion` | NEW install | `vitalia/frontend/src/components/ui/accordion.tsx` |
| `Calendar` (date picker) | NEW install | `vitalia/frontend/src/components/ui/calendar.tsx` |
| `Popover` | NEW install | `vitalia/frontend/src/components/ui/popover.tsx` |
| `Select` | NEW install | `vitalia/frontend/src/components/ui/select.tsx` |
| `Form` (RHF wrapper) | NEW install | `vitalia/frontend/src/components/ui/form.tsx` |
| `Sonner` (toast) | NEW install | `vitalia/frontend/src/components/ui/sonner.tsx` |
| `Button` · `Badge` · `Avatar` · `Alert` · `Dialog` · `DropdownMenu` · `Input` · `Textarea` · `Tabs` · `ScrollArea` · `Separator` · `Skeleton` · `Tooltip` | ✅ shipped F1 | `vitalia/frontend/src/components/ui/` |

Comando install batch:
```bash
cd vitalia/frontend && npx shadcn@latest add sheet accordion calendar popover select form sonner
```

### Componentes NEW por feature

| Componente | Path | Justificación NEW |
|---|---|---|
| `ValeriaAgendaView` | `vitalia/frontend/src/features/valeria/components/agenda/ValeriaAgendaView.tsx` | Feature root client. Wrapper compositor — no existe equivalente |
| `AgendaCalendar` | `.../agenda/AgendaCalendar.tsx` | Calendar shell — refactor desde slice-1-agenda mockup |
| `DayCalendar` | `.../agenda/DayCalendar.tsx` | Variante día con react-window |
| `WeekCalendar` | `.../agenda/WeekCalendar.tsx` | Variante semana grid 7×13 |
| `MonthCalendar` | `.../agenda/MonthCalendar.tsx` | Variante mes con dots agregados |
| `AgendaSlot` | `.../agenda/AgendaSlot.tsx` | Molécula slot — Design Contract § 3.2 (border-status + origin-badge) |
| `AppointmentDrawer` | `.../agenda/AppointmentDrawer.tsx` | Sheet wrapper con 5 acordeones — pattern Vitalia local |
| `CobrarSaldoSubform` | `.../agenda/CobrarSaldoSubform.tsx` | Subform inline RHF + Zod. ★ corazón valor F2-S1 |
| `AgendaPresetFilters` | `.../agenda/AgendaPresetFilters.tsx` | Chip row 5 filtros single-select |
| `CrearCitaButton` | `.../agenda/CrearCitaButton.tsx` | DropdownMenu 3 opciones + form modal |
| `CrearCitaForm` | `.../agenda/CrearCitaForm.tsx` | Form unificado walk-in/teléfono/desde-paciente |
| `PatientAutocomplete` | `.../agenda/PatientAutocomplete.tsx` | Combobox Shadcn + search debounced `/api/crm/patients?q=` (PHI masked results) |
| `AgendaHeader` | `.../agenda/AgendaHeader.tsx` | View-toggle + date-picker + freshness indicator |
| `FreshnessIndicator` | `.../agenda/FreshnessIndicator.tsx` | "Actualizado hace Xs" + botón refresh manual |
| `MobileBottomSheet` | `.../agenda/MobileBottomSheet.tsx` | Sheet side=bottom 95vh wrapper para mobile |
| `AppointmentDrawerSkeleton` | `.../agenda/AppointmentDrawerSkeleton.tsx` | Skeleton placeholder durante fetch detail |
| `SkeletonCalendar` | `.../agenda/SkeletonCalendar.tsx` | Skeleton grid pre-fetch |

### Componentes REUSE de F1

| Componente | Path | Reutilización |
|---|---|---|
| `EmptyState` | `vitalia/frontend/src/components/shared/shell-organism/EmptyState.tsx` | 3 variants: empty/error/filtered |
| `SubTabHeader` | `vitalia/frontend/src/components/shared/shell-organism/SubTabHeader.tsx` | Header agenda inicial |
| `StatusDot` | `vitalia/frontend/src/components/shared/shell-organism/StatusDot.tsx` | Indicators origen/status |
| `TogglePill` | `vitalia/frontend/src/components/shared/shell-organism/TogglePill.tsx` | View toggle día/semana/mes |
| `PHIMaskedText` | `vitalia/frontend/src/components/shared/phi/PHIMaskedText.tsx` | Render nombre+DNI masked en slots + drawer |

### Hooks NEW

| Hook | Path | Responsabilidad |
|---|---|---|
| `useAgendaGrid` | `.../valeria/api/agenda.ts` | React Query grid + filters + polling 30s |
| `useAgendaAggregates` | `.../valeria/api/agenda.ts` | React Query month aggregates |
| `useAppointmentDetail` | `.../valeria/api/agenda.ts` | Detail by `appointment_id` |
| `useChargeMutation` | `.../valeria/api/payments.ts` | POST /charge + invalidate grid + emit fiscal sagás |
| `useFiscalEmitMutation` | `.../valeria/api/fiscal.ts` | POST /fiscal/emit |
| `useAgendaFilters` | `.../valeria/hooks/useAgendaFilters.ts` | URL params + chip state |
| `useDrawerStore` | `.../valeria/store/drawer-store.ts` | zustand: selectedSlotId + resize width localStorage |
| `useDrawerWidth` | `.../valeria/hooks/useDrawerWidth.ts` | localStorage persist 440-640px |
| `useTenantLocale` | `vitalia/frontend/src/lib/tenant-locale.ts` (root rule helper) | currency + timezone tenant default |
| `useFreshness` | `.../valeria/hooks/useFreshness.ts` | "Actualizado hace Xs" computed from `dataUpdatedAt` |

### Anti-duplication scan

Pre-write verificación (per `.claude/rules/anti-duplication.md`):

```bash
# Buscar drawer right-side patterns en otros brands
find ${WS}/core ${WS}/{nicolify,comunify,lupulo}/frontend/src -name "*Drawer*.tsx" 2>/dev/null
# Resultado esperado: Nicolify closer-studio tiene Sheet pattern → REUSE pattern (no código), construir brand-local
```

**Decisión:** `AppointmentDrawer` es Vitalia-local (HIPAA-lite specific: PHI masking, dual filter, audit log). Pattern Sheet+Accordion es lift candidate cuando ≥2 brands necesiten drawer right-side con secciones colapsables → escalate `/pm-luana` `core/luana-core-ui/` futuro (NO blocker F2-S1).

---

## § Data flow (conceptual)

### Endpoints consumidos

| Method | Path | Propósito | Notes |
|---|---|---|---|
| GET | `/api/v1/scheduling/agenda/grid?tenant_id&clinic_id&view&date&preset_filter` | Slots para view+date | Dual filter `tenant_id+clinic_id` (HIPAA-lite) |
| GET | `/api/v1/scheduling/agenda/aggregates?tenant_id&clinic_id&month` | Counts por día (MonthCalendar) | NO bulk slots |
| GET | `/api/v1/scheduling/appointments/{appointment_id}` | Detail single (drawer) | PHI masked en response (DNI masked, name first-initial) |
| POST | `/api/v1/scheduling/appointments` | Crear cita | Body: patient (existing or new), doctor, service, datetime, origin |
| PATCH | `/api/v1/scheduling/appointments/{id}/status` | Cancelar/completar/no-show | Body: `{new_status, reason?}` + audit log |
| GET | `/api/v1/crm/patients?q=&clinic_id=&limit=10` | Autocomplete pacientes existentes | PHI masked results |
| POST | `/api/v1/payments/charge` | Cobro saldo (payment-adapter-mvp) | Body: `{appointment_id, amount, currency, method, fiscal_emit}` |
| POST | `/api/v1/fiscal/emit` | Emisión boleta/factura (fiscal-emission-pe) | Body: `{payment_id, doc_type}` |
| POST | `/api/v1/scheduling/appointments/{id}/notify` | Enviar recordatorio WhatsApp template-only | Body: `{template_id}` — ComplianceService valida |
| POST | `/api/v1/telemetry/events` | Eventos críticos (agenda_viewed, charge_*, etc.) | Sanitize payload |

### React Query keys

```ts
['agenda', 'grid', { tenantId, clinicId, view, date, presetFilter }]
['agenda', 'aggregates', { tenantId, clinicId, month }]
['agenda', 'appointment', { appointmentId }]
['crm', 'patients', { tenantId, clinicId, q }]
```

### Mutations + invalidations

| Mutation | Invalida |
|---|---|
| `useChargeMutation` | `['agenda', 'grid', ...]` + `['agenda', 'appointment', appointmentId]` |
| `useCreateAppointmentMutation` | `['agenda', 'grid', ...]` |
| `useUpdateAppointmentStatusMutation` | idem grid + appointment |
| `useFiscalEmitMutation` | `['agenda', 'appointment', appointmentId]` |
| `useSendNotificationMutation` | `['agenda', 'appointment', appointmentId]` (history acción) |

### Form libraries

- RHF + Zod schemas (`agenda-schema.ts`)
- `CobrarSaldoSubform`: schema `chargeSchema` con discriminated union por currency
- `CrearCitaForm`: schema `createAppointmentSchema` con conditional patient (new vs existing)

### Estado global

- React Query cache: data tier
- Zustand local feature `useDrawerStore` (`selectedSlotId`, `drawerWidth`, `isOpen`)
- Zustand local feature `useAgendaFiltersStore` (chip activo, URL sync)
- NO Zustand global cross-feature (FSD-Lite boundary)
- localStorage: `vitalia.agenda.lastView` · `vitalia.agenda.drawerWidth`

---

## § Microcopy (Spanish neutro LatAm)

<!-- voseo-allowed: reference glosario (forbidden voseo examples below contextualizan al builder) -->

### Headers + Empty states

| Lugar | Copy |
|---|---|
| Page title (browser tab) | "Agenda · Valeria · Vitalia" |
| AgendaHeader h1 | "Agenda" |
| Date picker placeholder | "Elegí una fecha" |
| FreshnessIndicator | "Actualizado hace 12s" / "Actualizando…" |
| FreshnessIndicator stale | "Sin conexión · datos no actualizados" |
| Refresh button aria-label | "Actualizar agenda ahora" |
| Empty day heading | "No hay turnos este día" |
| Empty day body | "Tomate un café o creá una cita walk-in." |
| Empty day CTA | "+ Crear cita" |
| Empty filtered heading | "Ningún turno coincide con el filtro" |
| Empty filtered CTA | "Limpiar filtros" |
| Empty error heading | "No pudimos cargar tu agenda" |
| Empty error body | "Verificá tu conexión e intentá de nuevo." |
| Empty error CTA | "Reintentar" |

### Chips preset

| Chip | Copy |
|---|---|
| Hoy | "📅 Hoy" |
| Por confirmar mañana | "⏰ Por confirmar mañana" |
| Re-agendar pendientes | "↩️ Re-agendar pendientes" |
| No-shows del día | "🚫 No-shows del día" |
| Saldos pendientes | "💰 Saldos pendientes" |

### View toggle

| Botón | Copy |
|---|---|
| Día | "Día" |
| Semana | "Semana" |
| Mes | "Mes" |

### Crear cita dropdown

| Opción | Copy |
|---|---|
| Walk-in | "Paciente walk-in (nuevo)" |
| Teléfono | "Reserva telefónica (nuevo)" |
| Desde existente | "Desde paciente existente" |

### Drawer header

| Lugar | Copy |
|---|---|
| Botón "Ver ficha" enabled | "Ver ficha del paciente" |
| Botón "Ver ficha" disabled tooltip | "Pacientes — próximamente disponible en Fase 2" |
| Close button aria-label | "Cerrar drawer del turno" |

### Acordeones drawer

| Sección | Trigger label |
|---|---|
| Turno | "Turno" |
| Pago / saldo | "Pago / saldo" |
| Histórico de pagos | "Histórico de pagos" |
| Notas internas | "Notas internas" |
| Acciones avanzadas | "Acciones avanzadas" |

### Acciones turno

| Botón | Copy |
|---|---|
| Re-agendar | "Re-agendar" |
| Cancelar (trigger dialog) | "Cancelar turno" |
| Marcar completado | "✓ Marcar como completado" |
| Marcar no-show | "🚫 Marcar como no-show" |
| Cancelar — Dialog title | "¿Cancelar este turno?" |
| Cancelar — Dialog body | "Se notificará al paciente. Esta acción no se puede deshacer fácilmente." |
| Cancelar — Dialog confirm | "Sí, cancelar turno" |
| Cancelar — Dialog cancel | "Volver" |
| No-show — Dialog title | "¿Marcar como no-show?" |
| No-show — Dialog body | "Se registrará en el histórico del paciente. Podés deshacer en las próximas 24h desde el historial." |
| No-show — Dialog confirm | "Sí, marcar no-show" |

### Subform Cobrar saldo

| Campo | Label |
|---|---|
| Monto | "Monto" |
| Currency select | "Moneda" |
| Method | "Método de pago" |
| Method opciones | "Efectivo · Tarjeta · Transferencia · Mercado Pago · Otro" |
| Emit invoice toggle | "Emitir comprobante" |
| Fiscal doc type | "Tipo de comprobante" |
| Fiscal doc opciones (PE) | "Boleta electrónica · Factura electrónica" |
| Fiscal doc opciones (AR) | "Factura B · Factura A · Recibo" |
| Notes | "Notas (opcional)" |
| Submit button | "Cobrar {currency} {amount}" (dinámico) |
| Submit loading | "Procesando cobro…" |
| Success toast | "Cobro {currency} {amount} registrado · {doc_type} emitida" + link "Ver comprobante" |
| Error payment | "No pudimos procesar el cobro. Intentá de nuevo en unos segundos." |
| Error fiscal (payment OK) | "Cobro registrado, pero el comprobante quedó pendiente. Podés reintentar la emisión." |
| Conflict 409 | "Este saldo ya fue cobrado por otro usuario. Refrescando tu agenda…" |
| Stale banner | "Este turno fue actualizado por otro usuario." |
| Stale recargar | "Recargar datos" |

### Histórico pagos

| Estado | Copy |
|---|---|
| Empty | "Aún no hay pagos registrados para este turno." |
| Row | "{date} · {currency} {amount} · {method} · {doc_type} {doc_url ? '(ver)' : ''}" |

### Acciones avanzadas

| Acción | Copy |
|---|---|
| Enviar recordatorio WhatsApp | "Enviar recordatorio por WhatsApp" |
| Template select | "Elegí un template" |
| Template 1 | "Recordatorio de turno (mañana)" |
| Template 2 | "Confirma asistencia (24h antes)" |
| Template 3 | "Reagendar — opciones disponibles" |
| Submit recordatorio | "Enviar recordatorio" |
| Success | "Recordatorio enviado correctamente." |
| Error PHI bloqueado | "No se puede enviar info médica por canales no seguros. Usá el portal del paciente." |
| Reasignar doctor | "Reasignar doctor" |
| Cambiar duración | "Cambiar duración del turno" |

### Spanish neutro check

- ❌ Voseo forbidden: vos/sos/tenés/podés/mirá/dejá → tú/eres/tienes/puedes/mira/deja (excepto sales_agent voice per tenant)
- ❌ Léxico regional: laburo/quilombo/pibe/dale/che/bárbaro → trabajo/lío/chico/asígnale/bien
- ✅ Tildes + ñ + apertura `¿`/`¡` mandatory
- ✅ Microcopy escrito en infinitivo o imperativo neutro

---

## § Responsive breakpoints

| Breakpoint | Tailwind | Behavior |
|---|---|---|
| Mobile | `<md` (<768px) | DayCalendar only · Drawer bottom-sheet 95vh · Chip filters carousel horizontal scrollable · CrearCita FAB bottom-right |
| Tablet | `md-lg` (768-1024px) | Week+Day views (Mes disabled tooltip "Disponible en pantalla mayor") · Drawer side=right 380px fixed |
| Desktop | `lg-xl` (1024-1440px) | All 3 views · Drawer side=right resizable 440-640px localStorage default 440 |
| Wide | `xl+` (>1440px) | Same desktop · Drawer default 480px localStorage |

Mobile UX details:

- View toggle muestra solo `[Día]` enabled, `[Semana]` `[Mes]` con tooltip "Disponible en pantalla mayor (≥768px)"
- AppointmentDrawer: `<Sheet side="bottom">` con drag handle visible top + close X top-right
- AgendaPresetFilters: `<ScrollArea orientation="horizontal">` con shadow indicators left/right cuando hay overflow
- CrearCitaButton: FAB position `fixed bottom-4 right-4` con `<Tooltip>` "Crear cita" + dropdown UP-direction

---

## § Accessibility (WCAG 2.1 AA)

### ARIA labels

- `<AgendaSlot>` → `role="button"`, `aria-label="Slot {hora} {día} · {patient_masked} · {servicio} · {status_human}"`, `aria-haspopup="dialog"`, `aria-expanded={isSelected}`
- `<AgendaCalendar>` → `role="grid"`, `aria-label="Calendario {view}"`
- `<AppointmentDrawer>` (Sheet) → `role="dialog"`, `aria-modal="true"`, `aria-labelledby="drawer-title"`, `aria-describedby="drawer-description"`
- `<CobrarSaldoSubform>` inputs todos `<Label htmlFor>` + `aria-required` + `aria-invalid` cuando error
- Toast → `<div role="status" aria-live="polite">` para success, `role="alert" aria-live="assertive"` para errors
- Chips preset → `<button role="switch" aria-checked={isActive}>`

### Keyboard navigation

- Tab order columnar: Lun9 → Lun10 → … Lun21 → Mar9 → … (vertical priority dentro de cada día)
- Enter/Space en slot → abre drawer
- Esc en drawer → cierra + devuelve focus al slot
- Shift+Tab desde primer slot → focus pasa al `+ Crear cita` button
- Focus trap activo dentro drawer (Tab cycle interno)
- Click `+ Crear cita` → dropdown abre con focus en primera opción

### Contrast ratios

- Texto body: ≥4.5:1 (verificable axe)
- Texto secundario: ≥4.5:1
- Border slot status: ≥3:1 contra background calendar
- Focus ring: ≥3:1 visible en ambos themes

### Screen reader hints

- `<span class="sr-only">` para contexto adicional (ej. "Slot en estado pagado, origen walk-in, paciente P. Hernández")
- Toast notifications anunciadas via `aria-live`
- Drawer open → screen reader anuncia título + descripción

---

## § Telemetría

### Eventos críticos (7) — funnel completo cobro + acciones

| Event | Trigger | Props |
|---|---|---|
| `agenda_viewed` | Page mount + onMount React Query GET success | `tenant_id, clinic_id, view, date, slot_count` |
| `slot_drawer_opened` | Click slot → drawer open | `tenant_id, clinic_id, appointment_id_hash, slot_status, origin` |
| `charge_initiated` | Click submit CobrarSaldoSubform | `tenant_id, clinic_id, payment_method, amount_bucket (0-50/50-100/100-500/500+), currency, fiscal_doc_emit_intent: bool` |
| `charge_succeeded` | POST /charge 200 | `tenant_id, clinic_id, payment_method, amount_bucket, currency, fiscal_doc_emitted: bool, duration_ms` |
| `charge_failed` | POST /charge !200 o /fiscal/emit !200 | `tenant_id, clinic_id, error_code, retry_count, stage: 'payment' | 'fiscal'` |
| `invoice_emitted` | POST /fiscal/emit 200 | `tenant_id, clinic_id, doc_type, country` |
| `reminder_sent` | POST /notify success | `tenant_id, clinic_id, template_id, channel: 'whatsapp'` |

### HIPAA-lite payload constraints

- **PROHIBIDO** en props: `patient_name`, `patient_dni`, `patient_phone`, `diagnosis`, `treatment`, `exact_amount` (use bucket), `doctor_name` (use `doctor_id_hash`)
- `appointment_id` → siempre hash UUID (no PK secuencial leak)
- Sanitize via `sanitize_payload(props, compliance_level='hipaa_lite')` antes emit

### Sink

- Reuse `copilot_trace_event` table OR NEW `growth_studio_event` table (TBD architect — both work, architect decide cost/separation)
- Async fire-forget OK para telemetry (NO bloquea UX), distinto de audit_log (sync mandatory)

---

## § Brand voice

- **Chrome UI (este story 100%):** Spanish neutro LatAm estándar, sin per-tenant voice. NO voseo. NO léxico regional.
- **Templates WhatsApp:** templates predefinidos backend respetan voz tenant del `sales_agent` SSoT (`personality_profiles.system_instruction`). Vitalia tenants AR pueden tener templates voseados; PE/MX/CO/CL neutro. F2-S1 NO edita templates — solo selecciona del catálogo.

---

## § HIPAA-lite checklist (overlay vitalia)

Toda implementation MUST cumplir (verificable per `vitalia/.claude/rules/hipaa-lite.md`):

### Dual filter tenant + clinic

- ✅ Todo query backend: `.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)`
- ✅ Arch fitness: `vitalia/backend/tests/architecture/test_phi_dual_filter.py` cubre nuevos endpoints scheduling
- ✅ Cross-clinic query bloqueada → 404 (no 403, no leak existencia)

### Audit log row obligatorio (sync write)

- ✅ Cada read drawer → row `{action: 'read_appointment_detail', resource_id, user_id, ...}`
- ✅ Cada charge → row `{action: 'charge', payload_redacted: {amount, method, currency}}`
- ✅ Cada cancel/no-show/complete → row `{action: 'status_change', from_status, to_status}`
- ✅ Cada notify WhatsApp → row `{action: 'send_notification', template_id, channel}`
- ✅ Audit log scoped a `vitalia.audit` module (NO reusar engine — Vitalia tiene clinic_id extra)

### PHI masking visual

- ✅ Slot title: `P. Hernández` (first-initial + apellido) NO `Pedro Hernández`
- ✅ Drawer header: DNI masked `12.***.***` (primer y último char + asteriscos middle)
- ✅ Email masked: `p***@gmail.com`
- ✅ Phone masked: `+51 9** *** 423`
- ✅ Component reuse: `<PHIMaskedText>` shared `/components/shared/phi/`

### Sanitize en traces

- ✅ Sentry capture body excluye PHI fields per `phi_fields.py`
- ✅ Telemetry events sanitized
- ✅ console.log NUNCA muestra PHI dev mode

### ComplianceService channel guard

- ✅ `POST /notify` valida pre-send: si `template_content` contiene PHI fields → BlockedChannelError
- ✅ Templates aprobadas en seed/admin (NO free text user)
- ✅ Audit log row obligatorio

### Encryption (server-side, transparente FE)

- Backend encrypt `patient_*` PHI columns con pgcrypto (responsabilidad scheduling/payments BE)

---

## § Acceptance criteria checklist

| AC | Criterio | Scenario |
|---|---|---|
| AC-1 | Page `/{tenant}/valeria/agenda` renderiza WeekCalendar default | SC-1 |
| AC-2 | Toggle día/semana/mes funciona + URL params persist | SC-1, SC-9 |
| AC-3 | localStorage `vitalia.agenda.lastView` persiste preferencia | SC-1 |
| AC-4 | Cada AgendaSlot renderiza con border-status correcto + origin badge | SC-1, SC-4 (matrix) |
| AC-5 | Click slot abre AppointmentDrawer con datos PHI masked | SC-1, SC-10 |
| AC-6 | Drawer resizable 440-640px + width persiste localStorage | SC-1 |
| AC-7 | 5 acordeones (Turno+Pago expandidos default, resto collapsed) | SC-1 |
| AC-8 | Subform Cobrar saldo emite pago + comprobante sin recargar página | SC-1 |
| AC-9 | Cancelar + No-show abren Dialog confirm | SC-3 (action gates) |
| AC-10 | Audit log row para cada read drawer + charge + status change + notify | SC-1, SC-4, SC-5 |
| AC-11 | 5 chips preset filtran correctamente (URL + DB) | SC-1 |
| AC-12 | + Crear cita dropdown 3 opciones (walk-in/teléfono/desde-existente) | SC-1 |
| AC-13 | Visual goldens light + dark per view (día/semana/mes) | SC-10 |
| AC-14 | Visual golden drawer abierto + subform expanded | SC-1, SC-2 |
| AC-15 | a11y axe pass WCAG 2.1 AA en calendar + drawer + subform | SC-10 |
| AC-16 | Mobile: vista día only + drawer bottom-sheet 95vh + FAB | SC-1 (responsive) |
| AC-17 | Tenant switcher hard redirect + invalida React Query + reset drawer | SC-3 |
| AC-18 | NO PHI en logs (sanitize_payload) ni URLs (whitelist params) | SC-4 |
| AC-19 | Cross-tenant + cross-clinic query bloqueada (dual filter) | SC-4 |
| AC-20 | Race condition concurrent charge → 409 + UI graceful | SC-5 |
| AC-21 | Concurrent users polling 30s → stale banner + refresh | SC-6 |
| AC-22 | Network failure → 3 retries + EmptyState error + reintentar manual | SC-7 |
| AC-23 | Empty day → EmptyState con CTA crear cita | SC-8 |
| AC-24 | Large dataset 200+ slots día → react-window virtualization | SC-9 |
| AC-25 | MonthCalendar consume /aggregates endpoint (no bulk slots) | SC-9 |
| AC-26 | Multi-currency (PEN/ARS/USD override) renderiza correctamente | SC-11 |
| AC-27 | Spanish neutro LatAm en todos los strings UI | (pre-commit hook check) |
| AC-28 | Vitest unit + Playwright functional + axe pass | (CI gates) |
| AC-29 | 7 telemetry events emitidos sin PHI en payload | (vitest mocks + backend tests) |
| AC-30 | WhatsApp notify template-only + ComplianceService guard + audit | (backend test) |

---

## § Deliverables (paths exactos)

### Frontend

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx` | MODIFY (era empty-state F1-S10) |
| `vitalia/frontend/src/features/valeria/components/agenda/ValeriaAgendaView.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaCalendar.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/DayCalendar.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/WeekCalendar.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/MonthCalendar.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaSlot.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawer.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerSkeleton.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/CobrarSaldoSubform.tsx` | NEW (★) |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaPresetFilters.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/CrearCitaButton.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/CrearCitaForm.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/PatientAutocomplete.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaHeader.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/FreshnessIndicator.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/MobileBottomSheet.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/SkeletonCalendar.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/api/agenda.ts` | NEW (useAgendaGrid, useAggregates, useAppointmentDetail) |
| `vitalia/frontend/src/features/valeria/api/agenda-server.ts` | NEW (SSR initial state) |
| `vitalia/frontend/src/features/valeria/api/payments.ts` | NEW (useChargeMutation) |
| `vitalia/frontend/src/features/valeria/api/fiscal.ts` | NEW (useFiscalEmitMutation) |
| `vitalia/frontend/src/features/valeria/hooks/useAgendaFilters.ts` | NEW |
| `vitalia/frontend/src/features/valeria/hooks/useDrawerWidth.ts` | NEW |
| `vitalia/frontend/src/features/valeria/hooks/useFreshness.ts` | NEW |
| `vitalia/frontend/src/features/valeria/store/drawer-store.ts` | NEW (zustand) |
| `vitalia/frontend/src/features/valeria/store/filters-store.ts` | NEW (zustand) |
| `vitalia/frontend/src/features/valeria/types/agenda.types.ts` | NEW |
| `vitalia/frontend/src/features/valeria/types/agenda-schema.ts` | NEW (Zod) |
| `vitalia/frontend/src/lib/tenant-locale.ts` | MODIFY/EXTEND si helper no existe (useTenantLocale + formatTenantMoney) |
| `vitalia/frontend/src/components/ui/{sheet,accordion,calendar,popover,select,form,sonner}.tsx` | NEW (npx shadcn install) |

### Backend (scheduling module brand-extension NEW)

| File | Acción |
|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/__init__.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/domain/__init__.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/domain/agenda_filter.py` | NEW (whitelist enum) |
| `vitalia/backend/src/modules/vitalia/scheduling/domain/appointment_origin.py` | NEW (enum walk_in/telefono/proactivo_adrian) |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/__init__.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/agenda_grid_repository.py` | NEW (dual filter + react-window pagination) |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/agenda_aggregates_repository.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/application/__init__.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/application/agenda_grid_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/application/appointment_detail_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/application/charge_orchestrator.py` | NEW (saga payment + fiscal + audit) |
| `vitalia/backend/src/modules/vitalia/scheduling/api/__init__.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py` | NEW (4 endpoints: grid, aggregates, detail, status_change) |
| `vitalia/backend/src/modules/vitalia/scheduling/api/charge_router.py` | NEW (POST /charge) |
| `vitalia/backend/src/modules/vitalia/scheduling/api/notify_router.py` | NEW (POST /notify ComplianceService) |
| `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/agenda_dtos.py` | NEW (Pydantic v2 PHI-masked) |
| `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/charge_dtos.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/persistence/__init__.py` | NEW |
| `vitalia/backend/src/modules/vitalia/scheduling/persistence/models/appointment_payment.py` | NEW (mirror si engine añade) o nuevo brand-local |
| `vitalia/backend/src/modules/vitalia/scheduling/persistence/migrations/XXXX_agenda_drawer_phase2.py` | NEW (idempotent IF NOT EXISTS — appointment_payment + audit_log_drawer cols si necesario) |
| `vitalia/backend/src/modules/vitalia/scheduling/extensions.py` | NEW (Extension SDK registry brand) |

### Tests

| File | Acción |
|---|---|
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/ValeriaAgendaView.test.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AgendaSlot.test.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AppointmentDrawer.test.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/CobrarSaldoSubform.test.tsx` | NEW (cubre charge happy + 409 + fiscal error + multi-currency) |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AgendaPresetFilters.test.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/CrearCitaButton.test.tsx` | NEW |
| `vitalia/frontend/src/features/valeria/api/__tests__/agenda.test.ts` | NEW (React Query hooks) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-cobro.spec.ts` | NEW (SC-1, SC-2) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-tenant-switch.spec.ts` | NEW (SC-3) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-concurrent-users.spec.ts` | NEW (SC-6) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-network.spec.ts` | NEW (SC-7) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-empty.spec.ts` | NEW (SC-8) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-large-dataset.spec.ts` | NEW (SC-9) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-keyboard.spec.ts` | NEW (SC-10) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-i18n.spec.ts` | NEW (SC-11) |
| `vitalia/frontend/e2e/shell-organism/valeria-agenda-mobile.spec.ts` | NEW (responsive) |
| `vitalia/frontend/e2e/__screenshots__/agenda/*.png` | NEW (~14 visual goldens: 3 views × 2 themes + drawer + subform success/error/conflict + mobile + slot matrix) |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_agenda_grid_service.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_drawer_charge_flow.py` | NEW (SC-1, SC-2, SC-5) |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_phi_url_protection.py` | NEW (SC-4) |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_dual_filter_clinic_isolation.py` | NEW (SC-4) |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_audit_log_drawer.py` | NEW (audit log row cada action) |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_notify_compliance_guard.py` | NEW (template-only + PHI block) |
| `vitalia/backend/tests/architecture/test_scheduling_module_ddd.py` | NEW (extends pattern brand) |

---

## § Reuse map (extraído + extendido del checkpoint)

| Origen | Componente/pattern | Adaptación Vitalia F2-S1 |
|---|---|---|
| Vitalia archived — `vitalia-slice-1-agenda/02-design-ui-mockup.html` | Calendar shell + AppointmentDrawer original draft | Migrar concept + adaptar tokens shell-organism + agregar subform Cobrar saldo + nuevo route group |
| Engine — `core/luana-core-scheduling/` (read-only) | Models `Appointment`, `Booking`, queries grid | CONSUME via brand wrapper. NO mirror. |
| Engine — `core/luana-core-platform/` (read-only) | Tenant + clinic isolation patterns | EXTEND brand-local con clinic_id dual filter |
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/crm/` | Patient model + PHI masking | REUSE via API `/api/crm/patients?q=` |
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/clinics/` | Clinic model + tenant_clinic junction | REUSE |
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/compliance/` | ComplianceService + phi_fields.py | REUSE para notify + sanitize |
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/audit/` | audit_log table + writer | EXTEND brand schema clinic_id + resource_type='appointment_*' |
| Service-story `vitalia-payment-adapter-mvp` | Charge gateway (Stripe/MP/efectivo) | CONSUME via POST /api/payments/charge |
| Service-story `vitalia-fiscal-emission-pe` | Boleta/factura emission PE + AR + MX | CONSUME via POST /api/fiscal/emit |
| Shadcn primitives | Sheet · Accordion · Calendar · Popover · Select · Form · Sonner · Dialog · DropdownMenu · Tabs | npx install + style con Vitalia tokens |
| Nicolify FE shipped — `closer-studio` (read-only reference) | Right-drawer Sheet animation + focus management + accordion sections | TRANSPONER pattern (no código) al AppointmentDrawer Vitalia-local |
| Vitalia F1-S5 shipped — `ValeriaSidebar` rail/full/collapsed states | Sheet width persist + drag handle pattern | TRANSPONER drag handle pattern al resize del Drawer |

---

## § Definición de "Done"

1. ✅ Todos los 30 AC verificados via Playwright + Vitest (CI gates GREEN)
2. ✅ 11 gherkin scenarios PASS (SC-1..SC-11)
3. ✅ Visual goldens ratificados Chris (≥14 snapshots)
4. ✅ Backend tests HIPAA-lite (PHI no leak + dual filter + audit log + ComplianceService guard) pass
5. ✅ Frontend tests Vitest ≥80% coverage on new files
6. ✅ Spanish neutro pre-commit hook GREEN
7. ✅ Arch fitness tests pass (`test_scheduling_module_ddd.py` + `test_phi_dual_filter.py`)
8. ✅ Story commits pushed `wip/vitalia` con Conventional Commits
9. ✅ Service-deps blockers `developed` (payment-adapter + fiscal-pe)
10. ✅ T-{n}-result.md escrito con SHAs + log decisiones
11. ✅ Handoff `/auditor` emitido (auto-handoff per story-closure-gate)
12. ✅ Auditor APPROVED + CHECKPOINTS C1-C5 GREEN
13. ✅ `/pm-vitalia merge` → state `done` → capability `scheduling/valeria-agenda` promovida
14. ✅ Archive story → `vitalia/docs/archive/2026/stories/vitalia-fase2-valeria-agenda/`

---

## § Próximo paso post-done

- F2-S2 `vitalia-fase2-valeria-pacientes` activa el link "Ver ficha completa" del drawer (capability check toggle)
- F2-S4 `vitalia-fase2-adrian-embudo` consume API agenda para auto-crear slot al marcar lead `reservado`
- F2-S6 `vitalia-fase2-adrian-propuestas` consume API para crear slot inicial post-aprobación propuesta
- F2-S11 `vitalia-fase2-camila-voz` consume API para detectar `status=completed` y disparar NPS trigger
- Capability `scheduling/valeria-agenda` registrada en `vitalia/docs/product/capabilities/scheduling/valeria-agenda.yaml`

---

## § Referencias

- **Brand docs schema:** `.claude/rules/brand-docs-schema.md` (R1+R2+R3)
- **HIPAA-lite overlay:** `vitalia/.claude/rules/hipaa-lite.md`
- **Mockup gate:** `vitalia/.claude/rules/shell-mockup-per-component.md`
- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 3 (átomos/moléculas) · § 7 (routing) · § 8 (a11y) · § 9 (testing)
- **Template:** `vitalia/docs/specs/templates/01-spec-shell-template.md`
- **Mockup integral shell ref:** `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html`
- **Navigation tree:** `vitalia/docs/product/stories/vitalia-shell-organism/navigation-tree.md` § valeria.agenda
- **Slice-1 archive (refactor source):** `vitalia/docs/archive/2026/stories/vitalia-slice-1-agenda/02-design-ui-mockup.html`
- **Service stories:** `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/` · `vitalia/docs/product/stories/vitalia-fiscal-emission-pe/`
- **Frontend FSD:** `.claude/rules/frontend-fsd.md`
- **Master data + currency:** `.claude/rules/master-data.md` · `.claude/rules/currency-handling.md`
- **Spanish neutro glosario:** `.claude/rules/spanish-text.md`
- **Anti-duplication:** `.claude/rules/anti-duplication.md`
- **TDD mandatory:** `.claude/rules/tdd-mandatory.md`
- **Po-ux v4.1 gate:** `.claude/skills/po-ux/SKILL.md` § Step 5
