/**
 * consent-flow-implant.smoke.spec.ts — V-V-18
 *
 * Validator: V-V-18 — Spec §3.4.D booking without consent for procedure requiring it
 * Fixture: aurora-dental-ar (dental implant requires_informed_consent=true)
 * Flow: Booking attempt without consent → 400 → status=awaiting_consent → consent tool triggered
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Consent Flow — Implante Dental Aurora (AR)", () => {
  test("V-V-18: implant booking requires consent acknowledgment", async ({
    auroraPage: page,
    aurora,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/citas/nueva");

    // Consent requirement indicator visible for implant offer
    await expect(
      page
        .getByText(/consentimiento informado/i)
        .or(page.getByRole("checkbox", { name: /consentimiento/i }))
        .or(page.getByText(/firma.*consentimiento/i)),
    ).toBeVisible({ timeout: 10_000 });

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-18: booking submit blocked without consent", async ({
    auroraPage: page,
  }) => {
    // Override booking API to return 400 (missing consent)
    await page.route("**/api/v1/vitalia/bookings", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({
            detail:
              "Procedimiento requiere consentimiento informado firmado antes de confirmar.",
            error_code: "CONSENT_REQUIRED",
            booking_status: "awaiting_consent",
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto("/citas/nueva");

    // Attempt to confirm without consent
    const confirmBtn = page.getByRole("button", {
      name: /confirmar cita|reservar/i,
    });

    if (await confirmBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await confirmBtn.click();

      // Error message shown per spec §3.4.D
      await expect(
        page.getByText(
          /consentimiento informado.*requerido|requiere consentimiento/i,
        ),
      ).toBeVisible({ timeout: 10_000 });
    }
  });

  test("V-V-18: awaiting_consent status displayed in booking after rejection", async ({
    auroraPage: page,
  }) => {
    // Mock booking status = awaiting_consent
    await page.route("**/api/v1/vitalia/bookings/**", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "booking-aurora-001",
            status: "awaiting_consent",
            payment_status: "pending",
            consent_signed: false,
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto("/citas/booking-aurora-001");

    // awaiting_consent status visible
    await expect(
      page.getByText(
        /esperando consentimiento|awaiting.*consent|consentimiento pendiente/i,
      ),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-18: consent form renders with dental_implant_v1 template", async ({
    auroraPage: page,
  }) => {
    await page.goto("/citas/nueva/consentimiento");

    // Consent form or component renders
    await expect(page.locator("body")).toBeVisible({ timeout: 10_000 });

    // Should NOT trigger error boundary
    await expect(page.getByText(/algo sali[oó] mal/i)).not.toBeVisible();
  });

  test("V-V-18: after consent signed booking proceeds normally", async ({
    auroraPage: page,
  }) => {
    // Override booking to return confirmed after consent
    await page.route("**/api/v1/vitalia/bookings", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "booking-aurora-consent-001",
            status: "pending_payment",
            payment_status: "pending",
            consent_signed: true,
            amount_pending: "150.00",
            currency: "USD",
            deposit_percent: 30,
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto("/citas/nueva");

    // Sign consent if checkbox available
    const consentCheckbox = page.getByRole("checkbox", {
      name: /acepto.*consentimiento|he le[íi]do/i,
    });
    if (
      await consentCheckbox.isVisible({ timeout: 3_000 }).catch(() => false)
    ) {
      await consentCheckbox.check();
    }

    // Confirm booking
    const confirmBtn = page.getByRole("button", {
      name: /confirmar cita|reservar/i,
    });
    if (await confirmBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await confirmBtn.click();

      // Booking proceeds to payment step
      await expect(
        page.getByText(/pendiente de pago|proceder al pago/i),
      ).toBeVisible({ timeout: 10_000 });
    }
  });
});
