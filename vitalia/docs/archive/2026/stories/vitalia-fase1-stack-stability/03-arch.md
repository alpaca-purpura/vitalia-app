<!-- voseo-allowed: internal architecture documentation, infra-only story -->

---
brand: vitalia
story_id: vitalia-fase1-stack-stability
state: ready
depends_on: []
blocks:
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
target_version: 1.0
written_at: 2026-05-22
sub_architect: /architect (single-shot full-stack — FE-only story)
arch_version: 1
links:
  spec: "01-spec.md"
  design_contract: "../../../architecture/SHELL-DESIGN-CONTRACT.md"
  adr_002_target: "../../../architecture/ADR-vitalia-002-vt-deprecation-plan.md"
  adr_003_protocol: "../../../architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md"
  rule_shell_mockup: "../../../../.claude/rules/shell-mockup-per-component.md"
  rule_hipaa: "../../../../.claude/rules/hipaa-lite.md"
  rule_fsd: "../../../../../.claude/rules/frontend-fsd.md"
---

# F1-S0 vitalia-fase1-stack-stability — 03-arch

## § 0 — Context Summary

**Story type:** infra-only FE bootstrap (single-shot full-stack — no BE, no AGENTIC surface).
**Architect run on:** 2026-05-22
**Modules touched:** `vitalia/frontend/` ONLY.

**Surface → builder → auditor mapping:**

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/**` (Shadcn install + tokens + Playwright visual + arch test + ADR doc) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/backend/**` | **N/A** — story 100% FE | N/A |
| Agentic surfaces (`copilot/`, `sales_agent/`) | **N/A** | N/A |

**Skills consulted:**
- `frontend-expert`: FSD-Lite boundaries + arch fitness ratchet shrink-only
- `playwright-expert`: `@project=visual` config + goldens generation + maxDiffPixelRatio 0.001
- `tessl__shadcn-ui`: copy-paste vendored pattern (NO npm package)
- `tessl__tailwind`: theme.extend.colors.agent.* via CSS vars HSL formato
- `vitalia/.claude/rules/shell-mockup-per-component.md` (consume — F1-S0 declarada exenta per ADR-vitalia-003 § Excepciones)
- `vitalia/.claude/rules/hipaa-lite.md` (consume — **no-phi-scope declared**: F1-S0 NO toca rutas autenticadas ni tablas PHI)

**Engine boundaries:** F1-S0 NO toca `core/luana-core-*/`. NO importa `luana_core_*` ni `@luana/*`. NO toca otros brands.

**capability YAML files affected (post-merge updates required):** N/A — F1-S0 es infra UI bootstrap, no expone capability funcional user-facing. Capabilities entrarán Fase 1 stories siguientes (F1-S2..S10).

**Architecture gates that must keep passing:**
- `vitalia/frontend/src/__tests__/architecture/*.test.ts` (FSD-Lite boundaries existentes)
- `vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts` (NEW arch test creado en T-5)

**CONTEXT-BRIEF source:** self-ran greps + direct reads (CONTEXT-BRIEF.md no presente; story es small + ratificada whole-doc por Chris).

---

## § 1 — Surfaces involved

### § 1.1 — FE only (100%)

`vitalia/frontend/` recibe:
- Install Shadcn UI + 8 primitivos copy-paste (`button avatar dropdown-menu input badge textarea tabs tooltip`)
- CSS vars Shadcn-standard + 7 agent tokens (`--agent-{lisa,lucas,adrian,valeria,camila,mateo,config}` + soft variants)
- `tailwind.config.ts` extend theme.colors (Shadcn base + agent.*)
- `src/lib/utils.ts` con `cn()` helper estándar Shadcn
- `playwright.config.ts` `@project=visual` block
- 2 test pages auxiliares Playwright (`primitives-showcase.tsx`, `agent-tokens-swatch.tsx`)
- 1 spec Playwright visual baseline + 6 goldens
- 1 arch fitness test NEW (`test-no-vt-classes-in-new-features.test.ts`)
- 1 ADR doc NEW (`vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md`)

### § 1.2 — BE explicitly N/A

**Reason:** F1-S0 NO introduce endpoints, DTOs, models, migraciones, services, ni repositorios. Es 100% infra FE local. Stack `make dev-vitalia` reusa BE shipped Vitalia sin cambios.

### § 1.3 — AGENTIC explicitly N/A

**Reason:** F1-S0 NO toca `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/`. NO modifica tools, prompts, slots cache, LangGraph state, ni eval goldens. Owner `builder-agentic` NO se invoca para esta story.

---

## § 2 — FE architecture detail

### § 2.1 — Shadcn install pattern (vendored copy-paste, NOT npm package)

`components.json` config verbatim post `npx shadcn@latest init`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

8 primitivos instalados via `npx shadcn@latest add button avatar dropdown-menu input badge textarea tabs tooltip`:

| # | Primitive | Path post-install |
|---|---|---|
| 1 | Button | `vitalia/frontend/src/components/ui/button.tsx` |
| 2 | Avatar | `vitalia/frontend/src/components/ui/avatar.tsx` |
| 3 | DropdownMenu | `vitalia/frontend/src/components/ui/dropdown-menu.tsx` |
| 4 | Input | `vitalia/frontend/src/components/ui/input.tsx` |
| 5 | Badge | `vitalia/frontend/src/components/ui/badge.tsx` |
| 6 | Textarea | `vitalia/frontend/src/components/ui/textarea.tsx` |
| 7 | Tabs | `vitalia/frontend/src/components/ui/tabs.tsx` |
| 8 | Tooltip | `vitalia/frontend/src/components/ui/tooltip.tsx` |

Shadcn CLI agrega automáticamente al `package.json`:
- `@radix-ui/react-{avatar,dropdown-menu,tabs,tooltip,slot,label}`
- `class-variance-authority`
- `clsx` + `tailwind-merge`
- `lucide-react`

Lockfile `package-lock.json` MUST committed con SHA pin de cada dep.

### § 2.2 — CSS vars schema (verbatim Design Contract § 5.1)

`vitalia/frontend/src/app/globals.css` recibe 2 bloques NEW + preserva bloque `.vt-*` legacy intacto.

```css
@layer base {
  :root {
    /* Surface Shadcn standard */
    --background: 0 0% 100%;
    --foreground: 240 10% 4%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 4%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 4%;
    --primary: 198 99% 49%;
    --primary-foreground: 0 0% 100%;
    --secondary: 240 5% 96%;
    --secondary-foreground: 240 6% 10%;
    --muted: 240 5% 96%;
    --muted-foreground: 240 4% 46%;
    --accent: 287 53% 37%;
    --accent-foreground: 0 0% 100%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 6% 90%;
    --input: 240 6% 90%;
    --ring: 198 99% 49%;
    --radius: 0.625rem;

    /* Agent tokens — 7 base + 6 soft variants */
    --agent-lisa: 156 100% 41%;          /* #00D084 NEW */
    --agent-lisa-soft: 156 80% 92%;
    --agent-lucas: 0 0% 7%;              /* #111111 NEW */
    --agent-lucas-soft: 0 0% 92%;
    --agent-adrian: 198 99% 49%;         /* #01b2f8 = primary */
    --agent-adrian-soft: 197 90% 89%;
    --agent-valeria: 287 53% 37%;        /* #7b2d91 */
    --agent-valeria-soft: 287 53% 90%;
    --agent-camila: 244 84% 32%;         /* #180d95 */
    --agent-camila-soft: 244 53% 92%;
    --agent-mateo: 53 99% 51%;           /* #fee209 */
    --agent-config: 240 4% 46%;          /* neutral gray */
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

    /* Agent dark soft variants */
    --agent-lisa-soft: 156 60% 15%;
    --agent-lucas-soft: 0 0% 20%;
    --agent-adrian-soft: 198 60% 20%;
    --agent-valeria-soft: 287 40% 25%;
    --agent-camila-soft: 244 50% 20%;
  }
}
```

**Crítico:** bloque `.vt-*` legacy (150+ utility classes) NO se elimina en F1-S0. Estrategia deprecación progresiva documentada en ADR-vitalia-002 § 3 (las `.vt-*` apuntan a las nuevas CSS vars `--background`, `--foreground`, etc., para compatibilidad temporal sin romper `(dashboard)/` shipped).

### § 2.3 — tailwind.config.ts extend theme.colors

```ts
// vitalia/frontend/tailwind.config.ts (extend existing)
export default {
  // ... config existente preserved
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
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
}
```

### § 2.4 — src/lib/utils.ts cn() helper Shadcn estándar

```ts
// vitalia/frontend/src/lib/utils.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
```

Si `utils.ts` ya existe en Vitalia shipped (verificar pre-install), agregar `cn()` named export (no sobreescribir helpers existentes).

### § 2.5 — playwright.config.ts @project=visual block

```ts
// vitalia/frontend/playwright.config.ts (extend existing)
projects: [
  // ... smoke, a11y, mobile existentes preserved
  {
    name: 'visual',
    use: {
      ...devices['Desktop Chrome'],
      viewport: { width: 1440, height: 900 },
      colorScheme: 'light',
    },
    snapshotPathTemplate: 'e2e/__screenshots__/{testFilePath}/{arg}{ext}',
    expect: {
      toHaveScreenshot: {
        maxDiffPixelRatio: 0.001,  // 0.1% tolerance
        animations: 'disabled',
        caret: 'hide',
      },
    },
  },
]
```

Verbatim Design Contract § 9.4. Si `playwright.config.ts` ya tiene `projects` array, agregar `visual` como nuevo entry sin tocar los otros.

### § 2.6 — Test pages auxiliares + spec visual baseline

**Test pages (fixtures Playwright, NO rutas Next.js prod):**

```
vitalia/frontend/e2e/__test-pages__/stack-stability/
├── primitives-showcase.tsx       # renderiza 8 primitivos × variantes
└── agent-tokens-swatch.tsx       # renderiza 7 swatches color + label hex
```

`primitives-showcase.tsx` skeleton:

```tsx
'use client'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'

export function PrimitivesShowcase(): React.ReactElement {
  return (
    <main className="bg-background text-foreground p-8 space-y-8">
      <section aria-label="buttons">
        <Button variant="default">Default</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="destructive">Destructive</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="link">Link</Button>
      </section>
      {/* ... resto de 8 primitivos */}
    </main>
  )
}
```

**Spec Playwright visual baseline:**

```
vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts
```

Genera 6 goldens (light + dark cada uno):
- `dashboard-legacy-{light,dark}.png` — regression `(dashboard)/` shipped
- `shadcn-primitives-{light,dark}.png` — 8 primitivos showcase
- `agent-tokens-swatch-{light,dark}.png` — 7 agent swatches

**Goldens path:** `vitalia/frontend/e2e/__screenshots__/stack-stability/`

### § 2.7 — Arch fitness test test-no-vt-classes-in-new-features.test.ts

```ts
// vitalia/frontend/src/__tests__/architecture/test-no-vt-classes-in-new-features.test.ts
import { describe, it, expect } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'fs'
import { join } from 'path'

const SHELL_PATHS = [
  'src/app/[tenantId]/(shell-organism)',
  'src/components/shared/shell-organism',
]
const VT_PATTERN = /\bvt-[a-z]/

function* walkFiles(dir: string): Generator<string> {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) yield* walkFiles(full)
    else if (/\.(tsx?|css)$/.test(entry)) yield full
  }
}

describe('no .vt-* classes in shell-organism new features (ADR-vitalia-002 § 6)', () => {
  it('every file under SHELL_PATHS is free of .vt-* utility classes', () => {
    const root = process.cwd()
    const offenders: string[] = []
    for (const relPath of SHELL_PATHS) {
      const abs = join(root, relPath)
      let exists = false
      try { statSync(abs); exists = true } catch { /* path doesnt exist yet — GREEN by emptiness */ }
      if (!exists) continue
      for (const f of walkFiles(abs)) {
        const content = readFileSync(f, 'utf-8')
        if (VT_PATTERN.test(content)) offenders.push(f)
      }
    }
    expect(offenders).toEqual([])
  })
})
```

**GREEN by emptiness inicial:** los paths `(shell-organism)/` no existen aún en F1-S0 (los crea F1-S4). Test pasa por iteración vacía. Cuando F1-S4 crea el route group, test sigue GREEN porque builder NO usa `.vt-*` en código nuevo.

### § 2.8 — ADR-vitalia-002-vt-deprecation-plan.md (8 secciones)

Path: `vitalia/docs/architecture/ADR-vitalia-002-vt-deprecation-plan.md`

Magic comment header: `<!-- voseo-allowed: internal architecture documentation -->`

8 secciones obligatorias:

1. **Contexto** — por qué `.vt-*` existen, problema deuda técnica, alineación Shadcn
2. **Inventario .vt-*** — scan `globals.css` listar 150+ classes con counts
3. **Estrategia compatibility temporal** — bloque `.vt-*` apunta a nuevas CSS vars
4. **Migration policy progresiva** — cada feature shipped que migra al shell-organism refactoriza a Tailwind directo
5. **Final drop** — story dedicada fin Fase 2 (`vitalia-fase2-vt-deprecation-final`)
6. **Arch fitness test enforcement** — referencia `test-no-vt-classes-in-new-features.test.ts`
7. **Post-install audit checklist supply-chain** — diff review line-by-line los 8 primitivos `.tsx` contra registry oficial Shadcn `https://ui.shadcn.com/r/`, lockfile pin review, version pinning, no auto-upgrades sin re-review
8. **Riesgos + mitigaciones** — Tailwind v4 React 19 compat, Shadcn React 19 peer-dep, `.vt-*` deprecation rompe shipped dashboard, registry supply-chain, CSS vars colisión, Playwright flaky, goldens commit weight

---

## § 3 — Cross-cutting decisions

### § 3.1 — .vt-* preservation strategy

Decisión D1: NO migrar `.vt-*` en F1-S0. Coexistencia temporal (1 release post F1-S0). Bloque `.vt-bg-*` → `background-color: hsl(var(--background))` para evitar regression visual del `(dashboard)/` shipped. Migración final → story dedicada `vitalia-fase2-vt-deprecation-final` al cierre Fase 2.

**Justificación:** D2 Design Contract § 1 cementa "deprecar `.vt-*` COMPLETO" pero D3 cementa "migration path = route group paralelo" (coexistencia). F1-S0 honra ambas: instala infra NEW + preserva legacy.

### § 3.2 — Tailwind v4 empirical verification (Scenario 2)

**Risk register:** learning 2026-05-21 reportó "Tailwind no renderiza"; subagent Explore 2026-05-22 reportó "operativo". Discrepancia → F1-S0 verifica empíricamente via Scenario 2 spec (`make dev-vitalia` + visual check browser).

**Fallback path documentado en ADR-vitalia-002 § 8:** si Tailwind v4 incompatible con React 19 → downgrade temporal Tailwind v3 hasta v4 stabilize (Tailwind v4 stable Q1 2026 per upstream).

### § 3.3 — Shadcn React 19 peer-dep handling (Scenario 5)

Shadcn declared React 19 compat 2025-Q4. Si peer-dep conflict en install:
- Workaround: `package.json` `overrides: { "react": "$react" }` para forzar React 19 single-version resolution
- Fallback documented ADR-vitalia-002 § 8: pin Shadcn CLI version a release verified-compat con React 19

### § 3.4 — Supply-chain audit (ADR-vitalia-002 § 7)

`/auditor` review del PR F1-S0 examina diff line-by-line los 8 primitivos `.tsx` copy-paste contra registry Shadcn oficial. Auditor manual catchea código injection si lo hubiera. Cualquier story Fase 2 que agregue primitives nuevos repite este review gate.

Si en futuro `/pm-luana scan-promotables` detecta patrón cross-brand de supply-chain risk → lift a `core/luana-core-platform/security/supply-chain-policy.md` o `.claude/rules/supply-chain-policy.md` raíz.

---

## § 4 — Test Construction Plan summary

Detalle completo en `04-validators.yaml § test_construction_plan`. Resumen:

- **playwright_required:** true (visual baselines only — NO behavior E2E)
- **base_path:** `vitalia/frontend/e2e/{__test-pages__,visual,__screenshots__}/stack-stability/`
- **creation_order (11 steps):** Shadcn install → globals.css tokens → tailwind extend → playwright config → test pages → spec baseline → arch test → ADR → Tailwind v4 empirical check → build verify → goldens generation + Chris ratify
- **POMs required:** none (no behavior E2E)
- **Fixtures required:** none (no auth/data setup)

---

## § 5 — Engine boundaries

**NO toca:**
- `core/luana-core-*/` (engine packages) — story 100% brand-local
- `nicolify/`, `comunify/`, `lupulo/` (otros brands) — scope exclusivo Vitalia
- `vitalia/backend/` (BE shipped Vitalia) — F1-S0 NO modifica APIs ni schemas

**Consume read-only (sin modificar):**
- Shadcn registry oficial `https://ui.shadcn.com/r/` (build-time fetch durante install)
- `@radix-ui/*` peer-deps via npm (lockfile pin)

---

## § 6 — Anti-patterns prohibidos

- ❌ Editar `vitalia/frontend/src/app/[tenantId]/(dashboard)/` legacy (`(dashboard)/` debe seguir funcionando idéntico post-install — golden regression catcha)
- ❌ Migrar `.vt-*` classes a Tailwind directo en esta story (eso es `vitalia-fase2-vt-deprecation-final`)
- ❌ Instalar Shadcn en `nicolify/frontend/`, `comunify/frontend/`, `lupulo/frontend/` (scope brand-local Vitalia)
- ❌ Hex hardcoded en componentes (use `bg-agent-lisa` no `bg-[#00D084]`)
- ❌ `any` TypeScript en código nuevo (utils.ts, test pages, arch test)
- ❌ Default exports (FSD-Lite enforce — named exports only)
- ❌ Importar `core/luana-core-*/` directo desde frontend
- ❌ Hardcoded `/home/chalreme/` paths (use `process.cwd()` + relative paths)
- ❌ Frameworks externos no-Tailwind (Bootstrap, Material UI) en mockups o componentes
- ❌ Lorem ipsum o data USA en fixtures test pages — use AR/MX/CO/PE/CL realistic

---

## § 7 — References

- **01-spec.md** — `vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md` (665 LOC, Chris-ratified 2026-05-22 whole-doc)
- **SHELL-DESIGN-CONTRACT.md** — `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (633 LOC, ratified 2026-05-22)
- **ADR-vitalia-003 shell-mockup-per-component-protocol** — `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` (F1-S0 declarada exenta § Excepciones)
- **Rule overlay shell-mockup-per-component** — `vitalia/.claude/rules/shell-mockup-per-component.md` (consumed — no-mockup-scope declared)
- **Rule overlay hipaa-lite** — `vitalia/.claude/rules/hipaa-lite.md` (consumed — **no-phi-scope declared**)
- **Rule raíz frontend-fsd** — `.claude/rules/frontend-fsd.md` (boundaries que F1-S1+ heredan)
- **Rule raíz spanish-text** — `.claude/rules/spanish-text.md` (no-copy-scope F1-S0; ADR lleva magic comment `voseo-allowed`)
- **Rule raíz tdd-mandatory** — `.claude/rules/tdd-mandatory.md` (RED tests precede GREEN — arch test creado pre-uso)
