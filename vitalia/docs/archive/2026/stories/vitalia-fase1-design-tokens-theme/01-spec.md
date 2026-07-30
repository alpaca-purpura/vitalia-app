<!-- voseo-allowed: internal spec documentation -->

---
story_id: vitalia-fase1-design-tokens-theme
brand: vitalia
type: ui-story
phase: fase-1
module: shell-organism
agent_owner: shell
capability: shell.design-tokens-theme
po_version: 1.0
last_modified: 2026-05-22
state: refining
ratified_by_chris: false
ratified_visual_by_chris: false
ratified_visual_mockups: []
parallel_safe: false
priority: critical
estimated_dev_days: 1-2
dependencies:
  hard: [vitalia-fase1-stack-stability]
  soft: []
service_blockers: []
blocks_hard:
  - vitalia-fase1-topbar-global
  - vitalia-fase1-shell-layout-5050
  - vitalia-fase1-valeria-rail-history
  - vitalia-fase1-ribbon-6-tabs
reuse_map_summary: "REUSE next-themes (npm oficial) · NEW ThemeToggle component shell-organism · CSS vars + Tailwind extend verbatim Design Contract § 5.1 + § 5.2 · NO Storybook (decisión Chris 2026-05-22 — diferido a stack-setup story dedicada)"
links:
  design_contract: "vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md"
  predecessor: "vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md"
  mockup_visual: "vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html"
  outcome_master: "vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md"
  template_shell_spec: "vitalia/docs/specs/templates/01-spec-shell-template.md"
  mockup_per_component_protocol: "vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md"
---

# F1-S1 `vitalia-fase1-design-tokens-theme` — 01-spec

## § 1 — Resumen ejecutivo

F1-S1 cementa el sistema de design tokens Vitalia post-Shadcn (instalado en F1-S0) + integra `next-themes` provider en `app/layout.tsx` + construye el componente `ThemeToggle` (botón `ghost icon` Shadcn con íconos Lucide `Moon`/`Sun`) que alterna `<html data-theme="light|dark">` con persistencia `localStorage` automática (next-themes) y SSR-safe (no FOUC). Esta es la primera story que **construye un componente user-facing del shell** (F1-S0 era infra puro), y es prerequisite hard de F1-S2 (TopBarGlobal consume `ThemeToggle` como child).

**Decisiones cementadas Chris 2026-05-22 (5 batched /po-ux):**
- D1 — Theme states: `light` + `dark` ÚNICAMENTE (`enableSystem: false`). Razón: scope minimal Fase 1, evitar 3-state cycle complexity. Si en futuro user feedback pide system-theme → story dedicada Fase 2.
- D2 — Mockup format: toggle aislado en card neutral con 4 states side-by-side (light-idle · light-hover · dark-idle · dark-hover). Razón: componente atómico, no requiere contexto TopBar dummy.
- D3 — Storybook: **N/A en F1-S1** (consistente con F1-S0 ratificado). Drop `ThemeToggle.stories.tsx` del checkpoint draft. Tests = `vitest unit` + `Playwright visual goldens` suficientes. Stack Storybook se cementa en story dedicada futura si Chris lo pide.
- D4 — storageKey: **`"vitalia-theme"` namespaced**. Razón: defense-in-depth coexistencia multi-brand FE en mismo dominio (preview env, multi-app subdomain). Sin overhead extra.
- D5 — useTheme hook: **drop wrapper** `src/hooks/useTheme.ts`. ThemeToggle.tsx hace `import { useTheme } from 'next-themes'` directo. Razón: scope minimal, sin wrapper innecesario. Si futuro tracking/analytics de theme changes → agregar wrapper en story dedicada.

**Anti-objetivos (explícito qué NO hace esta historia):**

- NO construir `TopBarGlobal` (eso es F1-S2 — esta story produce solo el componente `ThemeToggle` standalone que F1-S2 va a embeber)
- NO migrar `.vt-*` legacy classes (eso es story final Fase 2 `vitalia-fase2-vt-deprecation-final` per ADR-vitalia-002)
- NO crear theme picker custom (usar `next-themes` npm oficial)
- NO soportar OS system theme (D1 ratificada — scope minimal)
- NO crear Storybook `.stories.tsx` (D3 ratificada)
- NO crear `src/hooks/useTheme.ts` wrapper (D5 ratificada — import next-themes directo)
- NO tocar route group `(shell-organism)/` (eso es F1-S4)
- NO modificar `(dashboard)/` legacy salvo wrap `<ThemeProvider>` que es necesario para que F1-S1+ funcione (transparente al legacy — no rompe styling existente)
- NO instalar `next-themes` en otras brands (scope brand-local Vitalia)

---

## § 2 — Visión (paradigma shell-organism)

F1-S1 es el **primer componente real del shell-organism** — F1-S0 dejó Shadcn instalado + CSS vars en `globals.css` + `tailwind.config.ts` extend. F1-S1 ahora:

1. Completa CSS vars Shadcn-standard al 100% verbatim Design Contract § 5.1 (algunas estaban parciales post-F1-S0; F1-S1 cementa todas)
2. Integra `ThemeProvider` en `app/layout.tsx` (root layout brand vitalia)
3. Construye `ThemeToggle` component reusable bajo `src/components/shared/shell-organism/` (PRIMER componente del directorio shell-organism — F1-S2..S10 lo van a poblar con TopBarGlobal, ValeriaSidebar, Ribbon, etc.)
4. Cementa convención `data-theme` attribute (vs `class="dark"` alternativo) — decisión técnica para que CSS vars `.dark` block se active correctamente
5. Genera 2 Playwright visual goldens (light + dark) que F1-S2+ heredan como contrato visual del botón ghost-icon

**Agente owner:** SHELL (transversal — no es de un agente específico)
**Color oficial:** neutral / accent — ThemeToggle usa `variant="ghost" size="icon"` (sin background, sin border, hover muestra `--accent` sutil)
**Avatar PNG:** N/A (story infra-shell)

---

## § 3 — Atomic Design Layers (referencia Design Contract § 3)

> F1-S1 construye 1 átomo (`ThemeToggle` reutilizando `Button` + `Moon`/`Sun`) + completa tokens infraestructura. Una sola "molécula trivial".

### § 3.1 — Átomos consumidos (instalados en F1-S0)

| Átomo | Path | Cómo se usa en F1-S1 |
|---|---|---|
| `Button` | `vitalia/frontend/src/components/ui/button.tsx` | `<Button variant="ghost" size="icon" aria-label="..." aria-pressed="...">` |
| `Moon` (Lucide) | `lucide-react` npm | `<Moon className="h-[1.2rem] w-[1.2rem]" />` (light state visible) |
| `Sun` (Lucide) | `lucide-react` npm | `<Sun className="h-[1.2rem] w-[1.2rem]" />` (dark state visible) |

### § 3.2 — Moléculas construidas

| Molécula | Path | Variantes | Props | Notas |
|---|---|---|---|---|
| `ThemeToggle` | `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` | 4 states visuales (light-idle · light-hover · dark-idle · dark-hover) | ninguna (componente self-contained, lee/escribe theme via `useTheme()` hook de next-themes) | Client component (`'use client'`). aria-label dinámico per current theme. data-testid="theme-toggle" para Playwright |

### § 3.3 — Organismos construidos

**N/A — esta story es atómica (1 molécula).** Organismos consumen `ThemeToggle`:
- F1-S2 `TopBarGlobal` embebe `<ThemeToggle />` en la rightmost area junto a TenantSwitcher

### § 3.4 — Templates / Pages modificadas

| Path | Acción | Detalle |
|---|---|---|
| `vitalia/frontend/package.json` | MODIFY | `+ "next-themes": "^0.3.0"` (latest stable React 19 compat). `+ "lucide-react"` (ya instalado en F1-S0 via Shadcn deps — confirmar) |
| `vitalia/frontend/src/app/globals.css` | MODIFY | Completar CSS vars Shadcn-standard verbatim Design Contract § 5.1 (algunas parciales post-F1-S0). Bloque `:root` + `.dark` con TODAS las vars: `--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`, `--popover-foreground`, `--primary` + `--primary-foreground`, `--secondary` + `--secondary-foreground`, `--muted` + `--muted-foreground`, `--accent` + `--accent-foreground`, `--destructive` + `--destructive-foreground`, `--border`, `--input`, `--ring`, `--radius`. Bloque `.dark` con dark variants. Preservar `.vt-*` legacy block |
| `vitalia/frontend/tailwind.config.ts` | MODIFY (verificar/completar) | F1-S0 ya extendió `colors.agent.*`. F1-S1 verifica que TODAS las vars Shadcn-standard estén consumidas: `colors.background`, `colors.foreground`, `colors.primary { DEFAULT, foreground }`, `colors.secondary { DEFAULT, foreground }`, `colors.muted { DEFAULT, foreground }`, `colors.accent { DEFAULT, foreground }`, `colors.card { DEFAULT, foreground }`, `colors.popover { DEFAULT, foreground }`, `colors.border`, `colors.input`, `colors.ring`, `colors.destructive { DEFAULT, foreground }` + `borderRadius.{ lg, md, sm }` consumiendo `var(--radius)`. Verbatim Design Contract § 5.2 |
| `vitalia/frontend/src/app/layout.tsx` | MODIFY | Wrap `<html lang="es" suppressHydrationWarning>` + `<body>{children}</body>` con `<ThemeProvider attribute="data-theme" defaultTheme="light" enableSystem={false}>`. Import `ThemeProvider from 'next-themes'`. `suppressHydrationWarning` en `<html>` es REQUIRED por next-themes (evita hydration mismatch warning) |
| `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` | NEW | Client component según § 3.2 |
| `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.test.tsx` | NEW | Vitest unit: render light + render dark + click toggles theme + aria-label cambia + aria-pressed cambia |
| ~~`vitalia/frontend/src/hooks/useTheme.ts`~~ | **DROPPED** | D5 ratificada Chris 2026-05-22 — ThemeToggle.tsx hace `import { useTheme } from 'next-themes'` directo. Sin wrapper innecesario. |
| `vitalia/frontend/e2e/__test-pages__/design-tokens-theme/theme-toggle-showcase.tsx` | NEW | Test page Playwright fixture — renderiza `<ThemeToggle />` aislado en card centrada con padding controlado para snapshot consistente |
| `vitalia/frontend/e2e/visual/design-tokens-theme/theme-toggle.spec.ts` | NEW | Spec Playwright `@project=visual` genera 2 goldens (light + dark) |
| `vitalia/frontend/e2e/regression/design-tokens-theme/theme-toggle-interaction.spec.ts` | NEW | Spec Playwright behavior — click toggle alterna `<html data-theme>` + persistencia localStorage + reload preserva theme |
| `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-{light,dark}.png` | NEW (×2) | Goldens generados por spec visual (Chris ratify visual antes de commit) |
| `vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/mockups/theme-toggle.html` | NEW | Mockup HTML por-componente per `vitalia/.claude/rules/shell-mockup-per-component.md` — 4 states side-by-side (light-idle · light-hover · dark-idle · dark-hover) en card neutral. Chris ratify ANTES de transition refining→refined |

---

## § 4 — Reuse Map exhaustivo

### § 4.1 — REUSE desde Nicolify

**N/A — F1-S1 es greenfield Vitalia.** Nicolify NO tiene `ThemeToggle` shipped (dashboard Nicolify es light-only por design decision Q3 2025). F1-S1 establece la convención `data-theme` que eventualmente Nicolify puede adoptar via promotion.

### § 4.2 — REUSE desde core/luana-core-*

**N/A — F1-S1 es 100% infra FE local.** No consume packages `luana_core_*` ni TS packages `@luana/*`.

### § 4.3 — REUSE desde Vitalia shipped

| Asset | Path actual | Acción en F1-S1 |
|---|---|---|
| `vitalia/frontend/src/components/ui/button.tsx` (instalado F1-S0) | shipped post-F1-S0 | **REUSE** vía `<Button variant="ghost" size="icon">` |
| `vitalia/frontend/src/app/globals.css` (F1-S0 parcialmente lleno) | shipped post-F1-S0 | **COMPLETAR** CSS vars Shadcn-standard al 100% verbatim Design Contract § 5.1 |
| `vitalia/frontend/tailwind.config.ts` (F1-S0 colors.agent.* extendido) | shipped post-F1-S0 | **VERIFY/COMPLETE** colors Shadcn-standard mapeo via `hsl(var(--...))` |
| `vitalia/frontend/src/lib/utils.ts::cn()` (F1-S0 helper) | shipped post-F1-S0 | **REUSE** dentro `ThemeToggle.tsx` para className composition |
| `vitalia/frontend/src/app/layout.tsx` existente | shipped pre-F1-S1 | **MODIFY** wrap con ThemeProvider — `suppressHydrationWarning` agregado en `<html>` |
| Avatars PNGs agentes | shipped recovery 2026-05-21 | **NO TOCAR** — F1-S1 no consume avatars |
| Storage Clerk auth + middleware | shipped | **NO TOCAR** — F1-S1 no toca rutas autenticadas |
| Legacy `(dashboard)/` page tree | shipped | **TRANSPARENTE** — wrap `ThemeProvider` en root layout es transparente al legacy (legacy seguirá renderizando light theme por defecto porque sus components no usan tokens nuevos todavía — solo `.vt-*` legacy que tienen colores hardcoded). Goldens regression F1-S0 deben seguir pasando |

### § 4.4 — NEW (creado en esta historia)

| Artefacto NEW | Razón |
|---|---|
| `ThemeToggle` component | Componente shell-specific — Shadcn registry NO incluye ThemeToggle pre-built (es ejemplo de docs pero no en `components/ui/`). Convención brand-local Vitalia |
| `next-themes` npm dep | npm oficial — único proveedor SSR-safe theme provider para Next.js 16 App Router. Sin esto: FOUC durante hydration |
| `useTheme.ts` hook wrapper (TBD según iteración) | Conveniencia future-proof para agregar telemetría/analytics si Chris pide tracking de theme changes. Si no se necesita → drop, import directo `from 'next-themes'` |
| Test page + 2 specs Playwright + goldens | Visual baseline + behavior coverage |
| Mockup HTML per-component | Cumplimiento mandatorio `vitalia/.claude/rules/shell-mockup-per-component.md` |

### § 4.5 — Legacy `/home/chalreme/Documentos/ap_sales_agent`

**N/A — F1-S1 no consulta legacy single-brand pre-multibrand.**

---

## § 5 — API contracts (BE ↔ FE)

**N/A runtime — esta story es 100% FE local, sin endpoints consumidos.**

### Build-time note: next-themes npm fetch

`npm install next-themes` resuelve dep `^0.3.x` (latest stable React 19 compat). Lockfile pin en `package-lock.json` garantiza reproducibilidad. Sin red durante install → falla npm (igual que cualquier otra dep).

### Local storage convention

next-themes config: **`storageKey="vitalia-theme"`** (D4 ratificada Chris 2026-05-22). Defense-in-depth coexistencia multi-brand FE en mismo dominio. ThemeProvider props:
```tsx
<ThemeProvider
  attribute="data-theme"
  defaultTheme="light"
  enableSystem={false}
  storageKey="vitalia-theme"
>
  {children}
</ThemeProvider>
```

---

## § 6 — Acceptance Criteria (Gherkin AI-resistant)

> 5 scenarios funcionales activos + 1 a11y + 1 i18n + 1 bloque consolidado N/A con razón. Total: 8 entradas que satisfacen gate `/po-ux v4.1`.

### Scenario 1 — `happy-path` (type: happy + light→dark toggle)

**Given:**
- F1-S0 completado (Shadcn + tokens base instalados)
- F1-S1 implementación pre-cambios: `ThemeToggle` no existe, `<ThemeProvider>` no envuelve layout, CSS vars `.dark` block puede estar incompleto
- Test fixture: usuario landed en cualquier ruta legacy `(dashboard)/...` (theme inicial = `light` per `defaultTheme`)

**When:**
- Implementación F1-S1 deployed
- Usuario click `[data-testid="theme-toggle"]` en componente embebido (test page o futuro TopBar F1-S2)

**Then:**
- `<html data-theme="light">` cambia a `<html data-theme="dark">`
- Icon visible cambia de `Moon` (light state — sugiere "switch to dark") a `Sun` (dark state — sugiere "switch to light")
- `getComputedStyle(document.body).backgroundColor` cambia (de light bg ~#fff a dark bg, verifica que `.dark` CSS vars block aplica)
- `localStorage.getItem('vitalia-theme')` retorna `'dark'`
- aria-pressed atributo del button cambia de `"false"` a `"true"`
- aria-label cambia de "Cambiar tema (actual: claro)" a "Cambiar tema (actual: oscuro)"
- NO console errors ni warnings

**playwright_required:** true
**Graders:**
- E2E behavior: `vitalia/frontend/e2e/regression/design-tokens-theme/theme-toggle-interaction.spec.ts` (click + assert DOM + assert localStorage + assert aria attrs)
- Visual golden light: `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-light.png`
- Visual golden dark: `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-dark.png`
- Unit: `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.test.tsx` (render + interaction)

---

### Scenario 2 — `persistence` (type: happy + reload preserva theme)

**Given:**
- F1-S1 deployed
- Usuario seteó `dark` theme via toggle en sesión previa
- `localStorage.getItem('vitalia-theme')` = `'dark'`

**When:**
- Usuario hace reload página (F5 o nueva pestaña abriendo URL guardada)

**Then:**
- Página renderiza directamente con `<html data-theme="dark">` desde el primer paint (NO FOUC = NO flash de light antes de aplicar dark)
- next-themes script `inline` en `<head>` corre ANTES de hydration React, sin parpadeo
- Toggle muestra `Sun` icon (dark state) directamente, no transición visible
- `getComputedStyle` confirma dark vars aplicadas desde paint inicial

**playwright_required:** true
**Graders:**
- E2E behavior: spec con `page.goto()` + `page.evaluate(() => localStorage.setItem('vitalia-theme', 'dark'))` + `page.reload()` + assert `html data-theme === 'dark'` en primer frame
- Visual diff: NO frame diff entre antes y después del FCP (First Contentful Paint) — caso flaky → spec usa `waitForLoadState('domcontentloaded')` + screenshot inmediato

---

### Scenario 3 — `negative-fouc` (type: negative — FOUC detection durante SSR)

**Given:**
- F1-S1 implementación parcial: `<ThemeProvider>` integrado pero `suppressHydrationWarning` faltante en `<html>` (typo o olvido)
- Build production (`npm run build` + `npm start`)

**When:**
- Usuario carga página con localStorage `theme=dark`

**Then:**
- Hydration warning visible en console: "Warning: Prop `className` did not match. Server: '...' Client: '...'"
- (Si flagrant) Flash visual durante hydration — momentary `data-theme="light"` aplicado server-side antes del client switch a `dark`
- Developer fix: agregar `suppressHydrationWarning` en `<html lang="es" suppressHydrationWarning>`
- Re-verify Scenario 2 pass post-fix

**playwright_required:** true
**Graders:**
- Pre-fix: spec captura console errors via `page.on('pageerror')` + assertion fails
- Post-fix: spec assertion 0 console warnings

---

### Scenario 4 — `edge` (type: edge — agent tokens resolvables post-completion)

**Given:**
- F1-S1 completado: CSS vars Shadcn-standard + agent tokens completos en `globals.css` (light + dark) + Tailwind extend completo

**When:**
- Test page renderiza `<div className="bg-primary text-primary-foreground p-4">primary swatch</div>` + idem para `bg-accent`, `bg-muted`, `bg-card`, `bg-popover`, `bg-destructive` + `bg-agent-{lisa,lucas,adrian,valeria,camila,mateo,config}`
- Playwright `@project=visual` snapshot en light + dark

**Then:**
- En light: `bg-primary` resuelve a `#01b2f8` (Adrián cyan), `bg-accent` a `#7b2d91` (Valeria purpura), `bg-agent-lisa` a `#00D084`, etc. verbatim Design Contract § 5.1
- En dark: vars `.dark` block aplican (background ≈ near-black, foreground ≈ near-white, primary/accent mantienen pero soft variants accesibles)
- Visual diff vs goldens `tokens-swatch-{light,dark}.png` < 0.1% pixel ratio
- Heredado de F1-S0 visual goldens 5-6 — F1-S1 los re-genera completos post-completion

**playwright_required:** true
**Graders:**
- Visual: regression del agent-tokens-swatch.png golden (heredado F1-S0 con potencial update si F1-S0 tenía vars parciales)
- Vitest introspection: `src/__tests__/tokens/test-shadcn-vars-resolvable.test.ts` valida que TODA var Shadcn-standard esté presente en :root + .dark

---

### Scenario 5 — `accessibility` (type: WCAG AA — sub-categoría mandatory v4.1)

**Given:**
- F1-S1 ThemeToggle deployed
- Playwright fixture con `@axe-core/playwright` configurado

**When:**
- Page render `<ThemeToggle />` + axe scan ruleset WCAG 2.1 AA
- Keyboard navigation: usuario Tab hasta el botón + Enter o Space para activar

**Then:**
- axe scan: 0 violations
- Button tiene accessible name via `aria-label` ("Cambiar tema (actual: claro/oscuro)")
- Button tiene `role="button"` implícito + `aria-pressed="true|false"` dinámico
- Focus visible (Shadcn Button ghost variant tiene `focus-visible:ring-2 focus-visible:ring-ring`)
- Contrast ratio: icon Moon/Sun foreground vs background ≥ 3:1 (UI component target WCAG AA non-text)
- Keyboard Enter activa toggle (mismo behavior que click)
- Keyboard Space activa toggle (mismo behavior que click)
- No keyboard trap (Tab sale del botón correctamente)

**playwright_required:** true
**Graders:**
- axe: `vitalia/frontend/e2e/a11y/design-tokens-theme/theme-toggle.spec.ts` con `injectAxe()` + `checkA11y()` strict
- Keyboard: spec con `page.keyboard.press('Tab')` + `page.keyboard.press('Enter')` + assert toggle ocurrió

---

### Scenario 6 — `i18n` (type: Spanish neutro — sub-categoría mandatory v4.1)

**Given:**
- F1-S1 ThemeToggle deployed
- aria-label dinámico: "Cambiar tema (actual: claro)" / "Cambiar tema (actual: oscuro)"

**When:**
- Code review + Playwright spec lee aria-label en ambos states

**Then:**
- NO voseo (`vos/sos/tenés/podés/cambiá/dale`) en aria-label
- NO léxico regional argentino/chileno
- Tildes correctas (ninguna en estos strings, pero verificable globalmente)
- Test programático: `await expect(button).toHaveAttribute('aria-label', /^Cambiar tema \(actual: (claro|oscuro)\)$/)` matches sin variantes regionales
- Verbatim glosario `.claude/rules/spanish-text.md` validation

**playwright_required:** true
**Graders:**
- E2E aria-label assertion: spec en `theme-toggle-interaction.spec.ts` extiende para verificar string exacto
- Vitest: `ThemeToggle.test.tsx` snapshot aria-label rendering
- Lint (auto): pre-commit hook `scripts/git-hooks/pre-commit` Section 5 voseo scan sobre `ThemeToggle.tsx`

---

### Scenario 7 — `adversarial` (type: not_applicable con razón rigurosa)

**adversarial: not_applicable**

**Razón:** F1-S1 ThemeToggle es componente FE puramente client-side stateful (theme = local user preference). NO toca:
- Auth (no Clerk session interaction)
- PHI (no medical/patient data)
- Tenant context (theme es per-user-device, no per-tenant)
- API endpoints (zero fetch)
- Form submission (no input user-provided body)
- URL params / query strings (theme no se pasa via URL)
- WebSocket / SSE (no streaming)

El único vector adversarial teórico es **localStorage manipulation** (usuario malicioso o XSS injection cambia `vitalia-theme` value a string arbitrario). Mitigación nativa:
- next-themes filtra strings inválidos (solo acepta `'light'` o `'dark'`)
- Si localStorage tiene valor corrupto → next-themes falla gracefully a `defaultTheme: 'light'`
- XSS injection es vector multi-vector que requiere CSP + sanitization defense-in-depth (no scope F1-S1)

Si futuro `/auditor` re-clasifica esto como vector real → spawn scenario adversarial dedicado.

---

### Scenario 8 — `not_applicable batch` (sub-categorías mandatory que no aplican)

> Gate `/po-ux v4.1` requiere cubrir sub-categorías con scenario o `not_applicable_reason` explícito. F1-S1 es componente atómico self-contained client-side state, las siguientes 5 sub-categorías genuinamente no aplican:

```yaml
not_applicable_sub_categories:
  - sub_category: race_condition
    reason: "F1-S1 no introduce endpoints con create/update DB ni unique constraints. Toggle escribe a localStorage (single-process single-tab) — race entre tabs mismo origin es trivial (last-write-wins, sin pérdida data)."
  - sub_category: concurrent_users
    reason: "F1-S1 theme es per-user-device-localStorage. NO hay multi-user shared state. Diferentes users en diferentes devices/sesiones tienen themes independientes por design — eso ES el comportamiento esperado, no edge case."
  - sub_category: network_failure
    reason: "F1-S1 zero fetch FE runtime. localStorage es síncrono local. next-themes resolve theme inline en <head> antes de cualquier network activity."
  - sub_category: empty_state
    reason: "F1-S1 no introduce list/dashboard que pueda tener 0 items. ThemeToggle siempre tiene 1 state activo (light o dark), nunca 'empty'."
  - sub_category: large_dataset
    reason: "F1-S1 no introduce data fetching ni rendering de listas. ThemeToggle es componente atómico con 2 states fijos."
  - sub_category: mobile-responsive
    reason: "ThemeToggle es Button size='icon' (24×24px o similar) — diseñado para responsive nativo. NO requiere breakpoints específicos. Su posicionamiento responsive es responsabilidad de F1-S2 TopBar (que embebe ThemeToggle)."
  - sub_category: loading-state
    reason: "next-themes resuelve theme sincrónicamente desde localStorage en script inline <head>. Zero async, zero loading state. (Excepción: SSR initial paint sin localStorage value disponible → next-themes maneja vía suppressHydrationWarning + cliente hidrata theme inmediatamente. Cubierto en Scenario 3)."
```

---

## § 7 — Visual Goldens (mockup como source of truth)

### § 7.1 — 2 snapshots requeridos

| # | Snapshot | Viewport | Theme | Propósito | Path golden |
|---|---|---|---|---|---|
| 1 | `theme-toggle-light` | 400×300 | light | ThemeToggle aislado en card neutral, Moon icon visible | `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-light.png` |
| 2 | `theme-toggle-dark` | 400×300 | dark | ThemeToggle aislado en card neutral, Sun icon visible | `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-dark.png` |

**Adicional update:** `tokens-swatch-{light,dark}.png` (heredado de F1-S0) se regenera si F1-S1 completa CSS vars que estaban parciales post-F1-S0. Detección automática vía Playwright @project=visual.

### § 7.2 — Trazabilidad mockup → golden → componente

| Mockup ref | Golden path | Componente verificado | Design Contract ref |
|---|---|---|---|
| `vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/mockups/theme-toggle.html` (4 states) | `theme-toggle-light.png` + `theme-toggle-dark.png` | `ThemeToggle.tsx` | § 3.1 átomos + § 5.1 dark vars |

### § 7.3 — Test pages auxiliares (Playwright fixtures)

**Path:** `vitalia/frontend/e2e/__test-pages__/design-tokens-theme/`

```
__test-pages__/
└── design-tokens-theme/
    └── theme-toggle-showcase.tsx     # Renderiza <ThemeToggle/> aislado en card centrada
```

### § 7.4 — Mockup HTML per-component (gate visual bloqueante)

**Path:** `vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/mockups/theme-toggle.html`

**Contenido obligatorio:**
- Tailwind CSS CDN cargado
- CSS vars Vitalia inline (`:root { --background: ...; --primary: ...; --accent: ...; }` + `.dark { ... }`)
- 4 states side-by-side en card neutral:
  1. **Light + idle:** botón ghost icon, fondo card neutro, icon Moon
  2. **Light + hover:** mismo botón con hover state (bg-accent/10 subtle)
  3. **Dark + idle:** card en dark mode, icon Sun
  4. **Dark + hover:** dark + hover state
- Label inferior cada state ("Light · Idle", "Light · Hover", "Dark · Idle", "Dark · Hover")
- Spanish neutro labels (aria-label visible inline para revisar)
- Sin frameworks externos (NO Bootstrap, NO Material UI)
- Datos LatAm si aplica (N/A para componente atómico sin texto contextual)

**Workflow ratificación Chris:**
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/mockups
python3 -m http.server 8888
# Chris abre http://localhost:8888/theme-toggle.html
# Itera con /po-ux hasta ratify → frontmatter ratified_visual_by_chris: true
```

### § 7.5 — Generación inicial vs verify

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# Generación inicial (builder ejecuta tras finalizar ThemeToggle + ThemeProvider integration):
npx playwright test --project=visual --grep "design-tokens-theme" --update-snapshots
# Chris revisa diff humano vs mockup HTML + Design Contract § 5.1 antes de ratify

# Verify CI (auto en cada PR FE):
npx playwright test --project=visual --grep "design-tokens-theme"
# Falla si diff > 0.1% pixels
```

### § 7.6 — Tolerancia + animaciones (verbatim Design Contract § 9.4)

- `maxDiffPixelRatio: 0.001` (0.1%)
- `animations: 'disabled'` (sin flaky en hover transitions)
- `caret: 'hide'`
- **Special note ThemeToggle:** hover state requiere `page.hover()` + screenshot inmediato. Playwright `animations: 'disabled'` previene flaky de Shadcn Button hover transition.

---

## § 8 — Acceptance criteria operacionales

| # | Criterio | Verificación |
|---|---|---|
| AC-1 | `npm install next-themes` ejecutado, lockfile committed | `package.json` + `package-lock.json` diff review |
| AC-2 | `globals.css` tiene TODAS las CSS vars Shadcn-standard en `:root` + `.dark` verbatim Design Contract § 5.1 | `grep -c "^\\s*--" vitalia/frontend/src/app/globals.css` ≥ 30 (15+ light + 15+ dark) |
| AC-3 | `tailwind.config.ts` mapea TODAS las vars Shadcn-standard via `hsl(var(--...))` | Vitest introspection test |
| AC-4 | `layout.tsx` wrap `<ThemeProvider attribute="data-theme" defaultTheme="light" enableSystem={false}>` | grep + import test |
| AC-5 | `<html lang="es" suppressHydrationWarning>` agregado | grep `suppressHydrationWarning` |
| AC-6 | `ThemeToggle.tsx` existe + 'use client' directive + correct props/aria attrs | File existence + grep |
| AC-7 | Tailwind class `bg-primary` renderiza `#01b2f8` (light) | Scenario 4 visual golden |
| AC-8 | Tailwind class `bg-agent-lisa` renderiza `#00D084` | Heredado F1-S0 Scenario 4 golden agent-tokens-swatch |
| AC-9 | Click `<ThemeToggle>` alterna `<html data-theme="light">` ↔ `data-theme="dark"` | Scenario 1 grader E2E |
| AC-10 | localStorage `vitalia-theme` persiste selección | Scenario 1 grader E2E |
| AC-11 | Reload página preserva theme seleccionado (NO FOUC) | Scenario 2 grader E2E + Scenario 3 grader negative |
| AC-12 | a11y: button `aria-label` dinámico + `aria-pressed` correcto | Scenario 5 grader axe + assertion |
| AC-13 | Keyboard activation (Enter + Space) funciona | Scenario 5 keyboard grader |
| AC-14 | i18n: aria-label Spanish neutro (NO voseo) | Scenario 6 grader |
| AC-15 | Playwright visual golden ThemeToggle light + dark generados + Chris ratify | Scenario 1 visual graders |
| AC-16 | Vitest unit: render light + render dark + click toggle + state changes | `ThemeToggle.test.tsx` existencia + green |
| AC-17 | `npx tsc --noEmit` 0 errors | Shell exit 0 |
| AC-18 | `npx eslint src/` 0 errors | Shell exit 0 |
| AC-19 | `npm run build` PASS (production build) | Shell exit 0 |
| AC-20 | Mockup HTML `mockups/theme-toggle.html` existe + ratificado Chris (4 states) | File existence + frontmatter `ratified_visual_by_chris: true` |
| AC-21 | NO `.vt-*` class usada en código nuevo (arch fitness test heredado F1-S0 green) | Arch test green |
| AC-22 | Goldens regression F1-S0 (`dashboard-legacy-light.png` + `dashboard-legacy-dark.png`) siguen pasando (ThemeProvider wrap es transparente al legacy) | Visual diff < 0.1% |

---

## § 9 — Zero deuda técnica — checklist mandatorio

- [ ] **Lint:** `npx eslint src/` --max-warnings 0
- [ ] **TypeScript:** `npx tsc --noEmit` 0 errors
- [ ] **Format:** `npx prettier --check vitalia/frontend/src/components/shared/shell-organism/`
- [ ] **Vitest tests:** unit ThemeToggle + existing regression PASS
- [ ] **Playwright behavior E2E:** Scenarios 1, 2, 3 pass + Scenarios 5, 6 a11y/i18n pass
- [ ] **Playwright visual goldens:** 2 baselines (light + dark) generados + Chris ratify
- [ ] **NO `.vt-*` classes en código nuevo:** arch test green (heredado F1-S0)
- [ ] **NO `any` TypeScript** en código nuevo (ThemeToggle.tsx + tests + hooks)
- [ ] **NO default exports** en código nuevo (FSD-Lite enforce — `export function ThemeToggle()` named)
- [ ] **NO cross-feature imports** (boundaries ESLint pass — ThemeToggle solo importa `@/components/ui/button` + `lucide-react` + `next-themes`)
- [ ] **NO cross-brand imports** (`{other_brand}/...`)
- [ ] **NO core engine direct edits** (F1-S1 NO toca `core/luana-core-*`)
- [ ] **CSS variables consumidas** en `tailwind.config.ts` extend (NO hex hardcoded en `ThemeToggle.tsx`)
- [ ] **Spanish neutro LatAm:** aria-label "Cambiar tema (actual: claro/oscuro)" — NO voseo
- [ ] **Lockfile committed:** `vitalia/frontend/package-lock.json` con `next-themes` agregada
- [ ] **Build production:** `npm run build` exit 0
- [ ] **Storybook story:** N/A (D3 ratificada Chris 2026-05-22 — Storybook diferido)
- [ ] **Mobile responsive:** N/A componente atómico (botón icon)
- [ ] **Dark mode:** ESTA story implementa dark mode infra completa
- [ ] **HIPAA-lite no-phi-scope declared:** F1-S1 es UI shell sin PHI ni rutas autenticadas con data sensible
- [ ] **`ratified_visual_by_chris: true`** post mockup HTML ratify
- [ ] **`ratified_visual_mockups`** lista contiene path `mockups/theme-toggle.html`
- [ ] **`ratified_visual_iter: N`** iter número de ratificación final

---

## § 10 — Dependencies map

### § 10.1 — Dependencies hard

```
F1-S1 depende hard de F1-S0:
  - F1-S0 produce: components.json + 8 primitives + globals.css base CSS vars + tailwind.config.ts extend + utils.ts cn helper
  - F1-S1 consume: Button primitive + cn helper + tokens infraestructura para completar CSS vars
```

### § 10.2 — Dependencies soft

```
N/A
```

### § 10.3 — Service blockers BE

```
N/A — F1-S1 es 100% FE local.
```

### § 10.4 — Esta historia bloquea (downstream)

```
F1-S1 desbloquea HARD 4 stories Fase 1:
  1. vitalia-fase1-topbar-global              (F1-S2 — embebe ThemeToggle)
  2. vitalia-fase1-shell-layout-5050          (F1-S4 — consume CSS vars completas)
  3. vitalia-fase1-valeria-rail-history       (F1-S5 — consume agent tokens + Button)
  4. vitalia-fase1-ribbon-6-tabs              (F1-S7 — consume agent tokens)
```

---

## § 11 — Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **next-themes React 19 peer-dep conflict** | Baja | Alto | next-themes ^0.3.0 declared React 19 compat 2025-Q4. Scenario 3 atrapa con build production. Workaround: `--legacy-peer-deps` si necesario |
| **FOUC (Flash of Unstyled Content)** durante SSR hydration | Media | Medio | Scenario 3 catchea. Mitigación: `suppressHydrationWarning` en `<html>` + next-themes inline `<head>` script (auto via ThemeProvider) |
| **CSS vars dark block incompleto** post F1-S0 | Media | Medio | Scenario 4 verifica todas las vars resolvables. Vitest introspection test (`test-shadcn-vars-resolvable.test.ts`) enforce |
| **localStorage corruption / XSS** (vector teórico) | Baja | Bajo | next-themes filtra strings inválidos → fallback a `defaultTheme`. CSP + sanitization defense-in-depth fuera scope F1-S1 |
| **Legacy `(dashboard)/` rompe con ThemeProvider wrap** | Baja | Medio | Goldens regression F1-S0 (`dashboard-legacy-light.png` + `dashboard-legacy-dark.png`) catchan. `.vt-*` legacy block tiene colores hardcoded — independiente de CSS vars Shadcn-standard |
| **Hover transition flaky en Playwright visual** | Media | Bajo | `animations: 'disabled'` (Design Contract § 9.4). Si flaky persiste: aumentar `maxDiffPixelRatio` a 0.002 solo para hover snapshots |
| **`storageKey` collision con otra app** (e.g., Nicolify FE en mismo dominio) | Baja | Bajo | D4 ratificada: `storageKey="vitalia-theme"` namespaced (defense-in-depth) |

---

## § 12 — Definición de "Done"

F1-S1 transitions `developing → developed` cuando:

1. **Todos los AC-1..AC-22 del § 8 verificados** (manual + automated)
2. **Todos los items aplicables del checklist § 9 ✓**
3. **2 Playwright visual goldens generados + ratificados Chris**
4. **6 Gherkin scenarios funcionales (1, 2, 3, 4, 5, 6) pass** + Scenario 7 adversarial documentado N/A + Scenario 8 bloque N/A documentado
5. **Mockup HTML `mockups/theme-toggle.html` ratificado Chris** (frontmatter `ratified_visual_by_chris: true`)
6. **Arch fitness tests heredados F1-S0 siguen GREEN** (test-no-vt-classes-in-new-features)
7. **Story commits pushed** + branch `wip/vitalia` sync con `main`
8. **`T-{n}-result.md`** escrito con SHA commits + log decisiones implementación (next-themes version pinned, storageKey elegido, useTheme.ts hook wrapper kept/dropped según iteración)
9. **Handoff `/auditor`** emitido automáticamente (story closure gate)

Auditor APPROVED → `/pm-vitalia merge` → state `done` → 4 stories downstream unblocked.

---

## § 13 — Referencias

### SSoT obligatorios citados

- **Design Contract** atomic design SSoT: `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (§ 3.1 átomos + § 5.1 CSS vars verbatim + § 5.2 Tailwind extend verbatim)
- **Predecessor story F1-S0**: `vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md`
- **Template spec SHELL**: `vitalia/docs/specs/templates/01-spec-shell-template.md`
- **Mockup HTML integral** visual SSoT: `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html`
- **Outcome master** Fase 1+2: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md` v2.0

### Reglas raíz aplicables

- **FSD-Lite enforcement**: `.claude/rules/frontend-fsd.md` (ThemeToggle vive en `components/shared/shell-organism/`, boundaries pass)
- **HIPAA-lite overlay**: `vitalia/.claude/rules/hipaa-lite.md` — **no-phi-scope declared**: F1-S1 es UI shell sin PHI
- **Spanish neutro**: `.claude/rules/spanish-text.md` — aria-label "Cambiar tema (actual: claro/oscuro)" pass
- **Brand docs schema R1+R2+R3**: `.claude/rules/brand-docs-schema.md`
- **Story closure gate**: `.claude/rules/story-closure-gate.md`
- **Shell mockup-per-component protocol**: `vitalia/.claude/rules/shell-mockup-per-component.md` (F1-S1 APLICA — mockup `theme-toggle.html` obligatorio pre-refined)

### § 13.1 — Protocolo mockup-per-component (APLICA)

F1-S1 **SÍ está sujeta** al protocolo. Mockup HTML `mockups/theme-toggle.html` (4 states) ratificado Chris ANTES de transition refining→refined.

### § 13.2 — Compliance scope (no-phi-scope declared)

F1-S1 es infra UI shell. NO toca `patient_*`, `medical_*`, `treatment_*`, ni rutas autenticadas con data sensible. Salvaguardas HIPAA-lite no aplican.

---

## § 14 — Changelog spec

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-22 | Draft inicial `/po-ux`. 5 decisiones cementadas G6 batched Chris: D1 light/dark only (enableSystem:false), D2 mockup 4 states aislados card neutral, D3 Storybook N/A, D4 storageKey="vitalia-theme" namespaced, D5 drop useTheme.ts wrapper (import next-themes directo). 8 Gherkin scenarios (1 happy toggle + 1 persistence + 1 negative FOUC + 1 edge agent tokens + 1 a11y + 1 i18n + 1 adversarial N/A + 1 not_applicable batch 7 sub-categorías). Sub-categorías v4.1: a11y + i18n covered explicit, race/concurrent/network/empty/large/mobile/loading N/A con razón. Mockup HTML producido (4 states), pendiente Chris ratify visual + spec whole-doc. |
