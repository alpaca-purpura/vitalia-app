---
story_id: vitalia-fase1-ribbon-6-tabs
brand: vitalia
type: ui-story
state: refining
outcome: vitalia-mvp-ui-foundation
phase: fase-1
module: shell-organism
capability: shell.ribbon
po_ux_version: 2
ratified_by_chris: false
last_modified: 2026-05-24
authors: [/po-ux]
spec_anchors:
  shell_design_contract: vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
  shell_template: vitalia/docs/specs/templates/01-spec-shell-template.md
  predecessor_archive: vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/01-spec.md
  predecessor_capability: vitalia/docs/product/capabilities/shell-organism/valeria-chat.yaml
ssot_extensions:
  agent_catalog: vitalia/frontend/src/lib/agent-catalog.ts (EXTEND — NO crear lib/agents/catalog.ts)
---

# F1-S7 · `vitalia-fase1-ribbon-6-tabs` — 01-spec.md (unified)

> **/po-ux UI-standard.** Gherkin + wireframes inline + estados visuales + microcopy + graders en este único archivo. NO existe `02-design-ui.md` separado por design.

## § Context

**Outcome:** `vitalia-mvp-ui-foundation` (contenedor Fase 1 + Fase 2 shell-organism).
**Módulo afectado:** `shell-organism`.
**Insertion point:** dentro de `AppPanelSlot` (heredado F1-S4 shell-layout-5050) — primera fila del grid `[Ribbon | Sub-tabs | Content]`. Visible en ambos modos shell (`agentic` 50/50 y `web` rail 60px).

**Out-of-scope explícito (anti-creep):**
- ❌ NO Sub-tabs línea 2 (eso es F1-S8)
- ❌ NO content per tab (eso son empty-states F1-S10 + Fase 2)
- ❌ NO bell icon notifications (Fase 2 postponed)
- ❌ NO Mateo en el Ribbon — Mateo es agente transversal que aparece en otro surface (story futura definirá dónde)
- ❌ NO RBAC para ConfigTab — visible siempre en F1-S7 (TODO Fase 2)
- ❌ NO telemetría wireada — `ribbon_tab_clicked` queda anotado como TODO Fase 2

**Decisión cementada — modos shell:** el Ribbon renderiza idéntico en modos `agentic` y `web` (misma horizontal h-14, 5 tabs + ConfigTab, `overflow-x-auto`). NO if-statements `mode === 'web'`. La única diferencia entre modos es el ancho disponible del AppPanel; el Ribbon se adapta vía `flex` + `overflow-x-auto` natural.

**Catalog SSoT — EXTEND existente (anti-duplication):** `vitalia/frontend/src/lib/agent-catalog.ts` ya vive (creado F1-S6). F1-S7 NO crea `lib/agents/catalog.ts` (path duplicado). Extiende el `AgentDescriptor` con 2 campos nuevos:

```ts
export interface AgentDescriptor {
  slug: AgentSlug
  name: string
  role: string
  colorToken: string
  colorSoftToken: string
  hex: string
  thumbnail: string
  transparent: string
  initial: string
  // ★ NEW F1-S7:
  tabLabel: string         // verbo/sust corto ("Mi Clínica"/"Atraer"/"Vender"/"Operar"/"Mantener")
  defaultSubtab: string    // slug subtab default al cliquear ribbon ("marca"/"lanzar"/"inbox"/"agenda"/"voz")
}
```

`AGENT_RIBBON_ORDER` constante nueva: `['lisa', 'lucas', 'adrian', 'valeria', 'camila']` (Mateo excluido explícitamente).

## § Gherkin scenarios

> **Sub-categorías mandatory v4.1 que aplican:** `accessibility` + `i18n`. Las demás (`race_condition`, `concurrent_users`, `network_failure`, `empty_state`, `large_dataset`) están marcadas `not_applicable_reason` porque el Ribbon es UI navegacional puro (5 tabs estáticos, sin fetch FE, sin create/update, sin pagination).

### SC-1 happy · click tab agente navega a default subtab

```gherkin
Given usuario en /{tenantId}/lisa/marca, active tab Lisa visible con bg-agent-lisa-soft tint
When click RibbonTab "Atraer" (Lucas)
Then router.push("/{tenantId}/lucas/lanzar") se invoca (AGENT_CATALOG.lucas.defaultSubtab="lanzar")
And el segmento URL [agent] cambia a "lucas"
And active state migra: Lucas tab muestra bg-agent-lucas-soft + label font-semibold
And Lisa tab pierde tint (text-muted-foreground, font-medium)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-nav.spec.ts" }
  - { type: visual_state, screen: "active-lucas", element: "[data-testid=ribbon-tab-lucas]", expect: "data-active=true · class~=bg-agent-lucas-soft" }
  ```

### SC-2 happy · URL deep link marca active state correcto

```gherkin
Given usuario navega directamente (deep link) a /{tenantId}/camila/voz
When la página carga
Then `extractAgentFromPath(pathname)` devuelve "camila"
And Camila tab renderiza con bg-agent-camila-soft + label font-semibold
And los otros 4 tabs agentes + ConfigTab quedan inactivos (text-muted-foreground)
And aria-selected="true" solo en Camila tab
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-deeplink.spec.ts" }
  - { type: visual_state, screen: "active-camila", element: "[data-testid=ribbon-tab-camila]", expect: "aria-selected=true" }
  ```

### SC-3 happy · ConfigTab navega a /{tenantId}/config/cuenta

```gherkin
Given active tab cualquier agente (ej. Valeria en /{tenantId}/valeria/agenda)
When click ConfigTab (IconButton ⚙ right-aligned)
Then router.push("/{tenantId}/config/cuenta") se invoca
And ConfigTab muestra estado active (bg-muted más oscuro o ring sutil — definido en estados visuales)
And tooltip "Configurar" se oculta tras click
And Valeria tab pierde tint
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-config-nav.spec.ts" }
  ```

### SC-4 negative · URL con agent slug inválido → idle state

```gherkin
Given usuario navega a /{tenantId}/foobar/baz (segmento [agent]="foobar" inválido)
When la página carga
Then `extractAgentFromPath(pathname)` devuelve null (no matchea AgentSlug)
And ninguno de los 5 tabs agentes muestra active state
And ConfigTab también queda inactivo
And NO se lanza error en consola (defensive null check)
And aria-selected="false" en todos los tabs
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-invalid-agent.spec.ts" }
  - { type: visual_state, screen: "idle-no-active", element: "[data-testid=ribbon]", expect: "no [data-active=true]" }
  ```

### SC-5 edge · viewport mobile 375px → horizontal scroll

```gherkin
Given viewport 375x667 (mobile portrait)
When la página carga con active=lisa
Then el Ribbon renderiza horizontal con overflow-x-auto
And solo Lisa + Lucas + parte de Adrián son visibles sin scroll
And scrollbar nativo (o styled) aparece al fondo
And user puede scrollear lateral para alcanzar ConfigTab al final
And ConfigTab mantiene `ml-auto` (queda último en orden DOM, no flota fijo)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-mobile.spec.ts" }
  - { type: visual_golden, path: "vitalia/frontend/e2e/__screenshots__/shell/ribbon-mobile-375.png" }
  ```

### SC-6 adversarial · prompt injection en path (XSS) → safe

```gherkin
Given usuario navega a /{tenantId}/<script>alert(1)</script>/foo (segmento [agent] con script)
When la página carga
Then `extractAgentFromPath` devuelve null (no matchea AgentSlug enum)
And React JSX auto-escape sanea el segment si se renderiza en cualquier lado
And NO se ejecuta el script
And ribbon renderiza idle state (sin tab activo)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-xss-guard.spec.ts" }
  - { type: state_check, target: dom, query: "document.querySelector('script[data-injected]')", expect: "null" }
  ```

### SC-7 a11y · keyboard navigation WAI-ARIA tablist completo

```gherkin
Given foco en body (al cargar página)
When Tab → focus va al primer tab activable (Lisa por roving tabindex)
And Arrow Right → focus mueve a Lucas (sin activar — no router.push aún)
And Arrow Right → focus a Adrián
And Home → focus regresa a Lisa
And End → focus salta a ConfigTab (último)
And Enter en ConfigTab focused → router.push("/{tenantId}/config/cuenta")
Then en cada paso, focus ring visible (ring-2 ring-ring) sobre el tab focused
And screen reader anuncia "tab, {tabLabel}, {N de 6}" al focus change
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-keyboard.spec.ts" }
  - { type: axe, ruleset: "wcag2aa", scope: "[data-testid=ribbon]" }
  ```

### SC-8 i18n · microcopy Spanish neutro renderizado correcto

```gherkin
Given Ribbon renderizado en /{tenantId}/lisa/marca (active=lisa)
When inspeccionamos textos visibles
Then verificamos verbatim:
  | tab     | tabLabel       | tabRole (10px)          |
  | lisa    | "Mi Clínica"   | "Lisa"                  |
  | lucas   | "Atraer"       | "Lucas"                 |
  | adrian  | "Vender"       | "Adrián"                |
  | valeria | "Operar"       | "Valeria"               |
  | camila  | "Mantener"     | "Camila"                |
And ConfigTab aria-label="Configurar" + tooltip text="Configurar"
And NO aparece voseo (vos/sos/tenés/podés/dale)
And tildes correctas (Adrián con tilde, Clínica con tilde)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-i18n.spec.ts" }
  - { type: visual_state, screen: "tabLabels-lightTheme", element: "[data-testid=ribbon] button", expect: "innerText match copy table" }
  ```

### SC-9 edge · avatar PNG falla → fallback initial

```gherkin
Given thumbnail PNG de Valeria 404 (asset removed / network blocked / CDN flake)
When Ribbon renderiza tab Valeria
Then Shadcn `<Avatar>` componente detecta fallo via `<AvatarImage>` onError
And `<AvatarFallback>` muestra letra "V" (AGENT_CATALOG.valeria.initial)
And el background del fallback es bg-agent-valeria-soft (color identificable de Valeria)
And el tab sigue funcional (click navega a /{tenantId}/valeria/agenda)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-avatar-fallback.spec.ts" }
  ```

### Sub-categorías NOT applicable (justificación explícita)

| Sub-cat | Aplicable | Razón |
|---|---|---|
| `race_condition` | ❌ | Ribbon es UI nav puro: sin create/update, sin unique constraint. router.push es idempotente. |
| `concurrent_users` | ❌ | Sin list/detail filterable. Cada user tiene su URL propia client-side. |
| `network_failure` | ❌ | Ribbon NO hace fetch FE — solo router.push (next-routing local). Avatar fallback (SC-9) cubre el único network dependency. |
| `empty_state` | ❌ | Ribbon es lista estática de 5 tabs fijos + ConfigTab. No hay data fetched. SC-4 cubre el "edge" de active=null (URL inválido). |
| `large_dataset` | ❌ | 5 tabs + ConfigTab. No hay pagination. |

## § Wireframe inline (ASCII art)

### Vista global — modo agentic (split 50/50, AppPanel ≈ 640px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TopBarGlobal (TenantSwitcher + ShellModeToggle + ThemeToggle)               │
├──────────────────────────────────────┬───────────────────────────────────────┤
│                                      │ ┌─── Ribbon (h-14) ─────────────────┐│
│  ValeriaSidebar                      │ │[●Lisa][●Lucas][●Adrián][●Valeria]││
│  - ChatHeader (Valeria avatar)       │ │ MiClín  Atraer  Vender   Operar  ││
│  - ChatMessages (6 mocks)            │ │ ▒▒▒▒▒▒                            ││
│  - ChatComposer                      │ │            [●Camila]         [⚙]  ││
│  (50% width = ~640px)                │ │             Mantener              ││
│                                      │ └───────────────────────────────────┘│
│                                      ├───────────────────────────────────────┤
│                                      │ Sub-tabs (F1-S8 placeholder)         │
│                                      ├───────────────────────────────────────┤
│                                      │ Content area (F1-S10 empty states)   │
│                                      │                                      │
│                                      │                                      │
└──────────────────────────────────────┴───────────────────────────────────────┘
                              ↑ Ribbon = AppPanelSlot first row
                              ↑ overflow-x-auto (active=Lisa scroll-into-view)
                              ↑ ConfigTab right-aligned (ml-auto)
```

### Detalle — Ribbon h-14 (vista plana, active=Lisa)

```
┌─ Ribbon ──────────────────────────────────────────────────────────────────┐
│ ▒▒▒▒▒▒▒▒▒▒                                                                │
│ ▒ ● Mi  ▒    ● Atraer    ● Vender    ● Operar    ● Mantener        [⚙]    │
│ ▒ Clín. ▒                                                                 │
│ ▒ Lisa  ▒    Lucas       Adrián      Valeria     Camila          tooltip  │
│ ▒▒▒▒▒▒▒▒▒▒                                                       on hover │
└───────────────────────────────────────────────────────────────────────────┘
  ↑ active                ↑ inactive                                ↑ IconButton
    bg-agent-lisa-soft       text-muted-foreground                    40x40
    label font-semibold      label font-medium                        right-aligned
    avatar 28px circle       avatar 28px circle, no ring              ml-auto
    role 10px muted          role 10px muted                          Settings icon Lucide
```

### Detalle — ConfigTab (active)

```
ConfigTab inactive:                ConfigTab active (/{tenantId}/config/cuenta):
┌────────┐                         ┌────────┐
│   ⚙    │ ← icon Lucide 20px      │   ⚙    │ ← icon + bg-muted más oscuro
│ 40x40  │   muted-foreground      │ 40x40  │   foreground color
│ bg-mut │   on hover              │ bg-mut │   ring-1 ring-border
│        │                         │ active │
└────────┘                         └────────┘
tooltip on hover: "Configurar"     tooltip suprimido si focused/active
aria-label="Configurar"            aria-label="Configurar"
                                   data-active="true"
```

### Mobile 375px (SC-5)

```
┌──── viewport 375px ────┐
│ TopBarGlobal (compact) │
├────────────────────────┤
│ Valeria chat (mode=agentic en mobile = 100%) o rail (mode=web mobile) │
│                        │
├────────────────────────┤
│ ┌─ Ribbon ─────────────────────────────────────→ scroll →
│ │[●Lisa][●Lucas][●Adr..│ ← visible
│ │ MiCl   Atraer  Vender│
│ │ ▒▒▒▒                 │
│ └──────────────────────│ overflow-x-auto, ConfigTab al fondo del scroll
├────────────────────────┤
│ Sub-tabs (F1-S8)       │
├────────────────────────┤
│ Content                │
└────────────────────────┘
```

> Nota mobile mode: en F1-S4 quedó deferred cómo se layoutea el shell <768px. F1-S7 asume que el Ribbon vive dentro del AppPanelSlot y respeta `overflow-x-auto` natural — no introduce paradigma mobile-específico (no bottom-nav, no dropdown). Visual golden mobile-375 captura el comportamiento horizontal-scroll.

## § Estados visuales

### Por tab agente (5 variantes, idénticos en estructura)

| Estado | Trigger | Background | Label `tabLabel` | Sub-label `role` | Avatar | Border |
|---|---|---|---|---|---|---|
| `inactive` | `[agent]` URL segment ≠ slug | transparent | `text-muted-foreground` · `font-medium` · `whitespace-nowrap` | `text-muted-foreground/70` 10px · `whitespace-nowrap` | 28px circle, sin ring | sin border-bottom |
| `inactive:hover` | mouse over inactive | `bg-muted` | `text-foreground` · `font-medium` · `whitespace-nowrap` | `text-muted-foreground` 10px | 28px circle, sin ring | sin border-bottom |
| `inactive:focus` | keyboard focus | `bg-muted` | `text-foreground` · `font-medium` · `whitespace-nowrap` | `text-muted-foreground` 10px | 28px circle | outline → `ring-2 ring-ring ring-offset-1` |
| `active` | `[agent]` URL segment = slug | `bg-agent-{agent}-soft` | `text-foreground` · `font-semibold` · `whitespace-nowrap` | `text-muted-foreground` 10px · `whitespace-nowrap` | 28px circle | sin border-bottom |
| `active:hover` | mouse over active | `bg-agent-{agent}-soft` (PRESERVA tint del agente — NUNCA degrada a `bg-muted`. Specificity HARD: data-active selector debe ganar sobre :hover) | `text-foreground` · `font-semibold` | `text-muted-foreground` 10px | 28px circle | sin border-bottom |
| `active:focus` | keyboard focus en active | `bg-agent-{agent}-soft` | `text-foreground` · `font-semibold` | `text-muted-foreground` 10px | 28px circle | `ring-2 ring-ring ring-offset-1` |
| `avatar-fallback` | PNG `thumbnail` 404 | hereda parent state | hereda | hereda | `<AvatarFallback>` con `initial` + `bg-agent-{agent}-soft` | hereda |

### ConfigTab (IconButton 40x40)

| Estado | Trigger | Background | Icon color | Tooltip | aria-label |
|---|---|---|---|---|---|
| `inactive` | URL ≠ `config` segment | `bg-muted` | `text-muted-foreground` | oculto | "Configurar" |
| `inactive:hover` | mouse over | `bg-muted/80` | `text-foreground` | "Configurar" visible | "Configurar" |
| `inactive:focus` | keyboard focus | `bg-muted` + `ring-2 ring-ring ring-offset-1` | `text-foreground` | "Configurar" visible | "Configurar" |
| `active` | URL = `/config/...` | `bg-muted` + `ring-1 ring-border` + `data-active=true` | `text-foreground` | oculto (no necesita pista) | "Configurar" |
| `active:focus` | keyboard focus en active | `bg-muted` + `ring-2 ring-ring ring-offset-1` | `text-foreground` | oculto | "Configurar" |

## § Componentes (reuse > new)

| Componente | Path repo | Acción | Notas |
|---|---|---|---|
| `Avatar` (Shadcn) | `vitalia/frontend/src/components/ui/avatar.tsx` | reuse | Avatar + AvatarImage + AvatarFallback para fallback PNG-404 (SC-9) |
| `Tooltip` (Shadcn) | `vitalia/frontend/src/components/ui/tooltip.tsx` | reuse | TooltipProvider + Trigger + Content para ConfigTab "Configurar" |
| `Button` (Shadcn variants ghost) | `vitalia/frontend/src/components/ui/button.tsx` | reuse opcional | ConfigTab puede ser `<Button variant="ghost" size="icon">` o `<button>` raw — definir en `/architect-fe` |
| `cn()` util | `vitalia/frontend/src/lib/utils.ts` | reuse | composición clases |
| `Settings` (Lucide icon) | `lucide-react` | reuse | ConfigTab icon |
| `AGENT_CATALOG` constante | `vitalia/frontend/src/lib/agent-catalog.ts` | **EXTEND** | + `tabLabel` + `defaultSubtab` por agente. NO crear `lib/agents/catalog.ts` separado. |
| `Ribbon` organismo | `vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx` | **NEW** | usePathname + useRouter + useParams · roving tabindex pattern |
| `RibbonTab` molécula | `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx` | **NEW** | render por slug agente (no `agent === 'config'` branch) |
| `ConfigTab` molécula | `vitalia/frontend/src/components/shared/shell-organism/ConfigTab.tsx` | **NEW** | IconButton 40x40 + Tooltip · sin label visible |
| `extractAgentFromPath` helper | `vitalia/frontend/src/lib/agent-catalog.ts` (junto al catalog) o `lib/agents/routing.ts` | **NEW** | parse pathname → AgentSlug \| 'config' \| null · `/architect-fe` decide path final |
| `AppPanelSlot` wrapper | `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | **MODIFY** | reemplaza placeholder `<div ribbon />` por `<Ribbon />` real |
| `_agent-tw-classes.ts` allowlist | `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` | **MODIFY** | agregar `bg-agent-{slug}-soft` 5 classes si no están (Tailwind purge safety) |

**Justificación NEW components (4 archivos):**
- `Ribbon.tsx` — no existe organismo equivalente; `ValeriaSidebar` es otro layer del shell, no reutilizable.
- `RibbonTab.tsx` — patrón de tab con avatar + label + sub-label específico de este organism; no es Shadcn `<Tabs>` (que asume `<TabsContent>` inline incompatible con Next.js routes).
- `ConfigTab.tsx` — IconButton 40x40 con Tooltip, semánticamente distinto (no es un tab agente, es navegación a admin).
- `extractAgentFromPath` helper — utility puro, podría vivir en `lib/agent-catalog.ts` (junto al catalog) o en `lib/agents/routing.ts` — `/architect-fe` decide path final.

**Anti-pattern bloqueado:** NO usar Shadcn `<Tabs>` Radix-based — su API asume `<TabsContent>` inline y nuestra navegación es route-based (Next.js URL segments). Implementación custom es justificada.

**Cross-brand mirror check:** patrón Ribbon es brand-local Vitalia. Si nicolify/comunify/lupulo/futuros adoptan multi-agente ribbon similar → lift candidate a `core/luana-core-ui-shell/` futuro (promotion proposal `/pm-luana`). Hoy NO existe paralelismo cross-brand.

## § Data flow (conceptual)

- **No API consumed.** Ribbon es UI nav puro. Click → `router.push()`. URL → `usePathname()` → derive active.
- **No React Query keys.** No fetch.
- **No mutations.** Stateless component derive de URL.
- **No form library.** No inputs.
- **No global state (zustand).** Active agent es derived from URL — single source of truth.
- **Routing:** `useParams<{ tenantId: string }>()` + `usePathname()` + `useRouter()` (Next.js App Router). Path target: `/{tenantId}/{agent}/{defaultSubtab}`.

## § Microcopy (Spanish neutro LatAm)

| Lugar | Copy |
|---|---|
| Lisa tab — tabLabel | "Mi Clínica" |
| Lisa tab — role (sub-label 10px) | "Lisa" |
| Lucas tab — tabLabel | "Atraer" |
| Lucas tab — role | "Lucas" |
| Adrián tab — tabLabel | "Vender" |
| Adrián tab — role | "Adrián" |
| Valeria tab — tabLabel | "Operar" |
| Valeria tab — role | "Valeria" |
| Camila tab — tabLabel | "Mantener" |
| Camila tab — role | "Camila" |
| ConfigTab tooltip / aria-label | "Configurar" |
| Ribbon aria-label (nav wrapper) | "Agentes" |
| Avatar alt attr (cada tab) | "" (decorativo — el screen reader lee `tabLabel`+`role` del label parent) |

<!-- voseo-allowed: glosario check verification only — copy table arriba es Spanish neutro real -->
**Spanish neutro check verbatim:**
- ✅ NO voseo (no "andá", "configurá", "fijate", "dale")
- ✅ Tildes correctas: "Adrián", "Clínica", "Cómo" (donde apliquen — ninguno en este spec)
- ✅ ñ donde aplique (no aplica aquí)
- ✅ Léxico neutro (no "laburo", "quilombo")

## § Responsive breakpoints

| Breakpoint | Ribbon behavior | Sub-elementos |
|---|---|---|
| `mobile < 768px` | `overflow-x-auto` horizontal scroll. ConfigTab al final del DOM (`ml-auto`). | Avatars 28px se mantienen. Labels visibles (no colapsan). |
| `tablet 768-1024px` | igual mobile pero con más tabs visibles sin scroll | igual |
| `desktop ≥ 1024px (lg)` | Todos los 6 elementos (5 tabs + ConfigTab) caben sin scroll en modo `web`. En modo `agentic` (split 50/50, AppPanel ~640px) Lisa+Lucas+Adrián caben + parte Valeria; resto vía scroll. | igual |

**Decisión cementada:** sin breakpoint-specific markup (`md:hidden`, `lg:flex`). Una sola implementación responsive vía `overflow-x-auto`.

## § Accessibility (WCAG 2.1 AA)

- **Landmark:** `<nav role="tablist" aria-label="Agentes">` wrapper del Ribbon.
- **Tab elements:** **6 elementos** dentro del tablist — 5 agent tabs + ConfigTab. TODOS con `role="tab"` (decisión cementada Q13 batch 5 — ConfigTab es peer del tablist, pattern Slack/Notion). Cada uno `<button role="tab" aria-selected={active} tabIndex={active ? 0 : -1} aria-label="..." data-testid="ribbon-tab-{slug|config}">`. **Roving tabindex** pattern — solo el active tiene `tabIndex=0`, el resto `tabIndex=-1`.
- **Keyboard (full WAI-ARIA tablist sobre 6 elementos):**
  - `Tab` → entra al primer tab activable (active o primer tab si idle)
  - `Arrow Right` / `Arrow Left` → mueve focus entre los 6 tabs (con wrap circular: ArrowRight desde ConfigTab → Lisa; ArrowLeft desde Lisa → ConfigTab)
  - `Home` → primer tab (Lisa, índice 0)
  - `End` → último tab (ConfigTab, índice 5)
  - `Enter` / `Space` → activa el tab focused (router.push)
- **Focus visible:** `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1` (heredado tokens Shadcn).
- **Color contrast:**
  - Texto sobre `bg-agent-{agent}-soft` debe cumplir ≥ 4.5:1. Verificar tokens en `globals.css` (heredado design-tokens-theme F1-S1).
  - Texto muted-foreground sobre transparent ≥ 4.5:1.
  - Icon Settings ≥ 3:1.
- **Screen reader expected announcements:**
  - Focus en tab Lisa active: "Mi Clínica, Lisa, tab seleccionado, 1 de 6"
  - Focus en tab Lucas inactive: "Atraer, Lucas, tab, 2 de 6, presione Enter para activar"
  - Focus en ConfigTab: "Configurar, botón, 6 de 6"
- **Avatar alt:** `alt=""` (decorativo — info redundante con label parent).
- **Tooltip ConfigTab:** Radix `<Tooltip>` provee a11y aria-describedby auto.

**Grader axe:** `wcag2aa` ruleset sobre `[data-testid=ribbon]` scope. Fallar critical-violations.

## § Telemetría (TODO Fase 2)

> **NO implementar en F1-S7.** Anotado como deuda futura para no olvidar al wireear analytics provider real.

```yaml
# Pendiente Fase 2 — NO instrumentar en F1-S7:
events:
  - name: ribbon_tab_clicked
    trigger: onClick en RibbonTab o ConfigTab
    props:
      from_agent: string | null         # active anterior (lisa/lucas/adrian/valeria/camila/config/null)
      to_agent: string                  # target navigate
      tenantId: string
      timestamp: ISO8601
```

## § Brand voice

Ribbon es **chrome UI puro** (no muestra contenido user-facing dinámico per-tenant) → usa Spanish neutro estándar (no per-tenant voice). Microcopy ya verificado Spanish neutro arriba.

`personality_profiles.system_instruction` per tenant NO aplica a este componente.

## § Open questions (post-batch 4, resueltas)

> Resueltas en este spec. Listadas para audit trail.

| # | Pregunta | Resolución (batch + opción) |
|---|---|---|
| Q1 | Catalog SSoT path | Batch 1 — Reusar `lib/agent-catalog.ts` + extender campos `tabLabel` + `defaultSubtab` |
| Q2 | Mateo en ribbon | Batch 1 — NO en ribbon (default checkpoint Goal) |
| Q3 | Layout modos web vs agentic | Batch 1 — Misma horizontal en ambos modos (default) |
| Q4 | Active visual style | Batch 2 — Solo `bg-agent-{agent}-soft` tint + label `font-semibold` (flat) |
| Q5 | Hover inactive feedback | Batch 2 — `bg-muted` + `text-foreground` (Shadcn default) |
| Q6 | Mobile behavior | Batch 2 — Horizontal scroll natural (`overflow-x-auto`) |
| Q7 | ConfigTab style | Batch 3 — IconButton 40x40 + Tooltip "Configurar" + sin label visible |
| Q8 | Keyboard a11y | Batch 3 — WAI-ARIA tablist completo (Arrow + Home/End + Enter + roving tabindex) |
| Q9 | Telemetría | Batch 3 — Deferred Fase 2 (TODO documentado arriba) |
| Q10 | Microcopy tabLabel | Batch 4 — Verbatim checkpoint (Mi Clínica · Atraer · Vender · Operar · Mantener) |
| Q11 | Visual goldens scope | Batch 4 — 11 goldens (ver tabla abajo) |
| Q12 | Avatar fallback + ConfigTab RBAC | Batch 4 — `<Avatar fallback={initial}>` Shadcn · ConfigTab siempre visible (RBAC TODO Fase 2) |
| Q13 | ConfigTab semantic role (audit Playwright reveló role=null inválido en mockup) | Batch 5 — `role="tab"` dentro del `<nav role="tablist">` (peer del resto, Slack/Notion pattern). Keyboard nav recorre 6 tabs (5 agentes + Config). `End` → ConfigTab. Cementado en 03-arch.md § 2.4 desde iter 1. |
| Q14 | Tabs widths uniformes vs orgánicos | Batch 5 — Orgánicos (label-driven, sin `min-w`). Tabs toman el width necesario para su content. `flex-shrink-0` por seguridad pero sin `min-w-[Npx]`. |
| Q15 | tabLabel + role wrap a 2 líneas en widths estrechos (audit Playwright crítico) | Batch 5 — Agregar `whitespace-nowrap` a span de tabLabel + span de role en RibbonTab. Garantiza ribbon `h-14` uniforme en modo agentic (split 50/50, panel ~640px). |
| Q16 | Active:hover degrada el tint del agente (audit Playwright bug latente) | Batch 5 — Active state PRESERVA `bg-agent-{slug}-soft` durante hover (CSS specificity HARD: selector `data-active=true` debe ganar sobre `:hover`). En Tailwind: `data-[active=true]:bg-agent-{slug}-soft` tiene specificity más alta que `hover:bg-muted` natural. |

## § Visual goldens (11 total — Playwright `toHaveScreenshot`)

> Path canónico: `vitalia/frontend/e2e/__screenshots__/shell/`. Naming verbatim:

| # | File | Viewport | Theme | Estado capturado |
|---|---|---|---|---|
| 1 | `ribbon-active-lisa.png` | 1280x800 | light | active=lisa (bg-agent-lisa-soft) |
| 2 | `ribbon-active-lucas.png` | 1280x800 | light | active=lucas |
| 3 | `ribbon-active-adrian.png` | 1280x800 | light | active=adrian |
| 4 | `ribbon-active-valeria.png` | 1280x800 | light | active=valeria |
| 5 | `ribbon-active-camila.png` | 1280x800 | light | active=camila |
| 6 | `ribbon-active-config.png` | 1280x800 | light | active=config (ConfigTab ring + data-active) |
| 7 | `ribbon-idle.png` | 1280x800 | light | URL agent="foobar" inválido → ningún active |
| 8 | `ribbon-dark.png` | 1280x800 | dark | active=valeria + dark tokens |
| 9 | `ribbon-mobile-375.png` | 375x667 | light | active=lisa + horizontal scroll |
| 10 | `ribbon-keyboard-focus.png` | 1280x800 | light | active=lisa, keyboard focus en Lucas (ring-2 visible) |
| 11 | `ribbon-hover-inactive.png` | 1280x800 | light | active=lisa, mouse hover sobre Lucas (bg-muted) |

> Nota: el checkpoint original proponía 12 goldens (6 active × 2 themes). Tras batch 4 Chris ratificó set de 11 que cubre todos los estados con menos duplicación (mantenimiento más liviano si tokens cambian).

## § Deliverables (resumen para `/architect`)

| File | Acción | Notas |
|---|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` | MODIFY (EXTEND) | + campos `tabLabel`, `defaultSubtab` per agente · + constante `AGENT_RIBBON_ORDER` (excluye mateo) · agregar helper `extractAgentFromPath` (o nuevo `lib/agents/routing.ts`) |
| `vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx` | NEW | Organismo principal |
| `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx` | NEW | Molécula tab agente con Avatar + label + role |
| `vitalia/frontend/src/components/shared/shell-organism/ConfigTab.tsx` | NEW | IconButton 40x40 + Tooltip |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | MODIFY | reemplaza placeholder `<Ribbon />` real |
| `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` | MODIFY | agregar `bg-agent-{slug}-soft` allowlist 5 classes (purge safety) si faltan |
| `vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-{nav,deeplink,config-nav,invalid-agent,mobile,xss-guard,keyboard,i18n,avatar-fallback}.spec.ts` | NEW | 9 specs Playwright (1 per SC funcional) |
| `vitalia/frontend/e2e/__screenshots__/shell/ribbon-*.png` (×11) | NEW | Visual goldens |
| Unit tests Vitest (RibbonTab.test.tsx, ConfigTab.test.tsx, Ribbon.test.tsx, extractAgentFromPath.test.ts) | NEW | TDD per componente — `/architect-fe` dicta `test_construction_plan` |

## § Próximo paso post-refined

1. Chris ratifica este spec (`ratified_by_chris: true`)
2. State transition `refining → refined` (gate v4.1 CHECK: 4 base + 7 sub-cat aplicables o `not_applicable_reason` justificado ✅)
3. AUTO-CHAIN `/architect vitalia vitalia-fase1-ribbon-6-tabs` → produce ready package:
   - `03-arch.md` (con § Test Construction Plan v4.1)
   - `04-validators.yaml` (5 categorías incluyendo `architectural_validation`)
   - `05-guidelines.md` (`must_load_skills` enforceable)
   - `06-tickets.yaml` (`gherkin_coverage` mandatory)

## § Pre-handoff gate v4.1 (auto-check)

| Item | Status |
|---|---|
| 4 scenarios base (happy + negative + edge + adversarial) | ✅ (SC-1/2/3 happy + SC-4 negative + SC-5 edge + SC-6 adversarial) |
| `race_condition` sub-cat | ✅ N/A justificado (UI nav puro) |
| `concurrent_users` sub-cat | ✅ N/A justificado (sin list filterable) |
| `network_failure` sub-cat | ✅ N/A justificado (sin fetch FE; SC-9 cubre avatar PNG edge) |
| `empty_state` sub-cat | ✅ N/A justificado (lista estática) + SC-4 cubre idle |
| `large_dataset` sub-cat | ✅ N/A justificado (5 tabs fijos) |
| `accessibility` sub-cat | ✅ SC-7 (keyboard WAI-ARIA tablist) + axe wcag2aa grader |
| `i18n` sub-cat | ✅ SC-8 (microcopy Spanish neutro verbatim verify) |
| `playwright_required: true` en scenarios funcionales FE | ✅ 9/9 SC funcionales |
| `then:` verificables (NO vagos) | ✅ todos cuantificables |
| `graders:` declarados (e2e + visual_state + axe + state_check) | ✅ |
| Wireframes inline | ✅ ASCII (global + detalle + mobile) |
| Estados visuales (idle/loading/success/error/empty/active/hover/focus) | ✅ por tab + ConfigTab + avatar fallback |
| Microcopy Spanish neutro | ✅ verificado |
| Componentes reuse > new (cada NEW justificado) | ✅ 4 NEW justificados, 5 reuse |
| Responsive breakpoints | ✅ tabla 3 breakpoints |
| Accessibility section | ✅ WCAG 2.1 AA + roving tabindex + screen reader announcements |

**Gate v4.1: PASS ✅** — listo para Chris ratificar y transitar `refining → refined`.
