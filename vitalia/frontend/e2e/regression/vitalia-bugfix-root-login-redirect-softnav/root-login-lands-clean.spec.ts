// cap: shell-organism.shell-vitalia
// story-origin: vitalia-bugfix-root-login-redirect-softnav
/**
 * root-login-lands-clean.spec.ts — root "/" autenticado aterriza en el shell
 * SIN colgarse y SIN refresh manual (RN: edge-redirect mata el soft-nav in-render).
 *
 * Bug: tras loguearse, Clerk afterSignIn manda a "/". El Server Component
 * app/page.tsx hacía ahí un redirect() IN-RENDER hacia /{tenant}/mateo/agenda →
 * soft-nav intra route-group (shell-organism) [layout dynamic({ssr:false})] →
 * "Rendered more hooks than during the previous render" en el Router de Next 16
 * (~40% flake → render colgado hasta refrescar). Fix: edge-redirect 307 en
 * proxy.ts ANTES de que renderice app/page.tsx.
 *
 * Como el bug era ~40% flaky, el flujo se ejerce ×N veces (LOOP_COUNT) para
 * confirmar que el fix es 100% determinístico + cero "Rendered more hooks".
 *
 * REAL-BACKEND: sin mocks del surface bajo prueba (doctrina verification-real-not-200).
 * Gate anti-burbuja via base.ts (pageerror + console.error de hidratación) —
 * el "Rendered more hooks" bubblea como pageerror y lo capturamos también explícito.
 *
 * Run (NUNCA make e2e — Docker OOM):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test \
 *     e2e/regression/vitalia-bugfix-root-login-redirect-softnav/root-login-lands-clean.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";

const DESKTOP = { width: 1280, height: 720 };
// El bug era ~40% flaky → 8 corridas dan >99.9% de probabilidad de cazarlo si
// reapareciera (1 - 0.6^8 ≈ 0.983 por corrida; 8 corridas ≈ certeza práctica).
const LOOP_COUNT = 8;
const HOOKS_ERROR = /Rendered more hooks than during the previous render/i;

test.describe("Root login redirect — root '/' aterriza limpio en el shell (sin soft-nav in-render)", () => {
  test.use({ viewport: DESKTOP });
  // ×8 navegaciones a "/" + espera del shell montado. networkidle per-nav en dev
  // puede tomar ~5-8s cada una → margen amplio.
  test.setTimeout(120_000);

  test(`navega a "/" ×${LOOP_COUNT} → siempre /{tenant}/mateo/agenda con shell montado, sin "Rendered more hooks"`, async ({
    page,
  }) => {
    const hooksErrors: string[] = [];
    page.on("pageerror", (err) => {
      if (HOOKS_ERROR.test(err.message)) {
        hooksErrors.push(`pageerror: ${err.message}`);
      }
    });
    page.on("console", (msg) => {
      if (msg.type() === "error" && HOOKS_ERROR.test(msg.text())) {
        hooksErrors.push(`console.error: ${msg.text()}`);
      }
    });

    for (let i = 0; i < LOOP_COUNT; i++) {
      // Hard-nav a la raíz exacta (simula el afterSignIn que aterriza en "/").
      await page.goto("/", { waitUntil: "domcontentloaded" });

      // El edge-redirect (307) debe llevar a /{tenant}/mateo/agenda SIN refresh.
      await page.waitForURL(/\/mateo\/agenda/, { timeout: 25_000 });
      expect(
        page.url(),
        `loop ${i + 1}/${LOOP_COUNT}: la raíz "/" no aterrizó en mateo/agenda`,
      ).toContain("/mateo/agenda");
      // Debe ser un tenant UUID en la URL (no "/" colgado, no org_xxx).
      expect(page.url()).toContain(TENANT_ID);

      // El shell debe montar (no quedar colgado en "rendering"). main#main-content
      // visible = el Router montó limpio tras el redirect del edge.
      const mainVisible = await page
        .locator("main#main-content")
        .isVisible({ timeout: 15_000 })
        .catch(() => false);
      expect(
        mainVisible,
        `loop ${i + 1}/${LOOP_COUNT}: shell NO montó (render colgado — el bug reapareció)`,
      ).toBe(true);
    }

    // Cero "Rendered more hooks" en ninguna de las corridas → fix determinístico.
    expect(
      hooksErrors,
      `Apareció "Rendered more hooks" tras ×${LOOP_COUNT} aterrizajes a "/": ${hooksErrors.join(" | ")}`,
    ).toEqual([]);
    // El gate anti-burbuja (teardown base.ts) confirma además cero error runtime.
  });
});
