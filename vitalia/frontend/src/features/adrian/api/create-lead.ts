// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * create-lead.ts — React Query mutation for creating a new lead (T-FE-3).
 *
 * useCreateLead: POST /api/v1/crm/leads → LeadCardDTO (created, status 201)
 *
 * On success: invalidates board so the new lead appears in its column.
 * Submit flow: POST → redirect to /embudo?view=kanban&highlight={id}
 * (NewLeadPage handles the router.push; this hook does the API call).
 *
 * spec_anchor: 03-arch-fe.md § api/create-lead.ts + 01-spec.md § V5 SC-nuevo
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import type { LeadCardDTO, LeadFunnelStage } from "../types/embudo.types";

const API_BASE = "/api/v1/crm";

// ── Payload ───────────────────────────────────────────────────────────────────

export interface CreateLeadPayload {
  /** PHI: encrypted at rest, non-PHI marketing prospect name */
  name: string;
  /** Channel slug (whatsapp / instagram / meta / referido / web / otro) */
  channel: string;
  /** At least one contact field required (RHF form validates ≥1) */
  phone: string | null;
  email: string | null;
  /** Default: interesado */
  stage: LeadFunnelStage;
  serviceInterest: string | null;
  tags: string[];
  notes: string;
}

/**
 * useCreateLead — POST /crm/leads.
 *
 * On success: invalidates all board queries so the new lead appears.
 * Caller (NewLeadPage) handles the redirect + highlight.
 */
export function useCreateLead() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateLeadPayload): Promise<LeadCardDTO> => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      const raw = await fetchClient<unknown>(`${API_BASE}/leads`, {
        method: "POST",
        token,
        tenantId,
        body: JSON.stringify({
          name: payload.name,
          channel: payload.channel,
          phone: payload.phone,
          email: payload.email,
          stage: payload.stage,
          service_interest: payload.serviceInterest,
          tags: payload.tags,
          notes: payload.notes,
        }),
      });
      return keysToCamel<LeadCardDTO>(raw);
    },
    onSuccess: () => {
      // Invalidate all board variants — new lead appears in its column
      queryClient.invalidateQueries({ queryKey: ["crm", "board"] });
    },
  });
}
