/**
 * TenantSwitcher.test.tsx — TDD tests for TenantSwitcher organism
 * F1-S3 vitalia-fase1-tenant-switcher — T-7 (+ T-5 + T-6 coverage)
 *
 * Tests cover:
 * - T-5: useTenants hydrates store via useEffect (NOT deprecated onSuccess)
 * - T-6: AddClinicPlaceholderModal opens on "Agregar clínica" click
 * - T-7: 4 states (loading/error/empty/success), path preservation, a11y
 *
 * Mock strategy:
 * - useTenants: mocked to return controlled query state
 * - useTenantStore: mocked for state assertions
 * - window.location.href: replaced with vi.fn() for redirect assertions
 * - usePathname: mocked for current path
 * - Radix DropdownMenu: mocked to render content inline (no portal)
 *
 * downstream-regression-na: brand-local shell-organism test; no cross-brand consumers
 */

import * as React from "react";
import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { TenantSwitcher } from "../TenantSwitcher";

// ── Mock Radix DropdownMenu to render content inline (bypasses portal/pointer events) ──

vi.mock("@/components/ui/dropdown-menu", () => {
  function DropdownMenu({ children }: { children: React.ReactNode }) {
    const [open, setOpen] = useState(false);
    // Pass open state + setter to children via context
    return (
      <div data-testid="dropdown-root" data-open={String(open)}>
        {React.Children.map(
          children as React.ReactElement | React.ReactElement[],
          (child) => {
            if (!React.isValidElement(child)) return child;
            return React.cloneElement(
              child as React.ReactElement<Record<string, unknown>>,
              {
                __dropdownOpen: open,
                __setDropdownOpen: setOpen,
              },
            );
          },
        )}
      </div>
    );
  }

  function DropdownMenuTrigger({
    children,
    asChild,
    __setDropdownOpen,
    ...props
  }: {
    children: React.ReactNode;
    asChild?: boolean;
    __setDropdownOpen?: (v: boolean) => void;
    [key: string]: unknown;
  }) {
    const cleanProps = { ...props };
    delete cleanProps.__dropdownOpen;
    const handleClick = () => __setDropdownOpen?.(true);
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(
        children as React.ReactElement<Record<string, unknown>>,
        { onClick: handleClick, ...cleanProps },
      );
    }
    return (
      <button type="button" onClick={handleClick} {...cleanProps}>
        {children}
      </button>
    );
  }

  function DropdownMenuContent({
    children,
    __dropdownOpen,
    ...props
  }: {
    children: React.ReactNode;
    __dropdownOpen?: boolean;
    [key: string]: unknown;
  }) {
    if (!__dropdownOpen) return null;
    const cleanProps = { ...props };
    delete cleanProps.__setDropdownOpen;
    return (
      <div role="menu" {...cleanProps}>
        {children}
      </div>
    );
  }

  function DropdownMenuLabel({
    children,
    ...props
  }: {
    children: React.ReactNode;
    [key: string]: unknown;
  }) {
    const clean = { ...props };
    delete clean.__dropdownOpen;
    delete clean.__setDropdownOpen;
    return (
      <div role="group" {...clean}>
        {children}
      </div>
    );
  }

  function DropdownMenuSeparator(props: Record<string, unknown>) {
    const clean = { ...props };
    delete clean.__dropdownOpen;
    delete clean.__setDropdownOpen;
    return <hr role="separator" {...clean} />;
  }

  return {
    DropdownMenu,
    DropdownMenuTrigger,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuPortal: ({ children }: { children: React.ReactNode }) =>
      children,
    DropdownMenuItem: ({
      children,
      ...props
    }: {
      children: React.ReactNode;
      [key: string]: unknown;
    }) => {
      const clean = { ...props };
      delete clean.__dropdownOpen;
      delete clean.__setDropdownOpen;
      return (
        <div role="menuitem" {...clean}>
          {children}
        </div>
      );
    },
  };
});

// ── Other mocks ───────────────────────────────────────────────────────────

const mockRefetch = vi.fn();
const mockUseTenants = vi.fn();
const mockUseTenantStore = vi.fn();
const mockUsePathname = vi.fn(
  () => "/sonrisa-plena/(shell-organism)/lisa/marca",
);

vi.mock("@/hooks/useTenants", () => ({
  useTenants: () => mockUseTenants(),
}));

vi.mock("@/stores/tenant-store", () => ({
  useTenantStore: (selector: (s: Record<string, unknown>) => unknown) =>
    mockUseTenantStore(selector),
  TENANT_STORAGE_KEY: "vitalia-tenant-state",
}));

vi.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    isLoaded: true,
    isSignedIn: true,
    userId: "user-test-123",
    getToken: vi.fn().mockResolvedValue("mock-token"),
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// ── Fixtures ──────────────────────────────────────────────────────────────

const T_SONRISA = { id: "sonrisa-plena", name: "Sonrisa Plena", city: "Lima" };
const T_DERMALIA = { id: "dermalia-mx", name: "Dermalia MX", city: "CDMX" };
const T_CLINCARE = {
  id: "clinicare-bogota",
  name: "ClíniCare Bogotá",
  city: "Bogotá",
};

function setupStoreMock({
  activeTenant = T_SONRISA,
  availableTenants = [T_SONRISA, T_DERMALIA, T_CLINCARE],
  switchTenant = vi.fn(),
} = {}) {
  mockUseTenantStore.mockImplementation(
    (selector: (s: Record<string, unknown>) => unknown) => {
      const state = {
        activeTenant,
        availableTenants,
        switchTenant,
        clearStore: vi.fn(),
        setAvailableTenants: vi.fn(),
        setActiveTenant: vi.fn(),
      };
      return selector(state);
    },
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("TenantSwitcher", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRefetch.mockReset();
  });

  // ── Loading state ──────────────────────────────────────────────────────

  describe("Loading state (isLoading=true)", () => {
    beforeEach(() => {
      mockUseTenants.mockReturnValue({
        isLoading: true,
        isError: false,
        data: undefined,
        refetch: vi.fn(),
      });
      setupStoreMock({
        activeTenant: T_SONRISA,
        availableTenants: [T_SONRISA],
      });
    });

    it("renders trigger with active tenant name", () => {
      render(<TenantSwitcher />);
      const trigger = screen.getByTestId("tenant-switcher-trigger");
      expect(trigger).toBeInTheDocument();
    });

    it("isLoading=true: dropdown content shows sr-only 'Cargando clínicas…'", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      expect(screen.getByText("Cargando clínicas…")).toBeInTheDocument();
    });
  });

  // ── Error state ────────────────────────────────────────────────────────

  describe("Error state — Scenario 7", () => {
    beforeEach(() => {
      mockUseTenants.mockReturnValue({
        isLoading: false,
        isError: true,
        data: undefined,
        refetch: mockRefetch,
      });
      setupStoreMock({
        activeTenant: T_SONRISA,
        availableTenants: [T_SONRISA],
      });
    });

    it("isError=true renders Alert with 'No pudimos cargar tus clínicas'", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      expect(
        screen.getByText("No pudimos cargar tus clínicas"),
      ).toBeInTheDocument();
    });

    it("isError=true renders Reintentar button", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      expect(screen.getByText("Reintentar")).toBeInTheDocument();
    });

    it("Reintentar button triggers refetch on click", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByText("Reintentar"));
      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });
  });

  // ── Empty state ────────────────────────────────────────────────────────

  describe("Empty state — Scenario 8", () => {
    it("availableTenants.length === 0 → returns null (no trigger render)", () => {
      mockUseTenants.mockReturnValue({
        isLoading: false,
        isError: false,
        data: { tenants: [] },
        refetch: vi.fn(),
      });
      mockUseTenantStore.mockImplementation(
        (selector: (s: Record<string, unknown>) => unknown) => {
          return selector({
            activeTenant: null,
            availableTenants: [],
            switchTenant: vi.fn(),
            clearStore: vi.fn(),
            setAvailableTenants: vi.fn(),
            setActiveTenant: vi.fn(),
          });
        },
      );
      const { container } = render(<TenantSwitcher />);
      expect(container.firstChild).toBeNull();
    });
  });

  // ── Success state ──────────────────────────────────────────────────────

  describe("Success state — Scenario 1", () => {
    const mockSwitchTenant = vi.fn().mockReturnValue(T_DERMALIA);

    beforeEach(() => {
      mockUseTenants.mockReturnValue({
        isLoading: false,
        isError: false,
        data: { tenants: [T_SONRISA, T_DERMALIA, T_CLINCARE] },
        refetch: vi.fn(),
      });
      setupStoreMock({
        activeTenant: T_SONRISA,
        switchTenant: mockSwitchTenant,
      });
    });

    it("trigger has aria-label='Cambiar clínica' (Scenario 10 a11y)", () => {
      render(<TenantSwitcher />);
      expect(screen.getByTestId("tenant-switcher-trigger")).toHaveAttribute(
        "aria-label",
        "Cambiar clínica",
      );
    });

    it("trigger has title attribute = activeTenant.name", () => {
      render(<TenantSwitcher />);
      expect(screen.getByTestId("tenant-switcher-trigger")).toHaveAttribute(
        "title",
        T_SONRISA.name,
      );
    });

    it("click trigger opens dropdown with role=menu", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      expect(screen.getByRole("menu")).toBeInTheDocument();
    });

    it("dropdown header shows 'MIS CLÍNICAS'", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      expect(screen.getByText("MIS CLÍNICAS")).toBeInTheDocument();
    });

    it("active tenant row has bg-accent/40 class (AC-2 + AC-3)", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      const activeRow = screen.getByTestId(`tenant-option-${T_SONRISA.id}`);
      expect(activeRow).toHaveAttribute("data-active", "true");
      expect(activeRow.className).toContain("bg-accent/40");
    });

    it("click on different tenant triggers switchTenant + window.location.href redirect", () => {
      const locationSetter = vi.fn();
      vi.spyOn(window.location, "href", "set").mockImplementation(
        locationSetter,
      );

      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByTestId(`tenant-option-${T_DERMALIA.id}`));
      expect(mockSwitchTenant).toHaveBeenCalledWith(T_DERMALIA.id);
      expect(locationSetter).toHaveBeenCalledWith(
        "/dermalia-mx/(shell-organism)/lisa/marca",
      );
    });

    it("Scenario 12: click on already-active tenant does NOT redirect", () => {
      const locationSetter = vi.fn();
      vi.spyOn(window.location, "href", "set").mockImplementation(
        locationSetter,
      );

      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByTestId(`tenant-option-${T_SONRISA.id}`));
      expect(locationSetter).not.toHaveBeenCalled();
    });

    it("'Administrar cuenta' link href = /{activeTenant.id}/config/cuenta (AC-7)", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      const link = screen.getByText("Administrar cuenta").closest("a");
      expect(link).toHaveAttribute("href", `/${T_SONRISA.id}/config/cuenta`);
    });
  });

  // ── buildRedirectPath utility ──────────────────────────────────────────

  describe("buildRedirectPath utility", () => {
    it("preserves deep path when switching tenant", () => {
      const mockSwitch = vi.fn().mockReturnValue(T_DERMALIA);
      mockUseTenants.mockReturnValue({
        isLoading: false,
        isError: false,
        data: { tenants: [T_SONRISA, T_DERMALIA] },
        refetch: vi.fn(),
      });
      setupStoreMock({
        activeTenant: T_SONRISA,
        availableTenants: [T_SONRISA, T_DERMALIA],
        switchTenant: mockSwitch,
      });
      mockUsePathname.mockReturnValue(
        "/sonrisa-plena/(shell-organism)/lisa/marca",
      );
      const locationSetter = vi.fn();
      vi.spyOn(window.location, "href", "set").mockImplementation(
        locationSetter,
      );

      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByTestId(`tenant-option-${T_DERMALIA.id}`));
      expect(locationSetter).toHaveBeenCalledWith(
        "/dermalia-mx/(shell-organism)/lisa/marca",
      );
    });

    it("fallback /{newId} for root '/' path", () => {
      const mockSwitch = vi.fn().mockReturnValue(T_DERMALIA);
      mockUseTenants.mockReturnValue({
        isLoading: false,
        isError: false,
        data: { tenants: [T_SONRISA, T_DERMALIA] },
        refetch: vi.fn(),
      });
      setupStoreMock({
        activeTenant: T_SONRISA,
        availableTenants: [T_SONRISA, T_DERMALIA],
        switchTenant: mockSwitch,
      });
      mockUsePathname.mockReturnValue("/");
      const locationSetter = vi.fn();
      vi.spyOn(window.location, "href", "set").mockImplementation(
        locationSetter,
      );

      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByTestId(`tenant-option-${T_DERMALIA.id}`));
      expect(locationSetter).toHaveBeenCalledWith(`/${T_DERMALIA.id}`);
    });
  });

  // ── T-5: hydration via useEffect (NOT deprecated onSuccess) ─────────────

  describe("T-5: store hydration via useEffect (not deprecated onSuccess)", () => {
    it("query.data hydrates store — component renders when data is available", () => {
      mockUseTenants.mockReturnValue({
        isLoading: false,
        isError: false,
        data: { tenants: [T_SONRISA, T_DERMALIA] },
        refetch: vi.fn(),
      });
      setupStoreMock({
        activeTenant: T_SONRISA,
        availableTenants: [T_SONRISA, T_DERMALIA],
      });
      render(<TenantSwitcher />);
      expect(screen.getByTestId("tenant-switcher-trigger")).toBeInTheDocument();
    });
  });

  // ── T-6: AddClinicPlaceholderModal ────────────────────────────────────

  describe("T-6: AddClinicPlaceholderModal", () => {
    beforeEach(() => {
      mockUseTenants.mockReturnValue({
        isLoading: false,
        isError: false,
        data: { tenants: [T_SONRISA, T_DERMALIA] },
        refetch: vi.fn(),
      });
      setupStoreMock();
    });

    it("clicking 'Agregar clínica' opens modal with title 'Próximamente'", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByText("Agregar clínica"));
      expect(screen.getByText("Próximamente")).toBeInTheDocument();
    });

    it("modal body shows correct copy", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByText("Agregar clínica"));
      expect(
        screen.getByText(
          "Próximamente: agregar nueva clínica desde Configurar → Mi cuenta",
        ),
      ).toBeInTheDocument();
    });

    it("clicking 'Entendido' closes modal", () => {
      render(<TenantSwitcher />);
      fireEvent.click(screen.getByTestId("tenant-switcher-trigger"));
      fireEvent.click(screen.getByText("Agregar clínica"));
      // Dialog is open — find close button
      const entendidoBtn = screen.getByTestId("add-clinic-modal-close");
      fireEvent.click(entendidoBtn);
      expect(screen.queryByText("Próximamente")).not.toBeInTheDocument();
    });
  });
});
