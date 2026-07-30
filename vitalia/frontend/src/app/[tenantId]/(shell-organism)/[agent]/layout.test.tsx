/**
 * Unit tests — [agent]/layout.tsx (Server Component).
 *
 * Vitest + @testing-library/react.
 *
 * AgentLayout valida el agent slug y llama notFound() si inválido.
 * Es un Server Component async — lo testamos con render async
 * y mocks de next/navigation.
 *
 * TDD RED-first → GREEN: tests escritos antes de la implementación.
 * spec_anchor: 03-arch-fe.md § 9.5 + 06-tickets.yaml T-4 SC-2
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// vi.mock is hoisted — cannot reference variables declared below.
// Use vi.fn() inline and then get the spy via import.
vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
  redirect: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// Import AFTER mocks
import * as navigation from "next/navigation";
import AgentLayout from "./layout";

const mockNotFound = vi.mocked(navigation.notFound);

const makeParams = (agent: string) =>
  Promise.resolve({ tenantId: "clinic-x", agent });

describe("AgentLayout", () => {
  beforeEach(() => {
    mockNotFound.mockClear();
  });

  it("renderiza children cuando agent slug es válido (lisa)", async () => {
    const { container } = render(
      await AgentLayout({
        children: <div data-testid="child">hijo</div>,
        params: makeParams("lisa"),
      }),
    );
    expect(screen.getByTestId("child")).toBeInTheDocument();
    expect(container.textContent).toContain("hijo");
  });

  it("renderiza children cuando agent slug es válido (mateo — v1.2 Operar en ribbon)", async () => {
    // v1.2 (2026-05-30): mateo IS a valid ribbon agent now
    render(
      await AgentLayout({
        children: <div data-testid="child-v">mateo</div>,
        params: makeParams("mateo"),
      }),
    );
    expect(screen.getByTestId("child-v")).toBeInTheDocument();
  });

  it("renderiza children cuando agent slug es válido (config)", async () => {
    render(
      await AgentLayout({
        children: <div data-testid="child-cfg">config</div>,
        params: makeParams("config"),
      }),
    );
    expect(screen.getByTestId("child-cfg")).toBeInTheDocument();
  });

  it("llama notFound() cuando agent slug es inválido (foo)", async () => {
    await expect(
      AgentLayout({
        children: <div>irrelevante</div>,
        params: makeParams("foo"),
      }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    expect(mockNotFound).toHaveBeenCalledTimes(1);
  });

  it("llama notFound() cuando agent slug es 'valeria' (v1.2 — supervisor sidebar, no ribbon tab)", async () => {
    // v1.2 (2026-05-30): valeria is NOT a valid ribbon agent — isValidAgent('valeria') = false
    await expect(
      AgentLayout({
        children: <div>valeria</div>,
        params: makeParams("valeria"),
      }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    expect(mockNotFound).toHaveBeenCalledTimes(1);
  });

  it("llama notFound() cuando agent slug está vacío", async () => {
    await expect(
      AgentLayout({
        children: <div>empty</div>,
        params: makeParams(""),
      }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    expect(mockNotFound).toHaveBeenCalledTimes(1);
  });

  it("llama notFound() con payload XSS", async () => {
    await expect(
      AgentLayout({
        children: <div>xss</div>,
        params: makeParams("<script>alert(1)</script>"),
      }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    expect(mockNotFound).toHaveBeenCalledTimes(1);
  });
});
