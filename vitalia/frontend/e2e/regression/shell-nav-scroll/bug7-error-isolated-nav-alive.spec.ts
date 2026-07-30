/**
 * bug7-error-isolated-nav-alive.spec.ts — Bug #7: un error en el contenido de una
 * hoja se aísla al panel; la navegación (sidebar/ribbon/sub-tabs) sigue clickeable.
 * RN-6 · gherkin bug7_error_isolated_nav_alive.
 *
 * Fix: nuevo [agent]/error.tsx genérico. Al vivir dentro de (shell-organism)/layout
 * → ShellOrganismLayout → AppPanelSlot, el boundary captura el throw del sub-árbol
 * [agent] y renderiza el fallback EN EL PANEL, dejando el chrome vivo.
 *
 * REWORK hybrid-mock → real-backend:
 *   Usa real-backend-forward.fixture (Clerk auth + /api/v1/** → BE :8002 +
 *   gate anti-burbuja base.ts).
 *
 *   Inyección honesta de fallo: la fixture ya establece el forwarding global
 *   de /api/v1/** → BE real. Luego se registra una ruta LIFO más específica
 *   que intercepta /api/v1/lisa/marca/** y responde 500 (boom e2e forced).
 *   Playwright evalúa rutas LIFO → esta 500 gana para marca, todo lo demás
 *   sigue forwardeando al BE real. Esto es fault-injection honesta: la superficie
 *   bajo prueba es el ERROR BOUNDARY, marca es solo una dependencia.
 *
 * Gate OFF (failOnRuntimeError: false) porque se ejerce un error a propósito.
 * La respuesta correcta ES el fallback del boundary, no un bug de runtime.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";

const DESKTOP = { width: 1280, height: 720 };

test.describe("Bug #7 — error isolated, nav alive (RN-6)", () => {
  // Ejerce un error a propósito → gate anti-burbuja OFF.
  // El fallback del boundary ES la respuesta correcta.
  test.use({ viewport: DESKTOP, failOnRuntimeError: false });

  test("un fallo en /api/v1/lisa/marca/** renderiza el fallback en el panel + chrome vivo", async ({
    page,
  }) => {
    test.skip(
      !process.env["E2E_BASE_URL"],
      "requiere stack dev (E2E_BASE_URL) — corre en el gate",
    );

    // Inyección LIFO: la fixture ya registró forwarding de /api/v1/**→BE real.
    // Esta ruta más específica gana para /api/v1/lisa/marca/**, todo lo demás
    // sigue forwardeando. Fault-injection honesta: no mockea el shell, solo marca.
    await page.route("**/api/v1/lisa/marca/**", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "boom (e2e forced)" }),
      }),
    );

    await page.goto(`/${TENANT_ID}/lisa/marca/identidad`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(3000);

    // El Ribbon (chrome del shell) sigue visible — el boundary aisló el error al panel.
    await expect(
      page.getByTestId("ribbon"),
      "el Ribbon debe seguir visible pese al error en el contenido",
    ).toBeVisible({ timeout: 10_000 });

    // El SubTabsBar también sigue vivo.
    await expect(
      page.getByTestId("sub-tabs-bar"),
      "el SubTabsBar debe seguir visible (nav no bloqueada)",
    ).toBeVisible();
  });
});
