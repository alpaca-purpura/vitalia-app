<!-- voseo-allowed: internal architecture documentation -->

---
story_id: vitalia-fase1-topbar-global
brand: vitalia
state: ready
written_at: 2026-05-22
target_version: v1.0
depends_on: [vitalia-fase1-stack-stability, vitalia-fase1-design-tokens-theme]
blocks_hard: [vitalia-fase1-shell-layout-5050]
schema_version: v4.1
---

# F1-S2 `vitalia-fase1-topbar-global` — 03-arch (consolidated)

## § 1 — Surfaces involved

| Surface | Touch | Notes |
|---|---|---|
| BE | ❌ N/A | Story 100% FE local. No endpoints. No DB. |
| FE | ✅ YES | LogoMark + TopBarGlobal + TenantSwitcherSlot + layout.tsx skip link + 6 visual goldens + 3 Playwright specs |
| AGENTIC | ❌ N/A | No agentic tools/prompts/workflows |
| Engine | ❌ N/A | NO toca `core/luana-core-*/` |
| Other brands | ❌ N/A | NO toca `{other_brand}/` |

---

## § 2 — FE architecture detail

### § 2.1 — Brand assets in `public/brand/`

Path canónico: `vitalia/frontend/public/brand/`

| Asset | Size | Purpose | Modes |
|---|---|---|---|
| `vitalia-ico.png` | ~156KB | Libélula multicolor (cyan + púrpura + magenta + amarillo + verde lima) | Both light + dark (multi-tono funciona ambos modes) |
| `vitalia-logo.png` | ~107KB | Libélula + wordmark "VITALIA" navy `#1a1a5e` | Light mode |
| `vitalia-logo-dark.png` | ~93KB | Libélula + wordmark "VITALIA" white | Dark mode (D6 ✓ ratified Chris 2026-05-22) |

Pre-step T-1 verifica que los 3 PNG estén committed antes de implementar componentes.

### § 2.2 — `LogoMark.tsx` átomo

**Path:** `vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx`

**Type:** Server component (NO `'use client'`)

**Implementation pattern verbatim:**

```tsx
import Image from 'next/image'
import { cn } from '@/lib/utils'

type Size = 'sm' | 'md' | 'lg'
type Variant = 'full' | 'mark'

interface LogoMarkProps {
  size?: Size
  variant?: Variant
  href?: string
  className?: string
}

const heights: Record<Size, number> = { sm: 24, md: 32, lg: 40 }
const aspectRatios: Record<Variant, number> = { full: 3, mark: 1 }

const assetSrc = {
  full: { light: '/brand/vitalia-logo.png', dark: '/brand/vitalia-logo-dark.png' },
  mark: { light: '/brand/vitalia-ico.png', dark: '/brand/vitalia-ico.png' }, // libélula multicolor funciona ambos modes
} as const

export function LogoMark({
  size = 'md',
  variant = 'full',
  href = '/',
  className,
}: LogoMarkProps) {
  const h = heights[size]
  const w = Math.round(h * aspectRatios[variant])

  return (
    <a
      href={href}
      aria-label="Vitalia inicio"
      className={cn('inline-flex items-center', className)}
    >
      {/* Light mode asset */}
      <Image
        src={assetSrc[variant].light}
        alt="Vitalia"
        width={w}
        height={h}
        className="block dark:hidden"
        priority
      />
      {/* Dark mode asset */}
      <Image
        src={assetSrc[variant].dark}
        alt="Vitalia"
        width={w}
        height={h}
        className="hidden dark:block"
        priority
      />
    </a>
  )
}
```

**Decisiones técnicas:**
- Server component (no estado, no hooks de cliente)
- `Image` con `priority` porque TopBar es above-fold (LCP candidate)
- Doble `Image` con `block dark:hidden` / `hidden dark:block` para swap SSR-safe (NO `useEffect` para detectar theme)
- Height-based sizing preserva aspect ratio del asset original
- Named export (NO default — FSD-Lite rule)

### § 2.3 — `TopBarGlobal.tsx` organismo

**Path:** `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx`

**Type:** Server component

**Implementation pattern:**

```tsx
import { LogoMark } from './LogoMark'
import { ThemeToggle } from './ThemeToggle'
import { TenantSwitcherSlot } from './TenantSwitcherSlot'

export function TopBarGlobal() {
  return (
    <header
      role="banner"
      data-testid="topbar-global"
      className="h-12 border-b border-border bg-background flex items-center justify-between px-5 relative z-50"
    >
      {/* Desktop: full logo (libélula + wordmark) */}
      <LogoMark variant="full" className="hidden md:inline-flex" />
      {/* Mobile: mark only (libélula) */}
      <LogoMark variant="mark" className="inline-flex md:hidden" />

      <div className="flex items-center gap-2">
        <ThemeToggle />
        <TenantSwitcherSlot />
      </div>
    </header>
  )
}
```

**Responsive strategy cementada:** 2 instancias de `LogoMark` con CSS visibility swap (`hidden md:inline-flex` vs `inline-flex md:hidden`). SSR-safe. NO conditional render basado en JS viewport detection (que requeriría `useEffect` + causaría hydration mismatch).

### § 2.4 — `TenantSwitcherSlot.tsx` placeholder

**Path:** `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx`

```tsx
// TODO(F1-S3 vitalia-fase1-tenant-switcher): reemplazar return null con <TenantSwitcher />
// Drop-in pattern: este componente se reemplaza dentro de TopBarGlobal sin layout shift
export function TenantSwitcherSlot() {
  return null
}
```

Server component. Returns null (no DOM element). F1-S3 reemplaza el body con `<TenantSwitcher />` sin tocar `TopBarGlobal.tsx`.

### § 2.5 — `layout.tsx` modify (skip link a11y)

**Path:** `vitalia/frontend/src/app/layout.tsx`

**Modificaciones:**

1. Agregar skip link ANTES de `{children}`:

```tsx
<body>
  <a
    href="#main-content"
    className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-[200] focus:p-2 focus:bg-primary focus:text-primary-foreground"
  >
    Saltar al contenido
  </a>
  <ThemeProvider {...providerProps}>
    {children}
  </ThemeProvider>
</body>
```

2. Verificar que el main content wrapper tiene `id="main-content"`. Si no existe, agregarlo (puede vivir en `(shell-organism)/layout.tsx` o en el root layout según la estructura actual):

```tsx
<main id="main-content">
  {/* shell content */}
</main>
```

**Constraint:** NO romper el `<ThemeProvider>` wrap de F1-S1 ni el `suppressHydrationWarning` en `<html>`.

### § 2.6 — Vitest unit tests

| Test file | Coverage |
|---|---|
| `LogoMark.test.tsx` | Render cada combination (6: 3 sizes × 2 variants) · assert dimensions correctas · assert aria-label="Vitalia inicio" · assert href default `/` · assert Image src correcto por variant + mode (light vs dark via class) |
| `TopBarGlobal.test.tsx` | Render TopBar · assert role="banner" · assert data-testid · assert composición children (2 LogoMark instances con classes responsive + ThemeToggle + TenantSwitcherSlot) · assert classes Tailwind correctas |
| `TenantSwitcherSlot.test.tsx` | Assert returns null (no DOM element rendered) |

### § 2.7 — Playwright specs (3 + 2 test pages)

**Test pages** (`vitalia/frontend/e2e/__test-pages__/topbar-global/`):

| File | Contenido |
|---|---|
| `topbar-showcase.tsx` | Renderiza `<TopBarGlobal />` en página full con dummy main content (placeholder text "F1-S2 mockup main") y `id="main-content"` para skip link target |
| `logo-mark-showcase.tsx` | Renderiza grid 3×2 (6 combinations) en card centrada para snapshot consistente |

**Specs:**

| File | Tipo | Cobertura |
|---|---|---|
| `e2e/regression/topbar-global/topbar-interaction.spec.ts` | Behavior | Tab nav skip link visible · Enter jump a `#main-content` · ThemeToggle click integration (theme swap + LogoMark asset swap) · viewport resize 375 vs 1440 (responsive LogoMark variant switch) · aria-label assertions |
| `e2e/visual/topbar-global/topbar.spec.ts` | Visual baseline | 4 goldens TopBar (light/dark × desktop/mobile) · maxDiffPixelRatio 0.001 |
| `e2e/visual/topbar-global/logo-mark.spec.ts` | Visual baseline | 2 goldens LogoMark grid (light/dark × 6 combinations) |
| `e2e/a11y/topbar-global/topbar.spec.ts` | A11y | `@axe-core/playwright` WCAG 2.1 AA scan + keyboard nav (Tab/Enter/Shift+Tab) + banner landmark + aria-label assertions |

### § 2.8 — 6 Playwright visual goldens

Path: `vitalia/frontend/e2e/__screenshots__/topbar-global/`

| Golden | Viewport | Theme |
|---|---|---|
| `topbar-light-desktop.png` | 1440×900 | light |
| `topbar-dark-desktop.png` | 1440×900 | dark |
| `topbar-light-mobile.png` | 375×667 | light |
| `topbar-dark-mobile.png` | 375×667 | dark |
| `logo-mark-grid-light.png` | 800×400 | light |
| `logo-mark-grid-dark.png` | 800×400 | dark |

---

## § 3 — Cross-cutting decisions

### § 3.1 — Responsive strategy: CSS swap (NOT JS viewport detection)

**Decisión:** 2 instancias `LogoMark` con Tailwind `hidden md:inline-flex` / `inline-flex md:hidden` swap.

**Razón:** SSR-safe (no hydration mismatch), no `useEffect`, simple CSS responsive. Trade-off: 2 nodos DOM (uno oculto), but Image lazy loading via Next.js mitiga (el oculto NO se descarga por CSS `display: none`).

### § 3.2 — Brand assets en `public/brand/`

**Decisión:** PNG vía Next.js Image en `public/brand/` (D5 ratificada).

**Razón:** Next.js Image auto-optimiza (WebP/AVIF + responsive sizing + lazy loading), reduce peso real entregado <30KB cada asset. SVG roadmap diferido a story dedicada futura.

### § 3.3 — Dark mode asset swap

**Decisión:** Doble `<Image>` con CSS `block dark:hidden` / `hidden dark:block` (D6 ✓ ratified).

**Razón:** SSR-safe swap automático. Asset dark `vitalia-logo-dark.png` (wordmark white) provisto por Chris 2026-05-22. Sin fallback interim necesario.

### § 3.4 — Skip link estilizado con CSS vars

**Decisión:** Skip link consume `bg-primary text-primary-foreground` Shadcn vars (F1-S1 completed).

**Razón:** Mantiene brand coherence + WCAG AA contrast automático (primary cyan + white text foreground ≥ 4.5:1).

### § 3.5 — TenantSwitcherSlot drop-in pattern

**Decisión:** `returns null` puro. F1-S3 reemplaza el body con `<TenantSwitcher />` sin tocar TopBarGlobal.tsx.

**Razón:** Sin layout shift cuando F1-S3 monta el real component. Asume max-width razonable del TenantSwitcher (~140-180px) — F1-S3 spec va a cementar.

---

## § 4 — Test Construction Plan summary

Detalle completo en `04-validators.yaml § test_construction_plan`. Resumen:

- **playwright_required:** true (behavior + 6 visual goldens + a11y)
- **base_path:** `vitalia/frontend/e2e/{__test-pages__,regression,visual,a11y,__screenshots__}/topbar-global/`
- **creation_order:** 12 steps (assets verify → LogoMark → TenantSwitcherSlot → TopBarGlobal → layout skip link → test pages → 3 specs → goldens generation → regression verify → build)
- **poms_required:** opcional (TopBarPage POM ligero)
- **fixtures_required:** themeFixture · viewportFixture · axeFixture

---

## § 5 — Engine boundaries

- **NO** edita `core/luana-core-*/` (engine). F1-S2 100% FE local Vitalia.
- **NO** edita `{other_brand}/` (nicolify, comunify, lupulo, futuras).
- **NO** edita `vitalia/backend/`.
- **NO** edita `vitalia/.claude/` ni `.claude/`.

---

## § 6 — Anti-patterns prohibidos

- ❌ Editar `(dashboard)/` legacy
- ❌ Conditional render LogoMark based on JS viewport detection (use CSS responsive)
- ❌ `useEffect` para detectar dark mode (use CSS `dark:` classes)
- ❌ `<img>` raw (use Next.js `<Image>`)
- ❌ Hex hardcoded en components (use Tailwind tokens)
- ❌ Default exports
- ❌ `any` TypeScript
- ❌ Cross-brand imports
- ❌ Cross-feature imports (no `import` desde `features/*`)
- ❌ Importar `core/luana-core-*`
- ❌ Modificar `ThemeToggle.tsx` (F1-S1 — solo reuse vía import)
- ❌ Modificar `globals.css` (F1-S1 cementó vars)
- ❌ Modificar `tailwind.config.ts` (F1-S1 verified)
- ❌ Asset CDN externo (todos local en `public/brand/`)
- ❌ Skip link styling fuera Shadcn vars

---

## § 7 — References

- `vitalia/docs/product/stories/vitalia-fase1-topbar-global/01-spec.md` (Gherkin 9 scenarios + 6 decisiones D1-D6)
- `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/topbar-global.html` (4 states ratificado)
- `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/logo-mark.html` (6 combinations ratificado)
- `vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/03-arch.md` (predecessor F1-S1 — ThemeToggle reuse)
- `vitalia/docs/product/stories/vitalia-fase1-stack-stability/03-arch.md` (predecessor F1-S0 — Shadcn install + tokens base)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 3.1 átomos + § 3.3 organismos + § 5 tokens
- `vitalia/.claude/rules/shell-mockup-per-component.md` (consume — F1-S2 APPLIED, 2 mockups ratified)
- `vitalia/.claude/rules/hipaa-lite.md` (consume — no-phi-scope declared)
- `.claude/rules/frontend-fsd.md`
- `.claude/rules/spanish-text.md`
- `.claude/rules/anti-duplication.md`
- `.claude/rules/tdd-mandatory.md`
