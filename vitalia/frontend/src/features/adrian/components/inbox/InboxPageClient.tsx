// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * InboxPageClient.tsx — "use client" wrapper for /inbox route.
 *
 * Wraps the inbox feature with nuqs NuqsAdapter (required for useQueryStates).
 * Wires all 5 panels + modal using Zustand state + nuqs URL state.
 *
 * Per 03-arch-fe.md § 2:
 *   - NuqsAdapter required at Client boundary for useQueryStates
 *   - useInboxStore for UI state (contactSidebarOpen, toolsSheetOpen, etc.)
 *   - useInboxUrlState for selected conversation (URL param ?lead=)
 *   - useConversationDetail for compound detail (conversation + lead + messages)
 *
 * "use client" required for:
 *   - NuqsAdapter (Next.js App Router adapter for nuqs)
 *   - useInboxStore (Zustand UI state)
 *   - useInboxUrlState (nuqs URL state hook)
 *   - useConversationDetail (React Query data fetch)
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState } from "react";
import { NuqsAdapter } from "nuqs/adapters/next/app";

import { useInboxStore } from "../../store/inbox-store";
import { useInboxUrlState } from "../../lib/url-state";
import { useConversationDetail } from "@/features/crm-shared";
import { InboxLayout } from "./InboxLayout";
import { ConversationListPanel } from "./ConversationListPanel";
import { InboxThread } from "./InboxThread";
import { ContactSidebar } from "./ContactSidebar";
import { ActivityStream } from "./ActivityStream";
import { AdrianToolsSheet } from "./AdrianToolsSheet";

/**
 * InboxPageClient — Client entry point for /inbox.
 * Renders within RSC page.tsx (Server Component wrapper).
 *
 * Wires:
 *   - Left pane: ConversationListPanel (search + filters + list)
 *   - Center pane: InboxThread + ActivityStream (sticky bottom)
 *   - Right pane: ContactSidebar (HIPAA-lite PHI-aware, role-gated NPS)
 *   - Slide-over: AdrianToolsSheet (read-only tools panel)
 */
/**
 * Outer wrapper — mounts NuqsAdapter BEFORE any nuqs hook fires.
 * `useInboxUrlState()` (which uses `useQueryStates` from nuqs) MUST live in
 * a descendant of `<NuqsAdapter>`, otherwise nuqs throws NUQS-404.
 */
export function InboxPageClient() {
  return (
    <NuqsAdapter>
      <InboxPageContent />
    </NuqsAdapter>
  );
}

/**
 * Inner content — runs INSIDE NuqsAdapter scope, safe to call useInboxUrlState.
 */
function InboxPageContent() {
  const contactSidebarOpen = useInboxStore((s) => s.contactSidebarOpen);

  // Tools sheet state — local until T-inbox-fe-6 adds toolsSheetOpen to store
  const [toolsSheetOpen, setToolsSheetOpen] = useState(false);

  const [{ conv: conversationId }] = useInboxUrlState();
  const { data: convDetail } = useConversationDetail(conversationId);

  return (
    <>
      <InboxLayout
        contactSidebarOpen={contactSidebarOpen}
        conversationListSlot={<ConversationListPanel />}
        threadSlot={
          <>
            {conversationId ? (
              <InboxThread conversationId={conversationId} />
            ) : (
              <div
                className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center"
                data-testid="thread-empty"
              >
                <p className="text-sm vt-text-muted">
                  Selecciona una conversación de la lista para comenzar.
                </p>
              </div>
            )}
            <ActivityStream conversationId={conversationId} />
          </>
        }
        contactSidebarSlot={
          convDetail ? (
            <ContactSidebar
              conversationId={convDetail.conversation.id}
              leadId={convDetail.lead.id}
              contact={{
                patientId: convDetail.lead.id,
                name: convDetail.lead.name,
                phone: convDetail.lead.phone,
                email: convDetail.lead.email,
                serviceInterest: convDetail.lead.service_interest,
                statusTag: convDetail.conversation.stage_decision,
                npsHistory: undefined,
              }}
            />
          ) : null
        }
      />
      <AdrianToolsSheet
        open={toolsSheetOpen}
        onClose={() => setToolsSheetOpen(false)}
        conversationId={conversationId}
      />
    </>
  );
}
