// cap: auth.clerk-middleware
// story-origin: vitalia-fase1-s3-TBD
"use client";

/**
 * useSignOutCleanup — clears tenant store and localStorage on Clerk sign-out.
 * F1-S3 vitalia-fase1-tenant-switcher — T-4
 *
 * Watches Clerk `isSignedIn` for a false transition (true → false).
 * When sign-out is detected:
 * 1. Calls useTenantStore.clearStore() to reset Zustand state
 * 2. Removes localStorage key TENANT_STORAGE_KEY (clears persisted activeTenant)
 *
 * Cross-user isolation: prevents tenant data from a previous user session
 * leaking into a new user's session on the same browser.
 *
 * Intended usage: mount in TenantStoreBootstrap (root layout invisible component).
 *
 * No Clerk Organizations used — per MEMORY.md::no-clerk-organizations 2026-05-20.
 * Uses useAuth() only for isLoaded + isSignedIn — no orgId, no useOrganization.
 *
 * 03-arch.md § 2.7-bis — implementation verbatim.
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — this hook manages session cleanup only, no PHI access.
 *
 * downstream-regression-na: brand-local hook; no cross-brand consumers
 */

import { useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useTenantStore, TENANT_STORAGE_KEY } from "@/stores/tenant-store";

/**
 * Mounts sign-out cleanup listener.
 * Call once in TenantStoreBootstrap (root layout).
 */
export function useSignOutCleanup(): void {
  const { isLoaded, isSignedIn } = useAuth();
  const clearStore = useTenantStore((s) => s.clearStore);

  useEffect(() => {
    if (!isLoaded) return;
    if (isSignedIn === false) {
      clearStore();
      try {
        localStorage.removeItem(TENANT_STORAGE_KEY);
      } catch {
        // localStorage may be unavailable in SSR or restricted contexts
      }
    }
  }, [isLoaded, isSignedIn, clearStore]);
}
