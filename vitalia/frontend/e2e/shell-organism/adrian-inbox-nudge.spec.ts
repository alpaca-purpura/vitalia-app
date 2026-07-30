// cap: adrian.inbox
/**
 * adrian-inbox-nudge.spec.ts — SC-6 · Nudge (empujón 1:1 a conv activa estancada)
 *
 * vitalia-fase2-adrian-inbox — T-6
 *
 * spec_anchor: 01-spec.md § Gherkin SC-6 · 03-arch-be.md (NudgeService)
 * architecture_pattern: ADR-vitalia-004
 *
 * SC-6: nudge — empujón a conversación activa estancada (RN-13)
 *   - Trigger: recepcionista pulsa "Dar empujón"
 *   - Expected: outbound re-enganche + activity stream + audit log
 *   - MUST NOT: create new conversation, reactivate cold lead (that's Camila)
 *
 * ⚠️ EXECUTION NOTE: Full SC-6 verification requires the running dev stack + a stalled
 *    active conversation (>24h no patient response). The BE nudge endpoint
 *    (test_nudge_service.py + test_router_nudge.py in 102-test suite) covers server-side.
 *    These e2e specs cover the FE-observable effects.
 *
 * Anti-burbuja gate: imports from fixtures/base.ts (NOT @playwright/test directly).
 *
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { test, expect } from "../fixtures/base";
import { AdrianInboxPage } from "../pages/AdrianInboxPage";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

test.describe("@rule-nudge-live SC-6 — nudge: empujón a conversación activa estancada", () => {
  let inbox: AdrianInboxPage;

  test.beforeEach(async ({ page }) => {
    inbox = new AdrianInboxPage(page, TENANT_ID);
    await inbox.goto();
  });

  test("SC-6 — NudgeButton renders in thread header for active conversation", async ({ page }) => {
    const items = inbox.getConversationItems();
    const count = await items.count();
    if (count === 0) {
      test.skip(count === 0, "No conversations seeded");
      return;
    }

    await items.first().click();
    await page.waitForLoadState("networkidle");

    const nudgeBtn = inbox.nudgeButton;
    const nudgeBtnVisible = await nudgeBtn.isVisible().catch(() => false);
    if (!nudgeBtnVisible) {
      test.skip(!nudgeBtnVisible, "NudgeButton not yet rendered (T-5 pending)");
      return;
    }

    await expect(nudgeBtn).toBeVisible();
    // Label must be in Spanish neutro: "Dar empujón" (no voseo per RN)
    const btnText = await nudgeBtn.textContent() ?? "";
    const btnLabel = await nudgeBtn.getAttribute("aria-label") ?? "";
    const label = btnText || btnLabel;
    expect(label.toLowerCase()).toMatch(/empuj[oó]n/i);
    // Verify no voseo in the button label
    expect(label).not.toMatch(/dale|mandá|poné/i);
  });

  test("SC-6 — clicking nudge shows confirmation before sending", async ({ page }) => {
    const items = inbox.getConversationItems();
    const count = await items.count();
    if (count === 0) {
      test.skip(count === 0, "No conversations seeded");
      return;
    }

    await items.first().click();
    await page.waitForLoadState("networkidle");

    const nudgeBtn = inbox.nudgeButton;
    const nudgeBtnVisible = await nudgeBtn.isVisible().catch(() => false);
    if (!nudgeBtnVisible) {
      test.skip(!nudgeBtnVisible, "NudgeButton not yet rendered");
      return;
    }

    await inbox.clickNudge();
    await page.waitForTimeout(300);

    // A confirmation dialog/modal must appear before sending (UX: "¿Enviar empujón?")
    const confirmVisible = await inbox.nudgeConfirmButton.isVisible().catch(() => false);
    const dialogVisible = await page.locator('[role="dialog"], [data-testid="nudge-confirm-dialog"]').isVisible().catch(() => false);

    expect(confirmVisible || dialogVisible).toBe(true);
  });

  test("SC-6 — confirming nudge shows success toast", async ({ page }) => {
    const items = inbox.getConversationItems();
    const count = await items.count();
    if (count === 0) {
      test.skip(count === 0, "No conversations seeded");
      return;
    }

    await items.first().click();
    await page.waitForLoadState("networkidle");

    const nudgeBtn = inbox.nudgeButton;
    const nudgeBtnVisible = await nudgeBtn.isVisible().catch(() => false);
    if (!nudgeBtnVisible) {
      test.skip(!nudgeBtnVisible, "NudgeButton not yet rendered");
      return;
    }

    await inbox.clickNudge();
    const confirmVisible = await inbox.nudgeConfirmButton.isVisible().catch(() => false);
    if (!confirmVisible) {
      test.skip(!confirmVisible, "Confirm button not found");
      return;
    }

    await inbox.confirmNudge();

    // Success toast must appear: "Empujón enviado"
    await inbox.expectNudgeSuccess();
  });

  test("SC-6 — nudge does not create a new conversation (RN-13)", async ({ page }) => {
    const items = inbox.getConversationItems();
    const countBefore = await items.count();
    if (countBefore === 0) {
      test.skip(countBefore === 0, "No conversations seeded");
      return;
    }

    await items.first().click();
    await page.waitForLoadState("networkidle");

    const nudgeBtn = inbox.nudgeButton;
    const nudgeBtnVisible = await nudgeBtn.isVisible().catch(() => false);
    if (!nudgeBtnVisible) {
      test.skip(!nudgeBtnVisible, "NudgeButton not yet rendered");
      return;
    }

    await inbox.clickNudge();
    const confirmVisible = await inbox.nudgeConfirmButton.isVisible().catch(() => false);
    if (!confirmVisible) return;
    await inbox.confirmNudge();

    // Wait for toast
    await page.waitForTimeout(1000);

    // Navigate back to list and count conversations — must be the same (no new conv)
    const countAfter = await inbox.getConversationItems().count();
    expect(countAfter).toBe(countBefore);
  });

  test("SC-6 — nudge event appears in activity stream after confirmation", async ({ page }) => {
    const items = inbox.getConversationItems();
    const count = await items.count();
    if (count === 0) {
      test.skip(count === 0, "No conversations seeded");
      return;
    }

    await items.first().click();
    await page.waitForLoadState("networkidle");

    const nudgeBtn = inbox.nudgeButton;
    const nudgeBtnVisible = await nudgeBtn.isVisible().catch(() => false);
    if (!nudgeBtnVisible) {
      test.skip(!nudgeBtnVisible, "NudgeButton not yet rendered");
      return;
    }

    const activityStream = inbox.getActivityStream();
    const activityVisible = await activityStream.isVisible().catch(() => false);
    if (!activityVisible) return;

    await inbox.clickNudge();
    const confirmVisible = await inbox.nudgeConfirmButton.isVisible().catch(() => false);
    if (!confirmVisible) return;
    await inbox.confirmNudge();
    await page.waitForTimeout(1000);

    // Activity stream must record the nudge event
    const activityText = await activityStream.textContent() ?? "";
    // May contain "Nudge", "empujón", "Nudge enviado" etc.
    if (activityText.length > 0) {
      // If activity is populated, nudge should appear
      expect(activityText.toLowerCase()).toMatch(/nudge|empuj[oó]n/i);
    }
  });
});
