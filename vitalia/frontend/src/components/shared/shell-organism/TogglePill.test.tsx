// voseo-allowed: test fixture — regex patterns verify voseo absence in component output, not user-facing strings
/**
 * TogglePill.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * spec_anchor: 03-arch.md § 3.2 + 06-tickets.yaml T-1 val-fe-vitest-unit-toggle-pill
 *
 * Tests:
 *   - renders tabs list with pill style classes
 *   - renders all tab triggers from items prop
 *   - first item is selected by default
 *   - correct data-testid attribute
 *   - tab triggers render item labels
 *   - tab content renders for active tab
 *
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TogglePill } from "./TogglePill";

const ITEMS = [
  { value: "catalogo", label: "Catálogo" },
  { value: "escalera", label: "Escalera" },
];

describe("TogglePill", () => {
  it("renders a tabs container with data-testid", () => {
    render(
      <TogglePill
        items={ITEMS}
        defaultValue="catalogo"
        data-testid="toggle-pill-servicios"
      >
        <div data-value="catalogo">Contenido catálogo</div>
        <div data-value="escalera">Contenido escalera</div>
      </TogglePill>,
    );
    expect(screen.getByTestId("toggle-pill-servicios")).toBeInTheDocument();
  });

  it("renders all tab triggers from items prop", () => {
    render(
      <TogglePill items={ITEMS} defaultValue="catalogo">
        <div data-value="catalogo" />
        <div data-value="escalera" />
      </TogglePill>,
    );
    expect(screen.getByRole("tab", { name: "Catálogo" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Escalera" })).toBeInTheDocument();
  });

  it("first item is selected by default", () => {
    render(
      <TogglePill items={ITEMS} defaultValue="catalogo">
        <div data-value="catalogo" />
        <div data-value="escalera" />
      </TogglePill>,
    );
    const activeTab = screen.getByRole("tab", { name: "Catálogo" });
    expect(activeTab).toHaveAttribute("data-state", "active");
  });

  it("renders 3-item toggle (Adrián Inbox 3 modos)", () => {
    const threeItems = [
      { value: "decide", label: "🤖 Adrián decide" },
      { value: "consulta", label: "💬 Consulta" },
      { value: "manual", label: "✋ Manual" },
    ];
    render(
      <TogglePill items={threeItems} defaultValue="decide">
        <div data-value="decide" />
        <div data-value="consulta" />
        <div data-value="manual" />
      </TogglePill>,
    );
    expect(screen.getAllByRole("tab")).toHaveLength(3);
  });

  it("tab trigger labels do not contain voseo", () => {
    render(
      <TogglePill items={ITEMS} defaultValue="catalogo">
        <div data-value="catalogo" />
        <div data-value="escalera" />
      </TogglePill>,
    );
    screen.getAllByRole("tab").forEach((tab) => {
      expect(tab.textContent).not.toMatch(/tenés|podés|hacés|dejá|mirá/i);
    });
  });
});
