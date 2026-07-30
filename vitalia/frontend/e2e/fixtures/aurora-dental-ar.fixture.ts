/**
 * aurora-dental-ar.fixture.ts — Clínica Dental Aurora (AR)
 *
 * Fixture: AR dental clinic, plan_tier=clinic
 * country=AR, clinic_type=dental, currency=USD
 * voice: voseo permitido per personality_profile
 *
 * Seeded by: vitalia/backend/scripts/seed_fixture_clinics.py
 * Spec: § 13.1 Aurora dental
 */
import { test as base, expect } from "../auth.fixture";
import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Aurora fixture data constants (mirror seed_fixture_clinics.py)
// ---------------------------------------------------------------------------

export const AURORA_FIXTURE = {
  tenantId: process.env["AURORA_TENANT_ID"] ?? "aurora-dental-ar-test",
  clinicName: "Clínica Dental Aurora",
  clinicType: "dental" as const,
  country: "AR",
  city: "Buenos Aires",
  planTier: "clinic" as const,
  currency: "USD",
  doctors: [
    { name: "Dra. González", specialty: "Implantología" },
    { name: "Dr. Martínez", specialty: "Ortodoncia" },
    { name: "Dra. Romero", specialty: "Odontología general" },
  ],
  sampleOffer: {
    name: "Implante Dental Premium",
    type: "dental_implant",
    priceUsd: 500,
    depositPercent: 30,
  },
  patientName: "Juan Pérez",
  brandPrimary: "#0EA5E9",
  brandSecondary: "#0F172A",
  brandAccent: "#FBBF24",
} as const;

// ---------------------------------------------------------------------------
// Fixture type extensions
// ---------------------------------------------------------------------------

export type AuroraFixtures = {
  /** Pre-authenticated page set up for Aurora Dental AR tenant */
  auroraPage: Page;
  /** Aurora tenant fixture data */
  aurora: typeof AURORA_FIXTURE;
};

// ---------------------------------------------------------------------------
// Mock API responses for Aurora (network mocking via page.route)
// ---------------------------------------------------------------------------

async function setupAuroraMocks(page: Page): Promise<void> {
  // Mock: clinic profile API
  await page.route(
    "**/api/v1/vitalia/onboarding/clinic-profile",
    async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            tenant_id: AURORA_FIXTURE.tenantId,
            clinic_name: AURORA_FIXTURE.clinicName,
            clinic_type: AURORA_FIXTURE.clinicType,
            country: AURORA_FIXTURE.country,
            city: AURORA_FIXTURE.city,
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    },
  );

  // Mock: onboarding plans
  await page.route("**/api/v1/vitalia/onboarding/plans", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: "solo_doctor",
          name: "Solo Doctor",
          price_usd: 99,
          max_doctors: 1,
        },
        { id: "clinic", name: "Clínica", price_usd: 199, max_doctors: 10 },
        {
          id: "multi_site",
          name: "Multi-Sede",
          price_usd: 399,
          max_doctors: -1,
        },
      ]),
    });
  });

  // Mock: brand studio sections
  await page.route("**/api/v1/brand-studio/sections**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          enabled_sections: ["identity", "contact", "team", "testimonials"],
          sections: {
            identity: {
              clinic_name: AURORA_FIXTURE.clinicName,
              tagline: "Tu sonrisa, nuestra prioridad",
              primary_color: AURORA_FIXTURE.brandPrimary,
              secondary_color: AURORA_FIXTURE.brandSecondary,
              accent_color: AURORA_FIXTURE.brandAccent,
            },
            contact: {
              address: "Av. Corrientes 1234, CABA",
              phone: "+54-11-4567-8900",
            },
            team: { doctors: AURORA_FIXTURE.doctors },
            testimonials: [
              {
                quote: "Excelente atención, muy profesionales",
                author: "María R.",
                rating: 5,
              },
            ],
          },
        }),
      });
    } else if (route.request().method() === "PATCH") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ saved: true }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: offer presets
  await page.route(
    "**/api/v1/offers/presets/medical_services_v1**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          preset_id: "medical_services_v1",
          label_es: "Servicio médico",
          preset_types: ["dental_implant", "ortodoncia", "consulta_dental"],
          requires_consent: true,
          supports_deposit: true,
        }),
      });
    },
  );

  // Mock: create offer
  await page.route("**/api/v1/offers", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "offer-aurora-implant-001",
          tenant_id: AURORA_FIXTURE.tenantId,
          name: AURORA_FIXTURE.sampleOffer.name,
          status: "draft",
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: available booking slots
  await page.route(
    "**/api/v1/vitalia/bookings/available-slots**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            slot_iso: "2026-05-20T10:00:00Z",
            doctor_id: "dr-martinez",
            doctor_name: "Dr. Martínez",
            available: true,
          },
          {
            slot_iso: "2026-05-20T11:00:00Z",
            doctor_id: "dr-gonzalez",
            doctor_name: "Dra. González",
            available: true,
          },
          {
            slot_iso: "2026-05-21T09:00:00Z",
            doctor_id: "dr-martinez",
            doctor_name: "Dr. Martínez",
            available: true,
          },
        ]),
      });
    },
  );

  // Mock: create booking
  await page.route("**/api/v1/vitalia/bookings", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "booking-aurora-001",
          tenant_id: AURORA_FIXTURE.tenantId,
          offer_id: "offer-aurora-implant-001",
          status: "pending_payment",
          payment_status: "pending",
          amount_paid: null,
          amount_pending: "500.00",
          currency: "USD",
          deposit_percent: AURORA_FIXTURE.sampleOffer.depositPercent,
          slot_iso: "2026-05-20T10:00:00Z",
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: treatment followup
  await page.route("**/api/v1/vitalia/treatments/*/followup", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        treatment_id: "treatment-aurora-001",
        patient_name: AURORA_FIXTURE.patientName,
        treatment_name: "Implante Dental",
        current_step: "D5_control",
        adherence_score: 0.8,
        status: "active",
        milestones: [
          {
            day: 0,
            name: "Cirugía",
            status: "done",
            date_iso: "2026-05-01T09:00:00Z",
          },
          {
            day: 5,
            name: "Control",
            status: "done",
            date_iso: "2026-05-06T10:00:00Z",
          },
          {
            day: 14,
            name: "Sutura",
            status: "upcoming",
            date_iso: "2026-05-15T09:00:00Z",
          },
          { day: 90, name: "Corona", status: "pending", date_iso: null },
        ],
        next_action: {
          type: "sutura_removal",
          date_iso: "2026-05-15T09:00:00Z",
        },
        manual_handoff: { active: false },
      }),
    });
  });

  // Mock: compliance audit log
  await page.route(
    "**/api/v1/vitalia/medical-compliance/events**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total: 347,
          events: [
            {
              id: "evt-1",
              event_type: "consent_signed",
              severity: "info",
              created_at: "2026-05-10T10:00:00Z",
            },
            {
              id: "evt-2",
              event_type: "pii_detected",
              severity: "warning",
              created_at: "2026-05-09T14:00:00Z",
            },
            {
              id: "evt-3",
              event_type: "prompt_injection_blocked",
              severity: "critical",
              created_at: "2026-05-08T08:00:00Z",
            },
          ],
          breakdown: {
            pii_detected: 3,
            consent_requested: 28,
            consent_signed: 27,
            safety_escalation: 2,
            prompt_injection_blocked: 1,
            cross_tenant_attempt: 0,
          },
        }),
      });
    },
  );
}

// ---------------------------------------------------------------------------
// Fixture extension
// ---------------------------------------------------------------------------

export const test = base.extend<AuroraFixtures>({
  aurora: async ({}, use) => {
    await use(AURORA_FIXTURE);
  },

  auroraPage: async ({ authedPage }, use) => {
    // Override tenantId in localStorage for Aurora
    await authedPage.addInitScript((tid: string) => {
      localStorage.setItem("x-tenant-id", tid);
    }, AURORA_FIXTURE.tenantId);

    // Set up Aurora-specific network mocks
    await setupAuroraMocks(authedPage);

    await use(authedPage);
  },
});

export { expect };
