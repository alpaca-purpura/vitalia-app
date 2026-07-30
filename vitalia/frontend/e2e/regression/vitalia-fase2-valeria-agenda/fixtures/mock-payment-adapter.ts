/**
 * mock-payment-adapter.ts — MSW handlers for payment adapter stub
 *
 * F2-S1 Option A: service-blocker vitalia-payment-adapter-mvp NOT developed.
 * Provides MSW page.route() mocks for:
 *   - POST /api/v1/payments/charge → 200 success
 *   - POST /api/v1/payments/charge → 503 payment adapter down
 *   - POST /api/v1/payments/charge → 409 balance already charged (optimistic lock)
 *   - GET  /api/v1/payments/idempotency/{key} → lookup existing
 *
 * Usage in spec:
 *   import { setupPaymentAdapterMock, PaymentAdapterScenario } from '../fixtures/mock-payment-adapter';
 *   await setupPaymentAdapterMock(page, 'success');
 *
 * Stubs are SCOPED PER TEST (page.route is per-page) — no cross-test contamination.
 *
 * DEPRECATED: replace when vitalia-payment-adapter-mvp story=done
 *
 * downstream-regression-na: brand-local vitalia E2E MSW mock fixture
 *
 * @see 04-validators.yaml § test_construction_plan step 2
 * @see 03-arch § 8.6 Option A stubs
 */

import type { Page, Route } from "@playwright/test";

// ---------------------------------------------------------------------------
// Scenario types
// ---------------------------------------------------------------------------

export type PaymentAdapterScenario =
  | "success"
  | "success_no_fiscal"
  | "payment_503"
  | "payment_409_conflict"
  | "idempotency_hit";

// ---------------------------------------------------------------------------
// Response builders
// ---------------------------------------------------------------------------

const buildSuccessResponse = (idempotencyKey: string) => ({
  payment_id: `pay-${idempotencyKey.slice(0, 8)}`,
  status: "approved",
  amount: 80,
  currency: "PEN",
  method: "tarjeta",
  processed_at: new Date().toISOString(),
  idempotency_key: idempotencyKey,
});

const build503Response = () => ({
  error_code: "PAYMENT_ADAPTER_503",
  message: "El servicio de pago no está disponible. Intentá de nuevo.",
  retry_after_seconds: 30,
});

const build409Response = (latestState: object) => ({
  error_code: "BALANCE_ALREADY_CHARGED",
  message: "Este saldo ya fue cobrado por otro usuario.",
  latest_state: latestState,
});

// ---------------------------------------------------------------------------
// Setup helpers per scenario
// ---------------------------------------------------------------------------

/**
 * Register MSW-style network mock via page.route() for payment adapter.
 * Scoped to the provided page instance (no global contamination).
 */
export async function setupPaymentAdapterMock(
  page: Page,
  scenario: PaymentAdapterScenario,
): Promise<void> {
  await page.route("**/api/v1/payments/charge", async (route: Route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }

    const body = route.request().postDataJSON() as {
      idempotency_key?: string;
      appointment_id?: string;
    } | null;
    const key = body?.idempotency_key ?? "mock-key-fallback";

    switch (scenario) {
      case "success":
      case "success_no_fiscal":
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(buildSuccessResponse(key)),
        });
        break;

      case "payment_503":
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify(build503Response()),
        });
        break;

      case "payment_409_conflict":
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: JSON.stringify(
            build409Response({
              appointment_id: body?.appointment_id ?? "apt-001",
              payment_status: "paid",
              balance_version: 2,
              charged_at: new Date().toISOString(),
            }),
          ),
        });
        break;

      case "idempotency_hit":
        // Returns existing payment (idempotent replay)
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ...buildSuccessResponse(key),
            idempotency_replayed: true,
          }),
        });
        break;

      default:
        await route.continue();
    }
  });
}

/**
 * Mock idempotency lookup endpoint.
 */
export async function setupIdempotencyLookupMock(
  page: Page,
  idempotencyKey: string,
  exists: boolean,
): Promise<void> {
  await page.route(
    `**/api/v1/payments/idempotency/${idempotencyKey}`,
    async (route: Route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      if (exists) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(buildSuccessResponse(idempotencyKey)),
        });
      } else {
        await route.fulfill({
          status: 404,
          contentType: "application/json",
          body: JSON.stringify({ error_code: "NOT_FOUND" }),
        });
      }
    },
  );
}

/**
 * Unregister all payment adapter mocks on this page.
 * Call in test.afterEach when needed (normally handled by page teardown).
 */
export async function clearPaymentAdapterMocks(page: Page): Promise<void> {
  await page.unrouteAll({ behavior: "ignoreErrors" });
}
