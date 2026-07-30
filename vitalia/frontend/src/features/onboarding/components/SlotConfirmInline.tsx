// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * SlotConfirmInline — inline slot confirmation widget in the chat thread.
 *
 * Visual reference: wizard-brand-studio.html — Bonus NLU section
 * Shows extracted slot value + confirm/reject/edit flow.
 *
 * States:
 *   - idle: shows extracted value + Confirm + "No es correcto" buttons
 *   - editing: shows text input for correction + Save + Cancel
 *   - confirmed: shows "Confirmado" badge
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";
import type { WizardSlot, SlotSource } from "../types/wizard-onboarding.types";

export interface SlotConfirmInlineProps {
  /** The slot to confirm */
  slot: WizardSlot;
  /** Called when user confirms (with original or corrected value) */
  onConfirm: (value: string, source: SlotSource) => void;
  /** Called when user rejects (should re-prompt assistant) */
  onReject: () => void;
  /** Whether confirmation is in progress (shows loading) */
  isConfirming?: boolean;
  /** Additional CSS classes */
  className?: string;
}

type ConfirmState = "idle" | "editing" | "confirmed";

/**
 * Inline slot confirm widget — fits inside a chat message bubble.
 */
export function SlotConfirmInline({
  slot,
  onConfirm,
  onReject,
  isConfirming = false,
  className,
}: SlotConfirmInlineProps) {
  const [confirmState, setConfirmState] = useState<ConfirmState>("idle");
  const [editValue, setEditValue] = useState(slot.value ?? "");
  const inputRef = useRef<HTMLInputElement>(null);
  const copy = WIZARD_COPY.slotConfirm;

  // Focus input when entering edit mode
  useEffect(() => {
    if (confirmState === "editing" && inputRef.current) {
      inputRef.current.focus();
    }
  }, [confirmState]);

  if (confirmState === "confirmed") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full px-3 py-1",
          "bg-green-100 text-green-700 text-xs font-medium",
          className,
        )}
        aria-live="polite"
      >
        <span aria-hidden="true">✓</span>
        {copy.confirmedBadge}
      </span>
    );
  }

  if (confirmState === "editing") {
    return (
      <div
        className={cn(
          "rounded-xl border border-gray-200 bg-white p-3 space-y-2",
          className,
        )}
        role="group"
        aria-label={`Corrección: ${slot.label}`}
      >
        <label
          htmlFor={`slot-edit-${slot.slotId}`}
          className="block text-xs font-medium text-gray-700"
        >
          {copy.editInputLabel}
        </label>
        <input
          id={`slot-edit-${slot.slotId}`}
          ref={inputRef}
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className={cn(
            "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm",
            "focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent",
            "text-gray-900 placeholder-gray-400",
          )}
          onKeyDown={(e) => {
            if (e.key === "Enter" && editValue.trim()) {
              const trimmed = editValue.trim();
              onConfirm(trimmed, "user_correction");
              setConfirmState("confirmed");
            }
            if (e.key === "Escape") {
              setEditValue(slot.value ?? "");
              setConfirmState("idle");
            }
          }}
          aria-label={copy.editInputLabel}
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => {
              const trimmed = editValue.trim();
              if (!trimmed) return;
              onConfirm(trimmed, "user_correction");
              setConfirmState("confirmed");
            }}
            disabled={!editValue.trim() || isConfirming}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium",
              "bg-blue-700 text-white",
              "hover:bg-blue-800 transition-colors duration-150",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
            )}
          >
            {copy.editSaveButton}
          </button>
          <button
            type="button"
            onClick={() => {
              setEditValue(slot.value ?? "");
              setConfirmState("idle");
            }}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium border border-gray-300",
              "text-gray-600 hover:bg-gray-50 transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400",
            )}
          >
            {copy.editCancelButton}
          </button>
        </div>
      </div>
    );
  }

  // idle state
  return (
    <div
      className={cn(
        "rounded-xl border border-cyan-200 bg-cyan-50 p-3 space-y-2",
        className,
      )}
      role="group"
      aria-label={`Confirmar dato: ${slot.label}`}
    >
      <p className="text-xs text-gray-500">{copy.promptPrefix}</p>
      <p className="text-sm font-semibold text-gray-800">
        <span className="text-xs text-gray-500 font-normal">
          {slot.label}:{" "}
        </span>
        {slot.value}
      </p>
      <div className="flex gap-2 flex-wrap">
        <button
          type="button"
          onClick={() => {
            onConfirm(slot.value ?? "", "extracted_url");
            setConfirmState("confirmed");
          }}
          disabled={isConfirming}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium",
            "bg-blue-700 text-white",
            "hover:bg-blue-800 transition-colors duration-150",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
          )}
          aria-label={`Confirmar: ${slot.value}`}
        >
          {copy.confirmButton}
        </button>
        <button
          type="button"
          onClick={() => setConfirmState("editing")}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium border border-gray-300",
            "text-gray-600 hover:bg-gray-50 transition-colors duration-150",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400",
          )}
        >
          {copy.editLabel}
        </button>
        <button
          type="button"
          onClick={onReject}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium",
            "text-gray-500 hover:text-gray-700 transition-colors duration-150",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400",
          )}
        >
          {copy.rejectButton}
        </button>
      </div>
    </div>
  );
}

SlotConfirmInline.displayName = "SlotConfirmInline";
