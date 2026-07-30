/**
 * wizard-onboarding.page.ts — POM for /onboarding/wizard
 *
 * Per playwright-expert POM patterns:
 *   - Encapsulate all locator logic
 *   - Provide action methods for user flows
 *   - NO test assertions in POM (assertions live in spec)
 *
 * Route: /onboarding/wizard (vitalia frontend port 3002)
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

export class WizardOnboardingPage {
  readonly page: Page;

  // ─── Page-level locators ──────────────────────────────────────────────────
  readonly wizardLayout: Locator;
  readonly topBar: Locator;
  readonly topBarTitle: Locator;
  readonly closeButton: Locator;
  readonly chatSection: Locator;
  readonly previewSection: Locator;

  // ─── Slot tracker ──────────────────────────────────────────────────────────
  readonly slotTracker: Locator;
  readonly slotPills: Locator;

  // ─── Chat thread ──────────────────────────────────────────────────────────
  readonly chatThread: Locator;
  readonly messageInput: Locator;
  readonly sendButton: Locator;
  readonly typingIndicator: Locator;

  // ─── Live preview panel ───────────────────────────────────────────────────
  readonly whatsAppPreview: Locator;
  readonly landingSnippetPreview: Locator;

  // ─── Modals ───────────────────────────────────────────────────────────────
  readonly closeModal: Locator;
  readonly closeModalCancelButton: Locator;
  readonly closeModalConfirmButton: Locator;

  // ─── Completion ───────────────────────────────────────────────────────────
  readonly completionOverlay: Locator;
  readonly completionCta: Locator;

  constructor(page: Page) {
    this.page = page;

    // Layout
    this.wizardLayout = page.getByRole("application");
    this.topBar = page.getByRole("banner");
    this.topBarTitle = page.getByText("Configuración de tu clínica");
    this.closeButton = page.getByRole("button", { name: /cerrar asistente/i });
    this.chatSection = page.getByRole("region", { name: /conversación/i });
    this.previewSection = page.getByRole("region", { name: /vista previa/i });

    // Slot tracker
    this.slotTracker = page.getByRole("navigation");
    this.slotPills = page.locator("[data-slot-pill]");

    // Chat
    this.chatThread = page.getByRole("log");
    this.messageInput = page.getByRole("textbox", {
      name: /escribe tu mensaje/i,
    });
    this.sendButton = page.getByRole("button", { name: /enviar/i });
    this.typingIndicator = page.getByLabel(/Vitalia está escribiendo/i);

    // Live preview
    this.whatsAppPreview = page.getByRole("region", {
      name: /cómo escribe adrián/i,
    });
    this.landingSnippetPreview = page.getByRole("region", {
      name: /tu página web/i,
    });

    // Close modal
    this.closeModal = page.getByRole("alertdialog");
    this.closeModalCancelButton = page.getByRole("button", {
      name: /continuar configurando/i,
    });
    this.closeModalConfirmButton = page.getByRole("button", {
      name: /salir de todos modos/i,
    });

    // Completion
    this.completionOverlay = page.getByRole("main");
    this.completionCta = page.getByRole("button", { name: /ir al panel/i });
  }

  // ─── Navigation ───────────────────────────────────────────────────────────

  async goto() {
    await this.page.goto("/onboarding/wizard");
  }

  // ─── Chat actions ─────────────────────────────────────────────────────────

  async sendMessage(text: string) {
    await this.messageInput.fill(text);
    await this.sendButton.click();
  }

  async sendUrl(url: string) {
    await this.sendMessage(url);
  }

  async waitForAssistantResponse(timeout = 15_000) {
    // Wait for typing indicator to appear then disappear
    await this.typingIndicator
      .waitFor({ state: "visible", timeout })
      .catch(() => {
        // Typing indicator may be very brief; that's OK
      });
    await this.typingIndicator
      .waitFor({ state: "hidden", timeout })
      .catch(() => {
        // Already gone or never appeared
      });
  }

  async waitForFirstMessage(timeout = 10_000) {
    await this.page.waitForSelector('[role="log"] > *', { timeout });
  }

  // ─── Slot actions ─────────────────────────────────────────────────────────

  async confirmSlot(value: string) {
    const confirmInput = this.page.getByRole("textbox", {
      name: /confirmar valor/i,
    });
    await confirmInput.fill(value);
    const saveBtn = this.page.getByRole("button", { name: /guardar/i }).first();
    await saveBtn.click();
  }

  // ─── Close modal actions ──────────────────────────────────────────────────

  async openCloseModal() {
    await this.closeButton.click();
    await this.closeModal.waitFor({ state: "visible" });
  }

  async cancelClose() {
    await this.closeModalCancelButton.click();
    await this.closeModal.waitFor({ state: "hidden" });
  }

  async confirmClose() {
    await this.closeModalConfirmButton.click();
  }

  // ─── Assertions (helpers for common checks) ───────────────────────────────

  async isReady(timeout = 15_000) {
    await this.topBarTitle.waitFor({ state: "visible", timeout });
  }
}
