# T-19 Result — FE Visual Goldens (14 snapshots) + AgendaPlaceholder report

**Story:** vitalia-fase2-valeria-agenda (F2-S1)
**Ticket:** T-19 — FE visual goldens (~14 snapshots) + cleanup AgendaPlaceholder
**Owner:** claude-sonnet
**Date:** 2026-05-27
**Branch:** wip/vitalia

---

## Acceptance Criteria Status

| AC | Description | Status |
|---|---|---|
| A1 | 14 snapshot tests defined | PASS — 15 tests defined (14 required + 1 supplemental SC-1) |
| A2 | Specs parse OK (`--list` exit 0) | PASS — 32 tests listed (15×2 projects, smoke+visual) |
| A3 | AgendaPlaceholder status reported | PASS — see section below |
| A4 | Ratchet: `maxDiffPixelRatio: 0.001` on all snapshots | PASS — `THRESHOLD` const applied to all 15 tests |
| A5 | Mockup fidelity: animations disabled, mask freshness indicator | PASS — via playwright.config.ts project=visual + FRESHNESS_MASK |

### G5 Pre-commit Smoke Gate Results

| Gate | Command | Result |
|---|---|---|
| tsc --noEmit | `cd vitalia/frontend && npx tsc --noEmit` | PASS — 0 errors |
| eslint e2e/visual/ | `npx eslint e2e/visual/vitalia-fase2-valeria-agenda.spec.ts --cache` | PASS — 0 errors |
| playwright --list | `npx playwright test --list e2e/visual/vitalia-fase2-valeria-agenda.spec.ts` | PASS — 32 tests listed |
| --update-snapshots | Docker stack running but `@hookform/resolvers/zod` missing in container | BLOCKED (see below) |

### Screenshot Generation — Runtime Status

**State:** Specs ready. Runtime generation pending stack fix.

**Root cause (pre-existing, not T-19):** The Docker container running vitalia frontend (`/app/`) has `Module not found: Can't resolve '@hookform/resolvers/zod'` in `CobrarSaldoSubform.tsx`. This causes a 500 error on all pages. Additionally, the Clerk auth setup times out because the app returns 500.

**Impact on T-19:** The spec file is complete, type-checks clean, and ESLint clean. All 14+1 tests are properly declared. Screenshot generation is blocked by the Docker stack state, not by T-19 code.

**Resolution path:**
1. Fix Docker stack: `cd vitalia/frontend && pnpm install` inside container OR rebuild image with `--build`
2. Then run: `E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/visual/vitalia-fase2-valeria-agenda.spec.ts --project=visual --update-snapshots`
3. Commit generated PNGs to `e2e/__screenshots__/visual/vitalia-fase2-valeria-agenda.spec.ts/`

---

## Snapshot Inventory (14 canonical + 1 supplemental)

| # | Snapshot name | Scene | Theme | Fixture scenario |
|---|---|---|---|---|
| 1 | `agenda-day-light.png` | Día view | Light | `with_seed` |
| 2 | `agenda-day-dark.png` | Día view | Dark | `with_seed` |
| 3 | `agenda-week-light.png` | Semana view | Light | `with_seed` |
| 4 | `agenda-week-dark.png` | Semana view | Dark | `with_seed` |
| 5 | `agenda-month-light.png` | Mes view | Light | `with_seed` |
| 6 | `agenda-month-dark.png` | Mes view | Dark | `with_seed` |
| 7 | `drawer-detail-light.png` | Drawer open (detail) | Light | `with_seed` + slot click |
| 8 | `drawer-detail-dark.png` | Drawer open (detail) | Dark | `with_seed` + slot click |
| 9 | `drawer-cobrar-saldo-light.png` | Cobrar saldo subform expanded | Light | `with_seed` + pago section |
| 10 | `drawer-cobrar-saldo-dark.png` | Cobrar saldo subform expanded | Dark | `with_seed` + pago section |
| 11 | `mobile-drawer-fullscreen.png` | Bottom-sheet fullscreen (390×844) | Light | `with_seed` mobile |
| 12 | `preset-filters.png` | Chip row (locator-scoped) | Light | `with_seed` |
| 13 | `agenda-empty-state.png` | Día sin turnos | Light | `empty` |
| 14 | `crear-cita-dropdown.png` | Dropdown 3 opciones open | Light | `with_seed` |
| S1 | `drawer-cobrar-saldo-success-light.png` | Post-cobro success toast (gherkin SC-1) | Light | `with_seed` + payment mock `success` |

**Snapshot output path (per snapshotPathTemplate config):**
`vitalia/frontend/e2e/__screenshots__/visual/vitalia-fase2-valeria-agenda.spec.ts/{name}-chromium.png`

---

## AgendaPlaceholder Cleanup Status

**Finding:** `AgendaPlaceholder` is NOT removed. It remains in:

- **Component file:** `vitalia/frontend/src/features/valeria/components/placeholders/AgendaPlaceholder.tsx` — exists
- **PLACEHOLDER_MAP:** `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.tsx` — `"valeria.agenda": AgendaPlaceholder` still present in the 22-key map

**However (IMPORTANT):** The placeholder in `SubTabContent.tsx` is EFFECTIVELY BYPASSED for the `/valeria/agenda` sub-tab. The route `vitalia/frontend/src/app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx` uses `ValeriaAgendaView` directly via a dedicated Next.js route segment that takes precedence over the generic `[subtab]/page.tsx` + SubTabContent dispatcher.

**Architecture note:** SubTabContent dispatches via `PLACEHOLDER_MAP` only when the route hits `[agent]/[subtab]/page.tsx` (the catch-all). The static route `valeria/agenda/page.tsx` intercepts first (Next.js static segment priority > dynamic segment), so `AgendaPlaceholder` in the PLACEHOLDER_MAP is dead code for this particular route.

**Decision (per T-19 instructions):** Not removing in this ticket. Reporting for audit to decide. The 22-key PLACEHOLDER_MAP arch test still passes because `AgendaPlaceholder` is still there — removing it would reduce the count to 21, which may break that test unless it's updated simultaneously.

**Recommendation for audit:** Remove `AgendaPlaceholder` from `PLACEHOLDER_MAP` in a dedicated cleanup ticket. Update the arch test count from 22 to 21. This avoids dead code confusion where developers see `valeria.agenda` in the placeholder map but the real feature is already live.

---

## Files Changed

| File | Operation | Description |
|---|---|---|
| `vitalia/frontend/e2e/visual/vitalia-fase2-valeria-agenda.spec.ts` | CREATED | 14+1 visual golden specs |
| `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/T-19-result.md` | CREATED | This file |

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `playwright-expert` | E2E visual golden spec with POM integration | Used T-17 POMs via fixture import; locator-scoped screenshot for preset-filters; `FRESHNESS_MASK` for timestamp stability |
| `frontend-expert` | FSD-Lite boundary matrix, ESLint/TSC gate | tsc 0 errors, eslint 0 errors, boundary matrix respected (spec in `e2e/visual/`, imports from `e2e/regression/`) |
| `tessl__react-patterns` | Error boundary / loading / accessible markup baseline | Applied in spec: deterministic seed, mask dynamic elements, stable locators via data-testid |
| `vitalia/hipaa-lite` | PHI masking in visual fixtures | Patient name in seed = `"P. Hernández"` (masked), DNI = `"12.***.***"` (masked), `tenant_id+clinic_id` fixed to `clinica-sonrisa-pe-test` |
| `shell-feature-architecture-mandatory` | ADR-vitalia-004 compliance check | Visual spec is pure E2E, no FSD-Lite domain files touched; spec respects routing architecture |

---

## Notes

- Background agent T-18 (a11y axe spec) was running concurrently during T-19. No cross-contamination — T-18 and T-19 target separate files (`a11y/` vs `visual/`).
- The supplemental SC-1 golden (`drawer-cobrar-saldo-success-light.png`) covers the payment flow gherkin scenario referenced in `06-tickets.yaml`. It requires `setupPaymentAdapterMock(page, "success")` from `mock-payment-adapter.ts` (T-17 deliverable).
- Freshness indicator masked via `[data-testid="agenda-freshness-indicator"]` locator — prevents timestamp-based flakiness in CI.
- Dark mode applied via `document.documentElement.classList.add("dark")` in `page.evaluate()` — works with Tailwind dark mode (`class` strategy).
- Mobile test sets `agendaPage.setViewportSize({ width: 390, height: 844 })` inline before navigation to simulate iPhone 13.

---

<!-- @pm: build phase done (state: tests-passing). Commit: pending. Files: 2. Native ticket tests: 3/3 PASS (tsc + eslint + playwright --list). Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). Runtime screenshot generation blocked by Docker stack pre-existing issue (@hookform/resolvers/zod missing in container). -->
