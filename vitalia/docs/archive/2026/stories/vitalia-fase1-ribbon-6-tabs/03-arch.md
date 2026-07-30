<!-- voseo-allowed: glosario reference + internal architecture documentation -->

---
story_id: vitalia-fase1-ribbon-6-tabs
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-25
architect_iter: 1
architect_run_on: 2026-05-25
surfaces: FE_ONLY
predecessors_done:
  - vitalia-fase1-shell-layout-5050   # F1-S4 — AppPanelSlot placeholder pattern
  - vitalia-fase1-valeria-chat-skeleton # F1-S6 — agent-catalog.ts SSoT origin
---

# F1-S7 · vitalia-fase1-ribbon-6-tabs · 03-arch.md (consolidado FE)

## § 0 — Context Summary

- **Story:** `vitalia-fase1-ribbon-6-tabs` · outcome `vitalia-mvp-ui-foundation` · phase `fase-1`.
- **PR folder:** `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/`
- **Architect run on:** 2026-05-25 (Step 0 `date -u +%Y-%m-%d` = 2026-05-25, `date -u +%Y-%m` = 2026-05). Opus 4.7 knowledge cutoff Jan 2026; library currency (Next.js 16 App Router + React 19 + Shadcn/Radix Avatar+Tooltip+Button + Tailwind v4) verified live via canonical docs on 2026-05-25 — versiones cementadas F1-S0/F1-S4/F1-S6 sin upgrade.
- **Modules touched:** `shell-organism` (brand-local Vitalia frontend chrome — módulo doc `vitalia/docs/product/modules/shell-organism.md`).
- **Surfaces:** FE_ONLY · ZERO BE · ZERO AGENTIC · ZERO engine touch. NO fetch, NO API, NO LLM, NO PHI. Sólo UI nav puro.

### Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` (MODIFY EXTEND + helper) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab}.tsx` (NEW organism + 2 moléculas) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` (MODIFY: reemplaza skeleton placeholder por `<Ribbon />` real) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` (MODIFY: agregar helper `agentBorderClass` para active border-bottom — bg-soft helpers ya existen) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` (MODIFY shrink-only extend NEW names) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/test-ribbon-no-shadcn-tabs.test.ts` (NEW arch test) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/**` (NEW Playwright suite + POM + fixtures) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/__screenshots__/shell/ribbon-*.png` (×11 visual goldens NEW) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |

ZERO BE surface. ZERO AGENTIC surface. ZERO engine touch. R23 NO aplica (zero agentic, all FE production_code).

### Skills consulted (decisions ratified verbatim)

- **`frontend-expert`** — FSD-Lite: `components/shared/shell-organism/` correct para chrome cross-feature; `lib/agent-catalog.ts` EXTEND in-place (no nuevo `lib/agents/`); Server-First default + `'use client'` solo en hojas con hooks/event handlers (`Ribbon.tsx` consume `usePathname` + `useRouter` + `useParams` + keyboard state). Tests colocated `__tests__/` siblings. Runtime quality checklist: useEffect deps complete, no stale closures (handleKeyDown lee refs, no closures), hydration safety (pathname disponible via hook desde primer render Client).
- **`tessl__react-patterns`** — React 19 + Next.js 16 App Router: `'use client'` necesario en `Ribbon.tsx` (hooks `usePathname`/`useRouter`/`useParams` + `useRef` para roving tabindex DOM access + `onKeyDown` handler). `RibbonTab.tsx` + `ConfigTab.tsx` reciben handlers como props pero como viven dentro del padre Client heredan boundary. Roving tabindex pattern: índice `focusedIdx` en parent, refs array `tabRefs.current[]` para focus management imperativo (vía `tabRefs.current[idx]?.focus()` en handler). Sin `useEffect` para focus inicial (sería stale closure trap) — focus se mueve en respuesta a keyDown sync.
- **`tessl__shadcn-ui`** — REUSE primitives F1-S0: `Avatar` + `AvatarImage` + `AvatarFallback` (graceful PNG-404 fallback con initial letra), `Tooltip` + `TooltipProvider` + `TooltipTrigger` + `TooltipContent` (ConfigTab "Configurar" hover hint). `Button` variant ghost size icon disponible pero NO usado en RibbonTab/ConfigTab — son `<button>` raw con `cn()` classes propias (Shadcn Button impone size=icon=`size-9` que es 36px, no 40px del spec). ANTI-PATTERN confirmado: NO usar Shadcn `<Tabs>` Radix-based (su API asume `<TabsContent>` inline incompatible con Next.js route-based nav).
- **`tessl__tailwind`** — Semantic tokens ONLY (DC §5.1): `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `ring-ring`, `bg-agent-{slug}-soft`. Las 5 classes `bg-agent-{slug}-soft` ya están definidas en `globals.css` (F1-S1 + F1-S6 fill mateo gap) y purge-safe via `_agent-tw-classes.ts::agentBgSoftClass()` (consume desde Ribbon active state). NO hex literales. NO arbitrary values.
- **`tessl__vitest`** — Colocated `Component.test.tsx`. RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `next/navigation` via `vi.mock('next/navigation')` retornando `usePathname`/`useRouter`/`useParams` stubs. Cobertura unit: `Ribbon.test.tsx` (render 6 tabs + roving tabindex keyboard + active detection), `RibbonTab.test.tsx` (estados inactive/active/avatar fallback render), `ConfigTab.test.tsx` (tooltip render + IconButton 40x40), `extractAgentFromPath.test.ts` (puro — segments parsing).
- **`playwright-expert`** — Path canon NEW `e2e/regression/vitalia-fase1-ribbon-6-tabs/` (estructura `regression/{story-id}/` heredada F1-S6 final, consistente con `e2e/__screenshots__/shell/`). POM `RibbonPage` con métodos `goto({tenantId, agent, subtab})`, `getTab(slug)`, `clickTab(slug)`, `pressKey(key)`, `getActiveTab()`, `getConfigTab()`, `getTooltip()`, `setViewport()`, `setTheme()`. Fixtures REUSE `shell-theme.fixture.ts` + `clerk-auth.fixture.ts` (public route `/test-stack/shell-layout` bypassa auth gate). Visual goldens iter 1: `--update-snapshots --project=visual` post Chris ratify side-by-side mockup `ribbon.html`. Axe ruleset `wcag2aa`. Port 3002 vitalia. Native Linux (NO docker).
- **`tessl__nextjs-app-router-modularization`** — `'use client'` boundaries: `Ribbon.tsx` root Client por hooks (`usePathname` + `useRouter` + `useParams`); sub-componentes `RibbonTab.tsx` + `ConfigTab.tsx` también Client (reciben event handler props + onKeyDown). NO crear nuevas routes — `Ribbon.tsx` consume URL existente via `usePathname()` y dispara `router.push()` a paths que F1-S9 (routing-shell) implementará. En F1-S7 el `router.push` puede 404 (target route `/[tenantId]/[agent]/[subtab]/page.tsx` aún no existe) — gherkin spec asume comportamiento de redirect (browser navega, eventual 404 post-F1-S9 cubierto).
- **`backend-expert` / `copilot-expert` / `sales-agent-expert` / `offer-expert` / `brand-expert` / `metrics-expert` / `offer-type-preset-expert`** — NO cargar. Story es FE only chrome UI nav puro sin BE/agentic/dominio negocio (HIPAA-lite scope: `not_applicable`, ZERO PHI).

### CONTEXT-BRIEF source

Self-ran greps Path B + Read directos (CONTEXT-BRIEF.md absent — story-by-story sin Haiku context-builder). Lectura prioritaria ejecutada:

- `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/{checkpoint.md,01-spec.md,mockups/ribbon.html}`
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md`
- `vitalia/docs/product/modules/shell-organism.md`
- `vitalia/docs/product/capabilities/shell-organism/{valeria-chat,valeria-sidebar,layout-5050}.yaml`
- `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/{03-arch.md,06-tickets.yaml}` (AppPanelSlot pattern)
- `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-chat-skeleton/{03-arch.md,04-validators.yaml,05-guidelines.md,06-tickets.yaml}` (agent-catalog SSoT origin)
- `vitalia/frontend/src/lib/agent-catalog.ts` (EXTEND target — shape actual)
- `vitalia/frontend/src/components/shared/shell-organism/{AppPanelSlot.tsx,_agent-tw-classes.ts}` (MODIFY targets)
- `vitalia/frontend/src/components/ui/{avatar,tooltip,button}.tsx` (Shadcn primitives reuse)
- `vitalia/frontend/src/__tests__/architecture/test-agent-catalog-ssot.test.ts` + `test-no-cross-brand-shell-mirror.test.ts` (gates)
- Vitalia overlay rules: `vitalia/.claude/rules/{hipaa-lite,shell-mockup-per-component}.md`
- Cardinal rules: `frontend-fsd.md`, `spanish-text.md`, `tdd-mandatory.md`, `tenant-isolation.md`, `anti-duplication.md`.

### capability YAML files affected (post-merge updates required, paradigma post 2026-05)

- **NEW** `vitalia/docs/product/capabilities/shell-organism/ribbon.yaml` — capability nueva F1-S7 (`vitalia.shell-organism.ribbon`, status `live` post-merge; descripción: ribbon horizontal 5 tabs agentes (Lisa/Lucas/Adrián/Valeria/Camila) + ConfigTab IconButton; navegación route-based con `useRouter().push` a `/{tenantId}/{agent}/{defaultSubtab}`; active state via `usePathname` extraction; WAI-ARIA tablist completo con roving tabindex; avatar fallback graceful).
- **MODIFY** `vitalia/docs/product/capabilities/shell-organism/layout-5050.yaml` — agregar mención `AppPanelSlot ribbon placeholder reemplazado por <Ribbon /> real (F1-S7)` en Surfaces/Frontend.
- **AUTO-REGEN** `vitalia/docs/product/modules/shell-organism.md` — auto-list block via `scripts/reconcile_capabilities.py --brand vitalia` (R3 gitignored ok — list block es tracked).

### Architecture gates that must keep passing (extend, no break)

- `test_fsd_boundaries.test.ts` — shell-organism NO importa features/*; `lib/agent-catalog.ts` consumido cross-shell sin violar FSD.
- `test-no-cross-brand-shell-mirror.test.ts` — extend con nombres NEW (`Ribbon`, `RibbonTab`, `ConfigTab`, `extractAgentFromPath`, `AGENT_RIBBON_ORDER`).
- `test-shell-store-schema-readonly-f1-s5.test.ts` — invariant heredado F1-S5 (shell-store NO modificado, F1-S7 no toca store).
- `test-agent-catalog-ssot.test.ts` — extiende cobertura ya existente (agent-catalog.ts en allowlist hex/thumbnail; F1-S7 EXTEND no introduce hex nuevo).
- `test_no_hardcoded_colors.test.ts` — tokens semánticos ONLY; F1-S7 consume `bg-agent-{slug}-soft` via `agentBgSoftClass()` switch.
- `test_no_voseo_in_copy.test.ts` + `test-vitalia-ui-strings-no-voseo.test.ts` — microcopy verbatim 11 strings (`Mi Clínica`, `Atraer`, `Vender`, `Operar`, `Mantener`, `Configurar`, `Agentes` aria-label, 5 role labels).
- `test_server_first.test.ts` — `'use client'` allowlist shrink-only extend (Ribbon + RibbonTab + ConfigTab justificadamente client).
- `test-no-vt-classes-in-new-features.test.ts` — NO `.vt-*` legacy utility classes en NEW code.
- `test-skip-link-target.test.ts` — `<main id="main-content">` NO afectado (out-of-scope).
- **NEW** `test-ribbon-no-shadcn-tabs.test.ts` — invariant: NO import de `@/components/ui/tabs` (`<Tabs>` Radix-based) en Ribbon ni RibbonTab ni ConfigTab. Garantiza patrón route-based nav justificado.

## § 0.1 — Existing Systems Audit (NO NEW LAYER rule)

### Source of evidence

- [x] Self-run greps (Path B — context-builder fallback; CONTEXT-BRIEF.md absent for this story)

### Audit cross-module ejecutado

```bash
WS=/home/chalreme/Proyectos/luana-vitalia

# 1. Cross-brand mirror scan (anti-duplication.md cardinal rule)
for b in nicolify comunify lupulo; do
  for name in Ribbon RibbonTab ConfigTab extractAgentFromPath AGENT_RIBBON_ORDER; do
    matches=$(grep -rln "$name" $WS/$b/frontend/src 2>/dev/null | grep -v node_modules | wc -l)
    if [ "$matches" -gt 0 ]; then echo "$b::$name → $matches matches"; fi
  done
done
# Result: 0 matches en las 3 brands. ✅ No mirror existente.

# 2. Engine TS packages (core/@luana/*)
find $WS/core -name "Ribbon*" -o -name "ribbon*" 2>/dev/null | head
# Result: 0 matches. Engine TS packages no exponen shell ribbon abstraction. ✅

# 3. Same-brand existing duplicates (vitalia/frontend/src)
find $WS/vitalia/frontend/src -name "Ribbon*" -o -name "ConfigTab*" 2>/dev/null
# Result: 0 matches NEW names. ✅

# 4. Catalog SSoT path verification (anti-duplication HARD per checkpoint)
ls $WS/vitalia/frontend/src/lib/agent-catalog.ts $WS/vitalia/frontend/src/lib/agents/catalog.ts 2>/dev/null
# Result: agent-catalog.ts existe (F1-S6), lib/agents/catalog.ts NO existe. ✅ EXTEND in-place

# 5. Tailwind bg-agent-{slug}-soft already defined?
grep -E "bg-agent-(lisa|lucas|adrian|valeria|camila)-soft" $WS/vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts
# Result: 5 matches presentes en agentBgSoftClass(). ✅ Reuse helper existente.

# 6. AppPanelSlot current shape (target MODIFY)
grep -E "F1-S7|Ribbon|skeleton" $WS/vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx
# Result: skeleton placeholder explícitamente labeled "F1-S7 / S8 / S10". ✅ MODIFY swap clean.

# 7. Shadcn Tabs Radix usage scan (anti-pattern check)
grep -rln "@/components/ui/tabs\|<Tabs " $WS/vitalia/frontend/src/components 2>/dev/null
# Result: 0 matches — Shadcn Tabs primitive instalado pero no consumido. ✅ Arch test NEW enforce.
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `agent-catalog.ts` SSoT | `vitalia/frontend/src/lib/agent-catalog.ts` | active F1-S6 done | **EXTEND in-place** — agregar `tabLabel: string` + `defaultSubtab: string` a `AgentDescriptor` + `AGENT_RIBBON_ORDER` constante + helper `extractAgentFromPath`. NO crear `lib/agents/catalog.ts` separado (anti-duplication HARD). |
| `_agent-tw-classes.ts` Tailwind helpers | `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` | active F1-S6 done | **EXTEND in-place** — agregar `agentBorderBottomClass(slug)` opcional (F1-S7 NO usa border-bottom per spec batch 2 Q4 — `bg-agent-{slug}-soft` tint únicamente). Por ahora MODIFY mínimo si surge necesidad; default: 0 changes (reuse `agentBgSoftClass`). |
| `AppPanelSlot.tsx` skeleton placeholder | `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | active F1-S4 done | **MODIFY** — reemplazar skeleton silhouette ribbon (líneas 44-69) por `<Ribbon />` real. Sub-tabs skeleton + content skeleton **PRESERVAR** (F1-S8 + F1-S10 los reemplazarán). Slot label "F1-S7/S8/S10" actualizar a "F1-S8/S10" (S7 listo). |
| Shadcn `Avatar` + `Tooltip` + `Button` | `vitalia/frontend/src/components/ui/{avatar,tooltip,button}.tsx` | active F1-S0 done | **REUSE sin modificar** — Avatar para fallback PNG-404 (SC-9), Tooltip para ConfigTab. Button NO usado (size icon = 36px ≠ spec 40px). |
| `Ribbon`, `RibbonTab`, `ConfigTab`, `extractAgentFromPath`, `AGENT_RIBBON_ORDER` | n/a | does-not-exist | **NEW** (justificado — brand-local shell pattern Vitalia, zero matches cross-brand, no engine core overlap, no Shadcn primitive equivalente per anti-pattern bloqueado en spec). |
| Test path canon `e2e/regression/{story-id}/` | n/a | active F1-S6 inauguró `e2e/shell-organism/` final | **NEW path** `e2e/regression/vitalia-fase1-ribbon-6-tabs/` — heredado del checkpoint que cita ese path; consistente con `e2e/__screenshots__/shell/` para visual goldens. |

### Decisión por sistema

- **`agent-catalog.ts`**: EXTEND in-place (anti-duplication HARD per checkpoint). Cero archivos nuevos en `lib/agents/`.
- **`AppPanelSlot.tsx`**: MODIFY (swap skeleton ribbon por componente real, preserve resto skeleton).
- **`Ribbon`, `RibbonTab`, `ConfigTab`**: NEW justified — patrón brand-local, no Shadcn equivalente, no cross-brand mirror.
- **`extractAgentFromPath`**: NEW utility puro co-located en `lib/agent-catalog.ts` (decisión: NO crear `lib/agents/routing.ts` separado — la función pertenece semánticamente al catalog porque consume `AgentSlug` enum + retorna `AgentSlug | 'config' | null`).
- **Test arch NEW `test-ribbon-no-shadcn-tabs.test.ts`**: NEW invariant — garantiza patrón route-based nav justificado, previene regresión futura a `<Tabs>` Radix.

**Cross-brand lift evaluation:** patrón Ribbon es brand-local Vitalia. Per `.claude/rules/anti-duplication.md`, lift se dispara on second occurrence. F1-S7 es primera ocurrencia → NEW correct.

**LIFT_CANDIDATE notes (futuras stories):**

- Si nicolify/comunify/lupulo/futuros adoptan patrón multi-agente ribbon similar → lift candidate a `core/luana-core-ui-shell/` futuro (promotion proposal `/pm-luana`). Hoy NO existe paralelismo cross-brand.
- `extractAgentFromPath` co-located en `agent-catalog.ts` por simplicidad SSoT. Si en F1-S8 (sub-tabs-line2) o F1-S9 (routing-shell) emerge necesidad de helpers de routing más amplios (e.g., `extractSubtabFromPath`, `buildAgentPath`), considerar separar `lib/agents/routing.ts` en esa story (no en F1-S7).

## § 1 — Surfaces involved (verbatim)

| Surface | Aplica | Owner |
|---|---|---|
| BE (FastAPI Python) | NO | — |
| AGENTIC (LangGraph / deepagents / sales_agent) | NO | — |
| FE (Next.js 16 App Router + Shadcn + Tailwind + roving tabindex pattern) | **SÍ** | `builder-frontend` Sonnet/opencode |

## § 2 — FE Architecture Detail

### § 2.1 — `agent-catalog.ts` EXTEND (anti-duplication HARD)

`vitalia/frontend/src/lib/agent-catalog.ts` — **MODIFY** existente. Agregar 2 campos a `AgentDescriptor` + constante `AGENT_RIBBON_ORDER` + helper `extractAgentFromPath`.

```ts
// EXISTING (preserve):
export type AgentSlug = "lisa" | "valeria" | "adrian" | "lucas" | "camila" | "mateo";

export interface AgentDescriptor {
  slug: AgentSlug;
  name: string;
  role: string;
  colorToken: string;
  colorSoftToken: string;
  hex: string;
  thumbnail: string;
  transparent: string;
  initial: string;
  // ★ NEW F1-S7 — añadir como campos REQUIRED:
  tabLabel: string;       // verbo/sustantivo corto para Ribbon ("Mi Clínica", "Atraer", "Vender", "Operar", "Mantener", "Tecnología")
  defaultSubtab: string;  // slug del subtab default al cliquear ribbon ("marca", "lanzar", "inbox", "agenda", "voz", "tech")
}

// MODIFY AGENT_CATALOG entries — agregar tabLabel + defaultSubtab a cada agente:
export const AGENT_CATALOG: Record<AgentSlug, AgentDescriptor> = {
  lisa:    { ..., tabLabel: "Mi Clínica", defaultSubtab: "marca" },
  lucas:   { ..., tabLabel: "Atraer",     defaultSubtab: "lanzar" },
  adrian:  { ..., tabLabel: "Vender",     defaultSubtab: "inbox" },
  valeria: { ..., tabLabel: "Operar",     defaultSubtab: "agenda" },
  camila:  { ..., tabLabel: "Mantener",   defaultSubtab: "voz" },
  mateo:   { ..., tabLabel: "Tecnología", defaultSubtab: "ia" },   // NO en ribbon order, pero shape completa
};

// ★ NEW F1-S7 constants + helper:

/** Orden canónico de tabs en el Ribbon. Mateo EXCLUIDO (agente transversal — out-of-scope F1-S7). */
export const AGENT_RIBBON_ORDER: readonly AgentSlug[] = ["lisa", "lucas", "adrian", "valeria", "camila"] as const;

/** Tab slug especial — ConfigTab no es AgentSlug pero comparte API de activación URL. */
export type RibbonTabSlug = AgentSlug | "config";

/**
 * Extrae el segmento [agent] del pathname.
 *
 * Pattern URL: /{tenantId}/{agent}/{subtab}/... → retorna {agent} si matchea slug válido,
 * null si segmento inválido, ausente, o XSS payload.
 *
 * Casos:
 *   /tenant-x/lisa/marca       → "lisa"
 *   /tenant-x/config/cuenta    → "config"
 *   /tenant-x/foobar/baz       → null (slug inválido)
 *   /tenant-x                  → null (no hay segmento [agent])
 *   /                          → null (vacío)
 *   /<script>...               → null (sanitization implícita por regex de slugs)
 */
export function extractAgentFromPath(pathname: string | null | undefined): RibbonTabSlug | null {
  if (!pathname) return null;
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length < 2) return null;
  const candidate = segments[1];
  if (candidate === "config") return "config";
  if ((AGENT_SLUGS as string[]).includes(candidate)) {
    return candidate as AgentSlug;
  }
  return null;
}
```

**Decisiones cementadas:**

- **D1 — Mateo en catalog pero NO en ribbon:** `AgentSlug` mantiene los 6 agentes (incluyendo mateo) por compat F1-S6 (ChatHeader/MessageBubble param). `AGENT_RIBBON_ORDER` excluye mateo. `tabLabel` + `defaultSubtab` de mateo son shape-completa por consistencia type-safe (mateo aparecerá en surface futura — out-of-scope F1-S7).
- **D2 — `extractAgentFromPath` co-located:** vive en `agent-catalog.ts` (consume `AgentSlug` enum + `AGENT_SLUGS`). Decisión simplificada vs `lib/agents/routing.ts` separado (SSoT proximidad). Si F1-S8/F1-S9 requieren más helpers routing → considerar separar entonces.
- **D3 — Sin validation framework:** `extractAgentFromPath` retorna `null` para invalid (no throw, no Zod). XSS payload `/<script>...` queda como `null` porque `<script>` no matchea ningún slug. React JSX auto-escape cubre defense-in-depth.
- **D4 — `tabLabel` para mateo:** "Tecnología" (verbo/sustantivo corto Spanish neutro). NO consumido por Ribbon F1-S7 pero requerido por TypeScript per `Record<AgentSlug, AgentDescriptor>` exhaustivo.

### § 2.2 — `Ribbon.tsx` organism (NEW)

`vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx` — NEW.

**Client Component justification:**
- Consume `usePathname()` + `useRouter()` + `useParams()` de `next/navigation` (Client-only hooks).
- Implementa roving tabindex con `useRef<(HTMLButtonElement | null)[]>` + state `focusedIdx` (Client state).
- Event handler `onKeyDown` para WAI-ARIA tablist keyboard support.

**Shape:**

```tsx
'use client';

import { useState, useRef, useCallback, type KeyboardEvent } from "react";
import { usePathname, useRouter, useParams } from "next/navigation";
import { AGENT_CATALOG, AGENT_RIBBON_ORDER, extractAgentFromPath, type AgentSlug, type RibbonTabSlug } from "@/lib/agent-catalog";
import { RibbonTab } from "./RibbonTab";
import { ConfigTab } from "./ConfigTab";

/**
 * Ribbon — Vitalia shell organismo (F1-S7).
 *
 * Barra horizontal arriba del AppPanel con 5 tabs agente (Lisa/Lucas/Adrián/Valeria/Camila)
 * + ConfigTab (⚙️ Configurar) right-aligned. Active state derivado de URL via usePathname.
 * Click navega a `/{tenantId}/{agent}/{defaultSubtab}`. WAI-ARIA tablist completo con
 * roving tabindex (Arrow Left/Right + Home + End + Enter + Space).
 *
 * spec_anchor: 01-spec.md § Gherkin SC-1..SC-9 + § Wireframe + § Accessibility
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */
export function Ribbon() {
  const pathname = usePathname();
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  const activeSlug: RibbonTabSlug | null = extractAgentFromPath(pathname);

  // Roving tabindex: índice del tab focused (no necesariamente el active).
  // Initial focusedIdx = index del active si existe, sino 0 (Lisa).
  const initialFocusIdx = activeSlug === "config"
    ? AGENT_RIBBON_ORDER.length
    : (activeSlug !== null ? AGENT_RIBBON_ORDER.indexOf(activeSlug as AgentSlug) : 0);
  const safeInitialIdx = initialFocusIdx >= 0 ? initialFocusIdx : 0;
  const [focusedIdx, setFocusedIdx] = useState<number>(safeInitialIdx);

  // Refs array para focus management imperativo (6 elementos: 5 agentes + ConfigTab)
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const totalTabs = AGENT_RIBBON_ORDER.length + 1; // 5 + 1 ConfigTab

  const navigateTo = useCallback((slug: RibbonTabSlug) => {
    const tenantId = params?.tenantId;
    if (!tenantId) return;
    if (slug === "config") {
      router.push(`/${tenantId}/config/cuenta`);
      return;
    }
    const descriptor = AGENT_CATALOG[slug];
    router.push(`/${tenantId}/${slug}/${descriptor.defaultSubtab}`);
  }, [params, router]);

  const focusTab = useCallback((idx: number) => {
    const safeIdx = ((idx % totalTabs) + totalTabs) % totalTabs;
    setFocusedIdx(safeIdx);
    tabRefs.current[safeIdx]?.focus();
  }, [totalTabs]);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLElement>) => {
    switch (e.key) {
      case "ArrowRight":
        e.preventDefault();
        focusTab(focusedIdx + 1);
        return;
      case "ArrowLeft":
        e.preventDefault();
        focusTab(focusedIdx - 1);
        return;
      case "Home":
        e.preventDefault();
        focusTab(0);
        return;
      case "End":
        e.preventDefault();
        focusTab(totalTabs - 1);
        return;
      case "Enter":
      case " ": {
        e.preventDefault();
        if (focusedIdx < AGENT_RIBBON_ORDER.length) {
          navigateTo(AGENT_RIBBON_ORDER[focusedIdx]);
        } else {
          navigateTo("config");
        }
        return;
      }
    }
  }, [focusedIdx, focusTab, navigateTo, totalTabs]);

  return (
    <nav
      role="tablist"
      aria-label="Agentes"
      data-testid="ribbon"
      onKeyDown={handleKeyDown}
      className="flex h-14 items-stretch gap-1 overflow-x-auto border-b border-border bg-card px-3"
    >
      {AGENT_RIBBON_ORDER.map((slug, idx) => (
        <RibbonTab
          key={slug}
          ref={(el) => { tabRefs.current[idx] = el; }}
          slug={slug}
          active={activeSlug === slug}
          tabIndex={focusedIdx === idx ? 0 : -1}
          onClick={() => navigateTo(slug)}
          onFocus={() => setFocusedIdx(idx)}
        />
      ))}
      <ConfigTab
        ref={(el) => { tabRefs.current[AGENT_RIBBON_ORDER.length] = el; }}
        active={activeSlug === "config"}
        tabIndex={focusedIdx === AGENT_RIBBON_ORDER.length ? 0 : -1}
        onClick={() => navigateTo("config")}
        onFocus={() => setFocusedIdx(AGENT_RIBBON_ORDER.length)}
      />
    </nav>
  );
}
```

**Decisiones cementadas:**

- **D5 — Roving tabindex pattern oficial WAI-ARIA:** `focusedIdx` state + refs array + `tabIndex={0|-1}` per tab. Solo el focused tiene `tabIndex=0`, el resto `tabIndex=-1`. Tab key entra al focused; Arrow keys mueven focus sin activar.
- **D6 — Wrap circular:** ArrowRight desde último → Lisa; ArrowLeft desde Lisa → ConfigTab. Modulo aritmético `((idx % total) + total) % total` para safe negative.
- **D7 — Click vs Enter/Space:** click navega inmediato; Enter/Space en focused tab navega (no toggles). Sin double-fire (handler único `navigateTo`).
- **D8 — `useCallback` para handlers:** evita re-render de RibbonTab children cuando focusedIdx cambia. `tabRefs` ref-callback inline OK porque pasa ref directo (no closure).
- **D9 — onFocus sync:** click directo sobre tab inactive llama `onFocus` antes de onClick → setFocusedIdx update OK (sin double-fire navigate por onFocus, sólo state).
- **D10 — Active vs focused son ORTOGONALES:** `active` se deriva de URL (`extractAgentFromPath`); `focusedIdx` se deriva de keyboard interaction. Diff conceptual: focused = "que tab tiene focus visible", active = "que tab refleja el segmento [agent] URL".
- **D11 — ConfigTab no es AgentSlug:** índice especial `AGENT_RIBBON_ORDER.length` (= 5). Type unión `RibbonTabSlug = AgentSlug | "config"`.

### § 2.3 — `RibbonTab.tsx` molécula (NEW)

`vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx` — NEW.

```tsx
'use client';

import { forwardRef } from "react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { AGENT_CATALOG, type AgentSlug } from "@/lib/agent-catalog";
import { agentBgSoftClass } from "./_agent-tw-classes";
import { cn } from "@/lib/utils";

export interface RibbonTabProps {
  slug: AgentSlug;
  active: boolean;
  tabIndex: 0 | -1;
  onClick: () => void;
  onFocus: () => void;
}

/**
 * RibbonTab — Vitalia shell molécula (F1-S7).
 *
 * Botón tab agente con Avatar + tabLabel + role label.
 * Active state: bg-agent-{slug}-soft tint + label font-semibold.
 * Inactive state: transparent + text-muted-foreground + hover:bg-muted.
 *
 * Avatar fallback: si PNG 404 → <AvatarFallback> con initial letter sobre bg-agent-{slug}-soft.
 *
 * spec_anchor: 01-spec.md § Estados visuales · 03-arch.md § 2.3
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */
export const RibbonTab = forwardRef<HTMLButtonElement, RibbonTabProps>(function RibbonTab(
  { slug, active, tabIndex, onClick, onFocus },
  ref,
) {
  const descriptor = AGENT_CATALOG[slug];

  return (
    <button
      ref={ref}
      type="button"
      role="tab"
      aria-selected={active}
      tabIndex={tabIndex}
      data-testid={`ribbon-tab-${slug}`}
      data-active={active ? "true" : "false"}
      onClick={onClick}
      onFocus={onFocus}
      className={cn(
        // base layout
        "flex shrink-0 items-center gap-2 rounded-md px-4 text-sm transition-colors",
        // focus ring
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        // active vs inactive — active:hover PRESERVA el tint del agente (Q16 cement)
        // Specificity HARD: data-[active=true]:bg-agent-X-soft gana sobre hover:bg-muted natural
        // porque attribute selector + pseudo-class > pseudo-class sola en CSS specificity.
        active
          ? cn(
              agentBgSoftClass(slug),
              "font-semibold text-foreground",
              // active:hover NUNCA degrada (Q16)
              `hover:${agentBgSoftClass(slug)}`,
            )
          : "font-medium text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Avatar className="size-7 shrink-0" aria-hidden="true">
        <AvatarImage src={descriptor.thumbnail} alt="" />
        <AvatarFallback className={cn(agentBgSoftClass(slug), "text-foreground")}>
          {descriptor.initial}
        </AvatarFallback>
      </Avatar>
      {/* Q15 cement: whitespace-nowrap garantiza ribbon h-14 uniforme en widths estrechos */}
      <span className="flex flex-col items-start leading-tight whitespace-nowrap">
        <span className="whitespace-nowrap">{descriptor.tabLabel}</span>
        <span className="whitespace-nowrap text-[10px] text-muted-foreground">{descriptor.name}</span>
      </span>
    </button>
  );
});
```

**Decisiones cementadas:**

- **D12 — `forwardRef` para roving tabindex:** parent (Ribbon) necesita `ref.focus()` imperativo. `forwardRef` con HTMLButtonElement.
- **D13 — `Avatar` Shadcn:** REUSE primitive con `size-7` override (28px per spec). `AvatarImage src` apunta a `descriptor.thumbnail` (`/agents/{slug}/thumbnail.png`). `AvatarFallback` con `initial` letter sobre `agentBgSoftClass(slug)` background (color identificable del agente).
- **D14 — `alt=""` decorativo:** info redundante con label parent. Screen reader lee `tabLabel`+`role` del button.
- **D15 — `data-active` attr:** facilita Playwright querying + visual goldens snapshot identification.
- **D16 — NO border-bottom:** decisión Batch 2 Q4 — solo bg-soft tint + font-semibold (flat). Cero `border-b` classes.
- **D17 — `agentBgSoftClass()` consumer:** REUSE helper F1-S6 (`_agent-tw-classes.ts`) — JIT-safe switch, no template strings.
- **D17.1 — `whitespace-nowrap` HARD (Q15 cement post audit Playwright):** ambos spans (`tabLabel` + `name`) deben tener `whitespace-nowrap`. Sin esto, "Mi Clínica" (2 words) wrappea a 2 líneas en widths estrechos (modo agentic split 50/50, panel ~640px) → row height crece → ribbon `h-14` se rompe. Audit Playwright `/tmp/ribbon-inspect/00-full-light.png` evidenció el bug en mockup ratificado.
- **D17.2 — `active:hover` preserva tint (Q16 cement):** repetir `hover:${agentBgSoftClass(slug)}` cuando `active=true` para forzar specificity sobre hover natural. Sin esto, mouse sobre active tab degrada momentáneamente a gris (`:hover` con misma specificity gana por orden CSS). Auditor `tests/architecture/test-ribbon-active-hover-preserves-tint.test.ts` enforces (computed style check post-hover event).
- **D17.3 — Tabs orgánicos NO uniformes (Q14 cement):** decisión Batch 5 — cada tab toma width necesario para su content. `shrink-0` para evitar squash, pero **NO `min-w-[Npx]`**. Labels variables ("Atraer" ~95px vs "Mi Clínica" ~140px) producen tabs asimétricos pero compactos. En widths estrechos `overflow-x-auto` cubre la diferencia.

### § 2.4 — `ConfigTab.tsx` molécula (NEW)

`vitalia/frontend/src/components/shared/shell-organism/ConfigTab.tsx` — NEW.

```tsx
'use client';

import { forwardRef } from "react";
import { Settings } from "lucide-react";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export interface ConfigTabProps {
  active: boolean;
  tabIndex: 0 | -1;
  onClick: () => void;
  onFocus: () => void;
}

/**
 * ConfigTab — Vitalia shell molécula (F1-S7).
 *
 * IconButton 40x40 right-aligned (`ml-auto`) con icon ⚙ Settings (Lucide).
 * Active state: bg-muted + ring-1 ring-border + data-active="true".
 * Inactive: bg-muted + text-muted-foreground.
 * Hover inactive: bg-muted/80 + text-foreground + Tooltip "Configurar" visible.
 * Focus visible: ring-2 ring-ring ring-offset-1.
 *
 * Tooltip "Configurar" oculta tras click (active state) — Radix default behavior:
 * tooltip se asocia a hover/focus state, click no necesariamente lo cierra; UX cementada
 * spec § 5 SC-3 "tooltip se oculta tras click" implementada via `delayDuration` natural
 * de Radix + click triggers navigation (re-render unmounting).
 *
 * spec_anchor: 01-spec.md § Estados visuales ConfigTab · 03-arch.md § 2.4
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */
export const ConfigTab = forwardRef<HTMLButtonElement, ConfigTabProps>(function ConfigTab(
  { active, tabIndex, onClick, onFocus },
  ref,
) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          ref={ref}
          type="button"
          role="tab"
          aria-label="Configurar"
          aria-selected={active}
          tabIndex={tabIndex}
          data-testid="ribbon-config-tab"
          data-active={active ? "true" : "false"}
          onClick={onClick}
          onFocus={onFocus}
          className={cn(
            "ml-auto inline-flex size-10 shrink-0 items-center justify-center self-center rounded-md transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
            active
              ? "bg-muted text-foreground ring-1 ring-border"
              : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground",
          )}
        >
          <Settings className="size-5" aria-hidden="true" />
        </button>
      </TooltipTrigger>
      <TooltipContent side="bottom" sideOffset={4}>Configurar</TooltipContent>
    </Tooltip>
  );
});
```

**Decisiones cementadas:**

- **D18 — `<Tooltip>` Shadcn primitive REUSE:** `TooltipTrigger asChild` envuelve el `<button>` raw. `TooltipContent` debajo (`side="bottom"`).
- **D19 — Tooltip on active:** Radix tooltip se asocia a hover/focus state. Click → navigation → componente re-render con active state → tooltip cierra naturalmente. Auditor verifica vía Playwright spec SC-3 (`getTooltip()` no visible post click).
- **D20 — `size-10` (40x40):** explícito vía Tailwind. NO usar Shadcn `Button size="icon"` (`size-9` = 36px conflict). `inline-flex items-center justify-center` para Lucide icon centering.
- **D21 — `ml-auto` right-align:** `ConfigTab` consume class `ml-auto` que en flex container empuja al final. Self-center via `self-center` (h-14 ribbon container, 40px tab vertical-centered).
- **D22 — `aria-label="Configurar"` mandatory:** sin label text visible → screen reader necesita aria-label explícito. Tooltip "Configurar" es complementario (hover/focus hint visual).

### § 2.5 — `AppPanelSlot.tsx` MODIFY

`vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` — MODIFY.

**Cambios:**

1. Reemplazar el bloque skeleton ribbon (líneas 44-69 — silhouette con 5 avatares + Configurar) por `<Ribbon />` real.
2. PRESERVAR el bloque sub-tabs skeleton (líneas 71-77 — F1-S8 lo reemplazará).
3. PRESERVAR el bloque content skeleton (líneas 79-90 — F1-S10 lo reemplazará).
4. Actualizar slot label: "AppPanelSlot · F1-S7 / S8 / S10" → "AppPanelSlot · F1-S8 / S10" (S7 listo).
5. AppPanelSlot deja de ser Server Component **siempre** — ahora hospeda `<Ribbon />` que es Client. **OPCIÓN A** (recomendada): mantener AppPanelSlot Server Component que renderiza `<Ribbon />` (Next.js soporta Server hosting Client perfectamente — boundary natural). **OPCIÓN B**: convertir AppPanelSlot a Client. Decisión: **OPCIÓN A** (Server-First default + Ribbon Client se monta dentro).

```tsx
// AppPanelSlot.tsx (modified — keep Server Component, host <Ribbon />)
import { Ribbon } from "./Ribbon";

export function AppPanelSlot({ children }: AppPanelSlotProps) {
  return (
    <section
      role="region"
      aria-label="Panel aplicación"   // ← updated (no longer "placeholder F1-S7/S8/S10")
      data-testid="app-panel-slot"
      className="relative flex h-full min-h-0 flex-col overflow-hidden bg-background"
    >
      {/* Ribbon real (F1-S7) — reemplaza skeleton */}
      <Ribbon />

      {/* Sub-tabs skeleton (~40px) — F1-S8 reemplazará */}
      <div className="hidden md:flex items-center gap-3 border-b border-border px-4 h-10">
        <div className="h-2 w-16 rounded bg-muted opacity-45" />
        <div className="h-2 w-20 rounded bg-muted opacity-45" />
        <div className="h-2 w-14 rounded bg-muted opacity-45" />
        <div className="h-2 w-[70px] rounded bg-muted opacity-45" />
      </div>

      {/* Content area silhouette — F1-S10 reemplazará */}
      <div className="flex-1 min-h-0 overflow-hidden flex flex-col gap-4 p-6">
        <div className="h-3.5 w-[42%] rounded bg-muted opacity-45" />
        <div className="h-2 w-[78%] rounded bg-muted opacity-45" />
        <div className="h-2 w-[60%] rounded bg-muted opacity-45" />
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="h-[120px] rounded-md bg-muted opacity-55" />
          <div className="h-[120px] rounded-md bg-muted opacity-55" />
          <div className="h-[120px] rounded-md bg-muted opacity-55" />
          <div className="h-[120px] rounded-md bg-muted opacity-55" />
        </div>
      </div>

      {/* Children pass-through (preserved from F1-S4) */}
      {children !== undefined && (
        <div className="absolute inset-0 z-10 pointer-events-none">
          <div className="h-full w-full pointer-events-auto">{children}</div>
        </div>
      )}

      {/* Slot label updated */}
      <span
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 whitespace-nowrap rounded-md border border-dashed border-border bg-background/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground pointer-events-none"
        aria-hidden="true"
      >
        AppPanelSlot · F1-S8 / S10
      </span>
    </section>
  );
}
```

**Tests update:**
- `AppPanelSlot.test.tsx` existing tests (5 unit tests heredados F1-S4) deben seguir GREEN. Verificar:
  - `<Ribbon />` se renderiza ahora donde antes había el skeleton (test selector `[data-testid=ribbon]` presente).
  - El bloque skeleton sub-tabs sigue presente.
  - El bloque skeleton content sigue presente.
  - Slot label actualizado a "F1-S8 / S10".

### § 2.6 — `_agent-tw-classes.ts` (no MODIFY required)

`bg-agent-{slug}-soft` para los 5 agentes activos (lisa/lucas/adrian/valeria/camila) **ya está cubierto** por `agentBgSoftClass()` existente F1-S6. NO se requiere modificar el archivo. Solo Mateo está incluido pero no consumido por Ribbon (excluido del order).

Si auditor reporta classes faltantes en Tailwind purge → root cause es JIT scanner missing files, fix vía añadir paths al `tailwind.config.ts` content array (no en este helper).

### § 2.7 — Arch test NEW — `test-ribbon-no-shadcn-tabs.test.ts`

`vitalia/frontend/src/__tests__/architecture/test-ribbon-no-shadcn-tabs.test.ts` — NEW.

Invariant: NO import de `@/components/ui/tabs` en `Ribbon.tsx`, `RibbonTab.tsx`, `ConfigTab.tsx`. Garantiza patrón route-based nav justificado (anti-pattern bloqueado en spec).

```ts
import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const ROOT = resolve(__dirname, "../../..");

describe("arch: Ribbon does NOT import Shadcn <Tabs> Radix-based primitive", () => {
  const RIBBON_FILES = [
    "src/components/shared/shell-organism/Ribbon.tsx",
    "src/components/shared/shell-organism/RibbonTab.tsx",
    "src/components/shared/shell-organism/ConfigTab.tsx",
  ];

  it("no import from @/components/ui/tabs (Radix-based — incompatible with route nav)", () => {
    const violations: string[] = [];
    for (const rel of RIBBON_FILES) {
      const abs = resolve(ROOT, rel);
      if (!existsSync(abs)) continue;
      const src = readFileSync(abs, "utf-8");
      // Match: import ... from "@/components/ui/tabs"
      if (/from\s+["']@\/components\/ui\/tabs["']/.test(src)) {
        violations.push(`${rel}: imports @/components/ui/tabs — use route-based nav pattern instead`);
      }
    }
    expect(violations).toHaveLength(0);
  });

  it("no JSX <Tabs ...> usage in Ribbon files", () => {
    const violations: string[] = [];
    for (const rel of RIBBON_FILES) {
      const abs = resolve(ROOT, rel);
      if (!existsSync(abs)) continue;
      const src = readFileSync(abs, "utf-8");
      // Match: <Tabs (with space or end)
      if (/<Tabs[\s>]/.test(src)) {
        violations.push(`${rel}: uses <Tabs> JSX — Radix Tabs assumes inline <TabsContent>, incompatible with Next.js route segments`);
      }
    }
    expect(violations).toHaveLength(0);
  });
});
```

### § 2.8 — Tailwind classes pattern (purge safety)

Las classes Tailwind dinámicas consumidas:

- `bg-agent-{slug}-soft` ×5 — ya purge-safe via `_agent-tw-classes.ts::agentBgSoftClass()` switch (NO template strings).
- `bg-muted`, `bg-muted/80`, `bg-card`, `bg-background` — semantic tokens estáticos, purge-safe.
- `text-foreground`, `text-muted-foreground` — semantic tokens, purge-safe.
- `border-border`, `ring-border`, `ring-ring`, `ring-offset-1`, `ring-2`, `ring-1` — semantic tokens, purge-safe.

Cero arbitrary values (`[10px]` text-size sí permitido — heredado F1-S6 `text-[10px]` para role sub-label). Cero hex literales.

## § 3 — Data flow

- **No API consumed.** Ribbon es UI nav puro. Click → `router.push()`. URL → `usePathname()` → derive active.
- **No React Query keys.** No fetch.
- **No mutations.** Stateless component derive de URL.
- **No global state (zustand).** Active agent es derived from URL — single source of truth.
- **Routing:** `useParams<{ tenantId: string }>()` + `usePathname()` + `useRouter()` (Next.js App Router). Path target: `/{tenantId}/{agent}/{defaultSubtab}` o `/{tenantId}/config/cuenta`.

## § 4 — Tenant isolation

N/A para Ribbon (no DB queries, no fetches, no PHI). PERO: `useParams<{ tenantId: string }>()` debe usarse para route push — NUNCA hardcodear tenantId. Si `params?.tenantId` es undefined (caso edge, ej. tested en isolation sin route group), navigation se cancela (early return en `navigateTo`). Auditor verifica el guard.

## § 5 — HIPAA-lite scope

`not_applicable`. Ribbon es chrome UI nav puro sin acceso a PHI. No queries a `patient_*`, `medical_*`, `treatment_*`. No outbound messaging. No audit log. Vitalia overlay `hipaa-lite.md` no aplica a esta story.

## § 6 — Cross-cutting decisions

| ID | Decision | Justification |
|---|---|---|
| CC-1 | EXTEND `agent-catalog.ts` (NO crear `lib/agents/catalog.ts`) | Anti-duplication HARD per checkpoint. Catalog SSoT vive en `agent-catalog.ts` desde F1-S6. |
| CC-2 | Mateo en `AgentSlug` enum + `tabLabel`/`defaultSubtab` shape-completos pero EXCLUIDO de `AGENT_RIBBON_ORDER` | Mateo es agente transversal (surface futura — out-of-scope F1-S7); preservar type-safe exhaustive `Record<AgentSlug, AgentDescriptor>`. |
| CC-3 | Roving tabindex pattern manual (NO Shadcn `<Tabs>` Radix) | Spec § Componentes anti-pattern bloqueado: Shadcn Tabs asume `<TabsContent>` inline incompatible con Next.js route-based nav. Implementation custom justificada. |
| CC-4 | Active vs focused ortogonales | Active = URL-derived (stateless). Focused = keyboard-state (parent component). Diff conceptual respetado en spec § Accessibility roving tabindex. |
| CC-5 | `extractAgentFromPath` co-located en `agent-catalog.ts` | SSoT proximidad — consume AgentSlug enum directo. Separar `lib/agents/routing.ts` solo si F1-S8/F1-S9 requieren helpers adicionales (deferred). |
| CC-6 | AppPanelSlot mantiene Server Component | `<Ribbon />` Client hospedado dentro — Next.js soporta boundary natural. Server-First default preserved. |
| CC-7 | NO border-bottom en active tab (solo bg-soft tint) | Decisión Batch 2 Q4 spec — flat design ratificado. |
| CC-8 | Misma horizontal ambos modos shell (agentic + web) | Decisión Batch 1 spec — NO if-statements `mode === 'web'`. `overflow-x-auto` adapta natural. |
| CC-9 | Tests path `e2e/regression/{story-id}/` | Consistencia con checkpoint + visual goldens `e2e/__screenshots__/shell/`. F1-S6 final inauguró `e2e/shell-organism/` pero F1-S7 sigue checkpoint path canónico. |
| CC-10 | Visual goldens: 11 PNGs (NO 12) | Decisión Batch 4 Chris — set 11 cubre todos estados con menos duplicación. |
| CC-11 | Sub-tabs + content skeleton **preservados** en AppPanelSlot | F1-S8 + F1-S10 los reemplazarán en sus stories. F1-S7 scope estrictamente al ribbon row. |

## § 7 — LIFT_CANDIDATE notes (out-of-tickets)

- **L-1 — `Ribbon` + `RibbonTab` + `ConfigTab` cross-brand lift:** si nicolify/comunify/lupulo adoptan patrón multi-agente ribbon similar → triggerea `/pm-luana` promotion proposal a `core/luana-core-ui-shell/` (TS package futuro). Hoy 0 matches cross-brand.
- **L-2 — `extractAgentFromPath` helper:** posible lift a engine si patrón URL `/{tenantId}/{agent}/{subtab}` se replica cross-brand. Hoy brand-local Vitalia.
- **L-3 — Roving tabindex pattern:** si emerge en otras stories Vitalia (e.g., sub-tabs F1-S8 con keyboard nav similar) → considerar extraer hook `useRovingTabindex` a `vitalia/frontend/src/hooks/`. Hoy in-line en Ribbon.tsx.

NO crear tickets para estos LIFT_CANDIDATES en F1-S7 — son señales para `/pm-vitalia` o `/pm-luana` cuando segundo consumer emerja.

## § 8 — Risks

| Risk | Mitigation |
|---|---|
| `router.push("/{tenantId}/{agent}/{subtab}")` → 404 en F1-S7 (route `/[tenantId]/[agent]/[subtab]/page.tsx` aún no existe — F1-S9) | Aceptado per spec § Data flow. Tests Playwright verifican `URL change` (no `page renders`). F1-S9 cubre rutas reales. |
| `usePathname()` retorna `null` en algunos edge cases SSR | `extractAgentFromPath(null)` retorna `null` → ribbon renderiza idle (sin active). SC-4 cubre. |
| Tailwind JIT no purga `bg-agent-{slug}-soft` si `_agent-tw-classes.ts` no se importa | YA importado en F1-S6 por ChatHeader/MessageBubble/etc. RibbonTab importa explícito → garantiza inclusión. |
| Focus management race condition (refs array stale) | `tabRefs.current[idx]` accedido sync en handler — no stale closure. Test Playwright SC-7 verifica Arrow keys. |
| Avatar PNG 404 silent failure | `<AvatarFallback>` Shadcn maneja `onError` automático via Radix Avatar primitive. SC-9 cubre. |
| Tooltip ConfigTab persistente post click (no oculta) | Radix Tooltip cierra naturalmente al click → re-render. SC-3 grader verifica `getTooltip()` no visible post click. Si flaky → fallback explicit `setOpen(false)` en onClick (no expected). |
| F1-S7 toca `agent-catalog.ts` mientras otra story podría tocarlo (parallel safety) | Story checkpoint estado `refined` → `ready` → `developing` secuencial. Single worktree `wip/vitalia` per parallel-safety.md M14 con lock bucket `code`. |

## § 9 — Test surfaces (TDD-mandatory RED-first)

Per `tdd-mandatory.md`, tests primero RED → componentes GREEN.

| Layer | Tests primero (RED) | Componente después (GREEN) |
|---|---|---|
| Unit lib | `src/lib/__tests__/agent-catalog.test.ts` EXTEND (tests para `tabLabel`+`defaultSubtab`+`AGENT_RIBBON_ORDER`+`extractAgentFromPath`) | `agent-catalog.ts` EXTEND |
| Unit molecules | `RibbonTab.test.tsx` + `ConfigTab.test.tsx` | `RibbonTab.tsx` + `ConfigTab.tsx` |
| Unit organism | `Ribbon.test.tsx` | `Ribbon.tsx` |
| Integration | `AppPanelSlot.test.tsx` extend (verify `<Ribbon />` renderiza dentro) | `AppPanelSlot.tsx` MODIFY |
| Arch | `test-ribbon-no-shadcn-tabs.test.ts` NEW + extend `test-no-cross-brand-shell-mirror.test.ts` | n/a (arch tests son self-RED) |
| E2E behavior | 9 specs Playwright (1 per SC funcional) en `e2e/regression/vitalia-fase1-ribbon-6-tabs/` | `Ribbon.tsx` + integration |
| Visual goldens | 11 PNGs en `e2e/__screenshots__/shell/` | iter 1 post Chris ratify side-by-side mockup `ribbon.html` |

## § 10 — Test Construction Plan (★ v4.1 mandatory)

```yaml
playwright_required: true
base_path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/"

creation_order:
  - "T-1: lib/__tests__/agent-catalog.test.ts EXTEND (RED) → lib/agent-catalog.ts EXTEND (GREEN). Foundation: tabLabel + defaultSubtab + AGENT_RIBBON_ORDER + extractAgentFromPath."
  - "T-2: RibbonTab.test.tsx + ConfigTab.test.tsx (RED) → RibbonTab.tsx + ConfigTab.tsx (GREEN). Moléculas low-level (consume T-1 catalog)."
  - "T-3: Ribbon.test.tsx (RED) → Ribbon.tsx (GREEN). Organism root con roving tabindex + URL active extraction. Consume T-2."
  - "T-4: AppPanelSlot.test.tsx extend (RED) → AppPanelSlot.tsx MODIFY (GREEN). Integration: swap skeleton ribbon por <Ribbon />. Arch test test-ribbon-no-shadcn-tabs.test.ts NEW. Extend test-no-cross-brand-shell-mirror.test.ts."
  - "T-5: e2e/regression/vitalia-fase1-ribbon-6-tabs/poms/ribbon-page.pom.ts + fixtures + 9 Playwright spec files (NEW) + 11 visual goldens (--update-snapshots iter 1 post Chris ratify side-by-side mockup ribbon.html). Axe wcag2aa + i18n + a11y keyboard."

scenario_to_test:
  SC-1: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-nav.spec.ts"
  SC-2: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-deeplink.spec.ts"
  SC-3: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-config-nav.spec.ts"
  SC-4: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-invalid-agent.spec.ts"
  SC-5: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-mobile.spec.ts"
  SC-6: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-xss-guard.spec.ts"
  SC-7: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-keyboard.spec.ts"
  SC-8: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-i18n.spec.ts"
  SC-9: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-avatar-fallback.spec.ts"

poms_required:
  - path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/poms/ribbon-page.pom.ts"
    methods:
      - "goto({ tenantId, agent, subtab })"
      - "getTab(slug)"
      - "getConfigTab()"
      - "getTooltip()"
      - "clickTab(slug)"
      - "clickConfigTab()"
      - "pressKey(key)"
      - "getActiveSlug()"
      - "getFocusedTabSlug()"
      - "setViewport(width, height)"
      - "setTheme(theme)"

fixtures_required:
  - path: "vitalia/frontend/e2e/fixtures/shell-theme.fixture.ts"
    action: "REUSE F1-S5/F1-S6 — light/dark toggle helpers via localStorage addInitScript"
  - path: "vitalia/frontend/e2e/fixtures/clerk-auth.fixture.ts"
    action: "REUSE F1-S3 — public route /test-stack/shell-layout bypassa Clerk gate (preferred) o auth.fixture si la página real lo requiere"

visual_goldens:
  base_path: "vitalia/frontend/e2e/__screenshots__/shell/"
  count: 11
  list:
    - "ribbon-active-lisa.png (1280x800 light, active=lisa)"
    - "ribbon-active-lucas.png (1280x800 light, active=lucas)"
    - "ribbon-active-adrian.png (1280x800 light, active=adrian)"
    - "ribbon-active-valeria.png (1280x800 light, active=valeria)"
    - "ribbon-active-camila.png (1280x800 light, active=camila)"
    - "ribbon-active-config.png (1280x800 light, active=config — ConfigTab ring + data-active)"
    - "ribbon-idle.png (1280x800 light, URL agent=foobar inválido → ningún active)"
    - "ribbon-dark.png (1280x800 dark, active=valeria + dark tokens)"
    - "ribbon-mobile-375.png (375x667 light, active=lisa + horizontal scroll)"
    - "ribbon-keyboard-focus.png (1280x800 light, active=lisa keyboard focus en Lucas — ring-2 visible)"
    - "ribbon-hover-inactive.png (1280x800 light, active=lisa mouse hover sobre Lucas — bg-muted)"
  ratchet: shrink_only_post_chris_ratify
  diff_threshold: "maxDiffPixelRatio: 0.001"
```

## § 11 — Acceptance Criteria (verbatim from checkpoint)

| AC | Verificación |
|---|---|
| AC-1 | Ribbon visible top del AppPanel altura 56px (h-14) |
| AC-2 | 5 RibbonTabs renderizados con PNG avatars |
| AC-3 | ConfigTab al final right-aligned (`ml-auto`) con `<Settings />` icon Lucide |
| AC-4 | Tab activa: `bg-agent-{slug}-soft` tint + `font-semibold` (NO border-bottom, NO avatar ring per Batch 2 Q4) |
| AC-5 | Tab inactiva: `text-muted-foreground` · hover `bg-muted` + `text-foreground` |
| AC-6 | Click tab → `router.push('/{tenantId}/{agent}/{defaultSubtab}')` (consume `useParams` + `AGENT_CATALOG[slug].defaultSubtab`) |
| AC-7 | URL change updates active state vía `extractAgentFromPath(usePathname())` derive |
| AC-8 | a11y: `role="tablist"` (nav wrapper) + `role="tab"` per button + `aria-selected={active}` + `aria-label="Configurar"` ConfigTab |
| AC-9 | Visual golden 11 PNGs (6 active states + idle + dark + mobile + keyboard focus + hover inactive) |
| AC-10 | Horizontal scroll en viewport estrecho (`overflow-x-auto` natural) |
| AC-11 | Vitest unit (RibbonTab, ConfigTab, Ribbon, extractAgentFromPath) + Playwright functional (9 specs) |
| AC-12 | Avatar fallback Shadcn `<AvatarFallback>` con initial letter + `bg-agent-{slug}-soft` background |

## § 12 — Architectural fitness impact

Allowlists shrink-only:

- `test_server_first.test.ts` — extend allowlist con NEW client components (Ribbon, RibbonTab, ConfigTab) — justificado `useRouter`/`usePathname`/`useParams`/`useRef`/`useState`. Commit body justifica.
- `test-no-cross-brand-shell-mirror.test.ts` — extend names allowlist con `Ribbon`, `RibbonTab`, `ConfigTab`, `extractAgentFromPath`, `AGENT_RIBBON_ORDER`. Verifica 0 matches en `nicolify/comunify/lupulo/frontend/src`.
- `test-agent-catalog-ssot.test.ts` — `agent-catalog.ts` ya en `KNOWN_HARDCODES` allowlist. EXTEND no agrega hex nuevos. NO change needed allowlist.
- `test-vitalia-ui-strings-no-voseo.test.ts` — extend regex glossary check verifica nuevos strings (`Mi Clínica`, `Atraer`, `Vender`, `Operar`, `Mantener`, `Configurar`, `Agentes`, role names) sin voseo.
- `test-ribbon-no-shadcn-tabs.test.ts` — NEW arch test. Allowlist N/A (forbidden import check).

## § 13 — capability YAML + modules/{m}.md Updates Required (post 2026-05 paradigma)

Post-merge auto via `/pm-vitalia` Phase E DOCS:

- **NEW** `vitalia/docs/product/capabilities/shell-organism/ribbon.yaml` (status: live, story_introduced: vitalia-fase1-ribbon-6-tabs)
- **MODIFY** `vitalia/docs/product/capabilities/shell-organism/layout-5050.yaml` (mention F1-S7 swap skeleton → real Ribbon)
- **AUTO-REGEN** `vitalia/docs/product/modules/shell-organism.md` via `scripts/reconcile_capabilities.py --brand vitalia` (R3 — gitignored ok; list block tracked)

## § 14 — Cross-cutting concerns

- **Tenant isolation:** N/A queries; `useParams.tenantId` propaga via URL routing (no hardcode).
- **Currency / master data:** N/A (no monetary, no datetime UI).
- **Spanish neutro LatAm:** Microcopy verbatim Batch 4 spec § Microcopy. Cero voseo. Tildes correctas (Adrián, Clínica). Glossary `test-vitalia-ui-strings-no-voseo.test.ts` extend.
- **PII:** ZERO PHI. `hipaa-lite.md` scope `not_applicable`.
- **Native-first dev:** Tests Vitest + Playwright corren native Linux (NUNCA docker exec). Port 3002 vitalia.

## § 15 — Research Notes (DATE-AWARE)

- **WAI-ARIA Tablist pattern (roving tabindex)**: https://www.w3.org/WAI/ARIA/apg/patterns/tabs/ · accessed 2026-05-25. Pattern oficial: solo focused tab tiene `tabIndex=0`, los demás `tabIndex=-1`. Arrow keys mueven focus + opcional auto-activate. Enter/Space activan. Decisión F1-S7: NO auto-activate on focus (focus ≠ activate — user must Enter/Space para `router.push`). Justificación: route-based nav implica navegación side-effect que no debería disparar por mover focus.
- **Next.js 16 App Router**: https://nextjs.org/docs/app/api-reference/functions/use-pathname · accessed 2026-05-25. `usePathname()` retorna string actual; Client Component only. `useRouter()` retorna router con `push(href)`. `useParams<T>()` retorna params typed.
- **Shadcn UI Avatar**: https://ui.shadcn.com/docs/components/avatar · accessed 2026-05-25. Radix Avatar primitive maneja `onError` automático via `AvatarImage` → `AvatarFallback` swap. NO necesita `useState [imgError]` manual.
- **Shadcn UI Tooltip**: https://ui.shadcn.com/docs/components/tooltip · accessed 2026-05-25. `TooltipTrigger asChild` envuelve element custom. `TooltipContent side="bottom"` positioning. Default `delayDuration=0` aceptado para "Configurar" hint inmediato.
- **Tailwind v4 JIT purge safety**: https://tailwindcss.com/docs/content-configuration · accessed 2026-05-25. Dynamic class names via template strings (`bg-agent-${slug}`) NO purge-safe. Solución: switch/map explícito (heredado F1-S6 `_agent-tw-classes.ts::agentBgSoftClass`).
- **Knowledge cutoff disclosure**: Opus 4.7 cutoff Jan 2026. Para WAI-ARIA Tablist pattern (W3C standard estable desde 2020+) + Next.js 16 (released late 2025 per ecosystem) + Shadcn UI (versiones cementadas F1-S0) — patterns válidos sin cambios disruptivos verificados live 2026-05-25.

## § 16 — Open Questions for PM

Ninguna. Spec § Open questions documenta 12 Q resueltas en batches 1-4 con Chris. No hay ambigüedad pendiente para builder.

