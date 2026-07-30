// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * EspecialistaLinkPicker.test.tsx — Picker unit tests.
 *
 * Covers:
 *   - Loading skeleton while staff roster loads
 *   - Roster renders available doctors (not already linked)
 *   - Already-linked doctors excluded from the roster list
 *   - "Todos los especialistas ya están vinculados" message when all linked
 *   - "No hay especialistas registrados aún" when roster is empty
 *   - Checking a doctor checkbox calls useLinkSpecialist
 *   - Autosave on-check (no "Guardar" button — RN-20)
 *   - Close button calls onClose
 *
 * spec_anchor: 01-spec.md §Workspace Pestaña 3 · 03-arch-fe.md §8 Tests
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-abc",
}));

const mockUseStaffList = vi.fn();
const mockLink = vi.fn();

vi.mock("../../../api/staff", () => ({
  useStaffList: () => mockUseStaffList(),
}));

vi.mock("../../../api/servicios", () => ({
  useLinkSpecialist: () => ({ mutate: mockLink, isPending: false }),
}));

import { EspecialistaLinkPicker } from "../EspecialistaLinkPicker";

type StaffItem = {
  id: string;
  firstName: string;
  lastName: string;
  specialty?: string;
};

function makeStaff(over: Partial<StaffItem> = {}): StaffItem {
  return {
    id: "doc-1",
    firstName: "María",
    lastName: "González",
    specialty: "Odontología",
    ...over,
  };
}

describe("EspecialistaLinkPicker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton while roster is loading", () => {
    mockUseStaffList.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={[]}
        onClose={vi.fn()}
      />
    );
    const pulses = container.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThanOrEqual(3);
  });

  it("shows 'No hay especialistas registrados aún' when roster is empty", () => {
    mockUseStaffList.mockReturnValue({ data: { items: [] }, isLoading: false });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={[]}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText("No hay especialistas registrados aún.")).toBeInTheDocument();
  });

  it("renders available doctors in the roster (not already linked)", () => {
    mockUseStaffList.mockReturnValue({
      data: {
        items: [
          makeStaff({ id: "doc-1", firstName: "María", lastName: "González" }),
          makeStaff({ id: "doc-2", firstName: "Carlos", lastName: "Pérez" }),
        ],
      },
      isLoading: false,
    });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={[]}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText("María González")).toBeInTheDocument();
    expect(screen.getByText("Carlos Pérez")).toBeInTheDocument();
  });

  it("excludes already-linked doctors from the roster", () => {
    mockUseStaffList.mockReturnValue({
      data: {
        items: [
          makeStaff({ id: "doc-1", firstName: "María", lastName: "González" }),
          makeStaff({ id: "doc-2", firstName: "Carlos", lastName: "Pérez" }),
        ],
      },
      isLoading: false,
    });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={["doc-1"]} // doc-1 already linked
        onClose={vi.fn()}
      />
    );
    expect(screen.queryByText("María González")).not.toBeInTheDocument();
    expect(screen.getByText("Carlos Pérez")).toBeInTheDocument();
  });

  it("shows 'Todos los especialistas ya están vinculados' when all are linked", () => {
    mockUseStaffList.mockReturnValue({
      data: {
        items: [
          makeStaff({ id: "doc-1", firstName: "María", lastName: "González" }),
        ],
      },
      isLoading: false,
    });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={["doc-1"]}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText("Todos los especialistas ya están vinculados.")).toBeInTheDocument();
  });

  it("calls useLinkSpecialist when checkbox is checked (autosave on-mark — RN-20)", async () => {
    const user = userEvent.setup();
    mockUseStaffList.mockReturnValue({
      data: {
        items: [makeStaff({ id: "doc-1", firstName: "María", lastName: "González" })],
      },
      isLoading: false,
    });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={[]}
        onClose={vi.fn()}
      />
    );
    const checkbox = screen.getByRole("checkbox");
    await user.click(checkbox);
    expect(mockLink).toHaveBeenCalledWith("doc-1");
  });

  it("does NOT have a 'Guardar' button (autosave on-check, RN-20)", () => {
    mockUseStaffList.mockReturnValue({
      data: { items: [makeStaff()] },
      isLoading: false,
    });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={[]}
        onClose={vi.fn()}
      />
    );
    expect(screen.queryByRole("button", { name: /guardar/i })).not.toBeInTheDocument();
  });

  it("calls onClose when 'Cerrar' is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    mockUseStaffList.mockReturnValue({ data: { items: [] }, isLoading: false });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={[]}
        onClose={onClose}
      />
    );
    await user.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("renders specialty label alongside doctor name", () => {
    mockUseStaffList.mockReturnValue({
      data: {
        items: [makeStaff({ id: "doc-1", firstName: "Ana", lastName: "López", specialty: "Dermatología" })],
      },
      isLoading: false,
    });
    render(
      <EspecialistaLinkPicker
        offerId="offer-123"
        linkedDoctorIds={[]}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText("· Dermatología")).toBeInTheDocument();
  });
});
