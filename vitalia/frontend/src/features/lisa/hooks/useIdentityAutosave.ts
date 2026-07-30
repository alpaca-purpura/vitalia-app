// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * useIdentityAutosave.ts — Autosave hook for brand identity section.
 *
 * Debounce 600ms on form change → useMutation PUT /lisa/marca/identity.
 * React Query invalidation on success.
 * AutosaveStatus propagated to AutosaveBadge.
 *
 * Pattern:
 *   - useAuth() → getToken() + orgId
 *   - RHF watch() triggers debounced mutation
 *   - Status transitions: idle → dirty (on change) → saving → saved | error
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 deliverables + 03-arch.md § 4
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */


import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marcaKeys, updateIdentity } from "../api/marca";
import type { AutosaveStatus } from "@/components/marca/shared/AutosaveBadge";
import type { IdentityFormValues } from "../types/marca/identity-schema";

const DEBOUNCE_MS = 600;

interface UseIdentityAutosaveOptions {
  tenantId: string;
  clinicId?: string | null;
}

export interface UseIdentityAutosaveReturn {
  autosaveStatus: AutosaveStatus;
  savedAt: Date | null;
  /** Call this on every RHF change (or useEffect watching form.watch()). */
  scheduleAutosave: (values: IdentityFormValues) => void;
  /** Cancel any pending debounce (e.g., on component unmount). */
  cancelAutosave: () => void;
}

export function useIdentityAutosave({
  tenantId,
  clinicId,
}: UseIdentityAutosaveOptions): UseIdentityAutosaveReturn {
  const { getToken, userId } = useAuth();
  const queryClient = useQueryClient();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [autosaveStatus, setAutosaveStatus] = useState<AutosaveStatus>("idle");
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const mutation = useMutation({
    mutationFn: async (values: IdentityFormValues) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return updateIdentity({ token, tenantId, clinicId, userId }, values);
    },
    onMutate: () => {
      setAutosaveStatus("saving");
    },
    onSuccess: () => {
      setAutosaveStatus("saved");
      setSavedAt(new Date());
      void queryClient.invalidateQueries({ queryKey: marcaKeys.identity(tenantId) });
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
    (values: IdentityFormValues) => {
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
