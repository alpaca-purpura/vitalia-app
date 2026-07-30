// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s4-TBD
/**
 * Shell Organism Route Group Layout — Server Component.
 * F1-S9 vitalia-fase1-routing-shell — T-3
 *
 * 03-arch-fe.md § 2.1 — tenant validation server-side.
 *
 * Responsabilidades:
 *   1. Verificar sesión Clerk (auth() → userId). Sin sesión → /sign-in.
 *   2. Obtener lista de tenants del usuario (fetchUserTenants).
 *      Error de red → NetworkErrorFallback (SC-7).
 *   3. Sin tenants asignados → audit log + sign-out redirect (SC-8).
 *   4. tenantId de URL ∉ user.tenants → audit log + redirect al primer
 *      tenant válido (SC-4, SC-5).
 *   5. tenantId válido → render ShellOrganismLayout.
 *
 * No "use client" — Server Component obligatorio para auth() + redirect().
 * No metadata export — las páginas hijas son dueñas de su metadata.
 * Route group (shell-organism) no aparece en la URL.
 *
 * HIPAA-lite: audit log payload SOLO userId (opaque Clerk ID) +
 *   attemptedTenant + timestamp. Sin PHI. Transport: console.warn F1-S9.
 *
 * spec_anchor: 03-arch-fe.md § 2.1 + 06-tickets.yaml T-3
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

// T-V1: ShellLayoutWire uses @luana/ui-kit ShellLayout (kit store + brand props).
// ShellOrganismLayout (local chrome) is kept until T-V2 deletes it.
import { ShellLayoutWire } from "./_components/ShellLayoutWire";
import { fetchUserTenants } from "@/lib/iam/api";
import { logCrossTenantAttempt, logNoTenantsAssigned } from "@/lib/iam/audit";
import { DEFAULT_LANDING_SUBPATH } from "@/lib/shell-routes";
import { NetworkErrorFallback } from "./_components/NetworkErrorFallback";

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}

export default async function Layout({ children, params }: LayoutProps) {
  const { tenantId } = await params;

  // SC-01: sin sesión Clerk → redirect a /sign-in
  const { userId } = await auth();
  if (!userId) {
    redirect("/sign-in");
  }

  // SC-7: error de red al obtener tenants → NetworkErrorFallback
  let tenants: Awaited<ReturnType<typeof fetchUserTenants>>;
  try {
    tenants = await fetchUserTenants(userId);
  } catch (err) {
    // No loguear PHI — solo userId opaque + error de conexión
    console.warn("[audit]", {
      action: "tenant_fetch_failure",
      userId,
      error: String(err),
      timestamp: new Date().toISOString(),
    });
    return <NetworkErrorFallback />;
  }

  // SC-8: usuario sin tenants asignados → sign-out + error en sign-in
  if (tenants.length === 0) {
    logNoTenantsAssigned({ userId });
    redirect("/sign-out?next=/sign-in?error=no_tenants_assigned");
  }

  // SC-4, SC-5: tenantId de URL no pertenece al usuario → redirect al primero válido.
  // Bug #1 fix (vitalia-bugfix-shell-nav-scroll-errors T-1): destino vía SSoT
  // DEFAULT_LANDING_SUBPATH (= mateo/agenda); antes valeria/agenda → 404.
  const isValidTenant = tenants.some((t) => t.id === tenantId);
  if (!isValidTenant) {
    logCrossTenantAttempt({ userId, attemptedTenant: tenantId });
    redirect(`/${tenants[0].id}/${DEFAULT_LANDING_SUBPATH}`);
  }

  // Happy path: tenant válido → render shell
  // T-V1: ShellLayoutWire (@luana/ui-kit) replaces ShellOrganismLayout (local chrome).
  // T-V2 will remove the old ShellOrganismLayout import and clean up chrome/.
  // `tenantId` is validated above; ShellLayoutWire only needs `children` (no Server props needed
  // — ShellLayout is dynamic({ssr:false}) and reads its own zustand + usePathname internally).
  void tenantId; // used for audit/validation above; ShellLayoutWire reads from URL
  return <ShellLayoutWire>{children}</ShellLayoutWire>;
}
