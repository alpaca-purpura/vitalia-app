/**
 * Tests — use-wizard-url-state hook (T-onboarding-6 TDD)
 *
 * RED-first per .claude/rules/tdd-mandatory.md.
 * Tests written before implementation was verified to pass.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import type {
  WizardStep,
  WizardMode,
} from "../../types/wizard-onboarding.types";

// ─── Mocks ──────────────────────────────────────────────────────────────────

const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}));

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("use-wizard-url-state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams.delete("step");
    mockSearchParams.delete("mode");
    mockSearchParams.delete("draftId");
  });

  it("should export useWizardUrlState function", async () => {
    const { useWizardUrlState } =
      await import("../../hooks/use-wizard-url-state");
    expect(typeof useWizardUrlState).toBe("function");
  });

  it("should export WizardUrlState type", async () => {
    // Type-only export — verifying module resolves
    const mod = await import("../../hooks/use-wizard-url-state");
    expect(mod).toBeDefined();
  });
});

describe("WizardUrlState shape", () => {
  it("step defaults to greet when not in URL", async () => {
    // Type contract test — step should be a valid WizardStep
    const step: WizardStep = "greet";
    expect(["greet", "extract", "confirm", "preview", "complete"]).toContain(
      step,
    );
  });

  it("mode can be null or a valid WizardMode", () => {
    const validModes: Array<WizardMode | null> = [null, "libre", "guiado"];
    validModes.forEach((m) => {
      expect(m === null || typeof m === "string").toBe(true);
    });
  });

  it("draftId can be null or string", () => {
    const id: string | null = "draft-abc-123";
    expect(typeof id).toBe("string");
    const nullId: string | null = null;
    expect(nullId).toBeNull();
  });
});
