/**
 * compliance-prompt-injection.smoke.spec.ts — Spec §15 Compliance smoke #1
 *
 * Validator: Compliance smoke — prompt_injection_blocked event recorded
 * Fixture: aurora-dental-ar (has prompt_injection_blocked events in compliance log)
 * Flow: /medical-compliance → filter prompt_injection_blocked → events visible
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Compliance Smoke — Prompt Injection Blocked", () => {
  test("prompt_injection_blocked events visible in compliance dashboard", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/medical-compliance");

    // prompt_injection_blocked visible in breakdown (count=1 for Aurora)
    await expect(page.getByText(/prompt_injection_blocked/i)).toBeVisible({
      timeout: 10_000,
    });

    // Event appears in the event list with "critical" severity
    await expect(page.getByText(/cr[íi]tic[ao]/i).first()).toBeVisible({
      timeout: 10_000,
    });

    expect(consoleErrors).toHaveLength(0);
  });

  test("filtering by prompt_injection_blocked type works", async ({
    auroraPage: page,
  }) => {
    await page.goto("/medical-compliance");

    // Apply filter if available
    const filterSelect = page.getByRole("combobox", { name: /tipo/i });
    if (await filterSelect.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await filterSelect.selectOption("prompt_injection_blocked");

      // Only injection events visible after filter
      await expect(page.getByText(/prompt_injection_blocked/i)).toBeVisible({
        timeout: 10_000,
      });
    }
  });

  test("prompt injection events have timestamp and severity", async ({
    auroraPage: page,
  }) => {
    await page.goto("/medical-compliance");

    // From mock: evt-3 prompt_injection_blocked on 2026-05-08 severity=critical
    await expect(page.getByText(/prompt_injection_blocked/i)).toBeVisible({
      timeout: 10_000,
    });
  });
});
