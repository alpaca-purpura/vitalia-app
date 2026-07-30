# T-6 Result — TopBarGlobal hamburger button mobile drawer trigger

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Ticket:** T-6
**State:** pushed
**Commit SHA:** 5d68436b
**Branch:** wip/vitalia
**Files touched:** 2

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite, Server→Client conversion, `"use client"` leaf pattern | ADD-ONLY: convert TopBarGlobal to `"use client"` (click handler requires it). Arch test `test_server_first.test.ts` checks inverse (hooks without `"use client"`) — our conversion satisfies it. |
| `tessl__shadcn-ui` | Lucide `Menu` icon + Shadcn `Button` component selection | `Button` variant=`ghost` size=`icon` from `@/components/ui/button` (already installed F1-S0). Lucide `Menu` from `lucide-react`. |
| `tessl__react-patterns` | Stable selector pattern for Zustand, `aria-hidden` decorative icon | Two separate `useShellStore` selectors (one per setter) — stable identity, no inline object. `Menu` icon gets `aria-hidden="true"` (decorative). |
| `tessl__vitest` | Mock `useShellStore` for click handler test isolation | `vi.mock("@/stores/shell-store", ...)` with selector-aware mock function. `mockSetValeriaState` + `mockSetShellMode` as `vi.fn()` captured per test via `beforeEach` clear. |

---

## Diff summary

### `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx`

**4 changes (ADD-ONLY, no deletions of existing logic):**

1. Added `"use client";` as first line (conversion from Server Component)
2. Added imports: `Menu` from `lucide-react`, `Button` from `@/components/ui/button`, `useShellStore` from `@/stores/shell-store`
3. Added selectors inside component: `const setValeriaState = useShellStore((s) => s.setValeriaState)` + `const setShellMode = useShellStore((s) => s.setShellMode)` + `handleOpenValeria` handler
4. Added hamburger `<Button>` BEFORE `<LogoMark>` (D7 spec position), changed left div gap to `gap-2 md:gap-3`

**Existing logic preserved intact:**
- `<header role="banner" data-testid="topbar-global" className="h-12 ... z-50">` — unchanged
- `<LogoMark variant="full">` + `<LogoMark variant="mark">` — unchanged
- `<TenantSwitcher />` — unchanged
- `<ThemeToggle />` — unchanged

### `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.test.tsx`

**Added 9 new tests (3 new describe blocks), preserved 6 existing tests:**

New tests:
- `[T-6] hamburger button rendered with md:hidden class`
- `[T-6] hamburger aria-label is 'Abrir panel Valeria' (Spanish neutro, D7)`
- `[T-6] hamburger has data-testid='topbar-hamburger'`
- `[T-6] hamburger icon Menu has aria-hidden='true' (decorative)`
- `[T-6] click hamburger dispatches setValeriaState('full') + setShellMode('agentic')`
- `[regression] LogoMark still rendered (F1-S2 preserved)`
- `[regression] TenantSwitcher still rendered (F1-S3 preserved)`
- `[regression] ThemeToggle still rendered (F1-S1 preserved)`
- `[regression] header data-testid='topbar-global' with h-12 and z-50 (structure preserved)`

Added mock: `vi.mock("@/stores/shell-store", ...)` with selector-aware mock + `mockSetValeriaState` / `mockSetShellMode` vi.fn().

---

## Validators

### G5 pre-commit gate — ALL PASS

| Gate | Result | Notes |
|---|---|---|
| `npx vitest run TopBarGlobal.test.tsx` | ✅ 15/15 PASS | 6 heredados + 9 nuevos |
| `npx tsc --noEmit` | ✅ 0 errors | Strict mode clean |
| `npx eslint TopBarGlobal.tsx` | ✅ 0 errors/warnings | |
| `npx prettier --check TopBarGlobal.tsx` | ✅ OK | |
| Arch tests (architecture/) | ⚠️ 2 failed (pre-existing) | `test_server_first.test.ts` fails on `useKeyboardShortcuts.ts` (T-1 pre-existing, confirmed via git stash) — NOT introduced by T-6 |

### TDD RED → GREEN verification

- **RED**: 5 T-6 tests failed before implementation (element `topbar-hamburger` not found)
- **GREEN**: All 15 tests pass after implementation
- **Regression**: 6 pre-existing tests continue GREEN

---

## Architecture fitness

**Arch test `test_server_first.test.ts`**: The test checks for files that USE client hooks WITHOUT declaring `"use client"`. Our conversion ADDS `"use client"` along with the hooks — satisfies the test requirement. Pre-existing failure on `useKeyboardShortcuts.ts` (T-1) is NOT related to T-6.

**FSD boundary**: `TopBarGlobal.tsx` is in `components/shared/shell-organism/` — NOT in `features/*`. No FSD boundary violated.

**Anti-duplication**: No new component introduced. ADD-ONLY modification to existing file.

---

## Live verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (WSL2 bridge not applicable). Manual verification escalated to Chris staging gate per `chrome-devtools-verify` skill deprecation notice.

The hamburger button renders visually as `md:hidden` — it will only be visible at `<768px` viewport width. Functional behavior (drawer open) verified via unit tests: click dispatches correct Zustand setters.

---

## Spanish neutro compliance

- aria-label: `"Abrir panel Valeria"` — tuteo, no voseo ✅
- No user-facing voseo strings introduced ✅
