// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * usePersonalityAutosave.ts — Autosave hook for brand personality (Voz y tono).
 *
 * Debounce 600ms on form change → useMutation PATCH /lisa/marca/personality.
 * React Query invalidation on success.
 * AutosaveStatus propagated to AutosaveBadge.
 *
 * Pattern mirrors useIdentityAutosave.ts (T-5):
 *   - useAuth() → getToken() + orgId
 *   - scheduleAutosave(values) debounces mutation
 *   - Status transitions: idle → dirty → saving → saved | error
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 deliverables + 03-arch.md § 4
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marcaKeys } from "../api/marca";
import { updatePersonality } from "../api/marca-voice-api";
import type { AutosaveStatus } from "@/components/marca/shared/AutosaveBadge";
import type { PersonalityPatchPayload } from "../api/marca-voice-api";

const DEBOUNCE_MS = 600;

interface UsePersonalityAutosaveOptions {
  tenantId: string;
  clinicId?: string | null;
}

export interface UsePersonalityAutosaveReturn {
  autosaveStatus: AutosaveStatus;
  savedAt: Date | null;
  /** Call on every RHF form change to schedule a debounced save. */
  scheduleAutosave: (values: PersonalityPatchPayload) => void;
  /** Cancel any pending debounce (on unmount or manual cancel). */
  cancelAutosave: () => void;
}

export function usePersonalityAutosave({
  tenantId,
  clinicId,
}: UsePersonalityAutosaveOptions): UsePersonalityAutosaveReturn {
  const { getToken, userId } = useAuth();
  const queryClient = useQueryClient();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [autosaveStatus, setAutosaveStatus] = useState<AutosaveStatus>("idle");
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const mutation = useMutation({
    mutationFn: async (values: PersonalityPatchPayload) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return updatePersonality({ token, tenantId, clinicId, userId }, values);
    },
    onMutate: () => {
      setAutosaveStatus("saving");
    },
    onSuccess: () => {
      setAutosaveStatus("saved");
      setSavedAt(new Date());
      void queryClient.invalidateQueries({
        queryKey: marcaKeys.personality(tenantId),
      });
    },
    onError: () => {
      setAutosaveStatus("error");
    },
  });

  const cancelAutosave = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const scheduleAutosave = useCallback(
    (values: PersonalityPatchPayload) => {
      setAutosaveStatus("dirty");
      cancelAutosave();
      timerRef.current = setTimeout(() => {
        mutation.mutate(values);
      }, DEBOUNCE_MS);
    },
    [mutation, cancelAutosave],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancelAutosave();
    };
  }, [cancelAutosave]);

  return { autosaveStatus, savedAt, scheduleAutosave, cancelAutosave };
}
