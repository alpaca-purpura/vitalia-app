// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * AdrianInboxView.tsx — T-5: replace skeleton with real 3-pane layout.
 *
 * 3-pane ResizablePanelGroup layout (per 03-arch-fe.md § 3):
 *   Left  (~24%): ConversationListPanel (search + filters + conv list)
 *   Center (~52%): InboxThread (thread view, empty state when no conv selected)
 *   Right  (~24%): ContactSidebar (PHI-aware, toggle via contactSidebarOpen)
 *
 * Mobile (<768px): single-panel fallback (thread when conv selected, list otherwise).
 *
 * RN-11: fills 100% of the panel — no max-width hard constraint.
 * RN-12: "Modo conversación" remembers Valeria prior state (ConversationModeButton).
 *
 * Props: SSR-hydrated initialData + URL state (initialConvId, initialFilter).
 *
 * "use client" — Client root: owns React Query hydration + Zustand + URL state.
 *
 * HIPAA-lite: no PHI in URL (only conv UUID); PHI masking in ContactSidebar.
 * FSD-Lite: no cross-feature imports. Uses only @/features/crm-shared (allowed boundary).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § 3 + 06-tickets.yaml T-5
 */

"use client";

import { useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { useInboxStore } from "../../store/inbox-store";
import { useValeriaReaccion } from "../../hooks/useValeriaReaccion";
import { useConversationDetail } from "@/features/crm-shared";
import type { InitialInboxState } from "@/features/adrian/api/inbox-server";
import { ConversationListPanel } from "./ConversationListPanel";
import { InboxThread } from "./InboxThread";
import { ContactSidebar } from "./ContactSidebar";
import { InboxEmptyPanel } from "./InboxEmptyPanel";
import { getLastViewedConv } from "../../lib/last-viewed-conv";
import { cn } from "@/lib/cn";

/** Minimal pulse placeholder while auto-select resolves the first conversation. */
function ThreadLoadingPlaceholder() {
  return (
    <div
      className="flex h-full flex-col gap-3 p-6"
      aria-hidden="true"
      data-testid="inbox-thread-loading"
    >
      <div className="h-9 w-2/3 animate-pulse rounded-2xl rounded-tl-sm vt-bg-muted" />
      <div className="h-9 w-1/2 animate-pulse self-end rounded-2xl rounded-tr-sm vt-bg-muted" />
      <div className="h-14 w-3/5 animate-pulse rounded-2xl rounded-tl-sm vt-bg-muted" />
    </div>
  );
}

// ── Props ────────────────────────────────────────────────────────────────────

export interface AdrianInboxViewProps {
  /** SSR-hydrated initial data (conversation list + optional detail). */
  initialData: InitialInboxState;
  /** UUID of the conversation to deep-link (from ?conv= searchParam). */
  initialConvId: string | null;
  /** Inbox filter from URL searchParam (whitelisted). */
  initialFilter: string | null;
  /** Tenant ID (from URL params — drives RQ key scope). */
  tenantId: string;
}

// ── AdrianInboxView ───────────────────────────────────────────────────────────

/**
 * AdrianInboxView — real 3-pane inbox layout.
 * T-5: replaces the T-3 skeleton with ResizablePanelGroup + sub-panels.
 */
export function AdrianInboxView({
  initialData,
  initialConvId,
  initialFilter: _initialFilter,
  tenantId,
}: AdrianInboxViewProps) {
  const searchParams = useSearchParams();

  const activeConvId = useInboxStore((s) => s.activeConvId);
  const setActiveConvId = useInboxStore((s) => s.setActiveConvId);
  const contactSidebarOpen = useInboxStore((s) => s.contactSidebarOpen);
  const setContactSidebarOpen = useInboxStore((s) => s.setContactSidebarOpen);

  // Auto-collapse the contact sidebar when the agent panel gets too narrow, so the
  // thread (and its crowded header) gets room (UI-AUDIT-3 #3). Only auto-COLLAPSES —
  // never auto-opens — so it respects a manual toggle once the user acts.
  const desktopRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = desktopRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const NARROW_PX = 960;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? el.clientWidth;
      if (w > 0 && w < NARROW_PX && useInboxStore.getState().contactSidebarOpen) {
        setContactSidebarOpen(false);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [setContactSidebarOpen]);

  // Resolve conv ID: store (click selection, guaranteed reactive) takes precedence;
  // fall back to the URL ?conv= param for deep-link/refresh (spec RN-14/AC-3).
  const convIdFromUrl = searchParams.get("conv");
  const resolvedConvId = activeConvId ?? convIdFromUrl;

  // The SSR list tells us whether any conversation exists — used to show a skeleton
  // (while auto-select resolves) vs the real "no conversations" empty state, with no
  // flash of the empty message on a normal load (UI-AUDIT #1).
  const hasSsrConversations = initialData.conversations.length > 0;

  // Auto-select on entry (UI-AUDIT #1): deep-link ?conv= → last-viewed (persisted) →
  // newest from SSR. Runs once on mount; the client ConversationListPanel is the
  // reliable fallback when SSR returned no list.
  useEffect(() => {
    if (activeConvId) return;
    if (initialConvId) {
      setActiveConvId(initialConvId);
      return;
    }
    const persisted = getLastViewedConv(tenantId);
    if (persisted && initialData.conversations.some((c) => c.id === persisted)) {
      setActiveConvId(persisted);
      return;
    }
    const newest = initialData.conversations[0]?.id;
    if (newest) setActiveConvId(newest);
    // Run only on mount — intentionally omitting deps
  }, []);

  // Valeria reacciona: derive context when active conversation changes
  useValeriaReaccion(resolvedConvId);

  // Contact details for the ContactSidebar come from the SAME compound detail
  // query the thread uses (React Query dedupes by ["crm","conversation",id] — no
  // extra request). The lead carries the real PHI fields (name/phone/email/stage).
  const { data: detail } = useConversationDetail(resolvedConvId);
  const detailLead = detail?.lead ?? null;

  return (
    <NuqsAdapter>
      <section
        aria-label="Inbox de Adrián"
        className="flex h-full w-full flex-col overflow-hidden"
        data-testid="adrian-inbox-view"
      >
      {/* ── Desktop: 3-pane flex layout (≥768px) ──────────────────────────────
          Fixed-width side panels + flex-1 thread (Gmail-style). Robust vs the
          react-resizable-panels v4 sizing pitfall (defaultSize ignored without
          panel ids + useDefaultLayout). Resizable handles deferred. */}
      <div
        ref={desktopRef}
        className="hidden md:flex h-full w-full overflow-hidden"
        data-testid="inbox-desktop"
      >
        {/* Left: Conversation list (manages its own URL state — nuqs) */}
        <div
          className="w-80 shrink-0 border-r vt-border overflow-hidden"
          data-testid="inbox-panel-left"
        >
          <ConversationListPanel className="h-full" />
        </div>

        {/* Center: Thread (fills remaining space) */}
        <div
          className="flex-1 min-w-0 overflow-hidden"
          data-testid="inbox-panel-center"
        >
          {resolvedConvId ? (
            <InboxThread conversationId={resolvedConvId} className="h-full" />
          ) : hasSsrConversations ? (
            <ThreadLoadingPlaceholder />
          ) : (
            <InboxEmptyPanel
              variant="thread"
              data-testid="inbox-thread-empty"
              className="h-full"
            />
          )}
        </div>

        {/* Right: ContactSidebar (fixed width, toggle) */}
        {contactSidebarOpen && (
          <div
            className="w-80 shrink-0 border-l vt-border overflow-hidden"
            data-testid="inbox-panel-right"
          >
            {resolvedConvId ? (
              <ContactSidebar
                conversationId={resolvedConvId}
                leadId={detailLead?.id ?? resolvedConvId}
                contact={{
                  patientId: detailLead?.id ?? resolvedConvId,
                  name: detailLead?.name ?? null,
                  phone: detailLead?.phone ?? null,
                  email: detailLead?.email ?? null,
                  serviceInterest: detailLead?.service_interest ?? null,
                  statusTag: detailLead?.stage ?? null,
                }}
                className="h-full"
              />
            ) : hasSsrConversations ? (
              <ThreadLoadingPlaceholder />
            ) : (
              <InboxEmptyPanel variant="contact" className="h-full" />
            )}
          </div>
        )}
      </div>

      {/* ── Mobile: Single panel fallback (<768px) ──────────────────────────── */}
      <div
        className={cn("flex h-full w-full flex-col md:hidden")}
        data-testid="inbox-mobile"
        role="region"
        aria-label="Inbox de Adrián (móvil)"
      >
        {resolvedConvId ? (
          <InboxThread conversationId={resolvedConvId} className="flex-1" />
        ) : (
          <ConversationListPanel className="flex-1" />
        )}
      </div>
      </section>
    </NuqsAdapter>
  );
}
