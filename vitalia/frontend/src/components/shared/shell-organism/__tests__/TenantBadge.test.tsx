/**
 * TenantBadge.test.tsx — TDD RED-first tests for TenantBadge Server Component
 * F1-S3 vitalia-fase1-tenant-switcher — T-2
 *
 * TenantBadge is a Server Component that renders 2-char initials
 * with a deterministic background color from tenant-palette.
 *
 * gherkin_coverage: AC-3 + Scenario 1 — TenantBadge renderiza initials correctos + palette color
 *
 * downstream-regression-na: brand-local shell-organism test; no cross-brand consumers
 */

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TenantBadge } from "../TenantBadge";
import { pickPaletteColor } from "@/lib/tenant-palette";

const SONRISA = { id: "sonrisa-plena", name: "Sonrisa Plena", city: "Lima" };
const DERMALIA = { id: "dermalia-mx", name: "Dermalia MX", city: "CDMX" };
const CLINCARE = {
  id: "clinicare-bogota",
  name: "ClíniCare Bogotá",
  city: "Bogotá",
};

describe("TenantBadge", () => {
  it("renders 2-char uppercase initials from name (Sonrisa Plena → SP)", () => {
    const { getByText } = render(<TenantBadge tenant={SONRISA} />);
    expect(getByText("SP")).toBeInTheDocument();
  });

  it("renders 2-char uppercase initials (Dermalia MX → DM)", () => {
    const { getByText } = render(<TenantBadge tenant={DERMALIA} />);
    expect(getByText("DM")).toBeInTheDocument();
  });

  it("renders 2-char uppercase initials from accented name (ClíniCare Bogotá → CB)", () => {
    const { getByText } = render(<TenantBadge tenant={CLINCARE} />);
    expect(getByText("CB")).toBeInTheDocument();
  });

  it("has aria-hidden=true (decorative element)", () => {
    const { container } = render(<TenantBadge tenant={SONRISA} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge).toHaveAttribute("aria-hidden", "true");
  });

  it("applies bg class from pickPaletteColor", () => {
    const { container } = render(<TenantBadge tenant={SONRISA} />);
    const badge = container.firstChild as HTMLElement;
    const { bg } = pickPaletteColor(SONRISA.id);
    expect(badge.className).toContain(bg.replace("bg-", ""));
  });

  it("applies text class from pickPaletteColor", () => {
    const { container } = render(<TenantBadge tenant={SONRISA} />);
    const badge = container.firstChild as HTMLElement;
    const { text } = pickPaletteColor(SONRISA.id);
    expect(badge.className).toContain(text.replace("text-", ""));
  });

  it("is a named export (not default)", () => {
    expect(typeof TenantBadge).toBe("function");
  });

  it("accepts optional className prop", () => {
    const { container } = render(
      <TenantBadge tenant={SONRISA} className="extra-class" />,
    );
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("extra-class");
  });

  it("single word name produces 1-char initial (e.g. 'Vitalia' → 'V')", () => {
    const singleWord = { id: "vitalia-test", name: "Vitalia", city: "Lima" };
    const { getByText } = render(<TenantBadge tenant={singleWord} />);
    expect(getByText("V")).toBeInTheDocument();
  });

  it("empty name falls back to '?'", () => {
    const emptyName = { id: "empty-test", name: "", city: "Lima" };
    const { getByText } = render(<TenantBadge tenant={emptyName} />);
    expect(getByText("?")).toBeInTheDocument();
  });
});
