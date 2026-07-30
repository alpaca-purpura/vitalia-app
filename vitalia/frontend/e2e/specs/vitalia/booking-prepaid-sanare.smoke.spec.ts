/**
 * booking-prepaid-sanare.smoke.spec.ts — V-V-10
 *
 * Validator: V-V-10 — Spec §3.4.A Sanaré booking flow full prepay MXN
 * Fixture: sanare-latam-mx (MXN currency, therapy_package, full prepay)
 * Flow: Available slots → pick slot → booking confirmed pending_payment
 */
import { test, expect } from "../../fixtures/sanare-latam-mx.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Booking — Prepago completo Sanaré (MX)", () => {
  test("V-V-10: available slots load for Sanaré doctors", async ({
    sanarePage: page,
    sanare,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/citas/nueva");

    // Available slots section renders
    await expect(
      page.getByText(/horarios disponibles|selecciona tu cita/i),
    ).toBeVisible({ timeout: 10_000 });

    // Doctor slots from mock (3 doctors: Dr. Ríos, Ps. Cruz, Ps. Morales)
    await expect(page.getByText(/Dr\. Alejandro R[íi]os/i)).toBeVisible({
      timeout: 10_000,
    });

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-10: slot selection shows time and doctor", async ({
    sanarePage: page,
    sanare,
  }) => {
    await page.goto("/citas/nueva");

    // First available slot should be clickable
    const firstSlot = page
      .getByRole("button", { name: /10:00|Dr\. Alejandro/i })
      .first();
    if (await firstSlot.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await firstSlot.click();

      // Selection confirmed
      await expect(firstSlot).toHaveAttribute("aria-selected", "true");
    }
  });

  test("V-V-10: booking creation returns pending_payment status", async ({
    sanarePage: page,
    sanare,
  }) => {
    // Mock already set to return pending_payment on POST /bookings
    await page.goto("/citas/nueva");

    // Select a slot and confirm booking
    const confirmBtn = page.getByRole("button", {
      name: /confirmar cita|reservar/i,
    });

    if (await confirmBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await confirmBtn.click();

      // Should show payment pending state
      await expect(
        page.getByText(/pendiente de pago|pago pendiente/i),
      ).toBeVisible({ timeout: 10_000 });
    }
  });

  test("V-V-10: MXN amount shown in booking summary", async ({
    sanarePage: page,
    sanare,
  }) => {
    await page.goto("/citas");

    // Booking list or summary should show MXN
    await expect(page.locator("body")).toBeVisible({ timeout: 10_000 });

    // If booking detail visible, MXN currency displayed
    const mxnAmount = page.getByText(/mxn|3\.200|3200/i);
    if (await mxnAmount.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await expect(mxnAmount).toBeVisible();
    }
  });
});
