/**
 * shell-theme.fixture.ts — Playwright fixture extending auth.fixture for shell + theme E2E.
 *
 * F1-S4 vitalia-fase1-shell-layout-5050 — T-7
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8 (extended ValeriaSidebarPage fixtures)
 *
 * Extends auth.fixture.ts to add:
 *   - `shellPage`: authedPage with deterministic localStorage pre-seeded
 *     (shellMode + valeriaState + theme) via addInitScript BEFORE navigation.
 *     Prevents Zustand hydration from reading stale/random state.
 *   - `darkShellPage`: same but forces dark theme for visual goldens.
 *   - `valeriaPage`: Page seeded with valeriaState='rail' + shellMode='agentic' + light theme.
 *   - `valeriaFullPage`: Page seeded with valeriaState='full' + shellMode='agentic' + light theme.
 *   - `valeriaRailPage`: Page seeded with valeriaState='rail' + shellMode='agentic' + light theme.
 *   - `valeriaMobilePage`: Page at mobile viewport (375x667) with drawer closed.
 *   - `valeriaPom`: convenience ValeriaSidebarPage POM bound to valeriaPage.
 *
 * addInitScript executes BEFORE page scripts — deterministic for visual goldens.
 *
 * Shell storage keys (must stay in sync with shell-store.ts):
 *   SHELL_STORAGE_KEY = 'vitalia-shell-state'
 *   SHELL_GROUP_ID    = 'vitalia-shell-split-agentic'
 *
 * Theme key: 'vitalia-theme' (next-themes stores to localStorage).
 *
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import { test as base } from "../auth.fixture";
import type { Page } from "@playwright/test";
import { ShellLayoutPage } from "../pages/ShellLayoutPage";
import { ValeriaSidebarPage } from "../pages/ValeriaSidebarPage";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SHELL_STORAGE_KEY = "vitalia-shell-state";
const SHELL_SPLIT_KEY = "vitalia-shell-split-agentic";
/** Default split: [50, 50] as react-resizable-panels v4 stores percentages */
const DEFAULT_SPLIT_AGENTIC = JSON.stringify([50, 50]);

// ---------------------------------------------------------------------------
// Fixtures interface
// ---------------------------------------------------------------------------

export interface ShellThemeFixtures {
  /** Authenticated page with agentic shell + valeriaState='full' + light theme pre-seeded. */
  shellPage: Page;
  /** Authenticated page with agentic shell + valeriaState='full' + DARK theme pre-seeded. */
  darkShellPage: Page;
  /** POM instance bound to shellPage. */
  shellPom: ShellLayoutPage;

  // ── F1-S5 ValeriaSidebar fixtures ─────────────────────────────────────────
  /** Page seeded with valeriaState='rail' + shellMode='agentic' + light theme. */
  valeriaPage: Page;
  /** Page seeded with valeriaState='full' + shellMode='agentic' + light theme. */
  valeriaFullPage: Page;
  /** Page seeded with valeriaState='rail' + shellMode='agentic' + light theme (alias). */
  valeriaRailPage: Page;
  /** Page at mobile viewport (375x667), valeriaState='collapsed', shellMode='web'. */
  valeriaMobilePage: Page;
  /** ValeriaSidebarPage POM bound to valeriaPage. */
  valeriaPom: ValeriaSidebarPage;
}

// ---------------------------------------------------------------------------
// Fixture implementation
// ---------------------------------------------------------------------------

/**
 * Seed localStorage deterministically via addInitScript.
 * Runs BEFORE any page script — guarantees Zustand hydrates from this state.
 */
async function seedShellLocalStorage(
  page: Page,
  options: {
    shellMode?: "agentic" | "web";
    valeriaState?: "full" | "rail" | "collapsed";
    theme?: "light" | "dark" | "system";
  } = {},
): Promise<void> {
  const {
    shellMode = "agentic",
    valeriaState = "full",
    theme = "light",
  } = options;

  const shellState = JSON.stringify({
    state: { shellMode, valeriaState },
    version: 0,
  });

  await page.addInitScript(
    ({ shellKey, splitKey, shellStateStr, splitStr, themeKey, themeValue }) => {
      // Seed shell state (Zustand persist format)
      localStorage.setItem(shellKey, shellStateStr);
      // Seed split persistence (react-resizable-panels v4 format)
      localStorage.setItem(splitKey, splitStr);
      // Seed theme (next-themes format)
      localStorage.setItem(themeKey, themeValue);
    },
    {
      shellKey: SHELL_STORAGE_KEY,
      splitKey: SHELL_SPLIT_KEY,
      shellStateStr: shellState,
      splitStr: DEFAULT_SPLIT_AGENTIC,
      themeKey: "vitalia-theme",
      themeValue: theme,
    },
  );
}

// ---------------------------------------------------------------------------
// Extended test with shell-theme fixtures
// ---------------------------------------------------------------------------

export const test = base.extend<ShellThemeFixtures>({
  /**
   * shellPage: authenticated page with deterministic shell state (agentic, full, light).
   * Uses authedPage as base (Clerk token injected + tenantId available).
   */
  shellPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, {
      shellMode: "agentic",
      valeriaState: "full",
      theme: "light",
    });
    await use(authedPage);
  },

  /**
   * darkShellPage: authenticated page with dark theme for visual goldens.
   */
  darkShellPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, {
      shellMode: "agentic",
      valeriaState: "full",
      theme: "dark",
    });
    await use(authedPage);
  },

  /**
   * shellPom: convenience POM bound to shellPage.
   */
  shellPom: async ({ shellPage }, use) => {
    await use(new ShellLayoutPage(shellPage));
  },

  // ── F1-S5 ValeriaSidebar fixtures ───────────────────────────────────────────

  /**
   * valeriaPage: authenticated page seeded with valeriaState='rail' for functional specs.
   */
  valeriaPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, {
      shellMode: "agentic",
      valeriaState: "rail",
      theme: "light",
    });
    await use(authedPage);
  },

  /**
   * valeriaFullPage: authenticated page seeded with valeriaState='full'.
   */
  valeriaFullPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, {
      shellMode: "agentic",
      valeriaState: "full",
      theme: "light",
    });
    await use(authedPage);
  },

  /**
   * valeriaRailPage: authenticated page seeded with valeriaState='rail' (alias).
   */
  valeriaRailPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, {
      shellMode: "agentic",
      valeriaState: "rail",
      theme: "light",
    });
    await use(authedPage);
  },

  /**
   * valeriaMobilePage: authenticated page at mobile viewport (375x667), drawer closed.
   * valeriaState='collapsed' so no drawer on load.
   * Note: test.use({ viewport }) is preferred in spec — this fixture provides the page
   * with correct localStorage seeding; callers must also set viewport via test.use().
   */
  valeriaMobilePage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, {
      shellMode: "web",
      valeriaState: "collapsed",
      theme: "light",
    });
    await use(authedPage);
  },

  /**
   * valeriaPom: ValeriaSidebarPage POM bound to valeriaPage (rail state).
   */
  valeriaPom: async ({ valeriaPage }, use) => {
    await use(new ValeriaSidebarPage(valeriaPage));
  },
});

export { expect } from "@playwright/test";
