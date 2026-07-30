# T-5 Implementation Log — Legacy Route Group Cleanup

**Story:** vitalia-fase1-routing-shell  
**Ticket:** T-5 — Delete legacy (dashboard)/ + (app)/ + fidelizacion E2E + capability YAMLs cleanup  
**Branch:** wip/vitalia  
**Date:** 2026-05-25  

---

## Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix + arch ratchet patterns | Confirmed: `rm -rf` for app dirs; `git rm` for tracked files; tsconfig.json cleanup |
| `tessl__react-patterns` | Not applicable — no new components (pure deletion ticket) | N/A |
| `tessl__nextjs-app-router-modularization` | Verifying Server/Client boundary for deleted route groups | Confirmed: all deleted pages were Server Components with Client sub-components |

---

## Step 0 — Skill invocation gate

Declared skills: `frontend-expert` (always), `tessl__react-patterns` (always). Domain skills not needed (no new FE code — pure deletion ticket).

---

## Step 1 — Consumer verification (features/dashboard/)

```bash
grep -rln "from .*features/dashboard" vitalia/frontend/src/
```

Result: zero consumers outside `(dashboard)/page.tsx` itself. Safe to delete.

---

## Step 2 — Deletions executed

### App route groups deleted

- `rm -rf vitalia/frontend/src/app/(dashboard)/` — 17+ files including layout.tsx, page.tsx, offers/*, bookings/*, appointments/*, brand-studio/*, fidelizacion/, medical-compliance/, patients/*, treatments/*
- `rm -rf vitalia/frontend/src/app/(app)/` — inbox sub-route (3 files)
- `rm -rf vitalia/frontend/src/features/dashboard/` — zero consumers verified

### E2E files git rm'd

- `vitalia/frontend/e2e/pages/fidelizacion.page.ts`
- `vitalia/frontend/e2e/specs/regression/fidelizacion-follow-up-doctor-vencido.spec.ts`
- `vitalia/frontend/e2e/specs/regression/fidelizacion-adversarial.spec.ts`
- `vitalia/frontend/e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts`
- `vitalia/frontend/e2e/specs/regression/fidelizacion-absence-no-optin.spec.ts`
- `vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts`

### Capability YAML deleted

- `vitalia/docs/product/capabilities/dashboard/welcome-state.yaml`

---

## Step 3 — E2E spec modifications

4 specs modified to remove `(dashboard)` authenticated test blocks:

| File | Change |
|---|---|
| `e2e/visual/visual-smoke.spec.ts` | Removed `authTest.describe("SC-16 — Visual baseline dashboard autenticado...")` block + import |
| `e2e/visual/stack-stability/dev-stack-baseline.spec.ts` | Removed "dashboard legacy regression" describe block (2 tests); kept shadcn primitives + agent tokens swatch |
| `e2e/mobile/mobile-smoke.spec.ts` | Removed `authTest.describe("SC-15 — Mobile smoke dashboard autenticado...")` block + import |
| `e2e/a11y/a11y-smoke.spec.ts` | Removed authenticated dashboard block + unused authTest import; kept AxeBuilder (still used for public pages) |

All 4 specs now cover only public pages (`/sign-in`, `/sign-up`, `/onboarding/wizard`). Authenticated coverage lives in `e2e/regression/vitalia-fase1-routing-shell/`.

---

## Step 4 — Capability YAML modifications

6 YAMLs modified — `(dashboard)` FE path stripped, `fe_planned_phase2` added:

| YAML | package_path change | fe_planned_phase2 |
|---|---|---|
| `booking/prepaid-booking-advisory-locks.yaml` | Removed `+ vitalia/frontend/src/app/(dashboard)/*` | `vitalia-fase2-valeria-agenda` |
| `compliance/compliance-hipaa-lite-audit.yaml` | Removed `+ vitalia/frontend/src/app/(dashboard)/medical-compliance` | `vitalia-fase2-lisa-compliance` |
| `brand_studio/brand-studio-medical-sections.yaml` | Changed from `vitalia/frontend/src/app/(dashboard)/brand-studio` to `vitalia/config/brand.yaml + vitalia/backend/src/modules/vitalia/brand/extensions.py` | `vitalia-fase2-lisa-marca` |
| `offer_studio/medical-services-offer-preset.yaml` | Changed from `vitalia/frontend/src/app/(dashboard)/offers` to `vitalia/config/brand.yaml + vitalia/backend/src/modules/vitalia/offer/extensions.py` | `vitalia-fase2-lisa-servicios` |
| `patients/patient-records-medical-history.yaml` | Removed `+ vitalia/frontend/src/app/(dashboard)/patients` | `vitalia-fase2-valeria-pacientes` |
| `treatments/treatment-followup-workflow.yaml` | Removed `+ vitalia/frontend/src/app/(dashboard)/treatments` | `vitalia-fase2-valeria-pacientes` |

`status: live` preserved in all 6 (BE modules intact).
`platform/shell-foundation-shadcn-tailwind-v4.yaml` untouched (KEEP INTACT).

---

## Step 5 — tsconfig.json fix

**Problem:** `.next/dev/types/validator.ts` (stale, root-owned) referenced deleted page routes → TSC errors.

**Fix:** Removed `.next/dev/types/**/*.ts` from `tsconfig.json` `include` array. This is the correct config: `.next/dev/types/` is a Turbopack dev-mode artifact, not a standard Next.js type declaration path. The standard path `.next/types/**/*.ts` (kept) covers production type validation.

---

## Step 6 — Quality gate results

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/ --cache` | 0 errors |
| `vitest run --coverage` | 148 test files, 1549 tests — ALL PASSED |
| Coverage: Statements | 82.56% (≥20% threshold) |
| Coverage: Branches | 91.76% (≥20% threshold) |
| Coverage: Functions | 67.75% (≥20% threshold) |
| Coverage: Lines | 82.56% (≥20% threshold) |
| Arch test `test-no-dashboard-route-group.test.ts` | 3/3 GREEN (was RED before T-5) |

---

## Step 7 — Verification greps (final state)

```
find vitalia/frontend/src/app -path '*(dashboard)*'  → EMPTY ✓
find vitalia/frontend/src/app -path '*(app)*'        → EMPTY ✓
welcome-state.yaml                                   → DELETED ✓
fe_planned_phase2 in all 6 YAMLs                    → PRESENT (6/6) ✓
platform/shell-foundation yaml                       → INTACT ✓
(dashboard) in E2E specs                             → COMMENTS ONLY ✓
```

---

## Anti-patterns verified NOT done

- No BE modules touched (bookings/compliance/patients/treatments backends intact)
- `status: live` not changed in any YAML
- `platform/shell-foundation-shadcn-tailwind-v4.yaml` not deleted
- No voseo added
- No inline `style={{}}` (no new components)
- No `git add .` / `-A` / `-u`

---

## Live verification

`chrome-devtools-verify` not invoked — this is a pure deletion ticket with no new UI surface. No user-facing components added. The authenticated shell coverage lives in `e2e/regression/vitalia-fase1-routing-shell/` (T-3 and T-4 work). Escalate to Chris staging gate per protocol.
