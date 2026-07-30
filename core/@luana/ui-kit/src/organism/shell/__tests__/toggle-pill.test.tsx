// cap: platform.lift-shell-chrome-ui-kit
/**
 * toggle-pill.test.tsx — T-K3 port of TogglePill.test.tsx.
 *
 * Port of conduct verbatim. Generic items (no vitalia-specific labels).
 * TogglePill props are identical between vitalia and kit (no brand coupling).
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TogglePill } from "../TogglePill";

const ITEMS = [
  { value: "opcion-a", label: "Opción A" },
  { value: "opcion-b", label: "Opción B" },
];

describe("TogglePill — render", () => {
  it("renders a tabs container with data-testid", () => {
    render(
      <TogglePill
        items={ITEMS}
        defaultValue="opcion-a"
        data-testid="toggle-pill-test"
      >
        <div data-value="opcion-a">Contenido A</div>
        <div data-value="opcion-b">Contenido B</div>
      </TogglePill>,
    );
    expect(screen.getByTestId("toggle-pill-test")).toBeInTheDocument();
  });

  it("renders all tab triggers from items prop", () => {
    render(
      <TogglePill items={ITEMS} defaultValue="opcion-a">
        <div data-value="opcion-a" />
        <div data-value="opcion-b" />
      </TogglePill>,
    );
    expect(screen.getByRole("tab", { name: "Opción A" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Opción B" })).toBeInTheDocument();
  });

  it("defaultValue item is selected (data-state='active')", () => {
    render(
      <TogglePill items={ITEMS} defaultValue="opcion-a">
        <div data-value="opcion-a" />
        <div data-value="opcion-b" />
      </TogglePill>,
    );
    const activeTab = screen.getByRole("tab", { name: "Opción A" });
    expect(activeTab).toHaveAttribute("data-state", "active");
  });

  it("renders 3-item toggle (3 modes)", () => {
    const threeItems = [
      { value: "modo-auto", label: "🤖 Auto" },
      { value: "modo-consulta", label: "💬 Consulta" },
      { value: "modo-manual", label: "✋ Manual" },
    ];
    render(
      <TogglePill items={threeItems} defaultValue="modo-auto">
        <div data-value="modo-auto" />
        <div data-value="modo-consulta" />
        <div data-value="modo-manual" />
      </TogglePill>,
    );
    expect(screen.getAllByRole("tab")).toHaveLength(3);
  });

  it("tab trigger labels do not contain voseo (Spanish neutro)", () => {
    render(
      <TogglePill items={ITEMS} defaultValue="opcion-a">
        <div data-value="opcion-a" />
        <div data-value="opcion-b" />
      </TogglePill>,
    );
    screen.getAllByRole("tab").forEach((tab) => {
      expect(tab.textContent).not.toMatch(/tenés|podés|hacés|dejá|mirá/i);
    });
  });
});
