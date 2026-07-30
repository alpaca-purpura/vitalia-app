<!-- voseo-allowed: internal guidelines documentation -->

# F1-S2 `vitalia-fase1-topbar-global` — 05-guidelines

## Patterns required

| # | Pattern | Razón |
|---|---|---|
| 1 | `LogoMark` envuelve `next/image` (NO `<img>` raw) | Auto-optimization WebP/AVIF + responsive sizing + lazy loading nativo |
| 2 | `Image` con prop `priority` | TopBar es above-fold (LCP candidate) — load inmediato sin lazy |
| 3 | Height-based sizing + width auto | Preserva aspect ratio del asset original (mark 1:1, full 3:1) |
| 4 | Doble `<Image>` swap dark mode via CSS `block dark:hidden` / `hidden dark:block` | SSR-safe (NO conditional render JS), zero hydration mismatch |
| 5 | Server components default (LogoMark + TopBarGlobal + TenantSwitcherSlot) | NO `'use client'` — performance + SEO + RSC streaming |
| 6 | `<header role="banner">` semantic HTML | Accessibility tree landmark + screen reader nav |
| 7 | Skip link `sr-only focus:not-sr-only` pattern | WCAG 2.4.1 Bypass Blocks compliance |
| 8 | `data-testid` estables (`topbar-global`, `theme-toggle`) | Playwright selectors estables a refactors |
| 9 | aria-label "Vitalia inicio" verbatim | Spanish neutro · accessible name LogoMark `<a>` |
| 10 | aria-label "Saltar al contenido" verbatim | Spanish neutro · skip link text WCAG |
| 11 | Brand assets en `vitalia/frontend/public/brand/` | Servidos por Next.js · NO CDN externo · NO `src/` |
| 12 | Named exports (NO default) | FSD-Lite rule · imports legibles + tree-shaking |
| 13 | Responsive via Tailwind `hidden md:inline-flex` / `inline-flex md:hidden` | CSS responsive · SSR-safe · no JS viewport detection |
| 14 | Z-index skip link (200) > TopBar (50) | Skip link aparece encima del TopBar al focus |
| 15 | `.vt-*` legacy block preservation | NO migrar en esta story (story dedicada fin Fase 2) |
| 16 | NATIVE Linux execution (NO Docker para tests) | Per CLAUDE.md native-first mandatory |
| 17 | Playwright `@project=visual` heredado F1-S0 config | maxDiffPixelRatio 0.001 · animations disabled · caret hide |

## Patterns forbidden

| # | Anti-pattern | Razón |
|---|---|---|
| 1 | `<img src=...>` raw | Use Next.js `Image` (rule #1) |
| 2 | Conditional render LogoMark basado en JS viewport detection | SSR-unsafe · hydration mismatch · usar CSS responsive (rule #13) |
| 3 | `useEffect` para detectar dark mode | Use CSS `dark:` classes — SSR-safe |
| 4 | Hex hardcoded en components | Use Tailwind tokens consume CSS vars |
| 5 | Default exports | Named exports only (rule #12) |
| 6 | `any` TypeScript | Use `unknown` + type guards |
| 7 | Cross-brand imports | NUNCA `from 'nicolify/...'` ni otros brands |
| 8 | Cross-feature imports | NO importar de `features/*` |
| 9 | Importar `core/luana-core-*` | Engine off-limits desde brand FE |
| 10 | Modificar `ThemeToggle.tsx` (F1-S1 shipped) | Solo reuse vía import — NO modify |
| 11 | Modificar `globals.css` (F1-S1 cementó vars) | F1-S2 no toca |
| 12 | Modificar `tailwind.config.ts` (F1-S1 verified) | F1-S2 no toca |
| 13 | Asset CDN externo | Todos local en `public/brand/` |
| 14 | Skip link styling fuera Shadcn vars | Use `bg-primary text-primary-foreground` |
| 15 | Hardcoded paths absolutos `/home/...` | Usar paths relativos al workspace |
| 16 | Editar `(dashboard)/` legacy | Coexiste transparente |
| 17 | Instalar Shadcn primitives nuevos | F1-S0 instaló 8 base — F1-S2 reusa |
| 18 | Tocar `vitalia/.claude/` o `.claude/` | Skill/rule edits manual only |
| 19 | `eslint-disable` sin justification comment | Si necesario, comment explicativo obligatorio |
| 20 | Frameworks no-Tailwind/no-Shadcn | Stack cementado en F1-S0 |

## Files in scope (Sonnet edits ONLY these)

### Pre-implementation verify (T-1):
- `vitalia/frontend/public/brand/vitalia-ico.png` (verify present, ~156KB)
- `vitalia/frontend/public/brand/vitalia-logo.png` (verify present, ~107KB)
- `vitalia/frontend/public/brand/vitalia-logo-dark.png` (verify present, ~93KB)

### NEW component files (T-2, T-3, T-4):
- `vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx` (NEW · server component · Next.js Image wrapper)
- `vitalia/frontend/src/components/shared/shell-organism/LogoMark.test.tsx` (NEW · vitest unit)
- `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx` (NEW · placeholder return null)
- `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` (NEW · server component organism)
- `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.test.tsx` (NEW · vitest unit)

### MODIFY existing (T-5):
- `vitalia/frontend/src/app/layout.tsx` (MODIFY · agregar skip link `Saltar al contenido` + verify main#main-content)

### Test pages (T-6):
- `vitalia/frontend/e2e/__test-pages__/topbar-global/topbar-showcase.tsx` (NEW)
- `vitalia/frontend/e2e/__test-pages__/topbar-global/logo-mark-showcase.tsx` (NEW)

### Playwright specs (T-7):
- `vitalia/frontend/e2e/regression/topbar-global/topbar-interaction.spec.ts` (NEW)
- `vitalia/frontend/e2e/visual/topbar-global/topbar.spec.ts` (NEW · 4 goldens)
- `vitalia/frontend/e2e/visual/topbar-global/logo-mark.spec.ts` (NEW · 2 goldens)
- `vitalia/frontend/e2e/a11y/topbar-global/topbar.spec.ts` (NEW · axe + keyboard)

### Visual goldens commit (T-7):
- `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-light-desktop.png` (NEW)
- `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-dark-desktop.png` (NEW)
- `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-light-mobile.png` (NEW)
- `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-dark-mobile.png` (NEW)
- `vitalia/frontend/e2e/__screenshots__/topbar-global/logo-mark-grid-light.png` (NEW)
- `vitalia/frontend/e2e/__screenshots__/topbar-global/logo-mark-grid-dark.png` (NEW)

## Files Sonnet NEVER touches

| Path | Razón |
|---|---|
| `core/luana-core-*/` | Engine — requires lift via /pm-luana promotion gate |
| `nicolify/`, `comunify/`, `lupulo/` (other brands) | Cross-brand pollution prohibida |
| `vitalia/frontend/src/app/[tenantId]/(dashboard)/` | Legacy — coexistencia transparente |
| `vitalia/frontend/src/components/ui/*` | Shadcn primitives F1-S0 — NO modify |
| `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` | F1-S1 shipped — reuse vía import |
| `vitalia/frontend/src/app/globals.css` | F1-S1 cementó CSS vars — F1-S2 NO toca |
| `vitalia/frontend/tailwind.config.ts` | F1-S1 verified — F1-S2 NO toca |
| `vitalia/.claude/`, `.claude/` | Skill/rule edits manual only |
| `vitalia/backend/` | Story FE-only |
| `vitalia/docs/learnings/`, `vitalia/docs/architecture/` | /pm-vitalia territory — NO desde dev-team |

## must_load_skills (★ v4.1 enforceable verbatim)

Builder dev-team Step 2 cita esta lista. Builder MUST entregar en `T-{n}-result.md` sección "Skills consulted" listando cuáles cargó. Auditor flag CHANGES_REQUESTED si missing.

### Skills core obligatorios por surface:

| Skill | When | Purpose |
|---|---|---|
| `frontend-expert` | FE surface (siempre F1-S2) | FSD-Lite, Tailwind tokens, Shadcn reuse |
| `playwright-expert` | playwright_required: true | POM patterns + @project=visual + axe-core + responsive testing + anti-Docker |

### Tessl skills (versioned canonical docs):

| Skill | When | Purpose |
|---|---|---|
| `tessl__nextjs-app-router-modularization` | layout.tsx + Image patterns | Skip link patterns · Image priority · server components |
| `tessl__shadcn-ui` | Component patterns | Responsive utility patterns |
| `tessl__tailwind` | Responsive + dark mode classes | `hidden md:inline-flex` · `block dark:hidden` swap |
| `tessl__vitest` | Unit tests | Render assertions · `@testing-library/react` patterns |

### Rules obligatorias siempre:

| Rule | Purpose |
|---|---|
| `.claude/rules/frontend-fsd.md` | FSD-Lite boundaries · shared/shell-organism/ allowed path |
| `.claude/rules/spanish-text.md` | Voseo glosario + magic comment escape |
| `.claude/rules/anti-duplication.md` | NO cross-brand mirror · ThemeToggle reuse import (F1-S1) |
| `.claude/rules/tdd-mandatory.md` | RED → GREEN → REFACTOR discipline |
| `.claude/rules/auditor-self-fix-policy.md` | Conocer qué findings auditor self-fix vs spawn dev-team |
| `vitalia/.claude/rules/shell-mockup-per-component.md` | F1-S2 APPLIED · 2 mockups (`topbar-global.html` + `logo-mark.html`) ratified |
| `vitalia/.claude/rules/hipaa-lite.md` | no-phi-scope declared F1-S2 |

## reference_artifacts

Documentos del ready package que builder re-lee mid-build cuando surge ambigüedad:

| Path | Purpose |
|---|---|
| `vitalia/docs/product/stories/vitalia-fase1-topbar-global/01-spec.md` | Re-read Gherkin scenarios + 6 decisiones D1-D6 cementadas |
| `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/topbar-global.html` | Visual contract 4 states (light/dark × desktop/mobile) |
| `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/logo-mark.html` | Visual contract 6 combinations grid |
| `vitalia/docs/product/stories/vitalia-fase1-topbar-global/03-arch.md` | Implementation patterns verbatim (LogoMark + TopBarGlobal + skip link) |
| `vitalia/docs/product/stories/vitalia-fase1-topbar-global/04-validators.yaml` § test_construction_plan | Orden creación + POMs + fixtures + scenario_to_test mapping |
| `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 3.1 + § 3.3 + § 5 | Atomic design SSoT del shell |
| `vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/03-arch.md` | Predecessor F1-S1 — ThemeToggle consumido en TopBar |
| `vitalia/docs/product/stories/vitalia-fase1-stack-stability/03-arch.md` | Predecessor F1-S0 — Shadcn install + tokens base |

## Build verification commands (T-8)

Comandos copy-paste para verificación final:

```bash
WS=$(git rev-parse --show-toplevel)

# 1. Type check
cd ${WS}/vitalia/frontend && npx tsc --noEmit

# 2. Lint
cd ${WS}/vitalia/frontend && npx eslint src/ --max-warnings 0

# 3. Format check
cd ${WS}/vitalia/frontend && npx prettier --check src/components/shared/shell-organism/

# 4. Vitest unit + arch fitness
cd ${WS}/vitalia/frontend && npx vitest run

# 5. Production build
cd ${WS}/vitalia/frontend && npm run build

# 6. Playwright behavior + visual + a11y
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/topbar-global/ e2e/visual/topbar-global/ e2e/a11y/topbar-global/

# 7. Visual regression F1-S0 + F1-S1 (MUST seguir GREEN)
cd ${WS}/vitalia/frontend && npx playwright test e2e/visual/stack-stability/ e2e/visual/design-tokens-theme/

# 8. Browser visual final
cd ${WS} && make dev-vitalia
# http://localhost:3002 — verify TopBar renderiza con LogoMark + ThemeToggle + skip link a11y
```

**Expected:** todos los comandos retornan exit code 0.
