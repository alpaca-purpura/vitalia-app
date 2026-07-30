// cap: scheduling.mateo-agenda
/**
 * PatientPickerWithCreate.test.tsx — TDD RED-first (T-FE-2)
 *
 * Scenarios:
 *  - SC-crear-paciente: inline mini-form opens, create fires, preselects patient WITHOUT navigating
 *  - SC-paciente-incompleto: submit without name → validation error shown
 *  - SC-paciente-duplicado: BE returns is_duplicate=true → "¿Usar existente?" prompt (RN-9)
 *  - SC-empty-pacientes: empty search shows empty state
 *  - SC-pacientes-grandes: windowed render via EntityPicker (cursor pagination)
 *
 * Regression guard — T-FE-4 bug #5:
 *  - SC-crear-paciente-sin-telefono: name-only create (phone blank) MUST call mutation.
 *    Root cause: InlineCreateSchema phone:"" failed min(6) → RHF blocked submit silently.
 *    Fix: empty-string phone transforms to null (optional field, not required by BE).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// Mock EntityPicker from @luana/ui-kit
vi.mock("@luana/ui-kit", () => ({
  EntityPicker: ({
    createAction,
    onChange,
    value,
    searchFn,
    placeholder,
    testId,
  }: {
    createAction?: { label: (q: string) => string; onCreate: (q: string) => void };
    onChange?: (item: { id: string; name: string }) => void;
    value?: { id: string; name: string } | null;
    searchFn: (args: { q: string; cursor?: string | null; limit: number }) => Promise<{ items: { id: string; name: string }[]; nextCursor?: string | null }>;
    placeholder?: string;
    testId?: string;
  }) => {
    const [query, setQuery] = React.useState("");
    const [results, setResults] = React.useState<{ id: string; name: string }[]>([]);
    const tid = testId ?? "entity-picker";

    const search = async (q: string) => {
      setQuery(q);
      const res = await searchFn({ q, cursor: null, limit: 20 });
      setResults(res.items);
    };

    return (
      <div data-testid={tid}>
        <input
          data-testid={`${tid}-search`}
          placeholder={placeholder}
          onChange={(e) => void search(e.target.value)}
        />
        {value && (
          <span data-testid={`${tid}-selected`}>{value.name}</span>
        )}
        {results.map((r) => (
          <button
            key={r.id}
            data-testid={`${tid}-option-${r.id}`}
            onClick={() => onChange?.(r)}
          >
            {r.name}
          </button>
        ))}
        {results.length === 0 && query === "" && (
          <span data-testid={`${tid}-empty`}>Sin resultados</span>
        )}
        {createAction && query.length > 0 && (
          <button
            data-testid={`${tid}-create-action`}
            onClick={() => {
              createAction.onCreate(query);
            }}
          >
            {createAction.label(query)}
          </button>
        )}
      </div>
    );
  },
}));

// Mock hooks used inside PatientPickerWithCreate
const mockCreatePatient = vi.fn();
const mockSearchPatients = vi.fn();

vi.mock("../../../hooks/use-patients", () => ({
  useSearchPatients: () => ({
    searchFn: mockSearchPatients,
  }),
  useCreatePatientInline: () => ({
    mutateAsync: mockCreatePatient,
    isPending: false,
    error: null,
  }),
}));

import { PatientPickerWithCreate } from "../PatientPickerWithCreate";

describe("PatientPickerWithCreate", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchPatients.mockResolvedValue({ items: [], nextCursor: null, total: 0 });
  });

  it("SC-crear-paciente: inline form opens on createAction, creates patient, preselects WITHOUT leaving form", async () => {
    const onChange = vi.fn();
    mockCreatePatient.mockResolvedValue({
      patientId: "new-patient-uuid",
      nameMasked: "J*** G***",
      phoneMasked: "+54 9 11 ****",
      isDuplicate: false,
    });

    const user = userEvent.setup();
    render(
      <PatientPickerWithCreate
        value={null}
        onChange={onChange}
        tenantId="t-1"
      />,
    );

    // Type in the search
    const searchInput = screen.getByTestId("patient-picker-search");
    await user.type(searchInput, "Juan");

    // Click create action
    const createBtn = await screen.findByTestId("patient-picker-create-action");
    await user.click(createBtn);

    // Inline form should appear
    expect(screen.getByTestId("patient-inline-form")).toBeInTheDocument();

    // Fill in name
    const nameInput = screen.getByTestId("patient-inline-name");
    await user.clear(nameInput);
    await user.type(nameInput, "Juan García");

    // Fill in phone
    const phoneInput = screen.getByTestId("patient-inline-phone");
    await user.type(phoneInput, "+5491112345678");

    // Submit
    await user.click(screen.getByTestId("patient-inline-submit"));

    await waitFor(() => {
      expect(mockCreatePatient).toHaveBeenCalledWith(
        expect.objectContaining({ name: "Juan García" }),
      );
    });

    // After create, onChange called with patientId, NOT a navigation
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith("new-patient-uuid");
    });
  });

  it("SC-paciente-incompleto: submit without name shows validation error", async () => {
    const user = userEvent.setup();
    render(
      <PatientPickerWithCreate
        value={null}
        onChange={vi.fn()}
        tenantId="t-1"
      />,
    );

    // Open inline form
    const searchInput = screen.getByTestId("patient-picker-search");
    await user.type(searchInput, "X");
    const createBtn = await screen.findByTestId("patient-picker-create-action");
    await user.click(createBtn);

    // Try to submit without filling name
    await user.click(screen.getByTestId("patient-inline-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("patient-inline-name-error")).toBeInTheDocument();
    });
    expect(mockCreatePatient).not.toHaveBeenCalled();
  });

  it("SC-paciente-duplicado: BE is_duplicate=true shows '¿Usar existente?' prompt (RN-9)", async () => {
    const onChange = vi.fn();
    mockCreatePatient.mockResolvedValue({
      patientId: "existing-patient-uuid",
      nameMasked: "J*** G***",
      phoneMasked: "+54 9 11 ****",
      isDuplicate: true,
    });

    const user = userEvent.setup();
    render(
      <PatientPickerWithCreate
        value={null}
        onChange={onChange}
        tenantId="t-1"
      />,
    );

    const searchInput = screen.getByTestId("patient-picker-search");
    await user.type(searchInput, "Juan");
    const createBtn = await screen.findByTestId("patient-picker-create-action");
    await user.click(createBtn);

    const nameInput = screen.getByTestId("patient-inline-name");
    await user.type(nameInput, "Juan García");
    const phoneInput = screen.getByTestId("patient-inline-phone");
    await user.type(phoneInput, "+5491112345678");

    await user.click(screen.getByTestId("patient-inline-submit"));

    // Duplicate prompt shown
    await waitFor(() => {
      expect(screen.getByTestId("patient-duplicate-prompt")).toBeInTheDocument();
    });

    // Accepting uses the existing patient
    await user.click(screen.getByTestId("patient-duplicate-use-existing"));
    expect(onChange).toHaveBeenCalledWith("existing-patient-uuid");
  });

  it("SC-empty-pacientes: empty search shows empty state", async () => {
    mockSearchPatients.mockResolvedValue({ items: [], nextCursor: null, total: 0 });

    render(
      <PatientPickerWithCreate
        value={null}
        onChange={vi.fn()}
        tenantId="t-1"
      />,
    );

    expect(screen.getByTestId("patient-picker-empty")).toBeInTheDocument();
  });

  // ── Regression guard: T-FE-4 bug #5 — submit never fires with empty phone ──
  // RED: with the old schema (phone: z.string().min(6)...), leaving phone blank
  // caused RHF validation to block handleSubmit → mutation was NEVER called.
  // GREEN: after fix (empty-string → null transform), name-only create works.
  it("SC-crear-paciente-sin-telefono: name-only (phone blank) MUST call mutation [regression guard bug#5]", async () => {
    const onChange = vi.fn();
    mockCreatePatient.mockResolvedValue({
      patientId: "created-no-phone-uuid",
      nameMasked: "M*** P***",
      phoneMasked: null,
      isDuplicate: false,
    });

    const user = userEvent.setup();
    render(
      <PatientPickerWithCreate
        value={null}
        onChange={onChange}
        tenantId="t-1"
      />,
    );

    // Open inline form via createAction
    const searchInput = screen.getByTestId("patient-picker-search");
    await user.type(searchInput, "María");
    const createBtn = await screen.findByTestId("patient-picker-create-action");
    await user.click(createBtn);

    // Fill name only — leave phone BLANK (the buggy path)
    const nameInput = screen.getByTestId("patient-inline-name");
    await user.clear(nameInput);
    await user.type(nameInput, "María Pérez");
    // phone input untouched — stays empty ""

    // Click submit
    await user.click(screen.getByTestId("patient-inline-submit"));

    // Mutation MUST have been called (was silently swallowed before fix)
    await waitFor(() => {
      expect(mockCreatePatient).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "María Pérez",
          phone: null, // "" transformed to null by schema
        }),
      );
    });

    // onChange called with the new patientId
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith("created-no-phone-uuid");
    });
  });

  // L5: chip shows typed name, not server-masked name
  it("L5: chip shows the typed name (data.name) after inline create, not nameMasked", async () => {
    const onChange = vi.fn();
    mockCreatePatient.mockResolvedValue({
      patientId: "l5-patient-uuid",
      nameMasked: "J*** G***",   // server-masked — should NOT appear in chip
      phoneMasked: null,
      isDuplicate: false,
    });

    const user = userEvent.setup();
    render(
      <PatientPickerWithCreate
        value={null}
        onChange={onChange}
        tenantId="t-1"
      />,
    );

    // Open inline form
    const searchInput = screen.getByTestId("patient-picker-search");
    await user.type(searchInput, "Juan");
    const createBtn = await screen.findByTestId("patient-picker-create-action");
    await user.click(createBtn);

    // Fill and submit
    const nameInput = screen.getByTestId("patient-inline-name");
    await user.clear(nameInput);
    await user.type(nameInput, "Juan García");
    await user.click(screen.getByTestId("patient-inline-submit"));

    // Chip should show the typed name, NOT the masked version
    await waitFor(() => {
      const chip = screen.getByTestId("patient-chip");
      expect(chip).toBeInTheDocument();
      expect(chip.textContent).toContain("Juan García");
      expect(chip.textContent).not.toContain("J*** G***");
    });
  });

  // L4: phone and email labels show (opcional) hint
  it("L4: phone and email labels show (opcional) in inline create form", async () => {
    const user = userEvent.setup();
    render(
      <PatientPickerWithCreate
        value={null}
        onChange={vi.fn()}
        tenantId="t-1"
      />,
    );

    const searchInput = screen.getByTestId("patient-picker-search");
    await user.type(searchInput, "Test");
    const createBtn = await screen.findByTestId("patient-picker-create-action");
    await user.click(createBtn);

    const phoneLabel = screen.getByText(/Teléfono/i).closest("label");
    expect(phoneLabel?.textContent).toContain("opcional");

    const emailLabel = screen.getByText(/Correo electrónico/i).closest("label");
    expect(emailLabel?.textContent).toContain("opcional");
  });
});
