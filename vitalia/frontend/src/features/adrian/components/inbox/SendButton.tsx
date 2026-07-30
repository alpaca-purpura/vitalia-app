// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * SendButton.tsx — Send message CTA button for inbox composer.
 *
 * Dynamic label:
 *   - effectiveMode="instruction" → "Dar instrucción"
 *   - handler_mode="ai"          → "Enviar como Adrián ➤"
 *   - handler_mode="human"       → "Enviar"
 *
 * T-FE-1: added effectiveMode prop for instruction mode label.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";
import type { ComposerMode } from "../../types/operator-instruction";

export interface SendButtonProps {
  handlerMode: "ai" | "human";
  /** Derived effective mode (instruction | direct). Defaults to 'direct'. */
  effectiveMode?: ComposerMode;
  onClick: () => void;
  disabled?: boolean;
  isPending?: boolean;
  className?: string;
}

/**
 * SendButton — dynamic label CTA for sending a message or instruction.
 */
export function SendButton({
  handlerMode,
  effectiveMode = "direct",
  onClick,
  disabled,
  isPending,
  className,
}: SendButtonProps) {
  const label =
    effectiveMode === "instruction"
      ? INBOX_COPY.composer.sendButtonInstruction
      : handlerMode === "ai"
        ? INBOX_COPY.composer.sendButtonAi
        : INBOX_COPY.composer.sendButtonHuman;

  const isInstructionMode = effectiveMode === "instruction";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || isPending}
      aria-label={label}
      aria-busy={isPending}
      className={cn(
        "flex-shrink-0 px-4 py-2 rounded-xl text-sm font-semibold",
        "text-white transition-opacity duration-150",
        isInstructionMode
          ? "bg-amber-600 hover:bg-amber-700 dark:bg-amber-500 dark:hover:bg-amber-600"
          : handlerMode === "ai"
            ? "vt-bg-gradient-agent"
            : "vt-bg-azul-marino",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        className,
      )}
    >
      {isPending ? (
        <span
          aria-hidden="true"
          className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
        />
      ) : (
        <>
          {label}
          {!isInstructionMode && handlerMode === "ai" && (
            <span aria-hidden="true"> ➤</span>
          )}
        </>
      )}
    </button>
  );
}
