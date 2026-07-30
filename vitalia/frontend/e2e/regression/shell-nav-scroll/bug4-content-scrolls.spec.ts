/**
 * bug4-content-scrolls.spec.ts — Bug #4: el contenido de la hoja scrollea cuando
 * excede el alto del panel. RN-4 · gherkin bug4_content_scrolls.
 *
 * Causa raíz: AppPanelSlot content wrapper tenía overflow-hidden → recortaba toda
 * hoja larga. Fix: overflow-y-auto (mantiene flex-1 min-h-0). El <section>/<main>
 * del shell siguen overflow-hidden (marco fijo).
 *
 * REWORK hybrid-mock → real-backend:
 *   Usa real-backend-forward.fixture (Clerk auth + /api/v1/** → BE :8002 +
 *   gate anti-burbuja base.ts). Ruta: lucas/lanzar (placeholder dispatcher,
 *   ruta limpia sin api 4xx — gate ON).
 *
 *   Cualquier ruta que monte AppPanelSlot sirve para verificar overflow-y: auto
 *   en el DOM. lucas/lanzar es la ruta limpia canónica (sin 404 pre-existentes
 *   de marca/BE gap).
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";

const DESKTOP = { width: 1280, height: 720 };

test.describe("Bug #4 — content scrolls (RN-4)", () => {
  test.use({ viewport: DESKTOP });

  test("el contenedor de contenido del panel es scrolleable (overflow-y: auto)", async ({
    page,
  }) => {
    test.skip(
      !process.env["E2E_BASE_URL"],
      "requiere stack dev (E2E_BASE_URL) — corre en el gate",
    );
    // lucas/lanzar: ruta placeholder limpia, gate anti-burbuja ON.
    // Cualquier ruta que monte AppPanelSlot sirve para la aserción DOM.
    await page.goto(`/${TENANT_ID}/lucas/lanzar`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(2500);

    // AppPanelSlot expone data-testid="app-panel-slot".
    // Su hijo de contenido (flex-grow: 1) es el contenedor scrolleable.
    const overflowY = await page.evaluate(() => {
      const slot = document.querySelector('[data-testid="app-panel-slot"]');
      if (!slot) return "no-slot";
      const kids = Array.from(slot.children) as HTMLElement[];
      const content = kids.find(
        (k) => getComputedStyle(k).flexGrow === "1",
      );
      return content ? getComputedStyle(content).overflowY : "no-content-div";
    });

    expect(
      ["auto", "scroll"],
      `el contenedor de contenido debe scrollear, computed overflowY=${overflowY}`,
    ).toContain(overflowY);
    // El gate anti-burbuja (teardown de base.ts via mergeTests) confirma cero errores runtime.
  });
});
