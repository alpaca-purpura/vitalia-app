---
story_id: vitalia-shell-state-persistence
brand: vitalia
type: ui-story
state: refining
architecture_pattern: ADR-vitalia-004
new_adr_candidate: ADR-vitalia-006-ssr-safe-persisted-store
cap_target: valeria.shell
cap_change_type: extend
po_ux_version: 2
ratified_by_chris: true
ratified_at: '2026-05-28T20:33:00-05:00'
mockup_gate: exempt
mockup_gate_reason: "no introduce componentes ni estados visuales nuevos — collapsed/rail/full ratificados en F1-S5; solo cambia trigger + persistencia (ratificado Chris 2026-05-28)"
---

# 01-spec — vitalia-shell-state-persistence

> Followup **fix transversal** de la suite shell-organism (Fase 1). NO crea componentes
> nuevos — corrige el **contrato de persistencia** de los stores Zustand bajo SSR + define
> el **comportamiento mobile** del shell para que la usabilidad no se rompa. La parte
> "cómo técnico" (patrón SSR-safe + ADR-vitalia-006) es de `/architect`; este spec fija
> el **qué observable**.

## § Context

- **Release:** F1 (`vitalia/docs/product/releases/F1.yaml`) · `outcome: vitalia-mvp-ui-foundation`
- **Módulo:** shell-organism (chrome agéntico Valeria) — componentes ya `done` Fase 1
- **Parent:** `vitalia-fase1-shell-layout-5050-race-fix` (origen del diagnóstico, ver `00-research.md`)
- **Insertion point:** el shell que envuelve toda ruta `[tenantId]/(shell-organism)/...` — afecta a TODA la app autenticada (transversal)
- **Naturaleza:** `fix` (persistencia rota PROD REAL) + `extend` (1 scenario nuevo: comportamiento mobile-collapsed)

### Bugs que resuelve (confirmados)

1. **Persistencia rota (PROD REAL).** `valeriaState`/`shellMode` NO sobreviven reload. El
   store auto-hidrata contra el default y **pisa `localStorage`** en cada carga (write
   espurio del ciclo persist bajo SSR). Causa raíz confirmada en `checkpoint.md § Causa raíz`.
2. **Drawer mobile auto-abre (acoplado a #1).** A <768px con default `full`, `ValeriaSidebar`
   monta su drawer (`role=dialog`) ABIERTO sin tocar el burger. `useViewportGuard` no cubre <768.

### Decisión de usabilidad ratificada (Chris 2026-05-28): mobile "collapsed pero recuerda"

El comportamiento mobile NO es "forzar collapsed siempre". Es:
- **Default fresh (sin estado mobile recordado):** drawer **cerrado** (collapsed). Mata el auto-open.
- **Recuerda:** si el usuario abre el drawer en mobile, esa elección se recuerda y se restaura en el reload.
- **Independencia desktop/mobile:** el estado del drawer mobile persiste en un slice **separado** de
  `valeriaState` (rail/full/collapsed desktop). Así una preferencia desktop `full` **NUNCA** se traduce
  en auto-open mobile (rompía el acople con bug #1). `/architect` define la forma exacta del store
  (ej. campo persistido `mobileDrawerOpen: boolean` default `false`, o guard mobile sobre slice propio).

### Out of scope (anti-creep)

- Rediseño visual del shell, ribbon, sub-tabs o chat de Valeria (ratificados Fase 1, intactos).
- Sincronización cross-tab de la preferencia (multi-tab broadcast) — defer, no es el bug.
- Migrar `react-resizable-panels` u otra lib (lo evalúa `/architect` solo si es la vía del fix).
- Cambiar el default desktop (`full`) — ratificado por Chris (mockup Fase 1). Se mantiene.

## § Prior art applied

- **Engine consumed:** ninguno — no existe patrón persist/store SSR-safe en `core/@luana/*` para importar.
- **Cross-brand:** ninguno reusable — **solo vitalia** usa Zustand `persist` (grep: comunify/nicolify/lupulo = 0 hits). Sin mirror posible.
- **Reused (propio vitalia):** los 4 stores `persist` existentes son el scope (shell-store, tenant-store, agenda-store, agenda-filters-store) — el fix aplica el mismo patrón a todos.
- **Learnings aplicados:** 0 hits en `docs/learnings/` + `vitalia/docs/learnings/` para `hydrat|zustand|ssr`. El research de esta story (`00-research.md`) documenta 4 técnicas probadas que NO convergieron — `/architect` NO debe repetirlas tal cual.
- **Lift candidate detectado:** si el patrón SSR-safe sale limpio → learning `promotable: candidate` para `/pm-luana` (Next 16 + Zustand persist aplica a futuros brand frontends).
- **Net-new justificado:** patrón "persisted store SSR-safe" brand-local + `ADR-vitalia-006` candidate — `ADR-vitalia-004` (shell sub-tab) NO cubre persistencia-bajo-SSR (gap real).

## § Gherkin scenarios

> Los IDs `[REG-*]` mapean a tests de regresión YA escritos (hoy `.skip`). Los `[UNIT-*]`
> son unit tests vitest nuevos del hydration del store (el bug es timing SSR+hydration,
> caro de iterar solo por E2E).

### SC-1 · happy — `valeriaState` sobrevive reload `[REG: resize-and-state.spec.ts → "shell state (valeriaState) survives reload"]`
```gherkin
Given un usuario autenticado en una ruta del shell en desktop (≥1104px)
  And setea valeriaState='rail' (shortcut "r" o control de rail)
  And localStorage['vitalia-shell-state'].valeriaState === 'rail'
When recarga la página (full reload)
Then localStorage['vitalia-shell-state'].valeriaState sigue siendo 'rail'
  And el shell renderiza Valeria en estado 'rail' (no vuelve a 'full')
```
- `playwright_required: true`
- graders:
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/shell-state-persistence/valeria-state-survives-reload.spec.ts" }`
  - `{ type: state_check, target: localStorage, query: "vitalia-shell-state.valeriaState", expect: "rail" }`

### SC-2 · happy — `shellMode` sobrevive reload
```gherkin
Given un usuario en desktop con shellMode='web' seteado vía el toggle
  And localStorage['vitalia-shell-state'].shellMode === 'web'
When recarga la página
Then shellMode sigue siendo 'web' en localStorage y en el render
```
- `playwright_required: true`
- graders: `{ type: state_check, target: localStorage, query: "vitalia-shell-state.shellMode", expect: "web" }`

### SC-3 · adversarial (el bug exacto) — NO hay write espurio del default durante el ciclo SSR+hydration `[UNIT + REG]`
```gherkin
Given localStorage['vitalia-shell-state'].valeriaState === 'rail' (preferencia previa)
When la página atraviesa el ciclo SSR-skeleton → hydration → client-mount (reload)
Then en NINGÚN momento se escribe valeriaState='full' (el default) a localStorage
  And el primer valor observable post-hydration es 'rail'
```
- `playwright_required: true` (+ unit determinista)
- graders:
  - `{ type: unit, path: "vitalia/frontend/src/stores/__tests__/shell-store-hydration.test.ts", note: "mock localStorage + SSR flag: rehidratar NO debe disparar setItem con el default" }`
  - `{ type: e2e, note: "instrumentar localStorage.setItem y assert que 'full' nunca se escribe cuando había 'rail' guardado" }`

### SC-4 · happy mobile (★ scenario NUEVO — `extend`) — fresh user arranca collapsed sin auto-abrir drawer `[REG: mobile-collapse.spec.ts → "ValeriaSlot oculto mobile"]`
```gherkin
Given un viewport mobile (<768px)
  And NO hay estado de drawer mobile recordado (usuario nuevo / storage limpio)
When el shell monta
Then el drawer mobile arranca CERRADO (role=dialog NO presente/abierto en el DOM)
  And el burger (botón de apertura) es visible y accesible
  And esto es independiente de cualquier valeriaState desktop persistido (ej. 'full' NO auto-abre)
```
- `playwright_required: true`
- graders:
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/shell-state-persistence/mobile-collapsed-default.spec.ts" }`
  - `{ type: visual_state, screen: "mobile-initial", element: "[role=dialog]", expect: "not-present" }`

### SC-5 · happy mobile — el burger abre el drawer on-demand
```gherkin
Given mobile (<768px) con el drawer cerrado
When el usuario toca el burger
Then el drawer (role=dialog) se abre con Valeria
  And el foco se mueve al drawer (focus trap activo)
```
- `playwright_required: true`
- graders: `{ type: e2e, note: "tap burger → role=dialog visible + focus dentro" }`

### SC-5b · happy mobile (★ "recuerda" — decisión Chris) — el drawer mobile recuerda su estado entre reloads
```gherkin
Given mobile (<768px) y el usuario abrió el drawer (burger)
  And el slice de drawer mobile quedó persistido como abierto
When recarga la página (mobile)
Then el drawer se restaura ABIERTO (recuerda la elección del usuario)
When luego el usuario cierra el drawer y recarga de nuevo
Then el drawer se restaura CERRADO
  And en ningún caso el estado mobile altera el valeriaState desktop persistido (slices independientes)
```
- `playwright_required: true`
- graders:
  - `{ type: e2e, note: "abrir drawer → reload → sigue abierto; cerrar → reload → sigue cerrado" }`
  - `{ type: state_check, target: localStorage, note: "slice mobile-drawer persiste separado de valeriaState" }`

### SC-6 · edge / empty_state — primera visita sin preferencia guardada
```gherkin
Given localStorage NO tiene 'vitalia-shell-state' (usuario nuevo / storage limpio)
When monta el shell en desktop
Then Valeria arranca en el default 'full' y shellMode='agentic'
  And se escribe localStorage UNA vez con el default (no hay clobber — no había nada que pisar)
```
- `playwright_required: true`
- graders: `{ type: state_check, target: localStorage, query: "vitalia-shell-state", expect: "{valeriaState:'full',shellMode:'agentic'}" }`

### SC-7 · negative / adversarial — `localStorage` corrupto no rompe el shell
```gherkin
Given localStorage['vitalia-shell-state'] contiene JSON inválido o un valueState fuera del enum
When monta el shell
Then el store cae al default de forma segura (sin crash, sin pantalla en blanco)
  And no se propaga la corrupción al render
```
- `playwright_required: true`
- graders: `{ type: unit, note: "seed localStorage con basura → store hidrata a default sin throw" }`

### SC-8 · accessibility (WCAG AA) — drawer mobile + burger navegables por teclado
```gherkin
Given mobile (<768px) en 'collapsed'
When el usuario navega con teclado (Tab al burger → Enter)
Then el drawer abre, el foco entra al drawer, Escape lo cierra y devuelve foco al burger
  And el burger tiene aria-label en español neutro y aria-expanded refleja el estado
```
- `playwright_required: true`
- graders: `{ type: axe, ruleset: "wcag2aa" }` · `{ type: e2e, note: "keyboard open/close + focus return" }`

### Sub-categorías mandatory — cobertura / not_applicable

| Sub-categoría | Estado | Cubre / razón |
|---|---|---|
| `race_condition` | not_applicable | persistencia client-local single-tab; sin create/unique-constraint. (Cross-tab fuera de scope.) |
| `concurrent_users` | not_applicable | store client-local; no hay server data ni multi-tenant query en este path. |
| `network_failure` | not_applicable | el path de persistencia es `localStorage` puro; sin fetch de red. |
| `empty_state` | ✅ SC-6 | primera visita sin preferencia guardada. |
| `large_dataset` | not_applicable | el store persiste 2 enums; no hay listas/paginación. |
| `accessibility` | ✅ SC-8 | drawer + burger teclado/screen-reader WCAG AA. |
| `i18n` | not_applicable | no introduce copy nuevo; el `aria-label` del burger ya existe en español neutro (se verifica en SC-8, no cambia). |

> Todos los `not_applicable` por naturaleza del fix (persistencia/SSR client-local). Requiere ratificación Chris en Step 5 gate.

## § Wireframe (referencia — sin mockup nuevo)

Visual SSoT = mockups Fase 1 ya ratificados (mockup gate exento, ver abajo):
- `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html` (estados collapsed/rail/full)
- `vitalia/docs/archive/2026/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` (shell integral)

Esta story no cambia el aspecto de ningún estado — solo **cuándo** se aplica (default mobile cerrado)
y la **persistencia** (invisible). El contrato visible queda en § Estados visuales abajo.

## § Estados visuales

| Estado | Trigger | Valeria | Drawer mobile | Notas |
|---|---|---|---|---|
| `desktop-restored` | ≥1104px + preferencia guardada | el valor persistido (`rail`/`full`/`collapsed`) | n/a | SC-1/SC-2 — sobrevive reload |
| `desktop-default` | ≥1104px + sin preferencia | `full` / `agentic` | n/a | SC-6 — primera visita |
| `tablet-guard` | [768,1104) | forzado `rail` (guard existente, sin cambio) | n/a | comportamiento Fase 1 intacto |
| `mobile-collapsed` | <768px, sin estado mobile recordado o último=cerrado | n/a (drawer es el toggle) | cerrado (no en DOM) | SC-4 — **nuevo**. Default fresh = cerrado, independiente de valeriaState desktop |
| `mobile-drawer-open` | <768px + tap burger, O último estado recordado=abierto | drawer con Valeria | abierto (`role=dialog`, focus trap) | SC-5 / SC-5b — recuerda entre reloads |

## § Componentes (todos REUSADOS — cero nuevos)

| Componente | Path | Cambio |
|---|---|---|
| `useShellStore` | `vitalia/frontend/src/stores/shell-store.ts` | patrón persist SSR-safe (`/architect`) |
| `useTenantStore` + agenda stores | `vitalia/frontend/src/stores/tenant-store.ts`, `features/valeria/store/*` | mismo patrón (transversal) |
| `ShellOrganismLayout` (+ Skeleton) | `.../shell-organism/ShellOrganismLayout.tsx` | skeleton NO debe consumir el store (boundary) |
| `TopBarGlobal` | `.../shell-organism/TopBarGlobal.tsx` | no suscribir store en contexto skeleton/SSR |
| `ValeriaSidebar` | `.../shell-organism/ValeriaSidebar.tsx` | drawer cerrado por default mobile |
| `useViewportGuard` | `.../shell-organism/useViewportGuard.ts` | extender a <768 → `collapsed` (one-way) |

> Ningún componente Shadcn primitive (`components/ui/`) ni shared cross-feature se toca. El fix vive en stores + shell-organism. `/architect` define el patrón exacto.

## § Data flow (conceptual — `/architect` lo concreta)

- **Sin API.** Estado 100% client-local vía Zustand `persist` (`localStorage`, key `vitalia-shell-state`).
- **Hydration:** el store debe hidratar **solo client-side** (dentro del chunk `ssr:false`), sin escribir el default durante SSR/skeleton/pre-hydration.
- **Viewport guard:** one-way force en mount — `[768,1104)` → `rail` (existente); `<768` → `collapsed` (nuevo). Desktop ≥1104 respeta el valor persistido.

## § Microcopy

Sin copy nuevo. El `aria-label` del burger y los controles existentes se mantienen en español neutro LatAm (verificado en SC-8). No se introduce voseo.

## § Responsive breakpoints (contrato observable)

- `< 768px` (mobile): drawer arranca **cerrado por default** (fresh); **recuerda** abierto/cerrado entre reloads vía slice mobile independiente. Burger abre. **(decisión usabilidad ratificada Chris)**
- `[768, 1104)` (tablet): guard fuerza `rail` (Fase 1, sin cambio).
- `≥ 1104px` (desktop): respeta la preferencia persistida `valeriaState` (`full` default si no hay).

## § Accessibility

- Burger: `aria-label` español neutro + `aria-expanded` sincronizado con el estado del drawer.
- Drawer mobile: focus trap al abrir, `Escape` cierra y devuelve foco al burger, `role=dialog` + `aria-modal`.
- Sin regresión de contraste/teclado en los estados ratificados Fase 1.

## § Mockup gate (ADR-vitalia-003) — RATIFICADO EXENTO (Chris 2026-05-28)

Esta story **NO introduce componentes ni estados visuales nuevos**: `collapsed`/`rail`/`full`
de `ValeriaSidebar` + drawer mobile ya fueron ratificados visualmente en Fase 1 (F1-S5
`valeria-rail.html` + estados). Solo cambia **cuándo** se aplica el estado cerrado (default
mobile) y la **persistencia** (invisible). → **Exenta de mockup-per-component nuevo**
(cae en "modifica comportamiento de componente ya ratificado"). Ratificado por Chris.

## § Architecture handoff note (para `/architect`)

- El fix es **arquitectónico + transversal** (4 stores persist). Producir/citar **ADR-vitalia-006
  "SSR-safe persisted store"**.
- Evaluar Opción surgical (skeleton store-free + hydration gate) vs Opción patrón (factory
  `createPersistedStore()` SSR-safe aplicado a los 4 stores). Documentar tradeoff.
- NO repetir las 4 técnicas fallidas de `00-research.md`.
- **Mobile "recuerda" (ratificado):** el estado abierto/cerrado del drawer mobile persiste en un
  slice **independiente** de `valeriaState` (default cerrado). Definir la forma exacta (ej. campo
  `mobileDrawerOpen: boolean` en shell-store, o guard mobile sobre slice propio) — clave: una
  preferencia desktop `full` NO debe auto-abrir el drawer mobile.
- Des-skipear los 3 tests de regresión + agregar unit tests de hydration + tests "recuerda" (SC-5b).
