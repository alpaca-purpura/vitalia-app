<!-- voseo-allowed: glosario reference + internal architecture documentation -->

---
story_id: vitalia-fase1-shell-layout-5050
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-23
architect_iter: 1
architect_run_on: 2026-05-23
surfaces: FE only
---

# F1-S4 · vitalia-fase1-shell-layout-5050 · 03-arch.md (consolidado)

## § 0 — Context Summary

- **Story:** vitalia-fase1-shell-layout-5050 — outcome `vitalia-mvp-ui-foundation` fase-1.
- **PR folder:** `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/`
- **Architect run on:** 2026-05-23 (Step 0 captured: `date -u +%Y-%m-%d` → 2026-05-23, `date -u +%Y-%m` → 2026-05). Opus 4.7 knowledge cutoff Jan 2026; library currency verified live via WebSearch on 2026-05-23.
- **Modules touched:** `shell-organism` (brand-local module — Vitalia frontend chrome).
- **Surface → builder → auditor mapping (PM uses to spawn correct agents):**

  | Surface | Builder | Auditor |
  |---|---|---|
  | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/**` | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/components/shared/shell-organism/**` (Shell* + Slots) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/stores/shell-store.ts` | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/e2e/**` (Playwright) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |

  NO BE surface · NO AGENTIC surface. R23 NO aplica (zero agentic).

- **Skills consulted (decisions ratified verbatim):**
  - `frontend-expert` — Server-first preference + "use client" solo en hojas con state; FSD-Lite boundaries (`components/shared/shell-organism/` correct for cross-feature chrome); confirm test colocation (`__tests__/` sibling).
  - `playwright-expert` — POM pattern (`ShellLayoutPage`), Clerk auth fixture, visual goldens via `@project=visual`, freshness gate pre-run, port 3002 vitalia.
  - `tessl__shadcn-ui` (via WebSearch verification) — Shadcn's `Resizable` wraps `react-resizable-panels` (v4.11.1, published 8 days ago as of 2026-05-23). Provides nativa accessibility, keyboard `ArrowLeft`/`ArrowRight` step nav, persistence via panel `id` + `autoSaveId`, smooth animations, constraint handling. **Adopted as canonical (decision § Resize Implementation).**
  - `tessl__react-patterns` — Server Components default; Client Components solo en hojas con `useShellStore` o resize handler. Hydration safety: zustand `persist` is synchronous on client, no SSR mismatch when store consumed inside `'use client'` leaf.
  - `tessl__tailwind` — semantic tokens (`bg-card`, `border-border`, `bg-background`) consumed via `globals.css` CSS vars (Design Contract §5.1). No hardcoded hex.
  - `tessl__vitest` — colocated tests `Component.test.tsx`. RTL + `@testing-library/jest-dom`. Mock zustand store via direct `useShellStore.setState` o `vi.mock`.
  - `tessl__nextjs-app-router-modularization` — route group `(shell-organism)/` parallel to `(dashboard)/` legacy, no interference. `[tenantId]` dynamic segment NEW (first usage in vitalia).
  - `claude-md-management` — Spanish neutro neutro estándar (no voseo en strings user-facing UI).

- **CONTEXT-BRIEF source:** self-ran greps Path B + Read on 01-spec.md verbatim + Read SHELL-DESIGN-CONTRACT.md §§ 3.4/5.1/6.1/9 + Read mockups paths + Read ADR-vitalia-003. CONTEXT-BRIEF.md absent (story-by-story without Haiku context-builder).

- **Cross-module anti-duplication audit (NO-NEW-LAYER):** see § Existing Systems Audit below. **Verdict: NEW (justified — brand-local shell pattern, zero matches in nicolify/comunify/lupulo, no engine core overlap).**

- **capability YAML files affected (post-merge updates required, paradigma post 2026-05):**
  - `vitalia/docs/product/capabilities/platform/shell.layout-5050.yaml` — NEW (status: planned → live post-merge per § 13 abajo).
  - `vitalia/docs/product/modules/platform.md` — auto-list refresh post-merge (via `reconcile_capabilities.py --brand vitalia`).

- **Architecture gates that must keep passing:**
  - `vitalia/frontend/src/__tests__/architecture/*.test.ts` (FSD boundaries · no-cross-brand · semantic tokens · skip-link target) — allowlists shrink only.
  - `vitalia/frontend/src/__tests__/architecture/test-page-padding.test.ts` (heredado — design tokens consumption).
  - Visual goldens shrink-only ratchet post-ratificación (`shell-mockup-per-component.md`).

## § 0.1 — Existing Systems Audit (NO NEW LAYER rule)

### Source of evidence

- [x] Self-run greps (Path B — context-builder fallback; CONTEXT-BRIEF.md absent for this story)
- [ ] CONTEXT-BRIEF.md § 7 + § 8 (not generated for this story)

### Audit cross-module ejecutado

```bash
# 1. Cross-brand mirror scan (anti-duplication.md § lift shared rule)
for b in nicolify comunify lupulo; do
  for name in ShellOrganismLayout ValeriaSidebarSlot AppPanelSlot ShellModeToggle shell-store; do
    grep -rln "$name" $b/ 2>/dev/null
  done
done
# Result: 0 matches en las 3 brands. ✅ No mirror existente.

# 2. Engine core consultation (READ-ONLY, no propose modify)
find core/luana-core-* -name "*.ts" -o -name "*.tsx" 2>/dev/null | head
# Result: core packages son Python (luana_core_*). NO TS shell abstraction en engine. ✅

# 3. Same-brand existing duplicates
find vitalia/frontend/src -name "ShellOrganismLayout*" -o -name "ValeriaSidebarSlot*" -o -name "AppPanelSlot*" -o -name "shell-store*" 2>/dev/null
# Result: 0 matches. ✅ Net-new files.

# 4. Resize lib already installed?
grep -E '"react-resizable-panels"' vitalia/frontend/package.json
# Result: NOT installed. Will be added by T-3 via `pnpm add react-resizable-panels`.

# 5. Reused F1-S1/S2/S3 components
ls vitalia/frontend/src/components/shared/shell-organism/{TopBarGlobal,LogoMark,ThemeToggle,TenantSwitcher}.tsx
# Result: ALL exist. ✅ REUSE without modification per § 1 anti-creep.
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `TopBarGlobal` | `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | active F1-S2 done | **REUSE sin modificar** — ya monta LogoMark + TenantSwitcher + ThemeToggle. No agregar `ShellModeToggle` adentro (see § Resolution Q7 abajo). |
| `LogoMark` / `ThemeToggle` / `TenantSwitcher` | mismo dir | active F1-S1/S2/S3 done | **REUSE** (consumidas via TopBarGlobal — no necesitan ser tocadas). |
| `useTenantStore` (zustand persist) | `vitalia/frontend/src/stores/tenant-store.ts` | active F1-S3 done | **REUSE** patrón (mismo middleware `persist` + `createJSONStorage`). `useShellStore` NEW sigue mismo template (independent store, no acoplamiento). |
| Skip link `<a href="#main-content">` | `vitalia/frontend/src/app/layout.tsx` línea 33-38 | active F1-S2 done | **REUSE** — apunta a `#main-content` que esta story (T-3) crea como `<main id="main-content" tabIndex={-1}>` dentro de `ShellOrganismLayout`. |
| Route group `(dashboard)/` legacy con AppShell | `vitalia/frontend/src/app/(dashboard)/` + `src/components/shared/shell/AppShell.tsx` | active legacy | **PRESERVE intacto** — coexiste paralelo per D3 SHELL-DESIGN-CONTRACT (Phase 2 lo deprecate). |

### Decisión por sistema

- **`ShellOrganismLayout`, `ValeriaSidebarSlot`, `AppPanelSlot`, `useShellStore`, `ShellModeToggle`**: **NEW** (justified). No equivalent existente en vitalia ni en otras brands. No engine core overlap (shell-organism es brand-local Vitalia — futuro lift candidate cuando lupulo/fitflow adopten patrón similar via `core/luana-core-ui-shell/`, fuera del scope F1-S4).
- **TopBarGlobal/LogoMark/ThemeToggle/TenantSwitcher**: **EXTEND consumo** — importadas y montadas dentro de `ShellOrganismLayout`. No edits a los archivos.
- **Skip link en root layout**: **EXTEND target** — esta story provee el `<main id="main-content">` que el skip-link de root layout ya referencia (F1-S2 deployment).

**Cross-brand lift evaluation:** patrón shell-organism aún no replicado en otras brands. Per `.claude/rules/anti-duplication.md`, lift se dispara **on second occurrence** (DRY threshold = 2 consumers). F1-S4 es primera ocurrencia → NEW correct. Auditor (post-merge) o future story que duplique en lupulo → triggerea `/pm-luana` promotion proposal para `core/luana-core-ui-shell/`.

## § 1 — Surfaces involved (verbatim)

| Surface | Aplica | Owner |
|---|---|---|
| BE (FastAPI Python) | NO | — |
| AGENTIC (LangGraph / deepagents / sales_agent) | NO | — |
| FE (Next.js 16 App Router + Shadcn + Tailwind + Zustand) | **SÍ** | `builder-frontend` Sonnet/opencode |

## § 2 — FE Architecture Detail

### § 2.1 — Route Group + Layout root (NEW route segment `[tenantId]`)

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/
├── layout.tsx                  # Thin server boundary — passes tenantId param + children
└── page.tsx                    # Default landing — server-side `redirect('/{tenantId}/lisa/marca')`
```

**`app/[tenantId]/(shell-organism)/layout.tsx`** (Server Component — thin):

```tsx
import { ShellOrganismLayout } from "@/components/shared/shell-organism/ShellOrganismLayout";

export default function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { tenantId: string };
}) {
  return (
    <ShellOrganismLayout tenantId={params.tenantId}>
      {children}
    </ShellOrganismLayout>
  );
}
```

**`app/[tenantId]/(shell-organism)/page.tsx`** (Server Component — redirect):

```tsx
import { redirect } from "next/navigation";

export default function ShellRootPage({ params }: { params: { tenantId: string } }) {
  redirect(`/${params.tenantId}/lisa/marca`);
}
```

Note: el `redirect` server-side a `/{tenantId}/lisa/marca` confía en que la ruta `/[tenantId]/[agent]/[subtab]/page.tsx` existirá en F1-S9 (routing-shell). En F1-S4 todavía no — la página puede 404 si el user navega directo a `/(shell-organism)`. SCN-1 igual valida el redirect (Next.js redirect emite 307 navegacional, el browser sigue; el 404 final es post-F1-S9). El gherkin spec ya lo asume en SC-1.

### § 2.2 — `ShellOrganismLayout` template (Client Component — JUSTIFICATION)

`vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx`

**Client Component justification:**
- Consume `useShellStore` (zustand hook → Client-only).
- Hosts `PanelGroup` from `react-resizable-panels` (drag interaction → needs DOM access).
- Hosts viewport-aware logic (`window.matchMedia('(min-width: 1024px)')` → cliente).

```tsx
'use client';

import { TopBarGlobal } from "./TopBarGlobal";
import { ValeriaSidebarSlot } from "./ValeriaSidebarSlot";
import { AppPanelSlot } from "./AppPanelSlot";
import { useShellStore } from "@/stores/shell-store";
import { useViewportGuard } from "./useViewportGuard";
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels";
import { cn } from "@/lib/utils";

export interface ShellOrganismLayoutProps {
  children: React.ReactNode;
  tenantId: string;
}

export function ShellOrganismLayout({ children, tenantId }: ShellOrganismLayoutProps) {
  const shellMode = useShellStore((s) => s.shellMode);
  const valeriaState = useShellStore((s) => s.valeriaState);

  // Edge case auto-fix: viewport [768-1023] + valeriaState='full' → force 'rail'
  useViewportGuard();

  // Calculate min/max for Valeria panel as % of viewport
  // (react-resizable-panels v4 uses percent units, not px)
  const minValeriaPct = valeriaState === "full" ? 38 /* ~620/1640 */ : 22 /* ~360/1640 */;
  const minAppPct = 30; // ~480/1640
  const defaultValeriaPct = shellMode === "agentic" ? 50 : 5; /* web rail ~60px */

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      <TopBarGlobal />

      {shellMode === "agentic" ? (
        // Desktop ≥md: resizable 2-panel grid. Mobile <md: 1-col w/ Valeria drawer (TBD F1-S5+).
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-hidden md:block hidden"
          aria-label="Contenido principal"
        >
          <PanelGroup
            direction="horizontal"
            autoSaveId="vitalia-shell-split-agentic"
            className="h-full"
          >
            <Panel
              id="valeria-panel"
              order={1}
              defaultSize={defaultValeriaPct}
              minSize={minValeriaPct}
              collapsible={false}
            >
              <ValeriaSidebarSlot />
            </Panel>
            <PanelResizeHandle
              id="shell-handle"
              className={cn(
                "w-1 bg-border hover:bg-primary/40 focus-visible:bg-primary",
                "data-[resize-handle-state=drag]:bg-primary",
                "transition-colors outline-none"
              )}
              aria-label="Redimensionar paneles"
            />
            <Panel
              id="app-panel"
              order={2}
              defaultSize={100 - defaultValeriaPct}
              minSize={minAppPct}
            >
              <AppPanelSlot>{children}</AppPanelSlot>
            </Panel>
          </PanelGroup>
        </main>
      ) : (
        // shellMode === 'web' → static grid 60px/1px/1fr
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 grid grid-cols-[60px_1px_1fr] overflow-hidden md:grid hidden"
          aria-label="Contenido principal"
        >
          <ValeriaSidebarSlot />
          <div className="bg-border" aria-hidden="true" />
          <AppPanelSlot>{children}</AppPanelSlot>
        </main>
      )}

      {/* Mobile fallback (< md): single-column layout */}
      <main
        id="main-content"
        tabIndex={-1}
        className="flex-1 overflow-hidden md:hidden"
        aria-label="Contenido principal"
      >
        <AppPanelSlot>{children}</AppPanelSlot>
        {/* Mobile drawer trigger: F1-S5 will add a burger button in TopBar slot */}
      </main>
    </div>
  );
}
```

**Implementation note — duplicate `<main id="main-content">` 3 times:** Each branch (`shellMode==='agentic'`, `shellMode==='web'`, mobile fallback) renders its own `<main>` but with `md:hidden` / `md:block` / `md:grid` mutually exclusive Tailwind classes. Only ONE `<main>` is visible in the DOM at any given viewport. Skip-link `href="#main-content"` resolves to the visible one. Auditor will verify only-one-active via Playwright.

Alternative considered: use a single conditional render. Rejected because CSS-driven branching avoids JS-side viewport detection for the initial paint, preventing hydration mismatch when SSR-rendered viewport differs from client.

### § 2.3 — `ValeriaSidebarSlot` (Server Component placeholder)

`vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx`

```tsx
/**
 * ValeriaSidebarSlot — placeholder F1-S4.
 * F1-S5/F1-S6 reemplazará con ValeriaSidebar real (rail + history + chat).
 * Server Component (zero state — pure render).
 */
export function ValeriaSidebarSlot() {
  return (
    <aside
      data-testid="valeria-sidebar-slot"
      role="complementary"
      aria-label="Panel Valeria (placeholder — F1-S5/S6 lo construirá)"
      className="h-full border-r border-border bg-card flex flex-col overflow-hidden"
    >
      <div className="flex-1 grid place-items-center text-muted-foreground text-sm">
        ValeriaSidebar — pendiente F1-S5/S6
      </div>
    </aside>
  );
}
```

### § 2.4 — `AppPanelSlot` (Server Component placeholder)

`vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx`

```tsx
/**
 * AppPanelSlot — placeholder F1-S4.
 * F1-S7/F1-S8/F1-S10 reemplazará con Ribbon + SubTabsBar + ContentArea.
 * Server Component (slot for children).
 */
export interface AppPanelSlotProps {
  children: React.ReactNode;
}

export function AppPanelSlot({ children }: AppPanelSlotProps) {
  return (
    <section
      data-testid="app-panel-slot"
      role="region"
      aria-label="Panel aplicación (placeholder — F1-S7/S8/S10 lo construirá)"
      className="h-full bg-background flex flex-col overflow-hidden"
    >
      {children ?? (
        <div className="flex-1 grid place-items-center text-muted-foreground text-sm">
          AppPanel — pendiente F1-S7/S8/S10
        </div>
      )}
    </section>
  );
}
```

### § 2.5 — `useShellStore` (Zustand persist)

`vitalia/frontend/src/stores/shell-store.ts`

```ts
/**
 * shell-store.ts — global shell state (valeriaState + shellMode).
 * F1-S4 vitalia-fase1-shell-layout-5050 — T-1.
 *
 * Schema cementado en SHELL-DESIGN-CONTRACT.md §6.1.
 * Persistence: localStorage key 'vitalia-shell-state'.
 * partialize: both fields persisted (no transient state).
 *
 * Default valeriaState resolution (ratified architect § 2.5.1):
 *   - 'full' (override of DC §6.1 'rail' default) → matches agentic mockup default
 *     que muestra Valeria con history visible. F1-S5/S6 puede revisitar si rail
 *     funcional cambia el default.
 *
 * downstream-regression-na: brand-local store; no cross-brand consumers.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ValeriaState = "collapsed" | "rail" | "full";
export type ShellMode = "agentic" | "web";

export interface ShellStoreState {
  valeriaState: ValeriaState;
  shellMode: ShellMode;
  setValeriaState: (s: ValeriaState) => void;
  cycleValeriaState: () => void;  // rail ↔ full toggle
  setShellMode: (m: ShellMode) => void;
}

export const SHELL_STORAGE_KEY = "vitalia-shell-state" as const;

type PersistedState = {
  valeriaState: ValeriaState;
  shellMode: ShellMode;
};

export const useShellStore = create<ShellStoreState>()(
  persist(
    (set, get) => ({
      valeriaState: "full",         // ★ default 'full' (architect resolution Q1)
      shellMode: "agentic",          // ★ default 'agentic'
      setValeriaState: (s) => set({ valeriaState: s }),
      cycleValeriaState: () =>
        set({ valeriaState: get().valeriaState === "full" ? "rail" : "full" }),
      setShellMode: (m) => set({ shellMode: m }),
    }),
    {
      name: SHELL_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      version: 1,
      partialize: (state): PersistedState => ({
        valeriaState: state.valeriaState,
        shellMode: state.shellMode,
      }),
    }
  )
);
```

#### § 2.5.1 — Ambiguity resolution: default `valeriaState`

**Ambiguity:** DC §6.1 dice default `'rail'`. 01-spec.md §1 (SCN-1) dice default `'full'` para mostrar shell completo.

**Resolution: default `'full'` (override DC §6.1).** Justificación:

1. **Mockup ratificado (`shell-layout-agentic.html`)** muestra Valeria con rail (60px) + history (280px) + chat (resto). Eso es state='full'. La spec ratificó este mockup explícitamente (gate visual).
2. **Funcional sentido user-onboarding:** primer visita Vitalia → user ve la sidebar completa de Valeria visible (capacidad agente) sin necesidad de descubrir el rail expand button. Si default='rail', user solo ve íconos hasta que F1-S5 deploye el botón.
3. **F1-S5 puede revisitar:** cuando rail button + state cycling esté funcional (F1-S5), si UX testing muestra que default='rail' es mejor adoption metric, change SHELL_STORAGE_KEY version bump + migration. Por ahora 'full' es el contrato visual ratificado.
4. **DC §6.1 actualizar:** post-merge, `/pm-vitalia` actualiza SHELL-DESIGN-CONTRACT.md §6.1 línea 363 cambiando `'rail'` → `'full'` con commit msg cita esta resolution + iter.

### § 2.6 — `useViewportGuard` (custom hook — viewport edge case)

`vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts`

```ts
/**
 * useViewportGuard — auto-force valeriaState 'rail' cuando viewport [768-1023]
 * + state='full' no quepa (min 1104px requeridos).
 *
 * Resolution architect § Q9.
 * Re-evalúa on window resize (debounced 100ms).
 * Idempotent — solo escribe si state cambia.
 *
 * F1-S5+ puede agregar override para state='collapsed' si UX testing lo pide.
 */
'use client';
import { useEffect } from "react";
import { useShellStore } from "@/stores/shell-store";

const FULL_MODE_MIN_VIEWPORT = 1104; // 620 + 4 + 480 + safety
const MD_BREAKPOINT = 768;

export function useViewportGuard() {
  const valeriaState = useShellStore((s) => s.valeriaState);
  const setValeriaState = useShellStore((s) => s.setValeriaState);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let raf = 0;
    const evaluate = () => {
      const w = window.innerWidth;
      if (w >= MD_BREAKPOINT && w < FULL_MODE_MIN_VIEWPORT && valeriaState === "full") {
        setValeriaState("rail");
      }
    };

    const onResize = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(evaluate);
    };

    evaluate();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(raf);
    };
  }, [valeriaState, setValeriaState]);
}
```

Note: el guard NO restaura a `'full'` cuando el viewport vuelve a ≥1104 — eso es decisión del user (rail button F1-S5). El guard es one-way protective.

### § 2.7 — `ShellModeToggle` (disabled placeholder)

`vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.tsx`

```tsx
/**
 * ShellModeToggle — disabled chip placeholder F1-S4.
 * F1-S5/S7+ activará interaction → setShellMode('agentic' | 'web').
 *
 * Renderizado dentro de TopBarGlobal slot derecho (re-orderable).
 * IMPORTANT: F1-S4 NO modifica TopBarGlobal.tsx — el toggle se monta DENTRO
 * del ShellOrganismLayout como overlay/sibling. Por F1-S5 acordaremos
 * si mover dentro de TopBarGlobal definitivo.
 */
'use client';
import { useShellStore } from "@/stores/shell-store";

export function ShellModeToggle() {
  const shellMode = useShellStore((s) => s.shellMode);
  return (
    <button
      type="button"
      disabled
      data-testid="shell-mode-toggle"
      aria-disabled="true"
      aria-label={`Modo de shell: ${shellMode === "agentic" ? "agéntico" : "web"} activo`}
      title="Modo (agéntico/web) — toggle se activa en F1-S5/S7"
      className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground opacity-60 cursor-not-allowed"
    >
      <span>{shellMode === "agentic" ? "Agéntico" : "Web"}</span>
    </button>
  );
}
```

**Mounting decision (resolves Q7):** `ShellModeToggle` se renderiza **dentro de `ShellOrganismLayout`** justo después del `<TopBarGlobal />`, absoluto positioned over the TopBar area. NO se modifica `TopBarGlobal.tsx` (REUSE intacto). Concretamente:

```tsx
// inside ShellOrganismLayout, after <TopBarGlobal />:
<div className="absolute top-1.5 left-1/2 -translate-x-1/2 z-50 pointer-events-auto">
  <ShellModeToggle />
</div>
```

Rationale: F1-S2 ratificó `TopBarGlobal.tsx` y este story declara "REUSE sin modificar" (§ 1.1 anti-creep). Cuando F1-S5 active el toggle, podrá decidir si mover dentro del TopBar (modificándolo entonces con su propia story) o mantener el overlay pattern.

### § 2.8 — File tree exacto

```
vitalia/frontend/src/
├── app/
│   └── [tenantId]/                                       # NEW dynamic segment
│       └── (shell-organism)/                             # NEW route group
│           ├── layout.tsx                                # NEW (thin Server boundary)
│           └── page.tsx                                  # NEW (redirect to /{tenantId}/lisa/marca)
├── components/
│   └── shared/
│       └── shell-organism/
│           ├── ShellOrganismLayout.tsx                   # NEW (Client — main + resize)
│           ├── ValeriaSidebarSlot.tsx                    # NEW (Server placeholder)
│           ├── AppPanelSlot.tsx                          # NEW (Server placeholder)
│           ├── ShellModeToggle.tsx                       # NEW (Client disabled chip)
│           ├── useViewportGuard.ts                       # NEW (Client hook)
│           ├── ShellOrganismLayout.test.tsx              # NEW (Vitest unit)
│           ├── ValeriaSidebarSlot.test.tsx               # NEW (Vitest unit)
│           ├── AppPanelSlot.test.tsx                     # NEW (Vitest unit)
│           ├── ShellModeToggle.test.tsx                  # NEW (Vitest unit)
│           ├── useViewportGuard.test.ts                  # NEW (Vitest unit)
│           ├── TopBarGlobal.tsx                          # REUSE (no edits)
│           ├── LogoMark.tsx                              # REUSE (no edits)
│           ├── ThemeToggle.tsx                           # REUSE (no edits)
│           ├── TenantSwitcher.tsx                        # REUSE (no edits)
│           ├── TenantOption.tsx                          # REUSE (no edits)
│           ├── TenantBadge.tsx                           # REUSE (no edits)
│           ├── TenantStoreBootstrap.tsx                  # REUSE (no edits)
│           └── AddClinicPlaceholderModal.tsx             # REUSE (no edits)
├── stores/
│   ├── shell-store.ts                                    # NEW (Zustand persist)
│   ├── __tests__/
│   │   └── shell-store.test.ts                          # NEW (Vitest unit)
│   └── tenant-store.ts                                   # REUSE (no edits)
└── __tests__/
    └── architecture/                                     # extend allowlists (shrink-only)

vitalia/frontend/e2e/
├── pages/
│   └── ShellLayoutPage.ts                                # NEW POM (Playwright)
├── fixtures/
│   └── shell-theme.fixture.ts                            # NEW (theme/storage state)
├── regression/
│   └── vitalia-fase1-shell-layout-5050/
│       ├── render-agentic-default.spec.ts                # NEW (SC-1)
│       ├── mobile-collapse.spec.ts                       # NEW (SC-2)
│       ├── resize-and-state.spec.ts                      # NEW (SC-3)
│       ├── a11y-keyboard.spec.ts                         # NEW (SC-4)
│       └── visual-goldens.spec.ts                        # NEW (6 PNG snapshots)
└── __screenshots__/
    └── shell-layout-5050/
        ├── agentic-1280x800-light.png                   # NEW (golden gen iter 1)
        ├── agentic-1280x800-dark.png                    # NEW
        ├── agentic-rail-1280x800.png                    # NEW
        ├── web-1280x800-light.png                       # NEW
        ├── web-1280x800-dark.png                        # NEW
        └── agentic-mobile-375x667.png                   # NEW
```

**Package.json delta (T-3):**

```diff
   "dependencies": {
+    "react-resizable-panels": "^4.11.1",
     ...
   }
```

### § 2.9 — Resize Implementation Decision

**Decision: Option A — `react-resizable-panels` v4 (Shadcn-canonical wrapper).**

| Criterion | Option A: `react-resizable-panels` | Option B: Custom `useResizable` hook |
|---|---|---|
| Maintenance | ✅ Active (v4.11.1 published 8 days ago, 2026-05-23) | ⚠️ Owned by Vitalia team |
| LOC | ~30 LOC integration | ~80-120 LOC manual |
| A11y | ✅ Native `role="separator"` + keyboard ArrowLeft/Right | ⚠️ Manual implementation needed |
| Persistence | ✅ Built-in `autoSaveId` → localStorage automatic | ⚠️ Manual debounced write |
| Constraint clamping | ✅ `minSize`/`maxSize` props enforce | ⚠️ Manual clamp in onDrag handler |
| Animations | ✅ Native smooth | ⚠️ Manual |
| Shadcn precedent | ✅ It IS the Shadcn `Resizable` underlying lib | ⚠️ Reinvents pattern |
| Bundle size | ~12kB gzip | ~3kB gzip |
| Risk | low (mature, widely adopted — 2035 dependents) | medium (reimplement bugs) |

**Why A wins:** for a brand-local feature with multiple visual + functional goldens to maintain, leveraging the canonical Shadcn-recommended lib reduces test surface (less custom code to test) and aligns with cross-brand future lift (lupulo/fitflow se beneficiarían del mismo dep). The 9 kB bundle delta is acceptable for chrome UI.

**v4 API used (versioned-pinned):**
- `PanelGroup` (container, `direction="horizontal"`, `autoSaveId`)
- `Panel` (`id`, `order`, `defaultSize`, `minSize`, `maxSize`, `collapsible`)
- `PanelResizeHandle` (renders separator with native a11y role)

**Note:** v4 uses **percent units, not px**. Min sizes calculated as `% of viewport`:
- `minValeriaPct = (valeriaState === 'full' ? 620 : 360) / viewport_px * 100` — approximated to 38% / 22% at 1640px reference. **Validation at runtime** via `PanelGroup` `onLayout` callback if necesario refine (T-3 evaluate).
- Alternative px-precision: wrap with a `useResizeObserver` and recompute `minSize` prop on viewport change. **Adopted** if `% approximation` falla SC-3 boundary assertions.

### § 2.10 — Server vs Client Component decision tree

| Component | Type | Justification |
|---|---|---|
| `app/[tenantId]/(shell-organism)/layout.tsx` | **Server** | Thin boundary; reads `params.tenantId`; passes to ShellOrganismLayout. No state, no DOM. |
| `app/[tenantId]/(shell-organism)/page.tsx` | **Server** | Simple `redirect()` call. |
| `ShellOrganismLayout.tsx` | **Client** (`'use client'`) | Consume `useShellStore` (hook) + `PanelGroup` (DOM interactive). |
| `ValeriaSidebarSlot.tsx` | **Server** | Pure render placeholder. No state. |
| `AppPanelSlot.tsx` | **Server** | Pure render placeholder with `{children}` slot. |
| `ShellModeToggle.tsx` | **Client** (`'use client'`) | Reads `useShellStore` for current mode. |
| `useViewportGuard.ts` | **Client hook** | `useEffect` + `window` access. |
| `shell-store.ts` | **Client-only module** | Zustand store accessed via hook from Client Components. |

### § 2.11 — Cross-cutting decisions

| Concern | Decision |
|---|---|
| Tenant isolation | URL param `[tenantId]` propagated via Next.js routing. Auth/middleware (Clerk) gates upstream — F1-S4 confía en eso (out-of-scope FE). `fetchClient` no-aplica (F1-S4 sin fetch propio). |
| PII / PHI | N/A — chrome UI, no PHI fields. `hipaa_lite_scope: not_applicable` per `vitalia/.claude/rules/hipaa-lite.md`. |
| Currency / locale | N/A — no monetary, no dates rendered en este shell. |
| Spanish neutro | Strings UI Spanish neutro LatAm per `.claude/rules/spanish-text.md` (sin voseo). Aria-labels + tooltips revisados (§ 2 mockup ratificado). |
| Brand voice | N/A — chrome estándar Vitalia. Brand voice per-tenant aplica en sales_agent + Valeria chat (F1-S6+). |
| Native-first dev | TSC/ESLint/Vitest/Playwright nativo Linux (`${WS}/.venv/bin` no aplica — FE only). Comandos `npx`. |
| HIPAA-lite scope | `not_applicable` — story toca solo layout/UI sin patient_*/medical_*/treatment_*. Per overlay rule § Aplica. |

## § 3 — Test Construction Plan ★ v4.1

### § 3.1 — `creation_order` (TDD RED-first per ticket)

1. **T-1 unit** — `shell-store.test.ts` (RED initial → import fails → write store).
2. **T-2 unit** — `ValeriaSidebarSlot.test.tsx` + `AppPanelSlot.test.tsx` (RED → write Server Components).
3. **T-3 unit** — `useViewportGuard.test.ts` + `ShellOrganismLayout.test.tsx` (RED → write layout + hook).
4. **T-3 visual** — Iter 1 golden generation via `--update-snapshots`; CI-verify subsequent runs.
5. **T-4 unit** — page.tsx redirect test (Vitest `expect.poll` on next/navigation mock).
6. **T-5 unit** — `ShellModeToggle.test.tsx` (RED → write disabled chip).
7. **T-6 unit** — full module Vitest run (coverage threshold per `frontend-expert`).
8. **T-7 E2E + visual goldens** — Playwright POM creation + 4 functional specs + 6 visual specs.

### § 3.2 — `scenario_to_test` mapping

| Gherkin | Test file | Type | POM |
|---|---|---|---|
| SC-1 happy 50/50 default | `regression/vitalia-fase1-shell-layout-5050/render-agentic-default.spec.ts` | Playwright E2E | `ShellLayoutPage` |
| SC-2 mobile colapsa | `regression/vitalia-fase1-shell-layout-5050/mobile-collapse.spec.ts` | Playwright E2E + visual | `ShellLayoutPage` |
| SC-3 resize boundary + state | `regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts` | Playwright E2E | `ShellLayoutPage` |
| SC-4 a11y keyboard + axe | `regression/vitalia-fase1-shell-layout-5050/a11y-keyboard.spec.ts` | Playwright E2E + axe | `ShellLayoutPage` |
| Visual goldens (6 PNGs) | `regression/vitalia-fase1-shell-layout-5050/visual-goldens.spec.ts` | Playwright @project=visual | `ShellLayoutPage` |

### § 3.3 — POMs required

`vitalia/frontend/e2e/pages/ShellLayoutPage.ts`:

```ts
import type { Page, Locator } from '@playwright/test';

export class ShellLayoutPage {
  readonly page: Page;
  readonly topbar: Locator;
  readonly main: Locator;
  readonly valeriaSlot: Locator;
  readonly appSlot: Locator;
  readonly resizeHandle: Locator;
  readonly shellModeToggle: Locator;
  readonly skipLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.topbar = page.locator('[data-testid="topbar-global"]');
    this.main = page.locator('main#main-content:visible');
    this.valeriaSlot = page.locator('[data-testid="valeria-sidebar-slot"]:visible');
    this.appSlot = page.locator('[data-testid="app-panel-slot"]:visible');
    this.resizeHandle = page.locator('[data-resize-handle="true"]:visible');
    this.shellModeToggle = page.locator('[data-testid="shell-mode-toggle"]');
    this.skipLink = page.locator('a[href="#main-content"]');
  }

  async gotoShell(tenantId: string = 'acme-clinic') {
    await this.page.goto(`/${tenantId}`);
    await this.main.waitFor({ state: 'visible' });
  }

  async setShellModeViaStore(mode: 'agentic' | 'web') {
    await this.page.evaluate((m) => {
      const stateJson = localStorage.getItem('vitalia-shell-state');
      const parsed = stateJson ? JSON.parse(stateJson) : { state: {} };
      parsed.state = { ...parsed.state, shellMode: m };
      localStorage.setItem('vitalia-shell-state', JSON.stringify(parsed));
    }, mode);
    await this.page.reload();
    await this.main.waitFor({ state: 'visible' });
  }

  async setValeriaStateViaStore(state: 'collapsed' | 'rail' | 'full') {
    await this.page.evaluate((s) => {
      const stateJson = localStorage.getItem('vitalia-shell-state');
      const parsed = stateJson ? JSON.parse(stateJson) : { state: {} };
      parsed.state = { ...parsed.state, valeriaState: s };
      localStorage.setItem('vitalia-shell-state', JSON.stringify(parsed));
    }, state);
    await this.page.reload();
  }

  async dragResizeHandle(deltaX: number) {
    const box = await this.resizeHandle.boundingBox();
    if (!box) throw new Error('resize handle not visible');
    await this.page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await this.page.mouse.down();
    await this.page.mouse.move(box.x + box.width / 2 + deltaX, box.y + box.height / 2, { steps: 12 });
    await this.page.mouse.up();
  }

  async getValeriaWidth(): Promise<number> {
    const box = await this.valeriaSlot.boundingBox();
    return box?.width ?? 0;
  }

  async getPersistedSplit(): Promise<string | null> {
    return this.page.evaluate(() => localStorage.getItem('vitalia-shell-split-agentic'));
  }
}
```

### § 3.4 — Fixtures required

`vitalia/frontend/e2e/fixtures/shell-theme.fixture.ts` — sets initial `vitalia-theme=light|dark` + `vitalia-shell-state` in `addInitScript` before navigation (for visual goldens determinism).

Clerk auth fixture reused from existing `vitalia/frontend/e2e/auth.fixture.ts` (per `playwright-expert` SSoT pattern — F1-S3 deployment).

### § 3.5 — Visual goldens (6 PNGs)

Each PNG generated with `toHaveScreenshot()` against an `addInitScript` deterministic state + viewport pinned:

| Path | Viewport | Theme | State | Trigger |
|---|---|---|---|---|
| `e2e/__screenshots__/shell-layout-5050/agentic-1280x800-light.png` | 1280×800 | light | shellMode=agentic, valeriaState=full | first paint |
| `e2e/__screenshots__/shell-layout-5050/agentic-1280x800-dark.png` | 1280×800 | dark | idem | first paint |
| `e2e/__screenshots__/shell-layout-5050/agentic-rail-1280x800.png` | 1280×800 | light | shellMode=agentic, valeriaState=rail | setValeriaStateViaStore('rail') + reload |
| `e2e/__screenshots__/shell-layout-5050/web-1280x800-light.png` | 1280×800 | light | shellMode=web, valeriaState=rail | setShellModeViaStore('web') + reload |
| `e2e/__screenshots__/shell-layout-5050/web-1280x800-dark.png` | 1280×800 | dark | idem | setShellModeViaStore('web') + reload |
| `e2e/__screenshots__/shell-layout-5050/agentic-mobile-375x667.png` | 375×667 | light | shellMode=agentic | first paint mobile |

Tolerance `maxDiffPixelRatio: 0.001` per DC §9.4 + ADR-vitalia-003 protocol. Ratchet shrink-only post-ratificación.

### § 3.6 — `playwright_required: true` HARD

Per v4.1 + ui-story type: HARD requirement. All 4 functional specs + 6 visual goldens in scope. CI gate enforce post-merge.

### § 3.7 — `must_load_skills` enforceable (cf. 05-guidelines)

`frontend-expert` · `playwright-expert` · `tessl__react-patterns` · `tessl__shadcn-ui` · `tessl__tailwind` · `tessl__vitest` · `tessl__nextjs-app-router-modularization`.

### § 3.8 — `architectural_validation` (≥3 sub-tests)

1. **FSD-Lite boundary check** — `vitalia/frontend/src/__tests__/architecture/test-fsd-imports.test.ts` (existing extend) — assert `shell-organism/*` no importa de `features/*` (it's `components/shared` — chrome).
2. **Skip-link target presence** — `vitalia/frontend/src/__tests__/architecture/test-skip-link-target.test.ts` (NEW) — parsea ShellOrganismLayout, assert `id="main-content"` + `tabIndex={-1}` presente.
3. **Zustand store schema invariant** — `vitalia/frontend/src/stores/__tests__/shell-store.test.ts` (NEW) — assert exported types `ValeriaState`, `ShellMode`, `SHELL_STORAGE_KEY` match DC §6.1 contract.
4. **Cross-brand mirror grep** — `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` (NEW) — bash subprocess greps `nicolify/comunify/lupulo` para `ShellOrganismLayout|shell-store`, fail if matches > 0.
5. **No-default-export ratchet (heredado)** — extends existing allowlist (T-1..T-5 all named exports).

### § 3.9 — `scenario_coverage` 100%

Cada Gherkin scenario tiene ≥1 test ejecutable (functional spec O visual golden assertion). § 3.2 mapping completo. Sub-categorías mandatory v4.1 (§ 01-spec.md §2):

| Sub-cat | Aplica | Cobertura |
|---|---|---|
| race_condition | NO (`not_applicable_reason`: layout sin create/update, sólo render + browser side-effect local) | — |
| concurrent_users | NO (`not_applicable_reason`: layout root sin queries filtradas; tenant isolation upstream BE) | — |
| network_failure | NO (`not_applicable_reason`: layout puro sin fetch propio — F1-S5/S6 cubre cuando chat fetch llegue) | — |
| empty_state | NO (`not_applicable_reason`: slots placeholders por diseño; empty real es F1-S10 scope) | — |
| large_dataset | NO (`not_applicable_reason`: layout no renderiza listas) | — |
| accessibility | **SÍ** | SC-4 (keyboard nav + axe ruleset wcag2aa + skip-link reachable) |
| i18n | **SÍ** | SC-1 Spanish neutro microcopy assertion + tenant name "Sonrisa Plena · Lima centro" en TenantSwitcher |

### § 3.10 — `iteration` policy

- `max_iterations: 10`
- `on_fail`: fix targeted file (single file edit per iter, no scope creep).
- `cap_reached`: escalate Chris with `T-{n}-impl-log.md` cap_reached summary.

## § 4 — Architecture Fitness Impact

- Gates that must keep passing (allowlists shrink only):
  - `vitalia/frontend/src/__tests__/architecture/*.test.ts` (FSD-Lite + boundaries + no-default-export)
  - `vitalia/frontend/src/__tests__/architecture/test-page-padding.test.ts` (design tokens consumption)
  - Visual goldens ratchet (shrink-only — once ratificados, modificarlos requiere ratificación Chris explícita per `shell-mockup-per-component.md`)
- Allowlist updates expected: T-3 introduce `<main>` element 3 veces en ShellOrganismLayout (CSS-hidden branches). Existing arch test may flag — extender allowlist con justificación inline `// architect § 2.2 — mutually-exclusive viewport branches, only one main visible at a time`.
- New gate ADDED (T-7 architectural test): `test-no-cross-brand-shell-mirror.test.ts` (§ 3.8 item 4).

## § 5 — Migration Notes

N/A — FE only, no DB schema change, no BE migration.

## § 6 — capability YAML + modules/{m}.md Updates Required (post 2026-05 paradigma)

Post-merge tasks for `/pm-vitalia` (Fase F merge, parte de `07-merge.md` § 3):

1. **NEW** `vitalia/docs/product/capabilities/platform/shell.layout-5050.yaml`:

   ```yaml
   capability_id: shell.layout-5050
   module: platform
   status: live
   description: "Shell layout root with 2-panel split (agentic 50/50 + web rail mode), resizable, persistent state."
   verification:
     commands:
       - "cd vitalia/frontend && npx tsc --noEmit"
       - "cd vitalia/frontend && npx vitest run src/components/shared/shell-organism src/stores"
       - "cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase1-shell-layout-5050/"
     gherkin_evidence: "vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/06-audit/gherkin-matrix.md"
   blocks_stories:
     - vitalia-fase1-valeria-rail-history
     - vitalia-fase1-valeria-chat-skeleton
     - vitalia-fase1-ribbon-6-tabs
     - vitalia-fase1-routing-shell
     - vitalia-fase1-empty-states
   ```

2. **UPDATE** `vitalia/docs/product/modules/platform.md` auto-list section — adds `shell.layout-5050` entry post `make portfolio` o `reconcile_capabilities.py --brand vitalia`.

3. **UPDATE** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` §6.1 — change `valeriaState` default `'rail'` → `'full'` with commit msg citing this story's resolution (§ 2.5.1).

## § 7 — Research Notes (DATE-AWARE)

| Source | URL | Accessed | Library version | Knowledge cutoff note | Takeaway |
|---|---|---|---|---|---|
| react-resizable-panels npm | https://www.npmjs.com/package/react-resizable-panels | 2026-05-23 | v4.11.1 (published 8 days ago) | Topic researched live; Opus 4.7 cutoff Jan 2026 | Lib actively maintained, 2035 dependents. Adopted as canonical (§ 2.9). |
| Shadcn UI Resizable | https://ui.shadcn.com/docs/components/radix/resizable | 2026-05-23 | v4 API | post-cutoff (Shadcn updates 2026-Q1) | Shadcn wraps react-resizable-panels v4; same API. Pattern endorsed cross-FE community. |
| Next.js 16 Server Components | https://nextjs.org/docs (App Router) | 2026-05-23 | latest stable | partially post-cutoff | Server-first default; `'use client'` boundary semantics unchanged from cutoff-known. |
| Zustand persist | https://github.com/pmndrs/zustand/blob/main/docs/integrations/persisting-store-data.md | 2026-05-23 | v5.0.5 (installed) | pre-cutoff | `partialize` + `createJSONStorage(localStorage)` pattern unchanged. Existing F1-S3 `tenant-store.ts` matches. |

## § 8 — Open Questions for PM (escalations)

None blocking. Resolved unilaterally per architect authority:

- **Q1 Default valeriaState ambiguity** — Resolved as `'full'` (§ 2.5.1). PM `/pm-vitalia` updates DC §6.1 post-merge.
- **Q2 Resize lib decision** — Resolved option A `react-resizable-panels` (§ 2.9). Adds to package.json T-3.
- **Q3 ShellModeToggle mount location** — Resolved: overlay sibling de TopBarGlobal dentro ShellOrganismLayout, sin modificar TopBarGlobal (§ 2.7). F1-S5 puede revisitar.
- **Q4 Viewport edge case [768-1023] + state='full'** — Resolved via `useViewportGuard` one-way force a 'rail' (§ 2.6).
- **Q5 Triple `<main>` element pattern** — Resolved: mutually-exclusive Tailwind `md:hidden`/`md:block`/`md:grid` branches, only one visible per viewport (§ 2.2). Auditor enforced via Playwright `.locator(':visible')` count.
- **Q6 Visual goldens path** — Resolved: `e2e/__screenshots__/shell-layout-5050/` per § 3.5 (matches DC §9.2).
- **Q7 Mobile drawer trigger absent en F1-S4** — Resolved: deferred to F1-S5+ (burger button TODO). Mobile fallback `<main>` muestra solo AppPanelSlot — Valeria oculta hasta F1-S5 active el drawer trigger.

## § 9 — Drift surveillance / context-validator notes

- CONTEXT-BRIEF.md absent for this story (small ui-story, self-validated). No § 11 Faithfulness gaps to cite.
- All citations in this document point to files verified exist (read directly) or commands tested (find/grep). No fabricated paths.

