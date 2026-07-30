// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * lisa/marca/page.tsx — Redirect to default sub-sub-tab (identidad).
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * /[tenantId]/lisa/marca → /[tenantId]/lisa/marca/identidad (default sub-sub-tab).
 *
 * Server Component default. Uses Next.js `redirect()` (server-side, no client JS).
 * PHI never in URL/searchParams (ADR constraint).
 *
 * T-4 vitalia-fase2-lisa-marca
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-4
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { redirect } from "next/navigation";

interface LisaMarcaPageProps {
  params: Promise<{ tenantId: string }>;
}

/**
 * LisaMarcaPage — redirects to the default sub-sub-tab.
 * Server Component. No data fetching — pure routing redirect.
 */
export default async function LisaMarcaPage({ params }: LisaMarcaPageProps) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/lisa/marca/identidad`);
}
