// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
"use client";

/**
 * CopilotChat — chat interface within the CopilotRail.
 *
 * Renders a chat history area + message input.
 * This component is the UI shell only (T-infra-7 scope).
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { cn } from "@/lib/cn";

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: string;
}

export interface CopilotChatProps {
  /** Initial messages (e.g. from server-side prefetch) */
  initialMessages?: ChatMessage[];
  /** Callback when user sends a message */
  onSendMessage?: (message: string) => void | Promise<void>;
  /** Whether the chat is loading a response */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Chat interface for Vitalia's AI copilot.
 * Loading/empty/error states included per tessl__react-patterns.
 */
export function CopilotChat({
  initialMessages = [],
  onSendMessage,
  isLoading = false,
  className,
}: CopilotChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = inputValue.trim();
    if (!text) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");

    if (onSendMessage) {
      await onSendMessage(text);
    }
  }, [inputValue, onSendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        void handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages area */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-3"
        role="log"
        aria-live="polite"
        aria-label="Historial del chat"
        aria-busy={isLoading}
      >
        {/* Empty state */}
        {messages.length === 0 && !isLoading && (
          <div
            className="flex flex-col items-center justify-center h-full gap-3 text-center"
            aria-label="Sin mensajes"
          >
            <div
              className="w-12 h-12 rounded-full vt-bg-gradient-agent flex items-center justify-center vt-text-white text-lg font-bold"
              aria-hidden="true"
            >
              VA
            </div>
            <p className="text-sm vt-text-muted">
              Hola, soy Valeria. ¿En qué puedo ayudarte hoy?
            </p>
          </div>
        )}

        {/* Message list */}
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-2",
              message.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            {message.role === "agent" && (
              <div
                className="w-6 h-6 rounded-full vt-bg-gradient-agent flex items-center justify-center vt-text-white text-[10px] font-bold shrink-0 mt-1"
                aria-hidden="true"
              >
                VA
              </div>
            )}
            <div
              className={cn(
                "max-w-[80%] px-3 py-2 text-sm",
                message.role === "user"
                  ? "rounded-[var(--radius-bubble)] rounded-br-sm vt-bg-azul-marino vt-text-white"
                  : "rounded-[var(--radius-bubble)] rounded-bl-sm vt-bg-muted vt-text",
              )}
              role={message.role === "agent" ? "status" : undefined}
            >
              {message.content}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div
            className="flex gap-2 justify-start"
            aria-label="El copiloto está respondiendo"
          >
            <div
              className="w-6 h-6 rounded-full vt-bg-gradient-agent flex items-center justify-center vt-text-white text-[10px] font-bold shrink-0 mt-1"
              aria-hidden="true"
            >
              VA
            </div>
            <div className="flex items-center gap-1 px-3 py-2 rounded-[var(--radius-bubble)] rounded-bl-sm vt-bg-muted">
              <span
                className="w-1.5 h-1.5 rounded-full vt-bg-muted animate-bounce"
                style={{ animationDelay: "0ms" }}
                aria-hidden="true"
              />
              <span
                className="w-1.5 h-1.5 rounded-full vt-bg-muted animate-bounce"
                style={{ animationDelay: "150ms" }}
                aria-hidden="true"
              />
              <span
                className="w-1.5 h-1.5 rounded-full vt-bg-muted animate-bounce"
                style={{ animationDelay: "300ms" }}
                aria-hidden="true"
              />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} aria-hidden="true" />
      </div>

      {/* Input area */}
      <div className="shrink-0 p-3 border-t vt-border vt-bg-surface">
        <div className="flex gap-2 items-end">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe un mensaje..."
            rows={1}
            className={cn(
              "flex-1 resize-none rounded-[var(--radius)] text-sm",
              "px-3 py-2 min-h-[36px] max-h-[120px]",
              "vt-bg-muted vt-text border vt-border",
              "placeholder:vt-text-faint",
              "focus:outline-none focus:vt-border-cian focus:ring-1 vt-ring-cian",
              "transition-colors",
            )}
            aria-label="Escribe un mensaje al copiloto"
            disabled={isLoading}
          />
          <button
            onClick={() => void handleSend()}
            disabled={!inputValue.trim() || isLoading}
            className={cn(
              "shrink-0 flex items-center justify-center w-9 h-9",
              "rounded-[var(--radius)] font-bold vt-text-white text-sm",
              "vt-bg-gradient-app-cta",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "hover:opacity-90 transition-opacity",
              "focus-visible:outline-none focus-visible:ring-2 vt-ring-cian",
            )}
            aria-label="Enviar mensaje"
          >
            ↑
          </button>
        </div>
        <p className="text-[10px] vt-text-faint mt-1 text-center">
          Enter para enviar · Shift+Enter para nueva línea
        </p>
      </div>
    </div>
  );
}
