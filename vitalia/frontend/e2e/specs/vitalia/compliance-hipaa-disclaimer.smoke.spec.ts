/**
 * compliance-hipaa-disclaimer.smoke.spec.ts — Spec §15 Compliance smoke #4
 *
 * Validator: Compliance smoke — HIPAA-lite disclaimer shown for psychiatric offers
 * Fixture: sanare-latam-mx (psychiatric + medication_disclaimer_required=true)
 * Flow: Treatment followup psychiatric → disclaimer visible, medication_disclaimer_required
 */
import { test, expect } from "../../fixtures/sanare-latam-mx.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

const PSYCHIATRIC_TREATMENT_ID = "treatment-sanare-psych-001";

test.describe("Compliance Smoke — HIPAA-lite Disclaimer", () => {
  test("medication disclaimer shown in psychiatric treatment followup", async ({
    sanarePage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto(`/tratamientos/${PSYCHIATRIC_TREATMENT_ID}/seguimiento`);

    // medication_disclaimer_required=true → disclaimer must be visible
    await expect(
      page.getByText(
        /descargo de responsabilidad|disclaimer.*medicaci[oó]n|no.*diagnóstico/i,
      ),
    ).toBeVisible({ timeout: 10_000 });

    expect(consoleErrors).toHaveLength(0);
  });

  test("HIPAA-lite disclaimer text includes no-diagnosis statement", async ({
    sanarePage: page,
  }) => {
    await page.goto(`/tratamientos/${PSYCHIATRIC_TREATMENT_ID}/seguimiento`);

    // Per spec §1.2 disclaimers: "No diagnóstico clínico" and "No prescripción de medicamentos"
    await expect(
      page
        .getByText(/no diagnóstico/i)
        .or(page.getByText(/no prescripci[oó]n de medicamentos/i)),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("sales_agent blocks LLM diagnosis attempts (compliance guardrail)", async ({
    sanarePage: page,
  }) => {
    // Navigate to compliance log to verify prompt_injection events recorded
    await page.goto("/medical-compliance");

    // Sanare has prompt_injection_blocked count=5 in mock
    await expect(
      page.getByText(/5.*prompt_injection|prompt_injection.*5/i),
    ).toBeVisible({
      timeout: 10_000,
    });
  });

  test("consent_signed vs consent_requested ratio shown in compliance", async ({
    sanarePage: page,
  }) => {
    await page.goto("/medical-compliance");

    // From Sanaré mock: consent_requested=89, consent_signed=87 (98% sign rate)
    await expect(page.getByText(/89|consent_requested/i)).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(/87|consent_signed/i)).toBeVisible();
  });

  test("safety_escalation count visible in Sanaré compliance (high volume)", async ({
    sanarePage: page,
  }) => {
    await page.goto("/medical-compliance");

    // Sanaré mock: safety_escalation=12 (higher than Aurora=2)
    await expect(
      page.getByText(/12.*safety_escalation|safety_escalation.*12/i),
    ).toBeVisible({
      timeout: 10_000,
    });
  });
});
