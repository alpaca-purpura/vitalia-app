---
story_id: vitalia-fase1-sub-tabs-line2
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.sub-tabs
state: done
last_modified: 2026-05-25T10:45:00Z
auditor_started_at: 2026-05-25T10:15:00Z
auditor_finished_at: 2026-05-25T10:35:00Z
audit_verdict: APPROVED
audit_iterations: 1
self_fix_iter: 1
self_fix_commits:
  - 7bcef820   # prettier auto-fix AppPanelSlot.test.tsx (whitelist #2)
phase: MERGED
merged_at: 2026-05-25T10:45:00Z
merged_by: /pm-vitalia
merge_artifact: 07-merge.md
capability_promoted: vitalia.shell-organism.sub-tabs
last_artifact: T-6-result.md
dev_team_started_at: 2026-05-25T09:35:00Z
dev_team_finished_at: 2026-05-25T10:12:00Z
dev_team_owner: claude-sonnet (via builder-frontend autonomous loop)
tickets_pushed: [T-1, T-2, T-3, T-4, T-5, T-6]
commits:
  T-1: 09152867
  T-2: 8350d912
  T-3: e2b68ad2
  T-4: 27fbf9db
  T-5: 76b66d62
  T-6: 33c2af59
  docs: a8bde800
phase_d_local_coverage: pending_audit  # 9 scenarios SC-1..SC-9 + visual goldens iter-1 deferred
ratified_by_chris: true
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-25T09:05:00Z
ratified_visual_iter: 1
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/mockups/sub-tabs.html
batch_1_decisions:
  Q1_ssot_path: extend_agent_catalog
  Q2_icons: emojis
  Q3_keyboard_nav: roving_tabindex
  Q4_height: min-h-[42px]
  Q5_null_agent: return_null
phase: READY_PACKAGE_CLOSED
autonomous_chain: true                  # Chris ratificó workflow autónomo /architect → /dev-team → /auditor → /pm-vitalia merge
chain_authorized_at: 2026-05-25T09:05:00Z
chain_authorized_by: chris
parallel_safe: false
priority: high
estimated_dev_days: 1
dependencies:
  hard: [vitalia-fase1-ribbon-6-tabs]
  soft: []
blocks_hard: [vitalia-fase1-routing-shell]
reuse_map_summary: "NEW · consume AGENT_SUBTABS whitelist · routing Next.js"
spawned_at: 2026-05-22
next_action: "DONE — story merged + archived. Next: F1-S9 vitalia-fase1-routing-shell (blocks_hard ya unblocked)."

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: sub-tabs   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S8 vitalia-fase1-sub-tabs-line2 — checkpoint

## Goal

`SubTabsBar` organismo: barra horizontal LÍNEA 2 debajo del Ribbon, dinámica per agente activo. Renderiza las sub-tabs del agente (4·5·4·2·4·3 según AGENT_SUBTABS whitelist) con active state per URL segment `[subtab]`. Color tint por agente (bg-agent-{name}-soft + text-agent-{name} cuando active).

## Anti-objetivos

- NO contenido sub-tab (eso es F1-S10 empty-states)
- NO N3-dyn workspaces (Fase 2)
- NO breadcrumb "vía Valeria" indicator (postponed)

## Scope verbatim

### § 1 — `AGENT_SUBTABS` whitelist

`vitalia/frontend/src/lib/agents/subtabs.ts` (per Design Contract § 7.2):

```ts
export interface SubTabMeta {
  id: string
  label: string
  icon: string
}

export const AGENT_SUBTABS: Record<AgentKey, readonly SubTabMeta[]> = {
  lisa: [
    { id: 'marca',      label: 'Marca',      icon: '🏥' },
    { id: 'doctores',   label: 'Doctores',   icon: '👨‍⚕️' },
    { id: 'servicios',  label: 'Servicios',  icon: '🩺' },
    { id: 'compliance', label: 'Compliance', icon: '🛡️' },
  ],
  lucas: [
    { id: 'lanzar',     label: 'Lanzar',     icon: '🚀' },
    { id: 'envuelo',    label: 'En vuelo',   icon: '📡' },
    { id: 'recursos',   label: 'Recursos',   icon: '📚' },
    { id: 'resultados', label: 'Resultados', icon: '📈' },
    { id: 'mercado',    label: 'Mercado',    icon: '🌍' },
  ],
  adrian: [
    { id: 'inbox',      label: 'Inbox',       icon: '💬' },
    { id: 'embudo',     label: 'Embudo',      icon: '🎯' },
    { id: 'outbound',   label: 'Outbound',    icon: '📣' },
    { id: 'propuestas', label: 'Propuestas',  icon: '💼' },
  ],
  valeria: [
    { id: 'agenda',    label: 'Agenda',    icon: '📆' },
    { id: 'pacientes', label: 'Pacientes', icon: '👥' },
  ],
  camila: [
    { id: 'voz',         label: 'Voz del paciente', icon: '🎤' },
    { id: 'reactivar',   label: 'Reactivar',         icon: '🪃' },
    { id: 'multiplicar', label: 'Multiplicar',       icon: '🤝' },
    { id: 'reputacion',  label: 'Reputación',        icon: '📊' },
  ],
  config: [
    { id: 'cuenta',     label: 'Mi cuenta',  icon: '🏢' },
    { id: 'conexiones', label: 'Conexiones', icon: '🔌' },
    { id: 'avanzado',   label: 'Avanzado',   icon: '🔬' },
  ],
} as const
```

### § 2 — `SubTabsBar` organismo

`vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx`:

```tsx
'use client'
import { usePathname, useRouter, useParams } from 'next/navigation'
import { SubTab } from './SubTab'
import { AGENT_SUBTABS } from '@/lib/agents/subtabs'
import { extractAgentFromPath, extractSubtabFromPath } from '@/lib/agents/routing'

export function SubTabsBar() {
  const pathname = usePathname()
  const router = useRouter()
  const params = useParams<{ tenantId: string }>()

  const activeAgent = extractAgentFromPath(pathname)
  const activeSubtab = extractSubtabFromPath(pathname)
  const subtabs = activeAgent ? AGENT_SUBTABS[activeAgent] : []

  if (!activeAgent || subtabs.length === 0) return null

  return (
    <nav
      role="tablist"
      aria-label={`Sub-secciones ${activeAgent}`}
      className="min-h-[42px] bg-card border-b border-border flex items-center px-4 gap-1 overflow-x-auto"
    >
      {subtabs.map(st => (
        <SubTab
          key={st.id}
          subtab={st}
          color={activeAgent}
          active={st.id === activeSubtab}
          onClick={() => router.push(`/${params.tenantId}/${activeAgent}/${st.id}`)}
        />
      ))}
    </nav>
  )
}
```

### § 3 — `SubTab` molécula

```tsx
const COLOR_ACTIVE_CLASS: Record<AgentKey, string> = {
  lisa:    'bg-agent-lisa-soft text-agent-lisa',
  lucas:   'bg-agent-lucas-soft text-foreground',
  adrian:  'bg-agent-adrian-soft text-agent-adrian',
  valeria: 'bg-agent-valeria-soft text-agent-valeria',
  camila:  'bg-agent-camila-soft text-agent-camila',
  config:  'bg-muted text-foreground',
}

export function SubTab({ subtab, color, active, onClick }: SubTabProps) {
  return (
    <button
      role="tab"
      aria-selected={active}
      data-testid={`sub-tab-${subtab.id}`}
      data-color={color}
      onClick={onClick}
      className={cn(
        'px-3 py-1.5 rounded-md text-sm font-medium flex items-center gap-1.5 whitespace-nowrap transition-all',
        active ? cn('font-semibold', COLOR_ACTIVE_CLASS[color]) : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      )}
    >
      <span>{subtab.icon}</span>
      <span>{subtab.label}</span>
    </button>
  )
}
```

### § 4 — Replace SubTabsBarSlot in AppPanel

Update F1-S7 `AppPanelSlot.tsx` para usar `<SubTabsBar />` real.

### § 5 — `extractSubtabFromPath` helper

```ts
export function extractSubtabFromPath(pathname: string): string | null {
  const segments = pathname.split('/').filter(Boolean)
  return segments[2] || null  // /{tenant}/{agent}/{subtab}/...
}
```

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | SubTabsBar visible debajo del Ribbon altura min 42px |
| AC-2 | Sub-tabs dinámicas per active agent (4 Lisa · 5 Lucas · 4 Adrián · 2 Valeria · 4 Camila · 3 Config) |
| AC-3 | Active subtab con bg-agent-{color}-soft + text-agent-{color} |
| AC-4 | Click subtab → router.push `/{tenant}/{agent}/{subtab}` |
| AC-5 | Si no hay activeAgent (404 o redirect) → SubTabsBar oculto |
| AC-6 | a11y: `role="tablist"` + `role="tab"` + `aria-selected` |
| AC-7 | Visual golden 6 variants (per agente) light + dark |
| AC-8 | Horizontal scroll viewport estrecho |
| AC-9 | Vitest unit + Playwright functional |

## Gherkin scenarios

### Scenario 1 — happy nav

**Given:** Usuario en `/{tenant}/lisa/marca`, sub-tabs Lisa visibles

**When:** Click "Doctores"

**Then:**
- router.push `/{tenant}/lisa/doctores`
- Active subtab cambia a "Doctores" con bg-agent-lisa-soft
- Otras subtabs vuelven a muted

### Scenario 2 — agent change resets subtabs

**Given:** Usuario en `/{tenant}/lisa/doctores`

**When:** Click Ribbon Lucas

**Then:**
- router.push `/{tenant}/lucas/lanzar`
- SubTabsBar re-renders con sub-tabs Lucas (5 items)
- Active "Lanzar" (default)

### Scenario 3 — invalid subtab

**Given:** URL manual `/{tenant}/lisa/inexistente`

**When:** Página carga

**Then:**
- Ningún SubTab active
- (F1-S9 routing maneja redirect a default subtab — placeholder por ahora)

### Scenario 4 — keyboard a11y

**Given:** Focus en SubTab "Marca"

**When:** Arrow Right

**Then:** Focus a "Doctores" (siguiente)

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/lib/agents/subtabs.ts` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx` | NEW |
| `vitalia/frontend/src/lib/agents/routing.ts` | MODIFY (add extractSubtabFromPath) |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | MODIFY (compose SubTabsBar) |
| `vitalia/frontend/e2e/shell-organism/sub-tabs.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-{lisa,lucas,adrian,valeria,camila,config}-{light,dark}.png` | NEW (12 goldens) |

## Próximo paso post-done

F1-S9 routing-shell consolida App Router pages + redirects + 404 handling.

## Ready package artifacts (architect closure 2026-05-25T09:25:00Z)

- `03-arch.md` — surface BE/FE/AGENTIC contracts (only FE surface aplicable — single architect-frontend output)
- `04-validators.yaml` — 5-cat validators (non_functional + functional 9 SC + visual 13 goldens + agentic_eval N/A + architectural_validation)
- `05-guidelines.md` — files in scope + skills + rules + TDD strategy + commit protocol
- `06-tickets.yaml` — 6 tickets atómicos (T-1..T-6) DAG estricto · 13h total · ZERO Opus (FE no-agentic puro) · gherkin_coverage 100% (9/9 SC mapped) · validator_ids citados verbatim
