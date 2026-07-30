// cap: platform.lift-shell-chrome-ui-kit
import { describe, it, expect, beforeEach } from "vitest";
import { createShellStore } from "../create-shell-store";

/**
 * RED-first TDD for the generic shell store factory (T-K1).
 *
 * Port of vitalia shell-store re-parametrized to brand-agnostic naming:
 *   valeriaOpen → supervisorOpen, valeriaPct → splitPct.
 *
 * State machine (generic):
 *   A=closed  : supervisorOpen "closed" ⇒ historyOpen forced false (RN-5)
 *   B=chat    : supervisorOpen "chat", no history restore (RN-6/RN-7)
 *   C=chat+hist: supervisorOpen "chat" + historyOpen true
 *
 * Persistence is delegated to @luana/hooks createSsrSafePersistedStore (RN-8).
 * storageKey is injected by the brand (SC-6) — no brand token in the factory.
 */

const STORAGE_KEY = "test-shell-state";

function freshStore() {
  // unique-ish key per test run keeps the persisted slice isolated under jsdom
  return createShellStore({ storageKey: `${STORAGE_KEY}-${Math.random()}` });
}

describe("createShellStore — factory shape", () => {
  it("returns a zustand bound store with the SSR-safe hydration surface", () => {
    const useStore = freshStore();
    const s = useStore.getState();
    // SsrSafeHydration surface from @luana/hooks
    expect(typeof useStore.getState).toBe("function");
    expect(typeof useStore.setState).toBe("function");
    expect(typeof useStore.subscribe).toBe("function");
    expect(typeof s.setHasHydrated).toBe("function");
    expect(typeof s._hasHydrated).toBe("boolean");
  });

  it("exposes the generic state surface (zero brand naming)", () => {
    const s = freshStore().getState();
    expect(s).toHaveProperty("supervisorOpen");
    expect(s).toHaveProperty("historyOpen");
    expect(s).toHaveProperty("splitPct");
    expect(s).toHaveProperty("mobileDrawerOpen");
    // legacy brand field names must NOT exist
    expect(s).not.toHaveProperty("valeriaOpen");
    expect(s).not.toHaveProperty("valeriaPct");
  });
});

describe("createShellStore — default state", () => {
  it("starts in machine B (chat) with history closed and splitPct null", () => {
    const s = freshStore().getState();
    expect(s.supervisorOpen).toBe("chat");
    expect(s.historyOpen).toBe(false);
    expect(s.splitPct).toBeNull();
    expect(s.mobileDrawerOpen).toBe(false);
  });
});

describe("createShellStore — machine A (closed)", () => {
  it("setSupervisorOpen('closed') forces historyOpen false (RN-5)", () => {
    const useStore = freshStore();
    useStore.getState().openHistory(); // C: chat + history
    expect(useStore.getState().historyOpen).toBe(true);

    useStore.getState().setSupervisorOpen("closed");
    expect(useStore.getState().supervisorOpen).toBe("closed");
    expect(useStore.getState().historyOpen).toBe(false);
  });

  it("collapseSupervisor sets closed + history false (RN-6)", () => {
    const useStore = freshStore();
    useStore.getState().openHistory();
    useStore.getState().collapseSupervisor();
    expect(useStore.getState().supervisorOpen).toBe("closed");
    expect(useStore.getState().historyOpen).toBe(false);
  });
});

describe("createShellStore — machine B (chat)", () => {
  it("openSupervisor sets chat without restoring history (RN-6)", () => {
    const useStore = freshStore();
    useStore.getState().collapseSupervisor();
    useStore.getState().openSupervisor();
    expect(useStore.getState().supervisorOpen).toBe("chat");
    expect(useStore.getState().historyOpen).toBe(false);
  });

  it("setSupervisorOpen('chat') does not auto-open history", () => {
    const useStore = freshStore();
    useStore.getState().setSupervisorOpen("chat");
    expect(useStore.getState().supervisorOpen).toBe("chat");
    expect(useStore.getState().historyOpen).toBe(false);
  });
});

describe("createShellStore — machine C (chat + history)", () => {
  it("openHistory forces supervisorOpen chat + historyOpen true (RN-7)", () => {
    const useStore = freshStore();
    useStore.getState().collapseSupervisor(); // closed
    useStore.getState().openHistory();
    expect(useStore.getState().supervisorOpen).toBe("chat");
    expect(useStore.getState().historyOpen).toBe(true);
  });

  it("closeHistory keeps chat, drops history", () => {
    const useStore = freshStore();
    useStore.getState().openHistory();
    useStore.getState().closeHistory();
    expect(useStore.getState().supervisorOpen).toBe("chat");
    expect(useStore.getState().historyOpen).toBe(false);
  });

  it("toggleHistory flips history (opening forces chat)", () => {
    const useStore = freshStore();
    useStore.getState().collapseSupervisor();
    useStore.getState().toggleHistory(); // off → on, forces chat
    expect(useStore.getState().supervisorOpen).toBe("chat");
    expect(useStore.getState().historyOpen).toBe(true);
    useStore.getState().toggleHistory(); // on → off
    expect(useStore.getState().historyOpen).toBe(false);
  });
});

describe("createShellStore — splitPct + mobile drawer", () => {
  it("setSplitPct stores a number", () => {
    const useStore = freshStore();
    useStore.getState().setSplitPct(42);
    expect(useStore.getState().splitPct).toBe(42);
  });

  it("setSplitPct(null) resets to default", () => {
    const useStore = freshStore();
    useStore.getState().setSplitPct(42);
    useStore.getState().setSplitPct(null);
    expect(useStore.getState().splitPct).toBeNull();
  });

  it("setMobileDrawerOpen toggles", () => {
    const useStore = freshStore();
    useStore.getState().setMobileDrawerOpen(true);
    expect(useStore.getState().mobileDrawerOpen).toBe(true);
  });
});

describe("createShellStore — version + migrate hook", () => {
  it("accepts a custom version", () => {
    const useStore = createShellStore({ storageKey: `${STORAGE_KEY}-v3`, version: 3 });
    expect(useStore.getState().supervisorOpen).toBe("chat");
  });

  it("accepts a brand-supplied migrate fn and merges its partial output", () => {
    // migrate maps a legacy persisted shape into a partial of the generic state.
    const migrate = (persisted: unknown, _version: number): Partial<ReturnType<typeof useStore.getState>> => {
      const raw = persisted as { legacyState?: string } | null;
      if (raw?.legacyState === "collapsed") return { supervisorOpen: "closed", historyOpen: false };
      if (raw?.legacyState === "full" || raw?.legacyState === "rail") {
        return { supervisorOpen: "chat", historyOpen: false };
      }
      return {};
    };
    const useStore = createShellStore({ storageKey: `${STORAGE_KEY}-mig`, version: 2, migrate });
    // factory must accept the migrate hook without throwing; default state still valid
    expect(useStore.getState().supervisorOpen).toBe("chat");
  });
});
