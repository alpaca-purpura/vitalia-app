---
story_id: vitalia-bugfix-horarios-toolbar-sticky
type: bugfix
architecture_pattern: ADR-vitalia-004
module: clinics                                   # bucket code:clinics (cap clinics.lisa.doctores) — story-closure-gate cross-module

# Release entity (contenedor temporal · lifecycle.md § 5)
release: F2

# Capability lineage (v2 cement 2026-05-27)
cap_target: clinics.lisa.doctores                 # toolbar Horarios del workspace de doctor
cap_change_type: fix                              # bugfix CSS/layout · NO toca scenarios ni comportamiento
parent_story: null

state: done
phase_workflow: DONE
last_artifact: 07-merge.md
last_modified: 2026-06-15
next_action: "DONE — merged (07-merge.md). chris_verify SATISFIED. cap change_log type=fix en clinics.lisa-doctores. Core fix @luana/ui-kit 0.4.1 (commit 88c56dc9/2657203d) + @source 6597b3b1."
ratified_by_chris: true
spawned_at: 2026-06-15
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: null

chris_verify:
  required: true                                  # bugfix funcional UI → demo_required (#37 + story-closure-gate G)
  signoff:
    by: Chris
    date: 2026-06-15
    result: SATISFIED
    notes: "Chris confirmó live (incognito fresco): toolbar de Horarios queda fijo al scrollear (paridad N2/N3)."
    open_items: []
  rounds: []
audit_iterations: 0
defer_audit: false
defer_audit_reason: null
parked_reason: null
dropped_reason: null

# Autonomous-mode bugfix lite (Chris opt-in este turn): salta /architect ready package + /dev-team full build.
# Opus auditor-frontend (Carril R fix-and-own v5) implementa; main session live-verifica.
autonomous_mode: false                            # G (chris-verify) lo cubre el live-verify del PM + eyeball Chris

# Bugfix repro-first gate (ADR-011 · hereda hotfix-repro-mandatory.md)
hotfix_metadata:
  repro_verified: true
  trace_evidence:
    source: chris-report+screenshot
    ref: "/tmp/1100.png — Lisa > Staff > {doctor} > Horarios. Chris: 'la barra de opciones debería ser fixed, igual que el tab del módulo (N2) y los sub-tabs (N3)'. Al scrollear el calendario, el toolbar de la página (Disponibilidad + Semana/Mes + nav-semana ‹/› + Mostrar 24 horas) se desplaza en vez de quedar fijo."
  diagnosis_validates_handoff: true
  reproduced_local: false                         # a confirmar LIVE por el auditor + PM antes del fix

# Dev-app live verification gate (ADR-vitalia-008 · #37) — REQUIRED (toca superficie user-reachable)
dev_app_verified:
  required: true
  evidence:
    - action: "DIAGNÓSTICO (fix del agente inefectivo): live dev-app /lisa/staff/{doctorId}/horarios (auth dr.demo@vitalialat.com, 1280×720, 24h), medí rect.top al scrollear el scroller real."
      observed: "Bug confirmado: scroller real = content div CORE de AppPanelSlot (574/1410); al scrollear 836px los 4 toolbars se iban (heading 209→-627). Root cause: AppPanelSlot content-area era block + overflow-y-auto; EntityWorkspaceLayout usa flex-1 esperando padre flex → no clampaba."
    - action: "FIX core aplicado (@luana/ui-kit AppPanelSlot:137 +`flex flex-col` → 0.4.1) + re-verify LIVE en dev-app (mismo flujo, post FE restart + hard-reload bust cache)."
      observed: "FIXEADO: EWL clampa (574/574), grilla = único scroller interno (361/1197), toolbars FIJOS al scrollear grid 836px (heading 209→209, nav 272→272), day-header sticky, página no scrollea, bloque scrolleó 836px. Screenshot live-verify-fixed-scrolled.png. Guard Playwright behavioural corrió LIVE = 3 passed."
    - action: "DOWNSTREAM nicolify — live dev-app.nicolify.com (auth owner.demo@nicolify.com, fix aplicado a su core+restart)."
      observed: "Shell renderiza sano, content-area flex-col compilado, frame fijo, contenido normal scrollea dentro del content-area (probe 2000px→1960px, página no scrollea) → fix preserva scroll normal, cero regresión. Screenshot downstream-nicolify-shell.png. Mecánico: nicolify 198 tests + tsc verdes."
    - action: "DOWNSTREAM comunify + lupulo — verificación de consumo (2026-06-15, 2FA ya off)."
      observed: "comunify NO es consumer de @luana/ui-kit (0 imports, no en package.json, shell propio/pre-lift); lupulo placeholder (0 imports). El fix no puede alcanzarlos → fuera de scope, live-verify N/A. Consumers reales = vitalia + nicolify, AMBOS live-verificados → downstream COMPLETO. (comunify 38 tests verdes = su suite propia, no downstream del shell.)"
dod_live_verified: true                           # vitalia ejercido live (write/scroll real + efecto + logs); nicolify downstream live; comunify mecánico
dod_evidence:
  - action: "Scroll real del calendario Horarios (24h) con doctor seleccionado, dev-app vitalia"
    observed: "toolbars (Disponibilidad + Semana/Mes + nav-semana + Mostrar 24 horas) + day-header quedan FIJOS; solo scrollea la grilla de horas (paridad N2/N3). Confirmado por mediciones rect.top + Playwright 3-passed + screenshot."
    backend_log: "n/a — fix puramente FE/layout (sin writes BE); ejercido en el stack dev real corriendo."
verified_at: 2026-06-15
---

# Bugfix — toolbar de Horarios (Lisa STAFF) no queda fijo al scrollear

## Síntoma (cómo se ve)

Ruta: `…/lisa/staff/{doctorId}/horarios` (doctor seleccionado).
Screenshot: `/tmp/1100.png`.

Chris (2026-06-15): la **barra de opciones** de la vista Horarios **debería ser fixed**, igual
que el tab del módulo (N2: Marca/Staff/…) y los sub-tabs (N3: Perfil/Horarios/…) que **sí**
quedan fijos. Hoy, al scrollear el calendario (07:00→21:00/24h), el toolbar de la página se
desplaza fuera de vista.

"Barra de opciones" = el toolbar propio de la hoja Horarios:
- `DoctorHorariosView` header: **Disponibilidad** + toggle **Semana | Mes**
- `AvailabilityCalendar` header: nav de semana **‹ [rango] ›** + **Mostrar 24 horas**

## Diagnóstico inicial (PM · static code trace — a confirmar live)

- N3 (`EntitySubNavBar` en `@luana/ui-kit`) ya es `sticky top-0` y vive **fuera** del scroll
  container → queda fijo ✓ (consistente con que Chris ve N2/N3 fijos).
- **Por código**, el toolbar de Horarios YA está pensado para quedar fijo:
  - `DoctorHorariosView` heading wrapper = `flex-shrink-0`.
  - `AvailabilityCalendar` header (nav + 24h) = `flex-shrink-0`.
  - El scroll está pensado en la grilla interna: `<div className="flex-1 overflow-auto">`,
    con el day-header row `sticky top-0`.
- Que el toolbar igual scrollee ⇒ **cadena flex/`min-h-0`/`h-full` rota**: el scroll ocurre
  en un contenedor MÁS EXTERNO (probablemente el content-slot de `EntityWorkspaceLayout`
  `flex-1 min-h-0 overflow-auto`) en vez de en la grilla interna → todo el contenido de la
  hoja (incluido el toolbar) se desplaza.
- Como N3 queda fijo, el break está **en/bajo `EntityWorkspaceLayout`** (no arriba).

## Cadena de layout (mapa para el implementador)

```
@luana/ui-kit ShellLayout (core · vía ShellLayoutWire)        ← N1 ribbon + N2 + Valeria sidebar
  └─ [agent]/[…] panel-content slot
       └─ EntityWorkspaceLayout (core @luana/ui-kit)          ← N3 (EntitySubNavBar sticky ✓)
            div: flex flex-col flex-1 min-h-0 overflow-hidden
            ├─ EntitySubNavBar (sticky top-0)                  ← N3 FIJO ✓
            └─ content slot: div flex-1 min-h-0 overflow-auto  ← ⚠️ sospechoso (¿scrollea acá?)
                 └─ DoctorHorariosView (flex flex-col h-full min-h-0)   [vitalia]
                      ├─ heading + Semana/Mes (flex-shrink-0)           ← TOOLBAR 1
                      └─ wrapper (flex-1 min-h-0 overflow-hidden)
                           └─ AvailabilityCalendar (flex flex-col h-full)
                                ├─ header nav + 24h (flex-shrink-0)     ← TOOLBAR 2
                                ├─ grid (flex-1 overflow-auto)          ← scroll DEBE vivir acá
                                └─ hint (flex-shrink-0)
```

Archivos:
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/DoctorHorariosView.tsx`
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx`
- (core, NO tocar sin escalar) `core/@luana/ui-kit/src/EntityWorkspaceLayout.tsx`

## Bar de verificación (DONE)

- En `…/horarios` con doctor seleccionado y bloques que excedan el viewport, al scrollear el
  calendario: el toolbar (Disponibilidad + Semana/Mes + nav-semana + Mostrar 24 horas) y el
  day-header row **permanecen fijos**; SOLO scrollea la grilla de horas. Verificado **LIVE**
  en dev-app (scroll real + screenshot), no por suite verde ni GET 200.
- Sin regresión en `Mes` (MonthCalendar) ni en drag-to-create (los window-listeners del drag
  computan contra `getBoundingClientRect` de la columna — confirmar que el nuevo scroll no
  desfasa el hit-test).
- `cap_change_type: fix` → al merge, append `change_log` type=fix al cap `clinics.lisa.doctores`
  (sin scenarios nuevos). No cambia comportamiento de producto.

## Notas de scope

- Fix esperado **vitalia-local** (CSS/flex en la hoja Horarios). Si el ÚNICO fix correcto cae
  en core `@luana/ui-kit/EntityWorkspaceLayout` → **STOP + escalar a /pm-vitalia** (engine
  boundary → afecta todas las marcas → promotion gate `/pm-luana`).
- Tipo `bugfix` (lite, repro-first · ADR-011) — salta mockups/diseño; el repro es la conducta
  observada + el screenshot.
