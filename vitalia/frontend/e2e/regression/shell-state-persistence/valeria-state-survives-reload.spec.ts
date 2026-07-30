/**
 * valeria-state-survives-reload.spec.ts — SC-1/SC-2/SC-3: state persistence through reload.
 *
 * vitalia-shell-state-persistence T-5
 *
 * Gherkin coverage (01-spec.md):
 *   SC-1: valeriaState='rail' survives reload — localStorage still holds 'rail', store reads rail.
 *   SC-2: shellMode='web' survives reload.
 *   SC-3 (adversarial): 'full' (the default) is NEVER written to localStorage when 'rail'
 *         was the saved value — the exact clobbering bug fixed by createSsrSafePersistedStore.
 *
 * Validator (04-validators.yaml):
 *   val-fn-e2e-survives-reload (must_pass: true)
 *
 * Project: smoke
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-state-persistence/valeria-state-survives-reload.spec.ts \
 *     --project=smoke
 *
 * IMPORTANT — addInitScript semantics:
 *   Playwright's addInitScript runs on EVERY navigation in the page context, including reloads.
 *   This means setValeriaStateViaStore()+reload conflicts with fixture seeds (fixture seeds
 *   'full' on reload via addInitScript). The correct test pattern is:
 *
 *   1. Use the fixture that matches the target state (valeriaRailPage → seeds 'rail' on every nav)
 *   2. Navigate ONCE with addInitScript seeding the target value
 *   3. After hydration, verify the store read the correct value (not clobbered to default)
 *
 *   If the bug were present, even with addInitScript('rail'), the persist middleware would
 *   write 'full' (default) DURING hydration, overwriting the 'rail' in localStorage.
 *   The SSR-safe factory prevents this write (setItem NO-OP pre-hydration).
 *
 * Implementation assumptions (confirmed by reading source T-1..T-4):
 *   - SHELL_STORAGE_KEY = 'vitalia-shell-state' (shell-store.ts)
 *   - State shape: { state: { valeriaState, shellMode, mobileDrawerOpen }, version: 0 }
 *   - valeriaRailPage fixture: seeds valeriaState='rail' + shellMode='agentic' via addInitScript
 *   - instrumentSetItem() / getSetItemWrites() on ShellLayoutPage (extended T-5)
 *   - Test page: /test-stack/shell-layout (no Clerk prod route required)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/shell-theme.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const SHELL_STORAGE_KEY = "vitalia-shell-state";

test.describe("SC-1/SC-2/SC-3 — state persistence through reload (vitalia-shell-state-persistence)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  // ── SC-1: valeriaState='rail' is preserved after SSR+hydration ────────────
  //
  // Test strategy: valeriaRailPage fixture seeds 'rail' via addInitScript BEFORE navigation.
  // addInitScript runs before page scripts → localStorage has 'rail' before store initializes.
  // If the bug were present: store would write 'full' (default) during SSR/hydration → 'rail' lost.
  // With the fix: setItem is NO-OP pre-hydration → 'rail' is preserved until rehydrate() fires.
  // After rehydrate(): store reads 'rail' from localStorage → localStorage keeps 'rail'.

  test("SC-1 valeriaState 'rail' survives SSR+hydration cycle (not clobbered to default 'full')", async ({
    valeriaRailPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(valeriaRailPage);
    // Navigate with valeriaState='rail' pre-seeded (valeriaRailPage fixture)
    await pom.gotoShell(tenantId);
    await pom.waitForShellReady();

    // After navigation+hydration the store MUST read the seeded value ('rail'),
    // not the default ('full'). With the fix, no clobber write occurs.
    const state = await pom.getStorageState();
    expect(state?.valeriaState).toBe("rail");
  });

  // ── SC-2: shellMode='web' is preserved after SSR+hydration ───────────────
  //
  // NOTE on D2 auto-coupling (ValeriaSidebar.tsx useEffect):
  //   valeriaState='collapsed' → setShellMode('web')
  //   valeriaState='rail'|'full' → setShellMode('agentic')
  //
  // This means shellMode='web' is only stable when valeriaState='collapsed'.
  // When valeriaState='full'+'shellMode=web' is seeded, D2 writes 'agentic' post-hydration.
  // SC-2 verifies that localStorage correctly persists shellMode='web' when
  // seeded with valeriaState='collapsed' (the stable pairing per D2 coupling).
  //
  // The spec says "shellMode='web' survives reload" — tested with collapsed state
  // which is the real-world use case (user closed Valeria → web mode).

  test("SC-2 shellMode 'web' survives SSR+hydration cycle (collapsed+web — stable D2 pairing)", async ({
    authedPage,
    tenantId,
  }) => {
    // Seed shellMode='web' + valeriaState='collapsed' (D2-stable pairing):
    // ValeriaSidebar D2 effect: collapsed → setShellMode('web') — aligned.
    // This is the real-world state: user closed Valeria panel → web mode.
    await authedPage.addInitScript(
      ({ key, value }) => {
        localStorage.setItem(key, value);
      },
      {
        key: SHELL_STORAGE_KEY,
        value: JSON.stringify({
          state: {
            valeriaState: "collapsed",
            shellMode: "web",
            mobileDrawerOpen: false,
          },
          version: 0,
        }),
      },
    );

    const pom = new ShellLayoutPage(authedPage);
    await pom.gotoShell(tenantId);
    // TopBar visible is enough — no waitForShellReady needed for web mode
    // (data-shell-ready is only on agentic main)
    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    // Wait for D2 effect to settle
    await authedPage.waitForTimeout(300);

    // shellMode 'web' must survive hydration (aligned with D2 coupling: collapsed→web)
    const state = await pom.getStorageState();
    expect(state?.shellMode).toBe("web");
  });

  // ── SC-3: 'full' (default) NEVER written when 'rail' was saved ────────────
  //
  // This is the adversarial bug check. The SSR/pre-hydration window used to
  // clobber localStorage by writing the default ('full') before rehydrate ran.
  // createSsrSafePersistedStore fixes this with a setItem NO-OP until hydration.
  //
  // Test strategy:
  // 1. Override localStorage with 'rail' via addInitScript before navigation
  // 2. Install setItem spy after page load (captures SSR+hydration writes)
  // 3. Wait for full hydration
  // 4. Assert: ZERO writes of valeriaState='full' to the shell storage key

  test("SC-3 'full' is never written to storage when 'rail' was saved (adversarial bug check)", async ({
    valeriaRailPage,
    tenantId: _tenantId,
  }) => {
    const pom = new ShellLayoutPage(valeriaRailPage);

    // Navigate (valeriaRailPage seeds 'rail' via addInitScript)
    await valeriaRailPage.goto("/test-stack/shell-layout");

    // Install spy as early as possible — captures writes during hydration
    await pom.instrumentSetItem();

    // Wait for topBar to appear (SSR renders this)
    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    // Wait for full shell hydration
    await pom.waitForShellReady();

    // Additional wait for any async hydration effects to settle
    await valeriaRailPage.waitForTimeout(200);

    // Collect all setItem writes that happened during load + hydration
    const writes = await pom.getSetItemWrites();

    // Filter for writes to the shell storage key that contain valeriaState='full'
    const spuriousFullWrites = writes.filter(({ key, value }) => {
      if (key !== SHELL_STORAGE_KEY) return false;
      try {
        const parsed = JSON.parse(value) as {
          state?: { valeriaState?: string };
        };
        return parsed.state?.valeriaState === "full";
      } catch {
        return false;
      }
    });

    // SC-3 assertion: ZERO spurious 'full' writes (the bug would have caused ≥1)
    expect(spuriousFullWrites).toHaveLength(0);

    // Also verify: after hydration, valeriaState is still 'rail' in storage
    const state = await pom.getStorageState();
    expect(state?.valeriaState).toBe("rail");
  });

  // ── SC-3b: valeriaState + shellMode both preserved simultaneously ──────────
  //
  // Uses D2-stable pairings: valeriaState='rail' → shellMode='agentic' (D2 coupling).
  // Both non-default values preserved: 'rail' (non-default valeriaState) + 'agentic' (aligned).
  // The important thing is that 'rail' survives, not 'full' (the default).

  test("SC-3b valeriaState 'rail' + shellMode 'agentic' both survive SSR+hydration", async ({
    valeriaRailPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(valeriaRailPage);
    // valeriaRailPage seeds: valeriaState='rail' + shellMode='agentic' (D2-aligned)
    await pom.gotoShell(tenantId);
    await pom.waitForShellReady();

    // Both values must survive hydration
    const state = await pom.getStorageState();
    expect(state?.valeriaState).toBe("rail");
    // shellMode='agentic' is the D2 coupling result for rail — verify it's correct
    expect(state?.shellMode).toBe("agentic");
  });
});
