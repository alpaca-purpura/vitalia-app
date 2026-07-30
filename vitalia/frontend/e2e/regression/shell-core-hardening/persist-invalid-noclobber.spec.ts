// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * persist-invalid-noclobber.spec.ts — SC-18: estado inválido→fallback; reload no clobber (RN-4/RN-11)
 *
 * Verifica:
 *   1. Estado inválido en localStorage (valeriaOpen='bogus') → fallback a 'chat' (SC-18 sanitize).
 *   2. Reload con estado válido → no clobber (SSR skeleton no reescribe el valor).
 *   3. Version 0 (legacy) → migra a versión 1 (closed|chat).
 *
 * Real-backend. Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/persist-invalid-noclobber.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";
import { SHELL_STORAGE_KEY } from "../../fixtures/shell-hardening.fixture";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-18 — persist inválido→fallback + no-clobber SSR (RN-4/RN-11)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("valeriaOpen='bogus' → fallback a 'chat' (SC-18 sanitize)", async ({
    page,
    tenantId,
  }) => {
    // Seed invalid state (corrupt valeriaOpen)
    await page.addInitScript(
      ({ key }: { key: string }) => {
        localStorage.setItem(
          key,
          JSON.stringify({ state: { valeriaOpen: "bogus" }, version: 1 }),
        );
      },
      { key: SHELL_STORAGE_KEY },
    );

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Valeria should fall back to 'chat' (not crash)
    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen, "valeriaOpen='bogus' debe hacer fallback a 'chat'").toBe("chat");
  });

  test("reload no clobber: valeriaOpen='closed' persiste tras reload", async ({
    page,
    tenantId,
  }) => {
    // Seed closed state (valid)
    await page.addInitScript(
      ({ key }: { key: string }) => {
        localStorage.setItem(
          key,
          JSON.stringify({ state: { valeriaOpen: "closed" }, version: 1 }),
        );
      },
      { key: SHELL_STORAGE_KEY },
    );

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Reload — SSR skeleton MUST NOT clobber the user's 'closed' preference
    await page.reload();
    await pom.waitForShellReady();

    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen, "reload no debe clobber 'closed' (ADR-vitalia-006)").toBe("closed");
  });

  test("legacy version 0 (rail) → migra a 'chat' v1 (migration SC-18)", async ({
    page,
    tenantId,
  }) => {
    // Seed legacy state (version 0)
    await page.addInitScript(
      ({ key }: { key: string }) => {
        localStorage.setItem(
          key,
          JSON.stringify({
            state: { valeriaState: "rail", shellMode: "agentic" },
            version: 0,
          }),
        );
      },
      { key: SHELL_STORAGE_KEY },
    );

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Legacy 'rail' → new machine 'chat' (03-arch-fe § 1.2 migration)
    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen, "legacy 'rail' debe migrar a 'chat'").toBe("chat");
  });

  test("legacy version 0 (collapsed) → migra a 'closed' v1", async ({
    page,
    tenantId,
  }) => {
    await page.addInitScript(
      ({ key }: { key: string }) => {
        localStorage.setItem(
          key,
          JSON.stringify({
            state: { valeriaState: "collapsed", shellMode: "agentic" },
            version: 0,
          }),
        );
      },
      { key: SHELL_STORAGE_KEY },
    );

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen, "legacy 'collapsed' debe migrar a 'closed'").toBe("closed");
  });

  test("historyOpen nunca persiste abierto (RN-11)", async ({
    page,
    tenantId,
  }) => {
    // Simulate: someone manually injected historyOpen=true in localStorage
    await page.addInitScript(
      ({ key }: { key: string }) => {
        localStorage.setItem(
          key,
          JSON.stringify({
            state: { valeriaOpen: "chat", historyOpen: true },
            version: 1,
          }),
        );
      },
      { key: SHELL_STORAGE_KEY },
    );

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // historyOpen must be false after hydration (never persisted — RN-11)
    const historyOpen = await pom.getHistoryOpen();
    expect(historyOpen, "RN-11: historyOpen no se restaura aunque esté en localStorage").toBe(false);
  });
});
