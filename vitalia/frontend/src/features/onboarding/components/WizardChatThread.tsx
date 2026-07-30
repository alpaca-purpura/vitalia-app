// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * WizardChatThread — Onboarding-specific full chat thread.
 *
 * Visual reference: wizard-brand-studio.html (mockup v1 Batch 7)
 * Layout:
 *   - Valeria bubble: bg-muted rounded 18px 18px 18px 4px max-w-80% left-aligned
 *     - Avatar: w-8 h-8 rounded-full gradient, letter "V"
 *     - Timestamp: text-[10px] font-semibold
 *     - Action buttons: rounded-full bg-primary or border-primary
 *   - User bubble: bg-primary text-white rounded 18px 18px 4px 18px right-aligned
 *   - Typing dots: 3 animated dots
 *   - Bonus NLU section: bg-cyan/0.1 border-cyan/0.4 below extraction
 *   - Input composer: border-t bg-surface-alt
 *     - Paperclip + Input field + Send button
 *     - Footer: Back | Skip button | Mode indicator
 *
 * This component is a full chat implementation (replaces the shared/wizard/WizardChatThread.tsx stub).
 * Lives in features/onboarding/ with full wizard business logic.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";
import { SlotConfirmInline } from "./SlotConfirmInline";
import type {
  WizardChatMessage,
  SlotSource,
} from "../types/wizard-onboarding.types";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ValeAvatar({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        "bg-gradient-to-br from-blue-700 to-purple-600",
        "text-white text-xs font-bold select-none",
        className,
      )}
      aria-hidden="true"
    >
      V
    </span>
  );
}

ValeAvatar.displayName = "ValeAvatar";

function TypingDots() {
  return (
    <div
      className="self-start flex items-end gap-1 rounded-[18px_18px_18px_4px] px-3 py-2 bg-gray-100"
      aria-label={WIZARD_COPY.chat.typingIndicatorLabel}
      aria-live="polite"
    >
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
          style={{ animationDelay: `${delay}ms` }}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}

TypingDots.displayName = "TypingDots";

// ---------------------------------------------------------------------------
// Main props
// ---------------------------------------------------------------------------

export interface WizardChatThreadProps {
  /** Chat messages in chronological order */
  messages: WizardChatMessage[];
  /** Whether assistant is currently typing */
  isTyping?: boolean;
  /** Whether submission is in progress */
  isSubmitting?: boolean;
  /** Called when user sends a text message */
  onSend: (text: string) => void;
  /** Called when user confirms a slot inline */
  onConfirmSlot: (slotId: string, value: string, source: SlotSource) => void;
  /** Called when user rejects a slot (triggers re-prompt) */
  onRejectSlot: (slotId: string) => void;
  /** Called when user clicks "Back" */
  onBack?: () => void;
  /** Called when user clicks "Skip to defaults" */
  onSkip?: () => void;
  /** Optional slot currently being confirmed */
  confirmingSlotId?: string | null;
  /** Current mode label for footer */
  modeLabel?: string;
  /** Wizard progress 0..1 for aria */
  progress?: number;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Full wizard chat thread with input composer and slot confirm inline.
 */
export function WizardChatThread({
  messages,
  isTyping = false,
  isSubmitting = false,
  onSend,
  onConfirmSlot,
  onRejectSlot,
  onBack,
  onSkip,
  confirmingSlotId,
  modeLabel,
  progress = 0,
  className,
}: WizardChatThreadProps) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const copy = WIZARD_COPY.chat;

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed || isSubmitting) return;
    onSend(trimmed);
    setInputValue("");
    inputRef.current?.focus();
  }, [inputValue, isSubmitting, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div
      className={cn("flex flex-col h-full min-h-0", className)}
      role="region"
      aria-label={WIZARD_COPY.a11y.chatRegionLabel}
    >
      {/* Progress indicator */}
      <div className="h-0.5 bg-gray-100 flex-shrink-0" aria-hidden="true">
        <div
          className="h-0.5 bg-blue-700 transition-[width] duration-500"
          style={{ width: `${Math.min(1, Math.max(0, progress)) * 100}%` }}
          role="progressbar"
          aria-valuenow={Math.round(progress * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={WIZARD_COPY.a11y.progressLabel(
            Math.round(progress * 100),
          )}
        />
      </div>

      {/* Message list */}
      <div
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0"
        role="log"
        aria-live="polite"
        aria-label={WIZARD_COPY.a11y.chatRegionLabel}
        aria-busy={isTyping}
      >
        {messages.length === 0 && !isTyping && (
          <p className="text-xs text-gray-400 text-center py-8 italic">
            {copy.emptyState}
          </p>
        )}

        {messages.map((msg) => {
          const isAssistant = msg.role === "assistant";

          return (
            <div
              key={msg.id}
              className={cn(
                "flex flex-col gap-1.5 max-w-[80%]",
                isAssistant
                  ? "self-start items-start"
                  : "self-end items-end ml-auto",
              )}
            >
              {/* Avatar row (assistant only) */}
              {isAssistant && (
                <div className="flex items-center gap-2">
                  <ValeAvatar />
                  <span className="text-[10px] font-semibold text-blue-700">
                    {copy.assistantName}
                  </span>
                  {msg.timestamp && (
                    <span className="text-[10px] text-gray-400">
                      {msg.timestamp}
                    </span>
                  )}
                </div>
              )}

              {/* Message bubble */}
              <div
                className={cn(
                  "px-4 py-2.5 text-sm leading-relaxed",
                  isAssistant
                    ? "rounded-[18px_18px_18px_4px] bg-gray-100 text-gray-800"
                    : "rounded-[18px_18px_4px_18px] bg-blue-700 text-white",
                )}
                aria-label={
                  isAssistant
                    ? WIZARD_COPY.a11y.messageFromAssistant(msg.content)
                    : WIZARD_COPY.a11y.messageFromUser(msg.content)
                }
              >
                {msg.content}
              </div>

              {/* Slot confirm inline (if attached to this message) */}
              {isAssistant && msg.requiresSlotConfirm && msg.slotRef && (
                <SlotConfirmInline
                  slot={msg.slotRef}
                  onConfirm={(value, source) =>
                    onConfirmSlot(msg.slotRef!.slotId, value, source)
                  }
                  onReject={() => onRejectSlot(msg.slotRef!.slotId)}
                  isConfirming={confirmingSlotId === msg.slotRef.slotId}
                  className="mt-1"
                />
              )}

              {/* Bonus NLU section (extracted info summary) */}
              {isAssistant &&
                msg.slotRef &&
                !msg.requiresSlotConfirm &&
                msg.slotRef.status === "confirmed" && (
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-cyan-50 border border-cyan-200 text-[10px] text-cyan-700">
                      <span aria-hidden="true">○</span>
                      {copy.bonusNluLabel}
                    </span>
                  </div>
                )}
            </div>
          );
        })}

        {/* Typing indicator */}
        {isTyping && <TypingDots />}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} aria-hidden="true" />
      </div>

      {/* Input composer */}
      <div className="flex-shrink-0 border-t bg-gray-50 px-4 py-3">
        <div className="flex items-center gap-2 bg-white rounded-xl border border-gray-200 px-3 py-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={copy.inputPlaceholder}
            disabled={isSubmitting}
            aria-label={copy.inputPlaceholder}
            className={cn(
              "flex-1 min-w-0 text-sm text-gray-800 placeholder-gray-400",
              "bg-transparent focus:outline-none",
              isSubmitting && "opacity-50 cursor-not-allowed",
            )}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!inputValue.trim() || isSubmitting}
            aria-label={copy.sendButton}
            className={cn(
              "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
              "bg-blue-700 text-white",
              "hover:bg-purple-700 transition-colors duration-150",
              "disabled:opacity-40 disabled:cursor-not-allowed",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
            )}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22,2 15,22 11,13 2,9" />
            </svg>
          </button>
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-3">
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="text-xs text-gray-500 hover:text-gray-700 transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 rounded"
              >
                {copy.backButton}
              </button>
            )}
            {onSkip && (
              <button
                type="button"
                onClick={onSkip}
                className="text-xs text-gray-400 hover:text-gray-600 transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 rounded"
              >
                {copy.skipButton}
              </button>
            )}
          </div>
          {modeLabel && (
            <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wide">
              {modeLabel}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

WizardChatThread.displayName = "WizardChatThread";
