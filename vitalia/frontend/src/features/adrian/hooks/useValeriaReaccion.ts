// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * useValeriaReaccion.ts — T-5 NEW.
 *
 * Basic hook: when a conversation is opened, derives a context message
 * and 1-2 suggested actions for the Valeria sidebar panel.
 *
 * MVP implementation (03-arch-fe.md § 7):
 *   - On convId change → POST best-effort to Valeria chat context endpoint
 *   - Returns: { contextMessage, suggestedActions, isLoading, isError }
 *   - Graceful degradation: if POST fails, returns null/empty (never throws)
 *   - Non-PHI context only: stage, channel, offer (NO patient names, diagnoses)
 *
 * "use client" required — uses React hooks.
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";

// ── Types ────────────────────────────────────────────────────────────────────

export interface ValeriaReaccionResult {
  /** Brief context message for Valeria to show about this conversation */
  contextMessage: string | null;
  /** 1-2 suggested quick actions Valeria offers to the operator */
  suggestedActions: ValeriaAction[];
  isLoading: boolean;
  isError: boolean;
}

export interface ValeriaAction {
  id: string;
  label: string;
  /** Valeria prompt to pre-fill when operator clicks the suggestion */
  promptHint: string;
}

// Default empty result (graceful degradation)
const EMPTY_RESULT: ValeriaReaccionResult = {
  contextMessage: null,
  suggestedActions: [],
  isLoading: false,
  isError: false,
};

// ── useValeriaReaccion ───────────────────────────────────────────────────────

/**
 * Derives a Valeria context message + suggested actions for the active conversation.
 *
 * MVP: basic local derivation (no network call) with hardcoded suggestions.
 * A future story will add a real POST to the Valeria conversation context endpoint.
 *
 * @param convId - UUID of the active conversation (null = no active conv)
 */
export function useValeriaReaccion(
  convId: string | null,
): ValeriaReaccionResult {
  const { isLoaded, isSignedIn } = useAuth();
  const tenantId = useTenantId();
  const [result, setResult] = useState<ValeriaReaccionResult>(EMPTY_RESULT);

  useEffect(() => {
    if (!convId || !isLoaded || !isSignedIn || !tenantId) {
      setResult(EMPTY_RESULT);
      return;
    }

    // MVP: derive context locally (no network call in initial implementation)
    // A follow-up story will replace this with a real POST to Valeria context API.
    setResult({
      contextMessage: "Adrián está atendiendo esta conversación.",
      suggestedActions: [
        {
          id: "ask-stage",
          label: "¿En qué etapa está?",
          promptHint: `¿En qué etapa del embudo está la conversación ${convId}?`,
        },
        {
          id: "suggest-next",
          label: "¿Qué sigue?",
          promptHint: `¿Cuál sería el siguiente paso para avanzar esta conversación?`,
        },
      ],
      isLoading: false,
      isError: false,
    });
  }, [convId, isLoaded, isSignedIn, tenantId]);

  return result;
}
