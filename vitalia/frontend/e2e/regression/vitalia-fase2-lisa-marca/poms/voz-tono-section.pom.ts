/**
 * voz-tono-section.pom.ts — VozTonoSectionPage POM
 *
 * Page object for the Voz y tono sub-sub-tab within lisa/marca.
 * Covers: archetype selector (4 Jung archetypes salud-friendly),
 * voice compiler v2 textareas (6-block asi_hablo / asi_no_hablo model),
 * prohibited phrase warning alert, override button,
 * and BrandVoicePreview footer section.
 *
 * REWRITE (estabilizar-harness-e2e-lisa-marca T-1b):
 *   Real testids preserved:
 *     - voz-tono-section-root (VozTonoView data-testid)
 *     - archetype-selector (ArchetypeSelector container)
 *     - archetype-card-{caregiver|sage|healer|hero} (radio cards)
 *     - brand-voice-preview (BrandVoicePreview root section, with data-hash)
 *     - tone-block-asi-hablo-textarea (VoiceCompilerBlocks block 3)
 *     - tone-block-asi-no-hablo-textarea (VoiceTextareaWithWarning block 4)
 *
 *   Replaced phantom locators:
 *     - warningAlert → getByRole('alert') filtered by warning text
 *     - regeneratePreviewButton → getByRole('button', {name:/Regenerar/i})
 *
 *   DELETED (features NOT implemented in FE):
 *     - voiceBlocklistSection / addPhraseInput / addPhraseButton / blocklistItems
 *       (voice blocklist UI does NOT exist in the FE)
 *     - openingHookTextarea / mainBodyTextarea / closingCtaTextarea
 *       (3-block model is fiction; FE uses 6-block asi_hablo/asi_no_hablo)
 *     - warningPhraseList (warning is inline text, no <li> list)
 *     - previewOpeningHook / previewMainBody / previewClosingCta
 *       (BrandVoicePreview shows agent bubbles, not named blocks)
 *     - previewLoadingSkeleton / previewErrorState / previewEmptyState / previewCacheHitBadge
 *       (no dedicated testids on these states)
 *
 * No assertions in POM methods (assertions live in spec files).
 *
 * downstream-regression-na: brand-local vitalia e2e POM F2-S7
 *
 * @see 04-validators.yaml § test_construction_plan step 7
 */

import { expect } from "@playwright/test";
import type { Page, Locator } from "@playwright/test";

/** Jung archetypes available for salud brand (OQ-B resolution) */
export type SaludArchetype = "caregiver" | "sage" | "healer" | "hero";

export class VozTonoSectionPage {
  readonly page: Page;

  // ---------------------------------------------------------------------------
  // Section container — real testid "voz-tono-section-root"
  // ---------------------------------------------------------------------------

  readonly sectionRoot: Locator;

  // ---------------------------------------------------------------------------
  // Archetype selector (4 radio cards)
  // Real testids from ArchetypeSelector component
  // ---------------------------------------------------------------------------

  /** Container for all archetype radio cards */
  readonly archetypeSelector: Locator;

  readonly archetypeCaregiverCard: Locator;
  readonly archetypeSageCard: Locator;
  readonly archetypeHealerCard: Locator;
  readonly archetypeHeroCard: Locator;

  // ---------------------------------------------------------------------------
  // Voice compiler v2 textareas (6-block model)
  // VoiceCompilerBlocks exposes testIds: tone-block-asi-hablo-textarea
  //                                     tone-block-asi-no-hablo-textarea
  // The 3-block (opening-hook/main-body/closing-cta) testids NEVER existed.
  // ---------------------------------------------------------------------------

  /** "Así hablo" textarea (block 3 — plain, no warning detection) */
  readonly asiHabloTextarea: Locator;

  /** "Así no hablo" textarea (block 4 — VoiceTextareaWithWarning) */
  readonly asiNoHabloTextarea: Locator;

  // ---------------------------------------------------------------------------
  // Prohibited phrase warning
  // VoiceTextareaWithWarning renders <Alert role="alert"> when phrase detected.
  // Buttons: "Aplicar sugerencia" | "Guardar igual"
  // ---------------------------------------------------------------------------

  /** Warning alert (role="alert") */
  readonly warningAlert: Locator;

  /** "Guardar igual" button — dismiss warning, keep text */
  readonly warningOverrideButton: Locator;

  /** "Aplicar sugerencia" button — replace text with suggestion */
  readonly warningSuggestionButton: Locator;

  // ---------------------------------------------------------------------------
  // BrandVoicePreview footer (real testid "brand-voice-preview")
  // Shows Valeria (WhatsApp) + Camila (email) agent bubbles.
  // data-hash attribute tracks voice blocks hash.
  // ---------------------------------------------------------------------------

  /** BrandVoicePreview section container */
  readonly brandVoicePreview: Locator;

  /** "Regenerar" button (invalidates preview React Query cache) */
  readonly regeneratePreviewButton: Locator;

  // ---------------------------------------------------------------------------
  // Constructor
  // ---------------------------------------------------------------------------

  constructor(page: Page) {
    this.page = page;

    // Section root
    this.sectionRoot = page.locator('[data-testid="voz-tono-section-root"]');

    // Archetype selector
    this.archetypeSelector = page.locator(
      '[data-testid="archetype-selector"]',
    );
    this.archetypeCaregiverCard = page.locator(
      '[data-testid="archetype-card-caregiver"]',
    );
    this.archetypeSageCard = page.locator(
      '[data-testid="archetype-card-sage"]',
    );
    this.archetypeHealerCard = page.locator(
      '[data-testid="archetype-card-healer"]',
    );
    this.archetypeHeroCard = page.locator(
      '[data-testid="archetype-card-hero"]',
    );

    // Voice compiler blocks (6-block model)
    this.asiHabloTextarea = page.locator(
      '[data-testid="tone-block-asi-hablo-textarea"]',
    );
    this.asiNoHabloTextarea = page.locator(
      '[data-testid="tone-block-asi-no-hablo-textarea"]',
    );

    // Warning alert (role="alert" from VoiceTextareaWithWarning)
    this.warningAlert = page.getByRole("alert").filter({
      hasText: /Frase a revisar|Sugerencia/i,
    });

    // Action buttons inside the warning
    this.warningOverrideButton = page.getByRole("button", {
      name: /Guardar igual/i,
    });
    this.warningSuggestionButton = page.getByRole("button", {
      name: /Aplicar sugerencia/i,
    });

    // BrandVoicePreview
    this.brandVoicePreview = page.locator(
      '[data-testid="brand-voice-preview"]',
    );

    // Regenerar button (text matches "Regenerar" or "Cargando...")
    this.regeneratePreviewButton = page.getByRole("button", {
      name: /Regenerar/i,
    });
  }

  // ---------------------------------------------------------------------------
  // Archetype interaction helpers
  // ---------------------------------------------------------------------------

  /**
   * Clicks the archetype card for the given archetype slug.
   * Triggers autosave debounce.
   */
  async selectArchetype(archetype: SaludArchetype): Promise<void> {
    const cardMap: Record<SaludArchetype, Locator> = {
      caregiver: this.archetypeCaregiverCard,
      sage: this.archetypeSageCard,
      healer: this.archetypeHealerCard,
      hero: this.archetypeHeroCard,
    };
    await cardMap[archetype].click();
  }

  /**
   * Returns the currently selected archetype slug (ONCE-READ — diagnostics only).
   * For deterministic assertions use `waitForSelectedArchetype`.
   */
  async getSelectedArchetype(): Promise<SaludArchetype | null> {
    const archetypes: SaludArchetype[] = [
      "caregiver",
      "sage",
      "healer",
      "hero",
    ];
    for (const archetype of archetypes) {
      const card = this.archetypeSelector.locator(
        `[data-testid="archetype-card-${archetype}"][data-selected="true"]`,
      );
      const count = await card.count();
      if (count > 0) return archetype;
    }
    return null;
  }

  /**
   * Web-first wait: asserts the given archetype card reaches
   * `data-selected="true"`, re-checking until met or timeout.
   */
  async waitForSelectedArchetype(
    archetype: SaludArchetype,
    timeoutMs = 15_000,
  ): Promise<void> {
    const card = this.archetypeSelector.locator(
      `[data-testid="archetype-card-${archetype}"]`,
    );
    await expect(card).toHaveAttribute("data-selected", "true", {
      timeout: timeoutMs,
    });
  }

  // ---------------------------------------------------------------------------
  // Voice block helpers
  // ---------------------------------------------------------------------------

  /**
   * Fills a voice block textarea.
   * Accepts the real block names (asi_hablo / asi_no_hablo) plus
   * legacy 3-block names for backwards-compatible spec calls.
   * Legacy mapping: openingHook/mainBody → asiHablo; closingCta → asiNoHablo.
   */
  async fillBlock(
    block:
      | "asi_hablo"
      | "asi_no_hablo"
      | "openingHook"
      | "mainBody"
      | "closingCta",
    value: string,
  ): Promise<void> {
    const textarea =
      block === "asi_no_hablo" || block === "closingCta"
        ? this.asiNoHabloTextarea
        : this.asiHabloTextarea;
    await textarea.click();
    await textarea.fill(value);
  }

  /**
   * Returns the current text of a voice block textarea.
   */
  async getBlockValue(
    block:
      | "asi_hablo"
      | "asi_no_hablo"
      | "openingHook"
      | "mainBody"
      | "closingCta",
  ): Promise<string> {
    const textarea =
      block === "asi_no_hablo" || block === "closingCta"
        ? this.asiNoHabloTextarea
        : this.asiHabloTextarea;
    return textarea.inputValue();
  }

  // ---------------------------------------------------------------------------
  // Warning alert helpers
  // ---------------------------------------------------------------------------

  /** Returns whether the prohibited phrase warning alert is visible. */
  async isWarningAlertVisible(): Promise<boolean> {
    return this.warningAlert.isVisible();
  }

  /**
   * Returns the detected phrase text from the warning alert.
   * Alert shows: "Frase a revisar: «phrase»"
   */
  async getWarningPhrases(): Promise<string[]> {
    const text = await this.warningAlert.textContent();
    if (!text) return [];
    // Extract quoted phrase from the alert text
    const match = /[""«]([^""»]+)[""»]/.exec(text);
    return match ? [match[1]] : [];
  }

  /** Clicks "Guardar igual" to dismiss the warning (keeps original text). */
  async clickOverrideWarning(): Promise<void> {
    await this.warningOverrideButton.click();
  }

  /** Clicks "Aplicar sugerencia" to replace text with the suggestion. */
  async clickApplySuggestion(): Promise<void> {
    await this.warningSuggestionButton.click();
  }

  // ---------------------------------------------------------------------------
  // BrandVoicePreview helpers
  // ---------------------------------------------------------------------------

  /** Returns the BrandVoicePreview container locator. */
  getBrandVoicePreview(): Locator {
    return this.brandVoicePreview;
  }

  /**
   * Waits for the preview to load (becomes visible and not busy).
   * BrandVoicePreview shows agent bubbles (Valeria + Camila) when loaded.
   */
  async waitForPreviewLoaded(timeoutMs: number = 10_000): Promise<void> {
    await expect(this.brandVoicePreview).toBeVisible({ timeout: timeoutMs });
    await expect(this.brandVoicePreview).not.toHaveAttribute("aria-busy", "true", {
      timeout: timeoutMs,
    });
  }

  /**
   * Returns preview sample texts from BrandVoicePreview agent bubbles.
   * Maps to the legacy spec API: openingHook = Valeria bubble, mainBody = Camila bubble.
   */
  async getPreviewSamples(): Promise<{
    openingHook: string | null;
    mainBody: string | null;
    closingCta: string | null;
  }> {
    const valeraLabel = await this.brandVoicePreview
      .locator("text=Valeria")
      .first()
      .textContent()
      .catch(() => null);
    // Check if any non-skeleton text content exists in the preview bubbles
    const bubbleContent = await this.brandVoicePreview
      .locator("div[class*='rounded-lg']")
      .first()
      .textContent()
      .catch(() => null);
    return {
      openingHook: valeraLabel ? bubbleContent : null,
      mainBody: null,
      closingCta: null,
    };
  }

  /** Returns whether the preview cache hit badge is visible. */
  async isPreviewCacheHit(): Promise<boolean> {
    // BrandVoicePreview does not expose a cache-hit testid.
    // This check is retained for API compatibility but always returns false.
    return false;
  }
}
