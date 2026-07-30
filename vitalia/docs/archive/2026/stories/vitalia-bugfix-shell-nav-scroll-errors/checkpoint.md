---
story_id: vitalia-bugfix-shell-nav-scroll-errors
type: bugfix

# Release entity (contenedor temporal · lifecycle.md § 5)
release: F2

# Capability lineage (v2 cement 2026-05-27)
cap_target: null                                  # no es una cap única — higiene UX cross-cap del shell-organism
cap_change_type: fix                              # bugfix → fix (corrige comportamiento del shell · no agrega scenarios nuevos de negocio)
parent_story: null

state: done
phase_workflow: MERGED
module: shell
last_artifact: checkpoint.md (re-audit APPROVED · 6/6 live dev-app · SOLO falta demo_signoff Chris · sesión 2026-06-03)
last_modified: 2026-06-03T12:25:00-05:00
next_action: "★ ROOT-CAUSE bug#1 corregido (ver § Corrección root-cause bug#1). El 'agenda Rendered more hooks' del handoff NO era artefacto de build — era una soft-navigation de Next.js 16.2.3 al hacer redirect intra-route-group, expuesta por bug#1. Flake real ~40% en /{tenant}. FIX: edge-redirect en proxy.ts (commit 1d2a58b5) → 2/5→0/5 crashes, bug1 x5 limpio. + widget tsc env-fix (aeebe007). Pendiente para done: (1) rework 6 e2e specs hybrid→real-backend [builder-frontend EN CURSO]; (2) /auditor; (3) demo_signoff Chris (gate negocio); (4) /pm-vitalia merge. El deps-churn del container + Clerk brittle + el version-skew vite/vitest del lockfile-regen = dominio story estabilizar-harness-e2e-lisa-marca."
chrome_mcp_setup: "registrado user-scope (~/.claude.json) headful + persistent profile · Connected en CLI · PERO tools NO cargaron en sesión resumida (quirk: resume ≠ full restart). Live-verify se hizo vía Playwright real-backend en su lugar."
# DoD #37 (ADR-vitalia-008) — live-verify técnico LOGRADO (6/6 testables); falta demo_signoff Chris
dev_app_verified:
  required: true
  dod_live_verified: true                          # real stack + real Clerk auth + real backend (NO mock) — ver VERIFICATION-FINDINGS.md § RE-VERIFICACIÓN
  env: "localhost:3002 (FE container, sirve este worktree) + real BE :8002 via real-backend-forward.fixture · spec e2e/regression/shell-nav-scroll/_live-verify.spec.ts · exit 0, 7 passed + 1 flaky(retry-pass)"
  evidence:
    - "Bug #1: /{tenant} → URL termina /mateo/agenda (no 404) · console limpio · ★ ahora vía edge-redirect en proxy.ts (commit 1d2a58b5): 0/5 crashes en /{tenant}, bug1 x5 limpio. ANTES (Server Component redirect intra-group) flakeaba ~40% con 'Rendered more hooks'"
    - "Bug #1b: /{tenant}/valeria/agenda → 404 contextual"
    - "Bug #2: tenant-switcher-trigger visible con 1 tenant · ★ CORREGIDO 2026-06-03: NO funcionaba live (useTenants pegaba a /api/tenants → 404 en el stack real → selector oculto; el e2e viejo lo enmascaraba con activeTenant sembrado por storageState). FIX: useTenants → /api/v1/iam/users/me/tenants (commit b2d1dfd4). Verificado LIVE dev-app cold-start: clear activeTenant → reload → GET /me/tenants 200 → selector 'Sanaré LATAM' visible (único call = /me/tenants, cero /api/tenants)"
    - "Bug #3: ruta placeholder → 0 subtab-header-* (SubTabHeader removido)"
    - "Bug #4: app-panel-slot content overflow-y = auto (scrolleable)"
    - "Bug #5: Presencia → 0 'Editor de landing pública'"
    - "Bug #7: error boundary [agent]/error.tsx presente+wired (code-verified · live-trigger NO ejercido)"
  agenda_hooks_resolved: "★ CORREGIDO 2026-06-02 noche: el 'Rendered more hooks' NO era artefacto de build (build limpio, error persistía intermitente ~40% en /{tenant}). ROOT CAUSE REAL: Next.js 16.2.3 tira el error en su Router interno (useMemo) cuando un Server Component redirect() hace soft-navigation DENTRO del mismo route group (shell-organism) hacia la ruta pesada con dynamic({ssr:false}). Stack: 'at Router (next/dist/client/...)' — framework, no código vitalia, no features/mateo. Bug#1 lo expuso al cambiar target valeria/agenda(404 liviano)→mateo/agenda(real pesado). FIX en proxy.ts (edge 307, evita la soft-nav)."
  env_fix_applied: "container node_modules stale (sonner/react-window/react-hook-form) → pnpm install in container + restart FE. Dominio real: story estabilizar-harness-e2e-lisa-marca"
demo_required: true
demo_signoff:                                       # ★ DoD #37 §5 · gate de negocio — FIRMADO Chris
  signed_by: Chris
  date: 2026-06-03
  result: APPROVED
  notes: "Verificó los 6 bugs en vivo contra dev-app.vitalialat.com. Todos OK. Incluye bug#2 (selector tenant 'Sanaré LATAM') tras el fix /me/tenants."
  open_items: []
build_summary:
  commits:
    - "132d17f6 fix(vitalia) 32 files (los 6 fixes)"
    - "98061462 docs(vitalia) ready package"
    - "1d2a58b5 fix(vitalia-bugfix-shell) edge-redirect proxy.ts (root-cause real bug#1 · Next 16 soft-nav)"
    - "aeebe007 chore(vitalia-fe) excluir widget/vite.config.ts del tsc app (env-hygiene lockfile-skew)"
    - "80ebdba5 docs(vitalia-bugfix-shell) corrección root-cause + nota env skew"
    - "3dc7982e test(vitalia-bugfix-shell) rework 6 e2e specs hybrid-mock → real-backend (builder-frontend)"
    - "b2d1dfd4 fix(vitalia-bugfix-shell) bug#2 selector real — useTenants → /me/tenants (live-verify dev-app descubrió /api/tenants 404)"
  gates_green:
    - "tsc 0 source err (post widget exclude)"
    - "eslint clean (6 specs + src)"
    - "arch_fsd 171/171"
    - "fe_unit_shell 652/652"
    - "fe_unit_lisa_marca 92/92"
    - "shell-routes/proxy unit 15/15"
    - "e2e_shell_runtime_error_gate 15/15 LIVE (anti-burbuja real · :3002+:8002)"
    - "backend_log_clean ✅ (404 marca ≠ traceback)"
  gates_gap:
    - "fe_knip_deadcode: knip NO instalado (no está en package.json — env gap, NO de esta story). El riesgo que cubría (orphan _fixture.ts) está resuelto: _fixture.ts borrado vía git rm en 3dc7982e. Auditor: no fallar por tool ausente."
  fixes_applied: 6                                 # T-1..T-6 + hardening bug#1 (proxy edge-redirect)
  e2e_status: "rework hybrid-mock → real-backend DONE (commit 3dc7982e) + validado LIVE 15/15 por orchestrator. _fixture.ts borrado. _live-verify.spec.ts queda como dod-evidence manual."
observed_separate_bugs:
  - "mateo/agenda 'Rendered more hooks than during the previous render' (pre-existente, NO de este fix — shell layout limpio en presencia)"
  - "backend 404 /api/v1/lisa/marca/{visuals,identity,contact} para test tenant"
  - "lisa/staff StaffDirectoryHeader h1 'Staff' = mismo patrón Bug #3 → lisa-doctores (non-egoísmo)"
ratified_by_chris: true
ratified_at: 2026-06-02T19:47:20-05:00
ratified_note: "Bugfix lite (ADR-011): checkpoint body = spec-lite ratificado. Chris eligió /architect directo (skip /po) en chris-input 2026-06-02. Scope = 6 bugs shell. NO construye sub-tabs nuevas → ADR-003/004 build gates NO aplican; los fixes PRESERVAN el patrón ADR-vitalia-004 existente."
architecture_pattern: ADR-vitalia-004              # fixes preservan el patrón del shell existente (no construye sub-tab nueva)
autonomous_mode: true                              # PROPUESTO architect · RATIFICADO Chris ("solucionarlos hasta el done" 2026-06-02). Ceiling: done exige demo_signoff Chris (DoD #37 §5)
ready_package:
  - 03-arch.md          # mapa causa raíz por bug (6/6 validados leyendo código)
  - 04-validators.yaml  # gates + scenario_coverage + business_rules + playwright_visual_scope + demo_required
  - 05-guidelines.md    # files in scope + must_load_skills + patterns
  - 06-tickets.yaml     # T-1..T-6 + assignment per ticket
  - dispatch-plan.md    # autonomous_mode + matrix + DAG
spawned_at: 2026-06-02T19:29:12-05:00
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: null
audit_iterations: 2                              # iter1 APPROVED (quedó stale por bug#2 roto live) · iter2 RE-AUDIT del delta bug#2 (b2d1dfd4) APPROVED 2026-06-03: 5 gates green + endpoint user-scoped /me/tenants (no admin leak) + no orgId + city opt backward-compat + cold-start spec ejerce el fetch real
audit_verdict: APPROVED                          # técnico (re-auditado) · falta SOLO demo_signoff Chris (gate negocio §5) para merge
defer_audit: false
defer_audit_reason: null
parked_reason: null
dropped_reason: null

# Paradigm v4 — zona/caja (rule paradigm-arquitectura.md · Critical #36)
# Shell-organism = superficie transversal de la ZONA PLATAFORMA (chasis que envuelve a los agentes).
# Bug #1 (routing) + #4 (scroll) + #7 (error-boundary) = enforcement de usabilidad del chasis.
# Bug #2 (tenant selector) = Acceso/Configuración transversal. #3/#5 = higiene visual del chasis.
paradigm_zone: plataforma
paradigm_caja: configuracion                       # chasis transversal (acceso/onboarding/config comparten el shell)

# Bugfix repro-first gate (ADR-011 · hereda hotfix-repro-mandatory.md)
hotfix_metadata:
  repro_verified: false                            # Chris OBSERVÓ los 6 live en dev-app.vitalialat.com (evidencia abajo); repro LOCAL pendiente — /dev-team DEBE reproducir antes de spawn builder (gate ADR-011)
  repro_source: chris-live-observation-2026-06-02
  repro_env: "https://dev-app.vitalialat.com (autenticado · tenant e69a691d-070e-5caf-a053-6e74642ec100)"
  diagnosis_validates_handoff: pending             # diagnóstico por-bug abajo es HIPÓTESIS PM · /dev-team valida en repro local
# (dev_app_verified consolidado arriba — sección "# DoD #37 ... NO satisfecho aún")
---

# Bugfix — Shell-organism: routing post-login, selector de tenant, scroll, títulos, placeholder landing, error-boundary

> **Origen:** Chris ejerciendo dev-app.vitalialat.com live (2026-06-02), tenant
> `e69a691d-070e-5caf-a053-6e74642ec100`. 7 bugs reportados; **#6 (lisa/staff infinite loop)
> se folded a la story `vitalia-fase2-lisa-doctores`** (developing · dueña de esa superficie).
> Esta story cubre los **6 bugs del chasis shell-organism**.

> **Tipo `bugfix` (lite · repro-first · ADR-011):** puede saltar mockups/diseño de cero. El
> repro es la observación live de Chris; `/dev-team` reproduce local antes de tocar código.

---

## Bug #1 — Routing post-login lleva a ruta inexistente (404)

**Síntoma:** tras loguearse, redirige a
`/{tenantId}/valeria/agenda` → **esa ruta NO existe** → 404 / not-found.

**Hipótesis PM (a validar):** la ruta default post-login apunta a `valeria/agenda` pero
Valeria no tiene sub-tab `agenda` (agenda es de Mateo, ver `mateo/agenda/`). El default debe
apuntar a una ruta que SÍ exista (landing del shell o primer agente con sub-tab válida).

**Superficie:** `vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx` +
posible redirect en `app/page.tsx` / middleware / nav-tree default.

**Fix sugerido:** redirigir a una ruta válida garantizada (la home del shell o
`valeria/{primera-subtab-existente}`). Defensivo: validar que la ruta default exista en el
nav-tree antes de redirigir.

---

## ★ Corrección root-cause bug#1 (sesión 2026-06-02 noche · recon pre-auditor)

Al re-correr el live-verify de bug#1 en sesión nueva (DoD #37 — no confiar en el
"6/6" heredado), bug#1 **flakeaba ~40%** (`/{tenant}` 2/5) con un `pageerror:
Rendered more hooks than during the previous render`, dejando el landing colgado
en `/{tenant}` en vez de `mateo/agenda`. El handoff lo había descartado como
"artefacto de build roto (deps stale)" — **falso**: build limpio (sign-in 200,
deps presentes) y el error persistía intermitente.

**Diagnóstico (stack capturado):** el error se tira DENTRO del Router interno de
Next.js 16.2.3 (`at useMemo … at Router (next/dist/client/...)`), NO en código
vitalia ni en `features/mateo`. Causa: un Server Component `redirect()` que hace
**soft-navigation dentro del mismo route group `(shell-organism)`** hacia la ruta
pesada con `dynamic({ssr:false})` (ShellOrganismLayoutClient) → el Router
re-renderiza con un hook-count distinto. Nav **directa** (hard) a `mateo/agenda` =
limpia 3/3 → confirma que el trigger es la soft-nav del redirect. Bug#1 lo expuso
al cambiar el target de `valeria/agenda` (404, árbol liviano, no trip) a
`mateo/agenda` (ruta real pesada).

**El fix está EN la superficie de bug#1** (capa de redirect), NO en `features/mateo`:
mover el redirect de bare `/{tenant}` → `/{tenant}/mateo/agenda` del Server Component
al **edge** (`proxy.ts`, 307 HTTP) vía `bareTenantLandingRedirect()` en
`lib/shell-routes.ts`. El 307 hace que el browser pida la ruta destino con un fetch
fresco → el Router monta limpio → sin soft-nav. UUID-only match (no toca
sign-in/sign-out/marketing). Server Component redirect queda como defensa.

**Validación live:** `/{tenant}` 2/5 → **0/5** crashes; bug1 live-verify x5 limpio,
lands `mateo/agenda`. El entrypoint primario post-login (`/` → app/page.tsx →
`mateo/agenda`, cruza route groups) ya era limpio **5/5** (hard nav). Unit:
`shell-routes.test.ts` +4 tests de `bareTenantLandingRedirect`. Commit `1d2a58b5`.

**Caveat honesto:** es un *workaround* del bug de Next (evita el trigger), no un fix
del framework. Otras soft-navs intra-group podrían trip en el futuro → candidato a
learning cross-brand (Next 16 + shell `ssr:false`). Pendiente ratificar con Chris.

---

## Bug #2 — Selector de tenant no aparece con un solo tenant

**Síntoma:** el selector de tenant (parte superior) NO se muestra cuando el usuario tiene
**un solo tenant**. Debe aparecer **siempre**, aunque sea uno.

**Hipótesis PM:** `TenantSwitcher.tsx` / `TopBarGlobal.tsx` esconde el switcher si
`tenants.length <= 1`. Quitar esa condición → mostrar siempre (con un solo item =
estado read-only/badge, pero visible).

**Superficie:** `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx`
+ `TopBarGlobal.tsx` + `TenantBadge.tsx`.

---

## ★ Corrección root-cause bug#2 (sesión 2026-06-03 · live-verify dev-app pre-demo)

Verificando los 6 bugs en **dev-app.vitalialat.com** (Clerk real, Chrome MCP + docker
logs + network) descubrí que **bug#2 NO funcionaba live**: el `tenant-switcher-trigger`
estaba **ausente del DOM** y `activeTenant: null`.

**Diagnóstico (network + BE logs):** `useTenants` hacía `fetchClient("/api/tenants")`
→ en el stack real `/api/*`→BE:8002 → **404** (el BE NO tiene `/api/tenants`). Lista
vacía → `TenantSwitcher` retorna null (guard `availableTenants.length === 0`) → sin
selector. El endpoint real es `GET /api/v1/iam/users/me/tenants` (core/luana-core-iam
`auth_router` → `list[TenantSchema]`).

**⚠️ El e2e reworked TAMBIÉN lo enmascaraba:** pasaba bug#2 porque el `storageState`
sembraba un `activeTenant`, así que nunca ejercía el cold-start que pega a `/api/tenants`.
Es **otra vez** la trampa verificación-real-≠-200 (misma familia que el caso lisa-marca).
El "6/6 dod_live_verified" heredado estaba enmascarado en bug#1 **y** bug#2.

**Fix (commit b2d1dfd4) — Chris ratificó "fix acá":**
- `useTenants.ts` → `/api/v1/iam/users/me/tenants` (endpoint real) + `setAvailableTenants(query.data)` (array plano, no `.tenants`).
- `types.ts` → `Tenant` alineado al BE (`{id,name,slug?,role?,city?}`); `TenantsApiResponse` = array plano.
- `TenantOption.tsx` → `city` opcional (el endpoint real no la trae).
- `bug2 spec` → **cold-start honesto**: limpia el `activeTenant` persistido + navega `lucas/lanzar` (limpio, gate ON) → el selector solo aparece si `/me/tenants` puebla el store. Caza el bug que el e2e viejo no daba.

**Validación LIVE dev-app (cold-start):** clear `vitalia-tenant-state` → reload →
`GET /api/v1/iam/users/me/tenants` **200** → selector **"Sanaré LATAM"** visible
(`activeTenant` repoblado del fetch; único call de tenants = `/me/tenants`, cero
`/api/tenants`). Screenshot capturado. Gates: tsc 0 · eslint 0 · vitest **2502/2502** ·
arch 171/171 · e2e shell-nav-scroll **15/15**.

**Sistémico (separado, NO de esta story):** el live-verify también expuso otros gaps
de contrato FE↔BE pre-existentes en dev-app — `POST /api/telemetry/growth-studio-event`
→ 404, `GET /api/v1/scheduling/agenda/grid` → 422 (agenda SSR, degrada graceful).
Familia tenant-resolution / [[no-clerk-organizations]] "onboarding aún LEE org".
Candidatos a una story de contrato FE↔BE / IAM separada.

---

## Bug #3 — Títulos de hoja redundantes (eliminar en todas las hojas)

**Síntoma:** cada hoja muestra un título que duplica la opción ya marcada en la navegación.
No aporta — eliminar el título en **todas las hojas**.

**Superficie:** `shell-organism/SubTabContent.tsx` + páginas de sub-tab
(`(shell-organism)/[agent]/[subtab]/page.tsx`) — donde se renderiza el header/título de hoja.

**Fix sugerido:** remover el componente de título de hoja (o su render) de forma transversal.
Verificar que no rompa el layout (spacing) al quitarlo.

---

## Bug #4 — No se puede hacer scroll: contenido fijo, no se ve lo de abajo

**Síntoma:** estando en una hoja, no se puede desplazar hacia abajo — está fijo. Ni con la
rueda del mouse ni con barra de scroll (no aparece barra). En **todas las hojas**.

**Hipótesis PM:** el contenedor de contenido del `(shell-organism)/layout.tsx` tiene
`overflow: hidden` o altura fija (`h-screen` sin `overflow-y-auto` en el panel de contenido),
atrapando el contenido. El panel scrolleable debe tener `overflow-y-auto` + altura correcta.

**Superficie:** `vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx`
(+ `[agent]/layout.tsx` si anida).

**Severidad: ALTA** — bloquea ver contenido = bloqueante de usabilidad.

---

## Bug #5 — Eliminar recuadro "Editor de landing pública — próximamente" en Presencia

**Síntoma:** en la sección **Presencia** (Lisa) aparece un recuadro placeholder
"Editor de landing pública — próximamente". Eliminarlo.

**Superficie:** `shell-organism/SubTabContent.tsx` (placeholder de sub-tab no implementada)
o el contenido de la sub-tab Presencia/landing de Lisa.

**Nota scope:** quitar SOLO ese recuadro placeholder. NO construir el editor (eso es otra
story — `vitalia-fase2-lisa-landing-public`, en idea).

---

## Bug #7 — Al fallar algo, la navegación se bloquea (botones muertos)

**Síntoma:** cuando algo falla, ya no se puede navegar a ninguna parte — los botones quedan
como bloqueados. No tiene sentido.

**Hipótesis PM:** un error en un sub-árbol (ej. el infinite loop de bug #6, u otro throw)
escala y rompe el shell entero / el error boundary no aísla por panel → el chasis (sidebar +
nav) queda inutilizable. El error boundary debe aislar el fallo al panel de contenido y
mantener la navegación viva.

**Superficie:** error boundaries del shell (`(shell-organism)/.../error.tsx`) + estructura de
boundaries por panel. Hay `mateo/agenda/error.tsx` — verificar si hay boundary a nivel
shell que aísle el panel de contenido sin matar la nav.

**Severidad: ALTA** — un fallo aislado deja la app inusable. Relación causal con #6: el loop
de staff probablemente disparaba esto.

---

## Bar de verificación (DONE · DoD #37 — ejercer live, NO GET 200)

Por cada bug, ejercer la acción real en dev-app.vitalialat.com (autenticado) + leer console
(0 errores rojos, sin overlay Next) + confirmar efecto:

1. **#1** Login → aterriza en ruta que existe (no 404). Recargar mantiene ruta válida.
2. **#2** Con 1 tenant → el selector se ve en el topbar.
3. **#3** Ninguna hoja muestra título redundante. Layout sin huecos rotos.
4. **#4** Scroll funciona en una hoja con contenido largo (rueda + barra visible).
5. **#5** Presencia ya no muestra el recuadro "próximamente".
6. **#7** Forzar un error en un panel → la nav (sidebar/ribbon) sigue clickeable; el fallo
   queda aislado al panel de contenido.

## Notas de scope

- Solo FE de vitalia (`vitalia/frontend/src/`). No backend, no core, no otras brands.
- Módulo bucket: **shell** (distinto de `lisa` = lisa-doctores developing, y de la story
  e2e-harness developing) → WIP cap v2 module-scoped OK en paralelo.
- Anti-orphan (CONN): no crea superficies nuevas — corrige las existentes. Sin riesgo de isla.
- Bug #6 (lisa/staff infinite loop) NO está acá → folded a `vitalia-fase2-lisa-doctores`.
