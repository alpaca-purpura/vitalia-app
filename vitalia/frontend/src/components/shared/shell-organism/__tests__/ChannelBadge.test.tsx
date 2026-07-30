// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * ChannelBadge — Vitest unit tests (TDD RED-first extension, T-FE-1)
 *
 * Extends the T-3 inbox test coverage to validate:
 *   - Back-compat: existing channels (whatsapp, instagram, email, web, telegram) unchanged
 *   - NEW channels: meta, referido, tiktok render with correct label
 *   - All channels use CSS var references (no hardcoded hex)
 *   - channel-meta registry is consumed correctly
 *   - iconOnly prop still works for all channels
 *   - Unknown slug graceful fallback (still renders)
 *   - data-testid convention: `channel-badge-{channel}`
 *
 * spec_anchor: 03-arch-fe.md § EXTEND ChannelBadge (D.6)
 * downstream-regression-na: brand-local shared component
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChannelBadge } from "../ChannelBadge";

describe("ChannelBadge — back-compat (existing channels)", () => {
  it("renders WhatsApp channel with correct label", () => {
    render(<ChannelBadge channel="whatsapp" />);
    expect(screen.getByText("WhatsApp")).toBeInTheDocument();
  });

  it("renders Instagram channel with correct label", () => {
    render(<ChannelBadge channel="instagram" />);
    expect(screen.getByText("Instagram")).toBeInTheDocument();
  });

  it("renders email channel with correct label", () => {
    render(<ChannelBadge channel="email" />);
    expect(screen.getByText("Correo")).toBeInTheDocument();
  });

  it("renders web channel with correct label", () => {
    render(<ChannelBadge channel="web" />);
    expect(screen.getByText("Web")).toBeInTheDocument();
  });

  it("renders telegram channel with correct label", () => {
    render(<ChannelBadge channel="telegram" />);
    expect(screen.getByText("Telegram")).toBeInTheDocument();
  });

  it("iconOnly prop renders sr-only label for existing channels", () => {
    const { container } = render(<ChannelBadge channel="whatsapp" iconOnly />);
    const srOnly = container.querySelector(".sr-only");
    expect(srOnly).not.toBeNull();
    expect(srOnly?.textContent).toBe("WhatsApp");
  });

  it("has data-testid for whatsapp", () => {
    render(<ChannelBadge channel="whatsapp" />);
    expect(
      screen.getByTestId("channel-badge-whatsapp"),
    ).toBeInTheDocument();
  });
});

describe("ChannelBadge — NEW channels (T-FE-1 embudo extension)", () => {
  it("renders Meta channel", () => {
    render(<ChannelBadge channel="meta" />);
    expect(screen.getByTestId("channel-badge-meta")).toBeInTheDocument();
    // Should have a visible label (not undefined/empty)
    const badge = screen.getByTestId("channel-badge-meta");
    expect(badge.textContent?.trim().length).toBeGreaterThan(0);
  });

  it("renders Referido channel", () => {
    render(<ChannelBadge channel="referido" />);
    expect(screen.getByTestId("channel-badge-referido")).toBeInTheDocument();
    const badge = screen.getByTestId("channel-badge-referido");
    expect(badge.textContent?.trim().length).toBeGreaterThan(0);
  });

  it("renders TikTok channel", () => {
    render(<ChannelBadge channel="tiktok" />);
    expect(screen.getByTestId("channel-badge-tiktok")).toBeInTheDocument();
    const badge = screen.getByTestId("channel-badge-tiktok");
    expect(badge.textContent?.trim().length).toBeGreaterThan(0);
  });

  it("Meta badge label is Spanish neutro (no voseo)", () => {
    render(<ChannelBadge channel="meta" />);
    const badge = screen.getByTestId("channel-badge-meta");
    // Label should not contain voseo imperatives
    expect(badge.textContent).not.toMatch(/ás$|és$|ís$/);
  });

  it("Referido badge has aria-label", () => {
    render(<ChannelBadge channel="referido" />);
    const badge = screen.getByTestId("channel-badge-referido");
    expect(badge.getAttribute("aria-label")).toBeTruthy();
  });

  it("TikTok iconOnly renders sr-only label", () => {
    const { container } = render(<ChannelBadge channel="tiktok" iconOnly />);
    const srOnly = container.querySelector(".sr-only");
    expect(srOnly).not.toBeNull();
  });
});

describe("ChannelBadge — color integrity (no hardcoded hex)", () => {
  it("whatsapp badge has no inline hex style", () => {
    const { container } = render(<ChannelBadge channel="whatsapp" />);
    // style attribute should not contain hex literals
    const badge = container.querySelector("[data-testid]");
    const style = badge?.getAttribute("style") ?? "";
    expect(style).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });

  it("meta badge has no inline hex style", () => {
    const { container } = render(<ChannelBadge channel="meta" />);
    const badge = container.querySelector("[data-testid]");
    const style = badge?.getAttribute("style") ?? "";
    expect(style).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });
});

describe("ChannelBadge — graceful fallback for unknown slug", () => {
  it("renders an unknown slug without crashing", () => {
    render(<ChannelBadge channel="unknown-channel-xyz" />);
    expect(
      screen.getByTestId("channel-badge-unknown-channel-xyz"),
    ).toBeInTheDocument();
  });

  it("accepts className prop", () => {
    const { container } = render(
      <ChannelBadge channel="whatsapp" className="my-test-class" />,
    );
    expect(container.firstElementChild?.className).toContain("my-test-class");
  });
});
