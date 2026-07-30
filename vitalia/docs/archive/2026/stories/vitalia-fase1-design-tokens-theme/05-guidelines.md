<!-- voseo-allowed: internal guidelines documentation, FE-only story -->

# F1-S1 `vitalia-fase1-design-tokens-theme` — 05-guidelines

> Patterns required + forbidden + files in scope + skills/rules a cargar para builder (Sonnet ejecuta T-1..T-7).

## § 1 — Patterns required

### § 1.1 — next-themes integration verbatim D1+D4

- `<ThemeProvider attribute="data-theme" defaultTheme="light" enableSystem={false} storageKey="vitalia-theme">` props **verbatim** en `layout.tsx`.
- `attribute="data-theme"` setea `<html data-theme="light|dark">` (NO `class="dark"`).
- `defaultTheme="light"` — light por default (D1 ratificada).
- `enableSystem={false}` — NO soportar OS system theme (D1 — scope minimal F1).
- `storageKey="vitalia-theme"` — namespaced defense-in-depth (D4).

### § 1.2 — `<html lang="es" suppressHydrationWarning>` obligatorio

- next-themes inyecta script inline `<head>` que setea `data-theme` ANTES de hydration React.
- React emite hydration warning legítimo (server emite sin attribute, client tiene). `suppressHydrationWarning` silencia (es comportamiento esperado, no bug).
- Sin esto → Scenario 3 (negative FOUC) atrapa con console error + build production fail.

### § 1.3 — useTheme import directo (D5)

- `import { useTheme } from 'next-themes'` directo en `ThemeToggle.tsx`.
- **NO** crear wrapper `vitalia/frontend/src/hooks/useTheme.ts` (D5 ratificada — scope minimal).
- Si futuro tracking/analytics theme changes → agregar wrapper en story dedicada.

### § 1.4 — Shadcn Button ghost icon variant

- `<Button variant="ghost" size="icon">` — primitive instalado F1-S0.
- Sin background, sin border, hover muestra `--accent` sutil.
- Focus-visible ring vía Shadcn defaults (`focus-visible:ring-2 focus-visible:ring-ring`).
- **NO** crear nuevo button style — reuse primitive.

### § 1.5 — Lucide Moon + Sun icons

- `import { Moon, Sun } from 'lucide-react'` — lucide-react ya instalado F1-S0 via Shadcn deps.
- Conditional icon: Moon visible cuando theme=light (sugiere "switch to dark"); Sun visible cuando theme=dark.
- Size: `className="h-[1.2rem] w-[1.2rem]"` — consistent con Shadcn examples.
- **NO** usar custom SVGs ni emoji.

### § 1.6 — aria-label dinámico Spanish neutro

- Pattern verbatim: `` `Cambiar tema (actual: ${isDark ? 'oscuro' : 'claro'})` ``
- Regex match: `/^Cambiar tema \(actual: (claro|oscuro)\)$/`
- **NO** voseo (`vos/sos/tenés/cambiá`). Verbatim glosario `.claude/rules/spanish-text.md`.

### § 1.7 — aria-pressed boolean dinámico

- `aria-pressed={isDark}` — toggle button semantic per ARIA spec.
- `"true"` cuando dark active, `"false"` cuando light active.

### § 1.8 — data-testid="theme-toggle" para Playwright

- Selector estable que no depende de className/role drift.
- Único en la página (cada test page renderiza 1 ThemeToggle).

### § 1.9 — Tailwind v4 `darkMode` config

- `darkMode: ['class', '[data-theme="dark"]']` — honra next-themes attribute.
- Tailwind v4 default `darkMode: 'media'` activa via prefers-color-scheme OS (NO queremos).
- Config explícito es **crítico** para que variants `dark:` se activen cuando `<html data-theme="dark">`.

### § 1.10 — CSS vars verbatim Design Contract § 5.1

- `:root` + `.dark` blocks con TODAS las Shadcn-standard vars + agent tokens.
- Format HSL space-separated (no commas): `--primary: 198 99% 49%`.
- Comments preservados para referencia humana (`/* #01b2f8 */`).

### § 1.11 — Preserve `.vt-*` legacy block intacto

- `globals.css` tiene bloque `.vt-bg-*`, `.vt-text-*`, etc. con colores hardcoded.
- **NO** tocar — deprecación final es F2-S23 `vitalia-fase2-vt-deprecation-final`.
- Verify post-F1-S1 que goldens regression `dashboard-legacy-{light,dark}.png` siguen GREEN.

### § 1.12 — TDD RED → GREEN per validator

- ThemeToggle.test.tsx: tests escritos ANTES de implementar ThemeToggle.tsx (RED).
- Playwright specs: escritos ANTES de implementar test page fixture (RED para fixture, GREEN cuando component renderiza).
- Vitest introspection: escrito ANTES de completar globals.css (RED para vars faltantes, GREEN post-completion).

### § 1.13 — Spanish neutro LatAm (overlay vitalia + root)

- Aplicar a aria-label, sr-only text, comments user-facing si existieran.
- Pre-commit hook `scripts/git-hooks/pre-commit` Section 5 voseo scan auto en files staged.

### § 1.14 — NATIVE Linux host execution (no Docker tests)

- `make e2e*` PROHIBIDO (Docker, crashea local).
- Comandos via `cd vitalia/frontend && npx playwright test ...` con `E2E_BASE_URL=http://localhost:3002` (port vitalia per `docs/process/docker-dev-multibrand.md`).
- Vitest: `cd vitalia/frontend && npx vitest run`.

### § 1.15 — Playwright @project=visual config heredado F1-S0

- `maxDiffPixelRatio: 0.001` (0.1%)
- `animations: 'disabled'`
- `caret: 'hide'`
- **NO** tocar `playwright.config.ts` (config estable post-F1-S0).

### § 1.16 — Goldens regression F1-S0 verify GREEN post-F1-S1

- `dashboard-legacy-{light,dark}.png` — transparent legacy verify
- `agent-tokens-swatch-{light,dark}.png` — completion vars verify

---

## § 2 — Patterns forbidden

- ❌ Editar `(dashboard)/` legacy pages o `.vt-*` legacy block en `globals.css`
- ❌ Crear theme picker custom o dropdown 3-state (D1 ratificada light/dark only)
- ❌ `enableSystem={true}` (D1 ratificada)
- ❌ Crear `.stories.tsx` Storybook stories (D3 ratificada — N/A F1-S1)
- ❌ Crear `vitalia/frontend/src/hooks/useTheme.ts` wrapper (D5 ratificada)
- ❌ Cross-brand imports (`from "nicolify/..."` o `from "comunify/..."` etc.)
- ❌ Cross-feature imports (FSD-Lite boundaries ESLint enforce)
- ❌ Hex hardcoded en `ThemeToggle.tsx` (consume tokens vía Shadcn Button primitive)
- ❌ Default exports (`export default function ThemeToggle`) — usar `export function ThemeToggle()` named
- ❌ `any` TypeScript (ESLint rule activa)
- ❌ `eslint-disable` sin justification comment
- ❌ Importar `core/luana-core-*` o `@luana/*` (story 100% FE local vitalia)
- ❌ Hardcoded paths absolutos (`/home/chalreme/...`) en código o tests
- ❌ Frameworks no-Tailwind/no-Shadcn (NO Bootstrap, NO Material UI, NO Chakra)
- ❌ Tocar `playwright.config.ts` (config heredada estable)
- ❌ `make e2e*` o `docker exec` para tests (anti-pattern violatorio `.claude/rules/e2e-testing.md`)
- ❌ Editar mockup `theme-toggle.html` post-architect ratify (re-ratify Chris requerido)
- ❌ Skip `suppressHydrationWarning` en `<html>` (rompe hydration silent — Scenario 3 detecta)
- ❌ Tocar `vitalia/backend/` (story FE-only)
- ❌ Tocar `vitalia/.claude/rules/` o `.claude/rules/` (overlay/root rules)

---

## § 3 — Files in scope (Sonnet edits ONLY these)

### § 3.1 — MODIFY (5)

| Path | Justificación |
|---|---|
| `vitalia/frontend/package.json` | + `"next-themes": "^0.3.0"` dependency |
| `vitalia/frontend/package-lock.json` | lockfile diff post `npm install` |
| `vitalia/frontend/src/app/globals.css` | Completar Shadcn vars verbatim Design Contract § 5.1 (light + dark) |
| `vitalia/frontend/tailwind.config.ts` | Verify/complete colors extend + `darkMode: ['class', '[data-theme="dark"]']` config |
| `vitalia/frontend/src/app/layout.tsx` | Wrap `<ThemeProvider>` + `<html lang="es" suppressHydrationWarning>` |

### § 3.2 — NEW (9)

| Path | Tipo |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` | Client component (named export) |
| `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.test.tsx` | Vitest unit |
| `vitalia/frontend/e2e/__test-pages__/design-tokens-theme/theme-toggle-showcase.tsx` | Test page fixture |
| `vitalia/frontend/e2e/regression/design-tokens-theme/theme-toggle-interaction.spec.ts` | Playwright behavior |
| `vitalia/frontend/e2e/visual/design-tokens-theme/theme-toggle.spec.ts` | Playwright @project=visual |
| `vitalia/frontend/e2e/a11y/design-tokens-theme/theme-toggle.spec.ts` | Playwright + axe-core |
| `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-light.png` | Visual golden (Chris ratify) |
| `vitalia/frontend/e2e/__screenshots__/design-tokens-theme/theme-toggle-dark.png` | Visual golden (Chris ratify) |
| `vitalia/frontend/src/__tests__/tokens/test-shadcn-vars-resolvable.test.ts` | Vitest introspection |

---

## § 4 — Files NEVER touches

- `core/luana-core-*/` (engine — requeriría /pm-luana promotion gate)
- `nicolify/`, `comunify/`, `lupulo/` (cross-brand prohibido)
- `vitalia/frontend/src/app/[tenantId]/(dashboard)/` (legacy — transparent post ThemeProvider wrap)
- `vitalia/frontend/src/components/ui/*` (Shadcn primitives instalados F1-S0 — NO modificar)
- `vitalia/frontend/src/app/globals.css` bloque `.vt-*` legacy (preservar intacto)
- `vitalia/frontend/playwright.config.ts` (config estable heredada F1-S0)
- `vitalia/.claude/`, `.claude/` (skills/rules — meta-paradigm change requiere escalate)
- `vitalia/backend/` (story FE-only)
- `vitalia/config/brand.yaml` (no requiere flag flip)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (atomic design SSoT — consume verbatim, NO modify)
- `mockups/theme-toggle.html` post-architect (ratificado Chris — re-ratify si modifies)

---

## § 5 — Must load skills (v4.1 enforceable verbatim list)

Cargar ANTES de empezar implementación:

1. **`frontend-expert`** — FSD-Lite, Tailwind tokens, Shadcn reuse, component placement (`components/shared/shell-organism/` correct)
2. **`playwright-expert`** — POM patterns, @project=visual config, axe-core a11y, anti-Docker mandate, freshness gate
3. **`tessl__shadcn-ui`** — Button ghost icon variant patterns
4. **`tessl__tailwind`** — darkMode config Tailwind v4, dark mode custom selector
5. **`tessl__vitest`** — unit test patterns, render/fireEvent/screen testing-library
6. **`tessl__nextjs-app-router-modularization`** — layout.tsx wrap pattern, suppressHydrationWarning requirement, Server-First
7. **`.claude/rules/frontend-fsd.md`** — FSD-Lite boundary matrix (ThemeToggle bajo `components/shared/shell-organism/` permitido)
8. **`.claude/rules/spanish-text.md`** — aria-label voseo check glosario
9. **`.claude/rules/anti-duplication.md`** — no mirror cross-brand (ThemeToggle vitalia-local justificado)
10. **`.claude/rules/tdd-mandatory.md`** — TDD RED→GREEN per layer
11. **`vitalia/.claude/rules/shell-mockup-per-component.md`** — CONSUME (F1-S1 applied, mockup ratificado pre-architect ✓)
12. **`vitalia/.claude/rules/hipaa-lite.md`** — CONSUME (no-phi-scope declared, F1-S1 es UI shell sin PHI)

---

## § 6 — Reference artifacts

1. **`01-spec.md`** — Gherkin 8 scenarios + 22 AC operacionales + 5 decisiones D1-D5 cementadas
2. **`mockups/theme-toggle.html`** — visual contract ratificado Chris 2026-05-22 (4 states card neutral)
3. **`03-arch.md`** — this story's architecture (this dir)
4. **`04-validators.yaml`** § test_construction_plan + § scenario_coverage_map
5. **`vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`** § 5.1 (CSS vars verbatim) + § 5.2 (Tailwind extend verbatim)
6. **`../vitalia-fase1-stack-stability/03-arch.md`** — predecessor F1-S0 (Shadcn install + base vars + tailwind extend `colors.agent.*`)

---

## § 7 — Reproducible verification commands

Para builder durante build (sirve también para Chris verify manual post-merge):

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# 1. TypeScript strict
npx tsc --noEmit

# 2. ESLint 0 errors
npx eslint src/ --max-warnings 0

# 3. Prettier format check
npx prettier --check src/components/shared/shell-organism/

# 4. Vitest unit + introspection
npx vitest run

# 5. Production build (catchea Scenario 3 FOUC)
npm run build

# 6. Playwright behavior (Scenarios 1+2+3)
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=regression --grep design-tokens-theme

# 7. Playwright visual goldens (Scenarios 1 + 4 + cross-cutting transparent)
npx playwright test --project=visual --grep "design-tokens-theme|agent-tokens-swatch|dashboard-legacy"

# 8. Playwright a11y (Scenario 5)
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=a11y --grep design-tokens-theme

# 9. Visual goldens update (first generation post-implementation — Chris ratify pre-commit)
npx playwright test --project=visual --grep design-tokens-theme/theme-toggle --update-snapshots

# 10. Live verify Chris (dev stack)
make dev-vitalia
# Chris abre http://localhost:3002/__test-pages__/design-tokens-theme/theme-toggle-showcase
# Click toggle, verify visual + behavior end-to-end
```

**Expected:** todos los comandos retornan exit code 0.

