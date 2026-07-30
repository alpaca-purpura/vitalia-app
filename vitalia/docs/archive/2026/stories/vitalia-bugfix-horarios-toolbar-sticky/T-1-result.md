<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-1 result — Horarios toolbar sticky (Carril R fix-and-own)

**Verdict:** PASS (vitalia-local fix; NO core escalation)
**Date:** 2026-06-15
**Brand:** vitalia · Story: vitalia-bugfix-horarios-toolbar-sticky
**Live-verify:** deferred to PM (no Chrome DevTools MCP in this lane; FE :3002 hot-reload running)

## Diagnóstico — los DOS eslabones rotos de la cadena de scroll

La barra de opciones (toolbar de la página Horarios) se desplazaba porque el scroll
NO vivía en la grilla de horas — vivía en un contenedor más externo que arrastraba
todo el contenido de la hoja (toolbars incluidos). Confirmé el diagnóstico del PM
trazando la cadena real desde el content-slot hacia abajo, y encontré que el break
NO está bajo `EntityWorkspaceLayout` (core) sino DENTRO de la hoja vitalia, en dos
links que perdían su `min-h-0`/clamp:

Cadena real (la hoja se monta en `StaffWorkspaceShell` → `EntityWorkspaceLayout`, no
directo en la página):

```
EntityWorkspaceLayout content slot   flex-1 min-h-0 overflow-auto    ← CORE (no tocar) · scroller externo
  └─ DoctorHorariosView root         flex flex-col h-full min-h-0    ← ROTO #1: sin overflow-hidden
       ├─ heading franja              flex-shrink-0                   TOOLBAR 1
       └─ wrapper                     flex-1 min-h-0 overflow-hidden
            └─ AvailabilityCalendar   flex flex-col h-full
                 ├─ header franja      flex-shrink-0                  TOOLBAR 2
                 ├─ grid               flex-1 overflow-auto           ← ROTO #2: sin min-h-0
                 │    └─ day-header     sticky top-0                  (OK)
                 └─ hint               flex-shrink-0
```

**Roto #1 — `DoctorHorariosView` root sin `overflow-hidden`.** El content-slot de
`EntityWorkspaceLayout` es `overflow-auto` (CORE, canon N3 — no es nuestro). Como la
hoja no clampaba su propio overflow, cuando la grilla de 24h crece (24×48px = 1152px)
el contenido excede el box del slot, el SLOT scrollea, y las franjas toolbar
(flex-shrink-0) viajan con él.

**Roto #2 — grilla de horas `flex-1 overflow-auto` SIN `min-h-0`.** Un flex item
`flex-1` en columna tiene `min-height: auto` por default → NO encoge por debajo de su
contenido. La grilla se quedaba a 1152px de alto, `overflow-auto` nunca se activaba, y
el overflow burbujeaba hacia arriba (al header y, vía #1, al slot externo).

Ambos eslabones debían arreglarse: con sólo #1 la hoja clampa pero la grilla sigue sin
scrollear internamente; con sólo #2 la grilla scrollea pero el slot externo todavía
puede ganar. Los dos juntos fuerzan que el scroll viva SOLO en la grilla.

## Fix (vitalia-local, CSS/flex mínimo)

- `DoctorHorariosView.tsx` root: `flex flex-col h-full min-h-0` → **`+ overflow-hidden`**.
  Hace de la hoja el límite de scroll; el slot core `overflow-auto` ya nunca necesita
  scrollear porque su hijo nunca lo excede.
- `AvailabilityCalendar.tsx` grilla (`role="grid"`): `flex-1 overflow-auto` →
  **`flex-1 min-h-0 overflow-auto`**. Deja que el item encoja y que `overflow-auto`
  realmente capture el scroll de las horas. El day-header se mantiene fijo vía su
  `sticky top-0` existente.

Las dos franjas toolbar (`flex-shrink-0`) y el day-header (`sticky top-0`) ya estaban
correctos — quedan fijos una vez que el scroll se confina a la grilla.

## Engine boundary — NO escalation

NO se tocó `core/@luana/ui-kit/EntityWorkspaceLayout.tsx`. El content-slot
`overflow-auto` del core es válido y compartido por todas las marcas; el fix correcto
era confinar el scroll en la hoja vitalia (clamp + min-h-0), no cambiar el slot core.
Cambiar `overflow-auto`→`overflow-hidden` en el core habría afectado todas las marcas
→ habría requerido /pm-luana promotion gate. Preferí el fix en la hoja, como pidió la
tarea (punto 3 HARD).

## No-rompe

- **Vista Mes (`MonthCalendar`):** sin cambios; suite month-calendar verde (23/23).
- **Drag-to-create:** los window-listeners computan `e.clientY - column.getBoundingClientRect().top`.
  Ambos son viewport-relativos. Mover el scroll a la grilla interna no desfasa el
  hit-test: cuando la grilla scrollea, el `rect.top` de la columna se mueve
  viewport-relativo igual que `clientY`, así que `clientY - rect.top` sigue siendo el
  offset correcto dentro de la columna. Sin desync. Suite de drag (hour-from-client-y +
  past-cell) verde.

## Regression guard (TDD RED→GREEN)

Nuevo: `…/horarios/__tests__/horarios-toolbar-sticky.test.tsx` (5 structural-class asserts).
jsdom no tiene motor de layout (no puede medir scrollHeight) → guard estructural por
clases load-bearing. Documentado en el header del test.

- **RED** (source revertido — quito `overflow-hidden` del root y `min-h-0` de la grilla):
  2/5 tests FALLAN (`DoctorHorariosView root clamps overflow`, `grid owns the scroll`).
- **GREEN** (fix aplicado): 5/5 PASS.

Asserts: root tiene `overflow-hidden`+`h-full`+`min-h-0` · grilla `role=grid` tiene
`flex-1`+`min-h-0`+`overflow-auto` · franja toolbar página `flex-shrink-0` · franja
header calendario `flex-shrink-0` · day-header `sticky top-0`.

## Gates (native host, workspace root — NO Docker)

| Gate | Comando | Estado |
|---|---|---|
| TypeScript strict | `npx tsc --noEmit` | ✅ exit 0 |
| ESLint | `npx eslint src/features/lisa --cache` | ✅ exit 0 |
| Vitest horarios | `npx vitest run …/horarios` | ✅ 6 files / 34 tests |
| Vitest full (horarios + month-calendar + integration) | idem + month-calendar.test.tsx + horarios.test.tsx | ✅ 8 files / 74 tests |
| Regression guard RED→GREEN | nuevo test | ✅ RED 2/5 fail → GREEN 5/5 pass |

## Archivos tocados

- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/DoctorHorariosView.tsx` (root `+overflow-hidden` + comentario)
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx` (grilla `+min-h-0` + comentario)
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/__tests__/horarios-toolbar-sticky.test.tsx` (NUEVO — regression guard)

## Pendiente PM (sesión main)

Live-verify del scroll real en dev-app `/lisa/staff/{doctorId}/horarios`: scrollear
07:00→21:00 y "Mostrar 24 horas" → confirmar que las dos franjas toolbar + day-header
quedan FIJOS y sólo scrollea la grilla de horas (paridad N2/N3). Confirmar también que
drag-to-create sigue aterrizando en la celda correcta tras scrollear.
