# T-1 LIVE-VERIFY — Horarios toolbar sticky (PM /pm-vitalia · Chrome DevTools MCP)

**Fecha:** 2026-06-15 · **Verdict:** BUG PRESENTE (fix del subagente inefectivo) · root cause = **CORE** → escalar /pm-luana.
**Entorno:** dev-app.vitalialat.com (cloudflared → :3002), auth `dr.demo@vitalialat.com`, viewport 1280×720, vista "Mostrar 24 horas" (24×48=1152px fuerza overflow).

## 1. El fix del subagente NO funcionó (verde-fantasma)

El Opus auditor-frontend devolvió PASS con guard "RED→GREEN" + gates verdes, pero su guard es
un test estructural en **jsdom (sin motor de layout)** → solo verifica que existan clases, no
la conducta real. Live-verify lo refuta:

- Scroller real = **content div de CORE `AppPanelSlot`** (`flex-1 min-h-0 overflow-y-auto`):
  `clientH 574 / scrollH 1410`.
- Al scrollear ese scroller 836px → los 4 toolbars se van de pantalla:
  `heading 209→-627`, `semana 214→-622`, `navPrev 272→-564`, `toggle24 272→-564`.
- N3 (`EntitySubNavBar`) NO se va: tiene `sticky top-0` → por eso Chris lo ve fijo.

(Mi primera medición dio falso `toolbarsFixed:true` porque scrolleé `grid.scrollTop`, que no
es el scroller — `grid.scrollHeight === clientHeight`. Al ubicar el scroller real, el bug saltó.)

→ Refuerza [[verification-real-not-200]]: un guard estructural jsdom para un bug de **layout**
da confianza falsa. El guard correcto es Playwright real (scroll + medir `rect.top`).

## 2. Root cause REAL (cadena de altura, viewport 672 útil)

```
app-panel-slot (core)            flex h-full min-h-0 flex-col overflow-hidden   clientH 672  ✓ bounded
 └ content div (core AppPanelSlot:137)  flex-1 min-h-0 overflow-y-auto · BLOCK  clientH 574 / scrollH 1410  ← SCROLLER
    └ EntityWorkspaceLayout (core)  flex flex-col flex-1 min-h-0 overflow-hidden  clientH 1410  ← NO clampa
       ├ EntitySubNavBar (N3)       sticky top-0                                  (sobrevive)
       └ content slot (core)        flex-1 min-h-0 overflow-auto                  1410
          └ DoctorHorariosView      flex flex-col h-full min-h-0 overflow-hidden  1367   [vitalia]
             ├ heading + Semana/Mes  flex-shrink-0                                TOOLBAR 1
             └ wrapper               flex-1 min-h-0 overflow-hidden
                └ AvailabilityCalendar flex flex-col h-full                       1271
                   ├ header nav+24h   flex-shrink-0                              TOOLBAR 2
                   └ grid             flex-1 min-h-0 overflow-auto  1197/1197 (no scrollea internamente)
```

**El eslabón roto NO está en los componentes vitalia** (DoctorHorariosView/AvailabilityCalendar,
que el agente tocó). Está en el **montaje core**:

- `AppPanelSlot` (core `core/@luana/ui-kit/src/organism/shell/AppPanelSlot.tsx:137`) renderiza
  el área de contenido como **`<div className="flex-1 min-h-0 overflow-y-auto">` (display:block)**
  — su comentario dice "único contenedor scrolleable de la hoja" (correcto para páginas normales).
- `EntityWorkspaceLayout` (core) usa **`flex-1`** en su root, esperando un **padre flex-column**
  para clampar. Pero su padre (el content div) es **block** → su `flex-1` es **inerte** → EWL
  crece a la altura de su contenido (1410) → el content div scrollea TODO (toolbars incluidos);
  N3 sobrevive solo por su `sticky`.

Es un **mismatch de contrato entre dos componentes CORE** (`AppPanelSlot` block-scroll ↔
`EntityWorkspaceLayout` flex-child). Afecta **toda marca que monte EWL dentro del shell**:
vitalia (lisa/staff + adrián/embudo lead), nicolify (embudo lead workspace), comunify.

## 3. Fix CORE verificado live (1 línea)

`core/@luana/ui-kit/src/organism/shell/AppPanelSlot.tsx:137`:
```diff
- <div className="flex-1 min-h-0 overflow-y-auto">
+ <div className="flex flex-col flex-1 min-h-0 overflow-y-auto">
```
Hacer el área de contenido una **flex-column** (sin quitar `overflow-y-auto`). Verificado en vivo:

| métrica | baseline (bug) | con fix |
|---|---|---|
| content div (panel) | 574 / scrollH 1410 → scrollea | 574 / 574 → **fijo** ✓ |
| EntityWorkspaceLayout | clientH 1410 (no clampa) | 574 / 574 → **clampa** ✓ |
| grid horas | 1197/1197 (no scroller) | 361 / 1197 → **scroller interno** ✓ |
| toolbars al scrollear grid 836px | −836px (se van) | **0 (FIJOS)** ✓ |
| panel content scrollTop | — | **0 (no scrollea)** ✓ |

Páginas normales (hoja = un solo bloque alto) en una flex-column con `overflow-y-auto` siguen
scrolleando (el bloque crece, el content div scrollea) → **no rompe** el caso común. (A confirmar
por el promotion gate + downstream regression per-brand — `auditor-downstream-regression.md`.)

**Complemento vitalia (ya aplicado por el agente, load-bearing CON el fix core):**
`AvailabilityCalendar` grid `+min-h-0` (deja que la grilla encoja y capture el scroll). Sin el
fix core no tiene efecto; con él, es necesario.

## 4. Por qué esto es engine boundary (no /pm-vitalia)

`@luana/ui-kit` es engine compartido (27 paquetes core). Modificarlo requiere el **promotion gate
`/pm-luana`** + verificación downstream en cada marca consumidora (vitalia/nicolify/comunify).
`anti-duplication.md` + `auditor-downstream-regression.md` + el constraint HARD de esta story
(scope notes) lo exigen. /pm-vitalia NO toca core.

## 5. Pendiente

1. **Chris ratifica** el cambio de scope: lo que parecía bugfix UI minimal vitalia-local es un
   fix CORE cross-brand (3 marcas). Sigue siendo chico (1 línea core + 1 complemento), pero pasa
   por `/pm-luana`.
2. `/pm-luana`: promotion proposal `@luana/ui-kit AppPanelSlot` + aplicar + **downstream regression
   per-brand** (montar EWL en vitalia lisa+adrián, nicolify embudo, comunify; live-verify scroll).
3. Reemplazar el guard estructural jsdom por un **Playwright real** (scroll + assert toolbar
   fixity) — el jsdom no puede medir layout (verde-fantasma).
4. Re-correr este live-verify post-fix en las 3 marcas → recién ahí `dod_live_verified: true`.
