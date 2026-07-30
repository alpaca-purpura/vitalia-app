// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-set-mode.ts — Mutation hook to change handler mode (ai ↔ human).
 *
 * Endpoint: PATCH /api/v1/vitalia/inbox/conversations/{conversationId}/mode
 *
 * Key features:
 * - OCC: expected_updated_at in the BODY (BE SetModeRequest) prevents stale write
 * - Optimistic update: immediately reflects mode change in UI
 * - 409 Conflict → rollback optimistic state + re-fetch + caller shows toast
 * - SC-03: OCC conflict scenario verified in test suite
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient, ApiError } from "@/lib/api/fetchClient";
import {
  conversationDetailKeyForInvalidation,
  conversationsListKeyForInvalidation,
} from "./_keys";
import type { ConversationDetail } from "../types/inbox.types";
import type { Conversation } from "@/features/crm-shared";

export interface SetModeInput {
  /** New handler mode */
  newMode: "ai" | "human";
  /** Whether the agent should wait for operator approval before sending */
  proposalRequired: boolean;
  /** OCC: conversation.updated_at used as ETag */
  expectedUpdatedAt: string;
}

export interface SetModeResult {
  conversation: Conversation;
}

/**
 * Mutation to toggle handler mode with optimistic UI update and OCC rollback.
 *
 * @param conversationId - The conversation to update.
 */
export function useSetMode(conversationId: string) {
  const { getToken} = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (input: SetModeInput): Promise<SetModeResult> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return fetchClient<SetModeResult>(
        `/api/v1/vitalia/inbox/conversations/${conversationId}/mode`,
        {
          method: "PATCH",
          token,
          tenantId,
          clinicId,
          body: JSON.stringify({
            mode: input.newMode,
            proposal_required: input.proposalRequired,
            expected_updated_at: input.expectedUpdatedAt,
          }),
        },
      );
    },
    onMutate: async (input) => {
      const key = conversationDetailKeyForInvalidation(conversationId);
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<ConversationDetail>(key);

      // Optimistic update: reflect mode change immediately
      if (previous) {
        qc.setQueryData<ConversationDetail>(key, {
          ...previous,
          conversation: {
            ...previous.conversation,
            handler_mode: input.newMode,
            proposal_required: input.proposalRequired,
          },
        });
      }

      return { previous };
    },
    onError: (err, _input, ctx) => {
      // Rollback optimistic update
      if (ctx?.previous) {
        qc.setQueryData(conversationDetailKeyForInvalidation(conversationId), ctx.previous);
      }
      // On OCC conflict: re-fetch fresh state so UI reflects server truth
      if (err instanceof ApiError && err.status === 409) {
        void qc.invalidateQueries({ queryKey: conversationDetailKeyForInvalidation(conversationId) });
      }
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: conversationDetailKeyForInvalidation(conversationId) });
      void qc.invalidateQueries({ queryKey: conversationsListKeyForInvalidation() });
    },
  });
}
