/**
 * RED tests — NPSTagBadge (T-infra-7 TDD)
 * Tests written BEFORE implementation (TDD RED-first).
 */

import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import React from "react";

// These imports will fail until NPSTagBadge is implemented (RED state)
import { NPSTagBadge } from "@/components/shared/nps/NPSTagBadge";

describe("NPSTagBadge", () => {
  it("renders detractor badge for score 0-6", () => {
    const { container } = render(<NPSTagBadge score={5} />);
    const badge = container.querySelector("[data-nps-category='detractor']");
    expect(badge).toBeTruthy();
  });

  it("renders passive badge for score 7-8", () => {
    const { container } = render(<NPSTagBadge score={7} />);
    const badge = container.querySelector("[data-nps-category='passive']");
    expect(badge).toBeTruthy();
  });

  it("renders promoter badge for score 9-10", () => {
    const { container } = render(<NPSTagBadge score={10} />);
    const badge = container.querySelector("[data-nps-category='promoter']");
    expect(badge).toBeTruthy();
  });

  it("renders without score (no NPS recorded)", () => {
    const { container } = render(<NPSTagBadge score={null} />);
    // Should render a neutral state
    expect(container.firstChild).toBeTruthy();
  });

  it("includes accessible label", () => {
    const { container } = render(<NPSTagBadge score={9} />);
    const badge = container.querySelector("[aria-label]");
    expect(badge).toBeTruthy();
  });
});
