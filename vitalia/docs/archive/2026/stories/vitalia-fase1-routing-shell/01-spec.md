<!-- voseo-allowed: internal /po-ux spec documentation, not user-facing -->
---
story_id: vitalia-fase1-routing-shell
brand: vitalia
type: ui-story
state: refining
outcome: vitalia-mvp-ui-foundation
phase: fase-1
module: shell-organism
capability: shell.routing
po_ux_version: 2
ratified_by_chris: true
ratified_at: 2026-05-25T16:30:00Z
ratified_visual_by_chris: not_applicable  # routing puro, sin componente visual nuevo (per shell-mockup-per-component.md § Scope NO aplica)
ratified_visual_reason: "F1-S9 es routing puro — reusa mockups F1-S2..S8 ratificados como referencia integral del shell. Único componente visual nuevo: not-found.tsx (especificado inline en este spec con wireframe ASCII)"
last_modified: 2026-05-25
po_ux_version: 2
batch_1_ratified_at: 2026-05-25
batch_2_ratified_at: 2026-05-25T16:30:00Z
batch_1_decisions:
  Q1_default_landing: valeria/agenda      # changed from F1-S4 default lisa/marca
  Q2_routing_file: proxy.ts                # Next.js 16 deprecated middleware.ts
  Q3_legacy_policy: delete_plus_redirect   # no legacy except marketing/ + public/[clinic-slug]/
  Q4_not_found_hierarchy: outer_plus_inner # (shell-organism)/not-found.tsx + [agent]/not-found.tsx
  Q5_v41_subcategories: "network_failure + accessibility + i18n applies; race/concurrent/empty/large N/A"
  scope_decision: monolithic               # single story, not split
batch_2_decisions:
  Q6_no_tenants_assigned: sign_out_plus_admin_message   # NOT /onboarding/wizard (that's post-sign-up flow only)
  Q7_network_error_retry: manual_only                   # no auto-retry, just "Reintentar" button
  Q8_endpoint_user_tenants: REUSE_CORE                  # core/luana-core-iam/auth_router.py:23 already has GET /me/tenants
  Q8_endpoint_path: "/api/v1/iam/me/tenants (or whatever /architect prefix resolves vs vitalia local /me collision)"
  Q9_capability_yamls: "1 DELETE (welcome-state) + 6 MODIFY (remove FE legacy path, add fe_planned_phase2) + 1 KEEP (shell-foundation)"
authors: [/po-ux]
spec_anchors:
  shell_design_contract: vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
  shell_template: vitalia/docs/specs/templates/01-spec-shell-template.md
  agent_catalog_ssot: vitalia/frontend/src/lib/agent-catalog.ts
  predecessor_F1_S4: vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/01-spec.md
  predecessor_F1_S7: vitalia/docs/archive/2026/stories/vitalia-fase1-ribbon-6-tabs/01-spec.md
  predecessor_F1_S8: vitalia/docs/archive/2026/stories/vitalia-fase1-sub-tabs-line2/01-spec.md
ssot_extensions:
  agent_catalog: vitalia/frontend/src/lib/agent-catalog.ts (EXTEND — isValidAgent + isValidSubtab validators)
overlay_rules:
  - vitalia/.claude/rules/hipaa-lite.md           # auth + tenant validation en proxy
  - vitalia/.claude/rules/shell-mockup-per-component.md  # gate visual N/A justificado arriba
external_docs:
  - https://nextjs.org/docs/app/api-reference/file-conventions/proxy
  - https://clerk.com/docs/reference/nextjs/clerk-middleware
---

# F1-S9 · `vitalia-fase1-routing-shell` — 01-spec.md (unified)

> **/po-ux UI-standard.** Routing puro shell-organism (sin componente UI nuevo salvo `not-found.tsx`). Gherkin + wireframe ASCII `not-found.tsx` + estados visuales + microcopy + graders en este archivo.

---

## § 1 — Resumen ejecutivo

Cementa el sistema de routing del shell-organism: `proxy.ts` (Next.js 16) con `clerkMiddleware()` + páginas dinámicas `[agent]/[subtab]/page.tsx` que validan contra `agent-catalog.ts` SSoT + `not-found.tsx` jerárquico (outer/inner) + tenant validation en server-component layout. Al merge, Vitalia queda sin código legacy frontend: borrá `app/(dashboard)/` y `app/(app)/` enteros, ajustá tests y marcá capabilities como `superseded by shell-organism`. Dueño puede entrar a `dev-app.vitalialat.com`, autenticarse, y navegar libremente los 6 tabs × 22 sub-tabs — contenido vacío (F1-S10) pero shell funcional.

**Outcome del usuario después de merge:** "puedo entrar a dev-app, autenticarme, navegar las 6 pestañas + 22 sub-tabs sin que rompa nada, y cualquier URL inválida me muestra un 404 amigable dentro del shell."

**Anti-objetivos** (anti-creep):

- NO contenido per sub-tab (eso es F1-S10 empty-states)
- NO componentes UI nuevos del shell (Ribbon/SubTabsBar/ValeriaSidebar ya hechos F1-S5..F1-S8)
- NO refactor del backend tenant ownership (BE devuelve lista de tenants del user — sin cambios)
- NO N3-dyn workspaces (Fase 2)
- NO mantener `(dashboard)/` ni `(app)/` legacy (Chris dictum 2026-05-25)
- NO redirects 308 desde URLs legacy hacia shell-organism (URLs legacy quedan 404 — dev-only previo a prod, no hay usuarios reales)

---

## § 2 — Visión (paradigma shell-organism)

F1-S9 es el cableado entre el shell construido por F1-S0..F1-S8 (átomos + moléculas + layout) y el dominio Next.js. Sin esto, el shell organism es código pero no aplicación navegable. Cementa la jerarquía URL canónica que la visión norte dicta: `/{tenantId}/{agent}/{subtab}` — el dueño piensa "voy a Valeria/Agenda", la URL refleja exactamente eso.

**Default landing post-login = `/{tenantId}/valeria/agenda`** (decisión Chris 2026-05-25, cambia el `/lisa/marca` original de F1-S4). Razón: la visión norte es "como una secretaria real, el dueño habla con Valeria"; Valeria/Agenda es la operación día-a-día más frecuente.

**Agente owner:** Shell (transversal — F1-S9 no pertenece a un agente específico, es plomería).

---

## § 3 — Atomic Design Layers (referencia Design Contract § 3)

### § 3.1 — Átomos consumidos

| Átomo | Fuente | Variante | Path local |
|---|---|---|---|
| `Button` | Shadcn | `default + asChild` | `components/ui/button.tsx` |

(Solo `Button` consumido en `not-found.tsx`. Resto de la story es server-side routing — no átomos UI.)

### § 3.2 — Moléculas construidas en esta historia

(Ninguna.)

### § 3.3 — Organismos construidos en esta historia

| Organismo | Composición | State management | Keyboard | Path nuevo |
|---|---|---|---|---|
| `NotFoundShell` (outer) | `Button + Link + ícono + título + descripción` | stateless | `Tab` → CTA · `Enter` → navegar | `app/[tenantId]/(shell-organism)/not-found.tsx` |
| `NotFoundAgent` (inner) | `Button + Link + ícono + texto contextual con nombre agente` | stateless | idem | `app/[tenantId]/(shell-organism)/[agent]/not-found.tsx` |

### § 3.4 — Templates / Pages modificadas/creadas

| Path Next.js | Acción |
|---|---|
| `vitalia/frontend/src/proxy.ts` | **NEW** — `clerkMiddleware()` + matcher Clerk 2026 + auth.protect() rutas privadas |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx` | **MODIFY** — cambiar redirect `lisa/marca` → `valeria/agenda` |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx` | **MODIFY** — agregar tenant validation server-side (fetch user tenants, valida `params.tenantId` ∈ list) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/layout.tsx` | **NEW** — valida agent slug vs `agent-catalog.ts::isValidAgent` |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.tsx` | **NEW** — redirect a `AGENT_CATALOG[agent].defaultSubtab` |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | **NEW** — valida subtab vs `agent-catalog.ts::isValidSubtab` + render placeholder hasta F1-S10 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx` | **NEW** — outer 404 (invalid agent) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/not-found.tsx` | **NEW** — inner 404 (invalid subtab dentro de agent válido) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[...slug]/page.tsx` | **DELETE** — catchall stub F1-S7 T-5 obsoleto post-F1-S9 |
| `vitalia/frontend/src/lib/agent-catalog.ts` | **EXTEND** — agregar `isValidAgent(slug)` + `isValidSubtab(agent, slug)` validators |
| `vitalia/frontend/src/lib/iam/api.ts` | **NEW** — `fetchUserTenants(userId)` consumiendo `GET /api/v1/iam/me/tenants` (core endpoint, NO duplicar — Q8 investigado) |
| `vitalia/backend/src/main.py` | **MODIFY** — montar `auth_router` desde `luana_core_iam.api.routers` (1 línea, pattern nicolify/backend/main.py:92). `/architect` decide prefix vs colisión con `/me` brand-local |
| `vitalia/frontend/src/app/(dashboard)/**` | **DELETE** — 8 sub-rutas legacy completas |
| `vitalia/frontend/src/app/(app)/**` | **DELETE** — 1 sub-ruta legacy (inbox) |
| `vitalia/frontend/e2e/pages/fidelizacion.page.ts` | **DELETE** — POM legacy |
| `vitalia/frontend/e2e/visual/visual-smoke.spec.ts` | **MODIFY** — remover assertions sobre (dashboard) |
| `vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts` | **MODIFY** — idem |
| `vitalia/frontend/e2e/mobile/mobile-smoke.spec.ts` | **MODIFY** — idem |
| `vitalia/frontend/e2e/a11y/a11y-smoke.spec.ts` | **MODIFY** — idem |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/*` | **NEW** — suite Playwright (ver § 5 graders) |
| `vitalia/docs/product/capabilities/dashboard/welcome-state.yaml` | **DELETE** — FE-only legacy, NO re-implementado en Fase 2 (default landing va directo a Valeria/Agenda sin welcome) |
| `vitalia/docs/product/capabilities/{booking,compliance,brand_studio,offer_studio,patients,treatments}/*.yaml` (6 archivos) | **MODIFY** — remover `+ vitalia/frontend/src/app/(dashboard)/...` del `package_path`, agregar `fe_planned_phase2: vitalia-fase2-{story}` field. NO cambiar `status: live` — BE sigue vivo. |
| `vitalia/docs/product/capabilities/platform/shell-foundation-shadcn-tailwind-v4.yaml` | **KEEP** — FE foundation activa, sin path `(dashboard)` específico |

**Cross-brand mirror check:** `proxy.ts` pattern es brand-local Vitalia (Next.js 16 + Clerk). Cuando Nicolify/Comunify/Lupulo upgrade Next.js 16 (futuro), candidate promotion a `core/luana-core-frontend-shared/` — anotar en `learnings/{date}-nextjs16-proxy-pattern.md` con `promotable: candidate`.

---

## § 4 — Context

- **Outcome:** `vitalia-mvp-ui-foundation` (contenedor Fase 1 + Fase 2 shell-organism).
- **Módulo afectado:** `shell-organism`.
- **Insertion point:** todo el árbol `app/[tenantId]/(shell-organism)/` (creado por F1-S4, extendido aquí).
- **User journey insertion point:**
  1. User abre `dev-app.vitalialat.com`
  2. Sin sesión → Clerk redirige a `/sign-in`
  3. Login → Clerk redirige a `/{tenantId}/(shell-organism)/` (root del shell)
  4. Root page redirige a `/{tenantId}/valeria/agenda` (F1-S9 default)
  5. User navega tabs Ribbon + sub-tabs SubTabsBar → URL cambia, content empty placeholder (F1-S10)
- **Predecesores done:** F1-S0..F1-S8 (todo el shell estructural).

---

## § 5 — Gherkin scenarios

### Base obligatorios (4)

#### SC-1 happy · login + default landing + navegación completa

```gherkin
Given un user autenticado con tenant_id=clinic-X en JWT
  And user abre https://dev-app.vitalialat.com/
When proxy.ts intercepta + Clerk valida sesión
  And browser carga /clinic-X/(shell-organism)/
  And root page server-side redirige a /clinic-X/valeria/agenda
  And user click Ribbon "Atraer" (Lucas tab)
  And user click SubTab "Recursos"
Then URL final = /clinic-X/lucas/recursos
  And Ribbon active state = Lucas
  And SubTabsBar active state = "Recursos"
  And content placeholder (F1-S10) renders sin error
  And page <title> = "Vitalia · Lucas · Recursos" (Spanish neutro)
```

| Grader | Detalle |
|---|---|
| e2e | `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/happy-navigation.spec.ts` |
| state_check | `document.title` matches expected per route |
| visual_state | Ribbon[data-state=active] = Lucas tab, SubTabsBar[data-state=active] = Recursos |
| playwright_required | true |

#### SC-2 negative · agent slug inválido

```gherkin
Given user autenticado en tenant=clinic-X
When user navega manualmente a /clinic-X/foo
Then proxy.ts pasa request (auth válida)
  And [agent]/layout.tsx ejecuta isValidAgent("foo") → false
  And Next.js renderiza app/[tenantId]/(shell-organism)/not-found.tsx (outer)
  And HTTP status code = 404
  And Ribbon NO renderiza (layout outer omite)
  And SubTabsBar NO renderiza
  And NotFoundShell muestra: ícono 🔍 + título "No encontramos esta vista" + CTA "Volver al inicio"
  And click CTA navega a /clinic-X/valeria/agenda
```

| Grader | Detalle |
|---|---|
| e2e | `.../not-found-outer.spec.ts` |
| state_check | `response.status === 404` |
| visual_state | `[data-testid=not-found-shell]` visible · Ribbon NOT in DOM |
| playwright_required | true |

#### SC-3 edge · subtab inválido dentro de agent válido

```gherkin
Given user autenticado en tenant=clinic-X
When user navega manualmente a /clinic-X/camila/foo
Then proxy.ts pasa request
  And [agent]/layout.tsx ejecuta isValidAgent("camila") → true
  And [agent]/[subtab]/page.tsx ejecuta isValidSubtab("camila", "foo") → false
  And Next.js renderiza app/[tenantId]/(shell-organism)/[agent]/not-found.tsx (inner)
  And HTTP status code = 404
  And Ribbon SÍ renderiza con Camila active
  And SubTabsBar SÍ renderiza con sub-tabs de Camila visibles SIN ninguna active
  And NotFoundAgent muestra: ícono + "No encontramos esa vista dentro de Camila" + CTA "Ir a la vista principal de Camila"
  And click CTA navega a /clinic-X/camila/voz (defaultSubtab de Camila)
```

| Grader | Detalle |
|---|---|
| e2e | `.../not-found-inner.spec.ts` |
| state_check | `response.status === 404` |
| visual_state | Ribbon[active=camila] visible · SubTabsBar visible sin tab activa · `[data-testid=not-found-agent]` |
| playwright_required | true |

#### SC-4 adversarial · cross-tenant access blocked

```gherkin
Given user A con JWT tenant_id=clinic-A
  And user A intenta acceder a /clinic-B/(shell-organism)/valeria/agenda
When proxy.ts pasa request (auth Clerk válida — sesión sí existe)
  And (shell-organism)/layout.tsx server-side ejecuta fetch GET /api/v1/iam/me/tenants
  And BE responde { tenants: [{ id: "clinic-A", ... }] }  // user A no pertenece a clinic-B
  And layout detecta params.tenantId="clinic-B" ∉ user.tenants
Then layout ejecuta redirect("/clinic-A/valeria/agenda")  // fallback al primer tenant válido
  And browser final URL = /clinic-A/valeria/agenda
  And NO se renderiza ningún chrome de clinic-B (NO leak)
  And audit log capture row { action: "cross_tenant_attempt", user_id: A, attempted_tenant: B, ip: ..., timestamp: ... }
```

| Grader | Detalle |
|---|---|
| e2e | `.../cross-tenant-blocked.spec.ts` (mockea Clerk session + BE response) |
| state_check | DB audit_log query confirms row |
| visual_state | final URL contains "clinic-A", NO render clinic-B chrome |
| playwright_required | true |

### Sub-categorías v4.1 mandatory

#### SC-5 network_failure · BE tenant fetch timeout

```gherkin
Given user autenticado
  And BE /api/v1/iam/me/tenants timeout (response > 5s)
When user navega a /clinic-X/(shell-organism)/
  And layout.tsx fetch falla con AbortError
Then layout server-side fallback:
  - log error structlog
  - render fallback UI: "Estamos teniendo problemas conectando con el servidor. Intenta de nuevo." + botón "Reintentar"
  - NO redirect ciclo infinito (gate: 1 intento + fallback)
  And HTTP status code = 200 (no 500 — degraded UX, no error técnico al user)
  And botón "Reintentar" hace router.refresh()
```

| Grader | Detalle |
|---|---|
| e2e | `.../network-failure-tenant-fetch.spec.ts` (Playwright `page.route()` intercepta + delay 6s) |
| visual_state | `[data-testid=network-error-fallback]` visible · button "Reintentar" focuseable |
| playwright_required | true |
| not_applicable_reason | N/A |

#### SC-6 accessibility · keyboard nav + screen reader anuncia cambio de página

```gherkin
Given user navegando con teclado solamente
  And screen reader activo (VoiceOver / NVDA)
When user presiona Tab para mover focus al Ribbon
  And user usa Arrow keys para mover entre tabs (paridad F1-S7 roving tabindex)
  And user presiona Enter en tab "Adrián"
Then URL cambia a /clinic-X/adrian/inbox
  And screen reader anuncia "Adrián, sub-tab Inbox" (via <main aria-live="polite"> o <title> change)
  And focus se mueve al primer elemento focuseable del content area
  And no-focus-trap detectable (Tab + Shift+Tab navega libre)
  And contraste todos los textos ≥ 4.5:1 (incluido not-found.tsx)
  And axe-core scan WCAG 2.1 AA passes
```

| Grader | Detalle |
|---|---|
| e2e | `.../a11y-keyboard-nav.spec.ts` + `.../axe-scan.spec.ts` |
| axe | `ruleset: "wcag21aa"` aplica a 22 sub-tab combos + 2 not-found pages |
| playwright_required | true |

#### SC-7 i18n · microcopy Spanish neutro LatAm

```gherkin
Given user navegando shell-organism
When renderiza cualquier not-found.tsx (outer o inner)
  And renderiza network-failure fallback
  And document.title cambia
Then todo string user-facing está en Spanish neutro:
  - NO voseo ("tú/tienes/puedes" no "vos/tenés/podés")
  - NO léxico regional ("dale", "laburo", "quilombo")
  - tildes + ñ + apertura ¿!  correctos
  - copy verificable contra glosario en .claude/rules/spanish-text.md
```

| Grader | Detalle |
|---|---|
| e2e | `.../i18n-spanish-neutro.spec.ts` (regex scan páginas renderizadas) |
| static_check | grep build output for forbidden tokens (vos, tenés, dale, etc.) |
| playwright_required | true |

#### SC-8 edge · user autenticado sin tenants asignados (Q6 edge case)

```gherkin
Given user con sesión Clerk válida pero sin tenant_id asignado en BE
  And BE responde GET /api/v1/iam/me/tenants → []
When user navega a /clinic-X/(shell-organism)/...
  And proxy.ts pasa request (auth Clerk OK)
  And layout.tsx fetch tenants → []
  And layout detecta tenants.length === 0
Then log audit_log row { action: "no_tenants_assigned", user_id, timestamp }
  And ejecutar Clerk sign-out programático
  And redirect a /sign-in?error=no_tenants_assigned
  And pantalla muestra mensaje: "Tu cuenta no tiene clínicas asignadas. Contactá al administrador de tu clínica para activar tu acceso."
  And NO se renderiza shell-organism chrome (NO leak)
```

| Grader | Detalle |
|---|---|
| e2e | `.../no-tenants-edge.spec.ts` (Playwright mockea BE response `{tenants:[]}`) |
| state_check | DB audit_log row + Clerk session cleared |
| visual_state | URL contains `error=no_tenants_assigned` · mensaje admin visible |
| playwright_required | true |

### N/A justificadas (4)

| Sub-categoría | Razón N/A |
|---|---|
| `race_condition` | No hay create/update con unique constraint. F1-S9 es solo navegación. |
| `concurrent_users` | Routing es per-session. No hay estado compartido cross-user. SC-4 cubre el caso adyacente (cross-tenant access). |
| `empty_state` | Empty per sub-tab es responsabilidad de F1-S10. F1-S9 solo cablea routing — el placeholder mientras tanto es un componente trivial inline. |
| `large_dataset` | No hay list/pagination en routing. Validators `isValidAgent`/`isValidSubtab` son O(1) sobre arrays de 6/22 elementos. |

---

## § 6 — Wireframes inline

### 6.1 — `not-found.tsx` OUTER (invalid agent) — sin chrome shell

```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│                              🔍                                │
│                                                               │
│                    No encontramos esta vista                  │
│                                                               │
│       Quizás el enlace está roto o el agente que buscas       │
│             no existe en esta clínica.                        │
│                                                               │
│                  ┌────────────────────────┐                   │
│                  │   Volver al inicio     │  ← Button default │
│                  └────────────────────────┘                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
   (fill viewport · centered · NO TopBar · NO Ribbon · NO Sidebar)
```

### 6.2 — `not-found.tsx` INNER (invalid subtab) — con chrome shell

```
┌──────────────────────────────────────────────────────────────────────┐
│ TopBar [Vitalia · TenantSwitcher · UserMenu]                          │
├──────────────────────────────────────────────────────────────────────┤
│ ValeriaSidebar (left, 50%)        │ AppPanel (right, 50%)            │
│                                    │                                  │
│                                    │ Ribbon: [Lisa Lucas Adrián       │
│                                    │          ▼Camila Valeria · ⚙]   │
│                                    │  ────────────────────────────    │
│                                    │ SubTabsBar: Voz · Reactivar ·    │
│                                    │             Multiplicar · Reput  │
│                                    │  (ninguna active)                │
│                                    │  ────────────────────────────    │
│                                    │                                  │
│                                    │             🔍                   │
│                                    │   No encontramos esa vista       │
│                                    │      dentro de Camila            │
│                                    │                                  │
│                                    │  ┌─────────────────────────┐    │
│                                    │  │ Ir a Voz del paciente   │    │
│                                    │  └─────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.3 — Network failure fallback (en `(shell-organism)/layout.tsx`)

```
┌──────────────────────────────────────────────────────────────┐
│ TopBar (sin TenantSwitcher porque no se cargó la lista)       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│                          ⚠️                                    │
│                                                               │
│        Estamos teniendo problemas conectando con el           │
│         servidor. Intenta de nuevo en unos segundos.          │
│                                                               │
│                  ┌────────────────────────┐                   │
│                  │     Reintentar         │                   │
│                  └────────────────────────┘                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## § 7 — Estados visuales

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `shell_loaded_default` | login + redirect default | TopBar · ValeriaSidebar · Ribbon (Valeria active) · SubTabsBar (Agenda active) · content placeholder F1-S10 | not-found · network-error |
| `shell_loaded_other_agent` | click Ribbon agent ≠ Valeria | TopBar · ValeriaSidebar · Ribbon (X active) · SubTabsBar (defaultSubtab(X) active) · content placeholder | not-found · network-error |
| `not_found_outer` | invalid agent slug | NotFoundShell (centered, fill viewport) | TopBar · Ribbon · SubTabsBar · ValeriaSidebar |
| `not_found_inner` | invalid subtab dentro agent válido | TopBar · ValeriaSidebar · Ribbon (agent active) · SubTabsBar (sin active) · NotFoundAgent | content placeholder |
| `network_error_fallback` | BE tenant fetch timeout | TopBar (sin TenantSwitcher poblado) · Network error message + Reintentar | Ribbon · SubTabsBar · ValeriaSidebar |
| `auth_redirect` | sin sesión Clerk | Clerk sign-in page (fuera del shell) | TODO el shell |

---

## § 8 — Componentes (reutilizar > inventar)

| Componente | Path | Decisión |
|---|---|---|
| `Button` | `vitalia/frontend/src/components/ui/button.tsx` | REUSE (Shadcn) |
| `ShellOrganismLayout` | `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx` | REUSE (F1-S4) |
| `Ribbon` | `vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx` | REUSE (F1-S7) |
| `SubTabsBar` | `vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx` | REUSE (F1-S8) |
| `ValeriaSidebar` | `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | REUSE (F1-S5+F1-S6) |
| `TopBarGlobal` | `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | REUSE (F1-S2) |
| `agent-catalog.ts` validators | `vitalia/frontend/src/lib/agent-catalog.ts` | EXTEND (NO crear nuevo archivo lib) |
| `NotFoundShell` (outer) | `app/[tenantId]/(shell-organism)/not-found.tsx` | NEW — no existe equivalente. Composición trivial (Button + Link + texto). |
| `NotFoundAgent` (inner) | `app/[tenantId]/(shell-organism)/[agent]/not-found.tsx` | NEW — variante contextual del outer. |
| `NetworkErrorFallback` | inline en `(shell-organism)/layout.tsx` (no archivo aparte) | NEW — uso único, no justifica componente separado |
| `proxy.ts` | `vitalia/frontend/src/proxy.ts` | NEW — Next.js 16 file convention |

**Justificación NEW NotFoundShell + NotFoundAgent:** Next.js 16 require que `not-found.tsx` viva en filesystem (no es importable como componente). Por convención del framework deben ser archivos separados. Composición trivial.

---

## § 9 — Data flow (conceptual)

### 9.1 — Routing tree post-merge

```
app/[tenantId]/(shell-organism)/
├── layout.tsx                    # F1-S4 MODIFY · tenant validation + ShellOrganismLayout
├── page.tsx                      # F1-S4 MODIFY · redirect → /[tenantId]/valeria/agenda
├── not-found.tsx                 # NEW · outer 404
├── [agent]/
│   ├── layout.tsx                # NEW · isValidAgent or notFound()
│   ├── page.tsx                  # NEW · redirect → /[tenantId]/[agent]/[defaultSubtab]
│   ├── not-found.tsx             # NEW · inner 404
│   └── [subtab]/
│       └── page.tsx              # NEW · isValidSubtab + render placeholder
└── [...slug]/                    # F1-S7 T-5 stub
    └── page.tsx                  # DELETE
```

### 9.2 — `proxy.ts` matcher pattern (verbatim Next.js 16 + Clerk 2026)

```ts
// vitalia/frontend/src/proxy.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/marketing(.*)',           // landing pública
  '/public/(.*)',              // landing agendamiento per clínica
  '/__clerk/(.*)',             // Clerk auth proxy interno
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Match all routes except _next, static files, well-known
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
    '/__clerk/(.*)',
  ],
};
```

### 9.3 — Tenant validation server-side (en `(shell-organism)/layout.tsx`)

```ts
// app/[tenantId]/(shell-organism)/layout.tsx — MODIFY F1-S9
import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { fetchUserTenants } from '@/lib/iam/api';

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}

export default async function Layout({ children, params }: LayoutProps) {
  const { tenantId } = await params;
  const { userId } = await auth();
  if (!userId) redirect('/sign-in');   // defense-in-depth (proxy ya lo hace)

  let tenants;
  try {
    tenants = await fetchUserTenants(userId);  // BE call → GET /api/v1/iam/me/tenants (core auth_router)
  } catch (err) {
    // Network failure — render fallback inline (ver § 6.3)
    return <NetworkErrorFallback />;
  }

  // Edge case Q6: user autenticado en Clerk pero sin tenants asignados en BE.
  // Política: sign-out + mensaje "Contactá a tu admin" (NO /onboarding/wizard, ese es post-sign-up).
  // Creación de tenants/users vive en admin Streamlit (memoria 2026-05-25).
  if (tenants.length === 0) {
    // Audit log + sign-out + redirect a sign-in con flag
    await logNoTenantsAssigned({ userId });
    redirect('/sign-out?next=/sign-in?error=no_tenants_assigned');
  }

  const isValidTenant = tenants.some(t => t.id === tenantId);
  if (!isValidTenant) {
    // Audit log + redirect al primer tenant válido
    await logCrossTenantAttempt({ userId, attemptedTenant: tenantId });
    redirect(`/${tenants[0].id}/valeria/agenda`);
  }

  return <ShellOrganismLayout tenantId={tenantId}>{children}</ShellOrganismLayout>;
}
```

### 9.4 — `agent-catalog.ts` EXTEND (validators)

```ts
// vitalia/frontend/src/lib/agent-catalog.ts — EXTEND F1-S9
export function isValidAgent(slug: string): slug is RibbonTabSlug {
  return slug in AGENT_CATALOG || slug === 'config';
}

export function isValidSubtab(agent: RibbonTabSlug, subtabSlug: string): boolean {
  const subtabs = RIBBON_SUBTABS[agent];
  return subtabs.some(st => st.id === subtabSlug);
}
```

### 9.5 — `[agent]/page.tsx` redirect default

```ts
// app/[tenantId]/(shell-organism)/[agent]/page.tsx — NEW
import { redirect, notFound } from 'next/navigation';
import { AGENT_CATALOG, isValidAgent, type RibbonTabSlug } from '@/lib/agent-catalog';

interface PageProps {
  params: Promise<{ tenantId: string; agent: string }>;
}

export default async function AgentRootPage({ params }: PageProps) {
  const { tenantId, agent } = await params;
  if (!isValidAgent(agent)) notFound();
  const defaultSubtab = AGENT_CATALOG[agent as RibbonTabSlug].defaultSubtab;
  redirect(`/${tenantId}/${agent}/${defaultSubtab}`);
}
```

### 9.6 — `[agent]/[subtab]/page.tsx`

```ts
// app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx — NEW
import { notFound } from 'next/navigation';
import { isValidAgent, isValidSubtab, type RibbonTabSlug } from '@/lib/agent-catalog';

interface PageProps {
  params: Promise<{ tenantId: string; agent: string; subtab: string }>;
}

export default async function SubtabPage({ params }: PageProps) {
  const { tenantId, agent, subtab } = await params;
  if (!isValidAgent(agent) || !isValidSubtab(agent as RibbonTabSlug, subtab)) {
    notFound();
  }
  // F1-S10 reemplazará este placeholder por <SubTabContent>
  return (
    <div className="flex items-center justify-center h-full text-muted-foreground">
      <p>Contenido próximamente — F1-S10 empty-states</p>
    </div>
  );
}
```

---

## § 10 — Microcopy (Spanish neutro LatAm)

| Lugar | Copy |
|---|---|
| `not-found.tsx` outer · ícono | 🔍 (emoji) |
| `not-found.tsx` outer · título | "No encontramos esta vista" |
| `not-found.tsx` outer · descripción | "Quizás el enlace está roto o el agente que buscas no existe en esta clínica." |
| `not-found.tsx` outer · CTA | "Volver al inicio" |
| `not-found.tsx` inner · ícono | 🔍 (emoji) |
| `not-found.tsx` inner · título | "No encontramos esa vista dentro de {AGENT_LABEL}" |
| `not-found.tsx` inner · descripción | "Quizás el enlace está roto o esa sub-pestaña no existe." |
| `not-found.tsx` inner · CTA | "Ir a la vista principal de {AGENT_LABEL}" |
| Network error · título | "Estamos teniendo problemas conectando con el servidor" |
| Network error · descripción | "Intenta de nuevo en unos segundos." |
| Network error · CTA | "Reintentar" |
| Sign-in error `no_tenants_assigned` · título | "Tu cuenta no tiene clínicas asignadas" |
| Sign-in error `no_tenants_assigned` · descripción | "Contactá al administrador de tu clínica para activar tu acceso." |
| Sign-in error `no_tenants_assigned` · CTA | "Volver a iniciar sesión" |
| `document.title` shell | "Vitalia · {AgentLabel} · {SubtabLabel}" (ej. "Vitalia · Valeria · Agenda") |
| `document.title` not-found | "Vitalia · Página no encontrada" |
| `document.title` network error | "Vitalia · Sin conexión" |

**Spanish neutro check:** NO voseo. NO regional. Tildes + ñ + apertura ¿!.

---

## § 11 — Responsive breakpoints

| Breakpoint | Comportamiento |
|---|---|
| Mobile (< 768px) | `not-found.tsx` outer mantiene centrado · CTA full-width · ValeriaSidebar drawer · Ribbon scroll horizontal |
| Tablet (768-1024px) | shell 50/50 ajustado · Ribbon comprimido (ícono solo en Mateo + Config) |
| Desktop (≥ 1024px) | shell 50/50 default · Ribbon labels full |

Routing en sí es responsive-agnostic (es server-side). Estados visuales no-found heredan responsive del shell layout.

---

## § 12 — Accessibility

- `not-found.tsx` outer: `<main role="main">` con tabindex programático para focus inicial al ícono
- `not-found.tsx` inner: skip-link respetado (heredado root layout)
- Screen reader: `<title>` change anuncia route change (Next.js 16 default + verificado en SC-6)
- Keyboard nav: Tab order = TopBar → TenantSwitcher → UserMenu → Ribbon (roving tabindex per F1-S7) → SubTabsBar (roving per F1-S8) → content
- Contraste: heredado tokens F1-S1 (≥ 4.5:1 garantizado por design tokens)
- `not-found.tsx` ícono `<span aria-hidden="true">🔍</span>` + texto descriptivo separado
- Focus visible: `focus:ring-2 focus:ring-primary` aplica vía Shadcn Button default

---

## § 13 — Telemetría (opcional)

```yaml
events:
  - { name: "shell_default_landing", trigger: "redirect post-login", props: ["tenantId", "agent_landed"] }
  - { name: "shell_route_change", trigger: "client-side nav", props: ["agent_prev", "agent_next", "subtab_prev", "subtab_next"] }
  - { name: "shell_not_found_outer", trigger: "invalid agent slug", props: ["attempted_slug"] }
  - { name: "shell_not_found_inner", trigger: "invalid subtab dentro agent válido", props: ["agent", "attempted_subtab"] }
  - { name: "shell_cross_tenant_attempt", trigger: "user fuera de tenant URL", props: ["user_id", "attempted_tenant"] }
  - { name: "shell_network_error_fallback", trigger: "tenant fetch failure", props: ["error_code"] }
```

(Telemetry wireing NO en F1-S9 — anotar TODO Fase 2. Events list ya cementada para que F2 cablee directo.)

---

## § 14 — Brand voice

UI chrome puro (no contenido per tenant) → Spanish neutro estándar. No aplica `personality_profiles.system_instruction`.

---

## § 15 — HIPAA-lite considerations

- Routing per se NO toca PHI. ✅
- `proxy.ts` NO loguea body request (matcher excluye `/api/*` del Clerk auth chain — Clerk maneja headers). ✅
- Cross-tenant attempt log en audit_log incluye solo `user_id` + `attempted_tenant_id` + `ip` + `timestamp` — NO PHI. ✅
- Tenant validation server-side via BE call con `Authorization: Bearer {clerk_token}` header — encrypted in transit. ✅
- `not-found.tsx` NO muestra PHI fields aunque user llegue por link malformado. ✅

---

## § 16 — Legacy cleanup checklist (★ Chris dictum 2026-05-25 — "no legacy en pre-prod")

| Item | Acción | Verificación post-merge |
|---|---|---|
| `app/(dashboard)/{offers,bookings,appointments,brand-studio,fidelizacion,medical-compliance,patients,treatments}/**` | `rm -rf` | `find app/\(dashboard\)` retorna vacío |
| `app/(app)/inbox/**` | `rm -rf` | idem |
| `app/(app)/` dir vacío | `rmdir` | idem |
| `app/(dashboard)/` dir vacío | `rmdir` | idem |
| E2E specs apuntando a `(dashboard)` | Eliminar specs legacy + POMs (`fidelizacion.page.ts`, refs en visual-smoke, mobile-smoke, a11y-smoke, dev-stack-baseline) | `grep -rln "(dashboard)" vitalia/frontend/e2e` retorna vacío |
| `capabilities/dashboard/welcome-state.yaml` | `git rm` | Archivo no existe + Q9 audit cita razón "no re-implementado en Fase 2" |
| 6 capabilities mixtas (booking, compliance, brand_studio, offer_studio, patients, treatments) | MODIFY: remover `+ vitalia/frontend/src/app/(dashboard)/...` del `package_path` + agregar `fe_planned_phase2: vitalia-fase2-{story}` field. NO cambiar `status: live`. | `grep -rln "(dashboard)" capabilities/` retorna vacío salvo platform/shell-foundation que no tiene path legacy |
| BE backend para esas features | NO TOCAR (sigue vivo, Fase 2 lo re-cablea al shell) | `vitalia/backend` sin cambios excepto montaje `auth_router` core |
| Database tables, seeds, fixtures | NO TOCAR (data layer intact) | idem |

**Mapping URL legacy → URL shell-organism (referencia Fase 2):**

| Legacy | Shell-organism (Fase 2 target) |
|---|---|
| `/(dashboard)/offers` | `/[tenantId]/lisa/servicios` (F2-S9) |
| `/(dashboard)/bookings` | `/[tenantId]/valeria/agenda` (F2-S1) |
| `/(dashboard)/appointments` | `/[tenantId]/valeria/agenda` (F2-S1) |
| `/(dashboard)/patients` | `/[tenantId]/valeria/pacientes` (F2-S2) |
| `/(dashboard)/treatments` | `/[tenantId]/valeria/pacientes` (F2-S2, sub-vista) |
| `/(dashboard)/brand-studio` | `/[tenantId]/lisa/marca` (F2-S7) |
| `/(dashboard)/medical-compliance` | `/[tenantId]/lisa/compliance` (F2-S10) |
| `/(dashboard)/fidelizacion` | `/[tenantId]/camila/voz` (F2-S11) |
| `/(app)/inbox` | `/[tenantId]/adrian/inbox` (F2-S3) |

(Esta tabla NO se implementa como redirect 308 — quedan 404 hasta Fase 2 trae cada feature. Dev-only environment, no usuarios reales aún. Si Chris ratifica diferente → bump po_ux_version.)

---

## § 17 — Acceptance criteria (sumario)

| AC | Verificación | Scenario |
|---|---|---|
| AC-1 | `/{tenant}/(shell-organism)/` redirige a `/{tenant}/valeria/agenda` | SC-1 |
| AC-2 | `/{tenant}/{agent}` redirige a `/{tenant}/{agent}/{defaultSubtab}` (6 agents × 1 default = 6 redirects) | SC-1 |
| AC-3 | URL inválida (`/{tenant}/foo`) → outer not-found 404 sin chrome | SC-2 |
| AC-4 | URL subtab inválido (`/{tenant}/camila/foo`) → inner not-found 404 con chrome | SC-3 |
| AC-5 | Sin sesión Clerk → proxy redirige a `/sign-in` | SC-1 (precondición) |
| AC-6 | User cross-tenant attempt → redirect al primer tenant válido + audit log | SC-4 |
| AC-7 | BE timeout fetch tenants → network error fallback + Reintentar | SC-5 |
| AC-8 | 22 sub-tab combos válidas navegables sin error | SC-1 + e2e completo |
| AC-9 | `document.title` actualiza per route | SC-1 |
| AC-10 | Ribbon + SubTabsBar active state sincronizado con URL | SC-1 |
| AC-11 | Keyboard nav + screen reader anuncia cambios de página · WCAG 2.1 AA | SC-6 |
| AC-12 | Todo microcopy Spanish neutro (no voseo, no regional) | SC-7 |
| AC-13 | `app/(dashboard)/`, `app/(app)/` eliminados completos · 5 specs E2E legacy eliminados/refactorizados | § 16 |
| AC-14 | `welcome-state.yaml` eliminado + 6 capability YAMLs modificados (path BE-only + `fe_planned_phase2`) + `platform/shell-foundation` intacto | § 16 |
| AC-15 | NO middleware.ts en repo · sí proxy.ts en `vitalia/frontend/src/` | grep |
| AC-16 | `agent-catalog.ts` EXTEND con `isValidAgent` + `isValidSubtab` exports | grep + type-check |
| AC-17 | `vitalia/backend/main.py` monta `auth_router` core (pattern nicolify/main.py:92) — `GET /api/v1/iam/me/tenants` accesible | curl + e2e |
| AC-18 | FE service `lib/iam/api.ts::fetchUserTenants(userId)` consume endpoint core — NO duplica logic | grep |
| AC-19 | Edge case user sin tenants → sign-out + `/sign-in?error=no_tenants_assigned` con mensaje "Contactá a tu admin" | e2e mockea response BE `{tenants: []}` |

---

## § 18 — Estimated dev days

- Setup proxy.ts + Clerk wiring + validators: **0.5d**
- Pages routing (`[agent]/[layout,page,not-found].tsx` + `[subtab]/page.tsx` + outer not-found): **0.5d**
- Tenant validation server-side + network error fallback: **0.5d**
- E2E Playwright suite (7 scenarios + axe scan + i18n scan): **1d**
- Legacy cleanup (delete dirs + refactor 5 specs + capabilities YAMLs): **0.5d**

**Total: 3 días dev** (re-estimado desde 1d original post scope expansion).

---

## § 19 — Próximo paso post-done

**F1-S10 vitalia-fase1-empty-states** implementa `SubTabContent` + `EmptyState` + `PlaceholderCard` para reemplazar el placeholder inline de F1-S9 `[agent]/[subtab]/page.tsx`. Sin F1-S9 done, F1-S10 no tiene routing donde insertar contenido.

Después de F1-S10 done → Fase 1 cerrada → arrancan stories Fase 2 (22 stories, 1 por sub-tab).
