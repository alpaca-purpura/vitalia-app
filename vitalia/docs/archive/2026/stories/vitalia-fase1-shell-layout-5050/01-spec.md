---
story_id: vitalia-fase1-shell-layout-5050
brand: vitalia
type: ui-story
state: refined
phase: fase-1
outcome: vitalia-mvp-ui-foundation
module: shell-organism
capability: shell.layout-5050
agent_owner: shell
ratified_by_chris: true
ratified_at: 2026-05-23T13:45:00Z
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-23T13:45:00Z
po_ux_version: v1
playwright_required: true
hipaa_lite_scope: not_applicable          # UI shell sin PHI — slots placeholders, datos paciente fuera de scope
---

# F1-S4 · vitalia-fase1-shell-layout-5050 · 01-spec.md

## § 1 — Context

- **Outcome:** `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md` — base UI shell-organism agéntica Vitalia
- **Phase 1 chain dependency:** F1-S0 stack-stability · F1-S1 design-tokens-theme · F1-S2 topbar-global · F1-S3 tenant-switcher → CHAIN COMPLETE 2026-05-23, esta story (F1-S4) la cierra como layout root.
- **Módulo:** shell-organism (componente compartido `vitalia/frontend/src/components/shared/shell-organism/`)
- **User journey insertion point:** primer route group dentro de `app/[tenantId]/(shell-organism)/`. Toda navegación post-login que use el nuevo paradigma entra por este layout. El `(dashboard)/` legacy queda intacto en paralelo (Phase 2 lo deprecate gradual).
- **SSoT arquitectura:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` §3.4 (`ShellOrganismLayout` template) + §5.1 (tokens CSS vars) + §6.1 (`shellStore` zustand).
- **Mockups visuales ratificados** (gate per `vitalia/.claude/rules/shell-mockup-per-component.md`):
  - `mockups/shell-layout-agentic.html` — split 50/50 con divisor resizable + min dinámico por valeriaState
  - `mockups/shell-layout-web.html` — rail 60px + 1fr fijo

### § 1.1 — Out-of-scope (anti-creep)

- **NO** se construye contenido interno del `ValeriaSidebar` (rail buttons funcionales, history fetch, chat skeleton). Eso es F1-S5 + F1-S6.
- **NO** se construye contenido interno del `AppPanel` (ribbon 6 tabs funcional, sub-tabs, content pages). Eso es F1-S7 + F1-S8 + F1-S10.
- **NO** se toca el route group legacy `app/[tenantId]/(dashboard)/` ni sus componentes (`AppShell.tsx`, `TopBar.tsx`, `Sidebar.tsx`). Coexisten sin interferencia.
- **NO** se activa el toggle UI agentic↔web (placeholder disabled en TopBar). Su activación es F1-S5/S7+.
- **NO** se introduce variant nuevo del `LogoMark` — se reusa contrato F1-S2 (`size='md' variant='full'` desktop, fallback `mark` < sm).

## § 2 — Gherkin scenarios

### SC-1 happy · render 50/50 default modo agentic

```gherkin
Given el usuario "Marcela Pérez" con clínica activa "Sonrisa Plena · Lima centro" autenticado vía Clerk
  And shellStore en estado inicial limpio (sin localStorage previo) o con valeriaState='full'
When navega a "/{tenantId}/(shell-organism)" en viewport 1280x800
Then el redirect a "/{tenantId}/lisa/marca" se ejecuta (default landing)
  And el TopBar de 48px se renderiza fijo en el top con LogoMark + toggle modo + ThemeToggle + TenantSwitcher
  And el <main id="main-content" tabindex="-1"> se renderiza con grid template "var(--valeria-w,1fr) 4px var(--app-w,1fr)"
  And ValeriaSidebarSlot ocupa ~50% (≥620px porque state='full' default)
  And AppPanelSlot ocupa el ~50% restante (≥480px)
  And el resize handle es visible entre ambos slots con aria-orientation="vertical"
  And shellMode persistido es 'agentic'
```
- `playwright_required: true`
- `graders:`
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/shell-layout-5050/render-agentic-default.spec.ts" }`
  - `{ type: visual_state, screen: "shell-agentic-1280", expect: "matches mockups/shell-layout-agentic.html viewport 1280x800 light" }`

### SC-2 negative · viewport < md colapsa a 1 columna sin romper

```gherkin
Given el usuario en /{tenantId}/(shell-organism) con shellMode='agentic'
When el viewport cae a 375x667 (mobile)
Then el grid colapsa a "grid-cols-1" (1 columna full-width)
  And el resize handle queda display:none (no draggable en mobile)
  And el ValeriaSidebarSlot queda visible solo cuando burger menu abre (drawer pattern)
  And el AppPanelSlot ocupa el 100% del viewport bajo el TopBar
  And NO se rompe el layout (no overflow horizontal, no contenido tapado)
```
- `playwright_required: true`
- `graders:`
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/shell-layout-5050/mobile-collapse.spec.ts" }`
  - `{ type: visual_state, screen: "shell-mobile-375", element: "main#main-content", expect: "grid-template-columns: 1fr (single column)" }`

### SC-3 edge · resize boundary clamp + persistencia + snap-up por state change

```gherkin
Given el usuario en shell agentic con valeriaState='full' (min Valeria 620px)
  And el viewport es 1440x900
When arrastra el resize handle hacia la izquierda hasta posición < 620px
Then el handle clamp en 620 (no permite achicar más)
  And el split footer indica el ratio actual con min Valeria 620px
  And localStorage[vitalia-shell-split-agentic] persiste el valor 620

Given el usuario en estado anterior (Valeria=620, state='full')
When cambia valeriaState a 'rail' (vía rail button — F1-S5 lo activará; en F1-S4 vía dev toggle)
Then el componente history-skel desaparece (display:none)
  And el min Valeria baja a 360px
  And el width actual (620) se mantiene (más espacio para chat, no auto-shrink)

Given el usuario con valeriaState='rail' y Valeria width = 400
When cambia valeriaState a 'full' (rail button — F1-S5 lo activará)
Then 400 < min 620 → snap-up automático a 620
  And el history-skel reaparece
  And localStorage[vitalia-valeria-state] persiste 'full'
```

> **DEFERRED 2026-05-23 (audit iter 3 ESCALATED Caso D):** la última assertion
> (`400 < min 620 → snap-up automático a 620` después de `setValeriaStateViaStore('rail')→reload→setValeriaStateViaStore('full')→reload→drag`) requiere refactor del lifecycle hydration race condition entre `dynamic({ssr:false})` mount + `useDefaultLayout` localStorage restore + ResizeObserver minSize calc. Fix iter 3 (commit 46fc8700 via `useGroupRef` Fix A) resolvió drag-clamp pero no este transition+drag-immediately edge case. Chris ratificó accept 33/34 Playwright pass rate + DEFER snap-up race a F1-S5/S6 lifecycle work (`vitalia-fase1-valeria-rail-history` / `vitalia-fase1-valeria-chat-skeleton`). Test `resize-and-state.spec.ts:114` marcado `test.skip(true, ...)` con razón documentada.
- `playwright_required: true`
- `graders:`
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/shell-layout-5050/resize-and-state.spec.ts" }`
  - `{ type: state_check, target: localStorage, query: "vitalia-shell-split-agentic", expect: ">=620 && <=viewport-min_app" }`

### SC-4 adversarial · a11y keyboard nav + skip link target

```gherkin
Given el usuario navega vía teclado (sin mouse)
When presiona Tab desde el TopBar
Then el foco recorre: LogoMark link → toggle modo (disabled, skip) → ThemeToggle → TenantSwitcher → main#main-content (skip-link target)
  And el resize handle es focusable (tabindex="0")
  And con handle focused, ArrowLeft/ArrowRight ajustan el split en pasos de 16px respetando mins

Given el usuario usa screen reader (NVDA / VoiceOver)
When llega al resize handle
Then el handle se anuncia como "separator, vertical, Redimensionar paneles"
  And los slots ValeriaSidebarSlot y AppPanelSlot tienen aria-label legible
  And el main element tiene id="main-content" + tabindex="-1" para que skip-link funcione

Given el usuario hostil intenta forzar viewport < 320px o desactivar JS
When la página carga
Then el layout degrada graceful (grid 1-col + assets PNG sirven sin JS)
  And no hay XSS surface (sin innerHTML dinámico, sin user input rendered)
  And tenant_id en URL no fuga a otros tenants (auth middleware protege antes del shell — out of F1-S4 scope, validar en BE)
```
- `playwright_required: true`
- `graders:`
  - `{ type: e2e, path: "vitalia/frontend/e2e/regression/shell-layout-5050/a11y-keyboard.spec.ts" }`
  - `{ type: axe, ruleset: "wcag2aa" }`

### Sub-categorías mandatory v4.1 (cobertura)

| Sub-categoría | Aplica | Cobertura |
|---|---|---|
| `race_condition` | NO (`not_applicable_reason: "layout sin create/update — sólo render + resize side-effect local browser"`) | — |
| `concurrent_users` | NO (`not_applicable_reason: "layout root sin queries de filtrado — tenant isolation aplica en BE upstream"`) | — |
| `network_failure` | NO (`not_applicable_reason: "layout puro sin fetch propio — F1-S5/S6 lo cubre cuando agreguen chat fetch"`) | — |
| `empty_state` | NO (`not_applicable_reason: "slots son placeholders por diseño — empty real es scope de F1-S10 empty-states story"`) | — |
| `large_dataset` | NO (`not_applicable_reason: "layout no renderiza listas"`) | — |
| `accessibility` | **SÍ** | SC-4 (keyboard nav + axe + skip-link target) |
| `i18n` | **SÍ** | SC-1 microcopy TopBar en Spanish neutro + assertion en SC-1 ("Sonrisa Plena · Lima centro") |

## § 3 — Wireframes inline

| Mockup HTML ratificado | URL local | Variant cubierta |
|---|---|---|
| `mockups/shell-layout-agentic.html` | `http://localhost:8888/shell-layout-agentic.html` | shellMode='agentic' split 50/50 + resize dinámico + min por valeriaState |
| `mockups/shell-layout-web.html` | `http://localhost:8888/shell-layout-web.html` | shellMode='web' grid `60px 1px 1fr` fijo (rail-only Valeria) |

ASCII summary (referencia rápida):

```
┌─ TopBarGlobal (48px) ───────────────────────────────────────────────┐
│ LogoMark           [toggle modo (placeholder)] [☾] [SP Sonrisa ▼]   │
├──────────────────┬─┬────────────────────────────────────────────────┤
│ ValeriaSidebar   │ │ AppPanelSlot                                   │
│   ┌──┬────┬───┐  │║│   ┌─────────────────────────────────────────┐  │
│   │R │His │   │  │║│   │ Ribbon 6 tabs                           │  │
│   │ail│tory│ Ch│  │║│   ├─────────────────────────────────────────┤  │
│   │60│280 │at│  │║│   │ SubTabsBar                               │  │
│   │px│px  │  │  │║│   ├─────────────────────────────────────────┤  │
│   │  │    │  │  │║│   │ ContentArea                              │  │
│   │  │    │  │  │║│   │                                          │  │
│   └──┴────┴──┘  │║│   └─────────────────────────────────────────┘  │
│  agentic full:  │║│                                                │
│   min 620px     │║│  min 480px                                     │
└──────────────────┴─┴────────────────────────────────────────────────┘
   ↑ ValeriaSidebarSlot         ↑ resize handle 4px (agentic only)
```

## § 4 — Estados visuales

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| **agentic default** (initial) | first visit, sin localStorage previo | TopBar · ValeriaSidebarSlot (rail+history+chat skeleton, valeriaState='full') · resize handle · AppPanelSlot (ribbon+subtabs+content skeleton) · footer devtools | drawer mobile |
| **agentic resized** | user dragged handle | mismo set, ratio custom | — |
| **agentic state='rail'** | rail button (F1-S5) o dev toggle cambia state | TopBar · ValeriaSidebarSlot sin history-skel · resize handle (min 360) · AppPanelSlot | history skeleton (display:none) |
| **web** | shellMode='web' (toggle F1-S5/S7+) | TopBar · ValeriaSidebar rail-only (60px) · static divider 1px · AppPanelSlot expandido | history · chat · resize handle |
| **mobile collapsed** | viewport < md (768px) | TopBar · AppPanelSlot 100% · burger hint en ValeriaSlot area | resize handle · history · chat |
| **mobile drawer-open** | burger menu tap (F1-S5+ lo activa) | overlay backdrop + ValeriaSidebar fixed inset | AppPanelSlot bajo backdrop |
| **dark mode** | ThemeToggle click | mismo set, paleta dark, `vitalia-logo-dark.png` swap CSS | — |

## § 5 — Componentes (reutilizar > inventar)

| Componente | Path | NEW / reuse | Justificación |
|---|---|---|---|
| `ShellOrganismLayout` | `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx` | **NEW** | Template del shell layout — el componente raíz que esta story construye. NO existe equivalente. |
| `ValeriaSidebarSlot` | `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx` | **NEW** (placeholder) | Slot vacío que F1-S5/F1-S6 reemplazará con `ValeriaSidebar` real. F1-S4 lo entrega como `aside` con border-right + aria-label + min-width responsive. |
| `AppPanelSlot` | `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | **NEW** (placeholder) | Idem — slot vacío que F1-S7/S8/S10 reemplazará. F1-S4 lo entrega como `section` con `{children}` slot + min-width responsive. |
| `useShellStore` | `vitalia/frontend/src/stores/shell-store.ts` | **NEW** | Zustand store con persist middleware. Schema cementado en Design Contract §6.1: `valeriaState ('collapsed'\|'rail'\|'full')` + `shellMode ('agentic'\|'web')` + setters + `cycleValeriaState`. |
| `ResizablePanels` (interno layout) | inline en `ShellOrganismLayout.tsx` o helper `useResizable` hook | **NEW** | Lógica de drag + min clamp + persist en localStorage. Considerar usar `react-resizable-panels` (Shadcn pattern) — decisión `/architect`. |
| `TopBarGlobal` | `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | **REUSE** F1-S2 done | Consume tal cual está deployado. No se modifica. |
| `LogoMark` | `vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx` | **REUSE** F1-S2 done | `size='md' variant='full'` default. Sin cambios. |
| `ThemeToggle` | `vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx` | **REUSE** F1-S1 done | Sin cambios. |
| `TenantSwitcher` | `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx` | **REUSE** F1-S3 done | Sin cambios. |
| Toggle modo (agentic↔web) UI | en `TopBarGlobal.tsx` o nuevo `ShellModeToggle.tsx` | **NEW — disabled placeholder F1-S4** | Solo renderizado, NO funcional. Activación en F1-S5/S7+. Chip neutral con label "Agéntico"/"Web". Disabled state evita interacción accidental. |

**Cross-brand mirror check (anti-duplication):** ningún componente shell-organism actual aparece en `nicolify/` o `comunify/` — patrón es brand-local Vitalia. Si en futuro lupulo/fitflow adoptan shell-organism similar → lift candidate a `core/luana-core-ui-shell/` (promotion proposal `/pm-luana`).

## § 6 — Data flow

- **API endpoints consumidos:** ninguno propio (`F1-S4` es layout puro; el redirect default `/{tenantId}/lisa/marca` confía en Next.js routing — no requiere fetch BE)
- **React Query keys:** ninguna en F1-S4 (consumers F1-S5/S6/S7 introducirán las suyas)
- **Mutations:** ninguna
- **Estado global:** `useShellStore()` (zustand con `persist` en `localStorage[vitalia-shell-state]`)
- **Estado local componente:** dragging state interno del resize handle (React useState)
- **Persistence keys (localStorage):**
  - `vitalia-shell-state` — JSON `{valeriaState, shellMode}` (zustand persist middleware)
  - `vitalia-shell-split-agentic` — string px del width Valeria en modo agentic
  - (heredados) `vitalia-theme` (light/dark) · `vitalia-active-tenant-id` (F1-S3)
- **Form library:** N/A (no forms en F1-S4)

## § 7 — Microcopy (Spanish neutro LatAm)

| Surface | Copy |
|---|---|
| Toggle modo (chip label, modo agentic) | "Agéntico" |
| Toggle modo (chip label, modo web) | "Web" |
| Toggle modo tooltip | "Modo (agéntico/web) — toggle se activa en F1-S5/S7" *(solo en mockup; en prod el tooltip explicará para qué sirve)* |
| Toggle modo aria-label | "Modo de shell: {agentic|web} activo" |
| Theme toggle aria-label | "Cambiar tema (claro/oscuro)" |
| TenantSwitcher aria-label | "Clínica activa: {tenant_name} · {tenant_location}" (heredado F1-S3) |
| `<main>` skip-link landing | `id="main-content"` + `tabindex="-1"` (sin texto visible — target del skip-link "Saltar al contenido principal" del TopBar) |
| Resize handle aria-label | "Redimensionar paneles" |
| ValeriaSidebarSlot aria-label | "Panel Valeria (placeholder — F1-S5/S6 lo construirá)" *(en mockup; en prod versión post-S5/S6 será "Panel de la asistente Valeria")* |
| AppPanelSlot aria-label | "Panel aplicación (placeholder — F1-S7/S8/S10 lo construirá)" *(idem)* |
| Mobile drawer hint | "Valeria — abrir desde menú" |

<!-- voseo-allowed: glosario reference -->
**Spanish neutro check:** copy tuteo verificado, sin `vos/sos/tenés/podés/dale/mirá`, sin léxico regional. Tildes + ñ + apertura `¿!` respetados.

## § 8 — Responsive breakpoints

| Breakpoint Tailwind | Viewport | Comportamiento |
|---|---|---|
| `< sm` (< 640px) | móvil pequeño | LogoMark variant='mark' (libélula 32x32) · TenantSwitcher sin nombre, sólo avatar · grid 1 col |
| `sm` (640-767px) | móvil grande / phablet | LogoMark variant='full' light/dark · grid 1 col (drawer aún < md) |
| `md` (768-1023px) | tablet vertical / desktop chico | grid 2 cols activado · split 50/50 default (con min Valeria=620 puede chocar — clamp aplica) |
| `lg` (1024-1279px) | desktop estándar | grid 2 cols cómodo · resize libre dentro mins |
| `xl` (≥ 1280px) | desktop wide | grid 2 cols óptimo · espacio sobrado para split user-controlled |

**Edge case `md=768px` con `valeriaState='full'`:** min Valeria 620 + min App 480 + handle 4 = 1104px requerido. A 768px no caben. Solución: en viewport entre `md` y `lg` donde `valeriaState='full'` no quepa, **forzar state a 'rail'** (auto-collapse history) hasta que viewport crezca de nuevo. Detalle de implementación: `/architect` define en 03-arch.md.

## § 9 — Accessibility

- **Skip link target:** `<main id="main-content" tabindex="-1">` — el TopBar (F1-S2 deployed) ya tiene "Saltar al contenido principal" que apunta acá vía `href="#main-content"`.
- **Resize handle:** `role="separator" aria-orientation="vertical" aria-label="Redimensionar paneles" tabindex="0"`. Soporta `ArrowLeft`/`ArrowRight` con step 16px. Foco visible (`focus:ring-2 focus:ring-ring`).
- **Slot regions:** `aside` con `aria-label` legible (ValeriaSidebarSlot) · `section` con `aria-label` (AppPanelSlot).
- **Keyboard nav order:** TopBar interactivos en orden visual L→R · resize handle (cuando exista en agentic) · main content. Tab order matches DOM order, sin `tabindex` positivos.
- **Contrast:** verificado en mockup tokens (Design Contract §5.1) — `--foreground`/`--background` ratio ≥ 4.5:1 light + dark. `--muted-foreground` ratio ≥ 3:1 (texto secundario).
- **Reduced motion:** drag dragging cursor sin transitions exuberantes. Si `prefers-reduced-motion: reduce` se respeta a futuro (no aplica directamente en F1-S4).
- **Screen reader test:** SC-4 cubre NVDA / VoiceOver del handle + slots.

## § 10 — Visual Goldens (per shell-mockup-per-component.md)

| Mockup HTML | Golden snapshot path | Componente React | Design Contract ref |
|---|---|---|---|
| `mockups/shell-layout-agentic.html` (light 1280x800) | `vitalia/frontend/e2e/__screenshots__/shell-layout-5050/agentic-1280x800-light.png` | `ShellOrganismLayout` modo agentic | §3.4 |
| `mockups/shell-layout-agentic.html` (dark 1280x800) | `vitalia/frontend/e2e/__screenshots__/shell-layout-5050/agentic-1280x800-dark.png` | idem dark | §3.4 + §5.1 dark tokens |
| `mockups/shell-layout-agentic.html` state='rail' (1280x800) | `vitalia/frontend/e2e/__screenshots__/shell-layout-5050/agentic-rail-1280x800.png` | idem con valeriaState='rail' | §6.1 |
| `mockups/shell-layout-web.html` (light 1280x800) | `vitalia/frontend/e2e/__screenshots__/shell-layout-5050/web-1280x800-light.png` | `ShellOrganismLayout` modo web | §3.4 |
| `mockups/shell-layout-web.html` (dark 1280x800) | `vitalia/frontend/e2e/__screenshots__/shell-layout-5050/web-1280x800-dark.png` | idem dark | §3.4 + §5.1 |
| `mockups/shell-layout-agentic.html` (mobile 375x667) | `vitalia/frontend/e2e/__screenshots__/shell-layout-5050/agentic-mobile-375x667.png` | grid 1 col + burger hint | §3.4 mobile drawer |

Tolerance `maxDiffPixelRatio: 0.001` (0.1%). Ratchet shrink-only post-ratificación.

## § 11 — Brand voice

N/A en surfaces user-facing F1-S4 (todo chrome UI standard — Spanish neutro estándar Vitalia, no per-tenant voice). El brand voice per-tenant aplica en sales_agent (F2+) y en mensajes user-facing del Valeria chat (F1-S6).

## § 12 — Telemetría (opcional)

```yaml
events:
  - { name: shell_organism_mounted, trigger: "ShellOrganismLayout first render", props: ["tenantId", "shellMode", "valeriaState", "viewport_width"] }
  - { name: shell_resized, trigger: "resize handle dragend", props: ["tenantId", "valeria_width_px", "ratio_pct"] }
  - { name: shell_mode_changed, trigger: "setShellMode call (F1-S5/S7+ activará)", props: ["tenantId", "from_mode", "to_mode"] }
  - { name: valeria_state_changed, trigger: "setValeriaState call (F1-S5 activará)", props: ["tenantId", "from_state", "to_state"] }
```

Opt-in: solo `shell_organism_mounted` es obligatorio en F1-S4. Los demás dependen de F1-S5+ donde la interactividad existirá. Pipeline events: heredar el del módulo `observability` brand (HIPAA-lite no aplica: no PHI).

## § 13 — Compliance & PHI scope

`hipaa_lite_scope: not_applicable` per `vitalia/.claude/rules/hipaa-lite.md` § Aplica → "NO aplica (solo tenant-isolation raíz basta): story toca únicamente layout/UI sin tocar patient_*/medical_*/treatment_*". `ShellOrganismLayout` es chrome UI sin PHI. El `tenantId` URL queda bajo dominio tenant-isolation raíz (`.claude/rules/tenant-isolation.md` enforced por middleware BE upstream).

## § 14 — Pre-handoff gate v4.1 (checklist)

- [x] 4 scenarios base (happy + negative + edge + adversarial)
- [x] Sub-categorías mandatory cubiertas o con `not_applicable_reason` explícito:
  - [x] race_condition (N/A documentado)
  - [x] concurrent_users (N/A documentado)
  - [x] network_failure (N/A documentado)
  - [x] empty_state (N/A documentado)
  - [x] large_dataset (N/A documentado)
  - [x] accessibility (SC-4)
  - [x] i18n (SC-1)
- [x] Todos scenarios funcionales con `playwright_required: true`
- [x] Cada `then:` verificable (assertions concretas)
- [x] `graders:` declarados (e2e + visual_state + axe + state_check)
- [x] Mockups HTML ratificados (`shell-layout-agentic.html` + `shell-layout-web.html`)
- [x] Estados visuales tabla completa (§4)
- [x] Microcopy Spanish neutro verificado (§7)
- [x] Componentes reuse > new (5 NEW + 4 REUSE F1-S1/S2/S3)
- [x] Responsive breakpoints declarados (§8)
- [x] Accessibility section completa (§9)
- [x] Visual goldens tabla (§10)
- [x] HIPAA-lite scope evaluado (N/A documentado §13)

**Gate v4.1: PASS.** State transition `refining → refined` aprobado.

## § 15 — Próximo paso

`/architect vitalia vitalia-fase1-shell-layout-5050` lee este `01-spec.md` + 2 mockups ratificados, decide surfaces (FE only — no BE / no agentic), spawnea `architect-orchestrator` → produce ready package:
- `03-arch.md` (Next.js App Router + zustand store + react-resizable-panels decision + test_construction_plan con POMs)
- `04-validators.yaml` (5 categorías incluyendo visual_goldens + architectural_validation FSD-Lite)
- `05-guidelines.md` (must_load_skills: `frontend-expert`, `playwright-expert`; required patterns Server Component preference, Client Component solo donde shellStore o drag)
- `06-tickets.yaml` (atómicos T-1 store · T-2 placeholders · T-3 layout + resize · T-4 redirect page · T-5 tests visual + functional)

State transition: refined → ready al cerrar `/architect`.
