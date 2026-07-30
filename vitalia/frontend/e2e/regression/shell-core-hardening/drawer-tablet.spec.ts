// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * drawer-tablet.spec.ts — SC-10: mobile/tablet drawer (viewport 800px)
 *
 * En viewport <1024px (tablet/mobile), el shell muestra:
 *   - El hamburger button en el topbar.
 *   - Al clic, abre ValeriaSidebar como role=dialog (drawer).
 *   - No hay panel splitter lateral.
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/drawer-tablet.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const TABLET_VIEWPORT = { width: 800, height: 1024 };

test.describe("SC-10 — mobile/tablet drawer (viewport 800px)", () => {
  test.use({ viewport: TABLET_VIEWPORT });

  test("hamburger visible en tablet viewport", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    // Wait for topbar to hydrate
    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    const hamburger = shellPage.getByTestId("topbar-hamburger");
    await expect(hamburger).toBeVisible({ timeout: 10_000 });
  });

  test("clic hamburger abre drawer (role=dialog)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    await pom.openMobileDrawerViaBurger();

    const isOpen = await pom.isMobileDrawerOpen();
    expect(isOpen, "drawer debe abrirse como role=dialog").toBe(true);
  });

  test("cerrar drawer: botón X cierra el dialog", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    await pom.openMobileDrawerViaBurger();
    await pom.closeMobileDrawer();

    const isOpen = await pom.isMobileDrawerOpen();
    expect(isOpen, "drawer debe estar cerrado tras clic X").toBe(false);
  });

  test("no hay resize handle en tablet (mobile = drawer, no splitter)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    const hasHandle = await pom.isResizeHandleVisible();
    // Tablet (<1024px) should not show the desktop resize handle
    expect(hasHandle, "no debe haber resize handle en tablet").toBe(false);
  });
});
