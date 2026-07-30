/**
 * valeria-chat-happy.spec.ts — SC-1 Scenario happy render with 6 mock messages
 *
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-8
 *
 * spec_anchor: 01-spec.md § 1 SC-1 · 03-arch.md § 3.2 Playwright E2E suite
 * gherkin: SC-1 happy · render 6 mensajes mock orden correcto
 *
 * Given: ValeriaChat mounted con chatStoreSeed (6 MOCK_MESSAGES)
 * When:  page loads (no user action)
 * Then:  ChatHeader visible, Mode Pill "🤖 Modo agente", 4 msg-bubbles,
 *        DelegateMarker visible, TypingIndicator visible,
 *        first message contains "Buenos días"
 *
 * Route: /test-stack/shell-layout (public, no Clerk auth required)
 * Project: matches smoke project pattern (shell-organism/*.spec.ts via testMatch)
 *
 * MOCK_MESSAGES order (spec § 5.3):
 *   id=1  role=bot    (valeria)  → msg-bubble [0]
 *   id=2  role=user              → msg-bubble [1]
 *   id=3  role=delegate         → msg-delegate (NOT a msg-bubble)
 *   id=4  role=bot    (camila)  → msg-bubble [2]
 *   id=5  role=user              → msg-bubble [3]
 *   id=6  role=thinking (camila) → msg-thinking (NOT a msg-bubble)
 *
 * Total msg-bubble count: 4 (bot/user/bot/user only — delegate + thinking excluded)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "./fixtures/chat-store-seed.fixture";

test.describe("SC-1 — ValeriaChat happy render (6 mock messages)", () => {
  test("renders ChatHeader with avatar, name, status, and Mode Pill", async ({
    chatStoreSeed,
  }) => {
    // chatStoreSeed fixture: seeded con MOCK_MESSAGES + navega a la ruta

    const chatPage = chatStoreSeed;

    // ChatHeader visible
    await expect(chatPage.getChatHeader()).toBeVisible();

    // Mode pill "🤖 Modo agente"
    await expect(chatPage.getModePill()).toBeVisible();
    await expect(chatPage.getModePill()).toContainText("Modo agente");

    // Avatar / name visible in header (ChatHeader data-testid="chat-header")
    const header = chatPage.getChatHeader();
    await expect(header).toBeVisible();
  });

  test("renders exactly 4 msg-bubble elements (bot/user only, excluding delegate and thinking)", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    // MOCK_MESSAGES produces: bot(valeria) + user + delegate + bot(camila) + user + thinking
    // msg-bubble count = 4 (role=bot × 2 + role=user × 2)
    // delegate marker + thinking indicator are NOT msg-bubble
    await expect(chatPage.getAllBubbles()).toHaveCount(4);
  });

  test("renders DelegateMarker visible", async ({ chatStoreSeed }) => {
    const chatPage = chatStoreSeed;

    await expect(chatPage.getDelegateMarker()).toBeVisible();
  });

  test("renders TypingIndicator (thinking) visible", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    await expect(chatPage.getThinkingIndicator()).toBeVisible();
  });

  test("first message bubble contains 'Buenos días'", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    // MOCK_MESSAGES[0]: bot(valeria) — "¡Buenos días! Tienes 8 turnos hoy…"
    await expect(chatPage.getMessage(0)).toContainText("Buenos días");
  });

  test("Composer input is visible and Send button is present", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    await expect(chatPage.getComposer()).toBeVisible();
    await expect(chatPage.getSendButton()).toBeVisible();
  });

  test("3 icon stub buttons are visible (📎 🎙️ ⚡)", async ({
    chatStoreSeed,
  }) => {
    const chatPage = chatStoreSeed;

    // Stubs: data-testid composer-attach, composer-voice, composer-quick
    await expect(
      chatPage.page.locator('[data-testid="composer-attach"]'),
    ).toBeVisible();
    await expect(
      chatPage.page.locator('[data-testid="composer-voice"]'),
    ).toBeVisible();
    await expect(
      chatPage.page.locator('[data-testid="composer-quick"]'),
    ).toBeVisible();
  });
});
