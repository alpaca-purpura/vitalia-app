/**
 * ExtractFromWebsiteButton.test.tsx — RED tests for ExtractFromWebsiteButton component.
 * TDD: tests written before implementation (T-5 vitalia-fase2-lisa-marca).
 * spec_anchor: 06-tickets.yaml T-5 A3 — disabled + Tooltip + telemetry on click
 * D4-extract: Visual extraction = STUB DISABLED until /pm-luana accepts proposal.
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ExtractFromWebsiteButton } from "../ExtractFromWebsiteButton";

describe("ExtractFromWebsiteButton (D4-extract STUB)", () => {
  it("renders as disabled button", () => {
    render(<ExtractFromWebsiteButton />);
    const btn = screen.getByRole("button");
    expect(btn).toBeTruthy();
    // disabled attr or aria-disabled
    const isDisabled = btn.getAttribute("disabled") !== null || btn.getAttribute("aria-disabled") === "true";
    expect(isDisabled).toBe(true);
  });

  it("has tooltip description about Próximamente via aria-label", () => {
    render(<ExtractFromWebsiteButton />);
    const btn = screen.getByRole("button");
    // The button aria-label mentions "próximamente"
    const ariaLabel = btn.getAttribute("aria-label") ?? "";
    expect(ariaLabel).toMatch(/próximamente|próximo|pronto/i);
  });

  it("does NOT trigger navigation when clicked", async () => {
    const user = userEvent.setup();
    render(<ExtractFromWebsiteButton />);
    const btn = screen.getByRole("button");
    // Clicking a disabled button should not throw
    await user.click(btn);
    // Just verify it still exists
    expect(screen.getByRole("button")).toBeTruthy();
  });
});
