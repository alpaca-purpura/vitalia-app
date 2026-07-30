// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * frozen.ts — React Query hooks for frozen leads (Recuperar view, T-FE-3).
 *
 * useFrozenLeads: GET /api/v1/crm/frozen → FrozenListResponse
 * useReactivateLead: POST /api/v1/crm/leads/{id}/reactivate
 *
 * spec_anchor: 03-arch-fe.md § api/frozen.ts + 01-spec.md § V4
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import { frozenKey } from "./_embudo-keys";
import type { FrozenListResponse, LeadCardDTO } from "../types/embudo.types";

const API_BASE = "/api/v1/crm";

/**
 * useFrozenLeads — fetches the list of frozen leads segmented by reason.
 *
 * Returns: FrozenListResponse { recienCongelados[], decidioNo[] }
 * Disabled when tenantId=null.
 * staleTime 120s — frozen leads change infrequently (auto-freeze cron).
 */
export function useFrozenLeads() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: frozenKey(),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      const raw = await fetchClient<unknown>(`${API_BASE}/frozen`, {
        token,
        tenantId,
      });
      return keysToCamel<FrozenListResponse>(raw);
    },
    enabled: isLoaded && !!isSignedIn && !!tenantId,
    staleTime: 120_000, // 2min — frozen list doesn't change frequently
  });
}

/**
 * useReactivateLead — POST /crm/leads/{id}/reactivate.
 *
 * On success: invalidates frozen list + board (reactivated lead returns to board).
 * Spec V4: reactivated lead returns to board at its last stage.
 */
export function useReactivateLead() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (leadId: string): Promise<LeadCardDTO> => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      const raw = await fetchClient<unknown>(`${API_BASE}/leads/${leadId}/reactivate`, {
        method: "POST",
        token,
        tenantId,
        body: JSON.stringify({}),
      });
      return keysToCamel<LeadCardDTO>(raw);
    },
    onSuccess: () => {
      // Invalidate frozen list and board
      queryClient.invalidateQueries({ queryKey: frozenKey() });
      // Invalidate all board queries — the lead reappears in its column
      queryClient.invalidateQueries({ queryKey: ["crm", "board"] });
    },
  });
}
