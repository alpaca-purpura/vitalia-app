// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s6-TBD
/**
 * chat-store.ts — Zustand store for Valeria chat state (F1-S6).
 *
 * spec_anchor: 01-spec.md § 5.3 + § 5.4 · 03-arch.md § 2.2 + § 2.3
 *
 * Separation of Concerns: chat lifecycle (ephemeral, user-driven) is separate from
 * shell layout state (shell-store.ts, persistent, UI chrome). Keeps F2-S* WebSocket
 * wiring clean — replace sendMessage mock with real SSE handler without touching shell.
 *
 * NOT persisted — chat is ephemeral cross-reload. Re-hydrates MOCK_MESSAGES on mount.
 * F2-S* will add persist via API/DB when WebSocket real is wired.
 *
 * sendMessage mock flow (spec § 5.4):
 * 1. Push user message + thinking indicator
 * 2. Set status='thinking'
 * 3. setTimeout 800ms → remove thinking + push bot canned response
 * 4. Set status='idle'
 *
 * Determinism: MOCK_RESPONSES[count % len] — NO random — Playwright golden stability.
 * Idempotency: status='thinking' guard prevents double dispatch.
 *
 * LIFT CANDIDATE: chat store pattern cross-brand when ≥2 brands need it.
 * Per anti-duplication.md — brand-local Vitalia per first occurrence.
 *
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: not_applicable — shell chrome UI, no PHI, mock data only.
 * No Clerk Organizations used — per MEMORY.md::no-clerk-organizations 2026-05-20.
 *
 * downstream-regression-na: brand-local store; no cross-brand consumers
 */

import { create } from "zustand/react"; // index export* falla en turbopack (HB-78)
import type { AgentSlug } from "@/lib/agent-catalog";
import { AGENT_CATALOG, DEFAULT_CHAT_AGENT } from "@/lib/agent-catalog";
import {
  MOCK_MESSAGES,
  MOCK_RESPONSES_BY_AGENT,
} from "@/stores/_mock-messages";
import {
  MOCK_CONVERSATIONS,
  type MockConversation,
} from "@/stores/_mock-conversations";

/** Message role — determines rendering variant */
export type MessageRole = "bot" | "user" | "delegate" | "thinking";

/** Chat message shape — covers all role variants */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  /** bot/user/thinking text content */
  content?: string;
  /** 'HH:MM' — calculated at runtime via es-PE locale */
  time?: string;
  /** bot/thinking source agent. Default: activeAgent */
  agent?: AgentSlug;
  /** delegate only — who delegates */
  fromAgent?: AgentSlug;
  /** delegate only — who receives the delegation */
  toAgent?: AgentSlug;
  /** delegate only — label of the mode ('Mantener', 'Reactivar', 'Multiplicar') */
  delegateMode?: string;
}

/** Chat store status */
export type ChatStatus = "idle" | "thinking" | "streaming";

/** Chat store interface */
export interface ChatStore {
  messages: ChatMessage[];
  /**
   * UI-local conversation history (T-3, RN-13). Archive-on-"+" target.
   * NOT backed by BE/agentic persistence — chrome-only, seeded from MOCK_CONVERSATIONS.
   * Real persistence is out of T-3 scope (would require /pm-vitalia escalate).
   */
  conversations: MockConversation[];
  /** Active agent for new messages. Default: 'valeria'. No UI consumer F1-S6. */
  activeAgent: AgentSlug;
  status: ChatStatus;
  /**
   * Mock sendMessage — simulates agent response with 800ms thinking delay.
   * Deterministic rotation: MOCK_RESPONSES[userCount % len].
   * Idempotent: no-op if status='thinking', empty, or whitespace-only content.
   */
  sendMessage(content: string): void;
  /** Reset chat — used for empty state testing and clear feature. */
  clearMessages(): void;
  /**
   * New conversation (T-3, "+", RN-13 / SC-8). UI-local only:
   *  1. If the current chat has messages → archive a generic non-PHI entry to
   *     the TOP of `conversations` (newest first, group 'today').
   *  2. Clear the chat (messages=[], status='idle') for a fresh start.
   * No-op archive when chat already empty (no phantom entry).
   * Title is generic ("Conversación HH:MM") — NEVER echoes message content (HIPAA-lite).
   */
  newConversation(): void;
  /**
   * Update active agent. API exists but NO UI consumer in F1-S6.
   * Prepared for future "AgentSwitcher dropdown in ChatHeader" sub-story.
   * Per spec § 0 D9 + 03-arch.md § 2.3 ratified.
   */
  setActiveAgent(agent: AgentSlug): void;
}

/**
 * Helper — get current time as HH:MM string using es-PE locale.
 * Consistent with spec § 5.4 + spec § 8 runtime time calculation.
 * Uses hour12: false to guarantee 24-hour format (e.g. '09:01') cross-environment.
 */
function getNowHHMM(): string {
  return new Date().toLocaleTimeString("es-PE", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/**
 * Helper — capitalize first letter of a string.
 * Used for thinking indicator: "valeria" → "Valeria está escribiendo…"
 */
function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Resolve initial messages for the store.
 *
 * Non-production only: reads `window.__chatStoreSeed__` if present.
 * Set via Playwright `page.addInitScript` in E2E tests BEFORE page load.
 * Falls back to MOCK_MESSAGES when not set (dev browser, test stack).
 *
 * This guard is intentionally BEFORE `create()` so it runs once at module init.
 * NODE_ENV guard ensures zero production footprint.
 */
function resolveInitialMessages(): ChatMessage[] {
  if (
    process.env.NODE_ENV !== "production" &&
    typeof window !== "undefined" &&
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    Array.isArray((window as any).__chatStoreSeed__)
  ) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (window as any).__chatStoreSeed__ as ChatMessage[];
  }
  return [...MOCK_MESSAGES];
}

export const useChatStore = create<ChatStore>((set, get) => ({
  // ── State ──────────────────────────────────────────────────────────────────
  messages: resolveInitialMessages(),
  // UI-local history seed (T-3). Spread → mutation-safe, empty-able for SC-13.
  conversations: [...MOCK_CONVERSATIONS],
  activeAgent: DEFAULT_CHAT_AGENT,
  status: "idle",

  // ── Actions ────────────────────────────────────────────────────────────────

  sendMessage: (content: string) => {
    const trimmed = content.trim();
    // No-op guards
    if (!trimmed) return;
    if (get().status === "thinking") return; // idempotency guard

    const activeAgent = get().activeAgent;
    const agentName =
      AGENT_CATALOG[activeAgent]?.name ?? capitalize(activeAgent);

    // Count prior user messages for deterministic rotation
    const userCount = get().messages.filter((m) => m.role === "user").length;

    // Get responses for active agent; fallback to valeria if empty
    const responses = MOCK_RESPONSES_BY_AGENT[activeAgent]?.length
      ? MOCK_RESPONSES_BY_AGENT[activeAgent]
      : MOCK_RESPONSES_BY_AGENT.valeria;

    const replyContent = responses[userCount % responses.length]?.content ?? "";

    const now = getNowHHMM();

    // Step 1+2: Push user message + thinking indicator, set status='thinking'
    set((s) => ({
      status: "thinking",
      messages: [
        ...s.messages,
        {
          id: crypto.randomUUID(),
          role: "user" as MessageRole,
          content: trimmed,
          time: now,
        },
        {
          id: crypto.randomUUID(),
          role: "thinking" as MessageRole,
          agent: activeAgent,
          content: `${agentName} está escribiendo…`,
        },
      ],
    }));

    // Step 3+4: After 800ms — remove thinking, push bot reply, set status='idle'
    setTimeout(() => {
      const replyTime = getNowHHMM();
      set((s) => ({
        status: "idle",
        messages: [
          ...s.messages.filter((m) => m.role !== "thinking"),
          {
            id: crypto.randomUUID(),
            role: "bot" as MessageRole,
            agent: activeAgent,
            content: replyContent,
            time: replyTime,
          },
        ],
      }));
    }, 800);
  },

  clearMessages: () => set({ messages: [], status: "idle" }),

  newConversation: () => {
    const { messages } = get();
    // Only archive when there is something to archive (no phantom entry).
    if (messages.length > 0) {
      const archived: MockConversation = {
        id: crypto.randomUUID(),
        // Generic, non-PHI title — NEVER echoes message content (HIPAA-lite chrome guard).
        title: `Conversación ${getNowHHMM()}`,
        meta: `${getNowHHMM()} · ${messages.length} mensajes`,
        group: "today",
      };
      set((s) => ({ conversations: [archived, ...s.conversations] }));
    }
    // Fresh start.
    set({ messages: [], status: "idle" });
  },

  setActiveAgent: (agent: AgentSlug) => set({ activeAgent: agent }),
}));

/**
 * E2E test hook — expose store on window in non-production.
 *
 * Playwright POMs (ValeriaChatPage) use `window.__chatStore__` for:
 * - `getActiveAgent()` — read store state without DOM queries
 * - `clearMessages()` — reset chat state programmatically
 * - `waitForStatus()` — poll status for thinking/idle transitions
 *
 * NODE_ENV guard ensures zero production footprint.
 * typeof window guard ensures SSR safety (Next.js server components).
 *
 * Magic: double-underscore convention (`__chatStore__`) signals test-only API.
 * Per 03-arch.md § 3.2 POM contract + T-7 production_code decision.
 */
if (process.env.NODE_ENV !== "production" && typeof window !== "undefined") {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).__chatStore__ = useChatStore;
}
