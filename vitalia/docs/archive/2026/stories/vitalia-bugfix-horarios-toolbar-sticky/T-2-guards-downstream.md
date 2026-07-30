<!-- voseo-allowed: internal harness artifact per spanish-text.md R25 (not user-facing) -->
# T-2 — Guards (verde-fantasma fix) + downstream regression

**Date:** 2026-06-15 · **Brand:** vitalia (+ cross-brand core verification) · Story: vitalia-bugfix-horarios-toolbar-sticky
**Verdict:** PASS
**Scope:** reframe jsdom guard honestly · add REAL behavioural guard (Playwright) · add core root-cause guard (vitest ui-kit) · run mechanical gates incl. downstream consumers. The core fix itself (1 line, PM-verified live) was NOT touched.

---

## 1. Problem fixed: the verde-fantasma guard

The prior subagent left a jsdom structural test (`horarios-toolbar-sticky.test.tsx`) that
went GREEN while the bug was still live. jsdom has no layout engine → it cannot detect a
scroll/overflow bug; it only checks that Tailwind classes are present. The PM's live-verify
(T-1-LIVE-VERIFY.md) refuted the green: the real root cause was a CORE component mismatch
(`@luana/ui-kit AppPanelSlot` content host was a `block`, not a flex-column), and the vitalia
leaf classes the jsdom test pinned were already correct. Classic verification-real-≠-verde.

## 2. Guards created / reframed

### (a) jsdom structural guard — REFRAMED HONESTLY (kept, re-documented)

File: `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/__tests__/horarios-toolbar-sticky.test.tsx`

- Header rewritten: now states explicitly **"structural-class presence only — does NOT verify
  scroll behaviour (jsdom has no layout engine)"**, cites the verde-fantasma episode, and points
  to where behaviour IS verified (Playwright spec + core vitest + PM live-verify).
- `describe` block + the 4 misleading `it()` labels reframed: "stays fixed" / "owns the scroll"
  → "carries the … classes". No longer claims it proves the toolbar stays fixed.
- Kept because it is a cheap tripwire: if a future refactor strips the vitalia leaf classes
  (`overflow-hidden`/`min-h-0`), it trips. Necessary-but-not-sufficient complement.
- Status: **5/5 PASS** (green, now honest).

### (b) Behavioural guard — NEW (Playwright, REAL browser)

File: `vitalia/frontend/e2e/regression/vitalia-bugfix-horarios-toolbar-sticky/toolbar-sticky.spec.ts`

- Auth: `vitalia-fase2-lisa-doctores.fixture` (`staffPage` → Clerk admin_clinic + tenant
  injected + staff endpoints mocked), mirrors the existing lisa/staff specs.
- Flow: viewport 1280×720 → navigate `/{tenant}/lisa/staff/{doctorId}/horarios` → wait for the
  `[role=grid][aria-label="Calendario de disponibilidad"]` → click `toggle-24h` (24×48=1152px →
  guaranteed overflow) → record `boundingBox().top` of the page toolbars + day-header → scroll
  the grid scroller (`scrollTop=600`) → assert each toolbar/day-header `.top` drifts ≤ 2px while
  the grid content scrolls. Also asserts the grid is the scroller (`scrollHeight>clientHeight`,
  `scrollTop>0`) — proof the scroll moved into the grid (the fix), not the panel.
- This is the assertion jsdom could not make: real layout engine, real scroll, measured rects.
- Mocks the `availability-occurrences` endpoint with tall data — correct for a *layout* test
  (fixity depends on the CSS scroll chain, not on real data); deterministic + fast.
- `--list` (smoke project): compiles + collected. **Executed LIVE** against dev stack
  (FE :3002 + BE :8002, preflight green): **3 passed (14.8s)** = setup + auth + the behavioural
  test. Toolbars stayed fixed; grid owned the scroll. Behavioural verification CLOSED (not deferred).

### (c) Root-cause guard — NEW (vitest, core ui-kit)

File: `core/@luana/ui-kit/src/organism/shell/__tests__/AppPanelSlot.test.tsx`

- Asserts the content host that wraps `children` carries `flex` + `flex-col` (the root-cause
  clamp) AND keeps `overflow-y-auto` + `flex-1` + `min-h-0`; and the panel `<section>` stays
  `overflow-hidden min-h-0` (fixed frame).
- jsdom-honest: it pins class presence, which IS sufficient to catch a silent revert of the
  `flex flex-col` clamp — the exact regression that would re-break all 3 EWL-mounting brands.
- **RED/GREEN proven:** reverted the fix (`flex flex-col …` → `flex-1 …`) → 1 test FAILS
  (`content host is a flex-column`); restored → 4/4 PASS. Not verde-fantasma itself.
- Status: **4/4 PASS**.

---

## 3. Mechanical gates — status per surface (native host, NEVER Docker)

| Surface | Gate | Command | Status |
|---|---|---|---|
| **ui-kit (core)** | vitest | `npx vitest run` | ✅ 21 files / 270 tests PASS (incl. new AppPanelSlot 4/4) |
| ui-kit (core) | tsc --noEmit | `npx tsc --noEmit` | ⚠️ 142 errors — **PRE-EXISTING BASELINE**, see §4. New file adds **0** (proven by stash-and-recount). Package gate is vitest (green). |
| **vitalia FE** | tsc --noEmit | `npx tsc --noEmit` | ✅ exit 0 |
| vitalia FE | eslint | `npx eslint src/features/lisa --cache` | ✅ exit 0 |
| vitalia FE | eslint (new spec) | `npx eslint e2e/.../toolbar-sticky.spec.ts` | ✅ exit 0 |
| vitalia FE | vitest | `npx vitest run src/features/lisa` | ✅ 49 files / 524 tests PASS (sticky guard 5/5) |
| vitalia FE | Playwright (behavioural) | preflight ✓ → `E2E_BASE_URL=…3002 npx playwright test …toolbar-sticky.spec.ts --project=smoke` | ✅ 3 passed (LIVE run) |
| **nicolify FE (downstream)** | tsc --noEmit | `npx tsc --noEmit` | ✅ exit 0 |
| nicolify FE (downstream) | vitest (shell/app/arch) | `npx vitest run src/stores src/app src/lib/routing src/__tests__/architecture` | ✅ 8 files / 198 tests PASS |
| **comunify FE (downstream)** | tsc --noEmit | `npx tsc --noEmit` | ✅ exit 0 |
| comunify FE (downstream) | vitest (app/arch) | `npx vitest run src/app src/__tests__` | ✅ 4 files / 38 tests PASS |

**Downstream verdict:** the shared core change (`flex flex-col` on `AppPanelSlot` content host)
breaks NEITHER nicolify NOR comunify. Both consume the same core component; tsc + shell/layout/arch
suites GREEN in both. Per `auditor-downstream-regression.md`, cross-brand consumers verified.

---

## 4. Pre-existing ui-kit `tsc --noEmit` baseline (NOT introduced here — honest disclosure)

`core/@luana/ui-kit` has **142 pre-existing `tsc --noEmit` errors**, all in existing test files
and `timezone-select.tsx`:
- `Property 'toBeInTheDocument'/'toHaveAttribute'/'toHaveClass' does not exist on type
  'Assertion<…>'` across the whole existing test suite (EntitySubNavBar, archetypes, EntityInfoCard,
  EntityWorkspaceLayout, chat-header, toggle-pill, top-bar-shell, label, …) — jest-dom matcher types
  are not wired into the package's `tsc --noEmit` (vitest provides them at runtime).
- `Intl.supportedValuesOf` / implicit-any in `src/timezone-select.tsx` (lib config).

Proven pre-existing: stashing my new `AppPanelSlot.test.tsx` and re-running → **142** errors;
with it → **142** errors. My file uses only `toContain`/`toBeGreaterThan` on plain strings/numbers
(no jest-dom matchers) → contributes 0. The package's real quality gate is `vitest run` (270/270
green) + `typecheck` script; I did NOT mask the baseline and did NOT attempt to "fix" it (out of
scope for this bugfix; candidate for a ui-kit test-types HB if Chris wants it tracked).

---

## 5. Files touched

- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/__tests__/horarios-toolbar-sticky.test.tsx` (reframed header + labels — honest scope)
- `vitalia/frontend/e2e/regression/vitalia-bugfix-horarios-toolbar-sticky/toolbar-sticky.spec.ts` (NEW — behavioural Playwright guard)
- `core/@luana/ui-kit/src/organism/shell/__tests__/AppPanelSlot.test.tsx` (NEW — core root-cause guard)

NOT touched: the verified core fix (`AppPanelSlot.tsx:142` `flex flex-col`), the vitalia
complements (`AvailabilityCalendar` grid `+min-h-0`, `DoctorHorariosView` root `+overflow-hidden`),
any other feature, any other brand's source.

---

## 6. Net effect on the verde-fantasma

The bug now has THREE layered guards, each at the right altitude:
1. **Behaviour** (Playwright, real browser, LIVE-executed) — the toolbar genuinely stays fixed.
2. **Root cause** (vitest ui-kit, RED/GREEN-proven) — the `flex flex-col` clamp can't be reverted silently.
3. **Leaf tripwire** (jsdom, honestly reframed) — the vitalia leaf classes can't be stripped silently.

The earlier false green is replaced by a real green that fails when the bug returns.
