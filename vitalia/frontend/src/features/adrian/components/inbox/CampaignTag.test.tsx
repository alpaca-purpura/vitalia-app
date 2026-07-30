/**
 * CampaignTag.test.tsx — Vitest unit tests.
 * F1-S10 vitalia-fase1-empty-states — T-5
 *
 * TDD RED-first per tdd-mandatory.md.
 * Tests: truncate >30 chars · tooltip on truncated name · pill renders · short name no truncate
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CampaignTag } from "./CampaignTag";

describe("CampaignTag", () => {
  it("renders pill with 📣 icon and short campaign name", () => {
    render(<CampaignTag campaignId="c1" campaignName="Limpieza-PE" />);
    expect(screen.getByRole("button")).toBeInTheDocument();
    expect(screen.getByText(/Limpieza-PE/)).toBeInTheDocument();
    expect(screen.getByText(/📣/)).toBeInTheDocument();
  });

  it("does NOT truncate names ≤30 chars", () => {
    const name = "A".repeat(30);
    render(<CampaignTag campaignId="c2" campaignName={name} />);
    // Full name visible, no ellipsis
    expect(screen.getByText(new RegExp(name))).toBeInTheDocument();
    // No title attribute (no tooltip needed)
    expect(screen.getByRole("button")).not.toHaveAttribute("title");
  });

  it("truncates names >30 chars to 30 chars + ellipsis", () => {
    const name = "Campaña Meta Facebook Google Ads Extra Long Name";
    render(<CampaignTag campaignId="c3" campaignName={name} />);
    // Should be truncated to first 30 chars + …
    const expected = name.slice(0, 30) + "…";
    expect(screen.getByText(new RegExp(expected, "i"))).toBeInTheDocument();
  });

  it("shows full name as title tooltip when name is truncated >30 chars", () => {
    const name = "Campaña Meta Facebook Google Ads Extra Long Name";
    render(<CampaignTag campaignId="c4" campaignName={name} />);
    const pill = screen.getByRole("button");
    expect(pill).toHaveAttribute("title", name);
  });

  it("has accessible aria-label with full campaign name", () => {
    const name = "Limpieza-PE";
    render(<CampaignTag campaignId="c5" campaignName={name} />);
    expect(
      screen.getByRole("button", { name: `Campaña: ${name}` }),
    ).toBeInTheDocument();
  });

  it("applies 'list' variant classes by default", () => {
    render(<CampaignTag campaignId="c6" campaignName="Test" />);
    const pill = screen.getByRole("button");
    expect(pill.className).toMatch(/text-\[10px\]/);
  });

  it("applies 'detail' variant classes when specified", () => {
    render(
      <CampaignTag campaignId="c7" campaignName="Test" variant="detail" />,
    );
    const pill = screen.getByRole("button");
    expect(pill.className).toMatch(/text-xs/);
  });
});
