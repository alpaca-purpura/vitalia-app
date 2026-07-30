# ADR-008 — Luana Core UI: shadcn copy-paste con CLI compartida

**Status:** accepted-partial *(CLI generator descartado — ver § Bitácora / As-built)*
**Date:** 2026-05-21
**Deciders:** Chris (ratificación inicial 2026-05-21) + /pm-luana (modo Core Engineering)
**Scope:** Engine TS package `core/@luana/ui-kit` (implementado) + brand consumers `{brand}/frontend/src/components/ui/`

## Context

Vitalia necesita design system urgente (caso origen: story `vitalia-slice-1-marketing` shipped state=done pero sidebar nav vacío + Tailwind v4 no renderiza tokens en runtime). Inventario revela gap brutal vitalia vs nicolify:

| Surface | Vitalia | Nicolify |
|---|---|---|
| Features | 8 (mayoría stubs) | 16 (estudios completos) |
| Shell/Nav system | `Sidebar.tsx` plano | `AppSidebar` + `SidebarContext` + `ShellMutexContext` + `NavigationOverlay` + `NavLink` + `NavigationContext` |
| UI primitives | ausente o mínimo | Shadcn completo + `form-runtime/` + `providers/` |
| Storybook | ❌ | ✅ `stories/{tokens,atoms,molecules,organisms}` |

Construir solo en vitalia/ riesga reincidir el patrón nicolify (built brand-only, deuda diferida cross-brand). Las 9 brands futuras heredarían la misma reinvención. Anti-duplication.md regla cardinal: **lift PROACTIVE cuando el patrón es obvio transversal**.

Pero shadcn-ui filosofía upstream es **"copy don't import"** — los componentes viven en el repo del consumer, no como dependencia. Esa decisión filosófica importa: cada brand puede tweakear su Button sin contract breakage upstream + sin governance semver pesada. Vs el modelo npm package que centraliza updates con costo de rigidez.

3 patterns evaluados:

| Pattern | Pro | Contra |
|---|---|---|
| npm package versionado | Governance limpio, semver formal, updates centralizados | Rompe filosofía shadcn "copy don't import"; rigidez per brand tweaks; cambia modelo mental |
| shadcn copy-paste con CLI compartida (recomendado) | Filosofía shadcn pura; brands ownan copia con flexibilidad; drift controlado con arch test | Drift cross-brand posible si CLI no se re-corre |
| Híbrido (primitives copy, agentic patterns npm) | Captura lo mejor de cada modelo | Doble governance + complejidad mental |

## Decision

Adoptar **shadcn copy-paste con CLI compartida** para `core/luana-core-ui/`:

### Mecánica

1. **Source of truth en engine:** `core/luana-core-ui/src/components/{atom,molecule,organism}/{name}/`
   Cada componente tiene su tree completo: `.tsx`, `.stories.tsx`, `.test.tsx`, `tokens.css` opcional, `README.md` con uso.

2. **CLI distribution:** `npx @luana/ui add {component}` copia el árbol desde engine a `{brand}/frontend/src/components/ui/{component}/`.

3. **Brand ownership:** una vez copiado, brand owna su copia. Puede tweakear estilos, agregar variants, ajustar comportamiento. Sin breaking contract upstream.

4. **Update workflow:** `npx @luana/ui update {component}` re-corre el copy con merge guiado (diff visual, prompts conflict resolution). NO auto-overwrite.

5. **Drift guard:** arch fitness test `{brand}/frontend/src/__tests__/architecture/test-ui-component-source-diff.test.ts` corre `npx @luana/ui diff {component}` y reporta divergencia. Drift permitido pero VISIBLE.

6. **Theme override mechanism:** tokens vitalia (paleta médica + spacing scale + typography) viven en `{brand}/frontend/src/lib/tokens/` y override CSS variables que componentes engine consumen via `var(--luana-color-primary)` etc.

### Estructura del package engine

```
core/luana-core-ui/
├── package.json                    # @luana/ui, version 0.1.0
├── tsconfig.json
├── README.md                       # quickstart + filosofía
├── src/
│   ├── components/
│   │   ├── atom/{button,input,label,badge,...}/
│   │   ├── molecule/{form-field,card,nav-item,...}/
│   │   └── organism/{app-sidebar,agent-rail,...}/
│   ├── tokens/                     # default tokens (brands override)
│   │   ├── colors.css
│   │   ├── spacing.css
│   │   └── typography.css
│   └── lib/
│       └── cn.ts                   # className utility (clsx + tailwind-merge)
├── cli/
│   ├── add.ts                      # npx @luana/ui add <name>
│   ├── update.ts                   # npx @luana/ui update <name>
│   ├── diff.ts                     # npx @luana/ui diff <name>
│   └── list.ts                     # npx @luana/ui list
├── tests/
│   ├── architecture/               # arch fitness engine-side
│   └── cli/                        # CLI behavior tests
└── stories/                        # Storybook centralizado por componente
```

### Semver per-component-tree (no per-package)

Cada componente tiene su `version.json` interno. Bumps independientes. Brand consumer ve qué versión copió + cuándo updated. Esto permite que `Button` evolucione sin forzar update de `Card`.

## Consequences

### Positive

- Filosofía shadcn preserved (brands ownan, flexibilidad)
- Cross-brand consistency con drift visible
- 9 brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow) heredan sin reinventar
- Storybook centralizado = docs único, no fragmentado per-brand
- Theme override mechanism mantiene identidad visual per-brand intacta

### Negative

- CLI debe mantenerse (es código adicional vs npm tradicional)
- Drift posible si brands no corren `update` periódicamente — mitigado con arch test que reporta divergencia
- Update conflicts requieren resolución manual (no auto-merge tipo npm)

### Pending review con Chris (NO cementado en este ADR)

**Shell/navigation pattern (organism layer):** Chris flageó tener una idea que reutiliza átomos pero permite navegación agéntica más sencilla. El patrón concreto para `AppSidebar` + nav system + agentic navigation NO se cementa en este ADR. Se discute separado antes de codificar primer organism.

## Implementation plan

Detalles operativos en promotion proposal `docs/promotion-protocol/proposals/2026-05-21-luana-core-ui-extraction.md`.

## Cross-references

- `docs/promotion-protocol/proposals/2026-05-21-luana-core-ui-extraction.md` — proposal extraction state=proposed
- `docs/product/outcomes/luana-core-ui-foundation.md` — outcome platform
- `.claude/rules/anti-duplication.md` — § lift shared rule (base preventive lift)
- `docs/architecture/luana-platform/ADR-001-luana-platform.md` — multibrand carve-out base
- Vitalia learning origen: `vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md`
- Shadcn upstream filosofía: https://ui.shadcn.com/docs (referencia externa para pattern "copy don't import")

## Bitácora / As-built (2026-06-01)

- 2026-05-21: opened state=proposed (Chris ratificó pattern shadcn copy-paste con CLI compartida en /pm-luana modo Core)
- **2026-06-01 — As-built:** el patrón CLI generator (`npx @luana/ui add/update/diff`) quedó **descartado**. Lo que se implementó es `core/@luana/ui-kit` — paquete flat sin CLI, distribuido como dependencia pnpm workspace estándar (`@luana/ui-kit`). El directorio `core/luana-core-ui/` con su `cli/` **no existe** en el repo. Un builder NO debe scaffoldearlo. Si se necesita retomar el patrón CLI o la carpeta `core/luana-core-ui/`, requiere ratificación Chris + promotion proposal nueva.
- state final: accepted-partial (filosofía shadcn copy-paste preservada; CLI = no implementado)
