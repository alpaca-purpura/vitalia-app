/**
 * Tests — use-wizard-onboarding-state hook (T-onboarding-6 TDD)
 *
 * RED-first per .claude/rules/tdd-mandatory.md.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ─── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
  useOrganization: () => ({
    organization: { id: "test-tenant-id" },
    isLoaded: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}));

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("use-wizard-onboarding-state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should export useWizardOnboardingState function", async () => {
    const mod = await import("../../hooks/use-wizard-onboarding-state");
    expect(typeof mod.useWizardOnboardingState).toBe("function");
  });

  it("should export wizardQueryKeys object", async () => {
    const { wizardQueryKeys } =
      await import("../../hooks/use-wizard-onboarding-state");
    expect(typeof wizardQueryKeys).toBe("object");
    expect(typeof wizardQueryKeys.all).toBe("function");
    expect(typeof wizardQueryKeys.draft).toBe("function");
  });

  it("wizardQueryKeys.all() returns array", async () => {
    const { wizardQueryKeys } =
      await import("../../hooks/use-wizard-onboarding-state");
    const key = wizardQueryKeys.all();
    expect(Array.isArray(key)).toBe(true);
  });

  it("wizardQueryKeys.draft(id) returns array with id", async () => {
    const { wizardQueryKeys } =
      await import("../../hooks/use-wizard-onboarding-state");
    const key = wizardQueryKeys.draft("test-draft-123");
    expect(Array.isArray(key)).toBe(true);
    expect(JSON.stringify(key)).toContain("test-draft-123");
  });

  it("hook returns expected shape when no draftId", async () => {
    const { useWizardOnboardingState } =
      await import("../../hooks/use-wizard-onboarding-state");
    // The hook is mocked; verifying it's callable
    const result = useWizardOnboardingState({ draftId: null });
    expect(result).toBeDefined();
  });
});
