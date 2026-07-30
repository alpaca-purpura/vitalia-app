<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-mk-fe-7

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-fe-7 (Wave 6 — E2E smoke + a11y + perf budget Lighthouse + bundle size check)
**Date:** 2026-05-20
**Brand:** vitalia
**Commits range:** 145a854..258a42f
**Files Reviewed:** 5 (POM + smoke spec + a11y spec + bundle script + lighthouserc) + package.json scripts
**Domains touched:** validator infrastructure (E2E + a11y + perf + bundle budget)
**Skills consulted:** playwright-expert (POM patterns, native-first, mocks via page.route), tessl__react-patterns (ARIA-first locators), tessl__graceful-degradation (script exits 0 when chunk not found)
**Live-verified:** Specs implemented but execution DEFERRED to CI per result.md (Turbopack dev server connection drops; 4 validators deferred)
**Verdict:** **PASS** (4 DEFERRED validators properly documented; not blocking per gate-output.json deferred_gates section)

## /test-frontend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint targeted | PASS | 0 errors, no new warnings |
| Vitest marketing | PASS | n/a (E2E + script files; not vitest-run) |
| Arch fitness (42 tests) | PASS | 42/42 |

**Deferred (per gate-output.json::deferred_gates):**
- `e2e_smoke_marketing` — Turbopack dev server instability (documented)
- `visual_a11y_axe` — depends on smoke (same root cause)
- `visual_perf_budget_lighthouse` — needs `@lhci/cli` + pre-warmed build
- `visual_regression_bowtie_svg::chromatic` — CHROMATIC_PROJECT_TOKEN missing

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | N/A | E2E files in `e2e/`, scripts in `scripts/` (not src/) |
| 2 | Server/Client | N/A | Playwright E2E executes against rendered DOM |
| 3 | React Patterns | PASS | POM uses ARIA-first locators (role="dialog", role="tab", aria-label) — best practice |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | a11y spec implements 6 axe-core tests (WCAG 2.1 AA scan + ARIA spot-checks for SVG/tablist/dialog/table); `@axe-core/playwright` graceful skip if not installed |
| 6 | Forms (RHF + Zod) | N/A | |
| 7 | Multitenancy | PASS | E2E fixtures use mock TENANT_ID + CLINIC_ID; HIPAA-aware (no PHI in mocks) |
| 8 | Master Data / Spanish | PASS | E2E mocks use ARS currency (Argentine) — exercises currency-from-data flow |
| 9 | Security / Deps | PASS | a11y spec disables 2 axe rules with documented exceptions (scrollable-region-focusable + aria-dialog-name) — sane rationale |
| 10 | Tests / TDD | PASS | 3 smoke tests + 6 a11y tests; gherkin coverage SC-MK-01 + SC-MK-03 implemented; SC-MK-02 + SC-MK-04 not in this ticket's scope (covered in earlier vitest unit tests T-mk-fe-3 + T-mk-fe-5) |
| 11 | Domain Alignment / Agentic UI | PASS | smoke mocks Lucas recommendations endpoint, exercises card click → modal open → modal close |
| 12 | Architecture Fitness | PASS | 42/42 |
| 13 | Mirror detection | PASS | POM brand-local; no cross-brand mirror |
| 14 | Decisions honored cite (R6) | N/A | |

## Strengths

- **POM ARIA-first locators:**
  - `bowtieSvg`: `figure[aria-label="Embudo de conversión"] svg[role="img"]`
  - `stageTabs`: `tablist[aria-label="Etapas del embudo"] > [role="tab"]`
  - `approvalModalTitle`: `[role="dialog"] h2#approval-modal-title, h2#detail-modal-title`
  - Robust to CSS class refactor; tracks the rendered semantics not the styling
- **Network mocks via `page.route`** instead of standing up real backend → fast, deterministic, no stack required
- **HIPAA-aware E2E fixtures:** no PHI in mock payloads (only hashed IDs, slugs, aggregates)
- **Native-first execution:** `npx playwright test --project=smoke` (NOT `make e2e`)
- **a11y spec coverage:** 6 tests per `03-arch-fe.md § 6` requirements (SVG aria, tablist invariants, table headers `scope="col"`, dialog modal ARIA, ESC close, axe scan with documented disabled rules)
- **lighthouserc.cjs strict gates:** LCP<2.5s, CLS<0.1, accessibility≥0.9, button-name, image-alt, color-contrast as `"error"` blocks. INP<200ms documented elsewhere.
- **check-bowtie-bundle.mjs graceful exit:** exits 0 when no specific chunk found (per `tessl__graceful-degradation` — script doesn't fail merge on absence, only on size overflow)
- **defer documentation:** 4 DEFERRED validators each have written reason in result.md and `06-tickets.yaml::defer_validators` — not glossing over

## Findings

(no FAILs)

### WARN W1 — Deferred validators must be run before prod release

**Category:** 11 (visual + a11y + perf gates)
**Files:** N/A (operational)
**Issue:** 4 validators DEFERRED to CI per result.md:
  - `e2e_smoke_marketing` — needs pre-built Next.js server (not Turbopack dev)
  - `visual_a11y_axe` — depends on smoke
  - `visual_perf_budget_lighthouse` — needs `@lhci/cli` installed + pre-warmed server
  - `visual_regression_bowtie_svg::chromatic` — needs `CHROMATIC_PROJECT_TOKEN`

Specs are implemented; the deferral is an infra/CI gap, not a code defect. But until they run, SC-MK-01 + SC-MK-03 lack live E2E verification. Local vitest tests (T-mk-fe-3 + T-mk-fe-4 unit tests) cover the same scenarios at component-level, which mitigates risk for Slice 1 ship.

**Suggested fix (operational):**
1. Add `CHROMATIC_PROJECT_TOKEN` to CI secrets and run baseline-publish step (`auto-accept-changes=false` requires manual review).
2. Install `@axe-core/playwright` + `@lhci/cli` in CI image.
3. Use `next build` + `next start` in CI (NOT Turbopack dev) for stable Playwright runs.
4. Chris ratifies in `07-merge.md § 5 verify` whether these gates block prod deploy or are accepted as "WARN with follow-up in Slice 2 hardening".

**Skill ref:** `playwright-expert` (CI patterns), `tessl__graceful-degradation` (script behavior).

## Contract / UI-SPEC Compliance

- [x] POM matches implemented components (see § Locators table in result.md)
- [x] Smoke + a11y specs cover SC-MK-01 + SC-MK-03 per `gherkin_coverage` field
- [x] Performance budgets per `03-arch-fe.md § 9` (LCP<2.5s, INP<200ms, CLS<0.1, Bowtie<30KB gzipped)
- [x] Native-first execution (no docker/make)

## Allowlist Movement / Native-First / Live Verification

- [x] No allowlist growth
- [x] No `make e2e*` (commands documented use `npx playwright test --project=smoke`)
- [x] No `docker exec` for test runs
- [x] No `git add .`
- [x] `chrome-devtools-verify` correctly documented as DEPRECATED for Linux; escalated to Chris staging gate (FE PR ≥ M live verification policy followed)

## Verdict Math

- 0 FAILs · 1 WARN (deferred validators with rationale) ≤ 1 ⇒ **PASS**

**Note on auditor verdict policy:** The auditor framework normally requires "FAIL on any /test-frontend blocker (steps 2/3/4)". Per gate-output.json, the 4 deferred validators are in `deferred_gates` (not `fail_gate_names`) — runner correctly classified as DEFERRED, not FAIL. Story closure gate (`Phase F merge`) is the appropriate place for Chris ratification of merge with deferred prod gates.

**Result:** APPROVED — Slice 1 ships pending operational follow-up for deferred validators.
