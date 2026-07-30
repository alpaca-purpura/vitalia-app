// cap: __shared__
// story-origin: TBD
/**
 * Root Landing — Server Component redirect (FALLBACK DEFENSIVO).
 * Post-merge fix (2026-05-27) — Clerk afterSignIn redirige a "/" por default,
 * y antes esta ruta devolvía 404. Esto rompía el flujo end-to-end manual:
 * usuario se loguea OK pero ve "This page could not be found".
 *
 * ★ vitalia-bugfix-root-login-redirect-softnav (2026-06-15): el HAPPY PATH del
 * root "/" autenticado se mueve al EDGE (proxy.ts → 307 a /{tenant}/mateo/agenda)
 * para eliminar el redirect() IN-RENDER de abajo, que soft-navegaba al route
 * group (shell-organism) [layout dynamic({ssr:false})] y disparaba el
 * "Rendered more hooks" de Next 16 (~40% flake → render colgado, requería
 * refresh). Este Server Component QUEDA como fallback defensivo: corre solo
 * cuando el edge NO pudo resolver el tenant (publicMetadata cold / tenant no-UUID
 * / Clerk API caída) → maneja los edge-cases (sin sesión, sin tenants, fetch
 * falla) con redirect() a sign-in, que es soft-nav inocua (sign-in NO está en el
 * route group del shell). SSoT del happy-path: lib/shell-routes.ts +
 * proxy.ts § Root-login hardening.
 *
 * Comportamiento:
 *   1. Si no hay sesión Clerk → redirect a /sign-in (defense-in-depth con proxy.ts).
 *   2. Si hay sesión + user tiene tenants → redirect a /{firstTenant.id}/{DEFAULT_LANDING_SUBPATH}
 *      (= mateo/agenda v1.2; antes valeria/agenda, que 404eaba — Bug #1
 *      vitalia-bugfix-shell-nav-scroll-errors T-1). SSoT en lib/shell-routes.ts.
 *   3. Si user no tiene tenants → redirect a /sign-in?error=no_tenants_assigned
 *      (SC-8 surface already implemented in sign-in/page.tsx).
 *   4. Si fetch tenants falla → redirect a /sign-in?error=no_tenants_assigned
 *      (graceful degradation — usuario ve mensaje administrativo).
 *
 * No "use client" — redirect() y auth() son Server Actions/server-only.
 *
 * downstream-regression-na: brand-local landing; no cross-brand consumers.
 */

import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { fetchUserTenants, IamApiError } from "@/lib/iam/api";
import { DEFAULT_LANDING_SUBPATH } from "@/lib/shell-routes";

export default async function RootLandingPage() {
  const { userId } = await auth();
  if (!userId) {
    redirect("/sign-in");
  }

  let tenants: Awaited<ReturnType<typeof fetchUserTenants>> = [];
  try {
    tenants = await fetchUserTenants(userId);
  } catch (err) {
    if (err instanceof IamApiError) {
      console.warn("[root-landing] fetchUserTenants failed:", err.code, err.message);
    } else {
      console.warn("[root-landing] fetchUserTenants unexpected error:", err);
    }
    redirect("/sign-in?error=no_tenants_assigned");
  }

  if (tenants.length === 0) {
    redirect("/sign-in?error=no_tenants_assigned");
  }

  redirect(`/${tenants[0].id}/${DEFAULT_LANDING_SUBPATH}`);
}
