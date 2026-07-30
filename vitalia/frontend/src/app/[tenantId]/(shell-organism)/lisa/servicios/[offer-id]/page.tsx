// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * [offer-id]/page.tsx — Default redirect to the resumen leaf.
 *
 * Navigating to /{tenantId}/lisa/servicios/{offer-id} (no leaf) redirects
 * to /{tenantId}/lisa/servicios/{offer-id}/resumen (leaf 1 default).
 *
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import { redirect } from "next/navigation";

interface OfferIdPageProps {
  params: Promise<{ tenantId: string; "offer-id": string }>;
}

export default async function OfferIdPage({ params }: OfferIdPageProps) {
  const { tenantId, "offer-id": offerId } = await params;
  redirect(`/${tenantId}/lisa/servicios/${offerId}/resumen`);
}
