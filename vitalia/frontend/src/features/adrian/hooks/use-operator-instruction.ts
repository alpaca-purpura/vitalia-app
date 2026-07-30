// cap: adrian.inbox
"use client";

/**
 * use-operator-instruction.ts — React Query mutation hook for operator instructions.
 *
 * RN-13: Instruction is PERSISTENT per-conversation, steers ALL subsequent turns.
 * RN-14: handler_mode==='human' → direct (message to lead); else → instruction (to Adrián).
 * SC-8: POST /api/v1/adrian/conversations/{id}/instruction — lead NEVER receives this.
 *
 * tenant via useTenantId() — NEVER Clerk orgId (tenant-isolation.md).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { useTenantId } from "@/hooks/useTenantId";
import { operatorInstructionApi } from "../api/operator-instruction";
import type {
  SetOperatorInstructionRequest,
  ComposerMode,
} from "../types/operator-instruction";

/**
 * Pure helper — derives the composer effective mode from handler_mode.
 * Mirrors legacy MessageInput.tsx pattern.
 *
 * handler_mode === 'human' (Adrián paused) → 'direct' (text goes to lead)
 * handler_mode === 'ai'    (Adrián decide) → 'instruction' (steers Adrián, NOT to lead)
 */
export function getEffectiveMode(handlerMode: "ai" | "human"): ComposerMode {
  return handlerMode === "human" ? "direct" : "instruction";
}

/**
 * useOperatorInstruction — mutation hook for setting operator instructions.
 *
 * On success, invalidates the conversation query so the instruction chip
 * reflects the persisted state.
 */
export function useOperatorInstruction() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: SetOperatorInstructionRequest) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("Not authenticated");
      return operatorInstructionApi.set(token, tenantId, payload);
    },
    onSuccess: (_data, variables) => {
      // Invalidate conversation detail so chip reflects persisted instruction
      void queryClient.invalidateQueries({
        queryKey: ["adrian", "conversation", variables.conversationId],
      });
    },
  });
}
