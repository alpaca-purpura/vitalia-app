# T-4 Implementation Log — AppPanelSlot Integration + Arch Tests

**Story:** vitalia-fase1-ribbon-6-tabs
**Ticket:** T-4
**Surface:** frontend
**Builder:** claude-sonnet-4-6
**Date:** 2026-05-25

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, quality baseline, arch tests protocol | Server-first default: AppPanelSlot stays Server Component; imports Client Component `<Ribbon />` — correct Next.js App Router boundary |
| `tessl__react-patterns` | Error boundaries, loading/empty states, accessible markup | Section/role=region/aria-label preserved; aria-busy not needed (static layout); aria-hidden on skeleton bars preserved |
| `tessl__nextjs-app-router-modularization` | Page mixes Server/Client concerns | AppPanelSlot (Server) imports Ribbon (Client) — natural boundary. No "use client" added to AppPanelSlot. `test_server_first.test.ts` already auto-detects; no changes needed since Ribbon already has "use client". |
| `tessl__shadcn-ui` | Component selection | Ribbon uses `<nav>` + `<button role="tab">` with roving tabindex — NOT Shadcn `<Tabs>` (route-based nav requires URL state, not internal Radix state). Arch test `test-ribbon-no-shadcn-tabs.test.ts` enforces this invariant. |
| `tessl__vitest` | Test setup, mocking Client Component dependencies | `vi.mock("next/navigation")` for usePathname/useRouter/useParams; `beforeEach(() => vi.clearAllMocks())` for isolation. |

---

## Files Modified

### MODIFY: `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx`

**Change summary:**
- Removed: 5 skeleton agent circles with `bg-agent-{slug}-soft opacity-65 rounded-full` classes
- Added: `import { Ribbon } from "./Ribbon"` + `<Ribbon />` as first child
- Updated: `aria-label` from `"Panel aplicación (placeholder — F1-S7/S8/S10 lo construirá)"` → `"Panel aplicación"`
- Updated: slot label text from `"AppPanelSlot · F1-S7 / S8 / S10"` → `"AppPanelSlot · F1-S8 / S10"` (S7 done)
- Updated: children rendering — direct (not absolute overlay) + content skeleton when no children
- Preserved: sub-tabs placeholder (`.h-10` with skeleton bars) — F1-S8 will replace
- Preserved: content skeleton (`.bg-muted.opacity-45` bars) — F1-S10 will replace
- Preserved: `data-testid="app-panel-slot"`, `role="region"`, named export

**Server/Client boundary decision:** AppPanelSlot remains a Server Component. It imports `<Ribbon />` which is a Client Component — this is the correct Next.js App Router pattern. The Client boundary lives at `Ribbon.tsx` (which has `"use client"`). No need to add `"use client"` to AppPanelSlot.

### MODIFY: `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx`

**Change summary:**
- Added `vi.mock("next/navigation", ...)` to provide usePathname/useRouter/useParams stubs for `<Ribbon />`
- Added `beforeEach(() => vi.clearAllMocks())` for mock isolation
- Tests updated to assert real Ribbon presence (`data-testid="ribbon"` nav with `role="tablist"`)
- Tests updated to assert skeleton circles REMOVED (`.rounded-full.opacity-65` count = 0)
- Tests updated for new aria-label value (`"Panel aplicación"` not placeholder text)
- Tests updated for new slot label (`"AppPanelSlot · F1-S8 / S10"`)
- 11 tests total, all GREEN

### NEW: `vitalia/frontend/src/__tests__/architecture/test-ribbon-no-shadcn-tabs.test.ts`

**Arch invariant:** Ribbon.tsx, RibbonTab.tsx, ConfigTab.tsx MUST NOT import from `@/components/ui/tabs`.

**Rationale:** Shadcn `<Tabs>` uses Radix TabsRoot/TabsTrigger/TabsContent API which manages active state internally and assumes inline content rendering — incompatible with Vitalia's route-based agent navigation pattern. The correct pattern is roving tabindex WAI-ARIA tablist with `usePathname()` for active state.

**Tests (6 total):**
- `Ribbon.tsx does NOT import from '@/components/ui/tabs'`
- `Ribbon.tsx does NOT use <Tabs*> JSX`
- `RibbonTab.tsx does NOT import from '@/components/ui/tabs'`
- `RibbonTab.tsx does NOT use <Tabs*> JSX`
- `ConfigTab.tsx does NOT import from '@/components/ui/tabs'`
- `ConfigTab.tsx does NOT use <Tabs*> JSX`

All 6 PASS (files verified to use `<button role="tab">` pattern).

### EXTEND: `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts`

**Change:** Added `Ribbon` to the F1-S7 describe block (was already had `RibbonTab`, `ConfigTab`, `AGENT_RIBBON_ORDER`, `extractAgentFromPath` — `Ribbon` itself was missing). Updated describe title from `T-2` to `T-4`.

New test: `"no matches for Ribbon in nicolify/comunify/lupulo"` — 21 tests total, all PASS.

### EXTEND: `vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts`

**Change:** Added new describe block `"F1-S7 Ribbon shell-organism microcopy — SC-8 i18n (T-4 EXTEND)"`:
- Added `RIBBON_SHELL_FILES` constant (Ribbon.tsx, RibbonTab.tsx, ConfigTab.tsx, agent-catalog.ts)
- Per-file voseo scan with graceful skip if file not found (T-2/T-3 dependency guard)
- Test: `agent-catalog.ts` contains "Mi Clínica" (tilde on Clínica)
- Test: `agent-catalog.ts` contains "Adrián" (tilde), no plain "Adrian" in non-comment lines

**ESLint fix applied:** replaced `require("fs").existsSync(absPath)` (forbidden `@typescript-eslint/no-require-imports`) with `existsSync` from the ES module import `import { existsSync, readFileSync } from "fs"`.

24 tests total, all PASS.

### `test_server_first.test.ts`: No changes needed

Examined the test: it only tracks `KNOWN_MISSING_USE_CLIENT` (files that use hooks WITHOUT "use client" directive). Since `Ribbon.tsx`, `RibbonTab.tsx`, `ConfigTab.tsx` all already have `"use client"` — they cause no violations. The test auto-passes without allowlist modification.

---

## Quality Gate Results

| Gate | Status | Notes |
|---|---|---|
| tsc --noEmit | PASS | 0 errors |
| ESLint (scoped) | PASS | Fixed require() → existsSync import in voseo test |
| Prettier (scoped) | PASS | Auto-fixed 4 files |
| AppPanelSlot.test.tsx | PASS | 11/11 tests GREEN |
| Arch fitness (full) | PASS | 107/107 tests across 18 test files |
| Full vitest --coverage | PASS | 1327/1327 tests across 137 files |

---

## ESLint Warning Baselines

No new ESLint warnings introduced. All modified files lint clean (0 errors, 0 warnings).

---

## §11 Gaps (from CONTEXT-BRIEF partial flag)

None — CONTEXT-BRIEF `Faithfulness flag: clean`.

---

## Live Verification

`chrome-devtools-verify` skill DEPRECATED for Linux Mint (WSL2+Windows bridge, requires rewrite). Escalated to Chris staging gate per protocol. Manual verification steps:
1. Start vitalia dev stack: `make dev-vitalia`
2. Navigate to `http://localhost:3002/{tenantId}/valeria/agenda`
3. Verify Ribbon renders with 5 agent tabs + ConfigTab
4. Verify clicking each tab updates URL + active state
5. Verify keyboard navigation (Arrow keys + Home/End)
6. Verify AppPanelSlot sub-tabs placeholder still visible below Ribbon
