// cap: platform.autosave-primitive-platform
// story-origin: build-autosave-primitive-luana T-2
"use client";

/**
 * AutosaveShowcase.tsx — Consumer-of-reference: mounts useAutosave + <AutosaveBadge>
 * end-to-end without any brand dependency.
 *
 * Purpose: prove the contract between @luana/hooks (useAutosave) and
 * @luana/ui-kit (AutosaveBadge) typechecks and works correctly together.
 *
 * This is a MINIMAL showcase — not a production UI. It should:
 *  1. Accept a save function and getToken function (injected by the consumer)
 *  2. Wire useAutosave with those functions
 *  3. Render <AutosaveBadge status={status} savedAt={savedAt} />
 *  4. Provide a textarea that triggers scheduleSave on change
 *
 * NOT for use in brand apps — each brand has its own form-runtime.
 * Use this file to verify the end-to-end contract typechecks (tsc --noEmit).
 *
 * ADR-012 — build-autosave-primitive-luana T-2
 */

import * as React from "react";
import { useAutosave } from "@luana/hooks";
import { AutosaveBadge } from "../AutosaveBadge";

// ── Props ─────────────────────────────────────────────────────────────────────

export interface AutosaveShowcaseProps {
  /**
   * Save function — injected by the consumer.
   * Receives the current text value + the resolved auth token.
   */
  save: (values: { text: string }, ctx: { token: string }) => Promise<unknown>;

  /**
   * Auth token provider — injected (no Clerk coupling).
   * The showcase works with any auth provider (or a stub returning "test-token").
   */
  getToken: () => Promise<string | null>;

  /**
   * Optional debounce override (ms). Defaults to 2000ms.
   * Useful in tests or demos to speed up the autosave cycle.
   */
  debounceMs?: number;

  /**
   * Optional placeholder for the textarea.
   */
  placeholder?: string;

  /**
   * Initial text value.
   */
  initialValue?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * AutosaveShowcase — minimal consumer wiring useAutosave + AutosaveBadge.
 *
 * Proves the @luana/hooks ↔ @luana/ui-kit contract without brand coupling.
 *
 * @example
 * ```tsx
 * <AutosaveShowcase
 *   save={(values, { token }) => api.patch('/notes', values, token)}
 *   getToken={() => clerk.getToken()}
 * />
 * ```
 */
export function AutosaveShowcase({
  save,
  getToken,
  debounceMs,
  placeholder = "Escribe algo para ver el autoguardado en acción…",
  initialValue = "",
}: AutosaveShowcaseProps) {
  const [text, setText] = React.useState(initialValue);

  const { status, savedAt, scheduleSave, retry } = useAutosave<{ text: string }>({
    save,
    getToken,
    debounceMs,
  });

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const next = e.target.value;
    setText(next);
    scheduleSave({ text: next });
  }

  return (
    <div className="flex flex-col gap-3 p-4 rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between gap-2">
        <label className="text-sm font-medium text-card-foreground" htmlFor="showcase-textarea">
          Nota de ejemplo
        </label>
        <AutosaveBadge status={status} savedAt={savedAt} />
      </div>

      <textarea
        id="showcase-textarea"
        value={text}
        onChange={handleChange}
        placeholder={placeholder}
        rows={4}
        className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      />

      {status === "error" && (
        <button
          type="button"
          onClick={retry}
          className="self-start text-xs underline text-destructive hover:text-destructive/80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 rounded"
        >
          Reintentar guardado
        </button>
      )}
    </div>
  );
}

AutosaveShowcase.displayName = "AutosaveShowcase";
