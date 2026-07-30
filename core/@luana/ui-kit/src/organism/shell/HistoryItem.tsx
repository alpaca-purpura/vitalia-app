// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * HistoryItem — conversation history item atom.
 * T-K2 port of vitalia HistoryItem (F1-S5 T-3). Brand-agnostic: the active
 * highlight class is injected (source hardcoded `bg-agent-valeria-soft`, a
 * brand token — RN-2). data-testid 'history-item' is generic, preserved verbatim.
 *
 * Active: `activeClass` bg + aria-current. Hover: hover:bg-muted.
 * "use client": onClick handler.
 */

import { cn } from "@luana/format/utils";

export interface HistoryItemProps {
  id: string;
  title: string;
  meta?: string;
  active: boolean;
  onClick: (id: string) => void;
  /** active-row bg class (brand soft token, e.g. supervisor soft bg). */
  activeClass?: string;
}

/** HistoryItem — single conversation row atom (client; click handler). */
export function HistoryItem({
  id,
  title,
  meta,
  active,
  onClick,
  activeClass,
}: HistoryItemProps) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={active}
      aria-current={active ? "true" : undefined}
      data-testid="history-item"
      onClick={() => onClick(id)}
      className={cn(
        "w-full text-left px-3 py-2 rounded-md transition-colors motion-reduce:transition-none",
        "hover:bg-muted",
        active && activeClass,
      )}
    >
      <p className="text-xs font-medium text-foreground truncate leading-tight">
        {title}
      </p>
      {/* a11y: active bg lowers muted-foreground contrast below WCAG AA — use
          text-foreground/80 when active; muted-foreground when inactive. */}
      <p
        className={cn(
          "text-[10px] mt-0.5 truncate leading-tight",
          active ? "text-foreground/80" : "text-muted-foreground",
        )}
      >
        {meta}
      </p>
    </button>
  );
}
