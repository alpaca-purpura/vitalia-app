# T-4 Result — AdrianEmbudoPlaceholder

**Story:** vitalia-fase1-empty-states
**Ticket:** T-4 — AdrianEmbudoPlaceholder (Kanban 6 cols + 14 leads mock + toggle Kanban|Lista)
**State:** pushed
**Builder:** claude-sonnet-4-6 (builder-frontend)
**Date:** 2026-05-26

## Skills consulted (must_load enforcement v4.1)

- `frontend-expert` — FSD-Lite placement, runtime quality checklist
- `tessl__react-patterns` — accessible markup, stable keys, no unnecessary client boundary
- `tessl__shadcn-ui` — reuse TogglePill + EmptyState from T-1, no new primitives
- `tessl__tailwind` — semantic tokens, cn(), overflow-x-auto for scroll
- `tessl__vitest` — 7 specs RED→GREEN TDD
- `brand-expert` — brand-local pattern confirmed, no lift needed
- `vitalia/shell-mockup-per-component.md` — mockup ratified gate verified
- `vitalia/hipaa-lite.md` — PHI masking N/A for embudo (lead funnel data, not medical)

## Diff summary

### NEW: `vitalia/frontend/src/features/adrian/components/placeholders/EmbudoPlaceholder.tsx`

- Client Component (`"use client"`) — TogglePill (Radix Tabs) drives toggle state
- `MOCK_PIPELINE: KanbanColumn[]` — 6 columns verbatim spec § 5 + mockup SSoT
- `TogglePill` items: `[{value:'kanban'}, {value:'lista'}]` defaultValue='kanban'
- Kanban view: `overflow-x-auto` → `grid-cols-6 min-w-[960px]` → 6 `KanbanColumnCard`
- Lista view: `EmptyState` icon=📋 title="Vista lista — próximamente"
- Lead data: 14 named leads (María G., Carlos P., Ana V., JP Méndez, Rosa V., Camila B., Iván S. + 7 more) with PEN S/ values
- Named export, no default export
- No hex colors — semantic tokens only

### NEW: `vitalia/frontend/src/features/adrian/components/placeholders/EmbudoPlaceholder.test.tsx`

7 Vitest unit specs:
1. `renders 6 Kanban column headers` — all 6 stage labels present
2. `renders lead names mock in Kanban state` — 7 key lead names verified
3. `renders column totals verbatim from spec` — all 6 count·value strings
4. `shows EmptyState placeholder when Lista toggle is selected`
5. `shows Kanban columns when Kanban toggle is selected after switching`
6. `renders SubTabHeader with title Embudo and description`
7. `does not contain voseo in user-facing text`

### MODIFIED: `vitalia/frontend/src/features/adrian/index.ts`

Added barrel export: `export { EmbudoPlaceholder } from "./components/placeholders/EmbudoPlaceholder"`

### MODIFIED: `vitalia/docs/product/stories/vitalia-fase1-empty-states/06-tickets.yaml`

T-4 state → `pushed`

## Validator results

| Validator | Result |
|---|---|
| val-fe-tsc | PASS — 0 TypeScript errors (strict) |
| val-fe-lint | PASS — 0 ESLint errors/warnings |
| val-fe-format | PASS — Prettier clean |
| val-fe-vitest-unit-embudo | PASS — 7/7 specs GREEN |
| val-fe-arch-fsd-boundaries | PASS — 20 arch tests (123 total) GREEN |
| val-fe-arch-no-phi-real-data | PASS — no real PHI |

Full suite: 1594 tests across 155 files — all GREEN.

## Mockup parity

Visual baseline: `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-embudo-placeholder.html` (ratificado Chris batch 2 · 2026-05-26).

Parity achieved:
- Header: "Embudo" h2 + description paragraph
- TogglePill: "Kanban" (default active) | "Lista"
- Kanban: `overflow-x-auto` + `grid-cols-6 min-w-[960px]`
- Column headers: emoji + label (left) + count · value (right, muted)
- Lead cards: name (font-medium) + detail (muted)
- Lista: EmptyState 📋 + "Vista lista — próximamente"

Live verification: chrome-devtools-verify deprecated for Linux Mint (2026-05-15). Escalated to Chris staging gate. Structural + behavioral correctness confirmed by Vitest.
