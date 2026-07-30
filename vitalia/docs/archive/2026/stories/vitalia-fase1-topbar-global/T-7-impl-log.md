# T-7 impl-log — fe-playwright-specs-3

**Story:** vitalia-fase1-topbar-global (F1-S2)
**Ticket:** T-7
**Date:** 2026-05-23
**Owner:** builder-frontend / Claude Sonnet 4.6

## Plan

Create 4 Playwright spec files covering regression + visual + a11y:

1. `e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts` — SC-01..SC-03 behavior
2. `e2e/visual/topbar-global/topbar.spec.ts` — SC-04..SC-05 visual goldens (2 goldens: light + dark desktop)
3. `e2e/visual/topbar-global/logo-mark.spec.ts` — SC-06..SC-09 visual goldens (4 goldens: grid light/dark + mobile light/dark)
4. `e2e/a11y/topbar-global/topbar.spec.ts` — SC-10..SC-13 a11y (axe + skip link + banner landmark)

Total: 6 visual goldens (from 03-arch.md § 3.3 table):
- topbar-light-desktop.png
- topbar-dark-desktop.png
- topbar-light-mobile.png
- topbar-dark-mobile.png
- logo-mark-grid-light.png
- logo-mark-grid-dark.png

## Files created

- `vitalia/frontend/e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts` (5 scenarios)
- `vitalia/frontend/e2e/visual/topbar-global/topbar.spec.ts` (2 goldens)
- `vitalia/frontend/e2e/visual/topbar-global/logo-mark.spec.ts` (4 goldens)
- `vitalia/frontend/e2e/a11y/topbar-global/topbar.spec.ts` (5 scenarios)

## Note on goldens

Visual goldens require `--update-snapshots` on first run against live dev server.
Goldens are not pre-committed — they're generated during Playwright execution.
Commands:
```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/visual/topbar-global/ --project=visual --update-snapshots
```

## Validators

| Validator | Status |
|---|---|
| `fe_typecheck` | ✅ 0 errors (Playwright TS specs check via tsc) |
| `fe_lint` | ✅ 0 errors (E2E specs excluded from linting per config) |
