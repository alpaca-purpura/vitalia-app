/**
 * sanare-latam-mx.fixture.ts — Sanaré LATAM (MX)
 *
 * Fixture: multi-country psychology+psychiatry multi_site
 * Primary country=MX, clinic_type=psychology+psychiatry, multi_currency
 * voice: neutro broad LatAm per personality_profile
 *
 * Seeded by: vitalia/backend/scripts/seed_fixture_clinics.py
 * Spec: § 13.1 Sanaré LATAM
 */
import { test as base, expect } from "../auth.fixture";
import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Sanaré fixture data constants
// ---------------------------------------------------------------------------

export const SANARE_FIXTURE = {
  tenantId: process.env["SANARE_TENANT_ID"] ?? "sanare-latam-mx-test",
  clinicName: "Sanaré LATAM",
  clinicType: "psychology" as const,
  country: "MX",
  city: "Ciudad de México",
  planTier: "multi_site" as const,
  currency: "MXN",
  doctors: [
    { name: "Dr. Alejandro Ríos", specialty: "Psiquiatría" },
    { name: "Ps. Valentina Cruz", specialty: "Psicología clínica" },
    { name: "Ps. Diego Morales", specialty: "Terapia de pareja" },
  ],
  sampleOffer: {
    name: "Paquete 4 sesiones bienestar",
    type: "therapy_package",
    priceMxn: 3200,
    priceUsd: 160,
    sessions: 4,
    prepayType: "full" as const,
  },
  patientName: "Fernanda López",
  multiSitePlaceholder: "Próximamente disponible",
} as const;

// ---------------------------------------------------------------------------
// Fixture type extensions
// ---------------------------------------------------------------------------

export type SanareFixtures = {
  /** Pre-authenticated page set up for Sanaré LATAM MX tenant */
  sanarePage: Page;
  /** Sanaré tenant fixture data */
  sanare: typeof SANARE_FIXTURE;
};

// ---------------------------------------------------------------------------
// Mock API responses for Sanaré
// ---------------------------------------------------------------------------

async function setupSanareMocks(page: Page): Promise<void> {
  // Mock: clinic profile (MX multi_site)
  await page.route(
    "**/api/v1/vitalia/onboarding/clinic-profile",
    async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            tenant_id: SANARE_FIXTURE.tenantId,
            clinic_name: SANARE_FIXTURE.clinicName,
            clinic_type: SANARE_FIXTURE.clinicType,
            country: SANARE_FIXTURE.country,
            city: SANARE_FIXTURE.city,
            multi_site: true,
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    },
  );

  // Mock: plans (all 3 including multi_site)
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

  // Mock: brand studio (multi_site psychology+psychiatry)
  await page.route("**/api/v1/brand-studio/sections**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          enabled_sections: ["identity", "contact", "team", "testimonials"],
          sections: {
            identity: {
              clinic_name: SANARE_FIXTURE.clinicName,
              tagline: "Bienestar mental para toda LatAm",
              primary_color: "#10B981",
              secondary_color: "#064E3B",
              accent_color: "#6EE7B7",
            },
            contact: {
              address: "Col. Roma Norte, CDMX, México",
              phone: "+52-55-1234-5678",
            },
            team: { doctors: SANARE_FIXTURE.doctors },
            testimonials: [
              {
                quote:
                  "El Dr. Ríos me ayudó con mi medicación. Excelente profesional.",
                author: "Carlos M.",
                rating: 5,
              },
              {
                quote:
                  "La terapia de pareja con la Ps. Cruz fue transformadora",
                author: "Ana y Luis R.",
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

  // Mock: offer presets (packages)
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
            "therapy_package",
            "psychiatric_consultation",
          ],
          requires_consent: false,
          supports_deposit: true,
          supports_recurring: true,
        }),
      });
    },
  );

  // Mock: create offer (packages with multi-currency)
  await page.route("**/api/v1/offers", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "offer-sanare-package-001",
          tenant_id: SANARE_FIXTURE.tenantId,
          name: SANARE_FIXTURE.sampleOffer.name,
          status: "draft",
          currency: "MXN",
          price: "3200.00",
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: available slots (multi-doctor MX)
  await page.route(
    "**/api/v1/vitalia/bookings/available-slots**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            slot_iso: "2026-05-25T10:00:00-06:00",
            doctor_id: "dr-rios",
            doctor_name: "Dr. Alejandro Ríos",
            available: true,
          },
          {
            slot_iso: "2026-05-25T12:00:00-06:00",
            doctor_id: "ps-cruz",
            doctor_name: "Ps. Valentina Cruz",
            available: true,
          },
          {
            slot_iso: "2026-05-26T09:00:00-06:00",
            doctor_id: "ps-morales",
            doctor_name: "Ps. Diego Morales",
            available: true,
          },
        ]),
      });
    },
  );

  // Mock: create booking (multi-currency MXN)
  await page.route("**/api/v1/vitalia/bookings", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "booking-sanare-001",
          tenant_id: SANARE_FIXTURE.tenantId,
          status: "pending_payment",
          payment_status: "pending",
          amount_paid: null,
          amount_pending: "3200.00",
          currency: "MXN",
          deposit_percent: 100,
          slot_iso: "2026-05-25T10:00:00-06:00",
          created_at: new Date().toISOString(),
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Mock: treatment followup (psychiatric medication tracking)
  await page.route("**/api/v1/vitalia/treatments/*/followup", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        treatment_id: "treatment-sanare-psych-001",
        patient_name: SANARE_FIXTURE.patientName,
        treatment_name: "Seguimiento psiquiátrico — SSRI ajuste dosis",
        current_step: "semana_4_control",
        adherence_score: 0.9,
        status: "active",
        milestones: [
          {
            day: 0,
            name: "Consulta inicial",
            status: "done",
            date_iso: "2026-04-01T10:00:00Z",
          },
          {
            day: 14,
            name: "Control 2 semanas",
            status: "done",
            date_iso: "2026-04-15T10:00:00Z",
          },
          {
            day: 28,
            name: "Ajuste dosis",
            status: "upcoming",
            date_iso: "2026-04-29T10:00:00Z",
          },
          {
            day: 90,
            name: "Evaluación 3 meses",
            status: "pending",
            date_iso: null,
          },
        ],
        next_action: { type: "dosis_review", date_iso: "2026-04-29T10:00:00Z" },
        manual_handoff: { active: false },
        medication_disclaimer_required: true,
      }),
    });
  });

  // Mock: compliance events (high volume multi_site)
  await page.route(
    "**/api/v1/vitalia/medical-compliance/events**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total: 1247,
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
              created_at: "2026-05-09T08:00:00Z",
            },
            {
              id: "evt-3",
              event_type: "safety_escalation",
              severity: "critical",
              created_at: "2026-05-08T11:00:00Z",
            },
            {
              id: "evt-4",
              event_type: "prompt_injection_blocked",
              severity: "critical",
              created_at: "2026-05-07T15:00:00Z",
            },
            {
              id: "evt-5",
              event_type: "consent_requested",
              severity: "info",
              created_at: "2026-05-06T09:00:00Z",
            },
          ],
          breakdown: {
            pii_detected: 3,
            consent_requested: 89,
            consent_signed: 87,
            safety_escalation: 12,
            prompt_injection_blocked: 5,
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

export const test = base.extend<SanareFixtures>({
  sanare: async ({}, use) => {
    await use(SANARE_FIXTURE);
  },

  sanarePage: async ({ authedPage }, use) => {
    await authedPage.addInitScript((tid: string) => {
      localStorage.setItem("x-tenant-id", tid);
    }, SANARE_FIXTURE.tenantId);

    await setupSanareMocks(authedPage);

    await use(authedPage);
  },
});

export { expect };
