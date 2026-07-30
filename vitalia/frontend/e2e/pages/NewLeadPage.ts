// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * NewLeadPage.ts — POM for /nuevo (create lead route-hoja, NOT a modal).
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 * Covers:
 *   SC-nuevo   submit → redirect /embudo?highlight={id} → card resaltada
 *   F-7        ruta-hoja /nuevo + EntitySubNavBar + RHF/Zod form
 *   RN-19      slug /nuevo precede [leadId] en route tree
 *
 * Route: /{tenantId}/adrian/embudo/nuevo
 *
 * downstream-regression-na: brand-local vitalia E2E POM
 * spec_anchor: 04-validators.yaml § poms_required
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

export class NewLeadPage {
  readonly page: Page;
  readonly tenantId: string;

  // ── EntitySubNavBar (workspace mode) ──────────────────────────────────────
  readonly entitySubNavBar: Locator;
  readonly backToEmbudoLink: Locator;
  readonly pageTitleBreadcrumb: Locator;

  // ── Form (RHF+Zod) ─────────────────────────────────────────────────────────
  readonly form: Locator;
  readonly nameInput: Locator;
  readonly channelSelect: Locator;
  readonly phoneInput: Locator;
  readonly emailInput: Locator;
  readonly stageSelect: Locator;
  readonly serviceInput: Locator;
  readonly notasTextarea: Locator;

  // ── Buttons ─────────────────────────────────────────────────────────────────
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  // ── Validation errors ───────────────────────────────────────────────────────
  readonly nameError: Locator;
  readonly channelError: Locator;
  readonly contactError: Locator;

  // ── States ─────────────────────────────────────────────────────────────────
  readonly successToast: Locator;
  readonly errorToast: Locator;
  readonly loadingSpinner: Locator;

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    // EntitySubNavBar
    this.entitySubNavBar = page
      .locator('[data-testid="entity-sub-nav-bar"]')
      .first();
    this.backToEmbudoLink = page
      .locator('[aria-label*="Embudo"], [data-testid="back-to-embudo"]')
      .first();
    this.pageTitleBreadcrumb = page
      .locator(
        '[data-testid="nuevo-lead-title"], h1:has-text("Nuevo lead"), h2:has-text("Nuevo lead")',
      )
      .first();

    // Form
    this.form = page
      .locator('[data-testid="new-lead-form"], form[aria-label*="lead"]')
      .first();
    this.nameInput = page
      .locator(
        '[data-testid="lead-name-input"], input[name="name"], input[aria-label*="nombre"]',
      )
      .first();
    this.channelSelect = page
      .locator(
        '[data-testid="lead-channel-select"], [aria-label*="canal"]',
      )
      .first();
    this.phoneInput = page
      .locator(
        '[data-testid="lead-phone-input"], input[name="phone"], input[aria-label*="teléfono"]',
      )
      .first();
    this.emailInput = page
      .locator(
        '[data-testid="lead-email-input"], input[name="email"], input[type="email"]',
      )
      .first();
    this.stageSelect = page
      .locator(
        '[data-testid="lead-stage-select"], [aria-label*="etapa"]',
      )
      .first();
    this.serviceInput = page
      .locator(
        '[data-testid="lead-service-input"], input[name="serviceInterest"]',
      )
      .first();
    this.notasTextarea = page
      .locator(
        '[data-testid="lead-notes-input"], textarea[name="notes"]',
      )
      .first();

    // Buttons
    this.submitButton = page
      .locator(
        '[data-testid="submit-new-lead"], button[type="submit"]:has-text("Crear")',
      )
      .first();
    this.cancelButton = page
      .locator(
        '[data-testid="cancel-new-lead"], button:has-text("Cancelar")',
      )
      .first();

    // Validation errors
    this.nameError = page
      .locator('[data-testid="name-error"], [aria-label*="nombre error"]')
      .first();
    this.channelError = page
      .locator('[data-testid="channel-error"]')
      .first();
    this.contactError = page
      .locator('[data-testid="contact-error"], [role="alert"]')
      .filter({ hasText: /teléfono|correo|contacto/i })
      .first();

    // States
    this.successToast = page
      .locator('[role="status"]')
      .filter({ hasText: /creado|listo/i })
      .first();
    this.errorToast = page
      .locator('[role="alert"]')
      .filter({ hasText: /error|falló/i })
      .first();
    this.loadingSpinner = page
      .locator(
        '[data-testid="submit-loading"], [aria-label*="Creando"]',
      )
      .first();
  }

  // ── Navigation ──────────────────────────────────────────────────────────────

  async goto(): Promise<void> {
    await this.page.goto(`/${this.tenantId}/adrian/embudo/nuevo`);
    await this.page.waitForLoadState("networkidle");
  }

  // ── Form interactions ───────────────────────────────────────────────────────

  async fillName(name: string): Promise<void> {
    await this.nameInput.fill(name);
  }

  async selectChannel(channel: string): Promise<void> {
    // Shadcn Select — click trigger then item
    await this.channelSelect.click();
    await this.page
      .locator(`[role="option"]:has-text("${channel}"), [data-value="${channel}"]`)
      .first()
      .click();
  }

  async fillPhone(phone: string): Promise<void> {
    await this.phoneInput.fill(phone);
  }

  async fillEmail(email: string): Promise<void> {
    await this.emailInput.fill(email);
  }

  async fillService(service: string): Promise<void> {
    await this.serviceInput.fill(service);
  }

  async fillNotas(notes: string): Promise<void> {
    await this.notasTextarea.fill(notes);
  }

  async fillMinimalForm(opts: {
    name: string;
    channel: string;
    phone?: string;
    email?: string;
  }): Promise<void> {
    await this.fillName(opts.name);
    await this.selectChannel(opts.channel);
    if (opts.phone) await this.fillPhone(opts.phone);
    if (opts.email) await this.fillEmail(opts.email);
  }

  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  async cancel(): Promise<void> {
    await this.cancelButton.click();
  }

  // ── Wait + assertions ───────────────────────────────────────────────────────

  async waitForFormLoaded(): Promise<void> {
    await this.form.waitFor({ state: "visible", timeout: 12_000 });
  }

  async expectFormVisible(): Promise<void> {
    await expect(this.form).toBeVisible();
    await expect(this.nameInput).toBeVisible();
  }

  async expectEntitySubNavBarVisible(): Promise<void> {
    await expect(this.entitySubNavBar).toBeVisible();
  }

  async expectRedirectToEmbudoWithHighlight(newLeadId?: string): Promise<void> {
    // After submit: redirect to /embudo?highlight={id}
    await expect(this.page).toHaveURL(
      new RegExp(`/adrian/embudo(\\?|.*highlight=)`),
      { timeout: 10_000 },
    );
    if (newLeadId) {
      expect(this.page.url()).toContain(`highlight=${newLeadId}`);
    }
  }

  async expectNameRequiredError(): Promise<void> {
    await expect(this.nameError).toBeVisible({ timeout: 4_000 });
  }

  async expectChannelRequiredError(): Promise<void> {
    await expect(this.channelError).toBeVisible({ timeout: 4_000 });
  }

  async expectNoPhiInUrl(): Promise<void> {
    const url = this.page.url();
    expect(url).not.toMatch(/nombre|paciente|email|dni/i);
  }
}
