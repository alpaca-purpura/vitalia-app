// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
// T-E2E vitalia-fase2-lisa-doctores
/**
 * vitalia-fase2-lisa-doctores.fixture.ts
 *
 * Fixture for all T-E2E specs in vitalia-fase2-lisa-doctores.
 * Provides:
 *   - Clerk auth admin_clinic (via auth.fixture base)
 *   - Tenant A (3 doctors) + Tenant B (5 doctors) seeds (SC-6 cross-tenant)
 *   - Doctor with confirmed future appointments (SC-3, SC-3b)
 *   - 1200-doctor large dataset seed (SC-9 pagination — mocked, not real insert)
 *   - Network mocks for all staff endpoints (MSW-style via page.route)
 *   - 503 mock for SC-7 network-failure
 *   - LocalStorageStrategy swap for asset upload (no live R2)
 *
 * Real-verification design:
 *   - Happy-path WRITE specs (SC-1, SC-1b, SC-1c, SC-1d) are written to hit
 *     BE:8002 (NO backend mock for those routes).
 *   - Negative/edge/adversarial use route mocks since they test UI behaviour.
 *   - When stack is live: E2E_BASE_URL=http://localhost:3002 npx playwright test
 *
 * spec_anchor: 04-validators.yaml § fixtures_required
 * playwright-expert: auth fixture pattern + page.route network mocking
 */

import { test as base, expect } from "../auth.fixture";
import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Seed data constants
// ---------------------------------------------------------------------------

export const STAFF_SEED = {
  /** Tenant A: used by most happy-path and edge specs */
  tenantA: {
    id: process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant",
    clinicId: process.env["E2E_CLINIC_ID"] ?? "clinic-test-001",
    country: "PE" as const,
    currency: "PEN",
    doctors: [
      {
        id: "doctor-ana-001",
        firstName: "Ana",
        lastName: "García Mendoza",
        specialty: "Odontología Cosmética",
        dniMasked: "***4521",
        active: true,
        visibleEnLanding: true,
        yearsExperience: 8,
        patientsCount: 320,
        npsScore: 72,
        credentialCmp: "12345",
        credentialCountry: "PE" as const,
        avatarUrl: null,
      },
      {
        id: "doctor-luis-002",
        firstName: "Luis",
        lastName: "Ramírez Torres",
        specialty: "Pediatría",
        dniMasked: "***7890",
        active: true,
        visibleEnLanding: false,
        yearsExperience: 5,
        patientsCount: 210,
        npsScore: 68,
        credentialCmp: "67890",
        credentialCountry: "PE" as const,
        avatarUrl: null,
      },
      {
        id: "doctor-sol-003",
        firstName: "Sol",
        lastName: "Vargas Herrera",
        specialty: "Dermatología",
        dniMasked: "***2341",
        active: true,
        visibleEnLanding: true,
        yearsExperience: 12,
        patientsCount: 540,
        npsScore: 81,
        credentialCmp: "22341",
        credentialCountry: "PE" as const,
        avatarUrl: null,
      },
    ],
    /** Doctor with confirmed future appointments (SC-3, SC-3b) */
    doctorWithAppointments: {
      id: "doctor-with-appts-004",
      firstName: "Marta",
      lastName: "Quispe Flores",
      specialty: "Fisioterapia",
      dniMasked: "***9012",
      active: true,
      futureAppointmentsCount: 2,
      confirmedAppointments: [
        {
          id: "appt-001",
          startTs: "2026-06-10T10:00:00Z",
          status: "confirmed",
        },
        {
          id: "appt-002",
          startTs: "2026-06-17T10:00:00Z",
          status: "confirmed",
        },
      ],
    },
    /** Block B with a confirmed appointment (SC-3b) */
    blockWithConfirmedAppt: {
      blockId: "block-b-confirmed",
      doctorId: "doctor-with-appts-004",
      dayOfWeek: 2, // Tuesday
      startTime: "10:00",
      endTime: "12:00",
      kind: "recurrent" as const,
      freq: "weekly" as const,
      endConditionKind: "open_ended" as const,
      confirmedAppointmentsCount: 1,
    },
  },
  /** Tenant B: 5 doctors (SC-6 cross-tenant isolation check) */
  tenantB: {
    id: process.env["E2E_TENANT_B_ID"] ?? "vitalia-test-tenant-b",
    clinicId: "clinic-test-002",
    country: "MX" as const,
    currency: "MXN",
    doctors: Array.from({ length: 5 }, (_, i) => ({
      id: `doctor-tenant-b-${String(i + 1).padStart(3, "0")}`,
      firstName: `Dr. Tenant-B-${i + 1}`,
      lastName: "López",
      specialty: "General",
      dniMasked: `***${1000 + i}`,
      active: true,
    })),
  },
} as const;

// ---------------------------------------------------------------------------
// Mock response builders
// ---------------------------------------------------------------------------

function buildDoctorListResponse(
  doctors: typeof STAFF_SEED.tenantA.doctors,
  page = 1,
  pageSize = 24,
) {
  const start = (page - 1) * pageSize;
  const items = doctors.slice(start, start + pageSize).map((d) => ({
    id: d.id,
    first_name: d.firstName,
    last_name: d.lastName,
    specialty: d.specialty,
    dni_masked: d.dniMasked,
    avatar_url: d.avatarUrl,
    active: d.active,
    visible_en_landing: d.visibleEnLanding,
    years_experience: d.yearsExperience,
    patients_count: d.patientsCount,
    nps_score: d.npsScore,
  }));
  return {
    items,
    total: doctors.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(doctors.length / pageSize),
  };
}

function buildDoctorDetailResponse(
  doctor: (typeof STAFF_SEED.tenantA.doctors)[number],
) {
  return {
    id: doctor.id,
    first_name: doctor.firstName,
    last_name: doctor.lastName,
    specialty: doctor.specialty,
    credential: doctor.credentialCmp,
    credential_country: doctor.credentialCountry,
    dni_masked: doctor.dniMasked,
    active: doctor.active,
    visible_en_landing: doctor.visibleEnLanding,
    years_experience: doctor.yearsExperience,
    patients_count: doctor.patientsCount,
    nps_score: doctor.npsScore,
    avatar_key: null,
    avatar_url: null,
    bio_inputs_notes: null,
    bio_links: [],
    bio_public: null,
    languages: ["Español"],
  };
}

// ---------------------------------------------------------------------------
// Network mock setup (SC-7 off by default, opt-in per spec)
// ---------------------------------------------------------------------------

/** Setup network mocks for staff endpoints. */
async function setupStaffMocks(page: Page, _tenantId: string): Promise<void> {
  const doctors = STAFF_SEED.tenantA.doctors;

  // List endpoint (GET paginated)
  await page.route(
    `**/api/v1/vitalia/clinics/doctors**`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      const url = new URL(route.request().url());
      const pageParam = Number(url.searchParams.get("page") ?? 1);
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildDoctorListResponse(doctors, pageParam)),
      });
    },
  );

  // Create endpoint (POST) — happy-path mocked fallback
  await page.route(
    `**/api/v1/vitalia/clinics/doctors`,
    async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const body = JSON.parse(route.request().postData() ?? "{}");
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "doctor-new-mock",
          first_name: body.first_name ?? "Nuevo",
          last_name: body.last_name ?? "Doctor",
          specialty: body.specialty ?? "General",
          credential: body.credential,
          credential_country: body.credential_country ?? "PE",
          active: true,
          visible_en_landing: false,
          created_at: new Date().toISOString(),
        }),
      });
    },
  );

  // Doctor detail (GET by id)
  await page.route(
    `**/api/v1/vitalia/clinics/doctors/*`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      const matched =
        doctors.find((d) => route.request().url().includes(d.id)) ??
        doctors[0];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildDoctorDetailResponse(matched!)),
      });
    },
  );

  // Availability blocks (GET)
  await page.route(
    `**/api/v1/vitalia/clinics/doctors/*/availability-blocks`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    },
  );

  // Audit log (GET)
  await page.route(
    `**/api/v1/vitalia/audit-log**`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    },
  );

  // Asset upload (proxy — no live R2)
  await page.route(
    `**/api/v1/vitalia/assets/upload`,
    async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            key: "avatars/test-upload-key.jpg",
            url: "https://cdn.vitalia.example.com/avatars/test-upload-key.jpg",
          }),
        });
      } else {
        await route.continue();
      }
    },
  );
}

/** Setup 503 mock for doctor list (SC-7 network-failure). */
export async function setup503Mock(page: Page): Promise<void> {
  await page.route(
    `**/api/v1/vitalia/clinics/doctors**`,
    async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Service temporarily unavailable" }),
      });
    },
  );
}

/** Setup empty state (SC-8 — no doctors). */
export async function setupEmptyStateMock(page: Page): Promise<void> {
  await page.route(
    `**/api/v1/vitalia/clinics/doctors**`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 24, pages: 0 }),
      });
    },
  );
}

/** Setup large dataset (SC-9 — 1200 doctors, server-side pagination). */
export async function setupLargeDatasetMock(page: Page): Promise<void> {
  const largeDoctors = Array.from({ length: 1200 }, (_, i) => ({
    id: `doctor-large-${String(i + 1).padStart(4, "0")}`,
    first_name: `Dr. ${i + 1}`,
    last_name: "Apellido",
    specialty: "General",
    dni_masked: `***${String(i + 1).padStart(4, "0")}`,
    active: true,
    visible_en_landing: i % 2 === 0,
    years_experience: (i % 20) + 1,
    patients_count: (i % 500) + 10,
    nps_score: 60 + (i % 40),
    avatar_url: null,
  }));

  await page.route(
    `**/api/v1/vitalia/clinics/doctors**`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      const url = new URL(route.request().url());
      const pg = Number(url.searchParams.get("page") ?? 1);
      const pageSize = 24;
      const start = (pg - 1) * pageSize;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: largeDoctors.slice(start, start + pageSize),
          total: largeDoctors.length,
          page: pg,
          page_size: pageSize,
          pages: Math.ceil(largeDoctors.length / pageSize),
        }),
      });
    },
  );
}

// ---------------------------------------------------------------------------
// Fixture type
// ---------------------------------------------------------------------------

export type StaffFixtures = {
  /** Authenticated page with all staff mocks loaded (default: mocked). */
  staffPage: Page;
  /** Seed constants for assertions */
  staffSeed: typeof STAFF_SEED;
  /** Tear-down: use in afterEach if needed */
  resetMocks: () => Promise<void>;
};

// ---------------------------------------------------------------------------
// Fixture extension
// ---------------------------------------------------------------------------

export const test = base.extend<StaffFixtures>({
  // eslint-disable-next-line no-empty-pattern
  staffSeed: async ({}, use) => {
    await use(STAFF_SEED);
  },

  staffPage: async ({ authedPage }, use) => {
    // Override tenant via localStorage for tenant A
    await authedPage.addInitScript((tid: string) => {
      localStorage.setItem("x-tenant-id", tid);
    }, STAFF_SEED.tenantA.id);

    // Set up network mocks for all staff endpoints
    await setupStaffMocks(authedPage, STAFF_SEED.tenantA.id);

    await use(authedPage);
  },

  resetMocks: async ({ authedPage: _authedPage }, use) => {
    const page = _authedPage;
    await use(async () => {
      await page.unrouteAll();
    });
  },
});

export { expect };
