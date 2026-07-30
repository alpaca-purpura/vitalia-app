# T-1 Impl Log — 6 moléculas foundational shell-organism + Vitest unit

**Story:** vitalia-fase1-empty-states  
**Ticket:** T-1  
**Brand:** vitalia  
**Date:** 2026-05-26  
**Builder:** claude-sonnet-4-6  

## Summary

T-1 entrega las 6 moléculas foundational del shell-organism y sus 3 archivos de test Vitest (TDD RED→GREEN). Todos los gates de calidad pasan.

## Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries, ESLint config, Vitest patterns, arch tests | Server Components default; named exports; PLACEHOLDER_MAP pattern |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys | `aria-hidden` en icon containers; `role="status"` en EmptyState; `aria-label` en StatusDot |
| `tessl__shadcn-ui` | Component selection — Tabs/TabsList/TabsTrigger from components/ui/tabs.tsx | Reuse Shadcn Tabs primitives; TogglePill wraps con pill styling override |
| `tessl__tailwind` | Utility classes + semantic tokens | `cn()` para conditional classes; cero `style={{}}` inline |
| `tessl__vitest` | Test setup, async patterns, mocking | happy-dom env; `@testing-library/react`; getByRole/getByTestId patterns |
| `tessl__nextjs-app-router-modularization` | Server/Client boundary split | Solo TogglePill necesita "use client" (Radix Tabs state) |

## Iteration Log

### Iter 1 — TDD RED (test files created, implementations missing)

Tests creados RED-first:
- `EmptyState.test.tsx` — 7 tests (icon rendering, h3 title, description, CTA button optional, aria-hidden, voseo check)
- `TogglePill.test.tsx` — 5 tests (container, items rendering, default selection, 3-item combo, voseo check)
- `SubTabContent.test.tsx` — 8 tests (data-testid combos, EmptyState fallback, SubTabHeader heading, label in content)

Resultado esperado: FAIL (imports unresolvable — RED).

### Iter 2 — GREEN (6 moléculas implementadas)

Implementados en orden de dependencia:

1. **StatusDot.tsx** — Server Component, 3 variantes (green/yellow/gray), semantic token colors
2. **EmptyState.tsx** — Server Component, icon 5xl opacity-50, h3 title, description max-w-md, CTA button opcional
3. **PlaceholderCard.tsx** — Server Component, consumes StatusDot, icon + h3 + desc + count badge
4. **SubTabHeader.tsx** — Server Component, h2 + description + CTA right-aligned, consume RibbonTabMeta
5. **TogglePill.tsx** — Client Component ("use client" por Radix Tabs state), pill styling override, re-export TabsContent
6. **SubTabContent.tsx** — Server Component (dispatcher), PLACEHOLDER_MAP 22 keys consume RIBBON_SUBTABS SSoT, EmptyState fallback

Resultados: 20/20 tests GREEN.

### Iter 3 — Prettier format fix

4 archivos necesitaban reformateo (PlaceholderCard, SubTabContent, EmptyState.test, SubTabContent.test). Ejecutado `npx prettier --write` en los 9 archivos nuevos. Tests todavía 20/20 GREEN post-format.

### Iter 4 — Architecture test fix

`test_no_voseo_in_copy.test.ts` FAIL: el regex del arch test solo reconocía `# voseo-allowed` (Python) y `<!-- voseo-allowed -->` (HTML), NO `// voseo-allowed` (TypeScript).

Fix doble:
1. Agregado `// voseo-allowed: test fixture ...` comment al inicio de `EmptyState.test.tsx` y `TogglePill.test.tsx`
2. Actualizado regex en arch test para soportar `//` comment style: `/(?:(?:#|\/\/)\s*voseo-allowed([: \t—]|$)|<!--\s*voseo-allowed[^>]*-->)/`

Resultado: 20/20 arch test files, 123/123 arch tests GREEN.

## Gate Results

| Gate | Result | Detail |
|---|---|---|
| TypeScript strict (`tsc --noEmit`) | PASS | 0 errors |
| ESLint 60+ rules | PASS | 0 errors |
| Vitest coverage | PASS | 1569 tests, 82.67% statements / 91.51% branches / 67.71% functions / 82.67% lines (all ≥20%) |
| Architecture fitness (20 test files) | PASS | 123 tests GREEN |
| T-1 unit tests (20) | PASS | 7 EmptyState + 5 TogglePill + 8 SubTabContent |

## Architecture Invariants Satisfied

- SubTabContent imports RIBBON_SUBTABS (READ-ONLY SSoT)
- PLACEHOLDER_MAP: exactly 22 keys (no mateo.* — RIBBON_SUBTABS.mateo === [])
- All keys: lisa(4) + lucas(5) + adrian(4) + valeria(2) + camila(4) + config(3) = 22
- No default exports
- No cross-brand imports
- Server-First boundaries: only TogglePill has "use client"
- FSD-Lite: molecules in `components/shared/shell-organism/`, not `features/`

## Files Changed

**NEW (9):**
- `vitalia/frontend/src/components/shared/shell-organism/StatusDot.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/EmptyState.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/PlaceholderCard.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/SubTabHeader.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/TogglePill.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/EmptyState.test.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/TogglePill.test.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/SubTabContent.test.tsx`

**MODIFIED (1):**
- `vitalia/frontend/src/__tests__/architecture/test_no_voseo_in_copy.test.ts` — regex updated to support `//` comment style for TS files

## Live Verification

`chrome-devtools-verify` skill marked DEPRECATED (designed for WSL2+Windows bridge, requires rewrite for Linux Mint). Manual verification escalated to Chris staging gate. All automated gates (tsc + eslint + vitest + arch tests) PASS.
