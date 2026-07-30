// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * lead.ts — React Query hooks for lead detail and timeline (T-FE-3).
 *
 * useLeadDetail: GET /api/v1/crm/leads/{id}/detail → LeadDetailResponse
 * useLeadTimeline: GET /api/v1/crm/leads/{id}/transitions → TimelineResponse
 *
 * - Disabled when tenantId=null (tenant-isolation.md)
 * - Disabled when leadId='' (no PHI in URL, leadId must be UUID)
 * - graceful-degradation: timeout (30s via fetchClient) + error boundary catches
 *
 * spec_anchor: 03-arch-fe.md § api/lead.ts + 01-spec.md § V3
 * downstream-regression-na: brand-local vitalia FE; no cross-brand consumers
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import { leadDetailKey, leadTransitionsKey } from "./_embudo-keys";
import type { LeadDetailResponse, TimelineResponse } from "../types/embudo.types";

const API_BASE = "/api/v1/crm";

/**
 * useLeadDetail — fetches full lead detail (Resumen view).
 *
 * Returns: LeadDetailResponse { lead, scoreBreakdown, autonomy }
 * Disabled when leadId='' or tenantId=null.
 * staleTime 60s — lead detail changes on stage transitions; moderate freshness.
 */
export function useLeadDetail(leadId: string) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: leadDetailKey(leadId),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      const raw = await fetchClient<unknown>(
        `${API_BASE}/leads/${leadId}/detail`,
        { token, tenantId },
      );
      return keysToCamel<LeadDetailResponse>(raw);
    },
    enabled: isLoaded && !!isSignedIn && !!tenantId && !!leadId,
    staleTime: 60_000, // 60s — detail changes on stage transitions
  });
}

/**
 * useLeadTimeline — fetches lead activity timeline (Historial view).
 *
 * RN-2 firewall: server-side filters out clinical data before responding.
 * This hook receives only commercial activities (stage moves, messages, deposits).
 *
 * Returns: TimelineResponse { events[] }
 * Disabled when leadId='' or tenantId=null.
 */
export function useLeadTimeline(leadId: string) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();

  return useQuery({
    queryKey: leadTransitionsKey(leadId),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      const raw = await fetchClient<unknown>(
        `${API_BASE}/leads/${leadId}/transitions`,
        { token, tenantId },
      );
      return keysToCamel<TimelineResponse>(raw);
    },
    enabled: isLoaded && !!isSignedIn && !!tenantId && !!leadId,
    staleTime: 30_000, // 30s — timeline updates with each agent turn
  });
}
