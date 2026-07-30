# 05-guidelines — vitalia-shell-state-persistence

> Guía de implementación para `builder-frontend` (Sonnet). FE-only. Patrón SSR-safe Zustand+Next
> es REQUERIDO; las 4 técnicas de `00-research.md` están PROHIBIDAS.

## must_load_skills (verbatim — builder cita en T-{n}-result.md "Skills consulted")

- `frontend-expert`
- `playwright-expert`
- `tessl__react-patterns`
- `tessl__nextjs-app-router-modularization`
- `tessl__vitest`
- `.claude/rules/frontend-fsd.md`
- `.claude/rules/spanish-text.md`
- `.claude/rules/anti-duplication.md`
- `.claude/rules/tdd-mandatory.md`

## must_load_artifacts

- `vitalia/docs/product/stories/vitalia-shell-state-persistence/01-spec.md` (8 scenarios SC-1..SC-8 + SC-5b — el contrato observable)
- `vitalia/docs/product/stories/vitalia-shell-state-persistence/00-research.md` (root cause + 4 técnicas FALLIDAS — NO repetir)
- `vitalia/docs/product/stories/vitalia-shell-state-persistence/03-arch.md` (§ 2 decisiones A+B + § 4 factory contract + § 3 file structure)
- `vitalia/docs/product/stories/vitalia-shell-state-persistence/04-validators.yaml` (test_construction_plan + scenario_coverage)
- `vitalia/docs/architecture/ADR-vitalia-006-ssr-safe-persisted-store.md` (patrón cementado SSoT)

## patterns REQUIRED

1. **Factory SSR-safe (`createSsrSafePersistedStore`)** — `skipHydration:true` + storage wrapper con `setItem` NO-OP hasta `_hasHydrated === true` + `onRehydrateStorage` que flipea el flag. ESTE es el patrón canónico cementado (ADR-vitalia-006).
2. **Rehydrate dentro del chunk `ssr:false`** — `useStoreHydration(store)` idempotente (ref-guard StrictMode), disparado desde `ShellOrganismLayoutClient` (shell) / primer Client Component consumer (otros stores). NUNCA module-level.
3. **Skeleton store-free** — `TopBarGlobal variant="skeleton"` NO suscribe `useShellStore`. El skeleton pasa `variant="skeleton"`; el render real usa default `interactive`.
4. **Mobile slice independiente** — `mobileDrawerOpen: boolean` (default `false`) persistido, SEPARADO de `valeriaState`. Drawer mobile lee `mobileDrawerOpen`, NO `valeriaState`. Burger setea `mobileDrawerOpen`. `useViewportGuard <768` NO toca `valeriaState`.
5. **TDD RED-first** — orden de `04-validators § creation_order`. Test que falla ANTES del código GREEN, por capa.
6. **Reuse POM** — `ShellLayoutPage.ts` + `shell-theme.fixture.ts` (extender, no recrear).

## patterns FORBIDDEN (las 4 técnicas que NO convergieron — 00-research.md)

1. ❌ `skipHydration:true` + `rehydrate()` a **module-level** (async → lee localStorage ya pisado).
2. ❌ `skipHydration:true` + `rehydrate()` en `useEffect` del Client **solo** (sin no-op de setItem → el write espurio lo precede; StrictMode 2×).
3. ❌ Guard en el efecto D2 de `ValeriaSidebar` **como único fix**.
4. ❌ Combinaciones de 1-3 + restart container (no atacan el boundary ni el setItem).
5. ❌ Migrar `react-resizable-panels` (out of scope; el `dynamic({ssr:false})` se mantiene).
6. ❌ Drawer mobile derivado de `valeriaState` (re-acopla bug #2 con #1).
7. ❌ Burger seteando `setValeriaState('full')` (debe setear `mobileDrawerOpen`).
8. ❌ Crear factory mirror en nicolify/comunify/lupulo (fix vitalia-local; lift es `/pm-luana`).

## files in scope (editar)

- `vitalia/frontend/src/lib/store/create-ssr-safe-persisted-store.ts` ★ NEW
- `vitalia/frontend/src/lib/store/use-store-hydration.ts` ★ NEW
- `vitalia/frontend/src/lib/store/__tests__/create-ssr-safe-persisted-store.test.ts` ★ NEW
- `vitalia/frontend/src/stores/shell-store.ts` (factory + `mobileDrawerOpen` slice)
- `vitalia/frontend/src/stores/tenant-store.ts` (factory)
- `vitalia/frontend/src/stores/__tests__/{shell-store-hydration,tenant-store-hydration}.test.ts` ★ NEW
- `vitalia/frontend/src/features/valeria/store/{agenda-store,agenda-filters-store}.ts` (factory)
- `vitalia/frontend/src/features/valeria/store/__tests__/agenda-stores-hydration.test.ts` ★ NEW
- `vitalia/frontend/src/components/shared/shell-organism/{ShellOrganismLayout,ShellOrganismLayoutClient,TopBarGlobal,ValeriaSidebar,useViewportGuard}.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/__tests__/no-store-in-ssr-skeleton.test.tsx` ★ NEW
- `vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/{resize-and-state,mobile-collapse}.spec.ts` (un-skip)
- `vitalia/frontend/e2e/regression/shell-state-persistence/{valeria-state-survives-reload,mobile-collapsed-default}.spec.ts` ★ NEW
- `vitalia/frontend/e2e/pages/ShellLayoutPage.ts` (extender helpers mobile drawer + instrumentSetItem)

## files NEVER touch

- `core/luana-core-*/src/` y `core/@luana/*` (engine — `/pm-luana` promotion gate)
- `nicolify/`, `comunify/`, `lupulo/` (otras brands — cross-brand prohibido)
- `vitalia/frontend/src/components/ui/` (primitivas Shadcn)
- `vitalia/frontend/src/lib/api/fetchClient.ts`
- `vitalia/frontend/src/app/layout.tsx` y otros features fuera de los 2 agenda stores
- Cualquier estado visual ratificado Fase 1 (collapsed/rail/full markup) — solo cambia CUÁNDO se aplica + la persistencia

## rationale

FE standard transversal fix → Sonnet sweet spot. Cero agentic (no Opus required). El patrón es
mecánico una vez cementado el factory; el riesgo está en NO repetir las 4 técnicas fallidas y en
respetar el slice mobile independiente. `playwright_required: true` por SC-1..SC-5b + SC-8.

## spanish neutro

`aria-label` burger existente ("Abrir panel Valeria" / "Cerrar panel Valeria") se mantiene neutro,
sin voseo. `aria-expanded` sincroniza con `mobileDrawerOpen`. Cero copy user-facing nuevo.
