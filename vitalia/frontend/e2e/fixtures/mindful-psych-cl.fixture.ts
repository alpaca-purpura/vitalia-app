/**
 * mindful-psych-cl.fixture.ts — Centro Mindful Santiago (CL)
 *
 * Fixture: CL psychology solo_doctor
 * country=CL, clinic_type=psychology, currency=CLP/USD
 * voice: neutro (Chilean tuteo) per personality_profile
 *
 * Seeded by: vitalia/backend/scripts/seed_fixture_clinics.py
 * Spec: § 13.1 Mindful Santiago
 */
import { test as base, expect } from "../auth.fixture";
import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Mindful fixture data constants
// ---------------------------------------------------------------------------

export const MINDFUL_FIXTURE = {
  tenantId: process.env["MINDFUL_TENANT_ID"] ?? "mindful-psych-cl-test",
  clinicName: "Centro Mindful Santiago",
  clinicType: "psychology" as const,
  country: "CL",
  city: "Santiago",
  planTier: "solo_doctor" as const,
  currency: "USD",
  doctors: [{ name: "Ps. Carolina Fuentes", specialty: "Psicología clínica" }],
  sampleOffer: {
    name: "Sesión individual orientativa",
    type: "individual_session",
    priceUsd: 80,
    prepayType: "full" as const,
  },
  patientName: "Sofía Torres",
} as const;

// ---------------------------------------------------------------------------
// Fixture type extensions
// ---------------------------------------------------------------------------

export type MindfulFixtures = {
  /** Pre-authenticated page set up for Centro Mindful Santiago tenant */
  mindfulPage: Page;
  /** Mindful tenant fixture data */
  mindful: typeof MINDFUL_FIXTURE;
};

// ---------------------------------------------------------------------------
// Mock API responses for Mindful
// ---------------------------------------------------------------------------

async function setupMindfulMocks(page: Page): Promise<void> {
  // Mock: clinic profile
  await page.route(
    "**/api/v1/vitalia/onboarding/clinic-profile",
    async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            tenant_id: MINDFUL_FIXTURE.tenantId,
            clinic_name: MINDFUL_FIXTURE.clinicName,
            clinic_type: MINDFUL_FIXTURE.clinicType,
            country: MINDFUL_FIXTURE.country,
            city: MINDFUL_FIXTURE.city,
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    },
  );

  // Mock: plans
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
      ]),
    });
  });

  // Mock: brand studio (psychology sections)
  await page.route("**/api/v1/brand-studio/sections**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          enabled_sections: ["identity", "contact", "team", "testimonials"],
          sections: {
            identity: {
              clinic_name: MINDFUL_FIXTURE.clinicName,
              tagline: "Tu bienestar mental, nuestra misión",
              primary_color: "#6366F1",
              secondary_color: "#1E1B4B",
              accent_color: "#A5B4FC",
            },
            contact: {
              address: "Providencia, Santiago, Chile",
              phone: "+56-9-8765-4321",
            },
            team: { doctors: MINDFUL_FIXTURE.doctors },
            testimonials: [
              {
                quote: "La Ps. Fuentes me ayudó a superar mi ansiedad",
                author: "Ana V.",
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

  // Mock: offer presets (psychology)
  await page.route(
    "**/api/v1/offers/presets/medical_services_v1**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          preset_id: "medical_services_v1",
          label_es: "Servicio médico",
          preset_types: [
            "individual_session",
            "orientative_session",
            "group_therapy",
          ],
          requires_consent: false,
          supports_deposit: false,
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
          id: "offer-mindful-session-001",
          tenant_id: MINDFUL_FIXTURE.tenantId,
          name: MINDFUL_FIXTURE.sampleOffer.name,
          status: "draft",
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: available slots (solo doctor)
  await page.route(
    "**/api/v1/vitalia/bookings/available-slots**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            slot_iso: "2026-05-22T14:00:00Z",
            doctor_id: "ps-fuentes",
            doctor_name: "Ps. Carolina Fuentes",
            available: true,
          },
          {
            slot_iso: "2026-05-22T16:00:00Z",
            doctor_id: "ps-fuentes",
            doctor_name: "Ps. Carolina Fuentes",
            available: true,
          },
        ]),
      });
    },
  );

  // Mock: create booking (full prepay)
  await page.route("**/api/v1/vitalia/bookings", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "booking-mindful-001",
          tenant_id: MINDFUL_FIXTURE.tenantId,
          status: "pending_payment",
          payment_status: "pending",
          amount_paid: null,
          amount_pending: "80.00",
          currency: "USD",
          deposit_percent: 100,
          slot_iso: "2026-05-22T14:00:00Z",
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: treatment followup (N/A for psychology — empty state)
  await page.route("**/api/v1/vitalia/treatments/*/followup", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        treatment_id: null,
        status: "empty",
        message: "Sin tratamientos activos para este paciente",
      }),
    });
  });

  // Mock: compliance events (minimal for psychology)
  await page.route(
    "**/api/v1/vitalia/medical-compliance/events**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total: 52,
          events: [
            {
              id: "evt-1",
              event_type: "consent_signed",
              severity: "info",
              created_at: "2026-05-10T10:00:00Z",
            },
          ],
          breakdown: {
            pii_detected: 0,
            consent_requested: 5,
            consent_signed: 5,
            safety_escalation: 0,
            prompt_injection_blocked: 0,
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

export const test = base.extend<MindfulFixtures>({
  mindful: async ({}, use) => {
    await use(MINDFUL_FIXTURE);
  },

  mindfulPage: async ({ authedPage }, use) => {
    await authedPage.addInitScript((tid: string) => {
      localStorage.setItem("x-tenant-id", tid);
    }, MINDFUL_FIXTURE.tenantId);

    await setupMindfulMocks(authedPage);

    await use(authedPage);
  },
});

export { expect };
