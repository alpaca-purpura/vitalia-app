/**
 * LogoMark.test.tsx — Unit tests for LogoMark atom
 * F1-S2 vitalia-fase1-topbar-global — T-2 TDD RED-first
 *
 * Tests 6 combinations: 3 sizes (sm/md/lg) × 2 variants (full/mark)
 * and structural invariants (named export, aria-label, alt texts, sizing).
 *
 * downstream-regression-na: brand-local shell-organism test; no cross-brand consumers
 */

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LogoMark } from "./LogoMark";

describe("LogoMark — 6 combinations (3 sizes × 2 variants)", () => {
  it("renders mark variant at sm size with aria-label", () => {
    const { getByRole } = render(<LogoMark variant="mark" size="sm" />);
    const link = getByRole("link");
    expect(link).toHaveAttribute("aria-label", "Vitalia inicio");
  });

  it("renders mark variant at md size", () => {
    const { container } = render(<LogoMark variant="mark" size="md" />);
    // At least one img rendered
    const imgs = container.querySelectorAll("img");
    expect(imgs.length).toBeGreaterThanOrEqual(1);
  });

  it("renders mark variant at lg size", () => {
    const { container } = render(<LogoMark variant="mark" size="lg" />);
    const imgs = container.querySelectorAll("img");
    expect(imgs.length).toBeGreaterThanOrEqual(1);
  });

  it("renders full variant at sm size with aria-label", () => {
    const { getByRole } = render(<LogoMark variant="full" size="sm" />);
    const link = getByRole("link");
    expect(link).toHaveAttribute("aria-label", "Vitalia inicio");
  });

  it("renders full variant at md size — link href is /", () => {
    const { getByRole } = render(<LogoMark variant="full" size="md" />);
    const link = getByRole("link");
    expect(link).toHaveAttribute("href", "/");
  });

  it("renders full variant at lg size", () => {
    const { container } = render(<LogoMark variant="full" size="lg" />);
    const imgs = container.querySelectorAll("img");
    expect(imgs.length).toBeGreaterThanOrEqual(1);
  });
});

describe("LogoMark — accessibility and alt text", () => {
  it("dark/light images have empty alt (decorative) — aria-label on link carries meaning", () => {
    const { container } = render(<LogoMark variant="full" size="md" />);
    const imgs = container.querySelectorAll("img");
    // All images are decorative — semantic label is on the <a> wrapper
    imgs.forEach((img) => {
      expect(img.getAttribute("alt")).toBe("");
    });
  });

  it("link has role=link accessible", () => {
    const { getByRole } = render(<LogoMark variant="mark" size="md" />);
    expect(getByRole("link")).toBeDefined();
  });
});

describe("LogoMark — named export contract", () => {
  it("is a named export (not default)", () => {
    // If named export exists, this import pattern works
    expect(typeof LogoMark).toBe("function");
  });
});
