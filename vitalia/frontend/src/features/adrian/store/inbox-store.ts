// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * inbox-store.ts — Inbox UI state (Zustand).
 * T-4 vitalia-fase2-adrian-inbox (MIGRATE from features/inbox/store/inbox-store.ts + EXTEND)
 *
 * UI-ONLY state: no server/API data here (that lives in React Query).
 * Persisted across re-renders within a session (not persisted to localStorage — HIPAA-lite).
 *
 * EXTEND (T-4): added `priorValeriaState` slot for ConversationModeButton (⛶full).
 * When user collapses Valeria via "Modo conversación", we store the prior state
 * so we can restore it when they toggle back.
 *
 * State shape per 03-arch-fe.md § 4 + § 6:
 *   - expandedActivityStream: boolean
 *   - contactSidebarOpen: boolean
 *   - attachQueue: File[]
 *   - retractingMessages: Set<string>
 *   - proactiveModalOpen: boolean
 *   - priorValeriaState: 'rail' | 'full' | null  ← NEW (T-4 EXTEND)
 *   - activeConvId: string | null                ← NEW (T-4 EXTEND — tracks active thread)
 *
 * PHI constraint: NEVER put PHI (patient names, phone, email, diagnosis) in this store.
 * Only IDs and UI flags.
 *
 * downstream-regression-na: brand-local FE store; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § 4 + § 6 + 06-tickets.yaml T-4
 */
"use client";

import { create } from "zustand/react"; // index export* falla en turbopack (HB-78)

/** ValeriaState shape (mirrors shell-store ValeriaState enum) */
export type ValeriaStateValue = "collapsed" | "rail" | "full";

/** Inbox UI state shape */
interface InboxState {
  /** Whether the ActivityStream is expanded (32px → 240px) */
  expandedActivityStream: boolean;
  /** Whether the ContactSidebar is visible (collapsable right panel) */
  contactSidebarOpen: boolean;
  /** Files queued for attachment before send */
  attachQueue: File[];
  /** Message IDs currently being retracted (for loading state on chip) */
  retractingMessages: Set<string>;
  /** Whether the ProactiveOutboundModal is open */
  proactiveModalOpen: boolean;
  /**
   * Prior Valeria state before "Modo conversación" collapsed it.
   * Used by ConversationModeButton to restore Valeria state on un-collapse.
   * null = full mode is not active or no prior state to restore.
   * T-4 EXTEND (03-arch-fe.md § 6)
   */
  priorValeriaState: ValeriaStateValue | null;
  /**
   * ID of the currently open conversation thread.
   * Used to trigger useValeriaReaccion and manage thread-scoped state.
   * T-4 EXTEND
   */
  activeConvId: string | null;
}

/** Inbox UI actions */
interface InboxActions {
  /** Toggle the ActivityStream expanded state */
  toggleActivityStream: () => void;
  /** Toggle the ContactSidebar visibility */
  toggleContactSidebar: () => void;
  /** Set the ContactSidebar visibility explicitly (used by the narrow-width auto-collapse) */
  setContactSidebarOpen: (open: boolean) => void;
  /** Add files to the attach queue */
  enqueueAttach: (files: File[]) => void;
  /** Remove a specific file from the attach queue by index */
  dequeueAttach: (index: number) => void;
  /** Clear all files from the attach queue (after send) */
  clearAttachQueue: () => void;
  /** Mark a message as being retracted (show spinner on chip) */
  markRetracting: (messageId: string) => void;
  /** Unmark a message from retracting state */
  unmarkRetracting: (messageId: string) => void;
  /** Open the proactive outbound modal */
  openProactiveModal: () => void;
  /** Close the proactive outbound modal */
  closeProactiveModal: () => void;
  /**
   * Store prior Valeria state before collapsing to full-canvas mode.
   * Called by ConversationModeButton before setValeriaState('collapsed').
   * T-4 EXTEND
   */
  setPriorValeriaState: (state: ValeriaStateValue | null) => void;
  /**
   * Set the active conversation ID.
   * Called when a conversation item is selected in InboxConvList.
   * T-4 EXTEND
   */
  setActiveConvId: (convId: string | null) => void;
  /** Reset all UI state (e.g. when navigating to a different conversation) */
  reset: () => void;
}

const initialState: InboxState = {
  expandedActivityStream: false,
  contactSidebarOpen: true,
  attachQueue: [],
  retractingMessages: new Set<string>(),
  proactiveModalOpen: false,
  priorValeriaState: null,
  activeConvId: null,
};

/**
 * useInboxStore — Zustand store for inbox UI state.
 *
 * Usage (Client Components only):
 *   const expandedActivityStream = useInboxStore((s) => s.expandedActivityStream);
 *   const toggleActivityStream = useInboxStore((s) => s.toggleActivityStream);
 *   // T-4 EXTEND:
 *   const priorValeriaState = useInboxStore((s) => s.priorValeriaState);
 *   const setPriorValeriaState = useInboxStore((s) => s.setPriorValeriaState);
 */
export const useInboxStore = create<InboxState & InboxActions>()((set) => ({
  ...initialState,

  toggleActivityStream: () =>
    set((s) => ({ expandedActivityStream: !s.expandedActivityStream })),

  toggleContactSidebar: () =>
    set((s) => ({ contactSidebarOpen: !s.contactSidebarOpen })),

  setContactSidebarOpen: (open) => set({ contactSidebarOpen: open }),

  enqueueAttach: (files) =>
    set((s) => ({ attachQueue: [...s.attachQueue, ...files] })),

  dequeueAttach: (index) =>
    set((s) => ({
      attachQueue: s.attachQueue.filter((_, i) => i !== index),
    })),

  clearAttachQueue: () => set({ attachQueue: [] }),

  markRetracting: (messageId) =>
    set((s) => ({
      retractingMessages: new Set([...s.retractingMessages, messageId]),
    })),

  unmarkRetracting: (messageId) =>
    set((s) => {
      const next = new Set(s.retractingMessages);
      next.delete(messageId);
      return { retractingMessages: next };
    }),

  openProactiveModal: () => set({ proactiveModalOpen: true }),

  closeProactiveModal: () => set({ proactiveModalOpen: false }),

  setPriorValeriaState: (state) => set({ priorValeriaState: state }),

  setActiveConvId: (convId) => set({ activeConvId: convId }),

  reset: () =>
    set({
      ...initialState,
      retractingMessages: new Set<string>(),
    }),
}));
