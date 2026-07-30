# T-6 result — Playwright specs + test page fixture

**Ticket:** T-6
**Story:** vitalia-fase1-design-tokens-theme (F1-S1)
**State:** done

## Summary

Created test page fixture and 3 Playwright spec files following the F1-S0 lesson: test pages in `e2e/__test-pages__/` require a Next.js route wrapper in `src/app/test-stack/`.

## Files created

### Test page fixture
- `vitalia/frontend/e2e/__test-pages__/design-tokens-theme/theme-toggle-showcase.tsx`
  - Renders `<ThemeToggle />` in centered card using `bg-background` / `bg-card` semantic tokens
  - Default export (required by Next.js dynamic import pattern)

### Next.js route wrapper
- `vitalia/frontend/src/app/test-stack/design-tokens-theme/page.tsx`
  - Public route (no auth required — proxy.ts already has `/test-stack(.*)` allowlist from F1-S0)
  - Imports from showcase file via `@/../e2e/__test-pages__/design-tokens-theme/theme-toggle-showcase`

### Playwright specs (require running dev server on port 3002)
- `vitalia/frontend/e2e/regression/design-tokens-theme/theme-toggle-interaction.spec.ts`
  - SC-01: click changes `data-theme="dark"` + localStorage + aria-pressed + icon swap
  - SC-01b: double click returns to light
  - SC-02: pre-set dark via localStorage → persists on load (FOUC prevention)
  - SC-03: zero console errors during hydration

- `vitalia/frontend/e2e/visual/design-tokens-theme/theme-toggle.spec.ts`
  - SC-04: light mode golden at 400×300 viewport
  - SC-05: dark mode golden at 400×300 viewport (pre-set via addInitScript)
  - Uses visual project (maxDiffPixelRatio: 0.001, animations: disabled)
  - First run requires: `npx playwright test e2e/visual/design-tokens-theme/ --project=visual --update-snapshots`

- `vitalia/frontend/e2e/a11y/design-tokens-theme/theme-toggle.spec.ts`
  - SC-06: axe-core WCAG 2.1 AA scan light mode → 0 violations
  - SC-07: axe-core WCAG 2.1 AA scan dark mode → 0 violations
  - SC-08: keyboard Tab→focus, Enter→activate, Space→activate

## E2E run command (requires `make dev-vitalia` on port 3002)

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test \
    e2e/regression/design-tokens-theme/ \
    e2e/a11y/design-tokens-theme/ \
    --project=chromium
```

## Notes

- These specs were NOT auto-executed (require live dev server)
- Visual goldens require `--update-snapshots` on first run to generate baselines
- Per `.claude/rules/e2e-testing.md`: native Playwright only (NUNCA `make e2e`)
