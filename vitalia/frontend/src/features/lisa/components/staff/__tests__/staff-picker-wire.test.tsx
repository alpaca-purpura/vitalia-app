// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-picker-wire.test.tsx — Vitest tests for the D3-A entity switcher wiring
 * (T-FE-switcher-wire).
 *
 * Covers:
 *   - buildDoctorWorkspaceHref: leaf-preserving navigation target (pure)
 *   - StaffWorkspaceShell renders the EntityPicker via entityIdentitySlot
 *     (slot REPLACES the static identity block — canon §6.3)
 *   - picking another doctor → router.push preserving the CURRENT leaf
 *   - picking the SAME doctor → no navigation (no-op)
 *
 * jsdom layout stubs mirror core EntityPicker.test.tsx (virtual-core measures
 * offsetWidth/offsetHeight which jsdom reports as 0 → stub a real viewport).
 *
 * TDD: written BEFORE the wiring (RED-first).
 *
 * T-FE-switcher-wire vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-delta.md § 2.2 + 04-validators.yaml V-D3A-1
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import {
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import {
  describe,
  it,
  expect,
  vi,
  beforeAll,
  afterAll,
  beforeEach,
} from "vitest";
import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  StaffWorkspaceShell,
  buildDoctorWorkspaceHref,
} from "../workspace/StaffWorkspaceShell";
import type { DoctorDetail } from "../../../types/staff.types";

// ── jsdom layout stubs (virtual-core needs a measurable viewport) ──────────────

const VIEWPORT = 300;
let origOffsetH: PropertyDescriptor | undefined;
let origOffsetW: PropertyDescriptor | undefined;
const origRO = (globalThis as { ResizeObserver?: unknown }).ResizeObserver;

beforeAll(() => {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  (globalThis as { ResizeObserver?: unknown }).ResizeObserver =
    ResizeObserverStub;
  origOffsetH = Object.getOwnPropertyDescriptor(
    HTMLElement.prototype,
    "offsetHeight",
  );
  origOffsetW = Object.getOwnPropertyDescriptor(
    HTMLElement.prototype,
    "offsetWidth",
  );
  Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
    configurable: true,
    get() {
      return VIEWPORT;
    },
  });
  Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
    configurable: true,
    get() {
      return VIEWPORT;
    },
  });
});

afterAll(() => {
  if (origOffsetH)
    Object.defineProperty(HTMLElement.prototype, "offsetHeight", origOffsetH);
  if (origOffsetW)
    Object.defineProperty(HTMLElement.prototype, "offsetWidth", origOffsetW);
  (globalThis as { ResizeObserver?: unknown }).ResizeObserver = origRO;
});

// ── Module mocks ───────────────────────────────────────────────────────────────

const pushMock = vi.fn();
const TENANT = "tenant-route-1";
const DOCTOR_ANA = "doctor-ana-001";
const DOCTOR_LUIS = "doctor-luis-002";
let mockPathname = `/${TENANT}/lisa/staff/${DOCTOR_ANA}/horarios`;

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => mockPathname,
  useParams: () => ({}),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: async () => "test-token",
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-uuid-1",
}));

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-uuid-1",
}));

vi.mock("@/hooks/useCurrentUser", () => ({
  ME_QUERY_KEY: ["me"] as const,
}));

vi.mock("@/stores/tenant-store", () => ({
  useTenantStore: (selector: (s: unknown) => unknown) =>
    selector({
      availableTenants: [{ id: "tenant-uuid-1", role: "owner" }],
      activeTenant: { id: "tenant-uuid-1", role: "owner" },
    }),
}));

const fetchClientMock = vi.fn();
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: (...args: unknown[]) => fetchClientMock(...args),
}));

// ── Fixtures ───────────────────────────────────────────────────────────────────

const ANA: DoctorDetail = {
  id: DOCTOR_ANA,
  firstName: "Ana",
  lastName: "García Mendoza",
  specialty: "Odontología Cosmética",
  active: true,
  credential: "12345",
  credentialCountry: "PE",
} as DoctorDetail;

const PICKER_PAGE = {
  items: [
    {
      id: DOCTOR_ANA,
      firstName: "Ana",
      lastName: "García Mendoza",
      specialty: "Odontología Cosmética",
      active: true,
    },
    {
      id: DOCTOR_LUIS,
      firstName: "Luis",
      lastName: "Ramírez Torres",
      specialty: "Pediatría",
      active: true,
    },
  ],
  total: 2,
  page: 1,
  pageSize: 20,
};

function setupFetchMock() {
  fetchClientMock.mockReset();
  fetchClientMock.mockImplementation(async (url: string) => {
    if (url.includes("/users/me")) return { id: "user-db-uuid-1" };
    if (url.includes("/clinics/doctors?")) return PICKER_PAGE;
    if (url.includes(`/clinics/doctors/${DOCTOR_ANA}`)) return ANA;
    return ANA;
  });
}

function renderShell() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <StaffWorkspaceShell
        tenantId={TENANT}
        doctorId={DOCTOR_ANA}
        initialDoctor={ANA}
      >
        <div data-testid="leaf-content" />
      </StaffWorkspaceShell>
    </QueryClientProvider>,
  );
}

// ── buildDoctorWorkspaceHref (pure leaf-preserve) ──────────────────────────────

describe("buildDoctorWorkspaceHref", () => {
  it("preserves the current leaf (horarios → horarios) — SC-D3A-1", () => {
    expect(
      buildDoctorWorkspaceHref(
        TENANT,
        DOCTOR_LUIS,
        `/${TENANT}/lisa/staff/${DOCTOR_ANA}/horarios`,
      ),
    ).toBe(`/${TENANT}/lisa/staff/${DOCTOR_LUIS}/horarios`);
  });

  it("preserves servicios", () => {
    expect(
      buildDoctorWorkspaceHref(
        TENANT,
        DOCTOR_LUIS,
        `/${TENANT}/lisa/staff/${DOCTOR_ANA}/servicios`,
      ),
    ).toBe(`/${TENANT}/lisa/staff/${DOCTOR_LUIS}/servicios`);
  });

  it("preserves pagina (4th leaf, forward-compat D3-D)", () => {
    expect(
      buildDoctorWorkspaceHref(
        TENANT,
        DOCTOR_LUIS,
        `/${TENANT}/lisa/staff/${DOCTOR_ANA}/pagina`,
      ),
    ).toBe(`/${TENANT}/lisa/staff/${DOCTOR_LUIS}/pagina`);
  });

  it("falls back to perfil when the leaf segment is missing", () => {
    expect(
      buildDoctorWorkspaceHref(
        TENANT,
        DOCTOR_LUIS,
        `/${TENANT}/lisa/staff/${DOCTOR_ANA}`,
      ),
    ).toBe(`/${TENANT}/lisa/staff/${DOCTOR_LUIS}/perfil`);
  });

  it("falls back to perfil on null pathname", () => {
    expect(buildDoctorWorkspaceHref(TENANT, DOCTOR_LUIS, null)).toBe(
      `/${TENANT}/lisa/staff/${DOCTOR_LUIS}/perfil`,
    );
  });

  it("falls back to perfil on an unknown trailing segment", () => {
    expect(
      buildDoctorWorkspaceHref(
        TENANT,
        DOCTOR_LUIS,
        `/${TENANT}/lisa/staff/${DOCTOR_ANA}/what-ever`,
      ),
    ).toBe(`/${TENANT}/lisa/staff/${DOCTOR_LUIS}/perfil`);
  });
});

// ── StaffWorkspaceShell wiring ─────────────────────────────────────────────────

describe("StaffWorkspaceShell — EntityPicker via entityIdentitySlot", () => {
  beforeEach(() => {
    pushMock.mockReset();
    mockPathname = `/${TENANT}/lisa/staff/${DOCTOR_ANA}/horarios`;
    setupFetchMock();
  });

  it("renders the picker trigger inside the identity slot (replaces static block)", async () => {
    renderShell();
    // Slot wrapper from core EntitySubNavBar (T-CORE)
    expect(screen.getByTestId("entity-identity-slot")).toBeInTheDocument();
    // Picker trigger shows the active doctor's name
    const trigger = screen.getByTestId("doctor-picker-trigger");
    expect(trigger).toHaveTextContent("Ana García Mendoza");
    // Static identity block must NOT render when the slot is provided
    expect(
      screen.queryByLabelText(/Editando: Ana García Mendoza/),
    ).not.toBeInTheDocument();
  });

  it("picking another doctor navigates PRESERVING the current leaf (SC-D3A-1)", async () => {
    renderShell();
    fireEvent.click(screen.getByTestId("doctor-picker-trigger"));
    const option = await screen.findByTestId(
      `doctor-picker-option-${DOCTOR_LUIS}`,
    );
    fireEvent.click(option);
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith(
        `/${TENANT}/lisa/staff/${DOCTOR_LUIS}/horarios`,
      );
    });
  });

  it("picking the SAME doctor does not navigate (no-op)", async () => {
    renderShell();
    fireEvent.click(screen.getByTestId("doctor-picker-trigger"));
    const option = await screen.findByTestId(
      `doctor-picker-option-${DOCTOR_ANA}`,
    );
    fireEvent.click(option);
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("picker search requests hit the server with active=true (RN-D3A-2)", async () => {
    renderShell();
    fireEvent.click(screen.getByTestId("doctor-picker-trigger"));
    await screen.findByTestId(`doctor-picker-option-${DOCTOR_LUIS}`);
    const listCall = fetchClientMock.mock.calls.find(
      (c) => typeof c[0] === "string" && (c[0] as string).includes("/clinics/doctors?"),
    );
    expect(listCall?.[0]).toContain("active=true");
  });
});
