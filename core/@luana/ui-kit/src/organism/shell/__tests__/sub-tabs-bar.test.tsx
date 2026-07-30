// cap: platform.lift-shell-chrome-ui-kit
/**
 * sub-tabs-bar.test.tsx — T-K3 port of SubTabsBar.test.tsx.
 *
 * Kit SubTabsBar receives agentCatalog + subTabsByAgent as props
 * (no hardcoded RIBBON_SUBTABS). Generic agent slugs "alfa"/"beta".
 * URL-derived active state via mocked usePathname/useParams.
 *
 * gherkin_coverage (from vitalia SC-1..SC-9):
 *   SC-1: renders nav role=tablist + N SubTabs
 *   SC-1: click SubTab → router.push (or onNavigate)
 *   SC-2: agent change re-renders with new sub-tabs
 *   SC-3: deep link → URL-derived active state
 *   SC-4: invalid agent (no sub-tabs) → return null total
 *   SC-5: invalid subtab → no tab active (all inactive)
 *   SC-8: roving tabindex + keyboard (Arrow/Home/End/Enter/Space)
 *   SC-9: nav aria-label dynamic per agent
 *   defensive: useParams.tenantId undefined → navigation cancelled
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SubTabsBar } from "../SubTabsBar";
import type { ShellAgentDescriptor, ShellSubTabMeta } from "../types";

// ── next/navigation mocks ─────────────────────────────────────────────────────
const mockPush = vi.fn();
const mockPathname = vi.fn(() => "/tenant-x/alfa/tab1");
const mockParams = vi.fn(() => ({ tenantId: "tenant-x" }));

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
  useRouter: () => ({ push: mockPush }),
  useParams: () => mockParams(),
}));

beforeEach(() => {
  mockPush.mockClear();
  mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
  mockParams.mockReturnValue({ tenantId: "tenant-x" });
});

// ── Generic mock catalog ──────────────────────────────────────────────────────
const MOCK_CATALOG: Record<string, ShellAgentDescriptor> = {
  alfa: {
    slug: "alfa",
    name: "Agente Alfa",
    role: "Rol alfa",
    colorToken: "agent-alfa",
    colorSoftToken: "agent-alfa-soft",
    initial: "A",
    tabLabel: "Alfa",
    defaultSubtab: "tab1",
  },
  beta: {
    slug: "beta",
    name: "Agente Beta",
    role: "Rol beta",
    colorToken: "agent-beta",
    colorSoftToken: "agent-beta-soft",
    initial: "B",
    tabLabel: "Beta",
    defaultSubtab: "tab1",
  },
};

const MOCK_SUBTABS: Record<string, readonly ShellSubTabMeta[]> = {
  alfa: [
    { id: "tab1", label: "Tab Uno", icon: "📋" },
    { id: "tab2", label: "Tab Dos", icon: "📊" },
    { id: "tab3", label: "Tab Tres", icon: "📁" },
  ],
  beta: [
    { id: "tab1", label: "Tab Uno Beta", icon: "📋" },
    { id: "tab2", label: "Tab Dos Beta", icon: "📊" },
    { id: "tab3", label: "Tab Tres Beta", icon: "📁" },
    { id: "tab4", label: "Tab Cuatro Beta", icon: "📌" },
    { id: "tab5", label: "Tab Cinco Beta", icon: "🎯" },
  ],
};

const getAgentClasses = (_slug: string) => ({
  accentBg: "bg-agent-alfa",
  softBg: "bg-agent-alfa-soft",
  accentText: "text-agent-alfa",
  accentBorder: "border-agent-alfa",
});

function defaultProps() {
  return {
    agentCatalog: MOCK_CATALOG,
    subTabsByAgent: MOCK_SUBTABS,
    getAgentClasses,
  };
}

// ── SC-1 — renders nav role=tablist + N SubTabs ───────────────────────────────

describe("SubTabsBar — renders nav + N SubTabs (SC-1)", () => {
  it("renders <nav role='tablist' data-testid='sub-tabs-bar'>", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    expect(nav).toBeInTheDocument();
    expect(nav.getAttribute("data-testid")).toBe("sub-tabs-bar");
  });

  it("renders exactly 3 SubTab children for alfa (3 sub-tabs)", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    expect(screen.getAllByRole("tab")).toHaveLength(3);
  });

  it("renders 5 SubTabs for beta", () => {
    mockPathname.mockReturnValue("/tenant-x/beta/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    expect(screen.getAllByRole("tab")).toHaveLength(5);
  });

  it("container className includes min-h-[42px] bg-card border-b overflow-x-auto", () => {
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    expect(nav.className).toContain("min-h-[42px]");
    expect(nav.className).toContain("bg-card");
    expect(nav.className).toContain("border-b");
    expect(nav.className).toContain("overflow-x-auto");
  });
});

// ── SC-1 — click SubTab → onNavigate / router.push ───────────────────────────

describe("SubTabsBar — click SubTab → navigation (SC-1)", () => {
  it("click tab2 for alfa → router.push('/tenant-x/alfa/tab2')", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const tabs = screen.getAllByRole("tab");
    // tabs[1] is tab2
    fireEvent.click(tabs[1]);
    expect(mockPush).toHaveBeenCalledWith("/tenant-x/alfa/tab2");
  });

  it("onNavigate override called instead of router.push", () => {
    const onNav = vi.fn();
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} onNavigate={onNav} />);
    fireEvent.click(screen.getAllByRole("tab")[0]);
    expect(onNav).toHaveBeenCalledWith("/tenant-x/alfa/tab1");
    expect(mockPush).not.toHaveBeenCalled();
  });
});

// ── SC-2 — agent change re-renders (SC-2) ────────────────────────────────────

describe("SubTabsBar — agent change re-renders (SC-2)", () => {
  it("re-render with beta path → 5 SubTabs + aria-label 'Sub-secciones Agente Beta'", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    const { rerender } = render(<SubTabsBar {...defaultProps()} />);

    mockPathname.mockReturnValue("/tenant-x/beta/tab1");
    rerender(<SubTabsBar {...defaultProps()} />);

    const nav = screen.getByRole("tablist");
    expect(nav.getAttribute("aria-label")).toBe("Sub-secciones Agente Beta");
    expect(screen.getAllByRole("tab")).toHaveLength(5);
  });
});

// ── SC-3 — URL-derived active state ──────────────────────────────────────────

describe("SubTabsBar — URL-derived active state (SC-3)", () => {
  it("tab2 is active when pathname segment matches tab2", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab2");
    render(<SubTabsBar {...defaultProps()} />);
    const tabs = screen.getAllByRole("tab");
    // tab2 is index 1 (id=tab2)
    expect(tabs[1].getAttribute("aria-selected")).toBe("true");
    expect(tabs[1].getAttribute("data-active")).toBe("true");
    expect(tabs[0].getAttribute("data-active")).toBe("false");
  });
});

// ── SC-4 — invalid agent → return null total ──────────────────────────────────

describe("SubTabsBar — invalid agent → return null (SC-4)", () => {
  it("unknown agent in path → component returns null → container.firstChild is null", () => {
    mockPathname.mockReturnValue("/tenant-x/gamma/anything");
    const { container } = render(<SubTabsBar {...defaultProps()} />);
    expect(container.firstChild).toBeNull();
  });

  it("no nav rendered when agent invalid", () => {
    mockPathname.mockReturnValue("/tenant-x/gamma/anything");
    render(<SubTabsBar {...defaultProps()} />);
    expect(screen.queryByTestId("sub-tabs-bar")).toBeNull();
  });

  it("root path → return null", () => {
    mockPathname.mockReturnValue("/");
    const { container } = render(<SubTabsBar {...defaultProps()} />);
    expect(container.firstChild).toBeNull();
  });

  it("null pathname → return null", () => {
    mockPathname.mockReturnValue(null as unknown as string);
    const { container } = render(<SubTabsBar {...defaultProps()} />);
    expect(container.firstChild).toBeNull();
  });
});

// ── SC-5 — invalid subtab → all inactive ─────────────────────────────────────

describe("SubTabsBar — invalid subtab → all inactive (SC-5)", () => {
  it("unknown subtab segment → 3 tabs rendered + none has aria-selected='true'", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/inexistente");
    render(<SubTabsBar {...defaultProps()} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(3);
    for (const tab of tabs) {
      expect(tab.getAttribute("aria-selected")).toBe("false");
    }
  });
});

// ── SC-8 — roving tabindex + keyboard (SC-8) ─────────────────────────────────

describe("SubTabsBar — roving tabindex + keyboard (SC-8)", () => {
  it("initial: active tab (tab1, idx 0) has tabIndex=0, others -1", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs[0].getAttribute("tabindex")).toBe("0");
    expect(tabs[1].getAttribute("tabindex")).toBe("-1");
  });

  it("Arrow Right → advances focused tab", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: "ArrowRight" });
    const tabs = screen.getAllByRole("tab");
    expect(tabs[1].getAttribute("tabindex")).toBe("0");
    expect(tabs[0].getAttribute("tabindex")).toBe("-1");
  });

  it("Arrow Left → wraps from tab1 (idx 0) to last (idx 2)", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: "ArrowLeft" });
    const tabs = screen.getAllByRole("tab");
    expect(tabs[2].getAttribute("tabindex")).toBe("0");
  });

  it("Home → focus first tab", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab3");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: "Home" });
    const tabs = screen.getAllByRole("tab");
    expect(tabs[0].getAttribute("tabindex")).toBe("0");
  });

  it("End → focus last tab", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: "End" });
    const tabs = screen.getAllByRole("tab");
    expect(tabs[2].getAttribute("tabindex")).toBe("0");
  });

  it("Enter on focused tab → router.push", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: "Enter" });
    expect(mockPush).toHaveBeenCalledWith("/tenant-x/alfa/tab1");
  });

  it("Space on focused tab → router.push", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: " " });
    expect(mockPush).toHaveBeenCalledWith("/tenant-x/alfa/tab1");
  });

  it("Arrow Right wraps from last to first", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab3");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: "ArrowRight" });
    const tabs = screen.getAllByRole("tab");
    expect(tabs[0].getAttribute("tabindex")).toBe("0");
  });

  it("Tab/Escape keys → no navigation, no focus change", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    const nav = screen.getByRole("tablist");
    fireEvent.keyDown(nav, { key: "Tab" });
    fireEvent.keyDown(nav, { key: "Escape" });
    expect(mockPush).not.toHaveBeenCalled();
    const tabs = screen.getAllByRole("tab");
    expect(tabs[0].getAttribute("tabindex")).toBe("0");
  });
});

// ── SC-9 — aria-label dynamic (SC-9) ─────────────────────────────────────────

describe("SubTabsBar — aria-label dynamic per agent (SC-9 i18n)", () => {
  it("alfa agent → aria-label='Sub-secciones Agente Alfa'", () => {
    mockPathname.mockReturnValue("/tenant-x/alfa/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    expect(screen.getByRole("tablist").getAttribute("aria-label")).toBe(
      "Sub-secciones Agente Alfa",
    );
  });

  it("beta agent → aria-label='Sub-secciones Agente Beta'", () => {
    mockPathname.mockReturnValue("/tenant-x/beta/tab1");
    render(<SubTabsBar {...defaultProps()} />);
    expect(screen.getByRole("tablist").getAttribute("aria-label")).toBe(
      "Sub-secciones Agente Beta",
    );
  });
});

// ── Defensive — useParams.tenantId undefined → navigation cancelled ───────────

describe("SubTabsBar — useParams.tenantId undefined → navigation cancelled", () => {
  it("useParams returns null → click tab → router.push NOT called", () => {
    mockParams.mockReturnValue(null as never);
    render(<SubTabsBar {...defaultProps()} />);
    const tabs = screen.queryAllByRole("tab");
    if (tabs.length > 0) {
      fireEvent.click(tabs[0]);
    }
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("useParams returns {} (no tenantId) → click tab → router.push NOT called", () => {
    mockParams.mockReturnValue({} as never);
    render(<SubTabsBar {...defaultProps()} />);
    const tabs = screen.queryAllByRole("tab");
    if (tabs.length > 0) {
      fireEvent.click(tabs[0]);
    }
    expect(mockPush).not.toHaveBeenCalled();
  });
});
