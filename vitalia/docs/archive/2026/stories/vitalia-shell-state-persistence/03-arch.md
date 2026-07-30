---
story_id: vitalia-shell-state-persistence
brand: vitalia
arch_version: 1
schema_version: v4.1
architect_run_on: '2026-05-29'
architecture_pattern: ADR-vitalia-004
adr_004_compliance: not-applicable-rationale
governing_adr: ADR-vitalia-006-ssr-safe-persisted-store
cap_target: valeria.shell
cap_change_type: extend
surfaces: [FE]
autonomous_mode: false
---

# 03-arch — vitalia-shell-state-persistence

> **Consolidado FE-only.** Esta story corrige un hazard arquitectónico transversal (4 stores
> Zustand `persist` que escriben su default a `localStorage` durante el ciclo SSR/skeleton) +
> agrega comportamiento mobile "collapsed pero recuerda". Cero BE, cero AGENTIC, cero engine.
> El "qué observable" lo fija `01-spec.md` (8 scenarios). Acá va el "cómo técnico".

## § 0 — Context Summary

- **Story:** `vitalia-shell-state-persistence` (followup FIX de `vitalia-fase1-shell-layout-5050-race-fix`)
- **Architect run on:** 2026-05-29
- **Modules touched (FE only):** `stores/` (4 stores) + `components/shared/shell-organism/` (5 archivos) + nuevo `lib/store/` (factory) + tests.
- **Naturaleza:** `fix` (persistencia rota PROD REAL) + `extend` (1 scenario nuevo mobile-collapsed → `valeria.shell`).

### Surface → builder → auditor mapping (PM usa para spawnear agentes)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/lib/store/**` (factory SSR-safe nuevo) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/stores/**` (4 stores persist) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/**` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/{src/stores/__tests__,e2e/regression}/**` (tests) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

> No hay surface BE ni AGENTIC. NO se spawnea `builder-backend` ni `builder-agentic`.

### Skills consultados (decisión tomada de cada uno)

- **frontend-expert** — FSD-Lite boundaries: el factory SSR-safe vive en `lib/store/` (capa `lib`, importable por `stores` y `features`), NUNCA en `components/shared`. Server-First respetado: el fix saca el store del path SSR.
- **playwright-expert** — des-skipear 3 regresiones existentes (no reescribir) + agregar e2e nuevos para SC-5b ("recuerda") y SC-4 (mobile-collapsed default). `E2E_BASE_URL` nativo, NUNCA `make e2e`.
- **tessl react-patterns / nextjs-app-router-modularization / vitest** — patrón canónico Zustand 5 + Next 16: `skipHydration:true` + flag `_hasHydrated` + storage wrapper que NO escribe hasta rehidratar client-side.

### CONTEXT-BRIEF source

- **Self-ran greps (Path B)** — no existe `CONTEXT-BRIEF.md` (story chica, brief skipped por `/pm-vitalia`). Scan NO-NEW-LAYER + cross-brand ejecutado por el architect (ver § Existing systems audit).

### capability YAML afectados (post-merge — Fase F.3)

- `vitalia/docs/product/capabilities/valeria/shell.yaml` — `cap_change_type: extend`. Append `change_log` entry + ≥1 atomic nuevo (mobile-collapsed-recuerda). NO crear cap nuevo. Si tiene `scenarios[]` y es user_visible → append SC-4 + SC-5b.
- `vitalia/docs/product/modules/shell-organism.md` (o `valeria.md` según mapping cap) — narrativa: drawer mobile recuerda estado.

### Architecture gates que deben seguir verdes

- FE arch fitness: `vitalia/frontend/src/__tests__/architecture/` (FSD boundaries: `lib` no importa `features`; `shared` no importa `features`; no default exports).
- `test_features_no_cross_imports.test.ts` (el factory en `lib` no rompe boundaries).
- tsc strict + eslint (sonarjs, boundaries, react-perf, prettier).
- **NUEVO gate propuesto:** `test-no-store-in-ssr-skeleton.test.tsx` (guard que el skeleton del shell NO suscriba `useShellStore`).

---

## § 1 — Root cause (CONFIRMADO — no re-investigar)

`ShellOrganismLayout.tsx` es `"use client"`. Su skeleton SSR/`loading`
(`ShellOrganismLayoutSkeleton`) renderiza `<TopBarGlobal/>`. `TopBarGlobal` suscribe
`useShellStore` (`setValeriaState`, `setShellMode`). El `dynamic({ssr:false})` envuelve
SOLO a `ShellOrganismLayoutClient` — **el skeleton queda fuera de ese boundary**. Resultado:
el middleware `persist` se evalúa en server-render + en la ventana pre-hidratación del
skeleton, auto-hidrata contra el default (`full/agentic`) y reescribe `localStorage` con ese
default, pisando la preferencia guardada en cada reload.

**4 técnicas que FALLARON (de `00-research.md` — PROHIBIDO repetir tal cual):**
1. `skipHydration:true` + `rehydrate()` a module-level (async → lee localStorage ya pisado).
2. `skipHydration:true` + `rehydrate()` en `useEffect` del Client solo (write espurio lo precede; StrictMode 2×).
3. Guard en el efecto D2 de `ValeriaSidebar` solo (necesario pero NO suficiente).
4. Combinaciones de los anteriores + restart container.

**Pieza faltante:** ninguna ataca el boundary. Mientras el store se evalúe DENTRO del skeleton
SSR, cualquier auto-hydrate/persist corre en ese contexto. El fix es doble: (A) sacar el store
del skeleton, y (B) hacer el `persist` write-safe hasta rehidratar client-side.

---

## § 2 — Architecture Decisions (Opción A vs B — tradeoff documentado)

### Decisión D1 — Combinar A (surgical boundary) + B (factory transversal). RECOMENDADA.

| Opción | Qué hace | Pro | Contra |
|---|---|---|---|
| **A — surgical** | Skeleton store-free (TopBarGlobal NO suscribe store en contexto skeleton) | Mata el bug exacto con mínimo blast radius | No previene recurrencia en los otros 3 stores |
| **B — factory** | `createSsrSafePersistedStore()` SSR-safe (storage no-op writes hasta `_hasHydrated`) aplicado a los 4 stores | Cementa el patrón; el hazard no puede recurrir | Más código; refactor de 4 stores |

**Decisión cementada (ADR-vitalia-006): A para el boundary del shell + B como convención para los 4 stores.** Razón: A elimina el trigger inmediato (la única ruta donde el skeleton SSR consume un persisted store hoy); B garantiza que si mañana otro consumer suscribe un persisted store en un path SSR, el `setItem` no-op pre-hydration evita el clobber. Defensa en profundidad.

### Decisión D2 — Factory `createSsrSafePersistedStore` (Opción B, el patrón)

Wrapper sobre `persist` con 3 propiedades:
1. **`skipHydration: true`** — el store NO auto-hidrata en module-eval (ni server ni client).
2. **Storage `setItem` no-op pre-hydration** — un `ssrSafeStorage(getStorage)` envuelve `createJSONStorage`; `setItem` es no-op MIENTRAS `_hasHydrated === false`. Esto neutraliza el write espurio aunque el store se evalúe en un contexto SSR/skeleton/StrictMode-double-invoke. `getItem`/`removeItem` pasan derecho.
3. **`_hasHydrated` flag + `onRehydrateStorage`** — un hook `useStoreHydration(store)` (o un `<StoreHydrationGate/>` en el chunk `ssr:false`) llama `store.persist.rehydrate()` UNA vez client-side; `onRehydrateStorage` setea `_hasHydrated = true` post-rehidrate. A partir de ahí `setItem` escribe normal.

> **Por qué esto SÍ converge donde fallaron las 4 técnicas:** las técnicas 1-2 dependían del *timing* del `rehydrate()` pero dejaban `setItem` activo, así que el ciclo persist escribía el default ANTES de que el rehydrate corriera. El no-op de `setItem` pre-hydration corta ese write en la raíz, independiente del timing.

### Decisión D3 — Disparo del rehydrate dentro del boundary `ssr:false`

El `rehydrate()` se dispara desde `ShellOrganismLayoutClient` (que ya es `ssr:false`), no a module-level ni en el skeleton. Para los stores no-shell (tenant, agenda, agenda-filters), el rehydrate se dispara en el primer Client Component que los consume (ya viven bajo el chunk client). Patrón: hook `useStoreHydration()` idempotente (React bail si ya hidratado; guard contra StrictMode double-invoke vía ref).

### Decisión D4 — Skeleton store-free (Opción A, surgical)

`TopBarGlobal` se parametriza para NO suscribir el store cuando se renderiza en el skeleton:
- **Approach elegido:** prop `variant?: "interactive" | "skeleton"` (default `"interactive"`). En `variant="skeleton"`, el burger handler es un no-op inerte (sin `useShellStore`) y NO se suscribe ningún selector del store. El skeleton pasa `variant="skeleton"`; el render real (en `ShellOrganismLayoutClient`) usa el default interactive.
- **Alternativa descartada:** skeleton sin `TopBarGlobal` (rompe el skip-link target inmediato `#main-content` + layout shift). Mantener el TopBar visible es requisito a11y de F1-S2.

### Decisión D5 — Mobile "collapsed pero recuerda" (slice independiente)

Spec § Decisión usabilidad + SC-4/SC-5b. Forma exacta del store:
- **Nuevo campo persistido en `shell-store`:** `mobileDrawerOpen: boolean` (default `false`), en un slice **independiente** de `valeriaState`. Persiste vía el mismo `partialize` (se agrega al `PersistedState`).
- **`valeriaState` (rail/full/collapsed) = desktop-only.** El render mobile del drawer en `ValeriaSidebar` deja de derivar `isExpanded` de `valeriaState` y pasa a leer `mobileDrawerOpen`. Así un `full` desktop NUNCA auto-abre el drawer mobile (rompe el acople con bug #1).
- **`useViewportGuard` extendido a `<768`:** al montar en mobile, **NO** toca `valeriaState`; el drawer arranca según `mobileDrawerOpen` (default `false` = cerrado fresh; recordado si el user lo abrió). One-way en mount, respetando el slice mobile recordado.
- **Burger (`TopBarGlobal` interactive):** en mobile, `onClick` setea `mobileDrawerOpen = true` (NO `setValeriaState('full')`). `aria-expanded` refleja `mobileDrawerOpen`.
- **Cierre drawer mobile:** `setMobileDrawerOpen(false)` (no toca `valeriaState` ni `shellMode`).

### Decisión D6 — `react-resizable-panels` se mantiene

El `dynamic({ssr:false})` impuesto por `react-resizable-panels` v4.11.1 (bare-name `localStorage` default param) sigue siendo el approach correcto. NO se migra la lib (out of scope spec). El fix opera SOBRE ese boundary, no lo elimina.

---

## § 3 — File structure (NEW vs MODIFIED)

```
vitalia/frontend/src/
  lib/store/
    create-ssr-safe-persisted-store.ts        ★ NEW — factory (D2)
    use-store-hydration.ts                     ★ NEW — hook rehydrate idempotente (D3)
    __tests__/create-ssr-safe-persisted-store.test.ts   ★ NEW — unit
  stores/
    shell-store.ts                             MODIFIED — usa factory + mobileDrawerOpen slice (D5)
    tenant-store.ts                            MODIFIED — usa factory
    __tests__/shell-store-hydration.test.ts    ★ NEW — unit (SC-3 + SC-7)
    __tests__/tenant-store-hydration.test.ts   ★ NEW — unit (smoke transversal)
  features/valeria/store/
    agenda-store.ts                            MODIFIED — usa factory
    agenda-filters-store.ts                    MODIFIED — usa factory
    __tests__/agenda-stores-hydration.test.ts  ★ NEW — unit (smoke transversal)
  components/shared/shell-organism/
    ShellOrganismLayout.tsx                    MODIFIED — skeleton pasa TopBarGlobal variant="skeleton" (D4)
    ShellOrganismLayoutClient.tsx              MODIFIED — dispara useStoreHydration(useShellStore) (D3)
    TopBarGlobal.tsx                           MODIFIED — prop variant + burger → mobileDrawerOpen (D4+D5)
    ValeriaSidebar.tsx                         MODIFIED — drawer mobile lee mobileDrawerOpen, no valeriaState (D5)
    useViewportGuard.ts                        MODIFIED — extiende <768 sin tocar valeriaState (D5)
    __tests__/no-store-in-ssr-skeleton.test.tsx  ★ NEW — arch guard (skeleton store-free)

vitalia/frontend/e2e/regression/
  vitalia-fase1-shell-layout-5050/
    resize-and-state.spec.ts                   MODIFIED — quitar .skip de 2 tests [DEFERRED]
    mobile-collapse.spec.ts                    MODIFIED — quitar .skip de "ValeriaSlot oculto mobile"
  shell-state-persistence/
    valeria-state-survives-reload.spec.ts      ★ NEW — SC-1/SC-2/SC-3 (no write espurio)
    mobile-collapsed-default.spec.ts           ★ NEW — SC-4 (fresh cerrado) + SC-5/SC-5b (recuerda) + SC-8 (a11y)
```

> NUNCA tocar: `components/ui/` (primitivas Shadcn), `lib/api/fetchClient.ts`, otros features, `core/`, otras brands.

---

## § 4 — Factory contract (signature load-bearing)

```ts
// lib/store/create-ssr-safe-persisted-store.ts
import { create, type StateCreator } from "zustand";
import { persist, createJSONStorage, type PersistOptions } from "zustand/middleware";

/** Marker añadido a todo store SSR-safe: false hasta rehidratar client-side. */
export interface SsrSafeHydration { _hasHydrated: boolean; setHasHydrated: (v: boolean) => void; }

/**
 * Envuelve createJSONStorage: setItem es NO-OP mientras getHydrated() === false.
 * Neutraliza el write espurio del default durante SSR/skeleton/StrictMode-double-invoke.
 */
function ssrSafeStorage(getHydrated: () => boolean) { /* getItem/removeItem passthrough; setItem guarded */ }

export function createSsrSafePersistedStore<T extends SsrSafeHydration>(
  initializer: StateCreator<T>,
  options: PersistOptions<T, Partial<T>>,   // name, partialize, version
): /* zustand store with .persist.rehydrate() */ { /* skipHydration:true + onRehydrateStorage → setHasHydrated(true) */ }
```

```ts
// lib/store/use-store-hydration.ts
/** Dispara store.persist.rehydrate() UNA vez client-side (idempotente, StrictMode-safe). */
export function useStoreHydration(store: { persist: { rehydrate: () => void } }): void;
```

---

## § 5 — Cross-cutting concerns

- **Tenant isolation:** N/A — estado 100% client-local (`localStorage`), sin queries. `tenant-store` persiste `activeTenant` (entidad de negocio, no PHI — ya documentado).
- **HIPAA-lite:** `not_applicable` — shell chrome + UI prefs, cero PHI en los 4 stores (confirmado: shell-store=layout, tenant-store=nombre clínica, agenda-store=drawerWidth, agenda-filters=lastView). El nuevo `mobileDrawerOpen` es boolean UI, no PHI.
- **PII / localStorage:** ningún campo PHI entra a `localStorage` (rule `hipaa-lite.md` § anti-pattern "PHI en localStorage" → respetado, no se agrega PHI).
- **Spanish neutro LatAm:** el `aria-label` del burger ("Abrir panel Valeria" / "Cerrar panel Valeria") ya existe en neutro — se mantiene, sin voseo. `aria-expanded` sincroniza con `mobileDrawerOpen`.
- **Native-first:** tests corren `npx vitest` / `npx playwright` nativo (host). NUNCA `make e2e`.
- **Currency / master-data:** N/A (sin montos, sin fechas en este path).

---

## § 6 — Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — no CONTEXT-BRIEF; story chica)

### Audit cross-module ejecutado
```
1. Engine factory persist/SSR-safe (core/@luana/):  0 hits productivos (solo node_modules). Sin factory a importar.
2. Cross-brand mirror zustand persist:
   - vitalia: 4 stores (shell, tenant, agenda, agenda-filters)
   - nicolify: 1 store (features/notifications/store/dismiss-store.ts) ★ usa persist
   - comunify / lupulo: 0 hits
3. Vitalia SSR-safe helper existente: NINGUNO (matches "hydrated" son useState component-local de props, no factory de store).
4. Full vitalia persist surface: exactamente los 4 stores nombrados (ningún otro store usa persist()).
```

### Sistemas existentes encontrados

| Sistema | Path | Patrón | Estado | Decisión |
|---|---|---|---|---|
| shell-store | `vitalia/frontend/src/stores/shell-store.ts` | `persist` raw | active, BUGGY (clobber) | **EXTEND** → factory |
| tenant-store | `vitalia/frontend/src/stores/tenant-store.ts` | `persist` raw | active | **EXTEND** → factory (mismo hazard latente) |
| agenda-store | `vitalia/frontend/src/features/valeria/store/agenda-store.ts` | `persist` raw | active | **EXTEND** → factory |
| agenda-filters-store | `vitalia/frontend/src/features/valeria/store/agenda-filters-store.ts` | `persist` raw | active | **EXTEND** → factory |
| nicolify dismiss-store | `nicolify/frontend/src/features/notifications/store/dismiss-store.ts` | `persist` raw | active (OTRA brand) | **NO MIRROR** — fix queda vitalia-local; lift candidate `/pm-luana` |
| engine factory SSR-safe | `core/@luana/*` | — | NO EXISTE | **NEW** (vitalia-local) justificado |

### Decisión por sistema
- **Los 4 stores vitalia:** EXTEND vía el factory `createSsrSafePersistedStore` (composición sobre `persist`). NO se recrea `persist`; se envuelve.
- **Factory nuevo (`lib/store/`):** NEW vitalia-local. **Por qué los existentes no sirven:** no hay factory SSR-safe en `core/@luana/*` ni en vitalia; el `persist` raw de Zustand NO ofrece el `setItem` no-op pre-hydration que mata el clobber. El "hydrated" pattern existente en vitalia es `useState` de props de Server Component, no aplica a stores. Criterio Chris (escala futura + cero deuda): cementar como convención evita re-discovery en cada store nuevo.
- **CROSS-BRAND MIRROR DETECTADO (nicolify dismiss-store):** NO mirror — el fix vive en vitalia. PERO el patrón ahora aplica a 2 brands → **lift candidate** real para `/pm-luana` (Next 16 + Zustand persist es transversal). Capturar learning `promotable: candidate` al merge (ya previsto en spec § Prior art applied). El fix NO toca nicolify (out of scope; story vitalia).

> **§11 drift flag (spec prior-art):** `01-spec.md § Prior art applied` afirmó "comunify/nicolify/lupulo = 0 hits". El scan del architect halló `nicolify/.../dismiss-store.ts` usando `persist`. NO cambia el scope (fix vitalia-local), pero refuerza el caso lift `/pm-luana`. Documentado para no re-litigar.

---

## § 7 — Test surfaces (TDD RED-first)

- **Unit (vitest, RED primero):**
  - `lib/store/__tests__/create-ssr-safe-persisted-store.test.ts` — factory: `setItem` no-op pre-hydration; escribe post-rehydrate; `_hasHydrated` flip.
  - `stores/__tests__/shell-store-hydration.test.ts` — SC-3 (mock localStorage seed 'rail' + SSR flag → rehidratar NO dispara setItem con default 'full'; primer valor post-hydration = 'rail') + SC-7 (JSON corrupto → default sin throw).
  - `stores/__tests__/tenant-store-hydration.test.ts` + `features/valeria/store/__tests__/agenda-stores-hydration.test.ts` — smoke transversal (factory aplicada bien, no clobber).
- **Component arch guard:** `components/shared/shell-organism/__tests__/no-store-in-ssr-skeleton.test.tsx` — render skeleton → assert NO suscribe `useShellStore` (spy en getState / render sin throw store-less).
- **E2E (playwright, des-skip + nuevos):**
  - Des-skip: `resize-and-state.spec.ts` ("shell state survives reload", "rail->full snap-up") + `mobile-collapse.spec.ts` ("ValeriaSlot oculto mobile").
  - NEW `valeria-state-survives-reload.spec.ts` — SC-1/SC-2/SC-3 (instrumentar `localStorage.setItem`, assert 'full' nunca escrito cuando había 'rail').
  - NEW `mobile-collapsed-default.spec.ts` — SC-4 (fresh cerrado) + SC-5 (burger abre) + SC-5b (recuerda abierto/cerrado entre reloads, slice independiente) + SC-8 (axe wcag2aa + keyboard open/close + focus return).

---

## § 8 — Architecture Fitness Impact

- Gates que corren: FE arch fitness (`src/__tests__/architecture/`), tsc, eslint, vitest coverage (≥20%).
- **Allowlist:** sin crecimiento. El factory en `lib/store/` respeta boundary (`lib` no importa `features`). 4 stores migran a factory sin nuevos imports cruzados.
- **Nuevo gate (shrink-only friendly):** `no-store-in-ssr-skeleton.test.tsx` agrega cobertura, no allowlist.

---

## § 9 — Open Questions for PM

1. **ADR number:** el caller pidió `ADR-vitalia-005-ssr-safe-persisted-store`, PERO `ADR-vitalia-005` YA EXISTE (`capability-model-4-dimensions`, Accepted 2026-05-27). Autoré **`ADR-vitalia-006-ssr-safe-persisted-store`** (siguiente libre). `checkpoint.md::new_adr_candidate` + frontmatter spec citan `005` → deben corregirse a `006` en el merge. (Architect no edita el spec ratificado; lo señalo a PM.)
2. **Lift `/pm-luana`:** nicolify ya tiene el hazard (`dismiss-store`). ¿Se eleva el patrón a `core/@luana/hooks` (o similar) en esta story como follow-up, o se difiere a un outcome `/pm-luana` dedicado? Recomendación: difiere — esta story queda vitalia-local + learning `promotable: candidate`.
