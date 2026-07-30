// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff.ts — MSW handlers for Staff directory API endpoints.
 *
 * Includes:
 *   - GET /api/v1/vitalia/clinics/doctors — list (with 503 variant for SC-7)
 *   - POST /api/v1/vitalia/clinics/doctors — create
 *   - GET /api/v1/vitalia/clinics/doctors/:id — detail
 *   - PATCH /api/v1/vitalia/clinics/doctors/:id — patch
 *
 * PHI-safe mock data: no real DNI/email/phone values.
 * Spanish neutro LatAm names — no voseo.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § MSW + 01-spec.md § SC-7
 * downstream-regression-na: brand-local vitalia FE mocks; no cross-brand consumers
 */

import { http, HttpResponse, delay } from "msw";
import type { DoctorListItem, DoctorDetail, PaginatedDoctors } from "../../features/lisa/types/staff.types";

const BASE = "http://localhost:8002";
const DOCTORS_PATH = `${BASE}/api/v1/vitalia/clinics/doctors`;

// ── Mock data (PHI-safe) ────────────────────────────────────────────────────────

// F1 fix: MSW mock data now mirrors the REAL BE camelCase contract (alias_generator=to_camel).
// Previously used "dniMasked" (FE-invented name); BE actually emits "maskedDni" (camelCase of masked_dni).
// The stats fields (patientsCount, npsScore) are nullable — no backend source yet, BE returns null.
// avatarUrl is not in the list DTO — only avatarKey (storage key). avatarUrl can be derived client-side.
const MOCK_DOCTORS: DoctorListItem[] = [
  {
    id: "doc-001",
    firstName: "Ana",
    lastName: "García Robles",
    displayName: "Ana García Robles",
    specialty: "Odontología cosmética",
    avatarKey: null,
    avatarUrl: null,
    yearsExperience: 8,
    patientsCount: null,
    npsScore: null,
    maskedDni: "***456",
    maskedEmail: "a***@test-vitalia.com",
    active: true,
    visibleEnLanding: false,
    createdAt: "2026-01-15T10:00:00Z",
  },
  {
    id: "doc-002",
    firstName: "Luis",
    lastName: "Morales Vera",
    displayName: "Luis Morales Vera",
    specialty: "Medicina estética",
    avatarKey: null,
    avatarUrl: null,
    yearsExperience: 5,
    patientsCount: null,
    npsScore: null,
    maskedDni: "***789",
    maskedEmail: "l***@test-vitalia.com",
    active: true,
    visibleEnLanding: false,
    createdAt: "2026-02-01T10:00:00Z",
  },
  {
    id: "doc-003",
    firstName: "Sol",
    lastName: "Paredes Castro",
    displayName: "Sol Paredes Castro",
    specialty: "Dermatología",
    avatarKey: null,
    avatarUrl: null,
    yearsExperience: 12,
    patientsCount: null,
    npsScore: null,
    maskedDni: "***012",
    maskedEmail: "s***@test-vitalia.com",
    active: true,
    visibleEnLanding: true,
    createdAt: "2025-11-10T10:00:00Z",
  },
];

const MOCK_DOCTOR_DETAIL: DoctorDetail = {
  id: "doc-001",
  firstName: "Ana",
  lastName: "García Robles",
  dni: "12345456", // Not real
  email: "ana.garcia@test-vitalia.com",
  phone: "+51 999 000 111",
  specialty: "Odontología cosmética",
  credential: "12345",
  credentialCountry: "PE",
  yearsExperience: 8,
  languages: ["es", "en"],
  bioInputsNotes: null,
  bioLinks: [],
  bioPublic: null,
  avatarKey: null,
  avatarUrl: null,
  visibleEnLanding: false,
  active: true,
  createdAt: "2026-01-15T10:00:00Z",
  updatedAt: "2026-05-31T08:00:00Z",
};

// ── Handlers ───────────────────────────────────────────────────────────────────

export const staffHandlers = [
  // GET /doctors — list (paginated)
  http.get(`${DOCTORS_PATH}`, async ({ request }) => {
    await delay(150);
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? "1");
    const pageSize = Number(url.searchParams.get("page_size") ?? "24");

    const response: PaginatedDoctors = {
      items: MOCK_DOCTORS,
      total: MOCK_DOCTORS.length,
      page,
      pageSize,
    };
    return HttpResponse.json(response);
  }),

  // POST /doctors — create
  http.post(`${DOCTORS_PATH}`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as Record<string, unknown>;

    // Simulate credential validation (SC-2: PE must be numeric)
    if (
      body["credential_country"] === "PE" &&
      typeof body["credential"] === "string" &&
      !/^\d+$/.test(body["credential"])
    ) {
      return HttpResponse.json(
        {
          detail: [
            {
              loc: ["body", "credential"],
              msg: "La credencial CMP debe ser numérica",
              type: "value_error",
            },
          ],
        },
        { status: 422 },
      );
    }

    // Return created doctor
    const created: DoctorDetail = {
      ...MOCK_DOCTOR_DETAIL,
      id: `doc-${Date.now()}`,
      firstName: String(body["first_name"] ?? ""),
      lastName: String(body["last_name"] ?? ""),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    return HttpResponse.json(created, { status: 201 });
  }),

  // GET /doctors/:id — detail
  http.get(`${DOCTORS_PATH}/:doctorId`, async ({ params }) => {
    await delay(100);
    const doctorId = params["doctorId"] as string;
    if (doctorId === "doc-001") {
      return HttpResponse.json(MOCK_DOCTOR_DETAIL);
    }
    const found = MOCK_DOCTORS.find((d) => d.id === doctorId);
    if (!found) {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    return HttpResponse.json({ ...MOCK_DOCTOR_DETAIL, id: doctorId, firstName: found.firstName, lastName: found.lastName });
  }),

  // PATCH /doctors/:id — patch
  http.patch(`${DOCTORS_PATH}/:doctorId`, async ({ request }) => {
    await delay(150);
    const body = await request.json();
    return HttpResponse.json({
      ...MOCK_DOCTOR_DETAIL,
      ...(body as object),
      updatedAt: new Date().toISOString(),
    });
  }),
];

// ── 503 handler variant for SC-7 (network failure testing) ────────────────────
// Usage in tests: server.use(staffHandlers503.doctors503)

export const staffHandlers503 = {
  /** Override GET /doctors to return 503 (SC-7: network failure banner) */
  doctors503: http.get(`${DOCTORS_PATH}`, async () => {
    await delay(50);
    return HttpResponse.json(
      { detail: "Service temporarily unavailable" },
      { status: 503 },
    );
  }),
};
