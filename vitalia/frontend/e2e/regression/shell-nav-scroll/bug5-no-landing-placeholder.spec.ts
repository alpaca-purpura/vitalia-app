/**
 * bug5-no-landing-placeholder.spec.ts — Bug #5: Presencia no muestra el recuadro
 * "Editor de landing pública — próximamente". RN-5 ·
 * gherkin bug5_no_landing_placeholder_presencia.
 *
 * Fix: removido InfoBannerLandingDescoped (render + import + exports + archivo).
 * El resto de Presencia (website, redes, trust signals, sedes) sigue funcionando.
 *
 * REWORK hybrid-mock → real-backend:
 *   Usa real-backend-forward.fixture (Clerk auth + /api/v1/** → BE :8002).
 *   Ruta: lisa/marca/presencia. Esta ruta emite 404s PRE-EXISTENTES en
 *   /api/v1/lisa/marca/{trust-catalog/PE,locations,visuals,identity,contact}
 *   (gaps del BE owned por otra story — NOT este bugfix). Por eso se usa
 *   gate SCOPED (failOnRuntimeError: false) con assertions manuales usando
 *   attachRuntimeErrorGuards + allowlist documentada de los 404s conocidos.
 *
 * ALLOWLIST CONOCIDA (shrink-only, NO agregar a base.ts global):
 *   /api/v1/lisa/marca/(trust-catalog|locations|visuals|identity|contact)
 *   Estos 404s son gaps del BE de otra story. Cualquier 5xx o 404 fuera
 *   de esta allowlist FALLA el test (contrato honesto).
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";
import {
  attachRuntimeErrorGuards,
  expectNoNextErrorOverlay,
} from "../../fixtures/base";
import type { RuntimeErrorCollections } from "../../fixtures/base";

const DESKTOP = { width: 1280, height: 720 };

/**
 * 404s pre-existentes en lisa/marca/presencia — gaps de BE owned por otra story.
 * Esta allowlist es SHRINK-ONLY: no agregar nuevas entradas sin PR + rationale.
 * @see vitalia/docs/product/stories/vitalia-fase2-lisa-marca/ (BE gaps pendientes)
 */
const KNOWN_BE_GAP_404 =
  /\/api\/v1\/lisa\/marca\/(trust-catalog|locations|visuals|identity|contact)/;

test.describe("Bug #5 — no landing placeholder in Presencia (RN-5)", () => {
  // Gate OFF porque la ruta emite 404s pre-existentes de BE (otra story).
  // Assertions manuales con allowlist documentada en su lugar.
  test.use({ viewport: DESKTOP, failOnRuntimeError: false });

  test("Presencia NO muestra el callout 'Editor de landing pública — próximamente'", async ({
    page,
  }) => {
    test.skip(
      !process.env["E2E_BASE_URL"],
      "requiere stack dev (E2E_BASE_URL) — corre en el gate",
    );

    // Adjuntar colectores manuales (gate scoped, no automático).
    const guards: RuntimeErrorCollections = attachRuntimeErrorGuards(page);

    await page.goto(`/${TENANT_ID}/lisa/marca/presencia`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(3000);

    // Aserción principal: el banner removido ya no existe.
    await expect(
      page.getByText(/Editor de landing pública/i),
      "el banner InfoBannerLandingDescoped debe estar eliminado",
    ).toHaveCount(0);
    expect(
      await page.getByRole("note").count(),
      "no debe haber elementos role=note (el banner usaba role=note)",
    ).toBe(0);

    // Runtime assertions manuales (gate scoped):
    // pageerror = NUNCA OK (burbuja JS).
    expect(guards.pageErrors, `pageerror inesperado: ${guards.pageErrors.join(" | ")}`).toEqual([]);

    // hydration errors = NUNCA OK.
    expect(guards.hydrationErrors, `error de hidratación: ${guards.hydrationErrors.join(" | ")}`).toEqual([]);

    // Next error overlay = NUNCA OK.
    await expectNoNextErrorOverlay(page);

    // /api/ 4xx: solo permitidos los BE-gap conocidos. Cualquier otro = falla.
    const unexpectedApi4xx = guards.failedApi.filter(
      (u) => !KNOWN_BE_GAP_404.test(u),
    );
    expect(
      unexpectedApi4xx,
      `/api/ 4xx fuera de la allowlist conocida: ${unexpectedApi4xx.join(" | ")}`,
    ).toEqual([]);

    // 5xx = NUNCA OK (incluso en rutas con BE gaps conocidos).
    const api5xx = guards.failedApi.filter((u) => / → 5\d\d$/.test(u));
    expect(
      api5xx,
      `5xx inesperado en /api/: ${api5xx.join(" | ")}`,
    ).toEqual([]);
  });
});
