// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * NuevoServicioPage.ts — POM for the BibliotecaPicker ("Nuevo servicio") flow.
 *
 * The BibliotecaPicker opens as a modal/panel from the Catálogo directory.
 * Two modes: "Buscar en la biblioteca" (library) vs "Personalizado" (custom form).
 *
 * RN-16: Crear = entrar a editar (redirect to workspace immediately after creation).
 *
 * downstream-regression-na: brand-local vitalia E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

export type NuevoServicioMode = "biblioteca" | "personalizado";

export class NuevoServicioPage {
  readonly page: Page;

  /** BibliotecaPicker container (modal or panel) */
  readonly pickerContainer: Locator;

  /** "Buscar en la biblioteca" mode button */
  readonly bibliotecaModeBtn: Locator;

  /** "Personalizado" mode button */
  readonly personalizadoModeBtn: Locator;

  /** Clinic type selector (Radix Select) — library mode */
  readonly clinicTypeSelect: Locator;

  /** Search input — library mode */
  readonly searchInput: Locator;

  /** Template list container */
  readonly templateList: Locator;

  /** Custom form — name input */
  readonly customNameInput: Locator;

  /** Custom form — submit button */
  readonly createAndConfigureBtn: Locator;

  /** Validation error container */
  readonly validationErrors: Locator;

  constructor(page: Page) {
    this.page = page;
    // The picker is rendered inline (not a dialog) in the catalog layout
    this.pickerContainer = page.getByTestId("biblioteca-picker");
    this.bibliotecaModeBtn = page.getByRole("button", { name: /Buscar en la biblioteca/i });
    this.personalizadoModeBtn = page.getByRole("button", { name: /Personalizado/i });
    this.clinicTypeSelect = page.locator('[aria-label="Especialidad de tu clínica"]');
    this.searchInput = page.getByLabel("Buscar servicio");
    this.templateList = page.getByTestId("template-list");
    this.customNameInput = page.getByLabel("Nombre del servicio");
    this.createAndConfigureBtn = page.getByRole("button", { name: /Crear y configurar/i });
    this.validationErrors = page.locator('[role="alert"], .text-destructive');
  }

  // ── Mode switching ───────────────────────────────────────────────────────────

  async switchToMode(mode: NuevoServicioMode): Promise<void> {
    if (mode === "biblioteca") {
      await this.bibliotecaModeBtn.click();
    } else {
      await this.personalizadoModeBtn.click();
    }
    await this.page.waitForTimeout(200);
  }

  // ── Library mode ─────────────────────────────────────────────────────────────

  async searchLibrary(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(400); // debounce
    await this.page.waitForLoadState("networkidle", { timeout: 10_000 });
  }

  async getTemplateCount(): Promise<number> {
    return await this.templateList.locator('[data-testid^="template-item-"]').count();
  }

  async clickUseTemplate(templateName: string): Promise<void> {
    const templateItem = this.page.locator('[data-testid^="template-item-"]', {
      hasText: templateName,
    });
    await templateItem.getByRole("button", { name: /Usar plantilla/i }).click();
    // RN-16: redirects to workspace
    await this.page.waitForLoadState("networkidle", { timeout: 20_000 });
  }

  // ── Custom mode ──────────────────────────────────────────────────────────────

  async fillCustomName(name: string): Promise<void> {
    await this.customNameInput.fill(name);
  }

  async fillCustomPrice(price: string): Promise<void> {
    const priceInput = this.page.getByLabel(/Precio/i).first();
    await priceInput.fill(price);
  }

  async submitCustomForm(): Promise<void> {
    await this.createAndConfigureBtn.click();
    // RN-16: on success redirects to workspace
  }

  async waitForWorkspaceRedirect(): Promise<void> {
    // After creation, URL changes to /{tenantId}/lisa/servicios/{offerId}/resumen
    await this.page.waitForURL(/\/lisa\/servicios\/[^/]+\/resumen/, { timeout: 15_000 });
    await this.page.waitForLoadState("networkidle", { timeout: 15_000 });
  }

  // ── Validation ───────────────────────────────────────────────────────────────

  async getValidationErrorTexts(): Promise<string[]> {
    const errors = await this.validationErrors.all();
    return Promise.all(errors.map((e) => e.innerText()));
  }

  async hasValidationError(text: string): Promise<boolean> {
    try {
      await this.page.getByText(text).waitFor({ state: "visible", timeout: 3_000 });
      return true;
    } catch {
      return false;
    }
  }

  // ── State ────────────────────────────────────────────────────────────────────

  async isPickerVisible(): Promise<boolean> {
    try {
      await this.pickerContainer.waitFor({ state: "visible", timeout: 5_000 });
      return true;
    } catch {
      return false;
    }
  }

  async isSearchDisabled(): Promise<boolean> {
    return await this.searchInput.isDisabled();
  }
}
