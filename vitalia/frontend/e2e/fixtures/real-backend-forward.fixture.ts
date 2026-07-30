/**
 * real-backend-forward.fixture.ts — Shared honest-backend forwarding fixture
 *
 * SSoT del transporte e2e → backend REAL (cap: brand_studio.lisa-marca).
 *
 * Resuelve dos problemas a la vez (anti-duplicación, anti-burbuja):
 *
 *   1. FORWARDING (LIFT del inline ×3 del parent): el FE en :3002 NO proxya
 *      `/api/v1/**` al BE en :8002. Esta fixture forwardea esas requests al BE
 *      REAL vía `page.request.fetch(:8002)`. El backend las procesa de verdad
 *      — cero mock del backend-bajo-prueba (RN-1). El forwarding vive ACÁ, NO
 *      copiado inline en 14 specs (`.claude/rules/anti-duplication.md`).
 *
 *   2. ANTI-BURBUJA (composición con `base.ts` vía `mergeTests`): cada test
 *      hereda el gate runtime (pageerror / hydration / api-4xx5xx / overlay de
 *      Next) que falla si el cliente vio cualquier error tras la hidratación
 *      (Critical Rule #37 §3). NO se recrea — se compone.
 *
 * ⚠️ HEADERS HONESTOS (post T-2/T-3): NO se inyecta `X-User-ID: TENANT_ID`
 *    (eso era el B6 mask que enmascaraba el sub-bug #1/#2). El browser real
 *    manda sus propios headers: `fetchClient` inyecta `X-Tenant-ID` desde
 *    Clerk + el api-layer manda el `X-User-ID` = Clerk userId real (T-2). El
 *    forwarding reenvía TODOS los headers del browser tal cual. Si una request
 *    falla por falta de header, ESO es el contrato roto que la suite debe
 *    exponer — no enmascararlo.
 *
 * Uso en specs:
 *   import { test, expect, TENANT_ID } from '../../fixtures/real-backend-forward.fixture';
 *   // `test` ya trae auth + forwarding + anti-burbuja sobre `page` y `authedPage`.
 *
 * Opt-out anti-burbuja cuando el test ejerce un error a propósito (503/timeout):
 *   test.use({ failOnRuntimeError: false });
 *
 * Stack requerido: backend :8002 + frontend :3002 UP (make dev-vitalia).
 *
 * downstream-regression-na: brand-local vitalia e2e shared fixture
 *
 * @see .claude/rules/anti-duplication.md (LIFT forwarding, no inline ×11)
 * @see .claude/rules/definition-of-done-live-verify.md (base.ts anti-burbuja)
 * @see e2e/fixtures/base.ts (runtime-error gate compuesto)
 * @see 06-tickets.yaml T-1 deliverable 1
 */

import path from "path";
import { mergeTests, test as base } from "@playwright/test";
import type { Page, Route } from "@playwright/test";
import { setupClerkTestingToken } from "@clerk/testing/playwright";
import { test as runtimeGate, expect } from "./base";

// ---------------------------------------------------------------------------
// Tenant + backend constants
// ---------------------------------------------------------------------------

/**
 * Tenant ID owned by the authenticated Clerk user (E2E_TENANT_ID).
 * VITALIA_PE_TENANT_ID is a secondary fallback for local overrides.
 * The slug fallback only applies when neither env var is set (would
 * cross-tenant-block — kept solely so imports don't crash without env).
 */
export const TENANT_ID =
  process.env["E2E_TENANT_ID"] ??
  process.env["VITALIA_PE_TENANT_ID"] ??
  "clinica-salud-vitalia-pe-test";

/**
 * Real backend URL for API forwarding (BE at :8002 in make dev-vitalia).
 * The FE at :3002 does not proxy /api/v1/** natively.
 */
export const BACKEND_API_URL =
  process.env["VITALIA_BE_URL"] ??
  process.env["NEXT_PUBLIC_API_URL"] ??
  "http://localhost:8002";

// __dirname = e2e/fixtures → ../../playwright/.clerk/user.json = vitalia/frontend/playwright/.clerk/user.json
// (matches playwright.config.ts `storageState: "playwright/.clerk/user.json"`).
const STORAGE_STATE_PATH = path.join(
  __dirname,
  "..",
  "..",
  "playwright",
  ".clerk",
  "user.json",
);

// ---------------------------------------------------------------------------
// Forwarding helper — page.route('**/api/v1/**') → page.request.fetch(:8002)
// ---------------------------------------------------------------------------

/**
 * Forwards every `/api/v1/**` request the browser makes to the real backend.
 *
 * The browser's own headers are reused VERBATIM (`allHeaders()`): `fetchClient`
 * injects `X-Tenant-ID` from Clerk; the api-layer injects the real `X-User-ID`
 * (Clerk userId, T-2). We deliberately do NOT add/override actor headers — an
 * honest contract means the browser's real request reaches the real BE.
 *
 * If the BE is unreachable the request falls through to the network (fails with
 * a real network error, surfaced by the anti-burbuja gate) rather than silently
 * passing.
 */
export async function forwardApiToRealBackend(page: Page): Promise<void> {
  await page.route("**/api/v1/**", async (route: Route) => {
    const url = route.request().url();
    const targetUrl = url.replace(
      /^https?:\/\/localhost:3002/,
      BACKEND_API_URL,
    );
    const method = route.request().method();
    const headers = await route.request().allHeaders();
    const body = route.request().postDataBuffer();

    try {
      const response = await page.request.fetch(targetUrl, {
        method,
        headers,
        data: body ?? undefined,
      });
      await route.fulfill({ response });
    } catch {
      // BE unreachable → fall through to network (real failure, no silent pass).
      await route.continue();
    }
  });
}

// ---------------------------------------------------------------------------
// Auth fixture — Clerk storageState + testing token (the 'authed' half)
// ---------------------------------------------------------------------------

const authed = base.extend<{ authedPage: Page }>({
  // The default page is pre-authenticated + forwarded to the real BE so specs
  // that use `page` directly already hit the honest backend.
  page: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: STORAGE_STATE_PATH,
    });
    const page = await context.newPage();
    await setupClerkTestingToken({ page });
    await forwardApiToRealBackend(page);
    await use(page);
    await page.close();
    await context.close();
  },

  // `authedPage` is an explicit alias of the forwarded, authenticated page so
  // the parent specs (which use `authedPage`) keep working after composition.
  authedPage: async ({ page }, use) => {
    await use(page);
  },
});

// ---------------------------------------------------------------------------
// Composed test — anti-burbuja gate (base.ts) + auth + real-backend forwarding
// ---------------------------------------------------------------------------

/**
 * The merged test object: every spec importing from here gets, on the SAME
 * `page`, the runtime-error gate (base.ts) AND Clerk auth + real-backend
 * forwarding. `mergeTests` composes the fixtures so both `page` overrides apply.
 */
export const test = mergeTests(runtimeGate, authed);

export { expect };
