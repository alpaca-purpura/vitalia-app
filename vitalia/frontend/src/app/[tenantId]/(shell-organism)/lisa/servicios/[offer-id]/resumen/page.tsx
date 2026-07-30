// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * resumen/page.tsx — Leaf 1: Resumen del servicio (Server Component).
 *
 * Delegates to ResumenView ("use client") for form interactivity (RHF + Zod +
 * autosave). Metadata title reflects the leaf context.
 *
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import type { Metadata } from "next";
import { ResumenView } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Resumen del servicio — Vitalia",
};

interface ResumenPageProps {
  params: Promise<{ tenantId: string; "offer-id": string }>;
}

export default async function ResumenPage({ params }: ResumenPageProps) {
  const { "offer-id": offerId } = await params;
  return <ResumenView offerId={offerId} />;
}
