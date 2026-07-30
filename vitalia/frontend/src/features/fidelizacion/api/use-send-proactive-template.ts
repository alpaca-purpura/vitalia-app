// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * use-send-proactive-template — Mutation hook for Adrián recordatorio.
 *
 * Endpoint: POST /api/v1/vitalia/fidelization/patients/{patientId}/send-proactive
 * Header: Idempotency-Key: crypto.randomUUID() (per 03-arch-fe.md § 4)
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  SendProactiveRequest,
  SendProactiveResponse,
} from "../types/re-engagement";

interface SendProactiveArgs {
  patientId: string;
  payload: SendProactiveRequest;
}

/**
 * Mutation for sending proactive WhatsApp template via Adrián sales agent.
 * Invalidates fidelización + inbox queries on success.
 */
export function useSendProactiveTemplate() {
  const queryClient = useQueryClient();
  const { getToken} = useAuth();
  const tenantId = useTenantId();

  return useMutation({
    mutationFn: async ({ patientId, payload }: SendProactiveArgs) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");

      const idempotencyKey = crypto.randomUUID();

      return vitaliaFetch<SendProactiveResponse>(
        `/api/v1/vitalia/fidelization/patients/${patientId}/send-proactive`,
        {
          token,
          tenantId, method: "POST",
          body: JSON.stringify(payload),
          headers: { "Idempotency-Key": idempotencyKey },
        },
      );
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fidelizacion"] });
      void queryClient.invalidateQueries({
        queryKey: ["inbox", "conversations"],
      });
    },
  });
}
