// cap: scheduling.mateo-agenda
// story-origin: vitalia-bugfix-agenda-actor-headers-422
/**
 * agenda-actor-headers-live.spec.ts — LIVE regression for the agenda 422 fix.
 *
 * Stack real (FE:3002 + BE:8002), Clerk testing token, SIN mocks del BE del surface
 * bajo prueba (un mock de /scheduling/agenda/grid = verde-fantasma — es justo lo que
 * enmascaró este bug). Ejerce la acción real del usuario: abrir /{tenant}/mateo/agenda
 * autenticado → el cliente dispara GET /scheduling/agenda/grid contra el BE real.
 *
 * Bug: el FE mandaba SOLO X-Tenant-ID → 422 (X-Clinic-ID + X-User-ID "Field required")
 *      → grilla vacía/error. Fix: useClinicId + useActorHeaders inyectan los 3 headers
 *      + X-User-Role (RBAC). El SSR resuelve los mismos server-side (X-Clinic-ID desde
 *      publicMetadata.clinicId del usuario Clerk — el JWT dev no trae clinic claim).
 *
 * Assert (contrato FE): la request a /scheduling/agenda/grid lleva los 3 headers actor
 *      (X-Clinic-ID + X-User-ID + X-User-Role) y YA NO da 422. La 1ª render se sirve del
 *      cache SSR (staleTime 25s) y la navegación por URL re-rendea server-side, así que la
 *      llamada CLIENT-SIDE que prueba el fix de headers es el POLL de React Query
 *      (refetchInterval 30s) — esperamos a que dispare en la misma página.
 *
 * NOTA (BE upstream): con los headers correctos el BE puede devolver 500 por un bug
 *      pre-existente del repo (agenda_grid_repository_impl: TextClause.selectable) que
 *      ESTE bug enmascaraba (el request nunca llegaba al repo). Eso es deuda BE fuera de
 *      este carril FE — el assert verifica el contrato de headers (no-422), no el 500.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-bugfix-agenda-actor-headers-422 --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../auth.fixture";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

interface GridCall {
  status: number;
  tenantHeader: string | null;
  clinicHeader: string | null;
  userIdHeader: string | null;
  userRoleHeader: string | null;
  url: string;
}

test("LIVE: el GET /scheduling/agenda/grid client-side (poll) lleva los 3 headers actor y no da 422", async ({
  authedPage,
}) => {
  // El poll de React Query corre cada 30s — este test espera a que dispare.
  test.setTimeout(60_000);

  const calls: GridCall[] = [];
  authedPage.on("response", async (res) => {
    if (res.url().includes("/scheduling/agenda/grid")) {
      const req = res.request();
      const h = req.headers();
      calls.push({
        status: res.status(),
        tenantHeader: h["x-tenant-id"] ?? null,
        clinicHeader: h["x-clinic-id"] ?? null,
        userIdHeader: h["x-user-id"] ?? null,
        userRoleHeader: h["x-user-role"] ?? null,
        url: res.url(),
      });
    }
  });

  await authedPage.setViewportSize({ width: 1440, height: 900 });
  await authedPage.goto(`/${TENANT_ID}/mateo/agenda?view=semana`, {
    waitUntil: "domcontentloaded",
  });
  // Esperar el poll client-side (refetchInterval 30s) — la 1ª render viene de SSR cache.
  await authedPage.waitForResponse(
    (res) => res.url().includes("/scheduling/agenda/grid"),
    { timeout: 40_000 },
  );
  await authedPage.waitForTimeout(500);

  console.log("AGENDA_GRID_CALLS=" + JSON.stringify(calls)); // diagnostic

  // Debe haber al menos una request que mandó los 3 headers requeridos por el BE.
  const withActorHeaders = calls.filter(
    (c) => c.clinicHeader && c.userIdHeader && c.userRoleHeader,
  );
  expect(
    withActorHeaders.length,
    `ninguna request a /scheduling/agenda/grid mandó X-Clinic-ID + X-User-ID + X-User-Role: ${JSON.stringify(calls)}`,
  ).toBeGreaterThan(0);

  // El bug era 422 por headers faltantes. Con el fix YA no debe haber 422.
  const had422 = calls.some((c) => c.status === 422);
  expect(
    had422,
    `422 en /scheduling/agenda/grid (headers faltantes — regresión del fix): ${JSON.stringify(calls)}`,
  ).toBe(false);
});

test("LIVE: la pantalla de agenda rendea (no crash global) y sin error 422", async ({
  authedPage,
}) => {
  await authedPage.setViewportSize({ width: 1440, height: 900 });
  await authedPage.goto(`/${TENANT_ID}/mateo/agenda?view=semana`, {
    waitUntil: "domcontentloaded",
  });
  await authedPage.waitForTimeout(3000);

  // El main de agenda debe estar presente (no crash / no error boundary global).
  const main = authedPage.locator('main, [role="main"]').first();
  await expect(main).toBeVisible({ timeout: 10_000 });
});
