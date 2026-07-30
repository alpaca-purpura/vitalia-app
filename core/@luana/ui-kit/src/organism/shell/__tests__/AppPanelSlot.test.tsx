// cap: platform.lift-shell-chrome-ui-kit
/**
 * AppPanelSlot.test.tsx — root-cause regression guard for the EWL toolbar-sticky bug.
 *
 * BUG (vitalia-bugfix-horarios-toolbar-sticky · verified live 2026-06-15):
 *   AppPanelSlot's content host was `<div className="flex-1 min-h-0 overflow-y-auto">`
 *   — a CSS `block`, not a flex-column. Sheets mounted with EntityWorkspaceLayout
 *   (EWL: N3 fixed + own inner scroll) use `flex-1` on their root, expecting a
 *   flex-column parent to clamp them. A `block` parent makes that `flex-1` inert →
 *   EWL grows to its content height → the panel scrolls the whole sheet (toolbars
 *   ride along; N3 survives only via its own `sticky`).
 *
 * FIX (1 line): make the content host a flex-column WITHOUT dropping overflow-y-auto:
 *   `flex flex-col flex-1 min-h-0 overflow-y-auto`. EWL then clamps to the panel
 *   height and scrolls internally; normal (single-block) pages still scroll via
 *   overflow-y-auto. Verified live (panel scrollTop 0; grid becomes the scroller;
 *   toolbars rect.top stays put). See vitalia/.../T-1-LIVE-VERIFY.md.
 *
 * This guard pins the load-bearing classes on the content host so the clamp for
 * EWL sheets cannot be reverted silently across the 3 brands that mount EWL in
 * the shell (vitalia lisa+adrián, nicolify embudo, comunify). jsdom has no layout
 * engine — this asserts class presence, not scroll behaviour (the behaviour lives
 * in the per-brand Playwright specs + PM live-verify). It IS sufficient to catch a
 * silent revert of the `flex flex-col` clamp, which is the entire point.
 */

import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type React from "react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-test/alfa/tab1",
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-test" }),
}));

import { AppPanelSlot } from "../AppPanelSlot";
import type { AppPanelSlotProps } from "../AppPanelSlot";
import type { ShellAgentDescriptor } from "../types";

const MOCK_AGENTS: ShellAgentDescriptor[] = [
  {
    slug: "alfa",
    name: "Agente Alfa",
    role: "Rol alfa",
    colorToken: "agent-alfa",
    colorSoftToken: "agent-alfa-soft",
    initial: "A",
    thumbnail: "/agents/alfa/thumbnail.png",
    tabLabel: "Alfa",
    defaultSubtab: "tab1",
  },
];

const MOCK_GET_AGENT_CLASSES = (_slug: string) => ({
  accentBg: "bg-agent-alfa",
  softBg: "bg-agent-alfa-soft",
  accentText: "text-agent-alfa",
  accentBorder: "border-agent-alfa",
});

function makeProps(
  overrides: Partial<AppPanelSlotProps> = {},
): AppPanelSlotProps {
  return {
    agentCatalog: MOCK_AGENTS,
    ribbonOrder: ["alfa"],
    subTabsByAgent: { alfa: [{ id: "tab1", label: "Tab 1", icon: "📋" }] },
    getAgentClasses: MOCK_GET_AGENT_CLASSES,
    configTabSlug: "config",
    configTabLabel: "Configuración",
    children: <div data-testid="panel-children">Content</div>,
    ...overrides,
  };
}

/** Walk down from the panel section to the content host that wraps `children`. */
function getContentHost(container: HTMLElement): HTMLElement {
  const children = container.querySelector('[data-testid="panel-children"]');
  expect(children).not.toBeNull();
  const host = children!.parentElement;
  expect(host).not.toBeNull();
  return host as HTMLElement;
}

describe("AppPanelSlot — content host is a flex-column scroll frame (EWL clamp guard)", () => {
  it("the content host that wraps children is a flex-column (root-cause clamp)", () => {
    // WITHOUT `flex flex-col`, EWL sheets (flex-1 root) don't clamp → the panel
    // scrolls the whole sheet → toolbars ride along (the toolbar-sticky bug).
    const { container } = render(<AppPanelSlot {...makeProps()} />);
    const host = getContentHost(container);
    expect(host.className).toContain("flex");
    expect(host.className).toContain("flex-col");
  });

  it("the content host keeps overflow-y-auto (normal pages still scroll)", () => {
    // The clamp must NOT come at the cost of overflow: single-block pages still
    // need the panel to be the scroller for their tall content.
    const { container } = render(<AppPanelSlot {...makeProps()} />);
    const host = getContentHost(container);
    expect(host.className).toContain("overflow-y-auto");
  });

  it("the content host keeps flex-1 + min-h-0 (bounded within the shell)", () => {
    const { container } = render(<AppPanelSlot {...makeProps()} />);
    const host = getContentHost(container);
    expect(host.className).toContain("flex-1");
    expect(host.className).toContain("min-h-0");
  });

  it("the panel section itself stays overflow-hidden (fixed frame, not the scroller)", () => {
    const { container } = render(<AppPanelSlot {...makeProps()} />);
    const section = container.querySelector(
      '[data-testid="app-panel-slot"]',
    ) as HTMLElement | null;
    expect(section).not.toBeNull();
    expect(section!.className).toContain("overflow-hidden");
    expect(section!.className).toContain("min-h-0");
  });
});
