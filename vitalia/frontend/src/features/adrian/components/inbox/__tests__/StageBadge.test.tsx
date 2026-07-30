/**
 * StageBadge.test.tsx — Unit tests for StageBadge + lead-stage-meta (UI-AUDIT #5b).
 *
 * Covers: label resolution, stage-specific color class, neutral fallback for
 * unknown stages, and the data-testid override (back-compat with the inbox list
 * `stage-chip` id the list tests + e2e POM depend on).
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StageBadge } from "../StageBadge";
import {
  LEAD_STAGE_META,
  getLeadStageMeta,
} from "@/lib/stages/lead-stage-meta";

describe("lead-stage-meta", () => {
  it("maps every known stage to a label + non-neutral color class", () => {
    for (const [slug, meta] of Object.entries(LEAD_STAGE_META)) {
      expect(meta.label.length).toBeGreaterThan(0);
      expect(meta.colorClass).not.toContain("bg-muted");
      expect(getLeadStageMeta(slug)).toEqual(meta);
    }
  });

  it("falls back to a neutral chip for an unknown stage", () => {
    const meta = getLeadStageMeta("totally-unknown");
    expect(meta.label).toBe("totally-unknown");
    expect(meta.colorClass).toContain("bg-muted");
  });
});

describe("StageBadge", () => {
  it("renders the Spanish neutro label for a known stage", () => {
    render(<StageBadge stage="interesado" />);
    expect(screen.getByText("Interesado")).toBeDefined();
  });

  it("applies the stage-specific color class", () => {
    render(<StageBadge stage="reservado_deposito" />);
    const badge = screen.getByTestId("stage-badge-reservado_deposito");
    expect(badge.className).toContain("bg-emerald-100");
  });

  it("honors a data-testid override (keeps the legacy stage-chip id)", () => {
    render(<StageBadge stage="calificando" data-testid="stage-chip" />);
    expect(screen.getByTestId("stage-chip")).toBeDefined();
    expect(screen.queryByTestId("stage-badge-calificando")).toBeNull();
  });

  it("renders an unknown stage without crashing (neutral fallback)", () => {
    render(<StageBadge stage="weird" />);
    const badge = screen.getByTestId("stage-badge-weird");
    expect(badge.textContent).toBe("weird");
    expect(badge.className).toContain("bg-muted");
  });
});
