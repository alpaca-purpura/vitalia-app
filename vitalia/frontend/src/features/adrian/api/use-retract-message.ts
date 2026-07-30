// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-retract-message.ts — Mutation hook for retracting (undoing) a sent message.
 *
 * Endpoint: POST /api/v1/vitalia/inbox/conversations/{conversationId}/messages/{messageId}/revert
 *
 * Key features:
 * - OCC: If-Match header with conversation.updated_at prevents stale retract
 * - 409 Conflict → conversation was updated; refresh + show conflict toast
 * - 410 Gone → action receipt expired (5min window); show expired toast
 * - Optimistic: marks message as retracted immediately; rolls back on error
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
import type { Message } from "../types/inbox.types";

export interface RetractMessageInput {
  conversationId: string;
  messageId: string;
  /** OCC: conversation.updated_at used as ETag for If-Match header */
  expectedUpdatedAt: string;
}

export interface RetractMessageResult {
  message: Message;
}

/**
 * Mutation to retract (undo) a sent message within the 5-minute action receipt window.
 */
export function useRetractMessage() {
  const { getToken} = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (
      input: RetractMessageInput,
    ): Promise<RetractMessageResult> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return fetchClient<RetractMessageResult>(
        `/api/v1/vitalia/inbox/conversations/${input.conversationId}/messages/${input.messageId}/revert`,
        {
          method: "POST",
          token,
          tenantId, clinicId,
          headers: {
            "If-Match": input.expectedUpdatedAt,
          },
          body: JSON.stringify({}),
        },
      );
    },
    onMutate: async (input) => {
      const detailKey = conversationDetailKeyForInvalidation(input.conversationId);
      await qc.cancelQueries({ queryKey: detailKey });
      const previousDetail = qc.getQueryData<ConversationDetail>(detailKey);

      // Optimistic: mark message as retracted
      if (previousDetail) {
        qc.setQueryData<ConversationDetail>(detailKey, {
          ...previousDetail,
          messages: previousDetail.messages.map((msg) =>
            msg.id === input.messageId
              ? { ...msg, retracted_at: new Date().toISOString() }
              : msg,
          ),
          action_receipts: previousDetail.action_receipts.filter(
            (r) => r.message_id !== input.messageId,
          ),
        });
      }

      return { previousDetail };
    },
    onError: (err, input, ctx) => {
      // Rollback optimistic update
      if (ctx?.previousDetail) {
        qc.setQueryData(
          conversationDetailKeyForInvalidation(input.conversationId),
          ctx.previousDetail,
        );
      }
      // For 409: re-fetch to get fresh state
      if (err instanceof ApiError && err.status === 409) {
        void qc.invalidateQueries({
          queryKey: conversationDetailKeyForInvalidation(input.conversationId),
        });
      }
      // 410 is handled by caller (show expired toast)
    },
    onSettled: (_data, _err, input) => {
      void qc.invalidateQueries({
        queryKey: conversationDetailKeyForInvalidation(input.conversationId),
      });
      void qc.invalidateQueries({ queryKey: conversationsListKeyForInvalidation() });
    },
  });
}
