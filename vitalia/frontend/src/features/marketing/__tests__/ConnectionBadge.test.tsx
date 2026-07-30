/**
 * ConnectionBadge tests — 4 sync states with color tokens and data-state attr
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

describe("ConnectionBadge", () => {
  it("test_idle_state — renders idle status with neutral token", async () => {
    const { ConnectionBadge } = await import("../components/ConnectionBadge");
    render(<ConnectionBadge status="idle" />);

    const badge = screen.getByTestId("connection-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.getAttribute("data-state")).toBe("idle");
    expect(badge.className).toContain("vt-text-neutral");
  });

  it("test_running_state — renders running status with warning token", async () => {
    const { ConnectionBadge } = await import("../components/ConnectionBadge");
    render(<ConnectionBadge status="running" />);

    const badge = screen.getByTestId("connection-badge");
    expect(badge.getAttribute("data-state")).toBe("running");
    expect(badge.className).toContain("vt-text-warning");
  });

  it("test_error_state — renders error status with danger token", async () => {
    const { ConnectionBadge } = await import("../components/ConnectionBadge");
    render(<ConnectionBadge status="error" />);

    const badge = screen.getByTestId("connection-badge");
    expect(badge.getAttribute("data-state")).toBe("error");
    expect(badge.className).toContain("vt-text-danger");
  });

  it("test_disconnected_state — renders disconnected status with danger token", async () => {
    const { ConnectionBadge } = await import("../components/ConnectionBadge");
    render(<ConnectionBadge status="disconnected" />);

    const badge = screen.getByTestId("connection-badge");
    expect(badge.getAttribute("data-state")).toBe("disconnected");
    expect(badge.className).toContain("vt-text-danger");
  });

  it("test_success_state — renders connected/idle with success token when explicit", async () => {
    const { ConnectionBadge } = await import("../components/ConnectionBadge");
    render(<ConnectionBadge status="idle" variant="success" />);

    const badge = screen.getByTestId("connection-badge");
    expect(badge.getAttribute("data-state")).toBe("idle");
    expect(badge.className).toContain("vt-text-success");
  });

  it("test_label_prop — renders custom label text", async () => {
    const { ConnectionBadge } = await import("../components/ConnectionBadge");
    render(<ConnectionBadge status="running" label="Sincronizando" />);

    expect(screen.getByText("Sincronizando")).toBeInTheDocument();
  });

  it("test_no_hardcoded_hex — badge class never contains # colors", async () => {
    const { ConnectionBadge } = await import("../components/ConnectionBadge");
    const { container } = render(<ConnectionBadge status="error" />);

    const allClasses =
      container.querySelector("[data-testid='connection-badge']")?.className ??
      "";
    expect(allClasses).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });
});
