// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * useContactAutosave.ts — Autosave hook for brand contact/presence section.
 *
 * Debounce 600ms on form change → useMutation PUT /lisa/marca/contact.
 * React Query invalidation on success.
 * AutosaveStatus propagated to AutosaveBadge.
 *
 * Pattern mirrors useIdentityAutosave.ts (T-5).
 * Partial payload — only changed fields sent per PUT.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 deliverables + 03-arch.md § 4.3
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marcaKeys } from "../api/marca";
import { updateContact } from "../api/marca-presence-api";
import type { BrandContactPatchPayload } from "../api/marca-presence-api";
import type { AutosaveStatus } from "@/components/marca/shared/AutosaveBadge";

const DEBOUNCE_MS = 600;

interface UseContactAutosaveOptions {
  tenantId: string;
  clinicId?: string | null;
}

/** Re-export API payload type for convenience — components import from here. */
export type ContactPatchPayload = BrandContactPatchPayload;

export interface UseContactAutosaveReturn {
  autosaveStatus: AutosaveStatus;
  savedAt: Date | null;
  /** Call this on every change to schedule a debounced PUT. */
  scheduleAutosave: (values: ContactPatchPayload) => void;
  /** Cancel any pending debounce (e.g., on component unmount). */
  cancelAutosave: () => void;
}

export function useContactAutosave({
  tenantId,
  clinicId,
}: UseContactAutosaveOptions): UseContactAutosaveReturn {
  const { getToken, userId } = useAuth();
  const queryClient = useQueryClient();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [autosaveStatus, setAutosaveStatus] = useState<AutosaveStatus>("idle");
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const mutation = useMutation({
    mutationFn: async (values: ContactPatchPayload) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return updateContact({ token, tenantId, clinicId, userId }, values);
    },
    onMutate: () => {
      setAutosaveStatus("saving");
    },
    onSuccess: () => {
      setAutosaveStatus("saved");
      setSavedAt(new Date());
      void queryClient.invalidateQueries({ queryKey: marcaKeys.contact(tenantId) });
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
    (values: ContactPatchPayload) => {
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
