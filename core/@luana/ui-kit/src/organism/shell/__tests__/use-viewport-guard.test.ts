// cap: platform.lift-shell-chrome-ui-kit
/**
 * use-viewport-guard.test.ts — T-K3 port of useViewportGuard.test.ts.
 *
 * Adapts vitalia's test contract to the kit's renamed exports:
 *   - VALERIA_MIN_PX → SUPERVISOR_MIN_PX (320)
 *   - DRAWER_BREAKPOINT (1024) — same name
 *   - INLINE_SPLIT_MIN_VIEWPORT (1280) — same name
 *   - valeriaOpen → supervisorOpen (ShellStoreState)
 *
 * STORE-INERT: hook NEVER mutates supervisorOpen/historyOpen/mobileDrawerOpen
 * at any viewport (binary machine + independent mobileDrawer D5).
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { createShellStore } from "../create-shell-store";

const useTestStore = createShellStore({
  storageKey: "test-viewport-guard-store",
  version: 1,
});

describe("useViewportGuard — import contract (T-2 kit)", () => {
  it("module exports useViewportGuard as named export", async () => {
    const mod = await import("../useViewportGuard");
    expect(typeof mod.useViewportGuard).toBe("function");
  });

  it("exports SUPERVISOR_MIN_PX = 320 (kit name; was VALERIA_MIN_PX in vitalia)", async () => {
    const mod = await import("../useViewportGuard");
    expect(mod.SUPERVISOR_MIN_PX).toBe(320);
  });

  it("exports DRAWER_BREAKPOINT = 1024", async () => {
    const mod = await import("../useViewportGuard");
    expect(mod.DRAWER_BREAKPOINT).toBe(1024);
  });

  it("exports INLINE_SPLIT_MIN_VIEWPORT = 1280", async () => {
    const mod = await import("../useViewportGuard");
    expect(mod.INLINE_SPLIT_MIN_VIEWPORT).toBe(1280);
  });

  it("does NOT export VALERIA_MIN_PX (legacy vitalia name)", async () => {
    const mod = (await import("../useViewportGuard")) as Record<string, unknown>;
    expect(mod.VALERIA_MIN_PX).toBeUndefined();
  });

  it("does NOT export FULL_STATE_MIN_VIEWPORT (legacy)", async () => {
    const mod = (await import("../useViewportGuard")) as Record<string, unknown>;
    expect(mod.FULL_STATE_MIN_VIEWPORT).toBeUndefined();
  });

  it("does NOT export MOBILE_BREAKPOINT (legacy; drawer breakpoint is 1024)", async () => {
    const mod = (await import("../useViewportGuard")) as Record<string, unknown>;
    expect(mod.MOBILE_BREAKPOINT).toBeUndefined();
  });
});

describe("useViewportGuard — store-inert contract (binary machine, D5)", () => {
  beforeEach(() => {
    useTestStore.setState({
      supervisorOpen: "chat",
      historyOpen: true,
      mobileDrawerOpen: false,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const viewports = [
    { label: "wide desktop (>=1280, inline split)", value: 1440 },
    { label: "narrow desktop ([1024,1280), clamp 320)", value: 1100 },
    { label: "drawer boundary (<1024)", value: 900 },
    { label: "mobile", value: 375 },
  ];

  for (const vp of viewports) {
    it(`does NOT mutate supervisorOpen at ${vp.label} = ${vp.value}`, async () => {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: vp.value,
      });
      const { useViewportGuard } = await import("../useViewportGuard");
      renderHook(() => useViewportGuard());
      expect(useTestStore.getState().supervisorOpen).toBe("chat");
    });
  }

  it("does NOT touch historyOpen at any viewport", async () => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1100,
    });
    const { useViewportGuard } = await import("../useViewportGuard");
    renderHook(() => useViewportGuard());
    expect(useTestStore.getState().historyOpen).toBe(true);
  });

  it("[D5] does NOT touch mobileDrawerOpen at any viewport (drawer = burger only)", async () => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 375,
    });
    const { useViewportGuard } = await import("../useViewportGuard");
    renderHook(() => useViewportGuard());
    expect(useTestStore.getState().mobileDrawerOpen).toBe(false);
  });
});

describe("useViewportGuard — clean mount / unmount", () => {
  beforeEach(() => {
    useTestStore.setState({ supervisorOpen: "chat", historyOpen: false });
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1280,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("mounts and unmounts without throwing", async () => {
    const { useViewportGuard } = await import("../useViewportGuard");
    const { unmount } = renderHook(() => useViewportGuard());
    expect(() => unmount()).not.toThrow();
  });

  it("does NOT mutate the store across mount + unmount", async () => {
    const { useViewportGuard } = await import("../useViewportGuard");
    const { unmount } = renderHook(() => useViewportGuard());
    unmount();
    expect(useTestStore.getState().supervisorOpen).toBe("chat");
    expect(useTestStore.getState().historyOpen).toBe(false);
  });
});
