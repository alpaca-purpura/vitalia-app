// cap: adrian.inbox
/**
 * operator-instruction.ts — API client for operator-instruction endpoint.
 *
 * Endpoint: POST /api/v1/adrian/conversations/{conversation_id}/instruction
 * Delivered by T-BE-3 (commit cdfbaaa6).
 *
 * fetchClient auto-injects X-Tenant-ID + Authorization from token+tenantId params.
 *
 * downstream-regression-na: brand-local FE api; no cross-brand consumers
 */

import { fetchClient } from "@/lib/api/fetchClient";
import type {
  SetOperatorInstructionRequest,
  SetOperatorInstructionResponse,
} from "../types/operator-instruction";

export const operatorInstructionApi = {
  /**
   * Persist an operator instruction for a conversation.
   * The instruction steers Adrián's next turn (persisted in agent_state_checkpoints JSONB).
   * The lead NEVER receives this text.
   */
  set: (
    token: string,
    tenantId: string,
    { conversationId, instruction }: SetOperatorInstructionRequest,
  ): Promise<SetOperatorInstructionResponse> =>
    fetchClient<SetOperatorInstructionResponse>(
      `/api/v1/adrian/conversations/${conversationId}/instruction`,
      {
        method: "POST",
        token,
        tenantId,
        body: JSON.stringify({ instruction }),
      },
    ),
};
