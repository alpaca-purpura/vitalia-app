# T-K3 Result — Kit barrel global + tests + CHANGELOG

**Story:** platform-lift-shell-chrome-ui-kit  
**Ticket:** T-K3  
**Date:** 2026-06-11  
**Status:** DONE  

## Commits

| SHA | Description |
|---|---|
| `b425fd42` | feat(ui-kit): T-K3 barrel global re-exports organism/shell (0.4.0) |
| `d9723884` | test(ui-kit): T-K3 batch-1 — ShellLayout, SupervisorCollapsedStrip, TopBarShell, useViewportGuard |
| `3b3b7fac` | test(ui-kit): T-K3 batch-2 — ChatHeader, SubTabsBar, TogglePill, ShellLayout props fix + routing nullguard |
| `d02dd6e1` | docs(ui-kit): T-K3 CHANGELOG 0.4.0 T-K2+T-K3 entries + migration notes |

## Gate results (G5)

| Gate | Result |
|---|---|
| `pnpm --filter @luana/ui-kit test` (vitest run) | **259 tests / 20 files — ALL GREEN** |
| `tsc --noEmit 2>&1 \| grep organism \| grep -v __tests__` | **0 errors** |
| Brand token grep (`vitalia\|valeria\|nicolify\|#01b2f8` in production source) | **0 matches** (JSDoc port-origin comments in test files only, pre-existing pattern) |

## Deliverables

### 1. `src/index.ts` barrel

Added `export * from "./organism/shell"` with guard comment:

```typescript
// ── Shell organism (T-K3 — brand-agnostic shell chrome, 0.4.0) ───────────────
// ⛔ react-resizable-panels Group/Panel/Separator NOT re-exported (shell barrel guards).
export * from "./organism/shell";
```

No symbol collision: kit's `Group` = form group component. Shell barrel explicitly guards react-resizable-panels primitives.

### 2. Tests (`src/organism/shell/__tests__/`)

7 new test files, 91 new tests (total: 259 tests / 20 files):

| File | Tests | Coverage |
|---|---|---|
| `shell-layout.test.tsx` | 6 | Mount + skeletonSlot + no-duplicate #main-content |
| `supervisor-collapsed-strip.test.tsx` | 12 | Button aria-label, thumbnail, name, status dot, click, onError fallback |
| `top-bar-shell.test.tsx` | 12 | D1 structure, slots, hamburger, interactive/skeleton variants, labels |
| `use-viewport-guard.test.ts` | 8 | SUPERVISOR_MIN_PX=320 exported; VALERIA_MIN_PX/legacy names absent |
| `chat-header.test.tsx` | 17 | SC-1/SC-4/action buttons/RN-4 SACRED @[24rem]:inline-flex |
| `sub-tabs-bar.test.tsx` | 26 | SC-1..SC-9 + keyboard roving tabindex + defensive nullguard |
| `toggle-pill.test.tsx` | 5 | Render, items, defaultValue, 3-mode, Spanish neutro |

Generic mock catalog throughout: agents "alfa"/"beta", supervisor "Supervisora Test". Zero brand tokens.

#### RN-4 SACRED test (critical regression guard)

```typescript
it("★ RN-4 SACRED: mode pill has @[24rem]:inline-flex (container query, NOT viewport breakpoint)", () => {
  renderHeader();
  const pill = screen.getByTestId("chat-mode-pill");
  expect(pill.className).toContain("@[24rem]:inline-flex");
  expect(pill.className).not.toContain("md:inline-flex");
});
```

### 3. `CHANGELOG.md`

Updated with T-K2 (32 visual components) and T-K3 (barrel + 91 tests + routing bugfix) sub-entries under 0.4.0. Includes migration notes for brands consuming the lift.

## Bugfix shipped (routing.ts)

`segmentsOf()` + the three `extract*FromPath()` functions now accept `string | null | undefined` pathname. Prevents crash when `usePathname()` returns `null` in SSR/test context. This was a latent bug caught by the null-pathname defensive test.

## Kit state after T-K3

```
@luana/ui-kit 0.4.0
├── src/index.ts               — full barrel (organism/shell re-exported)
├── src/organism/shell/        — 32 components + factory + types + routing
│   ├── __tests__/             — 7 test files (batch-1 + batch-2)
│   └── routing.ts             — null-safe pathname helpers
└── CHANGELOG.md               — 0.4.0 T-K1/T-K2/T-K3 + migration notes
```

Brands can now import any shell organism symbol directly from `@luana/ui-kit`.
