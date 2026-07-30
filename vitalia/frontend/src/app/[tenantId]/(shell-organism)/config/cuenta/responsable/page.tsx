// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * config/cuenta/responsable/page.tsx — Responsable sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/config/cuenta/responsable
 *
 * Server Component default. PHI never in URL/searchParams.
 * ResponsibleView ("use client") renders DPO reference (read-only).
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-1
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { ResponsibleView } from "@/features/config";

interface ResponsablePageProps {
  params: Promise<{ tenantId: string }>;
}

/** Skeleton loader for the responsable view. */
function ResponsableSkeleton() {
  return (
    <div
      aria-label="Cargando responsable"
      aria-busy="true"
      className="p-6 space-y-4"
    >
      <Skeleton className="h-5 w-[30%] rounded" />
      <Skeleton className="h-3 w-[50%] rounded opacity-60" />
      <div className="mt-4 rounded-lg border p-4 space-y-2">
        <Skeleton className="h-3 w-[60%] rounded" />
        <Skeleton className="h-3 w-[45%] rounded" />
        <Skeleton className="h-3 w-[30%] rounded" />
      </div>
    </div>
  );
}

/**
 * ResponsablePage — N3-static Server Component for config/cuenta/responsable.
 * Thin shell: resolves tenantId + renders ResponsibleView client root.
 *
 * tenantSlug = tenantId (UUID used in routes — matches /{tenantId}/config/avanzado).
 */
export default async function ResponsablePage({ params }: ResponsablePageProps) {
  const { tenantId } = await params;

  return (
    <Suspense fallback={<ResponsableSkeleton />}>
      <ResponsibleView tenantId={tenantId} tenantSlug={tenantId} />
    </Suspense>
  );
}
