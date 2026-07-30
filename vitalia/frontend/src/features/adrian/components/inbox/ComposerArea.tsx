// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ComposerArea.tsx — Composer panel assembling all input sub-components.
 *
 * Assembles:
 *   - MessageInput (textarea)
 *   - ComposerAttachButton (📎)
 *   - ComposerVoiceButton (🎤 MediaRecorder)
 *   - SendButton (dynamic Adrián / Yo label)
 *   - InstructionChip (persistent instruction badge — RN-13)
 *
 * Shows ProposalCardBanner above when agent-waiting-approval state (Adrián consulta
 * + has a pending proposed message).
 *
 * effectiveMode (RN-14 · SC-8):
 *   - handler_mode === 'human' (Adrián paused) → 'direct': sends to lead
 *   - handler_mode === 'ai'   (Adrián decide)  → 'instruction': steers Adrián, lead never sees
 *
 * Disabled entirely when handler_mode state = "agent-thinking".
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState, useCallback } from "react";
import { cn } from "@/lib/cn";
import { MessageInput } from "./MessageInput";
import { ComposerAttachButton } from "./ComposerAttachButton";
import { ComposerVoiceButton } from "./ComposerVoiceButton";
import { SendButton } from "./SendButton";
import { ProposalCardBanner } from "./ProposalCardBanner";
import { InstructionChip } from "./InstructionChip";
import { useSendMessage } from "../../api/use-send-message";
import { useInboxStore } from "../../store/inbox-store";
import { useOperatorInstruction, getEffectiveMode } from "../../hooks/use-operator-instruction";
import { INBOX_COPY } from "../../lib/copy";
import type { Conversation } from "@/features/crm-shared";
import type { VoiceReadyResult } from "./ComposerVoiceButton";

function randomIdempotencyKey(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export interface ComposerAreaProps {
  conversation: Conversation;
  /** Patient first name for placeholder personalisation */
  patientName?: string | null;
  /**
   * When set, ComposerArea shows ProposalCardBanner above.
   * Set to the text Adrián is proposing to send.
   */
  pendingProposalText?: string | null;
  /**
   * Currently active operator instruction for this conversation.
   * Shown as an editable chip when effectiveMode === 'instruction' (RN-13).
   */
  activeInstruction?: string | null;
  className?: string;
}

/**
 * ComposerArea — full message input + attach + voice + send assembler.
 * Supports effectiveMode: 'instruction' (decide) | 'direct' (paused).
 */
export function ComposerArea({
  conversation,
  patientName,
  pendingProposalText,
  activeInstruction,
  className,
}: ComposerAreaProps) {
  const [text, setText] = useState("");
  const [voiceReady, setVoiceReady] = useState<VoiceReadyResult | null>(null);
  const sendMessage = useSendMessage();
  const clearAttachQueue = useInboxStore((s) => s.clearAttachQueue);
  const attachQueue = useInboxStore((s) => s.attachQueue);
  const setInstruction = useOperatorInstruction();

  const { id: conversationId, handler_mode } = conversation;

  // RN-14: effectiveMode switches based on handler_mode
  const effectiveMode = getEffectiveMode(handler_mode);
  const isInstructionMode = effectiveMode === "instruction";

  const canSend =
    (text.trim().length > 0 || voiceReady !== null || attachQueue.length > 0) &&
    !sendMessage.isPending &&
    !setInstruction.isPending;

  const handleSend = useCallback(() => {
    if (!canSend) return;

    if (isInstructionMode) {
      // RN-13/SC-8: send as instruction to Adrián — lead NEVER receives this
      setInstruction.mutate(
        {
          conversationId,
          instruction: text.trim(),
        },
        {
          onSuccess: () => {
            setText("");
          },
        },
      );
      return;
    }

    // Direct mode: send as human message to lead
    if (voiceReady) {
      sendMessage.mutate(
        {
          conversationId,
          bodyText: voiceReady.transcriptionText,
          mediaUrl: voiceReady.mediaUrl,
          mediaKind: "audio",
          mediaDurationS: voiceReady.durationS,
          idempotencyKey: randomIdempotencyKey(),
        },
        {
          onSuccess: () => {
            setVoiceReady(null);
            setText("");
            clearAttachQueue();
          },
        },
      );
    } else if (text.trim()) {
      sendMessage.mutate(
        {
          conversationId,
          bodyText: text.trim(),
          idempotencyKey: randomIdempotencyKey(),
        },
        {
          onSuccess: () => {
            setText("");
            clearAttachQueue();
          },
        },
      );
    }
  }, [
    canSend,
    isInstructionMode,
    voiceReady,
    text,
    conversationId,
    sendMessage,
    setInstruction,
    clearAttachQueue,
  ]);

  const handleVoiceReady = useCallback((result: VoiceReadyResult) => {
    setVoiceReady(result);
    setText(result.transcriptionText);
  }, []);

  const handleApproveProposal = useCallback(() => {
    if (!pendingProposalText) return;
    sendMessage.mutate({
      conversationId,
      bodyText: pendingProposalText,
      idempotencyKey: randomIdempotencyKey(),
    });
  }, [pendingProposalText, conversationId, sendMessage]);

  const handleEditProposal = useCallback(() => {
    if (!pendingProposalText) return;
    setText(pendingProposalText);
  }, [pendingProposalText]);

  // Copy instruction back to textarea for editing
  const handleEditInstruction = useCallback((instructionText: string) => {
    setText(instructionText);
  }, []);

  // Clear instruction by posting empty string
  const handleClearInstruction = useCallback(() => {
    setInstruction.mutate({
      conversationId,
      instruction: "",
    });
  }, [conversationId, setInstruction]);

  // Instruction mode label header (shown above composer when in instruction mode)
  const instructionCopy = INBOX_COPY.instruction;

  return (
    <div className={cn("flex flex-col gap-2 p-3", className)}>
      {/* Instruction mode label (RN-14/SC-8) — shown when Adrián is in decide */}
      {isInstructionMode && (
        <div
          role="note"
          aria-label={instructionCopy.modeLabel}
          className="flex items-center gap-1.5 text-xs font-medium text-amber-700 dark:text-amber-400"
        >
          <span>{instructionCopy.modeLabel}</span>
          <span className="font-normal text-amber-600 dark:text-amber-500">
            · {instructionCopy.modeHint}
          </span>
        </div>
      )}

      {/* Active instruction chip (RN-13 persistent) */}
      {isInstructionMode && activeInstruction && (
        <InstructionChip
          activeInstruction={activeInstruction}
          isPending={setInstruction.isPending}
          onEdit={handleEditInstruction}
          onClear={handleClearInstruction}
        />
      )}

      {/* Proposal banner for Adrián consulta state */}
      {pendingProposalText && (
        <ProposalCardBanner
          proposedText={pendingProposalText}
          onApprove={handleApproveProposal}
          onEdit={handleEditProposal}
          isApproving={sendMessage.isPending}
        />
      )}

      {/* Voice ready preview badge */}
      {voiceReady && (
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs",
            "vt-bg-cian-8 vt-text-cian border vt-border-cian",
          )}
        >
          <span aria-hidden="true">🎤</span>
          <span className="flex-1 truncate">
            {voiceReady.transcriptionText}
          </span>
          <button
            type="button"
            onClick={() => {
              setVoiceReady(null);
              setText("");
            }}
            className="vt-text-muted hover:vt-text-danger text-xs"
            aria-label="Quitar nota de voz"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main composer row */}
      <div className="flex items-end gap-2">
        <MessageInput
          value={text}
          onChange={setText}
          onSubmit={handleSend}
          handlerMode={handler_mode}
          patientName={patientName}
          effectiveMode={effectiveMode}
          disabled={sendMessage.isPending || setInstruction.isPending}
          className="flex-1"
        />

        {/* Attach + Voice only in direct mode (no media in instruction) */}
        {!isInstructionMode && (
          <>
            <ComposerAttachButton
              conversationId={conversationId}
              disabled={sendMessage.isPending}
            />

            <ComposerVoiceButton
              conversationId={conversationId}
              onVoiceReady={handleVoiceReady}
              disabled={sendMessage.isPending}
            />
          </>
        )}

        <SendButton
          handlerMode={handler_mode}
          effectiveMode={effectiveMode}
          onClick={handleSend}
          disabled={!canSend}
          isPending={sendMessage.isPending || setInstruction.isPending}
        />
      </div>

      {/* SR live region for instruction set confirmation (a11y) */}
      {setInstruction.isSuccess && (
        <span role="status" aria-live="polite" className="sr-only">
          {instructionCopy.ariaLiveSet}
        </span>
      )}
    </div>
  );
}
