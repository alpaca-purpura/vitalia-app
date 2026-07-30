# T-6 impl-log — fe-test-pages

**Story:** vitalia-fase1-topbar-global (F1-S2)
**Ticket:** T-6
**Date:** 2026-05-23
**Owner:** builder-frontend / Claude Sonnet 4.6

## Plan

Create 2 test page fixtures + 2 Next.js route wrappers:

1. `e2e/__test-pages__/topbar-global/topbar-showcase.tsx` — TopBarGlobal full page
2. `e2e/__test-pages__/topbar-global/logo-mark-showcase.tsx` — LogoMark 6-cell grid (3 sizes × 2 variants)
3. `src/app/test-stack/topbar-global/page.tsx` — Next.js route wrapper
4. `src/app/test-stack/logo-mark/page.tsx` — Next.js route wrapper

Following F1-S1 lesson: route wrappers required for Playwright to avoid 404.
Both pages are public (no Clerk auth), accessible at:
- `/test-stack/topbar-global`
- `/test-stack/logo-mark`

## Files created

- `vitalia/frontend/e2e/__test-pages__/topbar-global/topbar-showcase.tsx`
- `vitalia/frontend/e2e/__test-pages__/topbar-global/logo-mark-showcase.tsx`
- `vitalia/frontend/src/app/test-stack/topbar-global/page.tsx`
- `vitalia/frontend/src/app/test-stack/logo-mark/page.tsx`

## Validators

| Validator | Status |
|---|---|
| `fe_typecheck` | ✅ 0 errors |
| `fe_lint` | ✅ 0 errors, 0 warnings |
