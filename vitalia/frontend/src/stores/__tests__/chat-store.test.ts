/**
 * chat-store.test.ts — TDD RED-first tests for chat-store Zustand store.
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-2
 *
 * Tests: sendMessage mock flow, clearMessages, setActiveAgent, deterministic
 * MOCK_RESPONSES rotation, idempotency guard (status='thinking'), empty/whitespace
 * guards, time format HH:MM, Spanish neutro verification (no voseo).
 *
 * gherkin_coverage:
 * - SC-1 happy: 6 mocks render, activeAgent='valeria', status='idle'
 * - SC-2 happy: sendMessage → user + 800ms thinking → canned bot
 * - SC-5 empty_state: clearMessages resets
 * - (idempotency) status='thinking' guard bloquea concurrent sends
 * - (future-prep) setActiveAgent API expuesto sin UI consumer F1-S6
 * - SC-7 i18n: MOCK_MESSAGES + MOCK_RESPONSES no voseo
 *
 * 03-arch.md § 2.2 + § 2.3 sendMessage flow + chat-store contract.
 * Named export (no default export) per FSD-Lite enforce.
 *
 * downstream-regression-na: brand-local store test; no cross-brand consumers
 * # voseo-allowed: test file verifies ABSENCE of voseo — references glosario terms in VOSEO_REGEX
 */

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { useChatStore } from "../chat-store";
import {
  MOCK_MESSAGES,
  MOCK_RESPONSES_BY_AGENT,
} from "@/components/shared/shell-organism/_mock-messages";
import { MOCK_CONVERSATIONS } from "@/components/shared/shell-organism/_mock-conversations";

describe("useChatStore", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Reset to initial state before each test
    useChatStore.setState({
      messages: [...MOCK_MESSAGES],
      activeAgent: "valeria",
      status: "idle",
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    useChatStore.getState().clearMessages();
  });

  // ── SC-1 happy: initial state ──────────────────────────────────────────────

  describe("initial state", () => {
    it("messages equals MOCK_MESSAGES (6 items)", () => {
      const { messages } = useChatStore.getState();
      expect(messages).toHaveLength(6);
    });

    it("activeAgent defaults to 'valeria'", () => {
      expect(useChatStore.getState().activeAgent).toBe("valeria");
    });

    it("status defaults to 'idle'", () => {
      expect(useChatStore.getState().status).toBe("idle");
    });

    it("MOCK_MESSAGES order: bot(valeria) → user → delegate → bot(camila) → user → thinking(camila)", () => {
      const { messages } = useChatStore.getState();
      expect(messages[0]?.role).toBe("bot");
      expect(messages[0]?.agent).toBe("valeria");
      expect(messages[1]?.role).toBe("user");
      expect(messages[2]?.role).toBe("delegate");
      expect(messages[3]?.role).toBe("bot");
      expect(messages[3]?.agent).toBe("camila");
      expect(messages[4]?.role).toBe("user");
      expect(messages[5]?.role).toBe("thinking");
      expect(messages[5]?.agent).toBe("camila");
    });

    it("MOCK_MESSAGES IDs stable '1'..'6' (deterministic for snapshots)", () => {
      const { messages } = useChatStore.getState();
      expect(messages[0]?.id).toBe("1");
      expect(messages[1]?.id).toBe("2");
      expect(messages[2]?.id).toBe("3");
      expect(messages[3]?.id).toBe("4");
      expect(messages[4]?.id).toBe("5");
      expect(messages[5]?.id).toBe("6");
    });
  });

  // ── SC-2 happy: sendMessage flow ─────────────────────────────────────────────

  describe("sendMessage", () => {
    it("sendMessage('test') pushes user message + thinking message + sets status='thinking'", () => {
      useChatStore.getState().clearMessages();
      useChatStore.getState().sendMessage("test");

      const { messages, status } = useChatStore.getState();
      // user message pushed
      const userMsg = messages.find((m) => m.role === "user");
      expect(userMsg).toBeDefined();
      expect(userMsg?.content).toBe("test");
      // thinking message pushed
      const thinkingMsg = messages.find((m) => m.role === "thinking");
      expect(thinkingMsg).toBeDefined();
      expect(thinkingMsg?.agent).toBe("valeria");
      // status = thinking
      expect(status).toBe("thinking");
    });

    it("after 800ms: thinking removed, bot canned reply added, status='idle'", () => {
      useChatStore.getState().clearMessages();
      useChatStore.getState().sendMessage("hola");

      // Before timer fires
      expect(useChatStore.getState().status).toBe("thinking");

      // Advance timer
      vi.advanceTimersByTime(800);

      const { messages, status } = useChatStore.getState();
      // No more thinking messages
      const thinkingMsgs = messages.filter((m) => m.role === "thinking");
      expect(thinkingMsgs).toHaveLength(0);
      // Bot reply exists
      const botMsgs = messages.filter((m) => m.role === "bot");
      expect(botMsgs.length).toBeGreaterThan(0);
      // status back to idle
      expect(status).toBe("idle");
    });

    it("bot canned reply content matches MOCK_RESPONSES[0] (first send, count=0)", () => {
      useChatStore.getState().clearMessages();
      useChatStore.getState().sendMessage("primera pregunta");
      vi.advanceTimersByTime(800);

      const { messages } = useChatStore.getState();
      const botMsg = messages.find((m) => m.role === "bot");
      expect(botMsg?.content).toBe(MOCK_RESPONSES_BY_AGENT.valeria[0]?.content);
    });

    it("MOCK_RESPONSES rotativo deterministic (count % len) per activeAgent", () => {
      useChatStore.getState().clearMessages();
      const responses = MOCK_RESPONSES_BY_AGENT.valeria;
      const len = responses.length;

      // Send len + 1 messages; the (len+1)th should cycle back to index 0
      for (let i = 0; i < len; i++) {
        useChatStore.getState().sendMessage(`pregunta ${i}`);
        vi.advanceTimersByTime(800);
      }

      // Now send one more — should cycle back to responses[0]
      useChatStore.getState().sendMessage("ciclo completo");
      vi.advanceTimersByTime(800);

      const { messages } = useChatStore.getState();
      const botMsgs = messages.filter((m) => m.role === "bot");
      // The last bot message should be responses[0] again (index len % len = 0)
      const lastBot = botMsgs[botMsgs.length - 1];
      expect(lastBot?.content).toBe(responses[0]?.content);
    });

    it("time format 'HH:MM' matches regex /^\\d{2}:\\d{2}$/", () => {
      useChatStore.getState().clearMessages();
      useChatStore.getState().sendMessage("test time");

      const { messages } = useChatStore.getState();
      const userMsg = messages.find((m) => m.role === "user");
      expect(userMsg?.time).toMatch(/^\d{2}:\d{2}$/);

      vi.advanceTimersByTime(800);
      const botMsg = useChatStore
        .getState()
        .messages.find((m) => m.role === "bot");
      expect(botMsg?.time).toMatch(/^\d{2}:\d{2}$/);
    });

    it("thinking message content shows agent name + 'está escribiendo…'", () => {
      useChatStore.getState().clearMessages();
      useChatStore.getState().sendMessage("test");

      const thinkingMsg = useChatStore
        .getState()
        .messages.find((m) => m.role === "thinking");
      expect(thinkingMsg?.content).toContain("está escribiendo");
    });
  });

  // ── (idempotency) status='thinking' guard ─────────────────────────────────

  describe("idempotency guard", () => {
    it("sendMessage while status='thinking' is a no-op (idempotency)", () => {
      useChatStore.getState().clearMessages();
      useChatStore.getState().sendMessage("primer mensaje");

      const messagesAfterFirst = useChatStore.getState().messages.length;

      // Call again while thinking
      useChatStore.getState().sendMessage("segundo mensaje ignorado");
      expect(useChatStore.getState().messages.length).toBe(messagesAfterFirst);

      vi.advanceTimersByTime(800);
    });

    it("sendMessage(empty string) is a no-op", () => {
      useChatStore.getState().clearMessages();
      const initialLen = useChatStore.getState().messages.length;
      useChatStore.getState().sendMessage("");
      expect(useChatStore.getState().messages.length).toBe(initialLen);
      expect(useChatStore.getState().status).toBe("idle");
    });

    it("sendMessage('   ') (whitespace) trimmed → no-op", () => {
      useChatStore.getState().clearMessages();
      const initialLen = useChatStore.getState().messages.length;
      useChatStore.getState().sendMessage("   ");
      expect(useChatStore.getState().messages.length).toBe(initialLen);
      expect(useChatStore.getState().status).toBe("idle");
    });
  });

  // ── SC-5 empty_state: clearMessages ──────────────────────────────────────────

  describe("clearMessages", () => {
    it("clearMessages sets messages=[] + status='idle'", () => {
      useChatStore.getState().clearMessages();
      const { messages, status } = useChatStore.getState();
      expect(messages).toHaveLength(0);
      expect(status).toBe("idle");
    });
  });

  // ── (future-prep) setActiveAgent ──────────────────────────────────────────────

  describe("setActiveAgent", () => {
    it("setActiveAgent('camila') updates activeAgent", () => {
      useChatStore.getState().setActiveAgent("camila");
      expect(useChatStore.getState().activeAgent).toBe("camila");
    });

    it("setActiveAgent back to 'valeria'", () => {
      useChatStore.getState().setActiveAgent("camila");
      useChatStore.getState().setActiveAgent("valeria");
      expect(useChatStore.getState().activeAgent).toBe("valeria");
    });
  });

  // ── T-3 conversations slice + newConversation (RN-13 / SC-8 / SC-13) ────────

  describe("conversations slice", () => {
    beforeEach(() => {
      useChatStore.setState({
        messages: [...MOCK_MESSAGES],
        conversations: [...MOCK_CONVERSATIONS],
        activeAgent: "valeria",
        status: "idle",
      });
    });

    it("conversations seeded from MOCK_CONVERSATIONS (8 items)", () => {
      expect(useChatStore.getState().conversations).toHaveLength(8);
    });

    it("conversations can be emptied (drives SC-13 empty history)", () => {
      useChatStore.setState({ conversations: [] });
      expect(useChatStore.getState().conversations).toHaveLength(0);
    });
  });

  describe("newConversation (RN-13 / SC-8)", () => {
    beforeEach(() => {
      vi.useRealTimers();
      useChatStore.setState({
        messages: [...MOCK_MESSAGES],
        conversations: [...MOCK_CONVERSATIONS],
        activeAgent: "valeria",
        status: "idle",
      });
    });

    it("clears the current chat (messages=[] + status='idle')", () => {
      useChatStore.getState().newConversation();
      const { messages, status } = useChatStore.getState();
      expect(messages).toHaveLength(0);
      expect(status).toBe("idle");
    });

    it("archives the current conversation to history (UI-local, prepended)", () => {
      const before = useChatStore.getState().conversations.length;
      useChatStore.getState().newConversation();
      const after = useChatStore.getState().conversations;
      expect(after.length).toBe(before + 1);
      // newest first
      expect(after[0]?.group).toBe("today");
    });

    it("does NOT archive when the chat is already empty (no phantom entry)", () => {
      useChatStore.setState({ messages: [] });
      const before = useChatStore.getState().conversations.length;
      useChatStore.getState().newConversation();
      expect(useChatStore.getState().conversations.length).toBe(before);
    });

    it("archived entry carries a non-PHI generic title (no message content leak)", () => {
      useChatStore.getState().newConversation();
      const archived = useChatStore.getState().conversations[0];
      expect(archived?.title).toBeTruthy();
      // title must NOT echo raw chat message content (HIPAA-lite chrome guard)
      expect(archived?.title).not.toContain("Tienes");
    });
  });

  // ── SC-7 i18n: MOCK_MESSAGES + MOCK_RESPONSES Spanish neutro tuteo ──────────

  describe("Spanish neutro verification", () => {
    const VOSEO_REGEX =
      /\b(vos|sos|tenés|podés|dale|mirá|fijate|empezá|querés|hacés|venís|dejá|poné|usá|elegí|agregá|configurá|revisá|guardá|abrí|volvé|cambiá|ofrecés|cobrás|activás|desactivás)\b/i;

    it("MOCK_MESSAGES verbatim spec § 6 (tuteo: Tienes, abro, ábrela) — no voseo", () => {
      const allContent = MOCK_MESSAGES.map((m) => m.content ?? "").join(" ");
      expect(VOSEO_REGEX.test(allContent)).toBe(false);
    });

    it("MOCK_RESPONSES verbatim spec § 8 (no voseo — tuteo form 'Quieres')", () => {
      const allContent = MOCK_RESPONSES_BY_AGENT.valeria
        .map((r) => r.content)
        .join(" ");
      expect(VOSEO_REGEX.test(allContent)).toBe(false);
    });

    it("MOCK_MESSAGES first msg contains 'Tienes' (tuteo form)", () => {
      const firstMsg = MOCK_MESSAGES[0];
      expect(firstMsg?.content).toContain("Tienes");
    });

    it("MOCK_MESSAGES user msg 5 contains 'ábrela' (tuteo)", () => {
      const msg5 = MOCK_MESSAGES[4];
      expect(msg5?.content).toContain("ábrela");
    });

    it("MOCK_RESPONSES contain 'Quieres' (tuteo) — no voseo variant", () => {
      const allContent = MOCK_RESPONSES_BY_AGENT.valeria
        .map((r) => r.content)
        .join(" ");
      expect(allContent).toContain("Quieres");

      expect(allContent).not.toMatch(/Querés/);
    });
  });
});
