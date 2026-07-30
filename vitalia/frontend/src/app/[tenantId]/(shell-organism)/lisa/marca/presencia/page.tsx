// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * lisa/marca/presencia/page.tsx — Presencia sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/lisa/marca/presencia
 *
 * Server Component default. Initial data hydration happens here;
 * interactive form logic lives in PresenciaView ("use client").
 * PHI never in URL/searchParams (ADR constraint).
 *
 * T-4 vitalia-fase2-lisa-marca (route), T-7 (PresenciaView wired)
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-7
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { PresenciaView } from "@/features/lisa";

interface PresenciaPageProps {
  params: Promise<{ tenantId: string }>;
}

/** Skeleton loader for the presencia form (shown during initial hydration). */
function PresenciaSkeleton() {
  return (
    <div
      aria-label="Cargando sección Presencia"
      aria-busy="true"
      className="flex flex-col gap-4 p-6"
    >
      <div className="h-5 w-[30%] rounded bg-muted animate-pulse" />
      <div className="h-3 w-[50%] rounded bg-muted opacity-60 animate-pulse" />
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="h-[80px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[80px] rounded-lg bg-muted opacity-50 animate-pulse" />
        <div className="h-[160px] rounded-lg bg-muted opacity-40 animate-pulse sm:col-span-2" />
      </div>
    </div>
  );
}

/**
 * PresenciaPage — N3-static Server Component for lisa/marca/presencia.
 * Passes tenantId to PresenciaView for fetchClient X-Tenant-ID propagation.
 */
export default async function PresenciaPage({ params }: PresenciaPageProps) {
  const { tenantId } = await params;

  return (
    <Suspense fallback={<PresenciaSkeleton />}>
      <PresenciaView tenantId={tenantId} />
    </Suspense>
  );
}
