/**
 * AutosaveBadge.test.tsx — RED tests for AutosaveBadge component.
 * TDD: tests written before implementation (T-5 vitalia-fase2-lisa-marca).
 * spec_anchor: 06-tickets.yaml T-5 validators
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AutosaveBadge } from "../AutosaveBadge";

describe("AutosaveBadge", () => {
  it("renders saving state", () => {
    render(<AutosaveBadge status="saving" />);
    expect(screen.getByText(/guardando/i)).toBeTruthy();
  });

  it("renders saved state with timestamp", () => {
    render(<AutosaveBadge status="saved" savedAt={new Date(Date.now() - 5000)} />);
    expect(screen.getByText(/guardado/i)).toBeTruthy();
  });

  it("renders error state", () => {
    render(<AutosaveBadge status="error" />);
    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.getByText(/error/i)).toBeTruthy();
  });

  it("renders dirty state", () => {
    render(<AutosaveBadge status="dirty" />);
    // dirty = unsaved changes indicator
    expect(screen.getByRole("status")).toBeTruthy();
  });

  it("renders idle state by default", () => {
    render(<AutosaveBadge status="idle" />);
    expect(screen.getByRole("status")).toBeTruthy();
  });

  it("applies accessible role status", () => {
    render(<AutosaveBadge status="saved" />);
    expect(screen.getByRole("status")).toBeTruthy();
  });
});
