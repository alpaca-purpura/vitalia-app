/**
 * TenantOption.test.tsx — TDD RED-first tests for TenantOption molecule
 * F1-S3 vitalia-fase1-tenant-switcher — T-3
 *
 * TenantOption renders: TenantBadge + name + city subtitle + Check icon (when active).
 *
 * gherkin_coverage: AC-3 + Scenario 1 — active marker check + bg-accent/40
 *
 * downstream-regression-na: brand-local shell-organism test; no cross-brand consumers
 */

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TenantOption } from "../TenantOption";

const SONRISA = { id: "sonrisa-plena", name: "Sonrisa Plena", city: "Lima" };

describe("TenantOption", () => {
  it("renders TenantBadge initials (SP for Sonrisa Plena)", () => {
    const { getByText } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    expect(getByText("SP")).toBeInTheDocument();
  });

  it("renders tenant name", () => {
    const { getByText } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    expect(getByText("Sonrisa Plena")).toBeInTheDocument();
  });

  it("renders city subtitle", () => {
    const { getByText } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    expect(getByText("Lima")).toBeInTheDocument();
  });

  it("active=true renders Check icon (aria-hidden)", () => {
    const { container } = render(
      <TenantOption tenant={SONRISA} active={true} />,
    );
    // Lucide Check renders as svg
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("active=true renders sr-only 'Clínica activa'", () => {
    const { getByText } = render(
      <TenantOption tenant={SONRISA} active={true} />,
    );
    const srOnly = getByText("Clínica activa");
    expect(srOnly).toBeInTheDocument();
    expect(srOnly.className).toContain("sr-only");
  });

  it("active=false does NOT render Check icon", () => {
    const { container } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    const svg = container.querySelector("svg");
    expect(svg).toBeNull();
  });

  it("active=false does NOT render 'Clínica activa'", () => {
    const { queryByText } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    expect(queryByText("Clínica activa")).toBeNull();
  });

  it("active row has bg-accent/40 class", () => {
    const { getByTestId } = render(
      <TenantOption tenant={SONRISA} active={true} />,
    );
    const row = getByTestId(`tenant-option-${SONRISA.id}`);
    expect(row.className).toContain("bg-accent/40");
  });

  it("inactive row has hover:bg-muted class", () => {
    const { getByTestId } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    const row = getByTestId(`tenant-option-${SONRISA.id}`);
    expect(row.className).toContain("hover:bg-muted");
  });

  it("data-testid format is tenant-option-{tenantId}", () => {
    const { getByTestId } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    expect(getByTestId("tenant-option-sonrisa-plena")).toBeInTheDocument();
  });

  it("data-active attribute matches active prop (true)", () => {
    const { getByTestId } = render(
      <TenantOption tenant={SONRISA} active={true} />,
    );
    expect(getByTestId("tenant-option-sonrisa-plena")).toHaveAttribute(
      "data-active",
      "true",
    );
  });

  it("data-active attribute matches active prop (false)", () => {
    const { getByTestId } = render(
      <TenantOption tenant={SONRISA} active={false} />,
    );
    expect(getByTestId("tenant-option-sonrisa-plena")).toHaveAttribute(
      "data-active",
      "false",
    );
  });

  it("is a named export (not default)", () => {
    expect(typeof TenantOption).toBe("function");
  });
});
