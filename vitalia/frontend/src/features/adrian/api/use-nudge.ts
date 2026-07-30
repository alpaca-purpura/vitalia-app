// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * use-nudge.ts — T-5 NEW.
 *
 * Mutation hook for sending a nudge (empujón) to a stalled conversation.
 * Calls: POST /api/v1/vitalia/inbox/conversations/{id}/nudge
 * (endpoint shipped in T-2 of vitalia-fase2-adrian-inbox)
 *
 * Idempotency: natural key (tenant, conv_id, 'nudge', day) on server side.
 * Client-side: button shows loading + disables on isPending to prevent double-click.
 *
 * On success: invalidates conversation detail + list (activity stream will show event).
 * On error: caller (NudgeButton) shows toast.
 *
 * "use client" required — uses React hooks (useAuth, useMutation).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import { conversationDetailKey, conversationsListKey } from "./_keys";

// ── Types ────────────────────────────────────────────────────────────────────

export interface NudgeInput {
  /** Conversation to nudge */
  conversationId: string;
  /** Optional reason shown in activity stream log (Spanish neutro) */
  reason?: string | null;
}

export interface NudgeResult {
  success: boolean;
  message: string;
  /** ISO 8601 timestamp of when the nudge was sent */
  sent_at: string;
}

// ── useNudge ─────────────────────────────────────────────────────────────────

/**
 * Mutation hook to send a nudge to a stalled conversation.
 *
 * Usage:
 *   const { mutate: nudge, isPending } = useNudge();
 *   nudge({ conversationId: conv.id });
 */
export function useNudge() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (input: NudgeInput): Promise<NudgeResult> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return fetchClient<NudgeResult>(
        `/api/v1/vitalia/inbox/conversations/${input.conversationId}/nudge`,
        {
          method: "POST",
          token,
          tenantId,
          clinicId,
          body: JSON.stringify({
            reason: input.reason ?? null,
          }),
        },
      );
    },
    onSettled: (_data, _err, input) => {
      // Refresh both list and detail so activity stream shows the nudge event
      void qc.invalidateQueries({
        queryKey: conversationDetailKey(input.conversationId),
      });
      void qc.invalidateQueries({ queryKey: conversationsListKey() });
    },
  });
}
