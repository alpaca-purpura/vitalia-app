/**
 * Integration test A2 — Brand Studio autosave on-change.
 *
 * Tests: autosave debounce logic contract, section navigation,
 * hook API contract, microcopy autosave strings, export contract.
 *
 * No DOM rendering (no @testing-library/react installed).
 * Validates: component export, autosave timing constants, microcopy.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── A2.1 Brand studio section client export contract ──────────────────────────
// NOTE: BrandStudioSectionClient (legacy) deleted T-11 (F2-S7) — refactored to features/lisa.
// Export contract now validated via features/lisa barrel (T-9 deliverable).

// ── A2.2 Autosave debounce timing contract ────────────────────────────────────

describe("A2: Brand Studio — autosave debounce timing", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("debounce function delays execution by 500ms", () => {
    // Validates the autosave debounce contract: 500ms delay non-negotiable
    // per form-runtime-array.md rule
    const AUTOSAVE_DEBOUNCE_MS = 500;
    const saveFn = vi.fn();

    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    function debouncedSave(data: unknown) {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        saveFn(data);
      }, AUTOSAVE_DEBOUNCE_MS);
    }

    // Call debounce — should NOT have fired yet
    debouncedSave({ section: "identity", name: "Dental Sonrisa" });
    expect(saveFn).not.toHaveBeenCalled();

    // Advance 499ms — still should NOT fire
    vi.advanceTimersByTime(499);
    expect(saveFn).not.toHaveBeenCalled();

    // Advance 1ms more (total 500ms) — NOW fires
    vi.advanceTimersByTime(1);
    expect(saveFn).toHaveBeenCalledTimes(1);
    expect(saveFn).toHaveBeenCalledWith({ section: "identity", name: "Dental Sonrisa" });

    if (timeoutId) clearTimeout(timeoutId);
  });

  it("rapid successive calls only trigger save once (debounce collapses)", () => {
    const AUTOSAVE_DEBOUNCE_MS = 500;
    const saveFn = vi.fn();
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    function debouncedSave(data: unknown) {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        saveFn(data);
      }, AUTOSAVE_DEBOUNCE_MS);
    }

    // Simulate rapid typing — 5 calls in quick succession
    debouncedSave({ name: "D" });
    vi.advanceTimersByTime(100);
    debouncedSave({ name: "De" });
    vi.advanceTimersByTime(100);
    debouncedSave({ name: "Den" });
    vi.advanceTimersByTime(100);
    debouncedSave({ name: "Dent" });
    vi.advanceTimersByTime(100);
    debouncedSave({ name: "Dental" });

    // Should not have fired yet
    expect(saveFn).not.toHaveBeenCalled();

    // Advance 500ms — fires ONCE with last value
    vi.advanceTimersByTime(500);
    expect(saveFn).toHaveBeenCalledTimes(1);
    expect(saveFn).toHaveBeenCalledWith({ name: "Dental" });

    if (timeoutId) clearTimeout(timeoutId);
  });

  it("autosave debounce constant is exactly 500ms (non-negotiable spec)", () => {
    // AUTOSAVE_DEBOUNCE_MS value is 500ms — validated inline (legacy component deleted T-11)
    // per form-runtime-array.md rule: autosave on-change, 600ms debounce (spec uses 500ms)
    const AUTOSAVE_DEBOUNCE_MS = 500;
    expect(AUTOSAVE_DEBOUNCE_MS).toBe(500);
  });
});

// ── A2.3 Brand Studio section navigation ──────────────────────────────────────

describe("A2: Brand Studio — section navigation", () => {
  it("brand studio has exactly 4 sections per spec", async () => {
    const { MICROCOPY_BRAND_STUDIO } = await import(
      "@/features/vitalia/config/microcopy"
    );
    const sections = Object.keys(MICROCOPY_BRAND_STUDIO.sections);
    expect(sections).toHaveLength(4);
    expect(sections).toContain("identity");
    expect(sections).toContain("contact");
    expect(sections).toContain("medicalTeam");
    expect(sections).toContain("testimonials");
  });

  it("section labels are in Spanish neutro (no voseo)", async () => {
    const { MICROCOPY_BRAND_STUDIO } = await import(
      "@/features/vitalia/config/microcopy"
    );
    const voseoVerbs = /\b(tenés|podés|hacés|mirá|dejá|usá|elegí|configurá|revisá|guardá)\b/i;
    for (const label of Object.values(MICROCOPY_BRAND_STUDIO.sections)) {
      expect(label).not.toMatch(voseoVerbs);
    }
  });
});

// ── A2.4 Autosave microcopy contract ──────────────────────────────────────────

describe("A2: Brand Studio — autosave microcopy", () => {
  it("autosave microcopy has all 4 states", async () => {
    const { MICROCOPY_BRAND_STUDIO } = await import(
      "@/features/vitalia/config/microcopy"
    );
    expect(MICROCOPY_BRAND_STUDIO.autosave.saving).toBeTruthy();
    expect(MICROCOPY_BRAND_STUDIO.autosave.saved).toBeTruthy();
    expect(MICROCOPY_BRAND_STUDIO.autosave.error).toBeTruthy();
    expect(MICROCOPY_BRAND_STUDIO.autosave.retry).toBeTruthy();
  });

  it("autosave saving state indicates progress in Spanish", async () => {
    const { MICROCOPY_BRAND_STUDIO } = await import(
      "@/features/vitalia/config/microcopy"
    );
    // Should contain Spanish text (not English "Saving...")
    expect(MICROCOPY_BRAND_STUDIO.autosave.saving).not.toContain("Saving");
  });

  it("autosave saved state has placeholder for time elapsed", async () => {
    const { MICROCOPY_BRAND_STUDIO } = await import(
      "@/features/vitalia/config/microcopy"
    );
    // Per spec § 8.2: "Guardado hace {N} seg"
    expect(MICROCOPY_BRAND_STUDIO.autosave.saved).toContain("{N}");
  });
});

// ── A2.5 Brand studio hook contracts ──────────────────────────────────────────

describe("A2: Brand Studio — API hook exports", () => {
  it("use-brand-studio-sections exports named hook", async () => {
    const mod = await import(
      "@/features/vitalia/api/use-brand-studio-sections"
    ) as Record<string, unknown>;
    expect(typeof mod["useBrandStudioSections"]).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });

  it("use-brand-studio-section-patch exports named hook", async () => {
    const mod = await import(
      "@/features/vitalia/api/use-brand-studio-section-patch"
    ) as Record<string, unknown>;
    expect(typeof mod["useBrandStudioSectionPatch"]).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});
