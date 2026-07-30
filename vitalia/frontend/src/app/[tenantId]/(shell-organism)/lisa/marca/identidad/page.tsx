// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * lisa/marca/identidad/page.tsx — Identidad sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/lisa/marca/identidad
 *
 * Server Component default. PHI never in URL/searchParams.
 * IdentidadView ("use client") handles interactive form logic.
 *
 * T-4 vitalia-fase2-lisa-marca (routing)
 * T-5 vitalia-fase2-lisa-marca (IdentidadView wiring)
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-5
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { IdentidadView } from "@/features/lisa";

interface IdentidadPageProps {
  params: Promise<{ tenantId: string }>;
}

/** Skeleton loader for the identidad form (shown during initial hydration). */
function IdentidadSkeleton() {
  return (
    <div
      aria-label="Cargando sección Identidad"
      aria-busy="true"
      className="flex flex-col gap-4 p-6"
    >
      <div className="h-5 w-[35%] rounded bg-muted animate-pulse" />
      <div className="h-3 w-[55%] rounded bg-muted opacity-60 animate-pulse" />
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="h-[100px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[100px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[100px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[100px] rounded-lg bg-muted opacity-50 animate-pulse" />
      </div>
    </div>
  );
}

/**
 * IdentidadPage — N3-static Server Component for lisa/marca/identidad.
 * Thin shell: resolves tenantId + renders IdentidadView client root.
 */
export default async function IdentidadPage({ params }: IdentidadPageProps) {
  const { tenantId } = await params;

  return (
    <Suspense fallback={<IdentidadSkeleton />}>
      <IdentidadView tenantId={tenantId} />
    </Suspense>
  );
}
