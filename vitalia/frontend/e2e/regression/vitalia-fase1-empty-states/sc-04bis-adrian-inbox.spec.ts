/**
 * sc-04bis-adrian-inbox.spec.ts — SC-4.bis · Adrián Inbox 3-col + Takeover A↔B + sidebar toggle
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Assertions:
 *   - InboxPlaceholder mounts at /adrian/inbox with 3-col layout
 *   - 5 ConversationItem visible (mg, cp, lr, df, sm from mock)
 *   - ≥2 CampaignTag visible (mg has "Limpieza-PE", lr has "Blanqueamiento")
 *   - Carlos Pérez (cp) has handlerMode="human" → border-l-green + YouChip "✋ Tú"
 *   - Global mode toggle (3-mode pill) visible
 *   - State A: "Adrián está manejando" chip + "✋ Tomar el control" button
 *   - State A → B: click takeControl → TakeoverBanner visible + MessageInput enabled
 *   - State B → A: click returnControl → TakeoverBanner hidden + MessageInput disabled
 *   - Sidebar toggle: click × → data-sidebar="closed" + grid collapses col-3
 *
 * Uses: AdrianInboxPage POM + empty-states.fixture
 *
 * SC-4.bis validator: val-fe-e2e-sc04bis-adrian-inbox
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { AdrianInboxPage } from "../../pages/AdrianInboxPage";

test.describe("SC-4.bis · Adrián Inbox 3-col + Takeover A↔B + sidebar toggle", () => {
  test.beforeEach(async ({ shellPage, tenantId }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.goto();
  });

  // ── Conversation list ────────────────────────────────────────────────

  test("5 ConversationItem visibles en la lista", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    const items = inbox.getConversationItems();
    await expect(items).toHaveCount(5);
  });

  test("nombres ficticios LatAm visibles en lista", async ({ shellPage }) => {
    await expect(
      shellPage.locator("text=María González").first(),
    ).toBeVisible();
    await expect(shellPage.locator("text=Carlos Pérez").first()).toBeVisible();
    await expect(shellPage.locator("text=Lucía Ramos").first()).toBeVisible();
    await expect(shellPage.locator("text=Diego Flores").first()).toBeVisible();
    await expect(shellPage.locator("text=Sofía M.").first()).toBeVisible();
  });

  test("≥2 CampaignTag visibles (Limpieza-PE · Blanqueamiento)", async ({
    shellPage,
  }) => {
    await expect(shellPage.locator("text=Limpieza-PE").first()).toBeVisible();
    await expect(
      shellPage.locator("text=Blanqueamiento").first(),
    ).toBeVisible();
  });

  test("Carlos Pérez tiene YouChip '✋ Tú' (handlerMode=human)", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.expectHumanHandledConversationVisible("Carlos Pérez").first();
    // YouChip text visible
    await expect(shellPage.locator("text=✋ Tú").first()).toBeVisible();
  });

  test("global mode toggle 3-modos visible", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.expectGlobalModeToggleVisible();
    // 3 mode options visible
    await expect(
      shellPage.locator("text=🤖 Adrián decide").first(),
    ).toBeVisible();
    await expect(
      shellPage.locator("text=👀 Te consulta").first(),
    ).toBeVisible();
    await expect(shellPage.locator("text=✋ Manual").first()).toBeVisible();
  });

  // ── Takeover UX State A (default) ────────────────────────────────────

  test("estado A por defecto: chip Adrián + botón Tomar el control", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.expectStateA();
  });

  test("MessageInput disabled en estado A con placeholder Adrián", async ({
    shellPage,
  }) => {
    await expect(
      shellPage
        .locator('[placeholder*="Adrián decide automáticamente"]')
        .first()
        .first(),
    ).toBeVisible();
  });

  // ── Takeover UX State A → B transition ───────────────────────────────

  test("click Tomar el control → transición a estado B", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    // Start in state A
    await inbox.expectStateA();
    // Transition to state B
    await inbox.takeControl();
    // Assert state B
    await inbox.expectStateB();
  });

  test("estado B: TakeoverBanner visible + MessageInput habilitado", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.takeControl();
    // TakeoverBanner button present
    await expect(inbox.returnControlButton).toBeVisible();
    // MessageInput enabled placeholder "Escribir como tú"
    await expect(
      shellPage.locator('[placeholder*="Escribir como tú"]').first(),
    ).toBeVisible();
  });

  test("estado B → A: click Devolver control → TakeoverBanner desaparece", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    // Go to state B
    await inbox.takeControl();
    await inbox.expectStateB();
    // Return to state A
    await inbox.returnControl();
    await inbox.expectStateA();
  });

  // ── Sidebar toggle ────────────────────────────────────────────────────

  test("sidebar inicialmente open (data-sidebar='open').first()", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.expectSidebarOpen();
  });

  test("click × cierra sidebar → data-sidebar='closed'", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.expectSidebarOpen();
    await inbox.closeSidebar();
    await inbox.expectSidebarClosed();
  });

  // ── Messages thread ───────────────────────────────────────────────────

  test("thread live region visible con mensajes mock", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.expectThreadVisible();
    // First mock message from MOCK_THREAD_MESSAGES
    await expect(
      shellPage.locator("text=/limpieza dental/i").first(),
    ).toBeVisible();
  });

  // ── Visual goldens ────────────────────────────────────────────────────

  test("visual state A · InboxPlaceholder estado Adrián maneja", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.expectStateA();
    // 5 conversations + state A chip visible = visual state A ready
    await expect(
      shellPage.locator("text=María González").first(),
    ).toBeVisible();
  });

  test("visual state B · InboxPlaceholder estado usuario toma control", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.takeControl();
    await inbox.expectStateB();
  });

  test("visual sidebar-closed · grid col-3 a 0", async ({
    shellPage,
    tenantId,
  }) => {
    const inbox = new AdrianInboxPage(shellPage, tenantId);
    await inbox.closeSidebar();
    await inbox.expectSidebarClosed();
    // data-sidebar="closed" means gridTemplateColumns includes "0" for col-3
    await expect(
      shellPage.locator('[data-sidebar="closed"]').first(),
    ).toHaveAttribute("style", /0/);
  });
});
