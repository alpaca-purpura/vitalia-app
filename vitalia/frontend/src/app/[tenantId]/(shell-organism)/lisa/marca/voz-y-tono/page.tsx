// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * lisa/marca/voz-y-tono/page.tsx — Voz y tono sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/lisa/marca/voz-y-tono
 *
 * Server Component default. Passes tenantId to VozTonoView ("use client").
 * PHI never in URL/searchParams (ADR constraint).
 *
 * T-4 + T-6 vitalia-fase2-lisa-marca
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-4 + T-6
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { VozTonoView } from "@/features/lisa";

interface VozTonoPageProps {
  params: Promise<{ tenantId: string }>;
}

/** Skeleton loader for the voz-y-tono form (shown during initial hydration). */
function VozTonoSkeleton() {
  return (
    <div
      data-testid="lisa-marca-loading-skeleton"
      aria-label="Cargando sección Voz y tono"
      aria-busy="true"
      className="flex flex-col gap-4 p-6"
    >
      <div className="h-5 w-[40%] rounded bg-muted animate-pulse" />
      <div className="h-3 w-[60%] rounded bg-muted opacity-60 animate-pulse" />
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="h-[120px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[120px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[120px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[120px] rounded-lg bg-muted opacity-50 animate-pulse" />
      </div>
      <div className="h-[200px] rounded-lg bg-muted opacity-40 animate-pulse" />
    </div>
  );
}

/**
 * VozTonoPage — N3-static Server Component for lisa/marca/voz-y-tono.
 * Wires VozTonoView (T-6) with tenantId from route params.
 */
export default async function VozTonoPage({ params }: VozTonoPageProps) {
  const { tenantId } = await params;

  return (
    <Suspense fallback={<VozTonoSkeleton />}>
      <VozTonoView tenantId={tenantId} />
    </Suspense>
  );
}
