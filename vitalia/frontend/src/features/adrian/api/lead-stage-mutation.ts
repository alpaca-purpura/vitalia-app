// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * lead-stage-mutation.ts — React Query mutation for stage transitions (T-FE-2).
 *
 * useLeadStageMutation: PATCH /api/v1/crm/leads/{id}/stage
 * - On success: invalidates board + lead detail RQ caches
 * - On 409 (optimistic lock): mutation error → UI rollback + toast (SC-5)
 * - On 422 (invalid skip): mutation error → UI rollback + toast (SC-2)
 * - Optimistic update (local state) managed in AdrianEmbudoView via onMutate
 *
 * spec_anchor: 03-arch-fe.md § api/lead-stage-mutation.ts + § Data layer
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import { boardKey, leadDetailKey, stageMutationKey } from "./_embudo-keys";
import type {
  StageTransitionPayload,
  StageTransitionResponse,
  BoardFilters,
} from "../types/embudo.types";

const API_BASE = "/api/v1/crm";

export interface LeadStageMutationVars extends StageTransitionPayload {
  leadId: string;
}

/**
 * useLeadStageMutation — PATCH /crm/leads/{id}/stage.
 *
 * Invalidates on success:
 *   - ['crm','board',...] — refreshes all board columns
 *   - ['crm','lead',id,'detail'] — refreshes lead detail if open
 *
 * Error codes surfaced to caller:
 *   - 409: optimistic lock conflict (SC-5)
 *   - 422: invalid stage transition (SC-2) — body includes allowed_next[]
 *   - 403: reservado gated (RN-4/5)
 */
export function useLeadStageMutation(currentFilters?: BoardFilters) {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: stageMutationKey(),
    mutationFn: async ({
      leadId,
      toStage,
      reason,
      note,
      version,
      triggeredBy = "manual_override",
    }: LeadStageMutationVars): Promise<StageTransitionResponse> => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      if (!tenantId) throw new Error("Sin tenant ID");

      const raw = await fetchClient<unknown>(
        `${API_BASE}/leads/${leadId}/stage`,
        {
          method: "PATCH",
          token,
          tenantId,
          body: JSON.stringify({
            to_stage: toStage,
            reason: reason ?? null,
            note: note ?? null,
            version,
            triggered_by: triggeredBy,
          }),
        },
      );
      return keysToCamel<StageTransitionResponse>(raw);
    },
    onSuccess: (_data, vars) => {
      // Invalidate board — all filter variants
      queryClient.invalidateQueries({ queryKey: boardKey(currentFilters) });
      // Invalidate lead detail if it was open
      queryClient.invalidateQueries({ queryKey: leadDetailKey(vars.leadId) });
      // ★ Cross-invalidation: Inbox + Embudo must stay synced on stage changes
      // useConversationDetail uses ["crm","conversation",conversationId] (contains lead + stage)
      // invalidate the entire crm.conversation namespace to refresh all open conversations
      queryClient.invalidateQueries({ queryKey: ["crm", "conversation"] });
      // Also invalidate whole inbox namespace as fallback for other refs
      queryClient.invalidateQueries({ queryKey: ["adrian", "inbox"] });
    },
    // Note: optimistic rollback is handled in AdrianEmbudoView via onMutate/onError
    // callbacks at the call site (not here — keeps mutation clean, state in store).
  });
}
