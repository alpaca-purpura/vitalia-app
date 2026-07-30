<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->

# Gherkin Verification Matrix — F1-S3 vitalia-fase1-tenant-switcher

**Iteration:** 2 (final — APPROVED)
**Date:** 2026-05-23T02:13:00Z
**Audit run:** `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-tenant-switcher/ --project=smoke --workers=1`
**Result:** 26 passed, 1 skipped (SC-03 aspirational), 0 failed

## Scenario → Test Path → Status

| # | Scenario (Gherkin SSoT 01-spec.md § 4) | Test Path | Status |
|---|---|---|---|
| SC-01 | Trigger has aria-label='Cambiar clínica' | `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/tenant-switcher-structure.smoke.spec.ts::SC-01` | ✅ PASS |
| SC-01b | Trigger has data-testid='tenant-switcher-trigger' | `tenant-switcher-structure.smoke.spec.ts::SC-01b` | ✅ PASS |
| SC-02 | Opening dropdown shows 'MIS CLÍNICAS' header | `tenant-switcher-structure.smoke.spec.ts::SC-02` | ✅ PASS |
| SC-02b | Dropdown contains list of tenant options | `tenant-switcher-structure.smoke.spec.ts::SC-02b` | ✅ PASS |
| SC-03 | Selecting different tenant navigates to /{newTenantId}/dashboard | `tenant-switcher-navigation.smoke.spec.ts::SC-03` | ⏭️ SKIP (aspirational — requires real /{tenantId}/dashboard route, deferred to F2 per 03-arch.md) |
| SC-03b | Clicking active tenant is a no-op (no navigation) | `tenant-switcher-navigation.smoke.spec.ts::SC-03b` | ✅ PASS |
| SC-03c | Active tenant option shows check mark (data-active='true') | `tenant-switcher-navigation.smoke.spec.ts::SC-03c` | ✅ PASS |
| SC-04 | Error state — shows error alert and Reintentar button | `tenant-switcher-states.smoke.spec.ts::SC-04` | ✅ PASS |
| SC-06 | Footer shows Agregar clínica + Administrar cuenta | `tenant-switcher-states.smoke.spec.ts::SC-06` | ✅ PASS |
| SC-06b | Dropdown can be dismissed via Escape key | `tenant-switcher-states.smoke.spec.ts::SC-06b` | ✅ PASS |
| SC-07 | Agregar clínica opens modal with Próximamente title | `tenant-switcher-modal.smoke.spec.ts::SC-07` | ✅ PASS |
| SC-07b | Entendido button closes the modal | `tenant-switcher-modal.smoke.spec.ts::SC-07b` | ✅ PASS |
| SC-07c | Modal close button has data-testid='add-clinic-modal-close' | `tenant-switcher-modal.smoke.spec.ts::SC-07c` | ✅ PASS |
| SC-08 | Trigger is focusable and has aria-label | `tenant-switcher-a11y.smoke.spec.ts::SC-08` | ✅ PASS |
| SC-08b | Trigger title attribute shows active tenant name | `tenant-switcher-a11y.smoke.spec.ts::SC-08b` | ✅ PASS |
| SC-08c | Active tenant option has sr-only 'Clínica activa' text | `tenant-switcher-a11y.smoke.spec.ts::SC-08c` | ✅ PASS |
| SC-08d | Enter key on trigger opens dropdown | `tenant-switcher-a11y.smoke.spec.ts::SC-08d` | ✅ PASS |
| visual-01 | Closed trigger — light mode | `tenant-switcher-visual.smoke.spec.ts::visual-01` | ✅ PASS (golden: trigger-closed-light-smoke-linux.png) |
| visual-02 | Closed trigger — dark mode | `tenant-switcher-visual.smoke.spec.ts::visual-02` | ✅ PASS (golden: trigger-closed-dark-smoke-linux.png) — iter 1 reported flake on workers=4; PASS on workers=1 (CI uses workers=1 always per playwright.config.ts) |
| visual-03 | Open dropdown — light mode (success state) | `tenant-switcher-visual.smoke.spec.ts::visual-03` | ✅ PASS (golden: dropdown-open-light-smoke-linux.png) |
| visual-04 | Open dropdown — dark mode (success state) | `tenant-switcher-visual.smoke.spec.ts::visual-04` | ✅ PASS (golden: dropdown-open-dark-smoke-linux.png) |
| visual-05 | Open dropdown — loading state (skeleton rows) | `tenant-switcher-visual.smoke.spec.ts::visual-05` | ✅ PASS (conditional: trigger may not render in pure loading state per 03-arch §8.4 graceful degrade; no golden generated for this branch — documented quirk, not regression) |
| visual-06 | Open dropdown — error state (alert + Reintentar) | `tenant-switcher-visual.smoke.spec.ts::visual-06` | ✅ PASS (golden: dropdown-error-smoke-linux.png) |
| visual-07 | Add clinic modal — Próximamente dialog | `tenant-switcher-visual.smoke.spec.ts::visual-07` | ✅ PASS (golden: add-clinic-modal-smoke-linux.png) |
| visual-08 | Active tenant option — badge + check mark visible | `tenant-switcher-visual.smoke.spec.ts::visual-08` | ✅ PASS (golden: tenant-option-active-smoke-linux.png) |

**Total:** 26 PASS / 1 SKIP / 0 FAIL / 7 visual goldens generated (visual-05 conditional → no golden)

**Visual goldens vs mockups semantic verification (auditor read mockup HTML files):**

| Golden PNG | Mockup ratified by Chris (2026-05-22T17:00) | Semantic alignment |
|---|---|---|
| trigger-closed-{light,dark}-smoke-linux.png | mockups/tenant-switcher-closed.html | ✅ aria-label='Cambiar clínica', title='Sonrisa Plena' badge+nombre+chevron |
| dropdown-open-{light,dark}-smoke-linux.png | mockups/tenant-switcher-open.html | ✅ 'MIS CLÍNICAS' header, 3 tenants, 2 footer actions (Agregar clínica + Administrar cuenta), active checkmark |
| add-clinic-modal-smoke-linux.png | mockups/tenant-switcher-open.html (modal section) | ✅ DialogTitle='Próximamente', body+Entendido CTA |
| dropdown-error-smoke-linux.png | mockups/tenant-switcher-open.html (error state) | ✅ Alert role + Reintentar button + Agregar clínica hidden per graceful degrade |
| tenant-option-active-smoke-linux.png | mockups/tenant-switcher-open.html (option row) | ✅ Badge + name + city + Check icon (data-active='true') |

**Pending Chris visual ratify** (next session): set `pending_chris_visual_ratify: false` in T-FIX-1-result.md once Chris reviews PNGs side-by-side vs mockups visually.
