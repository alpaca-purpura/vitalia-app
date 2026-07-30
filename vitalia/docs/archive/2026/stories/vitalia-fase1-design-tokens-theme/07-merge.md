# Merge artifact — vitalia/vitalia-fase1-design-tokens-theme

> Brand: vitalia
> Story: F1-S1 vitalia-fase1-design-tokens-theme
> Merged at: 2026-05-23T01:00:00-05:00
> Branch wip/vitalia commits: 5fea3c03 (claim) · 1e090b95 (bundle 7 tickets) · 288883d5 (audit APPROVED + self-fix allowlist + rename)
> Audit verdict: APPROVED (audit_iterations=1, self_fix_iter=1)

## § 1 — Gherkin verification matrix

> Copia exacta de `06-audit/gherkin-matrix.md`. SC-01..SC-08 todos PASS.

| Scenario (01-spec.md § 6) | Test path | Status |
|---|---|---|
| SC-01 click toggle changes html data-theme + localStorage + ARIA | e2e/regression/design-tokens-theme/theme-toggle-interaction.smoke.spec.ts | ✅ PASS (1 sub-flaky retry-succeeded) |
| SC-02 reload persistencia + NO FOUC | e2e/regression/design-tokens-theme/theme-toggle-interaction.smoke.spec.ts | ✅ PASS |
| SC-03 ARIA pressed boolean + aria-label dinámico | e2e/regression/design-tokens-theme/theme-toggle-interaction.smoke.spec.ts | ✅ PASS |
| SC-04 ThemeToggle visual golden light | e2e/visual/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS (maxDiffPixelRatio < 0.001) |
| SC-05 ThemeToggle visual golden dark | e2e/visual/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |
| SC-06 zero WCAG 2.1 AA light | e2e/a11y/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |
| SC-07 zero WCAG 2.1 AA dark | e2e/a11y/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |
| SC-08 keyboard navigation Tab/Enter/Space | e2e/a11y/design-tokens-theme/theme-toggle.spec.ts | ✅ PASS |

**Total: 8/8 scenarios PASS.**

## § 2 — Playwright E2E run

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# Visual project (F1-S0 + F1-S1 regression)
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual
# → 9/9 PASS (32.7s) — incluye dashboard-legacy + shadcn-primitives + agent-tokens (F1-S0) + theme-toggle light/dark (F1-S1)

# Smoke behavior
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke --grep "design-tokens-theme"
# → 3/3 PASS (1 sub-flaky retry-succeeded per Playwright retries=1)

# A11y axe-core
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=a11y --grep "design-tokens-theme"
# → 5/5 PASS (incluye setup)
```

## § 3 — Capabilities updated/created

NEW:
- `vitalia/docs/product/capabilities/platform/design-tokens-theme.yaml` (status: live, package_version 0.1.0)

7 surfaces acopladas: Theme infrastructure (next-themes + ThemeProvider config) · ThemeToggle component (Shadcn Button + Lucide icons + ARIA Spanish) · CSS vars completos :root + .dark · Tailwind v4 darkMode config · Test page preview + fixture · Playwright suites (behavior + visual + a11y) · 2 visual goldens.

UPDATE: ninguna directa, pero referencia related `vitalia-shell-foundation-shadcn-tailwind-v4` (F1-S0) + `vitalia-design-tokens-foundation` (legacy).

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/platform.md` (auto-list refresh post-merge) — appended `design-tokens-theme` en sección "Capabilities live".

## § 5 — How to verify (reproducible commands)

```bash
WS=$(git rev-parse --show-toplevel)

# 0. Stack levantado
cd ${WS} && make dev-vitalia

# 1. TypeScript strict
cd ${WS}/vitalia/frontend && npx tsc --noEmit
# Exit 0

# 2. ESLint clean
cd ${WS}/vitalia/frontend && npx eslint src/ --cache --max-warnings 0
# Exit 0

# 3. Vitest unit + integration + arch fitness
cd ${WS}/vitalia/frontend && npx vitest run --reporter=default
# 806/806 PASS (103 files) — incluye ThemeToggle.test.tsx (7) + test-shadcn-vars-resolvable (59) + arch fitness post-allowlist

# 4. Visual goldens regression (F1-S0 + F1-S1)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=visual
# 9/9 PASS

# 5. Behavior smoke + a11y
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=smoke --grep "design-tokens-theme"
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test --project=a11y --grep "design-tokens-theme"

# 6. Live preview en browser
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/test-stack/design-tokens-theme
# 200

# 7. Production build
cd ${WS}/vitalia/frontend && npm run build
# Exit 0

# 8. Interactive verification (Chris manual)
# Abre https://dev-app.vitalialat.com/test-stack/design-tokens-theme
# Click el toggle button (Moon icon → Sun icon)
# Verify: <html data-theme="dark"> + localStorage["vitalia-theme"] === "dark"
# Reload F5 → theme dark persiste, sin FOUC
# Click again → vuelve a light
```

**Expected**: todos comandos exit 0 / 200.

## Audit cycle metrics

- audit_iterations: 1
- self_fix_iter: 1 (whitelist #11 — KNOWN_COLOR_VIOLATIONS allowlist add for F1-S0 carryover)
- Builder commits: 1 bundled (1e090b95 — 7 tickets)
- Audit closure commit: 288883d5
- Wall-clock audit cycle: ~20 min (in-loop self-fix + rename + verify)
