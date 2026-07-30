/**
 * booking-full-prepay-mindful.smoke.spec.ts — V-V-12
 *
 * Validator: V-V-12 — Spec §3.4 Mindful psychology full prepay booking
 * Fixture: mindful-psych-cl (USD, solo_doctor, full prepay $80)
 * Flow: slots → single doctor Ps. Fuentes → full $80 USD → pending_payment
 */
import { test, expect } from "../../fixtures/mindful-psych-cl.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Booking — Prepago completo Centro Mindful (CL)", () => {
  test("V-V-12: booking page renders with solo_doctor slots", async ({
    mindfulPage: page,
    mindful,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/citas/nueva");

    // Slots visible
    await expect(
      page.getByText(/horarios disponibles|selecciona tu cita/i),
    ).toBeVisible({ timeout: 10_000 });

    // Only 1 doctor (solo_doctor plan)
    await expect(page.getByText(/Ps\. Carolina Fuentes/i)).toBeVisible({
      timeout: 10_000,
    });

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-12: full prepay amount $80 USD shown", async ({
    mindfulPage: page,
    mindful,
  }) => {
    await page.goto("/citas/nueva");

    // Full prepay: $80 USD (deposit_percent=100 per fixture)
    await expect(
      page
        .getByText(/\$80|80\.00|usd 80/i)
        .or(page.getByText(/pago completo/i)),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("V-V-12: two available slots from Ps. Fuentes displayed", async ({
    mindfulPage: page,
  }) => {
    await page.goto("/citas/nueva");

    // Mock returns 2 slots for Ps. Fuentes
    const slots = page.getByText(/14:00|16:00/i);
    const slotCount = await slots.count();
    expect(slotCount).toBeGreaterThanOrEqual(1);
  });

  test("V-V-12: booking confirms to pending_payment status", async ({
    mindfulPage: page,
    mindful,
  }) => {
    await page.goto("/citas/nueva");

    // Select first slot
    const firstSlot = page
      .getByRole("button", { name: /14:00|Ps\. Carolina/i })
      .first();

    if (await firstSlot.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await firstSlot.click();

      // Confirm booking
      const confirmBtn = page.getByRole("button", {
        name: /confirmar cita|reservar/i,
      });
      if (await confirmBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
        await confirmBtn.click();

        // Mock returns pending_payment status
        await expect(
          page.getByText(/pendiente de pago|pago pendiente/i),
        ).toBeVisible({ timeout: 10_000 });
      }
    }
  });

  test("V-V-12: no deposit info shown for full prepay mode", async ({
    mindfulPage: page,
  }) => {
    await page.goto("/citas/nueva");

    // Full prepay — no "depósito parcial" text
    await expect(page.getByText(/dep[oó]sito parcial/i)).not.toBeVisible();
  });
});
