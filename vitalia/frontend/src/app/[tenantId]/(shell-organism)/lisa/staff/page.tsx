// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * lisa/staff/page.tsx — Staff directory page (Server Component).
 *
 * ADR-vitalia-004 § 3 — Server-First default.
 * Fetches initial SSR data via getStaffInitialState for hydration.
 * Delegates all client interactivity to LisaStaffView ("use client").
 *
 * PHI NEVER in URL/searchParams (gate test_no_phi_in_url_params).
 * Ensure 'staff' is present in SHIPPED_STATIC_SUBTABS in agent-catalog.ts.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Routing + ADR-vitalia-004 § 3.1
 * downstream-regression-na: brand-local vitalia route; no cross-brand consumers
 */

import type { Metadata } from "next";
import { auth } from "@clerk/nextjs/server";
import { LisaStaffView } from "@/features/lisa";
import { getStaffInitialState } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Staff — Vitalia",
};

interface StaffPageProps {
  params: Promise<{ tenantId: string }>;
}

/**
 * StaffPage — Server Component.
 * Fetches initial staff data for SSR hydration.
 * Falls back gracefully (null initialData) when auth/network unavailable.
 */
export default async function StaffPage({ params }: StaffPageProps) {
  const { tenantId } = await params;

  // Get clinic context from Clerk metadata (if available)
  const session = await auth();
  const clinicId =
    (session.sessionClaims?.["clinic_id"] as string | undefined) ?? null;

  // SSR initial data — null fallback handled by client-side RQ
  const initialData = await getStaffInitialState(tenantId, clinicId);

  return (
    <div className="p-5 md:p-6">
      <LisaStaffView initialData={initialData ?? undefined} />
    </div>
  );
}
