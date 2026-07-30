// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-pause-adrian.ts — Mutation hook to pause Adrián (60 min or permanent).
 *
 * Endpoint: POST /api/v1/vitalia/inbox/conversations/{conversationId}/pause
 *
 * Pausing sets conversation.pause_until = now + duration_minutes on the server.
 * 60 min → duration_minutes=60. "Permanent" → a far-future duration (the BE has
 * no indefinite flag yet; PERMANENT_PAUSE_MINUTES ≈ 100 years is effectively
 * permanent for a conversation). Invalidates detail to refresh the paused state.
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
import type { Conversation } from "@/features/crm-shared";

/** Far-future duration used for "Pausar permanente" (BE has no indefinite flag). */
export const PERMANENT_PAUSE_MINUTES = 52_560_000; // ~100 years

export interface PauseAdrianInput {
  conversationId: string;
  /** Pause duration in minutes (60 = 1h · PERMANENT_PAUSE_MINUTES = permanent) */
  durationMinutes: number;
}

export interface PauseAdrianResult {
  conversation: Conversation;
}

/**
 * Mutation to pause Adrián for 60 minutes in the given conversation.
 */
export function usePauseAdrian() {
  const { getToken} = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (input: PauseAdrianInput): Promise<PauseAdrianResult> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return fetchClient<PauseAdrianResult>(
        `/api/v1/vitalia/inbox/conversations/${input.conversationId}/pause`,
        {
          method: "POST",
          token,
          tenantId,
          clinicId,
          body: JSON.stringify({
            duration_minutes: input.durationMinutes,
          }),
        },
      );
    },
    onSettled: (_data, _err, input) => {
      void qc.invalidateQueries({
        queryKey: conversationDetailKeyForInvalidation(input.conversationId),
      });
      void qc.invalidateQueries({ queryKey: conversationsListKeyForInvalidation() });
    },
  });
}
