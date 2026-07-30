/**
 * mock-fiscal-emission.ts — MSW handlers for fiscal emission stub
 *
 * F2-S1 Option A: service-blocker vitalia-fiscal-emission-pe NOT developed.
 * Provides MSW page.route() mocks for:
 *   - POST /api/v1/fiscal/emit → 200 boleta/factura emitida
 *   - POST /api/v1/fiscal/emit → 503 fiscal service down (compensation pattern)
 *
 * Note: Fiscal emit 503 does NOT rollback payment (saga compensation per A6).
 * FE shows success toast for payment + warning for fiscal retry pending.
 *
 * DEPRECATED: replace when vitalia-fiscal-emission-pe story=done
 *
 * downstream-regression-na: brand-local vitalia E2E MSW mock fixture
 *
 * @see 04-validators.yaml § test_construction_plan step 3
 * @see 03-arch § 8.6 Option A stubs + A6 saga compensation
 */

import type { Page, Route } from "@playwright/test";

// ---------------------------------------------------------------------------
// Scenario types
// ---------------------------------------------------------------------------

export type FiscalEmissionScenario =
  | "success_boleta"
  | "success_factura"
  | "fiscal_503"
  | "fiscal_503_retry_standalone";

// ---------------------------------------------------------------------------
// Response builders
// ---------------------------------------------------------------------------

const buildBoletaSuccess = (paymentId: string) => ({
  document_id: `doc-boleta-${paymentId.slice(0, 8)}`,
  document_type: "boleta",
  document_number: "B001-00001234",
  issued_at: new Date().toISOString(),
  pdf_url: `https://example.com/boletas/${paymentId}.pdf`,
  currency: "PEN",
  amount: 80,
  tax_amount: 0, // boleta PE: sin IGV desglosado para persona natural
  status: "emitted",
});

const buildFacturaSuccess = (paymentId: string) => ({
  document_id: `doc-factura-${paymentId.slice(0, 8)}`,
  document_type: "factura",
  document_number: "F001-00001234",
  issued_at: new Date().toISOString(),
  pdf_url: `https://example.com/facturas/${paymentId}.pdf`,
  currency: "PEN",
  amount: 96.8, // 80 + IGV 21%
  tax_amount: 16.8,
  status: "emitted",
});

const build503Response = () => ({
  error_code: "FISCAL_SERVICE_503",
  message:
    "El comprobante está en cola. Se emitirá en los próximos minutos. El pago fue registrado.",
  retry_available: true,
  retry_endpoint: "/api/v1/fiscal/emit/retry",
});

// ---------------------------------------------------------------------------
// Setup helpers per scenario
// ---------------------------------------------------------------------------

/**
 * Register fiscal emission mock via page.route().
 * Scoped to page — no global contamination.
 */
export async function setupFiscalEmissionMock(
  page: Page,
  scenario: FiscalEmissionScenario,
): Promise<void> {
  await page.route("**/api/v1/fiscal/emit", async (route: Route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }

    const body = route.request().postDataJSON() as {
      payment_id?: string;
      fiscal_doc_type?: string;
    } | null;
    const paymentId = body?.payment_id ?? "pay-mock-001";

    switch (scenario) {
      case "success_boleta":
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(buildBoletaSuccess(paymentId)),
        });
        break;

      case "success_factura":
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(buildFacturaSuccess(paymentId)),
        });
        break;

      case "fiscal_503":
      case "fiscal_503_retry_standalone":
        // Compensation pattern: payment succeeds, fiscal fails
        // FE must NOT show payment failure — only fiscal retry warning
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify(build503Response()),
        });
        break;

      default:
        await route.continue();
    }
  });
}

/**
 * Mock the fiscal retry standalone endpoint.
 */
export async function setupFiscalRetryMock(
  page: Page,
  documentId: string,
  retrySucceeds: boolean,
): Promise<void> {
  await page.route(
    "**/api/v1/fiscal/emit/retry",
    async (route: Route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      if (retrySucceeds) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            document_id: documentId,
            status: "emitted",
            pdf_url: `https://example.com/boletas/${documentId}.pdf`,
          }),
        });
      } else {
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify(build503Response()),
        });
      }
    },
  );
}
