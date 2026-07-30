// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * LisaStaffView.tsx — Client root for Lisa/Staff sub-tab.
 *
 * Thin wrapper that receives SSR initial data as props and passes to StaffDirectoryView.
 * Per ADR-vitalia-004 § 3.3: "use client" here; page.tsx stays pure Server Component.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § FSD-Lite + ADR-vitalia-004 § 3.3
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { NuqsAdapter } from "nuqs/adapters/next/app";
import { StaffDirectoryView } from "./StaffDirectoryView";
import type { PaginatedDoctors } from "../../types/staff.types";

interface LisaStaffViewProps {
  initialData?: PaginatedDoctors;
}

/**
 * LisaStaffView — client root for lisa/staff directory.
 * Hydrates StaffDirectoryView with SSR initial data.
 *
 * NuqsAdapter wraps the tree so useStaffFilters (useQueryStates) can work
 * without NUQS-404 error. Pattern mirrors InboxPageClient.tsx.
 */
export function LisaStaffView({ initialData }: LisaStaffViewProps) {
  return (
    <NuqsAdapter>
      <StaffDirectoryView initialData={initialData} />
    </NuqsAdapter>
  );
}
