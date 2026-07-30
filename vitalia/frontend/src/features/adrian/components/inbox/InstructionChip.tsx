// cap: adrian.inbox
"use client";

/**
 * InstructionChip.tsx — Shows the active operator instruction for a conversation.
 *
 * RN-13: instruction is PERSISTENT per-conversation. Shown as an editable/clearable chip.
 * Only rendered when effectiveMode === 'instruction' AND an instruction is active.
 *
 * Clearing sends instruction: "" which deactivates it on the BE.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

export interface InstructionChipProps {
  /** The currently active instruction text */
  activeInstruction: string;
  /** Whether a mutation is in flight (for loading state) */
  isPending?: boolean;
  /** Called when the operator clicks to edit (copies text back to composer) */
  onEdit: (text: string) => void;
  /** Called when the operator clears the instruction */
  onClear: () => void;
  className?: string;
}

/**
 * InstructionChip — displays the active operator instruction with edit/clear controls.
 */
export function InstructionChip({
  activeInstruction,
  isPending,
  onEdit,
  onClear,
  className,
}: InstructionChipProps) {
  const copy = INBOX_COPY.instruction;

  return (
    <div
      role="status"
      aria-label={copy.chipPrefix}
      className={cn(
        "flex items-start gap-2 px-3 py-2 rounded-lg text-xs",
        "bg-amber-50 border border-amber-200 text-amber-800",
        "dark:bg-amber-900/20 dark:border-amber-700 dark:text-amber-300",
        isPending && "opacity-60",
        className,
      )}
    >
      {/* Chip text */}
      <span className="flex-1 min-w-0">
        <span className="font-medium">{copy.chipPrefix}</span>{" "}
        <span className="truncate">{activeInstruction}</span>
      </span>

      {/* Edit — copies instruction text back to textarea */}
      <button
        type="button"
        onClick={() => onEdit(activeInstruction)}
        disabled={isPending}
        aria-label={copy.chipEditAriaLabel}
        className={cn(
          "flex-shrink-0 underline underline-offset-2 text-amber-700",
          "dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-200",
          "disabled:opacity-50 disabled:cursor-not-allowed",
        )}
      >
        Editar
      </button>

      {/* Clear */}
      <button
        type="button"
        onClick={onClear}
        disabled={isPending}
        aria-label={copy.chipClearAriaLabel}
        className={cn(
          "flex-shrink-0 text-amber-700 dark:text-amber-400",
          "hover:text-amber-900 dark:hover:text-amber-200",
          "disabled:opacity-50 disabled:cursor-not-allowed",
        )}
      >
        ✕
      </button>
    </div>
  );
}
