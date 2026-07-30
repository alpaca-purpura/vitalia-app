# T-5 Result — Legacy Route Group Cleanup

**Story:** vitalia-fase1-routing-shell  
**Ticket:** T-5  
**Status:** DONE — gates GREEN  
**Branch:** wip/vitalia  
**Date:** 2026-05-25  

---

## Summary

T-5 deleted all legacy `(dashboard)/` and `(app)/` route groups from `vitalia/frontend/src/app/`, cleaned up fidelizacion E2E files, removed the welcome-state capability YAML, updated 4 E2E specs to remove authenticated dashboard blocks, and stripped legacy FE paths from 6 capability YAMLs (adding `fe_planned_phase2` to each).

---

## Acceptance criteria

| AC | Status |
|---|---|
| `app/(dashboard)/` MUST NOT exist | PASS — directory deleted |
| `app/(app)/` MUST NOT exist | PASS — directory deleted |
| `features/dashboard/` deleted if zero consumers | PASS — zero consumers confirmed, deleted |
| Arch test `arch-no-dashboard-route-group` GREEN | PASS — 3/3 tests pass |
| 6 fidelizacion E2E files deleted | PASS |
| 4 E2E specs refactored (no auth dashboard refs) | PASS |
| `welcome-state.yaml` deleted | PASS |
| 6 capability YAMLs updated with `fe_planned_phase2` | PASS — all 6 have field |
| `status: live` preserved in all modified YAMLs | PASS |
| `platform/shell-foundation` YAML intact | PASS |
| TSC 0 errors | PASS |
| ESLint 0 errors | PASS |
| Vitest 148 files / 1549 tests all passed | PASS |
| Coverage ≥20% all categories | PASS (82.56%/91.76%/67.75%/82.56%) |

---

## Files changed

### Deleted (app routes)
- `vitalia/frontend/src/app/(dashboard)/` — entire directory (~17 files)
- `vitalia/frontend/src/app/(app)/` — entire directory (~3 files)
- `vitalia/frontend/src/features/dashboard/` — entire directory (zero consumers)

### Deleted (E2E — git rm)
- `e2e/pages/fidelizacion.page.ts`
- `e2e/specs/regression/fidelizacion-follow-up-doctor-vencido.spec.ts`
- `e2e/specs/regression/fidelizacion-adversarial.spec.ts`
- `e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts`
- `e2e/specs/regression/fidelizacion-absence-no-optin.spec.ts`
- `e2e/specs/smoke/fidelizacion.smoke.spec.ts`

### Deleted (capabilities)
- `vitalia/docs/product/capabilities/dashboard/welcome-state.yaml`

### Modified (E2E specs)
- `e2e/visual/visual-smoke.spec.ts` — removed SC-16 authenticated block
- `e2e/visual/stack-stability/dev-stack-baseline.spec.ts` — removed dashboard-legacy block
- `e2e/mobile/mobile-smoke.spec.ts` — removed SC-15 authenticated block
- `e2e/a11y/a11y-smoke.spec.ts` — removed authenticated block, kept public-page axe scans

### Modified (capability YAMLs)
- `capabilities/booking/prepaid-booking-advisory-locks.yaml`
- `capabilities/compliance/compliance-hipaa-lite-audit.yaml`
- `capabilities/brand_studio/brand-studio-medical-sections.yaml`
- `capabilities/offer_studio/medical-services-offer-preset.yaml`
- `capabilities/patients/patient-records-medical-history.yaml`
- `capabilities/treatments/treatment-followup-workflow.yaml`

### Modified (infra)
- `vitalia/frontend/tsconfig.json` — removed stale `.next/dev/types/**/*.ts` include (Turbopack dev artifact, not standard Next.js type path)

---

## Quality gates

```
tsc --noEmit        → 0 errors
eslint src/         → 0 errors
vitest run          → 148 files / 1549 tests PASS
coverage            → 82.56% stmts / 91.76% branch / 67.75% funcs / 82.56% lines
arch test T-4 RED   → NOW GREEN (3/3)
```
