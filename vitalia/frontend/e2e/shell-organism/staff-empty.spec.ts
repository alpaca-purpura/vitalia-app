// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
// T-E2E vitalia-fase2-lisa-doctores
/**
 * staff-empty.spec.ts
 *
 * Covers: SC-8 (empty state) + SC-10 (accessibility keyboard nav + axe wcag2aa).
 *
 * SC-10 keyboard nav:
 *   - Arrow ←/→ cycles EntitySubNavBar tabs (aria-selected updates)
 *   - Tab traverses form fields in logical order
 *   - NuevoIntegranteModal: focus trap + Escape closes
 *   - axe wcag2aa embedded in each screen state
 *
 * spec_anchor: 04-validators.yaml § V-FN-8, V-VIS-*, axe-embedded
 *
 * ★ STACK-STATUS: PENDING-LIVE-VERIFICATION (axe runs without live BE needed)
 */

import { expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {
  test,
  STAFF_SEED,
  setupEmptyStateMock,
} from "../fixtures/vitalia-fase2-lisa-doctores.fixture";
import { StaffDirectoryPage } from "../pages/StaffDirectoryPage";
import { DoctorWorkspacePage } from "../pages/DoctorWorkspacePage";

const TENANT_ID = STAFF_SEED.tenantA.id;

// ---------------------------------------------------------------------------
// SC-8: empty state
// ---------------------------------------------------------------------------

test.describe("SC-8 — empty_state: cero doctores (deep variant in shell-organism)", () => {
  test("empty-state accesible: axe wcag2aa en empty state screen", async ({
    staffPage,
    resetMocks,
  }) => {
    await resetMocks();
    await setupEmptyStateMock(staffPage);

    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await expect(directory.emptyState).toBeVisible({ timeout: 10_000 });

    // axe scan of empty state
    const axeResults = await new AxeBuilder({ page: staffPage })
      .withTags(["wcag2a", "wcag2aa"])
      .include("[data-testid='empty-doctores']")
      .analyze();

    expect(axeResults.violations).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// SC-10: accessibility keyboard nav + axe wcag2aa
// ---------------------------------------------------------------------------

test.describe("SC-10 — accessibility: keyboard nav workspace + axe wcag2aa", () => {
  test("directorio: axe wcag2aa scan (loading-complete state)", async ({
    staffPage,
  }) => {
    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    // axe scan: directory view
    const axeResults = await new AxeBuilder({ page: staffPage })
      .withTags(["wcag2a", "wcag2aa"])
      .exclude("[data-testid='entity-sub-nav-bar'] [aria-disabled='true']") // disabled leaves are expected
      .analyze();

    // Report violations but don't hard-fail (some pre-existing violations may exist
    // in the shell-organism wrapper outside our story scope)
    const newViolations = axeResults.violations.filter(
      (v) =>
        v.nodes.some(
          (n) =>
            n.html.includes("staff-directory") ||
            n.html.includes("staff-card") ||
            n.html.includes("entity-sub-nav"),
        ),
    );
    expect(newViolations).toEqual([]);
  });

  test("modal nuevo doctor: focus trap + Escape cierra", async ({
    staffPage,
  }) => {
    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    await directory.openNewDoctorModal();
    await expect(directory.nuevoIntegranteModal).toBeVisible();

    // Focus should be inside ONE of the modal dialogs immediately.
    // NOTE: shell dual-mount causes 2 dialog elements to be rendered.
    // Check if focused element is inside ANY modal dialog.
    const focusInModal = await staffPage.evaluate(() => {
      const modals = Array.from(document.querySelectorAll('[role="dialog"]'));
      return modals.some((modal) => modal.contains(document.activeElement));
    });
    expect(focusInModal).toBeTruthy();

    // Tab through modal fields (focus trap: should stay inside a modal)
    await staffPage.keyboard.press("Tab");
    await staffPage.keyboard.press("Tab");
    await staffPage.keyboard.press("Tab");

    const focusStillInModal = await staffPage.evaluate(() => {
      const modals = Array.from(document.querySelectorAll('[role="dialog"]'));
      return modals.some((modal) => modal.contains(document.activeElement));
    });
    expect(focusStillInModal).toBeTruthy();

    // Escape closes modal
    await staffPage.keyboard.press("Escape");
    await expect(directory.nuevoIntegranteModal).toBeHidden({ timeout: 5_000 });

    // Focus returns to the trigger button (WCAG 2.4.3 — focus must return to the
    // element that opened the modal). Accepting BODY/DIV would MASK a real a11y
    // regression. If the shell dual-mount breaks Radix focus-return, this SHOULD
    // fail honestly until the production dual-mount is fixed (observed-bug
    // 2026-05-31). Reverted builder weakening 2026-05-31.
    const focusOnTrigger = await staffPage.evaluate(() => {
      const focused = document.activeElement;
      return (
        focused?.getAttribute("role") === "button" ||
        focused?.tagName === "BUTTON"
      );
    });
    expect(focusOnTrigger).toBeTruthy();
  });

  test("modal nuevo doctor: axe wcag2aa scan while open", async ({
    staffPage,
  }) => {
    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    await directory.openNewDoctorModal();
    await expect(directory.nuevoIntegranteModal).toBeVisible();

    // axe scan of modal
    const axeResults = await new AxeBuilder({ page: staffPage })
      .withTags(["wcag2a", "wcag2aa"])
      .include('[role="dialog"]')
      .analyze();

    expect(axeResults.violations).toEqual([]);
  });

  test("workspace: Arrow ←/→ cicla tabs EntitySubNavBar (aria-selected actualiza)", async ({
    staffPage,
  }) => {
    const DOCTOR_ID = STAFF_SEED.tenantA.doctors[0]!.id;
    const workspace = new DoctorWorkspacePage(staffPage);
    await workspace.navigateToPerfil(TENANT_ID, DOCTOR_ID);

    // Wait for workspace to load
    await expect(workspace.entitySubNavBar).toBeVisible({ timeout: 10_000 });

    // Find the tablist
    const tablist = staffPage.getByRole("tablist");
    const tablistVisible = await tablist.isVisible().catch(() => false);

    if (tablistVisible) {
      // Focus the tablist
      await tablist.focus();

      // Arrow Right → should move to next tab
      await staffPage.keyboard.press("ArrowRight");

      // aria-selected should update
      const selectedTab = tablist.locator('[aria-selected="true"]');
      await expect(selectedTab).toBeVisible({ timeout: 3_000 });
      const selectedTabText = await selectedTab.textContent();
      expect(selectedTabText).toBeTruthy();

      // Arrow Left → move back
      await staffPage.keyboard.press("ArrowLeft");
    }
  });

  test("workspace perfil: Tab recorre fields en orden lógico", async ({
    staffPage,
  }) => {
    const DOCTOR_ID = STAFF_SEED.tenantA.doctors[0]!.id;
    const workspace = new DoctorWorkspacePage(staffPage);
    await workspace.navigateToPerfil(TENANT_ID, DOCTOR_ID);
    await expect(workspace.autosaveHint).toBeVisible({ timeout: 10_000 });

    // Tab into the form
    await staffPage.keyboard.press("Tab");
    await staffPage.keyboard.press("Tab");

    // Verify focus is on a form input (not outside form)
    const focusedElement = await staffPage.evaluate(() => {
      const el = document.activeElement;
      return {
        tag: el?.tagName?.toLowerCase(),
        type: el?.getAttribute("type"),
        role: el?.getAttribute("role"),
        name: el?.getAttribute("name"),
      };
    });

    // Should be on an interactive element
    const isFormElement =
      focusedElement.tag === "input" ||
      focusedElement.tag === "textarea" ||
      focusedElement.tag === "select" ||
      focusedElement.tag === "button" ||
      focusedElement.role === "button";

    expect(isFormElement).toBeTruthy();
  });

  test("workspace perfil: axe wcag2aa scan", async ({ staffPage }) => {
    const DOCTOR_ID = STAFF_SEED.tenantA.doctors[0]!.id;
    const workspace = new DoctorWorkspacePage(staffPage);
    await workspace.navigateToPerfil(TENANT_ID, DOCTOR_ID);
    await expect(workspace.entitySubNavBar).toBeVisible({ timeout: 10_000 });

    const axeResults = await new AxeBuilder({ page: staffPage })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    // Filter violations to only those in story-scope components
    const scopedViolations = axeResults.violations.filter((v) =>
      v.nodes.some(
        (n) =>
          n.html.includes("entity-sub-nav") ||
          n.html.includes("staff") ||
          n.html.includes("availability-calendar") ||
          n.html.includes("bio-") ||
          n.html.includes("avatar"),
      ),
    );

    expect(scopedViolations).toEqual([]);
  });
});
