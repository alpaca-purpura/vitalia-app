// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * doctores/page.tsx — Leaf 3: Especialistas (route segment = "doctores").
 *
 * NOTE: The route folder is "doctores" (not "especialistas") — matches the
 * locked test contract. Label displayed in nav = "Especialistas". See
 * ServicioWorkspaceShell SERVICIO_LEAVES and T-7-impl-log.md § Upstream deficiency.
 *
 * Delegates to EspecialistasView ("use client").
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import type { Metadata } from "next";
import { EspecialistasView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Especialistas del servicio — Vitalia",
};

interface DoctoresPageProps {
  params: Promise<{ tenantId: string; "offer-id": string }>;
}

export default async function DoctoresPage({ params }: DoctoresPageProps) {
  const { "offer-id": offerId } = await params;
  return <EspecialistasView offerId={offerId} />;
}
