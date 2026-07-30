// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * ScoreDonut — Vitest unit tests (TDD RED-first, T-FE-1)
 *
 * Validates:
 *   - Renders SVG donut with score value centered
 *   - Color class changes by score tier (green ≥70 / amber 40-69 / red <40)
 *   - a11y: number is visible text, aria-label present
 *   - No hardcoded hex (uses Tailwind token classes)
 *   - Edge cases: score 0, score 100, boundary values
 *
 * spec_anchor: 03-arch-fe.md § NEW ScoreDonut (D.5)
 * downstream-regression-na: brand-local shared component
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreDonut } from "../ScoreDonut";

describe("ScoreDonut", () => {
  it("renders the score number visibly", () => {
    render(<ScoreDonut score={48} />);
    expect(screen.getByText("48")).toBeInTheDocument();
  });

  it("renders an SVG element", () => {
    const { container } = render(<ScoreDonut score={65} />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
  });

  it("has aria-label for accessibility", () => {
    const { container } = render(<ScoreDonut score={72} />);
    const wrapper = container.firstElementChild;
    expect(wrapper?.getAttribute("aria-label")).toBeTruthy();
  });

  it("applies green token class for score >= 70", () => {
    const { container } = render(<ScoreDonut score={70} />);
    // The progress arc is the 2nd circle (track = [0], progress = [1])
    const circles = container.querySelectorAll("circle");
    const progressArc = circles[1];
    expect(progressArc?.className ?? container.innerHTML).toMatch(
      /emerald|stroke-emerald/,
    );
  });

  it("applies amber token class for score 40-69", () => {
    const { container } = render(<ScoreDonut score={55} />);
    const circles = container.querySelectorAll("circle");
    const progressArc = circles[1];
    expect(progressArc?.className ?? container.innerHTML).toMatch(
      /amber|stroke-amber/,
    );
  });

  it("applies red token class for score < 40", () => {
    const { container } = render(<ScoreDonut score={30} />);
    const circles = container.querySelectorAll("circle");
    const progressArc = circles[1];
    expect(progressArc?.className ?? container.innerHTML).toMatch(
      /red|destructive|stroke-red/,
    );
  });

  it("renders score 0 (edge case)", () => {
    render(<ScoreDonut score={0} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders score 100 (edge case)", () => {
    render(<ScoreDonut score={100} />);
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("renders boundary value 40 (amber lower bound)", () => {
    render(<ScoreDonut score={40} />);
    expect(screen.getByText("40")).toBeInTheDocument();
  });

  it("renders boundary value 69 (amber upper bound)", () => {
    render(<ScoreDonut score={69} />);
    expect(screen.getByText("69")).toBeInTheDocument();
  });

  it("does not contain raw hex color literals in rendered HTML", () => {
    const { container } = render(<ScoreDonut score={55} />);
    expect(container.innerHTML).not.toMatch(/#[0-9a-fA-F]{6}\b/);
  });

  it("accepts optional className prop", () => {
    const { container } = render(
      <ScoreDonut score={50} className="custom-class" />,
    );
    expect(container.firstElementChild?.className).toContain("custom-class");
  });

  it("aria-label includes the score value", () => {
    const { container } = render(<ScoreDonut score={78} />);
    const wrapper = container.firstElementChild;
    expect(wrapper?.getAttribute("aria-label")).toContain("78");
  });
});
