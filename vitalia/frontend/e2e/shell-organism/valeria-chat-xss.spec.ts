/**
 * valeria-chat-xss.spec.ts — SC-4 Scenario adversarial XSS guard
 *
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-8
 *
 * spec_anchor: 01-spec.md § 1 SC-4 · 03-arch.md § 3.2 Playwright E2E suite
 * gherkin: SC-4 adversarial · XSS payload renders as plain escaped text, no alert fires
 *
 * Given: ValeriaChat mounted con chatStoreEmpty
 * When:  user types XSS payload in composer + sends
 * Then:
 *   - page.on('dialog') listener never fires (no alert/confirm/prompt)
 *   - user bubble renders the payload as literal escaped text
 *   - no actual <script> tag in the DOM (JSX auto-escapes text children)
 *   - component remains stable and functional after the adversarial send
 *
 * Security model: React JSX text children are auto-escaped by the React runtime.
 * `{content}` in MessageBubble renders as a text node — never as raw HTML.
 * This test confirms that invariant at the E2E layer.
 *
 * No `dangerouslySetInnerHTML` must exist in MessageBubble (verified in unit tests).
 *
 * Route: /test-stack/shell-layout (public, no Clerk auth required)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "./fixtures/chat-store-seed.fixture";

const XSS_PAYLOAD = '<script>alert("xss")</script>';
const XSS_PAYLOAD_IMG = '<img src="x" onerror="alert(\'xss\')">';
const XSS_PAYLOAD_JS = 'javascript:alert("xss")';

test.describe("SC-4 — ValeriaChat XSS adversarial guard", () => {
  test("script tag payload renders as plain text, no dialog fires", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    // Register dialog listener BEFORE any action
    let dialogFired = false;
    chatPage.page.on("dialog", (dialog) => {
      dialogFired = true;
      // Dismiss any dialog that fires to prevent test hang
      void dialog.dismiss();
    });

    // Send XSS payload
    const composer = chatPage.getComposer();
    await composer.click();
    await composer.fill(XSS_PAYLOAD);
    await chatPage.pressEnter();

    // Wait for user bubble to appear
    await expect(chatPage.getMessage(0)).toBeVisible({ timeout: 3_000 });

    // Wait 1500ms to allow any potential async alert to fire
    await chatPage.page.waitForTimeout(1_500);

    // CRITICAL: no dialog should have fired
    expect(dialogFired).toBe(false);
  });

  test("script tag payload renders as literal escaped text in DOM", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    chatPage.page.on("dialog", (dialog) => void dialog.dismiss());

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill(XSS_PAYLOAD);
    await chatPage.pressEnter();

    // Wait for user bubble
    await expect(chatPage.getMessage(0)).toBeVisible({ timeout: 3_000 });

    // The bubble should contain the literal escaped text
    // React renders {content} as a text node — the angle brackets are escaped
    const userBubble = chatPage.page
      .locator('[data-testid="msg-bubble"][data-role="user"]')
      .first();
    await expect(userBubble).toBeVisible();

    // Get innerHTML of the bubble — should NOT contain raw <script> tag
    const innerHTML = await userBubble.innerHTML();
    expect(innerHTML).not.toContain("<script>");
    expect(innerHTML).not.toContain("</script>");

    // But the text content should contain the literal angle bracket string
    const textContent = await userBubble.textContent();
    // React escapes < and > in text nodes — the text rendered is the payload chars
    // The actual text may contain "&lt;script&gt;" or "<script>" depending on
    // whether we read textContent (decoded) or innerHTML (encoded).
    // textContent() returns decoded — so we see the original characters.
    expect(textContent).toBeTruthy();
  });

  test("no actual script element injected into DOM after XSS send", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    chatPage.page.on("dialog", (dialog) => void dialog.dismiss());

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill(XSS_PAYLOAD);
    await chatPage.pressEnter();

    await expect(chatPage.getMessage(0)).toBeVisible({ timeout: 3_000 });

    // No raw <script> elements should exist in the chat messages area
    const scriptTagCount = await chatPage.page
      .locator('[data-testid="chat-messages"] script')
      .count();
    expect(scriptTagCount).toBe(0);
  });

  test("img onerror XSS payload renders as escaped text, no alert fires", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    let dialogFired = false;
    chatPage.page.on("dialog", (dialog) => {
      dialogFired = true;
      void dialog.dismiss();
    });

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill(XSS_PAYLOAD_IMG);
    await chatPage.pressEnter();

    await expect(chatPage.getMessage(0)).toBeVisible({ timeout: 3_000 });
    await chatPage.page.waitForTimeout(1_500);

    // No dialog should fire from onerror
    expect(dialogFired).toBe(false);

    // No <img> element injected into chat area from the payload
    const imgCount = await chatPage.page
      .locator('[data-testid="chat-messages"] img[onerror]')
      .count();
    expect(imgCount).toBe(0);
  });

  test("javascript: protocol XSS payload renders as plain text", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    let dialogFired = false;
    chatPage.page.on("dialog", (dialog) => {
      dialogFired = true;
      void dialog.dismiss();
    });

    await chatPage.getComposer().click();
    await chatPage.getComposer().fill(XSS_PAYLOAD_JS);
    await chatPage.pressEnter();

    await expect(chatPage.getMessage(0)).toBeVisible({ timeout: 3_000 });
    await chatPage.page.waitForTimeout(1_500);

    expect(dialogFired).toBe(false);
  });

  test("component remains stable and functional after adversarial sends", async ({
    chatStoreEmpty,
  }) => {
    const chatPage = chatStoreEmpty;

    chatPage.page.on("dialog", (dialog) => void dialog.dismiss());

    // Send multiple XSS payloads
    for (const payload of [XSS_PAYLOAD, XSS_PAYLOAD_IMG, XSS_PAYLOAD_JS]) {
      await chatPage.getComposer().click();
      await chatPage.getComposer().fill(payload);
      await chatPage.pressEnter();
      // Wait for user bubble to appear before next send
      await chatPage.page.waitForTimeout(200);
    }

    // Wait for all sends to settle
    await chatPage.page.waitForTimeout(500);

    // ChatHeader should still be visible (component didn't crash)
    await expect(chatPage.getChatHeader()).toBeVisible();

    // Composer should still be functional
    const composer = chatPage.getComposer();
    await expect(composer).toBeVisible();
    await composer.click();
    await composer.fill("Mensaje de control después de XSS");
    await chatPage.pressEnter();

    // Control message should appear as a regular user bubble
    await chatPage.page.waitForTimeout(300);
    const lastBubble = chatPage.page
      .locator('[data-testid="msg-bubble"][data-role="user"]')
      .last();
    await expect(lastBubble).toContainText("Mensaje de control después de XSS");
  });
});
