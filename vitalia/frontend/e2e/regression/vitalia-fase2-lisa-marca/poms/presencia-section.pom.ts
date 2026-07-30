/**
 * presencia-section.pom.ts — PresenciaSectionPage POM
 *
 * Page object for the Presencia sub-sub-tab within lisa/marca.
 * Covers: website URL + social media fields, trust signals management.
 *
 * REWRITE (estabilizar-harness-e2e-lisa-marca T-1b):
 *   Real implementation:
 *     - PresenciaView data-testid "presencia-view" (section root)
 *     - WebsiteCard: <Input aria-label="URL del sitio web">
 *     - SocialMediaLinksEditor: 5 rows with ariaLabel per channel
 *         instagram → "Usuario de Instagram"
 *         tiktok   → "Usuario de TikTok"
 *         facebook → "Página de Facebook"
 *         google_business → "URL de Google Business"
 *         whatsapp → "Número de WhatsApp Business"
 *     - TrustSignalsEditor: no testids → use role/text/heading
 *         section heading: "Señales de autoridad"
 *         "Agregar" button for free-text "Otra"
 *         active certs: role="list" aria-label="Certificaciones activas"
 *         remove chip: button aria-label="Quitar certificación {label}"
 *
 *   DELETED phantom locators:
 *     - addressInput (contact-address-input — NOT implemented in FE)
 *     - phoneInput (contact-phone-input — NOT implemented in FE)
 *     - trustSignalsList (no testid; use role="list")
 *     - trustCatalogTrigger (no combobox; catalog is a <details> expander)
 *     - trustCatalogOptions (no testid; options inside <details>)
 *     - customTrustSignalInput (no testid; use getByLabel/getByPlaceholder)
 *     - addTrustSignalButton (no testid; use getByRole('button'))
 *     - trustSignalsEmptyState (no testid; inline text)
 *     - trustSignalsSection (no testid; use heading)
 *     - trust-signals-loading-skeleton (NOT rendered; loading shown via aria-busy)
 *
 * No assertions in POM methods (assertions live in spec files).
 *
 * downstream-regression-na: brand-local vitalia e2e POM F2-S7
 *
 * @see 04-validators.yaml § test_construction_plan step 8
 */

import type { Page, Locator } from "@playwright/test";

export class PresenciaSectionPage {
  readonly page: Page;

  // ---------------------------------------------------------------------------
  // Section container — real testid "presencia-view"
  // ---------------------------------------------------------------------------

  readonly sectionRoot: Locator;

  // ---------------------------------------------------------------------------
  // Digital presence fields
  // WebsiteCard: aria-label "URL del sitio web"
  // SocialMediaLinksEditor: each channel has ariaLabel per SOCIAL_CHANNELS config
  // ---------------------------------------------------------------------------

  /** Website URL input */
  readonly websiteInput: Locator;

  /** Instagram handle input */
  readonly instagramInput: Locator;

  /** TikTok handle input */
  readonly tiktokInput: Locator;

  /** Facebook page input */
  readonly facebookInput: Locator;

  /** Google Business URL input */
  readonly googleBusinessInput: Locator;

  /** WhatsApp Business number input */
  readonly whatsappInput: Locator;

  // ---------------------------------------------------------------------------
  // Trust signals
  // TrustSignalsEditor: no testids — use role/text/heading selectors
  // Section heading: "Señales de autoridad"
  // Active certs list: role="list" aria-label="Certificaciones activas"
  // "Agregar" button: getByRole('button', {name:/Agregar certif/i})
  // Empty state: inline text (no testid)
  // ---------------------------------------------------------------------------

  /** Trust signals card (scoped by heading "Señales de autoridad") */
  readonly trustSignalsSection: Locator;

  /** Active trust signals list (role="list" aria-label="Certificaciones activas") */
  readonly trustSignalsList: Locator;

  /** "Agregar" button for free-text "Otra" certification input */
  readonly addTrustSignalButton: Locator;

  /** Free-text "Otra" certification input */
  readonly customTrustSignalInput: Locator;

  /** Empty state text (shown when no certs; no testid — text content check) */
  readonly trustSignalsEmptyState: Locator;

  // ---------------------------------------------------------------------------
  // Constructor
  // ---------------------------------------------------------------------------

  constructor(page: Page) {
    this.page = page;

    // Section root
    this.sectionRoot = page.getByTestId("presencia-view");

    // Website input (WebsiteCard uses FormLabel + Input with aria-label)
    this.websiteInput = page.getByLabel(/URL del sitio web/i);

    // Social media inputs (SocialMediaLinksEditor ariaLabel per channel)
    this.instagramInput = page.getByLabel(/Usuario de Instagram/i);
    this.tiktokInput = page.getByLabel(/Usuario de TikTok/i);
    this.facebookInput = page.getByLabel(/P[áa]gina de Facebook/i);
    this.googleBusinessInput = page.getByLabel(/URL de Google Business/i);
    this.whatsappInput = page.getByLabel(/N[úu]mero de WhatsApp Business/i);

    // Trust signals section: scoped to the card containing the heading
    this.trustSignalsSection = page.locator(
      "div:has(> div > h3:text-is('Señales de autoridad'))",
    );

    // Active certs list (role="list" aria-label="Certificaciones activas")
    this.trustSignalsList = page.getByRole("list", {
      name: /Certificaciones activas/i,
    });

    // "Agregar" button for free-text "Otra" (inside the <details> expander)
    this.addTrustSignalButton = page.getByRole("button", {
      name: /Agregar certif/i,
    });

    // "Otra certificación..." placeholder input
    this.customTrustSignalInput = page.getByPlaceholder(
      /Otra certif/i,
    );

    // Empty state: inline text paragraph (no testid)
    this.trustSignalsEmptyState = page.getByText(
      /Aún no se han agregado certificaciones/i,
    );
  }

  // ---------------------------------------------------------------------------
  // Digital presence helpers
  // ---------------------------------------------------------------------------

  /** Fills the website URL input and triggers autosave. */
  async fillWebsite(url: string): Promise<void> {
    await this.websiteInput.click();
    await this.websiteInput.fill(url);
  }

  /** Returns the current website input value. */
  async getWebsiteValue(): Promise<string> {
    return this.websiteInput.inputValue();
  }

  /** Fills the Instagram handle input. */
  async fillInstagram(handle: string): Promise<void> {
    await this.instagramInput.click();
    await this.instagramInput.fill(handle);
  }

  /** Fills the TikTok handle input. */
  async fillTikTok(handle: string): Promise<void> {
    await this.tiktokInput.click();
    await this.tiktokInput.fill(handle);
  }

  /** Fills the Google Business URL input. */
  async fillGoogleBusiness(url: string): Promise<void> {
    await this.googleBusinessInput.click();
    await this.googleBusinessInput.fill(url);
  }

  // ---------------------------------------------------------------------------
  // Trust signal helpers
  // ---------------------------------------------------------------------------

  /**
   * Returns the number of active trust signal chips currently displayed.
   * Counts role="listitem" items inside the active certs list.
   */
  async getTrustSignalCount(): Promise<number> {
    const visible = await this.trustSignalsList.isVisible();
    if (!visible) return 0;
    return this.trustSignalsList.getByRole("listitem").count();
  }

  /**
   * Adds a custom (free-text "Otra") trust signal.
   * Assumes the <details> catalog is already expanded or will expand on interaction.
   */
  async addCustomTrustSignal(customValue: string): Promise<void> {
    await this.customTrustSignalInput.fill(customValue);
    await this.addTrustSignalButton.click();
  }

  /**
   * Removes a trust signal by its display label.
   * Clicks the "Quitar certificación {label}" button.
   */
  async removeTrustSignalByLabel(label: string): Promise<void> {
    await this.page
      .getByRole("button", { name: new RegExp(`Quitar certif.*${label}`, "i") })
      .click();
  }

  /**
   * Returns an array of trust signal label texts currently active.
   */
  async getTrustSignalValues(): Promise<string[]> {
    const visible = await this.trustSignalsList.isVisible();
    if (!visible) return [];
    const items = this.trustSignalsList.getByRole("listitem");
    const count = await items.count();
    const values: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await items.nth(i).textContent();
      if (text) values.push(text.trim());
    }
    return values;
  }

  /**
   * Returns whether the trust signals empty state text is visible.
   * (shown when no certifications have been added yet)
   */
  async isTrustSignalsEmptyStateVisible(): Promise<boolean> {
    return this.trustSignalsEmptyState.isVisible();
  }

  /**
   * Waits until the trust signals section loads.
   * TrustSignalsEditor fetches signals (React Query); wait until the section renders.
   * No loading skeleton testid — wait for the section root to be visible.
   */
  async waitForTrustSignalsLoaded(timeoutMs: number = 10_000): Promise<void> {
    await this.trustSignalsSection.waitFor({
      state: "visible",
      timeout: timeoutMs,
    });
  }
}
