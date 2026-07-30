# T-3 Implementation Log — Ribbon organism

**Story:** vitalia-fase1-ribbon-6-tabs (F1-S7)
**Ticket:** T-3 — Ribbon organism root + roving tabindex WAI-ARIA + URL-derived active + navigateTo
**Builder:** Claude Sonnet 4.6
**Date:** 2026-05-25

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | Baseline FSD-Lite structure, component boundaries, quality gates | Applied FSD-Lite shell-organism pattern; "use client" as first directive per arch test enforcement; named export only |
| `tessl__react-patterns` | Error boundaries, accessible markup, stable keys, memoization | role="tablist" + aria-label + role="tab" + aria-selected + aria-busy; useCallback for handlers; stable keys via slug |
| `tessl__nextjs-app-router-modularization` | Ribbon is Client Component (uses hooks) | Confirmed "use client" required; no Server Component split needed (organism is fully client) |
| `tessl__tailwind` | cn() usage, no inline style | Applied cn() pattern; all classes via Tailwind tokens |

## Iteration Log

### iter-1 — Initial implementation

**Phase RED (tests first):** `Ribbon.test.tsx` written covering 39 tests across all gherkin scenarios (SC-1, SC-2, SC-3, SC-4, SC-7, defensive, focus management).

**Phase GREEN (implementation):** `Ribbon.tsx` written per 03-arch.md § 2.2 pseudo-code.

**Issue 1 — TypeScript: AgentSlug cast**
- `AGENT_RIBBON_ORDER.indexOf(activeSlug as AgentSlug)` failed: `AGENT_RIBBON_ORDER` is typed as `readonly ("lisa" | "valeria" | "adrian" | "lucas" | "camila")[]` (excludes "mateo"), but `activeSlug` can be any `AgentSlug` including "mateo".
- Fix: Cast `(AGENT_RIBBON_ORDER as readonly string[]).indexOf(activeSlug)` — safe since indexOf of non-member returns -1, which is handled by the `>= 0` guard.

**Issue 2 — TypeScript: test mock defensive cases**
- `mockParams.mockReturnValue(null)` and `mockParams.mockReturnValue({})` failed TS strict check since the mock is typed with `{ tenantId: string }`.
- Fix: Added `as any` casts with ESLint disable comments for those 3 test lines — acceptable in test-land for defensive boundary testing.

**Issue 3 — Arch fitness: "use client" must be first line**
- The arch test `test_server_first.test.ts` checks that "use client" is the first non-empty line of files with client hooks.
- Initial file had JSDoc comment before "use client" directive.
- Fix: Moved `"use client";` to line 1 (before JSDoc).

**Issue 4 — ESLint: unused AgentSlug import**
- After changing the cast to `readonly string[]`, `AgentSlug` import became unused.
- Fix: Removed `type AgentSlug` from imports.

### Validation results (iter-1 final)

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/` | 0 errors, 0 new warnings |
| `vitest run --coverage` | 136/136 test files PASS, 1311/1311 tests PASS |
| Architecture fitness | All 20 arch tests PASS (including `test_server_first` with "use client" first line) |

## Key decisions

1. **onKeyDown on `<nav>` element** — per 03-arch.md, keyboard handler lives on the `<nav>` element. Events bubble up from child buttons naturally. No need to extend RibbonTab or ConfigTab props with `onKeyDown`.

2. **No `<TooltipProvider>` in Ribbon** — ConfigTab already wraps Tooltip internally. The `Tooltip` component in `components/ui/tooltip.tsx` includes TooltipProvider internally, so no outer provider needed.

3. **`(AGENT_RIBBON_ORDER as readonly string[]).indexOf(activeSlug)`** — safe modulo pattern; returns -1 for "mateo" or "config", then `>= 0` guard falls back to idx 0.

4. **Initial focusedIdx** — follows active tab from URL. If no active (invalid slug), defaults to 0. This means keyboard navigation starts at lisa on fresh load.

5. **Autosave on-change** — not applicable (no form). URL-derived state means no local "active" state to persist.

## Notes for T-4

- `AppPanelSlot.tsx` must add `Ribbon` to its `"use client"` allowlist in `test_server_first.test.ts`.
- T-4 must also extend `test-no-cross-brand-shell-mirror.test.ts` with "Ribbon", "RibbonTab", "ConfigTab", "extractAgentFromPath", "AGENT_RIBBON_ORDER".
- `AppPanelSlot` currently renders skeleton ribbon circles — T-4 replaces with `<Ribbon />`.
- The `data-testid="ribbon"` attribute in Ribbon is the integration point T-4's tests use.
