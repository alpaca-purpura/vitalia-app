// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * servicios/page.tsx — Doctor servicios placeholder page (Server Component).
 *
 * Business rule: "Servicios — pendiente · depende de Mi Clínica → Servicios"
 * This is the permanent placeholder until the Servicios story ships.
 *
 * ADR-vitalia-004 § 3: Server-First default.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Routing + 01-spec.md § Servicios pendiente
 */

import type { Metadata } from "next";
import { DoctorServiciosView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Servicios del integrante — Vitalia",
};

interface ServiciosPageProps {
  params: Promise<{ tenantId: string; "doctor-id": string }>;
}

export default async function ServiciosPage({ params: _params }: ServiciosPageProps) {
  return (
    <div className="p-5 md:p-6">
      <DoctorServiciosView />
    </div>
  );
}
