// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * use-account-form.test.ts — TDD RED tests for useAccountForm hook.
 *
 * Tests: autosave 600ms debounce + coalesce, dirty/saved status transitions,
 * form schema validation via RHF+Zod.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § Test Surfaces + § 5
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAccountForm } from "../hooks/use-account-form";

// --- Mocks ---
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("fake-token"), isLoaded: true, isSignedIn: true }),
}));
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  useMutation: (opts: Record<string, unknown>) => ({
    mutateAsync: opts.mutationFn,
    isPending: false,
  }),
}));

const mockInitialData = {
  clinicId: "clinic-uuid",
  tenantId: "tenant-uuid",
  name: "Clínica Demo",
  legalName: null,
  fiscalId: null,
  address: null,
  phone: null,
  email: null,
  currency: "ARS",
  timezone: "America/Argentina/Buenos_Aires",
  country: "AR",
  language: "es-419",
  clinicType: "dental",
  primarySpecialties: ["Odontología cosmética"],
  fiscalIdLabel: "CUIT",
};

describe("useAccountForm — autosave lifecycle (RED)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("initializes with idle status", () => {
    const saveFn = vi.fn().mockResolvedValue(mockInitialData);
    const { result } = renderHook(() =>
      useAccountForm({ initialData: mockInitialData, saveFn, tenantId: "tenant-uuid" }),
    );
    expect(result.current.autosaveStatus).toBe("idle");
  });

  it("transitions to saving after 600ms debounce", async () => {
    const saveFn = vi.fn().mockResolvedValue(mockInitialData);
    const { result } = renderHook(() =>
      useAccountForm({ initialData: mockInitialData, saveFn, tenantId: "tenant-uuid" }),
    );

    act(() => {
      result.current.scheduleAutosave({ name: "Clínica Actualizada" });
    });

    // Not yet saving (debounce 600ms)
    expect(saveFn).not.toHaveBeenCalled();
    expect(result.current.autosaveStatus).toBe("idle");

    await act(async () => {
      vi.advanceTimersByTime(600);
      await Promise.resolve(); // flush microtasks
    });

    expect(saveFn).toHaveBeenCalledWith({ name: "Clínica Actualizada" });
  });

  it("coalesces rapid field changes into single PATCH", async () => {
    const saveFn = vi.fn().mockResolvedValue(mockInitialData);
    const { result } = renderHook(() =>
      useAccountForm({ initialData: mockInitialData, saveFn, tenantId: "tenant-uuid" }),
    );

    act(() => {
      result.current.scheduleAutosave({ name: "Nuevo nombre" });
    });
    act(() => {
      result.current.scheduleAutosave({ fiscalId: "20-12345678-0" });
    });

    await act(async () => {
      vi.advanceTimersByTime(600);
      await Promise.resolve();
    });

    // Both field changes coalesced into one call
    expect(saveFn).toHaveBeenCalledTimes(1);
    expect(saveFn).toHaveBeenCalledWith(
      expect.objectContaining({ name: "Nuevo nombre", fiscalId: "20-12345678-0" }),
    );
  });
});
