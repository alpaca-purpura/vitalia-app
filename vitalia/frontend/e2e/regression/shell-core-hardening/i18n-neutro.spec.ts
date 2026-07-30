// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * i18n-neutro.spec.ts — SC-17: strings sin voseo en la UI del shell (spanish-text.md)
 *
 * Verifica que los strings user-facing del shell no contienen voseo rioplatense.
 * Patrones prohibidos: terminaciones en -ás/-és/-ís en imperativo, léxico marcado.
 *
 * Real-backend. Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/i18n-neutro.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

// Voseo patterns to check (from spanish-text.md)
const VOSEO_PATTERNS = [
  /\bsos\b/gi,
  /\btenés\b/gi,
  /\bpodés\b/gi,
  /\bmirá\b/gi,
  /\bdejá\b/gi,
  /\bponé\b/gi,
  /\busá\b/gi,
  /\belegí\b/gi,
  /\bagregá\b/gi,
  /\bconfigurá\b/gi,
  /\brevisá\b/gi,
  /\bguardá\b/gi,
  /\babrí\b/gi,
  /\bvolvé\b/gi,
  /\bcambiá\b/gi,
  /\bactivás\b/gi,
  /\bdesactivás\b/gi,
];

test.describe("SC-17 — strings neutro LatAm, sin voseo (spanish-text.md)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("shell UI: aria-labels del topbar/sidebar sin voseo", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Collect all aria-labels from the page
    const ariaLabels = await shellPage.evaluate(() => {
      const elements = Array.from(document.querySelectorAll("[aria-label]"));
      return elements.map((el) => el.getAttribute("aria-label") ?? "");
    });

    // Also collect button text
    const buttonTexts = await shellPage.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll("button"));
      return buttons.map((b) => b.textContent ?? "").filter(Boolean);
    });

    const allStrings = [...ariaLabels, ...buttonTexts];

    for (const pattern of VOSEO_PATTERNS) {
      for (const str of allStrings) {
        const match = str.match(pattern);
        if (match) {
          expect.fail(
            `Voseo detectado en UI string: "${match[0]}" en "${str}" (patrón: ${pattern.source})`,
          );
        }
      }
    }
  });

  test("topbar labels: correctos y sin voseo", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Check ThemeToggle label
    const themeLabel = await pom.themeToggle.getAttribute("aria-label");
    if (themeLabel) {
      for (const pattern of VOSEO_PATTERNS) {
        expect(themeLabel).not.toMatch(pattern);
      }
    }

    // Check collapse button label
    await pom.collapseToStripBtn.waitFor({ state: "visible", timeout: 10_000 });
    const collapseLabel = await pom.collapseToStripBtn.getAttribute("aria-label");
    if (collapseLabel) {
      for (const pattern of VOSEO_PATTERNS) {
        expect(collapseLabel).not.toMatch(pattern);
      }
    }
  });
});
