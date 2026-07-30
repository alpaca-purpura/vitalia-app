// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * [doctor-id]/page.tsx — Redirect to perfil (canonical workspace entry).
 *
 * /lisa/staff/{doctorId} → /lisa/staff/{doctorId}/perfil
 *
 * ADR-vitalia-004 § 3: Server Component default. redirect() built-in Next.js.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Routing
 */

import { redirect } from "next/navigation";

interface DoctorPageProps {
  params: Promise<{ tenantId: string; "doctor-id": string }>;
}

export default async function DoctorPage({ params }: DoctorPageProps) {
  const { tenantId, "doctor-id": doctorId } = await params;
  redirect(`/${tenantId}/lisa/staff/${doctorId}/perfil`);
}
