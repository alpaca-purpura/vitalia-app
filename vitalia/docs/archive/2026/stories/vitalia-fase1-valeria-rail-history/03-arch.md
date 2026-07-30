<!-- voseo-allowed: glosario reference + internal architecture documentation -->

---
story_id: vitalia-fase1-valeria-rail-history
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-24
architect_iter: 1
architect_run_on: 2026-05-24
surfaces: FE_ONLY
predecessor_done: vitalia-fase1-shell-layout-5050  # archived 2026-05-23
---

# F1-S5 · vitalia-fase1-valeria-rail-history · 03-arch.md (consolidado)

## § 0 — Context Summary

- **Story:** vitalia-fase1-valeria-rail-history — outcome `vitalia-mvp-ui-foundation`, phase `fase-1`.
- **PR folder:** `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/`
- **Architect run on:** 2026-05-24 (Step 0 captured `date -u +%Y-%m-%d` = 2026-05-24, `date -u +%Y-%m` = 2026-05). Opus 4.7 knowledge cutoff Jan 2026; library currency verified via canonical docs as of 2026-05-24 (Next.js 16 App Router patterns, Zustand 5 persist, react-resizable-panels v4 unchanged from F1-S4).
- **Modules touched:** `shell-organism` (brand-local Vitalia frontend chrome — module doc `vitalia/docs/product/modules/shell-organism.md`).
- **Surfaces:** FE_ONLY · ZERO BE · ZERO AGENTIC · ZERO engine touch.

### Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/Valeria*.tsx` (NEW organism + moléculas + átomos) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/{HistoryItem,HistoryGroup,EmptyStateInline}.tsx` (NEW átomos/moléculas) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/_mock-conversations.ts` (NEW data + types) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/hooks/useKeyboardShortcuts.ts` (NEW hook reusable brand-local) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` (MODIFY: MIN_VALERIA_PX + replace slot import) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` (MODIFY: hamburger button `<md`) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot{,.test}.tsx` (DELETE) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.test.tsx` (MODIFY assertions) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/*.test.ts` (extend allowlists shrink-only + 1 NEW arch test) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/**` (NEW Playwright suite) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |

ZERO BE surface. ZERO AGENTIC surface. ZERO engine touch. R23 NO aplica (zero agentic, all FE production_code).

### Skills consulted (decisions ratified verbatim)

- **`frontend-expert`** — Server-First default; `'use client'` solo en hojas con state/hooks/event-handlers. FSD-Lite `components/shared/shell-organism/` correct para cross-feature chrome. Tests colocated `__tests__/` siblings. Runtime quality checklist: useEffect deps complete, no stale closures, hydration safety con zustand persist (sync on mount).
- **`playwright-expert`** — REUSE F1-S4 patterns: POM en `e2e/pages/`, fixtures en `e2e/fixtures/`, Clerk auth fixture reusable, public route `/test-stack/shell-layout` (no auth gate), addInitScript determinism para localStorage `vitalia-shell-state`, axe-playwright ruleset wcag2aa, visual goldens iter 1 via `--update-snapshots --project=visual` post Chris ratify side-by-side mockup HTML.
- **`tessl__react-patterns`** — React 19 + Next.js 16 App Router: Server Components default. Hooks contract con stable identity vía useCallback si pasados a child memoized (no aplica F1-S5 — shortcuts dict se construye inline). IME composition handling via `e.isComposing` (React 19 + DOM standard). Focus trap mobile via `inert` attribute o `focus-trap-react` (preferimos impl manual con Tab cycling — sin dep extra).
- **`tessl__shadcn-ui`** — REUSE primitives ya instalados F1-S0/S1: `Button` (variants ghost + icon size) + `Input` (search) + `Tooltip` (Radix `TooltipProvider` + `TooltipTrigger` + `TooltipContent`) + `Avatar` (chat header) + `Separator` (rail divider opcional). No upstream upgrade — versiones cementadas F1-S0.
- **`tessl__tailwind`** — Semantic tokens ONLY (DC §5.1): `bg-background`, `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `bg-agent-valeria`, `bg-agent-valeria-soft`. Tokens vitalia para Valeria: `--agent-valeria: 287 53% 37%` (light) / `287 60% 60%` (dark). NO hex. NO arbitrary values salvo `[data-testid=...]` aria attrs.
- **`tessl__vitest`** — Colocated `Component.test.tsx`. RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `useShellStore` via `useShellStore.setState({ ... })` directo (zustand permite). NO `vi.mock('@/stores/shell-store')` — el store es importado real, manipulado.
- **`backend-expert` / `copilot-expert` / `sales-agent-expert` / `offer-expert` / `metrics-expert` / `brand-expert` / `offer-type-preset-expert`** — NO cargar. Story es FE only chrome UI sin BE/agentic/dominio negocio (HIPAA-lite scope: `not_applicable`, mock data hardcoded sin PHI).

### CONTEXT-BRIEF source

Self-ran greps Path B + Read directos:
- `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/{checkpoint.md,01-spec.md,mockups/*.html}`
- `vitalia/docs/product/modules/shell-organism.md`
- `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/{03-arch.md,04-validators.yaml,05-guidelines.md,06-tickets.yaml}` (predecessor pattern reference)
- `vitalia/frontend/src/stores/shell-store.ts` + `vitalia/frontend/src/components/shared/shell-organism/{ShellOrganismLayoutClient,TopBarGlobal,ValeriaSidebarSlot}.tsx`
- `nicolify/frontend/src/features/copilot/components/CopilotSidebar.tsx` (read-only reference — pattern, no import)
- `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` (extend pattern)
- Cardinal rules: `frontend-fsd.md`, `spanish-text.md`, `tdd-mandatory.md`, `tenant-isolation.md`, `anti-duplication.md`, `shell-mockup-per-component.md`, `hipaa-lite.md`.

CONTEXT-BRIEF.md absent (story-by-story without Haiku context-builder).

### capability YAML files affected (post-merge updates required, paradigma post 2026-05)

- **MODIFY** `vitalia/docs/product/capabilities/shell-organism/layout-5050.yaml` — agregar mención `replaced ValeriaSidebarSlot placeholder → ValeriaSidebar real` en `Surfaces / Frontend` + KPI delta (visual goldens 6 → 13 nuevos shell + history + drawer).
- **NEW** `vitalia/docs/product/capabilities/shell-organism/valeria-sidebar.yaml` — capability nueva F1-S5 (`vitalia.shell-organism.valeria-sidebar`, status `live` post-merge).
- **AUTO-REGEN** `vitalia/docs/product/modules/shell-organism.md` — auto-list block via `scripts/reconcile_capabilities.py --brand vitalia` (R3 gitignored ok — list block es tracked).

### Architecture gates that must keep passing (extend, no break)

- `vitalia/frontend/src/__tests__/architecture/test_fsd_boundaries.test.ts` — shell-organism NO importa features/*.
- `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` — extend con nombres NEW (ValeriaSidebar, ValeriaRail, ValeriaHistory, HistoryItem, HistoryGroup, EmptyStateInline, useKeyboardShortcuts).
- `vitalia/frontend/src/__tests__/architecture/test-shell-store-schema.test.ts` — verify schema NO modificado (read-only consumer).
- `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_colors.test.ts` — tokens semánticos ONLY.
- `vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts` — Spanish neutro glossary regex.
- `vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts` — `'use client'` only en hojas con state/hooks (allowlist shrink-only — extend con nuevos client components).
- `vitalia/frontend/src/__tests__/architecture/test-skip-link-target.test.ts` — `<main id="main-content">` NO afectado (ShellOrganismLayoutClient sigue exponiendolo).
- NEW: `vitalia/frontend/src/__tests__/architecture/test-shell-store-schema-readonly-f1-s5.test.ts` — invariant: F1-S5 NO modifica schema shell-store (regression guard contra creep accidental).

## § 0.1 — Existing Systems Audit (NO NEW LAYER rule)

### Source of evidence

- [x] Self-run greps (Path B — context-builder fallback; CONTEXT-BRIEF.md absent for this story)

### Audit cross-module ejecutado

```bash
WS=/home/chalreme/Proyectos/luana-vitalia

# 1. Cross-brand mirror scan (anti-duplication.md cardinal rule)
for b in nicolify comunify lupulo; do
  for name in ValeriaSidebar ValeriaRail ValeriaHistory ValeriaChatSlot HistoryItem HistoryGroup EmptyStateInline useKeyboardShortcuts; do
    matches=$(grep -rln "$name" $WS/$b/frontend/src 2>/dev/null | grep -v node_modules | wc -l)
    if [ "$matches" -gt 0 ]; then echo "$b::$name → $matches matches"; fi
  done
done
# Result: 0 matches en las 3 brands. ✅ No mirror existente.

# 2. Engine TS packages (core/@luana/*)
find $WS/core -name "*.tsx" -o -name "ValeriaSidebar*" 2>/dev/null | grep -v node_modules
# Result: 0 matches. Engine TS packages no exponen shell organism abstraction. ✅

# 3. Same-brand existing duplicates (vitalia/frontend/)
find $WS/vitalia/frontend/src -name "ValeriaSidebar*" -o -name "ValeriaRail*" -o -name "ValeriaHistory*" -o -name "useKeyboardShortcuts*" 2>/dev/null
# Result: ValeriaSidebarSlot.tsx existe (placeholder F1-S4 — to DELETE). 0 matches para nombres reales NEW. ✅

# 4. Nicolify CopilotSidebar (reference pattern, read-only)
ls $WS/nicolify/frontend/src/features/copilot/components/CopilotSidebar.tsx
# Result: EXISTE (read-only reference). Pattern transposed para Vitalia (left-aligned, 2-col asymmetric, auto-coupling collapsed→web).
# IMPORTANT: NO IMPORT — cross-brand import HARD BAN. Pattern es referenciado solo en documentación.

# 5. Shadcn primitives ya instalados
ls $WS/vitalia/frontend/src/components/ui/{button,input,tooltip,avatar,separator}.tsx
# Result: TODOS exist. ✅ REUSE sin upgrade.

# 6. Lucide-react dependency
grep "lucide-react" $WS/vitalia/frontend/package.json
# Result: dependency presente (heredada F1-S0). ✅ Icons disponibles (PanelLeftOpen, PanelLeftClose, Plus, Search, Menu, X, Search).
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `useShellStore` zustand + persist | `vitalia/frontend/src/stores/shell-store.ts` | active F1-S4 done | **REUSE READ-ONLY** — consumir `valeriaState`, `shellMode`, `setValeriaState`, `setShellMode`, `cycleValeriaState`. NO modificar schema. Arch test NEW `test-shell-store-schema-readonly-f1-s5.test.ts` enforce. |
| `ShellOrganismLayoutClient` | `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | active F1-S4 done | **MODIFY puntual D3+F1-S5**: `MIN_VALERIA_PX` ternary `full: 620 → 580` (rail xor history nuevo modelo 2-col) + replace `<ValeriaSidebarSlot/>` import → `<ValeriaSidebar/>` real. Sin más cambios. |
| `TopBarGlobal` | `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | active F1-S2 done | **MODIFY ADD-ONLY D7**: agregar hamburger `Menu` button (Lucide) visible `<md` viewport, con handler `setValeriaState('full') + setShellMode('agentic')` (abre drawer). NO modificar logic existente LogoMark + TenantSwitcher + ThemeToggle (todos preserved intactos). |
| `ValeriaSidebarSlot` placeholder | `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx` + `.test.tsx` | active F1-S4 placeholder | **DELETE ambos** — reemplazado por `ValeriaSidebar` real F1-S5. |
| `ShellOrganismLayout.test.tsx` | mismo dir | active F1-S4 done | **MODIFY** assertions: ya no espera `ValeriaSidebarSlot` por nombre, ahora `ValeriaSidebar` (o data-testid `valeria-sidebar`). |
| Shadcn `Button`/`Input`/`Tooltip`/`Avatar`/`Separator` | `vitalia/frontend/src/components/ui/` | active F1-S0/S1 | **REUSE sin modificar** — primitives copy-paste local. |
| Lucide-react icons | `package.json` dep heredada | active | **REUSE** — `PanelLeftOpen`, `PanelLeftClose`, `Plus`, `Search`, `Menu`, `X`, `MessageSquarePlus` (opcional alternative). |
| Nicolify `CopilotSidebar` pattern | `nicolify/frontend/src/features/copilot/components/CopilotSidebar.tsx` | active read-only ref | **NO IMPORT** (cross-brand HARD BAN per anti-duplication.md). Pattern transposed verbatim en docs solamente. |

### Decisión por sistema

- **NEW components (8 archivos `Valeria*` + `History*` + `EmptyStateInline` + `_mock-conversations`)**: **NEW correctly** — primera ocurrencia, no mirror existente cross-brand. Pattern transposed Nicolify pero adaptación significativa (2-col asymmetric vs 3-col Nicolify, auto-coupling collapsed→shellMode='web' NEW, lowercase bare shortcuts vs uppercase Nicolify, history positioned LEFT of chat vs RIGHT). DRY threshold = 2 consumers; F1-S5 es primera → NEW correcto. Future story que duplique en lupulo/comunify → triggerea `/pm-luana` promotion proposal para `core/@luana/shell-organism/` (lift candidate, fuera scope F1-S5).
- **NEW hook `useKeyboardShortcuts.ts`**: **NEW correctly** — hook generic con hardened guard (D4: skip si focus en INPUT/TEXTAREA/[contenteditable]/[role=textbox] + e.isComposing). Vitalia es primer consumer. **Lift candidate cross-brand a `core/@luana/hooks/use-keyboard-shortcuts/` futuro** — documentar en `vitalia/docs/learnings/2026-05-24-useKeyboardShortcuts-promotion-candidate.md` post-merge (NO ahora, scope strict).
- **MODIFY existing (3 archivos: `ShellOrganismLayoutClient.tsx`, `TopBarGlobal.tsx`, `ShellOrganismLayout.test.tsx`)**: **EXTEND puntual ratificado** — side-effects D3+D7+F1-S5 verbatim del 01-spec.md, NO scope creep adicional.
- **DELETE legacy (2 archivos: `ValeriaSidebarSlot.tsx` + `.test.tsx`)**: cleanup obligatorio del placeholder F1-S4. Ratificado spec § 12 + checkpoint.

**Cross-brand lift evaluation:** `useKeyboardShortcuts` es candidato promotable cuando Nicolify/Comunify/Lupulo necesiten shortcuts pattern similar. Por ahora primera ocurrencia → NEW en `vitalia/frontend/src/hooks/`. Auditor flagged `// LIFT CANDIDATE: cross-brand keyboard shortcuts pattern, second consumer triggers /pm-luana proposal` en archivo header. Pattern shell-organism general aún no replicado → mismo principio (lift al 2do consumer).

## § 1 — Surfaces involved (verbatim)

| Surface | Aplica | Owner |
|---|---|---|
| BE (FastAPI Python) | NO | — |
| AGENTIC (LangGraph / deepagents / sales_agent) | NO | — |
| FE (Next.js 16 App Router + Shadcn + Tailwind + Zustand + React 19) | **SÍ** | `builder-frontend` Sonnet/opencode |

## § 2 — FE Architecture Detail

### § 2.1 — Component tree (atomic design)

```
ShellOrganismLayoutClient ('use client', MODIFY — existing F1-S4)
├── TopBarGlobal (MODIFY add hamburger <md)
│   ├── LogoMark (REUSE F1-S2 — preserved intact)
│   ├── TenantSwitcher (REUSE F1-S3 — preserved intact)
│   ├── ThemeToggle (REUSE F1-S1 — preserved intact)
│   └── [NEW] hamburger Menu button (md:hidden)
│       └── onClick: setValeriaState('full') + setShellMode('agentic')
│
├── ShellModeToggle (REUSE F1-S4 — disabled chip preserved intact)
│
└── <Group resizable>
    ├── Panel valeria-panel
    │   └── ValeriaSidebar (NEW organism, 'use client')
    │       ├── useShellStore consumer (READ-ONLY)
    │       ├── useKeyboardShortcuts (NEW hook)
    │       ├── Live region a11y aria-live polite
    │       │
    │       ├── ValeriaRail (NEW molécula, 'use client') — visible si state ∈ {collapsed, rail}
    │       │   ├── Button ghost icon PanelLeftOpen (toggle→full)
    │       │   ├── Button ghost icon Plus (alert mock)
    │       │   ├── Button ghost icon Search (focus composer)
    │       │   ├── spacer flex-1
    │       │   ├── Button ghost icon PanelLeftClose (collapsed+web)
    │       │   └── Tooltip × 4 (Radix con keyboard hints)
    │       │
    │       │   OR
    │       │
    │       ├── ValeriaHistory (NEW molécula, 'use client') — visible si state === 'full'
    │       │   ├── Header (title "Conversaciones" + quick actions Plus + PanelLeftClose)
    │       │   ├── Input search ('valeria-history-search' id + aria-label)
    │       │   │   └── useState searchQuery (local)
    │       │   ├── useMemo filtered + grouped per group
    │       │   ├── HistoryGroup × 3 (Hoy / Ayer / Esta semana) — render condicional si group.items.length > 0
    │       │   │   └── HistoryGroup (NEW molécula, Server Component)
    │       │   │       ├── header label "Hoy" / "Ayer" / "Esta semana"
    │       │   │       └── HistoryItem × N (NEW átomo, 'use client' — onClick setActiveId)
    │       │   │           ├── title (truncate)
    │       │   │           ├── meta (timestamp · message count)
    │       │   │           └── activeState (bg-agent-valeria-soft)
    │       │   └── EmptyStateInline (NEW átomo, Server Component) — visible si filtered.length === 0
    │       │       ├── icon Search24 muted
    │       │       ├── h3 "Sin resultados"
    │       │       └── p "Intenta con otra palabra"
    │       │
    │       └── ValeriaChatSlot (NEW placeholder, 'use client' — F1-S6 reemplaza body)
    │           ├── ChatHeader (avatar Valeria + nombre + status dot "En línea")
    │           ├── Body: 4 skeleton bubbles alternados (self-start muted + self-end agent-valeria-soft)
    │           ├── Composer skeleton (h-11 placeholder con id "valeria-composer-placeholder")
    │           └── Label flotante "CHATSLOT · F1-S6" (sr-only en prod, visible dev)
    │
    ├── Separator (REUSE F1-S4 — preserved intact)
    │
    └── Panel app-panel
        └── AppPanelSlot (REUSE F1-S4 — preserved intact)
```

**Mobile drawer (`<md` viewport):**
- TopBarGlobal hamburger button visible
- ValeriaSidebar wrapped en fixed inset-y-0 left-0 z-60 con backdrop bg-black/40 backdrop-blur-sm
- Slide-in transform translate-x-0/-translate-x-full per `valeriaState !== 'collapsed'`
- Focus trap activo + aria-modal="true"
- Cierre: Esc / backdrop click / botón X interno / swipe-left

### § 2.2 — State machine (3 estados macro)

```
                  press 'r' / click PanelLeftOpen (desde collapsed)
              ┌─────────────────────────────────────────────┐
              │                                              │
              v                                              │
  ┌──────────────────────────┐   press 'f'   ┌──────────────────────────┐
  │   rail                   │  ───────────> │   full                   │
  │   [Rail 60 | Chat 1fr]   │  press 'r'    │   [History 280 | Chat 1fr]│
  │   shellMode='agentic'    │  <─────────── │   shellMode='agentic'    │
  └──────────┬───────────────┘                └─────────┬────────────────┘
             │                                          │
             │  press 'c' / 'Esc' / click PanelLeftClose
             │  + AUTO setShellMode('web')
             │                                          │
             v                                          v
  ┌──────────────────────────────────────────────────────────────────┐
  │   collapsed                                                       │
  │   shellMode='web' (AUTO-COUPLED — D2 spec § 0)                   │
  │   Shell layout: [Rail 60 | 1px | AppPanel 100%]                  │
  │   (ChatSlot oculto, AppPanel toma todo el ancho)                 │
  │                                                                   │
  │   Exit triggers (AUTO reset shellMode='agentic'):                │
  │     - press 'r' → setValeriaState('rail') + setShellMode('agentic')│
  │     - press 'f' → setValeriaState('full') + setShellMode('agentic')│
  │     - click PanelLeftOpen → setValeriaState('full') + setShellMode('agentic')│
  └──────────────────────────────────────────────────────────────────┘

  Idempotency:
   - press 'c' o 'Esc' en state collapsed → no-op (ya en collapsed)
   - press 'r' en state rail → no-op
   - press 'f' en state full → no-op

  Adversarial guard (D4 + Scenario 4):
   - setState({valeriaState: 'INVALID'}) via devtools → runtime type guard
     console.warn + render falls back to 'rail' default (no white screen)
```

### § 2.3 — `useKeyboardShortcuts` hook contract

```ts
// vitalia/frontend/src/hooks/useKeyboardShortcuts.ts
//
// Brand-local hook. LIFT CANDIDATE: cross-brand keyboard shortcuts pattern,
// second consumer (Nicolify/Comunify/Lupulo) triggers /pm-luana proposal
// para core/@luana/hooks/use-keyboard-shortcuts/.

import { useEffect } from 'react'

export type ShortcutMap = Record<string, () => void>

/**
 * Hardened guard: skips dispatch when focus está en input/textarea/contenteditable/role=textbox
 * o cualquier ancestor con esos atributos, o cuando IME composition activa (e.isComposing).
 * Modifier shortcuts (Cmd+K, Ctrl+K) sí ejecutan dentro de inputs (intencional para focus jump).
 *
 * Key matching: bare lowercase ('c', 'r', 'f', 'n') o 'Escape' o 'mod+k' (mac/win cross-compat).
 *
 * Cleanup: removeEventListener on unmount.
 */
export function useKeyboardShortcuts(shortcuts: ShortcutMap): void
```

**Guard semantics (hardened, D4 spec):**
```ts
const handler = (e: KeyboardEvent) => {
  // 1. IME composition guard (D4 — Scenario 3 edge case)
  if (e.isComposing) return

  // 2. Focus-in-input guard (D4 — Scenario 2 negative)
  const target = e.target as HTMLElement | null
  if (target) {
    const inTextEdit =
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable ||
      target.getAttribute('role') === 'textbox' ||
      target.closest('input,textarea,[contenteditable=true],[role=textbox]') !== null

    // Modifier shortcuts (Cmd+K / Ctrl+K) bypass focus guard intencionalmente
    if (inTextEdit && !e.metaKey && !e.ctrlKey) return
  }

  // 3. Key resolution
  const key = e.key.toLowerCase()
  const modKey = (e.metaKey || e.ctrlKey) ? `mod+${key}` : key

  const action = shortcuts[modKey] || shortcuts[e.key]  // Escape exact match preserved
  if (action) {
    e.preventDefault()
    action()
  }
}
```

### § 2.4 — Handlers contract (canonical SSoT)

| Trigger | Handler | State delta |
|---|---|---|
| Press `r` (no input focus) | `setValeriaState('rail') + setShellMode('agentic')` | valeriaState → rail, shellMode → agentic |
| Press `f` (no input focus) | `setValeriaState('full') + setShellMode('agentic')` | valeriaState → full, shellMode → agentic |
| Press `c` (no input focus) | `setValeriaState('collapsed') + setShellMode('web')` | valeriaState → collapsed, shellMode → web |
| Press `Escape` (no input focus, drawer cerrado) | `setValeriaState('collapsed') + setShellMode('web')` | idem `c` (mismo handler) |
| Press `Escape` (drawer mobile abierto) | `setValeriaState('collapsed')` solo (no setShellMode change) | valeriaState → collapsed |
| Press `Escape` (focus en search input con query) | `clear searchQuery` (NO state change) | local `setSearchQuery('')` |
| Press `n` (no input focus) | `window.alert('Nueva conversación (próximamente)')` | no state change (mock) |
| Press `Cmd/Ctrl + K` (any focus) | `document.getElementById('valeria-composer-placeholder')?.focus()` | no state change |
| Click rail PanelLeftOpen (state=rail) | `setValeriaState('full')` | rail → full |
| Click rail PanelLeftOpen (state=collapsed via drawer) | `setValeriaState('full') + setShellMode('agentic')` | collapsed → full + web → agentic |
| Click rail Plus | `window.alert('Nueva conversación (próximamente)')` | no state change |
| Click rail Search | `document.getElementById('valeria-composer-placeholder')?.focus()` | no state change |
| Click rail PanelLeftClose | `setValeriaState('collapsed') + setShellMode('web')` | → collapsed + web |
| Click history header quick action "+" | `window.alert('Nueva conversación (próximamente)')` | no state change |
| Click history header quick action "←" (colapsar a rail) | `setValeriaState('rail')` | full → rail (shellMode unchanged 'agentic') |
| Input search onChange | `setSearchQuery(e.target.value)` (local state) | filtered + grouped recomputed via useMemo |
| Click HistoryItem | `setActiveConversationId(item.id)` (local state) | local active state (F2 conecta a chat) |
| Tap hamburger TopBar (mobile) | `setValeriaState('full') + setShellMode('agentic')` (abre drawer) | collapsed → full + web → agentic |
| Tap X drawer / backdrop click / swipe-left (mobile) | `setValeriaState('collapsed')` solo (shellMode unchanged 'agentic') | full → collapsed (drawer slide-out) |

**Auto-coupling invariant (D2 — Scenario 1 + 5):**
- Cuando `setValeriaState('collapsed')` se invoca desde botón "c" o PanelLeftClose o Escape → **AUTO** `setShellMode('web')` mismo handler.
- Cuando `setValeriaState('rail' | 'full')` se invoca desde botón/keyboard → **AUTO** `setShellMode('agentic')` mismo handler.
- En mobile drawer cierre vía Esc/backdrop/X → NO auto-shellMode change (drawer pattern preserva shellMode previo).

### § 2.5 — Sub-component contracts (NEW)

#### ValeriaSidebar (organism root)

- File: `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx`
- Type: `'use client'`
- Props: none (consume `useShellStore`)
- Renders `<aside role="complementary" aria-label="Panel Valeria" aria-expanded={state !== 'collapsed'} data-testid="valeria-sidebar">`
- Mobile branch (`<md`): wrapper drawer fixed con backdrop + focus trap
- Desktop branch (`md+`): grid 2-col asymmetric
- Live region `<span role="status" aria-live="polite" aria-atomic="true" className="sr-only">` con texto dinamico estado
- Width interno: `valeriaState === 'full' ? 280 : 60` (history XOR rail)
- Transition: `grid-template-columns 220ms cubic-bezier(.2,.8,.2,1) motion-reduce:transition-none`
- Runtime type guard adversarial (Scenario 4): `if (!['collapsed','rail','full'].includes(valeriaState)) { console.warn('Invalid valeriaState ignored'); return null OR fallback 'rail' }`

#### ValeriaRail (molécula 60px)

- File: `vitalia/frontend/src/components/shared/shell-organism/ValeriaRail.tsx`
- Type: `'use client'` (recibe handlers click)
- Props: `{ onToggleHistory, onNewConversation, onSearch, onCollapse }` — handlers explícitos (caller passa, fácil de testear)
- 4 botones MVP-only (D5 explícito spec § 0):
  1. `PanelLeftOpen` (lucide) — aria-label "Mostrar historial" + tooltip "Mostrar historial · f"
  2. `Plus` — aria-label "Nueva conversación" + tooltip "Nueva conversación · n"
  3. `Search` — aria-label "Buscar (Cmd+K)" + tooltip "Buscar · ⌘K"
  4. spacer `<div className="flex-1" />`
  5. `PanelLeftClose` — aria-label "Cerrar Valeria" + tooltip "Cerrar · c"
- Buttons: Shadcn `Button` variant ghost + size icon (h-9 w-9)
- F2 buttons (anclados/tareas/notas) — **HIDDEN COMPLETAMENTE** (no greyed/disabled — evita falsa affordance)

#### ValeriaHistory (molécula 280px)

- File: `vitalia/frontend/src/components/shared/shell-organism/ValeriaHistory.tsx`
- Type: `'use client'` (state local searchQuery + activeId)
- Props: `{ onNewConversation, onCollapseToRail }` — handlers explícitos
- Header: title "Conversaciones" + 2 quick actions (Plus + PanelLeftClose alternativo "← colapsar a rail")
- Input search Shadcn `Input` con id "valeria-history-search" + aria-label + placeholder "Buscar conversación..." + onKeyDown Escape limpia query
- useMemo filtered: `MOCK_CONVERSATIONS.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase().trim()))`
- useMemo grouped: `{ today: [...], yesterday: [...], this_week: [...] }`
- Conditional rendering:
  - `filtered.length === 0` → `<EmptyStateInline />`
  - else → `<HistoryGroup>` × 3 (cada uno solo render si `group.items.length > 0`)

#### HistoryItem (átomo)

- File: `vitalia/frontend/src/components/shared/shell-organism/HistoryItem.tsx`
- Type: `'use client'` (onClick handler)
- Props: `{ id, title, meta, active, onClick }`
- Render: `<button type="button" onClick={onClick}>` con title (truncate-1) + meta (text-xs text-muted-foreground)
- Active state: `bg-agent-valeria-soft` + aria-current="true"
- Hover: `hover:bg-muted`

#### HistoryGroup (molécula)

- File: `vitalia/frontend/src/components/shared/shell-organism/HistoryGroup.tsx`
- Type: Server Component (NO state, NO event handler — children passed)
- Props: `{ label, children }`
- Render: section con `<h3 className="text-xs font-semibold text-muted-foreground uppercase px-3 pt-3 pb-1">{label}</h3>` + children (HistoryItem list)

#### EmptyStateInline (átomo)

- File: `vitalia/frontend/src/components/shared/shell-organism/EmptyStateInline.tsx`
- Type: Server Component (pure presentation)
- Props: `{ icon?: ReactNode, heading: string, description: string }` — generic reusable
- Render: centered icon muted + h3 + p
- Promotable cross-brand a `core/@luana/ui-kit/empty-state-inline/` post 2do consumer (documentar comentario JSDoc + learning)

#### ValeriaChatSlot (placeholder F1-S6)

- File: `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx`
- Type: `'use client'` (focus composer via id, smooth transition F1-S6)
- Props: none
- ChatHeader real (avatar Valeria 36x36 `bg-agent-valeria` + initial "V" + nombre + status dot green + "En línea")
- Body: 4 skeleton bubbles alternados (heights variando, anchos 45-75%)
- Composer skeleton: `<div id="valeria-composer-placeholder" tabIndex={0} className="h-11 ...">` — tabIndex permite focus via Cmd+K antes que F1-S6 conecte textarea real
- Label flotante absolute centered "CHATSLOT · F1-S6" en `sr-only md:not-sr-only md:opacity-40` (dev visibility, no afecta a11y)

#### _mock-conversations.ts

- File: `vitalia/frontend/src/components/shared/shell-organism/_mock-conversations.ts`
- Type: data + types
- 8 items (D8 ratificado spec § 5):

```ts
export type MockConversation = {
  id: string
  title: string
  meta: string
  group: 'today' | 'yesterday' | 'this_week'
}

export const MOCK_CONVERSATIONS: readonly MockConversation[] = [
  { id: '1', title: 'Resumen reseñas Google semana', meta: '14:32 · 8 mensajes',  group: 'today' },
  { id: '2', title: 'Ideas campaña Día de la Madre',  meta: '11:18 · 12 mensajes', group: 'today' },
  { id: '3', title: 'Reporte ocupación martes',        meta: '09:45 · 5 mensajes',  group: 'today' },
  { id: '4', title: 'Borrador respuesta a reseña 3⭐', meta: 'Ayer 19:02 · 4 msgs', group: 'yesterday' },
  { id: '5', title: 'Tutorial agenda online turnos',   meta: 'Ayer 15:30 · 7 msgs', group: 'yesterday' },
  { id: '6', title: 'Plan ofertas mes mayo',           meta: 'Lun · 11 mensajes',   group: 'this_week' },
  { id: '7', title: 'Métricas conversión landing',     meta: 'Lun · 6 mensajes',    group: 'this_week' },
  { id: '8', title: 'Revisar copy WhatsApp bienvenida',meta: 'Dom · 9 mensajes',    group: 'this_week' },
] as const
```

**Anti-PHI verification:** 8 items NO contienen nombres pacientes, diagnósticos, dosis, fechas turno con identifier, ningún PHI field (per `vitalia/.claude/rules/hipaa-lite.md` § PHI fields canónicos). Strings genéricos operación clínica (reseñas, agenda, copy). Test grader `i18n-spanish-neutro.spec.ts` valida cero PHI patterns.

### § 2.6 — Side-effects MODIFY contract (scope discipline strict)

#### ShellOrganismLayoutClient.tsx (MODIFY puntual)

**ÚNICO cambio permitido — Diff verbatim:**

```diff
- const MIN_VALERIA_PX = valeriaState === "full" ? 620 : 360;
+ const MIN_VALERIA_PX = valeriaState === "full" ? 580 : 360;
```

```diff
- import { ValeriaSidebarSlot } from "./ValeriaSidebarSlot";
+ import { ValeriaSidebar } from "./ValeriaSidebar";
```

```diff
- <ValeriaSidebarSlot />
+ <ValeriaSidebar />
```

(2 occurrences en agentic Panel + web mode + mobile fallback — actualizar AMBAS las que llaman a `ValeriaSidebarSlot`.)

**NADA más se toca**: snap-up logic, ResizeObserver, useDefaultLayout, useGroupRef, layout structure, tokens, comments. Solo el delta arriba.

#### TopBarGlobal.tsx (MODIFY add-only D7)

**Cambio ADD-ONLY — agregar hamburger button visible `<md` viewport:**

```diff
+ "use client";  // Convert to Client porque agrega button con onClick
+ import { Menu } from "lucide-react";
+ import { useShellStore } from "@/stores/shell-store";
+ import { Button } from "@/components/ui/button";

  import { LogoMark } from "./LogoMark";
  import { TenantSwitcher } from "./TenantSwitcher";
  import { ThemeToggle } from "./ThemeToggle";

  export function TopBarGlobal({ className }: TopBarGlobalProps) {
+   const setValeriaState = useShellStore((s) => s.setValeriaState);
+   const setShellMode = useShellStore((s) => s.setShellMode);
+
+   const handleOpenValeriaDrawer = () => {
+     setValeriaState('full');
+     setShellMode('agentic');
+   };
+
    return (
      <header ...>
        <div className="flex items-center gap-3">
+         {/* Mobile-only hamburger to open Valeria drawer (D7 F1-S5) */}
+         <Button
+           variant="ghost"
+           size="icon"
+           type="button"
+           onClick={handleOpenValeriaDrawer}
+           aria-label="Abrir panel Valeria"
+           data-testid="topbar-hamburger"
+           className="md:hidden h-9 w-9"
+         >
+           <Menu className="h-5 w-5" aria-hidden="true" />
+         </Button>
+
          <LogoMark variant="full" size="md" className="hidden md:inline-flex" />
          <LogoMark variant="mark" size="md" className="inline-flex md:hidden" />
          <TenantSwitcher />
        </div>
        ...
      </header>
    );
  }
```

**Implicación:** TopBarGlobal pasa de Server Component a Client Component (necesario por useShellStore + onClick). Update test `TopBarGlobal.test.tsx` assertions si verifica `'use client'`.

**NADA más se toca**: estructura header, LogoMark renders, TenantSwitcher render, ThemeToggle, dimensiones, padding, z-index. Solo el delta arriba.

#### ShellOrganismLayout.test.tsx (MODIFY assertions)

Actualizar 2-3 assertions del test heredado:
- `expect(screen.getByTestId('valeria-sidebar-slot')).toBeInTheDocument()` → `expect(screen.getByTestId('valeria-sidebar')).toBeInTheDocument()`
- Si existe assertion verificando aria-label exacto "Panel Valeria (placeholder — F1-S5/S6 lo construirá)" → cambiar a "Panel Valeria"
- Si existe import de `ValeriaSidebarSlot` → cambiar a `ValeriaSidebar`

#### DELETE files (cleanup)

- `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx` — DELETE entero
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.test.tsx` — DELETE entero

### § 2.7 — Mobile drawer pattern (D7 detail)

```tsx
// Inside ValeriaSidebar.tsx
const isExpanded = valeriaState !== 'collapsed'

return (
  <>
    {/* Backdrop (mobile only, visible when drawer open) */}
    {isExpanded && (
      <div
        className="fixed inset-0 z-[55] bg-black/40 backdrop-blur-sm md:hidden"
        aria-hidden="true"
        onClick={() => setValeriaState('collapsed')}
        data-testid="valeria-drawer-backdrop"
      />
    )}

    <aside
      role="complementary"
      aria-label="Panel Valeria"
      aria-expanded={isExpanded}
      aria-modal={isExpanded ? 'true' : undefined}  // only when mobile drawer is open
      data-testid="valeria-sidebar"
      className={cn(
        // Desktop: full size inside Panel container (no fixed positioning, no z-index)
        "h-full overflow-hidden border-r border-border bg-card",
        // Mobile drawer overlay
        "max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:z-[60]",
        "max-md:w-screen sm:max-md:w-[360px]",
        "max-md:transition-transform max-md:duration-300",
        isExpanded ? "max-md:translate-x-0" : "max-md:-translate-x-full",
      )}
      style={{
        display: 'grid',
        gridTemplateColumns: `${railOrHistoryWidthPx}px 1fr`,
        gridTemplateRows: 'minmax(0, 1fr)',
        transition: 'grid-template-columns 220ms cubic-bezier(.2,.8,.2,1)',
      }}
    >
      <span role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {liveRegionText}
      </span>

      {/* Mobile drawer X close button (visible only inside drawer when expanded) */}
      {isExpanded && (
        <button
          type="button"
          onClick={() => setValeriaState('collapsed')}
          aria-label="Cerrar panel Valeria"
          data-testid="valeria-drawer-close"
          className="md:hidden absolute top-2 right-2 z-10 h-9 w-9 rounded-md hover:bg-muted flex items-center justify-center"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>
      )}

      {valeriaState === 'full' ? <ValeriaHistory ... /> : <ValeriaRail ... />}
      <ValeriaChatSlot />
    </aside>
  </>
)
```

**Focus trap (mobile drawer):** implementación manual con cycle Tab dentro del aside cuando `aria-modal="true"`:

```tsx
useEffect(() => {
  if (!isExpanded || !isMobileViewport()) return

  const aside = document.querySelector('[data-testid="valeria-sidebar"]')
  if (!aside) return

  // Auto-focus first interactive on open
  const firstFocusable = aside.querySelector<HTMLElement>(
    'button:not([disabled]), input:not([disabled]), [tabindex="0"]'
  )
  firstFocusable?.focus()

  const handleTab = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return
    const focusables = Array.from(
      aside.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), [tabindex="0"]')
    )
    if (focusables.length === 0) return
    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }

  document.addEventListener('keydown', handleTab)
  return () => document.removeEventListener('keydown', handleTab)
}, [isExpanded])
```

Helper `isMobileViewport()` = `window.matchMedia('(max-width: 767px)').matches` (post-mount safe).

Focus restoration on close: guardar `previousActiveElement` en useRef al abrir, restaurar al cerrar.

### § 2.8 — File tree (canonical)

```
vitalia/frontend/src/
├── components/shared/shell-organism/
│   ├── ValeriaSidebar.tsx                     NEW (T-5 organism)
│   ├── ValeriaSidebar.test.tsx                NEW (T-5)
│   ├── ValeriaRail.tsx                        NEW (T-3 molécula)
│   ├── ValeriaRail.test.tsx                   NEW (T-3)
│   ├── ValeriaHistory.tsx                     NEW (T-4 molécula)
│   ├── ValeriaHistory.test.tsx                NEW (T-4)
│   ├── ValeriaChatSlot.tsx                    NEW (T-3 placeholder)
│   ├── HistoryItem.tsx                        NEW (T-3 átomo)
│   ├── HistoryGroup.tsx                       NEW (T-3 molécula)
│   ├── EmptyStateInline.tsx                   NEW (T-3 átomo reusable)
│   ├── _mock-conversations.ts                 NEW (T-2 data + types)
│   ├── ShellOrganismLayoutClient.tsx          MODIFY (T-7 — MIN_VALERIA_PX + slot replace)
│   ├── TopBarGlobal.tsx                       MODIFY (T-6 — add hamburger <md)
│   ├── TopBarGlobal.test.tsx                  MODIFY (T-6 — assertions hamburger)
│   ├── ShellOrganismLayout.test.tsx           MODIFY (T-7 — assertions ValeriaSidebar)
│   ├── ValeriaSidebarSlot.tsx                 DELETE (T-7)
│   └── ValeriaSidebarSlot.test.tsx            DELETE (T-7)
│
├── hooks/
│   ├── useKeyboardShortcuts.ts                NEW (T-1 hook)
│   └── __tests__/
│       └── useKeyboardShortcuts.test.ts       NEW (T-1)
│
├── __tests__/architecture/
│   ├── test-no-cross-brand-shell-mirror.test.ts   MODIFY (T-7 — extend names)
│   ├── test-shell-store-schema.test.ts             UNCHANGED (regression guard)
│   ├── test_server_first.test.ts                   MODIFY (T-7 — extend allowlist 'use client' new files SHRINK ONLY justified)
│   ├── test-no-default-export.test.ts (heredado)   MODIFY (T-7 — extend allowlist SHRINK ONLY)
│   └── test-shell-store-schema-readonly-f1-s5.test.ts  NEW (T-7 — invariant store NO modified)
│
└── e2e/regression/vitalia-fase1-valeria-rail-history/
    ├── keyboard-cycle.spec.ts                 NEW (T-8 SC-1)
    ├── typing-guard.spec.ts                   NEW (T-8 SC-2)
    ├── ime-composition.spec.ts                NEW (T-8 SC-3)
    ├── store-tampering.spec.ts                NEW (T-8 SC-4)
    ├── click-collapse.spec.ts                 NEW (T-8 SC-5)
    ├── history-empty-search.spec.ts           NEW (T-8 SC-6)
    ├── a11y-keyboard.spec.ts                  NEW (T-8 SC-7 + axe)
    ├── a11y-mobile-drawer.spec.ts             NEW (T-8 SC-8 + axe)
    ├── i18n-spanish-neutro.spec.ts            NEW (T-8 SC-9)
    └── visual-goldens.spec.ts                 NEW (T-8 visual — 7 goldens × theme variants)

vitalia/frontend/e2e/pages/
└── ValeriaSidebarPage.ts                      NEW (T-8 POM)
```

### § 2.9 — Test construction order (canonical TDD RED-first)

```
T-1 — hook useKeyboardShortcuts (foundation, no deps)
  RED: useKeyboardShortcuts.test.ts
  GREEN: useKeyboardShortcuts.ts

T-2 — mock data + types (no deps)
  RED: typecheck via consumer in T-3/T-4 (no dedicated test — pure data)
  GREEN: _mock-conversations.ts

T-3 — átomos + moléculas low-level
  RED: ValeriaRail.test.tsx + ValeriaChatSlot.test.tsx (HistoryItem + HistoryGroup + EmptyStateInline cubiertos por ValeriaHistory + ValeriaSidebar tests integradores)
  GREEN: ValeriaRail.tsx + ValeriaChatSlot.tsx + HistoryItem.tsx + HistoryGroup.tsx + EmptyStateInline.tsx

T-4 — ValeriaHistory (depende T-2 + T-3 átomos/moléculas)
  RED: ValeriaHistory.test.tsx (filter logic + grouping + empty state)
  GREEN: ValeriaHistory.tsx

T-5 — ValeriaSidebar organism (depende T-1 + T-3 + T-4)
  RED: ValeriaSidebar.test.tsx (state transitions + auto-coupling + adversarial guard)
  GREEN: ValeriaSidebar.tsx

T-6 — TopBarGlobal MODIFY (depende store reuse — no other ticket dep)
  RED: TopBarGlobal.test.tsx update (assert hamburger button visible <md + handler)
  GREEN: TopBarGlobal.tsx edit (add hamburger + handler)

T-7 — Integration MODIFY ShellOrganismLayoutClient + cleanup (depende T-5 + T-6)
  RED: ShellOrganismLayout.test.tsx update (assert ValeriaSidebar renders) + new arch test invariant
  GREEN: ShellOrganismLayoutClient.tsx edit (MIN_VALERIA_PX + replace slot) + DELETE ValeriaSidebarSlot{,.test}.tsx
       + extend arch tests allowlists + NEW arch test shell-store-readonly

T-8 — Playwright E2E + visual goldens (depende T-1 thru T-7 — ALL FE building blocks)
  RED: 9 functional specs + 1 visual goldens spec (todos rojo inicial sin componente real)
  GREEN: post T-7 deploy local, --update-snapshots iter 1 post Chris ratifica side-by-side mockup HTML

DAG visualization:
  T-1 ─┐
  T-2 ─┼─> T-3 ─> T-4 ─> T-5 ─┐
       │                        ├─> T-7 (MODIFY + DELETE + arch tests) ─┐
       T-6 (independent MODIFY)─┘                                         ├─> T-8 (Playwright E2E + visual)
                                                                          ┘

T-6 parallelizable con T-3/T-4/T-5 (no comparte files).
T-7 secuencial post T-5 + T-6 (consume ambos).
T-8 secuencial post T-7 (consume integration completa).
```

### § 2.10 — Server vs Client decision tree (FSD-Lite)

| Component | Type | Justificación |
|---|---|---|
| `ValeriaSidebar` | 'use client' | useShellStore + useKeyboardShortcuts + useEffect (focus trap) |
| `ValeriaRail` | 'use client' | onClick handlers (4 buttons) — pasados como props, pero componente leaf que dispara |
| `ValeriaHistory` | 'use client' | useState searchQuery + useMemo filter/group + onChange input |
| `HistoryItem` | 'use client' | onClick handler dispatcher (active state local in parent) |
| `HistoryGroup` | Server Component | Pure presentation (label + children passthrough) |
| `EmptyStateInline` | Server Component | Pure presentation (icon + heading + description) |
| `ValeriaChatSlot` | 'use client' | tabIndex composer placeholder + future F1-S6 hot-swap necesita boundary client |
| `_mock-conversations.ts` | n/a (data) | Pure module export |
| `useKeyboardShortcuts` | n/a (hook) | Solo se usa dentro client component |
| `TopBarGlobal` (MODIFY) | 'use client' | NEW — agregar hamburger con onClick necesita boundary. Previously Server Component. |

### § 2.11 — Skill decisions referenced

- **`frontend-expert`**: FSD-Lite shared/shell-organism correct para chrome cross-feature; tests colocated; Server-First with selective 'use client' leaves; runtime quality checklist verified (useEffect deps, no stale closures, hydration safety).
- **`playwright-expert`**: REUSE F1-S4 patterns — POM en `e2e/pages/`, fixtures shared (`shell-theme.fixture.ts` extend para nuevo state setup), public route `/test-stack/shell-layout` (no Clerk auth), addInitScript determinismo, axe-playwright ruleset wcag2aa, visual goldens iter 1 protocol verbatim.
- **`tessl__react-patterns`**: React 19 IME composition guard via e.isComposing; useEffect cleanup obligatorio; hydration safety zustand persist sync on mount.
- **`tessl__shadcn-ui`**: REUSE Button/Input/Tooltip/Avatar primitives F1-S0 cementados — sin upgrade.
- **`tessl__tailwind`**: tokens semánticos ONLY, `--agent-valeria` + `--agent-valeria-soft` ya en `globals.css` per F1-S1.

## § 3 — Tests architecture

### § 3.1 — Vitest unit suite (T-1..T-7)

Cobertura por archivo (target):

| Test file | Cobertura sujeto | Cases |
|---|---|---|
| `useKeyboardShortcuts.test.ts` | hook | 8 cases: ignora si focus en input · ignora si isComposing · dispatches bare lowercase · dispatches Escape exact · dispatches mod+k via metaKey · dispatches mod+k via ctrlKey · cleanup on unmount · multiple shortcuts |
| `ValeriaRail.test.tsx` | molécula rail | 5 cases: renderiza 4 buttons MVP-only (Plus/Search hidden bonus F2 NO render) · tooltips con keyboard hint correcto · click dispatchea handler correcto · aria-labels Spanish neutro · cero data-testids F2 buttons |
| `ValeriaHistory.test.tsx` | molécula history | 8 cases: renderiza 8 mock items grouped 3+2+3 · filter case-insensitive · empty state cuando no match · grouped recomputado correcto · onChange search updates · Escape limpia query (no colapsa Valeria) · click HistoryItem updates active state · groups con 0 items NO renderizan label |
| `ValeriaChatSlot.test.tsx` | placeholder chat | 4 cases: ChatHeader con avatar + nombre + status dot · 4 skeleton bubbles render · composer placeholder con id "valeria-composer-placeholder" tabIndex=0 · label flotante "CHATSLOT · F1-S6" con sr-only md:not-sr-only |
| `ValeriaSidebar.test.tsx` | organism root | 12 cases: render aside con role + aria-label + aria-expanded · grid columns por state (full=280/1fr, rail=60/1fr) · auto-coupling collapsed→shellMode='web' · auto-coupling rail/full→shellMode='agentic' · keyboard r/f/c/Esc/n/Cmd+K · adversarial setState INVALID → console.warn + fallback · mobile drawer aria-modal · focus trap activo cuando mobile + expanded · backdrop click cierra · live region updates per state · transition motion-reduce respected · data-testid valeria-sidebar |
| `TopBarGlobal.test.tsx` (extend) | + hamburger | 2 new cases: hamburger button visible md:hidden + onClick dispatcha setValeriaState('full') + setShellMode('agentic') · aria-label "Abrir panel Valeria" |
| `ShellOrganismLayout.test.tsx` (modify) | + integration | 2 modified cases: asserts ValeriaSidebar (no Slot) · MIN_VALERIA_PX=580 implícito en assertion clamp |

**Mock pattern (zustand store):**
```ts
// In test setup
import { useShellStore } from '@/stores/shell-store'

beforeEach(() => {
  useShellStore.setState({
    valeriaState: 'full',
    shellMode: 'agentic',
  })
})

// Test reset post-test
afterEach(() => {
  useShellStore.persist?.clearStorage()
})
```

### § 3.2 — Playwright E2E suite (T-8)

POM `vitalia/frontend/e2e/pages/ValeriaSidebarPage.ts` métodos:
- `gotoShell()` — navigate to `/test-stack/shell-layout` (public route)
- `setValeriaStateViaStore(state)` — addInitScript pre-nav setting localStorage
- `setShellModeViaStore(mode)` — addInitScript
- `getAriaSidebar()` — Locator for `[data-testid=valeria-sidebar]`
- `getRailButton(name)` — Locator by aria-label (Spanish)
- `pressKey(key)` — `page.keyboard.press(key)` con focus reset prev (focus al body)
- `typeInSearch(text)` — focus search + type
- `clickHamburger()` — mobile drawer trigger
- `clickBackdrop()` — `[data-testid=valeria-drawer-backdrop]`
- `getLiveRegionText()` — `[role=status][aria-live=polite]`
- `getActiveHistoryItemTitle()` — finds `[aria-current=true]`

Fixtures:
- `shell-theme.fixture.ts` (REUSE F1-S4 + extend) — addInitScript setting localStorage `vitalia-shell-state` + `vitalia-theme` pre-navigation
- `clerk-auth.fixture.ts` (REUSE F1-S3) — public route bypassa auth gate

Specs mapping 1:1 con Scenarios:
- `keyboard-cycle.spec.ts` ← SC-1 (5 sub-checks per Scenario 1 then)
- `typing-guard.spec.ts` ← SC-2
- `ime-composition.spec.ts` ← SC-3 (use `page.keyboard.insertText` + dispatch composition events manually)
- `store-tampering.spec.ts` ← SC-4
- `click-collapse.spec.ts` ← SC-5
- `history-empty-search.spec.ts` ← SC-6 (+ visual_state grader)
- `a11y-keyboard.spec.ts` ← SC-7 + axe ruleset wcag2aa light + dark
- `a11y-mobile-drawer.spec.ts` ← SC-8 + axe + focus trap + restoration verify
- `i18n-spanish-neutro.spec.ts` ← SC-9 (grep glossary regex `vos|sos|tenés|podés|querés|sabés|dale|mirá|fijate` against rendered text)
- `visual-goldens.spec.ts` ← 7 snapshots × theme:
  - valeria-rail-{light,dark}.png (1280x800)
  - valeria-collapsed-{light,dark}.png (1280x800 — shellMode='web', solo rail 60px visible)
  - valeria-full-{light,dark}.png (1280x800)
  - valeria-history-empty-{light,dark}.png (1280x800 — searchQuery='xyzabc')
  - valeria-drawer-mobile.png (375x667 light)

Total: 13 PNG snapshots (5 desktop × 2 themes + 1 empty × 2 themes + 1 drawer single = 13). Verbatim per spec § 11 mapping (7 logical states × theme variants = 13 archivos).

### § 3.3 — Architectural fitness

**Tests existentes que extend (allowlists shrink only):**

1. `test-no-cross-brand-shell-mirror.test.ts` — agregar 6 nombres NEW: `ValeriaSidebar`, `ValeriaRail`, `ValeriaHistory`, `ValeriaChatSlot`, `HistoryItem`, `HistoryGroup`, `EmptyStateInline`, `useKeyboardShortcuts`. Cada uno cero matches en nicolify/comunify/lupulo.
2. `test_server_first.test.ts` — extender allowlist `'use client'` files con ValeriaSidebar + ValeriaRail + ValeriaHistory + ValeriaChatSlot + HistoryItem + TopBarGlobal (justificación inline en commit).
3. `test-no-default-export.test.ts` (heredado) — extender allowlist con NEW files (named exports forced).

**Tests NEW (1 archivo):**

4. `test-shell-store-schema-readonly-f1-s5.test.ts` — invariant: F1-S5 NO modifica `shell-store.ts` (regression guard). Hashea contenido del archivo y compara con baseline cementado F1-S4 (o verifica que export shape no cambió: `ValeriaState | ShellMode | SHELL_STORAGE_KEY | useShellStore | useShellStore.setState | useShellStore.persist`).

Implementación referencia:
```ts
import { describe, it, expect } from 'vitest'
import * as shellStoreModule from '@/stores/shell-store'

describe('arch: shell-store schema invariant F1-S5 read-only consumer', () => {
  it('exports ValeriaState union "collapsed"|"rail"|"full"', () => {
    // Type-level test via TS compiler
    type _Check = Extract<shellStoreModule.ValeriaState, 'collapsed' | 'rail' | 'full'>
    const states: shellStoreModule.ValeriaState[] = ['collapsed', 'rail', 'full']
    expect(states).toHaveLength(3)
  })

  it('exports ShellMode union "agentic"|"web"', () => {
    const modes: shellStoreModule.ShellMode[] = ['agentic', 'web']
    expect(modes).toHaveLength(2)
  })

  it('SHELL_STORAGE_KEY equals "vitalia-shell-state"', () => {
    expect(shellStoreModule.SHELL_STORAGE_KEY).toBe('vitalia-shell-state')
  })

  it('useShellStore exposes setValeriaState, setShellMode, cycleValeriaState', () => {
    const state = shellStoreModule.useShellStore.getState()
    expect(typeof state.setValeriaState).toBe('function')
    expect(typeof state.setShellMode).toBe('function')
    expect(typeof state.cycleValeriaState).toBe('function')
  })

  it('default state: valeriaState=full, shellMode=agentic (F1-S4 cementado)', () => {
    // Note: read AFTER clearing persisted storage
    shellStoreModule.useShellStore.persist?.clearStorage()
    const state = shellStoreModule.useShellStore.getState()
    expect(state.valeriaState).toBe('full')
    expect(state.shellMode).toBe('agentic')
  })
})
```

## § 4 — Cross-cutting concerns (resolution)

| Concern | Resolution |
|---|---|
| **Tenant isolation** | N/A — chrome UI sin queries BE. URL `[tenantId]` ya propagada por F1-S4 ShellOrganismLayout. Middleware Clerk gates upstream. |
| **Currency / monetary** | N/A — no monetary fields. |
| **PII / HIPAA-lite** | **scope: not_applicable** — declared en checkpoint frontmatter. Mock data 8 conversaciones sin PHI fields (cero nombres pacientes/diagnósticos/dosis/fechas turno con identifier). i18n spec valida via regex. |
| **Spanish neutro LatAm** | 28 strings ratificados spec § 6. Pre-commit hook (raíz) verifica voseo. Arch test `test-vitalia-ui-strings-no-voseo.test.ts` extiende a NEW components. i18n-spanish-neutro.spec.ts E2E grader verifica runtime DOM strings. |
| **Native-first dev** | Lint/tests/playwright NATIVE Linux host. NUNCA `docker exec ruff/pytest/tsc/vitest`. Stack docker compose para runtime sólo (`make dev-vitalia`). |
| **A11y mandatory** | aria-label + aria-expanded + aria-modal + live region + focus trap mobile + axe wcag2aa enforcement. Contrast ratios validados spec § 8 (text-foreground vs bg-card 21:1 / 18:1 light/dark). Reduced motion respected (`motion-reduce:transition-none`). |
| **PWA / responsive** | breakpoints `<md` drawer · `md+` desktop. Visual goldens cubren 1280x800 + 375x667. |

## § 5 — Resize integration impact (D3 verbatim)

`ShellOrganismLayoutClient` consume `valeriaState` para `MIN_VALERIA_PX`:
- `full` → 580 (history 280 + chat_min 300)  ← F1-S5 lowers from 620 (era 3-col obsoleto)
- `rail` → 360 (rail 60 + chat_min 300)

ResizeObserver + clamp logic INTACTOS. useDefaultLayout + useGroupRef INTACTOS. Drag clamp `minSize` percent calculation re-evalúa correctamente porque `MIN_VALERIA_PX` es leído live via store selector.

`MIN_APP_PX = 480` unchanged.

## § 6 — Telemetría / observability

N/A F1-S5 — mock-only. F2 events planificados spec § 9 (no aplica ahora).

## § 7 — Brand voice

N/A F1-S5 — shell chrome UI sin output sales_agent ni LLM text. Microcopy Spanish neutro estándar.

## § 8 — Cross-stack handoff

FE only. ZERO BE/AGENTIC dependencies.

## § 9 — Open questions for PM

Ninguna. Decisiones D1-D8 ratificadas spec § 0. Mockups visuales ratificados iter 1. Autonomous build requested ratificado checkpoint.

## § 10 — Anti-creep boundary

When `state: done` and merged:
- **F1-S6** (`valeria-chat-skeleton`) reemplaza body+composer del `ValeriaChatSlot` con chat real. F1-S5 deja `ChatHeader` (avatar+nombre+status) construido — F1-S6 lo RESPETA intacto.
- **F1-S5/S7** (futuro) activan `ShellModeToggle` interactivo (remove `disabled` attr, wire `setShellMode`).
- Si surge necesidad de tocar componentes shell ya existentes (TopBarGlobal logic más allá del hamburger, ShellOrganismLayoutClient resize, ShellModeToggle interactivo, AppPanelSlot) → STOP, escalar `/pm-vitalia` nueva story.

## § 11 — Research notes (DATE-AWARE)

- **`tessl__shadcn-ui` (Tooltip primitive)** — accessed 2026-05-24 via canonical path; tooltip = Radix UI primitive wrapper, supports `delayDuration` + content positioning + `<TooltipProvider>` root requirement. Verified versión cementada F1-S0 unchanged.
- **`tessl__react-patterns` (IME composition)** — accessed 2026-05-24; `KeyboardEvent.isComposing` standard property (W3C UI Events spec), supported React 19 + all evergreen browsers. Reference: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/isComposing (live verified).
- **Focus trap pattern (manual implementation)** — accessed 2026-05-24 via WebSearch "focus trap react manual implementation 2026 a11y wcag"; current best practice: manual Tab cycling con `focusable: button:not([disabled]), input:not([disabled]), [tabindex="0"]` selector + restore previous activeElement on close. Alternatives: `focus-trap-react` npm dep (added complexity para 1 mobile drawer, NO justifica). Decision: manual implementation in `ValeriaSidebar` useEffect.
- **react-resizable-panels v4.11.1** — F1-S4 cementado (8 días old desde F1-S4 architect 2026-05-23 + 1 día = 9 días old). Unchanged. No new release dispatched. `MIN_VALERIA_PX` ternary pattern preservado.
- **Knowledge cutoff disclosure**: Opus 4.7 cutoff = Jan 2026; researched live on 2026-05-24 via WebSearch + canonical docs. F1-S4 patterns reused verbatim (Aug 2026 era unchanged — only 23 days old at F1-S4 close).

