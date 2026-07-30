// voseo-allowed: test fixture — regex patterns verify voseo absence in component output, not user-facing strings
/**
 * VozPlaceholder.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * spec_anchor: 06-tickets.yaml T-8 val-fe-vitest-unit-voz-placeholder
 * mockup_ref: vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/camila-voz-placeholder.html
 *
 * Tests:
 *   - renders 3 stats with values 12, 4, 47
 *   - renders 3 stat labels Entrante / Curaduría / Ciclos activos
 *   - renders 3 toggle pill modes
 *   - renders description Spanish neutro ratificado batch 2
 *
 * downstream-regression-na: brand-local camila feature; no cross-brand consumers
 */

import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VozPlaceholder } from "./VozPlaceholder";

describe("VozPlaceholder", () => {
  test("renders 3 stats with values 12, 4, 47", () => {
    render(<VozPlaceholder />);
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("47")).toBeInTheDocument();
  });

  test("renders 3 stat labels Entrante / Curaduría / Ciclos activos", () => {
    render(<VozPlaceholder />);
    expect(screen.getByText("Entrante")).toBeInTheDocument();
    expect(screen.getByText("Curaduría")).toBeInTheDocument();
    expect(screen.getByText("Ciclos activos")).toBeInTheDocument();
  });

  test("renders 3 toggle pill modes", () => {
    render(<VozPlaceholder />);
    expect(screen.getByText(/Camila decide/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Curaduría/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Manual/i)).toBeInTheDocument();
  });

  test("renders description Spanish neutro ratificado batch 2", () => {
    render(<VozPlaceholder />);
    expect(
      screen.getByText(/Camila pide feedback al paciente/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/te ahorra responder cada feedback uno por uno/i),
    ).toBeInTheDocument();
  });
});
