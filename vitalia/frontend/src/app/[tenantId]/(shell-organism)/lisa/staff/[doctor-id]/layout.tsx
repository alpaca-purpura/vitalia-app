// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * [doctor-id]/layout.tsx — Staff workspace layout (Server Component).
 *
 * Mounts StaffWorkspaceShell which renders EntitySubNavBar + content slot.
 * Fetches doctor initial data for SSR hydration of the workspace.
 *
 * ADR-vitalia-004 § 3: Server Component default.
 * PHI NEVER in URL/searchParams — [doctor-id] is a UUID, not PHI.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Routing
 * downstream-regression-na: brand-local vitalia route layout
 */

import { auth } from "@clerk/nextjs/server";
import { StaffWorkspaceShell, getDoctorInitialState } from "@/features/lisa";

interface DoctorWorkspaceLayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string; "doctor-id": string }>;
}

export default async function DoctorWorkspaceLayout({
  children,
  params,
}: DoctorWorkspaceLayoutProps) {
  const { tenantId, "doctor-id": doctorId } = await params;

  // Get clinic context from Clerk session metadata
  const session = await auth();
  const clinicId =
    (session.sessionClaims?.["clinic_id"] as string | undefined) ?? null;

  // SSR initial data — null fallback handled by client-side RQ
  const initialDoctor = await getDoctorInitialState(tenantId, doctorId, clinicId);

  return (
    <StaffWorkspaceShell
      tenantId={tenantId}
      doctorId={doctorId}
      initialDoctor={initialDoctor ?? undefined}
    >
      {children}
    </StaffWorkspaceShell>
  );
}
