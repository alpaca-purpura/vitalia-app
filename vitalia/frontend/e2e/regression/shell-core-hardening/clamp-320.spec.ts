// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * clamp-320.spec.ts — SC-9: clamp 320px en viewport [1024,1280) (RN-8)
 *
 * RN-8: clamp 320 en [1024,1280); sin rail 60.
 * Verifica que en un viewport de 1100px, al arrastrar el splitter a la izquierda,
 * el panel de Valeria no cae por debajo de 320px.
 * No hay "rail mode" de 60px (AC-1 eliminó shellMode).
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/clamp-320.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

// Viewport in the [1024,1280) range per RN-8
const VIEWPORT_1100 = { width: 1100, height: 800 };
/** New machine clamp: 320px (replaced 580/360 from legacy machine) */
const CLAMP_MIN_PX = 320;
const TOLERANCE_PX = 30;

test.describe("SC-9 — clamp 320px en viewport 1100 (RN-8)", () => {
  test.use({ viewport: VIEWPORT_1100 });

  test("drag far left: Valeria no cae por debajo de 320px", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const initialWidth = await pom.getValeriaWidth();
    expect(initialWidth).toBeGreaterThan(0);

    // Drag far left (500px) — should clamp at 320px
    await pom.dragResizeHandle(-500);
    await shellPage.waitForTimeout(200);

    const clampedWidth = await pom.getValeriaWidth();

    // Must not go below clamp
    expect(
      clampedWidth,
      `Valeria no debe caer por debajo de ${CLAMP_MIN_PX}px (RN-8 clamp)`,
    ).toBeGreaterThanOrEqual(CLAMP_MIN_PX - TOLERANCE_PX);
  });

  test("sin rail de 60px: Valeria nunca llega a 60px", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Drag as far left as possible
    await pom.dragResizeHandle(-1000);
    await shellPage.waitForTimeout(200);

    const minWidth = await pom.getValeriaWidth();

    // The old rail was 60px — now it should be clamped at 320px min
    expect(minWidth, "sin rail: ancho mínimo > 100px (no 60px rail)").toBeGreaterThan(100);
  });
});
