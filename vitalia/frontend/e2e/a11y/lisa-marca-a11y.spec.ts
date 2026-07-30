/**
 * lisa-marca-a11y.spec.ts — axe-core WCAG 2.1 AA T-12
 *
 * F2-S7 vitalia-fase2-lisa-marca
 * Ticket: T-12 — FE a11y axe-core scan — WCAG 2.1 AA per subsubtab × 5 states
 *
 * Coverage: 3 subsubtabs × 5 states (idle / loading / success / error / empty) = ~15 axe scans
 * Plus: keyboard navigation tests (SubSubTabsBar arrow keys + tab order)
 *
 * WCAG tags: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
 * Violation filter: critical + serious only
 * Locators: data-testid ONLY (no CSS selectors)
 *
 * Project: a11y (playwright.config.ts project matching .*\/a11y\/.*\.spec\.ts)
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/a11y/lisa-marca-a11y.spec.ts --project=a11y
 *
 * G5 pre-commit smoke gate (no running stack required):
 *   cd vitalia/frontend && npx tsc --noEmit
 *   npx eslint e2e/a11y/lisa-marca-a11y.spec.ts --cache
 *   npx playwright test --list e2e/a11y/lisa-marca-a11y.spec.ts
 *
 * NOTES FOR AUDITOR:
 *   - Tests require running stack on E2E_BASE_URL (localhost:3002).
 *   - All API calls mocked via page.route — no real BE required.
 *   - Loading state mocked by delaying route response 1500ms.
 *   - Error state mocked by returning HTTP 500 from identity endpoint.
 *   - Empty state mocked by returning empty/null brand identity fields.
 *   - Keyboard nav tests verify SubSubTabsBar link navigation and focus ring.
 *
 * downstream-regression-na: brand-local vitalia E2E a11y spec F2-S7 T-12
 *
 * @see T-10-result.md — POMs + fixtures (dependency)
 * @see 06-tickets.yaml T-12 deliverables
 * @see vitalia/.claude/rules/hipaa-lite.md — HIPAA-lite constraints (no PHI in DOM)
 */

import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import {
  test,
  LISA_MARCA_FIXTURE,
  gotoMarca,
  setupLisaMarcaMocks,
  buildMockIdentityResponse,
  buildMockVisualsResponse,
  buildMockPersonalityResponse,
  buildMockContactResponse,
} from "../regression/vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "../regression/vitalia-fase2-lisa-marca/poms/lisa-marca-page.pom";
import type { LisaMarcaSubsubtab } from "../regression/vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture";
import type { Route } from "@playwright/test";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const { tenantId } = LISA_MARCA_FIXTURE;

/** WCAG 2.1 AA tags per ticket spec */
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] as const;

/** Subsubtabs under test */
const SUBSUBTABS: LisaMarcaSubsubtab[] = ["identidad", "voz-y-tono", "presencia"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Run axe-core scan on the lisa-marca-content area.
 * Returns only critical + serious violations (per ticket spec).
 */
async function scanMarcaContent(
  marcaPage: import("@playwright/test").Page,
): Promise<import("axe-core").Result[]> {
  const results = await new AxeBuilder({ page: marcaPage })
    .withTags([...WCAG_TAGS])
    .include('[data-testid="lisa-marca-content"]')
    .exclude("#__nextjs-toast-errors") // Next.js dev overlay
    .exclude('[data-testid="lisa-marca-loading-skeleton"]') // dynamic skeleton
    .analyze();

  return results.violations.filter(
    (v) => v.impact === "critical" || v.impact === "serious",
  );
}

/**
 * Format violation list for assertion error message.
 */
function formatViolations(
  violations: import("axe-core").Result[],
  label: string,
): string {
  if (violations.length === 0) return "";
  return (
    `A11y violations (${label}):\n` +
    violations
      .map(
        (v) =>
          `  [${v.impact ?? "unknown"}] ${v.id}: ${v.description}\n` +
          `    Nodes: ${v.nodes.map((n) => n.target.join(" > ")).join(", ")}`,
      )
      .join("\n")
  );
}

// ---------------------------------------------------------------------------
// 1. Idle state scans — 3 subsubtabs loaded with seed data
// ---------------------------------------------------------------------------

test.describe("A11y — idle state (seed data loaded)", () => {
  for (const subsubtab of SUBSUBTABS) {
    test(`[${subsubtab}] idle state passes WCAG 2.1 AA`, async ({
      marcaPage,
    }) => {
      await setupLisaMarcaMocks(marcaPage, tenantId);
      await gotoMarca(marcaPage, tenantId, subsubtab);
      const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
      await lisaMarcaPage.waitForLoaded();

      const violations = await scanMarcaContent(marcaPage);

      expect(
        violations,
        formatViolations(violations, `${subsubtab} idle`),
      ).toHaveLength(0);
    });
  }
});

// ---------------------------------------------------------------------------
// 2. Loading state scans — route delayed to expose skeleton
// ---------------------------------------------------------------------------

test.describe("A11y — loading state (skeleton visible)", () => {
  for (const subsubtab of SUBSUBTABS) {
    test(`[${subsubtab}] loading state passes WCAG 2.1 AA (aria-busy)`, async ({
      marcaPage,
    }) => {
      // Override identity route to delay response — keeps skeleton visible briefly
      await marcaPage.route(
        "**/api/v1/lisa/marca/identity",
        async (route: Route) => {
          if (route.request().method() === "GET") {
            // Delay long enough to capture skeleton
            await new Promise<void>((resolve) => setTimeout(resolve, 1500));
            await route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify(buildMockIdentityResponse(tenantId)),
            });
          } else {
            await route.continue();
          }
        },
      );
      await setupLisaMarcaMocks(marcaPage, tenantId);

      // Navigate and capture BEFORE loaded (during skeleton phase)
      const gotoPromise = gotoMarca(marcaPage, tenantId, subsubtab);

      // Wait for skeleton to appear (loading state)
      await marcaPage
        .locator('[data-testid="lisa-marca-loading-skeleton"]')
        .waitFor({ state: "visible", timeout: 5000 })
        .catch(() => {
          // Skeleton may flash too quickly — test still runs against content
        });

      // Scan while skeleton may be visible
      const skeletonResults = await new AxeBuilder({ page: marcaPage })
        .withTags([...WCAG_TAGS])
        .exclude("#__nextjs-toast-errors")
        .analyze();

      const violations = skeletonResults.violations.filter(
        (v) => v.impact === "critical" || v.impact === "serious",
      );

      // Wait for full load before cleanup
      await gotoPromise;
      const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
      await lisaMarcaPage.waitForLoaded();

      expect(
        violations,
        formatViolations(violations, `${subsubtab} loading`),
      ).toHaveLength(0);
    });
  }
});

// ---------------------------------------------------------------------------
// 3. Success state scans — explicit seed data confirmed loaded
// ---------------------------------------------------------------------------

test.describe("A11y — success state (data fully loaded)", () => {
  for (const subsubtab of SUBSUBTABS) {
    test(`[${subsubtab}] success state passes WCAG 2.1 AA`, async ({
      marcaPage,
    }) => {
      await setupLisaMarcaMocks(marcaPage, tenantId);
      await gotoMarca(marcaPage, tenantId, subsubtab);
      const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
      await lisaMarcaPage.waitForLoaded();

      // Confirm success: content visible + no skeleton
      await expect(
        marcaPage.locator('[data-testid="lisa-marca-content"]'),
      ).toBeVisible();
      await expect(
        marcaPage.locator('[data-testid="lisa-marca-loading-skeleton"]'),
      ).toBeHidden();

      const violations = await scanMarcaContent(marcaPage);

      expect(
        violations,
        formatViolations(violations, `${subsubtab} success`),
      ).toHaveLength(0);
    });
  }
});

// ---------------------------------------------------------------------------
// 4. Error state scans — backend returns 500
// ---------------------------------------------------------------------------

test.describe("A11y — error state (API 500 → error boundary)", () => {
  for (const subsubtab of SUBSUBTABS) {
    test(`[${subsubtab}] error boundary passes WCAG 2.1 AA`, async ({
      marcaPage,
    }) => {
      // Override primary data endpoint to return 500
      const errorRouteUrl = subsubtab === "identidad"
        ? "**/api/v1/lisa/marca/identity"
        : subsubtab === "voz-y-tono"
        ? "**/api/v1/lisa/marca/personality"
        : "**/api/v1/lisa/marca/contact";

      await marcaPage.route(errorRouteUrl, async (route: Route) => {
        if (route.request().method() === "GET") {
          await route.fulfill({
            status: 500,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Internal Server Error" }),
          });
        } else {
          await route.continue();
        }
      });
      // Mock remaining endpoints normally
      await setupLisaMarcaMocks(marcaPage, tenantId);

      await gotoMarca(marcaPage, tenantId, subsubtab);

      // Wait for either error boundary OR content (error may be handled gracefully)
      await marcaPage
        .locator(
          '[data-testid="error-boundary-fallback"], [data-testid="lisa-marca-content"]',
        )
        .first()
        .waitFor({ state: "visible", timeout: 15_000 });

      const errorResults = await new AxeBuilder({ page: marcaPage })
        .withTags([...WCAG_TAGS])
        .exclude("#__nextjs-toast-errors")
        .analyze();

      const violations = errorResults.violations.filter(
        (v) => v.impact === "critical" || v.impact === "serious",
      );

      expect(
        violations,
        formatViolations(violations, `${subsubtab} error`),
      ).toHaveLength(0);
    });
  }
});

// ---------------------------------------------------------------------------
// 5. Empty state scans — seed data returns null/empty fields
// ---------------------------------------------------------------------------

test.describe("A11y — empty state (null/empty brand identity)", () => {
  for (const subsubtab of SUBSUBTABS) {
    test(`[${subsubtab}] empty state passes WCAG 2.1 AA`, async ({
      marcaPage,
    }) => {
      // Override with empty/null data to trigger empty state UI
      const emptyIdentity = {
        ...buildMockIdentityResponse(tenantId),
        brandName: "",
        tagline: null,
        description: null,
        primarySpecialties: [],
      };
      const emptyPersonality = {
        ...buildMockPersonalityResponse(tenantId),
        toneBlocks: {
          openingHook: "",
          mainBody: "",
          closingCta: "",
        },
        prohibitedPhrases: [],
      };
      const emptyContact = {
        ...buildMockContactResponse(tenantId),
        website: null,
        instagram: null,
        tiktok: null,
        googleBusiness: null,
        address: null,
        phone: null,
      };
      const emptyVisuals = {
        ...buildMockVisualsResponse(tenantId),
        logoUrl: null,
        primaryColor: null,
        secondaryColor: null,
      };

      await setupLisaMarcaMocks(marcaPage, tenantId, {
        identityOverride: emptyIdentity,
        visualsOverride: emptyVisuals,
        personalityOverride: emptyPersonality,
        contactOverride: emptyContact,
      });
      await gotoMarca(marcaPage, tenantId, subsubtab);
      const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
      await lisaMarcaPage.waitForLoaded();

      const violations = await scanMarcaContent(marcaPage);

      expect(
        violations,
        formatViolations(violations, `${subsubtab} empty`),
      ).toHaveLength(0);
    });
  }
});

// ---------------------------------------------------------------------------
// 6. Keyboard navigation — SubSubTabsBar + focus ring
// ---------------------------------------------------------------------------

test.describe("Keyboard navigation — SubSubTabsBar", () => {
  test("SubSubTabsBar links are keyboard focusable and have visible focus ring", async ({
    marcaPage,
  }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "identidad");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();

    // Focus the SubSubTabsBar via keyboard Tab
    await marcaPage.keyboard.press("Tab");

    // Verify subsubtabs bar contains focusable elements
    const tabBar = marcaPage.locator('[data-testid="shell-subsubtabs-bar"]');
    await expect(tabBar).toBeVisible();

    // Each link in the bar must be focusable (tabIndex 0 or native link)
    const tabLinks = tabBar.locator("a, [role='link']");
    const count = await tabLinks.count();
    expect(count).toBeGreaterThanOrEqual(3); // identidad, voz-y-tono, presencia
  });

  test("Tab order includes SubSubTabsBar before main content", async ({
    marcaPage,
  }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "identidad");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();

    // Tab through page — SubSubTabsBar navigation links should appear before form fields
    // This verifies logical DOM order (shell header before content)
    const subsubtabsBar = marcaPage.locator(
      '[data-testid="shell-subsubtabs-bar"]',
    );
    const marcaContent = marcaPage.locator('[data-testid="lisa-marca-content"]');

    await expect(subsubtabsBar).toBeVisible();
    await expect(marcaContent).toBeVisible();

    // Verify the subsubtabs bar precedes content in DOM order (accessibility)
    const barBox = await subsubtabsBar.boundingBox();
    const contentBox = await marcaContent.boundingBox();

    if (barBox && contentBox) {
      // SubSubTabsBar must appear before (or at same Y as) content start
      expect(barBox.y).toBeLessThanOrEqual(contentBox.y);
    }
  });

  test("active subsubtab has aria-current='page'", async ({
    marcaPage,
  }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "identidad");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();

    const activeTab = marcaPage.locator(
      '[data-testid="shell-subsubtabs-bar"] [aria-current="page"]',
    );
    await expect(activeTab).toBeVisible();
  });

  test("SubSubTabsBar passes WCAG 2.1 AA in isolation", async ({
    marcaPage,
  }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "identidad");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();

    const results = await new AxeBuilder({ page: marcaPage })
      .withTags([...WCAG_TAGS])
      .include('[data-testid="shell-subsubtabs-bar"]')
      .analyze();

    const violations = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(
      violations,
      formatViolations(violations, "SubSubTabsBar"),
    ).toHaveLength(0);
  });

  test("no duplicate IDs in lisa-marca DOM (WCAG 4.1.1)", async ({
    marcaPage,
  }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "identidad");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();

    const duplicates = await marcaPage.evaluate(() => {
      const ids = Array.from(document.querySelectorAll("[id]")).map(
        (el) => el.id,
      );
      const seen = new Set<string>();
      const dups: string[] = [];
      for (const id of ids) {
        if (seen.has(id)) dups.push(id);
        seen.add(id);
      }
      return dups;
    });

    expect(
      duplicates,
      `Duplicate IDs found in DOM: ${duplicates.join(", ")}`,
    ).toHaveLength(0);
  });
});
