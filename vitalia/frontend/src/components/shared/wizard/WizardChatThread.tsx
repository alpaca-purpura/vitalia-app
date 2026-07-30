// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * WizardChatThread — wizard chat thread for onboarding flows.
 *
 * Scaffold stub. Full implementation (with real copilot SSE streaming)
 * arrives in copilot-tools-impl story (Slice 2).
 *
 * Pattern: conversational wizard with agent messages + user inputs.
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { cn } from "@/lib/cn";

export interface WizardMessage {
  /** Unique message ID */
  id: string;
  /** Message role */
  role: "assistant" | "user";
  /** Message text content (Spanish neutro — no voseo) */
  content: string;
  /** Timestamp (already formatted) */
  timestamp?: string;
}

export interface WizardChatThreadProps {
  /** Chat messages in chronological order */
  messages?: WizardMessage[];
  /** Whether the assistant is currently typing */
  isTyping?: boolean;
  /** Wizard step progress (0..1) */
  progress?: number;
  /** Wizard step label */
  stepLabel?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Wizard chat thread — shows a conversational onboarding exchange.
 * Scaffold until Slice 2 copilot integration.
 */
export function WizardChatThread({
  messages = [],
  isTyping = false,
  progress = 0,
  stepLabel = "Inicio",
  className,
}: WizardChatThreadProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 vt-bg-surface vt-border",
        "border rounded-[var(--radius-lg)] overflow-hidden",
        className,
      )}
      aria-label={`Asistente de configuración — ${stepLabel}`}
      role="region"
    >
      {/* Progress bar */}
      <div className="h-1 vt-bg-muted" aria-hidden="true">
        <div
          className="h-1 vt-bg-cian transition-[width] duration-500"
          style={{ width: `${Math.min(1, Math.max(0, progress)) * 100}%` }}
          role="progressbar"
          aria-valuenow={Math.round(progress * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Progreso: ${Math.round(progress * 100)}%`}
        />
      </div>

      {/* Step label */}
      <div className="px-4 pt-3 pb-1 text-xs vt-text-muted font-medium">
        {stepLabel}
      </div>

      {/* Message list */}
      <div
        className="flex flex-col gap-2 px-4 pb-4 overflow-y-auto max-h-80"
        role="log"
        aria-live="polite"
        aria-label="Mensajes del asistente"
      >
        {messages.length === 0 && !isTyping && (
          <p className="text-xs vt-text-faint text-center py-4">
            El asistente iniciará la conversación aquí.
          </p>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex max-w-[80%] rounded-[var(--radius-bubble)] px-3 py-2",
              msg.role === "assistant"
                ? "self-start vt-bg-muted vt-text"
                : "self-end vt-bg-cian vt-text-white",
            )}
            aria-label={`${msg.role === "assistant" ? "Asistente" : "Tú"}: ${msg.content}`}
          >
            <p className="text-sm leading-relaxed">{msg.content}</p>
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div
            className="self-start flex items-center gap-1 vt-bg-muted rounded-[var(--radius-bubble)] px-3 py-2"
            aria-live="polite"
            aria-label="El asistente está escribiendo"
          >
            <span
              className="w-1.5 h-1.5 rounded-full vt-bg-cian-10 animate-bounce"
              style={{ animationDelay: "0ms" }}
              aria-hidden="true"
            />
            <span
              className="w-1.5 h-1.5 rounded-full vt-bg-cian-10 animate-bounce"
              style={{ animationDelay: "150ms" }}
              aria-hidden="true"
            />
            <span
              className="w-1.5 h-1.5 rounded-full vt-bg-cian-10 animate-bounce"
              style={{ animationDelay: "300ms" }}
              aria-hidden="true"
            />
          </div>
        )}
      </div>

      <p className="px-4 pb-3 text-xs vt-text-faint italic">
        Integración SSE pendiente — Slice 2 (copilot-tools-impl).
      </p>
    </div>
  );
}
