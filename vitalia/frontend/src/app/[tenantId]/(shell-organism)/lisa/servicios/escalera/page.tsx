// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * lisa/servicios/escalera/page.tsx — Escalera sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/lisa/servicios/escalera
 *
 * Server Component default. SSR-seeds the full list (page_size=200, no
 * pagination) via getServiciosInitialState({tenantId, view:"escalera"}) then
 * hydrates LisaServiciosView ("use client"). PHI never in URL/searchParams.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch-fe.md § Routing
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { LisaServiciosView, getServiciosInitialState } from "@/features/lisa";

interface EscaleraPageProps {
  params: Promise<{ tenantId: string }>;
}

function EscaleraSkeleton() {
  return (
    <section
      aria-label="Cargando escalera de valor"
      aria-busy="true"
      className="flex flex-col gap-3 p-6"
    >
      <div className="h-24 rounded-xl bg-muted opacity-50 animate-pulse" />
      <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="h-40 rounded-xl bg-muted opacity-50 animate-pulse" />
        <div className="h-40 rounded-xl bg-muted opacity-50 animate-pulse" />
        <div className="h-40 rounded-xl bg-muted opacity-50 animate-pulse" />
      </section>
      <div className="h-24 rounded-xl bg-muted opacity-50 animate-pulse" />
    </section>
  );
}

/**
 * EscaleraPage — N3-static Server Component for lisa/servicios/escalera.
 */
export default async function EscaleraPage({ params }: EscaleraPageProps) {
  const { tenantId } = await params;
  const initial = await getServiciosInitialState({
    tenantId,
    view: "escalera",
  });

  return (
    <Suspense fallback={<EscaleraSkeleton />}>
      <LisaServiciosView
        tenantId={tenantId}
        initialView="escalera"
        initialData={initial.list}
      />
    </Suspense>
  );
}
