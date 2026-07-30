# T-4 Result — Mobile "collapsed pero recuerda": mobileDrawerOpen slice + useViewportGuard <768

**Ticket:** T-4 — vitalia-shell-state-persistence  
**Builder:** builder-frontend (Sonnet)  
**Fecha:** 2026-05-28  
**Estado:** DONE — all quality gates GREEN

## Diff summary (files modified)

### Modified files (T-4 scope only)

| File | Change |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | Mobile drawer reads `mobileDrawerOpen` (independent slice) instead of deriving from `valeriaState`. `handleMobileClose` calls `setMobileDrawerOpen(false)` NOT `setValeriaState('collapsed')`. Adds selectors `mobileDrawerOpen` + `setMobileDrawerOpen`. |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.test.tsx` | SC-8 mobile tests fully rewritten per D5: new tests assert `mobileDrawerOpen` governs drawer, valeriaState='full' does NOT auto-open (critical Bug #2 decoupling test), close sets mobileDrawerOpen=false. 30 tests total (27 → 30). |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | Added `mobileDrawerOpen` selector + `aria-expanded={mobileDrawerOpen}` on burger + dynamic `aria-label` ("Abrir"/"Cerrar" panel Valeria based on drawer state). |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.test.tsx` | Added 2 new tests for `aria-expanded=false` + dynamic aria-label (español neutro). 20 tests total (18 → 20). |
| `vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts` | Formal D5 documentation: `<768` branch explicitly documents that hook has ZERO role in `mobileDrawerOpen` governance. Existing no-op behavior unchanged. |
| `vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.test.ts` | Added 3 new D5 tests: hook does NOT touch `mobileDrawerOpen` on mobile mount; valeriaState='full' does NOT translate to mobileDrawerOpen=true; formal no-op verification. 9 tests total (6 → 9). |

## Core contract implemented (D5 ADR-vitalia-006)

- **Desktop ≥1104:** `valeriaState` (rail/full/collapsed) governs Valeria panel — UNCHANGED.
- **Mobile <768:** Drawer open/closed governed SOLELY by `mobileDrawerOpen` (independent slice). Default `false` = closed fresh (SC-4). Persisted so user remembers (SC-5b).
- **Critical decoupling:** `valeriaState='full'` on desktop NEVER auto-opens mobile drawer (was Bug #2). Test "[SC-4 CRITICAL D5] mobile + valeriaState='full' + mobileDrawerOpen=false → drawer NOT rendered" is the regression lock.
- **Close actions:** backdrop click + X button → `setMobileDrawerOpen(false)`. `valeriaState` is NOT touched.
- **a11y:** `aria-expanded={mobileDrawerOpen}` on burger; dynamic `aria-label` ("Abrir"/"Cerrar panel Valeria").

## Validator outputs

### TypeScript strict
```
npx tsc --noEmit → 0 errors
```

### ESLint (changed files)
```
npx eslint ValeriaSidebar.tsx useViewportGuard.ts TopBarGlobal.tsx → 0 errors, 0 warnings
```

### Vitest with coverage

```
Test Files  211 passed (211)
Tests  2310 passed (2310)
Coverage:
  Statements:  83.52% (threshold: 20% ✅)
  Branches:    92.80% (threshold: 20% ✅)
  Functions:   69.96% (threshold: 20% ✅)
  Lines:       83.52% (threshold: 20% ✅)
```

### Architecture fitness

```
Test Files  24 passed (24)
Tests  148 passed (148)
```

- No allowlist growth
- No new circular imports (madge)
- No cross-brand pollution
- FSD boundaries respected (`lib/store` not imported from wrong layer)

### Shell-organism suite (targeted)

```
Test Files  30 passed (30)
Tests  484 passed (484)
```

## TDD verification

- **RED phase confirmed:** 4 new D5 mobile tests in ValeriaSidebar failed before code change (correct RED state).
- **GREEN phase:** All 4 tests pass after `mobileDrawerOpen` switch in ValeriaSidebar.
- **RED/GREEN for useViewportGuard:** 3 new D5 tests written; all pass (hook had correct no-op behavior; tests formalize the contract).
- **RED/GREEN for TopBarGlobal:** 2 new aria-expanded tests; pass because mock had `mobileDrawerOpen: false` and burger correctly renders `aria-expanded={false}`.

## Skills consulted

| Skill | Invocada por | Decisión tomada |
|---|---|---|
| `frontend-expert` | Mandatory always | FSD-Lite: `useShellStore` selectors (one per primitive), Server-First boundary preserved. ValeriaSidebar stays Client Component (state/effects). |
| `tessl__react-patterns` | Always: error boundaries, loading/error/empty, stable keys | Mobile drawer via `createPortal` (SSR guard preserved). No index keys. Selector stability via individual primitives. |
| `tessl__nextjs-app-router-modularization` | Page mixes Server+Client | Shell boundary: `ValeriaSidebar` is leaf Client Component — correct. No change needed to page.tsx structure. |
| `tessl__vitest` | Tests new | RED-first per `tdd-mandatory.md`. Used `useShellStore.setState({mobileDrawerOpen: true})` for direct store manipulation in tests. |
| `playwright-expert` | E2E scope (T-5 will own E2E) | T-4 scope = unit + component tests only. E2E spec `mobile-collapsed-default.spec.ts` is T-5 scope per 05-guidelines.md. |
| `.claude/rules/frontend-fsd.md` | FSD boundary matrix | ValeriaSidebar imports `useShellStore` from `@/stores/shell-store` (correct layer). No cross-feature imports. |
| `.claude/rules/spanish-text.md` | Spanish neutro LatAm | `aria-label` uses "Abrir panel Valeria" / "Cerrar panel Valeria" — tuteo, no voseo, correct tildes. |
| `.claude/rules/anti-duplication.md` | Anti-mirror cross-brand | Confirmed: no `mobileDrawerOpen` mirror in nicolify/comunify/lupulo. Fix stays vitalia-local per 05-guidelines FORBIDDEN #8. |
| `.claude/rules/tdd-mandatory.md` | Mandatory | RED tests written before GREEN code. Verified failing state documented above. |

## Depends-on verification

- **T-1 (DONE):** `shell-store.ts` has `mobileDrawerOpen: boolean` (default false) + `setMobileDrawerOpen`. Verified via Read — slice exists. ✅
- **T-2 (DONE):** `TopBarGlobal.tsx` burger `onClick` calls `setMobileDrawerOpen(true)`. Verified in current code. ✅ Added `aria-expanded={mobileDrawerOpen}` (T-4 scope addition).

## SCOPE DISCIPLINE (forbidden_to_touch — verified)

- ✅ NOT touched: `core/`, other brands, `components/ui/`, `app/layout.tsx`
- ✅ NOT touched: `lib/store/create-ssr-safe-persisted-store.ts` (T-1 scope)
- ✅ NOT touched: `ShellOrganismLayout.tsx`, `ShellOrganismLayoutClient.tsx` (T-3 scope)
- ✅ NOT touched: `stores/shell-store.ts` (already has the slice — no changes needed)
- ✅ NOT touched: e2e specs (T-5 scope per guidelines)

## Live verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (per SKILL.md note 2026-05-15). Escalating to Chris for staging gate manual verification per role instructions. Key manual verification steps:

1. Open `http://localhost:3002` on mobile viewport (<768px)
2. Verify drawer starts CLOSED (no role=dialog in DOM)
3. Tap burger → drawer opens → verify aria-expanded=true on burger
4. Reload → verify drawer restores to open (SC-5b remembered)
5. Close drawer → reload → verify drawer stays closed (SC-5b)
6. Set valeriaState='full' in desktop then switch to mobile → verify drawer is NOT auto-opened (Bug #2 regression)

## Commit SHA

`8467706a` — pushed to `wip/vitalia`
