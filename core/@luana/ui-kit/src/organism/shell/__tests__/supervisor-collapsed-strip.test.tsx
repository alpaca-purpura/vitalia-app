// cap: platform.lift-shell-chrome-ui-kit
/**
 * supervisor-collapsed-strip.test.tsx — T-K3 port of ValeriaCollapsedStrip.test.tsx.
 *
 * Behaviour ported verbatim; brand tokens replaced with generic props:
 *   - supervisorName: "Supervisora Test"
 *   - supervisorThumbnail: "/agents/supervisora-test/thumbnail.png"
 *   - supervisorInitial: "S"
 *   - openLabel: "Abrir a Supervisora Test"
 *   - stripTestId: "supervisor-collapsed-strip"
 *   - statusDotTestId: "supervisor-strip-status-dot"
 *
 * gherkin_coverage (from vitalia SC-5 / SC-16):
 *   - SC-5: click reopens supervisor (chat-only, no history)
 *   - SC-16 a11y: button aria-label + focus-visible
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SupervisorCollapsedStrip } from "../SupervisorCollapsedStrip";

// ── Generic props factory ─────────────────────────────────────────────────────
function makeProps(overrides: Partial<Parameters<typeof SupervisorCollapsedStrip>[0]> = {}) {
  return {
    onOpenSupervisor: vi.fn(),
    supervisorName: "Supervisora Test",
    supervisorThumbnail: "/agents/supervisora-test/thumbnail.png",
    supervisorInitial: "S",
    supervisorSoftBg: "bg-agent-supervisora-soft",
    statusDotClass: "bg-emerald-500",
    stripTestId: "supervisor-collapsed-strip",
    statusDotTestId: "supervisor-strip-status-dot",
    openLabel: "Abrir a Supervisora Test",
    ...overrides,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("SupervisorCollapsedStrip — render (SC-5 / SC-16)", () => {
  it("renders a button with the injected aria-label", () => {
    render(<SupervisorCollapsedStrip {...makeProps()} />);
    expect(
      screen.getByRole("button", { name: "Abrir a Supervisora Test" }),
    ).toBeInTheDocument();
  });

  it("renders the supervisor thumbnail img", () => {
    const { container } = render(<SupervisorCollapsedStrip {...makeProps()} />);
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    expect(img!.getAttribute("src")).toContain("/agents/supervisora-test/thumbnail.png");
  });

  it("renders the supervisor name label", () => {
    render(<SupervisorCollapsedStrip {...makeProps()} />);
    expect(screen.getByText("Supervisora Test")).toBeInTheDocument();
  });

  it("renders a decorative status dot (aria-hidden)", () => {
    render(<SupervisorCollapsedStrip {...makeProps()} />);
    const dot = screen.getByTestId("supervisor-strip-status-dot");
    expect(dot).toBeInTheDocument();
    expect(dot.getAttribute("aria-hidden")).toBe("true");
  });

  it("has data-testid='supervisor-collapsed-strip'", () => {
    render(<SupervisorCollapsedStrip {...makeProps()} />);
    expect(screen.getByTestId("supervisor-collapsed-strip")).toBeInTheDocument();
  });

  it("button has focus-visible affordance class", () => {
    render(<SupervisorCollapsedStrip {...makeProps()} />);
    const btn = screen.getByRole("button", { name: "Abrir a Supervisora Test" });
    expect(btn.className).toContain("focus-visible:");
  });
});

describe("SupervisorCollapsedStrip — reopen behaviour (SC-5)", () => {
  it("click calls onOpenSupervisor", () => {
    const onOpen = vi.fn();
    render(<SupervisorCollapsedStrip {...makeProps({ onOpenSupervisor: onOpen })} />);
    fireEvent.click(screen.getByRole("button", { name: "Abrir a Supervisora Test" }));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });
});

describe("SupervisorCollapsedStrip — avatar fallback (onError)", () => {
  it("onError removes img and shows initial letter", () => {
    const { container } = render(<SupervisorCollapsedStrip {...makeProps()} />);
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    fireEvent.error(img!);
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("S")).toBeInTheDocument();
  });

  it("shows initial when no thumbnail provided", () => {
    const { container } = render(
      <SupervisorCollapsedStrip
        {...makeProps({ supervisorThumbnail: undefined, supervisorInitial: "T" })}
      />,
    );
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("T")).toBeInTheDocument();
  });
});
