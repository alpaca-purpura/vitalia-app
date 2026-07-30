<!-- voseo-allowed: internal architecture documentation, design system SSoT -->

# Shell-Organism Design Contract — SSoT

> **Versión:** 1.5 · **Fecha:** 2026-06-11 (base 1.0 2026-05-22) · **Estado:** ratificado por Chris · **Branch:** wip/vitalia
>
> **★ v1.5 — EL CHROME VIVE EN `@luana/ui-kit` (lift `platform-lift-shell-chrome-ui-kit`, proposal 2026-06-01 migrated):** la implementación canónica del chrome (ShellLayout(Client) ex-ShellOrganismLayout, Supervisor{Sidebar,CollapsedStrip,History} ex-Valeria*, ChatPanel/ChatHeader/Chat*, Ribbon(Tab), SubTabsBar/SubTab/SubSubTabsBar, TopBarShell, AppPanelSlot, useViewportGuard, createShellStore) vive en `core/@luana/ui-kit/src/organism/shell/` (v0.4.0, brand-agnostic por props+CSS vars). Vitalia lo consume vía `ShellLayoutWire` (`app/[tenantId]/(shell-organism)/_components/`) que inyecta brand data (AGENT_CATALOG, supervisorName='Valeria', testIds legacy, tokens). Este contrato sigue siendo el SSoT del COMPORTAMIENTO + brand data de vitalia; la implementación se versiona en el kit (CHANGELOG 0.4.0). Quedan brand-local: LogoMark, ThemeToggle, Tenant*, SubTabContent (dispatcher), _agent-tw-classes, AddClinicPlaceholderModal.
>
> **Propósito:** documento canónico que cementa CADA átomo · molécula · organismo · template del shell-organism agéntico Vitalia. TODA historia de usuario Fase 1 y Fase 2 cita este doc como referencia técnica. Sin este doc, las historias serían textos sueltos sin contrato visual ni funcional verificable.
>
> **Fuente visual:** `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` (mockup ratificado 2026-05-22). Este Design Contract traduce ESE mockup a Next.js + Shadcn UI + Vitalia tokens.

---

## § 1 — Decisiones cementadas (input para Design Contract)

Pre-decisión Chris 2026-05-22, antes de empezar este doc:

| # | Decisión | Implicancia |
|---|---|---|
| D1 | Shadcn UI se instala AHORA en `vitalia/frontend/` | `npx shadcn@latest init` en F1-S0. Componentes copy-paste local |
| D2 | **Deprecar `.vt-*` utility classes COMPLETO** | Migrar a Tailwind directo + Shadcn. Stories incluyen migración por feature |
| D3 | Migration path = **route group paralelo** `(shell-organism)/` | Coexiste con `/(dashboard)/` viejo hasta Fase 2 completa |
| D4 | **Verificar Tailwind v4 empíricamente** | Story F1-S0 incluye `make dev-vitalia` + browser visual check |
| D5 | Atomic design strict | Componentes clasificados en átomos · moléculas · organismos · templates · pages |
| D6 | Cada componente ENTRA al sistema solo con Playwright golden visual + test funcional | Zero deuda técnica desde origen |

---

## § 2 — Atomic Design Layers — nomenclatura cementada

```
átomos       → primitivos sin lógica de dominio (Button, Input, Avatar, Icon)
moléculas    → átomos combinados con propósito específico (TabButton, RailIconButton, TenantOption)
organismos   → composiciones funcionales completas con estado (TopBarGlobal, ValeriaSidebar, Ribbon)
templates    → layouts que componen organismos (ShellOrganismLayout 50/50)
pages        → rutas Next.js que renderizan templates (/(shell-organism)/[agent]/[subtab]/page.tsx)
```

**Convención de paths Vitalia (FSD-Lite):**

```
vitalia/frontend/src/
├── components/
│   ├── ui/                       # Átomos Shadcn copy-paste (Button, Input, Avatar, ...)
│   └── shared/                   # Moléculas + organismos compartidos cross-feature
│       ├── shell-organism/       # Organismos del shell-organism (TopBarGlobal, ValeriaSidebar, Ribbon, SubTabs)
│       └── ...                   # Otros shared existentes (mantienen ubicación actual)
├── features/
│   └── {agent}/                  # Features per agente: lisa, lucas, adrian, valeria, camila, config
│       ├── components/           # Componentes específicos del agente
│       ├── api/
│       ├── hooks/
│       ├── store/
│       ├── types/
│       └── index.ts (barrel)
├── app/
│   ├── (dashboard)/              # LEGACY — coexiste hasta Fase 2 completa
│   └── [tenantId]/
│       └── (shell-organism)/     # NUEVO route group — shell-organism
│           ├── layout.tsx         # ShellOrganismTemplate (50/50)
│           ├── page.tsx           # Default landing
│           └── [agent]/
│               ├── layout.tsx
│               ├── page.tsx       # Default sub-tab (primera del agente)
│               └── [subtab]/
│                   └── page.tsx   # Vista específica
├── lib/
│   ├── tokens/                   # CSS vars + Tailwind theme extend
│   ├── api/                      # fetchClient (HIPAA dual filter)
│   └── ...
├── stores/                       # Zustand stores globales
│   ├── shell-state.ts            # NEW: valeria sidebar state, theme, active tenant
│   └── ...
└── hooks/                        # Hooks globales (useTenantLocale, useTheme, useShellState)
```

---

## § 3 — Inventario exhaustivo: mockup → componentes

> **Cada fila es un contrato.** El builder de la story respectiva DEBE producir EXACTAMENTE este componente con EXACTAMENTE estas props/state/a11y. Cualquier desviación falla el Playwright visual golden + auditor.

### § 3.1 — Átomos (átomos Shadcn instalables)

| Mockup ref | Átomo | Shadcn CLI install | Path local | Props clave | Usado en |
|---|---|---|---|---|---|
| `.topbar-btn` con 🌙/☀️ | `IconButton` (wrapper Button) | `npx shadcn add button` | `components/ui/button.tsx` | `variant="ghost" size="icon"` | TopBarGlobal · Rail · History toolbar |
| Logo "V" cuadrado gradiente | `LogoMark` | NEW (no Shadcn) | `components/shared/shell-organism/LogoMark.tsx` | `size, variant: full\|mark` | TopBarGlobal |
| `.tenant-item-avatar` "SP", "DM" | `Avatar` + fallback letras | `npx shadcn add avatar` | `components/ui/avatar.tsx` | `src, alt, fallback` | TenantSwitcher · Ribbon tabs · Chat header |
| `.tenant-switcher-btn` con ▾ | `Button` + chevron | `npx shadcn add button` | idem | `variant="outline"` | TopBarGlobal |
| `.tenant-switcher-dropdown` | `DropdownMenu` | `npx shadcn add dropdown-menu` | `components/ui/dropdown-menu.tsx` | items array | TenantSwitcher |
| `.history-search input` | `Input` | `npx shadcn add input` | `components/ui/input.tsx` | `placeholder` | History panel · Composer |
| `.rail-btn` cuadrado | `Button variant="ghost" size="icon"` | (Button reuso) | idem | + Tooltip wrap | Rail · History toolbar |
| `.kbd` (keyboard hint) | `Kbd` | NEW | `components/ui/kbd.tsx` | `children` | Footer mockup · Tooltips |
| `.chat-mode-pill` 🤖 | `Badge` | `npx shadcn add badge` | `components/ui/badge.tsx` | `variant="outline"` | Chat header · Camila modes · Adrián modes |
| `.composer-input` textarea | `Textarea` | `npx shadcn add textarea` | `components/ui/textarea.tsx` | `rows, placeholder` | Composer |
| `.composer-send` button | `Button` | (Button reuso) | idem | `variant="default"` | Composer |
| `.msg-bubble` user/bot | `MessageBubble` | NEW | `components/shared/shell-organism/MessageBubble.tsx` | `role: user\|bot, content` | Chat messages |
| `.msg-thinking` dots | `TypingIndicator` | NEW | `components/shared/shell-organism/TypingIndicator.tsx` | — | Chat messages while streaming |
| `.msg-delegate` italic | `DelegateMarker` | NEW | `components/shared/shell-organism/DelegateMarker.tsx` | `fromAgent, toAgent` | Chat messages |
| `.toggle-pill` segmented control | `Tabs` (Shadcn) | `npx shadcn add tabs` | `components/ui/tabs.tsx` | `defaultValue, items[]` | Catálogo\|Escalera · Kanban\|Lista · 3-modos Camila/Adrián |
| Tooltip al hover rail btn | `Tooltip` | `npx shadcn add tooltip` | `components/ui/tooltip.tsx` | `content, side` | Rail buttons · Topbar icons |
| Scrollbar styled | Tailwind utility | (Tailwind native) | global.css | — | History list · Chat messages · Content |

### § 3.2 — Moléculas (composiciones específicas)

| Mockup ref | Molécula | Composición | Props | State | Path |
|---|---|---|---|---|---|
| `.tenant-switcher-btn` + dropdown | `TenantSwitcher` | DropdownMenu + Avatar + Button | `currentTenant, tenants[], onSwitch` | localStorage `x-tenant-id` | `components/shared/shell-organism/TenantSwitcher.tsx` |
| `.topbar-btn` theme | `ThemeToggle` | Button + Icon (Moon/Sun) | — | localStorage `vitalia-theme` · ThemeProvider | `components/shared/shell-organism/ThemeToggle.tsx` |
| `.ribbon-tab` (5 agentes) | `RibbonTab` | Avatar + Labels + active border | `agent: AgentKey, active, onClick` | — (controlled) | `components/shared/shell-organism/RibbonTab.tsx` |
| `.ribbon-tab` ⚙️ Configurar | `ConfigTab` | IconBox + Labels | `active, onClick` | — | `components/shared/shell-organism/ConfigTab.tsx` |
| `.sub-tab` línea 2 | `SubTab` | Button con tint color agente | `label, color, active, onClick` | — | `components/shared/shell-organism/SubTab.tsx` |
| `.tenant-item` dropdown row | `TenantOption` | Avatar + Meta + active state | `tenant, active` | — | `components/shared/shell-organism/TenantOption.tsx` |
| `.history-item` row | `HistoryItem` | Title + Meta + active state | `conv: ConvSummary, active` | — | `components/shared/shell-organism/HistoryItem.tsx` |
| `.history-group` + label | `HistoryGroup` | Section + items | `label, items[]` | — | `components/shared/shell-organism/HistoryGroup.tsx` |
| `.chat-header` | `ChatHeader` | Avatar + Name + Status + Pill | `agent: 'valeria', status, mode` | — | `components/shared/shell-organism/ChatHeader.tsx` |
| `.empty-state` placeholder | `EmptyState` | Icon + Title + Desc | `icon, title, desc, action?` | — | `components/shared/shell-organism/EmptyState.tsx` |
| `.placeholder-card` grid card | `PlaceholderCard` | Icon + Title + Desc + Status dot | `icon, title, desc, status: shipped\|planned\|todo` | — | `components/shared/shell-organism/PlaceholderCard.tsx` |
| Pipeline col header + cards | `PipelineColumn` | Header + cards stack | `stage, count, value, leads[]` | — | `features/adrian/components/embudo/PipelineColumn.tsx` |
| Agenda slot cell | `AgendaSlot` | Status color border + content | `slot: SlotData, onClick` | — | `features/valeria/components/agenda/AgendaSlot.tsx` |

### § 3.3 — Organismos (composiciones funcionales con estado)

| Mockup ref | Organismo | Composición | State management | Keyboard | Path |
|---|---|---|---|---|---|
| `.topbar` header | `TopBarGlobal` | LogoMark + (ThemeToggle + TenantSwitcher) ★ cluster derecho orden fijo | — (consume hooks) | — | `components/shared/shell-organism/TopBarGlobal.tsx` |
| `.panel-valeria` 50% izq | `ValeriaSidebar` | `ValeriaCollapsedStrip` OR `ValeriaChat` + toggle historial (★ v1.4) | zustand `shellStore.valeriaOpen` + `historyOpen` | `C` colapsar · `F` abrir historial · `N` nueva conv · `Esc` cerrar overlays · `Cmd+K` focus composer | `components/shared/shell-organism/ValeriaSidebar.tsx` |
| ★ v1.4 NUEVO — tira 44px estado A | `ValeriaCollapsedStrip` | avatar real Valeria (thumbnail.png) + dot presencia + label "Valeria" · click → `openChat()` | — (recibe valeriaOpen=closed) | aria-label "Abrir a Valeria" · click/Enter/Space | `components/shared/shell-organism/ValeriaCollapsedStrip.tsx` |
| ~~`.valeria-rail` 60px~~ | ~~`ValeriaRail`~~ | **RETIRADO en T-3** (2026-06-10). Reemplazado por `ValeriaCollapsedStrip` (44px, con avatar real). La lógica de iconos de acceso rápido era prematura — Valeria opens to chat, no a rail de acciones. | — | — | ~~`components/shared/shell-organism/ValeriaRail.tsx`~~ DELETED |
| `.valeria-history` panel lateral | `ValeriaHistory` | Header `[+][◷][⟨]` + Search + HistoryGroup[] · botón "+" = nueva conv · "◷" = toggle historial · "⟨" = colapsar sidebar | React Query convs · search local · historyOpen additive push 260px fijo | — | `components/shared/shell-organism/ValeriaHistory.tsx` |
| `.valeria-chat` | `ValeriaChat` | ChatHeader + Messages + Composer | zustand `chatStore.messages` · WebSocket | (delegado) | `components/shared/shell-organism/ValeriaChat.tsx` |
| `.ribbon` 5 especialistas + Plataforma | `Ribbon` | RibbonTab[] + PlataformaTab | router state (active from URL) | — | `components/shared/shell-organism/Ribbon.tsx` |
|  ↳ ★★ v1.2 (2026-05-30) | Antes: 6 tabs (con Valeria + "Configurar"). Ahora: 5 especialistas (sin Valeria) + "Plataforma" | — | — | — |
| `.sub-tabs` línea 2 | `SubTabsBar` | SubTab[] (dinámico per tab) | router state | — | `components/shared/shell-organism/SubTabsBar.tsx` |
| barra N3-dynamic del detalle (patrón list→detail · § 7.2.2) | `EntitySubNavBar` ★ v1.4 CONSUMIDO de `@luana/ui-kit` | Back `‹ {rootLabel}` + identidad (avatar+nombre) + leaves (rutas) · prop `activeLeaf?: string\|null` agregada al kit (d3b06b11) | prop `entity` (null=directory mode → leaves disabled) · `activeLeaf` · NO en `AGENT_SUBSUBTABS` | roving tabindex + flechas L/R/Home/End | `import { EntitySubNavBar } from '@luana/ui-kit'` — brand-local RETIRADO (T-5) |
| `[doctor-id]/layout.tsx` workspace del detalle | `StaffWorkspaceShell` ★ v1.4 usa `EntityWorkspaceLayout` de kit | `EntityWorkspaceLayout` de `@luana/ui-kit` (sticky EntitySubNavBar + content slot) · construye hrefs de leaves · `usePathname` → activeLeaf · `activeLeaf` override prop | React Query doctor · zustand `staff-ui-store` | (delegado) | `features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx` |
| `[lead-id]/layout.tsx` workspace embudo (★ v1.4) | `LeadWorkspace` usa `EntityWorkspaceLayout` de kit | `EntityWorkspaceLayout` de `@luana/ui-kit` | React Query lead · zustand `crm-ui-store` | (delegado) | `features/adrian/components/embudo/workspace/LeadWorkspace.tsx` |
| `.content` body derecho | `ContentArea` | slot — children = page actual | — (Next.js routing) | — | (es el `{children}` del layout) |

> **★ v1.4 N3 consumers — brand-local `EntitySubNavBar.tsx` RETIRADO (commit `a042e1df`):** el archivo `components/shared/shell-organism/EntitySubNavBar.tsx` (258 líneas) fue eliminado. Todo consumer importa de `@luana/ui-kit` v0.3.x. El arch-test `test-no-cross-brand-shell-mirror.test.ts` 31/31 PASS verifica ausencia del mirror local. Evidence: T-5-result.md.

### § 3.4 — Templates (layouts)

| Mockup ref | Template | Composición | Variantes | Path |
|---|---|---|---|---|
| Layout shell completo | `ShellOrganismLayout` / `ShellOrganismLayoutClient` | TopBarGlobal + resizable panel `[ValeriaSidebar \| ContentSection]` (★ v1.4: `react-resizable-panels` + `ssr:false` dynamic; splitter persistido en `shell-store`) | ≥1280 default 30/70 · [1024,1280) clamp min 320px · <1024 drawer Shadcn (Valeria overlay, CSS gate `hidden lg:block` separator) | `app/[tenantId]/(shell-organism)/layout.tsx` + `ShellOrganismLayoutClient.tsx` |
| ContentSection | `ContentSection` | Ribbon + SubTabsBar + ContentArea | — | inline en layout o componente extraído |

> **★ v1.4 — `ShellModeToggle` y modos `agentic`/`web` RETIRADOS (T-2):** el toggle chip web/agéntico fue eliminado de `TopBarGlobal` y `ShellOrganismLayout`. No existe selector de modo. El shell siempre está en modo agéntico (ValeriaSidebar siempre presente). El antiguo modo "web" (Valeria → rail 60px, content 100%) no existe: colapsar Valeria ahora muestra `ValeriaCollapsedStrip` (44px), no una expansión del content a 100%. Commits: `b19a227d`, `b522043a` (T-2-result.md).

### § 3.5 — Pages (rutas concretas)

| Path Next.js | Renderiza | Default redirect |
|---|---|---|
| `/[tenantId]/(shell-organism)/page.tsx` | landing del shell | redirige a `/[tenantId]/(shell-organism)/lisa/marca` (default Lisa→Marca) |
| `/[tenantId]/(shell-organism)/[agent]/page.tsx` | landing del agente | redirige a primera sub-tab del agente |
| `/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | sub-tab específica | renderiza componente per agente+subtab |
| `/[tenantId]/(shell-organism)/[agent]/[subtab]/[entityId]/layout.tsx` | N3-dynamic DETALLE — monta `EntitySubNavBar` + SSR entidad + slot `{children}` (patrón list→detail · § 7.2.2 · staff usa `[doctor-id]`) | la lista/master es el `[subtab]/page.tsx` de arriba |
| `/[tenantId]/(shell-organism)/[agent]/[subtab]/[entityId]/[leaf]/page.tsx` | leaf activo del detalle (ej. staff: `perfil`·`horarios`·`servicios`) | `[entityId]` redirige al 1er leaf |

### § 3.6 — TopBar cluster (★ v1.4 hardening T-2)

> Contrato fijo post T-2. No agregar ni reordenar sin anotarlo acá.

```
[LogoMark]  ──────────────────────────  [ThemeToggle] [TenantSwitcher]
                  flex-1 (espacio)            cluster derecho (orden fijo)
```

- **Cluster derecho:** `ThemeToggle` primero, `TenantSwitcher` segundo. Orden inmutable.
- **Eliminado:** chip modo web/agéntico (`ShellModeToggle`) — RETIRADO en T-2. No reinstalar.
- **ThemeToggle:** `<button aria-label="Cambiar tema (claro/oscuro)" aria-pressed={isDark}>` — Moon/Sun icon swap vía `next-themes` `useTheme`.
- **TenantSwitcher:** DropdownMenu Radix · `aria-label="Cambiar clínica"` en trigger.
- **wiring dark:** `next-themes` vive en `vitalia/frontend/src/app/providers.tsx` (intacto post-hardening). NO mover.

### § 3.7 — Dark mode (★ v1.4 hardening T-6)

> Token audit completado. Hardcoded colors eliminados del core chrome.

| Archivo | Campo corregido | Antes | Después | Commit |
|---|---|---|---|---|
| `features/lisa/components/staff/DoctorPerfilView.tsx` l.348 | background wrapper | `bg-white` | `bg-background` | T-6 |
| `components/shared/shell-organism/TakeoverBanner.tsx` l.91 | banner dark variant | (ninguna) | `dark:bg-amber-600 dark:border-amber-600` | T-6 |

**Estado dark mode post-hardening:**
- CSS vars `--background`, `--foreground`, `--card`, etc. definidas en `globals.css` §5.1 — dark variants presentes en `.dark {}` block.
- `next-themes` wiring en `providers.tsx` — `ThemeProvider attribute="class"` (class-based toggle).
- No se agregaron nuevas dark variants a `globals.css` en T-6 (las existentes cubrían todos los casos restantes).
- ContactSidebar BUG (rgb(255,255,255) hardcoded) resuelto en T-2/T-3 (antes de T-6).

### § 3.8 — Soft-nav (★ v1.4 hardening T-4)

> Soft-nav = navegación SPA sin reload completo. Afecta principalmente chips/badges de métricas en embudo.

**Decisión A (implementada, commits T-4):**
- `EmbudoMetrics.tsx` frozen-kpi-badge: `<a href>` (band-aid hard-nav) → `<Link>` de `next/link` (soft-nav restaurado).
- `proxy.ts` edge-redirect: verificado sin cambios. El rewrites `/api`→BE ya existía como `bareTenantLandingRedirect` 307.
- `next.config.ts` rewrites `/api`→BE: agregado en T-7 para fix bug global `useTenants 404`.
- `ssr:false` en `ShellOrganismLayoutClient` (dynamic import) conservado — `react-resizable-panels` v4 requiere browser API. El edge-redirect en `proxy.ts` cubre el problema "soft-nav hacia layout ssr:false → Rendered more hooks" (Next 16.2.3 bug, ver `vitalia/docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md`).

**Anti-patrón prohibido:** `<a href>` para navegación intra-shell. Siempre `<Link>` de `next/link` o `router.push` para rutas dentro del shell-organism.

---

## § 4 — Shadcn CLI install plan (story F1-S0)

```bash
# Story F1-S0 ejecuta:
cd vitalia/frontend
npx shadcn@latest init
# Interactive prompts:
#  - Style: New York (vs Default)
#  - Base color: Slate
#  - CSS variables: yes
#  - Tailwind config: existing
#  - Import alias: @/ (already configured)

# Después de init, instalar primitivos del Design Contract § 3.1:
npx shadcn@latest add button avatar dropdown-menu input badge textarea tabs tooltip

# Componentes adicionales por agente (en stories Fase 2 según necesidad):
# Lisa Servicios canvas → npx shadcn add card scroll-area separator
# Adrián Embudo → npx shadcn add card + @dnd-kit/core (NPM, NO shadcn)
# Adrián Inbox → npx shadcn add sheet popover scroll-area
# Camila Voz → npx shadcn add accordion progress
# Valeria Agenda → custom date picker (no Shadcn primitive — built composite)
# Config Conexiones → npx shadcn add sheet card switch
```

**Output:** `vitalia/frontend/src/components/ui/` poblado · `components.json` versionado · primitives Tailwind/Radix listos.

---

## § 5 — Tokens system (nuevo, post-deprecación `.vt-*`)

> **Cambio estructural:** los 150+ `.vt-*` utility classes se reemplazan por:
> 1. CSS variables Shadcn-style (`--background`, `--foreground`, `--primary`, etc.) que VALORAN a colores Vitalia
> 2. Tailwind utility classes nativas (`bg-background`, `text-muted-foreground`, etc.)
> 3. Brand tokens extras (`--agent-lisa`, `--agent-lucas`, etc.) para colores agentes

### § 5.1 — CSS variables canónicas (light + dark)

```css
/* vitalia/frontend/src/app/globals.css */

@layer base {
  :root {
    /* Surface (Shadcn standard) */
    --background: 0 0% 100%;              /* #ffffff */
    --foreground: 240 10% 4%;             /* near-black */
    --card: 0 0% 100%;
    --card-foreground: 240 10% 4%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 4%;

    /* Primary = Vitalia cyan (Adrián) */
    --primary: 198 99% 49%;               /* #01b2f8 */
    --primary-foreground: 0 0% 100%;

    /* Secondary = neutral */
    --secondary: 240 5% 96%;
    --secondary-foreground: 240 6% 10%;

    /* Muted */
    --muted: 240 5% 96%;
    --muted-foreground: 240 4% 46%;

    /* Accent = Vitalia purpura (Valeria) */
    --accent: 287 53% 37%;                /* #7b2d91 */
    --accent-foreground: 0 0% 100%;

    /* Destructive */
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 98%;

    /* Border + input + ring */
    --border: 240 6% 90%;
    --input: 240 6% 90%;
    --ring: 198 99% 49%;                  /* matches primary */

    /* Radius */
    --radius: 0.625rem;

    /* === Agent tokens === */
    --agent-lisa: 156 100% 41%;           /* #00D084 — NEW token */
    --agent-lisa-soft: 156 80% 92%;
    --agent-lucas: 0 0% 7%;               /* #111111 — NEW token */
    --agent-lucas-soft: 0 0% 92%;
    --agent-adrian: 198 99% 49%;          /* #01b2f8 = same as --primary */
    --agent-adrian-soft: 197 90% 89%;
    --agent-valeria: 287 53% 37%;         /* #7b2d91 */
    --agent-valeria-soft: 287 53% 90%;
    --agent-camila: 244 84% 32%;          /* #180d95 */
    --agent-camila-soft: 244 53% 92%;
    --agent-mateo: 53 99% 51%;            /* #fee209 — reservado para Mateo (transversal sin tab) */
    --agent-config: 240 4% 46%;           /* neutral gray */
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

    --accent: 287 53% 50%;                /* lighter para dark mode */
    --accent-foreground: 0 0% 98%;

    --destructive: 0 63% 31%;
    --destructive-foreground: 0 0% 98%;

    --border: 240 4% 20%;
    --input: 240 4% 20%;
    --ring: 198 99% 49%;

    /* Agent tokens dark variants */
    --agent-lisa-soft: 156 60% 15%;
    --agent-lucas-soft: 0 0% 20%;
    --agent-adrian-soft: 198 60% 20%;
    --agent-valeria-soft: 287 40% 25%;
    --agent-camila-soft: 244 50% 20%;
  }
}
```

### § 5.2 — Tailwind config extend

```ts
// vitalia/frontend/tailwind.config.ts
export default {
  // ...
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        accent:  { DEFAULT: 'hsl(var(--accent))',  foreground: 'hsl(var(--accent-foreground))' },
        muted:   { DEFAULT: 'hsl(var(--muted))',   foreground: 'hsl(var(--muted-foreground))' },
        card:    { DEFAULT: 'hsl(var(--card))',    foreground: 'hsl(var(--card-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },

        // Agent tokens
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
      borderRadius: { lg: 'var(--radius)', md: 'calc(var(--radius) - 2px)', sm: 'calc(var(--radius) - 4px)' },
    },
  },
}
```

### § 5.3 — Deprecación `.vt-*` (plan)

Story F1-S0 incluye scan + plan deprecación. Strategy:

1. **Rename block:** todas las `.vt-bg-*`, `.vt-text-*`, `.vt-border-*` apuntan a las nuevas vars Shadcn-style (compatibilidad temporal — 1 release)
2. **Migration por feature:** cuando una feature migra al shell-organism (Fase 2), su código se refactoriza a Tailwind directo
3. **Final drop:** cuando 100% del código FE usa Tailwind directo, eliminamos `.vt-*` block del globals.css

**Story dedicada:** F2-S23 `vitalia-fase2-vt-deprecation-final` (último step, después de todas las Fase 2 features migradas).

---

## § 6 — State management (zustand stores)

### § 6.1 — `shellStore` (★ hardening T-1 2026-06-10 — máquina nueva)

> **Cambio breaking v1.4:** `ValeriaState = 'collapsed' | 'rail' | 'full'` y `ShellMode = 'agentic' | 'web'` **RETIRADOS**. Reemplazados por máquina de 2 dimensiones ortogonales. Commits: ver T-1-result.md (vitalia-shell-core-hardening).

```ts
// vitalia/frontend/src/stores/shell-store.ts
// Máquina Valeria post-hardening (T-1)

// ★ Estados activos (2 valores)
type ValeriaOpen = 'closed' | 'chat'
// 'closed' → tira 44px (ValeriaCollapsedStrip) — estado A
// 'chat'   → chat visible a la izquierda — estado B

// ★ historyOpen = dimensión aditiva (bool, NO persiste en storage)
// true → panel de historial empuja 260px fijos a la derecha de la sidebar
// No modifica el splitter central ni el ancho base del panel Valeria

// ★ RETIRADOS (no existen en runtime):
// - ValeriaState = 'collapsed' | 'rail' | 'full'
// - ShellMode = 'agentic' | 'web'
// - shellMode / setShellMode
// - cycleValeriaState (lógica inline reemplaza)

interface ShellStore {
  valeriaOpen: ValeriaOpen       // persiste
  historyOpen: boolean           // NO persiste (session-only)
  setValeriaOpen: (s: ValeriaOpen) => void
  toggleHistory: () => void
  openChat: () => void           // 'closed' → 'chat'
  closeValeria: () => void       // 'chat' → 'closed'
}

// Implementación usa createSsrSafePersistedStore de @luana/hooks
// (evita hydration mismatch al leer localStorage en SSR)
// Persiste solo valeriaOpen; historyOpen arranca false siempre
```

**Máquina de estados:**

```
              ┌──── strip click / reopenValeria() ────┐
              ▼                                        │
[closed] ─── openChat() ──────────────────────────► [chat]
              ▲                                        │
              └──── closeValeria() / ◀ colapsar ───────┘

historyOpen  ──── toggleHistory() ──►  true / false
             (additive — no cambia valeriaOpen)
```

**Layout implications:**

| valeriaOpen | historyOpen | Left panel |
|---|---|---|
| `closed` | — | 44px tira `ValeriaCollapsedStrip` (click → `chat`) |
| `chat` | false | Panel chat base (clamp 320px, default ~30%) |
| `chat` | true | Panel chat + 260px fijos `ValeriaHistory` (push, no overlay) |

**Responsivo:** `<1024px` → Valeria en drawer/overlay independientemente del store (CSS gate — `ShellOrganismLayoutClient` usa `hidden lg:block` separator + `Drawer` de Shadcn).

### § 6.2 — `themeStore` (NEW — light/dark)

> Alternativa: usar `next-themes` (recomendado). Story F1-S1 evalúa next-themes vs zustand custom.

### § 6.3 — `tenantStore` (NEW — clinic activa)

```ts
// vitalia/frontend/src/stores/tenant-store.ts
interface TenantStore {
  activeTenantId: string | null
  availableTenants: Tenant[]
  switchTenant: (id: string) => void  // persist + hard redirect
}
```

### § 6.4 — `chatStore` (NEW — Valeria chat)

Story F1-S6 define schema completo (mensajes + streaming state + conversation ID).

---

## § 7 — Routing structure cementada

### § 7.1 — App Router tree

```
app/
├── (auth)/                                 # LEGACY — sign-in / sign-up
├── (dashboard)/                            # LEGACY — coexiste hasta migración Fase 2 completa
│   ├── page.tsx
│   ├── patients/...
│   ├── appointments/...
│   ├── brand-studio/[section]/page.tsx
│   ├── fidelizacion/page.tsx
│   ├── medical-compliance/page.tsx
│   └── ...
├── [tenantId]/
│   ├── (shell-organism)/                   # NEW route group — shell-organism
│   │   ├── layout.tsx                       # ShellOrganismLayout (50/50)
│   │   ├── page.tsx                         # → redirect /[tenantId]/(shell-organism)/lisa/marca
│   │   └── [agent]/
│   │       ├── layout.tsx                   # — (vacío, propaga al children)
│   │       ├── page.tsx                     # → redirect a primera sub-tab del agente
│   │       └── [subtab]/
│   │           ├── page.tsx                 # sub-tab content (single panel) o redirect a primera subsubtab
│   │           ├── [subsubtab]/page.tsx     # ★ N3-static (sub-sub-tabs cabecera, opcional per AGENT_SUBSUBTABS)
│   │           └── [entityId]/              # ★ N3-dynamic (list→detail · § 7.2.2 · staff: [doctor-id])
│   │               ├── layout.tsx           #     monta EntitySubNavBar + SSR entidad + slot
│   │               └── [leaf]/page.tsx      #     leaf activo (ej. perfil·horarios·servicios)
│   └── ... (otras rutas legacy bajo [tenantId] si las hubiera)
└── layout.tsx (root)                       # Providers globales
```

### § 7.2 — Agent + subtab whitelist

```ts
// vitalia/frontend/src/lib/routing/shell-routes.ts
export const SHELL_AGENTS = ['lisa', 'lucas', 'adrian', 'valeria', 'camila', 'config'] as const
export type AgentKey = typeof SHELL_AGENTS[number]

export const AGENT_SUBTABS: Record<AgentKey, readonly string[]> = {
  lisa:    ['marca', 'doctores', 'servicios', 'compliance'],
  lucas:   ['lanzar', 'envuelo', 'recursos', 'resultados', 'mercado'],
  adrian:  ['inbox', 'embudo', 'outbound', 'propuestas'],
  valeria: ['agenda', 'pacientes'],
  camila:  ['voz', 'reactivar', 'multiplicar', 'reputacion'],
  config:  ['cuenta', 'conexiones', 'avanzado'],
} as const

export const AGENT_DEFAULT_SUBTAB: Record<AgentKey, string> = {
  lisa: 'marca',
  lucas: 'lanzar',
  adrian: 'inbox',
  valeria: 'agenda',
  camila: 'voz',
  config: 'cuenta',
}

// ★ NEW v1.1 (2026-05-27) — Nivel 3 estático (sub-sub-tabs cabecera) opcional per (agent, subtab).
// Solo declarar cuando la sub-tab agrupa 3+ vistas conceptualmente discretas.
// Default redirect cuando user llega a [agent]/[subtab]/ sin subsubtab: primera entry del array (KISS).
export const AGENT_SUBSUBTABS: Partial<Record<AgentKey, Partial<Record<string, readonly string[]>>>> = {
  lisa: {
    marca: ['identidad', 'voz-y-tono', 'presencia'],
    // doctores: undefined  → single panel
    // servicios: ['catalogo', 'escalera']  (futuro lisa-servicios)
    // compliance: ['semaforo', 'retencion', 'reportes']  (futuro lisa-compliance)
  },
  // Otros agentes declaran subsubtabs cuando aplica (en su story dedicada)
} as const
```

### § 7.2.1 — Niveles de navegación (★ v1.1 cementación 2026-05-27 · ★★ v1.2 addendum 2026-05-30)

```
N1 (Ribbon)           → [agent]                                    → 5 especialistas + tab Plataforma
                                                                      ★★ v1.2: Lisa · Mateo · Adrián · Lucas · Camila + Plataforma
                                                                      (antes: Lisa · Lucas · Adrián · Valeria · Camila + Configurar)
                                                                      Valeria = ValeriaSidebar (supervisora, NO en Ribbon)
                                                                      Mateo = Operar/Mi Día (agenda + bookings + pacientes del día)
N2 (SubTabsBar)       → [agent]/[subtab]                           → AGENT_SUBTABS whitelist
N3-static (NEW)       → [agent]/[subtab]/[subsubtab]               → AGENT_SUBSUBTABS opcional
N3-dynamic            → [agent]/[subtab]/[entityId]/[leaf]         → detalle de entidad (patrón list→detail · EntitySubNavBar · § 7.2.2)
```

**Reglas:**
- N3-static y N3-dynamic son **modos alternativos** de una sub-tab (vistas fijas de UNA hoja **O** colección de entidades list→detail — no ambas en el mismo segmento, porque `[subsubtab]` y `[entityId]` colisionarían)
- N3-static es **opcional** — solo cuando la sub-tab agrupa 3+ vistas discretas (Anti-pattern: Shadcn `Tabs` body en lugar de cabecera N3-static)
- N3-dynamic usa el patrón **list→detail** (`EntitySubNavBar`, ver § 7.2.2) — el sub-tab es una **lista** de entidades; al entrar a una, su **detalle** es un workspace con back + identidad + leaves (rutas). El `Sheet` (Shadcn) queda SOLO para paneles transitorios livianos (ej. valeria-agenda `AppointmentDrawer`), **NUNCA** para el detalle canónico de un item
- **Anti-pattern PROHIBIDO:** content tab nav fuera de la cabecera shell (sería "Nivel 4" implícito)

**Source decisión:** ADR-vitalia-004 v1.1 § 3.1.1 (cementación 2026-05-27 origen lisa-marca refinement).

### § 7.2.2 — Patrón list→detail (`EntitySubNavBar`) — ★ canónico para todo "lista → detalle" (cement 2026-06-03 · ★★ v1.4 lifted a `@luana/ui-kit` 2026-06-10)

> **Origen:** inventado en Vitalia (`lisa/staff` doctores · `ADR-vitalia-004 § D-1`). Adoptado cross-brand 2026-06-03 (Chris) — Nicolify lo portó re-temizado (ICP→buyers). **Reemplaza la noción stale "N3-dynamic = Sheet drawer / `[...slug]` catch-all".**
>
> **★★ v1.4 (T-5 hardening 2026-06-10):** `EntitySubNavBar` y `EntityWorkspaceLayout` CONSUMIDOS de `@luana/ui-kit` v0.3.x. Brand-local `components/shared/shell-organism/EntitySubNavBar.tsx` ELIMINADO (commit `a042e1df`). Prop `activeLeaf?: string | null` agregada al kit en commit `d3b06b11` (backward-compatible). Consumers vitalia: `StaffWorkspaceShell` + `LeadWorkspace` + `NewLeadPage`. Reference impl: `import { EntitySubNavBar, EntityWorkspaceLayout } from '@luana/ui-kit'`.

Cuando un sub-tab N2 **es una colección de entidades** (staff/doctores, pacientes, cuentas…) que se **listan** y luego se **entra al detalle** de una, se usa `EntitySubNavBar` (NO Sheet, NO catch-all):

- **Master (lista):** `[agent]/[subtab]/page.tsx` — grid/lista de cards. SIN `EntitySubNavBar` (es la lista).
- **Detalle (workspace):** click en un item → `[agent]/[subtab]/[entityId]/[leaf]` (staff: `[doctor-id]`). El `layout.tsx` monta `EntitySubNavBar` como **barra N3 superior** (stack Ribbon→SubTabsBar→**EntitySubNavBar**→contenido — NO un card flotante dentro del contenido).
- **Anatomía:** `[‹ {rootLabel}]  |  {avatar} {nombre}  |  {leaves…}` — leaves **pegadas a la izquierda** (después de la identidad).
- **Back link** (`rootLabel`) = nombre de la lista: `‹ Doctores` · `‹ Staff`.
- **Directory mode** (`entity=null`): leaves **deshabilitadas/atenuadas** (aria-disabled, tabIndex=-1, opacity ~.45) hasta que hay entidad.
- **Las leaves son RUTAS, NO Shadcn `Tabs`.** a11y (WAI-ARIA tablist · SC-10): `role="tablist"` + `role="tab"`/`aria-selected`/`aria-disabled` + roving tabindex + flechas (Left/Right/Home/End). `router.push` (no full reload — preserva React Query cache). NO registrado en `AGENT_SUBSUBTABS` (driven by `entity` prop).

**Props** (`EntitySubNavBarProps` — `@luana/ui-kit` v0.3.x): `rootHref` · `rootLabel` · `entity: {id, name, avatarUrl?}|null` · `leaves: {id, label, href}[]` · `activeLeaf?: string|null` (★ v1.4 — optional override; si ausente el kit deriva de `usePathname()`).

**Dos fuentes de leaves (misma barra, distinto origen):**

| Variante | Leaves | + agregar | Routing del leaf | Ejemplo | Live en Vitalia |
|---|---|---|---|---|---|
| **leaves fijos** | definidos por tipo de entidad (constante) | no | `[entityId]/{perfil\|horarios\|servicios}` | **staff/doctor** | ✅ sí (`lisa/staff`) |
| **leaves dinámicos** | colección **hija** en runtime + `+ agregar` | sí | `[entityId]/{datos\|[childId]}` | ICP→buyers (Nicolify) | ⏳ patrón disponible, sin consumer Vitalia aún |

> En la variante dinámica, la **entidad madre** (sus propios campos) vive en un leaf inicial (ej. `📋 Datos`) y los **hijos** son los leaves siguientes; el `+ agregar` crea un hijo nuevo.

**Routing:**
```
master:   app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx                       (lista)
detalle:  app/[tenantId]/(shell-organism)/[agent]/[subtab]/[entityId]/layout.tsx           (monta EntitySubNavBar + SSR entidad + slot)
          app/[tenantId]/(shell-organism)/[agent]/[subtab]/[entityId]/[leaf]/page.tsx      (leaf activo · [entityId] redirige al 1er leaf)
```
PHI/datos sensibles NUNCA en URL — `[entityId]` es UUID, no PHI.

**Lift realizado (★ v1.4):** `EntitySubNavBar` + `EntityWorkspaceLayout` ya viven en `@luana/ui-kit` v0.3.x (lift ejecutado en T-5 vitalia-shell-core-hardening). Brand-local RETIRADO. Consumers Vitalia importan del kit. Proposal shell completo (TopBar+Ribbon+ValeriaSidebar) sigue pendiente governance: `docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md`.

### § 7.3 — Static metadata catalog (★★ v1.2 addendum 2026-05-30)

```ts
// vitalia/frontend/src/lib/agent-catalog.ts  (SSoT actual)
// ★★ v1.2: Valeria removida del Ribbon; Mateo = Operar; config → Plataforma
export const AGENT_RIBBON_ORDER = ['lisa', 'mateo', 'adrian', 'lucas', 'camila'] as const
// (ConfigTab/PlataformaTab va aparte, no en el ribbon order de especialistas)

export const AGENT_CATALOG = {
  // 5 especialistas del Ribbon
  lisa:    { tabLabel: 'Mi Clínica', role: 'Lisa',    color: 'lisa',    avatarSrc: '/agents/lisa/thumbnail.png' },
  mateo:   { tabLabel: 'Operar',     role: 'Mateo',   color: 'mateo',   avatarSrc: '/agents/mateo/thumbnail.png' },  // ★★ v1.2: Mateo = Operar (reemplaza Valeria en Ribbon)
  adrian:  { tabLabel: 'Vender',     role: 'Adrián',  color: 'adrian',  avatarSrc: '/agents/adrian/thumbnail.png' },
  lucas:   { tabLabel: 'Atraer',     role: 'Lucas',   color: 'lucas',   avatarSrc: '/agents/lucas/thumbnail.png' },
  camila:  { tabLabel: 'Mantener',   role: 'Camila',  color: 'camila',  avatarSrc: '/agents/camila/thumbnail.png' },
  // Sidebar (NO en Ribbon)
  valeria: { role: 'Valeria', color: 'valeria', avatarSrc: '/agents/valeria/thumbnail.png', isSidebar: true },  // ★★ v1.2: solo sidebar, NO tab Ribbon
  // Tab Plataforma (reemplaza Configurar)
  plataforma: { tabLabel: 'Plataforma', role: 'Admin', color: 'config', iconName: 'Layers' },  // ★★ v1.2: antes { tabLabel: 'Configurar' }
} as const

export const RIBBON_SUBTABS = {
  lisa:   ['marca', 'servicios', 'doctores'],
  mateo:  ['agenda', 'pacientes'],  // ★★ v1.2: Mateo hereda agenda y pacientes de Valeria
  adrian: ['embudo', 'inbox', 'crm'],
  lucas:  ['bowtie', 'recomendaciones'],
  camila: ['reputacion', 'reactivar'],
} as const
```

PNGs ya en `vitalia/frontend/public/agents/{agent}/thumbnail.png` — verificado por inventario. Mateo ya tiene `thumbnail.png` desde bootstrap inicial.

---

## § 8 — Accessibility checklist (obligatorio per organismo)

| Organismo | a11y requirements |
|---|---|
| `TopBarGlobal` | `<header role="banner">` · logo `<a>` con `aria-label="Vitalia inicio"` |
| `ThemeToggle` | `<button aria-label="Cambiar tema (claro/oscuro)" aria-pressed={isDark}>` |
| `TenantSwitcher` | DropdownMenu Radix (a11y nativo) · `aria-label="Cambiar clínica"` en trigger |
| `ValeriaSidebar` | `<aside role="complementary" aria-label="Panel Valeria">` · `aria-expanded={valeriaOpen === 'chat'}` |
| `ValeriaCollapsedStrip` (★ v1.4) | `<button aria-label="Abrir a Valeria">` · tira 44px · avatar real + dot + label · click/Enter/Space → openChat() |
| ~~`ValeriaRail`~~ | **RETIRADO v1.4** — reemplazado por `ValeriaCollapsedStrip` |
| `ValeriaHistory` | `<nav aria-label="Historial conversaciones">` · search input `aria-label` |
| `ValeriaChat` | `<section role="region" aria-label="Chat con Valeria">` · messages `aria-live="polite"` |
| `Ribbon` | `<nav role="tablist" aria-label="Agentes">` · cada tab `role="tab" aria-selected` |
| `SubTabsBar` | `<nav role="tablist" aria-label="Sub-secciones {agente}">` |
| `ContentArea` | `<main id="main-content" tabindex="-1">` (focus management on route change) |

**Skip links:** `<a href="#main-content">Saltar al contenido</a>` en root layout.

**Keyboard shortcuts globales (Story F1-S5):**

| Tecla | Acción | Scope | ★ v1.4 |
|---|---|---|---|
| `C` | Valeria → closed (tira 44px) | Global, skip si focus en input | ★ antes era `collapsed` |
| ~~`R`~~ | ~~Valeria → rail~~ | — | **RETIRADO** (rail 60px eliminado) |
| `F` | Valeria → toggle historial (`historyOpen`) | Global, skip si focus en input | ★ antes era `full` |
| `N` | Nueva conversación Valeria (botón "+") | Global, skip si focus en input | sin cambio |
| `Esc` | Cerrar overlays / colapsar Valeria | Global | sin cambio |
| `Cmd/Ctrl+K` | Focus composer Valeria | Global, override default | sin cambio |
| `Tab` / `Shift+Tab` | Navigation natural | Web standard | sin cambio |

---

## § 9 — Testing strategy (per organismo)

### § 9.1 — Niveles de test

| Nivel | Herramienta | Qué prueba | Cuándo corre |
|---|---|---|---|
| **Unit** | Vitest + RTL | Componente aislado: props → render | Pre-commit · CI |
| **Integration** | Vitest + RTL | Organismo con state interno | CI |
| **Functional E2E** | Playwright `@project=smoke` | Flujo usuario completo (click tab → ve sub-tabs → click sub-tab → ve contenido) | Pre-push main · CI |
| **Visual golden** | Playwright `@project=visual` con `toHaveScreenshot()` | Componente render pixel-perfect vs golden snapshot generado del mockup HTML | CI · cada PR FE |
| **A11y** | Playwright `@project=a11y` con axe-core | WCAG 2.1 AA compliance | CI |

### § 9.2 — Golden snapshots — proceso

```bash
# Generación inicial (story F1-S1):
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend
npm run test:e2e:visual:update  # genera baseline screenshots por componente

# Verify en CI:
npm run test:e2e:visual  # falla si diff > 0.1% pixels
```

**Storage de goldens:** `vitalia/frontend/e2e/__screenshots__/{spec-name}/{component}-{viewport}.png` · gitignored hasta ratificación · gestionado por `.gitattributes` con LFS si crecen.

### § 9.3 — Por organismo: tests obligatorios

| Organismo | Unit | Integration | Functional E2E | Visual golden | A11y |
|---|---|---|---|---|---|
| `TopBarGlobal` | render con logo + slots | tenant switcher dropdown abre/cierra | abrir tema → cambia · abrir tenant → switchea | full snapshot light + dark | axe pass |
| `ValeriaSidebar` | render 2 estados (closed/chat) | keyboard shortcuts C/F/N | press C → tira strip · click strip → chat · press F → toggle history | strip snapshot + chat snapshot + chat+history snapshot | axe pass |
| `ValeriaCollapsedStrip` (★ v1.4) | render avatar+dot+label | click handler | click → openChat() | strip snapshot light + dark | axe pass |
| ~~`ValeriaRail`~~ | **RETIRADO v1.4** | — | — | — | — |
| `ValeriaHistory` | render groups + items | search filtra · click item activa | typing search reduce list · click conv → activa | full snapshot | axe pass |
| `ValeriaChat` | render messages bot/user | streaming dots aparecen | composer enter → mensaje aparece | snapshot con 5 mensajes ejemplo | axe pass |
| `Ribbon` | render 6 tabs | active tab change | click tab → URL cambia + tab activa visual | full ribbon snapshot per active tab (6) | axe pass |
| `SubTabsBar` | render sub-tabs per agente | click sub-tab → activa | URL refleja sub-tab | snapshot per agente (6) | axe pass |
| `ShellOrganismLayout` | render splitter 30/70 · drawer <1024 | resize splitter · colapsar Valeria → strip · toggle historial push 260px | full flow nav cross-agente · drawer open/close <1024 | snapshot 1280 + snapshot 1100 (clamp) + snapshot strip | axe pass |

### § 9.4 — Playwright `@project=visual` config

```ts
// vitalia/frontend/playwright.config.ts (extiende existente)
projects: [
  // ... smoke, a11y, mobile existentes
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

---

## § 10 — Mapeo Stories Fase 1 → componentes que construyen

> Cada historia es responsable de COMPONENTES CONCRETOS. Sin overlap. Story = ownership atómica.

| Story | Construye | Lifts del mockup | Tests obligatorios |
|---|---|---|---|
| **F1-S0** stack-stability | Shadcn install · tokens base · `.vt-*` deprecation plan | (infra) | Manual browser check + arch test "no .vt-* in new components" |
| **F1-S1** design-tokens-and-theme | `globals.css` vars (§5.1) · `tailwind.config.ts` extend (§5.2) · `<ThemeProvider>` · `ThemeToggle` (§3.2) · `useTheme` hook | Theme toggle ☀️/🌙 visible TopBar | Visual golden light + dark · Vitest theme toggle |
| **F1-S2** topbar-global | `TopBarGlobal` (§3.3) · `LogoMark` (§3.1) | TopBar header completo del mockup | Visual golden · a11y axe |
| **F1-S3** tenant-switcher | `TenantSwitcher` (§3.2) · `TenantOption` (§3.2) · `tenantStore` (§6.3) · API `/api/tenants` consume | Tenant dropdown completo del mockup | Functional E2E (click → switch) · visual golden open+closed |
| **F1-S4** shell-layout-5050 | `ShellOrganismLayout` (§3.4) · route group `app/[tenantId]/(shell-organism)/layout.tsx` · `shellStore.shellMode` (§6.1) | Estructura 50/50 base | Visual golden agentic + web modes |
| **F1-S5** valeria-rail-history | `ValeriaSidebar` · `ValeriaRail` · `ValeriaHistory` (§3.3) · keyboard handlers (§8) · `shellStore.valeriaState` · mock history data | Panel Valeria izq COMPLETO (rail + history transpuesta) | Functional E2E keyboard C/R/F/N · visual golden 3 states · a11y |
| **F1-S6** valeria-chat-skeleton | `ValeriaChat` (§3.3) · `ChatHeader` · `MessageBubble` · `TypingIndicator` · `DelegateMarker` · Composer (Textarea + IconButtons) · `chatStore` mock (§6.4) | Chat mockup con 5 mensajes ejemplo + composer | Visual golden con mensajes · functional (typing en composer) |
| **F1-S7** ribbon-6-tabs | `Ribbon` · `RibbonTab` · `ConfigTab` (§3.2-3.3) · routing wiring | Ribbon 6 tabs completo con active states | Visual golden per active tab (6 variants) · functional click → URL change |
| **F1-S8** sub-tabs-line2 | `SubTabsBar` · `SubTab` (§3.2-3.3) · routing wiring + dynamic per `AGENT_SUBTABS` | Línea 2 sub-tabs per agente | Visual golden 6 variants (per agente) · functional click → URL change |
| **F1-S9** routing-shell | App Router pages (§3.5) · `shell-routes.ts` whitelist (§7.2) · `AGENT_CATALOG` (§7.3) · default redirects · breadcrumb logic | Routing completo funcional | Functional E2E "navego entre tabs y URL refleja" · 404 si agent invalido |
| **F1-S10** empty-states-navegable | `EmptyState` + 22 sub-tab pages cada una con su empty-state · `PlaceholderCard` para casos especiales (Lisa Servicios cards, Conexiones grid, etc.) | Contenido placeholder navegable mockup | Visual golden por sub-tab (22 snapshots) · functional "todas las sub-tabs renderizan algo" |

| **vitalia-shell-core-hardening** (Fase 2 umbrella · 8 tickets · 2026-06-10) | T-1 store hardening (`valeriaOpen/historyOpen`) · T-2 layout hardening (splitter/topbar/no-chip) · T-3 `ValeriaCollapsedStrip` + retire `ValeriaRail` · T-4 soft-nav fix (`next/link`) · T-5 N3 lift `@luana/ui-kit` (delete brand-local `EntitySubNavBar`) · T-6 dark token audit · T-7 e2e suite 52+8 + 3 bug fixes · T-8 docs | Shell chrome responsivo + dark + N3 kit | E2E 20 specs `e2e/regression/shell-core-hardening/` · Vitest arch 631 PASS · T-7-result.md |

**Componentes específicos por agente** (Fase 2 — NO en Fase 1, salvo placeholder card mockup):
- `PipelineColumn` → F2-S4 adrian-embudo
- `AgendaSlot` → F2-S1 valeria-agenda
- (etc.)

---

## § 11 — Zero deuda técnica — checklist mandatorio por story

Toda historia DEBE pasar ANTES de merge:

- [ ] Lint 0 errors (ESLint config Vitalia)
- [ ] TypeScript strict 0 errors
- [ ] Vitest unit tests ≥80% coverage del componente nuevo
- [ ] Playwright functional E2E pasa
- [ ] Playwright visual golden generado + reviewed por Chris
- [ ] Playwright a11y axe pass
- [ ] NO `.vt-*` utility classes en código nuevo (arch test bloquea)
- [ ] NO `any` TypeScript (use `unknown` + guards)
- [ ] NO default exports (FSD-Lite enforce)
- [ ] NO cross-feature imports (FSD-Lite enforce)
- [ ] Componente documentado en Storybook (1+ story con variants)
- [ ] Spanish neutro LatAm en strings user-facing (excepto sales_agent voz tenant)
- [ ] CSS variables consumidas (NO hex hardcoded)
- [ ] Mobile responsive (breakpoint md+ minimum)
- [ ] Dark mode soportado (CSS vars switch)
- [ ] Skip link funcional (para organisms top-level)

---

## § 12 — Referencias cruzadas

- **Mockup HTML SSoT visual:** `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html`
- **Baseline funcional shell:** `vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md` (1069 líneas, 17 decisiones)
- **ADR-008 luana-core-ui (proposed):** `docs/architecture/luana-platform/ADR-008-luana-core-ui-shadcn-cli-pattern.md`
- **Engine consumido (Python BE):** `core/luana-core-{iam,platform,channels,copilot,observability,compliance}`
- **Pattern Copilot Nicolify (transponible):** `nicolify/frontend/src/features/copilot/components/CopilotSidebar.tsx`
- **Pattern TenantSwitcher Nicolify (reusable):** `nicolify/frontend/src/components/shared/layout/TenantSwitcher.tsx`
- **Tokens z-index Nicolify (copy-paste):** `nicolify/frontend/src/lib/tokens/z-index.ts`
- **★ v1.4 E2E suite shell hardening:** `vitalia/frontend/e2e/regression/shell-core-hardening/` (20 specs · 52+8 PASS)
- **★ v1.4 T-{1..8} result logs:** `vitalia/docs/product/stories/vitalia-shell-core-hardening/T-{1..8}-result.md`
- **★ v1.4 N3 kit lift:** `@luana/ui-kit` v0.3.x — `EntitySubNavBar` + `EntityWorkspaceLayout` + `activeLeaf` prop (commit d3b06b11)
- **★ v1.4 Lift proposal completo:** `docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md` § Estado post vitalia-shell-core-hardening
- **Next 16 soft-nav learning:** `vitalia/docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md`
- **HIPAA-lite overlay:** `vitalia/.claude/rules/hipaa-lite.md` (dual filter, audit log, sanitization en traces)
- **FSD-Lite enforcement:** `.claude/rules/frontend-fsd.md` + arch tests `vitalia/frontend/src/__tests__/architecture/`
- **Spanish neutro:** `.claude/rules/spanish-text.md` (glosario voseo → neutro)

---

## § 13 — Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-05-22 | Snapshot inicial post-ratificación Chris. 5 decisiones cementadas (D1-D6). 13 secciones. SSoT para todas las stories Fase 1. |
| 1.3 | 2026-06-03 | Formalizado patrón **list→detail (`EntitySubNavBar`)** como contrato (§ 3.3 organismos + § 3.5 pages + § 7.2.1 + nueva § 7.2.2). Reemplaza noción stale "N3-dynamic = Sheet drawer / `[...slug]` catch-all" por el patrón real ya implementado en `lisa/staff` (ADR-vitalia-004 § D-1). Back-port re-temizado del contract de Nicolify (que a su vez lo acreditó a Vitalia como origen). Lift candidate a `@luana/ui-kit` (N=2 consumers: staff Vitalia + ICP Nicolify). (v1.1/v1.2 fueron addenda inline sin row de changelog.) |
| 1.4 | 2026-06-10 | **Shell-core-hardening (8 tickets):** (1) §6.1 máquina store nueva `valeriaOpen: 'closed'\|'chat'` + `historyOpen` — `ValeriaState/ShellMode` RETIRADOS. (2) §3.3 `ValeriaCollapsedStrip` NUEVO (44px, avatar real) + `ValeriaRail` RETIRADO + `EntitySubNavBar`/`EntityWorkspaceLayout` CONSUMIDOS de `@luana/ui-kit` v0.3.x (brand-local eliminado, commit `a042e1df`). (3) §3.4 `ShellModeToggle` + modos web/agentic RETIRADOS; splitter `react-resizable-panels` + drawer <1024. (4) §3.6 Topbar cluster fijo `[ThemeToggle][TenantSwitcher]`. (5) §3.7 dark token audit (bg-white→bg-background + dark amber banner). (6) §3.8 soft-nav: `next/link` restaurado, edge-redirect proxy 307 conservado. (7) §8 a11y + §9 tests actualizados. (8) §3.5 nuevas sub-secciones §3.6–3.8. E2E: 52 specs PASS + 2 flaky-on-retry (T-7-result.md). |
