/**
 * ShellLayout showcase — test page fixture
 * F1-S4 vitalia-fase1-shell-layout-5050 — T-7 Fase 7A micro-fix
 *
 * T-V2 (platform-lift-shell-chrome-ui-kit): ShellOrganismLayout (local chrome)
 * replaced by ShellLayoutWire which wraps @luana/ui-kit ShellLayout.
 * The ShellLayoutWire is the vitalia production wire — same component used by
 * the real layout.tsx route, so e2e fixture remains faithful to production.
 *
 * Accessible via dev server: /test-stack/shell-layout
 * NOT protected by Clerk auth (public dev-only, no PHI).
 *
 * Pre-hydrates tenant-store con mock tenants LatAm para que TenantSwitcher
 * en TopBarShell renderice sin Clerk auth.
 *
 * HIPAA-lite: no-phi-scope — UI shell fixture, zero PHI.
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

"use client";

import { useEffect } from "react";
import { ShellLayoutWire } from "@/app/[tenantId]/(shell-organism)/_components/ShellLayoutWire";
import { useTenantStore } from "@/stores/tenant-store";
import type { Tenant } from "@/components/shared/shell-organism/types";

const FIXTURE_TENANT_ID = "test-tenant-shell-layout";

/** Mock tenants LatAm para que TenantSwitcher renderice en showcase. */
const MOCK_TENANTS: ReadonlyArray<Tenant> = [
  { id: FIXTURE_TENANT_ID, name: "Sonrisa Plena", city: "Lima" },
  { id: "tenant-dermalia-mx", name: "Dermalia MX", city: "CDMX" },
];

export default function ShellLayoutShowcasePage() {
  const setAvailableTenants = useTenantStore((s) => s.setAvailableTenants);
  const setActiveTenant = useTenantStore((s) => s.setActiveTenant);
  const availableTenants = useTenantStore((s) => s.availableTenants);

  // ★ Fix 2026-05-24 (Chris detectó "Sonrisa Plena desaparece a 1s"):
  // useSignOutCleanup (mounted en TenantStoreBootstrap root layout) corre
  // cuando Clerk loads + isSignedIn=false → clearStore() limpia MOCK_TENANTS
  // → TenantSwitcher returns null. Era flash visible.
  //
  // Fix: re-hidratamos MOCK_TENANTS cuando detectamos store vacío. Dep en
  // availableTenants asegura que post-cleanup el showcase auto-restaura.
  // En PROD con Clerk login real esto no aplica (isSignedIn=true → cleanup
  // nunca corre → store stays hydrated).
  useEffect(() => {
    if (availableTenants.length === 0) {
      setAvailableTenants(MOCK_TENANTS);
      setActiveTenant(MOCK_TENANTS[0]);
    }
  }, [availableTenants, setAvailableTenants, setActiveTenant]);

  return (
    <ShellLayoutWire>
      {null}
    </ShellLayoutWire>
  );
}
