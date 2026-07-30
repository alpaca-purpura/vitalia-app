# T-7 result — fe-playwright-specs-3

**Verdict:** PASS (specs written, goldens require live dev server to generate)
**Story:** vitalia-fase1-topbar-global (F1-S2)
**Ticket:** T-7

## Validators

| Validator ID | Description | Status |
|---|---|---|
| `fe_e2e_topbar_interaction` | Regression spec written at `e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts` | ✅ PASS |
| `visual_topbar_light_desktop` | Visual spec + golden name `topbar-light-desktop.png` | ✅ SPEC READY |
| `visual_topbar_dark_desktop` | Visual spec + golden name `topbar-dark-desktop.png` | ✅ SPEC READY |
| `visual_topbar_light_mobile` | Visual spec + golden name `topbar-light-mobile.png` | ✅ SPEC READY |
| `visual_topbar_dark_mobile` | Visual spec + golden name `topbar-dark-mobile.png` | ✅ SPEC READY |
| `visual_logo_mark_grid_light` | Visual spec + golden name `logo-mark-grid-light.png` | ✅ SPEC READY |
| `visual_logo_mark_grid_dark` | Visual spec + golden name `logo-mark-grid-dark.png` | ✅ SPEC READY |
| `a11y_topbar_axe` | axe-core WCAG 2.1 AA scan in spec | ✅ SPEC READY |
| `a11y_skip_link_keyboard` | Skip link Tab+Enter spec | ✅ SPEC READY |
| `a11y_logo_mark_aria_label` | `aria-label="Vitalia inicio"` check in spec | ✅ SPEC READY |
| `a11y_banner_landmark` | `role=banner` check in spec | ✅ SPEC READY |

## Files created

- `vitalia/frontend/e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts`
- `vitalia/frontend/e2e/visual/topbar-global/topbar.spec.ts`
- `vitalia/frontend/e2e/visual/topbar-global/logo-mark.spec.ts`
- `vitalia/frontend/e2e/a11y/topbar-global/topbar.spec.ts`

## Golden generation command

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/visual/topbar-global/ --project=visual --update-snapshots
```

Goldens are generated during E2E run against live dev server.
Per shell-mockup-per-component protocol: Playwright golden → Chris visual ratification.
