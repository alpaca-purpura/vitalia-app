// cap: shell-organism.shell-vitalia
// story-origin: TBD
"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import type { ComplianceEventListResponse } from "../types/compliance.types";
import { vitaliaQueryKeys } from "./query-keys";

export interface ComplianceEventsFilters {
  severity?: "info" | "medium" | "high";
  event_type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export function useComplianceEvents(filters: ComplianceEventsFilters = {}) {
  const { getToken, isLoaded, isSignedIn, sessionClaims } = useAuth();

  return useQuery({
    queryKey: vitaliaQueryKeys.compliance.events(filters),
    queryFn: async (): Promise<ComplianceEventListResponse> => {
      const token = await getToken();
      const tenantId = (
        sessionClaims?.public_metadata as Record<string, unknown>
      )?.active_tenant_id as string | undefined;
      if (!token) throw new Error("Not authenticated");
      const params = new URLSearchParams();
      if (filters.severity) params.set("severity", filters.severity);
      if (filters.event_type) params.set("event_type", filters.event_type);
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (filters.page) params.set("page", String(filters.page));
      if (filters.page_size) params.set("page_size", String(filters.page_size));
      const query = params.toString() ? `?${params.toString()}` : "";
      return vitaliaFetch<ComplianceEventListResponse>(
        `/api/v1/vitalia/medical-compliance/events${query}`,
        { token, tenantId: tenantId ?? "" },
      );
    },
    enabled: isLoaded && isSignedIn === true,
  });
}
