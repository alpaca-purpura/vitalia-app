// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ThreadHeader.tsx — Header bar for the conversation thread pane.
 *
 * Assembly of:
 *   - Patient name (unmasked lead) + real channel logo
 *   - ModeToggle: 2-state mode toggle (Adrián decide / consulta) via useModeToggle
 *   - NudgeButton: re-engagement nudge ("Dar empujón")
 *   - ContactSidebarToggle: toggles right sidebar (👤 Perfil)
 *
 * (Pausar Adrián lives in ThreadComposerDock; the activity glass-box lives in the
 *  bottom ActivityStream — neither is a header button anymore.)
 *
 * Uses useInboxStore for sidebar state. Uses useModeToggle for OCC mode switching.
 *
 * On mode conflict (409): shows conflict error state inline via isConflict.
 * Toast responsibility belongs to parent (ConversationThread).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { useInboxStore } from "../../store/inbox-store";
import {
  useModeToggle,
  conversationToSegmentValue,
} from "../../hooks/use-mode-toggle";
import type { ConversationDetail } from "../../types/inbox.types";
import { SocialLogo } from "@/components/shared/channels/SocialLogo";
import { ModeToggle } from "./ModeToggle";

/** Initials for the contact monogram (fallback "thumbnail" — no BE photo yet). */
function contactInitials(name: string | null | undefined): string {
  const parts = (name ?? "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const first = parts[0]?.[0] ?? "";
  const second = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? "") : "";
  return (first + second).toUpperCase() || "?";
}
import { NudgeButton } from "./NudgeButton";
import { ContactSidebarToggle } from "./ContactSidebarToggle";

interface ThreadHeaderProps {
  /** Full conversation detail (conversation + lead) */
  detail: ConversationDetail;
  className?: string;
}

/**
 * ThreadHeader — top bar for the conversation thread panel.
 * Client Component: owns mode toggle, store reads, and button callbacks.
 * Pausar Adrián moved to ThreadComposerDock (at the foot of the thread); the
 * VoiceStyleChip was removed (one-time config lives in Lisa › Marca › Voz y tono).
 */
export function ThreadHeader({ detail, className }: ThreadHeaderProps) {
  const { conversation, lead } = detail;
  const contactSidebarOpen = useInboxStore((s) => s.contactSidebarOpen);
  const toggleContactSidebar = useInboxStore((s) => s.toggleContactSidebar);

  const { toggle, isPending, isConflict } = useModeToggle(
    conversation.id,
    conversation,
  );

  const segmentValue = conversationToSegmentValue(conversation);

  return (
    <header
      className={cn(
        "flex flex-col gap-2 px-4 py-3 border-b vt-border shrink-0",
        "vt-bg-surface",
        className,
      )}
      data-testid="thread-header"
    >
      {/* Row 1: Patient name + channel + action buttons */}
      <div className="flex items-center justify-between gap-2">
        {/* Contact identity: real avatar (or monogram) + name + real channel logo. */}
        <div className="flex items-center gap-2 min-w-0">
          {lead.avatar_url ? (
            // Real WhatsApp/Instagram profile picture when the BE exposes it (#1).
            <img
              src={lead.avatar_url}
              alt=""
              className="h-9 w-9 shrink-0 rounded-full object-cover"
              data-testid="thread-header-avatar"
            />
          ) : (
            <span
              className="flex h-9 w-9 shrink-0 select-none items-center justify-center rounded-full vt-bg-cian-8 text-xs font-semibold vt-text-cian"
              aria-hidden
              data-testid="thread-header-avatar"
            >
              {contactInitials(lead.name)}
            </span>
          )}
          <span
            className="truncate text-sm font-semibold vt-text-foreground"
            data-testid="thread-header-patient-name"
          >
            {lead.name}
          </span>
          {/* Real social logo (SSoT social-channels). Keep testid for test + e2e POM;
              the SVG <title> carries the channel name as textContent. */}
          <span data-testid="thread-header-channel" className="shrink-0">
            <SocialLogo channel={conversation.channel} size={16} />
          </span>
        </div>

        {/* Action buttons: empujón · 👤 perfil (Pausar = dock · actividad = bottom stream) */}
        <div className="flex items-center gap-1 shrink-0">
          <NudgeButton conversationId={conversation.id} />
          <ContactSidebarToggle
            isOpen={contactSidebarOpen}
            onClick={toggleContactSidebar}
          />
        </div>
      </div>

      {/* Row 2: ModeToggle (2 modos) */}
      <div className="flex items-center gap-3 flex-wrap">
        <ModeToggle
          value={segmentValue}
          onChange={toggle}
          isPending={isPending}
          isConflict={isConflict}
        />
      </div>
    </header>
  );
}
