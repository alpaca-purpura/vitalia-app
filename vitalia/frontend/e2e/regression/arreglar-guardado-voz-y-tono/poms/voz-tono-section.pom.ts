/**
 * voz-tono-section.pom.ts — VozTonoSection POM for arreglar-guardado-voz-y-tono regression specs.
 *
 * Scoped to voz-y-tono sub-sub-tab: archetype selector, voice compiler blocks,
 * autosave badge, and page navigation.
 *
 * Methods per 04-validators.yaml § test_construction_plan step 3 (poms_required):
 *   goto()               — navigate to voz-y-tono for the given tenantId
 *   selectArchetype()    — click archetype card by name
 *   editVoiceBlock()     — fill a named voice block textarea
 *   getAutosaveStatus()  — read autosave badge data-state attribute
 *   reload()             — reload the page and wait for domcontentloaded
 *
 * No assertions in POM methods — assertions live in spec files.
 *
 * downstream-regression-na: brand-local vitalia e2e POM T-3 arreglar-guardado-voz-y-tono
 *
 * @see 04-validators.yaml § test_construction_plan step 3
 * @see 06-tickets.yaml T-3 deliverables
 */

import { expect } from "@playwright/test";
import type { Page, Locator } from "@playwright/test";

// Voice block names as shown in the UI and mapped to the textarea data-testid.
export type VoiceBlockName =
  | "Así hablo"
  | "Así no hablo"
  | "Contexto técnico"
  | "Formato"
  | "Ancla identidad"
  | "Contexto dominio";

/** Archetype slugs available in the salud brand. */
export type SaludArchetype = "caregiver" | "sage" | "healer" | "hero";

/** Autosave badge states matching AutosaveBadge data-state attribute. */
export type AutosaveStatus = "idle" | "dirty" | "saving" | "saved" | "error";

// Map from UI-facing block name to the data-testid suffix used in the component.
const BLOCK_TESTID_MAP: Record<VoiceBlockName, string> = {
  "Así hablo": "tone-block-asi-hablo-textarea",
  "Así no hablo": "tone-block-asi-no-hablo-textarea",
  "Contexto técnico": "tone-block-tech-context-textarea",
  "Formato": "tone-block-format-textarea",
  "Ancla identidad": "tone-block-identity-textarea",
  "Contexto dominio": "tone-block-context-textarea",
};

// Map from archetype slug to data-testid used in ArchetypeSelector component.
const ARCHETYPE_TESTID_MAP: Record<SaludArchetype, string> = {
  caregiver: "archetype-card-caregiver",
  sage: "archetype-card-sage",
  healer: "archetype-card-healer",
  hero: "archetype-card-hero",
};

export class VozTonoSectionPom {
  readonly page: Page;
  readonly tenantId: string;

  // ---------------------------------------------------------------------------
  // Core locators
  // ---------------------------------------------------------------------------

  /** Autosave badge indicator — data-state = idle|dirty|saving|saved|error */
  readonly autosaveBadge: Locator;

  /** Archetype selector container */
  readonly archetypeSelector: Locator;

  /** Section root (if rendered by VozTonoView) */
  readonly sectionRoot: Locator;

  /** Page main content area */
  readonly marcaContent: Locator;

  /** Loading skeleton */
  readonly loadingSkeleton: Locator;

  // ---------------------------------------------------------------------------
  // Constructor
  // ---------------------------------------------------------------------------

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    // The shell-organism layout may render multiple panels in the DOM.
    // Scope everything to the first voz-tono-section-root to avoid strict-mode violations.
    // We use .first() on the root and then scope children to it via .locator().
    this.sectionRoot = page.locator('[data-testid="voz-tono-section-root"]').first();
    this.marcaContent = page.locator('[data-testid="voz-tono-section-root"]').first();
    this.loadingSkeleton = page.locator('[data-testid="lisa-marca-loading-skeleton"]').first();

    // Scope badge and selector to within the section root to avoid duplicate matches
    // when the shell renders other sections with their own AutosaveBadge instances.
    this.autosaveBadge = this.sectionRoot.locator('[data-testid="autosave-badge"]');
    this.archetypeSelector = this.sectionRoot.locator('[data-testid="archetype-selector"]');
  }

  // ---------------------------------------------------------------------------
  // Navigation
  // ---------------------------------------------------------------------------

  /**
   * Navigate directly to the voz-y-tono sub-sub-tab for this tenant.
   * Waits for domcontentloaded.
   */
  async goto(): Promise<void> {
    await this.page.goto(`/${this.tenantId}/lisa/marca/voz-y-tono`);
    await this.page.waitForLoadState("domcontentloaded");
  }

  /**
   * Reload the page (simulates browser F5).
   * Waits for domcontentloaded.
   */
  async reload(): Promise<void> {
    await this.page.reload();
    await this.page.waitForLoadState("domcontentloaded");
  }

  /**
   * Wait until the page content is fully loaded (skeleton hidden, content visible).
   * Waits for voz-tono-section-root to appear (VozTonoView root div).
   * The loading skeleton from page.tsx (Suspense fallback) should have disappeared by then.
   *
   * Also waits for ArchetypeSelector to hydrate: either an archetype card is selected
   * (data-selected="true") OR the radiogroup is visible (empty/no-selection state).
   * This prevents getSelectedArchetype() returning null due to query in-flight timing.
   */
  async waitForLoaded(timeoutMs = 15_000): Promise<void> {
    // Skeleton is the Suspense fallback in page.tsx — it disappears when VozTonoView mounts.
    // If it's already gone, this resolves immediately.
    await this.loadingSkeleton
      .waitFor({ state: "hidden", timeout: timeoutMs })
      .catch(() => {
        // Skeleton might not render at all if hydration is fast — that's OK.
      });
    // The VozTonoView root div — this is the canonical "content is mounted" signal.
    await this.sectionRoot.waitFor({ state: "visible", timeout: timeoutMs });

    // Wait for the GET /personality query to hydrate: an archetype CARD renders
    // (cards + voice blocks share the same query). Tolerant (.catch) porque el
    // harness de lisa-marca tiene una race conocida de auth-readiness de Clerk en
    // el GET /personality in-browser (ver chris-input.md · pendiente harness-fix
    // dedicado). La query reintenta (retry:5 en VozTonoView); cuando hidrata, el
    // card aparece. Los asserts de cada spec usan polling (toHaveValue/waitFor).
    await this.sectionRoot
      .locator('[data-testid^="archetype-card-"]')
      .first()
      .waitFor({ state: "visible", timeout: timeoutMs })
      .catch(() => {
        // Personality GET aún no hidrató (race de Clerk) — el spec decide vía polling.
      });
  }

  // ---------------------------------------------------------------------------
  // Archetype interaction
  // ---------------------------------------------------------------------------

  /**
   * Click the archetype card with the given name (slug).
   * Triggers autosave debounce (600ms).
   *
   * @param name - One of the 4 salud archetypes: caregiver, sage, healer, hero.
   */
  async selectArchetype(name: SaludArchetype): Promise<void> {
    const testid = ARCHETYPE_TESTID_MAP[name];
    // Scope to sectionRoot to avoid strict-mode violation when shell has multiple panels.
    const card = this.sectionRoot.locator(`[data-testid="${testid}"]`);
    await card.click();
  }

  /**
   * Returns the currently selected archetype slug (ONCE-READ — diagnostics only).
   * Reads data-selected="true" from archetype cards. Returns null if none.
   *
   * ⚠️ NO usar para aserciones de estado hidratado (devuelve null si el GET
   * /personality aún no hidrató). Para aserciones usar `waitForSelectedArchetype`.
   */
  async getSelectedArchetype(): Promise<SaludArchetype | null> {
    const archetypes = Object.keys(ARCHETYPE_TESTID_MAP) as SaludArchetype[];
    for (const archetype of archetypes) {
      const card = this.sectionRoot.locator(
        `[data-testid="${ARCHETYPE_TESTID_MAP[archetype]}"][data-selected="true"]`,
      );
      if ((await card.count()) > 0) return archetype;
    }
    return null;
  }

  /**
   * Web-first wait: asserts the given archetype card reaches
   * `data-selected="true"`, re-checking until met or timeout. ESTE es el fix de
   * determinismo (B3) para los specs reload-persist des-quarantined.
   *
   * @param archetype - The archetype slug expected to be selected.
   */
  async waitForSelectedArchetype(
    archetype: SaludArchetype,
    timeoutMs = 15_000,
  ): Promise<void> {
    const card = this.sectionRoot.locator(
      `[data-testid="${ARCHETYPE_TESTID_MAP[archetype]}"]`,
    );
    await expect(card).toHaveAttribute("data-selected", "true", {
      timeout: timeoutMs,
    });
  }

  // ---------------------------------------------------------------------------
  // Voice block interaction
  // ---------------------------------------------------------------------------

  /**
   * Fill a named voice block textarea.
   * Triggers autosave debounce after fill.
   *
   * @param block - UI-facing block name (e.g., "Así hablo").
   * @param text  - The text to fill into the block.
   */
  async editVoiceBlock(block: VoiceBlockName, text: string): Promise<void> {
    const testid = BLOCK_TESTID_MAP[block];
    // Scope to sectionRoot to avoid strict-mode violation.
    const textarea = this.sectionRoot.locator(`[data-testid="${testid}"]`);
    await textarea.click();
    await textarea.fill(text);
  }

  /**
   * Returns the current value of a named voice block textarea.
   */
  async getVoiceBlockValue(block: VoiceBlockName): Promise<string> {
    const testid = BLOCK_TESTID_MAP[block];
    const textarea = this.sectionRoot.locator(`[data-testid="${testid}"]`);
    return textarea.inputValue();
  }

  // ---------------------------------------------------------------------------
  // Autosave badge helpers
  // ---------------------------------------------------------------------------

  /**
   * Returns the current autosave status from the badge data-state attribute.
   * Returns "idle" if badge is not visible or attribute is absent.
   */
  async getAutosaveStatus(): Promise<AutosaveStatus> {
    const visible = await this.autosaveBadge.isVisible();
    if (!visible) return "idle";
    const state = await this.autosaveBadge.getAttribute("data-state");
    if (
      state === "idle" ||
      state === "dirty" ||
      state === "saving" ||
      state === "saved" ||
      state === "error"
    ) {
      return state;
    }
    return "idle";
  }

  /**
   * Returns the text content of the autosave badge.
   * Returns null if badge is not visible.
   */
  async getAutosaveBadgeText(): Promise<string | null> {
    const visible = await this.autosaveBadge.isVisible();
    if (!visible) return null;
    return this.autosaveBadge.textContent();
  }

  /**
   * Waits until autosave badge shows "saved" state.
   * Throws if timeout exceeded.
   */
  async waitForAutosaveSaved(timeoutMs = 10_000): Promise<void> {
    await this.sectionRoot
      .locator('[data-testid="autosave-badge"][data-state="saved"]')
      .waitFor({ state: "visible", timeout: timeoutMs });
  }

  /**
   * Waits until autosave badge shows "saving" state.
   */
  async waitForAutosaveSaving(timeoutMs = 10_000): Promise<void> {
    await this.sectionRoot
      .locator('[data-testid="autosave-badge"][data-state="saving"]')
      .waitFor({ state: "visible", timeout: timeoutMs });
  }

  /**
   * Waits until autosave badge shows "error" state.
   */
  async waitForAutosaveError(timeoutMs = 10_000): Promise<void> {
    await this.sectionRoot
      .locator('[data-testid="autosave-badge"][data-state="error"]')
      .waitFor({ state: "visible", timeout: timeoutMs });
  }
}
