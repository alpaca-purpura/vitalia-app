# T-3 Result — ShellOrganismLayout + useViewportGuard + react-resizable-panels v4

**Story:** vitalia-fase1-shell-layout-5050
**Ticket:** T-3
**Commit:** dc39ba9d
**Branch:** wip/vitalia
**Date:** 2026-05-23

## Files Delivered

### New
- `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx` — Client Component, triple-main pattern, react-resizable-panels v4 Group/Panel/Separator
- `vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts` — one-way viewport guard hook
- `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.test.tsx` — 14 Vitest unit tests
- `vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.test.ts` — 7 Vitest unit tests
- `vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.tsx` — disabled chip stub (T-5 completes interaction)

### Modified
- `vitalia/frontend/package.json` — added `react-resizable-panels@^4.11.1`
- `pnpm-lock.yaml` — auto-updated by pnpm

## Validator Output

### TSC (val-fe-tsc)
```
npx tsc --noEmit
[no output — 0 errors]
```
**Status: PASS**

### ESLint (val-fe-lint)
```
npx eslint src/ --cache --max-warnings=0
[no output — 0 errors, 0 warnings]
```
**Status: PASS**

### Vitest (val-fe-vitest-unit)
```
Test Files  117 passed (117)
Tests       957 passed (957)
```
Includes 20 architecture fitness tests (all PASS).
**Status: PASS**

## Implementation Notes

### react-resizable-panels v4 API deviation from 03-arch.md
The 03-arch.md § 2.9 referenced v3 API (`PanelGroup`, `PanelResizeHandle`, `autoSaveId`, `direction`).
Installed version v4.11.1 uses a new API:

| 03-arch.md (v3) | Actual v4 | Notes |
|---|---|---|
| `PanelGroup` | `Group` | container component |
| `PanelResizeHandle` | `Separator` | accessibility-native |
| `direction="horizontal"` | `orientation="horizontal"` | prop renamed |
| `autoSaveId` | `useDefaultLayout({ id, ... })` | hook-based persistence |
| `Panel order={N}` | `Panel id={...}` | no `order` prop in v4 |

Layout persistence implemented via `useDefaultLayout({ id: "vitalia-shell-split-agentic", panelIds: [...], storage: localStorage })` — returns `{ defaultLayout, onLayoutChange, onLayoutChanged }` spread onto `Group`.

Test mocks updated to match v4 API names (Group, Panel, Separator, useDefaultLayout).

### Triple-main pattern
Three `<main id="main-content" tabIndex={-1}>` elements — CSS-driven mutually exclusive via Tailwind:
1. Agentic desktop: `hidden md:block` — contains `Group` with `Panel`s
2. Web desktop: `hidden md:grid grid-cols-[60px_1px_1fr]` — static CSS grid
3. Mobile fallback: `md:hidden` — single column, AppPanelSlot only

Only ONE main is visible at any viewport. Skip-link `#main-content` always resolves to a valid target.

### useViewportGuard one-way guard
- `FULL_STATE_MIN_VIEWPORT = 1104` (valeria 620 + handle ~4 + app 480)
- `MOBILE_BREAKPOINT = 768` (Tailwind `md`)
- Reads `useShellStore.getState().valeriaState` inside closure (avoids stale closure)
- RAF-debounced resize listener
- Cleanup via `removeEventListener` + `cancelAnimationFrame` on unmount
- NO auto-restore when viewport grows (one-way guard — user explicit via F1-S5 rail button)

## Gherkin Coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-1 happy: agentic default render | `ShellOrganismLayout.test.tsx`: renders TopBarGlobal + PanelGroup + Panel ids + PanelResizeHandle | PASS |
| SC-1 happy: skip-link target `id="main-content"` | `ShellOrganismLayout.test.tsx`: all main elements have id+tabIndex | PASS |
| SC-2 negative: mobile `<main md:hidden>` | `ShellOrganismLayout.test.tsx`: mobile branch exists with md:hidden | PASS |
| SC-3 edge: web mode grid no PanelGroup | `ShellOrganismLayout.test.tsx`: shellMode='web' renders no panel-group | PASS |
| SC-3 edge: viewport guard force 'rail' | `useViewportGuard.test.ts`: forces 'rail' at viewport=900 | PASS |
| SC-3 edge: no auto-restore on viewport grow | `useViewportGuard.test.ts`: state stays 'rail' after 900→1280 | PASS |
| SC-3 edge: no-op mobile <768 | `useViewportGuard.test.ts`: no-op at innerWidth=375 | PASS |
| SC-4 a11y: disabled ShellModeToggle | `ShellOrganismLayout.test.tsx`: toggle rendered disabled | PASS |

## Skills Consulted

- **frontend-expert**: FSD-Lite boundary (`components/shared/shell-organism/` correct for cross-feature chrome), `"use client"` required for hooks/DOM, test colocation, architecture fitness test expectation verified
- **tessl__react-patterns**: Error boundary at route level (ShellOrganismLayout wraps at layout level); loading/error/empty states deferred to slot content (F1-S5+); accessible markup (`aria-label`, `tabIndex=-1`, `role="separator"` on Separator); stable keys (id-based panels)
- **tessl__vitest**: Dynamic import pattern for RED-first TDD, `vi.mock` for react-resizable-panels + heavy deps, `useShellStore.setState()` for store setup
- **tessl__tailwind**: `cn()` for conditional classes on Separator, semantic tokens (`bg-border`, `bg-primary/40`), no inline styles
- **tessl__shadcn-ui**: react-resizable-panels v4 is the underlying lib of Shadcn `Resizable` primitive — confirmed v4 API differences from v3
- **tdd-mandatory**: RED (import fails) → GREEN (implementation) → REFACTOR (API v4 alignment + test mock updates)

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint native environment (designed for WSL2+Windows bridge, requires rewrite for Linux host). Manual verification steps escalated to Chris staging gate per skill deprecation notice:
1. `make dev-vitalia` to start stack
2. Navigate to `http://localhost:3002/{tenantId}` (dev port 3002)
3. Verify PanelGroup renders with Valeria + App panels
4. Drag resize handle, verify localStorage persistence
5. Resize viewport to 900px, verify valeriaState→'rail'
6. Verify mobile <768px shows only AppPanelSlot
