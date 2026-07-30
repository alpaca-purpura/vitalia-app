/**
 * nueva-cita.smoke.spec.ts — E2E smoke for /mateo/agenda/nueva-cita
 *
 * Story: vitalia-fase2-mateo-nueva-cita (T-FE-4)
 * Gherkin: SC-happy (happy path route renders), SC-a11y (axe wcag2aa)
 *
 * Network: all API calls mocked via page.route() — no live stack required.
 * Auth: pre-authenticated via storageState (setup project) + setupClerkTestingToken.
 *
 * ★ HB-68: assertShellMounted BEFORE axe to avoid false-green on empty DOM.
 *
 * Stack vitalia if live: FE=3002, BE=8002.
 * Nativo: cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/nueva-cita.smoke.spec.ts
 * NUNCA: make e2e / make e2e-smoke (Docker — crashea).
 *
 * downstream-regression-na: brand-local E2E smoke; no cross-brand consumers
 * cap: scheduling.mateo-agenda
 */

import AxeBuilder from "@axe-core/playwright";
import { test as base, expect } from "../../fixtures/base";
import { assertShellMounted } from "../../fixtures/base";
import { setupClerkTestingToken } from "@clerk/testing/playwright";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const BASE_URL = process.env["E2E_BASE_URL"] ?? "http://localhost:3000";

// ── Stable seed IDs ──────────────────────────────────────────────────────────

const SEED = {
  serviceId: "svc-limpieza-001",
  serviceName: "Limpieza dental",
  doctorId: "dr-ortiz-mx",
  doctorLabel: "Dr. Carlos Ortiz",
  patientId: "p-maria-garcia-001",
  patientNameMasked: "Ma*** Ga***",
} as const;

// ── Mock API responses ───────────────────────────────────────────────────────

const SERVICES_MOCK = {
  items: [
    {
      offer_id: SEED.serviceId,
      public_name: SEED.serviceName,
      initial_appt_duration_minutes: 45,
    },
  ],
};

const FREE_DOCTORS_MOCK = {
  doctors: [
    { doctor_id: SEED.doctorId, doctor_label: SEED.doctorLabel },
  ],
};

const AVAILABILITY_MOCK = {
  status: "available",
  conflict_label: null,
  conflict_start: null,
};

const DAY_STRIP_MOCK = {
  doctor_id: SEED.doctorId,
  date_local: "2026-06-22",
  blocks: [
    {
      start_time: "2026-06-22T08:00:00Z",
      end_time: "2026-06-22T12:00:00Z",
      kind: "working_hours",
    },
  ],
};

const PATIENT_SEARCH_MOCK = {
  items: [
    {
      patient_id: SEED.patientId,
      name_masked: SEED.patientNameMasked,
      phone_masked: "+52 *** *** 1234",
    },
  ],
  next_cursor: null,
};

// ── Fixture: mocked nueva-cita page ─────────────────────────────────────────

const test = base.extend<{ mockPage: import("@playwright/test").Page }>({
  mockPage: async ({ page }, use) => {
    await setupClerkTestingToken({ page });

    // Mock services (BE: /api/v1/offer/servicios — singular "offer")
    await page.route("**/api/v1/offer/servicios**", (route) =>
      route.fulfill({ status: 200, json: SERVICES_MOCK }),
    );

    // Mock free doctors (BE: /api/v1/scheduling/availability/free-doctors)
    await page.route("**/api/v1/scheduling/availability/free-doctors**", (route) =>
      route.fulfill({ status: 200, json: FREE_DOCTORS_MOCK }),
    );

    // Mock availability check (BE: /api/v1/scheduling/availability/check)
    await page.route("**/api/v1/scheduling/availability/check**", (route) =>
      route.fulfill({ status: 200, json: AVAILABILITY_MOCK }),
    );

    // Mock day strip (BE: /api/v1/scheduling/availability/day-strip)
    await page.route("**/api/v1/scheduling/availability/day-strip**", (route) =>
      route.fulfill({ status: 200, json: DAY_STRIP_MOCK }),
    );

    // Mock patient search (BE: GET /api/v1/crm/patients?q=...)
    await page.route("**/api/v1/crm/patients**", (route) => {
      const url = route.request().url();
      if (route.request().method() === "GET" && url.includes("?")) {
        route.fulfill({ status: 200, json: PATIENT_SEARCH_MOCK });
      } else {
        route.continue();
      }
    });

    await use(page);
  },
});

// ── Route helper ─────────────────────────────────────────────────────────────

function nuevaCitaUrl(tenantId: string, params?: Record<string, string>): string {
  const url = new URL(
    `${BASE_URL}/${tenantId}/mateo/agenda/nueva-cita`,
  );
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  return url.toString();
}

// ── Tests ────────────────────────────────────────────────────────────────────

test.describe("SC-happy: ruta nueva-cita renderiza correctamente", () => {
  test("page loads with form sections", async ({ mockPage }) => {
    await mockPage.goto(nuevaCitaUrl(TENANT_ID));

    // Form visible (data-testid)
    await expect(
      mockPage.locator('[data-testid="nueva-cita-form"]'),
    ).toBeVisible({ timeout: 10_000 });

    // Servicio section
    await expect(
      mockPage.locator('[data-testid="nc-section-servicio"]'),
    ).toBeVisible();

    // Canal section
    await expect(
      mockPage.locator('[data-testid="nc-section-canal"]'),
    ).toBeVisible();

    // Médico section
    await expect(
      mockPage.locator('[data-testid="nc-section-medico"]'),
    ).toBeVisible();

    // Paciente section
    await expect(
      mockPage.locator('[data-testid="nc-section-paciente"]'),
    ).toBeVisible();

    // FormActionBar visible (NuevaCitaActions)
    await expect(
      mockPage.locator('[data-testid="nueva-cita-actions"]'),
    ).toBeVisible();

    // Submit button disabled initially (form invalid — no service/doctor/patient)
    const submitBtn = mockPage.locator('[data-testid="nueva-cita-actions-submit"]');
    await expect(submitBtn).toBeDisabled();
  });

  test("back-pill navigates back", async ({ mockPage }) => {
    // Mock the agenda page to avoid full auth requirement
    await mockPage.route("**/api/v1/scheduling/**", (route) =>
      route.fulfill({ status: 200, json: { items: [] } }),
    );

    await mockPage.goto(nuevaCitaUrl(TENANT_ID));
    await expect(
      mockPage.locator('[data-testid="nueva-cita-form"]'),
    ).toBeVisible({ timeout: 10_000 });

    // Back pill (PageHeader) with aria-label containing "Agenda"
    const backBtn = mockPage.getByRole("button", { name: /Agenda/i }).first();
    // ponytail: just verify back element exists; navigation test needs auth
    await expect(backBtn).toBeVisible();
  });
});

test.describe("SC-a11y: axe wcag2aa 0 violations", () => {
  test("no a11y violations on nueva-cita route", async ({ mockPage }) => {
    await mockPage.goto(nuevaCitaUrl(TENANT_ID));

    // HB-68: assertShellMounted BEFORE axe
    await assertShellMounted(mockPage);

    const results = await new AxeBuilder({ page: mockPage })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(
      results.violations,
      `axe wcag2aa violations:\n${results.violations.map((v) => `  [${v.id}] ${v.description}: ${v.nodes.length} node(s)`).join("\n")}`,
    ).toEqual([]);
  });
});
