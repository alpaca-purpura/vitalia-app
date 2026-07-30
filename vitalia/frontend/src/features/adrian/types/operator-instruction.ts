// cap: adrian.inbox
"use client";

/**
 * operator-instruction.ts — TypeScript types for operator-instruction feature.
 *
 * Mirrors Pydantic DTOs from T-BE-3 (cdfbaaa6):
 *   SetOperatorInstructionRequest → SetOperatorInstructionResponse
 *   Endpoint: POST /api/v1/adrian/conversations/{conversation_id}/instruction
 *
 * NON-PHI: instruction is commercial text from the operator (not medical data).
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 */

/** Request payload for setting an operator instruction. */
export interface SetOperatorInstructionRequest {
  /** UUID of the conversation */
  conversationId: string;
  /**
   * Instruction text from the clinic operator to Adrián.
   * NON-PHI: commercial/operational guidance (e.g. "Ofrécele 10% de descuento").
   */
  instruction: string;
}

/** Response after persisting an operator instruction. */
export interface SetOperatorInstructionResponse {
  /** UUID of the conversation */
  conversationId: string;
  /** Whether an instruction is currently active for this conversation */
  instructionActive: boolean;
  /** ISO 8601 timestamp of last update */
  updatedAt: string;
}

/**
 * Composer effective mode.
 * - 'direct'      — handler_mode === 'human' (Adrián paused): message goes to lead
 * - 'instruction' — handler_mode === 'ai' (decide): instruction steers Adrián, lead never sees it
 */
export type ComposerMode = "instruction" | "direct";
