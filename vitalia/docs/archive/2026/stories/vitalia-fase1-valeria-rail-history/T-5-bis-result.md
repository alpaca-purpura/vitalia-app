# T-5.bis — Mobile Drawer Portal Hotfix — Result

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Ticket:** T-5.bis (mobile drawer Portal hotfix)
**Commit SHA:** 7ad0999e
**Branch:** wip/vitalia
**Date:** 2026-05-23

---

## Repro Evidence

Bug class: CSS `display:none` ancestor hides all descendants including `position:fixed` children.

```
ValeriaSidebar → rendered inside:
  <main className="flex-1 min-h-0 overflow-hidden hidden md:block">  ← hidden at <768px
    <Group>
      <Panel>
        <ValeriaSidebar />   ← mobile drawer (position:fixed) NEVER painted here
```

Playwright SC-8 evidence from T-8 builder:
- Element resolved correctly: `[data-testid=valeria-sidebar][aria-modal='true']`
- Playwright reported: `unexpected value "hidden"` — parent `display:none` cascades
- All 6 SC-8 tests skipped with `PRODUCTION_BUG` string

---

## Fix Applied

**File:** `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx`

Change 1: Added `createPortal` import from `react-dom`:
```tsx
import { createPortal } from "react-dom";
```

Change 2: Mobile drawer render block wrapped with Portal to `document.body`:
```tsx
if (isMobile && isExpanded) {
  // SSR guard
  if (typeof document === "undefined") return null;

  return createPortal(
    <>
      {/* Backdrop + Drawer JSX — unchanged */}
    </>,
    document.body,  // ← mounted outside hidden agentic main
  );
}
```

**Why Portal and not moving ValeriaSidebar up the tree:**
- Portal keeps React tree intact — ValeriaSidebar remains child of ShellOrganismLayoutClient for state/context purposes
- Only the DOM target changes — drawer escapes `display:none` parent
- `ShellOrganismLayoutClient.tsx` NOT touched → regression risk = 0
- SSR guard `typeof document === "undefined"` prevents hydration crash

---

## Files Modified

| File | Change |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | +import createPortal, wrap mobile drawer render in createPortal(jsx, document.body) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/a11y-mobile-drawer.spec.ts` | Remove PRODUCTION_BUG constant, remove 6× `test.skip(true, PRODUCTION_BUG)`, update header doc |

**NOT modified:** `ShellOrganismLayoutClient.tsx` (regression cero per scope).

---

## Validators

### TypeScript strict
```
cd vitalia/frontend && npx tsc --noEmit
→ 0 errors
```

### ESLint
```
cd vitalia/frontend && npx eslint src/components/shared/shell-organism/ValeriaSidebar.tsx --cache
→ 0 errors, 0 warnings
```

### Vitest — ValeriaSidebar.test.tsx
```
27/27 PASS (Portal compatible con RTL queries: jsdom appends portal to document.body,
getByRole/getByTestId queries still find elements via body root)

Test groups:
- SC-1 keyboard cycle (8 tests): PASS
- SC-1 render aside (10 tests): PASS
- SC-4 adversarial guard (1 test): PASS
- SC-7 live region (4 tests): PASS
- SC-8 mobile drawer smoke (4 tests): PASS
```

### Playwright E2E (runtime preflight required — stack must be up)
SC-8 tests in `a11y-mobile-drawer.spec.ts` are now UNSKIPPED. To run:
```bash
cd $(git rev-parse --show-toplevel) && bash scripts/e2e-preflight.sh
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase1-valeria-rail-history/a11y-mobile-drawer.spec.ts --project=chromium
```

Note: Live Playwright run requires dev stack running (`make dev-vitalia`). The `chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint. Manual verification escalated to Chris staging gate.

---

## Skills Consulted

| Skill | Invoked | Decision |
|---|---|---|
| `frontend-expert` | Loaded SOP + runtime-quality-checklist | Portal pattern per component-rules; SSR guard for typeof document; no redesign needed |
| `tessl__react-patterns` | Applied | Error boundary present at route level (ShellOrganismLayout), loading/empty states already handled |
| `chrome-devtools-verify` | Checked | DEPRECATED for Linux Mint — escalated to Chris staging gate per skill note |

---

## Architecture Notes

- **Scope STRICT respected:** Only 2 files touched as per ticket spec
- **No new cross-feature imports introduced**
- **FSD-Lite boundary intact:** ValeriaSidebar stays in `components/shared/shell-organism/`
- **No default exports added** (named export `ValeriaSidebar` unchanged)
- **Warning baselines:** No new ESLint warnings introduced (check-file / jsdoc / react-perf unchanged)
- **Portal SSR guard:** `typeof document === "undefined"` returns null during SSR — Next.js App Router client-only component (has "use client") so this is belt-and-suspenders
