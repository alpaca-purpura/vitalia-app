// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s3-TBD
"use client";

/**
 * TenantStoreBootstrap — invisible Client Component mounted in root layout.
 * F1-S3 vitalia-fase1-tenant-switcher — T-8
 *
 * Responsibilities (03-arch.md § 2.7, § 2.7-bis):
 * 1. Mounts useTenants() to trigger the /api/tenants fetch on app boot.
 *    React Query result hydrates Zustand store via the hook's useEffect.
 * 2. Mounts useSignOutCleanup() to listen for Clerk sign-out and clear store.
 *
 * This component renders null — it has no visual output.
 * It must be placed inside ClerkProvider + QueryClientProvider (via <Providers>).
 *
 * Client Component ("use client") — uses React Query + Clerk hooks.
 *
 * No Clerk Organizations used — per MEMORY.md::no-clerk-organizations 2026-05-20.
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — bootstraps tenant list (business entities, not PHI).
 *
 * downstream-regression-na: brand-local shell-organism component; no cross-brand consumers
 */

import { useTenants } from "@/hooks/useTenants";
import { useSignOutCleanup } from "@/hooks/useSignOutCleanup";

/**
 * TenantStoreBootstrap — invisible shell bootstrap component.
 * Renders null. Side effects: hydrates tenant store + listens for sign-out.
 */
export function TenantStoreBootstrap(): null {
  useTenants();
  useSignOutCleanup();
  return null;
}
