<!-- voseo-allowed: internal architecture documentation, FE-only story -->

---
brand: vitalia
story_id: vitalia-fase1-design-tokens-theme
state: ready
depends_on:
  - vitalia-fase1-stack-stability
blocks_hard:
  - vitalia-fase1-topbar-global
  - vitalia-fase1-shell-layout-5050
  - vitalia-fase1-valeria-rail-history
  - vitalia-fase1-ribbon-6-tabs
target_version: v1.0
written_at: 2026-05-22
sub_architect: /architect (single-shot full-stack — FE-only story)
arch_version: 1
links:
  spec: "01-spec.md"
  design_contract: "../../../architecture/SHELL-DESIGN-CONTRACT.md"
  predecessor_arch: "../vitalia-fase1-stack-stability/03-arch.md"
  rule_shell_mockup: "../../../../.claude/rules/shell-mockup-per-component.md"
  rule_hipaa: "../../../../.claude/rules/hipaa-lite.md"
  rule_fsd: "../../../../../.claude/rules/frontend-fsd.md"
  mockup_ratified: "mockups/theme-toggle.html"
---

# F1-S1 `vitalia-fase1-design-tokens-theme` — 03-arch

## § 0 — Context summary

- **PR / story:** F1-S1 `vitalia-fase1-design-tokens-theme`
- **Architect run on:** 2026-05-22
- **Brand:** vitalia (overlay HIPAA-lite — no-phi-scope declared, infra UI shell only)
- **Type:** ui-story (FE-only)
- **Modules touched:** `vitalia/frontend/` exclusively (NO backend, NO agentic, NO engine)
- **CONTEXT-BRIEF source:** spec 01-spec.md ratified (state=refined) + mockup theme-toggle.html ratified (4 states card neutral) + 5 decisiones D1-D5 cementadas Chris. NO Haiku context-builder brief (story autocontenida con SSoT vivo en 01-spec.md).

### § 0.1 — Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/app/{layout.tsx, globals.css}` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/tailwind.config.ts` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/{regression,visual,a11y,__test-pages__,__screenshots__}/design-tokens-theme/` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/tokens/` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| BE surface | N/A — story FE-only, sin endpoints | N/A |
| AGENTIC surface | N/A — sin LangGraph state, sin tools, sin prompts | N/A |

Zero Opus tickets. Story es FE no-agentic — Sonnet ejecuta todo T-1..T-7 contra validators.

### § 0.2 — Skills consultados

- `frontend-expert` (FSD-Lite boundaries, Tailwind tokens, Shadcn reuse) — confirmado ThemeToggle vive en `components/shared/shell-organism/` (path FSD válido)
- `playwright-expert` (POM patterns, @project=visual config heredado F1-S0, axe-core a11y, anti-Docker mandate) — confirmado specs nuevas reusan config heredada sin tocar
- `tessl__shadcn-ui` (Button ghost icon variant patterns) — Button primitive instalado F1-S0, reuse via `<Button variant="ghost" size="icon">`
- `tessl__tailwind` (darkMode config Tailwind v4) — confirmado `darkMode: ['class', '[data-theme="dark"]']` honra next-themes `attribute="data-theme"` (D4)
- `tessl__vitest` (unit test patterns ThemeToggle.test.tsx)
- `tessl__nextjs-app-router-modularization` (layout.tsx wrap pattern, `suppressHydrationWarning` requirement)
- Rule overlay `vitalia/.claude/rules/shell-mockup-per-component.md` — APLICA, mockup ratificado pre-architect
- Rule overlay `vitalia/.claude/rules/hipaa-lite.md` — CONSUME (no-phi-scope declared, F1-S1 es UI shell sin PHI)
- Rule root `.claude/rules/anti-duplication.md` — confirmado NO mirror cross-brand (ThemeToggle es vitalia-local, no candidate de lift a core post-MVP)
- Rule root `.claude/rules/frontend-fsd.md` — confirmado FSD-Lite boundaries pass (components/shared/shell-organism/ está dentro de `shared`)

### § 0.3 — Capability YAML files affected

Post-merge `/pm-vitalia` actualiza:

- `vitalia/docs/product/capabilities/shell-organism/design-tokens-theme.yaml` — NEW (status: planned → live post-merge) con `verification.commands` (npm run build + vitest + Playwright @project=visual goldens) + `verification.gherkin_evidence` (8 scenarios → tests map).
- `vitalia/docs/product/modules/shell-organism.md` — UPDATE auto-list incluye `design-tokens-theme` post-merge (R32 reconcile_capabilities).

### § 0.4 — Architecture gates que deben pasar

- `vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts` (heredado F1-S0) — debe seguir GREEN. ThemeToggle.tsx NO usa `.vt-*`.
- `vitalia/frontend/src/__tests__/architecture/test-page-padding.test.ts` (heredado) — N/A para ThemeToggle (no es page).
- FSD-Lite boundaries ESLint rule — `components/shared/shell-organism/` permitido import desde `@/components/ui/button` + npm deps.
- Vitest no `any` TypeScript / no default exports — enforced via ESLint rules existentes.

---

## § 1 — Surfaces involved

### § 1.1 — FE (THIS STORY — 100% scope)

| Surface | Path | Action |
|---|---|---|
| npm dep | `vitalia/frontend/package.json` + `package-lock.json` | MODIFY (+next-themes ^0.3.0) |
| Global tokens CSS | `vitalia/frontend/src/app/globals.css` | MODIFY (completar Shadcn vars verbatim Design Contract § 5.1) |
| Tailwind config | `vitalia/frontend/tailwind.config.ts` | MODIFY (verify/complete extend + `darkMode` config) |
| Root layout | `vitalia/frontend/src/app/layout.tsx` | MODIFY (wrap ThemeProvider + `suppressHydrationWarning`) |
| ThemeToggle component | `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` | NEW (client component) |
| ThemeToggle unit | `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.test.tsx` | NEW (vitest) |
| Test page fixture | `vitalia/frontend/e2e/__test-pages__/design-tokens-theme/theme-toggle-showcase.tsx` | NEW |
| E2E behavior | `vitalia/frontend/e2e/regression/design-tokens-theme/theme-toggle-interaction.spec.ts` | NEW (Playwright behavior) |
| E2E visual | `vitalia/frontend/e2e/visual/design-tokens-theme/theme-toggle.spec.ts` | NEW (Playwright @project=visual) |
| E2E a11y | `vitalia/frontend/e2e/a11y/design-tokens-theme/theme-toggle.spec.ts` | NEW (Playwright + axe-core) |
| Visual goldens | `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-{light,dark}.png` | NEW (×2) |
| Vars introspection | `vitalia/frontend/src/__tests__/tokens/test-shadcn-vars-resolvable.test.ts` | NEW (vitest introspection) |

### § 1.2 — BE — N/A

Story es 100% FE local. **NO endpoints, NO services, NO DTOs, NO migrations, NO arch fitness backend.** Zero `vitalia/backend/` touch.

### § 1.3 — AGENTIC — N/A

**NO LangGraph state, NO tools, NO prompts, NO subagents, NO evals.** Story es infra UI shell — no agentic surface. R23 `production_code: true → Opus` NO aplica porque NO hay agentic production code.

### § 1.4 — Engine — N/A

Story NO toca `core/luana-core-*/`. NO promotion proposal required.

### § 1.5 — Brand isolation

NO touches `nicolify/`, `comunify/`, `lupulo/` ni cualquier futura brand. ThemeToggle es vitalia-local — `next-themes` se instala únicamente en `vitalia/frontend/`. Cross-brand mirror scan: vacío (ThemeToggle no existe en otras brands; Nicolify dashboard es light-only por design decision Q3 2025 documentado en 01-spec.md § 4.1).

---

## § 2 — FE architecture detail

### § 2.1 — next-themes integration pattern

**npm install:**

```bash
cd vitalia/frontend
npm install next-themes
# Resuelve ^0.3.x latest stable React 19 compat (Q4 2025 release)
# Lockfile diff committed para reproducibilidad
```

**Workaround peer-dep React 19** (fallback si npm install falla):

```bash
npm install next-themes --legacy-peer-deps
```

**ThemeProvider props verbatim** (D1+D4 ratificadas Chris 2026-05-22):

```tsx
<ThemeProvider
  attribute="data-theme"      // ★ data-theme attribute, NOT class="dark"
  defaultTheme="light"          // ★ light default (D1)
  enableSystem={false}          // ★ NO OS system theme (D1 — scope minimal F1)
  storageKey="vitalia-theme"    // ★ namespaced (D4 defense-in-depth multi-brand)
>
  {children}
</ThemeProvider>
```

### § 2.2 — layout.tsx wrap pattern

Path: `vitalia/frontend/src/app/layout.tsx`

```tsx
import { ThemeProvider } from 'next-themes'
import './globals.css'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="data-theme"
          defaultTheme="light"
          enableSystem={false}
          storageKey="vitalia-theme"
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**`suppressHydrationWarning` REQUIRED** en `<html>` por next-themes. Sin esto:
- React emite `Warning: Prop className did not match. Server: '...' Client: '...'` durante hydration (next-themes inyecta `data-theme` inline `<head>` script ANTES de React hydrate, generando legitimate mismatch SSR vs client).
- Scenario 3 (`01-spec.md` § 6) atrapa esto vía `page.on('pageerror')` + build production failure.

### § 2.3 — ThemeToggle.tsx component

Path: `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx`

```tsx
'use client'

import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'
import { Moon, Sun } from 'lucide-react'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={`Cambiar tema (actual: ${isDark ? 'oscuro' : 'claro'})`}
      aria-pressed={isDark}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      data-testid="theme-toggle"
    >
      {isDark ? <Sun className="h-[1.2rem] w-[1.2rem]" /> : <Moon className="h-[1.2rem] w-[1.2rem]" />}
      <span className="sr-only">Cambiar tema</span>
    </Button>
  )
}
```

**Anclas técnicas verbatim:**

- **`'use client'` directive** — useTheme hook requiere React hooks runtime (no server component).
- **`import { useTheme } from 'next-themes'`** directo — **NO** wrapper `src/hooks/useTheme.ts` (D5 ratificada).
- **`import { Button } from '@/components/ui/button'`** — reuse Shadcn primitive instalado en F1-S0.
- **`import { Moon, Sun } from 'lucide-react'`** — lucide-react ya instalado vía Shadcn deps F1-S0.
- **`export function ThemeToggle()`** — **named export** (NO `export default`) — FSD-Lite enforce, ESLint rule `no-default-export` activa.
- **NO props** — componente self-contained, lee/escribe theme via useTheme hook.
- **`data-testid="theme-toggle"`** — Playwright selector estable (no depende de className/role drift).
- **`aria-label` dinámico Spanish neutro** — `"Cambiar tema (actual: claro)"` / `"Cambiar tema (actual: oscuro)"`. NO voseo (`.claude/rules/spanish-text.md`).
- **`aria-pressed` boolean** — toggle button semantic per ARIA spec.
- **Conditional icon Moon/Sun** — Moon visible cuando theme es light (sugiere "switch to dark"); Sun visible cuando dark (sugiere "switch to light").
- **`<span className="sr-only">`** — screen-reader fallback adicional (defense-in-depth a11y).
- **NO hex hardcoded** — Button ghost icon ya consume tokens vía Shadcn primitive.

### § 2.4 — globals.css completion verbatim Design Contract § 5.1

Path: `vitalia/frontend/src/app/globals.css`

**Estructura:**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* === Surface (Shadcn standard) === */
    --background: 0 0% 100%;
    --foreground: 240 10% 4%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 4%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 4%;

    /* === Primary (Vitalia cyan = Adrián) === */
    --primary: 198 99% 49%;
    --primary-foreground: 0 0% 100%;

    /* === Secondary === */
    --secondary: 240 5% 96%;
    --secondary-foreground: 240 6% 10%;

    /* === Muted === */
    --muted: 240 5% 96%;
    --muted-foreground: 240 4% 46%;

    /* === Accent (Vitalia purpura = Valeria) === */
    --accent: 287 53% 37%;
    --accent-foreground: 0 0% 100%;

    /* === Destructive === */
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 98%;

    /* === Border + input + ring === */
    --border: 240 6% 90%;
    --input: 240 6% 90%;
    --ring: 198 99% 49%;

    /* === Radius === */
    --radius: 0.625rem;

    /* === Agent tokens (vitalia-specific NEW) === */
    --agent-lisa: 156 100% 41%;
    --agent-lisa-soft: 156 80% 92%;
    --agent-lucas: 0 0% 7%;
    --agent-lucas-soft: 0 0% 92%;
    --agent-adrian: 198 99% 49%;
    --agent-adrian-soft: 197 90% 89%;
    --agent-valeria: 287 53% 37%;
    --agent-valeria-soft: 287 53% 90%;
    --agent-camila: 244 84% 32%;
    --agent-camila-soft: 244 53% 92%;
    --agent-mateo: 53 99% 51%;
    --agent-config: 240 4% 46%;
  }

  .dark {
    --background: 240 10% 4%;
    --foreground: 0 0% 98%;
    --card: 240 8% 8%;
    --card-foreground: 0 0% 98%;
    --popover: 240 8% 8%;
    --popover-foreground: 0 0% 98%;

    --primary: 198 99% 49%;
    --primary-foreground: 240 10% 4%;

    --secondary: 240 4% 16%;
    --secondary-foreground: 0 0% 98%;

    --muted: 240 4% 16%;
    --muted-foreground: 240 5% 65%;

    --accent: 287 53% 50%;
    --accent-foreground: 0 0% 98%;

    --destructive: 0 63% 31%;
    --destructive-foreground: 0 0% 98%;

    --border: 240 4% 20%;
    --input: 240 4% 20%;
    --ring: 198 99% 49%;

    /* Agent tokens dark variants */
    --agent-lisa-soft: 156 60% 15%;
    --agent-lucas-soft: 0 0% 20%;
    --agent-adrian-soft: 198 60% 20%;
    --agent-valeria-soft: 287 40% 25%;
    --agent-camila-soft: 244 50% 20%;
  }
}

/* === LEGACY .vt-* BLOCK — PRESERVAR INTACTO (no tocar) === */
/* Bloque .vt-bg-*, .vt-text-*, .vt-border-* etc instalado en seed legacy. */
/* Tiene colores hardcoded, NO depende de CSS vars Shadcn-standard. */
/* Deprecación final = story F2-S23 vitalia-fase2-vt-deprecation-final */
```

**F1-S0 instaló base parcial.** F1-S1 cementa **TODO** verbatim Design Contract § 5.1. Detección automática post-completion via vitest introspection (`test-shadcn-vars-resolvable.test.ts`).

### § 2.5 — tailwind.config.ts verify/extend

Path: `vitalia/frontend/tailwind.config.ts`

**Anclas técnicas:**

```ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class', '[data-theme="dark"]'],     // ★ honra next-themes attribute="data-theme" (D4)
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        // Agent tokens (heredado F1-S0)
        agent: {
          lisa: 'hsl(var(--agent-lisa))',
          'lisa-soft': 'hsl(var(--agent-lisa-soft))',
          lucas: 'hsl(var(--agent-lucas))',
          'lucas-soft': 'hsl(var(--agent-lucas-soft))',
          adrian: 'hsl(var(--agent-adrian))',
          'adrian-soft': 'hsl(var(--agent-adrian-soft))',
          valeria: 'hsl(var(--agent-valeria))',
          'valeria-soft': 'hsl(var(--agent-valeria-soft))',
          camila: 'hsl(var(--agent-camila))',
          'camila-soft': 'hsl(var(--agent-camila-soft))',
          mateo: 'hsl(var(--agent-mateo))',
          config: 'hsl(var(--agent-config))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}

export default config
```

**F1-S0 ya extendió `colors.agent.*`.** F1-S1 **VERIFY** que también extendió Shadcn-standard (background, foreground, primary{DEFAULT,foreground}, secondary{...}, muted{...}, accent{...}, card{...}, popover{...}, border, input, ring, destructive{...}) + `borderRadius { lg, md, sm }`. Si parciales → completar verbatim Design Contract § 5.2.

**`darkMode: ['class', '[data-theme="dark"]']`** es **CRÍTICO** — Tailwind v4 default `darkMode: 'media'` activa dark via prefers-color-scheme OS (NO queremos esto, D1 ratificada `enableSystem: false`). El config `['class', '[data-theme="dark"]']` honra el `data-theme` attribute que next-themes setea.

### § 2.6 — Playwright @project=visual (heredado F1-S0)

**NO modificar** `vitalia/frontend/playwright.config.ts` — config heredada de F1-S0 con projects ya configurados:

- `@project=smoke` — quick smoke tests
- `@project=regression` — full behavior coverage
- `@project=visual` — visual goldens con `maxDiffPixelRatio: 0.001`, `animations: 'disabled'`, `caret: 'hide'`
- `@project=a11y` — axe-core suite

F1-S1 **agrega specs nuevas** que consumen estos projects sin tocar config.

### § 2.7 — Playwright specs (3 nuevos)

**Behavior regression** (`e2e/regression/design-tokens-theme/theme-toggle-interaction.spec.ts`):

- Scenario 1 happy: navigate → click `[data-testid="theme-toggle"]` → assert `<html data-theme="dark">` + assert `localStorage.getItem('vitalia-theme') === 'dark'` + assert `aria-pressed="true"` + assert `aria-label` matches `"Cambiar tema (actual: oscuro)"`
- Scenario 2 persistence: `page.evaluate(() => localStorage.setItem('vitalia-theme', 'dark'))` → `page.reload()` → assert `<html data-theme="dark">` directly (no FOUC)
- Scenario 3 negative: `page.on('pageerror', ...)` capture console errors during hydration; pre-suppressHydrationWarning fix assertion fails, post-fix assertion 0 errors

**Visual goldens** (`e2e/visual/design-tokens-theme/theme-toggle.spec.ts`):

- Test page: `/__test-pages__/design-tokens-theme/theme-toggle-showcase`
- Spec light: navigate + `expect(page).toHaveScreenshot('theme-toggle-light.png', { maxDiffPixelRatio: 0.001, animations: 'disabled' })`
- Spec dark: set theme=dark via localStorage + reload + `expect(page).toHaveScreenshot('theme-toggle-dark.png', ...)`

**A11y** (`e2e/a11y/design-tokens-theme/theme-toggle.spec.ts`):

- `injectAxe()` + `checkA11y()` WCAG 2.1 AA strict
- Keyboard nav: `page.keyboard.press('Tab')` hasta focus button + `page.keyboard.press('Enter')` activa toggle + `page.keyboard.press('Space')` activa toggle (segundo press)
- Assert aria-label dinámico + aria-pressed dinámico

### § 2.8 — Vitest unit ThemeToggle.test.tsx

Path: `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.test.tsx`

**Setup:**

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider } from 'next-themes'
import { ThemeToggle } from './ThemeToggle'

function renderWithProvider(defaultTheme: 'light' | 'dark') {
  return render(
    <ThemeProvider attribute="data-theme" defaultTheme={defaultTheme} enableSystem={false} storageKey="vitalia-theme">
      <ThemeToggle />
    </ThemeProvider>
  )
}
```

**Tests:**

- `it('renders with Moon icon when theme is light')` — assert button + Moon SVG present + `aria-pressed="false"` + `aria-label` includes "claro"
- `it('renders with Sun icon when theme is dark')` — assert button + Sun SVG present + `aria-pressed="true"` + `aria-label` includes "oscuro"
- `it('toggles theme on click')` — render light → fireEvent.click(button) → assert next-themes setTheme called (or mock if needed) + aria attrs change
- `it('aria-label matches Spanish neutro pattern')` — regex `/^Cambiar tema \(actual: (claro|oscuro)\)$/` match

### § 2.9 — Test page fixture

Path: `vitalia/frontend/e2e/__test-pages__/design-tokens-theme/theme-toggle-showcase.tsx`

**Propósito:** Renderiza `<ThemeToggle />` aislado en card centrada con padding controlado para snapshot consistente. NO embebe el TopBar global (eso es F1-S2 scope).

```tsx
import { ThemeToggle } from '@/components/shared/shell-organism/ThemeToggle'

export default function ThemeToggleShowcasePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="rounded-lg border bg-card p-8 shadow-sm">
        <ThemeToggle />
      </div>
    </div>
  )
}
```

Test page accesible en dev via `/__test-pages__/design-tokens-theme/theme-toggle-showcase` (Playwright spec navigate target). Excluida del production bundle via Next.js convention (carpeta `__test-pages__` no es ruta válida en prod).

### § 2.10 — Vars introspection vitest

Path: `vitalia/frontend/src/__tests__/tokens/test-shadcn-vars-resolvable.test.ts`

**Setup:**

- `jsdom` environment
- Inject `globals.css` (lee file + injecta `<style>` en document)
- Iterate Shadcn-standard var list verbatim Design Contract § 5.1
- Per var: `getComputedStyle(document.documentElement).getPropertyValue('--' + name)` → assert non-empty string
- Test light (`:root`) + dark (`.dark` class on root)

**Var list cubierta** (15+ per mode):

`--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`, `--popover-foreground`, `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--destructive`, `--destructive-foreground`, `--border`, `--input`, `--ring`, `--radius`.

Plus agent tokens light: `--agent-lisa`, `--agent-lisa-soft`, `--agent-lucas`, `--agent-lucas-soft`, `--agent-adrian`, `--agent-adrian-soft`, `--agent-valeria`, `--agent-valeria-soft`, `--agent-camila`, `--agent-camila-soft`, `--agent-mateo`, `--agent-config`.

---

## § 3 — Cross-cutting decisions

### § 3.1 — `data-theme` attribute (NOT `class="dark"`)

**Decision rationale:**

- next-themes default usa `class="dark"` en `<html>`. Alternativo: `attribute="data-theme"` que setea `<html data-theme="light|dark">`.
- Elegimos **`data-theme`** (D4 ratificada):
  - **Más flexible:** permite múltiples themes futuros (high-contrast, sepia, focus-mode, etc.) sin colisión con sistema de clases (Tailwind ya usa `class` para utilities).
  - **Sintaxis HTML semánticamente cleaner:** `<html data-theme="dark">` describe estado UI, no aplica directamente CSS clases.
  - **Tailwind v4 honra custom selector:** config `darkMode: ['class', '[data-theme="dark"]']` activa variants `dark:` cuando attribute matches.
- Trade-off: requiere config Tailwind explícito (vs default `class`). Acceptable — explicit > implicit per Zen of Python (transposed).

### § 3.2 — `storageKey="vitalia-theme"` namespaced (D4)

- next-themes default `storageKey="theme"`. Cambiamos a `vitalia-theme` por:
  - **Defense-in-depth coexistencia multi-brand FE:** si futuro preview env hostea Nicolify/Vitalia/Comunify en mismo dominio (subdomain prefix), cada brand persiste theme propio sin colisión.
  - **Debugging clarity:** localStorage inspection clearly shows brand context.
  - **Sin overhead extra:** string literal change, zero runtime cost.

### § 3.3 — SSR safety: `suppressHydrationWarning` + next-themes inline `<head>` script

- next-themes inyecta script inline en `<head>` que setea `data-theme` ANTES de hydration React. Sin esto: FOUC (Flash of Unstyled Content) — primer paint en `light` (default), luego switch a `dark` post-hydration.
- React detecta SSR vs client `className` mismatch (server emite sin attribute, client tiene attribute) → emite hydration warning. `suppressHydrationWarning` en `<html>` silencia esa warning **legítima** (no es bug — es comportamiento esperado).
- Scenario 3 (`01-spec.md` § 6) verifica:
  - Pre-fix: console error captura via `page.on('pageerror')` assertion fails
  - Post-fix: 0 console errors

### § 3.4 — Legacy `(dashboard)/` transparent

- Bloque `.vt-*` legacy en `globals.css` tiene colores **hardcoded** (no consume CSS vars Shadcn-standard).
- ThemeProvider wrap es **defensive**: legacy components seguirán renderizando como antes (light hardcoded) porque NO usan tokens nuevos.
- Goldens regression F1-S0 (`dashboard-legacy-light.png` + `dashboard-legacy-dark.png`) deben seguir GREEN post-F1-S1.
- T-7 verify ticket re-corre estos goldens como acceptance.

---

## § 4 — Engine boundaries

**NO toca `core/luana-core-*/`.** F1-S1 es 100% FE local vitalia. NO promotion proposal required. NO downstream regression scope cross-brand.

---

## § 5 — Brand isolation

**NO toca `nicolify/`, `comunify/`, `lupulo/`, ni cualquier futura brand.** next-themes instalación es vitalia-local. ThemeToggle.tsx vive en `vitalia/frontend/src/components/shared/shell-organism/` — vitalia-specific. Cross-brand mirror scan: vacío (Nicolify NO tiene ThemeToggle shipped, comunify+lupulo en bootstrap pendientes).

---

## § 6 — Anti-patterns prohibidos

- Editar `(dashboard)/` legacy pages o `.vt-*` legacy block en `globals.css` (preservar intacto)
- Crear theme picker custom o dropdown 3-state (D1 ratificada: light/dark only via toggle button)
- Soportar OS system theme (`enableSystem={true}`) — D1 ratificada `enableSystem={false}`
- Crear `.stories.tsx` Storybook stories (D3 ratificada — N/A en F1-S1)
- Crear wrapper `src/hooks/useTheme.ts` (D5 ratificada — ThemeToggle import next-themes directo)
- Hex hardcoded en `ThemeToggle.tsx` (consume tokens vía Shadcn Button primitive)
- `any` TypeScript (ESLint rule activa)
- Default exports (FSD-Lite enforce — `export function ThemeToggle()` named)
- Cross-brand imports (`{other_brand}/...`)
- Cross-feature imports (FSD-Lite boundaries ESLint)
- Importar `core/luana-core-*` o `@luana/*` (story 100% FE local)
- Tocar config Playwright `playwright.config.ts` (config heredada F1-S0 estable)
- Test isolation insuficiente — todo Playwright spec usa `await page.context().clearCookies()` + `await page.evaluate(() => localStorage.clear())` antes de assertion para evitar test pollution
- Editar mockup `theme-toggle.html` post-architect (ratificado Chris — re-ratify requerido si modifies)

---

## § 7 — References

- **Spec:** `01-spec.md` (8 Gherkin scenarios + 5 decisiones D1-D5 cementadas + 22 AC operacionales)
- **Mockup ratificado:** `mockups/theme-toggle.html` (4 states: light-idle, light-hover, dark-idle, dark-hover)
- **Predecessor:** `../vitalia-fase1-stack-stability/03-arch.md` (F1-S0 instaló Shadcn + base CSS vars + Tailwind extend agent.*)
- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 5.1 (CSS vars verbatim) + § 5.2 (Tailwind extend verbatim)
- **Brand overlay rules:**
  - `vitalia/.claude/rules/shell-mockup-per-component.md` — APLICA, mockup ratificado pre-architect ✓
  - `vitalia/.claude/rules/hipaa-lite.md` — CONSUME, no-phi-scope declared (UI shell sin PHI)
- **Root rules:**
  - `.claude/rules/frontend-fsd.md` — FSD-Lite boundaries
  - `.claude/rules/spanish-text.md` — Spanish neutro LatAm aria-label
  - `.claude/rules/anti-duplication.md` — no cross-brand mirror (ThemeToggle vitalia-local)
  - `.claude/rules/tdd-mandatory.md` — TDD RED→GREEN per layer
  - `.claude/rules/story-closure-gate.md` — Fase A DEV → B AUDIT → F MERGE auto-handoff
- **Skills consumidos:** frontend-expert, playwright-expert, tessl__shadcn-ui, tessl__tailwind, tessl__vitest, tessl__nextjs-app-router-modularization

---

## § 8 — Research notes (date-aware)

- **next-themes ^0.3.0** — accessed 2026-05-22 via npm registry. React 19 peer-dep compat declared Q4 2025. Source: [next-themes docs](https://github.com/pacocoursey/next-themes). Knowledge cutoff Opus 4.7 = Jan 2026 — researched live via canonical URL.
- **Tailwind v4 `darkMode` config custom selector** — accessed 2026-05-22. `darkMode: ['class', '[data-theme="dark"]']` honra arbitrary attribute selector per Tailwind v4 release notes. Source: [Tailwind v4 docs](https://tailwindcss.com/docs/dark-mode).
- **Next.js 16 App Router `suppressHydrationWarning`** — accessed 2026-05-22. `<html suppressHydrationWarning>` is canonical pattern for next-themes integration per [Next.js docs](https://nextjs.org/docs/app/building-your-application/configuring/theme-providers).
- **WCAG 2.1 AA toggle button pattern** — accessed 2026-05-22 via [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/patterns/button/). `aria-pressed` + dynamic `aria-label` semantically correct for toggle UX.

---

## § 9 — Open questions for PM

None — spec ratificado state=refined, mockup ratificado, 5 decisiones D1-D5 cementadas. Architecture es directa consecuencia de spec + Design Contract verbatim.

