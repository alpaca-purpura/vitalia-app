# 07-merge — vitalia-bugfix-root-login-redirect-softnav

**Merged:** 2026-06-15 · **type:** bugfix · **cap:** auth.clerk-middleware (change_type: fix)
**chris_verify:** SATISFIED (Chris, 2026-06-15 — login cae directo en Mateo sin colgarse, live)

## Qué se arregló
Tras login, la app se colgaba en `/` ("rendering" en consola Next), había que refrescar para ver
Mateo. Root cause: `app/page.tsx` (root `/`) hacía `redirect()` in-render → soft-nav al route group
`(shell-organism)` `ssr:false` → "Rendered more hooks" (Next 16, ~40% flake). Mismo bug-class que
bug#1 (bare-tenant), pero el caso root `/` había quedado sin edge-ificar.

Fix: edge-redirect 307 en `proxy.ts`, scoped HARD a `pathname==='/'` autenticado →
`/{tenant}/mateo/agenda`, ANTES de renderizar `app/page.tsx` (mata el soft-nav). Tenant resuelto via
`clerkClient().getUser().publicMetadata.tenant_id` (edge-safe, mismo patrón que `resolveClinicId`).
`app/page.tsx` queda como fallback. `ssr:false` del shell sin tocar.

## Commits
- `a4345e74` — edge-redirect root `/` en proxy.ts + helpers shell-routes + tests + Playwright guard.

## Verificación
- Playwright real-backend 8/8 determinístico (root `/` → mateo/agenda, shell montado, 0× "Rendered
  more hooks"), adjacent bug1 e2e 4/4 (sin regresión). tsc 0, eslint 0, vitest 2436, arch 31.

## Cap ledger
`auth/clerk-middleware.yaml` — change_log append type=fix (sin scenarios nuevos).

## Nota cross-brand
nicolify/comunify probablemente tengan el mismo patrón (shell ssr:false + root redirect). Candidato
a lift del helper edge-redirect (`/pm-luana`) — flagueado, no incluido en esta story.
