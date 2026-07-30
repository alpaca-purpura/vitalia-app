// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * config/cuenta/preferencias/page.tsx — Preferencias sub-sub-tab Server Component.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * Route: /[tenantId]/config/cuenta/preferencias
 *
 * Server Component default. PHI never in URL/searchParams.
 * PreferencesView ("use client") handles currency/timezone selectors.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-1
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { PreferencesView } from "@/features/config";

interface PreferencesPageProps {
  params: Promise<{ tenantId: string }>;
}

/** Skeleton loader for the preferencias view. */
function PreferencesSkeleton() {
  return (
    <div
      aria-label="Cargando preferencias"
      aria-busy="true"
      className="p-6 space-y-4"
    >
      <Skeleton className="h-5 w-[35%] rounded" />
      <div className="mt-4 space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="space-y-1">
            <Skeleton className="h-3 w-[20%] rounded" />
            <Skeleton className="h-9 w-[280px] rounded-md" />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * PreferencesPage — N3-static Server Component for config/cuenta/preferencias.
 * Thin shell: resolves tenantId + renders PreferencesView client root.
 */
export default async function PreferencesPage({ params }: PreferencesPageProps) {
  const { tenantId } = await params;

  return (
    <Suspense fallback={<PreferencesSkeleton />}>
      <PreferencesView tenantId={tenantId} initialData={null} />
    </Suspense>
  );
}
