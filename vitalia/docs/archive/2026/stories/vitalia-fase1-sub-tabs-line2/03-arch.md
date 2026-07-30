<!-- voseo-allowed: glosario reference + internal architecture documentation -->

---
story_id: vitalia-fase1-sub-tabs-line2
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-25
architect_iter: 1
architect_run_on: 2026-05-25
surfaces: FE_ONLY
predecessors_done:
  - vitalia-fase1-shell-layout-5050     # F1-S4 — AppPanelSlot grid + skeleton pattern
  - vitalia-fase1-valeria-chat-skeleton # F1-S6 — agent-catalog SSoT origin
  - vitalia-fase1-ribbon-6-tabs         # F1-S7 — Ribbon + RibbonTab + ConfigTab + agent-catalog EXTEND pattern
---

# F1-S8 · vitalia-fase1-sub-tabs-line2 · 03-arch.md (consolidado FE)

## § 0 — Context Summary

- **Story:** `vitalia-fase1-sub-tabs-line2` · outcome `vitalia-mvp-ui-foundation` · phase `fase-1`.
- **PR folder:** `vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/`
- **Architect run on:** 2026-05-25 (Step 0 `date -u +%Y-%m-%d` = 2026-05-25, `date -u +%Y-%m` = 2026-05). Opus 4.7 knowledge cutoff Jan 2026; library currency (Next.js 16 App Router + React 19 + Shadcn primitives reused + Tailwind v4) verified live via canonical docs on 2026-05-25 — versiones cementadas F1-S0/F1-S4/F1-S6/F1-S7 sin upgrade.
- **Modules touched:** `shell-organism` (brand-local Vitalia frontend chrome — capability `vitalia.shell-organism.sub-tabs` NEW).
- **Surfaces:** FE_ONLY · ZERO BE · ZERO AGENTIC · ZERO engine touch. NO fetch, NO API, NO LLM, NO PHI (HIPAA-lite NOT applicable — UI nav puro sin patient data). Mirror estructural F1-S7 pero línea 2 dinámica per agente activo.

### Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` (MODIFY EXTEND — SubTabMeta + RIBBON_SUBTABS + extractSubtabFromPath) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/{SubTabsBar,SubTab}.tsx` (NEW organism + molécula) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` (MODIFY: reemplaza sub-tabs skeleton placeholder por `<SubTabsBar />` real) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` (MODIFY shrink-only extend NEW names) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts` (MODIFY allowlist extend NEW client components) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts` (MODIFY glossary check NEW microcopy) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/**` (NEW Playwright suite + POM + 9 specs + visual-goldens) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-*.png` (×13 visual goldens NEW) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |

ZERO BE surface. ZERO AGENTIC surface. ZERO engine touch. R23 NO aplica (zero agentic, all FE production_code; T-5 tests/POM/fixtures production_code=false but still sonnet/opencode eligible).

### Skills consulted (decisions ratified verbatim)

- **`frontend-expert`** — FSD-Lite: `components/shared/shell-organism/` correct para chrome cross-feature; `lib/agent-catalog.ts` EXTEND in-place (anti-duplication HARD per checkpoint Q1 — NO crear `lib/agents/subtabs.ts` paralelo); Server-First default + `'use client'` solo en hojas con hooks/event handlers (`SubTabsBar.tsx` consume `usePathname` + `useRouter` + `useParams` + `useState` + `useRef`). Tests colocated `__tests__/` siblings. Runtime quality checklist: useEffect deps complete, no stale closures (handleKeyDown lee refs/state vía closure react-19-safe), hydration safety (pathname disponible via hook desde primer render Client).
- **`tessl__react-patterns`** — React 19 + Next.js 16 App Router: `'use client'` necesario en `SubTabsBar.tsx` (hooks `usePathname`/`useRouter`/`useParams` + `useRef` para roving tabindex DOM access + `onKeyDown` handler). `SubTab.tsx` también Client (recibe event handler props + onClick + onFocus + forwardRef). Roving tabindex pattern verbatim de F1-S7 Ribbon: índice `focusedIdx` en parent, refs array `tabRefs.current[]` para focus management imperativo via `tabRefs.current[idx]?.focus()` en handler. Sin `useEffect` para focus inicial — focus mueve en respuesta a keyDown sync.
- **`tessl__shadcn-ui`** — NO se requiere Shadcn primitive nuevo. `SubTab` es `<button>` raw con `cn()` classes propias (paridad F1-S7 RibbonTab). NO usar Shadcn `<Tabs>` Radix-based (su API asume `<TabsContent>` inline incompatible con Next.js route-based nav — patrón heredado F1-S7 `test-ribbon-no-shadcn-tabs.test.ts` cubre Ribbon archivo; este story NO modifica esa lista pero acoge la misma decisión de patrón route-based).
- **`tessl__tailwind`** — Semantic tokens ONLY (DC §5.1): `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `ring-ring`, `bg-agent-{slug}-soft`, `text-agent-{slug}`. Las 5 classes `bg-agent-{slug}-soft` ya están definidas en `globals.css` (F1-S1) y reuse via `agentBgSoftClass(slug)` switch en `_agent-tw-classes.ts`. Las 5 classes `text-agent-{slug}` ya existen por F1-S6/F1-S1. Para SubTab necesitamos NEW helper `agentTextClassSubTab(slug)` (NO confundir con `agentTextClass` existente — el sub-tab usa text-agent-lisa/adrian/valeria/camila salvo Lucas que usa `text-foreground` excepción cementada en spec). NO hex literales. NO arbitrary values.
- **`tessl__vitest`** — Colocated `Component.test.tsx`. RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `next/navigation` via `vi.mock('next/navigation', () => ({ usePathname: vi.fn(), useRouter: vi.fn(), useParams: vi.fn() }))`. Cobertura unit: `SubTabsBar.test.tsx` (render N sub-tabs per agent + roving tabindex keyboard + active detection + null agent return null + invalid subtab no-active), `SubTab.test.tsx` (estados inactive/active per color/Lucas exception/Config exception), `agent-catalog.test.ts` EXTEND (SubTabMeta shape + RIBBON_SUBTABS 22 sub-tabs distribution + extractSubtabFromPath).
- **`playwright-expert`** — Path canon NEW `e2e/regression/vitalia-fase1-sub-tabs-line2/` (consistente con F1-S7 `e2e/regression/vitalia-fase1-ribbon-6-tabs/` y screenshots `e2e/__screenshots__/shell/`). POM `SubTabsBarPage` con métodos `goto({tenantId, agent, subtab})`, `getSubTabsBar`, `getSubTab(id)`, `clickSubTab(id)`, `pressKey(key)`, `getActiveSubtab()`, `getFocusedSubtabId()`, `getSubTabAriaSelected(id)`, `setViewport()`, `setTheme()`. Fixtures REUSE `shell-theme.fixture.ts` (REUSE F1-S5/F1-S6/F1-S7). Visual goldens iter 1: `--update-snapshots --project=visual` post Chris ratify side-by-side mockup `sub-tabs.html`. Axe ruleset `wcag2aa`. Port 3002 vitalia. Native Linux (NO docker).
- **`tessl__nextjs-app-router-modularization`** — `'use client'` boundaries: `SubTabsBar.tsx` root Client por hooks (`usePathname` + `useRouter` + `useParams`); sub-componente `SubTab.tsx` también Client (forwardRef + handlers). NO crear nuevas routes — `SubTabsBar.tsx` consume URL existente via `usePathname()` y dispara `router.push()` a paths que F1-S9 (routing-shell) implementará. En F1-S8 el `router.push` puede 404 (target route `/[tenantId]/[agent]/[subtab]/page.tsx` aún no existe consistente full) — gherkin spec asume comportamiento de redirect (browser navega, eventual 404 post-F1-S9 cubierto).
- **`backend-expert` / `copilot-expert` / `sales-agent-expert` / `offer-expert` / `brand-expert` / `metrics-expert` / `offer-type-preset-expert`** — NO cargar. Story es FE only chrome UI nav puro sin BE/agentic/dominio negocio (HIPAA-lite scope: `not_applicable`, ZERO PHI).

### CONTEXT-BRIEF source

Self-ran greps Path B + Read directos (CONTEXT-BRIEF.md absent — story-by-story sin Haiku context-builder). Lectura prioritaria ejecutada:

- `vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/{checkpoint.md,01-spec.md,mockups/sub-tabs.html}`
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md`
- `vitalia/docs/archive/2026/stories/vitalia-fase1-ribbon-6-tabs/{03-arch.md,04-validators.yaml,05-guidelines.md,06-tickets.yaml}` (predecesor pattern — Ribbon estructura idéntica replicable a SubTabsBar)
- `vitalia/docs/product/capabilities/shell-organism/ribbon.yaml` (predecesor capability SSoT — modelo para sub-tabs.yaml)
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 3.2 (SubTab/SubTabsBar molécula/organismo cementados) + § 7.2 (AGENT_SUBTABS whitelist exact shape) + § 7.3 (catalog metadata)
- `vitalia/frontend/src/lib/agent-catalog.ts` (EXTEND target — shape actual + AgentSlug + RibbonTabSlug + AGENT_RIBBON_ORDER + extractAgentFromPath ya existen F1-S7)
- `vitalia/frontend/src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab,AppPanelSlot,_agent-tw-classes}.tsx,ts` (patrón estructural a replicar)
- `vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/{poms/ribbon-page.pom.ts,ribbon-keyboard.spec.ts}` (POM + spec patterns a replicar)
- Vitalia overlay rules: `vitalia/.claude/rules/{hipaa-lite,shell-mockup-per-component}.md`
- Cardinal rules: `frontend-fsd.md`, `spanish-text.md`, `tdd-mandatory.md`, `tenant-isolation.md`, `anti-duplication.md`.

### capability YAML files affected (post-merge updates required, paradigma post 2026-05)

- **NEW** `vitalia/docs/product/capabilities/shell-organism/sub-tabs.yaml` — capability nueva F1-S8 (`vitalia.shell-organism.sub-tabs`, status `live` post-merge; descripción: barra horizontal LÍNEA 2 dinámica per agente activo + 22 sub-tabs total distribuidos 4·5·4·2·4·3 + WAI-ARIA tablist roving tabindex + null agent collapse total + Lucas/Config color exceptions).
- **MODIFY** `vitalia/docs/product/capabilities/shell-organism/ribbon.yaml` — agregar mención `AppPanelSlot sub-tabs placeholder reemplazado por <SubTabsBar /> real (F1-S8)` en sección downstream-unblocked.
- **AUTO-REGEN** `vitalia/docs/product/modules/shell-organism.md` — auto-list block via `scripts/reconcile_capabilities.py --brand vitalia` (R3 gitignored ok — list block es tracked).

### Architecture gates that must keep passing (extend, no break)

- `test_fsd_boundaries.test.ts` — shell-organism NO importa features/*; `lib/agent-catalog.ts` consumido cross-shell sin violar FSD.
- `test-no-cross-brand-shell-mirror.test.ts` — extend con nombres NEW (`SubTabsBar`, `SubTab`, `RIBBON_SUBTABS`, `extractSubtabFromPath`, `SubTabMeta`).
- `test-shell-store-schema-readonly-f1-s5.test.ts` — invariant heredado F1-S5 (shell-store NO modificado, F1-S8 no toca store).
- `test-agent-catalog-ssot.test.ts` — extiende cobertura ya existente (agent-catalog.ts EXTEND; F1-S8 EXTEND no introduce hex/thumbnail nuevos, solo añade `RIBBON_SUBTABS` const + `SubTabMeta` interface + `extractSubtabFromPath` helper).
- `test_no_hardcoded_colors.test.ts` — tokens semánticos ONLY; F1-S8 consume `bg-agent-{slug}-soft` + `text-agent-{slug}` via helpers switch.
- `test_no_voseo_in_copy.test.ts` + `test-vitalia-ui-strings-no-voseo.test.ts` — microcopy verbatim 22 sub-tab labels + 6 nav aria-labels (`Sub-secciones {AgentName}`) = 28 strings totales.
- `test_server_first.test.ts` — `'use client'` allowlist shrink-only extend (SubTabsBar + SubTab justificadamente client).
- `test-no-vt-classes-in-new-features.test.ts` — NO `.vt-*` legacy utility classes en NEW code.
- `test-skip-link-target.test.ts` — `<main id="main-content">` NO afectado (out-of-scope).
- `test-ribbon-no-shadcn-tabs.test.ts` — invariant heredado F1-S7 (Ribbon/RibbonTab/ConfigTab NO importan @/components/ui/tabs). F1-S8 NO modifica esa lista pero acoge mismo pattern (SubTabsBar NO importa @/components/ui/tabs — implícito en code review + voluntary acoplamiento de la decisión).

## § 0.1 — Existing Systems Audit (NO NEW LAYER rule)

### Source of evidence

- [x] Self-run greps (Path B — context-builder fallback; CONTEXT-BRIEF.md absent for this story)

### Audit cross-module ejecutado

```bash
WS=/home/chalreme/Proyectos/luana-vitalia

# 1. Cross-brand mirror scan (anti-duplication.md cardinal rule)
for b in nicolify comunify lupulo; do
  for name in SubTab SubTabsBar RIBBON_SUBTABS extractSubtabFromPath SubTabMeta; do
    matches=$(grep -rln "$name" $WS/$b/frontend/src 2>/dev/null | grep -v node_modules | wc -l)
    if [ "$matches" -gt 0 ]; then echo "$b::$name → $matches matches"; fi
  done
done
# Result: 0 matches en las 3 brands. ✅ No mirror existente.

# 2. Engine TS packages (core/@luana/*)
find $WS/core -name "SubTab*" -o -name "subtab*" 2>/dev/null | head
# Result: 0 matches. Engine TS packages no exponen shell sub-tabs abstraction. ✅

# 3. Same-brand existing duplicates (vitalia/frontend/src)
find $WS/vitalia/frontend/src -name "SubTab*" 2>/dev/null
# Result: 0 matches NEW names. ✅

# 4. Catalog SSoT path verification (anti-duplication HARD per checkpoint Q1)
ls $WS/vitalia/frontend/src/lib/agent-catalog.ts $WS/vitalia/frontend/src/lib/agents/subtabs.ts 2>/dev/null
# Result: agent-catalog.ts existe (F1-S6 + F1-S7), lib/agents/subtabs.ts NO existe. ✅ EXTEND in-place

# 5. Tailwind text-agent-{slug} already defined?
grep -E "text-agent-(lisa|lucas|adrian|valeria|camila)" $WS/vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts
# Result: 5 matches en agentTextClass(). ✅ Reuse posible — pero ojo: agentTextClass es FULL saturation, SubTab necesita variante con Lucas exception → NEW helper agentTextClassSubTab(slug)

# 6. AppPanelSlot current shape (target MODIFY)
grep -E "F1-S8|SubTabs|sub-tabs placeholder" $WS/vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx
# Result: sub-tabs skeleton placeholder explícitamente labeled "F1-S8 will replace". ✅ MODIFY swap clean (líneas 45-54).

# 7. Shadcn Tabs Radix usage scan (anti-pattern check — voluntario en SubTabsBar)
grep -rln "@/components/ui/tabs\|<Tabs " $WS/vitalia/frontend/src/components 2>/dev/null
# Result: 0 matches — Shadcn Tabs primitive instalado pero no consumido. ✅

# 8. Pre-existing AGENT_SUBTABS spec ref check (SHELL-DESIGN-CONTRACT § 7.2)
grep -n "AGENT_SUBTABS\|RIBBON_SUBTABS" $WS/vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
# Result: line 432 cita AGENT_SUBTABS como Record<AgentKey, readonly string[]>. F1-S8 cement uses RIBBON_SUBTABS (rename pattern paridad AGENT_RIBBON_ORDER F1-S7) con shape Record<RibbonTabSlug, readonly SubTabMeta[]> (richer — incluye icon + label además de id).
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `agent-catalog.ts` SSoT (post-F1-S7) | `vitalia/frontend/src/lib/agent-catalog.ts` | active F1-S6 + F1-S7 done | **EXTEND in-place** — agregar `SubTabMeta` interface + `RIBBON_SUBTABS: Record<RibbonTabSlug, readonly SubTabMeta[]>` constante (22 sub-tabs distribuidos 4·5·4·2·4·3) + helper `extractSubtabFromPath`. NO crear `lib/agents/subtabs.ts` separado (checkpoint Q1 cement — anti-duplication HARD F1-S7 paridad). |
| `_agent-tw-classes.ts` Tailwind helpers | `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` | active F1-S6 done | **EXTEND in-place** — agregar `agentTextClassSubTab(slug)` switch helper con Lucas exception (return `text-foreground` para lucas, `text-agent-{slug}` para los otros 4). NO confundir con `agentTextClass` existente (Lucas devuelve `text-agent-lucas` saturated — incorrecto para sub-tab donde lucas color es near-black y daña legibilidad). Justificado: helper específico para uso sub-tab + ratchet shrink-only. |
| `AppPanelSlot.tsx` skeleton sub-tabs placeholder | `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | active F1-S4 + F1-S7 done | **MODIFY** — reemplazar sub-tabs skeleton placeholder (líneas 45-54 actual con 4 bars `<div className="h-2 w-..."`) por `<SubTabsBar />` real. Content skeleton **PRESERVAR** (F1-S10 reemplazará). Slot label "AppPanelSlot · F1-S8 / S10" actualizar a "AppPanelSlot · F1-S10" (S8 listo). |
| `Ribbon` + `RibbonTab` + `ConfigTab` + roving tabindex pattern | `vitalia/frontend/src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab}.tsx` | active F1-S7 done | **REFERENCE / REUSE pattern** — `SubTabsBar.tsx` replica VERBATIM la estructura roving tabindex de `Ribbon.tsx` (focusedIdx + tabRefs + handleKeyDown). `SubTab.tsx` replica VERBATIM la estructura `forwardRef + data-testid + data-active + role="tab" + aria-selected + className conditional cn() pattern` de `RibbonTab.tsx` (sin Avatar — solo emoji + label). NO se modifica F1-S7. |
| `SubTabsBar`, `SubTab`, `RIBBON_SUBTABS`, `extractSubtabFromPath`, `SubTabMeta` | n/a | does-not-exist | **NEW** (justificado — brand-local shell pattern Vitalia F1-S8 fresco, zero matches cross-brand, no engine core overlap, no Shadcn primitive equivalente per anti-pattern bloqueado en spec). |
| Test path canon `e2e/regression/{story-id}/` | n/a | active F1-S6 inauguró + F1-S7 reusó `e2e/regression/{story-id}/` | **NEW path** `e2e/regression/vitalia-fase1-sub-tabs-line2/` — heredado del checkpoint/spec que cita ese path; consistente con `e2e/__screenshots__/shell/` para visual goldens. |

### Decisión por sistema

- **`agent-catalog.ts`**: EXTEND in-place (anti-duplication HARD per checkpoint Q1 + paridad F1-S7). Cero archivos nuevos en `lib/agents/`.
- **`_agent-tw-classes.ts`**: EXTEND in-place — agregar `agentTextClassSubTab(slug)` con Lucas exception. Helper específico a uso sub-tab (text color en active state) — NO sobreescribir `agentTextClass` existente que tiene semántica distinta (TypingIndicator/DelegateMarker).
- **`AppPanelSlot.tsx`**: MODIFY (swap skeleton sub-tabs placeholder por componente real, preserve resto skeleton + label `F1-S10`).
- **`SubTabsBar`, `SubTab`**: NEW justified — patrón brand-local F1-S8 fresco, no Shadcn equivalente, no cross-brand mirror, replica estructura F1-S7 (zero refactor riesgo).
- **`extractSubtabFromPath`**: NEW utility puro co-located en `lib/agent-catalog.ts` (decisión: NO crear `lib/agents/routing.ts` separado — la función pertenece semánticamente al catalog porque consume `RibbonTabSlug` enum + retorna `string | null`; paridad con `extractAgentFromPath` F1-S7 co-located misma file).
- **`SubTabMeta` interface**: NEW co-located en `lib/agent-catalog.ts` (paridad estructural — `AgentDescriptor` ya vive ahí).

**Cross-brand lift evaluation:** patrón SubTabsBar es brand-local Vitalia (consume Vitalia agent catalog + 22 sub-tabs verticales healthcare). Per `.claude/rules/anti-duplication.md`, lift se dispara on second occurrence. F1-S8 es primera ocurrencia → NEW correct.

**LIFT_CANDIDATE notes (futuras stories):**

- Si nicolify/comunify/lupulo/futuros adoptan patrón multi-agente ribbon + sub-tabs similar → lift candidate a `core/luana-core-ui-shell/` futuro (promotion proposal `/pm-luana`) junto al Ribbon F1-S7 (mismo lift conceptual). Hoy NO existe paralelismo cross-brand.
- `extractSubtabFromPath` co-located en `agent-catalog.ts` por simplicidad SSoT. Si en F1-S9 (routing-shell) emerge necesidad de helpers de routing más amplios (e.g., `buildAgentPath`, `buildSubtabPath`), considerar separar `lib/agents/routing.ts` en esa story (no en F1-S8).

## § 1 — Surfaces involved (verbatim)

| Surface | Aplica | Owner |
|---|---|---|
| BE (FastAPI Python) | NO | — |
| AGENTIC (LangGraph / deepagents / sales_agent) | NO | — |
| FE (Next.js 16 App Router + Shadcn + Tailwind + roving tabindex pattern verbatim F1-S7) | **SÍ** | `builder-frontend` Sonnet/opencode |


## § 2 — FE Architecture Detail

### § 2.1 — `agent-catalog.ts` EXTEND (anti-duplication HARD F1-S7 paridad)

`vitalia/frontend/src/lib/agent-catalog.ts` — **MODIFY** existente. Agregar `SubTabMeta` interface + `RIBBON_SUBTABS` constante + `extractSubtabFromPath` helper.

```ts
// EXISTING (preserve verbatim — NO modificar):
// - AgentSlug enum
// - AgentDescriptor interface
// - AGENT_CATALOG dict
// - DEFAULT_CHAT_AGENT
// - AGENT_SLUGS array
// - AGENT_RIBBON_ORDER tuple (F1-S7)
// - RibbonTabSlug union type (F1-S7)
// - extractAgentFromPath helper (F1-S7)

// ★ NEW F1-S8 — appended after F1-S7 block:

/**
 * Sub-tab descriptor — single sub-tab entry inside RIBBON_SUBTABS[slug].
 * 22 sub-tabs total distribuidos: lisa 4 · lucas 5 · adrian 4 · valeria 2 · camila 4 · config 3.
 * spec_anchor: 03-arch.md § 2.1 + 01-spec.md § Catalog SSoT § 1
 */
export interface SubTabMeta {
  /** URL segment identifier — slug kebab-case (e.g., "marca", "doctores", "envuelo"). */
  id: string;
  /** Visible label Spanish neutro LatAm — sin voseo (e.g., "Marca", "En vuelo", "Voz del paciente"). */
  label: string;
  /** Emoji icon (paridad ribbon catalog Q2 cement — emojis no lucide). */
  icon: string;
}

/**
 * Sub-tabs per ribbon tab — 22 sub-tabs distribuidos 4·5·4·2·4·3.
 * Counts: Lisa 4 · Lucas 5 · Adrián 4 · Valeria 2 · Camila 4 · Config 3.
 * Mateo EXCLUDED (transversal — not in AGENT_RIBBON_ORDER F1-S7).
 *
 * spec_anchor: 01-spec.md § 1 + 03-arch.md § 2.1 + SHELL-DESIGN-CONTRACT.md § 7.2
 */
export const RIBBON_SUBTABS: Record<RibbonTabSlug, readonly SubTabMeta[]> = {
  lisa: [
    { id: "marca",      label: "Marca",      icon: "🏥" },
    { id: "doctores",   label: "Doctores",   icon: "👨‍⚕️" },
    { id: "servicios",  label: "Servicios",  icon: "🩺" },
    { id: "compliance", label: "Compliance", icon: "🛡️" },
  ],
  lucas: [
    { id: "lanzar",     label: "Lanzar",     icon: "🚀" },
    { id: "envuelo",    label: "En vuelo",   icon: "📡" },
    { id: "recursos",   label: "Recursos",   icon: "📚" },
    { id: "resultados", label: "Resultados", icon: "📈" },
    { id: "mercado",    label: "Mercado",    icon: "🌍" },
  ],
  adrian: [
    { id: "inbox",      label: "Inbox",      icon: "💬" },
    { id: "embudo",     label: "Embudo",     icon: "🎯" },
    { id: "outbound",   label: "Outbound",   icon: "📣" },
    { id: "propuestas", label: "Propuestas", icon: "💼" },
  ],
  valeria: [
    { id: "agenda",    label: "Agenda",    icon: "📆" },
    { id: "pacientes", label: "Pacientes", icon: "👥" },
  ],
  camila: [
    { id: "voz",         label: "Voz del paciente", icon: "🎤" },
    { id: "reactivar",   label: "Reactivar",        icon: "🪃" },
    { id: "multiplicar", label: "Multiplicar",      icon: "🤝" },
    { id: "reputacion",  label: "Reputación",       icon: "📊" },
  ],
  config: [
    { id: "cuenta",     label: "Mi cuenta",  icon: "🏢" },
    { id: "conexiones", label: "Conexiones", icon: "🔌" },
    { id: "avanzado",   label: "Avanzado",   icon: "🔬" },
  ],
} as const satisfies Record<RibbonTabSlug, readonly SubTabMeta[]>;

/**
 * Extrae el segmento [subtab] del pathname.
 *
 * Pattern URL: /{tenantId}/{agent}/{subtab}/... → retorna {subtab} si segmento presente,
 * null si pathname incompleto o vacío.
 *
 * Defense-in-depth: NO valida que el subtab pertenezca a RIBBON_SUBTABS[agent] —
 * el consumidor (SubTabsBar) hace ese check via .find() y dispone defensive null si
 * el segmento no matchea (SC-5 "invalid subtab → no active"). XSS safe por React
 * JSX auto-escape on render (segmento se compara como string contra ids estáticos).
 *
 * Examples:
 *   /tenant-x/lisa/marca       → "marca"
 *   /tenant-x/camila/reactivar → "reactivar"
 *   /tenant-x/config/cuenta    → "cuenta"
 *   /tenant-x/lisa             → null (insufficient segments)
 *   /tenant-x                  → null
 *   /                          → null
 *   /<script>alert(1)</script> → null (insufficient segments — 1 segment after split filter Boolean)
 *
 * spec_anchor: 01-spec.md § 5 + § Gherkin SC-3/SC-5/SC-7 + 03-arch.md § 2.1
 */
export function extractSubtabFromPath(
  pathname: string | null | undefined,
): string | null {
  if (!pathname) return null;
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length < 3) return null;
  return segments[2] ?? null;
}
```

**Decisiones cementadas:**

- **D1 — Mateo EXCLUDED from `RIBBON_SUBTABS`:** mateo es transversal, no aparece en `AGENT_RIBBON_ORDER` F1-S7. `RIBBON_SUBTABS` es `Record<RibbonTabSlug, ...>` (NO `Record<AgentSlug, ...>`) — RibbonTabSlug excluye mateo por construcción. TypeScript exhaustiveness check garantiza.
- **D2 — Config INCLUDED:** `RibbonTabSlug = AgentSlug | "config"` (F1-S7). Config 3 sub-tabs entries: cuenta · conexiones · avanzado. Spanish neutro LatAm verbatim.
- **D3 — `SubTabMeta.icon` emoji string:** checkpoint Q2 cement — paridad con `AGENT_RIBBON_ORDER` thumbnail-or-initial pattern. NO lucide-react import (zero refactor + emoji nativo).
- **D4 — `extractSubtabFromPath` returns raw segment (no validation):** defensive null only if segments insufficient. Validation contra `RIBBON_SUBTABS[agent]` ids vive en consumidor `SubTabsBar` via `.find()`. Razón: helper puro tipo `string | null`, no asume context. XSS safe vía React JSX render text-content (segments[2] como `<script>...` produce data-testid raw pero React escapa).
- **D5 — `as const satisfies` modern TS pattern:** garantiza `readonly` tuples + type inference + key exhaustiveness. Paridad con `AGENT_RIBBON_ORDER` F1-S7 (`as const satisfies readonly AgentSlug[]`).
- **D6 — Icons emoji unicode (no SVG component):** strings literales con grapheme cluster válido. NO `<EmojiIcon name="..."/>` wrapper. Tests RTL match con `getByText('🏥')` o `getByText(/Marca/)` (text-content includes icon adjacent al label).

### § 2.2 — `SubTabsBar.tsx` organism (NEW)

`vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx` — NEW.

**Client Component justification:**
- Consume `usePathname()` + `useRouter()` + `useParams()` de `next/navigation` (Client-only hooks).
- Implementa roving tabindex con `useRef<(HTMLButtonElement | null)[]>` + state `focusedIdx` (Client state).
- Event handler `onKeyDown` para WAI-ARIA tablist keyboard support.
- Replica VERBATIM la estructura roving tabindex de `Ribbon.tsx` F1-S7 (zero divergencia patrón).

**Shape:**

```tsx
"use client";

import { useState, useRef, useCallback, type KeyboardEvent } from "react";
import { usePathname, useRouter, useParams } from "next/navigation";
import {
  AGENT_CATALOG,
  RIBBON_SUBTABS,
  extractAgentFromPath,
  extractSubtabFromPath,
  type RibbonTabSlug,
  type AgentSlug,
} from "@/lib/agent-catalog";
import { SubTab } from "./SubTab";

/**
 * SubTabsBar — Vitalia shell organismo línea 2 (F1-S8).
 *
 * Barra horizontal debajo del Ribbon (h-[42px] min) con N sub-tabs dinámicos
 * derivados del agente activo en URL via extractAgentFromPath(usePathname()).
 * Distribución: lisa 4 · lucas 5 · adrian 4 · valeria 2 · camila 4 · config 3.
 *
 * Active sub-tab derivado de URL via extractSubtabFromPath(pathname). Si el
 * segmento NO matchea ningún sub-tab id del agente → ningún active (SC-5).
 * Si no hay activeAgent (null) → return null total (SC-4 cement Q5 — gap colapsa).
 *
 * Click navega a /{tenantId}/{agent}/{subtab}. WAI-ARIA tablist completo con
 * roving tabindex (Arrow Left/Right + Home + End + Enter + Space + wrap-around).
 *
 * Paridad estructural con Ribbon F1-S7 — mismo patrón roving tabindex (focusedIdx
 * state + tabRefs array + handleKeyDown switch + modulo wrap-around). Diferencias:
 *   - Cantidad de tabs variable (2..5) por agente, no fijo 6 como Ribbon
 *   - No ConfigTab "extra" — todos los tabs son SubTab uniform
 *   - return null cuando no hay activeAgent (Ribbon nunca return null — siempre 6 tabs)
 *
 * spec_anchor: 01-spec.md § Gherkin SC-1..SC-9 + § Wireframe + § Accessibility
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */
export function SubTabsBar() {
  const pathname = usePathname();
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();

  // URL-derived active state — single source of truth
  const activeAgent: RibbonTabSlug | null = extractAgentFromPath(pathname);
  const activeSubtab: string | null = extractSubtabFromPath(pathname);

  // Sub-tabs available for active agent (empty array if activeAgent null)
  const subtabs = activeAgent !== null ? RIBBON_SUBTABS[activeAgent] : [];

  // Initial focus follows the active subtab if matches, else 0
  const initialFocusIdx = (() => {
    if (activeSubtab === null || subtabs.length === 0) return 0;
    const idx = subtabs.findIndex((st) => st.id === activeSubtab);
    return idx >= 0 ? idx : 0;
  })();

  const [focusedIdx, setFocusedIdx] = useState<number>(initialFocusIdx);

  // tabRefs[0..subtabs.length-1] = sub-tab buttons
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const totalTabs = subtabs.length;

  // Navigate to a subtab — guards null tenantId / activeAgent
  const navigateTo = useCallback(
    (subtabId: string) => {
      const tenantId = params?.tenantId;
      if (!tenantId || activeAgent === null) return;
      router.push(`/${tenantId}/${activeAgent}/${subtabId}`);
    },
    [params, router, activeAgent],
  );

  // Move focus to idx (circular modulo-safe wrap)
  const focusTab = useCallback(
    (idx: number) => {
      if (totalTabs === 0) return;
      const safeIdx = ((idx % totalTabs) + totalTabs) % totalTabs;
      setFocusedIdx(safeIdx);
      tabRefs.current[safeIdx]?.focus();
    },
    [totalTabs],
  );

  // Keyboard handler on <nav> — events bubble up from child buttons
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLElement>) => {
      if (totalTabs === 0) return;
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
          const subtab = subtabs[focusedIdx];
          if (subtab) navigateTo(subtab.id);
          return;
        }
        default:
          break;
      }
    },
    [focusedIdx, focusTab, navigateTo, totalTabs, subtabs],
  );

  // Q5 cement (checkpoint) — return null total cuando no hay activeAgent o no hay sub-tabs.
  // Grid AppPanel colapsa fila naturalmente (3 filas → 2 filas).
  if (activeAgent === null || subtabs.length === 0) {
    return null;
  }

  // Agent name para aria-label — Capitalize "Configuración" para config, "Lisa", "Lucas", etc.
  const ariaAgentName =
    activeAgent === "config"
      ? "Configuración"
      : (AGENT_CATALOG[activeAgent as AgentSlug].name ?? activeAgent);

  return (
    <nav
      role="tablist"
      aria-label={`Sub-secciones ${ariaAgentName}`}
      data-testid="sub-tabs-bar"
      onKeyDown={handleKeyDown}
      className="flex min-h-[42px] items-center gap-1 overflow-x-auto border-b border-border bg-card px-4"
    >
      {subtabs.map((st, idx) => (
        <SubTab
          key={st.id}
          ref={(el) => {
            tabRefs.current[idx] = el;
          }}
          subtab={st}
          color={activeAgent}
          active={st.id === activeSubtab}
          tabIndex={focusedIdx === idx ? 0 : -1}
          onClick={() => navigateTo(st.id)}
          onFocus={() => setFocusedIdx(idx)}
        />
      ))}
    </nav>
  );
}
```

**Decisiones cementadas:**

- **D7 — `min-h-[42px]` HARD (Q4 checkpoint cement):** `min-h-[42px]` (no `h-10` = 40px que era el placeholder F1-S7 AppPanelSlot). Razón: 2px extra dan más respiración + match mockup ratificado. Arbitrary value justificado (heredado F1-S6 patrón `text-[10px]` allowlist). Si auditor objeta, agregar `h-[42px]` → `min-h-[42px]` mismo valor pero crece si contenido lo demanda (más robusto).
- **D8 — `return null` Q5 cement:** when `activeAgent === null || subtabs.length === 0` → return null directo. Componente desmontado, grid AppPanel colapsa fila naturalmente. NO render `<nav>` vacío + NO render placeholder div. Scope checkpoint verbatim.
- **D9 — Roving tabindex pattern verbatim F1-S7:** mismo focusedIdx + tabRefs + handleKeyDown switch + modulo wrap-around. Diferencias: totalTabs es dinámico (no fijo 6 como Ribbon); guards adicionales `if (totalTabs === 0) return;` para edge case (no debe ocurrir post early-return null pero defense-in-depth).
- **D10 — `extractSubtabFromPath` consumption:** lee URL una vez (`pathname`), deriva tanto `activeAgent` (via `extractAgentFromPath`) como `activeSubtab` (via `extractSubtabFromPath`). Ambos pure functions. No re-render cascade.
- **D11 — Active vs focused son ORTOGONALES (paridad F1-S7 D10):** `active` se deriva de URL match contra subtab.id; `focused` se deriva de keyboard state. Diff conceptual: focused = "que sub-tab tiene focus visible", active = "que sub-tab refleja el segmento [subtab] URL".
- **D12 — `navigateTo` guards null `activeAgent`:** además del `tenantId` guard (paridad F1-S7), guarda contra `activeAgent === null` defensive (no debe pasar post early-return null pero safety).
- **D13 — Sub-tabs dinámicos via `RIBBON_SUBTABS[activeAgent]`:** lookup directo (no `.find()`). Type-safe: `activeAgent: RibbonTabSlug`, `RIBBON_SUBTABS: Record<RibbonTabSlug, readonly SubTabMeta[]>` → siempre array.
- **D14 — `aria-label` dynamic per agent name:** `"Sub-secciones {AgentName}"` con `AGENT_CATALOG[slug].name` para los 5 agentes y `"Configuración"` literal para `config`. Spanish neutro verbatim. NO voseo.
- **D15 — `useCallback` para handlers (paridad F1-S7 D8):** evita re-render de SubTab children cuando focusedIdx cambia. `tabRefs` ref-callback inline OK porque pasa ref directo (no closure).
- **D16 — `onFocus` sync (paridad F1-S7 D9):** click directo sobre sub-tab inactive llama `onFocus` antes de `onClick` → setFocusedIdx update OK (sin double-fire navigate por onFocus, sólo state).


### § 2.3 — `SubTab.tsx` molécula (NEW)

`vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx` — NEW.

**Client Component justification:**
- `forwardRef<HTMLButtonElement>` para parent SubTabsBar focus management imperativo.
- Recibe `onClick` + `onFocus` event handlers props.

**Shape:**

```tsx
"use client";

import { forwardRef } from "react";
import type { SubTabMeta, RibbonTabSlug } from "@/lib/agent-catalog";
import {
  agentBgSoftClass,
  agentTextClassSubTab,
} from "./_agent-tw-classes";
import { cn } from "@/lib/utils";

export interface SubTabProps {
  subtab: SubTabMeta;
  /** Agent color slug (or "config" — neutral muted). Drives bg-agent-*-soft tint in active state. */
  color: RibbonTabSlug;
  active: boolean;
  tabIndex: 0 | -1;
  onClick: () => void;
  onFocus: () => void;
}

/**
 * SubTab — Vitalia shell molécula línea 2 (F1-S8).
 *
 * Botón sub-tab individual: emoji icon + label.
 * Active state: bg-agent-{color}-soft tint + text-agent-{color} + font-semibold
 *   (Lucas excepción → text-foreground porque agent-lucas hex es near-black y daña legibilidad)
 *   (Config excepción → bg-muted + text-foreground porque config no es agente, color neutral)
 * Inactive state: text-muted-foreground + font-medium + bg-transparent + hover:bg-muted.
 *
 * active:hover preserva tint (paridad F1-S7 Q16 cement — repite hover:agentBgSoftClass(color)
 * para specificity sobre hover natural de inactive branch).
 *
 * spec_anchor: 01-spec.md § Estados visuales · 03-arch.md § 2.3 D17-D22
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */
export const SubTab = forwardRef<HTMLButtonElement, SubTabProps>(
  function SubTab({ subtab, color, active, tabIndex, onClick, onFocus }, ref) {
    return (
      <button
        ref={ref}
        type="button"
        role="tab"
        aria-selected={active}
        tabIndex={tabIndex}
        data-testid={`sub-tab-${subtab.id}`}
        data-color={color}
        data-active={active ? "true" : "false"}
        onClick={onClick}
        onFocus={onFocus}
        className={cn(
          // base layout — shrink-0 evita squash (paridad F1-S7 Q14)
          "flex shrink-0 items-center gap-1.5 rounded-md px-3 py-1.5 text-sm whitespace-nowrap transition-colors",
          // focus ring
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
          // active vs inactive
          active
            ? cn(
                // Color-specific bg-soft + text + font
                color === "config"
                  ? "bg-muted text-foreground"
                  : cn(
                      agentBgSoftClass(color),
                      agentTextClassSubTab(color),
                    ),
                "font-semibold",
                // active:hover preserva tint (Q16 cement paridad F1-S7)
                color === "config"
                  ? "hover:bg-muted"
                  : `hover:${agentBgSoftClass(color)}`,
              )
            : "font-medium text-muted-foreground hover:bg-muted hover:text-foreground",
        )}
      >
        <span aria-hidden="true">{subtab.icon}</span>
        <span>{subtab.label}</span>
      </button>
    );
  },
);
```

**Decisiones cementadas:**

- **D17 — `forwardRef` mandatory (paridad F1-S7 RibbonTab):** parent (SubTabsBar) necesita `tabRefs.current[idx]?.focus()` imperativo. `forwardRef<HTMLButtonElement, SubTabProps>`.
- **D18 — `agentTextClassSubTab(slug)` NEW helper:** vive en `_agent-tw-classes.ts` EXTEND. Diferencia con `agentTextClass` existente (F1-S6): para `lucas` retorna `text-foreground` (NO `text-agent-lucas`), porque agent-lucas color hex `#111111` (near-black) sobre `bg-agent-lucas-soft` rgba ~10% black tint produce contrast pobre. Para los otros 4 agentes (lisa/adrian/valeria/camila) retorna `text-agent-{slug}` igual que el helper original. Justificado en `01-spec.md § 5 SubTab molécula tabla active states`.
- **D19 — Config color exception:** `color === "config"` branch usa `bg-muted + text-foreground` neutral (Config no es agente, no tiene color marca). Mockup ratificado verbatim.
- **D20 — `active:hover` preserva tint (Q16 cement paridad F1-S7):** template literal `hover:${agentBgSoftClass(color)}` para specificity sobre hover natural. Conocido WARN-1 de F1-S7 (JIT purge edge case con template literal) — accepted same severity LOW: behavior correct porque active branch NO tiene `hover:bg-muted` competing.
- **D21 — `data-color` attribute:** facilita Playwright querying (`[data-testid=sub-tab-doctores][data-color=lisa]`) + visual goldens snapshot identification por color.
- **D22 — `data-active` attribute:** mismo pattern F1-S7 RibbonTab — facilita state inspection en specs + visual diff.
- **D23 — Icons emoji con `aria-hidden="true"`:** screen reader ignora el grapheme (puede leer "casa" o "stetoscopio" inconsistente per OS) — el label `<span>{subtab.label}</span>` adyacente provee texto significativo + es lo que el screen reader anuncia.
- **D24 — `gap-1.5` (6px) + `px-3 py-1.5`:** paridad mockup ratificado (`.sub-tab { padding: 6px 12px; gap: 6px; }`).
- **D25 — `whitespace-nowrap`:** garantiza label + icon en single line (no wrap a 2 líneas en widths estrechos, paridad F1-S7 Q15 cement RibbonTab).

### § 2.4 — `_agent-tw-classes.ts` EXTEND (agentTextClassSubTab helper)

`vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` — **MODIFY**. Agregar `agentTextClassSubTab(slug)` helper.

```ts
// EXISTING (preserve verbatim — NO modificar):
// - agentBgClass(slug)
// - agentBgSoftClass(slug)
// - agentTextClass(slug)         (Lucas devuelve text-agent-lucas — saturated para TypingIndicator etc.)
// - agentDotBgClass = agentBgClass

// ★ NEW F1-S8 — appended at end of file:

/**
 * Text color class for agent — SubTab variant.
 *
 * Lucas exception: agent-lucas hex is near-black (#111111). Over bg-agent-lucas-soft
 * tint (rgba ~10% black), text-agent-lucas produces poor contrast. SubTab active
 * label MUST use text-foreground for Lucas to preserve WCAG AA contrast.
 *
 * Other 4 agents (lisa/adrian/valeria/camila): return text-agent-{slug} normal.
 * Mateo: defensive default text-agent-valeria (mateo not in RIBBON_SUBTABS but type-safe fallback).
 *
 * spec_anchor: 01-spec.md § 5 SubTab active states · 03-arch.md § 2.3 D18
 */
export function agentTextClassSubTab(slug: AgentSlug): string {
  switch (slug) {
    case "lisa":
      return "text-agent-lisa";
    case "valeria":
      return "text-agent-valeria";
    case "adrian":
      return "text-agent-adrian";
    case "lucas":
      return "text-foreground"; // ★ EXCEPTION — Lucas color near-black, daña legibility
    case "camila":
      return "text-agent-camila";
    case "mateo":
      return "text-agent-valeria"; // defensive (mateo NOT in RIBBON_SUBTABS)
    default:
      return "text-agent-valeria";
  }
}
```

**Decisiones cementadas:**

- **D26 — NEW helper (no override existing):** `agentTextClass` (F1-S6) tiene semántica distinta (saturated full-color para TypingIndicator/DelegateMarker — Lucas saturated ahí está OK porque fondo bubble es bg-card claro, no bg-agent-lucas-soft). NEW helper específico para uso SubTab.
- **D27 — Mateo defensive default:** mateo NO está en `RibbonTabSlug` por construcción (excluido AGENT_RIBBON_ORDER F1-S7) — esta rama del switch es TypeScript exhaustiveness check requirement, no runtime path. Default fallback `text-agent-valeria` (alineado con `agentTextClass` original default).

### § 2.5 — `AppPanelSlot.tsx` MODIFY

`vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` — MODIFY.

**Cambios:**

1. Reemplazar el bloque sub-tabs skeleton placeholder (líneas 45-54 actual — 4 `<div>` bars `h-2 w-...`) por `<SubTabsBar />` real.
2. PRESERVAR el bloque content skeleton (líneas 56-73 — F1-S10 reemplazará).
3. PRESERVAR `<Ribbon />` (línea 43 — F1-S7 mantenido).
4. PRESERVAR children pass-through pattern.
5. Actualizar slot label: "AppPanelSlot · F1-S8 / S10" → "AppPanelSlot · F1-S10" (S8 listo).
6. AppPanelSlot sigue siendo Server Component (sin `'use client'`) — hospeda `<Ribbon />` Client + `<SubTabsBar />` Client (boundary natural Next.js Server-hosts-Client).

```tsx
// AppPanelSlot.tsx (modified — keep Server Component, host <Ribbon /> + <SubTabsBar />)
import { Ribbon } from "./Ribbon";
import { SubTabsBar } from "./SubTabsBar";

interface AppPanelSlotProps {
  children?: React.ReactNode;
}

export function AppPanelSlot({ children }: AppPanelSlotProps) {
  return (
    <section
      role="region"
      aria-label="Panel aplicación"
      data-testid="app-panel-slot"
      className="relative flex h-full min-h-0 flex-col overflow-hidden bg-background"
    >
      {/* Ribbon nav — F1-S7 (preserved) */}
      <Ribbon />

      {/* Sub-tabs nav — F1-S8 (real — replaces skeleton from F1-S7 era) */}
      <SubTabsBar />

      {/* Content area — children from route group pass-through (F1-S10 will fill skeleton) */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {children !== undefined ? (
          children
        ) : (
          /* Content skeleton — rendered when no children provided (F1-S10 placeholder) */
          <div aria-hidden="true" className="flex flex-col gap-4 p-6">
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
        )}
      </div>

      {/* Slot label — identifies remaining F1 placeholders */}
      <span
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 whitespace-nowrap rounded-md border border-dashed border-border bg-background/90 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground pointer-events-none"
        aria-hidden="true"
      >
        AppPanelSlot · F1-S10
      </span>
    </section>
  );
}
```

**Tests update:**

- `AppPanelSlot.test.tsx` existing tests (heredados F1-S4 + F1-S7) deben seguir GREEN. Verificar:
  - `<Ribbon />` se renderiza ahora (test selector `[data-testid=ribbon]` presente — heredado F1-S7).
  - `<SubTabsBar />` se renderiza (test selector `[data-testid=sub-tabs-bar]` presente — NEW F1-S8).
  - El bloque skeleton sub-tabs (4 bars) **REMOVED** del DOM (no longer present).
  - El bloque skeleton content sigue presente.
  - Slot label actualizado a "AppPanelSlot · F1-S10" (S8 removed del label).
  - Children pass-through preservado.

**Decisiones cementadas:**

- **D28 — AppPanelSlot Server Component:** mantiene patrón F1-S7 (Server-First default). Hospeda `<Ribbon />` + `<SubTabsBar />` Client components. Next.js boundary natural — NO requiere convertir AppPanelSlot a Client.
- **D29 — Sub-tabs row before content (DOM order):** `<Ribbon />` row 1 · `<SubTabsBar />` row 2 · content row 3. Si `<SubTabsBar />` retorna null (no activeAgent), el DOM flow colapsa naturalmente (no hueco visible). Grid CSS layout reactivo.
- **D30 — Slot label simplificado:** "AppPanelSlot · F1-S10" (eliminado "F1-S8" del label porque F1-S8 está listo). Próximo a eliminar el label completo será F1-S10 cuando reemplace content skeleton.

### § 2.6 — Tests architecture extensions

#### § 2.6.1 — `test-no-cross-brand-shell-mirror.test.ts` EXTEND

Agregar 5 NEW component/symbol names al cross-brand mirror scan:

```ts
// EXISTING extend allowlist names array — append:
const NEW_F1_S8_NAMES = [
  "SubTabsBar",
  "SubTab",
  "RIBBON_SUBTABS",
  "extractSubtabFromPath",
  "SubTabMeta",
];

// Existing names preserved (F1-S6 + F1-S7): ValeriaSidebar, ValeriaRail, ValeriaHistory,
// ValeriaChat, ChatHeader, MessageBubble, TypingIndicator, DelegateMarker, Ribbon, RibbonTab,
// ConfigTab, AppPanelSlot, extractAgentFromPath, AGENT_RIBBON_ORDER, etc.
```

Test: para cada nombre en F1-S8 EXTEND, grep cross-brand (`nicolify`/`comunify`/`lupulo`) `/frontend/src/`. 0 matches each.

#### § 2.6.2 — `test_server_first.test.ts` EXTEND

Agregar 2 NEW client component paths al `'use client'` allowlist (shrink-only, justificado):

```ts
// Existing allowlist preserved + append:
"src/components/shared/shell-organism/SubTabsBar.tsx",  // hooks usePathname/useRouter/useParams + useState focusedIdx + useRef tabRefs + onKeyDown handler
"src/components/shared/shell-organism/SubTab.tsx",       // forwardRef + onClick/onFocus handlers
```

Commit body MUST justificar extension (paridad commit body F1-S7 Ribbon/RibbonTab/ConfigTab).

#### § 2.6.3 — `test-vitalia-ui-strings-no-voseo.test.ts` EXTEND

Agregar scan paths NEW:

```ts
// EXISTING extend file list — append:
"src/components/shared/shell-organism/SubTabsBar.tsx",
"src/components/shared/shell-organism/SubTab.tsx",
```

Y agregar verificación verbatim strings:

```ts
// 22 sub-tab labels:
const F1_S8_SUBTAB_LABELS = [
  "Marca", "Doctores", "Servicios", "Compliance",
  "Lanzar", "En vuelo", "Recursos", "Resultados", "Mercado",
  "Inbox", "Embudo", "Outbound", "Propuestas",
  "Agenda", "Pacientes",
  "Voz del paciente", "Reactivar", "Multiplicar", "Reputación",
  "Mi cuenta", "Conexiones", "Avanzado",
];
// Verify Spanish neutro (sin voseo en glosario) + tildes correctos:
// "Reputación" (con tilde), "Mi cuenta" (sin tilde — palabra plana)
// "En vuelo" (separación correcta — NO "Enviolo")
// All 22 free of "vos/sos/tenés/podés/etc."
```

#### § 2.6.4 — `test-agent-catalog-ssot.test.ts` heredado (no MODIFY required)

El test existente F1-S6 + F1-S7 valida `AGENT_CATALOG` shape + `AgentDescriptor` keys + `AGENT_SLUGS` + `AGENT_RIBBON_ORDER` + `extractAgentFromPath`. F1-S8 EXTEND solo añade `RIBBON_SUBTABS` + `SubTabMeta` + `extractSubtabFromPath` — el test heredado debe seguir GREEN (assertions agregadas en `agent-catalog.test.ts` cubren los nuevos exports, no en este arch test).

Si por simetría se quiere agregar assertion mínima al arch test (e.g., "RIBBON_SUBTABS exists + has 6 entries"), OK opcional. Recomendación: mantener arch test minimal (1 ratchet por arch concern) — assertions específicas viven en unit test `agent-catalog.test.ts`.


## § 3 — Domain Entities

N/A — FE only nav UI puro. NO BE entities. NO Pydantic. NO migrations.

## § 4 — SQLAlchemy Models

N/A — ZERO BE surface.

## § 5 — Pydantic DTOs

N/A — ZERO BE surface.

## § 6 — API Routes

N/A — ZERO BE surface. Componente consume URL existente via `usePathname()`; navegación via `router.push()` a paths Next.js que F1-S9 routing-shell implementará (consume mismos `RIBBON_SUBTABS` + `extractSubtabFromPath` para redirects + 404).

## § 7 — TypeScript Types (Frontend)

Tipos completos en § 2.1. Resumen:

```ts
export interface SubTabMeta {
  id: string;
  label: string;
  icon: string;
}

export const RIBBON_SUBTABS: Record<RibbonTabSlug, readonly SubTabMeta[]>;

export function extractSubtabFromPath(
  pathname: string | null | undefined,
): string | null;

// Component props (NOT exported as type but documented):
interface SubTabProps {
  subtab: SubTabMeta;
  color: RibbonTabSlug;
  active: boolean;
  tabIndex: 0 | -1;
  onClick: () => void;
  onFocus: () => void;
}
```

## § 8 — Repository Interfaces

N/A — ZERO BE surface.

## § 9 — Application Services

N/A — ZERO BE surface.

## § 10 — Agentic Surfaces

N/A — ZERO AGENTIC surface (no LangGraph state, no specialist, no tools, no goldens, no sales_agent wire).

## § 11 — Migration Notes

N/A — ZERO BE surface, ZERO DB schema changes.

## § 12 — File Structure

### NEW files (8)

```
vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx
vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.test.tsx
vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx
vitalia/frontend/src/components/shared/shell-organism/SubTab.test.tsx
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/poms/sub-tabs-bar-page.pom.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-nav.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-agent-change.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-deeplink.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-null-agent.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-invalid-subtab.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-mobile-overflow.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-xss-guard.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-keyboard.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-i18n.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/visual-goldens.spec.ts
```

### NEW visual goldens (13 PNGs)

```
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lisa-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lisa-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lucas-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lucas-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-adrian-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-adrian-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-valeria-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-valeria-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-camila-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-camila-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-config-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-config-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-mobile-lucas-375.png
```

### MODIFY files (5)

```
vitalia/frontend/src/lib/agent-catalog.ts                                       # EXTEND: SubTabMeta + RIBBON_SUBTABS + extractSubtabFromPath
vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts                         # EXTEND: tests F1-S8 fields + helper
vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts       # EXTEND: agentTextClassSubTab helper (Lucas exception)
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx           # MODIFY: skeleton sub-tabs → <SubTabsBar /> real, slot label "F1-S10"
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx      # EXTEND: verify <SubTabsBar /> renders + skeleton sub-tabs REMOVED
vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts # EXTEND: 5 NEW names
vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts            # EXTEND allowlist NEW client components (justify commit body)
vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts # EXTEND glossary check NEW microcopy (22 sub-tab labels + 6 nav aria-labels)
```

### DELETE files

```
(ninguno — F1-S8 NO elimina archivos; reemplaza placeholder JSX dentro AppPanelSlot.tsx solamente)
```

## § 13 — Cross-Cutting Concerns

- **Tenant isolation:** URL `[tenantId]` propagado via `useParams<{ tenantId: string }>()`. `navigateTo` callback usa template literal `/${tenantId}/${activeAgent}/${subtabId}`. NUNCA hardcode `tenantId`. Defensive early-return si `params?.tenantId` undefined.
- **HIPAA-lite scope:** `not_applicable`. SubTabsBar es chrome UI nav puro sin PHI (no patient data, no medical info, no diagnosis labels en sub-tab strings). Verificación: 22 sub-tab labels = nombres de secciones funcionales (Marca, Doctores, Inbox, etc.), NO contiene identifiable patient information.
- **Currency / Master data:** N/A — no monetary values, no datetime fields, no tenant locale dependencies en este componente. Sub-tab labels son strings estáticos Spanish neutro.
- **Spanish neutro LatAm:** 22 sub-tab labels + 6 nav aria-labels (`Sub-secciones {AgentName}` para Lisa/Lucas/Adrián/Valeria/Camila/Configuración) verbatim del mockup ratificado. Sin voseo. Tildes correctos: "Reputación" (con tilde), "Adrián" (con tilde). `test-vitalia-ui-strings-no-voseo.test.ts` EXTEND enforce.
- **PII allowlist:** N/A — zero BE response models, zero data fetching.
- **Native-first dev:** lint + tests + playwright run native Linux (`cd vitalia/frontend && npx ...`). NEVER `docker exec`. Port 3002 vitalia.
- **XSS defense-in-depth:** `extractSubtabFromPath` retorna raw segment string. SubTabsBar consume y compara contra `RIBBON_SUBTABS[activeAgent]` ids estáticos via `.find()` — no match → no active. React JSX text-content auto-escape sanea cualquier payload renderizado. `data-testid={`sub-tab-${subtab.id}`}` usa subtab.id estático del catálogo (no URL segment) → no XSS injection vector. SC-7 spec verbatim.
- **Idempotency on writes:** N/A — no writes. `router.push()` es idempotente (navegar a misma URL no produce side-effects).
- **Boundary FSD:** `shell-organism/` consume `lib/agent-catalog.ts` (allowed shared lib). NO importa `features/*`. NO cross-brand. NO engine core.

## § 14 — Architecture Fitness Impact

Tests heredados (no MODIFY — verified GREEN post-build):
- `test_fsd_boundaries.test.ts` — shell-organism + lib imports válidos
- `test-shell-store-schema-readonly-f1-s5.test.ts` — shell-store NO modificado
- `test-agent-catalog-ssot.test.ts` — hex/thumbnail allowlist sin cambios (F1-S8 no introduce hex nuevos)
- `test_no_hardcoded_colors.test.ts` — tokens semánticos ONLY (bg-card, bg-muted, bg-agent-{slug}-soft via helper)
- `test-no-vt-classes-in-new-features.test.ts` — NO .vt-* en NEW files
- `test-skip-link-target.test.ts` — `<main id="main-content">` no afectado
- `test-ribbon-no-shadcn-tabs.test.ts` — heredado F1-S7 (Ribbon/RibbonTab/ConfigTab no importan @/components/ui/tabs); F1-S8 NO modifica esa lista — SubTabsBar/SubTab también NO importan @/components/ui/tabs (voluntary acoplamiento mismo pattern, verificable en code review pero no enforce arch test extension necesaria — out-of-scope creep). Si se quiere extender el test a SubTabsBar/SubTab, decisión de auditor/Chris post-merge (no en F1-S8).
- `test_no_voseo_in_copy.test.ts` — runtime voseo regex check sigue GREEN con 22 NEW labels (verificado glosario)
- `test_no_hardcoded_strings.test.ts` — heredado, NO afecta (sub-tab labels son data SSoT en agent-catalog.ts no inline JSX)

Tests EXTEND (shrink-only justified, commit body documenta):
- `test-no-cross-brand-shell-mirror.test.ts` — 5 NEW names appended
- `test_server_first.test.ts` — 2 NEW client component paths appended
- `test-vitalia-ui-strings-no-voseo.test.ts` — 22 NEW sub-tab labels + 6 NEW nav aria-labels verbatim check appended

Allowlists shrink-only respetado. NO new violations expected. NO arch test NEW required (F1-S7 inauguró `test-ribbon-no-shadcn-tabs.test.ts` — F1-S8 reusa el patrón pero no requiere arch test paralelo porque la regla "no Shadcn Tabs" es proyectada al SubTabsBar/SubTab via overlap conceptual; si futuro auditor quiere arch test paralelo `test-sub-tabs-no-shadcn-tabs.test.ts`, decisión post-merge).

## § 15 — capability YAML + modules/{m}.md Updates Required (post 2026-05 paradigma)

### NEW `vitalia/docs/product/capabilities/shell-organism/sub-tabs.yaml`

```yaml
capability_id: vitalia.shell-organism.sub-tabs
module: shell-organism
slug: sub-tabs
status: live
date_introduced: 2026-MM-DD   # populated al merge
story_introduced: vitalia-fase1-sub-tabs-line2
package_version: vitalia-frontend@0.1.0
package_path: vitalia/frontend/src/components/shared/shell-organism/
license: proprietary
lift_candidate: cross-brand-when-2-brands-need-multi-agent-ribbon-sub-tabs
surfaces:
  config:
    - vitalia/frontend/src/lib/agent-catalog.ts (EXTEND — SubTabMeta + RIBBON_SUBTABS + extractSubtabFromPath)
  backend: null
  frontend:
    - vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx
    - vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx
    - vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts (EXTEND agentTextClassSubTab)
    - vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx (MODIFY swap skeleton placeholder)
  tests:
    - vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.test.tsx
    - vitalia/frontend/src/components/shared/shell-organism/SubTab.test.tsx
    - vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts (EXTEND)
    - vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx (EXTEND)
    - vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/*.spec.ts (9 specs + visual-goldens)
  docs:
    - vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md § 7.2 (AGENT_SUBTABS whitelist source)
dependencies:
  - vitalia/frontend/src/lib/agent-catalog.ts (F1-S6 + F1-S7 SSoT)
  - vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx (F1-S4)
  - vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx (F1-S7 — context para activeAgent state)
  - vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts (F1-S6)
downstream_unblocks:
  - vitalia-fase1-routing-shell           # F1-S9 — consume extractSubtabFromPath + RIBBON_SUBTABS para redirects/404
  - vitalia-fase1-empty-states            # F1-S10 — 22 sub-tab placeholders consume mismo whitelist
gherkin_coverage:
  total_scenarios: 9
  mapped: 9
  scenarios:
    - SC-1: happy · click sub-tab navega correctly
    - SC-2: happy · cambio de agente re-renderiza sub-tabs
    - SC-3: happy · deep link a sub-tab arbitraria marca active state
    - SC-4: negative · activeAgent null → SubTabsBar oculto
    - SC-5: edge · sub-tab URL inválida → ningún SubTab active
    - SC-6: edge · viewport mobile 375px → horizontal scroll Lucas (5 sub-tabs)
    - SC-7: adversarial · XSS en sub-tab segment → safe
    - SC-8: a11y · keyboard navigation roving tabindex
    - SC-9: i18n · microcopy Spanish neutro renderizado correcto
```

### MODIFY `vitalia/docs/product/capabilities/shell-organism/ribbon.yaml`

Append a sección `downstream_unblocks` (o equivalente): `- vitalia-fase1-sub-tabs-line2` (F1-S8) ✅ shipped. AppPanelSlot sub-tabs placeholder reemplazado por `<SubTabsBar />` real.

### AUTO-REGEN `vitalia/docs/product/modules/shell-organism.md`

Si el archivo no existe (verificado en greps — actualmente NO existe `modules/shell-organism.md` separado; los modules existentes son `agentic.md`, `crm.md`, etc.), entonces post-merge `scripts/reconcile_capabilities.py --brand vitalia` debería generarlo agrupando todas las capabilities en `capabilities/shell-organism/*.yaml`. Si el script aún no soporta sub-directorios bajo `capabilities/`, queda como TODO post-merge para `/pm-vitalia` (no bloquea F1-S8).

## § 16 — Test Surfaces (TDD-mandatory)

TDD RED→GREEN per layer — orden cementado por dependencias:

```
Layer 1: lib/agent-catalog.ts EXTEND
  RED → lib/__tests__/agent-catalog.test.ts extend (SubTabMeta, RIBBON_SUBTABS, extractSubtabFromPath)
  GREEN → lib/agent-catalog.ts EXTEND

Layer 2: _agent-tw-classes.ts EXTEND (agentTextClassSubTab helper)
  RED → optional unit test (puede ir junto a SubTab.test.tsx vía import)
  GREEN → _agent-tw-classes.ts EXTEND

Layer 3: SubTab molécula (consume Layer 1 SubTabMeta + Layer 2 helper)
  RED → SubTab.test.tsx
  GREEN → SubTab.tsx

Layer 4: SubTabsBar organism (consume Layer 3 molécula + Layer 1 RIBBON_SUBTABS + extractSubtabFromPath)
  RED → SubTabsBar.test.tsx
  GREEN → SubTabsBar.tsx

Layer 5: Integration + arch (consume Layer 4 organism)
  RED → AppPanelSlot.test.tsx extend + arch tests EXTEND (cross-brand mirror, server-first, voseo)
  GREEN → AppPanelSlot.tsx MODIFY

Layer 6: E2E behavior + visual
  RED → POM sub-tabs-bar-page.pom.ts + 8 behavior specs + visual-goldens.spec.ts setup
  GREEN → assertions vs componente running en dev stack vitalia (port 3002) + visual goldens iter 1 (--update-snapshots) post Chris ratify side-by-side mockup
```

Coverage threshold: ≥20% lines/functions global (heredado `.claude/rules/frontend-quality.md`). Cobertura attendida F1-S8: ≥80% en `SubTabsBar.tsx` (logic-heavy con roving tabindex + null returns), ≥80% en `extractSubtabFromPath` (puro testeable trivial).

## § 17 — Research Notes (DATE-AWARE)

NO novel patterns introducidos — F1-S8 replica VERBATIM la estructura cementada por F1-S7 (Ribbon roving tabindex + extractAgentFromPath pattern). Toda decisión arquitectónica heredada de F1-S7 03-arch.md con citas verbatim (D5/D7-D11/D16/D17 paridad mapping).

**Cero WebSearch necesario.** Stack versions cementadas (Next.js 16, React 19, Shadcn primitives F1-S0, Tailwind v4) — sin upgrade en F1-S8.

**Sources internos consultados (no library docs externas):**

- `vitalia/docs/archive/2026/stories/vitalia-fase1-ribbon-6-tabs/03-arch.md` (F1-S7 pattern source) · accessed 2026-05-25
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § 7.2 (AGENT_SUBTABS whitelist canónico) · accessed 2026-05-25
- `vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/01-spec.md` v2 + mockup ratificado `sub-tabs.html` · accessed 2026-05-25

**Knowledge cutoff disclosure:** Opus 4.7 cutoff is Jan 2026. F1-S8 NO requiere conocimiento post-cutoff (sin nuevas APIs, sin nuevas libraries). Heredado F1-S7 que ya verificó stack currency en su Step 0.

## § 18 — Open Questions for PM

Ninguna. Batch 1 + Batch 2 ratificadas en checkpoint:

- Q1 SSoT path: EXTEND agent-catalog.ts ✅
- Q2 Icons: emojis ✅
- Q3 Keyboard nav: roving tabindex ✅
- Q4 Height: min-h-[42px] ✅
- Q5 activeAgent=null: return null total ✅
- Active:hover preserves tint (default F1-S7 Q16 paridad) ✅
- Config defaultSubtab: 'cuenta' (default per F1-S7 ConfigTab nav) ✅
- Wrap-around keyboard: Arrow Right en último → primero (default F1-S7 Ribbon) ✅

Autonomous chain ratificado: `/architect` → `/dev-team` → `/auditor` → `/pm-vitalia` merge.

## § 19 — Diff drift (CONTEXT-BRIEF Faithfulness)

N/A — CONTEXT-BRIEF.md absent for this story (Path B self-ran greps). § 11 Faithfulness gap N/A.

