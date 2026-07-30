// cap: __shared__
// story-origin: TBD
"use client";

/**
 * use-leads.ts — React Query hook for CRM leads list (paginated).
 *
 * Endpoint: GET /api/v1/vitalia/crm/leads
 *
 * PHI constraint: lead.name/phone/email must be rendered via PiiMaskedSpan.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import type { Lead } from "../types";

export interface LeadsFilters {
  stage?: string | null;
  search?: string | null;
  page?: number;
  pageSize?: number;
}

export interface LeadsResponse {
  leads: Lead[];
  total: number;
  page: number;
  page_size: number;
}

function buildLeadsUrl(filters: LeadsFilters): string {
  const params = new URLSearchParams();
  if (filters.stage) params.set("stage", filters.stage);
  if (filters.search) params.set("search", filters.search);
  if (filters.page != null) params.set("page", String(filters.page));
  if (filters.pageSize != null)
    params.set("page_size", String(filters.pageSize));
  const qs = params.toString();
  return `/api/v1/crm/leads${qs ? `?${qs}` : ""}`;
}

/**
 * Fetches the paginated leads list.
 *
 * @param filters - Optional filters
 */
export function useLeads(filters: LeadsFilters = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: ["crm", "leads", filters],
    queryFn: async () => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      // BE (crm LeadListResponse) returns { items, total, limit, offset }.
      // Adapt to the FE LeadsResponse shape { leads, total, page, page_size }.
      const res = await fetchClient<{
        items: Lead[];
        total: number;
        limit: number;
        offset: number;
      }>(buildLeadsUrl(filters), {
        token,
        tenantId,
        clinicId,
      });
      return {
        leads: res.items,
        total: res.total,
        page: res.limit > 0 ? Math.floor(res.offset / res.limit) + 1 : 1,
        page_size: res.limit,
      } satisfies LeadsResponse;
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 30_000,
  });
}
