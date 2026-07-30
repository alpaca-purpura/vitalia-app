// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-dual-mount-a11y-fix
/**
 * single-slot-live.spec.ts — LIVE verification of the dual-mount fix (T-2 · ADR-vitalia-008).
 *
 * This is a TRUE live-verify spec (Critical Rule #37 + definition-of-done-live-verify.md):
 *   - Runs against the REAL running dev stack (FE :3002 + BE :8002), authenticated
 *     with the Clerk testing token (auth.fixture → authedPage). NO backend mocking.
 *   - The doctores e2e suite mocks the backend (STAFF_SEED / page.route) → that is a
 *     FALSE-VERDE and does NOT count as live-verify. The dual-mount fix is shell-
 *     structural (count of <main> + AppPanelSlot), so it renders correctly regardless
 *     of backend data — we exercise the real shell and read the real DOM + console.
 *
 * Proves the fix from b65baae6 (single-main + single-slot):
 *   - exactly ONE  <main id="main-content">          (was 3 — triple-main HTML-invalid)
 *   - exactly ONE  [data-testid="app-panel-slot"]    (was 2 on desktop — testid dup)
 *   - NO "Rendered more hooks than during the previous render" (nicolify lesson, D3/D4)
 *   - NO hydration mismatch error
 *   - axe wcag2aa: zero duplicate-id / landmark-unique violations
 *
 * Covered modes (the 3 the checkpoint requires): agentic-desktop · web-desktop · mobile.
 * Surfaces: lisa.staff (bug origin) + lisa.marca.identidad + the Valeria sidebar (shell-wide).
 *
 * spec_anchor: vitalia-shell-dual-mount-a11y-fix/03-arch.md § Bar de verificación (DONE)
 * downstream-regression-na: brand-local vitalia shell spec; no cross-brand consumers
 */

import { test, expect } from "../../auth.fixture";
import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

const DESKTOP = { width: 1440, height: 900 };
const MOBILE = { width: 390, height: 844 };

type ShellMode = "agentic" | "web";

/** Seed shellMode in localStorage BEFORE the app boots (matches routing-shell.fixture). */
async function seedShellMode(page: Page, mode: ShellMode): Promise<void> {
  await page.addInitScript((m: string) => {
    localStorage.setItem(
      "vitalia-shell-state",
      JSON.stringify({
        state: { shellMode: m, valeriaState: "full" },
        version: 0,
      }),
    );
  }, mode);
}

/** Attach a console listener that captures the two fatal classes for this fix. */
function captureFatalConsole(page: Page): { fatal: string[] } {
  const fatal: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (
      /rendered more hooks than during the previous render/i.test(text) ||
      /hydrat/i.test(text) // hydration mismatch — caught explicitly (auth.fixture filters it out)
    ) {
      fatal.push(text);
    }
  });
  page.on("pageerror", (err) => {
    const text = String(err?.message ?? err);
    if (
      /rendered more hooks than during the previous render/i.test(text) ||
      /hydrat/i.test(text)
    ) {
      fatal.push(text);
    }
  });
  return { fatal };
}

/** Wait until the shell <main> is present and the app-panel slot has rendered. */
async function waitForShell(page: Page): Promise<void> {
  await page.locator("#main-content").first().waitFor({ state: "attached", timeout: 30_000 });
  await page
    .locator('[data-testid="app-panel-slot"]')
    .first()
    .waitFor({ state: "attached", timeout: 30_000 });
  // settle: let any conditional re-render / hydration flush
  await page.waitForTimeout(400);
}

async function assertSingleStructure(
  page: Page,
  fatal: string[],
  label: string,
): Promise<void> {
  const mainCount = await page.locator("#main-content").count();
  const slotCount = await page
    .locator('[data-testid="app-panel-slot"]')
    .count();

  expect(mainCount, `${label}: exactly one <main id="main-content">`).toBe(1);
  expect(slotCount, `${label}: exactly one [data-testid="app-panel-slot"]`).toBe(1);
  expect(
    fatal,
    `${label}: no "more hooks"/hydration console errors`,
  ).toEqual([]);
}

test.describe("dual-mount fix LIVE — single <main> + single AppPanelSlot (ADR-008)", () => {
  test("agentic-desktop · lisa.staff: 1 main + 1 slot, console clean", async ({
    authedPage,
  }) => {
    const { fatal } = captureFatalConsole(authedPage);
    await seedShellMode(authedPage, "agentic");
    await authedPage.setViewportSize(DESKTOP);
    await authedPage.goto(`/${TENANT_ID}/lisa/staff`, {
      waitUntil: "domcontentloaded",
    });
    await waitForShell(authedPage);
    await assertSingleStructure(authedPage, fatal, "agentic-desktop");
  });

  test("web-desktop · lisa.marca.identidad: 1 main + 1 slot, console clean", async ({
    authedPage,
  }) => {
    const { fatal } = captureFatalConsole(authedPage);
    await seedShellMode(authedPage, "web");
    await authedPage.setViewportSize(DESKTOP);
    await authedPage.goto(`/${TENANT_ID}/lisa/marca/identidad`, {
      waitUntil: "domcontentloaded",
    });
    await waitForShell(authedPage);
    await assertSingleStructure(authedPage, fatal, "web-desktop");
  });

  test("mobile · lisa.staff: 1 main + 1 slot, console clean", async ({
    authedPage,
  }) => {
    const { fatal } = captureFatalConsole(authedPage);
    await seedShellMode(authedPage, "agentic");
    await authedPage.setViewportSize(MOBILE);
    await authedPage.goto(`/${TENANT_ID}/lisa/staff`, {
      waitUntil: "domcontentloaded",
    });
    await waitForShell(authedPage);
    await assertSingleStructure(authedPage, fatal, "mobile");
  });

  test("axe wcag2aa: zero duplicate-id / landmark-unique violations on the shell", async ({
    authedPage,
  }) => {
    await seedShellMode(authedPage, "agentic");
    await authedPage.setViewportSize(DESKTOP);
    await authedPage.goto(`/${TENANT_ID}/lisa/staff`, {
      waitUntil: "domcontentloaded",
    });
    await waitForShell(authedPage);

    const results = await new AxeBuilder({ page: authedPage })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    // The dual-mount bug produced duplicate id="main-content" + duplicate landmarks.
    // These rule families MUST be clean after the fix (the rest of the shell may have
    // pre-existing violations outside this story's scope — not gated here).
    const fixScoped = results.violations.filter((v) =>
      ["duplicate-id", "duplicate-id-aria", "landmark-unique", "landmark-no-duplicate-banner"].includes(
        v.id,
      ),
    );
    expect(
      fixScoped,
      `axe duplicate-id/landmark violations: ${JSON.stringify(
        fixScoped.map((v) => ({ id: v.id, nodes: v.nodes.length })),
      )}`,
    ).toEqual([]);
  });
});
