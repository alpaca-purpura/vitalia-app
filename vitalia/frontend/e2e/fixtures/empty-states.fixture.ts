/**
 * empty-states.fixture.ts — Playwright fixture for F1-S10 empty-states E2E specs.
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Extends the base auth.fixture (Clerk testing token + tenant localStorage).
 * Seeds shell state (theme=light, agentic split=open) for consistent renders.
 *
 * Provides:
 *   - `shellPage`: authenticated page with light shell state seeded
 *   - `darkShellPage`: authenticated page with dark theme for visual specs
 *
 * Usage:
 *   import { test, expect } from "../../fixtures/empty-states.fixture";
 *
 * spec_anchor: 04-validators.yaml § test_construction_plan.fixtures_required
 * downstream-regression-na: brand-local vitalia E2E fixture; no cross-brand consumers
 */

import { test as base, expect } from "../auth.fixture";
import type { Page } from "@playwright/test";

export { expect };

// ── Types ─────────────────────────────────────────────────────────────────────

export interface EmptyStatesFixtures {
  /** Authenticated page with shell localStorage seeded (light theme). */
  shellPage: Page;
  /** Authenticated page with shell localStorage seeded (dark theme). */
  darkShellPage: Page;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const SHELL_STORAGE_KEY = "vitalia-shell-state";
const SHELL_SPLIT_KEY = "vitalia-shell-split-agentic";

// ── Helpers ───────────────────────────────────────────────────────────────────

async function seedShellLocalStorage(
  page: Page,
  theme: "light" | "dark" = "light",
): Promise<void> {
  const shellState = JSON.stringify({
    state: { shellMode: "agentic", valeriaState: "full" },
    version: 0,
  });
  const splitState = JSON.stringify([50, 50]);

  await page.addInitScript(
    ({
      shellKey,
      splitKey,
      shellStateStr,
      splitStr,
      themeKey,
      themeValue,
    }: {
      shellKey: string;
      splitKey: string;
      shellStateStr: string;
      splitStr: string;
      themeKey: string;
      themeValue: string;
    }) => {
      localStorage.setItem(shellKey, shellStateStr);
      localStorage.setItem(splitKey, splitStr);
      localStorage.setItem(themeKey, themeValue);
      localStorage.setItem("__vitalia_e2e__", "true");
    },
    {
      shellKey: SHELL_STORAGE_KEY,
      splitKey: SHELL_SPLIT_KEY,
      shellStateStr: shellState,
      splitStr: splitState,
      themeKey: "vitalia-theme",
      themeValue: theme,
    },
  );
}

// ── Extended test object ──────────────────────────────────────────────────────

export const test = base.extend<EmptyStatesFixtures>({
  /**
   * shellPage: authenticated page with deterministic light shell state.
   * Mirrors routing-shell.fixture pattern for consistency.
   */
  shellPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, "light");
    await use(authedPage);
  },

  /**
   * darkShellPage: authenticated page with dark theme for visual golden specs.
   */
  darkShellPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, "dark");
    await use(authedPage);
  },
});
