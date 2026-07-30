// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * notify.ts — Reminder notification mutation hook for Valeria Agenda.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * useSendNotificationMutation: POST /api/v1/notify/reminder
 * - Sends reminder via whatsapp/sms/email channel
 * - No cache invalidation (notification doesn't change appointment state)
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 * spec_anchor: 03-arch.md § 5.1 + 06-tickets.yaml T-12
 */

"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation } from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import { useClinicId } from "@/hooks/useClinicId";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import type { NotifyRequestDTO } from "../types/agenda-schema";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface SendNotificationResponse {
  messageId: string;
  channel: string;
  sentAt: string;
}

// ── useSendNotificationMutation ───────────────────────────────────────────────

/**
 * Mutation hook for sending a patient reminder.
 *
 * HIPAA-lite constraint: WhatsApp free tier is blocked for PHI content.
 * The BE ComplianceService validates channel before dispatch.
 * FE shows result of BE decision (success/blocked/failed).
 */
export function useSendNotificationMutation(tenantId: string) {
  const { getToken } = useAuth();
  const clinicId = useClinicId();
  const actorHeaders = useActorHeaders();

  return useMutation<SendNotificationResponse, Error, NotifyRequestDTO>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      // notify/reminder requires the HIPAA-lite dual filter + audit actor
      // (X-Clinic-ID + X-User-ID + X-User-Role) — only X-Tenant-ID → 422.
      return vitaliaFetch<SendNotificationResponse>("/api/v1/notify/reminder", {
        method: "POST",
        token,
        tenantId,
        headers: {
          ...actorHeaders,
          ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
        },
        body: JSON.stringify(payload),
      });
    },
    // No cache invalidation — reminders don't change appointment state
  });
}
