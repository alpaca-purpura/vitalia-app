---
brand: platform
date: 2026-06-03
slug: next16-softnav-redirect-rendered-more-hooks
promotable: candidate
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo]
tags: [nextjs16, app-router, redirect, ssr-false, dynamic-import, rendered-more-hooks, shell-organism, routing, edge-redirect, middleware, flaky]
origen: "story vitalia-bugfix-shell-nav-scroll-errors bug#1 · 2026-06-03"
ratified_by: chris
---

# Next 16 `redirect()` intra-route-group hacia layout `ssr:false` → "Rendered more hooks" (flaky)

## Qué aprendimos

Un **Server Component `redirect()`** que hace **soft-navigation DENTRO del mismo route group**
hacia una ruta cuyo layout usa `dynamic(..., { ssr:false })` **dispara `Rendered more hooks
than during the previous render` en el Router INTERNO de Next.js 16.2.3** (no en tu componente).
Es **flaky** (~40% en el caso vitalia) porque depende del timing de la transición + la
rehidratación de stores.

- **No es código tuyo.** El stack apunta a `at useMemo … at Router (next/dist/client/…)` —
  es el Router de Next, no un hook de la app. Los hooks de la app pueden estar 100% correctos.
- **No es "artefacto de build".** Con build limpio (deps presentes, `next dev` sano) el error
  **persiste intermitente**. Atribuirlo a "deps stale del container" fue el diagnóstico
  ERRÓNEO heredado que costó una sesión (ver caso origen).
- **Navegación dura NO lo dispara.** Ir directo a la URL destino (hard load) o cruzar route
  groups monta el Router fresco → limpio. Solo la **soft-nav intra-group** (layout compartido)
  lo trippea.
- **Lo expone un cambio de target de redirect:** vitalia redirigía `/{tenant}` →
  `valeria/agenda` (404, árbol liviano, no trip); al corregirlo a `mateo/agenda` (ruta real
  pesada con shell `ssr:false`) el bug latente quedó al descubierto.

## Cómo detectarlo

1. `pageerror: Rendered more hooks…` + stack con `at Router (next/dist/client/…)` → framework, no tu componente.
2. Flaky + dependiente de la transición (pasa al redirigir, no al navegar directo).
3. El landing queda colgado en la URL origen (la transición no completa) en vez de aterrizar.
4. Medí la tasa: corré el flujo N veces (`--repeat-each`) — un hook-bug real de la app sería 100% determinista; este es intermitente.

## Cómo arreglarlo (workaround robusto)

Hacé el redirect de **default-landing en el EDGE** (`middleware`/Next 16 `proxy.ts`, HTTP 307)
en vez de un `redirect()` in-render del Server Component. El 307 hace que el browser pida la
ruta destino con un **fetch fresco** → el Router monta limpio → sin soft-nav intra-group.

```ts
// proxy.ts (Next 16) / middleware.ts
const BARE_TENANT_PATH = /^\/([0-9a-f-]{36})\/?$/i;   // UUID-only: no toca sign-in/sign-out/marketing
export const proxy = clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) await auth.protect();
  const m = request.nextUrl.pathname.match(BARE_TENANT_PATH);
  if (m) return NextResponse.redirect(new URL(`/${m[1]}/${DEFAULT_LANDING_SUBPATH}`, request.url));
});
```

Matcher **acotado** (UUID/identificador específico) para no atrapar rutas de auth/públicas.
Dejá el Server Component `redirect()` como defensa para casos no cubiertos por el matcher.

## Aplicación cross-brand

Cualquier brand con **shell agéntico `ssr:false` + redirect de landing** está expuesta:
- **vitalia** (este caso) — `ShellOrganismLayoutClient` vía `dynamic({ssr:false})`.
- **nicolify / comunify** — usan shells de Luana-orquestador parecidos (`ssr:false`). Al cablear
  su routing de landing, usar **edge-redirect**, NO `redirect()` in-render intra-group.

## Caveat

Es un **workaround del trigger**, no un fix del bug de framework. Soft-navs profundas DENTRO
del route group (ej. navegar entre sub-tabs pesadas) podrían reaparecer. Si vuelve: misma
firma de stack → considerar (a) subir versión de Next si hay fix upstream, (b) reducir el
`ssr:false` del layout, o (c) más edge-redirects. Trackeá la versión de Next al revisar.

## Referencias

- Caso origen: `vitalia/docs/archive/2026/stories/vitalia-bugfix-shell-nav-scroll-errors/` (07-merge § Corrección root-cause bug#1)
- Fix: `vitalia/frontend/src/proxy.ts` + `src/lib/shell-routes.ts::bareTenantLandingRedirect`
- Relacionado: `[[verification-real-not-200]]`, `[[e2e-seeded-state-masks-cold-start]]` (el flake lo cazó la live-verify, no la suite verde)
