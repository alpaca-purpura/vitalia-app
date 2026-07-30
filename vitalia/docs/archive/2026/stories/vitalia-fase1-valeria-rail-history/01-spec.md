---
story_id: vitalia-fase1-valeria-rail-history
brand: vitalia
type: ui-story
state: refining
outcome: vitalia-mvp-ui-foundation
phase: fase-1
module: shell-organism
capability: shell.valeria-sidebar
agent_owner: shell
spawned_at: 2026-05-22
last_modified: 2026-05-23
po_ux_version: 1
ratified_by_chris: false
ratified_visual_by_chris: false
hipaa_lite_scope: not_applicable                  # shell chrome UI, mock data sin PHI
parallel_safe: true
priority: high
estimated_dev_days: 2-3
dependencies:
  hard: [vitalia-fase1-shell-layout-5050]         # done 2026-05-23 archived
  soft: []
blocks_hard: [vitalia-fase1-valeria-chat-skeleton]
reuse_map_summary: "REUSE 80% nicolify CopilotSidebar (TRANSPONER grid · invertir [chat][rail] → [rail][chat]) · adapt widths · renombrar Valeria · CSS vars Vitalia · agregar auto-coupling collapsed→shellMode='web' (no existe en Nicolify)"
side_effects_F1_S4:                               # ★ scope creep ratificado Chris 2026-05-23 batch 1b
  - "MODIFY vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx::MIN_VALERIA_PX (full: 620 → 580 porque rail XOR history 2-col model)"
  - "MODIFY vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx (agregar hamburger button <md viewport — abre Valeria drawer)"
next_action: "/po-ux mockups + iter Chris → ratify visual + spec → state refining→refined"
---

# F1-S5 vitalia-fase1-valeria-rail-history — 01-spec.md unificado

> **/po-ux fusión spec + UX/UI** · paradigm v4.1 · brand vitalia · type ui-story
> Owner spec: `/po-ux` · Pre-arch gate visual: `shell-mockup-per-component.md` (mockups HTML ratificados antes refined)

---

## § 0 Context

### Outcome + module + insertion point

- **Outcome:** `vitalia-mvp-ui-foundation` (Fase 1 shell esqueleto)
- **Módulo:** `shell-organism` (UI chrome, brand-local, NO cross-brand consumers, NO PHI)
- **Insertion point:** reemplaza `ValeriaSidebarSlot` placeholder (F1-S4) dentro de `ShellOrganismLayout` (route group `(shell-organism)/`)
- **Predecesores done:** F1-S0 stack-stability · F1-S1 design-tokens-theme · F1-S2 topbar-global · F1-S3 tenant-switcher · F1-S4 shell-layout-5050
- **Sucesor inmediato:** F1-S6 valeria-chat-skeleton (reemplaza `ValeriaChatSlot` placeholder con chat real)

### Goal (1-liner)

`ValeriaSidebar` organismo: panel izquierdo del shell agéntico con grid interno **`[Rail 60px | Chat 1fr]` o `[History 280px | Chat 1fr]`** según `valeriaState`. Rail y history son mutuamente exclusivos (rail = history colapsada). 3 estados macro (`collapsed` · `rail` · `full`), keyboard shortcuts `c/r/f/n/Esc/Cmd+K` con guard anti-typing endurecido, mobile drawer slide-in con backdrop.

### Out-of-scope explícito (anti-creep)

- ❌ NO implementar chat real ni mensajería (eso es F1-S6)
- ❌ NO WebSocket / streaming / SSE (Fase 2)
- ❌ NO funcionalidad real "Nueva conversación" — solo alert mock
- ❌ NO API `/api/conversations` real — mock data hardcoded en archivo
- ❌ NO botones rail F2 (anclados/tareas/notas) — Chris ratificó "4 botones MVP-only" (batch 2 Q5)
- ❌ NO modificar `shell-store.ts` schema (`valeriaState` + `shellMode` + setters ya cementados en F1-S3/S4)
- ❌ NO tocar route group `(dashboard)/` legacy

### Pre-conditions cementadas (F1-S4 SSoT)

- `shell-store.ts` exporta `valeriaState ∈ {collapsed|rail|full}` + `shellMode ∈ {agentic|web}` con setters + `cycleValeriaState` (rail↔full only)
- `valeriaState` default = `'full'` (architect override DC §6.1, ratificado iter 4 Chris 2026-05-23)
- `ShellOrganismLayout` ya respeta agentic 50/50 vs web 60+1fr
- Tokens Vitalia activos: `--agent-valeria: 287 53% 37%` (purple) · `--agent-valeria-soft: 287 53% 90%` (chip/active)

### Decisiones cardinales batch 1+2 (ratificadas 2026-05-23)

| ID | Decisión | Justificación |
|---|---|---|
| **D1** | Layout `full` = `[History 280 | Chat 1fr]` (2 cols, **rail oculto**); `rail` = `[Rail 60 | Chat 1fr]` (2 cols, **history oculto**). Mutuamente exclusivos | Matches Nicolify CopilotSidebar transpuesto a izq. Mental model: "rail = history colapsado" (Chris batch 1 verbatim) |
| **D2** | `valeriaState='collapsed'` auto-triggers `setShellMode('web')` (Valeria pasa a rail 60px fijo + AppPanel 100%). Press `r` o `f` vuelve auto a `shellMode='agentic'` | UX coherente: minimizar Valeria = pasar a modo web. Evita gap muerto dentro de columna 50% (Chris batch 1 Q2 Option A) |
| **D3** | Side-effect F1-S4: ajustar `MIN_VALERIA_PX` en `ShellOrganismLayoutClient.tsx`: `valeriaState === 'full' ? 580 : 360` (era 620 asumiendo 3 cols obsoletas) | Matemática nueva: full = `280 history + 300 chat_min = 580`. Drag clamp queda coherente |
| **D4** | Shortcuts bare lowercase `c/r/f/n` + `Esc` + `Cmd/Ctrl+K`. Guard endurecido: skip si `e.isComposing` (IME) OR target ∈ `INPUT`/`TEXTAREA`/`[contenteditable=true]`/`[role=textbox]` o cualquier ancestor con esos atributos | Cero colisión con typing en composer (F1-S6 será textarea/contenteditable). Modificadores Shift no resuelven (`Shift+C` igual rompe typing "CITA") |
| **D5** | Rail 4 botones MVP-only: `PanelLeftOpen` (toggle→full) · `Plus` (nueva — alert mock) · `Search` (focus composer Cmd+K) · `spacer flex-1` · `PanelLeftClose` (collapsed→shellMode='web'). F2 (anclados/tareas/notas) **hidden completamente**, no greyed — se agregan en su story respectiva | Look minimal Fase 1, evita falsas affordances disabled. Iconos Lucide ya en `@/components/ui/icon` |
| **D6** | `ValeriaChatSlot` placeholder (F1-S5) = `ChatHeader` real con avatar Valeria + nombre + status dot "En línea" + body con 4 skeleton bubbles (alternados self-start grey + self-end agent-valeria-soft) + skeleton composer. Label flotante "CHATSLOT · F1-S6" identifica placeholder | Sensación shell "lleno" desde MVP. F1-S6 reemplaza body+composer pero respeta el header (transición sin cambio visual disruptivo) |
| **D7** | Mobile (`<md` viewport): hamburger button NEW en `TopBarGlobal.tsx` (esquina izq) abre `ValeriaSidebar` como drawer full slide-in desde izquierda (100vw `<sm`, 360px `sm-md`) con backdrop `bg-black/40 backdrop-blur-sm`. Cierra con: `Esc`, backdrop click, botón X interno, swipe-left | Pattern estándar mobile SaaS. Reusa pattern Nicolify CopilotSidebar mobile drawer (transpuesto a izq) |
| **D8** | Mock conversaciones: 8 items operación clínica genérica sin PHI (overlay `hipaa-lite.md`). Hoy(3) + Ayer(2) + Esta semana(3). Strings ratificados batch 1 Q4 | Verosímil del día a día Valeria copiloto, cero riesgo regulatorio en data demo |

---

## § 1 Gherkin scenarios

> **★ v4.1 gate enforcement:** 4 base scenarios (happy + negative + edge + adversarial) + sub-categorías mandatory aplicables (a11y + i18n + empty_state) + `not_applicable_reason` explícito para race_condition/concurrent_users/network_failure/large_dataset.

```yaml
sub_categories_coverage:
  race_condition:
    applies: false
    not_applicable_reason: "Story no crea/edita recursos persistentes con unique constraint. Mock data es read-only hardcoded; valeriaState transitions son setState local sin DB."
  concurrent_users:
    applies: false
    not_applicable_reason: "Shell chrome per-user (zustand local + localStorage). No comparte estado entre tenants/users."
  network_failure:
    applies: false
    not_applicable_reason: "F1-S5 no realiza fetch API alguno. Mock conversaciones son import estático desde _mock-conversations.ts. F1-S6+ introducen WebSocket/HTTP — sus scenarios cubrirán network_failure."
  large_dataset:
    applies: false
    not_applicable_reason: "Mock data = 8 items hardcoded. Pagination/virtualization queda para Fase 2 cuando se conecte API real (out-of-scope F1-S5)."
  empty_state:    { applies: true, scenarios: [scenario-6] }
  accessibility:  { applies: true, scenarios: [scenario-7, scenario-8] }
  i18n:           { applies: true, scenarios: [scenario-9] }
```

---

### Scenario 1 — `happy` keyboard cycle de estados

```yaml
type: happy
playwright_required: true
given:
  - "Usuario autenticado en shell agéntico (route `/test-stack/shell-layout` para E2E sin Clerk)"
  - "valeriaState default = 'full' (architect override F1-S4)"
  - "shellMode default = 'agentic' (50/50 split)"
  - "Focus NO está en ningún <input>/<textarea>/[contenteditable]"
when:
  - "User presiona tecla `r`"
  - "User presiona tecla `f`"
  - "User presiona tecla `c`"
  - "User presiona tecla `Escape`"
  - "User presiona tecla `r` de nuevo"
then:
  - "Press `r`: ValeriaSidebar transitions a [Rail 60 | Chat 1fr], history desaparece, shellMode sigue 'agentic'"
  - "Press `f`: ValeriaSidebar transitions a [History 280 | Chat 1fr], rail desaparece"
  - "Press `c`: setValeriaState('collapsed') + setShellMode('web') auto-coupled. Shell layout pasa a [Rail 60 | 1px divider | AppPanel 1fr]. Chat oculto"
  - "Press `Esc`: idempotente — sigue en collapsed/web"
  - "Press `r` de nuevo: setValeriaState('rail') + setShellMode('agentic') auto-restored. Shell vuelve a 50/50"
  - "localStorage `vitalia-shell-store` persiste valeriaState + shellMode tras cada cambio"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/keyboard-cycle.spec.ts" }
  - { type: state_check, target: localStorage, key: "vitalia-shell-store", expect: "valeriaState matches final state" }
```

---

### Scenario 2 — `negative` typing en composer NO dispara shortcuts

```yaml
type: negative
playwright_required: true
given:
  - "ValeriaSidebar en state 'full'"
  - "User clickeó dentro del composer (textarea/contenteditable del ChatSlot placeholder o input search del history)"
  - "Focus actual = composer"
when:
  - "User escribe la palabra 'COMPRAR' (presiona C-O-M-P-R-A-R)"
  - "User presiona Enter"
then:
  - "Letras `c/r` (que son shortcuts globales) se escriben normalmente en el campo — NO transitan estado"
  - "valeriaState sigue 'full' (no cambió a rail ni collapsed)"
  - "Cero side-effect en localStorage shell-store"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/typing-guard.spec.ts" }
  - { type: state_check, target: input_value, expect: "COMPRAR (full text preserved)" }
```

---

### Scenario 3 — `edge` IME composition (acentos / lenguajes 2-byte)

```yaml
type: edge
playwright_required: true
given:
  - "Focus en composer textarea"
  - "User activa IME (Pinyin / acento muerto teclado español ej. `´` + `a` = `á`)"
when:
  - "User comienza composición IME (`e.isComposing === true`)"
  - "Durante composición, user accidentalmente roza tecla `r` o `c`"
then:
  - "Handler skip por `e.isComposing` guard — NO transition valeriaState"
  - "IME composition continúa sin interrupción"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/ime-composition.spec.ts" }
```

---

### Scenario 4 — `adversarial` shell-store tampering desde devtools

```yaml
type: adversarial
playwright_required: true
given:
  - "ValeriaSidebar en state 'rail'"
when:
  - "Atacante en devtools console ejecuta: useShellStore.setState({ valeriaState: 'INVALID' as any })"
then:
  - "Type guard en runtime ignora valor inválido OR ValeriaSidebar render falla gracefully (fallback a 'rail' default)"
  - "Cero crash app · cero white screen"
  - "Console warning structlog-equivalente (browser console.warn) emite 'Invalid valeriaState ignored'"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/store-tampering.spec.ts" }
  - { type: state_check, target: dom, selector: "[data-testid=valeria-sidebar]", expect: "renders without throwing" }
```

---

### Scenario 5 — `edge` click rail PanelLeftClose mientras shellMode='agentic'

```yaml
type: edge
playwright_required: true
given:
  - "ValeriaSidebar state='rail', shellMode='agentic' (50/50 split)"
when:
  - "User click botón `PanelLeftClose` (footer rail)"
then:
  - "setValeriaState('collapsed') + setShellMode('web') ejecutados (mismo handler que keyboard `c`)"
  - "Shell layout transitions 50/50 → [60px Rail | 1px | AppPanel 1fr] con animación 220ms"
  - "Chat se oculta, rail queda visible (4 botones MVP)"
  - "Click `PanelLeftOpen` o press `r`/`f` vuelve a agentic"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/click-collapse.spec.ts" }
```

---

### Scenario 6 — `empty_state` búsqueda sin resultados

```yaml
type: empty_state
sub_category: empty_state
playwright_required: true
given:
  - "ValeriaSidebar state='full' (history visible con 8 mock items)"
  - "Focus en input search del history"
when:
  - "User escribe 'xyzabc123' (string que no matchea ningún mock title)"
then:
  - "Lista de history items se filtra a 0 resultados"
  - "Componente `EmptyStateInline` muestra: icon Search24 muted + h3 'Sin resultados' + p 'Intenta con otra palabra' (Spanish neutro)"
  - "Grupos 'Hoy/Ayer/Esta semana' desaparecen (no mostrar labels vacíos)"
  - "Input search retiene texto escrito"
  - "Press Esc limpia búsqueda + restablece lista completa (NO colapsa Valeria mientras input tiene focus)"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/history-empty-search.spec.ts" }
  - { type: visual_state, screen: "history-empty", element: "[data-testid=history-empty-state]", expect: "visible + Spanish neutro copy" }
```

---

### Scenario 7 — `accessibility` keyboard navigation completo

```yaml
type: a11y
sub_category: accessibility
playwright_required: true
given:
  - "ValeriaSidebar montado (state='rail')"
  - "Screen reader simulated (axe-playwright + manual Tab traversal)"
when:
  - "User presiona Tab repetidamente comenzando desde TopBar"
then:
  - "Tab order lógico: TopBar items → Rail buttons (PanelLeftOpen → Plus → Search → PanelLeftClose) → ChatSlot composer placeholder"
  - "Cada botón rail anuncia su rol + nombre via `aria-label` (ej. 'Abrir historial conversaciones')"
  - "Aside raíz tiene `role='complementary'` + `aria-label='Panel Valeria'` + `aria-expanded={valeriaState !== 'collapsed'}`"
  - "Live region `role='status' aria-live='polite'` anuncia cambios de estado: 'Valeria con historial' / 'Valeria abierta' / 'Valeria cerrada'"
  - "Contrast ratio texto rail buttons hover ≥ 4.5:1 (tokens vitalia validan)"
  - "axe-playwright ruleset wcag2aa 0 violations en estados collapsed/rail/full"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/a11y-keyboard.spec.ts" }
  - { type: axe, ruleset: "wcag2aa", target: "[data-testid=valeria-sidebar]" }
```

---

### Scenario 8 — `accessibility` mobile drawer aria-modal + focus trap

```yaml
type: a11y
sub_category: accessibility
playwright_required: true
given:
  - "Viewport 375x667 (mobile)"
  - "Drawer cerrado, focus en TopBar hamburger button"
when:
  - "User press Enter (o tap) hamburger"
  - "User press Tab repetidamente dentro del drawer abierto"
  - "User press Esc"
then:
  - "Drawer abre con `aria-modal='true'` + focus auto-mueve al primer elemento interactivo dentro (input search history o primer rail button)"
  - "Focus trap activo: Tab cycle dentro del drawer, no escapa al background"
  - "Backdrop tiene `aria-hidden='true'` + click cierra drawer"
  - "Press Esc cierra drawer + focus auto-retorna al hamburger button (focus restoration)"
  - "axe-playwright 0 violations modal pattern"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/a11y-mobile-drawer.spec.ts" }
  - { type: axe, ruleset: "wcag2aa", target: "[data-testid=valeria-sidebar]" }
```

---

### Scenario 9 — `i18n` Spanish neutro LatAm renderizado

```yaml
type: i18n
sub_category: i18n
playwright_required: true
given:
  - "ValeriaSidebar state='full' montado en cualquier viewport"
when:
  - "Render completo del componente"
then:
  - "Todos los strings user-facing son Spanish neutro (tuteo, sin voseo): 'Conversaciones', 'Buscar conversación...', 'Nueva conversación', 'Hoy', 'Ayer', 'Esta semana', 'Sin resultados', 'Intenta con otra palabra', 'En línea', 'Valeria'"
  - "Tooltips rail buttons: 'Mostrar historial', 'Nueva conversación', 'Buscar (Cmd+K)', 'Cerrar Valeria'"
  - "Alert mock al press `n`: 'Nueva conversación (próximamente)'"
  - "aria-labels español neutro: 'Panel Valeria', 'Historial conversaciones', 'Cerrar panel Valeria'"
  - "Cero voseo: cero match contra glosario `.claude/rules/spanish-text.md` (`vos|sos|tenés|podés|querés|dale|mirá|fijate`)"
  - "Cero placeholders sin traducir tipo 'TODO' / 'Lorem ipsum' / 'Search...' (inglés)"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/i18n-spanish-neutro.spec.ts" }
  - { type: visual_state, screen: "history-full", element: "all-strings", expect: "matches Spanish neutro glossary" }
```

---

## § 2 Wireframes inline (ASCII + HTML mockups)

> Mockups HTML ratificados son SSoT visual per overlay `shell-mockup-per-component.md`. ASCII abajo es referencia rápida — el detalle visual exacto vive en los HTML.

### State `full` desktop (md+, agentic shellMode)

```
ShellOrganismLayout (50/50 agentic split):
┌──────────────────────────────────────────────────────────────────────────┐
│ TopBarGlobal: [Vitalia] [TenantSwitcher ▾]    [ThemeToggle 🌗] [User ▾] │ ← h-14
├──────────────────────────┬───────────────────────────────────────────────┤
│ ValeriaSidebar [full]    │ AppPanel (F1-S7..S10 ribbon + sub-tabs)       │
│ aside role="complementary"│                                               │
│                          │                                               │
│ ┌──────────┬───────────┐ │   [ribbon 6 tabs placeholder F1-S7]           │
│ │ History  │ ChatSlot  │ │   [sub-tabs línea 2 placeholder F1-S8]        │
│ │  280px   │  1fr      │ │                                               │
│ │          │           │ │   [contenido vacío / placeholder F1-S10]      │
│ │ ┌──────┐ │ ┌────────┐│ │                                               │
│ │ │🔍 ...│ │ │(·)Vale.││ │                                               │
│ │ └──────┘ │ │En línea││ │                                               │
│ │          │ └────────┘│ │                                               │
│ │ ▼ Hoy    │           │ │                                               │
│ │  · Res.. │ ■■■■■■■   │ │                                               │
│ │  · Ide.. │      ■■■  │ │                                               │
│ │  · Rep.. │ ■■■■■■■■■ │ │                                               │
│ │ ▼ Ayer   │      ■■   │ │                                               │
│ │  · Bor.. │           │ │                                               │
│ │  · Tut.. │┌─────────┐│ │                                               │
│ │ ▼ Esta   ││ composer││ │                                               │
│ │ semana   ││ skeleton││ │                                               │
│ │  · Plan..│└─────────┘│ │                                               │
│ │  · Mét.. │           │ │                                               │
│ │  · Rev.. │ [F1-S6]   │ │                                               │
│ └──────────┴───────────┘ │                                               │
└──────────────────────────┴───────────────────────────────────────────────┘
MIN Valeria = 280 + 300 = 580px (D3 fix MIN_VALERIA_PX)
```

### State `rail` desktop (md+, agentic shellMode)

```
ValeriaSidebar [rail]      │ AppPanel
┌─────┬─────────────────┐  │
│Rail │ ChatSlot 1fr    │  │
│60px │                 │  │
│ ▣   │ ┌─────────────┐ │  │  ▣ PanelLeftOpen  → press `f` o click → full
│ ✚   │ │(·)Valeria   │ │  │  ✚ Plus           → press `n` o click → alert mock
│ 🔍  │ │En línea     │ │  │  🔍 Search        → press Cmd+K → focus composer
│     │ └─────────────┘ │  │
│     │                 │  │  (spacer flex-1)
│     │ ■■■■■■■■        │  │
│     │       ■■■■■     │  │  ⯇ PanelLeftClose → press `c` o click → collapsed (web)
│     │ ■■■■■■■■■■■■    │  │
│     │      ■■■        │  │
│     │ ┌─────────────┐ │  │
│     │ │ composer    │ │  │
│     │ │ skeleton    │ │  │
│ ⯇   │ └─────────────┘ │  │
└─────┴─────────────────┘  │
MIN Valeria = 60 + 300 = 360px
```

### State `collapsed` desktop (auto-coupled a shellMode='web')

```
ShellOrganismLayout (web mode):
┌──────────────────────────────────────────────────────────────────────────┐
│ TopBarGlobal                                                             │
├─────┬────────────────────────────────────────────────────────────────────┤
│Rail │ AppPanel 1fr (100% content area)                                   │
│60px │                                                                    │
│ ▣   │   [ribbon + sub-tabs + contenido sin gap]                          │
│ ✚   │                                                                    │
│ 🔍  │                                                                    │
│     │                                                                    │
│ ⯇*  │   * Press `r` o `f` o click PanelLeftOpen → vuelve a agentic       │
└─────┴────────────────────────────────────────────────────────────────────┘
```

### Mobile (`<md`, drawer pattern)

```
Closed state:
┌──────────────────────┐
│ ☰ Vitalia       🌗 │ ← TopBar con hamburger NEW (D7 side-effect)
├──────────────────────┤
│  AppPanel 100%       │
│  (sin Valeria visible)│
└──────────────────────┘

After tap ☰ (drawer slide-in desde izq):
┌──────────────────────────────────┐
│ Valeria              ✕  │ ░░░░░░ │
│ ┌────────┬───────────┐  │ ░░ack  │
│ │History │ChatSlot   │  │ ░░dro  │
│ │ full   │           │  │ ░░p    │
│ │        │           │  │ ░░bg   │
│ │        │ composer  │  │ ░░40%  │
│ └────────┴───────────┘  │ ░blur  │
└──────────────────────────────────┘
Width: 100vw (<sm), 360px (sm-md)
```

### Mockups HTML (SSoT visual)

| Mockup | Path | Estados | Brand overlay |
|---|---|---|---|
| `valeria-rail.html` | `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html` | rail desktop · collapsed desktop · light + dark | mandatorio per `shell-mockup-per-component.md` |
| `valeria-history.html` | `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-history.html` | full desktop · full mobile drawer · empty search · light + dark | mandatorio per `shell-mockup-per-component.md` |

Servir local:
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups
python3 -m http.server 8888
# Chris abre http://localhost:8888/valeria-rail.html y /valeria-history.html
```

---

## § 3 Estados visuales (por surface)

### `ValeriaSidebar` raíz

| Estado | Trigger | Layout interno | Aside attrs |
|---|---|---|---|
| `idle` (initial mount, persisted='full') | render | `[History 280 | Chat 1fr]` | `aria-expanded="true" aria-label="Panel Valeria"` |
| `rail` | press `r`/click PanelLeftOpen | `[Rail 60 | Chat 1fr]` | `aria-expanded="true"` |
| `full` | press `f`/click PanelLeftOpen desde rail | `[History 280 | Chat 1fr]` | `aria-expanded="true"` |
| `collapsed` | press `c`/`Esc`/click PanelLeftClose | `[Rail 60]` solo (no chat). Shell layout switches a web mode | `aria-expanded="false"` |
| `drawer-open` (mobile) | tap hamburger TopBar | `[History 280 | Chat 1fr]` dentro de drawer | `aria-modal="true" aria-expanded="true"` + focus trap |

### `ValeriaHistory` panel

| Estado | Trigger | Visible | Oculto |
|---|---|---|---|
| `populated` (default) | mount + mock 8 items | Header "Conversaciones" + Search input + 3 grupos (Hoy/Ayer/Esta semana) + 8 items | EmptyStateInline |
| `searching` | user escribe en search | Lista filtrada por match `title.toLowerCase().includes(query)` + grupos sin items se ocultan | — |
| `empty` | search query sin matches | `EmptyStateInline` (icon Search24 muted + "Sin resultados" + "Intenta con otra palabra") | grupos + items |
| `loading` (futuro Fase 2) | N/A en F1-S5 | — | — (mock data sync) |

### `ValeriaRail` molécula

| Estado | Visible |
|---|---|
| `default` | 4 botones: PanelLeftOpen (top) · Plus · Search · [spacer] · PanelLeftClose (footer) |
| `hover-btn` | Tooltip Shadcn aparece con label + keyboard hint (ej. "Mostrar historial · f") |

### `ValeriaChatSlot` placeholder

| Estado | Visible |
|---|---|
| `placeholder` (default F1-S5) | ChatHeader real (avatar Valeria + "Valeria" + "• En línea") + 4 skeleton bubbles + skeleton composer + label flotante "CHATSLOT · F1-S6" |

---

## § 4 Componentes (reuse > new)

### Reuse desde Shadcn primitives (ya instalados F1-S0/S1)

| Componente | Path | Uso |
|---|---|---|
| `Button` (variant ghost, size icon) | `vitalia/frontend/src/components/ui/button.tsx` | Rail buttons + history quick actions |
| `Input` | `vitalia/frontend/src/components/ui/input.tsx` | Search history |
| `Tooltip` | `vitalia/frontend/src/components/ui/tooltip.tsx` | Hover hints rail buttons |
| `cn()` util | `vitalia/frontend/src/lib/utils.ts` | conditional classes |

### Reuse desde shell-organism F1-S2/S3/S4

| Componente | Path | Uso |
|---|---|---|
| `TopBarGlobal` | `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | MODIFY: agregar hamburger button `<md` (D7) |
| `useShellStore` | `vitalia/frontend/src/stores/shell-store.ts` | consumir valeriaState + shellMode + setters (sin modificar schema) |
| `ShellOrganismLayoutClient` | `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | MODIFY: `MIN_VALERIA_PX` full 620→580 (D3) + replace `<ValeriaSidebarSlot/>` por `<ValeriaSidebar/>` real |

### NEW componentes (8 archivos)

| Componente | Path | Justificación NEW |
|---|---|---|
| `ValeriaSidebar` | `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | Organismo raíz F1-S5. NO existe equivalente; nicolify CopilotSidebar es REUSE pattern pero transposed (no copy directo por D1 layout 2-col asymmetric) |
| `ValeriaRail` | idem dir / `ValeriaRail.tsx` | Molécula 60px rail. NEW (similar a `CopilotRail` Nicolify pero adapt) |
| `ValeriaHistory` | idem dir / `ValeriaHistory.tsx` | Molécula 280px history. NEW (similar a `CopilotHistoryPanel` Nicolify pero adapt) |
| `ValeriaChatSlot` | idem dir / `ValeriaChatSlot.tsx` | Placeholder header+skeleton bubbles. F1-S6 lo extiende, no reemplaza |
| `HistoryItem` | idem dir / `HistoryItem.tsx` | Row clicable title+meta+active. NEW |
| `HistoryGroup` | idem dir / `HistoryGroup.tsx` | Section label+items[]. NEW |
| `EmptyStateInline` | idem dir / `EmptyStateInline.tsx` | Empty state genérico para search sin resultados. NEW (candidate lift a `components/shared/` post-F1) |
| `_mock-conversations.ts` | idem dir / `_mock-conversations.ts` | Data hardcoded 8 items + types. NEW (eliminar cuando F2 conecta API real) |

### NEW hooks (1 archivo)

| Hook | Path | Justificación |
|---|---|---|
| `useKeyboardShortcuts` | `vitalia/frontend/src/hooks/useKeyboardShortcuts.ts` | Hook generic shortcuts + hardened guard (D4). NEW. Candidate lift a `core/luana-core-ui-hooks/` futuro (promotable cross-brand) |

### MODIFY (side-effects F1-S4 ratificados)

| Path | Cambio | Origen |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | `MIN_VALERIA_PX` ternary: 620→580 | D3 (Chris batch 1b) |
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | Replace import + render `<ValeriaSidebarSlot/>` → `<ValeriaSidebar/>` | F1-S5 propósito |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | Agregar hamburger button `<md` viewport + handler `setValeriaState('full') + setShellMode('agentic')` (abre drawer) | D7 (Chris batch 2) |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx` | DELETE (reemplazado por ValeriaSidebar real) | F1-S5 cleanup |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.test.tsx` | DELETE | idem |

---

## § 5 Data flow

### Estado client-side

- **Zustand `useShellStore`**: ya define `valeriaState` + `shellMode` + setters (sin cambios schema). Persist via `partialize`.
- **React state local en `ValeriaHistory`**: `const [searchQuery, setSearchQuery] = useState('')` para filter mock items.
- **NO React Query**: F1-S5 no consume API.

### Mock data shape

```ts
// _mock-conversations.ts
export type MockConversation = {
  id: string;
  title: string;
  meta: string;          // ej. "14:32 · 8 mensajes"
  group: 'today' | 'yesterday' | 'this_week';
  active?: boolean;       // futuro: highlight conversación activa
};

export const MOCK_CONVERSATIONS: MockConversation[] = [
  { id: '1', title: 'Resumen reseñas Google semana', meta: '14:32 · 8 mensajes', group: 'today' },
  { id: '2', title: 'Ideas campaña Día de la Madre', meta: '11:18 · 12 mensajes', group: 'today' },
  { id: '3', title: 'Reporte ocupación martes',      meta: '09:45 · 5 mensajes',  group: 'today' },
  { id: '4', title: 'Borrador respuesta a reseña 3⭐',meta: 'Ayer 19:02 · 4 msgs', group: 'yesterday' },
  { id: '5', title: 'Tutorial agenda online turnos', meta: 'Ayer 15:30 · 7 msgs', group: 'yesterday' },
  { id: '6', title: 'Plan ofertas mes mayo',         meta: 'Lun · 11 mensajes',    group: 'this_week' },
  { id: '7', title: 'Métricas conversión landing',   meta: 'Lun · 6 mensajes',     group: 'this_week' },
  { id: '8', title: 'Revisar copy WhatsApp bienvenida',meta: 'Dom · 9 mensajes',   group: 'this_week' },
];
```

### Filter logic (ValeriaHistory)

```ts
const filtered = useMemo(
  () => MOCK_CONVERSATIONS.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase().trim())
  ),
  [searchQuery]
);

const grouped = useMemo(
  () => ({
    today:     filtered.filter(c => c.group === 'today'),
    yesterday: filtered.filter(c => c.group === 'yesterday'),
    this_week: filtered.filter(c => c.group === 'this_week'),
  }),
  [filtered]
);
```

### Handlers

| Action | Handler |
|---|---|
| Click rail PanelLeftOpen (rail state) | `setValeriaState('full')` |
| Click rail PanelLeftOpen (collapsed state) | `setValeriaState('full') + setShellMode('agentic')` |
| Click rail Plus | `alert('Nueva conversación (próximamente)')` |
| Click rail Search | `document.getElementById('valeria-composer-placeholder')?.focus()` (F1-S6 conectará composer real) |
| Click rail PanelLeftClose | `setValeriaState('collapsed') + setShellMode('web')` |
| Click history quick action "+" | `alert('Nueva conversación (próximamente)')` |
| Click history quick action "←" colapsar | `setValeriaState('rail')` |
| Click HistoryItem | `setActiveConversationId(item.id)` (local state, futuro Fase 2 conecta a chat) |
| Press `c` / `Esc` (no input focus) | `setValeriaState('collapsed') + setShellMode('web')` |
| Press `r` (no input focus) | `setValeriaState('rail') + setShellMode('agentic')` |
| Press `f` (no input focus) | `setValeriaState('full') + setShellMode('agentic')` |
| Press `n` (no input focus) | `alert('Nueva conversación (próximamente)')` |
| Press `Cmd/Ctrl+K` | `document.getElementById('valeria-composer-placeholder')?.focus()` |
| Tap hamburger TopBar (mobile) | `setValeriaState('full') + setShellMode('agentic')` (abre drawer) |
| Tap X drawer / backdrop / swipe-left / `Esc` (mobile) | `setValeriaState('collapsed')` (cierra drawer, mantiene shellMode) |

---

## § 6 Microcopy (Spanish neutro LatAm)

<!-- voseo-allowed: glosario reference solo (forbidden voseo examples in this section's checklist) -->

| Lugar | Copy |
|---|---|
| `<aside>` aria-label | "Panel Valeria" |
| Live region rail | "Valeria abierta" / "Valeria con historial" / "Valeria cerrada" |
| Rail button `aria-label` PanelLeftOpen (rail→full) | "Mostrar historial" |
| Rail button `aria-label` Plus | "Nueva conversación" |
| Rail button `aria-label` Search | "Buscar (Cmd+K)" |
| Rail button `aria-label` PanelLeftClose | "Cerrar Valeria" |
| Tooltip PanelLeftOpen | "Mostrar historial · f" |
| Tooltip Plus | "Nueva conversación · n" |
| Tooltip Search | "Buscar · ⌘K" |
| Tooltip PanelLeftClose | "Cerrar · c" |
| History header title | "Conversaciones" |
| History quick action "+" tooltip | "Nueva conversación · n" |
| History quick action "←" tooltip | "Colapsar a barra · r" |
| Search input placeholder | "Buscar conversación..." |
| Search input `aria-label` | "Buscar conversación" |
| Group label `today` | "Hoy" |
| Group label `yesterday` | "Ayer" |
| Group label `this_week` | "Esta semana" |
| Empty state search heading | "Sin resultados" |
| Empty state search description | "Intenta con otra palabra" |
| Alert mock "n" | "Nueva conversación (próximamente)" |
| ChatSlot header title | "Valeria" |
| ChatSlot header status | "En línea" |
| ChatSlot label flotante | "CHATSLOT · F1-S6" |
| ChatSlot aria-label section | "Chat con Valeria (próximamente)" |
| Drawer mobile close button `aria-label` | "Cerrar panel Valeria" |
| Confirmation modal | _(N/A en F1-S5 — no destructive actions)_ |

**Glossary check enforcement:** ningún string contiene voseo verbs (`vos|sos|tenés|podés|querés|sabés|dale|mirá|fijate|dejá|poné|usá|hacé`) ni léxico regional. Tildes + ñ + apertura `¿!` cuando aplique. Test grader `i18n-spanish-neutro.spec.ts` regex-validates.

---

## § 7 Responsive breakpoints

| Breakpoint | Comportamiento |
|---|---|
| `<sm` (< 640px) | Drawer mobile full-width 100vw. Hamburger TopBar visible. Desktop ValeriaSidebar hidden (`hidden md:flex`) |
| `sm` (640-767px) | Drawer mobile 360px ancho fijo desde izq. Hamburger TopBar visible |
| `md` (768-1023px) | Desktop ValeriaSidebar visible. Layout agentic posible pero apretado (min 580px Valeria + 480px AppPanel = 1060px → solo se ve cómodo en md superior). En md inferior se ve "encimado" — aceptable, Chris no priorizó breakpoint intermedio. Hamburger TopBar oculto |
| `≥ lg` (1024px+) | Desktop ValeriaSidebar full visible. Layout agentic/web según shellMode |

CSS pattern:
```tsx
className="hidden md:flex"     // desktop ValeriaSidebar
className="md:hidden"           // mobile drawer + hamburger
```

---

## § 8 Accessibility

### ARIA contract

```html
<aside
  role="complementary"
  aria-label="Panel Valeria"
  aria-expanded={valeriaState !== 'collapsed'}
  data-testid="valeria-sidebar"
>
  <!-- Mobile drawer wrapper agrega aria-modal="true" + focus trap -->

  {/* Live region a11y */}
  <span
    role="status"
    aria-live="polite"
    aria-atomic="true"
    className="sr-only"
  >
    {valeriaState === 'collapsed' ? 'Valeria cerrada'
      : valeriaState === 'rail' ? 'Valeria abierta'
      : 'Valeria con historial'}
  </span>

  {/* Rail buttons */}
  <button aria-label="Mostrar historial" type="button" data-testid="rail-toggle-history">
    <PanelLeftOpen aria-hidden="true" />
  </button>
  ...

  {/* History panel */}
  <nav aria-label="Historial conversaciones" data-testid="history-panel">
    <input
      type="search"
      aria-label="Buscar conversación"
      placeholder="Buscar conversación..."
      data-testid="history-search"
    />
    ...
  </nav>

  {/* ChatSlot placeholder */}
  <section
    role="region"
    aria-label="Chat con Valeria (próximamente)"
    data-testid="valeria-chat-slot"
  >
    ...
  </section>
</aside>
```

### Focus management

- Initial mount: NO auto-focus (respeta default browser, focus va a TopBar primero)
- Mobile drawer open: focus auto-mueve a primer interactivo (input search si full, primer rail button si rail)
- Mobile drawer close: focus restoration al hamburger TopBar
- Cmd+K: focus a composer placeholder (F1-S6 conecta composer real)
- Focus trap mobile: `focus-trap-react` o impl manual con `KeyboardEvent.Tab` cycling

### Contrast (validado contra tokens Vitalia)

| Elemento | Light | Dark |
|---|---|---|
| Rail button icon vs bg | `text-foreground` (240 10% 4%) vs `bg-card` (0 0% 100%) → ratio ~21:1 ✓ | `text-foreground` (0 0% 98%) vs `bg-card` (240 8% 8%) → ratio ~18:1 ✓ |
| History item title hover | `text-foreground` vs `bg-muted` (240 5% 96%) → ratio ~16:1 ✓ | idem dark ratio ~14:1 ✓ |
| Active history item | `text-foreground` vs `bg-agent-valeria-soft` (287 53% 90%) → ratio ~13:1 ✓ | `text-foreground` vs `bg-agent-valeria-soft` (287 40% 25%) → ratio ~11:1 ✓ |

### Reduced motion

```tsx
className="transition-[grid-template-columns] duration-[220ms] motion-reduce:transition-none"
```

---

## § 9 Telemetría (opcional Fase 2)

Sin events en F1-S5 (mock-only). Para Fase 2 cuando integra analytics:

```yaml
events_F2_plan:
  - { name: "valeria_state_changed", trigger: "setValeriaState", props: ["from", "to", "trigger_source: keyboard|click|hamburger"] }
  - { name: "valeria_conversation_clicked", trigger: "HistoryItem click", props: ["conversation_id"] }
  - { name: "valeria_search_used", trigger: "input change debounced 500ms", props: ["query_length"] }
```

---

## § 10 Brand voice

N/A en F1-S5 — shell chrome UI puro, no muestra output sales_agent ni text generado por LLM. Microcopy es Spanish neutro estándar (§6). Voice tenant-specific se aplicará en F1-S6 (chat real) cuando se integre con `personality_profiles.system_instruction`.

---

## § 11 Visual Goldens mapping

> Per `shell-mockup-per-component.md` § Tests requeridos: mapping trazable mockup HTML → golden snapshot → componente React.

| Mockup HTML | Golden snapshot path | Componente React | Design Contract ref |
|---|---|---|---|
| `mockups/valeria-rail.html` (light) | `e2e/__screenshots__/shell/valeria-rail-light.png` | `ValeriaSidebar` state='rail' | DC §6.1 + §6.2 |
| `mockups/valeria-rail.html` (dark) | `e2e/__screenshots__/shell/valeria-rail-dark.png` | idem theme='dark' | idem |
| `mockups/valeria-rail.html` (collapsed) | `e2e/__screenshots__/shell/valeria-collapsed-light.png` + dark | `ValeriaSidebar` state='collapsed' (con auto-coupled shellMode='web') | DC §6.1 |
| `mockups/valeria-history.html` (light full desktop) | `e2e/__screenshots__/shell/valeria-full-light.png` | `ValeriaSidebar` state='full' | DC §6.3 |
| `mockups/valeria-history.html` (dark full desktop) | `e2e/__screenshots__/shell/valeria-full-dark.png` | idem | idem |
| `mockups/valeria-history.html` (empty search) | `e2e/__screenshots__/shell/valeria-history-empty-light.png` + dark | `ValeriaHistory` searchQuery='xyzabc' | DC §6.3 |
| `mockups/valeria-history.html` (mobile drawer) | `e2e/__screenshots__/shell/valeria-drawer-mobile.png` | `ValeriaSidebar` viewport 375x667 drawer open | DC §6.4 mobile |

Tolerance: `maxDiffPixelRatio: 0.001` (0.1%) per protocolo. Ratchet shrink-only.

---

## § 12 Deliverables

### Files NEW (10)

| Path | Tipo |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | client component organismo |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaRail.tsx` | client component molécula |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaHistory.tsx` | client component molécula |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx` | server component placeholder |
| `vitalia/frontend/src/components/shared/shell-organism/HistoryItem.tsx` | client component átomo |
| `vitalia/frontend/src/components/shared/shell-organism/HistoryGroup.tsx` | client component molécula |
| `vitalia/frontend/src/components/shared/shell-organism/EmptyStateInline.tsx` | server component átomo |
| `vitalia/frontend/src/components/shared/shell-organism/_mock-conversations.ts` | data + types |
| `vitalia/frontend/src/hooks/useKeyboardShortcuts.ts` | hook generic con hardened guard |
| `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html` | mockup HTML SSoT visual |
| `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-history.html` | mockup HTML SSoT visual |

### Files MODIFY (3)

| Path | Cambio |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | `MIN_VALERIA_PX`: full 620→580 (D3) + replace `<ValeriaSidebarSlot/>` → `<ValeriaSidebar/>` |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | Agregar hamburger button (Menu icon Lucide) visible `<md` con handler abre Valeria drawer (D7) |
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.test.tsx` | Update test assertions: ya no espera `ValeriaSidebarSlot`, ahora `ValeriaSidebar` |

### Files DELETE (2)

| Path | Razón |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx` | Reemplazado por `ValeriaSidebar` real |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.test.tsx` | idem |

### Files NEW tests (estimado — /architect refinará exact)

| Path | Tipo |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.test.tsx` | Vitest unit |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaRail.test.tsx` | Vitest unit |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaHistory.test.tsx` | Vitest unit (filter + grouping) |
| `vitalia/frontend/src/hooks/__tests__/useKeyboardShortcuts.test.ts` | Vitest hook |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/keyboard-cycle.spec.ts` | Playwright |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/typing-guard.spec.ts` | Playwright |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/ime-composition.spec.ts` | Playwright |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/store-tampering.spec.ts` | Playwright |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/click-collapse.spec.ts` | Playwright |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/history-empty-search.spec.ts` | Playwright + visual |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/a11y-keyboard.spec.ts` | Playwright + axe |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/a11y-mobile-drawer.spec.ts` | Playwright + axe |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/i18n-spanish-neutro.spec.ts` | Playwright |
| `vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts` | Playwright visual (7 snapshots light+dark) |
| `vitalia/frontend/e2e/__screenshots__/shell/valeria-{rail,collapsed,full}-{light,dark}.png` | golden snapshots (6) |
| `vitalia/frontend/e2e/__screenshots__/shell/valeria-history-empty-{light,dark}.png` | golden snapshots (2) |
| `vitalia/frontend/e2e/__screenshots__/shell/valeria-drawer-mobile.png` | golden snapshot (1) |

---

## § 13 Próximo paso post-done

- **F1-S6 `vitalia-fase1-valeria-chat-skeleton`** reemplaza body+composer del `ValeriaChatSlot` con chat real (mensajes + input enviado al backend mock).
- F1-S5 deja el `ChatHeader` (avatar+nombre+status) construido — F1-S6 lo respeta intacto.

---

## § 14 Open questions (para iterar Chris)

_(ninguna en draft v1 — todas las decisiones cardinales D1-D8 ratificadas en batches 1+2. Si surgen edge cases durante mockup review, bumpear `po_ux_version` y agregar aquí.)_

---

## § 15 Pre-handoff checklist v4.1

- [x] 4 scenarios base (happy + negative + edge + adversarial)
- [x] Sub-categorías mandatory: empty_state (Scenario 6) + accessibility (Scenarios 7+8) + i18n (Scenario 9). N/A reasons documentados (race_condition/concurrent_users/network_failure/large_dataset)
- [x] Cada scenario funcional FE tiene `playwright_required: true`
- [x] Cada `then:` verificable (specifics, no vagos)
- [x] `graders:` declarados (e2e + state_check + axe + visual_state)
- [x] Wireframes inline (ASCII §2) + HTML mockups TODO (gate visual `shell-mockup-per-component.md`)
- [x] Estados visuales (idle/loading/success/error/empty/drawer-open §3)
- [x] Microcopy Spanish neutro (§6) + glossary check explícito
- [x] Componentes reuse > new (justificación inline §4)
- [x] Responsive breakpoints (§7)
- [x] Accessibility section (§8)
- [x] Visual Goldens mapping (§11) per brand overlay
- [ ] ★ **PENDIENTE:** mockups HTML producidos + ratificados Chris (Task 2+3+4 en progress)

→ Una vez Chris ratifica mockups + spec → frontmatter `ratified_by_chris: true` + `ratified_visual_by_chris: true` + state refining→refined + AUTO-HANDOFF `/architect`.
