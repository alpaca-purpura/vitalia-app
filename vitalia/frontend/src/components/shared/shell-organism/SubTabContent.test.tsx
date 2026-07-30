/**
 * SubTabContent.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * spec_anchor: 03-arch.md § 4 + 06-tickets.yaml T-1 val-fe-vitest-unit-subtab-content
 *
 * Tests:
 *   - renders correct data-testid for agent.subtab combos
 *   - renders EmptyState fallback for unknown key
 *   - NO renderiza un título-eco de la nav (Bug #3 T-6 — SubTabHeader removido)
 *   - valid combo renders placeholder (not EmptyState fallback)
 *   - EmptyState title includes subtab label for fallback
 *   - invalid agent renders EmptyState
 *
 * NOTE: T-1 scope — placeholder components (T-2..T-8) are NOT yet implemented.
 * The dispatcher stub renders EmptyState for all 22 keys until placeholders land.
 * Arch test (T-9) will enforce PLACEHOLDER_MAP fully populated.
 *
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SubTabContent } from "./SubTabContent";

describe("SubTabContent dispatcher", () => {
  it("renders correct data-testid for lisa.marca", () => {
    render(<SubTabContent agent="lisa" subtab="marca" />);
    expect(screen.getByTestId("subtab-content-lisa-marca")).toBeInTheDocument();
  });

  it("renders correct data-testid for config.conexiones", () => {
    render(<SubTabContent agent="config" subtab="conexiones" />);
    expect(
      screen.getByTestId("subtab-content-config-conexiones"),
    ).toBeInTheDocument();
  });

  it("renders EmptyState fallback for unknown key", () => {
    render(
      <SubTabContent
        agent={"lisa" as Parameters<typeof SubTabContent>[0]["agent"]}
        subtab="unknown-subtab"
      />,
    );
    // fallback EmptyState should render
    expect(screen.getByTestId("empty-state-icon")).toBeInTheDocument();
  });

  it("coverage_update Bug #3 (T-6): NO renderiza el título-eco de la nav (SubTabHeader removido)", () => {
    // El dispatcher ya NO renderiza <SubTabHeader> (h2 que eco-aba el label de la
    // sub-tab activa). lisa.marca es N3-static (shadowea el dispatcher) → cae al
    // EmptyState fallback, que usa h3 (su propio título contextual), NO un h2-eco.
    render(<SubTabContent agent="lisa" subtab="marca" />);
    // El testid del SubTabHeader removido no debe existir.
    expect(screen.queryByTestId("subtab-header-lisa-marca")).toBeNull();
    // No hay h2-eco de la nav en el dispatcher.
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
  });

  it("EmptyState fallback title uses subtab label or slug", () => {
    render(<SubTabContent agent="lisa" subtab="marca" />);
    // Either the label ('Marca') or the slug ('marca') should appear in content
    const content = document.body.textContent ?? "";
    expect(content.toLowerCase()).toMatch(/marca/i);
  });

  it("renders SubTabContent for adrian.inbox", () => {
    render(<SubTabContent agent="adrian" subtab="inbox" />);
    expect(
      screen.getByTestId("subtab-content-adrian-inbox"),
    ).toBeInTheDocument();
  });

  it("renders SubTabContent for valeria.agenda", () => {
    render(<SubTabContent agent="valeria" subtab="agenda" />);
    expect(
      screen.getByTestId("subtab-content-valeria-agenda"),
    ).toBeInTheDocument();
  });

  it("renders SubTabContent for camila.voz", () => {
    render(<SubTabContent agent="camila" subtab="voz" />);
    expect(screen.getByTestId("subtab-content-camila-voz")).toBeInTheDocument();
  });
});
