// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * LisaServiciosView.tsx — Client root of the Lisa · Servicios sub-tab.
 *
 * Mirrors the shipped LisaStaffView pattern: wraps the directory in a
 * <NuqsAdapter> (URL filter state via useQueryStates) and composes the
 * ServiciosDirectoryHeader + the active sub-sub-tab body (CatalogoView |
 * EscaleraView). The view is decided by the SSR-resolved `initialView`
 * (the N3-static [subsubtab] route segment) — NEVER an internal Shadcn Tabs
 * (ADR-vitalia-004 § 3.1.1 — that is the Nivel 4 anti-pattern).
 *
 * SSR hydration: `initialData` seeds React Query for the matching view so the
 * first paint has data (no spinner flash).
 *
 * Spanish neutro LatAm — sin voseo.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * architecture_pattern: ADR-vitalia-004 (N3-static, React Query, nuqs, FSD-Lite)
 * spec_anchor: 03-arch-fe.md § 5 LisaServiciosView + 01-spec.md
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { NuqsAdapter } from "nuqs/adapters/next/app";
import { ServiciosDirectoryHeader } from "./ServiciosDirectoryHeader";
import { CatalogoView } from "./CatalogoView";
import { EscaleraView } from "./EscaleraView";
import { useServiciosFilters } from "../../hooks/use-servicios-filters";
import type {
  ServiceListResponse,
  ServiciosView,
} from "../../types/servicios.types";

export interface LisaServiciosViewProps {
  tenantId: string;
  /** N3-static segment resolved server-side: "catalogo" | "escalera". */
  initialView: ServiciosView;
  /** SSR-seeded list for the matching view (null on fetch error). */
  initialData?: ServiceListResponse | null;
}

/** Inner body — inside NuqsAdapter so useQueryStates works. */
function ServiciosBody({
  tenantId,
  initialView,
  initialData,
}: LisaServiciosViewProps) {
  const { filters, setSearch, setCategory, setRung, setActive } =
    useServiciosFilters();

  return (
    // G2-F1: page gutter (p-5 md:p-6) so the catalog/escalera content isn't flush
    // to the shell edges — matches the peer sub-tab convention (e.g. staff/page.tsx).
    <div className="space-y-4 p-5 md:p-6">
      <ServiciosDirectoryHeader
        filters={filters}
        tenantId={tenantId}
        onSearch={setSearch}
        onCategory={setCategory}
        onRung={setRung}
        onActive={setActive}
      />

      {initialView === "escalera" ? (
        <EscaleraView
          tenantId={tenantId}
          initialData={initialData ?? undefined}
        />
      ) : (
        <CatalogoView
          tenantId={tenantId}
          filters={filters}
          initialData={initialData ?? undefined}
        />
      )}
    </div>
  );
}

/**
 * LisaServiciosView — client root. Wrap in NuqsAdapter for URL filter state.
 */
export function LisaServiciosView(props: LisaServiciosViewProps) {
  return (
    <NuqsAdapter>
      <ServiciosBody {...props} />
    </NuqsAdapter>
  );
}
