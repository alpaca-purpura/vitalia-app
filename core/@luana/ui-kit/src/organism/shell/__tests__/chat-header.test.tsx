// cap: platform.lift-shell-chrome-ui-kit
/**
 * chat-header.test.tsx — T-K3 port of ChatHeader.test.tsx.
 *
 * Kit ChatHeader receives agent descriptor + stores + getAgentClasses by prop
 * (brand-agnostic, RN-2). Generic agent "alfa" instead of "valeria".
 *
 * gherkin_coverage (from vitalia SC-1/SC-4/SC-7/SC-8):
 *   SC-1: renders data-testid=chat-header, avatar img, name, status, mode-pill
 *   SC-4: avatar onError fallback → initial letter
 *   Action buttons: nueva conv · historial toggle · colapsar supervisor
 *   Container query class on mode pill: @[24rem]:inline-flex (RN-4 SACRED)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { create } from "zustand";
import { ChatHeader } from "../ChatHeader";
import type {
  ShellAgentDescriptor,
  ShellChatStoreApi,
  ShellStoreState,
  SupervisorOpen,
} from "../types";

// ── Generic agent descriptor ──────────────────────────────────────────────────
const ALFA_AGENT: ShellAgentDescriptor = {
  slug: "alfa",
  name: "Agente Alfa",
  role: "Rol del agente alfa",
  colorToken: "agent-alfa",
  colorSoftToken: "agent-alfa-soft",
  initial: "A",
  thumbnail: "/agents/alfa/thumbnail.png",
  tabLabel: "Alfa",
  defaultSubtab: "tab1",
};

// ── Mock shell store ──────────────────────────────────────────────────────────
type MockShellState = ShellStoreState & {
  supervisorOpen: SupervisorOpen;
  historyOpen: boolean;
  mobileDrawerOpen: boolean;
};

function createMockShellStore(initial: Partial<MockShellState> = {}) {
  const collapseSupervisor = vi.fn();
  const toggleHistory = vi.fn();
  const openSupervisor = vi.fn();
  const setSupervisorOpen = vi.fn();
  const openHistory = vi.fn();
  const closeHistory = vi.fn();
  const setHistoryOpen = vi.fn();
  const setSplitPct = vi.fn();
  const setMobileDrawerOpen = vi.fn();

  const store = create<MockShellState>(() => ({
    supervisorOpen: "chat" as SupervisorOpen,
    historyOpen: false,
    splitPct: null,
    mobileDrawerOpen: false,
    _hasHydrated: true,
    setHasHydrated: vi.fn(),
    setSupervisorOpen,
    openSupervisor,
    collapseSupervisor,
    setHistoryOpen,
    openHistory,
    closeHistory,
    toggleHistory: () => {
      const state = store.getState();
      store.setState({ historyOpen: !state.historyOpen });
    },
    setSplitPct,
    setMobileDrawerOpen,
    ...initial,
  }));

  // Attach the mock functions so tests can assert on them
  return Object.assign(store, { collapseSupervisor, toggleHistory });
}

// ── Mock chat store ───────────────────────────────────────────────────────────
function createMockChatStore() {
  const newConversation = vi.fn();
  const sendMessage = vi.fn();
  const clearMessages = vi.fn();
  const setActiveAgent = vi.fn();

  const store = create<ShellChatStoreApi & { _hasHydrated: boolean; setHasHydrated: () => void }>(() => ({
    messages: [],
    conversations: [],
    activeAgent: "alfa",
    status: "idle" as const,
    newConversation,
    sendMessage,
    clearMessages,
    setActiveAgent,
    _hasHydrated: true,
    setHasHydrated: vi.fn(),
  }));

  return Object.assign(store, { newConversation });
}

const getAgentClasses = (_slug: string) => ({
  accentBg: "bg-agent-alfa",
  softBg: "bg-agent-alfa-soft",
  accentText: "text-agent-alfa",
  accentBorder: "border-agent-alfa",
});

// ── Test setup ────────────────────────────────────────────────────────────────
let useShellStore: ReturnType<typeof createMockShellStore>;
let useChatStore: ReturnType<typeof createMockChatStore>;

beforeEach(() => {
  useShellStore = createMockShellStore({ supervisorOpen: "chat", historyOpen: false });
  useChatStore = createMockChatStore();
});

function renderHeader(agent = ALFA_AGENT, overrides: { historyOpen?: boolean } = {}) {
  if (overrides.historyOpen !== undefined) {
    useShellStore.setState({ historyOpen: overrides.historyOpen });
  }
  return render(
    <ChatHeader
      agent={agent}
      status="online"
      mode="agent"
      useShellStore={useShellStore as never}
      useChatStore={useChatStore as never}
      getAgentClasses={getAgentClasses}
      statusDotClass="bg-emerald-500"
    />,
  );
}

// ── SC-1 happy · renders avatar + name + status + mode pill ──────────────────

describe("ChatHeader — renders avatar + name + status (SC-1 happy)", () => {
  it("renders data-testid='chat-header'", () => {
    renderHeader();
    expect(screen.getByTestId("chat-header")).toBeInTheDocument();
  });

  it("renders avatar img with thumbnail src", () => {
    const { container } = renderHeader();
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    expect(img!.getAttribute("src")).toContain("/agents/alfa/thumbnail.png");
  });

  it("renders agent name 'Agente Alfa'", () => {
    renderHeader();
    expect(screen.getByText("Agente Alfa")).toBeInTheDocument();
  });

  it("renders status text containing agent role", () => {
    renderHeader();
    expect(screen.getByText(/En línea · Rol del agente alfa/)).toBeInTheDocument();
  });

  it("renders mode pill with '🤖 Modo agente'", () => {
    renderHeader();
    const pill = screen.getByTestId("chat-mode-pill");
    expect(pill).toBeInTheDocument();
    expect(pill.textContent).toContain("Modo agente");
  });

  it("★ RN-4 SACRED: mode pill has @[24rem]:inline-flex (container query, NOT viewport breakpoint)", () => {
    renderHeader();
    const pill = screen.getByTestId("chat-mode-pill");
    expect(pill.className).toContain("@[24rem]:inline-flex");
    // Must NOT have viewport breakpoint classes for this (md:inline-flex is wrong)
    expect(pill.className).not.toContain("md:inline-flex");
  });

  it("status dot is aria-hidden='true' (decorative)", () => {
    renderHeader();
    const dot = screen.getByTestId("supervisor-status-dot");
    expect(dot.getAttribute("aria-hidden")).toBe("true");
  });

  it("avatar container is aria-hidden='true' (decorative)", () => {
    renderHeader();
    const avatar = screen.getByTestId("supervisor-avatar");
    expect(avatar.getAttribute("aria-hidden")).toBe("true");
  });
});

// ── Action buttons ────────────────────────────────────────────────────────────

describe("ChatHeader — action buttons", () => {
  it("renders 'Nueva conversación' button", () => {
    renderHeader();
    expect(
      screen.getByRole("button", { name: "Nueva conversación" }),
    ).toBeInTheDocument();
  });

  it("history closed → button label 'Mostrar historial'", () => {
    renderHeader();
    expect(
      screen.getByRole("button", { name: "Mostrar historial" }),
    ).toBeInTheDocument();
  });

  it("history open → button label 'Ocultar historial'", () => {
    renderHeader(ALFA_AGENT, { historyOpen: true });
    expect(
      screen.getByRole("button", { name: "Ocultar historial" }),
    ).toBeInTheDocument();
  });

  it("renders colapsar button with agent name", () => {
    renderHeader();
    expect(
      screen.getByRole("button", { name: "Colapsar a Agente Alfa" }),
    ).toBeInTheDocument();
  });

  it("'Nueva conversación' click calls newConversation on chat store", () => {
    renderHeader();
    fireEvent.click(screen.getByRole("button", { name: "Nueva conversación" }));
    expect(useChatStore.newConversation).toHaveBeenCalledTimes(1);
  });

  it("historial toggle click toggles historyOpen", () => {
    renderHeader();
    fireEvent.click(screen.getByRole("button", { name: "Mostrar historial" }));
    expect(useShellStore.getState().historyOpen).toBe(true);
  });

  it("colapsar click calls collapseSupervisor", () => {
    renderHeader();
    fireEvent.click(screen.getByRole("button", { name: "Colapsar a Agente Alfa" }));
    expect(useShellStore.collapseSupervisor).toHaveBeenCalledTimes(1);
  });
});

// ── SC-4 adversarial — avatar onError fallback ───────────────────────────────

describe("ChatHeader — avatar onError fallback (SC-4)", () => {
  it("onError → shows initial letter 'A'", () => {
    const { container } = renderHeader();
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    fireEvent.error(img!);
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("after onError, avatar div shows initial (not img)", () => {
    const { container } = renderHeader();
    const img = container.querySelector("img");
    fireEvent.error(img!);
    const avatarDiv = screen.getByTestId("supervisor-avatar");
    expect(avatarDiv.textContent).toContain("A");
  });
});
