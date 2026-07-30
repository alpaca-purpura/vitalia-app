// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * no-web-toggle.spec.ts — SC-2: shell siempre agéntico, sin modo web (RN-1 · AC-1)
 *
 * Verifica que:
 *   1. El ShellModeToggle (data-testid="shell-mode-toggle") NO existe en el DOM.
 *   2. La UI no tiene referencia a shellMode alguno.
 *   3. No hay botón/chip con texto "web" o "agentic" como modo toggle.
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/no-web-toggle.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-2 — shell sin modo web (RN-1 · AC-1)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("ShellModeToggle (data-testid=shell-mode-toggle) ausente en el DOM", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // AC-1: ShellModeToggle eliminated — must be 0 in DOM
    const toggleCount = await shellPage
      .getByTestId("shell-mode-toggle")
      .count();
    expect(toggleCount, "ShellModeToggle debe ser 0 en el DOM (AC-1)").toBe(0);
  });

  test("no hay botón/chip con texto 'Modo web' o 'Modo agéntico'", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // No chip/button should reference the old toggle concept
    const webToggle = shellPage.locator(
      'button[aria-label*="web" i], button[aria-label*="agéntico" i]',
    );
    await expect(webToggle).toHaveCount(0);
  });

  test("topbar no contiene chip 'web'/'agentic' modo-switch", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const topBarHtml = await pom.topBar.innerHTML();
    // No reference to shellMode chip text
    expect(topBarHtml).not.toMatch(/modo web|modo agéntico|shellmode/i);
  });
});
