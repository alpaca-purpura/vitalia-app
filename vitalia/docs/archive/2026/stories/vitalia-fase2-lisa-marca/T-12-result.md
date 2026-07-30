# T-12 Result — FE a11y axe-core WCAG 2.1 AA

**Ticket:** T-12
**Story:** vitalia-fase2-lisa-marca (F2-S7)
**State:** pushed
**Date:** 2026-05-27

---

## Deliverables

| Deliverable | Status |
|---|---|
| `vitalia/frontend/e2e/a11y/lisa-marca-a11y.spec.ts` | CREATED |

## G5 Gate

| Gate | Result |
|---|---|
| tsc --noEmit | PASS |
| eslint | PASS |
| playwright --list | PASS (24 tests in `a11y` project) |

## Test Count

| Category | Tests |
|---|---|
| Idle state scans (3 subsubtabs) | 3 |
| Loading state scans (3 subsubtabs) | 3 |
| Success state scans (3 subsubtabs) | 3 |
| Error state scans (3 subsubtabs) | 3 |
| Empty state scans (3 subsubtabs) | 3 |
| Keyboard navigation tests | 5 |
| **Total** | **20** |

## Acceptance Criteria

| AC | Status | Notes |
|---|---|---|
| A1: axe-core 0 critical + 0 serious violations across 3 subsubtabs × 5 states | PLANNED (staging required) | Spec validates WCAG 2.1 AA on running stack |
| A2: Keyboard nav `aria-current="page"` correct + focus ring visible | PLANNED (staging required) | 5 keyboard nav tests included |

## WCAG Tags

`['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']` — full WCAG 2.1 AA per ticket spec.

## Notes

Tests require `E2E_BASE_URL=http://localhost:3002` with running Vitalia dev stack.
All API calls mocked via `page.route` — no real backend required.
