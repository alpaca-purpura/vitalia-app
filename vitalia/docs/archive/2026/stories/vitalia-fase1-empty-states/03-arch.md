<!-- voseo-allowed: technical documentation citing rule glosario verbatim -->
---
story_id: vitalia-fase1-empty-states
brand: vitalia
phase: fase-1
story_type: ui-story
surfaces: [FE]
architect_run_on: 2026-05-26
architect_iter: 1
spec_anchor: vitalia/docs/product/stories/vitalia-fase1-empty-states/01-spec.md
checkpoint_state: refined → ready (transition al cierre del paquete)
predecessor_arch_ref: vitalia/docs/archive/2026/stories/vitalia-fase1-routing-shell/03-arch-fe.md
ssot_consumed:
  - vitalia/frontend/src/lib/agent-catalog.ts (RIBBON_SUBTABS · 22 sub-tabs · READ-ONLY)
  - vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md (atomic layers + tokens)
mockup_ratified:
  - empty-states-grid.html
  - lisa-servicios-placeholder.html
  - adrian-embudo-placeholder.html
  - adrian-inbox-placeholder.html
  - camila-voz-placeholder.html
  - valeria-agenda-placeholder.html
  - config-conexiones-placeholder.html
---

# F1-S10 vitalia-fase1-empty-states — 03-arch.md

> Single-shot full-stack architect run. FE only (NO BE, NO agentic). Mock-only placeholder cierre Fase 1.

---

## § 0 — Context Summary

- **Story**: `vitalia-fase1-empty-states` (F1-S10) — última story Fase 1.
- **Architect run on**: 2026-05-26 (date-aware Step 0 captured: `2026-05-26 / 2026 / 2026-05`).
- **Modules touched**: shell-organism (vitalia FE feature features/{lisa,lucas,adrian,valeria,camila,config}, shared/shell-organism, app router page).
- **Surface → builder → auditor mapping** (PM consumirá esta tabla para spawn):

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/**` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/features/{lisa,lucas,adrian,valeria,camila,config}/components/**` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/**` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-empty-states/**` (Playwright suite) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/__screenshots__/visual/empty-states/**` (~70 PNG) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

No agentic surface · no BE surface · no engine `core/luana-core-*/` edits.

- **Skills consulted**:
  - `frontend-expert` → FSD-Lite slots + Server-First default + cn() utility + Atomic Design layers verbatim del Design Contract.
  - `brand-expert` (lookup) → Vitalia agent slugs + colors verbatim de `agent-catalog.ts` (no edit, READ-ONLY consume).
  - `playwright-expert` (deferred a auditor — invoca al construir POMs + fixtures en T-10).
  - Anti-duplication grep (Step audit) → ningún cross-brand mirror; sales_studio parity es **pattern conceptual**, no import (componentes nacen brand-local en `vitalia/frontend/src/features/adrian/components/inbox/`).
- **CONTEXT-BRIEF source**: spec compacto (01-spec.md ratificado v2 batch 1+2+3) + predecessor F1-S9 arch + mockups ratificados. NO CONTEXT-BRIEF.md generado (story compacta, /architect leyó spec directo).
- **capability YAML files affected** (post-merge updates required):
  - `vitalia/docs/product/capabilities/shell-organism/empty-states.yaml` (NEW) — capability `shell.empty-states` listing `subtab_dispatcher`, `placeholder_special_6`, `placeholder_generic_16`, `takeover_per_conversation_visual`.
  - `vitalia/docs/product/modules/shell-organism.md` (MODIFY auto-list) — agrega entry para esta capability + ciérre Fase 1.
- **Architecture gates that must keep passing**:
  - `vitalia/frontend/src/__tests__/architecture/test_fsd_boundaries.test.ts` (allowlist shrink-only)
  - `vitalia/frontend/src/__tests__/architecture/test_no_cross_brand_mirror.test.ts` (ban import other brand)
  - `vitalia/frontend/src/__tests__/architecture/test_subtab_content_uses_ribbon_subtabs_ssot.test.ts` (NEW — enforce SubTabContent dispatcher consume `RIBBON_SUBTABS`)
  - `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_subtab_keys.test.ts` (NEW — ban literal `'lisa.servicios'` outside dispatcher)
  - `vitalia/frontend/src/__tests__/architecture/test_no_phi_real_data.test.ts` (NEW — placeholders use mock-only, no PHI real)

### Existing systems audit (NO NEW LAYER rule)

| Source | Evidence |
|---|---|
| § 7 CONTEXT-BRIEF | N/A (no brief generated; spec 909 LOC ratificado cubre) |
| Self-run grep | `find vitalia/frontend/src/components/shared/shell-organism -type f` retorna shipped F1-S5..S9 (TopBarGlobal, Ribbon, ValeriaRail, SubTabsBar, layouts) — NO EmptyState / SubTabContent / placeholder generic existente |
| Self-run grep | `find vitalia/frontend/src/features/{adrian,valeria}/components -path "*inbox*"` o `*agenda*` retorna vacío post-shipped F1-S5..S9 — surface NEW |
| Cross-brand mirror check | `for B in nicolify comunify lupulo; do find ${WS}/$B/frontend/src -path "*shell-organism/SubTabContent*"; done` retorna vacío. Patrón único a vitalia (otras brands no tienen ribbon × sub-tab nested). NO promotion gate requerido. |
| `closer-studio` sales_studio shipped | `ap_sales_agent/frontend/src/features/closer-studio/components/inbox/` referenciado verbatim por spec § 3.2 como **pattern conceptual**. NUNCA import cross-brand — Vitalia construye su propio shape brand-local. Spec ratificó "lift candidate cross-brand futuro" si Fase 2 valida. |

**Decisión:** NEW (last resort justificado) — ninguno de los componentes propuestos existe; shell-organism Fase 1 paradigm es vitalia-único hoy. Si Fase 2 valida shape inbox/agenda en otras brands → `/pm-luana` promotion candidate a `core/luana-core-ui/`.

---

## § 1 — Surfaces involved

| Surface | Status | Builder | Notes |
|---|---|---|---|
| FE — `vitalia/frontend/src/**` | YES (single surface) | `builder-frontend` Sonnet | NEW moléculas/organismos/page MODIFY |
| BE — `vitalia/backend/src/**` | NO | — | F1-S10 mock-only, no API call |
| Agentic — `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/**` | NO | — | sin LangGraph state, sin prompt, sin tool |
| Engine — `core/luana-core-*/src/**` | NO | — | sin edit engine |

---

## § 2 — File tree exacto (paths brand-scoped)

```
vitalia/
├── frontend/
│   └── src/
│       ├── components/
│       │   └── shared/
│       │       └── shell-organism/
│       │           ├── EmptyState.tsx                              NEW · molécula generic
│       │           ├── PlaceholderCard.tsx                          NEW · molécula card status
│       │           ├── SubTabHeader.tsx                             NEW · h2 + descripción + CTA opcional
│       │           ├── StatusDot.tsx                                NEW · color dot verde/amarillo/gris
│       │           ├── TogglePill.tsx                               NEW · wrapper Shadcn Tabs styled pill
│       │           └── SubTabContent.tsx                            NEW · organismo dispatcher
│       │
│       ├── features/
│       │   ├── lisa/components/placeholders/
│       │   │   ├── MarcaPlaceholder.tsx                             NEW · genérico
│       │   │   ├── DoctoresPlaceholder.tsx                          NEW · genérico
│       │   │   ├── ServiciosPlaceholder.tsx                         NEW · ★ especial (toggle Catálogo|Escalera + 5 cards)
│       │   │   └── CompliancePlaceholder.tsx                        NEW · genérico
│       │   │
│       │   ├── lucas/components/placeholders/
│       │   │   ├── LanzarPlaceholder.tsx                            NEW · genérico
│       │   │   ├── EnvueloPlaceholder.tsx                           NEW · genérico
│       │   │   ├── RecursosPlaceholder.tsx                          NEW · genérico
│       │   │   ├── ResultadosPlaceholder.tsx                        NEW · genérico
│       │   │   └── MercadoPlaceholder.tsx                           NEW · genérico
│       │   │
│       │   ├── adrian/components/
│       │   │   ├── inbox/
│       │   │   │   ├── CampaignTag.tsx                              NEW · molécula pill clickable
│       │   │   │   ├── ConversationItem.tsx                         NEW · molécula con YouChip inline
│       │   │   │   ├── MessageBubble.tsx                            NEW · molécula in/out variants
│       │   │   │   ├── MessageInput.tsx                             NEW · molécula state dual
│       │   │   │   ├── ContactSidebar.tsx                           NEW · molécula PHI masking visual
│       │   │   │   ├── ThreadHeader.tsx                             NEW · molécula 2 estados A/B
│       │   │   │   └── TakeoverBanner.tsx                           NEW · molécula banner amarillo
│       │   │   └── placeholders/
│       │   │       ├── InboxPlaceholder.tsx                        NEW · ★ especial (3-col + takeover local state)
│       │   │       ├── EmbudoPlaceholder.tsx                       NEW · ★ especial (Kanban 6 cols + toggle)
│       │   │       ├── OutboundPlaceholder.tsx                     NEW · genérico
│       │   │       └── PropuestasPlaceholder.tsx                   NEW · genérico
│       │   │
│       │   ├── valeria/components/
│       │   │   ├── agenda/
│       │   │   │   ├── AgendaToolbar.tsx                            NEW · molécula period nav + CTA dropdown
│       │   │   │   ├── AgendaFilters.tsx                            NEW · molécula chips disabled
│       │   │   │   ├── AgendaDayHeader.tsx                          NEW · molécula day cell + today highlight
│       │   │   │   ├── AgendaSlot.tsx                               NEW · molécula slot rico (paciente·service·doctor·origin·status)
│       │   │   │   └── AgendaSummaryFooter.tsx                     NEW · molécula leyenda + Adrián+Lucas summary
│       │   │   └── placeholders/
│       │   │       ├── AgendaPlaceholder.tsx                       NEW · ★ especial (10 slots mock + toolbar + filters + summary)
│       │   │       └── PacientesPlaceholder.tsx                    NEW · genérico
│       │   │
│       │   ├── camila/components/placeholders/
│       │   │   ├── VozPlaceholder.tsx                              NEW · ★ especial (3-modos + 3 cards stats + footer aclarado)
│       │   │   ├── ReactivarPlaceholder.tsx                        NEW · genérico
│       │   │   ├── MultiplicarPlaceholder.tsx                      NEW · genérico
│       │   │   └── ReputacionPlaceholder.tsx                       NEW · genérico
│       │   │
│       │   └── config/components/placeholders/
│       │       ├── CuentaPlaceholder.tsx                            NEW · genérico
│       │       ├── ConexionesPlaceholder.tsx                        NEW · ★ especial (grid 6 categorías)
│       │       └── AvanzadoPlaceholder.tsx                          NEW · genérico
│       │
│       ├── app/
│       │   └── [tenantId]/
│       │       └── (shell-organism)/
│       │           └── [agent]/
│       │               └── [subtab]/
│       │                   └── page.tsx                            MODIFY · replace placeholder "TBD F1-S10" con <SubTabContent agent subtab/>
│       │
│       └── __tests__/
│           └── architecture/
│               ├── test_subtab_content_uses_ribbon_subtabs_ssot.test.ts   NEW · arch fitness
│               ├── test_no_hardcoded_subtab_keys.test.ts                  NEW · arch fitness
│               └── test_no_phi_real_data.test.ts                          NEW · arch fitness
│
└── frontend/
    ├── e2e/
    │   ├── pages/
    │   │   ├── ShellOrganismPage.ts                                NEW · POM (genérico 22 subtabs)
    │   │   ├── AdrianInboxPage.ts                                  NEW · POM (takeover UX state A/B)
    │   │   └── ValeriaAgendaPage.ts                                NEW · POM (toolbar + filters + grid)
    │   │
    │   ├── regression/vitalia-fase1-empty-states/
    │   │   ├── sc-01-navegacion-22-subtabs.spec.ts                NEW
    │   │   ├── sc-02-lisa-servicios.spec.ts                       NEW
    │   │   ├── sc-03-adrian-embudo.spec.ts                        NEW
    │   │   ├── sc-04-valeria-agenda.spec.ts                       NEW
    │   │   ├── sc-04bis-adrian-inbox.spec.ts                      NEW · takeover UX A↔B + sidebar toggle
    │   │   ├── sc-05-subtab-invalido.spec.ts                      NEW
    │   │   ├── sc-06-edge-no-shell-remount.spec.ts                NEW
    │   │   ├── sc-07-adversarial-xss.spec.ts                      NEW
    │   │   ├── sc-08-empty-states-genericos.spec.ts               NEW · parametrizado 16 genéricos
    │   │   ├── sc-09-a11y.spec.ts                                 NEW · axe wcag2aa
    │   │   └── sc-10-i18n.spec.ts                                 NEW · spanish neutro + tenant_locale
    │   │
    │   └── __screenshots__/visual/empty-states/
    │       ├── 22-subtabs-light/*.png                             NEW · 22 golden snapshots light
    │       ├── 22-subtabs-dark/*.png                              NEW · 22 golden snapshots dark
    │       ├── inbox-state-A-adrian-{light,dark}.png              NEW · 2 takeover state A
    │       ├── inbox-state-B-human-{light,dark}.png               NEW · 2 takeover state B
    │       └── responsive/{mobile,tablet,desktop}-*.png           NEW · ~24 responsive
```

**Conteo NEW**:
- moléculas shell-organism shared: 6
- moléculas inbox parity: 7
- moléculas agenda enriquecida: 5
- moléculas brand-local: 18 (= sub-set de las 30 totales — el resto son placeholders genéricos)
- organismos placeholders (especiales): 6
- placeholders genéricos: 16
- page MODIFY: 1
- arch tests NEW: 3
- POMs NEW: 3
- specs Playwright NEW: 11
- visual goldens: ~70 PNG

---

## § 3 — Atomic Design Layers

### § 3.1 — Átomos consumidos (READ-ONLY)

| Átomo | Fuente | Variante |
|---|---|---|
| `Button` | `vitalia/frontend/src/components/ui/button.tsx` | default · ghost · outline · destructive |
| `Tabs` | `vitalia/frontend/src/components/ui/tabs.tsx` | base — TogglePill lo wraps con clases styled |
| `Badge` | `vitalia/frontend/src/components/ui/badge.tsx` | secondary · outline |
| `Card` | `vitalia/frontend/src/components/ui/card.tsx` | default |
| `Input` | `vitalia/frontend/src/components/ui/input.tsx` | (ContactSidebar PHI masked display) |
| `Textarea` | `vitalia/frontend/src/components/ui/textarea.tsx` | (MessageInput) |
| `cn()` util | `vitalia/frontend/src/lib/utils.ts` | Tailwind merge mandatory |

### § 3.2 — 17 NEW moléculas

| # | Molécula | Path | Owner agent slice | Responsabilidad |
|---|---|---|---|---|
| 1 | `EmptyState` | `components/shared/shell-organism/EmptyState.tsx` | shared | icon emoji + h3 + descripción + opcional CTA · used by 16 genéricos |
| 2 | `PlaceholderCard` | `components/shared/shell-organism/PlaceholderCard.tsx` | shared | Card con icon + h3 + desc + StatusDot |
| 3 | `SubTabHeader` | `components/shared/shell-organism/SubTabHeader.tsx` | shared | h2 + descripción contextual + spacer + CTA opcional right-aligned |
| 4 | `StatusDot` | `components/shared/shell-organism/StatusDot.tsx` | shared | indicador color (`bg-green-500`/`bg-yellow-500`/`bg-gray-400`) reusado por PlaceholderCard + AgendaSlot status |
| 5 | `TogglePill` | `components/shared/shell-organism/TogglePill.tsx` | shared | wrapper de `<Tabs>` Shadcn con `data-testid` + styled pill (rounded-full background con border) |
| 6 | `CampaignTag` | `features/adrian/components/inbox/CampaignTag.tsx` | adrian | pill "📣 {campaignName}" trunca >30 chars + tooltip + href `/{tenantId}/lucas/lanzar?campaign={id}` (NO navega F1-S10) |
| 7 | `ConversationItem` | `features/adrian/components/inbox/ConversationItem.tsx` | adrian | avatar initials + temp-dot + stage-badge + channel-abbr + handler_mode border-l verde + YouChip inline |
| 8 | `MessageBubble` | `features/adrian/components/inbox/MessageBubble.tsx` | adrian | in/out variants + timestamp + sender attribution |
| 9 | `MessageInput` | `features/adrian/components/inbox/MessageInput.tsx` | adrian | textarea + send btn + attach. State dual (disabled state A / enabled state B con auto-focus). F1-S10: solo visual, sin RHF |
| 10 | `ContactSidebar` | `features/adrian/components/inbox/ContactSidebar.tsx` | adrian | header paciente + PHI masking visual (+51 9** ***-4321 / m***@gmail.com) + 🔓 botones decorativos + origen CampaignTag + tags + 3 action buttons (Agendar/Historial/Pasar a embudo) |
| 11 | `ThreadHeader` (★ takeover UX) | `features/adrian/components/inbox/ThreadHeader.tsx` | adrian | 2 estados: A (Adrián maneja) = avatar+nombre+canal + chip "🤖 Adrián decidiendo" + botón "✋ Tomar el control" + × sidebar. B (usuario) = avatar+nombre+canal solo (banner separado debajo) |
| 12 | `TakeoverBanner` (★) | `features/adrian/components/inbox/TakeoverBanner.tsx` | adrian | banner amarillo `border-l-4 border-yellow-500 bg-yellow-50/30` con icon ⚡ + título + meta + botón "🤖 Devolver a Adrián" |
| 13 | `AgendaToolbar` | `features/valeria/components/agenda/AgendaToolbar.tsx` | valeria | period nav (‹ "Semana 26-31 May 2026" ›) + toggle Día/Semana/Mes + "📅 Hoy" + CTA "+ Crear cita ▾" dropdown 3 origins |
| 14 | `AgendaFilters` | `features/valeria/components/agenda/AgendaFilters.tsx` | valeria | 6 chips visuales disabled (search · doctor · especialidad · status pago · no-show · walk-in). F1-S10 disabled; F2-S1 cablea Zustand |
| 15 | `AgendaDayHeader` | `features/valeria/components/agenda/AgendaDayHeader.tsx` | valeria | cell header con label corto (Lun) + day-num grande + `today` highlight color agent-valeria/agent-adrian |
| 16 | `AgendaSlot` | `features/valeria/components/agenda/AgendaSlot.tsx` | valeria | paciente + service + doctor + origin icon (🚶/📞/✉/✋) + status pill (✓ PAG / 30% / SIN PAGO / ⚠ NO-SHOW) · 4 variants color border-left |
| 17 | `AgendaSummaryFooter` | `features/valeria/components/agenda/AgendaSummaryFooter.tsx` | valeria | leyenda 4 status + texto "Adrián propuso N turnos hoy · M sin pago · Lucas: K leads listos" |

### § 3.3 — 8 NEW organismos (= placeholders especiales) + 16 placeholders genéricos

| # | Organismo | Path | Composición | Estado local |
|---|---|---|---|---|
| 1 | `SubTabContent` (dispatcher) | `components/shared/shell-organism/SubTabContent.tsx` | mapa `PLACEHOLDER_MAP: Record<\`${RibbonTabSlug}.${string}\`, ComponentType>` → mounted placeholder o `<EmptyState>` fallback. Lee `SubTabHeader` arriba | none (puramente declarativo) |
| 2 | `LisaServiciosPlaceholder` | `features/lisa/components/placeholders/ServiciosPlaceholder.tsx` | `TogglePill` (Catálogo\|Escalera default Catálogo) + grid 5 `PlaceholderCard` (4 services + 1 CTA "Nuevo tratamiento") | `useState<'catalogo'\|'escalera'>('catalogo')` |
| 3 | `AdrianEmbudoPlaceholder` | `features/adrian/components/placeholders/EmbudoPlaceholder.tsx` | `TogglePill` (Kanban\|Lista) + 6 columnas Pipeline. Cada col: header (emoji + label + count + value) + 3 lead cards mock (`{name} · ${money} · "hace {x}"`) | `useState<'kanban'\|'lista'>('kanban')` |
| 4 | `AdrianInboxPlaceholder` (★ enriquecido) | `features/adrian/components/placeholders/InboxPlaceholder.tsx` | `TogglePill` 3-modos + grid 3-col `320px / flex-1 / 288px`: ConversationList (5 `ConversationItem` mock con campañas/temp/stage/channel/1 human-handled YouChip) · ConversationThread (`ThreadHeader` 2-state + 4 `MessageBubble` + `MessageInput` dual + `TakeoverBanner` conditional) · `ContactSidebar` colapsable | `useState<'decide'\|'consulta'\|'manual'>('decide')` (global, decorativo) + `useState<boolean>(true)` sidebarOpen + `useState<'bot'\|'human'>('bot')` localTakeover (estado A/B) |
| 5 | `CamilaVozPlaceholder` | `features/camila/components/placeholders/VozPlaceholder.tsx` | `TogglePill` 3-modos + grid 3 `PlaceholderCard` (Entrante 12 / Curaduría 4 / Ciclos activos 47 con descripciones aclaradas batch 2) + footer aclarado | `useState<'decide'\|'curaduria'\|'manual'>('decide')` (decorativo) |
| 6 | `ValeriaAgendaPlaceholder` (★ enriquecido) | `features/valeria/components/placeholders/AgendaPlaceholder.tsx` | `AgendaToolbar` + `AgendaFilters` + grid 6 days × 8 hours rendered como: 1 row `AgendaDayHeader` × 6 + 8 rows × 6 cells (con 10 `AgendaSlot` mock + 6 cells lunch-time pattern stripe) + `AgendaSummaryFooter` | `useState<'dia'\|'semana'\|'mes'>('semana')` (decorativo) |
| 7 | `ConfigConexionesPlaceholder` | `features/config/components/placeholders/ConexionesPlaceholder.tsx` | grid 3×2 (6 categorías): Marketing · Mensajería · Pagos · Calendarios · Presencia · Técnicas (cada uno con icon + label + descripción 2 providers) | none |
| 8 | (`SubTabContent` ya contado arriba como #1) | — | — | — |

**16 placeholders genéricos** = wrapper de `EmptyState` con icon + label de `RIBBON_SUBTABS[agent].find(s => s.id === subtab)` + descripción uniforme "Vista placeholder — el contenido real se cablea en Fase 2." Cada uno es 8-15 LOC.

### § 3.4 — Template / page MODIFY

| Path | Acción | Cambio exacto |
|---|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | MODIFY | Reemplazar placeholder body "TBD F1-S10" (F1-S9 cementó) por `<SubTabContent agent={params.agent} subtab={params.subtab} />` |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.tsx` | NO TOCAR | F1-S9 ya redirige a defaultSubtab |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx` | NO TOCAR | F1-S9 cementado |

---

## § 4 — `SubTabContent` dispatcher pattern (type-safe consume SSoT)

### § 4.1 — Type-safe key derivation (consume `RIBBON_SUBTABS`)

`SubTabContent.tsx` MUST derivar el tipo de las keys del PLACEHOLDER_MAP a partir del SSoT. Type-only — sin import runtime de `RIBBON_SUBTABS` para construir keys.

```tsx
import type { RibbonTabSlug, SubTabMeta } from '@/lib/agent-catalog'
import { RIBBON_SUBTABS, isValidAgent, isValidSubtab } from '@/lib/agent-catalog'
import { SubTabHeader } from '@/components/shared/shell-organism/SubTabHeader'
import { EmptyState } from '@/components/shared/shell-organism/EmptyState'

// 22 placeholder imports …
import { ServiciosPlaceholder as LisaServiciosPlaceholder } from '@/features/lisa/components/placeholders/ServiciosPlaceholder'
import { InboxPlaceholder as AdrianInboxPlaceholder } from '@/features/adrian/components/placeholders/InboxPlaceholder'
// … etc.

type SubTabKey = `${RibbonTabSlug}.${string}` // mateo key never reaches dispatcher (RIBBON_SUBTABS.mateo: []; isValidAgent('mateo') === false)

const PLACEHOLDER_MAP = {
  'lisa.marca':          LisaMarcaPlaceholder,
  'lisa.doctores':       LisaDoctoresPlaceholder,
  'lisa.servicios':      LisaServiciosPlaceholder,
  'lisa.compliance':     LisaCompliancePlaceholder,
  'lucas.lanzar':        LucasLanzarPlaceholder,
  'lucas.envuelo':       LucasEnvueloPlaceholder,
  'lucas.recursos':      LucasRecursosPlaceholder,
  'lucas.resultados':    LucasResultadosPlaceholder,
  'lucas.mercado':       LucasMercadoPlaceholder,
  'adrian.inbox':        AdrianInboxPlaceholder,
  'adrian.embudo':       AdrianEmbudoPlaceholder,
  'adrian.outbound':     AdrianOutboundPlaceholder,
  'adrian.propuestas':   AdrianPropuestasPlaceholder,
  'valeria.agenda':      ValeriaAgendaPlaceholder,
  'valeria.pacientes':   ValeriaPacientesPlaceholder,
  'camila.voz':          CamilaVozPlaceholder,
  'camila.reactivar':    CamilaReactivarPlaceholder,
  'camila.multiplicar':  CamilaMultiplicarPlaceholder,
  'camila.reputacion':   CamilaReputacionPlaceholder,
  'config.cuenta':       ConfigCuentaPlaceholder,
  'config.conexiones':   ConfigConexionesPlaceholder,
  'config.avanzado':     ConfigAvanzadoPlaceholder,
} as const satisfies Record<SubTabKey, React.ComponentType>

interface Props {
  agent: RibbonTabSlug
  subtab: string
}

export function SubTabContent({ agent, subtab }: Props) {
  const subtabMeta = RIBBON_SUBTABS[agent].find(s => s.id === subtab)
  const key = `${agent}.${subtab}` as SubTabKey
  const Placeholder = PLACEHOLDER_MAP[key]

  return (
    <div className="p-7" data-testid={`subtab-content-${agent}-${subtab}`}>
      <SubTabHeader agent={agent} subtab={subtab} meta={subtabMeta} />
      {Placeholder ? (
        <Placeholder />
      ) : (
        <EmptyState
          icon={subtabMeta?.icon ?? '📄'}
          title={`${subtabMeta?.label ?? subtab} — próximamente`}
          description="Esta vista vive acá. Cuando Fase 2 implemente esta sub-tab, lo que ves cambiará."
        />
      )}
    </div>
  )
}
```

### § 4.2 — Architecture invariant (test enforced)

`test_subtab_content_uses_ribbon_subtabs_ssot.test.ts` (NEW arch fitness):

```ts
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { RIBBON_SUBTABS, AGENT_RIBBON_ORDER } from '@/lib/agent-catalog'

describe('SubTabContent arch fitness', () => {
  it('PLACEHOLDER_MAP contiene exactamente las 22 keys de RIBBON_SUBTABS', () => {
    const expectedKeys = AGENT_RIBBON_ORDER.flatMap(agent =>
      RIBBON_SUBTABS[agent].map(s => `${agent}.${s.id}`)
    )
    const source = readFileSync(__dirname + '/../../components/shared/shell-organism/SubTabContent.tsx', 'utf-8')
    for (const key of expectedKeys) {
      expect(source).toContain(`'${key}':`)
    }
    expect(expectedKeys).toHaveLength(22)
  })

  it('no hay PLACEHOLDER_MAP key para mateo (RIBBON_SUBTABS.mateo === [])', () => {
    const source = readFileSync(__dirname + '/../../components/shared/shell-organism/SubTabContent.tsx', 'utf-8')
    expect(source).not.toMatch(/'mateo\./)
  })

  it('SubTabContent importa RIBBON_SUBTABS (consume SSoT)', () => {
    const source = readFileSync(__dirname + '/../../components/shared/shell-organism/SubTabContent.tsx', 'utf-8')
    expect(source).toMatch(/from ['"]@\/lib\/agent-catalog['"]/)
    expect(source).toContain('RIBBON_SUBTABS')
  })
})
```

### § 4.3 — `test_no_hardcoded_subtab_keys.test.ts` (ban literal outside dispatcher)

```ts
import { describe, it, expect } from 'vitest'
import { execSync } from 'child_process'

describe('subtab key hardcoding ratchet', () => {
  it('literal "lisa.servicios" etc no aparece fuera del dispatcher + tests', () => {
    const allowlist = [
      'components/shared/shell-organism/SubTabContent.tsx',
      '__tests__/',
      'e2e/',
    ]
    const result = execSync(
      `grep -rln "['\\"]\\(lisa\\|lucas\\|adrian\\|valeria\\|camila\\|config\\)\\.[a-z]" vitalia/frontend/src/ || true`,
      { encoding: 'utf-8' }
    )
    const violations = result.split('\n').filter(p => p && !allowlist.some(a => p.includes(a)))
    expect(violations).toEqual([])
  })
})
```

---

## § 5 — Mock data strategy

**Principio:** Cada placeholder declara su mock data como `const`s top-of-file. Cero fetch APIs Fase 1. Tipos Zod opcionales para mock structure (mejora autocomplete + valida shape vs futuras DTOs F2).

### § 5.1 — Estructuras mock (top-of-file por placeholder especial)

**`AdrianInboxPlaceholder` mock:**

```tsx
const INBOX_CONVERSATIONS = [
  {
    id: 'conv-1', patient: 'María González', preview: 'Hola, vi su anuncio sobre limp...',
    elapsed: 'hace 2 min', temp: 'hot', channel: 'WA', stage: 'Calificando',
    selected: true, handler_mode: 'bot', campaign: 'Limpieza-PE',
  },
  {
    id: 'conv-2', patient: 'Carlos Pérez', preview: '¿tienen turno mañana?',
    elapsed: 'hace 8 min', temp: 'warm', channel: 'IG', stage: 'Nuevo',
    selected: false, handler_mode: 'human', campaign: null,  // ★ human-handled border-l verde + YouChip
  },
  {
    id: 'conv-3', patient: 'Lucía Ramos', preview: 'Gracias por la info!',
    elapsed: 'hace 1 h', temp: 'cold', channel: 'WA', stage: 'Cerrando',
    selected: false, handler_mode: 'bot', campaign: 'Blanqueamiento',
  },
  {
    id: 'conv-4', patient: 'Diego Flores', preview: '¿el blanqueamiento incluye...?',
    elapsed: 'hace 3 h', temp: 'warm', channel: 'WA', stage: 'Negociando',
    selected: false, handler_mode: 'bot', campaign: null,
  },
  {
    id: 'conv-5', patient: 'Sofía M.', preview: 'Confirmado el martes 10am',
    elapsed: 'ayer', temp: 'cold', channel: 'WA', stage: 'Cerrando',
    selected: false, handler_mode: 'bot', campaign: null,
  },
] as const

const SELECTED_THREAD_MESSAGES = [
  { id: 'msg-1', side: 'in',  text: 'Hola, vi su anuncio sobre limpieza dental. ¿Cuánto sale?', time: '12:10' },
  { id: 'msg-2', side: 'out', text: '¡Hola María! La limpieza dental es S/ 120, dura 30 min. ¿Te agendo?', time: '12:11', sender: 'Adrián' },
  { id: 'msg-3', side: 'in',  text: 'Sí, mañana al mediodía si tienen', time: '12:13' },
  { id: 'msg-4', side: 'out', text: 'Genial. Tengo disponible Mar 27 a las 12:00 con Dra. Soto. Te confirmo con un depósito de S/ 36 (30%). ¿Continúo?', time: '12:14', sender: 'Adrián' },
] as const

const CONTACT_MOCK = {
  name: 'María González',
  phone_masked: '+51 9** ***-4321',
  email_masked: 'm***@gmail.com',
  campaign: { id: 'limpieza-pe', name: 'Limpieza-PE' },
  stage: 'Calificando',
  tags: ['limpieza', 'primera vez'],
} as const
```

**`ValeriaAgendaPlaceholder` mock:**

```tsx
const WEEK_LABEL = 'Semana 26-31 May 2026'
const DAYS = [
  { label: 'Lun 26', day_num: 26, today: true },
  { label: 'Mar 27', day_num: 27, today: false },
  { label: 'Mié 28', day_num: 28, today: false },
  { label: 'Jue 29', day_num: 29, today: false },
  { label: 'Vie 30', day_num: 30, today: false },
  { label: 'Sáb 31', day_num: 31, today: false },
] as const

const HOURS = ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00'] as const

const SLOTS = [
  { day_idx: 0, hour: '09:00', patient: 'M. Rodríguez', service: 'Limpieza', doctor: 'Dr. Mendoza', origin: null, status: 'PAG' },
  { day_idx: 0, hour: '10:00', patient: 'S. López',     service: 'Blanqueamiento', doctor: 'Dra. Soto', origin: null, status: 'DEPOSITO' },
  { day_idx: 1, hour: '09:00', patient: 'L. Vega',      service: 'Consulta', doctor: 'Dra. Soto', origin: 'phone', status: 'DEPOSITO' },
  { day_idx: 1, hour: '11:00', patient: 'J. Pérez',     service: 'Consulta', doctor: 'Dr. Mendoza', origin: null, status: 'DEPOSITO' },
  { day_idx: 2, hour: '10:00', patient: 'A. Ruiz',      service: 'Consulta', doctor: 'Dr. Mendoza', origin: 'walkin', status: 'SIN_PAGO' },
  { day_idx: 2, hour: '14:00', patient: 'P. Sosa',      service: 'Endodoncia', doctor: 'Dr. Mendoza', origin: null, status: 'PAG' },
  { day_idx: 3, hour: '11:00', patient: 'M. Díaz',      service: 'Blanqueamiento', doctor: 'Dra. Soto', origin: 'proactiva', status: 'DEPOSITO' },
  { day_idx: 3, hour: '15:00', patient: 'R. Cruz',      service: 'Consulta', doctor: 'Dr. Mendoza', origin: null, status: 'DEPOSITO' },
  { day_idx: 4, hour: '09:00', patient: 'C. Núñez',     service: 'Consulta', doctor: 'Dr. Mendoza', origin: null, status: 'NO_SHOW' },
  { day_idx: 5, hour: '11:00', patient: 'Sofía B.',     service: 'Limpieza', doctor: 'Dra. Soto', origin: 'manual', status: 'PAG' },
] as const

const LUNCH_HOUR = '13:00'
```

**`AdrianEmbudoPlaceholder` mock:** 6 cols × 3 leads each (parametrizado top-of-file, ver T-4 ticket en 06-tickets.yaml).

### § 5.2 — PHI compliance (mock-only)

Todos los nombres son **ficticios LatAm**. Teléfono y email se muestran **masked desde el origen** (`+51 9** ***-4321`, `m***@gmail.com`) — sin unmask logic Fase 1. F2-S3 cablea RBAC `@require_phi_access` server-side per `vitalia/.claude/rules/hipaa-lite.md` § Access control.

Arch test `test_no_phi_real_data.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { execSync } from 'child_process'

describe('PHI guard mock-only', () => {
  it('placeholders no contienen DNI literal con 8 dígitos', () => {
    const result = execSync(
      `grep -rn "[0-9]\\{8\\}" vitalia/frontend/src/features/{adrian,valeria,camila}/components/ || true`,
      { encoding: 'utf-8' }
    )
    const matches = result.split('\n').filter(Boolean)
    expect(matches, `PHI suspicion (8-digit DNI): ${matches.join('\n')}`).toEqual([])
  })

  it('teléfono real (10+ dígitos consecutivos) bloqueado', () => {
    const result = execSync(
      `grep -rnE "[0-9]{10,}" vitalia/frontend/src/features/{adrian,valeria,camila}/components/ || true`,
      { encoding: 'utf-8' }
    )
    expect(result.split('\n').filter(Boolean)).toEqual([])
  })
})
```

---

## § 6 — Server / Client decision tree

**Default:** Server Components (Next.js 16 App Router · FSD-Lite). `"use client"` solo en hoja con `useState`/event handler.

| Componente | Server / Client | Razón |
|---|---|---|
| `[agent]/[subtab]/page.tsx` | Server | sin state local; sólo renderiza `<SubTabContent>` |
| `SubTabContent` | Server | dispatcher puro (no state, no eventos) |
| `SubTabHeader` | Server | header puro |
| `EmptyState` | Server | sin event handler (action opcional pasa de Client parent) |
| `PlaceholderCard` | Server | sin state |
| `StatusDot` | Server | leaf |
| `TogglePill` | **Client** | Shadcn Tabs requires Client (Radix primitive uses React state) |
| `LisaServiciosPlaceholder` | **Client** | `useState<'catalogo'\|'escalera'>` |
| `AdrianEmbudoPlaceholder` | **Client** | `useState<'kanban'\|'lista'>` |
| `AdrianInboxPlaceholder` | **Client** | 3 `useState`: global toggle + sidebarOpen + localTakeover state A/B |
| `CamilaVozPlaceholder` | **Client** | `useState<'decide'\|'curaduria'\|'manual'>` |
| `ValeriaAgendaPlaceholder` | **Client** | `useState<'dia'\|'semana'\|'mes'>` |
| `ConfigConexionesPlaceholder` | Server | sin state |
| 16 placeholders genéricos | Server | wrapper EmptyState puro |
| `ThreadHeader`, `TakeoverBanner` | **Client** | event onClick (parent coordina state) |
| `MessageInput` | **Client** | textarea controlled (placeholder swap + disabled) |
| `ConversationItem` | **Client** | onClick selection (futuro F2) — Fase 1 visual con `<button>` |
| `CampaignTag`, `MessageBubble`, `ContactSidebar` | Server | sin state local — onClick rebotado a parent Client |
| `AgendaToolbar` | **Client** | dropdown CTA + period nav buttons |
| `AgendaFilters` | Server | disabled F1 (no event) |
| `AgendaDayHeader`, `AgendaSlot`, `AgendaSummaryFooter` | Server | leaf |

**Arch invariant:** `frontend-fsd` enforce — Server Components son default; `"use client"` justificado per row.

---

## § 7 — Sales_studio parity detail (Adrián Inbox)

> **Conceptual reference:** `ap_sales_agent/frontend/src/features/closer-studio/components/inbox/*` shipped. Vitalia construye **brand-local** sin import cross-brand (anti-duplication rule). Si Fase 2 confirma shape resiste → `/pm-luana` lift candidate.

### § 7.1 — Layout widths

```
┌────────────────────────────────────────────────────────────────┐
│ TogglePill 3-modos                                              │ ← h-14 sticky top
├──────────────────┬──────────────────────────┬───────────────────┤
│  320px            │  flex-1                  │  288px            │ ← sidebarOpen=true
│  Conv. List       │  Thread                  │  Contact Sidebar  │
└──────────────────┴──────────────────────────┴───────────────────┘
                              │
                              ▼ click "×" header
┌──────────────────┬──────────────────────────┬───────────────────┐
│  320px            │  1fr                     │  0 (hidden)       │ ← sidebarOpen=false
└──────────────────┴──────────────────────────┴───────────────────┘
```

CSS classes:

```tsx
<div className="grid h-[calc(100vh-theme(spacing.14)-theme(spacing.20))] grid-cols-[320px_1fr_288px] data-[sidebar=closed]:grid-cols-[320px_1fr_0]"
     data-sidebar={sidebarOpen ? 'open' : 'closed'}>
```

### § 7.2 — ConversationItem visual contract

```tsx
function ConversationItem({ conv }: { conv: typeof INBOX_CONVERSATIONS[number] }) {
  return (
    <button
      className={cn(
        'flex w-full items-start gap-3 border-l-2 px-3 py-2 text-left hover:bg-muted/30',
        conv.selected && 'border-l-agent-adrian bg-muted/50',
        conv.handler_mode === 'human' && !conv.selected && 'border-l-2 border-l-green-500/60',
      )}
      data-testid={`conv-item-${conv.id}`}
    >
      <Avatar initials={conv.patient.split(' ').map(s => s[0]).join('').slice(0,2)} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1 text-sm">
          <TempDot temp={conv.temp} />
          <span className="font-medium truncate">{conv.patient}</span>
          {conv.handler_mode === 'human' && <YouChip />}
        </div>
        <div className="text-xs text-muted-foreground truncate">{conv.preview}</div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <span>{conv.elapsed}</span>
          <ChannelAbbr channel={conv.channel} />
          <StageBadge stage={conv.stage} />
          {conv.campaign && <CampaignTag id={conv.campaign} name={conv.campaign} />}
        </div>
      </div>
    </button>
  )
}

function YouChip() {
  return (
    <span
      className="ml-1 rounded border border-green-500/50 bg-green-100/30 px-1 text-[9px] font-semibold text-green-700"
      title="Tomaste el control · Adrián pausado en esta conversación"
    >✋ Tú</span>
  )
}
```

### § 7.3 — Takeover UX state machine (local React useState para F1; Zustand `handlerOverride[leadId]` documented F2-S3)

```
STATE A — Adrián maneja (default)
  ThreadHeader: avatar + nombre + canal + chip "🤖 Adrián decidiendo" + botón "✋ Tomar el control" + × sidebar
  TakeoverBanner: hidden
  MessageInput: disabled · placeholder "🤖 Adrián decide automáticamente · toma el control para escribir tú"
  Thread footer hint: "Adrián decidirá la próxima respuesta automáticamente · clic ✋ Tomar el control arriba para responder tú"
                   │
                   │  click "✋ Tomar el control" → setLocalTakeover('human')
                   ▼
STATE B — Usuario en control
  ThreadHeader: avatar + nombre + canal + × sidebar (sin chip ni botón takeover)
  TakeoverBanner: visible amarillo border-l-4 con título + meta + botón "🤖 Devolver a Adrián"
  MessageInput: enabled · auto-focus · placeholder "Escribir como tú a {patient_name}…"
  Thread footer hint: amarillo "⚡ Estás respondiendo como tú · Adrián volverá a manejar la conversación cuando devuelvas el control"
                   │
                   │  click "🤖 Devolver a Adrián" → setLocalTakeover('bot')
                   ▼
STATE A again
```

**F1 impl:** `const [localTakeover, setLocalTakeover] = useState<'bot'|'human'>('bot')` inside `AdrianInboxPlaceholder`. NO Zustand. NO backend wire (PATCH `/api/v1/inbox/conversations/{leadId}/handler` es F2-S3).

**F2-S3 cache:** spec ratificó conditional store path `features/adrian/store/inbox-store.ts` con `handlerOverride: Map<leadId, 'bot'|'human'>`. F1-S10 documenta el shape pero NO implementa el store.

---

## § 8 — Takeover UX detail (clave para auditor)

| Aspecto | F1-S10 (visual placeholder) | F2-S3 (real wiring) |
|---|---|---|
| State management | local React `useState<'bot'\|'human'>('bot')` en `AdrianInboxPlaceholder` parent | Zustand `useInboxStore.takeControl(leadId)` / `.releaseControl(leadId)` + `handlerOverride: Map<leadId,Mode>` |
| Backend wire | NINGUNA (no fetch) | PATCH `/api/v1/inbox/conversations/{leadId}/handler` body `{mode:'human'\|'bot'}` |
| Event emission | NINGUNA | `conversation.handler.taken_over` / `conversation.handler.released` |
| Persistencia | NINGUNA | Postgres column `conversation.handler_override` (default `null` = sigue global) |
| Engine impact | NINGUNA | `core/luana-core-sales-agent` consulta `handler_override` antes de procesar mensaje entrante; `'human'` → solo logea + no genera respuesta. `/pm-luana` promotion candidate Extension SDK EP-N `inbox_handler_override` |
| YouChip visibility | hardcoded en mock data (`conv.handler_mode === 'human'` static) | reactivo a `handlerOverride[conv.id]` |
| Banner amarillo | conditional render `{localTakeover === 'human' && <TakeoverBanner />}` | conditional render `{handlerOverride.get(selectedConvId) === 'human' && <TakeoverBanner />}` |

**Mock data state:** F1-S10 fija `conv-2` Carlos Pérez con `handler_mode: 'human'` para mostrar YouChip + border-l verde en list (otro escenario que el currently-selected). Click "✋ Tomar el control" en thread `conv-1` María Gonzalez activa state B para esa conv selected.

---

## § 9 — Agenda enriquecida detail

| Componente | Responsabilidad F1-S10 | Comportamiento Fase 2 |
|---|---|---|
| `AgendaToolbar` | period label estático "Semana 26-31 May 2026" + period toggle visual (Día\|Semana\|Mes) + "📅 Hoy" + CTA "+ Crear cita ▾" dropdown 3 opciones (Walk-in / Phone / Proactivo) | F2-S1 cablea `useAgendaWeek(weekStart)` + ±7 días reales + "Hoy" reset + CTA navega a modal Crear cita |
| `AgendaFilters` | 6 chips disabled (search input + Doctor dropdown + Especialidad dropdown + Status pago dropdown + ☐ no-show + ☐ walk-in) | F2-S1 cablea Zustand `useAgendaFilters` + URL searchParam preservation |
| `AgendaDayHeader` × 6 | Lun 26 highlight today (color `agent-valeria` en agentic mode / `agent-adrian` en web) | F2-S1 calcula `isToday(date)` dinámico |
| `AgendaSlot` × 10 | mock data (paciente + service + doctor + origin + status pill verbatim) | F2-S1 cablea con `Appointment` DTO real (patient_id + service_id + doctor_id + payment_status) + click → ContactSidebar payment subform |
| `AgendaSummaryFooter` | leyenda 4 status estática + texto "Adrián propuso 4 turnos hoy · 3 sin pago · Lucas: 3 leads listos" | F2-S1 cablea con `useAdrianAgendaSummary()` hook (cross-feature read via Lucas) |
| Lunch-time pattern | 6 cells fila 13:00 con `bg-stripes` Tailwind pattern + `aria-label="Horario de almuerzo"` | F2-S1 cablea `useWorkingHours(doctor_id)` per doctor |

**Status pills cores tokens Tailwind (ya cementados F1-S0):**

| Status | Background | Border-left | Icon |
|---|---|---|---|
| `PAG` | `bg-green-100/50` | `border-l-4 border-l-green-500` | `✓` |
| `DEPOSITO` (30%) | `bg-cyan-100/50` | `border-l-4 border-l-cyan-500` | `30%` |
| `SIN_PAGO` | `bg-amber-100/50` | `border-l-4 border-l-amber-500` | (sin icon) |
| `NO_SHOW` | `bg-red-100/30 line-through` | `border-l-4 border-l-red-500` | `⚠` |

---

## § 10 — Cross-cutting concerns

### § 10.1 — Tenant isolation (URL params pass-through)

F1-S10 NO hace fetch. NO toca tenant_id beyond pass-through:

- `[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` recibe `params.tenantId` per Next.js dynamic route.
- `<SubTabContent>` NO consume `tenantId` (placeholder is brand-local generic).
- Future F2 cableará `useTenantLocale()` para currency formatting.

### § 10.2 — PHI guard (HIPAA-lite overlay)

- NO PHI real Fase 1. Mock-only nombres LatAm ficticios.
- PHI fields display **siempre masked from origin** (no unmask logic):
  - Phone: `+51 9** ***-4321` literal string
  - Email: `m***@gmail.com` literal string
  - DNI: NO mostrado (futuro F2-S2 valeria-pacientes cablea RBAC)
- Arch test `test_no_phi_real_data.test.ts` ban 8+ dígitos consecutivos en `features/{adrian,valeria,camila}/components/`.

### § 10.3 — NO API endpoints

- Zero fetch.
- Zero React Query keys.
- Zero mutations.
- Zero form library (RHF/Zod). MessageInput textarea F1-S10 es uncontrolled visual; F2-S3 cablea RHF.

### § 10.4 — Spanish neutro LatAm

Toda copy verbatim del § 10 spec. Pre-commit hook valida glosario voseo. Allowed: `tú`, `eres`, `tienes`, `puedes`, `escribir`, `tomar el control`, `devolver`. Prohibited: `vos`, `tenés`, `podés`, `dejá`, `linkeá`.

`mockup-per-component.md` overlay rule: copy en mockups HTML ratificados Chris 2026-05-26 = SSoT. Builder reproduce textual.

### § 10.5 — Native-First dev

Builder corre TODO native Linux:

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint src/ --cache
cd ${WS}/vitalia/frontend && npx vitest run --coverage
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke
```

NUNCA `make e2e*` (Docker OOM). Per `.claude/rules/e2e-testing.md`.

---

## § 11 — Test Construction Plan ★ v4.1

> Mandatory para validators v4.1. Builder TDD: tests RED primero, GREEN segundo.

### § 11.1 — playwright_required

`playwright_required: true` (ui-story HARD per v4.1). 11 specs Playwright + ~70 visual goldens.

### § 11.2 — Creation order (numerado — DAG sequential)

```
1.  POMs creados primero (foundation):
    - vitalia/frontend/e2e/pages/ShellOrganismPage.ts                (genérico 22-subtab visit + assert)
    - vitalia/frontend/e2e/pages/AdrianInboxPage.ts                  (takeover UX A↔B helpers + sidebar toggle)
    - vitalia/frontend/e2e/pages/ValeriaAgendaPage.ts                (toolbar + filters + grid + slot click)

2.  Fixtures Playwright reusadas (NO NEW):
    - vitalia/frontend/e2e/fixtures/vitalia-auth.fixture.ts          (shipped F1-S0; SC tests reusan)

3.  Specs Playwright (11 specs) — orden DAG con dependencies:
    sc-01-navegacion-22-subtabs.spec.ts        # foundational — verifica 22 routes navegables
    sc-02-lisa-servicios.spec.ts                # foundational — toggle Catálogo|Escalera
    sc-03-adrian-embudo.spec.ts                 # foundational — Kanban 6 cols + toggle
    sc-04-valeria-agenda.spec.ts                # depende toolbar+filters+grid POM
    sc-04bis-adrian-inbox.spec.ts               # depende inbox POM + takeover UX
    sc-05-subtab-invalido.spec.ts               # reusa F1-S9 not-found hierarchy
    sc-06-edge-no-shell-remount.spec.ts         # observer-pattern DOM node ref
    sc-07-adversarial-xss.spec.ts               # reusa F1-S9 isValidSubtab() defensa
    sc-08-empty-states-genericos.spec.ts        # parametrizado over 16 sub-tabs
    sc-09-a11y.spec.ts                          # axe wcag2aa + keyboard nav
    sc-10-i18n.spec.ts                          # spanish neutro + tenant_locale PEN

4.  Vitest unit tests (7 archivos):
    - SubTabContent.test.tsx                    (dispatcher mapping + EmptyState fallback)
    - EmptyState.test.tsx                       (icon + title + desc + optional action)
    - TogglePill.test.tsx                       (state change visual)
    - ConversationItem.test.tsx                 (YouChip conditional render handler_mode='human')
    - ThreadHeader.test.tsx                     (takeover state A vs B visual)
    - AgendaSlot.test.tsx                       (4 status variants + 4 origins)
    - inbox-mock-shape.test.ts                  (zod schema validation mock data shape)

5.  Visual goldens (~70 PNG snapshots):
    Light + Dark × 22 sub-tabs = 44
    Inbox takeover state A light+dark = 2
    Inbox takeover state B light+dark = 2
    Inbox sidebar closed light+dark = 2
    Responsive (mobile 375 / tablet 768 / desktop 1280) × 6 placeholders especiales = ~18 (no se exigen 22)
```

### § 11.3 — Scenario_to_test mapping (de los 10 SC del spec)

| Scenario | Spec path | Visual goldens | Vitest unit | POMs needed |
|---|---|---|---|---|
| SC-1 happy 22 sub-tabs navegables | sc-01-navegacion-22-subtabs.spec.ts | 44 light+dark | SubTabContent.test.tsx | ShellOrganismPage |
| SC-2 Lisa Servicios toggle | sc-02-lisa-servicios.spec.ts | 2 (catalogo + escalera) | TogglePill.test.tsx | ShellOrganismPage |
| SC-3 Adrián Embudo Kanban | sc-03-adrian-embudo.spec.ts | 2 (kanban + lista) | TogglePill.test.tsx | ShellOrganismPage |
| SC-4 Valeria Agenda enriquecida | sc-04-valeria-agenda.spec.ts | 2 (week default light+dark) + 3 responsive | AgendaSlot.test.tsx + inbox-mock-shape | ValeriaAgendaPage |
| SC-4.bis Adrián Inbox + takeover | sc-04bis-adrian-inbox.spec.ts | 6 (state A · state B · sidebar closed × light+dark) | ConversationItem.test.tsx + ThreadHeader.test.tsx | AdrianInboxPage |
| SC-5 subtab inválido → 404 | sc-05-subtab-invalido.spec.ts | 1 (404 dentro shell) | — | ShellOrganismPage |
| SC-6 no shell re-mount | sc-06-edge-no-shell-remount.spec.ts | — | — | ShellOrganismPage |
| SC-7 XSS adversarial | sc-07-adversarial-xss.spec.ts | — | — | ShellOrganismPage |
| SC-8 16 genéricos param | sc-08-empty-states-genericos.spec.ts | reusa de SC-1 | EmptyState.test.tsx | ShellOrganismPage |
| SC-9 axe a11y | sc-09-a11y.spec.ts | — | — | ShellOrganismPage |
| SC-10 i18n spanish + locale | sc-10-i18n.spec.ts | — | — | ShellOrganismPage |

### § 11.4 — N/A justificadas

| Sub-category | Applies | Reason |
|---|---|---|
| `race_condition` | NO | F1-S10 sin writes / sin unique constraint |
| `concurrent_users` | NO | Routing per-session; sin state compartido cross-user |
| `network_failure` | NO | Cero fetch — todo mock hardcoded |
| `large_dataset` | NO | Mock fijo (5 conversaciones, 10 slots, 6 cols × 3 leads) |
| `accessibility` | YES | SC-9 axe wcag2aa |
| `i18n_l10n` | YES | SC-10 Spanish neutro |
| `empty_state` | YES | SC-8 16 genéricos parametrizado |

---

## § 12 — Cross-references

- **Spec ratificado:** `vitalia/docs/product/stories/vitalia-fase1-empty-states/01-spec.md` (v2 batch 1+2+3)
- **Checkpoint state:** `vitalia/docs/product/stories/vitalia-fase1-empty-states/checkpoint.md` (refined → ready post merge ready-package)
- **Predecessor arch (FE patterns):** `vitalia/docs/archive/2026/stories/vitalia-fase1-routing-shell/03-arch-fe.md`
- **SSoT consumidos:**
  - `vitalia/frontend/src/lib/agent-catalog.ts` (RIBBON_SUBTABS · 22 sub-tabs)
  - `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` (atomic layers + tokens · agent colors)
- **Brand overlay rules:**
  - `vitalia/.claude/rules/hipaa-lite.md` (PHI mock-only)
  - `vitalia/.claude/rules/shell-mockup-per-component.md` (7 mockups ratificados)
- **Universal rules consultadas:**
  - `.claude/rules/frontend-fsd.md` (boundaries FSD-Lite)
  - `.claude/rules/spanish-text.md` (neutro LatAm sin voseo)
  - `.claude/rules/tdd-mandatory.md` (RED → GREEN)
  - `.claude/rules/e2e-testing.md` (native Linux, NUNCA Docker)
  - `.claude/rules/anti-duplication.md` (no cross-brand mirror)
- **Visual mockups ratificados** (gate `shell-mockup-per-component.md`):
  - 7 mockups en `vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/` (Chris ratificó iter 2 · 2026-05-26)

---

## § 13 — Open questions for PM (post-architect)

Ninguna ambigüedad pendiente. Spec v2 ratificado + 3 batches Chris cement + 7 mockups visual ratificados. Ready package puede transitionar `refined → ready` y `/dev-team` arrancar Conv 2 sin clarificación adicional.

---

## § 14 — Research notes (date-aware)

**Patterns referenced as of 2026-05-26:**

- **Next.js 16 App Router** server-first defaults — `https://nextjs.org/docs/app/api-reference/file-conventions/page` (accessed 2026-05-26). Validado: dynamic segments `[agent]/[subtab]` permiten Server Component default; `"use client"` hojas para state.
- **Radix UI Tabs primitive** — `https://www.radix-ui.com/primitives/docs/components/tabs` (accessed 2026-05-26). TogglePill wraps Radix Tabs (Shadcn-style), requires Client Component (Radix uses internal React state).
- **WCAG 2.2 reference for axe-core wcag2aa** — `https://www.w3.org/WAI/WCAG22/quickref/` (accessed 2026-05-26). Heading hierarchy (h1→h2→h3), keyboard tab order, aria-live polite for state changes.
- **CVA + cn() Tailwind merge** — `https://cva.style/docs` (accessed 2026-05-26). cn() merges with twMerge under hood; safe for conditional classNames in `data-[state]` selectors.

**Knowledge cutoff disclosure:** Opus 4.7 cutoff is January 2026. Topics researched live on 2026-05-26 via WebSearch alignment. No state-of-the-art surface in F1-S10 — all patterns are well-established Next.js 16 + Radix + Tailwind. NO novel framework feature introduced.

