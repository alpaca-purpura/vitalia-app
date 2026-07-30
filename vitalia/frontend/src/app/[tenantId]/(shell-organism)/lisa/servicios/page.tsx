// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * lisa/servicios/page.tsx — Redirect to default sub-sub-tab (catalogo).
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * /[tenantId]/lisa/servicios → /[tenantId]/lisa/servicios/catalogo.
 *
 * Server Component default. In-render redirect() (server-side, no client JS).
 * The edge proxy (proxy.ts) also short-circuits this via
 * shellInRenderRedirectTarget to avoid the Next16 soft-nav "Rendered more
 * hooks" flake; this redirect() is the SSR fallback.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch-fe.md § Routing
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { redirect } from "next/navigation";

interface LisaServiciosPageProps {
  params: Promise<{ tenantId: string }>;
}

/**
 * LisaServiciosPage — redirects to the default sub-sub-tab (catalogo).
 * Server Component. No data fetching — pure routing redirect.
 */
export default async function LisaServiciosPage({
  params,
}: LisaServiciosPageProps) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/lisa/servicios/catalogo`);
}
