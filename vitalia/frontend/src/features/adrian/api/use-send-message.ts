// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-send-message.ts — Mutation hook for sending a message in a conversation.
 *
 * Endpoint: POST /api/v1/vitalia/inbox/conversations/{conversationId}/messages
 *
 * Key features:
 * - Idempotency-Key header (client-generated UUID) prevents duplicate sends
 * - Optimistic update: appends message to conversation detail cache immediately
 * - Invalidates conversation list + detail on settle
 *
 * SC-01: Happy path — send message → ActionReceipt returned → undo chip appears
 * SC-02: Audio message → transcription_text populated server-side
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import {
  conversationDetailKeyForInvalidation,
  conversationsListKeyForInvalidation,
} from "./_keys";
import type { Message } from "../types/inbox.types";
import type { ConversationDetail } from "../types/inbox.types";

export interface SendMessageInput {
  conversationId: string;
  bodyText?: string | null;
  mediaUrl?: string | null;
  mediaKind?: "audio" | "image" | "video" | "document" | null;
  mediaDurationS?: number | null;
  handlerModeOverride?: "ai" | "human" | null;
  /** Client-generated UUID — prevents duplicate sends on retry */
  idempotencyKey: string;
}

/**
 * Mutation to send a message.
 * Returns the persisted Message with action_receipt_expires_at for undo chip.
 */
export function useSendMessage() {
  const { getToken} = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (input: SendMessageInput): Promise<Message> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return fetchClient<Message>(
        `/api/v1/vitalia/inbox/conversations/${input.conversationId}/messages`,
        {
          method: "POST",
          token,
          tenantId, clinicId,
          headers: {
            "Idempotency-Key": input.idempotencyKey,
          },
          body: JSON.stringify({
            body_text: input.bodyText ?? null,
            media_url: input.mediaUrl ?? null,
            media_kind: input.mediaKind ?? null,
            media_duration_s: input.mediaDurationS ?? null,
            handler_mode_override: input.handlerModeOverride ?? null,
            idempotency_key: input.idempotencyKey,
          }),
        },
      );
    },
    onMutate: async (input) => {
      const detailKey = conversationDetailKeyForInvalidation(input.conversationId);
      await qc.cancelQueries({ queryKey: detailKey });
      const previousDetail = qc.getQueryData<ConversationDetail>(detailKey);
      // Optimistic: add a placeholder message
      if (previousDetail) {
        const optimisticMsg: Message = {
          id: `optimistic-${input.idempotencyKey}`,
          conversation_id: input.conversationId,
          sender_type: "agent_human",
          sender_user_id: null,
          body_text: input.bodyText ?? null,
          media_kind: input.mediaKind ?? null,
          media_url: input.mediaUrl ?? null,
          media_duration_s: input.mediaDurationS ?? null,
          transcription_text: null,
          transcription_confidence: null,
          retracted_at: null,
          retract_succeeded: null,
          handler_mode:
            input.handlerModeOverride ??
            previousDetail.conversation.handler_mode,
          sent_at: new Date().toISOString(),
          action_receipt_expires_at: null,
        };
        qc.setQueryData<ConversationDetail>(detailKey, {
          ...previousDetail,
          messages: [...previousDetail.messages, optimisticMsg],
        });
      }
      return { previousDetail };
    },
    onError: (_err, input, ctx) => {
      // Rollback optimistic update on error
      if (ctx?.previousDetail) {
        qc.setQueryData(conversationDetailKeyForInvalidation(input.conversationId), ctx.previousDetail);
      }
    },
    onSettled: (_data, _err, input) => {
      void qc.invalidateQueries({
        queryKey: conversationDetailKeyForInvalidation(input.conversationId),
      });
      void qc.invalidateQueries({ queryKey: conversationsListKeyForInvalidation() });
    },
  });
}
