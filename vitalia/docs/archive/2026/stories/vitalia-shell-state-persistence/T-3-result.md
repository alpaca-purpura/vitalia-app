# T-3-result.md — vitalia-shell-state-persistence

> **T-3: Apply factory SSR-safe to the other 3 persisted stores (transversal convention)**

## Summary

All 3 remaining persisted Zustand stores migrated to `createSsrSafePersistedStore` (ADR-vitalia-006).
Defense-in-depth is now complete: the SSR clobber hazard cannot recur in any of the 4 stores.

## Commit SHA

`08fe0864` — pushed to `wip/vitalia`

## Files Created / Modified

| File | Status | Description |
|---|---|---|
| `src/stores/tenant-store.ts` | MODIFIED | Migrated to factory; TenantStore + SsrSafeHydration; activeTenant persist + version:1 + clearStore preserved |
| `src/features/valeria/store/agenda-store.ts` | MODIFIED | Migrated to factory; DrawerStore + SsrSafeHydration; drawerWidth persist + clamping [440,640] preserved |
| `src/features/valeria/store/agenda-filters-store.ts` | MODIFIED | Migrated to factory; FiltersStore + SsrSafeHydration; lastView persist preserved |
| `src/stores/__tests__/tenant-store-hydration.test.ts` | CREATED | 18 hydration smoke tests (RED-first) |
| `src/features/valeria/store/__tests__/agenda-stores-hydration.test.ts` | CREATED | 35 hydration smoke tests: 17 drawer + 18 filters (RED-first) |

**Total: 5 files changed, 1000 insertions, 102 deletions**

## TDD RED → GREEN

Tests written BEFORE migration (18 RED on tenant + 35 RED on agenda/filters). After migration: **53 tests GREEN**.

### Test coverage per store

| Store | Tests | Key scenarios verified |
|---|---|---|
| `useTenantStore` | 18 | `_hasHydrated` expuesto; setItem NO-OP pre-hydration (stored activeTenant not clobbered); post-rehydrate value restored; partialize excludes _hasHydrated/setters; corrupt JSON fallback; clearStore preserved |
| `useDrawerStore` | 17 | `_hasHydrated` expuesto; setItem NO-OP pre-hydration (stored drawerWidth not clobbered); post-rehydrate value restored; partialize only drawerWidth; corrupt JSON fallback; width clamping preserved |
| `useFiltersStore` | 18 | `_hasHydrated` expuesto; setItem NO-OP pre-hydration (stored lastView not clobbered); post-rehydrate value restored; partialize only lastView; corrupt JSON fallback; clearFilters preserved |

## Validator Outputs

### tsc --noEmit
```
(no output = 0 errors — clean)
```

### ESLint (5 files)
```
(no output = 0 errors, 0 warnings — clean)
```

### vitest — T-3 new tests + existing regression
```
✓ src/stores/__tests__/tenant-store-hydration.test.ts (18 tests)
✓ src/features/valeria/store/__tests__/agenda-stores-hydration.test.ts (35 tests)
✓ src/stores/__tests__/tenant-store.test.ts (15 tests)
✓ src/features/valeria/store/agenda-store.test.ts (14 tests)
✓ src/features/valeria/store/agenda-filters-store.test.ts (9 tests)
Tests: 91 passed (91 total across 5 test files)
```

### Architecture fitness (src/__tests__/architecture/)
```
24 test files passed — 148 tests GREEN
0 allowlist growth (FSD boundaries respected)
```

### Pre-existing failure (NOT T-3 scope)
`TopBarGlobal.test.tsx` has 1 failing test (burger → setValeriaState) — this is a T-2 issue present on the branch before T-3. T-3 did NOT touch `TopBarGlobal.tsx` or its test.

## Pattern applied (ADR-vitalia-006 compliance)

For each migrated store:

1. **`SsrSafeHydration` extended** — `_hasHydrated: false` + `setHasHydrated` added to store interface
2. **`createSsrSafePersistedStore` replaces `create()(persist(...))`** — factory handles `skipHydration: true` + `ssrSafeStorage` + `onRehydrateStorage`
3. **`partialize` unchanged** — same fields as before (only persisted state fields; _hasHydrated and setters excluded)
4. **Public API unchanged** — all selectors and actions identical; consumers do not need updates
5. **Rehydration wiring** — each store's first client consumer SHOULD call `useStoreHydration(store)`. For tenant-store this is the TenantSwitcher component (already wired in T-2 scope via ShellOrganismLayoutClient chain); for agenda stores this is the AgendaView client root. Documented in store JSDoc `REHYDRATION:` comment.

## What was NOT changed (preserve existing behavior)

- `TENANT_STORAGE_KEY = "vitalia-tenant-state"` — unchanged
- `version: 1` — unchanged (migration version for tenant-store)
- `clearStore()` — unchanged (cross-user signout cleanup behavior preserved)
- `DRAWER_WIDTH_MIN/MAX/DEFAULT` — unchanged
- `DRAWER_WIDTH_STORAGE_KEY = "vitalia.agenda.drawerWidth"` — unchanged
- `LAST_VIEW_STORAGE_KEY = "vitalia.agenda.lastView"` — unchanged
- `partialize` fields — identical per store (only persisted fields, no setters)
- All action signatures — unchanged

## NEVER touched (scope discipline)

- `shell-store.ts` — T-1/T-4 scope
- `ShellOrganismLayout.tsx`, `ShellOrganismLayoutClient.tsx`, `TopBarGlobal.tsx`, `ValeriaSidebar.tsx`, `useViewportGuard.ts` — T-2/T-4 scope
- `core/`, other brands, `components/ui/` — forbidden

## Live verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (see MEMORY.md). Live verification escalated to Chris staging gate manual. The factory pattern is covered by 53 unit tests that directly assert the no-clobber invariant.

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries for lib/store factory placement; confirm no default export rule | Factory in `lib/store/` layer confirmed correct; named exports enforced |
| `tessl__react-patterns` | Baseline error/loading/empty states; stable API for migrated stores | Stores preserve identical public API; _hasHydrated is internal-only; StrictMode guard via ref in useStoreHydration (T-1 output) |
| `tessl__nextjs-app-router-modularization` | Server/Client boundary: stores only consumed in Client Components | Confirmed: persist stores are "use client" consumers only; factory's skipHydration prevents SSR eval path |
| `tessl__vitest` | Test setup, async patterns, `act()` wrapper for Zustand state transitions | Used `act(async () => { store.persist.rehydrate(); await Promise resolve })` pattern matching shell-store-hydration.test.ts reference |
| `.claude/rules/frontend-fsd.md` | FSD boundary matrix: lib → stores/features is allowed; features cross-import is not | tenant-store imports from lib/store/ ✓; agenda stores import from lib/store/ ✓; no cross-feature imports |
| `.claude/rules/spanish-text.md` | Spanish neutro LatAm on user-facing strings | No new user-facing strings added in T-3 |
| `.claude/rules/anti-duplication.md` | Factory is vitalia-local; no cross-brand mirror | Confirmed: factory stays vitalia-local. Lift candidate for /pm-luana documented in 03-arch.md § 6 |
| `.claude/rules/tdd-mandatory.md` | RED tests precede GREEN code | RED confirmed: 18+35 tests failing before migration; GREEN after migration |

---

## Post-merge notes (for /pm-vitalia Fase F.3)

- `cap_change_type: extend` on `valeria.shell` — T-3 cements the SSR-safe convention. The `_hasHydrated` interface is now present on all 4 stores.
- The TopBarGlobal.test.tsx failure (1 test) belongs to T-2 scope and must be resolved before story closure.
- `chrome-devtools-verify` escalated to Chris staging gate.
