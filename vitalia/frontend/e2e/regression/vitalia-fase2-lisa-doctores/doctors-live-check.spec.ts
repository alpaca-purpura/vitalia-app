// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * doctors-live-check.spec.ts — LIVE check del keystone doctors-500 fix.
 * Stack real (FE:3002 + BE:8002), Clerk testing token, SIN mocks.
 * Captura el status REAL de GET /clinics/doctors tras el fix (BE 422 guard + FE useClinicId).
 * NO es un golden — es diagnóstico live para decidir si el fix + la data (clinicId) están OK.
 */
import { test, expect } from "../../auth.fixture";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

test("LIVE: GET /clinics/doctors ya no da 500; reporta status + clinic header", async ({
  authedPage,
}) => {
  const calls: { status: number; tenantHeader: string | null; clinicHeader: string | null; url: string }[] = [];
  authedPage.on("response", async (res) => {
    if (res.url().includes("/clinics/doctors")) {
      const req = res.request();
      calls.push({
        status: res.status(),
        tenantHeader: req.headers()["x-tenant-id"] ?? null,
        clinicHeader: req.headers()["x-clinic-id"] ?? null,
        url: res.url(),
      });
    }
  });

  await authedPage.setViewportSize({ width: 1440, height: 900 });
  await authedPage.goto(`/${TENANT_ID}/lisa/staff`, { waitUntil: "domcontentloaded" });
  await authedPage.waitForTimeout(3500); // dejar que el directorio dispare su query

  console.log("DOCTORS_CALLS=" + JSON.stringify(calls)); // diagnostic

  // El fix mata el 500 desnudo. 500 = regresión.
  const had500 = calls.some((c) => c.status === 500);
  expect(had500, `500 en /clinics/doctors (debería ser 200 o 422): ${JSON.stringify(calls)}`).toBe(false);
});
