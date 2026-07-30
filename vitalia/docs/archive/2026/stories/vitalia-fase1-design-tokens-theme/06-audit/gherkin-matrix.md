# Gherkin verification matrix — vitalia/vitalia-fase1-design-tokens-theme

> Auditor: /auditor (Conv 3 review)
> Date: 2026-05-23
> Story state: developed → reviewing
> Branch: wip/vitalia

## Phase D Matrix

| Scenario (01-spec.md § 6) | Mapped test | Status |
|---|---|---|
| SC-01 click toggle changes html data-theme + localStorage + aria-state | e2e/regression/design-tokens-theme/theme-toggle-interaction.smoke.spec.ts | ✅ PASS (1 flaky retry-succeeded) |
| SC-02 reload persistencia + NO FOUC | e2e/regression/design-tokens-theme/theme-toggle-interaction.smoke.spec.ts | ✅ PASS |
| SC-03 ARIA pressed boolean + aria-label dinámico | e2e/regression/design-tokens-theme/theme-toggle-interaction.smoke.spec.ts | ✅ PASS |
| SC-04 ThemeToggle visual golden light | e2e/visual/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS (maxDiffPixelRatio < 0.001) |
| SC-05 ThemeToggle visual golden dark | e2e/visual/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |
| SC-06 zero WCAG 2.1 AA violations light mode | e2e/a11y/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |
| SC-07 zero WCAG 2.1 AA violations dark mode | e2e/a11y/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |
| SC-08 keyboard navigation Tab/Enter/Space | e2e/a11y/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |

## Summary

| Status | Count | Scenarios |
|---|---|---|
| ✅ PASS | 8 | SC-01..SC-08 |
| ⚠️ FLAKY | 1 (sub) | SC-01 retry-succeeded (race on first hydration before testing token applied) |
| ❌ FAIL | 0 | — |

## Phase D verdict

**ALL 8 SCENARIOS PASS** (1 sub-flaky retry-succeeded, acceptable per Playwright `retries: 1` config).

Visual goldens generados con stack 100% funcional (post F1-S0 Tailwind v4 + Shadcn + agent SSoT). Theme toggle persiste vía localStorage `vitalia-theme`. Hydration sin FOUC (suppressHydrationWarning + next-themes script inline).

## Reproducibility

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# Unit: ThemeToggle.test.tsx + test-shadcn-vars-resolvable.test.ts
npx vitest run

# Visual goldens
E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=visual --grep "design-tokens-theme"

# Behavior smoke (SC-01..SC-03)
E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=smoke --grep "design-tokens-theme"

# a11y (SC-06..SC-08)
E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=a11y --grep "design-tokens-theme"
```

## Caveat infra (no F1-S1 regression)

Playwright `smoke` project's `testMatch` includes `/e2e/visual/*.spec.ts/` glob (pre-existing pattern de F1-S0 era).
Esto provoca que el spec visual también se ejecute en smoke project, pero con viewport Desktop Chrome
default (~1280×720) en vez del configurado visual project (1440×900). Resultado: las goldens NO matchean
cuando smoke corre — falsa "fail" en smoke. El visual project siempre PASS (es el authoritative).

Fix recomendado follow-up story: ajustar smoke `testMatch` para excluir `/e2e/visual/` OR renombrar
visual specs con suffix `.visual.spec.ts` para que smoke regex no matchee. Fuera de scope F1-S1.
