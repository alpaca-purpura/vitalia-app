/**
 * TenantStoreBootstrap.test.tsx — Unit tests for TenantStoreBootstrap invisible component.
 * F1-S3 vitalia-fase1-tenant-switcher — T-8 TDD RED-first
 *
 * Tests:
 * - Named export contract
 * - Renders null (no DOM output)
 * - Calls useTenants hook on mount
 * - Calls useSignOutCleanup hook on mount
 *
 * Mocks:
 * - @/hooks/useTenants → verify called
 * - @/hooks/useSignOutCleanup → verify called
 *
 * downstream-regression-na: brand-local shell-organism test; no cross-brand consumers
 */

import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TenantStoreBootstrap } from "../TenantStoreBootstrap";

// Mock hooks — TenantStoreBootstrap tests focus on mount behavior, not hook internals.
const mockUseTenants = vi.fn();
const mockUseSignOutCleanup = vi.fn();

vi.mock("@/hooks/useTenants", () => ({
  useTenants: () => {
    mockUseTenants();
    return { data: undefined, isLoading: false, isError: false };
  },
}));

vi.mock("@/hooks/useSignOutCleanup", () => ({
  useSignOutCleanup: () => {
    mockUseSignOutCleanup();
  },
}));

describe("TenantStoreBootstrap — named export contract", () => {
  it("is a named export (not default)", () => {
    expect(typeof TenantStoreBootstrap).toBe("function");
  });

  it("function name is TenantStoreBootstrap", () => {
    expect(TenantStoreBootstrap.name).toBe("TenantStoreBootstrap");
  });
});

describe("TenantStoreBootstrap — renders null", () => {
  it("renders nothing (returns null)", () => {
    const { container } = render(<TenantStoreBootstrap />);
    expect(container.childNodes).toHaveLength(0);
  });

  it("has no accessible role or testid in DOM", () => {
    const { container } = render(<TenantStoreBootstrap />);
    expect(container.innerHTML).toBe("");
  });
});

describe("TenantStoreBootstrap — hook invocations", () => {
  it("calls useTenants hook on mount", () => {
    mockUseTenants.mockClear();
    render(<TenantStoreBootstrap />);
    expect(mockUseTenants).toHaveBeenCalledTimes(1);
  });

  it("calls useSignOutCleanup hook on mount", () => {
    mockUseSignOutCleanup.mockClear();
    render(<TenantStoreBootstrap />);
    expect(mockUseSignOutCleanup).toHaveBeenCalledTimes(1);
  });

  it("calls both hooks in single render", () => {
    mockUseTenants.mockClear();
    mockUseSignOutCleanup.mockClear();
    render(<TenantStoreBootstrap />);
    expect(mockUseTenants).toHaveBeenCalledTimes(1);
    expect(mockUseSignOutCleanup).toHaveBeenCalledTimes(1);
  });
});
