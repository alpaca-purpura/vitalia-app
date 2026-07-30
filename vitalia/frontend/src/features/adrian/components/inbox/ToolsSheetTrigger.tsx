// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ToolsSheetTrigger.tsx — Button that opens AdrianToolsSheet (right panel).
 *
 * Triggers the tools sheet via useInboxStore.toggleActivityStream (scaffolded).
 * The tools sheet itself is implemented in T-inbox-fe-6 (AdrianToolsSheet.tsx).
 * This component is the trigger button only — 🛠 icon in ThreadHeader.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

interface ToolsSheetTriggerProps {
  /** Whether the tools sheet is currently open */
  isOpen?: boolean;
  /** Called when user clicks the trigger */
  onClick: () => void;
  className?: string;
}

/**
 * ToolsSheetTrigger — icon button to open the Adrian tools sheet.
 */
export function ToolsSheetTrigger({
  isOpen = false,
  onClick,
  className,
}: ToolsSheetTriggerProps) {
  return (
    <button
      onClick={onClick}
      data-testid="tools-sheet-trigger"
      aria-label={INBOX_COPY.toolsSheet.ariaLabel}
      aria-expanded={isOpen}
      title={INBOX_COPY.toolsSheet.ariaLabel}
      className={cn(
        "inline-flex items-center justify-center rounded-lg cursor-pointer",
        "p-2 transition-colors",
        "focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-[var(--vitalia-cian)]",
        isOpen
          ? "vt-bg-primary/12 vt-text-primary"
          : "vt-text-foreground hover:vt-bg-muted",
        className,
      )}
    >
      {/* Tools icon — 🛠 */}
      <span aria-hidden="true" className="text-sm leading-none">
        🛠
      </span>
    </button>
  );
}
