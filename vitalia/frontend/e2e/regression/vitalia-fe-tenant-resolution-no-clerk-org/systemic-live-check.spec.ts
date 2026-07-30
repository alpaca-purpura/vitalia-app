// cap: iam.luana-core-adoption
// story-origin: vitalia-fe-tenant-resolution-no-clerk-org
/**
 * systemic-live-check.spec.ts — LIVE check del fix de tenant-resolution (no Clerk org).
 * Navega autenticado (stack real, SIN mocks) por rutas PHI que existen y captura el
 * status de las APIs. Objetivo: X-Tenant-ID ahora es UUID nuestro → 0 respuestas 5xx
 * por "badly formed hexadecimal UUID string". El backend log es la verdad (ver orquestador).
 */
import { test, expect } from "../../auth.fixture";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

const ROUTES = ["/lisa/staff", "/mateo/agenda", "/lisa/marca/identidad"];

test("LIVE: rutas PHI no devuelven 5xx por tenant UUID malformado", async ({
  authedPage,
}) => {
  const apiCalls: { route: string; url: string; status: number; tenant: string | null }[] = [];
  authedPage.on("response", (res) => {
    const u = res.url();
    if (u.includes("/api/v1/")) {
      apiCalls.push({
        route: "(current)",
        url: u.replace(/https?:\/\/[^/]+/, ""),
        status: res.status(),
        tenant: res.request().headers()["x-tenant-id"] ?? null,
      });
    }
  });

  await authedPage.setViewportSize({ width: 1440, height: 900 });
  for (const r of ROUTES) {
    await authedPage.goto(`/${TENANT_ID}${r}`, { waitUntil: "domcontentloaded" });
    await authedPage.waitForTimeout(2500);
  }

  const fivexx = apiCalls.filter((c) => c.status >= 500);
  // eslint-disable-next-line no-console
  console.log("API_5XX=" + JSON.stringify(fivexx));
  // eslint-disable-next-line no-console
  console.log(
    "API_SAMPLE=" +
      JSON.stringify(apiCalls.slice(0, 12).map((c) => ({ url: c.url, status: c.status, tenant: c.tenant }))),
  );

  expect(fivexx, `5xx en APIs PHI: ${JSON.stringify(fivexx)}`).toEqual([]);
});
