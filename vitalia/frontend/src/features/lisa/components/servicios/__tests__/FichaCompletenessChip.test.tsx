// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FichaCompletenessChip } from "../FichaCompletenessChip";

describe("FichaCompletenessChip", () => {
  it("renders the filled/total count as 'X/Y'", () => {
    render(<FichaCompletenessChip filled={4} total={7} />);
    expect(screen.getByText("4/7")).toBeInTheDocument();
  });

  it("exposes the percentage via aria for accessibility", () => {
    render(<FichaCompletenessChip filled={3} total={6} />);
    const chip = screen.getByTestId("completeness-chip");
    // 3/6 = 50%
    expect(chip).toHaveAttribute("aria-valuenow", "50");
  });

  it("shows 100% complete when all fields are filled", () => {
    render(<FichaCompletenessChip filled={7} total={7} />);
    expect(screen.getByText("7/7")).toBeInTheDocument();
    expect(screen.getByTestId("completeness-chip")).toHaveAttribute("aria-valuenow", "100");
  });

  it("handles zero total without dividing by zero", () => {
    render(<FichaCompletenessChip filled={0} total={0} />);
    expect(screen.getByText("0/0")).toBeInTheDocument();
    expect(screen.getByTestId("completeness-chip")).toHaveAttribute("aria-valuenow", "0");
  });
});
