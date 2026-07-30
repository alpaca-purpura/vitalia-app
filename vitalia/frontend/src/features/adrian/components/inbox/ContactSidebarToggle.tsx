// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ContactSidebarToggle.tsx — Button to toggle the contact sidebar (right panel).
 *
 * Reads/writes contactSidebarOpen from useInboxStore.
 * 👤 icon in ThreadHeader.
 * aria-expanded reflects current state.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { User } from "lucide-react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

interface ContactSidebarToggleProps {
  /** Whether the contact sidebar is currently open */
  isOpen: boolean;
  /** Called when user toggles */
  onClick: () => void;
  className?: string;
}

/**
 * ContactSidebarToggle — icon button to show/hide the contact sidebar.
 */
export function ContactSidebarToggle({
  isOpen,
  onClick,
  className,
}: ContactSidebarToggleProps) {
  const label = isOpen
    ? INBOX_COPY.contactSidebar.toggleClose
    : INBOX_COPY.contactSidebar.toggleOpen;

  return (
    <button
      onClick={onClick}
      data-testid="contact-sidebar-toggle"
      aria-label={label}
      aria-expanded={isOpen}
      title={label}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg cursor-pointer",
        "px-2.5 py-1.5 text-xs font-medium transition-colors",
        "focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-[var(--vitalia-cian)]",
        isOpen
          ? "vt-bg-primary/12 vt-text-primary"
          : "vt-text-foreground hover:vt-bg-muted",
        className,
      )}
    >
      <User className="h-3.5 w-3.5 shrink-0" aria-hidden focusable={false} />
      <span>Perfil</span>
    </button>
  );
}
