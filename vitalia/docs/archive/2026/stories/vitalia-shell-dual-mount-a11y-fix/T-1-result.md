---
ticket: T-1
story_id: vitalia-shell-dual-mount-a11y-fix
brand: vitalia
builder: builder-frontend (Sonnet 4.6)
date: 2026-06-01
commit: b65baae6
state: tests-passing
---

# T-1 Result — single-main + single-slot fix

## Diff summary

### Files modified

| File | Change |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | REWRITE — triple-main → single-main + single-slot (D1-D5) |
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.test.tsx` | REWRITE — old triple-main asserts → new single-main + single-slot asserts |

### Architecture decisions implemented

- **D1** — Single `<main id="main-content" tabIndex={-1} aria-label="Contenido principal">` wrapping ALL chrome variants. `containerRef` + `data-shell-ready` on this single `<main>`.
- **D2** — `<AppPanelSlot>{children}</AppPanelSlot>` rendered EXACTLY ONCE. Strategy: Valeria panel/separator hidden on mobile via CSS classes (`hidden md:flex` / `hidden md:block`), not via a separate mobile branch. This goes beyond nicolify (whose single-main still duplicated the slot in mobile branch).
- **D3** — ALL hooks called unconditionally at top before any branch: `useStoreHydration`, `useShellStore` selectors, `useViewportGuard`, `useRef`, `useState`×2, `useEffect`×2, `useGroupRef`, `useDefaultLayout`.
- **D4** — No `useMediaQuery`/`isDesktop` introduced. Desktop↔mobile gate is CSS only.
- **D5** — `<Group>` resizable always mounted; no conditional mount by viewport JS.

### Key difference from nicolify prior art

Nicolify (prior art read 2026-06-01): single `<main>` but STILL had `<AppPanelSlot>` in both desktop branch AND separate mobile branch → 2 slots in DOM on any viewport.

Vitalia fix: eliminates the separate mobile branch entirely. Mobile users see the same `<AppPanelSlot>` (inside the app-panel area) because Valeria panel container is CSS-hidden (not the whole structure). Single slot = 1 in DOM always.

## TDD RED→GREEN evidence

1. Rewrote `ShellOrganismLayout.test.tsx` with new assertions:
   - `document.querySelectorAll('#main-content').length === 1`
   - `getAllByTestId('app-panel-slot').length === 1`
   - `getAllByTestId('unique-child').length === 1`
2. Ran tests: **5 tests RED** against old triple-main component (confirmed correct RED state)
3. Rewrote `ShellOrganismLayoutClient.tsx` with single-main + single-slot
4. Ran tests: **22 tests GREEN**

## Gate output verbatim

```
# G5-1: ShellOrganismLayout.test.tsx
✓ src/components/shared/shell-organism/ShellOrganismLayout.test.tsx (22 tests) 104ms
Tests: 22 passed (22)

# G5-2: AppPanelSlot.test.tsx
✓ src/components/shared/shell-organism/AppPanelSlot.test.tsx (13 tests) 120ms
Tests: 13 passed (13)

# G5-3: skip-link arch test
✓ src/__tests__/architecture/test-skip-link-target.test.ts (2 tests) 1ms
Tests: 2 passed (2)

# G5-4: cross-brand mirror arch test
Tests: 23 failed | 3 passed (26)
→ PRE-EXISTING failures (verified by git stash + re-run before changes)
→ All 23 failures are about nicolify R0 shell rebuild (Ribbon, RibbonTab, SubTabsBar etc.)
→ NOT caused by this commit

# G5-5: TypeScript strict
cd vitalia/frontend && npx tsc --noEmit
→ 0 errors from src/ (exit 0)

# G5-6: ESLint
cd vitalia/frontend && npx eslint src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx src/components/shared/shell-organism/ShellOrganismLayout.test.tsx
→ 0 errors, 0 warnings
```

## Commit SHA

`b65baae6` — `fix(vitalia/shell-organism): T-1 single-main + single-slot — elimina triple-main pattern`

Files: 2 modified (313 insertions, 223 deletions)

## § Skills consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries, Server-First, runtime-quality-checklist (useEffect deps, stale closures) | Confirmed all hooks unconditional at top (D3); no new useEffect with missing deps; ESLint clean |
| `vitalia-design-system` | Shell SSoT: 5 agents Ribbon + Valeria sidebar, SHELL-DESIGN-CONTRACT, tokens | Confirmed `containerRef`/`data-shell-ready` stay on single `<main>`; aria-labels preserved in Spanish neutro LatAm |
| `tessl__react-patterns` | Hook-count stability (Rules of Hooks invariant) — core constraint of this bugfix | Verified D3: zero hooks inside JSX branches; `<Group>` always mounted not gated by JS viewport check (D4) |
| `tessl__vitest` | jsdom test patterns, mock setup for react-resizable-panels | `window.matchMedia` mock NOT needed (D4 confirmed: no `useMediaQuery` introduced); mock patterns preserved from existing test file |
| `chrome-devtools-verify` | Live verification gate (ADR-008, PR FE user-facing surface) | dev-app live verification is T-2 scope (depends_on T-1). T-2 covers Chrome MCP + Playwright transversal re-verification. T-1 is test-passing phase. |

## Mockup scope notes

This is a bugfix story (ADR-011). No `01-spec.md` / `02-design-ui.md` / mockups exist (correct per bugfix type). The SPEC is `checkpoint.md` + observed-bug doc.

## Live verification note

`chrome-devtools-verify` is T-2 scope (depends_on T-1, per `06-tickets.yaml`). T-2 covers:
- 5 agents × 3 modes transversal re-verification (vitest + axe)
- Chrome MCP live on dev-app (lisa + valeria desktop+mobile, console clean)
- E2E doctores: `getByTestId('btn-nuevo-integrante')` resolves to 1 without `.filter({visible:true})`

This T-1 result is `tests-passing`. T-2 escalates to live verification before `developed` state.
