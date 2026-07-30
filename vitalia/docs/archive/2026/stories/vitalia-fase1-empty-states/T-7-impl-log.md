# T-7 Implementation Log

**Story:** vitalia-fase1-empty-states  
**Ticket:** T-7  
**Date:** 2026-05-26  
**Session context:** resumed from prior session (context compaction at 6 files already created)

---

## Implementation Order

### Phase 1 — Molecules (prior session, pre-compaction)
1. `AgendaToolbar.tsx` — Client Component. Period toggle + CTA dropdown.
2. `AgendaFilters.tsx` — Server Component. 6 disabled chips.
3. `AgendaDayHeader.tsx` — Server Component. Day column header.
4. `AgendaSlot.tsx` — Server Component. Appointment block with 4 status + 4 origins.
5. `AgendaSummaryFooter.tsx` — Server Component. Status legend + summary text.

### Phase 2 — Organism (prior session, pre-compaction)
6. `AgendaPlaceholder.tsx` — Client Component. Full agenda grid orchestrator.

### Phase 3 — Tests (this session, post-compaction)
7. `AgendaSlot.test.tsx` — 11 tests (4 status variants, 4 origin icons, note, voseo).
8. `AgendaToolbar.test.tsx` — 13 tests (period toggle, CTA dropdown, nav).
9. `AgendaPlaceholder.test.tsx` — 13 tests (6 day headers, 10 slots, footer).

### Phase 4 — Barrel + Quality fixes
10. `vitalia/frontend/src/features/valeria/index.ts` — barrel exports for all 5 molecules + organismo.
11. Fix `"use client"` position (line 1 before JSDoc) to satisfy arch test FE-A5.
12. Replace `hsl(var(--agent-*))` with Tailwind utility classes (`text-agent-adrian`, etc.) to satisfy arch test FE-A1.
13. Move lunch stripe gradient to `.agenda-lunch-stripe` class in `globals.css`.
14. Fix React key prop: replace `<>` fragment with `<div className="contents">` keyed wrapper.

---

## Issues Encountered and Fixes

### Issue 1: `"use client"` not detected by arch test FE-A5
**Root cause:** Both `AgendaToolbar.tsx` and `AgendaPlaceholder.tsx` had `"use client"` after a long JSDoc comment (line 18 / line 28). The arch test checks `source.slice(0, 500)` for the directive using regex `/^\s*["']use client["']/m`. Since the JSDoc is >500 chars, the directive wasn't found.
**Fix:** Moved `"use client"` to line 1 (before the JSDoc) in both files.
**Note:** EmbudoPlaceholder.tsx has the same pattern and also places `"use client"` after JSDoc — but its JSDoc is also >500 chars. The test was not failing for EmbudoPlaceholder, suggesting the test was recently added or the file was excluded for other reasons. Regardless, the fix is correct: directive before JSDoc.

### Issue 2: `hsl()` inline Tailwind arbitrary values blocked by arch test FE-A1
**Root cause:** Used `text-[hsl(var(--agent-valeria))]`, `bg-[hsl(var(--agent-adrian-soft))]`, etc. as Tailwind arbitrary values. The arch test regex `hsl\s*\(` matched these in the source files.
**Fix:** Replaced ALL `hsl(var(--agent-*))` inline values with Tailwind utility classes that exist in `tailwind.config.ts`: `text-agent-valeria`, `text-agent-adrian`, `text-agent-lucas`, `bg-agent-valeria-soft`, `bg-agent-adrian-soft`, `border-agent-valeria`, `border-agent-adrian`, and opacity modifiers `bg-agent-adrian/20`, `from-agent-adrian/10`, `to-agent-adrian/5`.

### Issue 3: Lunch stripe CSS gradient contained `hsl()` in inline style
**Root cause:** AgendaPlaceholder had `style={{ background: "repeating-linear-gradient(...hsl(var(--muted))...)" }}`. The arch test scans ALL TS/TSX source strings.
**Fix:** Added `.agenda-lunch-stripe` CSS class to `globals.css` (which is EXEMPT from the hardcoded color test) with the gradient definition. Replaced inline style with `className="agenda-lunch-stripe ..."`.

### Issue 4: React key prop warning
**Root cause:** `TIME_SLOTS.map((time, rowIdx) => { return <> ... </> })` — fragments cannot have keys.
**Fix:** Replaced `<>` with `<div key={...} className="contents">` (CSS `display: contents` preserves grid layout without adding a visual wrapper).

---

## Skills Consulted

| Skill | Why Invoked | Key Decision |
|---|---|---|
| `frontend-expert` | ALWAYS mandatory — FSD boundaries, arch tests, ESLint config | Confirmed Tailwind agent tokens exist; `"use client"` must be first line; `contents` div for grid |
| `tessl__react-patterns` | Error boundaries, stable keys, memoization | Keyed wrapper via `className="contents"`; no memoization needed for Server Components |
| `tessl__shadcn-ui` | Component reuse | Used `cn()` throughout; no primitive recreation |
| `tessl__tailwind` | No inline styles, tokens | All agent colors via Tailwind classes; gradient to globals.css |
| `tessl__vitest` | Test setup, async | RED-first per EmbudoPlaceholder.test.tsx pattern |
| `tessl__nextjs-app-router-modularization` | Server+Client boundary | AgendaPlaceholder Client + Server Component children valid in Next.js 15 |

---

## Pre-existing Issues (NOT introduced by T-7)

- `src/features/adrian/components/inbox/ContactSidebar.tsx` TS errors (`patient` undefined, implicit `any`) — introduced by background agent T-5 inbox (currently running). Not in T-7 scope; confirmed via `git log`.

---

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Manual verification steps:

1. Start dev server: `make dev-vitalia` (port 3002)
2. Navigate to any Valeria/Agenda sub-tab in the shell
3. Verify: 6-column grid visible, 10 slots rendering, toolbar period toggle works, CTA dropdown opens/closes, lunch stripe at 13:00, footer shows "Adrián propuso 4 turnos hoy"
4. Escalated to Chris staging gate per protocol (chrome-devtools-verify unavailable on Linux Mint).
