// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * config/cuenta/datos/page.tsx — Datos sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/config/cuenta/datos
 *
 * Server Component default. PHI never in URL/searchParams.
 * AccountDataView ("use client") handles interactive form + autosave logic.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-1
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { AccountDataView } from "@/features/config";

interface DatosPageProps {
  params: Promise<{ tenantId: string }>;
}

/** Skeleton loader for the datos form (shown during initial hydration). */
function DatosSkeleton() {
  return (
    <div
      aria-label="Cargando datos de la cuenta"
      aria-busy="true"
      className="p-6 space-y-4"
    >
      <Skeleton className="h-5 w-[35%] rounded" />
      <Skeleton className="h-3 w-[55%] rounded opacity-60" />
      <div className="mt-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="space-y-1">
            <Skeleton className="h-3 w-[25%] rounded" />
            <Skeleton className="h-9 w-full rounded-md" />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * DatosPage — N3-static Server Component for config/cuenta/datos.
 * Thin shell: resolves tenantId + renders AccountDataView client root.
 */
export default async function DatosPage({ params }: DatosPageProps) {
  const { tenantId } = await params;

  return (
    <Suspense fallback={<DatosSkeleton />}>
      <AccountDataView tenantId={tenantId} initialData={null} />
    </Suspense>
  );
}
