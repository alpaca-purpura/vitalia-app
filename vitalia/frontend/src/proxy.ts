// cap: auth.clerk-middleware
// story-origin: TBD
/**
 * Clerk Proxy — Vitalia (T-1 vitalia-auth-base-functional)
 *
 * Next.js 16 renamed the `middleware` file convention to `proxy` (deprecation
 * v16.0.0). Same location (src/), same `config.matcher` API. The default export
 * is now named `proxy`. Clerk's `clerkMiddleware()` SDK helper is unchanged —
 * its name is historical, it just wraps a request handler that Next.js invokes
 * via the proxy convention.
 *
 * Protege todas las rutas excepto las explícitamente públicas.
 * Rutas públicas: sign-in, sign-up, landing pública por clínica,
 *   webhooks Clerk (BE los valida con HMAC), health check, marketing.
 *
 * Auth delegada 100% a Clerk — sin redirect manual ni RBAC.
 * auth.protect() redirige a /sign-in automáticamente si no hay sesión.
 *
 * SC-01: request sin sesión a ruta protegida → Clerk redirige a /sign-in
 * SC-02: request a /public/* → 200, sin redirect
 *
 * F1-S9 routing-shell: matcher polish + /marketing(.*) explicit
 */

import {
  clerkClient,
  clerkMiddleware,
  createRouteMatcher,
} from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

import {
  bareTenantLandingRedirect,
  isAuthedRootPath,
  rootLandingRedirect,
  shellInRenderRedirectTarget,
} from "@/lib/shell-routes";

/**
 * Resolves the user's tenant UUID from Clerk `publicMetadata.tenant_id` —
 * the SAME canonical source as the client `useTenantId()` + the server-side
 * `resolveClinicId()` in features/mateo/api/agenda-server.ts. Read via the
 * Clerk Backend API (clerkClient) because the dev JWT template does NOT inject
 * custom claims into sessionClaims (the agenda-actor-headers-422 fix proved the
 * claim path was empty). clerkClient uses HTTPS fetch → edge-runtime safe.
 *
 * Graceful: returns null on ANY failure (no tenant provisioned, Clerk API down,
 * non-string metadata) → the caller skips the 307 and lets the Server Component
 * `app/page.tsx` run its full fallback (fetchUserTenants → no_tenants_assigned /
 * network-error). The login flow is NEVER broken by this resolver.
 */
async function resolveTenantId(userId: string): Promise<string | null> {
  try {
    const client = await clerkClient();
    const user = await client.users.getUser(userId);
    const tenantId = (user.publicMetadata as Record<string, unknown>)[
      "tenant_id"
    ];
    return typeof tenantId === "string" && tenantId.length > 0
      ? tenantId
      : null;
  } catch {
    return null;
  }
}

const isPublicRoute = createRouteMatcher([
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/public(.*)",
  // F1-S9 routing-shell: matcher polish + /marketing(.*) explicit
  "/marketing(.*)",
  // Clerk internal routes (account portal, OAuth callbacks)
  "/__clerk/(.*)",
  "/api/v1/vitalia/webhooks(.*)",
  "/api/health",
  // F1-S0 visual baseline pages (dev-only preview, no auth required)
  // Used by Playwright @project=visual for goldens generation.
  // No expone datos sensibles — solo renderiza Shadcn primitives + agent tokens swatches.
  "/test-stack(.*)",
  // core-ds-foundation T-9: catalogo publico del design-system @luana/ui-kit.
  // Sin tenant, sin PHI — solo renderiza componentes con datos de ejemplo.
  "/showcase(.*)",
  // T-FE-pagina-publica (D3-D): página pública del doctor — no auth.
  // Anti-enumeration: BE returns identical 404 for toggle-OFF/unknown/cross-tenant.
  "/d/(.*)",
]);

export const proxy = clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect();
  }

  // Root-login hardening (vitalia-bugfix-root-login-redirect-softnav): Clerk
  // afterSignIn redirige client-side a "/". El Server Component app/page.tsx
  // hacía ahí un redirect() IN-RENDER hacia /{tenant}/mateo/agenda → soft-nav
  // intra route-group (shell-organism) cuyo layout es dynamic({ssr:false}) →
  // dispara "Rendered more hooks than during the previous render" en el Router
  // de Next 16 (~40% flake → render colgado hasta refrescar a mano). Mismo
  // bug-class que el landing bare-tenant de abajo, pero el caso root "/" (sin
  // tenant en la URL) quedó SIN edge-ificar. Acá lo movemos al EDGE (307): para
  // usuarios YA autenticados (auth.protect arriba mandó a sign-in a los
  // anónimos), resolvemos el tenant de publicMetadata.tenant_id (Clerk Backend
  // API — el JWT dev no trae el claim) y 307 a su landing. Si el tenant no
  // resuelve / no es UUID → NO redirige acá y deja que app/page.tsx haga su
  // fallback completo (fetchUserTenants → no_tenants_assigned / error de red).
  // Scope HARD a pathname === "/" (raíz exacta) — la resolución del tenant (una
  // llamada a Clerk) corre SOLO en ese caso, nunca en cada request.
  if (isAuthedRootPath(request.nextUrl.pathname)) {
    const { userId } = await auth();
    if (userId) {
      const tenantId = await resolveTenantId(userId);
      const target = rootLandingRedirect(tenantId);
      if (target) {
        return NextResponse.redirect(new URL(target, request.url));
      }
      // tenant no resuelto / no-UUID → cae a app/page.tsx (fallback defensivo).
    }
  }

  // Bug #1 hardening (vitalia-bugfix-shell-nav-scroll-errors): el redirect de
  // /{tenant} → /{tenant}/{DEFAULT_LANDING_SUBPATH} hecho por el Server Component
  // (shell-organism)/page.tsx queda DENTRO del mismo route group (shell-organism)
  // → Next.js 16.2.3 hace una soft-navigation parcial que dispara
  // "Rendered more hooks than during the previous render" en su Router interno
  // (~40% flake en navegación a /{tenant} bare; el landing queda colgado en
  // /{tenant} en vez de mateo/agenda). Hacer el redirect en el EDGE (307 HTTP)
  // elimina la soft-nav: el browser pide la ruta destino con un fetch fresco →
  // el Router monta limpio. Solo para usuarios ya autenticados (auth.protect
  // arriba ya mandó a sign-in a los anónimos). Server Component redirect queda
  // como defensa para tenants no-UUID (raro). Lógica de match en lib/shell-routes.ts.
  //
  // T-4 (vitalia-shell-core-hardening, Decisión A) — COVERAGE VERIFICADA: el
  // único redirect IN-RENDER intra-route-group del shell es este landing bare-
  // tenant; el 307 lo cubre. El flujo board→/adrian/recuperar (chip frozen-kpi)
  // NO necesita 307: /adrian/recuperar es una ruta estática real, sin redirect
  // in-render → su soft-nav (next/link) no dispara el "Rendered more hooks".
  // Por eso el band-aid hard-nav del chip se revirtió a next/link sin extender
  // este matcher. (grep `redirect(` en (shell-organism)/** = 0 fuera del landing.)
  const landingRedirect = bareTenantLandingRedirect(request.nextUrl.pathname);
  if (landingRedirect) {
    return NextResponse.redirect(new URL(landingRedirect, request.url));
  }

  // T-V2 (platform-lift-shell-chrome-ui-kit, 2026-06-11): la nota T-4 de arriba
  // ("el único redirect in-render es el landing") quedó FALSA — el censo del lift
  // encontró 4 redirect() in-render más (lisa/marca, [agent] bare, staff/[id],
  // embudo/[id]). Con el chrome consumido del kit el "Rendered more hooks" pasó
  // de flaky a determinista en esas rutas → TODOS al edge (307), mismo patrón.
  // Los page.tsx quedan como fallback defensivo. SSoT: lib/shell-routes.ts.
  const shellRedirect = shellInRenderRedirectTarget(request.nextUrl.pathname);
  if (shellRedirect) {
    return NextResponse.redirect(new URL(shellRedirect, request.url));
  }
});

export default proxy;

export const config = {
  matcher: [
    // Incluir todas las rutas excepto archivos estáticos Next.js y assets
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Incluir siempre rutas API y tRPC
    "/(api|trpc)(.*)",
  ],
};
