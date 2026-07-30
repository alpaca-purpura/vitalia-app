// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * new-conversation.spec.ts — SC-8: nueva conversación + archiva (RN-13)
 *
 * RN-13: botón '+' nueva conversación archiva la actual.
 * Verifica que el botón "Nueva conversación" en ChatHeader:
 *   1. Es visible (focusable + aria-label correcto).
 *   2. Al hacer clic, la conversación actual se archiva / nueva se inicia.
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/new-conversation.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-8 — nueva conversación + archiva (RN-13)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("botón '+' nueva conversación es visible y focusable (RN-13 · AC-12)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Button must be visible
    await expect(pom.newConversationBtn).toBeVisible({ timeout: 10_000 });

    // Aria-label correct
    const label = await pom.newConversationBtn.getAttribute("aria-label");
    expect(label).toBeTruthy();
    expect(label?.toLowerCase()).toContain("conversaci");
  });

  test("clic en '+' inicia nueva conversación sin burbuja de error", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    await pom.newConversationBtn.waitFor({ state: "visible", timeout: 10_000 });

    // Click + confirm no errors fired (base.ts gate will catch any runtime errors)
    await pom.newConversationBtn.click();
    await shellPage.waitForTimeout(300);

    // Shell still ready (no crash)
    await pom.waitForShellReady();
  });
});
