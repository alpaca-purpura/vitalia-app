// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * prueba-social/page.tsx — Leaf 5: Prueba social (Server Component).
 *
 * Delegates to PruebaSocialView ("use client").
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import type { Metadata } from "next";
import { PruebaSocialView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Prueba social — Vitalia",
};

interface PruebaSocialPageProps {
  params: Promise<{ tenantId: string; "offer-id": string }>;
}

export default async function PruebaSocialPage({ params }: PruebaSocialPageProps) {
  const { "offer-id": offerId } = await params;
  return <PruebaSocialView offerId={offerId} />;
}
