// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * para-adrian/page.tsx — Leaf 2: Argumentario para Adrián (Server Component).
 *
 * Delegates to ParaAdrianView ("use client").
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import type { Metadata } from "next";
import { ParaAdrianView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Para Adrián — Vitalia",
};

interface ParaAdrianPageProps {
  params: Promise<{ tenantId: string; "offer-id": string }>;
}

export default async function ParaAdrianPage({ params }: ParaAdrianPageProps) {
  const { "offer-id": offerId } = await params;
  return <ParaAdrianView offerId={offerId} />;
}
