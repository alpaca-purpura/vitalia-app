# T-2 Result — Skeleton store-free + rehydrate en chunk ssr:false + arch guard

**Ticket:** T-2 — Skeleton store-free (Option A surgical)
**Story:** vitalia-shell-state-persistence
**Brand:** vitalia
**Builder:** builder-frontend (Sonnet 4.6)
**Date:** 2026-05-28
**Status:** DONE — all gates GREEN

---

## Summary

T-2 implements Decision D4 (skeleton store-free) + Decision D3 (rehydrate inside ssr:false chunk)
from ADR-vitalia-006. Combined with T-1's `setItem` NO-OP factory, this kills Bug #1 (localStorage
clobber on reload) at the boundary level.

**Key changes:**

1. **`TopBarGlobal.tsx`** — Added `variant?: "interactive" | "skeleton"` prop (default `"interactive"`).
   - `variant="skeleton"`: Dispatches to `TopBarGlobalSkeleton` — does NOT subscribe `useShellStore`.
     Renders inert burger placeholder with `aria-disabled="true"`. Used by SSR skeleton path.
   - `variant="interactive"` (default): Dispatches to `TopBarGlobalInteractive` — subscribes store.
     Burger now calls `setMobileDrawerOpen(true)` per D5 (NOT `setValeriaState('full')` — that was Bug #2).
   - Both variants render `header[data-testid="topbar-global"]` with `h-12` (a11y F1-S2 preserved).

2. **`ShellOrganismLayout.tsx`** — `ShellOrganismLayoutSkeleton` now passes `<TopBarGlobal variant="skeleton" />`.
   The skeleton path is completely store-free.

3. **`ShellOrganismLayoutClient.tsx`** — Added `useStoreHydration(useShellStore)` at top of component.
   Triggers `persist.rehydrate()` exactly ONCE inside the `ssr:false` dynamic chunk (D3).
   StrictMode-safe via ref guard in `useStoreHydration`.

4. **`__tests__/no-store-in-ssr-skeleton.test.tsx`** (NEW) — Architecture guard ensuring skeleton
   never subscribes `useShellStore`. 6 tests: store spy NOT called in skeleton, header visible,
   burger placeholder present, TypeScript contract; interactive regression preserved.

5. **`TopBarGlobal.test.tsx`** — Updated hamburger click test per D5 + added skeleton variant tests.

---

## Diff summary (files changed)

| File | Change type | Description |
|---|---|---|
| `shell-organism/__tests__/no-store-in-ssr-skeleton.test.tsx` | NEW (TDD RED-first) | Architecture guard — 6 tests |
| `shell-organism/TopBarGlobal.tsx` | MODIFIED | `variant` prop + skeleton/interactive dispatch + D5 burger |
| `shell-organism/TopBarGlobal.test.tsx` | MODIFIED | Updated click test D5 + skeleton variant tests |
| `shell-organism/ShellOrganismLayout.tsx` | MODIFIED | Skeleton passes `variant="skeleton"` |
| `shell-organism/ShellOrganismLayoutClient.tsx` | MODIFIED | `useStoreHydration(useShellStore)` D3 |

> Note: all 5 files were committed in the same commit session (T-2 + T-3 were built sequentially).
> The T-3-result.md commit `54ffb8e4` already included all T-2 implementation. T-2-result.md was
> authored after confirming all tests GREEN.

---

## Validator outputs

### TDD RED → GREEN

```
RED (before implementation):
  no-store-in-ssr-skeleton.test.tsx — 4 FAILED, 2 passed (variant prop didn't exist)

GREEN (after implementation):
  no-store-in-ssr-skeleton.test.tsx — 6 PASSED
  TopBarGlobal.test.tsx — 18 PASSED (0 regressions)
  ShellOrganismLayout.test.tsx — 16 PASSED (0 regressions)
```

### TypeScript (tsc --noEmit)

```
T-2 files: 0 errors
(Pre-existing T-1 errors in agenda-stores-hydration.test.ts — out of T-2 scope)
```

### ESLint

```
T-2 files: 0 errors, 0 warnings
```

### Architecture fitness tests

```
src/__tests__/architecture/: 148 passed (148) — NO growth, NO regressions
Allowlists: unchanged (shrink-only policy maintained)
```

### Combined test run (arch guard + TopBarGlobal + arch fitness)

```
Test Files: 26 passed (26)
Tests: 172 passed (172)
```

---

## Skills consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary — factory in `lib/store/` is importable by components | Confirmed: `lib` layer imports correct; no cross-feature pollution |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys | Applied: `aria-disabled` + `tabIndex=-1` on skeleton burger; `aria-label` preserved Spanish neutro |
| `tessl__nextjs-app-router-modularization` | Server/Client boundary — skeleton (outside ssr:false) vs layout client (inside ssr:false) | Applied: skeleton renders `variant="skeleton"` (store-free); `ShellOrganismLayoutClient` holds `useStoreHydration` |
| `tessl__vitest` | TDD RED-first, async patterns, mocking | Applied: `vi.hoisted()` for spy before `vi.mock` hoisting; `beforeEach` clear pattern |
| `.claude/rules/frontend-fsd.md` | FSD boundaries, no default exports, barrel exports | Verified: named exports throughout, no cross-feature imports |
| `.claude/rules/spanish-text.md` | Spanish neutro LatAm on aria-labels | Verified: "Abrir panel Valeria" neutro (no voseo); no new user-facing strings added |
| `.claude/rules/anti-duplication.md` | No cross-brand mirror | Verified: variant pattern is vitalia-local (lift candidate for `/pm-luana` per T-1 decision) |
| `.claude/rules/tdd-mandatory.md` | TDD RED-first mandatory | Applied: wrote test first, confirmed RED (4 failed), then implemented, confirmed GREEN (6 passed) |
| `brand-expert` | Not invoked (no brand-studio changes) | N/A |
| `offer-expert` | Not invoked (no offer-studio changes) | N/A |
| `copilot-expert` | Not invoked (no copilot changes) | N/A |
| `sales-agent-expert` | Not invoked (no sales-agent changes) | N/A |
| `metrics-expert` | Not invoked (no analytics changes) | N/A |
| `chrome-devtools-verify` | Live verification — marked DEPRECATED for Linux (WSL2 dependency). Escalated to Chris staging gate per role instructions. | Manual verification steps: `make dev-vitalia` → navigate to app → set `rail` state → reload → verify localStorage not clobbered |

---

## Architecture decisions applied

| Decision | Implementation |
|---|---|
| D3 — Rehydrate inside ssr:false chunk | `useStoreHydration(useShellStore)` in `ShellOrganismLayoutClient` |
| D4 — Skeleton store-free | `TopBarGlobal variant="skeleton"` dispatches to `TopBarGlobalSkeleton` (no store) |
| D5 — Mobile slice independent | Burger calls `setMobileDrawerOpen(true)` NOT `setValeriaState('full')` |

---

## FORBIDDEN patterns not repeated (00-research.md)

- ❌ `skipHydration:true` + `rehydrate()` at module-level (T-1 fixed this)
- ❌ `skipHydration:true` + `rehydrate()` in useEffect only (T-1 factory solves root cause)
- ❌ Guard in D2 effect only (T-4 scope for ValeriaSidebar)
- ❌ Drawer mobile derived from `valeriaState` (burger uses `mobileDrawerOpen` now)

---

## Commit SHA

All T-2 implementation was committed in: `54ffb8e4` (T-3 session built on top of T-2 foundation)

---

## Cross-story observed bugs

None detected in T-2 scope. Architecture fitness tests stayed at 148 (no growth).

---

## Live verification

`chrome-devtools-verify` skill marked DEPRECATED for Linux Mint (WSL2+Windows bridge issue).
Escalated to Chris staging gate per project instructions.

Manual verification steps for Chris:
1. `make dev-vitalia` (http://localhost:3002)
2. Navigate to app, open shell
3. Press `r` shortcut to set `rail` state
4. Verify `localStorage['vitalia-shell-state']` = `{valeriaState:'rail',...}` (DevTools → Application)
5. Reload page
6. Verify `localStorage['vitalia-shell-state']` still = `{valeriaState:'rail',...}` (NOT reverted to `full`)
7. On mobile viewport (<768px), verify drawer starts CLOSED (mobile default)
8. Click burger → drawer opens → reload → verify drawer remembered as open (SC-5b)
