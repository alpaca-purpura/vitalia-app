// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * pagina/page.tsx — Workspace leaf "Página" for doctor public profile.
 *
 * Server Component (default, no "use client"). Matches pattern of perfil/page.tsx.
 * Layout: p-5 md:p-6 wrapper, delegates to DoctorPaginaView (Client Component).
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D
 */

import type { Metadata } from "next";
import { DoctorPaginaView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Página pública — Vitalia",
};

interface PaginaPageProps {
  params: Promise<{ tenantId: string; "doctor-id": string }>;
}

export default async function PaginaPage({ params }: PaginaPageProps) {
  const { "doctor-id": doctorId } = await params;
  return (
    <div className="p-5 md:p-6">
      <DoctorPaginaView doctorId={doctorId} />
    </div>
  );
}
