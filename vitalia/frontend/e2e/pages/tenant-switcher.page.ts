/**
 * tenant-switcher.page.ts — Page Object Model para TenantSwitcher
 *
 * F1-S3 vitalia-fase1-tenant-switcher — T-9
 *
 * Locators: data-testid first (ARIA como fallback).
 * Sin assertions en métodos POM — solo acciones + locators.
 *
 * 03-arch.md § 7 — path preservation redirect (/{newTenantId}/..)
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

// ---------------------------------------------------------------------------
// TenantSwitcherPage — POM
// ---------------------------------------------------------------------------

export class TenantSwitcherPage {
  readonly page: Page;

  // ── Trigger ────────────────────────────────────────────────────────────────
  readonly trigger: Locator;

  // ── Dropdown content ───────────────────────────────────────────────────────
  readonly dropdown: Locator;

  // ── Header label ──────────────────────────────────────────────────────────
  readonly headerLabel: Locator;

  // ── Loading state ─────────────────────────────────────────────────────────
  readonly loadingSkeletons: Locator;

  // ── Error state ───────────────────────────────────────────────────────────
  readonly errorAlert: Locator;
  readonly retryButton: Locator;

  // ── Footer actions ────────────────────────────────────────────────────────
  readonly addClinicButton: Locator;
  readonly manageAccountLink: Locator;

  // ── Modals ────────────────────────────────────────────────────────────────
  readonly addClinicModal: Locator;
  readonly addClinicModalClose: Locator;

  constructor(page: Page) {
    this.page = page;

    this.trigger = page.getByTestId("tenant-switcher-trigger");
    this.dropdown = page.getByTestId("tenant-switcher-dropdown");
    this.headerLabel = page.getByText("MIS CLÍNICAS");

    // Loading skeletons (sr-only text)
    this.loadingSkeletons = page.getByText("Cargando clínicas…");

    // Error state
    this.errorAlert = page.getByText("No pudimos cargar tus clínicas");
    this.retryButton = page.getByRole("button", { name: "Reintentar" });

    // Footer actions
    this.addClinicButton = page
      .getByRole("button", { name: "Agregar clínica" })
      .first();
    this.manageAccountLink = page.getByRole("link", {
      name: "Administrar cuenta",
    });

    // Add clinic placeholder modal
    this.addClinicModal = page.getByRole("dialog");
    this.addClinicModalClose = page.getByTestId("add-clinic-modal-close");
  }

  /**
   * Open the dropdown by clicking the trigger.
   * Waits for dropdown content to be visible.
   */
  async openDropdown(): Promise<void> {
    await this.trigger.click();
    await this.dropdown.waitFor({ state: "visible" });
  }

  /**
   * Close the dropdown by pressing Escape.
   */
  async closeDropdown(): Promise<void> {
    await this.page.keyboard.press("Escape");
  }

  /**
   * Get a tenant option locator by tenant ID.
   */
  tenantOption(tenantId: string): Locator {
    return this.page.getByTestId(`tenant-option-${tenantId}`);
  }

  /**
   * Select a tenant by ID (clicks the option row).
   * Note: causes hard navigation (window.location.href), so navigation is expected.
   */
  async selectTenant(tenantId: string): Promise<void> {
    await this.tenantOption(tenantId).click();
  }

  /**
   * Open the "Agregar clínica" placeholder modal.
   */
  async openAddClinicModal(): Promise<void> {
    await this.addClinicButton.click();
    await this.addClinicModal.waitFor({ state: "visible" });
  }

  /**
   * Close the "Agregar clínica" modal via "Entendido" button.
   */
  async closeAddClinicModal(): Promise<void> {
    await this.addClinicModalClose.click();
    await this.addClinicModal.waitFor({ state: "hidden" });
  }

  /**
   * Check if a tenant option is marked as active (data-active="true").
   */
  async isTenantActive(tenantId: string): Promise<boolean> {
    const option = this.tenantOption(tenantId);
    const active = await option.getAttribute("data-active");
    return active === "true";
  }

  /**
   * Get the trigger's aria-label attribute.
   */
  async getTriggerAriaLabel(): Promise<string | null> {
    return this.trigger.getAttribute("aria-label");
  }

  /**
   * Get the trigger's title attribute (tooltip).
   */
  async getTriggerTitle(): Promise<string | null> {
    return this.trigger.getAttribute("title");
  }
}
