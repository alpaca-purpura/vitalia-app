/**
 * shell-hardening.fixture.ts — Playwright fixture for shell-core-hardening specs.
 *
 * vitalia-shell-core-hardening — T-7
 *
 * Composes:
 *   - base.ts (gate anti-burbuja: pageerror/console-error/api≥400/Next overlay)
 *   - auth.fixture (Clerk testing token + tenantId + authedPage)
 *
 * Seeds localStorage pre-navigation with the NEW machine state (v1):
 *   valeriaOpen: 'chat' | 'closed'
 *   historyOpen: NOT persisted (always starts false)
 *
 * Usage in specs:
 *   import { test, expect } from '../../fixtures/shell-hardening.fixture';
 *
 * Shell storage keys (must stay in sync with shell-store.ts):
 *   SHELL_STORAGE_KEY = 'vitalia-shell-state'
 *   SHELL_SPLIT_KEY   = 'vitalia-shell-split-agentic'
 *
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import { mergeTests } from "@playwright/test";
import { test as baseGate } from "./base";
import { test as authed } from "../auth.fixture";
import type { Page } from "@playwright/test";
import type { ValeriaOpen } from "../pages/ShellLayoutPage";

// ---------------------------------------------------------------------------
// Constants (sync with shell-store.ts)
// ---------------------------------------------------------------------------

const SHELL_STORAGE_KEY = "vitalia-shell-state";
const SHELL_SPLIT_KEY = "vitalia-shell-split-agentic";
/** Default split [30, 70] — Valeria 30%, App 70% (RN-3) */
const DEFAULT_SPLIT = JSON.stringify([30, 70]);

// ---------------------------------------------------------------------------
// Fixtures interface
// ---------------------------------------------------------------------------

export interface ShellHardeningFixtures {
  /** Authenticated page with new machine defaults: valeriaOpen='chat', light, 30/70 split. */
  shellPage: Page;
  /** Authenticated page with Valeria closed (valeriaOpen='closed', state A). */
  closedShellPage: Page;
  /** Authenticated page seeded with dark theme. */
  darkShellPage: Page;
}

// ---------------------------------------------------------------------------
// Seed helper — new machine v1 shape
// ---------------------------------------------------------------------------

async function seedNewMachine(
  page: Page,
  opts: {
    valeriaOpen?: ValeriaOpen;
    theme?: "light" | "dark" | "system";
    split?: number[];
  } = {},
): Promise<void> {
  const {
    valeriaOpen = "chat",
    theme = "light",
    split = [30, 70],
  } = opts;

  // T-V2 lift: shape del kit — supervisorOpen/splitPct (v2). El param del
  // fixture conserva el nombre `valeriaOpen` (API estable para los specs).
  const shellState = JSON.stringify({
    state: { supervisorOpen: valeriaOpen, splitPct: null, mobileDrawerOpen: false },
    version: 2,
  });
  const splitStr = JSON.stringify(split);

  await page.addInitScript(
    ({
      shellKey,
      splitKey,
      shellStateStr,
      splitStr: spl,
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
      localStorage.setItem(splitKey, spl);
      localStorage.setItem(themeKey, themeValue);
    },
    {
      shellKey: SHELL_STORAGE_KEY,
      splitKey: SHELL_SPLIT_KEY,
      shellStateStr: shellState,
      splitStr,
      themeKey: "vitalia-theme",
      themeValue: theme,
    },
  );
}

// ---------------------------------------------------------------------------
// Merged test: base anti-bubble gate + auth
// ---------------------------------------------------------------------------

const baseTest = mergeTests(baseGate, authed);

export const test = baseTest.extend<ShellHardeningFixtures>({
  /**
   * shellPage: new-machine defaults. valeriaOpen='chat', 30/70 split, light theme.
   */
  shellPage: async ({ authedPage }, use) => {
    await seedNewMachine(authedPage, { valeriaOpen: "chat", theme: "light" });
    await use(authedPage);
  },

  /**
   * closedShellPage: Valeria closed (state A). valeriaOpen='closed', light theme.
   */
  closedShellPage: async ({ authedPage }, use) => {
    await seedNewMachine(authedPage, { valeriaOpen: "closed", theme: "light" });
    await use(authedPage);
  },

  /**
   * darkShellPage: valeriaOpen='chat', DARK theme.
   */
  darkShellPage: async ({ authedPage }, use) => {
    await seedNewMachine(authedPage, { valeriaOpen: "chat", theme: "dark" });
    await use(authedPage);
  },
});

export { expect } from "@playwright/test";
export type { ValeriaOpen };
export { DEFAULT_SPLIT, SHELL_STORAGE_KEY, SHELL_SPLIT_KEY };
