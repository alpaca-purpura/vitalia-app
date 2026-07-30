/**
 * FidelizacionKPIsHero — TDD RED tests.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FidelizacionKPIsHero } from "../FidelizacionKPIsHero";
import type { FidelizacionSummaryResponse } from "../../types/fidelizacion-summary";

const mockSummary: FidelizacionSummaryResponse = {
  patientsInFollowup: 42,
  nearAbandonment: 7,
  returnRate: 0.68,
  reEngagedThisPeriod: 12,
  npsAverage: 8.4,
  npsResponsesCount: 35,
  trendVsPreviousPeriod: {
    patientsInFollowup: 5,
    nearAbandonment: -2,
    returnRate: 0.05,
    reEngagedThisPeriod: 3,
    npsAverage: 0.2,
  },
};

describe("FidelizacionKPIsHero", () => {
  it("renders loading skeleton when isPending", () => {
    render(<FidelizacionKPIsHero isPending={true} data={null} />);
    // Should show skeleton/loading state, not actual numbers
    expect(screen.queryByText("42")).not.toBeInTheDocument();
  });

  it("renders KPI values when data is loaded", () => {
    render(<FidelizacionKPIsHero isPending={false} data={mockSummary} />);
    // Patients in followup
    expect(screen.getByText("42")).toBeInTheDocument();
    // Near abandonment
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("renders stat cards with role=status for accessibility", () => {
    render(<FidelizacionKPIsHero isPending={false} data={mockSummary} />);
    const statusElements = screen.getAllByRole("status");
    expect(statusElements.length).toBeGreaterThan(0);
  });

  it("renders aria-labels on stat cards", () => {
    render(<FidelizacionKPIsHero isPending={false} data={mockSummary} />);
    // Each KPI card should have descriptive aria-label
    const labeledElements = screen
      .getAllByRole("status")
      .filter((el) => el.getAttribute("aria-label") !== null);
    expect(labeledElements.length).toBeGreaterThan(0);
  });

  it("renders null summary gracefully", () => {
    render(<FidelizacionKPIsHero isPending={false} data={null} />);
    // Should render empty state without crashing
    expect(screen.getByRole("region")).toBeInTheDocument();
  });
});
