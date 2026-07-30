/**
 * accessibility-scan.smoke.spec.ts — V-V-20
 *
 * Validator: V-V-20 — Spec §10 Accessibility (axe-core, 0 critical/serious violations)
 * Fixture: aurora-dental-ar (representative tenant)
 * Flow: axe scan on key pages → critical + serious violations = 0
 *
 * Requires: @axe-core/playwright (install: npm i -D @axe-core/playwright)
 * If package unavailable: graceful skip with clear error message.
 */
import { test, expect } from "../../../fixtures/aurora-dental-ar.fixture";

// Graceful import — @axe-core/playwright may not be installed
let AxeBuilder: (typeof import("@axe-core/playwright"))["default"] | null =
  null;

test.describe("Accessibility — Vitalia UI axe-core scan (Aurora AR)", () => {
  test.beforeAll(async () => {
    try {
      const axeModule = await import("@axe-core/playwright");
      AxeBuilder = axeModule.default;
    } catch {
      // Package not installed — tests will be skipped with message
      AxeBuilder = null;
    }
  });

  test("V-V-20: brand studio has 0 critical/serious a11y violations", async ({
    auroraPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    await page.goto("/brand-studio");
    await page.waitForLoadState("domcontentloaded");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    if (criticalOrSerious.length > 0) {
      const details = criticalOrSerious
        .map(
          (v) =>
            `[${v.impact?.toUpperCase()}] ${v.id}: ${v.description}\n  Nodes: ${v.nodes.map((n) => n.target.join(", ")).join("; ")}`,
        )
        .join("\n");
      throw new Error(
        `Brand Studio has ${criticalOrSerious.length} critical/serious a11y violations:\n${details}`,
      );
    }

    expect(criticalOrSerious).toHaveLength(0);
  });

  test("V-V-20: onboarding has 0 critical/serious a11y violations", async ({
    auroraPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    await page.goto("/onboarding");
    await page.waitForLoadState("domcontentloaded");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(criticalOrSerious).toHaveLength(0);
  });

  test("V-V-20: compliance dashboard has 0 critical/serious a11y violations", async ({
    auroraPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    await page.goto("/medical-compliance");
    await page.waitForLoadState("domcontentloaded");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(criticalOrSerious).toHaveLength(0);
  });

  test("V-V-20: booking page has 0 critical/serious a11y violations", async ({
    auroraPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright not installed — run: npm i -D @axe-core/playwright",
      );
      return;
    }

    await page.goto("/citas/nueva");
    await page.waitForLoadState("domcontentloaded");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(criticalOrSerious).toHaveLength(0);
  });
});
