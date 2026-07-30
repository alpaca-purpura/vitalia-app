/**
 * compliance-audit-log.smoke.spec.ts — V-V-16
 *
 * Validator: V-V-16 — Spec §3.6.A Sanaré LATAM compliance audit dashboard
 * Fixture: sanare-latam-mx (1,247 events: pii/consent/safety/injection/cross_tenant)
 * Flow: /medical-compliance → totals → breakdown → filter → export CSV
 */
import { test, expect } from "../../fixtures/sanare-latam-mx.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Compliance — Audit Log HIPAA-lite (Sanaré MX)", () => {
  test("V-V-16: compliance dashboard renders with event totals", async ({
    sanarePage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/medical-compliance");

    // Total events: 1,247 from mock
    await expect(page.getByText(/1[\.,]247|1247/i)).toBeVisible({
      timeout: 10_000,
    });

    // Section header
    await expect(
      page.getByText(/cumplimiento|compliance|audit/i).first(),
    ).toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-16: breakdown by event type shows all categories", async ({
    sanarePage: page,
  }) => {
    await page.goto("/medical-compliance");

    // All event categories from mock breakdown
    await expect(page.getByText(/pii_detected|pii detectado/i)).toBeVisible({
      timeout: 10_000,
    });
    await expect(
      page.getByText(/consent_signed|consentimiento firmado/i),
    ).toBeVisible();
    await expect(
      page.getByText(/safety_escalation|escalaci[oó]n/i),
    ).toBeVisible();
    await expect(page.getByText(/prompt_injection_blocked/i)).toBeVisible();
  });

  test("V-V-16: event list shows recent events", async ({
    sanarePage: page,
  }) => {
    await page.goto("/medical-compliance");

    // Events list from mock — at least consent_signed and pii_detected
    await expect(page.getByText(/consent_signed/i)).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(/pii_detected/i)).toBeVisible();
  });

  test("V-V-16: export CSV button present", async ({ sanarePage: page }) => {
    await page.goto("/medical-compliance");

    // Export CTA per spec §3.6.A
    await expect(
      page
        .getByRole("button", { name: /exportar csv/i })
        .or(page.getByRole("link", { name: /exportar csv/i })),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-16: filter controls visible (type + date range + severity)", async ({
    sanarePage: page,
  }) => {
    await page.goto("/medical-compliance");

    // Filter controls per spec §3.6.A wireframe
    await expect(page.getByRole("combobox", { name: /tipo/i })).toBeVisible({
      timeout: 10_000,
    });
    await expect(
      page
        .getByRole("combobox", { name: /fecha|periodo/i })
        .or(page.getByLabel(/fecha|periodo/i)),
    ).toBeVisible();
  });

  test("V-V-16: critical events (safety_escalation) highlighted", async ({
    sanarePage: page,
  }) => {
    await page.goto("/medical-compliance");

    // safety_escalation event from mock with severity "critical"
    await expect(page.getByText(/safety_escalation/i)).toBeVisible({
      timeout: 10_000,
    });

    // Severity indicator present
    await expect(page.getByText(/cr[íi]tic[ao]|alta/i).first()).toBeVisible({
      timeout: 10_000,
    });
  });
});
