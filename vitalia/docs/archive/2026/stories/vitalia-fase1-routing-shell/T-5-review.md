<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-5 Legacy cleanup (dashboard + app + capabilities)

**Date:** 2026-05-26
**Brand:** vitalia
**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-5 — DELETE `(dashboard)/`+`(app)/`+`features/dashboard/`+5 fidelizacion E2E+`welcome-state.yaml` · MODIFY 4 legacy E2E specs+6 capability YAMLs
**Commit:** fcd1b3e4
**Files Reviewed:** ~30 deletions + 10 modifications (E2E + capability YAMLs)
**Domains touched:** Legacy cleanup (FE app dirs + E2E + capabilities) + brand-docs-schema R1+R2+R3
**Skills consulted:** frontend-expert · brand-docs-schema.md · anti-duplication.md · frontend-fsd.md · tdd-mandatory.md
**Live-verified:** N/A (deletion ticket — verification via arch test + capability reconcile)
**Verdict:** **APPROVED**

---

## /test-vitalia Gate Status (from gate-output.json iter 1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors |
| ESLint | PASS | 0 errors |
| Vitest | PASS | 148 files · 1549 tests · coverage 82.56%/91.76%/67.75%/82.56% |
| Arch fitness | PASS | `test-no-dashboard-route-group.test.ts` NOW GREEN 3/3 (was RED post T-4 by design) |

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | features/dashboard deleted (zero consumers verified per T-5-result.md) |
| 2 | Server/Client correctness | PASS | N/A — only deletions |
| 3 | React patterns | N/A | Deletion ticket |
| 4 | Code quality | PASS | tsc/eslint clean post-delete; tsconfig.json updated removing stale `.next/dev/types/**/*.ts` include |
| 5 | Accessibility | N/A | Deletion |
| 6 | Forms | N/A | — |
| 7 | Multitenancy | PASS | No new code affecting tenancy |
| 8 | Master Data | N/A | — |
| 9 | Security / Deps | PASS | No new deps |
| 10 | Tests / TDD | PASS | E2E specs refactored (4 MODIFY removed dashboard refs); 6 fidelizacion E2E DELETED (legacy); arch ratchet now enforces deletion |
| 11 | Domain Alignment | PASS | Capability YAMLs correctly modified per Q9 (1 DELETE + 6 MODIFY + 1 KEEP) |
| 12 | Arch Fitness | PASS | `test-no-dashboard-route-group.test.ts` GREEN ✅ |
| 13 | Mirror detection | N/A | Deletion only |
| 14 | Decisions honored (R6) | N/A | Ticket has no `decisions_applicable` field |

---

## Findings (verbatim verification checklist)

### PASS · Q9 capability YAMLs (1 DELETE + 6 MODIFY + 1 KEEP)

**Verified via filesystem scan:**
```bash
$ ls vitalia/docs/product/capabilities/dashboard/ 2>/dev/null
(empty — directory does not exist)
```
✅ `welcome-state.yaml` DELETED.

**6 capability YAMLs MODIFIED — all have `fe_planned_phase2` field:**
| File | fe_planned_phase2 target | status |
|---|---|---|
| `booking/prepaid-booking-advisory-locks.yaml` | `vitalia-fase2-valeria-agenda` | live ✅ |
| `compliance/compliance-hipaa-lite-audit.yaml` | `vitalia-fase2-lisa-compliance` | live ✅ |
| `brand_studio/brand-studio-medical-sections.yaml` | `vitalia-fase2-lisa-marca` | live ✅ |
| `offer_studio/medical-services-offer-preset.yaml` | `vitalia-fase2-lisa-servicios` | live ✅ |
| `patients/patient-records-medical-history.yaml` | `vitalia-fase2-valeria-pacientes` | live ✅ |
| `treatments/treatment-followup-workflow.yaml` | `vitalia-fase2-valeria-pacientes` | live ✅ |

All `status: live` preserved (BE alive). `package_path` updated to strip legacy FE path.

**1 KEEP verified:**
- `platform/shell-foundation-shadcn-tailwind-v4.yaml` — `status: live`, NO `fe_planned_phase2` field (untouched). ✅

### PASS · Filesystem cleanup verified

```bash
$ find vitalia/frontend/src/app -path "*\(dashboard\)*"
(empty)
$ find vitalia/frontend/src/app -path "*\(app\)*"
(empty)
$ find vitalia/frontend/src/features/dashboard
(empty)
```
All deletions correctly executed.

### PASS · E2E suite cleanup

**Deleted (git rm) — 6 fidelizacion E2E files:**
- `e2e/pages/fidelizacion.page.ts` ✅
- `e2e/specs/regression/fidelizacion-follow-up-doctor-vencido.spec.ts` ✅
- `e2e/specs/regression/fidelizacion-adversarial.spec.ts` ✅
- `e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts` ✅
- `e2e/specs/regression/fidelizacion-absence-no-optin.spec.ts` ✅
- `e2e/specs/smoke/fidelizacion.smoke.spec.ts` ✅

**Modified — 4 legacy E2E specs (stripped dashboard auth blocks):**
- `e2e/visual/visual-smoke.spec.ts` (removed SC-16 authenticated block)
- `e2e/visual/stack-stability/dev-stack-baseline.spec.ts` (removed dashboard-legacy block)
- `e2e/mobile/mobile-smoke.spec.ts` (removed SC-15 authenticated block)
- `e2e/a11y/a11y-smoke.spec.ts` (removed authenticated block, kept public-page axe scans)

### PASS · Brand-docs-schema R1+R2+R3 compliance

- **R1** (no MDs sueltos in `vitalia/docs/` root): N/A this ticket; capability YAMLs live in proper sub-dirs.
- **R2** (stories done → archive): N/A this ticket (story still `reviewing`, not yet `done`).
- **R3** (auto-gen files): no manual edits to BACKLOG / modules.md / portfolio. `reconcile_capabilities.py --check-mode` passed per T-5-result.md.

### PASS · Arch ratchet GREEN
`test-no-dashboard-route-group.test.ts` 3/3 GREEN:
- `app/(dashboard)/ MUST NOT exist` ✅
- `app/(app)/ MUST NOT exist` ✅
- `app/[tenantId]/(shell-organism)/ MUST exist` ✅

### PASS · tsconfig.json cleanup
Removed stale `.next/dev/types/**/*.ts` include (Turbopack dev artifact, not standard Next.js type path). Stale config removed pre-cleanup — preventive hygiene.

---

## Contract / UI-SPEC Compliance

- [x] AC-13 `(dashboard)/`+`(app)/` eliminados completos · 5 specs E2E legacy eliminados/refactorizados ✅
- [x] AC-14 `welcome-state.yaml` eliminado + 6 capability YAMLs modificados (path BE-only + `fe_planned_phase2`) + `platform/shell-foundation` intacto ✅

---

## Allowlist Movement
- [x] Allowlist shrunk (post-deletion arch test now GREEN where it was intentionally RED at T-4).
- [x] No warning baseline growth.

## Native-First Audit
- [x] No `docker exec`, no `make e2e`, no `git add .`/-A/-u.

## Skills Consulted (must_load enforcement v4.1)
- ✅ `frontend-expert` — features/dashboard deletion consumer verification
- ✅ `brand-docs-schema.md` — R1+R2+R3 compliance (auto-gen guardrails, capability YAMLs)
- ✅ `anti-duplication.md` — features/dashboard zero-consumer pre-delete grep
- ✅ `frontend-fsd.md` — boundary check post-delete
- ✅ `tdd-mandatory.md` — arch ratchet RED→GREEN cycle (T-4 RED → T-5 GREEN)

## Verdict Math
- ✅ No FAIL in cat 1/2/3/7/11/12/14
- ✅ No allowlist or warning baseline growth
- ✅ All deletions verified filesystem + capability YAMLs verified via grep
- ✅ Arch ratchet GREEN
- → **APPROVED**

---

<!-- @pm: REVIEW.md ready (verdict=APPROVED). Brand: vitalia. Cross-brand flags: 0. Engine-edit flags: 0. Live-verified: N/A (deletion ticket). -->
