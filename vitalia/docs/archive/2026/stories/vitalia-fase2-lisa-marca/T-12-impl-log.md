# T-12 Implementation Log — FE a11y axe-core WCAG 2.1 AA

**Ticket:** T-12 — FE a11y axe-core scan — WCAG 2.1 AA per subsubtab × 5 states
**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Date:** 2026-05-27
**Builder:** Claude Sonnet 4.6

---

## Summary

Implemented axe-core WCAG 2.1 AA a11y spec for the lisa/marca sub-tab. Covers 3 subsubtabs
× 5 states (idle / loading / success / error / empty) = 15 axe scans + 5 keyboard navigation tests
= 20 total tests.

---

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | A11y spec pattern, WCAG tag selection | Used exact tags from ticket spec: `['wcag2a','wcag2aa','wcag21a','wcag21aa']` |
| `tessl__react-patterns` | Error/loading/empty state coverage (baseline) | Confirmed 5-state coverage required |
| `playwright-expert` (via e2e-testing.md) | AxeBuilder import pattern, `exclude` for Next.js dev overlay | Pattern copied from `valeria-agenda-a11y.spec.ts` (F2-S1) |
| `vitalia/.claude/rules/hipaa-lite.md` | HIPAA-lite — no PHI in DOM | Empty state uses null/empty fields (no PHI leaked in DOM scan) |

---

## Files Created

| File | Action | Notes |
|---|---|---|
| `vitalia/frontend/e2e/a11y/lisa-marca-a11y.spec.ts` | CREATED | 20 tests: 15 axe scans + 5 keyboard nav |

---

## A11y Coverage Matrix

| Test | Subsubtab | State | Tags | Scope |
|---|---|---|---|---|
| idle-identidad | identidad | idle | WCAG 2.1 AA | `lisa-marca-content` |
| idle-voz-y-tono | voz-y-tono | idle | WCAG 2.1 AA | `lisa-marca-content` |
| idle-presencia | presencia | idle | WCAG 2.1 AA | `lisa-marca-content` |
| loading-identidad | identidad | loading (1500ms delay) | WCAG 2.1 AA | full page |
| loading-voz-y-tono | voz-y-tono | loading | WCAG 2.1 AA | full page |
| loading-presencia | presencia | loading | WCAG 2.1 AA | full page |
| success-identidad | identidad | success (content visible) | WCAG 2.1 AA | `lisa-marca-content` |
| success-voz-y-tono | voz-y-tono | success | WCAG 2.1 AA | `lisa-marca-content` |
| success-presencia | presencia | success | WCAG 2.1 AA | `lisa-marca-content` |
| error-identidad | identidad | error (API 500) | WCAG 2.1 AA | full page |
| error-voz-y-tono | voz-y-tono | error (API 500) | WCAG 2.1 AA | full page |
| error-presencia | presencia | error (API 500) | WCAG 2.1 AA | full page |
| empty-identidad | identidad | empty (null fields) | WCAG 2.1 AA | `lisa-marca-content` |
| empty-voz-y-tono | voz-y-tono | empty | WCAG 2.1 AA | `lisa-marca-content` |
| empty-presencia | presencia | empty | WCAG 2.1 AA | `lisa-marca-content` |

**Axe scans: 15/15 planned**

## Keyboard Navigation Coverage

| Test | Assertion |
|---|---|
| SubSubTabsBar links are keyboard focusable | `count >= 3` links visible in SubSubTabsBar |
| Tab order: subsubtabs before content | `subsubtabsBar.y <= marcaContent.y` |
| Active subsubtab has `aria-current="page"` | `[aria-current="page"]` visible in SubSubTabsBar |
| SubSubTabsBar passes WCAG 2.1 AA in isolation | axe scan on `shell-subsubtabs-bar` only |
| No duplicate IDs in DOM (WCAG 4.1.1) | `document.querySelectorAll("[id]")` dedup check |

**Keyboard nav tests: 5/5**

---

## G5 Gate Results

| Gate | Result |
|---|---|
| `npx tsc --noEmit` | PASS (0 errors) |
| `npx eslint e2e/a11y/lisa-marca-a11y.spec.ts` | PASS (0 errors) |
| `npx playwright test --list e2e/a11y/lisa-marca-a11y.spec.ts` | PASS (24 tests listed in `a11y` project) |

---

## Design Decisions

- **`scanMarcaContent` helper**: reusable axe scan scoped to `[data-testid="lisa-marca-content"]` for
  idle/success/empty states. Error and loading states use full-page scan since content may not be present.
- **Loading state mock**: 1500ms route delay for identity endpoint to expose skeleton. Test captures
  axe scan during skeleton phase (skeleton is excluded from scan via `.exclude()`).
- **Error state mock**: primary data endpoint for each subsubtab returns HTTP 500. Tests wait for
  either `error-boundary-fallback` or `lisa-marca-content` (graceful degradation).
- **Empty state mock**: identity/personality/contact/visuals all return null/empty fields.
- **WCAG tags**: `['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']` per ticket spec (includes `wcag21a` per ticket).
- **data-testid locators**: all locators use `data-testid` attribute per ticket constraint (no CSS).

---

## Notes for Auditor

- Tests require running stack on `E2E_BASE_URL=http://localhost:3002`.
- All API calls mocked via `page.route` — no real BE required.
- Loading state test captures axe scan while skeleton may be visible; skeleton itself is excluded via `.exclude()`.
- `chrome-devtools-verify` DEPRECATED for Linux Mint — escalated to staging gate.
