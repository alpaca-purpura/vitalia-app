// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * ChatComposer — brand-agnostic chat composer molécula.
 * T-K2 port of vitalia ChatComposer (F1-S6).
 *
 * Brand coupling removed: useChatStore injected by prop.
 * Copy (placeholder/button label) is generic Spanish neutro.
 * Supervisor name injected for accessible label.
 *
 * Textarea with auto-resize (useEffect [localValue]), 3 icon stubs decorative (D3),
 * Send button (disabled cuando vacío), onKeyDown Enter/Shift+Enter + IME guard,
 * sr-only label (a11y), kbd hint Cmd+K.
 *
 * "use client" required: useState (localValue) + useRef (textarea) +
 *   useEffect (auto-resize) + onKeyDown (event handlers).
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { useState, useRef, useEffect } from "react";
import { cn } from "@luana/format/utils";
import type { ShellChatStore, ShellChatStoreApi } from "./types";

/** Maximum height of auto-resize textarea in pixels. */
const TEXTAREA_MAX_HEIGHT_PX = 100;

export interface ChatComposerProps {
  /** Injected chat store — kit NEVER imports brand chat store directly. */
  useChatStore: ShellChatStore;
  /** Supervisor name for accessible sr-only label. */
  supervisorName: string;
  /** Composer textarea placeholder text. */
  placeholder?: string;
  /** Optional testid for the composer root. */
  "data-testid"?: string;
  /** Textarea element id (for sr-only label + mod+k focus). */
  composerInputId?: string;
  className?: string;
}

/**
 * ChatComposer — footer molécula with interactive textarea + Send button.
 *
 * Keyboard handlers:
 *   - Enter (no Shift, no isComposing) → sendMessage(trimmed) + clear
 *   - Shift+Enter → default newline (browser native)
 *   - IME composing → skip handler (e.isComposing guard)
 *
 * Auto-resize: useEffect [localValue] adjusts textarea height up to TEXTAREA_MAX_HEIGHT_PX.
 * Send disabled: localValue.trim().length === 0.
 */
export function ChatComposer({
  useChatStore,
  supervisorName,
  placeholder,
  "data-testid": testId = "chat-composer",
  composerInputId = "shell-chat-composer",
  className,
}: ChatComposerProps) {
  const [localValue, setLocalValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sendMessage = useChatStore((s: ShellChatStoreApi) => s.sendMessage);

  const resolvedPlaceholder = placeholder ?? `Escribe un mensaje…`;

  // ── Auto-resize effect ──────────────────────────────────────────────────
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const next = Math.min(el.scrollHeight, TEXTAREA_MAX_HEIGHT_PX);
    el.style.height = `${next}px`;
  }, [localValue]);

  // ── Handlers ────────────────────────────────────────────────────────────

  const handleSend = () => {
    const trimmed = localValue.trim();
    if (!trimmed) return;
    sendMessage(trimmed);
    setLocalValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // IME composition safety — skip handler during IME input.
    if (e.nativeEvent.isComposing) return;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    // Shift+Enter: default behavior (newline insertion)
  };

  const isSendDisabled = localValue.trim().length === 0;

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <footer
      data-testid={testId}
      className={cn(
        "border-t border-border bg-card px-3 py-2 shrink-0",
        className,
      )}
    >
      <div className="flex items-end gap-2">
        {/* Adornment stubs — decorative icon buttons (NOT disabled, title="próximamente") */}
        <div className="flex items-center gap-0.5 pb-1.5">
          <button
            type="button"
            data-testid="composer-attach"
            aria-label="Adjuntar archivo"
            title="Adjuntar (próximamente)"
            className="h-8 w-8 rounded-md hover:bg-muted text-muted-foreground flex items-center justify-center text-base"
          >
            <span aria-hidden="true">📎</span>
          </button>
          <button
            type="button"
            data-testid="composer-voice"
            aria-label="Mensaje de voz"
            title="Voz (próximamente)"
            className="h-8 w-8 rounded-md hover:bg-muted text-muted-foreground flex items-center justify-center text-base"
          >
            <span aria-hidden="true">🎙️</span>
          </button>
          <button
            type="button"
            data-testid="composer-quick"
            aria-label="Comandos rápidos"
            title="Comandos (próximamente)"
            className="h-8 w-8 rounded-md hover:bg-muted text-muted-foreground flex items-center justify-center text-base"
          >
            <span aria-hidden="true">⚡</span>
          </button>
        </div>

        {/* sr-only label — aria accessibility */}
        <label className="sr-only" htmlFor={composerInputId}>
          {`Mensaje para ${supervisorName}`}
        </label>

        {/* Textarea — auto-resize, controlled, Shadcn-compatible classes */}
        <textarea
          ref={textareaRef}
          id={composerInputId}
          data-testid="composer-input"
          rows={1}
          value={localValue}
          onChange={(e) => setLocalValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={resolvedPlaceholder}
          title="Enter envía · Shift+Enter salto de línea"
          className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed placeholder:text-muted-foreground focus:outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 max-h-[100px] overflow-y-auto"
        />

        {/* Send button — disabled when empty */}
        <button
          type="button"
          data-testid="composer-send"
          onClick={handleSend}
          disabled={isSendDisabled}
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition shrink-0 self-end disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Enviar
        </button>
      </div>
    </footer>
  );
}
