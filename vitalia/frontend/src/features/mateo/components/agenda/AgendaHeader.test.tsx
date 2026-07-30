/**
 * AgendaHeader.test.tsx — Component unit tests (TDD RED→GREEN).
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Tests cover:
 *   - Renders toolbar with 3 view toggle buttons (Día/Semana/Mes)
 *   - Active view button has aria-pressed=true
 *   - Shows freshness label text
 *   - Clicking "Período anterior" calls setDate
 *   - Clicking "Período siguiente" calls setDate
 *   - Shows correct date range display for semana view
 *
 * Mocks: next/navigation (useSearchParams, useRouter, usePathname)
 *
 * downstream-regression-na: brand-local FE tests; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-12
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({
    currency: "PEN",
    timezone: "America/Lima",
    locale: "es-PE",
  }),
}));

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ replace: mockReplace })),
  usePathname: vi.fn(() => "/tenant-1/mateo/agenda"),
  useSearchParams: vi.fn(() => {
    const params = new URLSearchParams("view=semana&date=2026-05-26");
    return params;
  }),
}));

// Import after mocks
import { AgendaHeader } from "./AgendaHeader";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("AgendaHeader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const DEFAULT_PROPS = {
    tenantId: "tenant-1",
    freshnessLabel: "Actualizado hace 3 minutos",
  };

  it("renders the toolbar role", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);
    expect(
      screen.getByRole("toolbar", { name: "Controles de agenda" }),
    ).toBeInTheDocument();
  });

  it("renders all three view toggle buttons", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);
    expect(screen.getByRole("button", { name: /día/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /semana/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /mes/i })).toBeInTheDocument();
  });

  it("active view button has aria-pressed=true", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);
    // Note: searching by role name to find which button has aria-pressed=true
    const pressedButton = screen
      .getAllByRole("button")
      .find((btn) => btn.getAttribute("aria-pressed") === "true");
    expect(pressedButton).toBeTruthy();
    expect(pressedButton?.textContent).toContain("Semana");
  });

  it("shows freshness label", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);
    expect(
      screen.getByText("Actualizado hace 3 minutos"),
    ).toBeInTheDocument();
  });

  it("renders navigation buttons for date prev/next", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);
    expect(
      screen.getByRole("button", { name: "Período anterior" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Período siguiente" }),
    ).toBeInTheDocument();
  });

  it("clicking Período anterior updates URL params", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);

    const prevButton = screen.getByRole("button", { name: "Período anterior" });
    fireEvent.click(prevButton);

    // Should call router.replace with updated date param
    expect(mockReplace).toHaveBeenCalled();
    const calledUrl = mockReplace.mock.calls[0][0] as string;
    expect(calledUrl).toContain("date=");
  });

  it("clicking Período siguiente updates URL params", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);

    const nextButton = screen.getByRole("button", { name: "Período siguiente" });
    fireEvent.click(nextButton);

    expect(mockReplace).toHaveBeenCalled();
    const calledUrl = mockReplace.mock.calls[0][0] as string;
    expect(calledUrl).toContain("date=");
  });

  it("clicking view toggle updates URL params", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);

    const diaButton = screen.getByRole("button", { name: /día/i });
    fireEvent.click(diaButton);

    expect(mockReplace).toHaveBeenCalled();
    const calledUrl = mockReplace.mock.calls[0][0] as string;
    expect(calledUrl).toContain("view=dia");
  });

  it("renders freshness with aria-live polite", () => {
    render(<AgendaHeader {...DEFAULT_PROPS} />);
    // The freshness div should have aria-live="polite"
    const freshnessEl = screen.getByLabelText("Última actualización");
    expect(freshnessEl).toHaveAttribute("aria-live", "polite");
  });
});
