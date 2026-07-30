// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-proactive-outbound.ts — Mutation hook for proactive outbound conversation.
 *
 * Endpoint: POST /api/v1/vitalia/inbox/proactive-outbound
 *
 * Starts a new outbound conversation from the ProactiveOutboundModal.
 * Server-side: ComplianceService validates channel before sending
 * (blocks WhatsApp marketing templates on unencrypted tier).
 *
 * Invalidates conversations list on success to show new conversation.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { useClinicId } from "@/hooks/useClinicId";
import { fetchClient } from "@/lib/api/fetchClient";
import { conversationsListKey } from "./_keys";
import type { Conversation } from "@/features/crm-shared";

export interface ProactiveOutboundInput {
  /** Lead/patient ID to contact */
  leadId: string;
  /** WhatsApp template ID */
  templateId: string;
  /** Template variable values keyed by placeholder name */
  templateVars?: Record<string, string>;
  /** Channel to use */
  channel: "whatsapp" | "instagram" | "facebook_messenger";
}

export interface ProactiveOutboundResult {
  conversation: Conversation;
}

/**
 * Mutation to initiate a proactive outbound conversation.
 * Blocked by ComplianceService if channel is unencrypted + medical content.
 */
export function useProactiveOutbound() {
  const { getToken} = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (
      input: ProactiveOutboundInput,
    ): Promise<ProactiveOutboundResult> => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      return fetchClient<ProactiveOutboundResult>(
        "/api/v1/vitalia/inbox/proactive-outbound",
        {
          method: "POST",
          token,
          tenantId, clinicId,
          body: JSON.stringify({
            lead_id: input.leadId,
            template_id: input.templateId,
            template_vars: input.templateVars ?? {},
            channel: input.channel,
          }),
        },
      );
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: conversationsListKey() });
    },
  });
}
