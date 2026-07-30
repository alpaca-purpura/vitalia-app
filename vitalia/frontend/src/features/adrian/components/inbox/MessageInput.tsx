// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * MessageInput.tsx — Textarea for composing messages.
 *
 * Fork adapter from Nicolify MessageInput.
 * - Dynamic placeholder per handler_mode / effectiveMode (from INBOX_COPY)
 * - Auto-grows up to ~4 lines (resize: none, max-height: 6rem)
 * - Supports Ctrl+Enter to submit
 *
 * effectiveMode (T-FE-1 RN-14):
 *   'instruction' → placeholder signals instruction context ("Instrucción a Adrián…")
 *   'direct'      → placeholder signals direct message to lead
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useRef, useCallback } from "react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";
import type { ComposerMode } from "../../types/operator-instruction";

export interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  handlerMode: "ai" | "human";
  /** Derived effective mode (instruction | direct). Defaults to 'direct'. */
  effectiveMode?: ComposerMode;
  patientName?: string | null;
  disabled?: boolean;
  className?: string;
}

function getPlaceholder(
  handlerMode: "ai" | "human",
  effectiveMode: ComposerMode,
  patientName?: string | null,
): string {
  if (effectiveMode === "instruction") {
    return INBOX_COPY.composer.placeholder.instructionToAdrian;
  }
  if (handlerMode === "ai") {
    return INBOX_COPY.composer.placeholder.adrianDecide;
  }
  const raw = INBOX_COPY.composer.placeholder.yoEscribo;
  return raw.replace("{patient_name}", patientName ?? "el paciente");
}

/**
 * MessageInput — auto-growing textarea for inbox composer.
 */
export function MessageInput({
  value,
  onChange,
  onSubmit,
  handlerMode,
  effectiveMode = "direct",
  patientName,
  disabled,
  className,
}: MessageInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Ctrl+Enter or Cmd+Enter submits
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        onSubmit();
      }
    },
    [onSubmit],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value);
    },
    [onChange],
  );

  const placeholder = getPlaceholder(handlerMode, effectiveMode, patientName);

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      rows={1}
      aria-label={placeholder}
      className={cn(
        "flex-1 min-w-0 resize-none rounded-xl px-3 py-2",
        "text-sm vt-text vt-bg-surface border vt-border",
        "placeholder:vt-text-faint",
        "focus:outline-none focus-visible:ring-1 focus-visible:ring-[var(--vitalia-cian-color)]",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "max-h-24 overflow-y-auto leading-relaxed",
        // Instruction mode: subtle amber tint on the textarea border
        effectiveMode === "instruction" &&
          "border-amber-300 dark:border-amber-700",
        className,
      )}
    />
  );
}
