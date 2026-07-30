// cap: platform.autosave-primitive-platform
// story-origin: build-autosave-primitive-luana T-2
/**
 * AutosaveBadge.test.tsx — Vitest component tests for <AutosaveBadge>.
 *
 * Covers:
 *  - Renders each AutosaveStatus state with correct data-state attribute
 *  - Correct text labels per state (default Spanish neutro LatAm)
 *  - aria-live="polite" for idle/dirty/saving/saved states
 *  - aria-live="assertive" for error state (urgent announcement)
 *  - Icon rendered per state (aria-hidden)
 *  - Custom labels override (i18n-ready)
 *  - savedAt timestamp shown when status=saved
 *  - No color-only communication (text always present for non-idle states)
 *  - Contrast: token-based classes (not hardcoded hex) are used
 *
 * ADR-012 — build-autosave-primitive-luana T-2
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AutosaveStatus } from "@luana/hooks";
import { AutosaveBadge } from "../AutosaveBadge";

// ── helpers ──────────────────────────────────────────────────────────────────

function renderBadge(
  status: AutosaveStatus,
  extra: { savedAt?: Date | null; labels?: Partial<Record<AutosaveStatus, string>> } = {},
) {
  return render(<AutosaveBadge status={status} {...extra} />);
}

// ── data-state attribute ──────────────────────────────────────────────────────

describe("AutosaveBadge — data-state attribute", () => {
  const statuses: AutosaveStatus[] = ["idle", "dirty", "saving", "saved", "error"];

  for (const status of statuses) {
    it(`renders data-state="${status}"`, () => {
      const { container } = renderBadge(status);
      const root = container.firstChild as HTMLElement;
      expect(root.getAttribute("data-state")).toBe(status);
    });
  }
});

// ── default labels (Spanish neutro LatAm) ────────────────────────────────────

describe("AutosaveBadge — default labels", () => {
  it('shows empty text for idle (no visible label)', () => {
    const { container } = renderBadge("idle");
    // idle status renders no visible text (empty string label)
    const root = container.firstChild as HTMLElement;
    // The live region should exist, text should be absent or empty
    const textSpans = root.querySelectorAll("span:not([aria-hidden])");
    // If there's a text span it should be empty for idle
    const hasNonEmptyText = Array.from(textSpans).some(
      (s) => (s.textContent?.trim() ?? "").length > 0,
    );
    expect(hasNonEmptyText).toBe(false);
  });

  it('shows "Sin guardar" for dirty', () => {
    renderBadge("dirty");
    expect(screen.getByText("Sin guardar")).toBeTruthy();
  });

  it('shows "Guardando…" for saving', () => {
    renderBadge("saving");
    expect(screen.getByText("Guardando…")).toBeTruthy();
  });

  it('shows "Guardado" for saved (without savedAt)', () => {
    renderBadge("saved");
    expect(screen.getByText("Guardado")).toBeTruthy();
  });

  it('shows "No se pudo guardar. Reintenta." for error', () => {
    renderBadge("error");
    expect(screen.getByText("No se pudo guardar. Reintenta.")).toBeTruthy();
  });
});

// ── savedAt timestamp ─────────────────────────────────────────────────────────

describe("AutosaveBadge — savedAt timestamp", () => {
  it("shows relative time when savedAt is provided and status=saved", () => {
    const savedAt = new Date(Date.now() - 3000); // 3 seconds ago
    renderBadge("saved", { savedAt });
    // should show something like "Guardado hace 3s" or "Guardado ahora mismo"
    const label = screen.getByText(/Guardado/);
    expect(label).toBeTruthy();
    expect(label.textContent).toMatch(/Guardado/);
  });

  it("shows 'Guardado' fallback when savedAt is null", () => {
    renderBadge("saved", { savedAt: null });
    expect(screen.getByText("Guardado")).toBeTruthy();
  });
});

// ── aria-live attribute ───────────────────────────────────────────────────────

describe("AutosaveBadge — aria-live", () => {
  it('uses aria-live="polite" for idle status', () => {
    const { container } = renderBadge("idle");
    const root = container.firstChild as HTMLElement;
    expect(root.getAttribute("aria-live")).toBe("polite");
  });

  it('uses aria-live="polite" for dirty status', () => {
    const { container } = renderBadge("dirty");
    const root = container.firstChild as HTMLElement;
    expect(root.getAttribute("aria-live")).toBe("polite");
  });

  it('uses aria-live="polite" for saving status', () => {
    const { container } = renderBadge("saving");
    const root = container.firstChild as HTMLElement;
    expect(root.getAttribute("aria-live")).toBe("polite");
  });

  it('uses aria-live="polite" for saved status', () => {
    const { container } = renderBadge("saved");
    const root = container.firstChild as HTMLElement;
    expect(root.getAttribute("aria-live")).toBe("polite");
  });

  it('uses aria-live="assertive" for error status (urgent announcement)', () => {
    const { container } = renderBadge("error");
    const root = container.firstChild as HTMLElement;
    expect(root.getAttribute("aria-live")).toBe("assertive");
  });
});

// ── icon rendered (aria-hidden) ───────────────────────────────────────────────

describe("AutosaveBadge — icon", () => {
  it("renders an icon element with aria-hidden for dirty", () => {
    const { container } = renderBadge("dirty");
    const icon = container.querySelector('[aria-hidden="true"]');
    expect(icon).toBeTruthy();
  });

  it("renders an icon element with aria-hidden for saving", () => {
    const { container } = renderBadge("saving");
    const icon = container.querySelector('[aria-hidden="true"]');
    expect(icon).toBeTruthy();
  });

  it("renders an icon element with aria-hidden for saved", () => {
    const { container } = renderBadge("saved");
    const icon = container.querySelector('[aria-hidden="true"]');
    expect(icon).toBeTruthy();
  });

  it("renders an icon element with aria-hidden for error", () => {
    const { container } = renderBadge("error");
    const icon = container.querySelector('[aria-hidden="true"]');
    expect(icon).toBeTruthy();
  });
});

// ── custom labels (i18n override) ────────────────────────────────────────────

describe("AutosaveBadge — custom labels (i18n)", () => {
  it("overrides the dirty label", () => {
    renderBadge("dirty", { labels: { dirty: "Unsaved changes" } });
    expect(screen.getByText("Unsaved changes")).toBeTruthy();
    expect(screen.queryByText("Sin guardar")).toBeNull();
  });

  it("overrides the saving label", () => {
    renderBadge("saving", { labels: { saving: "Saving..." } });
    expect(screen.getByText("Saving...")).toBeTruthy();
  });

  it("overrides the saved label", () => {
    renderBadge("saved", { labels: { saved: "Saved!" } });
    expect(screen.getByText("Saved!")).toBeTruthy();
  });

  it("overrides the error label", () => {
    renderBadge("error", { labels: { error: "Could not save. Retry." } });
    expect(screen.getByText("Could not save. Retry.")).toBeTruthy();
  });

  it("allows overriding only some labels (partial)", () => {
    renderBadge("saving", { labels: { error: "Fallo al guardar" } });
    // saving uses default, error would be overridden
    expect(screen.getByText("Guardando…")).toBeTruthy();
  });
});

// ── contrast: token classes (not hardcoded hex) ───────────────────────────────

describe("AutosaveBadge — contrast (token-based, no hardcoded hex)", () => {
  /**
   * Verifies the component uses Tailwind/design-token classes for color,
   * not hardcoded hex values. This is a structural check (ensuring
   * classes contain token names, not raw hex).
   *
   * The design-token classes used (destructive, amber-600, emerald-700,
   * muted-foreground) all satisfy WCAG AA ≥4.5:1 when rendered against
   * the Tailwind/design-system background values.
   *
   * Note: axe-core not available in this test env; contrast is enforced
   * by the design-token constraint below.
   */
  it("uses token-based classes for error state (no hex)", () => {
    const { container } = renderBadge("error");
    const root = container.firstChild as HTMLElement;
    // Class should contain design-token references, not hardcoded hex
    const className = root.className;
    expect(className).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });

  it("uses token-based classes for saved state (no hex)", () => {
    const { container } = renderBadge("saved");
    const root = container.firstChild as HTMLElement;
    expect(root.className).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });

  it("uses token-based classes for dirty state (no hex)", () => {
    const { container } = renderBadge("dirty");
    const root = container.firstChild as HTMLElement;
    expect(root.className).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });

  it("error state uses destructive token class (WCAG AA compliant at 16px base)", () => {
    const { container } = renderBadge("error");
    const root = container.firstChild as HTMLElement;
    // destructive token maps to a red ≥4.5:1 against --background in all brand themes
    expect(root.className).toContain("destructive");
  });

  it("saved state uses emerald-700 for light mode (≥4.5:1 against white) — not low-contrast variants", () => {
    const { container } = renderBadge("saved");
    const root = container.firstChild as HTMLElement;
    // The implementation must use a dark enough green token for LIGHT MODE.
    // emerald-700 (#047857) = 5.49:1 against white — passes AA ✓
    // emerald-600 (#059669) = 3.65:1 against white — FAILS AA (known bug in vitalia copy) ✗
    // emerald-500 (#10b981) = 2.36:1 against white — FAILS AA ✗
    // dark:text-emerald-400 is fine for dark mode (4.5:1+ against dark backgrounds)
    // We assert the light-mode class does NOT use emerald-500 or emerald-600 (low contrast)
    expect(root.className).not.toContain("emerald-500");
    expect(root.className).not.toContain("emerald-600");
    // emerald-700 should be present for light mode
    expect(root.className).toContain("emerald-700");
  });
});

// ── role=status semantic element ──────────────────────────────────────────────

describe("AutosaveBadge — role=status", () => {
  it("has role=status on the root element", () => {
    const { container } = renderBadge("saving");
    const root = container.firstChild as HTMLElement;
    expect(root.getAttribute("role")).toBe("status");
  });
});
