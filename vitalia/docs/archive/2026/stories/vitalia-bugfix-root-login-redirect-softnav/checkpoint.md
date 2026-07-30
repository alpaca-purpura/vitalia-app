---
story_id: vitalia-bugfix-root-login-redirect-softnav
type: bugfix
architecture_pattern: ADR-vitalia-004
module: iam                                        # bucket code:iam (auth/proxy) — distinto de clinics/scheduling

release: F2

cap_target: auth.clerk-middleware
cap_change_type: fix
parent_story: null

state: done
phase_workflow: MERGED
last_artifact: T-1-result.md
last_modified: 2026-06-15
next_action: "G — Chris se loguea en dev-app y confirma que cae directo en Mateo sin colgarse/refrescar (signoff). Luego /pm-vitalia merge→done (cap change_log type=fix en auth.clerk-middleware). Fix: edge-redirect del root `/` en proxy.ts (307, tenant via clerkClient publicMetadata). Verificado live: Playwright 8/8 determinístico, 0× 'Rendered more hooks'."
ratified_by_chris: true
spawned_at: 2026-06-15
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: null
autonomous_mode: false

chris_verify:
  required: true
  signoff:
    by: Chris
    date: 2026-06-15
    result: SATISFIED
    notes: "Chris confirmó live (incognito fresco): tras login cae directo en Mateo, sin colgarse ni refrescar."
    open_items: []
  rounds: []

hotfix_metadata:
  repro_verified: true
  reproduced_local: true
  repro_command: "Login en dev-app → Clerk redirige client-side a `/` → app/page.tsx redirect() in-render a /{tenant}/mateo/agenda soft-navega al grupo (shell-organism) ssr:false → 'rendering' colgado en la consola Next, no avanza; refresh (hard nav) recién muestra Mateo. ~40% flake conocido (Next 16 'Rendered more hooks')."
  diagnosis_validates_handoff: true

dev_app_verified:
  required: true
  evidence:
    - action: "Navegar a `/` (raíz) autenticado ×8 contra stack dev real (localhost:3002, Clerk dr.demo@vitalialat.com, tenant e69a691d-…), simulando el afterSignIn"
      observed: "Las 8 corridas aterrizan determinísticamente en /{tenant}/mateo/agenda con main#main-content montado (shell vivo), SIN refresh manual. 0 × 'Rendered more hooks' (pageerror+console). Gate anti-burbuja base.ts verde."
      backend_log: "FE :3002 responde 307 en `/` (edge-redirect proxy.ts antes de app/page.tsx) · /api/v1/** forwardeadas al BE :8002 real sin 4xx/5xx tras la hidratación."
dod_live_verified: true
dod_evidence:
  - action: "Playwright real-backend root-login-lands-clean.spec.ts ×8 loop (smoke, localhost:3002, Clerk auth real)"
    observed: "3 passed (22.6s) — root '/' → mateo/agenda, shell montado, cero 'Rendered more hooks', cero error runtime"
    backend_log: "BE :8002 /health 200 · forwarding /api/v1 real-backend sin error · adjacent bug1 bare-tenant e2e 4/4 passed (sin regresión)"
verified_at: 2026-06-15
---

# Bugfix — post-login se queda colgado en `/` ("rendering"), hay que refrescar para ver Mateo

## Síntoma (Chris)

Tras loguearme se queda "pensando" con `rendering` en la consola de Next y NO avanza;
tengo que refrescar para que recién aparezca Mateo (la landing).

## Root cause (confirmado · patrón documentado)

`vitalia/frontend/src/app/page.tsx` (root `/`) es un Server Component que hace
`redirect(\`/${tenants[0].id}/${DEFAULT_LANDING_SUBPATH}\`)` (= `/{tenant}/mateo/agenda`)
post-login. Clerk (afterSignIn) redirige **client-side** a `/` → ese `redirect()` in-render
**soft-navega** al route group `(shell-organism)`, cuyo layout (`ShellLayoutWire` → `ShellLayout`)
es `dynamic({ssr:false})` → dispara **"Rendered more hooks than during the previous render"** en
el Router interno de Next 16 (~40% flake) → render colgado en `/`; el refresh = hard-nav, monta limpio.

**Mismo bug-class que el ya-fixeado `vitalia-bugfix-shell-nav-scroll-errors` (bug#1)** — pero ese
fix cubrió el caso **bare-tenant** (`/{tenant}` → landing) vía `proxy.ts` `bareTenantLandingRedirect`.
El caso **root `/`** (sin tenant en la URL, lo hace `app/page.tsx`) quedó SIN edge-ificar → sigue
in-render → sigue colgándose. Learning SSoT: `docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md`.

## Fix (FE · extender el patrón edge-redirect ya probado)

Mover el redirect `/` → `/{tenant}/{landing}` al **EDGE** en `proxy.ts` (307 HTTP), para usuarios
ya autenticados, igual que `bareTenantLandingRedirect`. Diferencia: el root `/` es **data-driven**
(necesita el primer tenant del usuario) → el middleware debe resolver el tenant (IAM
`fetchUserTenants`, server-side, con el token de Clerk del middleware) y 307 a
`/{firstTenant.id}/{DEFAULT_LANDING_SUBPATH}`. `/` es hit solo post-login (raro) → el costo del
fetch en middleware es aceptable. El `app/page.tsx` `redirect()` queda como **fallback** (defensa
para casos raros / tenant no-UUID). Preservar los edge-cases que ya maneja page.tsx: sin sesión →
sign-in (ya lo hace `auth.protect()`); sin tenants → `/sign-in?error=no_tenants_assigned`; fetch
falla → idem (graceful). NO cambiar el `ssr:false` del shell (está por diseño).

## Bar de verificación (DONE)

- Playwright real-backend (localhost:3002, auth dr.demo): login → **termina en `/{tenant}/mateo/agenda`
  con el shell montado, SIN refresh manual** (correr varias veces — el bug era ~40% flaky, el fix
  debe ser 100% determinístico). 0 × "Rendered more hooks" en consola.
- tsc + eslint + vitest verdes. Si el edge-redirect del root rompe algún test de routing → adaptarlo.
- Live (#37): Chris abre dev-app, se loguea → cae directo en Mateo sin colgarse. (Browser MCP caído →
  Playwright real cubre la conducta; Chris confirma manual el eyeball = signoff G.)
- `cap_change_type: fix` → append change_log type=fix a `auth.clerk-middleware`.

## Notas de scope

- Brand-local vitalia FE (`proxy.ts` + `app/page.tsx` + `lib/shell-routes.ts`). No core, no BE, no otras marcas.
- nicolify/comunify pueden tener el MISMO bug (mismo patrón shell ssr:false + root redirect) → si aplica,
  candidato a lift del helper de edge-redirect a un patrón compartido (escalar /pm-luana). Por ahora vitalia.
