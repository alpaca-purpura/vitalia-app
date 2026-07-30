// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * fiscal.ts — Fiscal document emission mutation hook for Valeria Agenda.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * useFiscalEmitMutation: POST /api/v1/fiscal/emit
 * - Emits boleta/factura/ticket for a payment record
 * - Invalidates grid + appointment detail on success
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 * spec_anchor: 03-arch.md § 5.1 + 06-tickets.yaml T-12
 */

"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import { useClinicId } from "@/hooks/useClinicId";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import type { FiscalDocument } from "../types/agenda.types";
import { agendaKeys } from "./agenda";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FiscalEmitVariables {
  paymentId: string;
  appointmentId: string;
  docType: "factura" | "boleta" | "ticket";
}

// ── useFiscalEmitMutation ─────────────────────────────────────────────────────

/**
 * Mutation hook for emitting a fiscal document (boleta/factura/ticket).
 *
 * Dependency: vitalia-fiscal-emission-pe story (state: refining).
 * This hook connects to the fiscal adapter — in tests, use MSW/vi.fn() to stub.
 */
export function useFiscalEmitMutation(tenantId: string) {
  const { getToken } = useAuth();
  const clinicId = useClinicId();
  const actorHeaders = useActorHeaders();
  const queryClient = useQueryClient();

  return useMutation<FiscalDocument, Error, FiscalEmitVariables>({
    mutationFn: async ({ paymentId, docType }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      // fiscal/emit requires the HIPAA-lite dual filter + audit actor
      // (X-Clinic-ID + X-User-ID + X-User-Role) — only X-Tenant-ID → 422.
      return vitaliaFetch<FiscalDocument>("/api/v1/fiscal/emit", {
        method: "POST",
        token,
        tenantId,
        headers: {
          ...actorHeaders,
          ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
        },
        body: JSON.stringify({
          payment_id: paymentId,
          doc_type: docType,
        }),
      });
    },
    onSuccess: (_, { appointmentId }) => {
      // Invalidate grid + appointment detail (fiscal badge updates)
      void queryClient.invalidateQueries({ queryKey: agendaKeys.all(tenantId) });
      void queryClient.invalidateQueries({
        queryKey: agendaKeys.detail(tenantId, appointmentId),
      });
    },
  });
}
