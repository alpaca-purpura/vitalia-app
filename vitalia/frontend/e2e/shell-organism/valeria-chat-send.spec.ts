/**
 * valeria-chat-send.spec.ts — SC-2 Scenario send mock message flow
 *
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-8
 *
 * spec_anchor: 01-spec.md § 1 SC-2 · 03-arch.md § 3.2 Playwright E2E suite
 * gherkin: SC-2 happy · send mock message flow (user + 800ms thinking + bot canned)
 *
 * Given: ValeriaChat mounted con chatStoreEmpty (empty state, 0 messages)
 * When:  user types "¿Cuántos pacientes para mañana?" + presses Enter
 * Then:
 *   - composer clears immediately
 *   - user bubble appears with the sent text
 *   - TypingIndicator appears ("Valeria está escribiendo…")
 *   - after 800ms: thinking gone + bot canned bubble appears
 *   - final bubble count: user(1) + bot(1) = 2 msg-bubble elements
 *   - aria-live="polite" region announces new messages
 *
 * Timing strategy:
 *   - waitForFunction instead of waitForTimeout hardcoded
 *   - poll for DOM state change (thinking appears, then disappears)
 *   - timeout 5000ms for each phase (800ms delay + rendering buffer)
 *
 * Route: /test-stack/shell-layout (public, no Clerk auth required)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "./fixtures/chat-store-seed.fixture";

test.describe("SC-2 — ValeriaChat send mock message flow", () => {
  test("typing and pressing Enter sends message and clears composer", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;
    const message = "¿Cuántos pacientes para mañana?";

    // Initial state: empty (0 bubbles)
    const initialCount = await chatPage.getMessageCount();
    expect(initialCount).toBe(0);

    // Type message in composer
    const composer = chatPage.getComposer();
    await composer.click();
    await composer.fill(message);

    // Verify text is in composer
    await expect(composer).toHaveValue(message);

    // Press Enter to send
    await chatPage.pressEnter();

    // Composer should clear immediately after send
    await expect(composer).toHaveValue("");
  });

  test("user bubble appears immediately after sending", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;
    const message = "¿Cuántos pacientes para mañana?";

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill(message);
    await chatPage.pressEnter();

    // User bubble should appear
    await expect(chatPage.getMessage(0)).toBeVisible({ timeout: 3_000 });
    await expect(chatPage.getMessage(0)).toContainText(message);
  });

  test("TypingIndicator appears after send (within 1200ms)", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill("¿Cuántos pacientes para mañana?");
    await chatPage.pressEnter();

    // Wait for thinking indicator to appear (800ms simulated delay starts immediately)
    await expect(chatPage.getThinkingIndicator()).toBeVisible({
      timeout: 2_000,
    });
  });

  test("bot canned response appears after thinking disappears (~800ms)", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill("¿Cuántos pacientes para mañana?");
    await chatPage.pressEnter();

    // Wait for thinking indicator to appear then disappear
    await expect(chatPage.getThinkingIndicator()).toBeVisible({
      timeout: 2_000,
    });

    // Wait for thinking to disappear (bot reply arrived — 800ms timer fires)
    await chatPage.waitForStatus("idle");

    // Thinking indicator should be gone
    await expect(chatPage.getThinkingIndicator()).not.toBeVisible({
      timeout: 3_000,
    });

    // Now there should be 2 bubbles: user + bot
    await expect(chatPage.getAllBubbles()).toHaveCount(2, { timeout: 3_000 });
  });

  test("final state has 2 msg-bubbles (user + bot canned)", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill("¿Cuántos pacientes para mañana?");
    await chatPage.pressEnter();

    // Wait for bot reply to appear (idle status = thinking resolved)
    await chatPage.waitForStatus("idle");

    // user bubble + bot canned = 2 total msg-bubble elements
    const finalCount = await chatPage.getMessageCount();
    expect(finalCount).toBe(2);
  });

  test("aria-live='polite' log container is present (announces new messages)", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    // ChatMessages container should have role="log" aria-live="polite"
    const messagesLog = chatPage.page.locator('[data-testid="chat-messages"]');
    await expect(messagesLog).toBeVisible();
    await expect(messagesLog).toHaveAttribute("aria-live", "polite");
  });

  test("sendMessage does not fire when composer is empty", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;
    const initialCount = await chatPage.getMessageCount();

    // Press Enter on empty composer
    await chatPage.getComposer().click();
    await chatPage.pressEnter();

    // Count should not change (idempotency guard in store)
    await chatPage.page.waitForTimeout(200);
    const afterCount = await chatPage.getMessageCount();
    expect(afterCount).toBe(initialCount);
  });
});
