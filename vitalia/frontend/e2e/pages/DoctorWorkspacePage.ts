// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * DoctorWorkspacePage.ts — Playwright POM for doctor workspace.
 *
 * Covers: EntitySubNavBar + perfil autosave + bio generation + avatar upload.
 *
 * Used by T-E2E specs for SC-10 (keyboard nav) and visual goldens.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 04-validators.yaml § POM fixtures
 *
 * Note: the dual-mount workaround (.filter({visible:true})) was removed on
 * T-FIX-2 (2026-06-01) — vitalia-shell-dual-mount-a11y-fix (c9d2bd31) fixed
 * the shell to render a single `[data-testid="app-panel-slot"]` per viewport.
 */

import type { Page, Locator } from "@playwright/test";

export class DoctorWorkspacePage {
  readonly page: Page;

  /** Visible app-panel-slot — root for all panel-scoped locators (B2 fix). */
  readonly panelRoot: Locator;

  // Navigation
  readonly entitySubNavBar: Locator;
  readonly backToStaffLink: Locator;
  readonly perfilTab: Locator;
  readonly horariosTab: Locator;
  readonly serviciosTab: Locator;
  readonly entityName: Locator;

  // Entity switcher (D3-A — EntityPicker via entityIdentitySlot, canon §6.3)
  // Trigger lives in the N3 bar; popover content portals to <body> → page-scoped.
  readonly pickerTrigger: Locator;
  readonly pickerContent: Locator;
  readonly pickerSearch: Locator;
  readonly pickerListbox: Locator;
  readonly pickerEmpty: Locator;
  readonly pickerFooter: Locator;

  // Perfil form
  readonly specialtyInput: Locator;
  readonly phoneInput: Locator;
  readonly yearsExperienceInput: Locator;
  readonly languagesInput: Locator;
  readonly visibilityToggle: Locator;
  readonly autosaveHint: Locator;

  // Bio repo inputs
  readonly bioNotesTextarea: Locator;
  readonly bioLinkInput: Locator;
  readonly bioAddLinkButton: Locator;
  readonly generateBioButton: Locator;

  // Avatar uploader
  readonly avatarButton: Locator;
  readonly dropzoneArea: Locator;

  // Servicios placeholder
  readonly serviciosPlaceholder: Locator;

  constructor(page: Page) {
    this.page = page;

    // Single app-panel-slot (vitalia-shell-dual-mount-a11y-fix resolved double-mount).
    this.panelRoot = page.getByTestId("app-panel-slot");

    // Nav — panel-scoped
    this.entitySubNavBar = this.panelRoot.getByTestId("entity-sub-nav-bar");
    this.backToStaffLink = this.panelRoot.getByRole("link", { name: /Staff/i });
    this.perfilTab = this.panelRoot.getByTestId("entity-leaf-perfil");
    this.horariosTab = this.panelRoot.getByTestId("entity-leaf-horarios");
    this.serviciosTab = this.panelRoot.getByTestId("entity-leaf-servicios");
    this.entityName = this.panelRoot.locator(
      "[data-testid='entity-sub-nav-bar'] .truncate",
    );

    // Picker (T-FE-switcher-wire) — trigger in N3 bar, content in portal
    this.pickerTrigger = this.panelRoot.getByTestId("doctor-picker-trigger");
    this.pickerContent = page.getByTestId("doctor-picker-content");
    this.pickerSearch = page.getByTestId("doctor-picker-search");
    this.pickerListbox = page.getByTestId("doctor-picker-listbox");
    this.pickerEmpty = page.getByTestId("doctor-picker-empty");
    this.pickerFooter = page.getByTestId("doctor-picker-footer");

    // Perfil — panel-scoped
    this.specialtyInput = this.panelRoot.getByLabel("Especialidad");
    this.phoneInput = this.panelRoot.getByLabel("Teléfono");
    this.yearsExperienceInput = this.panelRoot.getByLabel("Años de experiencia");
    this.languagesInput = this.panelRoot.getByLabel(
      "Idiomas (separados por coma)",
    );
    this.visibilityToggle = this.panelRoot.getByLabel("Visible en landing");
    this.autosaveHint = this.panelRoot.getByText(
      "Los cambios se guardan automáticamente",
    );

    // Bio — panel-scoped
    this.bioNotesTextarea = this.panelRoot.getByLabel("Notas para la bio");
    this.bioLinkInput = this.panelRoot.getByLabel("URL de referencia");
    this.bioAddLinkButton = this.panelRoot.getByRole("button", {
      name: "Agregar",
    });
    this.generateBioButton = this.panelRoot.getByRole("button", {
      name: /Generar bio/i,
    });

    // Avatar — panel-scoped
    this.avatarButton = this.panelRoot.getByRole("button", {
      name: /Cambiar foto/i,
    });
    this.dropzoneArea = this.panelRoot.getByTestId("dropzone-area");

    // Servicios — panel-scoped
    this.serviciosPlaceholder = this.panelRoot.getByTestId("servicios-placeholder");
  }

  async navigateToPerfil(tenantId: string, doctorId: string) {
    await this.page.goto(`/${tenantId}/lisa/staff/${doctorId}/perfil`);
  }

  async navigateToHorarios(tenantId: string, doctorId: string) {
    await this.page.goto(`/${tenantId}/lisa/staff/${doctorId}/horarios`);
  }

  async navigateToServicios(tenantId: string, doctorId: string) {
    await this.page.goto(`/${tenantId}/lisa/staff/${doctorId}/servicios`);
  }

  /** Click a leaf tab by id and wait for navigation */
  async clickLeaf(leafId: "perfil" | "horarios" | "servicios") {
    const tab = this.panelRoot.getByTestId(`entity-leaf-${leafId}`);
    await tab.click();
    await this.page.waitForURL(`**/${leafId}`);
  }

  /** Press Arrow key on the tablist for keyboard nav (SC-10) */
  async pressArrowRight() {
    const tablist = this.panelRoot.getByRole("tablist");
    await tablist.focus();
    await this.page.keyboard.press("ArrowRight");
  }

  async pressArrowLeft() {
    const tablist = this.panelRoot.getByRole("tablist");
    await tablist.focus();
    await this.page.keyboard.press("ArrowLeft");
  }

  /** Fill specialty and wait for autosave */
  async fillSpecialtyAndWait(value: string) {
    await this.specialtyInput.clear();
    await this.specialtyInput.fill(value);
    // Wait 600ms debounce + server response
    await this.page.waitForTimeout(800);
  }

  /** Click generate bio and wait for sections to appear */
  async generateBio() {
    await this.generateBioButton.click();
    await this.page.waitForSelector("[contenteditable]", { timeout: 10_000 });
  }

  // ── Entity switcher helpers (D3-A) ──────────────────────────────────────────

  /** Open the doctor picker popover and wait for the first page to render. */
  async openPicker() {
    await this.pickerTrigger.click();
    await this.pickerContent.waitFor({ state: "visible", timeout: 10_000 });
  }

  /** Type into the picker search (server-side debounced 200ms). */
  async searchInPicker(q: string) {
    await this.pickerSearch.fill(q);
  }

  /** Option locator by doctor id. */
  pickerOption(doctorId: string): Locator {
    return this.page.getByTestId(`doctor-picker-option-${doctorId}`);
  }

  /** Pick a doctor by id and wait for the leaf-preserving navigation. */
  async pickDoctorById(doctorId: string, expectedLeaf: string) {
    await this.pickerOption(doctorId).click();
    await this.page.waitForURL(`**/lisa/staff/${doctorId}/${expectedLeaf}`, {
      timeout: 15_000,
    });
  }
}
