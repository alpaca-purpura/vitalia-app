/**
 * identidad-section.pom.ts — IdentidadSectionPage POM
 *
 * Page object for the Identidad sub-sub-tab within lisa/marca.
 * Covers: brand name, tagline, logo upload, color picker,
 * team preview link, and edit-config (clinic vertical read-only) link.
 *
 * REWRITE (estabilizar-harness-e2e-lisa-marca T-1b):
 *   - Phantom testids replaced with REAL selectors (getByRole > getByLabel > getByTestId).
 *   - `descriptionTextarea` DELETED — IdentityCard has no description field.
 *   - Logo drop zone: <button> with aria-label (no testid).
 *   - Logo file input: sr-only with aria-label "Seleccionar archivo de logo".
 *   - Logo errors: getByRole('alert') filtered by error-message text.
 *   - Color hex inputs: getByLabel per ColorTriadEditor aria-label pattern.
 *   - editConfigLink → getByRole('link', {name:/Editar especialidad/i}).
 *   - teamPreviewLink → getByRole('link', {name:/Gestionar equipo/i}).
 *   - extractionStubButton → getByRole('button', {name:/Extraer del sitio web/i}).
 *
 * DELETED phantom locators:
 *   - descriptionTextarea (field does not exist in IdentityCard)
 *   - primaryColorPicker / secondaryColorPicker (no popover trigger — inline swatch)
 *   - secondaryColorHexInput (ColorTriadEditor uses primary/accent/background)
 *   - clinicVerticalBadge (no testid; badge is rendered via Shadcn Badge component)
 *   - teamPreviewCount (no testid; shown as text inside TeamPreviewRow)
 *   - removeLogoButton (LogoDropZone renders "Cambiar logo" ghost button, not remove)
 *   - logoPreviewImage (Image component; no testid)
 *   - extractionStubTooltip (TooltipContent; no testid; tooltip on hover)
 *   - logoSizeErrorAlert / logoTypeErrorAlert (merged into logoValidationAlert)
 *
 * No assertions in POM methods (assertions live in spec files).
 *
 * downstream-regression-na: brand-local vitalia e2e POM F2-S7
 *
 * @see 04-validators.yaml § test_construction_plan step 6
 */

import type { Page, Locator } from "@playwright/test";

export class IdentidadSectionPage {
  readonly page: Page;

  // ---------------------------------------------------------------------------
  // Section container — real testid "identidad-view"
  // ---------------------------------------------------------------------------

  readonly sectionRoot: Locator;

  // ---------------------------------------------------------------------------
  // Brand name + tagline form (no description field)
  // ---------------------------------------------------------------------------

  /** Brand name input — label: "Nombre de la clínica" (htmlFor=brand-name-input) */
  readonly nameInput: Locator;

  /** Tagline input — label: "Tagline" (htmlFor=tagline-input) */
  readonly taglineInput: Locator;

  // ---------------------------------------------------------------------------
  // Logo upload
  // LogoDropZone renders a <button role="button"> with dynamic aria-label.
  // The hidden file input has aria-label "Seleccionar archivo de logo".
  // Validation errors render as <p role="alert"> (one element, covers both size+type).
  // ---------------------------------------------------------------------------

  /** Logo drop zone button (aria-label matches "Subir logo" or "Cambiar logo") */
  readonly logoDropZone: Locator;

  /** Hidden file input (sr-only, aria-label "Seleccionar archivo de logo") */
  readonly logoFileInput: Locator;

  /** Logo validation alert — covers both size and format errors */
  readonly logoValidationAlert: Locator;

  // ---------------------------------------------------------------------------
  // Color picker (ColorTriadEditor — inline swatches, no popover)
  // Hex inputs have aria-label "{Label}: valor hexadecimal"
  // ---------------------------------------------------------------------------

  /** Primary color hex input */
  readonly primaryColorHexInput: Locator;

  /** Accent color hex input */
  readonly accentColorHexInput: Locator;

  /** Background color hex input */
  readonly backgroundColorHexInput: Locator;

  // ---------------------------------------------------------------------------
  // Clinic vertical read-only
  // ClinicVerticalReadOnly renders a <Link> with aria-label containing "Editar"
  // ---------------------------------------------------------------------------

  /** "Editar" link to /onboarding/clinic-config */
  readonly editConfigLink: Locator;

  // ---------------------------------------------------------------------------
  // Team preview
  // TeamPreviewRow renders a <Link> with aria-label "Gestionar integrantes del equipo"
  // (only when doctoresStoryDone=true; otherwise a disabled <span>)
  // ---------------------------------------------------------------------------

  /** "Gestionar equipo" link */
  readonly teamPreviewLink: Locator;

  // ---------------------------------------------------------------------------
  // Visual extraction stub
  // ExtractFromWebsiteButton is a disabled <Button aria-label="Extraer colores...">
  // ---------------------------------------------------------------------------

  /** Disabled "Extraer del sitio web" button */
  readonly extractionStubButton: Locator;

  // ---------------------------------------------------------------------------
  // Constructor
  // ---------------------------------------------------------------------------

  constructor(page: Page) {
    this.page = page;

    // Section root
    this.sectionRoot = page.getByTestId("identidad-view");

    // Form fields
    this.nameInput = page.getByLabel(/Nombre de la cl[íi]nica/);
    this.taglineInput = page.getByLabel(/Tagline/);

    // Logo drop zone button
    this.logoDropZone = page.getByRole("button", {
      name: /Subir logo|Cambiar logo/i,
    });

    // Hidden file input
    this.logoFileInput = page.getByLabel(/Seleccionar archivo de logo/i);

    // Logo validation alert (size or format error)
    this.logoValidationAlert = page
      .getByRole("alert")
      .filter({ hasText: /MB|Formato|l[íi]mite|permitido/i });

    // Color hex inputs
    this.primaryColorHexInput = page.getByLabel(
      /Color primario: valor hexadecimal/i,
    );
    this.accentColorHexInput = page.getByLabel(
      /Color accent: valor hexadecimal/i,
    );
    this.backgroundColorHexInput = page.getByLabel(
      /Color de fondo: valor hexadecimal/i,
    );

    // Clinic vertical edit link
    this.editConfigLink = page.getByRole("link", {
      name: /Editar especialidad/i,
    });

    // Team preview link
    this.teamPreviewLink = page.getByRole("link", {
      name: /Gestionar (integrantes del )?equipo/i,
    });

    // Extraction stub button
    this.extractionStubButton = page.getByRole("button", {
      name: /Extraer (colores y tipograf[íi]a del sitio web|del sitio web)/i,
    });
  }

  // ---------------------------------------------------------------------------
  // Form interaction helpers
  // ---------------------------------------------------------------------------

  /** Returns the current value of the brand name input. */
  async getNameInputValue(): Promise<string> {
    return this.nameInput.inputValue();
  }

  /** Clears and fills the brand name input. Triggers autosave debounce (600ms). */
  async fillName(value: string): Promise<void> {
    await this.nameInput.click();
    await this.nameInput.fill(value);
  }

  /** Clears and fills the tagline input. */
  async fillTagline(value: string): Promise<void> {
    await this.taglineInput.click();
    await this.taglineInput.fill(value);
  }

  // ---------------------------------------------------------------------------
  // Logo upload helpers
  // ---------------------------------------------------------------------------

  /** Returns the logo drop zone button locator. */
  getLogoDropZone(): Locator {
    return this.logoDropZone;
  }

  /**
   * Uploads a logo file via the hidden file input.
   * Check logoValidationAlert after calling if testing validation.
   */
  async uploadLogo(filePath: string): Promise<void> {
    await this.logoFileInput.setInputFiles(filePath);
  }

  /** Returns whether the logo validation error alert is visible. */
  async isLogoValidationErrorVisible(): Promise<boolean> {
    return this.logoValidationAlert.isVisible();
  }

  // ---------------------------------------------------------------------------
  // Color picker helpers
  // ---------------------------------------------------------------------------

  /** Fills the primary color hex input and commits with Enter. */
  async fillPrimaryHex(hexValue: string): Promise<void> {
    await this.primaryColorHexInput.fill(hexValue);
    await this.primaryColorHexInput.press("Enter");
  }

  /** Returns the current hex value of the primary color input. */
  async getPrimaryHexValue(): Promise<string> {
    return this.primaryColorHexInput.inputValue();
  }

  // ---------------------------------------------------------------------------
  // Navigation helpers
  // ---------------------------------------------------------------------------

  /** Returns the team preview link locator. */
  getTeamPreviewLink(): Locator {
    return this.teamPreviewLink;
  }

  /** Returns the "Editar especialidad" link locator. */
  getEditConfigLink(): Locator {
    return this.editConfigLink;
  }
}
