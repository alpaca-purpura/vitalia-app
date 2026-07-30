// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * _embudo-keys.ts — React Query key factory for adrian/embudo feature.
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Keys follow convention: ['crm', action, ...filtersStable]
 * per 03-arch-fe.md § 4 + test_react_query_keys_convention.test.ts.
 *
 * Module: 'crm' (not 'adrian') — matches BE module boundary (crm/board, crm/leads).
 * Subtab context in key for cross-invalidation:
 *   invalidateQueries({ queryKey: ['crm','board'] }) after PATCH /stage.
 *
 * downstream-regression-na: brand-local vitalia FE; no cross-brand consumers
 */
import type { BoardFilters } from "../types/embudo.types";

const CRM = "crm" as const;

/** Board query key — includes view + filters for cache segmentation (RN-14) */
export const boardKey = (filters: BoardFilters = {}) =>
  [CRM, "board", {
    view: filters.view ?? "kanban",
    sort: filters.sort ?? "stage_age_desc",
    origin: filters.origin ?? null,
    doctor: filters.doctor ?? null,
    stage: filters.stage ?? null,
    search: filters.search ?? null,
    operatedBy: filters.operatedBy ?? null,
  }] as const;

/** Lead detail (Resumen view) */
export const leadDetailKey = (leadId: string) =>
  [CRM, "lead", leadId, "detail"] as const;

/** Lead timeline (Historial view) */
export const leadTransitionsKey = (leadId: string) =>
  [CRM, "lead", leadId, "transitions"] as const;

/** Frozen leads list (Recuperar view) */
export const frozenKey = () => [CRM, "frozen"] as const;

/** Stage mutation key (for useMutation queryKey) */
export const stageMutationKey = () => [CRM, "lead", "stage-mutation"] as const;
