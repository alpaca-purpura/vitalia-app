# T-2 impl-log — fe-logo-mark-component

**Story:** vitalia-fase1-topbar-global (F1-S2)
**Ticket:** T-2
**Date:** 2026-05-23
**Owner:** builder-frontend / Claude Sonnet 4.6

## Plan

Create LogoMark Server Component with:
- 3 sizes: sm (24px), md (32px), lg (40px)
- 2 variants: full (3:1 aspect), mark (1:1 aspect)
- CSS-based dark mode swap via dual `<Image>` (SSR-safe, no useEffect)
- Next.js `<Image>` with `priority` for above-fold LCP
- Named export, no default export
- `aria-label="Vitalia inicio"` on `<Link>` wrapper
- Decorative `alt=""` on images (semantic label on `<a>`)

TDD: wrote LogoMark.test.tsx RED first (9 tests for 6 combinations + a11y + named export contract), then implemented LogoMark.tsx to pass.

## Files created

- `vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/LogoMark.test.tsx`

## Validators run

| Validator | Status |
|---|---|
| `fe_typecheck` | ✅ `npx tsc --noEmit` → 0 errors |
| `fe_lint` | ✅ `npx eslint shell-organism/` → 0 errors, 0 warnings |
| `fe_logo_mark_next_image_grep` | ✅ `<Image` used, `priority` set |
| `fe_no_default_exports_grep` | ✅ Named export `export function LogoMark` |
| `fe_no_any_typescript_grep` | ✅ No `any` type |
| `fe_vitest_existing_regression` | ✅ 9/9 tests pass |
