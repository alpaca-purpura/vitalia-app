# T-7 Result — Integration MODIFY + cleanup + arch tests extend

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Ticket:** T-7 — Wave 3 final
**State:** pushed
**Commit:** `42ed35b3`
**Branch:** wip/vitalia
**Date:** 2026-05-24

---

## Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | T-7 es ticket FE modificación shell organism + arch tests | Confirmed strict ADD-ONLY constraint per Chris; snap-up Fix A preserved intact; MIN_VALERIA_PX change from 620→580 (D3 decision: rail XOR history 2-col, not 3-col) |
| `tessl__react-patterns` | Production component modification (ShellOrganismLayoutClient) | No new patterns added; existing error boundary, loading states, aria preserved; `<ValeriaSidebar />` drop-in replacement inherits all aria from the organism itself |
| `tessl__vitest` | New arch test file + test modifications | Added new `describe` block in ShellOrganismLayout.test.tsx with MIN_VALERIA_PX invariant tests; new test-shell-store-schema-readonly-f1-s5.test.ts with 11 invariant tests |
| `anti-duplication.md` (via frontend-fsd.md) | Cross-brand mirror arch tests extension | Confirmed 0 cross-brand matches for all 8 new F1-S5 component names; arch test extended to guard this permanently |

---

## Diff Summary

### MODIFY: `ShellOrganismLayoutClient.tsx`

Two surgical changes only (Chris constraint "no malogres lo demás"):

1. **Import swap**: `ValeriaSidebarSlot` → `ValeriaSidebar` (real organism from T-5)
2. **MIN_VALERIA_PX**: `valeriaState === "full" ? 620 : 360` → `valeriaState === "full" ? 580 : 360`
   - D3 rationale: new 2-col XOR model — `full` = [History 280 | Chat 300 min] = 580px (old 3-col wrongly added rail 60 + history 280 + chat 280 = 620)
   - Comment updated to cite D3 F1-S5 XOR decision
3. **JSX replacements**: both `<ValeriaSidebarSlot />` occurrences (agentic panel + web mode grid) → `<ValeriaSidebar />`

**Preserved intact**: snap-up Fix A (useGroupRef useEffect), ResizeObserver, percent calculation, clampPct, layoutProps, TopBarGlobal, ShellModeToggle, AppPanelSlot, Separator, mobile main, all aria attributes.

### MODIFY: `ShellOrganismLayout.test.tsx`

- Mock updated: `vi.mock("./ValeriaSidebarSlot", ...)` → `vi.mock("./ValeriaSidebar", ...)` with `data-testid="valeria-sidebar"`
- Assertion updated: `getAllByTestId("valeria-sidebar-slot")` → `getAllByTestId("valeria-sidebar")`
- Test renamed: `"still renders valeria-sidebar-slot in web mode"` → `"still renders valeria-sidebar in web mode"`
- **New describe block** added: `"ShellOrganismLayout — MIN_VALERIA_PX invariant (D3)"` with 2 tests:
  - `MIN_VALERIA_PX === 580 when valeriaState='full'`
  - `MIN_VALERIA_PX === 360 when valeriaState='rail'`

### DELETE: `ValeriaSidebarSlot.tsx` + `ValeriaSidebarSlot.test.tsx`

Placeholder Server Component replaced by real `ValeriaSidebar` organism (T-5). Files deleted via `git rm` from earlier session; staged and committed cleanly.

### MODIFY: `test-no-cross-brand-shell-mirror.test.ts`

Extended with second `describe` block: `'arch: anti-duplication cross-brand mirror = 0 (F1-S5 NEW names T-7)'` containing 8 new tests:
- ValeriaSidebar, ValeriaRail, ValeriaHistory, ValeriaChatSlot, HistoryItem, HistoryGroup, EmptyStateInline, useKeyboardShortcuts — all confirm 0 matches in nicolify/comunify/lupulo

### NEW: `test-shell-store-schema-readonly-f1-s5.test.ts`

11 regression guard tests confirming shell-store.ts schema invariants:
- `ValeriaState` union: `collapsed | rail | full`
- `ShellMode` union: `agentic | web`
- `SHELL_STORAGE_KEY` === `'vitalia-shell-state'`
- Setters present: `setValeriaState`, `setShellMode`, `cycleValeriaState`
- Defaults: `valeriaState: 'full'`, `shellMode: 'agentic'`
- State transitions verify correctly (including `cycleValeriaState` rail↔full cycle)

---

## Validators Results

| Validator | Result | Notes |
|---|---|---|
| `val-fe-tsc` | PASS | `npx tsc --noEmit` — 0 errors. Initial run found TS2552 (ValeriaSidebarSlot not found after first edit); fixed by targeted second Edit for web mode grid; confirmed clean. |
| `val-fe-lint` | PASS | `npx eslint src/ --cache` — 0 errors. Baselines did not grow. |
| `val-fe-vitest-unit` | PASS | 1080/1080 tests pass across 126 test files. Targeted T-7 suite: 39/39 pass (ShellOrganismLayout.test.tsx + test-no-cross-brand-shell-mirror.test.ts + test-shell-store-schema-readonly-f1-s5.test.ts). |
| `val-fe-arch-no-cross-brand-mirror` | PASS | All 8 new F1-S5 names confirm 0 matches across nicolify/comunify/lupulo. |
| `val-fe-arch-shell-store-readonly` | PASS | 11 invariant tests pass; shell-store.ts was NOT modified (READ-ONLY respected). |
| `val-fe-arch-server-first` | PASS | `KNOWN_MISSING_USE_CLIENT` allowlist unchanged; ValeriaSidebar already has `"use client"` correctly applied. |
| `val-fe-arch-fsd` | PASS | No new cross-feature imports introduced. |
| `val-fe-arch-skip-link` | PASS | Triple-main pattern with `id="main-content"` preserved on all 3 branches (agentic/web/mobile). |

---

## Regression Check

**Snap-up Fix A (F1-S4 critical behavior) — PRESERVED INTACT:**
- `useGroupRef()` hook reference unchanged
- `useEffect([containerWidth, minValeriaPct, groupRef])` unchanged  
- `getLayout()` / `setLayout()` imperative calls unchanged
- ResizeObserver / `setContainerWidth` / `clampPct` unchanged
- `useDefaultLayout` / `layoutProps` / `onLayoutChanged` unchanged

**MIN_VALERIA_PX verification:**
- `full` path: `580` (D3 — 2-col XOR: history 280 + chat 300)
- `rail` path: `360` (unchanged from F1-S4 — rail 60 + chat 300)
- String percent enforcement via `\`${minValeriaPct}%\`` preserved (native v4 drag clamping)

**ValeriaSidebar integration:**
- `data-testid="valeria-sidebar"` confirmed at lines 147, 159, 182, 206 in ValeriaSidebar.tsx
- Drop-in replacement: aside role="complementary" aria-label="Panel Valeria" preserved from organism
- `"use client"` directive present in ValeriaSidebar.tsx (no SSR issues)

---

## F1-S5 Wave 3 Closure

T-7 completes Wave 3 (integration). Story dependency chain:
- T-1 (hook) ✅ pushed `2ffb9200`
- T-4 (ValeriaHistory) ✅ pushed `a3494da1`
- T-5 (ValeriaSidebar organism) ✅ pushed `3b4db9c6`
- T-6 (TopBarGlobal hamburger) ✅ pushed `5d68436b`
- **T-7 (integration + cleanup + arch tests) ✅ pushed `42ed35b3`** ← THIS TICKET

**Remaining:** T-2 (mock data — ready), T-3 (atoms+molecules — ready), T-8 (Playwright E2E + visual goldens — ready, depends T-1..T-7)

T-7 unblocks T-8 (final Wave 4).

---

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (per project context 2026-05-15 note — designed for WSL2+Windows bridge). Manual verification steps for Chris staging gate:

1. `make dev-vitalia` to bring up stack
2. Navigate to `http://localhost:3002/test-stack/shell-layout`
3. Verify `ValeriaSidebar` renders (not the old slot skeleton silhouettes)
4. Press `f` → full state: observe Valeria panel has [History 280px | Chat 1fr] XOR layout
5. Press `r` → rail state: observe [Rail 60px | Chat 1fr] XOR layout
6. Drag resize handle in agentic mode: confirm 580px minimum enforced (no squeezing below)
7. Inspect console: no errors, snap-up Fix A fires correctly on hydration

Escalated to Chris staging gate for live verification.
