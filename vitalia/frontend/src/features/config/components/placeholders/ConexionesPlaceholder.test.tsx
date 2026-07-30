/**
 * ConexionesPlaceholder.test.tsx — Vitest unit tests.
 * F1-S10 vitalia-fase1-empty-states — T-3
 *
 * TDD RED-first: tests written before component (per tdd-mandatory.md).
 * Tests cover:
 *   1. All 6 category names rendered
 *   2. Badge counts correct: 2 activas (Marketing) + 1 activa (Mensajería) + 1 activa (Calendarios) visible
 *   3. "no configurado" badges for Pagos, Presencia, Técnicas
 *   4. Header title and description
 *
 * spec_anchor: 06-tickets.yaml T-3 acceptance validators
 *   val-fe-vitest-unit-conexiones (implied), val-fe-tsc, val-fe-lint
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConexionesPlaceholder } from "./ConexionesPlaceholder";

describe("ConexionesPlaceholder", () => {
  it("renders all 6 connection category names", () => {
    render(<ConexionesPlaceholder />);

    expect(screen.getByText("Marketing")).toBeInTheDocument();
    expect(screen.getByText("Mensajería")).toBeInTheDocument();
    expect(screen.getByText("Pagos")).toBeInTheDocument();
    expect(screen.getByText("Calendarios")).toBeInTheDocument();
    expect(screen.getByText("Presencia")).toBeInTheDocument();
    expect(screen.getByText("Técnicas")).toBeInTheDocument();
  });

  it("shows correct active badges: '2 activas' (Marketing), '1 activa' (Mensajería), '1 activa' (Calendarios)", () => {
    render(<ConexionesPlaceholder />);

    // Badge content — "2 activas" for Marketing
    expect(screen.getByTestId("badge-active-marketing")).toHaveTextContent(
      "2 activas",
    );

    // "1 activa" appears for both Mensajería and Calendarios
    const oneActivaBadges = screen.getAllByText("1 activa");
    expect(oneActivaBadges).toHaveLength(2);

    // Verify specifically mensajería and calendarios have active badges
    expect(screen.getByTestId("badge-active-mensajeria")).toHaveTextContent(
      "1 activa",
    );
    expect(screen.getByTestId("badge-active-calendarios")).toHaveTextContent(
      "1 activa",
    );
  });

  it("shows 'no configurado' for Pagos, Presencia, and Técnicas", () => {
    render(<ConexionesPlaceholder />);

    // 3 cards should show "no configurado"
    const noConfiguradoBadges = screen.getAllByText("no configurado");
    expect(noConfiguradoBadges).toHaveLength(3);

    // Verify via testids
    expect(screen.getByTestId("badge-none-pagos")).toHaveTextContent(
      "no configurado",
    );
    expect(screen.getByTestId("badge-none-presencia")).toHaveTextContent(
      "no configurado",
    );
    expect(screen.getByTestId("badge-none-tecnicas")).toHaveTextContent(
      "no configurado",
    );
  });

  it("renders header with title 'Conexiones' and description", () => {
    render(<ConexionesPlaceholder />);

    expect(
      screen.getByRole("heading", { level: 2, name: "Conexiones" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Integraciones externas agrupadas por categoría."),
    ).toBeInTheDocument();
  });

  it("renders providers list for each category", () => {
    render(<ConexionesPlaceholder />);

    expect(
      screen.getByText("Meta Ads · Google Ads · TikTok Ads"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("WhatsApp · ManyChat · Instagram DM"),
    ).toBeInTheDocument();
    expect(screen.getByText("Stripe · MercadoPago · Yape")).toBeInTheDocument();
    expect(screen.getByText("Google Calendar · Outlook")).toBeInTheDocument();
    expect(
      screen.getByText("Sitio web · Instagram · Facebook · Google Business"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Webhooks · API tokens · Zapier"),
    ).toBeInTheDocument();
  });

  it("renders '→ Configurar' arrow on each card (6 instances)", () => {
    render(<ConexionesPlaceholder />);

    const arrows = screen.getAllByText("→ Configurar");
    expect(arrows).toHaveLength(6);
  });

  it("renders exactly 6 connection cards", () => {
    const { container } = render(<ConexionesPlaceholder />);

    const cards = container.querySelectorAll("[data-testid^='conexion-card-']");
    expect(cards).toHaveLength(6);
  });
});
