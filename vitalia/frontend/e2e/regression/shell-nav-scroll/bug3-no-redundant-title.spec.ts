/**
 * bug3-no-redundant-title.spec.ts — Bug #3: ninguna hoja muestra un título superior
 * que duplique la opción de navegación activa. RN-3 · gherkin bug3_no_redundant_sheet_title.
 *
 * Fix: removido <SubTabHeader> del dispatcher + h2-eco de IdentidadView/VozTonoView/
 * PresenciaView. Se PRESERVAN headings de sección intra-contenido (form sections).
 *
 * REWORK hybrid-mock → real-backend:
 *   Usa real-backend-forward.fixture (Clerk auth + /api/v1/** → BE :8002 +
 *   gate anti-burbuja base.ts). Ruta: lucas/lanzar (placeholder dispatcher,
 *   ruta limpia sin api 4xx — gate ON).
 *
 *   NOTA: el test "presencia h2-eco" (variante original) fue removido de este
 *   e2e y cubierto por el test unitario fe_unit_lisa_marca (Vitest) que verifica
 *   PresenciaView sin necesitar el stack full. Esta suite verifica la invariante
 *   structural del dispatcher (SubTabHeader removido) en ruta limpia.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";

const DESKTOP = { width: 1280, height: 720 };

test.describe("Bug #3 — no redundant sheet title (RN-3)", () => {
  test.use({ viewport: DESKTOP });

  test("una hoja placeholder (lucas/lanzar) NO duplica el label de la sub-tab activa (SubTabHeader removido)", async ({
    page,
  }) => {
    test.skip(
      !process.env["E2E_BASE_URL"],
      "requiere stack dev (E2E_BASE_URL) — corre en el gate",
    );
    // lucas/lanzar: placeholder dispatcher limpio, sin api 4xx → gate anti-burbuja ON.
    await page.goto(`/${TENANT_ID}/lucas/lanzar`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(2500);

    // El SubTabHeader del dispatcher tenía data-testid="subtab-header-{agent}-{subtab}".
    // Fue removido del dispatcher; no debe existir en ninguna hoja.
    await expect(
      page.getByTestId(/^subtab-header-/),
      "el SubTabHeader-eco del dispatcher debe estar removido",
    ).toHaveCount(0);
    // El gate anti-burbuja (teardown de base.ts via mergeTests) confirma cero errores runtime.
  });
});
