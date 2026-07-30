// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * use-wizard-url-state.ts — URL state management for wizard onboarding page.
 *
 * Uses Next.js native useSearchParams + useRouter (nuqs not installed — per
 * package.json check 2026-05-18). Mirrors the onboardingParsers spec from
 * 03-arch-fe.md § 3.6:
 *
 *   step:    WizardStep (default "greet")
 *   mode:    WizardMode | null
 *   draftId: string | null
 *
 * Uses router.replace() for intra-wizard state changes (no history entry).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type {
  WizardMode,
  WizardStep,
  WizardUrlState,
} from "../types/wizard-onboarding.types";

const VALID_STEPS: WizardStep[] = [
  "greet",
  "extract",
  "confirm",
  "simulate",
  "complete",
];
const VALID_MODES: WizardMode[] = ["libre", "guiado"];
const DEFAULT_STEP: WizardStep = "greet";

function parseStep(raw: string | null): WizardStep {
  if (raw && (VALID_STEPS as string[]).includes(raw)) {
    return raw as WizardStep;
  }
  return DEFAULT_STEP;
}

function parseMode(raw: string | null): WizardMode | null {
  if (raw && (VALID_MODES as string[]).includes(raw)) {
    return raw as WizardMode;
  }
  return null;
}

export interface UseWizardUrlStateReturn {
  /** Current URL state */
  urlState: WizardUrlState;
  /** Update one or more URL params (replace — no history push) */
  setUrlState: (patch: Partial<WizardUrlState>) => void;
  /** Navigate to next step (replace) */
  advanceStep: (nextStep: WizardStep) => void;
  /** Clear all URL state (replace with defaults) */
  resetUrlState: () => void;
}

/**
 * Hook: manages wizard onboarding URL state via Next.js searchParams.
 * All mutations use router.replace() (intra-wizard, no history entry).
 */
export function useWizardUrlState(): UseWizardUrlStateReturn {
  const router = useRouter();
  const searchParams = useSearchParams();

  const urlState = useMemo<WizardUrlState>(
    () => ({
      step: parseStep(searchParams.get("step")),
      mode: parseMode(searchParams.get("mode")),
      draftId: searchParams.get("draftId"),
    }),
    [searchParams],
  );

  const buildParams = useCallback(
    (patch: Partial<WizardUrlState>): URLSearchParams => {
      const next = new URLSearchParams(searchParams.toString());
      const merged = { ...urlState, ...patch };

      if (merged.step && merged.step !== DEFAULT_STEP) {
        next.set("step", merged.step);
      } else {
        next.delete("step");
      }

      if (merged.mode) {
        next.set("mode", merged.mode);
      } else {
        next.delete("mode");
      }

      if (merged.draftId) {
        next.set("draftId", merged.draftId);
      } else {
        next.delete("draftId");
      }

      return next;
    },
    [searchParams, urlState],
  );

  const setUrlState = useCallback(
    (patch: Partial<WizardUrlState>) => {
      const params = buildParams(patch);
      router.replace(`?${params.toString()}`);
    },
    [buildParams, router],
  );

  const advanceStep = useCallback(
    (nextStep: WizardStep) => {
      setUrlState({ step: nextStep });
    },
    [setUrlState],
  );

  const resetUrlState = useCallback(() => {
    router.replace("?");
  }, [router]);

  return { urlState, setUrlState, advanceStep, resetUrlState };
}
