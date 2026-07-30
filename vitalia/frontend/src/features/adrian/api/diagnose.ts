// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * diagnose.ts — React Query hook for lead AI diagnose (T-FE-3).
 *
 * useDiagnose: POST /api/v1/crm/leads/{id}/diagnose → DiagnoseResponse
 *
 * Triggered on-demand from RecuperarView when operator wants AI recommendation
 * for a frozen lead. Lazy-fetch via useMutation (not a query).
 *
 * spec_anchor: 03-arch-fe.md § api/diagnose.ts + 01-spec.md § V4
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import type { DiagnoseResponse } from "../types/embudo.types";

const API_BASE = "/api/v1/crm";

/**
 * useDiagnose — triggers AI diagnosis for a frozen lead.
 *
 * Returns: DiagnoseResponse { leadId, recommendation, urgency, suggestedAction }
 * Each call is a fresh POST (not cached) — diagnosis is stateless.
 */
export function useDiagnose() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();

  return useMutation({
    mutationFn: async (leadId: string): Promise<DiagnoseResponse> => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      const raw = await fetchClient<unknown>(
        `${API_BASE}/leads/${leadId}/diagnose`,
        {
          method: "POST",
          token,
          tenantId,
          body: JSON.stringify({}),
        },
      );
      return keysToCamel<DiagnoseResponse>(raw);
    },
  });
}
