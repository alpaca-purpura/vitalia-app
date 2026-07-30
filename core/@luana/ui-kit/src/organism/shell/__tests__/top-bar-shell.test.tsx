// cap: platform.lift-shell-chrome-ui-kit
/**
 * top-bar-shell.test.tsx — T-K3 port of TopBarGlobal.test.tsx.
 *
 * Behaviour ported verbatim; vitalia-coupled specifics adapted to kit's slots API:
 *   - ThemeToggle / TenantSwitcher → generic slot children
 *   - supervisorName: "Supervisora Test"
 *   - mobileDrawerOpen controlled via createShellStore
 *
 * gherkin_coverage:
 *   - D1: header role=banner, h-12, data-testid=topbar-global
 *   - slots: logoSlot + rightClusterSlot rendered
 *   - hamburger: lg:hidden, aria-label dynamic
 *   - variant="skeleton": inert burger (aria-disabled)
 *   - variant="interactive": calls setMobileDrawerOpen via store
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { TopBarShell } from "../TopBarShell";
import { createShellStore } from "../create-shell-store";

// ── Store factory ─────────────────────────────────────────────────────────────
// Use createShellStore for the interactive variant tests.
const useTestShellStore = createShellStore({
  storageKey: "test-topbar-shell-store",
  version: 1,
});

beforeEach(() => {
  useTestShellStore.setState({ mobileDrawerOpen: false });
});

// ── Slot fixtures ─────────────────────────────────────────────────────────────
const MockLogo = () => <div data-testid="mock-logo">Logo</div>;
const MockRightCluster = () => <div data-testid="mock-right-cluster">Cluster</div>;

describe("TopBarShell — structure (D1)", () => {
  it("renders <header role='banner'>", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("has data-testid='topbar-global'", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    expect(screen.getByTestId("topbar-global")).toBeInTheDocument();
  });

  it("header has h-12 class", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    const header = screen.getByRole("banner");
    expect(header.className).toContain("h-12");
  });

  it("renders logoSlot content", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    expect(screen.getByTestId("mock-logo")).toBeInTheDocument();
  });

  it("renders rightClusterSlot content", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    expect(screen.getByTestId("mock-right-cluster")).toBeInTheDocument();
  });
});

describe("TopBarShell — hamburger button", () => {
  it("renders burger with data-testid='topbar-hamburger'", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    expect(screen.getByTestId("topbar-hamburger")).toBeInTheDocument();
  });

  it("burger has lg:hidden class (mobile only)", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    const burger = screen.getByTestId("topbar-hamburger");
    expect(burger.className).toContain("lg:hidden");
  });

  it("skeleton burger has default aria-label with supervisor name", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    const burger = screen.getByTestId("topbar-hamburger");
    expect(burger.getAttribute("aria-label")).toContain("Supervisora Test");
  });

  it("skeleton burger is aria-disabled='true' (inert)", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
      />,
    );
    const burger = screen.getByTestId("topbar-hamburger");
    expect(burger.getAttribute("aria-disabled")).toBe("true");
  });
});

describe("TopBarShell — variant=interactive (store-subscribed)", () => {
  it("interactive: clicking burger opens mobile drawer (setMobileDrawerOpen true)", async () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="interactive"
        useShellStore={useTestShellStore}
      />,
    );
    const burger = screen.getByTestId("topbar-hamburger");
    fireEvent.click(burger);
    expect(useTestShellStore.getState().mobileDrawerOpen).toBe(true);
  });

  it("interactive: onBurgerClick override is called instead of store action", async () => {
    const onBurger = vi.fn();
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="interactive"
        useShellStore={useTestShellStore}
        onBurgerClick={onBurger}
      />,
    );
    fireEvent.click(screen.getByTestId("topbar-hamburger"));
    expect(onBurger).toHaveBeenCalledTimes(1);
    // Store should NOT have been mutated (override bypassed the store action)
    expect(useTestShellStore.getState().mobileDrawerOpen).toBe(false);
  });
});

describe("TopBarShell — labels override", () => {
  it("custom openSupervisor label applied to burger", () => {
    render(
      <TopBarShell
        supervisorName="Supervisora Test"
        logoSlot={<MockLogo />}
        rightClusterSlot={<MockRightCluster />}
        variant="skeleton"
        labels={{ openSupervisor: "Mostrar panel de asistente" }}
      />,
    );
    const burger = screen.getByTestId("topbar-hamburger");
    expect(burger.getAttribute("aria-label")).toBe("Mostrar panel de asistente");
  });
});
