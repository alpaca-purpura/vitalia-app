/**
 * Unit tests — NetworkErrorFallback (Server Component) + RefreshButton (Client leaf).
 *
 * Vitest + @testing-library/react.
 *
 * NetworkErrorFallback es un Server Component puro (sin hooks). Lo testeamos
 * con @testing-library/react que lo renderiza sincrónicamente (compatible con
 * Server Components que no usen async data — este componente es síncrono y
 * solo compone JSX).
 *
 * RefreshButton usa useRouter() → mockeamos next/navigation.
 *
 * spec_anchor: 03-arch-fe.md § 2.1 + 06-tickets.yaml T-3 (SC-7)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// Mock next/navigation para RefreshButton
const mockRefresh = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: mockRefresh }),
}));

import { NetworkErrorFallback } from "./NetworkErrorFallback";
import { RefreshButton } from "./RefreshButton";

describe("NetworkErrorFallback", () => {
  it("renderiza el mensaje de error de red", () => {
    render(<NetworkErrorFallback />);

    expect(
      screen.getByText("Estamos teniendo problemas conectando con el servidor"),
    ).toBeInTheDocument();
  });

  it("renderiza la descripción correcta", () => {
    render(<NetworkErrorFallback />);

    expect(
      screen.getByText("Intenta de nuevo en unos segundos."),
    ).toBeInTheDocument();
  });

  it("tiene data-testid='network-error-fallback'", () => {
    render(<NetworkErrorFallback />);

    expect(screen.getByTestId("network-error-fallback")).toBeInTheDocument();
  });

  it("contiene el botón Reintentar", () => {
    render(<NetworkErrorFallback />);

    expect(screen.getByTestId("network-error-retry")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Reintentar" }),
    ).toBeInTheDocument();
  });

  it("renderiza el ícono de advertencia con aria-label", () => {
    render(<NetworkErrorFallback />);

    expect(
      screen.getByRole("img", { name: "Advertencia" }),
    ).toBeInTheDocument();
  });
});

describe("RefreshButton", () => {
  beforeEach(() => {
    mockRefresh.mockClear();
  });

  it("renderiza el botón con texto 'Reintentar'", () => {
    render(<RefreshButton />);

    expect(
      screen.getByRole("button", { name: "Reintentar" }),
    ).toBeInTheDocument();
  });

  it("tiene data-testid='network-error-retry'", () => {
    render(<RefreshButton />);

    expect(screen.getByTestId("network-error-retry")).toBeInTheDocument();
  });

  it("llama router.refresh() al hacer click", () => {
    render(<RefreshButton />);

    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));

    expect(mockRefresh).toHaveBeenCalledTimes(1);
  });
});
