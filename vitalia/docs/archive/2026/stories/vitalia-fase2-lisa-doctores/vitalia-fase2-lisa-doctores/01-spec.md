---
story_id: vitalia-fase2-lisa-doctores
brand: vitalia
type: ui-story
state: refined
architecture_pattern: ADR-vitalia-004
po_ux_version: 2
cap_target: lisa.doctores
cap_change_type: new
agent_owner: lisa
map_zone: agentes
map_box: lisa
module: clinics
ratified_by_chris: true
ratified_visual_by_chris: true
---

# 01-spec · vitalia-fase2-lisa-doctores — Directorio + Workspace de **Staff** (Lisa)

> **★ v2 (ratificado Chris 2026-05-31):** sub-tab renombrada **Doctores → Staff** (contenedor del equipo; el ítem-persona sigue siendo "doctor"). Ruta FE = `lisa/staff`. Acuerdos UX cementados esta iteración: (1) **N3-dyn siempre visible** (raíz Staff + integrante + hojas), **pegada arriba (sticky) full-width**, espejo de Marca/Identidad → candidata a **componente UX reusable** `SubSubTabsBar` con entidad dinámica; (2) **autosave en todos los campos** (sin botón Guardar — `form-runtime-array.md` + ADR-004 §3.5); (3) **Bio = repo de insumos** (texto + archivos vía dropzone + links) → "✨ Generar bio" en secciones editables, sin inventar; (4) **Horarios formato 24h** con check "Mostrar 24 horas" (base 07:00–21:00); (5) **Servicios = pendiente** (depende de historia futura "Mi Clínica · Servicios"). Componente de adjuntos: **shadcn Dropzone** (`diragb/shadcn-dropzone`, sobre `react-dropzone`).

## § Context

- **Release:** F2 (`vitalia/docs/product/releases/F2.yaml`)
- **Módulo técnico:** `clinics` (backend) + consume `scheduling` + engine. **Zona/caja del mapa:** Agentes → **Lisa**.
- **Insertion point:** sección **Staff** del agente Lisa. **Sin tabs internos (política ARQ FE: la hoja es el último nivel)** — cada sub-sección es una ruta-hoja, espejando `lisa/marca/{presencia,voz-y-tono,identidad}`:
  - `lisa/staff` → directorio del equipo (hoja)
  - `lisa/staff/[doctor-id]` → redirect a `/perfil` (igual que `lisa/marca` → `/identidad`)
  - `lisa/staff/[doctor-id]/perfil` → **Perfil** — hoja default del integrante
  - `lisa/staff/[doctor-id]/horarios` → **Horarios** (calendario) — hoja
  - `lisa/staff/[doctor-id]/servicios` → **Servicios** — hoja
  - La navegación es **ruteo real** (cada hoja = su propia URL), NO `<Tabs>`. Verificado en mockup con Playwright: deep-link + back/forward respetan cada hoja.

### ★ Layout constraint (cementar como UX, ratificado Chris 2026-05-30)
- El contenido del agente vive en una **hoja con la conversación de Valeria al costado** (panel chat ~320px a la derecha) → la **columna de contenido es ANGOSTA**. TODO se diseña **full-width de esa columna** y para **verse bien en poco espacio** (cards apiladas 1-col, calendario compacto, no grids anchos).

### ★ Navegación de entidad dinámica (N3-dynamic) — patrón nuevo, ratificado Chris 2026-05-30/31
Tira de tercer nivel **SIEMPRE visible** (coherente con Identidad), **pegada arriba (sticky) y full-width** (mismo tratamiento visual que `SubSubTabsBar` de Marca: pills, activo = fondo sutil, no relleno):
`[👨‍⚕️ Staff]  |  {avatar+Nombre del integrante}  |  [👤 Perfil] [🗓️ Horarios] [🩺 Servicios]`
- En el **directorio**: `Staff` activo + "Selecciona un integrante" + Perfil/Horarios/Servicios **deshabilitados** (opacity .45, no clickeables).
- Al **entrar a un integrante**: el chip muestra avatar+nombre y se **habilitan** las 3 hojas; `Staff` actúa de raíz/volver.
- `Perfil/Horarios/Servicios` = las hojas del integrante (rutas reales).
- **⚠️ Cross-cutting → componente UX reusable:** este patrón aplica a TODO workspace de entidad dinámica (pacientes de Valeria/Mateo, leads de Adrián, etc.). Se promueve a **componente UX `SubSubTabsBar` con entidad dinámica** (átomo/molécula del design system) + **addendum a `ADR-vitalia-004` § 3.1.1**. La generalización del componente shell se escala como decisión ARQ (ver § Handoff ARQ); para esta story el spec asume el patrón.
- **Capability:** `lisa.doctores` (NEW). Sucede a `clinics-brand-extension` (deprecated) + consume `prepaid-booking-advisory-locks`.

### Goal
Lisa administra el **Staff** (equipo): directorio visual (cards, personal-branding) + workspace por integrante con 3 hojas-ruta (**Perfil · Horarios · Servicios**). El **Perfil** incluye un **repo de insumos para promoción** (texto + archivos + links → "✨ Generar bio" en secciones editables) que consume el agente de ventas. **Horarios** = calendario de bloques mutables (recurrentes/puntuales) que alimentan la Agenda de Valeria. Validación de credencial colegio médico por país, toggle de visibilidad en landing público, y **autosave** en todos los campos.

### Out-of-scope (anti-creep) — ratificado Chris 2026-05-30/31
- **Tab KPIs DIFERIDO** a story futura (cuando analytics esté end-to-end).
- **Servicios = PENDIENTE en esta story** — la hoja existe en estado "pendiente · depende de Servicios"; la selección real del catálogo depende de la historia futura **"Mi Clínica · Servicios"**, que se crea al cerrar esta. No hay UI funcional de selección de servicios todavía.
- **UI de landing público DIFERIDA** a `vitalia-fase2-lisa-landing-public`. Acá: solo el toggle "Visible en landing" + el endpoint público read-only PHI-masked.
- **Peer-review entre integrantes** — out.
- **Parsing/OCR de los archivos adjuntos** (extraer texto de PDFs de diploma/CV) — out; el MVP de la bio usa el texto pegado + metadatos de los archivos, sin pipeline de extracción.
- NO recrear el sistema de slots/agenda (ya existe en `scheduling/` + engine).

## § Prior art applied

- **Engine consumido:**
  - `luana-core-scheduling` — disponibilidad/slots base (la availability del doctor se escribe hacia acá).
  - `luana-core-commercial-calendar` — **reglas de recurrencia** del template de horarios (Chris eligió recurrencia avanzada → se CONSUME el motor de recurrencia del engine, NO se reimplementa).
  - `luana-core-assets` — backend **`infrastructure/storage/r2.py` dedicado a Cloudflare R2** (boto3 + presigned, con fallback `local.py`). **nicolify ya lo consume** (`nicolify/backend/src/main.py`) → patrón de referencia a copiar. Se usa para el avatar/foto del doctor (`AssetKind`). Key tenant-scoped.
- **Reused de vitalia (mismo brand):**
  - `vitalia/backend/src/modules/vitalia/clinics/` (domain `clinic.py`, `clinic_model.py`, repo, service, router) — el doctor cuelga de la clínica.
  - `vitalia/backend/src/modules/vitalia/infrastructure/models/doctor_extension_model.py` + `DoctorExtensionRepository` (`# cap: booking.prepaid-booking-advisory-locks`) — EXTEND, no recrear.
  - `vitalia/backend/src/modules/vitalia/scheduling/` (`agenda_slot`, `create_appointment_service`, `agenda_grid_service`, `agenda_router`) — el form "crear cita" de Valeria reconoce los doctores nuevos.
  - `booking/prepaid-booking-advisory-locks.yaml` — `available-slots` endpoint + advisory locks (consumido, no tocado).
  - `vitalia/frontend/src/features/lisa/` (api, components, hooks, store, types, utils) — feature existe; se agrega sub-carpeta `components/doctores/`.
- **Reused PHI masking:** patrón masking DNI/email/phone del overlay `vitalia/.claude/rules/hipaa-lite.md` (full set ratificado).
- **Learnings aplicados:**
  - `vitalia/docs/learnings/2026-05-27-service-deps-option-a-stubs-msw.md` (stubs/MSW para deps de servicio en FE durante dev).
  - `vitalia/docs/learnings/2026-05-30-clerk-godmatrix-mint-live-verification.md` (verificación real ≠ HTTP 200 — los scenarios se ejercen de verdad, write incluido).
- **Lift candidates:** ninguno nuevo (clinic/doctor son brand-local salud; si 2da brand replica → promotion EP futuro).
- **Net-new justificado:** UI `features/lisa/components/staff/*` + rutas `lisa/staff/` (hoy `features/lisa/components/` solo tiene `marca` + `placeholders`).

## § Gherkin scenarios

> **★ Modelo de horarios (ratificado Chris 2026-05-30):** la disponibilidad del doctor **NO es un template fijo**. Es un conjunto de **bloques de disponibilidad** que se agregan y eliminan continuamente (los especialistas trabajan en varios lugares y dan su disponibilidad semana a semana / mes a mes). Cada bloque es:
> - **Recurrente** (día-de-semana + franja horaria + regla: semanal / quincenal / etc.) con condición de fin: **fecha-fin** O **número de iteraciones** O abierto.
> - O **puntual** (one-off): una fecha concreta + franja (para "esta semana sumo el sábado").
> Los bloques son **eliminables en cualquier momento**. Eliminar un bloque retira la disponibilidad **futura** proyectada por ese bloque (las citas ya confirmadas se preservan). La recurrencia se **expande/proyecta consumiendo `luana-core-commercial-calendar`** y materializa availability hacia `scheduling`.

### SC-1 — happy: crear doctor + agregar bloque recurrente con fecha-fin (playwright_required: true)
**Given:** usuario `admin_clinic` autenticado en `lisa/staff`, clínica activa con ≥1 servicio.
**When:**
1. Click "+ Nuevo doctor" → modal → Nombre, Apellido, DNI, Email, Phone, Especialidad, **Credencial CMP `12345` (PE)**, Activo=on, foto opcional (upload directo a R2 vía assets).
2. Submit → navega a la hoja **Perfil** (`[doctor-id]`).
3. Va a la hoja **Horarios** (`[doctor-id]/horarios`) → en el calendario (vista semana) **arrastra** sobre lun 9:00→13:00 → popover "¿Repetir?" → semanal · también mié y vie · **fecha-fin = +8 semanas** → confirma.
4. (Bloque queda visible en el calendario en todas sus semanas.)
**Then:**
- Doctor creado · **audit log** (`doctor.created`).
- El bloque persiste · backend **expande la recurrencia vía `commercial-calendar`** hasta la fecha-fin · materializa availability hacia `scheduling` solo para ese rango (no 90d arbitrarios — respeta la condición de fin).
- En `scheduling` (Agenda Valeria) el form "crear cita" lista al doctor con los slots reales del bloque.
- Round-trip: recargar workspace → el bloque y su fecha-fin siguen.
- `graders:`
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase2-lisa-doctores/doctores-crear-happy.spec.ts" }`
  - `{ type: state_check, target: db, query: "SELECT max(slot_date) FROM availability_slots WHERE doctor_id=:id AND tenant_id=:t", expect: "<= fecha_fin del bloque" }`
  - `{ type: state_check, target: db, query: "SELECT action FROM audit_log WHERE entity='doctor' AND action='created' AND tenant_id=:t ORDER BY created_at DESC LIMIT 1", expect: "created" }`

### SC-1b — happy: bloque recurrente por número de iteraciones (playwright_required: true)
**Given:** doctor existente, hoja Horarios (calendario).
**When:** arrastra sábado 10:00→14:00 → popover repetir **quincenal**, **N iteraciones = 6**.
**Then:** backend proyecta exactamente **6 ocurrencias** (quincenales) vía commercial-calendar · availability materializada solo para esas 6 fechas · el bloque muestra "6 de 6 · finaliza el {fecha calculada}". `graders:` e2e + `{ type: state_check, query: "SELECT count(distinct slot_date) FROM availability_slots WHERE doctor_id=:id AND block_id=:b", expect: "6" }`

### SC-1c — happy: navegar a otra semana + bloque puntual (one-off) (playwright_required: true)
**Given:** doctor con bloques recurrentes ya cargados (visibles en cada semana).
**When:** click **‹/›** para ir a la semana siguiente → arrastra sábado 9:00→12:00 → popover **"Solo esta semana"** (sin recurrencia).
**Then:** se suma disponibilidad solo para esa fecha puntual · los bloques recurrentes siguen visibles en su grilla · Agenda Valeria reconoce el puntual. Confirma el modelo "semanas distintas". `graders:` e2e (navegación temporal) + state_check 1 slot_date.

### SC-1d — happy: eliminar un bloque desde el calendario (disponibilidad mutable) (playwright_required: true)
**Given:** doctor con 3 bloques; el bloque B2 (recurrente) no tiene citas futuras confirmadas.
**When:** click en el bloque B2 en el calendario → popover → "Eliminar" → confirma.
**Then:**
- B2 desaparece · **availability futura proyectada por B2 se retira** (slots futuros sin cita liberados/eliminados) · slots de B1 y B3 intactos · availability **pasada** no se toca.
- audit `doctor.availability_block_deleted`.
- `graders:` e2e + `{ type: state_check, query: "SELECT count(*) FROM availability_slots WHERE block_id=:b2 AND slot_date >= current_date", expect: "0" }`

### SC-2 — negative: credencial colegio médico inválida (playwright_required: true)
**Given:** modal "Nuevo doctor", país tenant = PE (credencial CMP numérica).
**When:** ingresa credencial `abc` (no numérica) + submit.
**Then:**
- Backend `credential_validator` rechaza **422** con `{ field: "credential", message: "La credencial CMP debe ser numérica" }`.
- UI muestra error inline en el field + foco automático en él.
- NO persiste (cero filas nuevas en doctor + cero audit `created`).
- `graders:` `{ type: e2e, path: ".../doctores-credencial-invalida.spec.ts" }` · `{ type: visual_state, screen: "modal-nuevo-doctor", element: "input[name=credential]", expect: "border-destructive + aria-invalid=true" }`

### SC-3 — edge: doctor desactivado con citas futuras (playwright_required: true)
**Given:** doctor existente con ≥2 citas futuras agendadas.
**When:** toggle "Activo" → off + confirma en modal.
**Then:**
- `doctor.active=false` (soft, NO hard delete) · audit `doctor.deactivated`.
- Slots futuros: backend **NO cancela** citas existentes (preserva data) pero **excluye al doctor** del form "crear cita" futuro.
- Alert UI: "Doctor desactivado. {N} citas futuras siguen vigentes. ¿Reasignar manualmente?" con link a Agenda.
- `graders:` e2e + `{ type: state_check, query: "SELECT active FROM doctors WHERE id=:id", expect: "false" }` + `{ type: state_check, query: "SELECT count(*) FROM appointments WHERE doctor_id=:id AND start_ts > now() AND status!='cancelled'", expect: "unchanged" }`

### SC-3b — edge: eliminar bloque con cita futura confirmada (playwright_required: true)
**Given:** bloque B con una cita confirmada el martes próximo a las 10:00.
**When:** admin intenta "Eliminar" el bloque B.
**Then:**
- UI **advierte** antes de borrar: "Este bloque tiene {N} cita(s) confirmada(s). Si lo eliminás, esas citas seguirán vigentes pero el doctor dejará de estar disponible para nuevas reservas en ese horario."
- Si confirma: B se elimina · slots futuros **sin cita** se liberan · la(s) cita(s) confirmada(s) **se preservan** (no se cancelan) · audit `doctor.availability_block_deleted` con `preserved_appointments=N`.
- `graders:` e2e + `{ type: state_check, query: "SELECT count(*) FROM appointments WHERE block_origin=:b AND status='confirmed' AND start_ts>now()", expect: "unchanged (N)" }`

### SC-4 — adversarial: cross-tenant doctor view (playwright_required: true)
**Given:** usuario tenant A intenta abrir doctor de tenant B.
**When:** navega `/{tenant-A}/lisa/staff/{doctor_B_id}`.
**Then:**
- Backend **dual filter** (tenant_id + clinic_scope) bloquea → **404 genérico** (no 403, no filtrado de existencia).
- Audit log `cross_tenant_attempt` con actor + target.
- `graders:` e2e adversarial + `{ type: state_check, query: "SELECT action FROM audit_log WHERE action='cross_tenant_attempt'", expect: "1 row" }`

### Sub-categorías mandatory

#### SC-5 — race_condition: dos admin crean doctor con mismo DNI simultáneo (playwright_required: false → integration)
**Given:** 2 requests `POST /api/v1/vitalia/clinics/doctors` concurrentes, mismo `(tenant_id, dni)`.
**When:** ambos submit en la misma ventana.
**Then:** unique constraint `(tenant_id, dni)` garantiza que solo uno persiste · el segundo recibe **409 Conflict** "Ya existe un doctor con ese documento". `graders:` `{ type: integration, path: "vitalia/backend/tests/modules/vitalia/clinics/test_doctor_dni_race.py" }`

#### SC-6 — concurrent_users: aislamiento multi-tenant en directorio (playwright_required: true)
**Given:** tenant A (3 doctores) y tenant B (5 doctores) consultando `lisa/staff` al mismo tiempo.
**Then:** A ve exactamente sus 3, B sus 5 · cero leak cross-tenant en el grid ni en search/filter. `graders:` integration + e2e.

#### SC-7 — network_failure: fetch directorio falla (playwright_required: true)
**Given:** `GET /api/v1/vitalia/clinics/doctors` responde 503/timeout.
**Then:** UI muestra **error banner + botón "Reintentar"** (no pantalla en blanco, no crash) · al reintentar y resolver, renderiza el grid. `graders:` e2e con `page.route` mock 503.

#### SC-8 — empty_state: clínica sin doctores (playwright_required: true)
**Given:** clínica activa con 0 doctores.
**Then:** **empty-state** con ilustración + heading "Aún no hay doctores en tu equipo" + CTA "Agregar primer doctor" (abre modal). NO tabla vacía, NO spinner infinito. `graders:` e2e + `{ type: visual_state, screen: "directorio-empty", element: "[data-testid=empty-doctores]", expect: "visible" }`

#### SC-9 — large_dataset: 1000+ doctores (playwright_required: true)
**Given:** clínica con 1200 doctores.
**Then:** grid pagina (server-side, page size 24) o virtualiza · search/filter responden <500ms · sin congelar el browser. `graders:` integration (pagination correctness) + e2e (scroll/paginación).

#### SC-10 — accessibility: keyboard nav workspace tabs + form (playwright_required: true)
**Given:** foco en primer tab (Bio) del workspace.
**Then:** Arrow ←/→ cicla tabs (`aria-selected` actualiza, screen reader anuncia) · Tab recorre fields en orden lógico · modal "Nuevo doctor" atrapa foco (focus trap) + Escape cierra. `graders:` `{ type: axe, ruleset: "wcag2aa" }` + e2e keyboard.

#### SC-11 — i18n: spanish neutro + credencial por país + currency override (playwright_required: true)
**Given:** tenants en PE/AR/MX/CL.
**Then:** labels de credencial cambian por país (PE: CMP · AR: matrícula nacional+provincial · MX: cédula profesional · CL: registro nacional) · copy en spanish neutro (sin voseo) · el pricing override per-doctor del tab Servicios usa currency del tenant_locale (no hardcoded). `graders:` e2e multi-locale + state_check currency.

## § Wireframes inline

### Directorio (`lisa/staff`) — ASCII
```
┌──────────────────────────────────────────────────────────┐
│ Doctores                          [ + Nuevo doctor ]       │
│ [ 🔍 Buscar...        ]  [ Especialidad ▾ ]  [ Activo ▾ ] │
├──────────────────────────────────────────────────────────┤
│ ┌───────────┐ ┌───────────┐ ┌───────────┐               │
│ │  (avatar) │ │  (avatar) │ │  (avatar) │   grid cards   │
│ │ Dra. Ana  │ │ Dr. Luis  │ │ Dra. Sol  │   (no tabla)   │
│ │ Cardiología│ │ Pediatría │ │ Dermatol. │               │
│ │ 8a · 320p │ │ 5a · 210p │ │ 12a · 540p│   stats tiny   │
│ │ NPS 72    │ │ NPS 68    │ │ NPS 81    │               │
│ │[Ver perfil]│ │[Ver perfil]│ │[Ver perfil]│               │
│ └───────────┘ └───────────┘ └───────────┘               │
│                         ‹ 1 2 3 ... ›   (pagination)     │
└──────────────────────────────────────────────────────────┘
```

### Shell completo (columna angosta + Valeria al costado)
```
┌───────────────────────────────────────────────┬───────────────┐
│ Lisa · Mateo · Adrián · Lucas · Camila  Platf. │   Valeria     │  ribbon N1
│ Marca · [Staff] · Servicios · Compliance       │  (chat        │  ribbon N2
│ [Staff] / Dra. Ana · Perfil·Horarios·Servicios │   supervisora │  ribbon N3-dyn ★
├───────────────────────────────────────────────┤   ~320px)     │
│ (contenido full-width de la columna angosta)   │  [mensajes…]  │
│                                                 │  [input ____] │
└───────────────────────────────────────────────┴───────────────┘
   La fila N3-dyn solo aparece dentro de un doctor. KPIs → futuro.
   Perfil/Horarios/Servicios = rutas-hoja reales (no Tabs).
```

### Hoja Perfil (`lisa/staff/[doctor-id]/perfil`) — ASCII
```
┌──────────────────────────────────────────────────────────┐
│ ✓ Los cambios se guardan automáticamente   (autosave)     │
│ (avatar R2) [⬆ Subir foto]                                 │
│ Nombre · Apellido · Especialidad · Credencial             │  grid auto-fit
│ Años exp · Idiomas                          (full-width)   │  (1/2/3 col)
│ ┌── Bio para promoción ───────────────  [✨ Generar bio]──┐│
│ │ Notas/datos (pegá libremente) [textarea]               ││
│ │ Archivos (diploma/CV/cert) [▒ dropzone arrastrar/click]││  ← shadcn Dropzone
│ │   📄 Diploma_UPCH.pdf · 240 KB · ✕                      ││
│ │ Links [https://… ] [+ Agregar link]  🔗 chip ✕         ││
│ │ ── Bio pública generada (editable · en secciones) ──   ││
│ │ [RESUMEN]            (contenteditable)                  ││
│ │ [FORMACIÓN Y CREDENCIALES]                             ││
│ │ [ENFOQUE DE ATENCIÓN]                                  ││
│ └────────────────────────────────────────────────────────┘│
│ ☑ Visible en el sitio público                             │
└──────────────────────────────────────────────────────────┘
  Sin botón "Guardar" — autosave on-change (debounce 600ms).
```

### Hoja Horarios (`lisa/staff/[doctor-id]/horarios`) — calendario tipo Google Calendar
```
┌──────────────────────────────────────────────────────────┐
│ ✓ Los cambios se guardan automáticamente                  │
│ Horarios       [‹ Semana ant.]  Jul 7–13  [Sem. sig. ›]   │
│ [Semana ▾ / Mes]                          [ + Bloque ]    │
│ ☑ Mostrar 24 horas   (base 07:00–21:00 · formato 24h)     │
├──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────────┤
│ hora │ Lun  │ Mar  │ Mié  │ Jue  │ Vie  │ Sáb  │ Dom      │
│ 08   │      │      │      │      │      │      │          │
│ 09   │▓▓▓▓▓▓│      │▓▓▓▓▓▓│      │▓▓▓▓▓▓│      │          │  ← bloque
│ 10   │▓ B1 ▓│      │▓ B1 ▓│      │▓ B1 ▓│░ B3 ░│          │     (arrastrar
│ 11   │▓▓▓▓▓▓│      │▓▓▓▓▓▓│      │▓▓▓▓▓▓│░ pun ░│          │      para crear)
│ 12   │      │      │      │      │      │░ tual░│          │
│ 13   │      │      │      │      │      │      │          │
│ ...  │      │      │      │      │      │      │          │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────────┘
  • Arrastrar sobre la grilla → crea bloque (popover: ¿repetir?
    semanal/quincenal · fecha-fin o N° iteraciones · o "solo esta semana").
  • Clic en bloque → editar / eliminar.
  • ‹ › navega semanas (cada semana puede tener disponibilidad distinta).
  • Bloques recurrentes se ven en todas sus semanas; puntuales solo en la suya.
  → expande recurrencia (commercial-calendar) → materializa hacia scheduling.
```

### Hoja Servicios (`lisa/staff/[doctor-id]/servicios`) — PENDIENTE
```
┌──────────────────────────────────────────────────────────┐
│              🩺  Servicios del integrante — pendiente      │
│  Acá vas a poder elegir, del catálogo de Mi Clínica →     │
│  Servicios, los tratamientos que ofrece (precio propio    │
│  opcional). Depende de la historia "Mi Clínica·Servicios",│
│  que se crea al cerrar esta.   [⏳ Planned · dep. Servicios]│
└──────────────────────────────────────────────────────────┘
```
> Diseño futuro (cuando exista el catálogo): multi-select treatments + precio override per-integrante con currency del tenant_locale. NO se construye en esta story.

> Mockup HTML de fidelidad: `mockups/doctores.html`.

## § Estados visuales

| Estado | Trigger | Visibles | Ocultos |
|---|---|---|---|
| `loading` | fetch directorio | skeleton cards (×6) | grid, empty |
| `success` | data ok | grid cards + filtros + pagination | skeleton, empty, error |
| `empty` | 0 doctores | empty-state + CTA | grid, skeleton |
| `error` | fetch 5xx/timeout | error banner + Reintentar | grid, skeleton |
| `saving` (workspace) | submit tab | spinner en botón Save (disabled) | — |
| `save-error` | submit falla | toast error + form intacto | — |

## § Componentes (reuse > new)

| Componente | Path | Reuse/New |
|---|---|---|
| `Button`, `Input`, `Select`, `Dialog`, `Popover`, `Checkbox`, `Switch`, `Badge`, `Card`, `Skeleton` | `vitalia/frontend/src/components/ui/` | reuse (Shadcn). **NO `Tabs`** (política ARQ: sub-nav por rutas) |
| **shadcn Dropzone** (file upload drag&drop) | `components/ui/dropzone.tsx` | **INSTALAR** (`diragb/shadcn-dropzone`, sobre `react-dropzone`; hoy `components/ui/` no lo tiene). Lista nombre/tamaño/remove + multi-archivo. Usado por `AvatarUploader` + `BioRepoInputs` |
| `SubSubTabsBar` (N3-dyn con entidad dinámica) | `components/shared/shell-organism/SubSubTabsBar.tsx` (extender el existente o variante) | **componente UX reusable** — raíz + chip entidad + hojas; estados habilitado/deshabilitado; sticky full-width. Ver § Handoff ARQ |
| `AvatarUploader` (presigned R2 vía assets) | `.../staff/AvatarUploader.tsx` | NEW (consume `luana-core-assets` presigned POST; sube directo browser→R2, sin proxy API; usa Dropzone) |
| `BioRepoInputs` + `GeneratedBioSections` | `.../staff/perfil/*.tsx` | NEW — repo de insumos (notas textarea + Dropzone archivos + links) + botón "✨ Generar bio" + bio en secciones `contenteditable` (Resumen·Formación·Enfoque). Autosave on-change |
| `StaffDirectoryView` | `vitalia/frontend/src/features/lisa/components/staff/StaffDirectoryView.tsx` | NEW (no existe equivalente; `features/lisa/components/` solo tiene `marca`+`placeholders`) |
| `StaffCard` | `.../staff/StaffCard.tsx` | NEW |
| `NuevoIntegranteModal` | `.../staff/NuevoIntegranteModal.tsx` | NEW |
| `StaffWorkspaceShell` (header + N3-dyn sub-nav por rutas) + páginas-hoja `[doctor-id]/page.tsx` (redirect→perfil), `[doctor-id]/perfil/page.tsx`, `.../horarios/page.tsx`, `.../servicios/page.tsx` | `app/.../lisa/staff/[doctor-id]/...` | NEW (rutas-hoja, NO tabs) |
| `AvailabilityCalendar` (vista semana día×hora · drag-to-create · navegación temporal ‹›) + `BloquePopover` (repetir: semanal/quincenal + fecha-fin/N-iter/puntual · editar · eliminar) | `.../doctores/horarios/*.tsx` | NEW (clon Google-Calendar; recurrencia se resuelve backend vía commercial-calendar). Evaluar lib base (ej. react-big-calendar / FullCalendar) en /architect, o grid propio con dnd. |

## § Data flow (conceptual)

- `GET /api/v1/vitalia/clinics/doctors?clinic=&q=&specialty=&active=&page=` → directorio (paginado).
- `POST /api/v1/vitalia/clinics/doctors` → crea (valida credencial) → invalida `['lisa','doctores','list']`.
- `GET /api/v1/vitalia/clinics/doctors/{id}` → workspace.
- `PATCH /api/v1/vitalia/clinics/doctors/{id}` → Bio/active/visible-landing/avatar_key.
- **Horarios (bloques):**
  - `GET /api/v1/vitalia/clinics/doctors/{id}/availability-blocks` → lista de bloques.
  - `POST /.../availability-blocks` → crea bloque (recurrente con `end_date`|`occurrences` o puntual) → backend expande vía `commercial-calendar` + materializa hacia `scheduling`.
  - `PATCH /.../availability-blocks/{block_id}` → edita (reproyecta futuro).
  - `DELETE /.../availability-blocks/{block_id}` → elimina + retira availability futura (preserva citas confirmadas).
- **Avatar (assets + R2):**
  - `POST /api/v1/vitalia/assets/presign-upload` → consume `luana_core_assets.StorageService.generate_presigned_upload` → devuelve `{upload_url, fields, key}` · el browser hace POST directo a R2 · luego `PATCH doctor` con `avatar_key`.
  - lectura: `GET /api/v1/vitalia/assets/presign-download?key=` (privado) o URL pública si bucket público para avatares landing.
- `PUT /api/v1/vitalia/clinics/doctors/{id}/servicios` → treatments + pricing override.
- **Bio repo:** `PATCH doctor { bio_inputs_notes, bio_links[] }` (autosave) + archivos vía presign (mismo flujo que avatar, kind=`credential_doc`) + `POST /api/v1/vitalia/clinics/doctors/{id}/generate-bio` → devuelve secciones {resumen, formacion, enfoque} → autosave de la bio editada.
- React Query keys: `['lisa','staff','list',filters]`, `['lisa','staff',id]`, `['lisa','staff',id,'blocks']`. Forms: RHF + Zod. Autosave on-change (debounce 600ms), **sin submit-driven** salvo el modal "Nuevo integrante". Estado global: ninguno.
- **Nota de naming:** la ruta FE es `lisa/staff`; los endpoints backend pueden seguir bajo `clinics/doctors` (entidad doctor) — el architect decide el path final del API. La regla es: ruta de usuario = Staff, entidad de dominio = doctor.

## § Endpoint público — profundización (ratificado Chris 2026-05-30)

`GET /api/public/clinic/{tenant_slug}/doctors` — **read-only, sin auth, PHI-masked, channel-guarded**. Propósito: alimentar la landing pública de la clínica (UI en `vitalia-fase2-lisa-landing-public`) con el "equipo médico" (doctors-as-faces, señal de confianza/trust).

**Qué expone (solo doctores con `visible_en_landing=true` y `active=true`):**

| Campo | Incluido | Nota |
|---|---|---|
| `display_name` | ✅ | "Dra. Ana Pérez" |
| `specialty` | ✅ | especialidad pública |
| `avatar_url` | ✅ | URL pública R2 (o presigned download) del avatar |
| `years_experience` | ✅ | señal de autoridad |
| `languages` | ✅ | idiomas que atiende |
| `bio_public` | ✅ | bio (versión pública, sin datos sensibles) |
| `credential_label` | ✅ (opcional) | "CMP 12345" como trust signal — **configurable** (clínica decide si muestra el número o solo "Colegiado/a") |
| `dni`, `email`, `phone` | ❌ | NUNCA en público (PHI/PII) |
| `kpis`, `revenue`, `pacientes` | ❌ | internos |
| `availability` cruda | ❌ | el público reserva vía `bookings/available-slots`, no ve la grilla interna |

**Channel guard:** un test de arquitectura/contrato verifica que el serializer público **no pueda** filtrar campos PHI/PII aunque el modelo los tenga (allow-list explícita, no deny-list).

## § Storage de assets — `luana-core-assets` + Cloudflare R2

> NO se recrea storage; se **consume** `luana-core-assets` (backend `storage/r2.py` dedicado a Cloudflare R2, boto3 + presigned ya implementados). **nicolify ya lo consume** → copiar ese wiring. `wrangler 4.86.0` ya está instalado para el provisioning.

**Flujo avatar (upload directo, sin proxy por el API):**
1. FE pide `POST /api/v1/vitalia/assets/presign-upload` (kind=`avatar`, filename, content_type).
2. BE (vía `StorageService.generate_presigned_upload`) devuelve `{upload_url, fields, key}`. Key tenant-scoped: `{tenant_id}/avatar/{uuid}-{filename}`. Límite 10MB + content-type image/* enforced en la policy del presign.
3. Browser hace `POST` multipart directo a **R2** (no pasa por nuestro backend → barato + rápido).
4. FE confirma con `PATCH doctor { avatar_key }`.

**Config R2 necesaria (build / `.env`, gitignored — NO en docs):**
- `ASSETS_R2_ENDPOINT_URL` = `https://298e02eb64fc6d67d4f7737f1c48cab6.r2.cloudflarestorage.com`
- `ASSETS_R2_ACCESS_KEY_ID` + `ASSETS_R2_SECRET_ACCESS_KEY` → **generar en R2 → Manage R2 API Tokens → S3 credentials** (el token `cfat_…` que pasó Chris es CF API token para wrangler/provisioning, NO sirve como llave S3 de boto3).
- `ASSETS_R2_BUCKET` = ej. `vitalia-assets` (+ opcional `vitalia-assets-public` para avatares de landing).
- `ASSETS_R2_REGION` = `auto`.

**Tareas de provisioning (van a `/architect` → ticket build, NO se hacen en refining):**
- Instalar/usar `wrangler` (o CF API con `cfat_`) para crear bucket(s) R2.
- Generar R2 S3 credentials → cargar en `.env.dev` (gitignored).
- CORS del bucket para permitir el POST directo desde el dominio del frontend.
- Registrar el router de assets en vitalia (`include_router`) — hoy vitalia no consume assets aún.

> ⚠️ **Seguridad:** el `cfat_…` se pegó en chat plano → rotar tras provisioning. Las llaves R2 viven solo en `.env` (gitignored), nunca en spec/docs/commits.

## § Microcopy (Spanish neutro LatAm)

| Lugar | Copy |
|---|---|
| Page title | "Staff" |
| Subtítulo | "Equipo de la clínica · perfiles, horarios y servicios" |
| CTA nuevo | "+ Nuevo integrante" |
| Buscador | "Buscar integrante…" |
| N3 placeholder (sin selección) | "Selecciona un integrante" |
| Empty heading | "Aún no hay integrantes en tu equipo" |
| Empty CTA | "Agregar primer integrante" |
| Submit modal | "Crear integrante" |
| Autosave hint | "Los cambios se guardan automáticamente" |
| Bio CTA | "✨ Generar bio" |
| Bio hint | "Juntá el material del integrante (texto, diplomas, CV, links). Al generar, Lisa arma una bio profesional en secciones usando solo este material — no inventa." |
| Dropzone | "Arrastrá o hacé clic para subir · PDF, JPG, PNG, DOCX · hasta 10 MB" |
| Success toast | "Cambios guardados" |
| Error toast | "No pudimos guardar. Intenta de nuevo." |
| Error credencial | "La credencial CMP debe ser numérica" |
| Desactivar confirm | "¿Desactivar a este integrante? Sus citas futuras seguirán vigentes." |
| Visible landing | "Visible en el sitio público" |
| Error banner | "No pudimos cargar el equipo." + "Reintentar" |
| Servicios pendiente | "Servicios del integrante — pendiente · depende de Mi Clínica → Servicios" |

<!-- voseo-allowed: glosario reference -->
**Check:** sin voseo (`vos/tenés/podés`), sin léxico regional. Tildes + ñ + `¿!`.

## § Responsive
- Mobile (<768): grid → 1 col; workspace tabs → scroll horizontal; modal full-screen.
- Tablet (768-1024): grid 2 col; tabs compactos.
- Desktop (>1024): grid 3-4 col; workspace tabs fijos.

## § Accessibility
- ARIA labels en todos los inputs + `aria-invalid` en errores.
- Focus visible (`focus:ring-2 focus:ring-primary`); focus trap en modal; Escape cierra.
- Tabs con `role=tablist`/`tab`/`tabpanel` + Arrow nav + `aria-selected`.
- Contrast ≥4.5:1 texto, ≥3:1 UI.

## § HIPAA-lite (FULL set — ratificado Chris 2026-05-30)
> Overlay `vitalia/.claude/rules/hipaa-lite.md`.
- **tenant-isolation dual filter** (tenant_id + clinic_scope) en TODA query (incluido get_by_id).
- **Audit log** en create/update/deactivate/cross-tenant-attempt (actor + entity + action + ts).
- **RBAC:** solo `admin_clinic` edita; otros roles read-only (toggle/edit ocultos o disabled).
- **Encryption at-rest (pgcrypto)** en campos sensibles del perfil (DNI, credencial, contacto).
- **Retención** según política vertical (campos sensibles).
- **Masking** de DNI/email/phone en vistas de lista y en endpoint público.
- **Channel guards** en el endpoint público (`/api/public/clinic/...`) → solo campos no-PHI + masked.

## § Business rules (→ cap `lisa.doctores`)

| id | regla | severidad | enforcement / código | audit |
|---|---|---|---|---|
| `credential-validator-country-specific` | La credencial del colegio médico se valida según el país del tenant: PE = CMP numérico · AR = matrícula nacional + provincial · MX = cédula profesional · CL = registro nacional. Inválida → 422, no persiste. | high | `clinics/application/credential_validator.py` | no |
| `dni-unique-per-tenant` | No pueden existir dos doctores con el mismo `(tenant_id, dni)`. Constraint a nivel DB. Colisión concurrente → 409. | high | unique constraint + repo | no |
| `recurrence-end-condition-required` | Un bloque recurrente DEBE declarar condición de fin: `end_date` O `occurrences` O `open_ended=true` explícito. No se permite recurrencia infinita implícita. | high | domain `AvailabilityBlock` validation | no |
| `availability-projection-via-engine` | La expansión de la recurrencia se resuelve consumiendo `luana-core-commercial-calendar`. PROHIBIDO reimplementar lógica de recurrencia en vitalia. | critical | `.claude/rules/anti-duplication.md` · service que llama al engine | no |
| `availability-block-mutable` | Los bloques se agregan/editan/eliminan en cualquier momento. Editar o eliminar **reproyecta solo el futuro**; la availability pasada nunca se modifica. | high | `availability_block_service` | no |
| `delete-block-preserves-confirmed-appointments` | Eliminar un bloque retira slots futuros SIN cita; las citas **confirmadas** se preservan (no se cancelan). Si hay citas confirmadas → warning obligatorio antes de borrar. | critical | service + UI confirm modal | yes (`availability_block_deleted` con `preserved_appointments`) |
| `doctor-soft-deactivate` | Desactivar es soft (`active=false`), nunca hard delete. Doctor inactivo se excluye del form "crear cita" futuro pero sus citas vigentes se preservan. | high | repo soft-delete + scheduling filter | yes |
| `avatar-presigned-direct-r2` | El avatar se sube por presigned POST directo browser→R2 (sin proxy API). Key tenant-scoped `{tenant_id}/avatar/{uuid}-{file}`. Límite 10MB + content-type `image/*` enforced en la policy del presign. | medium | `luana_core_assets.StorageService` | no |
| `public-endpoint-phi-allowlist` | El endpoint público usa allow-list explícita de campos (display_name, specialty, avatar_url, years_experience, languages, bio_public, credential_label opcional). PHI/PII (dni/email/phone/kpis) NUNCA serializable, aunque el modelo lo tenga. | critical | serializer allow-list + arch/contract test (channel guard) | no |
| `visible-en-landing-requires-active` | Un doctor solo aparece en el endpoint público si `visible_en_landing=true` Y `active=true`. Desactivar lo quita del público automáticamente. | medium | query filter público | no |
| `rbac-only-admin-clinic-edits` | Solo rol `admin_clinic` puede crear/editar/eliminar doctores, bloques y servicios. Otros roles (doctor/nurse/receptionist) → read-only (controles ocultos/disabled + 403 backend). | critical | `@require_role` decorator + FE guard | yes (intentos denegados) |
| `tenant-clinic-dual-filter` | Toda query filtra `tenant_id` + scope de clínica (incluido get_by_id). Acceso cross-tenant → 404 genérico + audit. | critical | `.claude/rules/tenant-isolation.md` + `vitalia/.claude/rules/hipaa-lite.md` | yes (`cross_tenant_attempt`) |
| `encryption-at-rest-sensitive` | Campos sensibles del perfil (DNI, credencial, contacto) cifrados at-rest (pgcrypto), full HIPAA-lite set. | critical | `vitalia/.claude/rules/hipaa-lite.md` | no |
| `audit-on-all-mutations` | Toda mutación (create/update/deactivate/block add-delete/cross-tenant-attempt) escribe audit log (actor + entity + action + ts). | high | audit service | yes |
| `servicios-pricing-currency-tenant-locale` | (futuro · cuando se construya Servicios) El pricing override per-integrante usa la currency del `tenant_locale` (AR:ARS, CL:CLP, MX:MXN, CO:COP, PE:PEN, BR:BRL). Nunca hardcoded. | medium | `.claude/rules/master-data.md` | no |
| `autosave-no-save-button` | Todos los campos del workspace (Perfil, Horarios, Servicios futuro) son **autoguardables** on-change (debounce 600ms). PROHIBIDO botón "Guardar" (rompe autosave). UI muestra hint "Los cambios se guardan automáticamente". | high | `form-runtime-array.md` + ADR-vitalia-004 §3.5 | no |
| `bio-generated-from-inputs-no-invent` | "✨ Generar bio" produce la bio pública **solo a partir del material aportado** (notas pegadas + archivos + links del integrante) — **no inventa** datos. Salida en secciones editables (Resumen · Formación y credenciales · Enfoque de atención). La bio resultante alimenta al agente de ventas para promocionar al integrante. | high | service de generación (consume material; sin alucinación) | no |
| `bio-attachments-via-assets-r2` | Los archivos del repo de bio (diploma/CV/certificados) se suben por presigned directo browser→R2 vía `luana-core-assets` (mismo patrón que el avatar). Key tenant-scoped, límite 10MB, tipos PDF/JPG/PNG/DOCX. NO parsing/OCR del contenido en esta story. | medium | `luana_core_assets.StorageService` | no |

## § Telemetría
```yaml
events:
  - { name: "lisa_doctores_list_viewed", trigger: "page mount", props: ["filters"] }
  - { name: "lisa_doctor_created", trigger: "modal submit success", props: ["doctor_id","specialty"] }
  - { name: "lisa_doctor_horarios_saved", trigger: "horarios save", props: ["doctor_id","recurrence_type"] }
  - { name: "lisa_doctor_deactivated", trigger: "toggle off confirm", props: ["doctor_id","future_appts_count"] }
```

## § Estimación
- Original 3-4d → **revisada 7-9d** por:
  - (a) bloques de disponibilidad mutables (add/edit/delete) con recurrencia fecha-fin/N-iter/puntual vía `commercial-calendar`.
  - (b) full HIPAA-lite (pgcrypto + audit + channel guards).
  - (c) **integración inicial de `luana-core-assets` + provisioning R2** (vitalia primer consumidor: registrar router assets, config R2, bucket + CORS + credenciales S3, AvatarUploader presigned).
- **Candidato fuerte a split** en /architect: (1) doctores CRUD + bio + servicios, (2) horarios-calendario + scheduling wiring, (3) assets+R2 + avatar + endpoint público. Lo decide /architect al armar tickets; lo dejo flagueado.

## § Handoff ARQ — decisiones cross-cutting (escalar, NO build en esta story)

Esta story depende de 2 patrones nuevos que exceden su scope (tocan shell-organism / ADR / engine config). Se escalan a decisión ARQ antes/durante `/architect`:

1. **`EntityBreadcrumbBar` (N3-dynamic nav)** — fila contextual de ribbon `‹ Lista de X / {entidad} · {hojas}` para workspaces de entidad dinámica. Aplica a TODO agente (pacientes de Valeria/Mateo, leads de Adrián, etc.), no solo doctores. Requiere **addendum a `ADR-vitalia-004` § 3.1.1** + componente en `components/shared/shell-organism/`. Decisión: ¿se construye el componente genérico en esta story (y se cementa el ADR) o en una story-protocol previa?
2. **Layout full-width + columna angosta (coexistencia con Valeria chat)** — ya es implícito en el shell, pero conviene cementarlo como **regla UX permanente** ("toda funcionalidad de agente se diseña full-width de columna angosta, legible en poco espacio"). Chris pidió recordarlo siempre → al cerrar, proponer: (a) memory entry, (b) línea en `ADR-vitalia-004` o nueva rule `vitalia/.claude/rules/`, (c) mención en `SHELL-DESIGN-CONTRACT.md`.
3. **assets + R2 provisioning** (ver § Storage) — bucket + CORS + R2 S3 keys en `.env`, registrar router assets en vitalia (copiar de nicolify).

---

## ★ Delta v3 — scope extension (2026-06-11 · FIRMA 1 funcional Chris vía AskUserQuestion)

> Tres ítems ratificados en la reanudación (story `developing`, post shell-core-hardening). Origen: `chris-input.md` entries 2026-06-11. Gherkin + matriz del delta se GENERAN al firmar el mockup delta (FIRMA 2 — W0.5-bis). Cita canon: `docs/architecture/luana-platform/design-system-canon.md` §2.4 · §2.6 · §6.3-6.4.

### D3-A · Switcher de entidad en la franja N3 (EntityPicker canon §2.4 — "canon tal cual" ratificado)

**Funcional (viñetas):**
- Dentro del workspace de un doctor, el nombre en la franja N3 deja de ser chip estático → **trigger `▾`** que abre el **`EntityPicker`** (YA construido en `core/@luana/ui-kit`, canon §2.4): buscador server-side debounced + lista paginada (cursor, 20) + render windowed + item = avatar iniciales + nombre + especialidad + ✓ en el activo.
- **Al seleccionar otro doctor → navega a `/lisa/staff/[nuevo-id]/{hoja-actual}` PRESERVANDO la hoja** (ratificado: si estás en Horarios de Ana → Horarios de Carlos).
- Master mode (directorio, `entity=null`): sin cambios.
- Estados: loading (skeleton rows) · empty "Sin resultados" · error inline + reintentar. a11y combobox (↑↓/Enter/Esc, focus al search al abrir) — ya cubierto por el componente core.
- Datos: consume `GET /clinics/doctors?q=&page=` existente (búsqueda + paginación ya shipped). Cero campo nuevo. Tenant-scoped vía header (sin cambios).
- **Implementación (handoff ARQ):** EXTEND `EntitySubNavBar` core con prop opcional de picker (composición canon §6.3) — promotion proposal liviana `/pm-luana` (aditiva, brand-agnostic). Doctores = 1er consumidor real (hoy solo showcase).

**RN-D3A-1:** la lista del picker solo muestra staff del tenant actual (filtro server, jamás client-side de colección completa — canon §2.4 ❌ cargar todo).
**RN-D3A-2:** doctor inactivo no aparece en el picker por default.

### D3-B · Material para bio — carga de documentos FUNCIONAL + homologación canon ("funcional completa ahora" ratificado)

**Estado actual (audit 2026-06-11):** `BioRepoInputs.tsx` — dropzone con `onFilesChange` NO-OP (los archivos NO se suben ni persisten), sin lista de subidos, `DoctorDetail` sin campo de archivos; `<textarea>`/`<button>` crudos (D1); emojis autosave inline (viola canon §2.6); chips de links sin validación.

**Funcional (viñetas):**
- **Subida REAL a R2** vía proxy assets existente (patrón `useAvatarUpload`; `kind` lo decide /architect — `credential_doc` existente o `bio_doc` nuevo). Persiste por doctor, tenant-scoped.
- **Lista de documentos subidos**: filas con icono por tipo (PDF/IMG/DOCX) + nombre (truncado) + tamaño + fecha + acciones **descargar** y **eliminar** (con confirmación).
- Estados: subiendo (progreso por archivo) · error de subida (reintentar/quitar) · empty (texto suave) · límites PDF/JPG/PNG/DOCX ≤10MB, múltiple.
- **Homologación visual al canon:** sección como las demás cards del perfil (borde + header acento `agent-lisa`) · átomos `Textarea` + `Button` reales (matar `<textarea>`/`<button>` crudos) · links con validación URL (Zod) + chip con icono · **eliminar emojis autosave inline** (la `FloatingAutosaveIndicator` única de la página cubre — canon §2.6).
- **Contrato BE (delta chico):** `DoctorDetail.bioFiles[] {id, filename, sizeBytes, contentType, uploadedAt}` + descarga (URL presigned o proxy) + `DELETE` asset (tenant+doctor scoped, audit log — superficie staff).

**RN-D3B-1:** eliminar un archivo NO altera la bio generada previa (la bio es snapshot de texto, no referencia viva).
**RN-D3B-2:** archivo rechazado (tipo/tamaño) → feedback inline; jamás subida silenciosa fallida.

### D3-C · Horarios — casuística de recurrencia (bug sospechado · "toda la casuística" ratificado)

**Sospecha Chris:** el calendario no respeta el número de repeticiones. Código: la lógica `occurrences` SÍ existe (`availability_projection_service.py` — weekly/biweekly × end_date/occurrences/open_ended) → bug sutil probable. Cero cambio visual (el calendario gusta).

**Mandato (repro-first + batería exhaustiva — verificación REAL write+efecto, nunca GET 200):**
1. semanal (1 día) × occurrences=N → EXACTAMENTE N instancias (single-día: N ciclos × 1 día = N · sin cambio)
2. quincenal (1 día) × occurrences=N → N instancias espaciadas 14d
   <!-- ★ RECONCILE round-6 (Chris 2026-06-15): "N repeticiones" = N CICLOS COMPLETOS. Multi-día → count = N × len(días): Mar+Jue ×3 = 6 (3 Mar + 3 Jue), cada semana completa. (Antes este punto decía "N totales, NO contar semanas" — INVERTIDO por decisión de producto.) -->
2b. **multi-día × occurrences=N → N semanas COMPLETAS** (cada repetición incluye todos los días): Mar+Jue ×3 = 6 turnos
3. end_date → última instancia INCLUYE el día final (TZ tenant)
4. open_ended → ventana de proyección correcta (ni corta antes ni proyecta infinito)
5. edición de bloque recurrente post-creación → conteo NO se reinicia ni duplica instancias
6. puntual + recurrente solapados mismo día → ambos visibles
7. borrado de bloque recurrente → desaparecen TODAS las instancias proyectadas
8. TZ: bloque creado en TZ tenant renderiza el día correcto (borde de medianoche)

Si el repro confirma bug → regression test RED que lo reproduce PRIMERO, fix después (tdd-mandatory + hotfix-repro). Evidencia por caso en `dod_evidence`.

#### D3-B.1 · Regeneración de bio + visibilidad (ratificado Chris 2026-06-11 ronda 2)

- **Regenerar siempre disponible.** Si ya existe bio → modal de confirmación: "Reemplazará el contenido actual de las 3 secciones (incluidas tus ediciones manuales). ¿Generar de nuevo?". Sin bio previa → genera directo.
- **"Última generación: {fecha}"** visible junto al botón ✨ Generar bio (BE persiste `bio_generated_at`).
- **Empty state explícito** cuando nunca se generó: "Aún no se generó la bio — agrega material y presiona ✨ Generar bio" (NO cajas contenteditable vacías mudas).
- **Mini-caption de visibilidad** bajo el toggle "Visible en landing": aclara dónde se usa el perfil público ("Se muestra en la página pública de la clínica"). El link compartible mobile + consumo por Adrián NO van en esta story (ver § Derivadas).

**RN-D3B-3:** regenerar con bio existente requiere confirmación explícita (pisa ediciones manuales — diseño ratificado: sin protección por-sección).
**RN-D3B-4:** `bio_generated_at` se actualiza SOLO en generación IA (no en ediciones manuales).

#### § Derivadas del delta (ratificado Chris 2026-06-11 — NO crear stories nuevas, cablear en existentes)

| Requerimiento | Hogar | Por qué |
|---|---|---|
| Adrián consume perfil doctor (bio + especialidad + servicios en su contexto de venta) + acción "compartir link del doctor" cuando el lead pregunta por el doctor o se le asigna | `vitalia-fase2-adrian-canal-inbound` (refined · module sales_agent — dueña del ex-sales_agent) | Chris: "deberías agregarlo a una historia que ya exista que implemente lo que antes era el sales_agent y ahora es adrián" |
| ~~Página pública del doctor → landing-public~~ **REVERTIDO 2026-06-11 (v3.1):** la página del doctor va EN ESTA story (§ D3-D). La landing de la CLÍNICA queda parkeada en `lisa-landing-public` (Chris: "no sé si irá") — son cosas distintas: el lead siempre busca quién lo atiende | esta story | Chris: "no lo dejes como requerimiento" |

### D3-D · Página pública del doctor (mini-Doctoralia mobile) + perfil estructurado + flujo estado-driven (v3.1 — repensado, ratificación pendiente FIRMA 2)

> Corrección Chris 2026-06-11 ronda 3: la página del doctor NO se deriva (la landing de la clínica está parkeada; la del doctor es distinta — el usuario siempre busca información de quién lo atiende). El perfil extraído debe ser MÁS RICO que 3 blobs. El flujo de generación NO puede invitar a "regenerar porque sí".

**1 · Nueva hoja N3 "Página"** (4ª hoja: Perfil · Horarios · Servicios · **Página**) — pipeline completo en un lugar:
- **Estado + link:** pill Publicada/Borrador · URL estable compartible (`/d/{clinica-slug}/{doctor-slug}`) · Copiar link · Ver página · toggle "Visible públicamente" (OFF → link muestra "perfil no disponible"). El bloque bio/material SALE de la hoja Perfil (cross-link card la reemplaza).
- **Material privado** (insumos — nunca se publica tal cual): notas + archivos (dropzone funcional D3-B) + links.
- **Perfil generado ESTRUCTURADO** (mejora vs BioPublic 3 blobs): `Titular` (1 línea venta) · `Resumen` · `Formación[]` (título — institución — año, lista estructurada) · `Credenciales verificables[]` (chips: CMP nro verificado, certificaciones) · `Enfoque` · `Idiomas[]`. Todo editable inline + autosave.
- **Página pública mobile-first** (mini-Doctoralia): header foto+nombre+especialidad+clínica + badge "✓ CMP verificado" + stats (años exp · casos · idiomas) + resumen + formación + enfoque + **CTA "💬 Consultar por WhatsApp"** → deep-link al WhatsApp de la clínica (el lead VUELVE al funnel de Adrián — loop cerrado). Preview en frame de teléfono dentro del workspace.

**2 · Flujo de generación estado-driven (mata el "regenerar porque sí"):**
- **Nunca generado:** empty state + CTA único "✨ Generar perfil".
- **Generado, sin material nuevo:** sección quieta — "Última generación: {fecha}" + menú ⋮ (Regenerar todo, secundario escondido). SIN CTA primario.
- **Material nuevo detectado** (insumo con `updated_at > bio_generated_at`): banner contextual "⚡ Agregaste {N} archivos/notas después de la última generación" + CTA "✨ Actualizar perfil". El CTA primario SOLO existe cuando hay algo que incorporar.
- Confirmación de overwrite (RN-D3B-3) aplica cuando hay ediciones manuales.

**RN-D3D-1:** la página pública solo expone el perfil estructurado generado/editado + datos no-PHI (jamás insumos crudos ni documentos adjuntos).
**RN-D3D-2:** URL del doctor estable (slug); toggle OFF no rompe el link (página "no disponible"), lo desactiva.
**RN-D3D-3:** CTA WhatsApp de la página apunta al número de la clínica del tenant (config conexiones) — el retorno entra por el canal de Adrián.
**RN-D3D-4:** detección de material nuevo = timestamps insumos vs `bio_generated_at` (server, no heurística client).

**Adrián (sin cambios de hogar):** el ENVÍO automático del link por Adrián sigue en `vitalia-fase2-adrian-canal-inbound` (scope-add ya escrito) — esta story PROVEE la página + URL; aquella la envía.

#### D3-D.1 · Correcciones ratificadas Chris 2026-06-11 ronda 4 (v3.2)

- **Dominio de la página = variable de entorno, NUNCA hardcodeado:** dev → `dev-app.vitalialat.com` · testing → `test-app.vitalialat.com` · prod → `app.vitalialat.com`. URL completa: `{APP_BASE_URL}/d/{clinica-slug}/{doctor-slug}`.
- **La página del doctor es INFORMATIVA pura — SIN CTA de contacto** (se eliminó el botón WhatsApp propuesto): el lead ya viene de la conversación con Adrián; la página solo construye confianza. **RN-D3D-3 REEMPLAZADA:** la página NO incluye botones de contacto/reserva/WhatsApp.
- **Sin stats de venta:** fuera el row "años · casos · idiomas" del header. Solo carrera profesional.
- **Estructura Doctoralia-style (secciones de la página):** header sobrio (foto · nombre · especialidad · badge "✓ Nro. colegiatura CMP verificado") → Sobre mí → Formación (lista título/institución/año) → Experiencia profesional (lista puesto/lugar/años) → Tratamientos (chips) → Certificaciones y membresías (✓ lista) → Idiomas (condicional) → Consultorio (nombre + dirección, informativo).
- **Perfil estructurado del editor (campos finales):** Sobre mí · Formación[] · Experiencia profesional[] · Tratamientos y enfoque · Certificaciones y membresías[] · Idiomas[]. (Se eliminó "Titular" — tono venta fuera de una página informativa.)
- **RN-D3D-5 (idiomas):** la sección Idiomas solo se renderiza en la página pública si el doctor habla MÁS de un idioma (español-only → no se muestra nada). Posición discreta (abajo, antes de Consultorio) — nunca stat prominente.

#### D3-C.1 · REPRO CONCRETO (Chris live 2026-06-11) + root cause anclado — supersede "bug sutil"

- **Repro Chris (dev-app):** bloque recurrente con **2 repeticiones** de un día → el calendario lo **repite indefinidamente**.
- **Root cause CONFIRMADO por inspección** (`trace_evidence`): `AvailabilityCalendar.tsx::recurrentBlockVisibleInWeek` (líneas ~93-115) solo evalúa `end_date`; para `end_condition_kind=occurrences` retorna `true` SIEMPRE → pinta el bloque en TODAS las semanas. El BE proyecta BIEN (`availability_projection_service.py`). **Es render FE, no BD.** <!-- ★ RECONCILE round-6: el count del rrule pasó a `occurrences × len(days_of_week)` = N ciclos completos (ratificado Chris 2026-06-15). -->**
- **Drift de arquitectura:** el FE duplica lógica de expansión local por semana en vez de consumir la proyección BE (SSoT) — misma clase del patrón contrato-imaginado (4ª vez en esta story). **Dirección del fix (architect concreta):** ambas vistas (semana + mes) consumen ocurrencias proyectadas del BE; muere la expansión client-side.
- TDD: regression test RED primero — weekly×occurrences=2 → FE pinta EXACTAMENTE 2 semanas + BE proyecta 2 fechas.

### D3-E · Vista de MES del calendario de horarios (NEW — ratificado Chris 2026-06-11 ronda 5)

> Hoy solo existe grilla semanal (`AvailabilityCalendar` week grid). Chris: "me parece genial que agregues la vista de mes, eso no hay actualmente. Revisa en nuestro código lo que tenemos allí y mejóralo."

**Funcional:**
- Toggle **Semana | Mes** en el header de Horarios (pills, default semana — drag-create vive solo en semana).
- Grilla mes clásica (6×7): cada celda-día muestra chips compactos de bloques (hora inicio–fin, tint `agent-lisa`; overflow "+N más").
- Click en un día → salta a la vista semana de esa semana (el día enfocado). Crear/editar bloques = solo en semana (MVP).
- **Datos: la vista mes consume la PROYECCIÓN BE del rango visible** (no expansión client-side — coherente con el fix D3-C).
- Estados: loading skeleton de grilla · mes sin bloques (empty suave) · error + reintentar.
- Navegación: ‹ mes anterior · hoy · mes siguiente ›. a11y: grid navegable, aria-labels por día.

**RN-D3E-1:** la vista mes refleja EXACTAMENTE las ocurrencias proyectadas por el BE (un bloque occurrences=2 aparece en exactamente 2 fechas del mes/meses).
**RN-D3E-2:** sin escritura desde la vista mes (read + navegación) en este MVP.

---

## § Gherkin Delta v3 (GENERADO en FIRMA 2 — 2026-06-11) + Matriz

> Formato compacto: `SC-id · tipo · given/when/then · Covers · grader`. Todos los funcionales FE: `playwright_required: true` con doctrina real-backend (auth.fixture, sin mock del surface bajo prueba).

**D3-A · Switcher**
- `SC-D3A-1` happy · doctor abierto en hoja Horarios / clic ▾ + elegir otro doctor / navega a `/lisa/staff/{otro}/horarios` (hoja PRESERVADA) + contenido del otro doctor renderiza · Covers RN-D3A-1 · e2e
- `SC-D3A-2` negative · buscar "zzqx" en picker / lista vacía / "Sin resultados" visible · e2e
- `SC-D3A-3` edge · doctor inactivo existe / abrir picker / NO aparece (RN-D3A-2) · e2e + state_check
- `SC-D3A-4` a11y · picker abierto / navegar ↑↓ + Enter + Esc / selección por teclado funciona + axe wcag2aa · e2e

**D3-B · Documentos funcional**
- `SC-D3B-1` happy · PDF 2MB válido / drop / fila aparece con nombre+tamaño+fecha + asset persistido en R2/DB (state_check) + GET detail trae bioFiles[] · e2e real-backend
- `SC-D3B-2` happy · archivo subido / clic eliminar + confirmar / fila desaparece + asset borrado (state_check) + audit row · e2e
- `SC-D3B-3` negative · archivo 15MB o .exe / drop / error inline, NADA se sube (RN-D3B-2) · e2e
- `SC-D3B-4` edge · descarga / clic ⬇ / archivo descarga (status 200 + content-type correcto) · e2e
- `SC-D3B-5` network_failure · upload con 503 simulado / fila error + Reintentar (no crash) · e2e

**D3-D · Página pública + generación estado-driven**
- `SC-D3D-1` happy · doctor visible ON con perfil generado / GET `/d/{clinica}/{doctor}` SIN auth / página renderiza secciones estructuradas (Sobre mí→Consultorio), badge colegiatura, CERO PHI paciente, CERO botón contacto · e2e público
- `SC-D3D-2` negative · toggle OFF / abrir link / "perfil no disponible" (no 404 roto, no leak) (RN-D3D-2) · e2e
- `SC-D3D-3` edge · doctor español-only / página pública / sección Idiomas AUSENTE (RN-D3D-5) · e2e
- `SC-D3D-4` happy · perfil generado + subir archivo nuevo / volver a hoja Página / banner "⚡ material nuevo" + CTA Actualizar VISIBLE; sin material nuevo → banner AUSENTE (RN-D3D-4) · e2e real-backend
- `SC-D3D-5` edge · perfil con edición manual / clic Actualizar / modal confirmación overwrite (RN-D3B-3) · e2e
- `SC-D3D-6` adversarial · URL pública de doctor de OTRO tenant/clinica slug-fuzzing / no leak cross-tenant (404/no-disponible genérico) · e2e + state_check

**D3-C · Casuística recurrencia (batería — BE integration + e2e paint)**
- `SC-D3C-1` ★REGRESSION (repro Chris) · weekly occurrences=2 / proyectar + pintar / BE: EXACTAMENTE 2 fechas · FE semana: pinta SOLO en esas 2 semanas · FE mes: 2 chips · backend_integration + e2e
- `SC-D3C-2` · biweekly occurrences=3 / 3 fechas espaciadas 14d (span 6 semanas) · backend_integration + e2e
- `SC-D3C-3` · end_date / última ocurrencia INCLUYE el día final (TZ tenant) · backend_integration
- `SC-D3C-4` · open_ended / proyección respeta horizonte (ni corta ni infinita) · backend_integration
- `SC-D3C-5` · editar bloque recurrente post-creación / conteo NO se reinicia ni duplica · backend_integration + e2e
- `SC-D3C-6` · puntual + recurrente solapados mismo día / ambos visibles · e2e
- `SC-D3C-7` · borrar bloque recurrente / desaparecen TODAS las ocurrencias · e2e + state_check
- `SC-D3C-8` · TZ borde medianoche / día correcto en render · backend_integration

**D3-E · Vista de mes**
- `SC-D3E-1` happy · bloques con occurrences=2 / abrir vista Mes / chips SOLO en las 2 fechas proyectadas (RN-D3E-1) · e2e
- `SC-D3E-2` happy · vista mes / clic en un día / salta a vista semana de esa semana · e2e
- `SC-D3E-3` empty_state · mes sin bloques / empty suave · e2e
- `SC-D3E-4` large_dataset · doctor con 30+ bloques/mes / overflow "+N más" + sin jank · e2e

**Matriz delta:** RN-D3A-1→SC-D3A-1 · RN-D3A-2→SC-D3A-3 · RN-D3B-1→(cubierta por diseño snapshot, verif en SC-D3D-5) · RN-D3B-2→SC-D3B-3 · RN-D3B-3→SC-D3D-5 · RN-D3B-4→SC-D3D-4 · RN-D3D-1→SC-D3D-1 · RN-D3D-2→SC-D3D-2 · RN-D3D-4→SC-D3D-4 · RN-D3D-5→SC-D3D-3 · RN-D3E-1→SC-D3E-1/SC-D3C-1 · RN-D3E-2→SC-D3E-2. **Huecos: ninguno · SC huérfanos: ninguno.**

### D3-F · Editor de recurrencia clon Google Calendar + display de ocurrencias (ratificado Chris 2026-06-12 ronda 6)

> Chris: "mejora el cómo se muestran las ocurrencias y hazlo como un clon de google calendar que uno pone y puede poner repetir e incluso días específicos". **Diseño-por-referencia:** el patrón de Google Calendar ES el mockup (universalmente conocido); se compone con átomos canon (Select canónico §2.5 + chips). Goldens lo ratifican en G.

**Funcional — editor (en BloquePopover):**
- Select "Repetir": `No se repite` · `Todos los días` · `Cada semana el {día}` · `Cada 2 semanas el {día}` · `Personalizado…`
- `Personalizado…` abre sub-editor (igual Google): **"Repetir cada [N] semana(s)"** + **chips de días L M X J V S D (multi-select)** + **"Termina":** `Nunca` (open_ended) · `El [fecha]` (end_date) · `Después de [N] repeticiones` (occurrences).
- **Resumen humano SIEMPRE visible** del patrón elegido: "Se repite cada 2 semanas los lunes y jueves, 8 veces" / "Se repite cada semana el martes, hasta el 30 jul 2026".

**Funcional — display de ocurrencias (mejora):**
- Bloques recurrentes en el calendario muestran el **resumen corto del patrón** (no solo "Semanal/Quincenal").
- Lo pintado = EXACTAMENTE las ocurrencias proyectadas por el BE (fix D3-C — sin expansión client-side), en semana y mes.

**Dominio (extensión BE):**
- `day_of_week` (single) → **`days_of_week: list`** (multi-día) + **`interval: int`** (1=semanal, 2=quincenal, N personalizado). Migración idempotente; compat: bloques existentes → lista de 1 + interval por freq.
- Proyección: `rrule(byweekday=days_of_week, interval=interval, ...)` — rrule ya lo soporta nativo.

**RN-D3F-1:** el resumen humano refleja EXACTAMENTE la regla persistida (misma fuente, no texto paralelo).
**RN-D3F-2:** multi-día × occurrences → `count` cuenta OCURRENCIAS totales (no semanas) — semántica Google.
**RN-D3F-3:** bloques legacy (single day) siguen proyectando idéntico post-migración.

**Scenarios:** `SC-D3F-1` custom L+J cada 2 semanas ×8 → BE proyecta 8 ocurrencias correctas + calendario pinta 8 · `SC-D3F-2` "Todos los días" ×7 → 7 días consecutivos · `SC-D3F-3` resumen humano correcto para cada preset + custom · `SC-D3F-4` bloque legacy pre-migración proyecta idéntico (regression) · `SC-D3F-5` a11y chips días por teclado. Covers → matriz: RN-D3F-1→SC-D3F-3 · RN-D3F-2→SC-D3F-1 · RN-D3F-3→SC-D3F-4. Huecos: ninguno.

#### D3-D.2 · Escenarios de CONSTRUCCIÓN de la página pública (completitud — self-audit /po-ux 2026-06-12, pedido Chris "todo para que funcione bien")

> Cierra los huecos del lote SC-D3D-1..6: la página como artefacto completo (mobile-first, preview WhatsApp, estados degradados).

**RN adicionales:**
- **RN-D3D-6 (perfil parcial):** la página renderiza con las secciones que EXISTAN — mínimo garantizado: identidad (nombre+especialidad+colegiatura+clínica). Sección sin contenido → se omite (nunca caja vacía). Doctor visible ON sin perfil generado → página válida con el mínimo.
- **RN-D3D-7 (preview WhatsApp):** la página emite Open Graph (`og:title` = nombre + especialidad · `og:description` = inicio de Sobre mí o especialidad · `og:image` = foto del doctor o fallback marca) — el link enviado por Adrián muestra card de preview decente en WhatsApp.
- **RN-D3D-8 (foto faltante):** sin foto → avatar iniciales con tint (igual workspace). Nunca imagen rota.
- **RN-D3D-9 (slug inexistente):** `/d/{x}/{y}` desconocido → misma vista "perfil no disponible" genérica (sin distinguir no-existe vs apagado — anti-enumeración).

**Scenarios:**
- `SC-D3D-7` happy · viewport 390×844 (mobile) / abrir página / layout mobile-first correcto sin overflow horizontal + legible · e2e mobile project
- `SC-D3D-8` happy · viewport desktop / misma página / degrada bien (contenido centrado, max-width) · e2e
- `SC-D3D-9` edge · doctor visible ON, perfil NUNCA generado / abrir página / mínimo garantizado renderiza, cero cajas vacías (RN-D3D-6) · e2e real-backend
- `SC-D3D-10` happy · fetch HTML de la página / `og:title`+`og:description`+`og:image` presentes y correctos (RN-D3D-7) · e2e state_check
- `SC-D3D-11` edge · doctor sin foto / página + og:image / avatar iniciales + og fallback (RN-D3D-8) · e2e
- `SC-D3D-12` negative · slug inexistente / "perfil no disponible" idéntico a toggle-OFF (RN-D3D-9, anti-enumeración) · e2e
- `SC-D3D-13` accessibility · página pública / axe wcag2aa 0 violations + navegable teclado · e2e a11y
- `SC-D3D-14` i18n · todo copy de la página Spanish neutro (sin voseo) · grep + e2e
- `SC-D3D-15` happy · workspace: clic "📋 Copiar link" / clipboard contiene URL correcta del entorno; clic "👁 Ver página" / abre la página · e2e

**Matriz addendum:** RN-D3D-6→SC-D3D-9 · RN-D3D-7→SC-D3D-10 · RN-D3D-8→SC-D3D-11 · RN-D3D-9→SC-D3D-12. Huecos: ninguno · SC huérfanos: ninguno.

### § Ledger Delta v3 — estado de construcción (Step 4.5b · actualizado por /dev-team 2026-06-12)

**✅ construido + verificado live (writes reales + logs + efecto):** D3-A completo (SC-D3A-1..4 — e2e 6/6 + live switcher preserva hoja) · D3-B upload/lista/borrar/descargar (SC-D3B-1..5 — POST 201 live + fila + estados; nota: la cadena destapó 3 capas latentes: URL proxy fantasma + FK engine + tabla assets ausente) · D3-C fix + batería (SC-D3C-1..8 — BE 26 tests + live weekly×2 = semanas 0,1,1,0) · D3-E vista mes (SC-D3E-1..4 — 23 vitest + 4 e2e) · D3-F editor+domain (SC-D3F-1..5 — resumen humano exacto live, POST 201 daysOfWeek/interval, migración 042 compat).
**✅ construido, verificación live FINAL en curso:** D3-D página pública (SC-D3D-1..15 — endpoints + ruta /d + og + anti-enum verificados; profileState detail wiring = último parche en vuelo).
**⬜ pendiente:** ninguno del delta. (KPIs tab + Servicios reales = ya diferidos pre-delta a stories propias, sin cambio.)

---

## ★ Reconcile bug7 (rounds 4-6) — ratificado Chris 2026-06-15 (Fase R)

> Deltas verificados live por Chris (G `chris_verify.signoff: SATISFIED`) + ejercidos real-backend por dev-team. Esta sección es el SSoT de comportamiento ratificado para el `/auditor` (allowlist de scope — `chris_verify.rounds` en checkpoint). Detalle por round: `T-FIX-bug7-round{4,5,6}-result.md`.

### Round-4 — día-de-semana (TZ)
- **RN-D3F-4 (paint TZ):** el bloque se pinta en la columna del **día real** seleccionado. `lunes → columna Lun` (nunca Dom). Root cause: `getCurrentWeekMonday()` derivaba la fecha vía `toISOString()` tras `setDate` local → bajo offset UTC negativo (Lima −05) de tarde/noche la semana se anclaba en martes → grilla corrida. Fix: SSoT TZ-estable `src/lib/format/calendarDates.ts` (componentes locales, nunca `toISOString`) + el calendario **descarta** (no clampea) ocurrencias fuera de `[0,6]`. Validador: `bug7-r4-dow.spec.ts` (22 casos, ground truth = DB ISODOW + geometría DOM).

### Round-5 — borrado recurrente con scope + no-crear-pasado
- **RN-D3G-1 (delete scope):** al borrar un bloque **recurrente** la UI ofrece **"Solo este turno"** (`scope=occurrence` → excluye esa fecha de la serie vía `excluded_dates`; resto intacto) y **"Este y los siguientes"** (`scope=this_and_future` → trunca la serie: `end_date = fecha − 1 día`; slots ≥ fecha retirados). `one_off` borra directo (sin diálogo). Citas **confirmadas nunca se borran** en ningún scope. Migración **044** `excluded_dates JSONB`. Endpoint `DELETE …/availability-blocks/{id}?scope=&occurrence_date=` (default `series` = back-compat). Validador: `bug7-r5-dow.spec.ts #1a/#1b/#1c`.
- **RN-D3G-2 (no crear en el pasado):** celdas de fecha/hora pasadas **deshabilitadas** (grisadas, `data-past`, no abren popover). BE rechaza (`422`) crear `one_off` con `specific_date` pasada (+ recurrente con `end_date` pasada). Bloques existentes en el pasado siguen visibles. Validador: `bug7-r5-dow.spec.ts #2-FE` + pytest `test_availability_block_scoped_delete.py` (BE 422).

### Round-6 — "N repeticiones" = N ciclos completos
- **RN-D3F-2 (REVISADA · ver § validators):** "Después de N repeticiones" = **N ciclos COMPLETOS** del patrón (cada repetición incluye TODOS los días). `count = occurrences × len(days_of_week)`. Single-día: N×1 = N (sin cambio). Multi-día: cada semana completa (Mar+Jue ×3 = 6 turnos: 3 Mar + 3 Jue). Resumen FE dice "N repeticiones" (antes "N veces"). Validadores: `bug7-r5-dow.spec.ts #R6` + `bug7-r4-dow.spec.ts case 18` (L+J×8=16) + BE `test_availability_projection.py` + SC-D3F-1/2.
- **Dato pre-fix (open_item, NO bloquea):** bloques multi-día creados ANTES del round-6-fix mantienen su proyección vieja (el count se materializó al crear) → editar (re-proyecta) o recrear.
