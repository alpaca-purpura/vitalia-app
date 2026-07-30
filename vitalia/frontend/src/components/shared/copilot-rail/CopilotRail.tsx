// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
"use client";

/**
 * CopilotRail — right-side copilot rail for Vitalia app.
 *
 * Width: 80px idle (icons only) / 460px chat-open.
 * Gradient trigger button uses vt-bg-gradient-agent class.
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { useState, useCallback } from "react";
import { cn } from "@/lib/cn";
import { CopilotChat } from "./CopilotChat";

export interface CopilotRailProps {
  /** Additional CSS classes */
  className?: string;
}

/**
 * Collapsible copilot rail. Idle = 80px icon strip, open = 460px chat panel.
 */
export function CopilotRail({ className }: CopilotRailProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  return (
    <aside
      className={cn(
        "flex flex-col shrink-0 h-screen",
        "vt-bg-surface border-l vt-border",
        "transition-[width] duration-300 ease-in-out overflow-hidden",
        isOpen ? "w-[460px]" : "w-20",
        className,
      )}
      aria-label="Panel de copiloto"
      role="complementary"
      aria-expanded={isOpen}
    >
      {/* Header: gradient trigger button */}
      <div
        className={cn(
          "flex items-center shrink-0 h-14 px-3 border-b vt-border",
          isOpen ? "justify-between" : "justify-center",
        )}
      >
        <button
          onClick={handleToggle}
          className={cn(
            "flex items-center justify-center gap-2",
            "rounded-[var(--radius-pill)] font-semibold",
            "vt-text-white vt-bg-gradient-agent",
            "transition-opacity hover:opacity-90",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 vt-ring-cian",
            isOpen ? "px-4 py-2 text-sm w-auto" : "w-10 h-10 text-lg",
          )}
          aria-label={isOpen ? "Cerrar copiloto" : "Abrir copiloto"}
          aria-controls="copilot-chat-panel"
          aria-expanded={isOpen}
        >
          <span aria-hidden="true">✦</span>
          {isOpen && <span>Copiloto</span>}
        </button>

        {isOpen && (
          <button
            onClick={handleToggle}
            className={cn(
              "p-1 rounded vt-text-muted",
              "hover:vt-bg-muted",
              "focus-visible:outline-none focus-visible:ring-2 vt-ring-cian",
              "transition-colors",
            )}
            aria-label="Cerrar panel de copiloto"
          >
            <span aria-hidden="true">✕</span>
          </button>
        )}
      </div>

      {/* Chat panel */}
      <div
        id="copilot-chat-panel"
        className={cn(
          "flex-1 overflow-hidden",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none",
        )}
        aria-hidden={!isOpen}
        role="region"
        aria-label="Chat con copiloto"
      >
        {isOpen && <CopilotChat />}
      </div>

      {/* Idle icons strip (when collapsed) */}
      {!isOpen && (
        <div
          className="flex-1 flex flex-col items-center py-4 gap-3"
          aria-hidden="true"
        >
          <div
            className="w-8 h-8 rounded-full vt-bg-gradient-agent flex items-center justify-center vt-text-white text-xs font-bold"
            title="Valeria"
          >
            VA
          </div>
        </div>
      )}
    </aside>
  );
}
