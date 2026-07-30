// cap: adrian.inbox
// story-origin: TBD
/**
 * InboxLayout.tsx — 3-pane inbox grid shell (scaffold).
 *
 * Fork adapter from nicolify/closer-studio/components/CloserLayout.tsx.
 * Token retokenization: bg-amber-50 → vt-bg-surface · violet-* → vt-purpura-*
 *
 * Layout: [Sidebar 240px] [ConvList 320px] [Thread flex] [ContactSidebar 280px collapsable]
 * Responsive: ContactSidebar hidden on sm/md, visible on lg+.
 *
 * Server Component (no state/effects — layout shell only).
 * Interactive children (ConversationListPanel, ConversationThread, ContactSidebar)
 * are Client Components rendered inside.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

interface InboxLayoutProps {
  /** Left pane: conversation list panel (320px) */
  conversationListSlot: React.ReactNode;
  /** Center pane: conversation thread (flex) */
  threadSlot: React.ReactNode;
  /** Right pane: contact sidebar (280px, collapsable) */
  contactSidebarSlot?: React.ReactNode;
  /** Whether the contact sidebar is open */
  contactSidebarOpen?: boolean;
  className?: string;
}

/**
 * InboxLayout — 3-pane grid for /inbox conversational interface.
 * Server Component: renders static grid skeleton.
 * Client-driven open/close state lives in InboxPageClient via useInboxStore.
 */
export function InboxLayout({
  conversationListSlot,
  threadSlot,
  contactSidebarSlot,
  contactSidebarOpen = false,
  className,
}: InboxLayoutProps) {
  return (
    <div
      className={cn(
        "flex h-full min-h-0 w-full overflow-hidden vt-bg-surface",
        className,
      )}
      role="main"
      aria-label={INBOX_COPY.pageTitle}
      data-testid="inbox-layout"
    >
      {/* Left pane — conversation list (320px fixed) */}
      <aside
        className="flex w-80 shrink-0 flex-col border-r vt-border"
        aria-label="Lista de conversaciones"
        data-testid="conversation-list-panel"
      >
        {conversationListSlot}
      </aside>

      {/* Center pane — conversation thread (flex grow) */}
      <section
        className="flex min-w-0 flex-1 flex-col"
        aria-label="Hilo de conversación"
        data-testid="conversation-thread-panel"
      >
        {threadSlot}
      </section>

      {/* Right pane — contact sidebar (280px, collapsable) */}
      {contactSidebarSlot !== undefined && (
        <aside
          className={cn(
            "hidden w-[280px] shrink-0 flex-col border-l vt-border lg:flex",
            !contactSidebarOpen && "lg:hidden",
          )}
          aria-label={INBOX_COPY.contactSidebar.ariaLabel}
          data-testid="contact-sidebar-panel"
          aria-hidden={!contactSidebarOpen}
        >
          {contactSidebarSlot}
        </aside>
      )}
    </div>
  );
}
