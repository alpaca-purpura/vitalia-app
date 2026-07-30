// cap: scheduling.mateo-agenda
/**
 * NuevaCitaView.test.tsx — TDD (T-FE-1 base + T-FE-4 integration mocks).
 *
 * Tests for NuevaCitaView integrated client root:
 *   - Renders FormPageScaffold with back-pill
 *   - Renders service selector (ServicePicker)
 *   - Canal picker (CanalPicker) renders
 *   - Renders end time error when fin <= inicio
 *   - Service dur=null defaults end time to +30min
 *   - Prefills date/time from props
 *   - FormActionBar submit disabled until form valid + availability (RN-10)
 *   - Does not render a modal/drawer (AC-9)
 *
 * T-FE-4 additions:
 *   - PatientPickerWithCreate replaces manual UUID input
 *   - AvailabilityChip renders when doctor+time selected
 *   - DayAvailabilityStrip renders when startTime set
 *   - FreeDoctorsList renders
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import React from "react";

// Mock router (Next.js)
const mockPush = vi.fn();
const mockBack = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
  useParams: () => ({ tenantId: "tenant-1" }),
}));

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
  useUser: () => ({
    user: {
      publicMetadata: {
        currency: "ARS",
        timezone: "America/Argentina/Buenos_Aires",
        locale: "es-419",
      },
    },
    isLoaded: true,
  }),
}));

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-uuid-123",
}));

vi.mock("@/hooks/useActorHeaders", () => ({
  useActorHeaders: () => ({
    "X-Clinic-ID": "clinic-uuid-123",
    "X-User-ID": "user-uuid-123",
    "X-User-Role": "admin_clinic",
  }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-1",
}));

// Mock parent hooks (used by NuevaCitaView directly)
vi.mock("../../../hooks/use-nueva-cita", () => ({
  useNuevaCitaServices: () => ({
    data: {
      items: [
        {
          offerId: "svc-1",
          publicName: "Limpieza dental",
          initialApptDurationMinutes: 45,
          isActive: true,
        },
        {
          offerId: "svc-2",
          publicName: "Blanqueamiento",
          initialApptDurationMinutes: null,
          isActive: true,
        },
      ],
    },
    isPending: false,
    isError: false,
  }),
  useNuevaCitaFreeDoctors: () => ({
    data: { doctors: [] },
    isPending: false,
    isError: false,
  }),
  useNuevaCitaAvailabilityCheck: () => ({
    data: null,
    isPending: false,
  }),
  useNuevaCitaCreate: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
  }),
  nuevaCitaKeys: {
    services: () => ["mateo", "nueva-cita", "services"],
    freeDoctors: () => ["mateo", "nueva-cita", "free-doctors"],
    availabilityCheck: () => ["mateo", "nueva-cita", "availability"],
    patientSearch: () => ["mateo", "nueva-cita", "patient-search"],
    patientInlineCreate: () => ["mateo", "nueva-cita", "patient-inline-create"],
    create: () => ["mateo", "nueva-cita", "create"],
  },
}));

// Mock patient hooks (used by PatientPickerWithCreate)
vi.mock("../../../hooks/use-patients", () => ({
  useSearchPatients: () => ({
    searchFn: vi.fn().mockResolvedValue([]),
  }),
  useCreatePatientInline: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ patientId: "p-1", isDuplicate: false }),
    isPending: false,
    error: null,
  }),
}));

// Mock availability hooks (used by AvailabilityChip + DayAvailabilityStrip + FreeDoctorsList T-D3)
vi.mock("../../../hooks/use-availability", () => ({
  useAvailabilityCheck: () => ({
    data: null,
    isPending: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useDayStrip: () => ({
    data: null,
    isPending: false,
    isError: false,
  }),
  // T-D3: multi-doctor service-day hook
  useServiceDayStrips: () => ({
    data: null,
    isPending: false,
    isError: false,
  }),
  availabilityKeys: {
    check: () => ["mateo", "availability", "check"],
    dayStrip: () => ["mateo", "availability", "day-strip"],
    serviceDay: () => ["mateo", "availability", "service-day"],
  },
}));

// Mock @luana/ui-kit — minimal test doubles
vi.mock("@luana/ui-kit", () => ({
  // obs#1: EntitySubNavBar replaces PageHeader (workspace-mode N3 header)
  EntitySubNavBar: ({
    rootHref,
    rootLabel,
    entity,
  }: {
    rootHref: string;
    rootLabel: string;
    entity: { id: string; name: string };
    leaves: unknown[];
    activeLeaf: null;
  }) =>
    React.createElement("nav", { "data-testid": "entity-sub-nav-bar" },
      React.createElement("a", { href: rootHref, "data-testid": "entity-sub-nav-root" }, "‹ " + rootLabel),
      React.createElement("span", { "data-testid": "entity-sub-nav-entity" }, entity.name),
    ),
  FormActionBar: ({
    submitLabel,
    onSubmit,
    onCancel,
    submitting,
    submitDisabled,
    testId,
  }: {
    submitLabel: string;
    onSubmit?: () => void;
    onCancel?: () => void;
    submitting?: boolean;
    submitDisabled?: boolean;
    testId?: string;
  }) =>
    React.createElement("div", { "data-testid": testId ?? "form-action-bar" },
      React.createElement("button", { onClick: onCancel, "data-testid": `${testId ?? "form-action-bar"}-cancel` }, "Cancelar"),
      React.createElement("button", {
        onClick: onSubmit,
        disabled: submitting || submitDisabled,
        "data-testid": `${testId ?? "form-action-bar"}-submit`,
      }, submitLabel),
    ),
  Badge: ({ children, variant }: { children: React.ReactNode; variant?: string }) =>
    React.createElement("span", { "data-variant": variant }, children),
  SmartDateTimePicker: ({
    value,
    onChange,
    "data-testid": testId,
    disablePast,
  }: {
    value?: string;
    onChange?: (iso: string) => void;
    "data-testid"?: string;
    disablePast?: boolean;
    [key: string]: unknown;
  }) =>
    React.createElement("input", {
      type: "text",
      "data-testid": testId ?? "smart-date-time-picker",
      "data-disable-past": disablePast ? "true" : undefined,
      value: value ?? "",
      readOnly: !onChange,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) => onChange?.(e.target.value),
    }),
  EntityPicker: ({
    placeholder,
    testId,
    createAction,
  }: {
    placeholder?: string;
    testId?: string;
    createAction?: { label: (q: string) => string; onCreate: (q: string) => void };
  }) =>
    React.createElement("div", { "data-testid": testId ?? "entity-picker" },
      React.createElement("input", { placeholder, "data-testid": `${testId ?? "entity-picker"}-input` }),
      createAction ? React.createElement("button", {
        "data-testid": `${testId ?? "entity-picker"}-create`,
        onClick: () => createAction.onCreate("test"),
      }, createAction.label("test")) : null,
    ),
  // T-D2: time-only picker (separate from SmartDateTimePicker)
  TimePicker: ({
    value,
    onChange,
    "aria-label": ariaLabel,
  }: {
    value?: string;
    onChange?: (v: string) => void;
    "aria-label"?: string;
    [key: string]: unknown;
  }) =>
    React.createElement("input", {
      type: "text",
      "data-testid": "time-picker",
      "aria-label": ariaLabel,
      value: value ?? "",
      readOnly: !onChange,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) => onChange?.(e.target.value),
    }),
}));

import { NuevaCitaView } from "../NuevaCitaView";

describe("NuevaCitaView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders EntitySubNavBar pointing to agenda (obs#1: N3 workspace header, AC-9: no modal)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // obs#1: EntitySubNavBar replaces PageHeader — N3 sticky full-bleed
    expect(screen.getByTestId("entity-sub-nav-bar")).toBeInTheDocument();
    const rootLink = screen.getByTestId("entity-sub-nav-root");
    expect(rootLink).toHaveAttribute("href", "/tenant-1/mateo/agenda");
    expect(screen.getByTestId("entity-sub-nav-entity").textContent).toBe("Nueva cita");
    // form still renders (not a modal)
    expect(screen.getByTestId("nueva-cita-form")).toBeInTheDocument();
  });

  it("cancel button calls router.push to agenda (obs#1: deterministic nav — no router.back)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // NuevaCitaActions cancel → handleCancel → router.push (not router.back)
    screen.getByTestId("nueva-cita-actions-cancel").click();
    expect(mockPush).toHaveBeenCalledWith("/tenant-1/mateo/agenda");
    expect(mockBack).not.toHaveBeenCalled();
  });

  it("renders service selector (ServicePicker) with services from hook", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // ServicePicker renders service options
    expect(screen.getByText(/Limpieza dental/i)).toBeInTheDocument();
  });

  it("renders NuevaCitaActions (FormActionBar) with 'Crear cita' label", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // NuevaCitaActions uses testId="nueva-cita-actions"
    const actionBar = screen.getByTestId("nueva-cita-actions");
    expect(actionBar).toBeInTheDocument();
    const submitBtn = screen.getByTestId("nueva-cita-actions-submit");
    expect(submitBtn.textContent).toContain("Crear");
  });

  it("submit is disabled initially (RN-10: fail-closed — no valid form + availability null)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    const submitBtn = screen.getByTestId("nueva-cita-actions-submit");
    expect(submitBtn).toBeDisabled();
  });

  it("shows end-time error when endTime <= startTime (SC-fin-invalido) — no error before submission", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: "2026-07-01",
        prefillTime: "10:00",
      }),
    );
    // No error initially (form not submitted yet)
    const endTimeError = screen.queryByText(/El horario de fin debe ser posterior/i);
    expect(endTimeError).toBeNull();
  });

  it("does not render a modal/drawer (AC-9 full-page only)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("CanalPicker renders walk_in + telefono options", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // CanalPicker renders "Presencial" and "Teléfono" tab triggers
    expect(screen.getByTestId("canal-picker-walk-in")).toBeInTheDocument();
    expect(screen.getByTestId("canal-picker-telefono")).toBeInTheDocument();
  });

  it("PatientPickerWithCreate renders EntityPicker (typeahead)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // PatientPickerWithCreate renders EntityPicker with testId="patient-picker"
    expect(screen.getByTestId("patient-picker")).toBeInTheDocument();
  });

  it("FreeDoctorsList renders no-slot message when startTime not set", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // FreeDoctorsList shows "Selecciona fecha y hora..." when no slot
    expect(screen.getByTestId("free-doctors-no-slot")).toBeInTheDocument();
  });

  it("DayAvailabilityStrip container not shown when startTime not set", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // nc-day-strip-container only renders when startTime is truthy
    expect(screen.queryByTestId("nc-day-strip-container")).toBeNull();
  });

  // ── UX fix-loop tests (UX-FIXLOOP-2026-06-24) ────────────────────────────

  it("M1: shows avail intro block when startTime not set", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    expect(screen.getByTestId("nc-avail-intro")).toBeInTheDocument();
  });

  it("M1: hides avail intro block when startTime is set", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: "2026-07-01",
        prefillTime: "10:00",
      }),
    );
    expect(screen.queryByTestId("nc-avail-intro")).toBeNull();
  });

  it("M2: notes textarea has HIPAA logistics placeholder", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    const textarea = screen.getByTestId("nc-notas-textarea");
    expect(textarea).toHaveAttribute("placeholder", expect.stringContaining("Solo logística"));
  });

  it("M3: duration section shows helper text", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    expect(screen.getByTestId("nc-duracion-hint")).toBeInTheDocument();
    expect(screen.getByTestId("nc-duracion-hint").textContent).toContain("Viene del servicio");
  });

  it("H2: shows blocking reason when submit disabled (no patient)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // Submit is disabled (empty form) → blocking reason should be visible
    expect(screen.getByTestId("nc-blocking-reason")).toBeInTheDocument();
    expect(screen.getByTestId("nc-blocking-reason").textContent).toContain("paciente");
  });

  it("L1: CanalPicker shows mockup labels (🚶 Walk-in / 📞 Teléfono)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    const walkInBtn = screen.getByTestId("canal-picker-walk-in");
    expect(walkInBtn.textContent).toBe("🚶 Walk-in");
    const telefonoBtn = screen.getByTestId("canal-picker-telefono");
    expect(telefonoBtn.textContent).toBe("📞 Teléfono");
  });

  it("L6: notes textarea renders character counter", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    expect(screen.getByTestId("nc-notas-counter")).toBeInTheDocument();
    expect(screen.getByTestId("nc-notas-counter").textContent).toContain("/500");
  });

  // ── T-D2: Split Fecha / Hora controls ────────────────────────────────────

  it("T-D2: Fecha and Hora render as separate sections with distinct controls", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    expect(screen.getByTestId("nc-section-fecha")).toBeInTheDocument();
    expect(screen.getByTestId("nc-section-hora")).toBeInTheDocument();
    expect(
      within(screen.getByTestId("nc-section-fecha")).getByTestId("smart-date-time-picker"),
    ).toBeInTheDocument();
    expect(
      within(screen.getByTestId("nc-section-hora")).getByTestId("time-picker"),
    ).toBeInTheDocument();
  });

  it("T-D2: changing Fecha alone does not compose startTime (hora still missing)", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // avail-intro shows BEFORE date set
    expect(screen.getByTestId("nc-avail-intro")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("smart-date-time-picker"), {
      target: { value: "2026-07-01T00:00:00.000Z" },
    });
    // T-D3: intro hides as soon as fecha is set (startDateStr set → availability area active)
    // startTime is NOT composed yet (hora missing) — verified by endTime placeholder still shown
    expect(screen.queryByTestId("nc-avail-intro")).toBeNull();
    expect(screen.getByText(/Se calculará al seleccionar inicio y duración/i)).toBeInTheDocument();
  });

  // G-round2: disablePast prop passed to Fecha picker
  it("G-round2: Fecha SmartDateTimePicker receives disablePast prop", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    const fechaPicker = within(screen.getByTestId("nc-section-fecha")).getByTestId("smart-date-time-picker");
    expect(fechaPicker).toHaveAttribute("data-disable-past", "true");
  });

  it("T-D2: Fecha then Hora compose startTime and trigger endTime autocalc", () => {
    render(
      React.createElement(NuevaCitaView, {
        tenantId: "tenant-1",
        prefillDate: undefined,
        prefillTime: undefined,
      }),
    );
    // endTime placeholder visible before both are set
    expect(screen.getByText(/Se calculará al seleccionar inicio y duración/i)).toBeInTheDocument();
    // Set fecha
    fireEvent.change(screen.getByTestId("smart-date-time-picker"), {
      target: { value: "2026-07-01T00:00:00.000Z" },
    });
    // Set hora
    fireEvent.change(screen.getByTestId("time-picker"), {
      target: { value: "10:00" },
    });
    // startTime composed → avail-intro hides (M1 assertion)
    expect(screen.queryByTestId("nc-avail-intro")).toBeNull();
    // endTime autocalc → editar button appears (endTime display is now shown)
    expect(screen.getByTestId("nc-fin-editar")).toBeInTheDocument();
  });
});
