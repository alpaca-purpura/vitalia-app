---
story_id: vitalia-fase1-stack-stability
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell                                  # transversal — no es de un agente
module: shell-organism / infra
capability: shell.foundation
state: done
phase_state: MERGED_ARCHIVED
last_artifact: 07-merge.md
last_modified: 2026-05-23
merged_at: 2026-05-23T01:35:00-05:00
merged_via_squash: pending  # squash de wip/vitalia → main al cierre Fase 1 completo (F1-S0..S10)
archive_path: vitalia/docs/archive/2026/stories/vitalia-fase1-stack-stability/
capability_promoted: vitalia/docs/product/capabilities/platform/shell-foundation-shadcn-tailwind-v4.yaml
developing_started_at: 2026-05-22T21:30:00-05:00
developing_completed_at: 2026-05-22T23:59:00-05:00
developing_owner: /dev-team (autonomous Sonnet/Opus per R23)
reviewing_started_at: 2026-05-23T00:30:00-05:00
reviewing_owner: /auditor (direct examination + in-loop fixes con Chris ratify cycle 2026-05-23T00:30 → 01:30)
audit_verdict: APPROVED
audit_verdict_ratified_by: chris
audit_verdict_ratified_at: 2026-05-23T01:30:00-05:00
audit_verdict_reason: "ESCALATED inicial resuelto in-loop con 6 fixes acumulados (Fix #1-4 commit 1a296b56 + Fix #5-6 commit 2d105e7e). Tailwind v4 PostCSS setup + agent SSoT + avatares ring color + cursor pointer + hover contrast defensive + 6 goldens Playwright ratificados Chris visualmente. Ver 06-audit/CHECKPOINTS.md § Resolución de Chris gates (post-ESCALATED in-loop session)."
chain_plan: "F1-S0 → F1-S1 → F1-S2 → F1-S3 secuencial (WIP cap developing ≤ 1) · auto-handoff /auditor on developed · auto-handoff /pm-vitalia merge on APPROVED · ratificado Chris 2026-05-22"
ratified_by_chris: true
ratified_visual_by_chris: not_applicable
ratified_visual_reason: "F1-S0 EXENTA del protocolo mockup-per-component (ADR-vitalia-003 § Excepciones) — es infra-only, no construye componentes user-facing nuevos"
po_ux_iterations: 3
parallel_safe: false                                 # blocker hard de toda Fase 1
priority: critical
estimated_dev_weeks: 0.5-1
# Escalations pendientes (no bloquean auditor):
# 1. marketing-nuqs-ssr-fix: url-state.ts parseAsStringEnum sin "use client" → next build fails (pre-existing, commit ac7b3e91)
# 2. T-4 goldens deferred: requires make dev-vitalia at :3002 + Chris ratify
# 3. .next Docker permissions: infra issue root-owned .next/dev
dependencies:
  hard: []                                           # no depende de nada
  soft: []
service_blockers: []
blocks_hard:                                          # esta story bloquea TODAS estas:
  - vitalia-fase1-design-tokens-theme
  - vitalia-fase1-topbar-global
  - vitalia-fase1-tenant-switcher
  - vitalia-fase1-shell-layout-5050
  - vitalia-fase1-valeria-rail-history
  - vitalia-fase1-valeria-chat-skeleton
  - vitalia-fase1-ribbon-6-tabs
  - vitalia-fase1-sub-tabs-line2
  - vitalia-fase1-routing-shell
  - vitalia-fase1-empty-states
reuse_map_summary: "infra-only — verifica Tailwind v4 + instala Shadcn + plan deprecación .vt-* (no migra contenido todavía)"
spawned_at: 2026-05-22
spawned_by: /pm-vitalia (post shell-organism cement)
next_action: "DONE — story archived. Próximo en chain: F1-S1 vitalia-fase1-design-tokens-theme transición ready → developing → /dev-team build."

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: shell-foundation-shadcn-tailwind-v4   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-fase1-stack-stability — checkpoint

## Goal

Preparar la base técnica para todas las stories Fase 1: verificar que Tailwind v4 renderiza correctamente, instalar Shadcn UI con tokens Vitalia, agregar tokens nuevos (agentes Lisa #00D084 + Lucas #111111), definir plan de deprecación incremental de las 150+ utility classes `.vt-*`, y dejar el dev stack arrancando limpio para que F1-S1 onwards puedan empezar inmediatamente.

## Anti-objetivos

- NO migrar `.vt-*` existentes a Tailwind directo (eso es otra story dedicada al final de Fase 2)
- NO crear componentes nuevos (eso son F1-S1+)
- NO tocar route group `(shell-organism)/` (eso es F1-S4)
- NO modificar `(dashboard)/` legacy

## Scope verbatim

### § 1 — Verificar Tailwind v4 runtime

Bug origen: learning 2026-05-21 `vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md` reportó "Tailwind no renderiza en runtime". Subagent Explore 2026-05-22 reportó "Tailwind v4 operativo". Resolver discrepancia empíricamente.

**Verificación:**
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}
make dev-vitalia
# Esperar ~30s arranque
xdg-open http://localhost:3002
# Visual check: ¿páginas renderizan con estilos? ¿Tailwind classes aplican?
```

**Resultado posible 1 — Tailwind OK:** skip fix, proceder a § 2 install Shadcn.
**Resultado posible 2 — Tailwind ROTO:** diagnosticar root cause:
- ¿PostCSS config?
- ¿`@tailwind` directives en globals.css?
- ¿Turbopack vs Webpack?
- ¿Tailwind v4 plugin compat React 19?

Documentar fix en T-impl-log + commit con detalle.

### § 2 — Instalar Shadcn UI

```bash
cd ${WS}/vitalia/frontend

# Init Shadcn con configuración Vitalia
npx shadcn@latest init
# Prompts:
#   Style: New York
#   Base color: Slate
#   CSS variables: yes
#   Tailwind config: existing
#   Import alias: @/ (already configured)

# Verificar components.json creado
ls components.json
cat components.json
```

Esperado: archivo `vitalia/frontend/components.json` versionado con config.

### § 3 — Instalar primitivos base Design Contract § 3.1

```bash
cd ${WS}/vitalia/frontend
npx shadcn@latest add button avatar dropdown-menu input badge textarea tabs tooltip
```

Esperado: `vitalia/frontend/src/components/ui/{button,avatar,dropdown-menu,input,badge,textarea,tabs,tooltip}.tsx` creados.

### § 4 — Agregar tokens nuevos agentes

Editar `vitalia/frontend/src/app/globals.css`:

```css
@layer base {
  :root {
    /* ... vars existentes Shadcn (post init) ... */

    /* === Vitalia agent tokens === */
    --agent-lisa: 156 100% 41%;           /* #00D084 — NEW */
    --agent-lisa-soft: 156 80% 92%;
    --agent-lucas: 0 0% 7%;               /* #111111 — NEW */
    --agent-lucas-soft: 0 0% 92%;
    --agent-adrian: 198 99% 49%;          /* #01b2f8 = primary */
    --agent-adrian-soft: 197 90% 89%;
    --agent-valeria: 287 53% 37%;         /* #7b2d91 = accent */
    --agent-valeria-soft: 287 53% 90%;
    --agent-camila: 244 84% 32%;          /* #180d95 */
    --agent-camila-soft: 244 53% 92%;
    --agent-mateo: 53 99% 51%;            /* #fee209 — transversal */
    --agent-config: 240 4% 46%;           /* neutral gray */
  }

  .dark {
    /* ... vars dark Shadcn ... */
    --agent-lisa-soft: 156 60% 15%;
    --agent-lucas-soft: 0 0% 20%;
    --agent-adrian-soft: 198 60% 20%;
    --agent-valeria-soft: 287 40% 25%;
    --agent-camila-soft: 244 50% 20%;
  }
}
```

Editar `vitalia/frontend/tailwind.config.ts` colors.extend agregando agentes (ver Design Contract § 5.2 verbatim).

### § 5 — Plan deprecación `.vt-*` (DOCUMENTAR, NO EJECUTAR migración)

Crear `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md` con:

1. **Inventario:** scan de `globals.css` para listar las 150+ `.vt-*` classes
2. **Estrategia compatibilidad temporal:** las `.vt-bg-*`, `.vt-text-*`, `.vt-border-*` quedan apuntando a las nuevas CSS vars Shadcn-style. Sin breaking change inmediato.
3. **Migration policy:** cuando una feature shipped se migra al shell-organism (Fase 2), su código refactoriza a Tailwind directo
4. **Final drop:** story dedicada al final de Fase 2 (`vitalia-fase2-vt-deprecation-final`)
5. **Arch fitness test NEW:** `vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts` — falla si nuevo código bajo `(shell-organism)/` usa `.vt-*` class

### § 6 — Verificación dev stack post-cambios

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# 1. Type check
npx tsc --noEmit

# 2. Lint
npx eslint src/ --max-warnings 0

# 3. Tests existentes (regresión)
npx vitest run

# 4. Build production (verifica Tailwind + Shadcn + tokens)
npm run build

# 5. Dev runtime (visual)
cd ${WS} && make dev-vitalia
# Browser http://localhost:3002 → verify NO console errors + estilos aplican
```

### § 7 — Crear arch fitness test deprecación

```ts
// vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

describe('arch: no .vt-* classes in shell-organism code', () => {
  it('shell-organism route group + new shared components NO use .vt-*', () => {
    const SHELL_PATHS = [
      'src/app/[tenantId]/(shell-organism)',
      'src/components/shared/shell-organism',
    ]
    const VT_PATTERN = /\bvt-[a-z]/

    const offenders: string[] = []
    for (const p of SHELL_PATHS) {
      // recursive scan .tsx/.ts files
      // if file content matches VT_PATTERN → push offender
    }
    expect(offenders).toEqual([])
  })
})
```

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | `make dev-vitalia` arranca sin errors en console (browser + terminal) |
| AC-2 | http://localhost:3002 renderiza con estilos Tailwind aplicados (heading typography + colors visibles) |
| AC-3 | `components.json` existe + config Shadcn correcta |
| AC-4 | `src/components/ui/{button,avatar,dropdown-menu,input,badge,textarea,tabs,tooltip}.tsx` existen |
| AC-5 | Import test: `import { Button } from '@/components/ui/button'` funciona sin errors |
| AC-6 | `globals.css` tiene CSS vars `--agent-lisa`, `--agent-lucas`, etc. |
| AC-7 | `tailwind.config.ts` `colors.agent.{name}` accesibles vía Tailwind classes (ej. `bg-agent-lisa`) |
| AC-8 | ADR-vitalia-002 escrito + ratificado |
| AC-9 | Arch fitness test creado (PASS — sin código shell-organism todavía) |
| AC-10 | `npx tsc --noEmit` 0 errors |
| AC-11 | `npx eslint src/` 0 errors |
| AC-12 | `npm run build` PASS |
| AC-13 | Tests existentes regresión PASS |

## Gherkin scenarios

### Scenario 1 — happy-path

**Given:** Repo clonado limpio, dependencias instaladas

**When:** Developer ejecuta `make dev-vitalia`

**Then:**
- Stack arranca sin errors
- http://localhost:3002 carga
- Tailwind classes (ej. `bg-blue-500`, `text-gray-800`) renderizan correctamente
- DevTools Console NO muestra "Failed to fetch CSS" o equivalente

**playwright_required:** true (smoke spec ya existe en `vitalia/frontend/e2e/`)

### Scenario 2 — Tailwind v4 bug detectado (negative)

**Given:** `make dev-vitalia` arrancado

**When:** Browser muestra HTML sin estilos aplicados (raw browser default)

**Then:**
- Developer documenta repro en T-impl-log
- Diagnosis incluye: PostCSS config check + `@tailwind` directives check + Turbopack mode check + Tailwind v4 plugin React 19 compat
- Fix aplicado + verificado visualmente
- Story NO se cierra hasta AC-2 pass

### Scenario 3 — Shadcn primitivo render correcto (happy)

**Given:** Shadcn instalado + Button primitive copy-paste local

**When:** Crear test page con `<Button variant="default">Hello</Button>`

**Then:**
- Botón renderiza con estilos Shadcn (padding · border-radius · color)
- Hover state funciona (color shift)
- Funcional click handler funciona

**playwright_required:** false (Vitest suffices)

### Scenario 4 — Agent tokens accessible (happy)

**Given:** `globals.css` + `tailwind.config.ts` actualizados

**When:** En test component usar `<div className="bg-agent-lisa">test</div>`

**Then:**
- Background color = `#00D084` (green Lisa)
- Si dark mode → `--agent-lisa-soft` aplica

## Deliverables (files producidos por esta story)

| File | Acción |
|---|---|
| `vitalia/frontend/components.json` | NEW (post `shadcn init`) |
| `vitalia/frontend/src/components/ui/button.tsx` | NEW |
| `vitalia/frontend/src/components/ui/avatar.tsx` | NEW |
| `vitalia/frontend/src/components/ui/dropdown-menu.tsx` | NEW |
| `vitalia/frontend/src/components/ui/input.tsx` | NEW |
| `vitalia/frontend/src/components/ui/badge.tsx` | NEW |
| `vitalia/frontend/src/components/ui/textarea.tsx` | NEW |
| `vitalia/frontend/src/components/ui/tabs.tsx` | NEW |
| `vitalia/frontend/src/components/ui/tooltip.tsx` | NEW |
| `vitalia/frontend/src/app/globals.css` | MODIFY (agregar agent tokens) |
| `vitalia/frontend/tailwind.config.ts` | MODIFY (agregar colors.agent.*) |
| `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md` | NEW |
| `vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts` | NEW |
| `vitalia/frontend/package.json` | MODIFY (add Shadcn deps: @radix-ui/*, class-variance-authority, clsx, tailwind-merge, lucide-react si no existe) |
| `vitalia/frontend/src/lib/utils.ts` | NEW or MODIFY (cn() helper de Shadcn) |

## Próximo paso post-done

Story F1-S1 `vitalia-fase1-design-tokens-theme` arranca refining → ready → developing. Ya con Shadcn instalado + agent tokens disponibles.
