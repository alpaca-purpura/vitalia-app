// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * horarios/page.tsx — Doctor horarios page (Server Component).
 *
 * Delegates interactivity to DoctorHorariosView ("use client").
 * Per ADR-vitalia-004 § 3: Server-First default; params are Promise (Next 16).
 * PHI never in URL/searchParams (doctor-id is a UUID, not PHI).
 *
 * T-FE-3 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Routing
 */

import type { Metadata } from "next";
import { DoctorHorariosView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Horarios del integrante — Vitalia",
};

interface HorariosPageProps {
  params: Promise<{ tenantId: string; "doctor-id": string }>;
}

export default async function HorariosPage({ params }: HorariosPageProps) {
  const { "doctor-id": doctorId } = await params;

  return <DoctorHorariosView doctorId={doctorId} />;
}
