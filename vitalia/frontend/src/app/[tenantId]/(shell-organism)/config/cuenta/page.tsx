// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * config/cuenta/page.tsx — Redirect to default sub-sub-tab (datos).
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * /[tenantId]/config/cuenta → /[tenantId]/config/cuenta/datos (default sub-sub-tab).
 *
 * Server Component default. Uses Next.js `redirect()` (server-side, no client JS).
 * PHI never in URL/searchParams (ADR constraint).
 * Edge redirect in shell-routes.ts N3_DEFAULT_LEAF handles the perf case.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-1
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { redirect } from "next/navigation";

interface ConfigCuentaPageProps {
  params: Promise<{ tenantId: string }>;
}

/**
 * ConfigCuentaPage — redirects to the default sub-sub-tab (datos).
 * Server Component. No data fetching — pure routing redirect.
 */
export default async function ConfigCuentaPage({
  params,
}: ConfigCuentaPageProps) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/config/cuenta/datos`);
}
