// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * lisa/servicios/catalogo/page.tsx — Catálogo sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/lisa/servicios/catalogo
 *
 * Server Component default. SSR-seeds the catalog list via
 * getServiciosInitialState({tenantId, view:"catalogo"}) then hydrates
 * LisaServiciosView ("use client"). PHI never in URL/searchParams (catalog is
 * NOT PHI · RN-13).
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch-fe.md § Routing
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { LisaServiciosView, getServiciosInitialState } from "@/features/lisa";

interface CatalogoPageProps {
  params: Promise<{ tenantId: string }>;
}

function CatalogoSkeleton() {
  return (
    <section
      aria-label="Cargando catálogo de servicios"
      aria-busy="true"
      className="flex flex-col gap-4 p-6"
    >
      <div className="h-5 w-[30%] rounded bg-muted animate-pulse" />
      <section className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-44 rounded-xl bg-muted opacity-50 animate-pulse"
          />
        ))}
      </section>
    </section>
  );
}

/**
 * CatalogoPage — N3-static Server Component for lisa/servicios/catalogo.
 */
export default async function CatalogoPage({ params }: CatalogoPageProps) {
  const { tenantId } = await params;
  const initial = await getServiciosInitialState({
    tenantId,
    view: "catalogo",
  });

  return (
    <Suspense fallback={<CatalogoSkeleton />}>
      <LisaServiciosView
        tenantId={tenantId}
        initialView="catalogo"
        initialData={initial.list}
      />
    </Suspense>
  );
}
