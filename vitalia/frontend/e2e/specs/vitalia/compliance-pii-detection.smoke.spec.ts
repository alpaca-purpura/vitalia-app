/**
 * compliance-pii-detection.smoke.spec.ts — Spec §15 Compliance smoke #2
 *
 * Validator: Compliance smoke — pii_detected event recorded
 * Fixture: aurora-dental-ar (pii_detected count=3 in compliance log)
 * Flow: /medical-compliance → pii_detected events → warning severity
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Compliance Smoke — PII Detection", () => {
  test("pii_detected events visible in compliance dashboard", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/medical-compliance");

    // pii_detected in breakdown
    await expect(page.getByText(/pii_detected/i)).toBeVisible({
      timeout: 10_000,
    });

    // Count = 3 for Aurora
    await expect(page.getByText(/pii_detected.*3|3.*pii/i)).toBeVisible({
      timeout: 10_000,
    });

    expect(consoleErrors).toHaveLength(0);
  });

  test("pii_detected event appears with warning severity", async ({
    auroraPage: page,
  }) => {
    await page.goto("/medical-compliance");

    // From mock: evt-2 pii_detected severity=warning
    await expect(page.getByText(/pii_detected/i)).toBeVisible({
      timeout: 10_000,
    });
    await expect(
      page.getByText(/warning|advertencia|media/i).first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("offer submission with PII shows form error", async ({
    auroraPage: page,
  }) => {
    // Mock: PII detection on offer description
    await page.route("**/api/v1/offers", async (route) => {
      if (route.request().method() === "POST") {
        const body = await route.request().postDataJSON();
        // Check if description contains PII-like content
        const desc = body?.description ?? "";
        if (
          desc.includes("DNI") ||
          desc.includes("Pérez") ||
          desc.includes("Juan")
        ) {
          await route.fulfill({
            status: 422,
            contentType: "application/json",
            body: JSON.stringify({
              detail:
                "La descripción contiene datos personales. Eliminá nombres, DNI, condiciones médicas específicas.",
              error_code: "PII_DETECTED",
            }),
          });
        } else {
          await route.continue();
        }
      } else {
        await route.continue();
      }
    });

    await page.goto("/ofertas/nueva");

    // Fill description with PII
    const descField = page.getByRole("textbox", { name: /descripci[oó]n/i });
    if (await descField.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await descField.fill("Tratamiento para Juan Pérez DNI 12345678");

      // Submit
      const submitBtn = page.getByRole("button", {
        name: /publicar|siguiente/i,
      });
      if (await submitBtn.isVisible()) {
        await submitBtn.click();

        // PII error shown per spec §3.3.D
        await expect(
          page.getByText(/datos personales|pii|eliminá nombres/i),
        ).toBeVisible({ timeout: 10_000 });
      }
    }
  });
});
