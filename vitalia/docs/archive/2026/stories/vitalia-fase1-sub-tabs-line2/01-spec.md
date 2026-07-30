---
story_id: vitalia-fase1-sub-tabs-line2
brand: vitalia
type: ui-story
state: refining
outcome: vitalia-mvp-ui-foundation
phase: fase-1
module: shell-organism
capability: shell.sub-tabs
po_ux_version: 2
ratified_by_chris: true
ratified_visual_by_chris: true
ratified_at: 2026-05-25T09:05:00Z
ratified_visual_at: 2026-05-25T09:05:00Z
ratified_visual_iter: 1
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/mockups/sub-tabs.html
last_modified: 2026-05-25
batch_1_ratified_at: 2026-05-25T08:55:00Z
batch_1_decisions:
  Q1_ssot_path: extend_agent_catalog  # NO crear lib/agents/subtabs.ts
  Q2_icons: emojis                     # paridad ribbon catalog
  Q3_keyboard_nav: roving_tabindex     # paridad F1-S7 Ribbon
  Q4_height: min-h-[42px]              # más respiración vs h-10
  Q5_null_agent: return_null           # gap colapsa, componente desmontado
authors: [/po-ux]
spec_anchors:
  shell_design_contract: vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
  shell_template: vitalia/docs/specs/templates/01-spec-shell-template.md
  predecessor_archive: vitalia/docs/archive/2026/stories/vitalia-fase1-ribbon-6-tabs/01-spec.md
  predecessor_capability: vitalia/docs/product/capabilities/shell-organism/ribbon.yaml
ssot_extensions:
  agent_catalog: vitalia/frontend/src/lib/agent-catalog.ts (EXTEND — NO crear lib/agents/subtabs.ts)
overlay_rules:
  - vitalia/.claude/rules/shell-mockup-per-component.md  # gate visual obligatorio antes refined
mockups_dir: vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/mockups/
---

# F1-S8 · `vitalia-fase1-sub-tabs-line2` — 01-spec.md (unified)

> **/po-ux UI-standard.** Gherkin + wireframe ASCII + mockup HTML por componente + estados visuales + microcopy + graders en este único archivo.

## § Context

**Outcome:** `vitalia-mvp-ui-foundation` (contenedor Fase 1 + Fase 2 shell-organism).
**Módulo afectado:** `shell-organism`.
**Insertion point:** LÍNEA 2 dentro de `AppPanelSlot` (heredado F1-S4 shell-layout-5050 + F1-S7 Ribbon real). Grid 3 filas del AppPanel: `[Ribbon h-14 · SubTabsBar h-[42px] · Content flex-1]`. Visible en ambos modos shell (`agentic` 50/50 y `web` rail 60px).

**Predecesores done:**
- F1-S7 `vitalia-fase1-ribbon-6-tabs` → `Ribbon` real (5 agentes + ConfigTab IconButton) + `agent-catalog.ts` extendido con `tabLabel + defaultSubtab + AGENT_RIBBON_ORDER + RibbonTabSlug + extractAgentFromPath`.
- F1-S6 `vitalia-fase1-valeria-chat-skeleton` → `ValeriaSidebar` panel izquierdo funcional.
- F1-S4 `vitalia-fase1-shell-layout-5050` → grid base con `AppPanelSlot`.

**Out-of-scope explícito (anti-creep):**
- ❌ NO contenido sub-tab (eso es F1-S10 empty-states + Fase 2 progresiva)
- ❌ NO N3-dyn workspaces (Fase 2)
- ❌ NO breadcrumb "vía Valeria" indicator (postponed)
- ❌ NO sub-tabs para Mateo (transversal, excluido del Ribbon F1-S7 → consecuentemente excluido del SubTabsBar F1-S8)
- ❌ NO RBAC para sub-tabs `compliance` (Lisa) ni `avanzado` (Config) — visibles siempre F1-S8 (TODO Fase 2)
- ❌ NO telemetría wireada — `sub_tab_clicked` queda anotado TODO Fase 2
- ❌ NO redirect `/{tenantId}/{agent}` → `/{tenantId}/{agent}/{defaultSubtab}` (eso es F1-S9 routing-shell)

**Decisión cementada — modos shell:** SubTabsBar renderiza idéntico en modos `agentic` y `web` (misma horizontal h-[42px], N sub-tabs dinámicos según agente activo, `overflow-x-auto`). NO if-statements `mode === 'web'`.

**Decisión cementada — anti-duplication SSoT (★ RECOMENDACIÓN — confirmar Chris Q1):** F1-S7 estableció `agent-catalog.ts` como SSoT único para metadata agentes. F1-S8 **EXTIENDE** ese mismo archivo agregando:

```ts
// agent-catalog.ts — F1-S8 EXTEND
export interface SubTabMeta {
  id: string
  label: string
  icon: string         // emoji o lucide icon name (decidir Q3)
}

/**
 * Sub-tabs per ribbon tab (5 agentes + config).
 * Counts: Lisa 4 · Lucas 5 · Adrián 4 · Valeria 2 · Camila 4 · Config 3.
 * Mateo EXCLUIDO (transversal, no en ribbon F1-S7).
 * spec_anchor: 01-spec.md F1-S8 § Scope.
 */
export const RIBBON_SUBTABS: Record<RibbonTabSlug, readonly SubTabMeta[]> = {
  lisa:    [...],   // 4 items
  lucas:   [...],   // 5 items
  adrian:  [...],   // 4 items
  valeria: [...],   // 2 items
  camila:  [...],   // 4 items
  config:  [...],   // 3 items
}

/** Extract [subtab] segment from /{tenant}/{agent}/{subtab}/... */
export function extractSubtabFromPath(pathname: string | null | undefined): string | null { ... }
```

NO crear `vitalia/frontend/src/lib/agents/subtabs.ts` ni `vitalia/frontend/src/lib/agents/routing.ts` (paths duplicados — viola anti-duplication R3 + rompe SSoT establecido F1-S7).

## § 1 — `RIBBON_SUBTABS` whitelist (data SSoT)

Total 22 sub-tabs distribuidos:

| Agente | Sub-tabs | Count | Default (de `defaultSubtab` catalog) |
|---|---|---|---|
| Lisa | `marca` · `doctores` · `servicios` · `compliance` | 4 | `marca` |
| Lucas | `lanzar` · `envuelo` · `recursos` · `resultados` · `mercado` | 5 | `lanzar` |
| Adrián | `inbox` · `embudo` · `outbound` · `propuestas` | 4 | `inbox` |
| Valeria | `agenda` · `pacientes` | 2 | `agenda` |
| Camila | `voz` · `reactivar` · `multiplicar` · `reputacion` | 4 | `voz` |
| Config | `cuenta` · `conexiones` · `avanzado` | 3 | (TODO Q5 — ConfigTab navega a `cuenta` actualmente) |

Labels canónicos (Spanish neutro LatAm, ratificados F1-S7 catalog extension):

| Slug | Label | Icon (★ Q3 decidir emoji vs lucide) |
|---|---|---|
| `lisa.marca` | "Marca" | 🏥 |
| `lisa.doctores` | "Doctores" | 👨‍⚕️ |
| `lisa.servicios` | "Servicios" | 🩺 |
| `lisa.compliance` | "Compliance" | 🛡️ |
| `lucas.lanzar` | "Lanzar" | 🚀 |
| `lucas.envuelo` | "En vuelo" | 📡 |
| `lucas.recursos` | "Recursos" | 📚 |
| `lucas.resultados` | "Resultados" | 📈 |
| `lucas.mercado` | "Mercado" | 🌍 |
| `adrian.inbox` | "Inbox" | 💬 |
| `adrian.embudo` | "Embudo" | 🎯 |
| `adrian.outbound` | "Outbound" | 📣 |
| `adrian.propuestas` | "Propuestas" | 💼 |
| `valeria.agenda` | "Agenda" | 📆 |
| `valeria.pacientes` | "Pacientes" | 👥 |
| `camila.voz` | "Voz del paciente" | 🎤 |
| `camila.reactivar` | "Reactivar" | 🪃 |
| `camila.multiplicar` | "Multiplicar" | 🤝 |
| `camila.reputacion` | "Reputación" | 📊 |
| `config.cuenta` | "Mi cuenta" | 🏢 |
| `config.conexiones` | "Conexiones" | 🔌 |
| `config.avanzado` | "Avanzado" | 🔬 |

## § 2 — Componentes (reuse > new)

| Componente | Path | Acción | Justificación |
|---|---|---|---|
| `agent-catalog.ts` | `vitalia/frontend/src/lib/agent-catalog.ts` | MODIFY (EXTEND) | Agregar `SubTabMeta` interface + `RIBBON_SUBTABS` const + `extractSubtabFromPath` helper. NO crear `lib/agents/subtabs.ts` (anti-duplication F1-S7 pattern). |
| `SubTabsBar.tsx` | `vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx` | NEW | Organismo nav LÍNEA 2. Lee URL → consume `RIBBON_SUBTABS[activeAgent]`. Render `<nav role="tablist">` horizontal. |
| `SubTab.tsx` | `vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx` | NEW | Molécula button individual. Props: `{ subtab, color, active, onClick }`. Tint agent-color en active. |
| `AppPanelSlot.tsx` | `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | MODIFY | Reemplazar placeholder sub-tabs (líneas 56-65 actual) con `<SubTabsBar />` real. |

**Cross-brand reuse signal:** SubTabsBar es brand-local Vitalia (consume Vitalia agent catalog). Lift candidate cuando ≥2 brands tengan ribbon+sub-tabs pattern. Hoy brand-local per anti-duplication.md.

## § 3 — Wireframe ASCII

### Layout en contexto (modo agentic split 50/50)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TopBarGlobal (Logo + tenant switcher + theme toggle + ⚙)               h-12 │
├────────────────────────────┬─────────────────────────────────────────────────┤
│ ValeriaSidebar (50%)        │  AppPanelSlot (50%)                            │
│                              │ ┌─────────────────────────────────────────┐  │
│ ChatHeader                   │ │ Ribbon: 🟢Lisa  ⚫Lucas  🔵Adrián       │  │
│ ChatMessages                 │ │         🟣Valeria  🟦Camila    ⚙        │ h-14
│ ChatComposer                 │ ├─────────────────────────────────────────┤  │
│                              │ │ ★ SubTabsBar (LÍNEA 2)                 │  │
│                              │ │   🏥 Marca │ 👨‍⚕️ Doctores │ 🩺 Serv. │  │ h-[42px]
│                              │ │   🛡️ Compliance                        │  │
│                              │ ├─────────────────────────────────────────┤  │
│                              │ │ Content area · F1-S10 empty states     │  │
│                              │ │                                         │ flex-1
└──────────────────────────────┴─────────────────────────────────────────────┘
```

### Layout en contexto (modo web, Valeria rail 60px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TopBarGlobal                                                            h-12 │
├──┬───────────────────────────────────────────────────────────────────────────┤
│V │  AppPanelSlot (más ancho)                                                  │
│a │  ┌──────────────────────────────────────────────────────────────────┐  │
│l │  │ Ribbon: 🟢Lisa  ⚫Lucas  🔵Adrián  🟣Valeria  🟦Camila        ⚙ │ h-14
│r │  ├──────────────────────────────────────────────────────────────────┤  │
│a │  │ ★ SubTabsBar — sub-tabs dinámicas per active agent             │ h-[42px]
│i │  │   📆 Agenda │ 👥 Pacientes                                       │  │
│l │  ├──────────────────────────────────────────────────────────────────┤  │
│  │  │ Content · F1-S10 empty states                                   │  │
│  │  │                                                                 │  │
└──┴────────────────────────────────────────────────────────────────────────┘
 60px
```

### Estado oculto (no activeAgent)

```
┌──────────────────────────────────────────────────┐
│ Ribbon: 🟢Lisa  ⚫Lucas  🔵Adrián …             │ h-14
├──────────────────────────────────────────────────┤
│ (★ SubTabsBar return null — gap colapsa)         │
├──────────────────────────────────────────────────┤
│ Content area                                     │
```

★ Decisión Q6: ¿return null total (gap colapsa) o `min-h-[42px]` placeholder vacío (preserva grid)? Recomiendo **return null** (consistente con scope checkpoint línea 107). Confirmar Chris.

## § 4 — Mockup HTML por componente (gate visual obligatorio)

> **Overlay rule:** `vitalia/.claude/rules/shell-mockup-per-component.md` bloquea transition `refining → refined` sin ratificación visual Chris.

**Path:** `vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/mockups/sub-tabs.html`

**Contenido obligatorio:**
- 6 variants per active agent: Lisa · Lucas · Adrián · Valeria · Camila · Config
- Light + dark mode toggle (mismo patrón F1-S7)
- Anatomy SubTab inactive/hover/focus/active (4 estados)
- Render en context (modo agentic + modo web)
- Datos LatAm realistas (no Lorem ipsum)
- Spanish neutro LatAm (sin voseo)
- Tailwind CDN + tokens Vitalia (mismos hex/soft del F1-S7 mockup)
- Sin Bootstrap ni Material UI (Tailwind + Shadcn-style)

**Comando preview:**

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/mockups
python3 -m http.server 8889   # 8889 para no chocar con otros mockups corriendo
# Chris abre http://localhost:8889/sub-tabs.html
```

**Estado:** ✅ Mockup HTML v1 escrito junto a este 01-spec.md (servir y revisar).

## § 5 — Estados visuales (tabla)

### SubTabsBar contenedor

| Estado | Trigger | Render |
|---|---|---|
| `hidden` | `activeAgent === null` | `return null` (componente desmontado). Grid AppPanel colapsa fila. |
| `visible` | `activeAgent ∈ RibbonTabSlug` | `<nav role="tablist">` con N sub-tabs (4·5·4·2·4·3 según agente). |
| `overflow` | Viewport estrecho (< ~480px AppPanel) | `overflow-x-auto` activa scroll lateral nativo. |

### SubTab molécula

| Estado | Visual |
|---|---|
| `inactive` | `text-muted-foreground · font-medium · bg-transparent` |
| `inactive:hover` | `bg-muted · text-foreground · font-medium` |
| `inactive:focus-visible` | inactive base + `outline-2 outline-ring outline-offset-1` |
| `active` (Lisa) | `bg-agent-lisa-soft · text-agent-lisa · font-semibold` |
| `active` (Lucas) | `bg-agent-lucas-soft · text-foreground · font-semibold` (Lucas color es near-black, no usar `text-agent-lucas`) |
| `active` (Adrián) | `bg-agent-adrian-soft · text-agent-adrian · font-semibold` |
| `active` (Valeria) | `bg-agent-valeria-soft · text-agent-valeria · font-semibold` |
| `active` (Camila) | `bg-agent-camila-soft · text-agent-camila · font-semibold` |
| `active` (Config) | `bg-muted · text-foreground · font-semibold` (Config no es agente, color neutral) |
| `active:hover` | active base **sin cambio** (preserve tint per F1-S7 Q16 cement equivalente) |
| `active:focus-visible` | active base + `outline-2 outline-ring outline-offset-1` |

## § 6 — Microcopy (Spanish neutro LatAm)

| Lugar | Copy |
|---|---|
| `<nav aria-label>` | `"Sub-secciones {agentName}"` (ej. `"Sub-secciones Lisa"`) |
| SubTab labels | tabla § 1 (todos Spanish neutro, sin voseo, con tildes/eñes) |
| Tooltip overflow | (futuro) `"Más sub-secciones · scrolleá lateral"` — postponed Fase 2 |

<!-- voseo-allowed: glosario reference (forbidden voseo examples) -->
**Spanish neutro check:** todos los labels ✅ — `"Marca"`, `"Doctores"`, `"En vuelo"`, `"Voz del paciente"`, `"Reputación"` (con tilde), `"Mi cuenta"`. NO voseo. NO léxico regional.

## § 7 — Data flow (conceptual)

- **No API calls** — SubTabsBar es UI navegacional pura. Data viene de URL (`usePathname`) + constante estática (`RIBBON_SUBTABS`).
- **No React Query** — no fetch, no mutations.
- **No form library** — no inputs.
- **Active state derivation** — single source of truth: URL segments via `extractAgentFromPath` (F1-S7 existing) + `extractSubtabFromPath` (F1-S8 NEW).
- **Navigation:** `router.push('/{tenant}/{agent}/{subtab}')` on click. F1-S9 routing-shell maneja redirects + 404.

## § 8 — Responsive breakpoints

- Mobile (< 768px): SubTabsBar visible, `overflow-x-auto` activo. Touch swipe lateral natural.
- Tablet (768-1024px): SubTabsBar visible, posible overflow en agentes con 4-5 sub-tabs depende de panel width.
- Desktop (> 1024px): SubTabsBar visible, todos los sub-tabs caben sin scroll en modo `agentic` (panel 50%) — Lucas con 5 tabs es caso límite, validar mockup.

## § 9 — Accessibility

- `<nav role="tablist" aria-label="Sub-secciones {agent}">` contenedor
- `<button role="tab" aria-selected={active} data-testid="sub-tab-{id}">` sub-tab
- Keyboard nav (★ Q4 — confirmar Chris):
  - **Opción A — Roving tabindex (★ recomendada, paridad F1-S7 Ribbon):** Arrow Left/Right mueve focus sin activar; Enter/Space activa (router.push). Home/End saltan al primer/último.
  - **Opción B — Tab order natural:** Tab/Shift+Tab pasa por cada sub-tab; Enter activa.
- Focus visible: `outline-2 outline-ring outline-offset-1`
- Contrast: bg-agent-{slug}-soft sobre text-agent-{slug} debe pasar WCAG AA (validado F1-S7).
- Screen reader: anuncia `"tab, Marca, 1 de 4"` al focus change.

## § 10 — Gherkin scenarios

> **Sub-categorías mandatory v4.1 que aplican:** `accessibility` + `i18n`. Las demás (`race_condition`, `concurrent_users`, `network_failure`, `empty_state`, `large_dataset`) marcadas `not_applicable_reason` porque SubTabsBar es UI navegacional pura (data estática constante, sin fetch FE, sin create/update, sin pagination, sin large datasets — máximo 5 sub-tabs por agente).

### SC-1 happy · click sub-tab navega correctly

```gherkin
Given usuario en /{tenantId}/lisa/marca
  And SubTabsBar visible con 4 sub-tabs Lisa
  And "Marca" active con bg-agent-lisa-soft + text-agent-lisa
When click SubTab "Doctores"
Then router.push("/{tenantId}/lisa/doctores") se invoca
  And el segmento URL [subtab] cambia a "doctores"
  And "Doctores" SubTab pasa a active (bg-agent-lisa-soft + text-agent-lisa + font-semibold)
  And "Marca" pierde tint (text-muted-foreground + font-medium)
  And aria-selected="true" solo en "Doctores"
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-nav.spec.ts" }
  - { type: visual_state, screen: "active-lisa-doctores", element: "[data-testid=sub-tab-doctores]", expect: "aria-selected=true · class~=bg-agent-lisa-soft" }
  ```

### SC-2 happy · cambio de agente re-renderiza sub-tabs

```gherkin
Given usuario en /{tenantId}/lisa/doctores
  And SubTabsBar muestra 4 sub-tabs Lisa
When click RibbonTab "Atraer" (Lucas)
Then router.push("/{tenantId}/lucas/lanzar") se invoca (defaultSubtab Lucas)
  And SubTabsBar re-renders con 5 sub-tabs Lucas (Lanzar · En vuelo · Recursos · Resultados · Mercado)
  And "Lanzar" SubTab active (bg-agent-lucas-soft + text-foreground)
  And aria-label nav actualiza a "Sub-secciones Lucas"
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-agent-change.spec.ts" }
  - { type: visual_state, screen: "post-agent-change-lucas", element: "[data-testid=sub-tabs-bar]", expect: "5 children · sub-tab-lanzar[aria-selected=true]" }
  ```

### SC-3 happy · deep link a sub-tab arbitraria marca active state

```gherkin
Given usuario navega directamente (deep link) a /{tenantId}/camila/reactivar
When la página carga
Then extractAgentFromPath devuelve "camila"
  And extractSubtabFromPath devuelve "reactivar"
  And SubTabsBar renderiza 4 sub-tabs Camila
  And "Reactivar" SubTab active con bg-agent-camila-soft + text-agent-camila
  And los otros 3 sub-tabs Camila inactivos (text-muted-foreground)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-deeplink.spec.ts" }
  - { type: visual_state, screen: "active-camila-reactivar", element: "[data-testid=sub-tab-reactivar]", expect: "aria-selected=true" }
  ```

### SC-4 negative · activeAgent null (URL inválida) → SubTabsBar oculto

```gherkin
Given usuario navega a /{tenantId}/foobar/anything ([agent]="foobar" inválido)
When la página carga
Then extractAgentFromPath devuelve null
  And SubTabsBar return null (componente NO renderizado en DOM)
  And document.querySelector("[data-testid=sub-tabs-bar]") es null
  And NO error en consola
  And grid AppPanel colapsa fila (Ribbon + Content sin gap)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-null-agent.spec.ts" }
  - { type: state_check, target: dom, query: "[data-testid=sub-tabs-bar]", expect: "null" }
  ```

### SC-5 edge · sub-tab URL inválida → ningún SubTab active

```gherkin
Given usuario navega a /{tenantId}/lisa/inexistente
  And lisa ∈ RibbonTabSlug pero "inexistente" ∉ RIBBON_SUBTABS.lisa
When la página carga
Then SubTabsBar renderiza con 4 sub-tabs Lisa (no return null — agente sí válido)
  And NINGÚN SubTab tiene aria-selected="true"
  And todos los SubTabs muestran inactive style (text-muted-foreground)
  And NO error en consola (defensive null check en extractSubtabFromPath comparison)
  And (F1-S9 routing-shell handleará redirect a defaultSubtab en futuro)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-invalid-subtab.spec.ts" }
  - { type: state_check, target: dom, query: "[data-testid=sub-tabs-bar] [aria-selected=true]", expect: "null" }
  ```

### SC-6 edge · viewport mobile 375px → horizontal scroll Lucas (5 sub-tabs)

```gherkin
Given viewport 375x667 (mobile portrait)
  And usuario en /{tenantId}/lucas/lanzar (5 sub-tabs Lucas — caso límite)
When la página carga
Then SubTabsBar renderiza horizontal con overflow-x-auto
  And solo "Lanzar" + "En vuelo" + parte de "Recursos" visibles sin scroll
  And user puede scrollear lateral para alcanzar "Mercado"
  And NO wrap (whitespace-nowrap en SubTab)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-mobile-overflow.spec.ts" }
  - { type: visual_golden, path: "vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-mobile-lucas-375.png" }
  ```

### SC-7 adversarial · XSS en sub-tab segment → safe

```gherkin
Given usuario navega a /{tenantId}/lisa/<script>alert(1)</script>
When la página carga
Then extractSubtabFromPath devuelve "<script>alert(1)</script>" como string (raw segment)
  And SubTabsBar compara con RIBBON_SUBTABS.lisa[].id → no match → NO sub-tab activo
  And NO se ejecuta el script (React JSX auto-escape + no dangerouslySetInnerHTML)
  And data-testid={raw_segment} sanitizado por React (text content, no HTML)
  And NO entry en DOM con tag <script>
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-xss-guard.spec.ts" }
  - { type: state_check, target: dom, query: "document.querySelector('script[data-injected]')", expect: "null" }
  ```

### SC-8 a11y · keyboard navigation roving tabindex (★ Q4 si Opción A ratificada)

```gherkin
Given foco en SubTabsBar (Tab desde Ribbon)
  And focus inicialmente en "Marca" (active=Lisa.marca)
When Arrow Right → focus a "Doctores" (NO activa router.push)
  And Arrow Right → focus a "Servicios"
  And Arrow Right → focus a "Compliance"
  And Arrow Right → focus wrap-around a "Marca" (★ Q4.bis confirmar wrap o stop)
  And Home → focus a "Marca"
  And End → focus a "Compliance"
  And Enter en "Doctores" focused → router.push("/{tenantId}/lisa/doctores")
Then en cada paso focus ring visible (outline ring)
  And screen reader anuncia "tab, {label}, {N} de 4"
  And axe-core scope=[data-testid=sub-tabs-bar] retorna 0 violations WCAG AA
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-keyboard.spec.ts" }
  - { type: axe, ruleset: "wcag2aa", scope: "[data-testid=sub-tabs-bar]" }
  ```

### SC-9 i18n · microcopy Spanish neutro renderizado correcto

```gherkin
Given usuario en /{tenantId}/camila/voz (sub-tabs Camila)
When la página renderiza SubTabsBar
Then los 4 labels visibles son exactamente:
   - "Voz del paciente" (con tilde)
   - "Reactivar"
   - "Multiplicar"
   - "Reputación" (con tilde)
  And aria-label="Sub-secciones Camila"
  And NO presencia de voseo ("Reactivá", "Multiplicalo", etc.)
  And NO presencia de hardcoded English ("Voice", "Reactivate", etc.)
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-i18n.spec.ts" }
  - { type: state_check, target: dom, query: "[data-testid=sub-tabs-bar] >>text=Reputación", expect: "exists · count=1" }
  ```

### SC-10 visual_golden · 12 goldens (6 agentes × 2 themes)

```gherkin
Given mockup ratificado Chris (sub-tabs.html) + SubTabsBar implementado
When CI corre playwright --update-snapshots false
Then 12 visual golden snapshots match con maxDiffPixelRatio: 0.001:
   - sub-tabs-lisa-light.png · sub-tabs-lisa-dark.png
   - sub-tabs-lucas-light.png · sub-tabs-lucas-dark.png
   - sub-tabs-adrian-light.png · sub-tabs-adrian-dark.png
   - sub-tabs-valeria-light.png · sub-tabs-valeria-dark.png
   - sub-tabs-camila-light.png · sub-tabs-camila-dark.png
   - sub-tabs-config-light.png · sub-tabs-config-dark.png
```

- **playwright_required: true**
- **graders:**
  ```yaml
  - { type: visual_golden, path: "vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-{slug}-{theme}.png" }
  ```

### Sub-categorías mandatory marked `not_applicable`

| Sub-categoría | Estado | Reason |
|---|---|---|
| `race_condition` | not_applicable | SubTabsBar es UI navegacional pura sin create/update ni unique constraints; nada que correr concurrente. |
| `concurrent_users` | not_applicable | No multi-tenant data fetch; data viene de constante estática + URL. |
| `network_failure` | not_applicable | No API calls (data estática client-side import). |
| `empty_state` | not_applicable | "Vacío" significa `activeAgent === null` y eso está cubierto en SC-4 con `return null` (no es empty data state, es ausencia de surface). |
| `large_dataset` | not_applicable | Máximo 5 sub-tabs por agente (Lucas), bounded constante. No pagination posible. |

## § 11 — Acceptance criteria (resumen tabla — match checkpoint scope)

| AC | Verificación | Mapeo scenario |
|---|---|---|
| AC-1 | SubTabsBar visible debajo del Ribbon, altura min 42px (`h-[42px]` ★ Q5 confirm vs h-10) | SC-1, SC-2 visual |
| AC-2 | Sub-tabs dinámicas per active agent (4·5·4·2·4·3) | SC-1..SC-3 |
| AC-3 | Active subtab con `bg-agent-{slug}-soft + text-agent-{slug}` (Lucas excepción → text-foreground) | SC-1, SC-3 visual + SC-10 goldens |
| AC-4 | Click subtab → `router.push('/{tenant}/{agent}/{subtab}')` | SC-1, SC-2 |
| AC-5 | Si `activeAgent === null` → SubTabsBar `return null` (no DOM) | SC-4 |
| AC-6 | a11y: `role="tablist"` + `role="tab"` + `aria-selected` + keyboard nav | SC-8 |
| AC-7 | Visual goldens 6 agentes × 2 themes = 12 PNGs | SC-10 |
| AC-8 | Horizontal scroll en viewport estrecho (Lucas 5 sub-tabs) | SC-6 |
| AC-9 | Vitest unit (SubTab + SubTabsBar + extractSubtabFromPath) + Playwright functional | implícito en graders |

## § 12 — Deliverables (handed off al `/architect`)

| File | Acción | LOC estimado |
|---|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` | MODIFY (EXTEND) | +60 LOC (SubTabMeta + RIBBON_SUBTABS + extractSubtabFromPath) |
| `vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx` | NEW | ~80 LOC |
| `vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx` | NEW | ~60 LOC |
| `vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.test.tsx` | NEW | ~150 LOC (Vitest) |
| `vitalia/frontend/src/components/shared/shell-organism/SubTab.test.tsx` | NEW | ~120 LOC (Vitest) |
| `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` | MODIFY | +40 LOC (subtabs whitelist + extractSubtabFromPath) |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | MODIFY | -10/+5 LOC (replace placeholder con `<SubTabsBar />`) |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx` | MODIFY | +20 LOC (mount SubTabsBar real) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/*.spec.ts` | NEW (9 specs) | ~600 LOC total |
| `vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-*.png` | NEW (12 goldens) | binary |

## § 13 — Capability shipped

Al merge F1-S8 → escribir/actualizar `vitalia/docs/product/capabilities/shell-organism/sub-tabs.yaml`:

```yaml
capability_id: shell.sub-tabs
module: shell-organism
slug: sub-tabs
status: live
date_introduced: 2026-MM-DD  # populated al merge
story_introduced: vitalia-fase1-sub-tabs-line2
package_version: vitalia@MAJOR.MINOR.PATCH
package_path: vitalia/frontend
license: proprietary
surfaces:
  config: vitalia/frontend/src/lib/agent-catalog.ts (EXTEND RIBBON_SUBTABS)
  backend: null
  frontend:
    - vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx
    - vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx
  tests:
    - vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.test.tsx
    - vitalia/frontend/src/components/shared/shell-organism/SubTab.test.tsx
    - vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/*.spec.ts
  docs:
    - vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md § 7.2
dependencies:
  - vitalia/frontend/src/lib/agent-catalog.ts (F1-S7 SSoT)
  - vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx (F1-S7)
  - vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx (F1-S4)
```

## § 14 — Próximo paso post-done

F1-S9 `vitalia-fase1-routing-shell` consolida App Router pages:
- `/{tenantId}/{agent}/{subtab}/page.tsx` server components
- Redirect `/{tenantId}/{agent}` → `/{tenantId}/{agent}/{defaultSubtab}` (consume `agent-catalog.ts.defaultSubtab`)
- 404 handling cuando agent o subtab inválido (cae a F1-S10 empty-state placeholder)

## § 15 — Batch 1 — RATIFICADO 2026-05-25T08:55Z

Todas decisiones cementadas a recomendación /po-ux. No requieren re-litigación post-handoff `/architect`.

| Q | Decisión | Impacto |
|---|---|---|
| **Q1 SSoT path** | ✅ EXTEND `vitalia/frontend/src/lib/agent-catalog.ts` (NO crear `lib/agents/subtabs.ts`) | anti-duplication F1-S7 pattern preservado |
| **Q2 Icons** | ✅ Emojis (paridad ribbon catalog) | zero refactor; emojis ya usados en `SubTabMeta` checkpoint |
| **Q3 Keyboard nav** | ✅ Roving tabindex (Arrow keys focus + Enter activa) | paridad F1-S7 Ribbon WAI-ARIA tablist completo |
| **Q4 Height** | ✅ `min-h-[42px]` (no `h-10`) | snapshot dimension fijo; 42px = más respiración |
| **Q5 activeAgent=null** | ✅ `return null` total (gap colapsa) | scope checkpoint preservado; grid 3 filas → 2 filas naturalmente |

**Batch 2 (refinamientos pequeños) auto-resueltos por defaults:**

- **Active:hover preserva tint** → SÍ (default mockup BLOCK 4 + F1-S7 paridad Q16 cement equivalente)
- **Config defaultSubtab** → `cuenta` (consistente F1-S7 ConfigTab.onClick → `/{tenantId}/config/cuenta`)
- **Wrap-around keyboard** → wrap al primero (default F1-S7 Ribbon pattern; Home/End atajos hard)

Si querés revisar batch 2 explícito, decímelo. Sino, esperás respuesta visual al mockup HTML (gate obligatorio shell-mockup-per-component.md).

## § 16 — Gate visual obligatorio (overlay rule)

`vitalia/.claude/rules/shell-mockup-per-component.md` bloquea transition `refining → refined` sin ratificación visual Chris.

**Servidor local activo:** `python3 -m http.server 8889` desde `mockups/`. Abrí en browser:

```
http://localhost:8889/sub-tabs.html
```

**Bloques a revisar (6 secciones):**

1. SubTabsBar in context · modo agentic (Lisa active 4 sub-tabs)
2. SubTabsBar in context · modo web (Valeria active 2 sub-tabs)
3. **6 variants showcase** — 1 SubTabsBar por agente (Lisa·Lucas·Adrián·Valeria·Camila·Config) — target visual goldens
4. Anatomy SubTab — 4 estados (inactive · hover · focus · active) sobre Lisa "Doctores"
5. Mobile 375px Lucas overflow horizontal (5 sub-tabs caso límite)
6. **Q5 cement preview** — Opción A return null lado a lado con Opción B placeholder (visual)

**Botón "🌙 Dark" / "☀️ Light"** en header del mockup cambia tema (ambos modos validables).

---

**Estado spec:** draft v2 · batch 1 cementado · pendiente ratificación visual Chris sobre mockup HTML.

**Próximo:** Chris revisa mockup → APROBAR o pedir ajustes visuales → si APROBAR · update `ratified_visual_by_chris: true` + `ratified_by_chris: true` → transition `refining → refined` → handoff `/architect vitalia vitalia-fase1-sub-tabs-line2`.
