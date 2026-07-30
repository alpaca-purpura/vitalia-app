// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * useVisualsAutosave.ts — Autosave hook for brand visuals section.
 *
 * Mirrors useIdentityAutosave pattern for PUT /lisa/marca/visuals.
 * Debounce 600ms on form change → useMutation.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 deliverables
 * downstream-regression-na: brand-local vitalia FE hook; no cross-brand consumers
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marcaKeys, updateVisuals } from "../api/marca";
import type { AutosaveStatus } from "@/components/marca/shared/AutosaveBadge";
import type { ClinicVisualsFormValues } from "../types/marca/visuals-schema";

const DEBOUNCE_MS = 600;

interface UseVisualsAutosaveOptions {
  tenantId: string;
  clinicId?: string | null;
}

export interface UseVisualsAutosaveReturn {
  autosaveStatus: AutosaveStatus;
  savedAt: Date | null;
  scheduleAutosave: (values: ClinicVisualsFormValues) => void;
  cancelAutosave: () => void;
}

export function useVisualsAutosave({
  tenantId,
  clinicId,
}: UseVisualsAutosaveOptions): UseVisualsAutosaveReturn {
  const { getToken, userId } = useAuth();
  const queryClient = useQueryClient();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [autosaveStatus, setAutosaveStatus] = useState<AutosaveStatus>("idle");
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const mutation = useMutation({
    mutationFn: async (values: ClinicVisualsFormValues) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return updateVisuals({ token, tenantId, clinicId, userId }, values);
    },
    onMutate: () => {
      setAutosaveStatus("saving");
    },
    onSuccess: () => {
      setAutosaveStatus("saved");
      setSavedAt(new Date());
      void queryClient.invalidateQueries({ queryKey: marcaKeys.visuals(tenantId) });
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
    (values: ClinicVisualsFormValues) => {
      setAutosaveStatus("dirty");
      cancelAutosave();
      timerRef.current = setTimeout(() => {
        mutation.mutate(values);
      }, DEBOUNCE_MS);
    },
    [mutation, cancelAutosave],
  );

  useEffect(() => {
    return () => {
      cancelAutosave();
    };
  }, [cancelAutosave]);

  return { autosaveStatus, savedAt, scheduleAutosave, cancelAutosave };
}
