/**
 * EmbudoPlaceholder.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * F1-S10 vitalia-fase1-empty-states — T-4
 * spec_anchor: 06-tickets.yaml T-4 val-fe-vitest-unit-embudo
 *
 * Tests:
 *   - renders 6 Kanban column headers (Interesado/Calificando/Considerando/Listo/Reservado/Decidió no)
 *   - renders lead names mock: María G., Carlos P., Ana V., JP Méndez, Rosa V., Camila B., Iván S.
 *   - renders totals: "12 · S/ 84k", "8 · S/ 62k", "5 · S/ 41k", "3 · S/ 28k", "2 · S/ 15k", "4 · —"
 *   - click toggle "Lista" → EmptyState "Vista lista — próximamente" aparece
 *   - click back "Kanban" → Kanban columns reaparecen
 *
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmbudoPlaceholder } from "./EmbudoPlaceholder";

describe("EmbudoPlaceholder", () => {
  it("renders 6 Kanban column headers", () => {
    render(<EmbudoPlaceholder />);
    // Use getAllByText for labels that appear in multiple places (e.g., column header + lead card detail)
    expect(screen.getAllByText(/Interesado/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Calificando/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Considerando/).length).toBeGreaterThanOrEqual(
      1,
    );
    expect(screen.getAllByText(/Listo/).length).toBeGreaterThanOrEqual(1);
    // "Reservado" appears both as column header and in lead card details
    expect(screen.getAllByText(/Reservado/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Decidió no/)).toBeInTheDocument();
  });

  it("renders lead names mock in Kanban state", () => {
    render(<EmbudoPlaceholder />);
    expect(screen.getByText("María G.")).toBeInTheDocument();
    expect(screen.getByText("Carlos P.")).toBeInTheDocument();
    expect(screen.getByText("Ana V.")).toBeInTheDocument();
    expect(screen.getByText("JP Méndez")).toBeInTheDocument();
    expect(screen.getByText("Rosa V.")).toBeInTheDocument();
    expect(screen.getByText("Camila B.")).toBeInTheDocument();
    expect(screen.getByText("Iván S.")).toBeInTheDocument();
  });

  it("renders column totals verbatim from spec", () => {
    render(<EmbudoPlaceholder />);
    expect(screen.getByText("12 · S/ 84k")).toBeInTheDocument();
    expect(screen.getByText("8 · S/ 62k")).toBeInTheDocument();
    expect(screen.getByText("5 · S/ 41k")).toBeInTheDocument();
    expect(screen.getByText("3 · S/ 28k")).toBeInTheDocument();
    expect(screen.getByText("2 · S/ 15k")).toBeInTheDocument();
    expect(screen.getByText("4 · —")).toBeInTheDocument();
  });

  it("shows EmptyState placeholder when Lista toggle is selected", async () => {
    const user = userEvent.setup();
    render(<EmbudoPlaceholder />);
    // Click the Lista tab trigger
    const listaTab = screen.getByRole("tab", { name: "Lista" });
    await user.click(listaTab);
    expect(screen.getByText("Vista lista — próximamente")).toBeInTheDocument();
  });

  it("shows Kanban columns when Kanban toggle is selected after switching", async () => {
    const user = userEvent.setup();
    render(<EmbudoPlaceholder />);
    // Switch to Lista first
    await user.click(screen.getByRole("tab", { name: "Lista" }));
    // Switch back to Kanban
    await user.click(screen.getByRole("tab", { name: "Kanban" }));
    // Kanban content should be visible again
    expect(screen.getByText("María G.")).toBeInTheDocument();
    expect(screen.getByText("Carlos P.")).toBeInTheDocument();
  });

  it("renders SubTabHeader with title Embudo and description", () => {
    render(<EmbudoPlaceholder />);
    expect(
      screen.getByRole("heading", { level: 2, name: /Embudo/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Pipeline de leads en 6 estados/),
    ).toBeInTheDocument();
  });

  it("does not contain voseo in user-facing text", () => {
    // voseo-allowed: regex tests for absence of voseo in rendered output (technical fixture, not user-facing string)
    const { container } = render(<EmbudoPlaceholder />);
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/tenés|podés|hacés|dejá|mirá|sos\b/i);
  });
});
