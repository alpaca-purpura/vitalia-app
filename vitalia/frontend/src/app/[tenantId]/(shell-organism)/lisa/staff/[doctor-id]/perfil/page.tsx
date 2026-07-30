// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * perfil/page.tsx — Doctor perfil page (Server Component).
 *
 * Delegates interactivity to DoctorPerfilView ("use client").
 * SSR hydration via parent layout's initialDoctor data.
 *
 * ADR-vitalia-004 § 3: Server-First default.
 * PHI NEVER in searchParams.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Routing + § Forms
 */

import type { Metadata } from "next";
import { DoctorPerfilView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Perfil del integrante — Vitalia",
};

interface PerfilPageProps {
  params: Promise<{ tenantId: string; "doctor-id": string }>;
}

export default async function PerfilPage({ params }: PerfilPageProps) {
  const { "doctor-id": doctorId } = await params;
  return (
    <div className="p-5 md:p-6">
      <DoctorPerfilView doctorId={doctorId} />
    </div>
  );
}
