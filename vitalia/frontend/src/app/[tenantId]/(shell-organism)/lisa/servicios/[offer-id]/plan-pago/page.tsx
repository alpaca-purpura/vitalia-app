// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * plan-pago/page.tsx — Leaf 4: Plan de pago (Server Component).
 *
 * Delegates to PlanPagoView ("use client").
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import type { Metadata } from "next";
import { PlanPagoView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Plan de pago — Vitalia",
};

interface PlanPagoPageProps {
  params: Promise<{ tenantId: string; "offer-id": string }>;
}

export default async function PlanPagoPage({ params }: PlanPagoPageProps) {
  const { "offer-id": offerId } = await params;
  return <PlanPagoView offerId={offerId} />;
}
