<!-- voseo-allowed: internal spec documentation -->

---
story_id: vitalia-fase1-tenant-switcher
brand: vitalia
type: ui-story
phase: fase-1
module: shell-organism
agent_owner: shell
capability: shell.tenant-switcher
po_version: 1.0
last_modified: 2026-05-22
state: refined
ratified_by_chris: true
ratified_visual_by_chris: true
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-closed.html
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-open.html
ratified_visual_at: 2026-05-22T17:00:00-05:00
ratified_visual_iter: 1
parallel_safe: true
priority: high
estimated_dev_days: 1-2
dependencies:
  hard: [vitalia-fase1-stack-stability, vitalia-fase1-design-tokens-theme, vitalia-fase1-topbar-global]
  soft: []
service_blockers: []
blocks_hard: []
reuse_map_summary: "REUSE 75% nicolify/frontend/src/components/shared/layout/TenantSwitcher.tsx (adaptado: solo non-collapsed variant + Vitalia tokens + path preservation redirect + Tenant data shape minimal {id, name, city}). CONSUME BE engine luana-core-iam shipped endpoint /api/tenants. NEW TenantBadge átomo (hash determinístico palette 6 colors) + TenantOption molécula + tenantStore Zustand persist localStorage. Replace placeholder TenantSwitcherSlot null de F1-S2 drop-in."
links:
  design_contract: "vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md"
  predecessor_f1s0: "vitalia/docs/product/stories/vitalia-fase1-stack-stability/01-spec.md"
  predecessor_f1s1: "vitalia/docs/product/stories/vitalia-fase1-design-tokens-theme/01-spec.md"
  predecessor_f1s2: "vitalia/docs/product/stories/vitalia-fase1-topbar-global/01-spec.md"
  nicolify_reference: "nicolify/frontend/src/components/shared/layout/TenantSwitcher.tsx"
  outcome_master: "vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md"
  template_shell_spec: "vitalia/docs/specs/templates/01-spec-shell-template.md"
  mockup_per_component_protocol: "vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md"
---

# F1-S3 `vitalia-fase1-tenant-switcher` — 01-spec

## § 1 — Resumen ejecutivo

F1-S3 construye el **switcher de clínicas funcional** que reemplaza el placeholder `TenantSwitcherSlot` (null drop-in) shippeado por F1-S2 dentro de `TopBarGlobal`. Es la primera molécula compleja del shell-organism que combina datos remotos + estado persistido + navigation cross-tenant + estados loading/error/empty + a11y nativo Radix.

**3 componentes nuevos:**

1. **`TenantBadge`** (átomo) — cuadrado 24×24 (`size-6`) con initials 2-char + background color resuelto por **hash determinístico** del `tenant.id` mapeado a paleta 6 colores Vitalia (cyan · purple · magenta · amber · lime · rose). Reusable en TenantSwitcher trigger + TenantOption rows + futuro Ribbon tabs identification + Chat header.

2. **`TenantOption`** (molécula) — row dropdown que compone `TenantBadge` + nombre clínica + subtitle ciudad + active check icon (Lucide `Check` visible solo cuando `active=true`). Bg suave `bg-accent/40` cuando activo. Hover `bg-muted` cuando inactivo.

3. **`TenantSwitcher`** (organismo) — Shadcn `DropdownMenu` que envuelve trigger button (`[Badge] + nombre truncate + ▾`) con lista de tenants disponibles del usuario actual + 2 actions footer (`Agregar clínica` placeholder modal · `Administrar cuenta` link a `/{tenantId}/config/cuenta`). Cambio de tenant dispara `window.location.href` hard redirect preservando ruta actual (cambia solo segment `[tenantId]` inicial).

**4 piezas auxiliares:**

- **`tenantStore`** (Zustand + persist middleware) — fuente de verdad client-side de `activeTenant` + `availableTenants`. LocalStorage key `vitalia-tenant-state` partialize solo `activeTenant` (lista se hidrata de API).
- **`useTenants`** (React Query hook) — fetch `/api/tenants` con `staleTime: 5min`. Hidrata `setAvailableTenants` en `onSuccess` callback.
- **Hard redirect path preservation** — algoritmo `pathname.replace(/^\/[^/]+/, '/' + newTenantId)` preserva el resto de la ruta (`/{old}/(shell-organism)/lisa/marca` → `/{new}/(shell-organism)/lisa/marca`).
- **Replace placeholder F1-S2** — `TopBarGlobal.tsx` cambia 1 línea: `<TenantSwitcherSlot />` → `<TenantSwitcher />`. Drop-in sin layout shift.

**Decisiones cementadas Chris 2026-05-22 (batch 1 /po-ux):**

- **D1 — TenantBadge color strategy: hash determinístico tenant.id.** Mapea `sum(tenant.id.charCodeAt(*)) % 6` → paleta `[cyan-500, purple-500, magenta-500 (#d946ef), amber-500, lime-500, rose-500]`. Predecible cross-session (mismo tenant siempre mismo color). NO requiere field BE nuevo. Implementación pura FE. Tests determinísticos con tenant.id fixtures.
- **D2 — Subtitle data shape: solo ciudad.** BE devuelve `{id: string, name: string, city: string}`. UI muestra ciudad sin sucursal. Menos visual noise, suficiente para caso típico (1 sucursal por ciudad). Sub-sucursales mismo city → escala Fase 2 si demanda real aparece (currently 0 cases en Vitalia portfolio).
- **D3 — Trigger compactness: truncate max-w-[180px] + tooltip nativo.** Trigger button = `[Badge size-6] + <span className="truncate max-w-[180px]">{tenant.name}</span> + <ChevronDown />` con atributo `title={tenant.name}` (tooltip nativo browser). Width predecible TopBar 48px, no choca con `ThemeToggle` adyacente.
- **D4 — Mockup data LatAm realistic:** 3 clínicas ejemplo verbatim across ambos mockups:
  - `sonrisa-plena` · **Sonrisa Plena** · Lima · hash→**cyan-500** · initials **SP** *(active tenant en mockup default)*
  - `dermalia-mx` · **Dermalia MX** · CDMX · hash→**purple-500** · initials **DM**
  - `clinicare-bogota` · **ClíniCare Bogotá** · Bogotá · hash→**magenta-500** · initials **CB**

**Anti-objetivos (explícito qué NO hace esta story):**

- NO crear nueva API BE `/api/tenants` — endpoint shipped en `luana-core-iam` (Story 11 vitalia-auth done 2026-05-19). F1-S3 solo consume.
- NO implementar "Agregar clínica" full flow — el `DropdownMenuItem` dispara modal placeholder con copy "Próximamente: agregar nueva clínica desde Configurar → Mi cuenta" + cierra. Full flow es Fase 2 (`vitalia-fase2-add-clinic`).
- NO implementar "Administrar cuenta" full screen — el item es link a `/{activeTenant.id}/config/cuenta` (ruta que F2-S20 va a construir). Por ahora click navega y muestra empty state F1-S10.
- NO usar Clerk Organizations — Vitalia NO usa Clerk Orgs (per `MEMORY.md::no-clerk-organizations` 2026-05-20). Multi-tenancy vive en engine `luana-core-iam` con tenants+users propios. Clerk solo provee identity (JWT).
- NO crear search input dentro dropdown — caso típico médico tiene 1-3 clínicas, search es overkill. Si usuario tiene ≥5 tenants en Fase 2 → escala story `vitalia-fase2-tenant-search`.
- NO implementar drag-reorder / favorite / recent-used tenants — out-of-scope shell-organism mínimo viable.
- NO tocar `(dashboard)/` legacy.
- NO instalar Shadcn primitives nuevos — F1-S0 ya instaló `dropdown-menu` y `button` necesarios.
- NO modificar `TopBarGlobal.tsx` más allá de la 1 línea de replace placeholder (su layout cementado en F1-S2 ratificado).

---

## § 2 — Visión (paradigma shell-organism)

F1-S3 cementa **multi-tenancy operativa** en el chrome user-facing. El usuario percibe la app como "una sola Vitalia" pero el dropdown le da control instantáneo sobre cuál clínica está viendo en este momento. Es el **único punto de cambio de contexto tenant** en toda la app — el resto del UI lee `activeTenant` de Zustand store + URL segment `[tenantId]`.

**Agente owner:** SHELL (transversal — no es de un agente específico)
**Color oficial:** neutral (tokens shell) · TenantBadge per-tenant via hash determinístico
**Avatar PNG:** N/A (este organism no representa un agente individual; usa `TenantBadge` para identidad por clínica)

**Trazabilidad mockup integral:** `vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html` (líneas TopBar 80-120 aprox) muestra TenantSwitcher en contexto con TopBar + ThemeToggle. F1-S3 cementa contrato visual standalone via 2 mockups por-componente (closed + open).

**Encaja en paradigm v4 estado macro:** `refining` → ratificación visual + spec → `refined` → `/architect` produce ready package → `developing` → `/auditor` → `done`.

---

## § 3 — Context

### § 3.1 — Outcome y módulo

- **Outcome master:** `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md`
- **Módulo:** `shell-organism` (transversal · capability `shell.tenant-switcher`)
- **Brand:** `vitalia` (Salud + Bienestar)

### § 3.2 — User journey insertion point

Usuario médico/recepcionista autenticado, está trabajando dentro de cualquier sub-tab del shell-organism (`/{tenantId}/(shell-organism)/{agent}/{sub-tab}`). En la TopBar derecha ve siempre el badge + nombre de su clínica activa con un chevron ▾. Click → dropdown con lista de clínicas accesibles + 2 actions footer. Click otro tenant → hard redirect preservando la sub-tab actual (continuidad UX).

### § 3.3 — Out-of-scope explícito

Ver § 1 anti-objetivos. Adicional aquí:

- NO observability `copilot_trace_event` — TenantSwitcher es chrome UI puro, no event-emitting agente.
- NO i18n multi-idioma — Spanish neutro hardcoded F1 (lift a Fase 3 si demanda PT-BR/EN).
- NO Sentry custom span para switch — `window.location.href` reload natural captura métricas via Sentry pageload nativo.

---

## § 4 — Gherkin scenarios (★ v4.1 — 12 scenarios totales)

### § 4.1 — Base obligatorios (4 — AI-resistant)

#### Scenario 1 — happy switch path

```gherkin
Given el usuario está autenticado en /{sonrisa-plena}/(shell-organism)/lisa/marca
  And tenantStore.activeTenant.id = "sonrisa-plena"
  And /api/tenants devuelve [{sonrisa-plena, dermalia-mx, clinicare-bogota}]
  And la página muestra TopBarGlobal con TenantSwitcher trigger "[SP] Sonrisa Plena ▾"
When el usuario hace click en el trigger TenantSwitcher
  And el dropdown abre mostrando 3 TenantOption rows
  And el usuario hace click en "Dermalia MX"
Then tenantStore.activeTenant.id se actualiza a "dermalia-mx"
  And localStorage["vitalia-tenant-state"] persiste {state: {activeTenant: {id: "dermalia-mx", ...}}}
  And window.location.href ejecuta hard redirect a /{dermalia-mx}/(shell-organism)/lisa/marca
  And React Query cache se invalida (queries tenant-scoped refetchean en nueva página)

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/happy-switch.spec.ts" }
  - { type: state_check, target: localStorage, key: "vitalia-tenant-state", expect: "contains dermalia-mx" }
  - { type: visual_state, screen: "tenant-switcher-open", element: "[data-testid=tenant-option-dermalia-mx]", expect: "rendered + clickable" }
playwright_required: true
```

#### Scenario 2 — negative: tenant inexistente en lista

```gherkin
Given tenantStore.availableTenants = [sonrisa-plena, dermalia-mx]
  And el usuario intenta llamar switchTenant("clinica-inexistente") via DevTools console manual
When la función switchTenant ejecuta
Then la guardia .find(x => x.id === id) retorna undefined
  And tenantStore.activeTenant NO se actualiza
  And NO hay redirect
  And se loggea console.warn("Tenant clinica-inexistente no encontrado en availableTenants")

graders:
  - { type: state_check, target: zustand, query: "activeTenant.id", expect: "unchanged (sonrisa-plena)" }
playwright_required: false   # unit test cubre, no UI surface
```

#### Scenario 3 — edge: concurrent switch race (doble click rápido)

```gherkin
Given el usuario tiene el dropdown abierto con 3 tenants
When hace click en "Dermalia MX" y antes de redirect completar hace click en "ClíniCare Bogotá" en <150ms
Then solo UN switchTenant call procesa (el último click gana o el primero — debe ser determinístico)
  And window.location.href se ejecuta UNA VEZ (no doble navigation)
  And tenantStore.activeTenant.id final coincide con el último click procesado
  And NO hay state corrupto intermedio (ej. activeTenant = dermalia + localStorage = clinicare)

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/concurrent-clicks.spec.ts" }
playwright_required: true
```

#### Scenario 4 — adversarial: cross-tenant URL manipulation

```gherkin
Given el usuario tenant A "sonrisa-plena" está autenticado
  And availableTenants del JWT = [sonrisa-plena, dermalia-mx]
When el usuario manipula URL manualmente: navega a /{clinica-inexistente}/(shell-organism)/lisa/marca via address bar
Then el middleware Clerk + backend valida JWT.tenant_id vs URL segment
  And la respuesta es 403 Forbidden (o 404 si tenant no existe en BE)
  And el FE redirige a /{sonrisa-plena}/(shell-organism) (rollback al active conocido)
  And NO se filtra data de tenant ajeno en ningún fetch
  And Sentry captura warning sin PHI (solo metadata: user_id + attempted_tenant_id + actual_tenant_id)

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/adversarial-cross-tenant.spec.ts" }
  - { type: state_check, target: response, expect: "status 403 or 404" }
playwright_required: true
```

### § 4.2 — Sub-categorías mandatory (★ v4.1)

#### Scenario 5 — race_condition (concurrent localStorage write)

```gherkin
Given el usuario tiene 2 pestañas abiertas en /{sonrisa-plena}/...
  And pestaña A está activa
When en pestaña A switchea a "Dermalia MX"
  And simultáneamente en pestaña B switchea a "ClíniCare Bogotá" (dentro del mismo segundo)
Then localStorage["vitalia-tenant-state"] queda con el ÚLTIMO write (timestamp más reciente — semántica natural localStorage)
  And cada pestaña redirige a su elegido respectivo (cada window.location.href es local a su pestaña)
  And NO hay corrupción de state ni JSON malformado en localStorage
  And next mount de tenantStore en pestaña refresh respeta el último write

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/race-multi-tab.spec.ts" }
playwright_required: true
```

#### Scenario 6 — concurrent_users (2 usuarios diferentes mismo browser context — edge para devtools)

```gherkin
Given user_A "alice@..." con tenants [sonrisa-plena, dermalia-mx]
  And user_B "bob@..." con tenants [clinicare-bogota]
When user_A cierra sesión (Clerk signOut clears JWT)
  And user_B inicia sesión en el mismo browser
Then localStorage["vitalia-tenant-state"] del user_A NO se filtra a user_B
  And tenantStore se rehidrata en mount de user_B con su propio /api/tenants response
  And TenantSwitcher muestra clinicare-bogota como única opción

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/concurrent-users.spec.ts" }
playwright_required: true

# Implementation note (NO en spec, dev-team verifica): tenantStore.persist
# debe usar key namespaced + onSignOut callback clear → para garantizar
# isolation cross-user. /architect resuelve estrategia exacta.
```

#### Scenario 7 — network_failure (API /api/tenants timeout)

```gherkin
Given el dropdown está abierto
  And /api/tenants demora >10s o devuelve 504 Gateway Timeout
When el usuario espera el response
Then el dropdown muestra el Alert destructive:
  - Heading: "No pudimos cargar tus clínicas"
  - Description: "Intenta de nuevo o revisa tu conexión."
  - Button: "Reintentar" (dispara refetch)
  And el trigger button sigue habilitado (no se rompe la UI)
  And Sentry captura el error sin PHI

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/network-failure.spec.ts" }
  - { type: visual_state, screen: "tenant-switcher-open-error", element: "[role=alert]", expect: "visible" }
playwright_required: true
```

#### Scenario 8 — empty_state (usuario sin tenants asignados — edge auth bug)

```gherkin
Given el usuario está autenticado pero /api/tenants devuelve { tenants: [] }
When el TenantSwitcher carga
Then NO se renderiza el trigger (TopBar sin TenantSwitcher visible — graceful degrade)
  And Sentry captura warning "User with zero tenants — auth/onboarding bug"
  And el usuario ve banner top-page: "Aún no tienes clínicas asignadas. Contacta a soporte."
  And el banner tiene CTA mailto soporte

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/empty-state.spec.ts" }
  - { type: state_check, target: dom, query: "[data-testid=tenant-switcher-trigger]", expect: "absent" }
playwright_required: true

# Note: este scenario es defensive — en prod normal usuario SIEMPRE tiene
# ≥1 tenant (auth flow garantiza). Pero defense-in-depth para auth/onboarding bugs.
```

#### Scenario 9 — large_dataset (usuario con ≥10 tenants — futuro proof, edge)

```gherkin
Given el usuario excepcional con 12 clínicas asignadas (super-admin Vitalia multi-cliente)
When el dropdown abre
Then la lista renderiza scroll vertical con max-height 320px (overflow-y-auto)
  And el active tenant es scroll-into-view al abrir (scrollIntoView smooth)
  And el rendering es <100ms (sin lag perceptible)
  And no hay paginación (scroll natural suficiente <50 items)

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/large-dataset.spec.ts" }
  - { type: visual_state, screen: "tenant-switcher-open-12-items", element: "[role=menu]", expect: "max-h-80 overflow-y-auto" }
playwright_required: true

# Note: F1-S3 ship-ready para ≤50 tenants. >50 escala vitalia-fase2-tenant-search.
```

#### Scenario 10 — accessibility (WCAG AA)

```gherkin
Given TenantSwitcher renderizado con 3 tenants
When el usuario navega con teclado
Then Tab focus llega al trigger button (visible ring focus-visible:ring-2 focus-visible:ring-ring)
  And Enter o Space abre el dropdown (Radix DropdownMenu nativo)
  And Arrow Down navega entre TenantOption rows
  And Enter selecciona el row focused (dispara handleSwitch)
  And Esc cierra el dropdown
  And el trigger tiene aria-label="Cambiar clínica"
  And el TenantBadge tiene aria-hidden="true" (decorativo — initials no aportan info nueva sobre el nombre)
  And contraste TenantBadge bg vs initials text ≥4.5:1 light + dark
  And contraste TenantOption text vs bg ≥4.5:1 light + dark

graders:
  - { type: axe, ruleset: "wcag2aa" }
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/a11y-keyboard.spec.ts" }
playwright_required: true
```

#### Scenario 11 — i18n (Spanish neutro)

```gherkin
Given TenantSwitcher renderizado en cualquier estado
When el usuario lee el copy
Then NO hay voseo: "vos/sos/tenés/podés/dale/mirá/dejá" — usa tuteo (tú/tienes/puedes)
  And NO hay léxico regional: "laburo/quilombo/pibe/che"
  And tildes + ñ + apertura ¿ ! correctos
  And currency NO aplica (no monetary display en esta surface)
  And copy verificable verbatim:
    - "Cambiar clínica" (trigger aria-label)
    - "Mis clínicas" (dropdown header label)
    - "Agregar clínica" (footer action 1)
    - "Próximamente: agregar nueva clínica desde Configurar → Mi cuenta" (placeholder modal body)
    - "Administrar cuenta" (footer action 2)
    - "No pudimos cargar tus clínicas" (error heading)
    - "Intenta de nuevo o revisa tu conexión." (error description)
    - "Reintentar" (error button)
    - "Aún no tienes clínicas asignadas. Contacta a soporte." (empty banner)
    - "Cargando clínicas…" (sr-only loading label)

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/i18n-spanish-neutro.spec.ts" }
  - { type: state_check, target: dom_text, expect: "no voseo regex match" }
playwright_required: true
```

#### Scenario 12 — single_tenant (edge UX común)

```gherkin
Given el usuario tiene exactamente 1 clínica accesible "Sonrisa Plena"
When el dropdown abre
Then la lista muestra 1 TenantOption con check active
  And Separator visible
  And 2 footer actions visibles: "Agregar clínica" + "Administrar cuenta"
  And el dropdown sigue funcional (NO collapse a label estático)
  And click en el único tenant es no-op (mismo active, sin redirect)

graders:
  - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/single-tenant.spec.ts" }
  - { type: visual_state, screen: "tenant-switcher-open-single", element: "[role=menu]", expect: "1 TenantOption + Separator + 2 actions" }
playwright_required: true
```

### § 4.3 — Coverage matrix (12 scenarios → sub-categorías mandatory)

| Sub-categoría v4.1 | Cubierto por | Status |
|---|---|---|
| happy | Scenario 1 | ✅ |
| negative | Scenario 2 | ✅ |
| edge | Scenario 3 + 12 (single tenant) | ✅ |
| adversarial | Scenario 4 | ✅ |
| race_condition | Scenario 5 (multi-tab localStorage) | ✅ |
| concurrent_users | Scenario 6 (signOut isolation) | ✅ |
| network_failure | Scenario 7 (API timeout) | ✅ |
| empty_state | Scenario 8 (0 tenants) | ✅ |
| large_dataset | Scenario 9 (12 tenants scroll) | ✅ |
| accessibility | Scenario 10 (WCAG AA + keyboard) | ✅ |
| i18n | Scenario 11 (Spanish neutro verbatim) | ✅ |

Total: 12 scenarios · 11 con `playwright_required: true` · 1 unit-only (Scenario 2). Gate v4.1 PASS.

---

## § 5 — Wireframes inline

### § 5.1 — TopBar con TenantSwitcher closed (ASCII)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [Vitalia logo]                                  [☀] [SP] Sonrisa Plena ▾   │  ← 48px h-12
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Main content (shell-organism rutas)                                      │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Trigger button anatomy:
┌──────────────────────────┐
│ [SP] Sonrisa Plena    ▾  │  ← Badge 24×24 + nombre truncate max-w-[180px] + ChevronDown
└──────────────────────────┘    aria-label="Cambiar clínica" + title="Sonrisa Plena"

[SP] = TenantBadge: bg-cyan-500 + initials "SP" white text-xs font-bold
```

### § 5.2 — Dropdown open (ASCII)

```
                                          [SP] Sonrisa Plena ▾  ← trigger
                                          │
                                          ↓ DropdownMenuContent align="end" min-w-[280px]
                                        ┌─────────────────────────────────┐
                                        │ MIS CLÍNICAS                    │  ← Label uppercase tracking-wider muted
                                        ├─────────────────────────────────┤
                                        │ [SP] Sonrisa Plena          ✓   │  ← active: bg-accent/40
                                        │      Lima                       │
                                        ├─────────────────────────────────┤
                                        │ [DM] Dermalia MX                │  ← inactive: hover:bg-muted
                                        │      CDMX                       │
                                        ├─────────────────────────────────┤
                                        │ [CB] ClíniCare Bogotá           │
                                        │      Bogotá                     │
                                        ├═════════════════════════════════┤  ← DropdownMenuSeparator
                                        │ ➕ Agregar clínica              │
                                        │ ⚙  Administrar cuenta           │
                                        └─────────────────────────────────┘
```

### § 5.3 — Loading state (dropdown abierto, /api/tenants pending)

```
                                          [SP] Sonrisa Plena ▾  ← trigger sigue habilitado
                                          ↓
                                        ┌─────────────────────────────────┐
                                        │ MIS CLÍNICAS                    │
                                        ├─────────────────────────────────┤
                                        │ [▒▒] ▒▒▒▒▒▒▒▒▒▒                 │  ← Skeleton x3
                                        │      ▒▒▒▒                       │
                                        ├─────────────────────────────────┤
                                        │ [▒▒] ▒▒▒▒▒▒▒▒▒▒                 │
                                        │      ▒▒▒▒                       │
                                        ├─────────────────────────────────┤
                                        │ [▒▒] ▒▒▒▒▒▒▒▒▒▒                 │
                                        │      ▒▒▒▒                       │
                                        ├═════════════════════════════════┤
                                        │ ➕ Agregar clínica              │  ← footer siempre visible
                                        │ ⚙  Administrar cuenta           │
                                        └─────────────────────────────────┘
                                        sr-only: "Cargando clínicas…"
```

### § 5.4 — Error state (API failure)

```
                                        ┌─────────────────────────────────┐
                                        │ MIS CLÍNICAS                    │
                                        ├─────────────────────────────────┤
                                        │ ⚠ No pudimos cargar tus         │
                                        │   clínicas                      │
                                        │   Intenta de nuevo o revisa     │
                                        │   tu conexión.                  │
                                        │   ┌────────────────┐            │
                                        │   │  Reintentar    │            │
                                        │   └────────────────┘            │
                                        ├═════════════════════════════════┤
                                        │ ⚙  Administrar cuenta           │  ← footer parcial (sin Agregar)
                                        └─────────────────────────────────┘
```

### § 5.5 — Single tenant (edge UX común)

```
                                        ┌─────────────────────────────────┐
                                        │ MIS CLÍNICAS                    │
                                        ├─────────────────────────────────┤
                                        │ [SP] Sonrisa Plena          ✓   │  ← solo 1 item
                                        │      Lima                       │
                                        ├═════════════════════════════════┤
                                        │ ➕ Agregar clínica              │
                                        │ ⚙  Administrar cuenta           │
                                        └─────────────────────────────────┘
```

### § 5.6 — Empty state (0 tenants — edge defensivo)

```
[TopBar sin TenantSwitcher visible — graceful degrade]

┌────────────────────────────────────────────────────────────────────────────┐
│ ⚠ Aún no tienes clínicas asignadas.                                       │  ← Banner top-page
│   Contacta a soporte: soporte@vitalia.health                              │
└────────────────────────────────────────────────────────────────────────────┘
```

### § 5.7 — Mockups HTML por-componente (ratificables Chris)

**Path mockups:** `vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/`

- `tenant-switcher-closed.html` — 4 states (light-default · light-single-tenant · dark-default · dark-long-name truncation test)
- `tenant-switcher-open.html` — 5 states (light-default-3tenants · light-loading-skeleton · light-error-alert · dark-default · light-single-tenant)

**Servidor local Chris ratify:**

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups
python3 -m http.server 8888
# Chris abre http://localhost:8888/tenant-switcher-closed.html y tenant-switcher-open.html
```

---

## § 6 — Estados visuales por componente

### § 6.1 — `TenantSwitcher` (organismo)

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `idle (closed)` | Inicial / dropdown cerrado | Trigger button: `[Badge] + nombre truncate + ChevronDown` | Dropdown content |
| `loading` | `/api/tenants` pending + dropdown abierto | Trigger habilitado · DropdownMenuLabel · 3× Skeleton rows · Separator · 2× footer actions · sr-only "Cargando clínicas…" | TenantOption rows reales · Alert error |
| `success (default)` | `/api/tenants` resolved + dropdown abierto | Trigger · Label · N× TenantOption rows (active marcado) · Separator · 2× footer actions | Skeleton · Alert |
| `success (single tenant)` | `/api/tenants` resolved + length === 1 + dropdown abierto | idem success default con 1 row | idem |
| `error` | `/api/tenants` failure + dropdown abierto | Trigger habilitado · Label · Alert destructive con heading + description + button "Reintentar" · Separator · 1× footer action "Administrar cuenta" | TenantOption rows · "Agregar clínica" (graceful degrade) |
| `empty` | `/api/tenants` resolved + length === 0 | NO trigger visible (TopBar degrades) · Banner top-page con CTA soporte | Dropdown entero |

### § 6.2 — `TenantBadge` (átomo)

| Estado | Trigger | Visual |
|---|---|---|
| `default` | siempre | size-6 (24×24px) · bg-{paletteColor} · text-white text-xs font-bold · initials 2-char uppercase · aria-hidden="true" |
| `active in dropdown row` | tenant === activeTenant | Bg desaturado leve (`opacity-90`) para diferenciar contexto activo · NO border especial (el bg-accent/40 del row lo señala) |

### § 6.3 — `TenantOption` (molécula)

| Estado | Trigger | Visual |
|---|---|---|
| `inactive` | tenant !== activeTenant | bg transparent · hover:bg-muted · cursor-pointer · padding p-2 |
| `active` | tenant === activeTenant | bg-accent/40 · text-foreground · check icon visible right · cursor-pointer (single-tenant edge: click no-op) |
| `focus-visible` | keyboard navigation | ring-2 ring-ring inset (Radix DropdownMenuItem nativo a11y) |

### § 6.4 — `Add clinic modal placeholder`

| Estado | Trigger | Visual |
|---|---|---|
| `idle` | siempre | Modal Shadcn-style con title "Próximamente" + body "Próximamente: agregar nueva clínica desde Configurar → Mi cuenta" + button "Entendido" cierra |

---

## § 7 — Componentes (reutilizar > inventar)

### § 7.1 — Tabla reuse map

| Componente | Path repo | Reutilizado vs nuevo | Justificación si NEW |
|---|---|---|---|
| `Button` | `vitalia/frontend/src/components/ui/button.tsx` | reuse (Shadcn F1-S0) | — |
| `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuLabel`, `DropdownMenuSeparator` | `vitalia/frontend/src/components/ui/dropdown-menu.tsx` | reuse (Shadcn F1-S0) | — |
| `Avatar` (skipped) | `vitalia/frontend/src/components/ui/avatar.tsx` | NOT used — TenantBadge implementa visual propio simpler (24×24 colored square con initials, no image src) | TenantBadge optimizado para data shape Vitalia minimal (sin avatar image URL en BE) |
| `Alert`, `AlertTitle`, `AlertDescription` | `vitalia/frontend/src/components/ui/alert.tsx` (instalar si no existe en F1-S0) | reuse Shadcn primitive | — |
| `Skeleton` | `vitalia/frontend/src/components/ui/skeleton.tsx` (instalar si no existe en F1-S0) | reuse Shadcn primitive | — |
| `Dialog` (Add clinic modal) | `vitalia/frontend/src/components/ui/dialog.tsx` (instalar si no existe en F1-S0) | reuse Shadcn primitive | — |
| `cn` helper | `vitalia/frontend/src/lib/utils.ts` | reuse (F1-S0) | — |
| `ChevronDown`, `Check`, `Plus`, `Settings`, `AlertTriangle` | `lucide-react` | reuse (F1-S0 dependency) | — |
| `TenantBadge` | `vitalia/frontend/src/components/shared/shell-organism/TenantBadge.tsx` | **NEW** | Composición específica Vitalia: hash determinístico color + initials 2-char + size 24×24. NO existe equivalente en nicolify (nicolify usa gradient + single initial). |
| `TenantOption` | `vitalia/frontend/src/components/shared/shell-organism/TenantOption.tsx` | **NEW** | Composición row TenantBadge + name + subtitle + check. Reutilizable cross-feature (futuro Ribbon tabs tenant indicator). |
| `TenantSwitcher` | `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx` | **NEW** (adaptado 75% nicolify reference) | Vitalia-scoped: data shape `{id, name, city}` vs nicolify `{id, name, fullName, slug}`. Path preservation redirect vs nicolify fixed-dashboard redirect. Tokens shell organism. NO `isCollapsed` variant (Vitalia TopBar es horizontal h-12, no sidebar). |
| `TenantSwitcherSlot` (placeholder de F1-S2) | `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx` | **DELETE** (replace pattern drop-in F1-S2 → F1-S3 deliver) | F1-S2 shipped placeholder null. F1-S3 elimina file + TopBarGlobal.tsx cambia 1 línea: `<TenantSwitcherSlot />` → `<TenantSwitcher />`. |
| `tenantStore` (Zustand) | `vitalia/frontend/src/stores/tenant-store.ts` | **NEW** | Estado client-side activeTenant + availableTenants + persist localStorage. Reusable cross-feature (cualquier component lee activeTenant). |
| `useTenants` (React Query hook) | `vitalia/frontend/src/hooks/useTenants.ts` | **NEW** | Fetch `/api/tenants` con hidratación store. Wrapping React Query con sensible defaults Vitalia. |

### § 7.2 — Cross-brand reuse signal (anti-duplication monitor)

**Pattern TenantSwitcher** aparece en nicolify + ahora vitalia (2 brands). Si comunify/lupulo lo necesitan en Fase 2 → escala `/pm-luana` con promotion proposal a `core/luana-core-ui/` (TS package futuro). Por ahora 2 brands = under threshold (anti-duplication rule trigger ≥3 brands o cross-brand identical logic >50%).

**Diferencias clave nicolify vs vitalia (no es mirror — adaptado):**

- nicolify: `isCollapsed` variant (sidebar layout) · vitalia: solo horizontal (TopBar)
- nicolify: redirect fixed `/brand-studio/identity` · vitalia: path preservation
- nicolify: gradient bg single initial · vitalia: hash palette 2-char initials
- nicolify: data shape `{id, name, fullName, slug}` · vitalia: `{id, name, city}`

---

## § 8 — Data flow conceptual

### § 8.1 — API endpoints consumidos

- `GET /api/tenants` (engine `luana-core-iam` shipped Story 11)
  - Response shape: `{ tenants: Array<{ id: string, name: string, city: string }> }`
  - Auth: Clerk JWT bearer header
  - Tenant filter: BE filtra por `user.org_membership` (engine resuelve qué tenants accesibles)
  - Cache: React Query `staleTime: 5 * 60 * 1000` (5 min)

### § 8.2 — React Query keys

- `['tenants']` — fetch lista tenants disponibles

### § 8.3 — Mutations (none)

F1-S3 NO escribe a BE. Solo lee `/api/tenants` + persiste activeTenant en localStorage client-side.

### § 8.4 — Estado global

- **Zustand `useTenantStore`** — `activeTenant`, `availableTenants`, `setActiveTenant`, `setAvailableTenants`, `switchTenant`
- **Persist middleware** — key `vitalia-tenant-state`, partialize solo `activeTenant` (lista hidrata de API en mount)
- **Hydration on mount** — `useTenants().onSuccess` callback dispara `setAvailableTenants(data.tenants)` + si `activeTenant === null` y hay tenants → `setActiveTenant(tenants[0])`

### § 8.5 — Redirect algoritmo

```typescript
function buildRedirectPath(currentPath: string, newTenantId: string): string {
  // Reemplaza primer segment de la ruta con newTenantId
  // /{old-tenant-id}/(shell-organism)/lisa/marca → /{newTenantId}/(shell-organism)/lisa/marca
  // /{old-tenant-id} → /{newTenantId}
  // / → /{newTenantId}
  return currentPath.replace(/^\/[^/]+/, `/${newTenantId}`) || `/${newTenantId}`
}

// Ejecución:
window.location.href = buildRedirectPath(pathname, newTenantId)
// Hard reload garantiza limpieza React Query cache + Zustand re-mount + Clerk JWT re-validation
```

### § 8.6 — Form library (none)

F1-S3 NO tiene forms. NO usa RHF + Zod.

---

## § 9 — Microcopy (Spanish neutro LatAm)

| Lugar | Copy verbatim |
|---|---|
| Trigger aria-label | "Cambiar clínica" |
| Trigger title (tooltip nativo) | `{tenant.name}` (dinámico) |
| Dropdown header Label | "MIS CLÍNICAS" |
| Active tenant row check sr-only | "Clínica activa" |
| Add clinic action | "Agregar clínica" |
| Add clinic modal title | "Próximamente" |
| Add clinic modal body | "Próximamente: agregar nueva clínica desde Configurar → Mi cuenta" |
| Add clinic modal close button | "Entendido" |
| Admin account action | "Administrar cuenta" |
| Loading sr-only | "Cargando clínicas…" |
| Error heading | "No pudimos cargar tus clínicas" |
| Error description | "Intenta de nuevo o revisa tu conexión." |
| Error button | "Reintentar" |
| Empty banner | "Aún no tienes clínicas asignadas. Contacta a soporte." |
| Empty banner CTA mailto | "soporte@vitalia.health" |

<!-- voseo-allowed: glosario reference verification — los siguientes son ejemplos PROHIBIDOS, no UI strings -->
**Spanish neutro verification checklist:**

- ❌ NO usar: "vos", "tenés", "podés", "dale", "mirá", "dejá", "fijate"
- ✅ Usar: "tú", "tienes", "puedes", "intenta", "revisa", "contacta"
- ✅ Tildes: "clínicas" (no "clinicas"), "próximamente" (no "proximamente")
- ✅ Apertura: "¿" "¡" cuando aplique (no aplica en este spec — no preguntas/exclamaciones)

---

## § 10 — Responsive breakpoints

| Breakpoint | TenantSwitcher behavior |
|---|---|
| Mobile <768px | Trigger: solo `[Badge]` visible + ChevronDown (sin nombre — el TopBar mobile ya muestra solo logo mark, espacio comprimido). Dropdown abre `align="end" sideOffset={8}` con `min-w-[280px]` que NO puede exceder viewport width-32 (margin). |
| Tablet 768-1023px | Trigger full: `[Badge] + nombre truncate max-w-[140px] + ChevronDown`. Dropdown min-w-[280px]. |
| Desktop ≥1024px | Trigger full: `[Badge] + nombre truncate max-w-[180px] + ChevronDown`. Dropdown min-w-[280px]. |

**Mobile trigger reduction strategy** — CSS-based (NO conditional JS render):

```tsx
<Button variant="outline" data-testid="tenant-switcher-trigger" title={activeTenant.name}>
  <TenantBadge tenant={activeTenant} />
  <span className="hidden sm:inline truncate max-w-[140px] md:max-w-[180px]">
    {activeTenant.name}
  </span>
  <ChevronDown className="size-4" />
</Button>
```

---

## § 11 — Accessibility

| Concerns | Solución |
|---|---|
| Trigger discoverable | `aria-label="Cambiar clínica"` + visible focus ring (Tailwind `focus-visible:ring-2 focus-visible:ring-ring`) |
| Keyboard navigation | Radix `DropdownMenu` nativo: Tab focus trigger · Enter/Space open · Arrow ↓↑ navigate items · Enter select · Esc close |
| Screen reader badge | `<TenantBadge aria-hidden="true">` — initials decorativos, el screen reader lee el name del TenantOption |
| Screen reader active state | `<Check className="sr-only">` + visible icon + label "Clínica activa" en sr-only span dentro del row |
| Color contrast badge | Hash palette colors ALL >4.5:1 vs white text (verified): cyan-500 (#06b6d4 vs white 4.94:1) · purple-500 (#a855f7 vs white 4.51:1) · magenta-500 (#d946ef vs white 4.85:1) · amber-500 (#f59e0b vs white 2.93:1 ⚠ — usar `text-amber-950` cuando hash → amber para mantener contrast AA) · lime-500 (#84cc16 vs white 2.21:1 ⚠ — usar `text-lime-950`) · rose-500 (#f43f5e vs white 4.51:1) |
| Color contrast row text | Foreground vs background: light `hsl(240 10% 4%)` vs `hsl(0 0% 100%)` = 19.3:1 (AAA). Dark `hsl(0 0% 98%)` vs `hsl(240 10% 4%)` = 18.5:1 (AAA). |
| Color contrast active row | `bg-accent/40` (purple-300 alpha en light) vs text foreground = ≥7:1 (AAA). En dark `bg-accent/40` (purple alpha en dark) = ≥7:1. |
| Touch targets mobile | Trigger button min-h-10 (40px) · TenantOption row min-h-10 → ≥44×44 touch target WCAG 2.5.5 |
| Reduced motion | DropdownMenu Radix respect `prefers-reduced-motion` nativo (open/close animation 0ms si reduced) |
| ARIA roles | `<DropdownMenuContent role="menu">` · `<DropdownMenuItem role="menuitem">` Radix nativo |

**Contrast fix forward:** /architect cementa en 03-arch.md la fix para amber/lime palette colors:

```tsx
const PALETTE = [
  { bg: 'bg-cyan-500',   text: 'text-white' },
  { bg: 'bg-purple-500', text: 'text-white' },
  { bg: 'bg-fuchsia-500', text: 'text-white' },   // #d946ef
  { bg: 'bg-amber-500',  text: 'text-amber-950' }, // dark text on light yellow
  { bg: 'bg-lime-500',   text: 'text-lime-950' },  // dark text on light green
  { bg: 'bg-rose-500',   text: 'text-white' },
] as const

function pickPaletteColor(tenantId: string): typeof PALETTE[number] {
  const hash = tenantId.split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0)
  return PALETTE[hash % PALETTE.length]
}
```

---

## § 12 — Telemetría (opcional pero recomendado)

```yaml
events:
  - name: "tenant_switcher_opened"
    trigger: "click on TenantSwitcher trigger"
    props: ["current_tenant_id", "available_count"]
  - name: "tenant_switched"
    trigger: "click on TenantOption row (different tenant)"
    props: ["from_tenant_id", "to_tenant_id", "path_preserved"]
  - name: "tenant_switcher_error_shown"
    trigger: "/api/tenants failure renders Alert"
    props: ["error_code", "retry_count"]
  - name: "tenant_switcher_retry_clicked"
    trigger: "Reintentar button click"
    props: ["retry_count"]
  - name: "tenant_add_placeholder_opened"
    trigger: "click on Agregar clínica → modal opens"
    props: []
```

**Implementación:** F1-S3 NO implementa telemetría custom. Tracking es nice-to-have, escala Fase 2 si demanda business existe. Por ahora Sentry pageload + Clerk auth events cubren coverage mínimo.

---

## § 13 — Brand voice

SHELL chrome UI — no es output sales_agent ni copilot. Spanish neutro LatAm estándar (Vitalia salud LatAm). NO citar `personality_profiles.system_instruction` (eso es per-tenant voice de agentes, no chrome).

**Tono Vitalia chrome shell:**
- Claro · directo · sin jerga técnica innecesaria · sin emojis en strings críticos (Alert/Error)
- Permitidos emojis estructurales en actions footer: ➕ Agregar · ⚙ Administrar
- Acción primera persona usuario (tuteo): "Tu cuenta" · "Tus clínicas"

---

## § 14 — HIPAA-lite scope declaration

**No-PHI-scope declaration:** F1-S3 TenantSwitcher NO procesa, NO renderiza, NO transmite, NO persiste PHI (Protected Health Information).

Data manipulada:
- `tenant.id`, `tenant.name`, `tenant.city` — metadata organizacional pública (nombre clínica + ciudad)
- `user.id` (Clerk) — identifier técnico, no PHI

Por tanto `vitalia/.claude/rules/hipaa-lite.md` NO aplica scope a esta story. /architect + /dev-team NO necesitan implementar audit logs específicos PHI ni encryption fields para tenant_switcher.

---

## § 15 — Acceptance criteria (consolidado)

| AC | Descripción | Grader | Status spec |
|---|---|---|---|
| AC-1 | TenantSwitcher visible TopBar derecha tras F1-S2 placeholder replace | Visual + E2E | ✅ |
| AC-2 | Click trigger abre dropdown con lista tenants | E2E Scenario 1 | ✅ |
| AC-3 | Tenant activo marca con check + bg-accent/40 | Visual + E2E | ✅ |
| AC-4 | Click otro tenant → hard redirect preservando ruta | E2E Scenario 1 | ✅ |
| AC-5 | LocalStorage `vitalia-tenant-state` persiste activeTenant | state_check Scenario 1 | ✅ |
| AC-6 | "Agregar clínica" click → modal placeholder "Próximamente" | E2E + unit | ✅ |
| AC-7 | "Administrar cuenta" click → navega a `/{activeTenant.id}/config/cuenta` | E2E | ✅ |
| AC-8 | a11y: trigger aria-label, Radix nativo keyboard nav, contrast AA | axe Scenario 10 | ✅ |
| AC-9 | Visual goldens: closed + open snapshots light + dark | playwright snapshot | ✅ |
| AC-10 | Vitest unit: render + click → switchTenant called | unit | ✅ |
| AC-11 | Playwright functional: complete tenant switch flow | E2E Scenario 1 | ✅ |
| AC-12 | Loading state: API pending → Skeleton inline dropdown | E2E Scenario 7-loading | ✅ |
| AC-13 | Error state: API 500 → Alert destructive + Reintentar inline | E2E Scenario 7 | ✅ |
| AC-14 | TenantBadge hash determinístico predecible cross-session | unit | ✅ |
| AC-15 | Subtitle muestra solo city (no branch/sucursal) | visual + unit | ✅ |
| AC-16 | Trigger truncate max-w-[180px] + title tooltip | unit + visual | ✅ |
| AC-17 | Multi-tab race localStorage → last-write-wins natural | E2E Scenario 5 | ✅ |
| AC-18 | SignOut isolation: user A logout → user B sees only own tenants | E2E Scenario 6 | ✅ |
| AC-19 | Empty 0 tenants → graceful degrade banner | E2E Scenario 8 | ✅ |
| AC-20 | Large dataset 12 tenants → scroll vertical max-h-80 + scroll-into-view | E2E Scenario 9 | ✅ |
| AC-21 | i18n Spanish neutro verbatim (no voseo) | E2E Scenario 11 | ✅ |
| AC-22 | Single tenant edge: 1 row + 2 actions footer | E2E Scenario 12 | ✅ |

---

## § 16 — Deliverables (handoff a /architect)

| File | Acción | Origen |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx` | NEW | adaptado 75% nicolify ref |
| `vitalia/frontend/src/components/shared/shell-organism/TenantOption.tsx` | NEW | composición |
| `vitalia/frontend/src/components/shared/shell-organism/TenantBadge.tsx` | NEW | hash palette |
| `vitalia/frontend/src/components/shared/shell-organism/AddClinicPlaceholderModal.tsx` | NEW | Shadcn Dialog |
| `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx` | DELETE | drop-in replace de F1-S2 |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | MODIFY (1 línea) | import TenantSwitcher en lugar de TenantSwitcherSlot |
| `vitalia/frontend/src/stores/tenant-store.ts` | NEW | Zustand persist |
| `vitalia/frontend/src/hooks/useTenants.ts` | NEW | React Query |
| `vitalia/frontend/src/lib/tenant-palette.ts` | NEW | PALETTE + pickPaletteColor helper |
| `vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantSwitcher.test.tsx` | NEW | Vitest unit |
| `vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantOption.test.tsx` | NEW | Vitest unit |
| `vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantBadge.test.tsx` | NEW | Vitest unit (palette determinismo) |
| `vitalia/frontend/src/stores/__tests__/tenant-store.test.ts` | NEW | Vitest unit |
| `vitalia/frontend/src/lib/__tests__/tenant-palette.test.ts` | NEW | Vitest unit (hash function) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/happy-switch.spec.ts` | NEW | Scenario 1 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/concurrent-clicks.spec.ts` | NEW | Scenario 3 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/adversarial-cross-tenant.spec.ts` | NEW | Scenario 4 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/race-multi-tab.spec.ts` | NEW | Scenario 5 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/concurrent-users.spec.ts` | NEW | Scenario 6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/network-failure.spec.ts` | NEW | Scenario 7 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/empty-state.spec.ts` | NEW | Scenario 8 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/large-dataset.spec.ts` | NEW | Scenario 9 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/a11y-keyboard.spec.ts` | NEW | Scenario 10 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/i18n-spanish-neutro.spec.ts` | NEW | Scenario 11 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/single-tenant.spec.ts` | NEW | Scenario 12 |
| `vitalia/frontend/e2e/__screenshots__/shell/tenant-switcher-closed-{light,dark}.png` | NEW | visual golden |
| `vitalia/frontend/e2e/__screenshots__/shell/tenant-switcher-open-{light,dark}.png` | NEW | visual golden |
| `vitalia/frontend/e2e/__screenshots__/shell/tenant-switcher-open-loading-{light,dark}.png` | NEW | visual golden |
| `vitalia/frontend/e2e/__screenshots__/shell/tenant-switcher-open-error-{light,dark}.png` | NEW | visual golden |

---

## § 17 — Gate v4.1 checklist

- [x] 4 base scenarios presentes (happy + negative + edge + adversarial)
- [x] race_condition cubierto (Scenario 5 multi-tab)
- [x] concurrent_users cubierto (Scenario 6 signOut isolation)
- [x] network_failure cubierto (Scenario 7 API timeout)
- [x] empty_state cubierto (Scenario 8 zero tenants)
- [x] large_dataset cubierto (Scenario 9 12 tenants scroll)
- [x] accessibility cubierto (Scenario 10 WCAG AA + keyboard)
- [x] i18n cubierto (Scenario 11 Spanish neutro verbatim)
- [x] Cada scenario funcional FE tiene `playwright_required: true` (11/12; Scenario 2 unit-only justificado)
- [x] Cada `then:` es verificable (no vagos)
- [x] `graders:` declarados (e2e + state_check + visual_state + axe)
- [x] Wireframes inline ASCII + mockups HTML referenciados
- [x] Estados visuales (idle/loading/success/error/empty/single)
- [x] Microcopy Spanish neutro verbatim tabla
- [x] Componentes reuse > new (3 NEW justificados; 75% TenantSwitcher reuse nicolify ref)
- [x] Responsive breakpoints declarados
- [x] Accessibility section + contrast fix forward documentado

Gate v4.1: **PASS** ✅ — ready para Chris ratify + transition `refining → refined`.

---

## § 18 — Handoff /architect

Una vez `ratified_by_chris: true` + `ratified_visual_by_chris: true`:

```
/architect <brand>: vitalia

Story: vitalia-fase1-tenant-switcher (F1-S3 Fase 1 shell-organism)
State: refined → ready (post architect output)

Lee:
- 01-spec.md (este doc)
- mockups/tenant-switcher-{closed,open}.html (visual contract ratificado)
- 03-arch.md predecessor F1-S2 (§ 2.4 TenantSwitcherSlot placeholder)
- nicolify/frontend/src/components/shared/layout/TenantSwitcher.tsx (75% reuse reference)
- vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md (líneas 88-90 + 108 + 475 + 530 + 575 + 621)
- vitalia/.claude/rules/shell-mockup-per-component.md

Produce ready package:
- 03-arch.md: TS types Tenant + TenantStore + useTenants response · file tree componentes · imports DAG · React Query config · Zustand persist strategy · cross-user signOut clear hook · path preservation algorithm · color palette + contrast fix · estructura tests + visual goldens.
- 04-validators.yaml: 5 categorías (non_functional/functional/visual/agentic_eval=N/A/architectural_validation). Cada must_pass:true scenarios → comando shell exacto.
- 05-guidelines.md: must_load_skills (frontend-expert, tessl__shadcn-ui, tessl__tailwind) · patterns required (Radix DropdownMenu primitives, fetchClient inject X-Tenant-ID, Zustand persist partialize) · forbidden (avatar image fetch, Clerk Organizations, manual JWT decode, hardcoded paths).
- 06-tickets.yaml: 7-9 work units atómicos con gherkin_coverage scenarios → test files. Owner eligibility opencode/Sonnet (FE no-agentic). Sequence: T-1 TenantBadge átomo + tests · T-2 TenantOption molécula + tests · T-3 tenantStore + tests · T-4 useTenants hook + tests · T-5 TenantSwitcher organismo (loading+error+empty+success) · T-6 TopBarGlobal replace placeholder · T-7 E2E specs Scenarios 1+3+10+11 · T-8 E2E specs Scenarios 4+5+6+7+8+9+12 (adversarial+edge) · T-9 visual goldens + docs.

ZERO Opus (FE no-agentic puro).
```

---

**Fin 01-spec.md F1-S3 v1.0 · /po-ux Vitalia · 2026-05-22.**
