// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo-board.ts — React Query hooks for Embudo board (T-FE-2).
 *
 * useEmbudoBoard: GET /api/v1/crm/board → BoardResponse
 * - Query key: ['crm','board', filters] (test_react_query_keys_convention)
 * - Disabled when tenantId=null (tenant-isolation.md)
 * - graceful-degradation: timeout (30s via fetchClient) + error boundary catches
 *
 * spec_anchor: 03-arch-fe.md § api/embudo-board.ts
 * downstream-regression-na: brand-local vitalia FE; no cross-brand consumers
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import { boardKey } from "./_embudo-keys";
import type { BoardFilters, BoardResponse } from "../types/embudo.types";

const API_BASE = "/api/v1/crm";

/**
 * useEmbudoBoard — fetches the Kanban/List board data.
 *
 * Disabled when tenantId=null (tenant-isolation: every request requires tenant scope).
 * Stale time 30s — board data changes as Adrián moves leads; short stale fits the
 * real-time supervision use case.
 *
 * Error handling: React Query surfaces isError; UI renders error banner + Reintentar.
 * Timeout: fetchClient AbortController (30s default).
 */
export function useEmbudoBoard(filters: BoardFilters = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: boardKey(filters),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      // Build query string
      const params = new URLSearchParams();
      if (filters.view) params.set("view", filters.view);
      if (filters.sort) params.set("sort", filters.sort);
      if (filters.origin) params.set("origin", filters.origin);
      if (filters.doctor) params.set("doctor", filters.doctor);
      if (filters.stage) params.set("stage", filters.stage);
      if (filters.search) params.set("search", filters.search);
      if (filters.operatedBy) params.set("operated_by", filters.operatedBy);

      const qs = params.toString();
      const url = `${API_BASE}/board${qs ? `?${qs}` : ""}`;

      const raw = await fetchClient<unknown>(url, { token, tenantId });
      return keysToCamel<BoardResponse>(raw);
    },
    enabled: isLoaded && !!isSignedIn && !!tenantId,
    staleTime: 30_000, // 30s — board refreshes relatively often
    // retry: use QueryClient default (tests set retry:false)
  });
}
