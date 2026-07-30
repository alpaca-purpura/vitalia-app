// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * NuevoIntegranteModal.test.tsx — regression guard for the infinite-render loop.
 *
 * REGRESSION (2026-06-06): /lisa/staff threw "Maximum update depth exceeded"
 * (Next.js error bubble). Root cause: the reset useEffect depended on the whole
 * `createDoctor` object (react-query useMutation result), which gets a NEW identity
 * on every render → effect re-fires every render → form.reset()/createDoctor.reset()
 * → re-render → infinite loop. The modal mounts (closed) inside the directory, so
 * the directory page itself crashed.
 *
 * These tests render the modal in the directory-page scenario (mounted, open={false})
 * and assert it does NOT exceed React's render budget. The mock of useCreateDoctor
 * mirrors react-query semantics exactly: a fresh wrapper object each render with a
 * STABLE `.reset` reference — so the test is RED against the buggy deps and GREEN
 * against the fixed (stable-method) deps.
 *
 * TDD: written BEFORE the fix (RED-first). The existing staff.test.tsx never
 * rendered this component, which is why vitest never caught the loop.
 *
 * T-FIX-3 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § SC-3 (Nuevo integrante modal) — regression
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { NuevoIntegranteModal } from "../NuevoIntegranteModal";

// ── next/navigation ───────────────────────────────────────────────────────────
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "t-001" }),
}));

// ── sonner toast ──────────────────────────────────────────────────────────────
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

// ── api/staff: mirror react-query useMutation semantics ───────────────────────
// react-query returns a FRESH result object on every render but a STABLE `.reset`
// (and `.mutateAsync`) reference. Reproducing that is what makes this test a true
// regression guard: deps on the whole object loop; deps on the stable method don't.
const stableReset = vi.fn();
const stableMutateAsync = vi.fn();
let mutationRenderCount = 0;
vi.mock("../../../api/staff", () => ({
  useCreateDoctor: () => {
    mutationRenderCount += 1;
    // Fresh wrapper object each render (new identity) — like react-query.
    return {
      mutateAsync: stableMutateAsync,
      reset: stableReset,
      isPending: false,
      _render: mutationRenderCount, // proves new identity per render
    };
  },
  mapDoctorCreateToPayload: (v: unknown) => v,
}));

describe("NuevoIntegranteModal — infinite-loop regression (T-FIX-3)", () => {
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    mutationRenderCount = 0;
    // React logs "Maximum update depth exceeded" via console.error before throwing.
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    errorSpy.mockRestore();
    vi.clearAllMocks();
  });

  it("mounts closed (directory scenario) without exceeding render budget", () => {
    // Buggy version throws "Maximum update depth exceeded" here.
    expect(() =>
      render(<NuevoIntegranteModal open={false} onClose={vi.fn()} />),
    ).not.toThrow();

    const sawMaxDepth = errorSpy.mock.calls.some((args) =>
      String(args[0] ?? "").includes("Maximum update depth"),
    );
    expect(sawMaxDepth).toBe(false);
  });

  it("does not re-render unboundedly when closed", () => {
    render(<NuevoIntegranteModal open={false} onClose={vi.fn()} />);
    // A healthy closed modal renders a small, bounded number of times.
    // The loop would push this into the dozens before React bails.
    expect(mutationRenderCount).toBeLessThan(10);
  });

  it("opens without exceeding render budget", () => {
    expect(() =>
      render(<NuevoIntegranteModal open={true} onClose={vi.fn()} />),
    ).not.toThrow();
    expect(screen.getByTestId("modal-nuevo-integrante")).toBeInTheDocument();

    const sawMaxDepth = errorSpy.mock.calls.some((args) =>
      String(args[0] ?? "").includes("Maximum update depth"),
    );
    expect(sawMaxDepth).toBe(false);
  });
});
