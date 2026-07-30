# Gherkin verification matrix — vitalia/vitalia-fase1-topbar-global

> Auditor: /auditor (Conv 3 direct examination)
> Date: 2026-05-23
> State: developed → reviewing

## Phase D Matrix (per 01-spec.md § 6 + tests delivered T-7)

| Scenario | Mapped test | Status |
|---|---|---|
| SC-01 TopBar render altura 48px + LogoMark izq + ThemeToggle der | TopBarGlobal.test.tsx + e2e regression topbar-interaction.smoke.spec | ✅ PASS |
| SC-02 Skip link a11y Tab+Enter foco main-content | e2e a11y topbar-a11y.spec.ts (axe + keyboard) | ✅ PASS |
| SC-03 Mobile responsive viewport 375px sin overflow | e2e visual topbar-baseline.spec.ts topbar-mobile-{light,dark}.png | ✅ PASS |
| SC-04 Theme switch persists across TopBar bg+border | e2e regression topbar-interaction.smoke + visual dark goldens | ✅ PASS |
| SC-05 LogoMark 6 combinations (3 sizes × 2 variants) | LogoMark.test.tsx (9 tests covers full/mark × sm/md/lg) | ✅ PASS |
| SC-06 LogoMark dark variant swap (libélula+wordmark white) | e2e visual logo-mark-dark.png | ✅ PASS |
| SC-07 TenantSwitcherSlot returns null (placeholder for F1-S3) | TenantSwitcherSlot.test.tsx (3 tests) | ✅ PASS |
| SC-08-13 ARIA banner role + landmarks + axe WCAG | e2e a11y suite | ✅ PASS |

**Total: 13/13 scenarios PASS.**

## Verdict

ALL PASS. Builder delivered 8 tickets clean, 824/824 vitest, 43/43 arch fitness, tsc + eslint clean.

## Reproducibility

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

npx vitest run                                                              # 824/824
npx tsc --noEmit                                                            # 0 errors
npx eslint src/ --max-warnings 0                                            # 0 errors
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual     # 15/15 (F1-S0 6 + F1-S1 2 + F1-S2 7 + smoke baselines)
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke --grep topbar
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=a11y --grep topbar

curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/test-stack/topbar-global   # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/test-stack/logo-mark       # 200
```
