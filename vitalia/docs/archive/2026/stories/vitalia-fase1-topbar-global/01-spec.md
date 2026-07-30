<!-- voseo-allowed: internal spec documentation -->

---
story_id: vitalia-fase1-topbar-global
brand: vitalia
type: ui-story
phase: fase-1
module: shell-organism
agent_owner: shell
capability: shell.topbar-global
po_version: 1.0
last_modified: 2026-05-22
state: refining
ratified_by_chris: false
ratified_visual_by_chris: false
ratified_visual_mockups: []
parallel_safe: false
priority: critical
estimated_dev_days: 1
dependencies:
  hard: [vitalia-fase1-stack-stability, vitalia-fase1-design-tokens-theme]
  soft: []
service_blockers: []
blocks_hard:
  - vitalia-fase1-shell-layout-5050
reuse_map_summary: "NEW LogoMark átomo (3 sizes × 2 variants = 6 combinations) wrapping brand asset PNGs (vitalia-ico.png libélula multicolor + vitalia-logo.png libélula+wordmark navy) via Next.js Image · NEW TopBarGlobal organismo (48px thin) compose ThemeToggle (F1-S1) + TenantSwitcherSlot placeholder (F1-S3 fills) · Skip link a11y agregado a (shell-organism)/layout · Dark mode wordmark dependency: requires vitalia-logo-dark.png asset (white/cyan wordmark) — pending Chris entrega"
links:
  design_contract: "vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md"
  predecessor_f1s0: "vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md"
  predecessor_f1s1: "vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/01-spec.md"
  mockup_visual_integral: "vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html"
  outcome_master: "vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md"
  template_shell_spec: "vitalia/docs/specs/templates/01-spec-shell-template.md"
  mockup_per_component_protocol: "vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md"
---

# F1-S2 `vitalia-fase1-topbar-global` — 01-spec

## § 1 — Resumen ejecutivo

F1-S2 construye los **primeros dos componentes visuales user-facing del shell-organism**:

1. **`LogoMark`** (átomo) — identidad de marca Vitalia: **libélula multicolor estilizada** (cyan + púrpura + magenta + amarillo + verde lima) como icono brand. Asset PNG real provisto por Chris (`vitalia-ico.png` libélula solo · `vitalia-logo.png` libélula + wordmark "VITALIA" navy `#1a1a5e` tipografía sans tracking abierto). 3 sizes (sm 24px / md 32px default / lg 40px height) × 2 variants (`full` libélula+wordmark · `mark` solo libélula) = 6 combinations. Renderizado vía **Next.js `<Image>`** con auto-optimization (WebP/AVIF). Wrap `<a href="/">` con `aria-label="Vitalia inicio"`.

2. **`TopBarGlobal`** (organismo) — barra superior thin de 48px (`h-12`) presente en todas las rutas del shell-organism. Layout: `LogoMark` izquierda + `<div class="flex gap-2">` derecha conteniendo `<ThemeToggle />` (F1-S1) + `<TenantSwitcherSlot />` (placeholder null que F1-S3 va a reemplazar drop-in).

Además agrega **skip link** a11y en el shell layout (`Saltar al contenido` → `#main-content`) per WCAG 2.4.1 Bypass Blocks.

**Decisiones cementadas Chris 2026-05-22 (6 batched /po-ux):**

- D1 — LogoMark scope: 3 sizes (sm 24px · md 32px · lg 40px **height-based**) + 2 variants (full · mark) = 6 combinations totales. Razón: cubrir casos uso futuros (TopBar md, sidebar logo sm, splash lg) sin spawn future stories. Height-based porque el logo wide tiene aspect-ratio ~3:1 (libélula+wordmark) y mark cuadrado ~1:1 — height fija + width auto preserva proporciones.
- D2 — Mobile responsive: LogoMark switch a `variant='mark'` vía CSS `@media (max-width: 767px)` — desktop ≥768px muestra `Vitalia_Logo` full, mobile <768px solo `Vitalia_Ico` libélula. Sin hamburger menu. Razón: con solo 2-3 acciones derecha cabe perfecto a 375px+.
- D3 — TenantSwitcherSlot: `returns null` puro (sin placeholder visible). F1-S3 reemplaza la línea drop-in con `<TenantSwitcher />`. Razón: sin layout shift al monter el real component, más limpio visualmente.
- D4 — Mockups separados per shell-mockup-per-component rule: `topbar-global.html` (4 states: light+desktop · light+mobile · dark+desktop · dark+mobile) + `logo-mark.html` (grid 6 combinations 3 sizes × 2 variants, toggle dark mode). Razón: convención one-mockup-per-component del rule, fácil revisar visual contract individual.
- **D5 — Formato logo: PNG via Next.js Image ahora + roadmap SVG futuro.** Assets reales `vitalia-ico.png` (libélula 500×500 ≈156KB) + `vitalia-logo.png` (libélula+wordmark VITALIA navy ≈107KB) en `vitalia/frontend/public/brand/`. Next.js Image auto-optimiza (WebP/AVIF + responsive sizing) → peso real entregado <30KB. Story futura `vitalia-fase2-logo-svg-conversion` convierte a SVG inline cuando se necesite theme-aware coloring del wordmark (paths SVG editables, fill via CSS vars).
- **D6 — Dark mode wordmark: ✅ RESUELTA 2026-05-22 — Chris entregó `vitalia-logo-dark.png` (libélula multicolor + wordmark "VITALIA" en blanco).** Asset copiado a `vitalia/frontend/public/brand/vitalia-logo-dark.png` (~93KB) + `mockups/assets/`. En light mode usa `vitalia-logo.png` (wordmark navy `#1a1a5e` ~14:1 vs white bg WCAG AAA). En dark mode usa `vitalia-logo-dark.png` (wordmark white ~21:1 vs near-black bg WCAG AAA). Sin fallback interim necesario — D6 dependency cerrada.

**Anti-objetivos (explícito qué NO hace esta historia):**

- NO incluir `TenantSwitcher` funcional (eso es F1-S3 — esta story produce slot null drop-in compatible)
- NO incluir notificaciones bell icon (postponed Fase 2)
- NO incluir search bar global (postponed Fase 2)
- NO incluir user avatar/profile menu (postponed Fase 2 — está cubierto en Configurar tab)
- NO tocar shell layout 50/50 (eso es F1-S4)
- NO tocar route group `(shell-organism)/` (creación es F1-S9 routing-shell, F1-S2 solo introduce componentes reusables)
- NO modificar `(dashboard)/` legacy
- NO instalar Shadcn primitives nuevos (F1-S0 ya instaló los 8 base; F1-S2 solo usa Button + reusa cn helper)
- NO crear hamburger menu (D2 ratificada — no necesario con 2-3 acciones derecha)

---

## § 2 — Visión (paradigma shell-organism)

F1-S2 es el **anchor visual del shell** — la barra superior que el usuario ve siempre, presente en todas las rutas del shell-organism. Cementa la **identidad de marca Vitalia** (LogoMark con gradient brand) en el chrome principal de la app. Y deja preparado el **slot derecho** para que F1-S3 (TenantSwitcher) lo poble con el switcher real sin layout shift.

**Agente owner:** SHELL (transversal — no es de un agente específico)
**Color oficial:** brand gradient (cyan + púrpura) en LogoMark · neutral en TopBar background
**Avatar PNG:** N/A (este shell organism no representa un agente individual)

**Trazabilidad mockup integral:** `dual-mode-shell.html` (líneas 80-120 aprox) muestra TopBar en contexto. F1-S2 cementa contrato visual standalone via 2 mockups por-componente.

---

## § 3 — Atomic Design Layers (referencia Design Contract § 3)

### § 3.1 — Átomos consumidos (instalados en F1-S0)

| Átomo | Path | Cómo se usa en F1-S2 |
|---|---|---|
| `Button` | `vitalia/frontend/src/components/ui/button.tsx` | Indirecto vía `<ThemeToggle/>` (F1-S1) — F1-S2 NO usa Button directo |
| `cn` helper | `vitalia/frontend/src/lib/utils.ts` | className composition en LogoMark + TopBarGlobal |

### § 3.2 — Moléculas construidas

**N/A** — F1-S2 construye 1 átomo (LogoMark) + 1 organismo (TopBarGlobal) sin nivel intermedio molécula.

### § 3.3 — Átomos NEW

| Átomo | Path | Variantes | Props | Notas |
|---|---|---|---|---|
| `LogoMark` | `vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx` | 3 sizes × 2 variants = 6 combinations | `size?: 'sm' \| 'md' \| 'lg'` (default `'md'`) · `variant?: 'full' \| 'mark'` (default `'full'`) · `href?: string` (default `'/'`) | Server component (sin `'use client'`). Wrap `<a>` con `aria-label="Vitalia inicio"`. Renderiza Next.js `<Image>` apuntando a `/brand/vitalia-ico.png` (variant='mark') o `/brand/vitalia-logo.png` (variant='full'). Height-based sizing con `width: 'auto'` para preservar aspect ratio (mark ~1:1, full ~3:1). Dark mode swap a `/brand/vitalia-logo-dark.png` cuando asset disponible (D6 dependency) |

**Size dimensions (height-based, width auto per aspect ratio):**

| Size | Height px | Width approx (variant='mark') | Width approx (variant='full') |
|---|---|---|---|
| `sm` | 24px | ~24px (1:1) | ~72px (3:1) |
| `md` | 32px | ~32px (1:1) | ~96px (3:1) |
| `lg` | 40px | ~40px (1:1) | ~120px (3:1) |

**Implementación pattern (LogoMark.tsx):**

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
const aspectRatios = { full: 3, mark: 1 }

const assetSrc = {
  full: { light: '/brand/vitalia-logo.png', dark: '/brand/vitalia-logo-dark.png' },
  mark: { light: '/brand/vitalia-ico.png', dark: '/brand/vitalia-ico.png' }, // libélula multicolor funciona ambos modes
}

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
      {/* Dark mode asset (D6 — when available) */}
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

**Nota implementación dark mode:** doble `<Image>` con CSS `block dark:hidden` / `hidden dark:block` permite swap automático. Cuando D6 asset `vitalia-logo-dark.png` llega → drop-in. Interim si no llega para build: ambos `<Image>` apuntan al mismo `vitalia-logo.png` con CSS filter inversion (rough fallback) O forzar `variant='mark'` en dark mode wrapper (cleaner).

### § 3.3.1 — Organismos NEW

| Organismo | Path | Composición | Notas |
|---|---|---|---|
| `TopBarGlobal` | `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | `<LogoMark />` + `<div className="flex items-center gap-2"><ThemeToggle /><TenantSwitcherSlot /></div>` | Server component default. `<header role="banner">` semantic. Height fijo `h-12` (48px). `border-b border-border bg-background z-50 relative`. Padding horizontal `px-5` (20px). Responsive: en mobile <768px, LogoMark switch a `variant='mark'` vía CSS responsive class swap |

### § 3.3.2 — Placeholders NEW (drop-in para F1-S3)

| Placeholder | Path | Contenido | Notas |
|---|---|---|---|
| `TenantSwitcherSlot` | `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx` | `return null` con TODO comment | Server component default. F1-S3 reemplaza el body con `<TenantSwitcher />` real. F1-S2 deja la línea import + render en TopBarGlobal lista para drop-in sin layout shift |

### § 3.4 — Templates / Pages modificadas

| Path | Acción | Detalle |
|---|---|---|
| `vitalia/frontend/public/brand/vitalia-ico.png` | NEW | Asset libélula 500×500 transparente (copy desde `/home/chalreme/Trabajo/Vitalia/Vitalia_Ico_Transparente.png`) — ~156KB |
| `vitalia/frontend/public/brand/vitalia-logo.png` | NEW | Asset libélula+wordmark "VITALIA" navy transparente — ~107KB |
| `vitalia/frontend/public/brand/vitalia-logo-dark.png` | NEW ✓ (D6 resuelta) | Asset libélula+wordmark "VITALIA" en blanco para dark mode — entregado Chris 2026-05-22 — ~93KB |
| `vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx` | NEW | Átomo per § 3.3 (Next.js Image wrapper) |
| `vitalia/frontend/src/components/shared/shell-organism/LogoMark.test.tsx` | NEW | Vitest unit: render cada combination (3 sizes × 2 variants) + verifica aria-label + href + gradient classes |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | NEW | Organismo per § 3.3.1 |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.test.tsx` | NEW | Vitest unit: render TopBar + verifica role=banner + altura + composición children |
| `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx` | NEW | Placeholder per § 3.3.2 |
| `vitalia/frontend/src/app/layout.tsx` | MODIFY | Agregar skip link `<a href="#main-content">` antes de `{children}`. Skip link `sr-only` hasta `:focus`, ahí aparece top-left con `bg-primary text-primary-foreground` |
| `vitalia/frontend/e2e/__test-pages__/topbar-global/topbar-showcase.tsx` | NEW | Test page Playwright fixture — renderiza `<TopBarGlobal />` aislado en página completa para snapshot consistente |
| `vitalia/frontend/e2e/__test-pages__/topbar-global/logo-mark-showcase.tsx` | NEW | Test page renderiza grid 3×2 (3 sizes × 2 variants) en card neutral para snapshot 6 combinations |
| `vitalia/frontend/e2e/regression/topbar-global/topbar-interaction.spec.ts` | NEW | Playwright behavior — verifica skip link a11y (Tab + Enter focus jump) + theme toggle integration end-to-end |
| `vitalia/frontend/e2e/visual/topbar-global/topbar.spec.ts` | NEW | Playwright `@project=visual` genera 4 goldens TopBar (desktop+light · desktop+dark · mobile+light · mobile+dark) |
| `vitalia/frontend/e2e/visual/topbar-global/logo-mark.spec.ts` | NEW | Playwright `@project=visual` genera 2 goldens LogoMark (grid combinations light + dark) |
| `vitalia/frontend/e2e/a11y/topbar-global/topbar.spec.ts` | NEW | Playwright + axe-core WCAG 2.1 AA + skip link keyboard nav |
| `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-{light-desktop,dark-desktop,light-mobile,dark-mobile}.png` | NEW (×4) | TopBar goldens |
| `vitalia/frontend/e2e/__screenshots__/topbar-global/logo-mark-grid-{light,dark}.png` | NEW (×2) | LogoMark 6 combinations grid goldens |
| `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/topbar-global.html` | NEW | Mockup HTML por-componente per `vitalia/.claude/rules/shell-mockup-per-component.md` — 4 states (light+desktop · light+mobile · dark+desktop · dark+mobile) |
| `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/logo-mark.html` | NEW | Mockup HTML por-componente — grid 6 combinations (3 sizes × 2 variants) con toggle dark mode |

---

## § 4 — Reuse Map exhaustivo

### § 4.1 — REUSE desde Nicolify

**N/A — F1-S2 es greenfield Vitalia shell-organism.** Nicolify NO tiene shell-organism paradigm (dashboard tradicional sidebar+main). LogoMark + TopBarGlobal son brand-local Vitalia.

### § 4.2 — REUSE desde core/luana-core-*

**N/A — F1-S2 es 100% infra FE local.**

### § 4.3 — REUSE desde Vitalia shipped

| Asset | Path actual | Acción en F1-S2 |
|---|---|---|
| `Button` primitive (F1-S0 install) | `vitalia/frontend/src/components/ui/button.tsx` | INDIRECT reuse vía `<ThemeToggle/>` F1-S1 |
| `ThemeToggle` component (F1-S1) | `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` | **REUSE** dentro `<TopBarGlobal>` derecha |
| `cn` helper (F1-S0) | `vitalia/frontend/src/lib/utils.ts` | **REUSE** className composition |
| Agent tokens CSS vars (F1-S1) | `vitalia/frontend/src/app/globals.css` | **REUSE** vía Tailwind classes `from-agent-adrian to-agent-valeria` en LogoMark gradient |
| Shadcn-standard CSS vars (F1-S1) | `vitalia/frontend/src/app/globals.css` | **REUSE** vía Tailwind classes `bg-background border-border text-foreground` |
| `data-theme` attribute + dark mode (F1-S1) | `vitalia/frontend/src/app/layout.tsx` ThemeProvider | **REUSE** transparent — TopBarGlobal styles consume CSS vars auto-switch |

### § 4.4 — NEW (creado en esta historia)

| Artefacto NEW | Razón |
|---|---|
| `LogoMark` átomo | Identidad de marca Vitalia — no existe equivalente Shadcn ni en Vitalia shipped. 6 combinations escalable a futuros casos uso |
| `TopBarGlobal` organismo | Shell anchor — no existe equivalente. Convención brand-local |
| `TenantSwitcherSlot` placeholder | Drop-in pattern para F1-S3 sin layout shift |
| Skip link `<a href="#main-content">` | WCAG 2.4.1 Bypass Blocks compliance — no existe en shipped Vitalia |
| 5 Playwright specs + 6 goldens + 2 test pages | Visual baseline + behavior + a11y coverage |
| 2 mockups HTML per-component | Cumplimiento `vitalia/.claude/rules/shell-mockup-per-component.md` (F1-S2 sujeta) |

### § 4.5 — Legacy `/home/chalreme/Documentos/ap_sales_agent`

**N/A — F1-S2 no consulta legacy.**

---

## § 5 — API contracts (BE ↔ FE)

**N/A runtime — 100% FE local sin endpoints consumidos.**

### Build-time note

LogoMark + TopBarGlobal son server components default. Solo `ThemeToggle` (embebido) tiene `'use client'`. Render SSR-safe.

---

## § 6 — Acceptance Criteria (Gherkin AI-resistant)

> 5 scenarios funcionales activos + 1 a11y + 1 i18n + 1 responsive + 1 adversarial N/A + 1 not_applicable batch. Total: 9 entradas que satisfacen gate `/po-ux v4.1`.

### Scenario 1 — `happy-render-desktop` (type: happy)

**Given:**
- F1-S0 + F1-S1 deployed (Shadcn + tokens + ThemeToggle ready)
- Viewport desktop 1440×900
- Usuario navega a cualquier ruta shell-organism (e.g., test page `/topbar-showcase`)

**When:**
- Página carga

**Then:**
- `<header role="banner" data-testid="topbar-global">` visible top de la página
- Altura computada exacta `48px` (`h-12` = 48px)
- LogoMark izquierda: Next.js Image renderiza `vitalia-logo.png` (libélula multicolor + wordmark "VITALIA" navy) — altura 32px (md default), width auto ~96px
- ThemeToggle derecha (icon Moon visible en light)
- TenantSwitcherSlot derecha de ThemeToggle: `return null` (sin elemento visible en DOM, sin gap visual)
- `border-b border-border` bottom border visible
- `bg-background` (light → `#ffffff`, dark → near-black)
- Padding horizontal `px-5` (20px each side)
- `z-50 relative` positioning

**playwright_required:** true
**Graders:**
- E2E behavior: `vitalia/frontend/e2e/regression/topbar-global/topbar-interaction.spec.ts`
- Visual golden: `topbar-light-desktop.png`
- DOM: `expect(page.getByTestId('topbar-global')).toHaveCSS('height', '48px')`
- Composition: `expect(page.getByTestId('topbar-global').getByRole('link', { name: 'Vitalia inicio' })).toBeVisible()`

---

### Scenario 2 — `happy-render-mobile-responsive` (type: happy + responsive sub-cat mandatory)

**Given:**
- F1-S2 deployed
- Viewport mobile 375×667

**When:**
- Página carga

**Then:**
- TopBar mantiene altura 48px exacta (no se compacta verticalmente)
- LogoMark visible: switch a variant='mark' efectivo vía CSS responsive — desktop muestra `vitalia-logo.png` full · mobile <768px muestra `vitalia-ico.png` solo libélula
- Equivalente visual mobile: solo aparece la libélula multicolor (sin wordmark "VITALIA")
- ThemeToggle visible derecha
- TenantSwitcherSlot null
- NO horizontal scroll (overflow hidden o flex correctamente)
- NO hamburger menu (D2 ratificada — no necesario)
- A 320px viewport (smaller test): TopBar sigue funcionando pero NO declarado como soportado (F1-S2 declara min viewport 375px)

**playwright_required:** true
**Graders:**
- Visual golden: `topbar-light-mobile.png` (375px wide)
- DOM: `expect(page.locator('text=Vitalia')).toHaveCSS('position', 'absolute')` (sr-only pattern) OR `.not.toBeVisible()` según implementación
- Layout: `await page.setViewportSize({ width: 375, height: 667 })` + screenshot inmediato

---

### Scenario 3 — `theme-switch-applies-topbar` (type: happy + dark mode integration)

**Given:**
- F1-S2 deployed
- TopBar visible, theme actual light
- Usuario click `<ThemeToggle/>` embebido en TopBar

**When:**
- Theme cambia a dark

**Then:**
- TopBar `bg-background` cambia de `#ffffff` (light) a `hsl(240 10% 4%)` ≈ near-black (dark)
- TopBar `border-border` cambia (light → dark variant)
- LogoMark swap automático asset: `vitalia-logo.png` (light, wordmark navy) → `vitalia-logo-dark.png` (dark, wordmark white — D6 resuelta ✓)
- Libélula multicolor del icono MANTIENE colors (es brand multi-tono, funciona ambos modes — los cyan + púrpura + amarillo + verde se ven bien sobre cualquier bg)
- Wordmark "VITALIA" cambia de navy `#1a1a5e` (light) a white (dark, asset D6 ✓)
- ThemeToggle icon cambia Moon → Sun
- Visual diff golden `topbar-dark-desktop.png` < 0.1%

**playwright_required:** true
**Graders:**
- Visual golden: `topbar-dark-desktop.png`
- DOM CSS: `expect(getByTestId('topbar-global')).toHaveCSS('background-color', /rgb\(\d+,\s*\d+,\s*\d+\)/)` + compare light vs dark numerical
- Brand check: LogoMark gradient classes mantienen `from-agent-adrian to-agent-valeria` (no cambian con theme)

---

### Scenario 4 — `logo-mark-variants-grid` (type: edge — 6 combinations render correctly)

**Given:**
- F1-S2 deployed
- Test page `logo-mark-showcase.tsx` renderiza grid 3×2:
  ```
  | sm full | md full | lg full |
  | sm mark | md mark | lg mark |
  ```

**When:**
- Playwright `@project=visual` snapshot del test page en light + dark

**Then:**
- 6 combinations renderizan según size dimensions tabla § 3.3
- `size='sm' variant='full'`: vitalia-logo.png h=24px w=~72px (libélula + wordmark VITALIA pequeño)
- `size='md' variant='full'`: vitalia-logo.png h=32px w=~96px (default)
- `size='lg' variant='full'`: vitalia-logo.png h=40px w=~120px
- `size='sm' variant='mark'`: vitalia-ico.png h=24px w=24px (solo libélula 1:1)
- `size='md' variant='mark'`: vitalia-ico.png h=32px w=32px
- `size='lg' variant='mark'`: vitalia-ico.png h=40px w=40px
- Libélula multicolor preservada (cyan + púrpura + magenta + amarillo + verde lima)
- Wordmark "VITALIA" navy `#1a1a5e` en light · white en dark (D6 asset ✓)
- Visual diff golden `logo-mark-grid-light.png` + `logo-mark-grid-dark.png` < 0.1%

**playwright_required:** true
**Graders:**
- Visual goldens: `logo-mark-grid-light.png` + `logo-mark-grid-dark.png`
- Vitest unit: `LogoMark.test.tsx` renderiza cada combination con expected classes asserted

---

### Scenario 5 — `accessibility-skip-link` (type: accessibility WCAG 2.4.1 — sub-categoría mandatory)

**Given:**
- F1-S2 deployed (skip link agregado en `app/layout.tsx`)
- Usuario en shell-organism route con TopBar + main content visible

**When:**
- Usuario press `Tab` desde el body root (primer Tab event)

**Then:**
- Skip link "Saltar al contenido" aparece visible top-left de la página
- Skip link tiene `focus:not-sr-only` (visible solo al focus)
- Styling: `focus:absolute focus:top-0 focus:left-0 focus:z-[200] focus:p-2 focus:bg-primary focus:text-primary-foreground`
- Contrast ratio del skip link ≥ 4.5:1 (text WCAG AA)
- Press `Enter` → focus jumps to `#main-content` (URL fragment update + scroll si necesario)
- Press `Tab` segunda vez → focus pasa al siguiente elemento (LogoMark `<a>`)
- Press `Shift+Tab` desde LogoMark → vuelve al skip link (re-aparece)
- axe-core scan: 0 violations

**playwright_required:** true
**Graders:**
- E2E behavior + a11y: `vitalia/frontend/e2e/a11y/topbar-global/topbar.spec.ts`
- Keyboard: `await page.keyboard.press('Tab')` + assert skip link focused
- Focus check: `expect(page.locator('[href="#main-content"]')).toBeFocused()`
- Jump: press Enter + assert `page.url()` ends with `#main-content`
- axe: `injectAxe()` + `checkA11y()` ruleset WCAG 2.1 AA

---

### Scenario 6 — `accessibility-banner-landmark` (type: accessibility — semantic HTML)

**Given:**
- F1-S2 deployed
- Screen reader simulation (Playwright axe + manual VoiceOver test)

**When:**
- Accessibility tree inspect

**Then:**
- `<header role="banner">` correctly identified as landmark
- LogoMark `<a aria-label="Vitalia inicio">` exposed as link with name "Vitalia inicio"
- ThemeToggle button exposed con aria-label dinámico (cubierto F1-S1)
- TenantSwitcherSlot null → no elemento expuesto al accessibility tree (clean)
- Skip link exposed con name "Saltar al contenido"
- Tab order lógico: skip link → LogoMark link → ThemeToggle → main content (post-skip)
- NO violations axe WCAG 2.1 AA

**playwright_required:** true
**Graders:**
- axe scan strict ruleset
- Manual cross-check Chris con VoiceOver (Mac) o NVDA (Win) post-implementación (NO blocking automated, pero anotado en T-result.md)

---

### Scenario 7 — `i18n-microcopy` (type: i18n Spanish neutro — sub-categoría mandatory)

**Given:**
- F1-S2 deployed con strings user-facing: "Vitalia" (brand name) · "Vitalia inicio" (aria-label LogoMark) · "Saltar al contenido" (skip link text)

**When:**
- Code review + grep voseo + Playwright assertion

**Then:**
- NO voseo (`vos/sos/tenés/podés/saltá/dale`)
- NO léxico regional (`laburo`, `quilombo`, etc.)
- Tildes correctas ("Saltar" sin tilde extraña, "contenido" sin tilde)
- "Vitalia" brand name mantiene capitalización exacta
- Spanish neutro LatAm validation programática:
  - `expect(linkAriaLabel).toBe('Vitalia inicio')`
  - `expect(skipLinkText).toBe('Saltar al contenido')`
- pre-commit hook scan voseo green sobre LogoMark.tsx + TopBarGlobal.tsx + layout.tsx changes

**playwright_required:** true
**Graders:**
- E2E aria-label assertion
- Vitest snapshot strings
- Pre-commit voseo scan auto

---

### Scenario 8 — `adversarial` (type: not_applicable con razón rigurosa)

**adversarial: not_applicable**

**Razón:** F1-S2 TopBar + LogoMark son componentes puramente presentacionales server-side render sin user input, sin auth surface, sin PHI, sin fetch API. El `<a href="/">` en LogoMark es link estático a root tenant URL (no toma user-controlled URL). Skip link `<a href="#main-content">` es URL fragment estática. Vectores adversarial teóricos:

- XSS via brand name "Vitalia" → es string hardcoded en source, no user input
- Open redirect via LogoMark href → es link estático `/`, no parameterized
- Clickjacking → no aplica (TopBar es chrome de la propia app, no embebida en iframes externos)

Si futuro evolution: LogoMark recibe tenant logo URL dinámico (multi-tenant white-label) → spawn scenario adversarial dedicado en story dedicada.

---

### Scenario 9 — `not_applicable batch` (sub-categorías mandatory que no aplican)

```yaml
not_applicable_sub_categories:
  - sub_category: race_condition
    reason: "F1-S2 no introduce endpoints DB con create/update ni unique constraints. Componentes puramente presentacionales."
  - sub_category: concurrent_users
    reason: "F1-S2 no introduce list/detail multi-user. TopBar es chrome estático per-usuario."
  - sub_category: network_failure
    reason: "F1-S2 zero fetch FE runtime. LogoMark + TopBarGlobal son SSR estáticos. ThemeToggle (F1-S1) tampoco tiene fetch."
  - sub_category: empty_state
    reason: "F1-S2 no introduce list/dashboard. TopBar siempre renderiza (no empty state posible)."
  - sub_category: large_dataset
    reason: "F1-S2 no introduce data fetching ni pagination. Componentes estáticos."
  - sub_category: loading-state
    reason: "F1-S2 es SSR síncrono. Sin async ni loading states. ThemeToggle hydration es cubierto en F1-S1 Scenario 3."
```

---

## § 7 — Visual Goldens (mockup como source of truth)

### § 7.1 — 6 snapshots requeridos

| # | Snapshot | Viewport | Theme | Propósito | Path golden |
|---|---|---|---|---|---|
| 1 | `topbar-light-desktop` | 1440×900 | light | TopBar desktop con LogoMark full (mark+texto) + ThemeToggle Moon | `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-light-desktop.png` |
| 2 | `topbar-dark-desktop` | 1440×900 | dark | Idem dark mode (LogoMark gradient mantiene) | `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-dark-desktop.png` |
| 3 | `topbar-light-mobile` | 375×667 | light | TopBar mobile con LogoMark solo cuadrado V (texto sr-only) | `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-light-mobile.png` |
| 4 | `topbar-dark-mobile` | 375×667 | dark | Idem mobile dark | `vitalia/frontend/e2e/__screenshots__/topbar-global/topbar-dark-mobile.png` |
| 5 | `logo-mark-grid-light` | 800×400 | light | Grid 3×2 (3 sizes × 2 variants) en card neutral | `vitalia/frontend/e2e/__screenshots__/topbar-global/logo-mark-grid-light.png` |
| 6 | `logo-mark-grid-dark` | 800×400 | dark | Idem dark mode | `vitalia/frontend/e2e/__screenshots__/topbar-global/logo-mark-grid-dark.png` |

### § 7.2 — Trazabilidad mockup → golden → componente

| Mockup ref | Golden path | Componente verificado | Design Contract ref |
|---|---|---|---|
| `mockups/topbar-global.html` (4 states) | `topbar-{light,dark}-{desktop,mobile}.png` (×4) | `TopBarGlobal.tsx` | § 3.3.1 TopBarGlobal + § 4 ShellTemplate |
| `mockups/logo-mark.html` (6 combinations) | `logo-mark-grid-{light,dark}.png` (×2) | `LogoMark.tsx` | § 3.1 LogoMark átomo + § 5.1 agent tokens |

### § 7.3 — Test pages auxiliares (Playwright fixtures)

**Path:** `vitalia/frontend/e2e/__test-pages__/topbar-global/`

```
__test-pages__/topbar-global/
├── topbar-showcase.tsx              # Renderiza <TopBarGlobal/> en página full con dummy main content
└── logo-mark-showcase.tsx           # Renderiza grid 3×2 de LogoMark en card centrada
```

### § 7.4 — Mockups HTML per-component (gate visual bloqueante)

**Paths:**
1. `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/topbar-global.html`
2. `vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups/logo-mark.html`

**Contenido obligatorio (D4 ratificada — mockups separados):**

**`topbar-global.html`:**
- Tailwind CDN + CSS vars Vitalia inline
- 4 states side-by-side o tabbed:
  1. Light + desktop (1440px width simulada)
  2. Light + mobile (375px width simulada)
  3. Dark + desktop
  4. Dark + mobile
- TopBar real con LogoMark + ThemeToggle (visual placeholder, sin JS funcional) + TenantSwitcherSlot null (gap puro)
- Below TopBar: dummy main content area mostrando "F1-S2 TopBar mockup · main content placeholder"
- Spanish neutro labels
- Skip link visible en focus state (simulated)

**`logo-mark.html`:**
- Grid 3×2 (3 sizes columns × 2 variants rows): sm-full, md-full, lg-full, sm-mark, md-mark, lg-mark
- Label inferior cada cell: "sm · full", "md · full" (default), "lg · full", "sm · mark", "md · mark", "lg · mark"
- Toggle dark mode (button top-right)
- Tablas contrato técnico inline (props + dimensions verbatim § 3.3)

**Workflow ratificación Chris:**
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase1-topbar-global/mockups
python3 -m http.server 8888
# http://localhost:8888/topbar-global.html
# http://localhost:8888/logo-mark.html
```

### § 7.5 — Generación inicial vs verify

```bash
cd ${WS}/vitalia/frontend
npx playwright test --project=visual --grep "topbar-global" --update-snapshots
# Chris ratify visual diff humano antes commit goldens

# Verify CI auto en PRs FE:
npx playwright test --project=visual --grep "topbar-global"
```

### § 7.6 — Tolerancia (Design Contract § 9.4)

- `maxDiffPixelRatio: 0.001`
- `animations: 'disabled'`
- `caret: 'hide'`

---

## § 8 — Acceptance criteria operacionales

| # | Criterio | Verificación |
|---|---|---|
| AC-1 | `LogoMark.tsx` existe con 3 sizes × 2 variants = 6 combinations | File + Vitest unit cada combination |
| AC-2 | LogoMark renderiza assets PNG correctos: light=`vitalia-logo.png` (variant=full) o `vitalia-ico.png` (variant=mark) · dark=`vitalia-logo-dark.png` o mantiene `vitalia-ico.png` | Visual golden + Next.js Image src assertion |
| AC-2b | Assets `public/brand/vitalia-{ico,logo,logo-dark}.png` existen + committed | File existence |
| AC-3 | LogoMark default props: `size='md'`, `variant='full'` | Vitest unit default render |
| AC-4 | LogoMark `<a aria-label="Vitalia inicio" href="/">` semantic + accessible | E2E aria assertion |
| AC-5 | `TopBarGlobal.tsx` existe con `<header role="banner" data-testid="topbar-global">` | File + E2E DOM |
| AC-6 | TopBar altura computada exacta `48px` (h-12) | E2E CSS height assertion |
| AC-7 | TopBar composición correcta: LogoMark izq + (ThemeToggle + TenantSwitcherSlot) der | E2E composition check |
| AC-8 | `TenantSwitcherSlot.tsx` existe + retorna null + TODO comment apunta F1-S3 | File + grep |
| AC-9 | Mobile responsive 375px: texto "Vitalia" sr-only via @media | Visual golden mobile + CSS check |
| AC-10 | Skip link `<a href="#main-content">Saltar al contenido</a>` agregado en layout.tsx | grep + Scenario 5 E2E |
| AC-11 | Skip link `sr-only focus:not-sr-only` visible solo al focus | Scenario 5 E2E keyboard |
| AC-12 | Skip link `focus:bg-primary focus:text-primary-foreground` contrast ≥ 4.5:1 | axe ruleset |
| AC-13 | Light + Dark mode ambos renderizan TopBar correctamente (LogoMark gradient mantiene brand) | Visual goldens × 4 |
| AC-14 | `npx tsc --noEmit` 0 errors | Shell exit 0 |
| AC-15 | `npx eslint src/` 0 errors | Shell exit 0 |
| AC-16 | `npm run build` PASS | Shell exit 0 |
| AC-17 | Mockup HTML `mockups/topbar-global.html` (4 states) existe + ratificado Chris | File + frontmatter `ratified_visual_by_chris: true` |
| AC-18 | Mockup HTML `mockups/logo-mark.html` (6 combinations) existe + ratificado Chris | File + frontmatter ratify |
| AC-19 | a11y axe scan TopBar + skip link 0 violations | Scenario 5 + 6 grader |
| AC-20 | Goldens regression F1-S0 + F1-S1 siguen GREEN (TopBar es additive, no rompe nada shipped) | Visual diff |
| AC-21 | Spanish neutro: "Vitalia inicio" + "Saltar al contenido" NO voseo | Pre-commit scan + E2E assertion |
| AC-22 | NO `.vt-*` classes en código nuevo (arch fitness heredado F1-S0) | Arch test green |

---

## § 9 — Zero deuda técnica — checklist mandatorio

- [ ] **Lint:** `npx eslint src/` --max-warnings 0
- [ ] **TypeScript:** `npx tsc --noEmit` 0 errors
- [ ] **Format:** `npx prettier --check vitalia/frontend/src/components/shared/shell-organism/`
- [ ] **Vitest tests:** LogoMark.test.tsx + TopBarGlobal.test.tsx + existing regression PASS
- [ ] **Playwright behavior E2E:** Scenarios 1, 2, 3 pass + Scenario 5 a11y pass + Scenario 7 i18n pass
- [ ] **Playwright visual goldens:** 6 baselines generados + Chris ratify
- [ ] **NO `.vt-*` classes en código nuevo:** arch test green
- [ ] **NO `any` TypeScript** en código nuevo
- [ ] **NO default exports** en código nuevo (LogoMark + TopBarGlobal + TenantSwitcherSlot todos named exports)
- [ ] **NO cross-feature imports** (boundaries pass)
- [ ] **NO cross-brand imports**
- [ ] **NO core engine direct edits** (F1-S2 NO toca core/luana-core-*)
- [ ] **CSS vars consumidas** (NO hex hardcoded en componentes)
- [ ] **Spanish neutro LatAm:** aria-label + brand name + skip link
- [ ] **Build production:** `npm run build` exit 0
- [ ] **Storybook story:** N/A (consistencia con F1-S0 + F1-S1 ratificadas — Storybook stack diferido)
- [ ] **Mobile responsive:** Scenario 2 verificado a 375px
- [ ] **Dark mode:** Scenario 3 + visual goldens dark mode pass
- [ ] **HIPAA-lite no-phi-scope declared:** F1-S2 es UI chrome shell sin PHI
- [ ] **`ratified_visual_by_chris: true`** post 2 mockups ratify (topbar-global.html + logo-mark.html)
- [ ] **`ratified_visual_mockups`** lista contiene 2 paths
- [ ] **`ratified_visual_iter`** = iter number final ratificación

---

## § 10 — Dependencies map

### § 10.1 — Dependencies hard

```
F1-S2 depende hard de:
  - F1-S0 (Shadcn install + tokens base + tailwind extend + utils.ts cn)
  - F1-S1 (next-themes + ThemeToggle component + Shadcn vars completas + tailwind colors mapping)

Razón concreta:
  - LogoMark gradient consume `bg-gradient-to-br from-agent-adrian to-agent-valeria` → require agent tokens F1-S1
  - TopBarGlobal embebe `<ThemeToggle />` → require F1-S1 component shipped
  - Dark mode test requires F1-S1 ThemeProvider integrated
```

### § 10.2 — Dependencies soft

```
N/A
```

### § 10.3 — Service blockers BE

```
N/A — F1-S2 100% FE.
```

### § 10.4 — Esta historia bloquea (downstream)

```
F1-S2 desbloquea HARD 1 story directa:
  - vitalia-fase1-shell-layout-5050 (F1-S4 — incluye TopBar en layout)

Y desbloquea SOFT (preparan slot):
  - vitalia-fase1-tenant-switcher (F1-S3 — reemplaza TenantSwitcherSlot null con real component, drop-in)
```

---

## § 11 — Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Mobile responsive layout break** a viewport extremo (<375px) | Baja | Bajo | Scenario 2 declara 375px como min viewport soportado. F1-S2 no certifica 320px. Si user reporta → story dedicada futura |
| **LogoMark assets PNG no committed o broken paths** | Baja | Alto | Pre-commit verify `public/brand/*.png` exist. CI golden generation falla si missing. AC-2b file existence catch |
| ~~`vitalia-logo-dark.png` asset NO entregado~~ | ~~RESUELTA~~ | ~~RESUELTA~~ | ✓ Chris entregó asset 2026-05-22. D6 cerrada. Sin fallback necesario |
| **Next.js Image optimization rompe (CDN config / static export)** | Baja | Medio | Test page `topbar-showcase.tsx` verifica render. Production build `npm run build` catchea config issues |
| **Skip link no aparece al Tab** (CSS focus selector roto) | Baja | Alto (a11y violation) | Scenario 5 E2E keyboard nav verifica explícito |
| **TenantSwitcherSlot null causa layout shift cuando F1-S3 monta real component** | Baja | Bajo | Drop-in pattern explícito — F1-S3 reemplaza la línea import + render, layout matemáticamente idéntico si dimensions del componente real son razonables. Mitigación: en F1-S3 spec se cementa max-width del TenantSwitcher real para que no rompa layout |
| **Agent tokens (`agent-adrian`, `agent-valeria`) no resuelvan en build** | Baja | Alto | F1-S1 cementó CSS vars completas + tailwind config. F1-S2 reusa. Si rompe → indicates F1-S1 incompleto y se rollback |
| **Skip link causa duplicate tab key event en algunos browsers** | Baja | Bajo | next.js + React 19 manejan Tab correctamente. Si flaky → spec con retry |

---

## § 12 — Definición de "Done"

F1-S2 transitions `developing → developed` cuando:

1. **AC-1..AC-22 del § 8 verificados**
2. **Checklist § 9 ✓ aplicables**
3. **6 visual goldens generados + Chris ratify**
4. **7 Gherkin scenarios funcionales (1-7) pass** + Scenario 8 adversarial N/A + Scenario 9 batch N/A documentado
5. **2 mockups HTML ratificados Chris** (`topbar-global.html` + `logo-mark.html`)
6. **Arch fitness tests heredados F1-S0 siguen GREEN**
7. **Story commits pushed** + branch `wip/vitalia` sync con main
8. **`T-{n}-result.md`** con SHA + log decisiones implementación
9. **Handoff `/auditor`** auto-emitido (story closure gate)

Auditor APPROVED → `/pm-vitalia merge` → state `done` → F1-S4 unblocked.

---

## § 13 — Referencias

### SSoT obligatorios citados

- **Design Contract** atomic design: `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 3.1 (átomos) + § 3.3 (organismos) + § 5 (tokens)
- **Predecessor F1-S0**: `vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md`
- **Predecessor F1-S1**: `vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/01-spec.md`
- **Mockup integral SSoT**: `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html`
- **Template spec SHELL**: `vitalia/docs/specs/templates/01-spec-shell-template.md`

### Reglas raíz aplicables

- **FSD-Lite**: `.claude/rules/frontend-fsd.md` (LogoMark + TopBarGlobal + TenantSwitcherSlot bajo `components/shared/shell-organism/`)
- **HIPAA-lite overlay**: `vitalia/.claude/rules/hipaa-lite.md` — **no-phi-scope declared**
- **Spanish neutro**: `.claude/rules/spanish-text.md`
- **Brand docs schema R1+R2+R3**: `.claude/rules/brand-docs-schema.md`
- **Story closure gate**: `.claude/rules/story-closure-gate.md`
- **Shell mockup-per-component**: `vitalia/.claude/rules/shell-mockup-per-component.md` (F1-S2 SUJETA — 2 mockups requeridos)

### § 13.1 — Protocolo mockup-per-component (APLICA)

F1-S2 SUJETA. 2 mockups HTML obligatorios pre-refined:
1. `mockups/topbar-global.html` (4 states light/dark × desktop/mobile)
2. `mockups/logo-mark.html` (6 combinations 3 sizes × 2 variants + dark toggle)

### § 13.2 — Compliance scope (no-phi-scope declared)

F1-S2 chrome shell sin PHI. Salvaguardas HIPAA-lite no aplican.

---

## § 14 — Changelog spec

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-22 | Draft inicial `/po-ux`. 4 decisiones G6 batched Chris D1-D4: LogoMark 6 combinations, mobile responsive @media, TenantSwitcherSlot null, mockups separados. 9 Gherkin scenarios (responsive + a11y + i18n covered, race/concurrent/network/empty/large/loading N/A). 2 mockups HTML pendientes generación. |
| 1.1 | 2026-05-22 | **REWORK significativo post Chris envió assets reales brand** (`Vitalia_Ico_Transparente.png` libélula multicolor + `Vitalia_Logo_Transparente.png` libélula+wordmark VITALIA navy). LogoMark deja de ser "cuadrado gradient + V" (placeholder asumido) y pasa a wrappear PNG assets via Next.js Image. Sizes ahora height-based (24/32/40px) con width auto preservando aspect ratio (mark 1:1, full 3:1). 2 decisiones nuevas D5+D6: D5 PNG via Next.js Image ahora + roadmap SVG futuro (story dedicada), D6 dark mode requires `vitalia-logo-dark.png` asset PENDING Chris entrega. Assets copiados a `public/brand/` + `mockups/assets/`. AC-2 reformulado, AC-2b NEW. Riesgos § 11 ampliados. |
| 1.2 | 2026-05-22 | **D6 ✓ RESUELTA.** Chris entregó `Vitalia_Logo_fondo_oscuro.png` (libélula multicolor + wordmark VITALIA white). Asset copiado a `vitalia/frontend/public/brand/vitalia-logo-dark.png` (~93KB) + mockups. Spec § Decisiones, § Deliverables, § Riesgos, § Scenarios actualizados (drop fallback interim, drop dependency abierta). Mockup `topbar-global.html` State 3 dark desktop ahora usa asset real (eliminado filter CSS placeholder). Mockup `logo-mark.html` celdas variant='full' dark mode swap a asset real via CSS rules. 2 mockups HTML LISTOS para Chris ratify visual. F1-S2 sin dependencies abiertas. |
