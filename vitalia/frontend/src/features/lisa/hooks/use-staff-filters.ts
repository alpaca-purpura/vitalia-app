// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * use-staff-filters.ts — URL-backed staff directory filters.
 *
 * Persists filters in URL searchParams (q/specialty/active/page) using nuqs.
 * PHI NEVER in URL/searchParams (gate test_no_phi_in_url_params).
 * Filter values are non-PHI metadata (specialty label, active bool, free-text search).
 *
 * Per ADR-vitalia-004 § 3: URL searchParams for filter state (not Zustand/RQ).
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Data layer + § Forms
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

"use client";

import { useQueryStates, parseAsString, parseAsInteger } from "nuqs";
import type { StaffFilters } from "../types/staff.types";

/**
 * useStaffFilters — syncs staff directory filter state with URL searchParams.
 *
 * Returns:
 *   filters     — current StaffFilters (for React Query key + API call)
 *   setFilters  — update any subset of filters
 *   resetFilters — clear all filters (back to page 1)
 */
export function useStaffFilters(): {
  filters: StaffFilters;
  setQ: (q: string) => void;
  setSpecialty: (specialty: string) => void;
  setActive: (active: "true" | "false" | "") => void;
  setPage: (page: number) => void;
  resetFilters: () => void;
} {
  const [state, setState] = useQueryStates(
    {
      q: parseAsString.withDefault(""),
      specialty: parseAsString.withDefault(""),
      active: parseAsString.withDefault(""),
      page: parseAsInteger.withDefault(1),
    },
    {
      history: "push",
      shallow: true,
    },
  );

  const filters: StaffFilters = {
    q: state.q || undefined,
    specialty: state.specialty || undefined,
    active: (state.active as StaffFilters["active"]) || undefined,
    page: state.page,
  };

  const setQ = (q: string) => void setState({ q, page: 1 });
  const setSpecialty = (specialty: string) =>
    void setState({ specialty, page: 1 });
  const setActive = (active: "true" | "false" | "") =>
    void setState({ active, page: 1 });
  const setPage = (page: number) => void setState({ page });
  const resetFilters = () =>
    void setState({ q: "", specialty: "", active: "", page: 1 });

  return { filters, setQ, setSpecialty, setActive, setPage, resetFilters };
}
