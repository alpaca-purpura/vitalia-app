/**
 * crear-cita-button-page.pom.ts — CrearCitaButtonPage POM
 *
 * Page Object Model for the "+ Crear cita" dropdown button.
 * Covers the 3 creation modes: walk-in, teléfono, desde-paciente-existente.
 *
 * Methods per 04-validators.yaml test_construction_plan step 8:
 *   openDropdown, selectOption, fillPatientNewData,
 *   searchPatient (autocomplete), submit
 *
 * The button appears in:
 *   - Agenda toolbar header
 *   - Mobile FAB (Floating Action Button) on day view
 *   - Empty state CTA (SC-8)
 *
 * No assertions in POM methods — only actions + locators.
 *
 * downstream-regression-na: brand-local vitalia E2E POM F2-S1
 *
 * @see 04-validators.yaml § poms_required[3]: CrearCitaButtonPage
 * @see SC-8 empty state CTA
 * @see 03-arch.md § 5 crear-cita flow
 */

import type { Page, Locator } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type CrearCitaOption = "walk-in" | "telefono" | "existente";

export interface NewPatientData {
  /** Full name (will be masked server-side post-creation) */
  name: string;
  /** Phone number */
  phone: string;
  /** Service type */
  service: string;
  /** Appointment date (YYYY-MM-DD) */
  date?: string;
  /** Appointment time (HH:MM) */
  time?: string;
  /** Notes */
  notes?: string;
}

export interface ExistingPatientSearch {
  /** Search query (name fragment, phone, or masked DNI) */
  query: string;
  /** Expected result item to click (by visible text) */
  selectResultText?: string;
}

// ---------------------------------------------------------------------------
// CrearCitaButtonPage POM
// ---------------------------------------------------------------------------

export class CrearCitaButtonPage {
  readonly page: Page;

  // ── Button / trigger locators ─────────────────────────────────────────────

  /** "+ Crear cita" toolbar button */
  readonly toolbarButton: Locator;
  /** Mobile FAB button */
  readonly fabButton: Locator;
  /** Empty state CTA button */
  readonly emptyStateCta: Locator;
  /** Dropdown menu */
  readonly dropdown: Locator;

  // ── Dropdown options ──────────────────────────────────────────────────────

  /** Walk-in option */
  readonly walkInOption: Locator;
  /** Teléfono option */
  readonly telefonoOption: Locator;
  /** Desde paciente existente option */
  readonly existenteOption: Locator;

  // ── Form locators (new patient / appointment) ─────────────────────────────

  /** Create appointment form/sheet */
  readonly createForm: Locator;
  /** Patient name input (new patient) */
  readonly patientNameInput: Locator;
  /** Patient phone input */
  readonly patientPhoneInput: Locator;
  /** Service select */
  readonly serviceSelect: Locator;
  /** Date picker */
  readonly dateInput: Locator;
  /** Time picker */
  readonly timeInput: Locator;
  /** Notes textarea */
  readonly notesInput: Locator;
  /** Patient search input (for existing patient lookup) */
  readonly patientSearchInput: Locator;
  /** Autocomplete results list */
  readonly searchResults: Locator;
  /** Submit button */
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;

    this.toolbarButton = page.locator(
      '[data-testid="agenda-crear-cita-btn"]',
    );
    this.fabButton = page.locator('[data-testid="agenda-crear-cita-fab"]');
    this.emptyStateCta = page.locator(
      '[data-testid="empty-state-crear-cita-cta"]',
    );
    this.dropdown = page.locator('[data-testid="crear-cita-dropdown"]');

    this.walkInOption = page.locator(
      '[data-testid="crear-cita-option-walk-in"]',
    );
    this.telefonoOption = page.locator(
      '[data-testid="crear-cita-option-telefono"]',
    );
    this.existenteOption = page.locator(
      '[data-testid="crear-cita-option-existente"]',
    );

    this.createForm = page.locator('[data-testid="crear-cita-form"]');
    this.patientNameInput = page.locator(
      '[data-testid="crear-cita-patient-name"]',
    );
    this.patientPhoneInput = page.locator(
      '[data-testid="crear-cita-patient-phone"]',
    );
    this.serviceSelect = page.locator('[data-testid="crear-cita-service"]');
    this.dateInput = page.locator('[data-testid="crear-cita-date"]');
    this.timeInput = page.locator('[data-testid="crear-cita-time"]');
    this.notesInput = page.locator('[data-testid="crear-cita-notes"]');
    this.patientSearchInput = page.locator(
      '[data-testid="crear-cita-patient-search"]',
    );
    this.searchResults = page.locator(
      '[data-testid="crear-cita-search-results"]',
    );
    this.submitButton = page.locator('[data-testid="crear-cita-submit-btn"]');
  }

  // ── Dropdown ──────────────────────────────────────────────────────────────

  /**
   * Open the "+ Crear cita" dropdown from the toolbar.
   * Waits for the dropdown to be visible.
   */
  async openDropdown(): Promise<void> {
    await this.toolbarButton.click();
    await this.dropdown.waitFor({ state: "visible", timeout: 3_000 });
  }

  /**
   * Open the dropdown from the mobile FAB.
   */
  async openDropdownFromFab(): Promise<void> {
    await this.fabButton.click();
    await this.dropdown.waitFor({ state: "visible", timeout: 3_000 });
  }

  /**
   * Click one of the three creation options.
   * Opens the create appointment form/sheet.
   */
  async clickOption(option: CrearCitaOption): Promise<void> {
    switch (option) {
      case "walk-in":
        await this.walkInOption.click();
        break;
      case "telefono":
        await this.telefonoOption.click();
        break;
      case "existente":
        await this.existenteOption.click();
        break;
    }
    await this.createForm.waitFor({ state: "visible", timeout: 3_000 });
  }

  // ── Walk-in / teléfono form ───────────────────────────────────────────────

  /**
   * Fill form for a new patient (walk-in or teléfono).
   */
  async fillPatientNewData(data: NewPatientData): Promise<void> {
    await this.patientNameInput.fill(data.name);
    await this.patientPhoneInput.fill(data.phone);
    await this.serviceSelect.selectOption(data.service);
    if (data.date) {
      await this.dateInput.fill(data.date);
    }
    if (data.time) {
      await this.timeInput.fill(data.time);
    }
    if (data.notes) {
      await this.notesInput.fill(data.notes);
    }
  }

  // ── Existing patient lookup ───────────────────────────────────────────────

  /**
   * Search for an existing patient using autocomplete.
   * Waits for results to appear then optionally clicks a result.
   */
  async searchPatient(search: ExistingPatientSearch): Promise<void> {
    await this.patientSearchInput.fill(search.query);
    await this.searchResults.waitFor({ state: "visible", timeout: 5_000 });
    if (search.selectResultText) {
      await this.searchResults
        .locator(`text=${search.selectResultText}`)
        .first()
        .click();
    }
  }

  // ── Submit ────────────────────────────────────────────────────────────────

  /**
   * Submit the create appointment form.
   */
  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Get all visible option labels in the dropdown.
   */
  async getDropdownOptionLabels(): Promise<string[]> {
    const options = this.dropdown.locator(
      '[data-testid^="crear-cita-option-"]',
    );
    const count = await options.count();
    const labels: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await options.nth(i).textContent();
      if (text) labels.push(text.trim());
    }
    return labels;
  }
}
