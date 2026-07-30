// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * use-servicios-filters.ts — URL-backed catalog filters (nuqs).
 *
 * Persists filters in URL searchParams (q/category/rung/active) using nuqs.
 * PHI NEVER in URL/searchParams (gate test_no_phi_in_url_params): all filter
 * values are non-PHI catalog metadata (category label, ladder rung, active bool,
 * free-text service-name search). A service catalog is NOT PHI (RN-13) — only a
 * patient Case is PHI, and Cases never reach the URL.
 *
 * Per ADR-vitalia-004 § 3: URL searchParams for filter state (not Zustand/RQ).
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § Data layer + § Forms
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

"use client";

import { useMemo } from "react";
import { useQueryStates, parseAsString } from "nuqs";
import type {
  ServiciosFilters,
  OfferValueLevel,
} from "../types/servicios.types";

const ACTIVE_VALUES = ["all", "active", "inactive"] as const;

/**
 * useServiciosFilters — syncs catalog filter state with URL searchParams.
 *
 * Returns the stable ServiciosFilters object (React Query key + API call) plus
 * granular setters that always reset to the default page.
 */
export function useServiciosFilters(): {
  filters: ServiciosFilters;
  setSearch: (search: string) => void;
  setCategory: (category: string | null) => void;
  setRung: (rung: OfferValueLevel | null) => void;
  setActive: (active: ServiciosFilters["active"]) => void;
  resetFilters: () => void;
} {
  const [state, setState] = useQueryStates(
    {
      q: parseAsString.withDefault(""),
      category: parseAsString.withDefault(""),
      rung: parseAsString.withDefault(""),
      active: parseAsString.withDefault("all"),
    },
    { history: "push", shallow: true },
  );

  const filters: ServiciosFilters = useMemo(
    () => ({
      search: state.q,
      category: state.category || null,
      rung: (state.rung || null) as OfferValueLevel | null,
      active: ((ACTIVE_VALUES as readonly string[]).includes(state.active)
        ? state.active
        : "all") as ServiciosFilters["active"],
    }),
    [state.q, state.category, state.rung, state.active],
  );

  const setSearch = (search: string) => void setState({ q: search });
  const setCategory = (category: string | null) =>
    void setState({ category: category ?? "" });
  const setRung = (rung: OfferValueLevel | null) =>
    void setState({ rung: rung ?? "" });
  const setActive = (active: ServiciosFilters["active"]) =>
    void setState({ active });
  const resetFilters = () =>
    void setState({ q: "", category: "", rung: "", active: "all" });

  return { filters, setSearch, setCategory, setRung, setActive, resetFilters };
}
