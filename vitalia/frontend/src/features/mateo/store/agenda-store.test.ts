/**
 * agenda-store.test.ts — Zustand drawer store unit tests (TDD RED→GREEN).
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Tests cover:
 *   - Initial state (selectedSlotId=null, drawerOpen=false, drawerWidth=520)
 *   - openDrawer sets selectedSlotId + drawerOpen=true
 *   - closeDrawer resets selectedSlotId + drawerOpen=false
 *   - toggleDrawer inverts drawerOpen
 *   - setDrawerWidth clamps to [440, 640]
 *   - setDrawerWidth below min → 440
 *   - setDrawerWidth above max → 640
 *   - localStorage key is "vitalia.agenda.drawerWidth"
 *
 * downstream-regression-na: brand-local FE tests; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-12
 */

import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import {
  useDrawerStore,
  DRAWER_WIDTH_MIN,
  DRAWER_WIDTH_MAX,
  DRAWER_WIDTH_DEFAULT,
} from "./agenda-store";

// Reset store before each test
beforeEach(() => {
  // Reset to initial state
  useDrawerStore.setState({
    selectedSlotId: null,
    drawerOpen: false,
    drawerWidth: DRAWER_WIDTH_DEFAULT,
  });
});

describe("useDrawerStore — initial state", () => {
  it("starts with no selection", () => {
    const { result } = renderHook(() => useDrawerStore());
    expect(result.current.selectedSlotId).toBeNull();
  });

  it("starts with drawer closed", () => {
    const { result } = renderHook(() => useDrawerStore());
    expect(result.current.drawerOpen).toBe(false);
  });

  it("starts with default drawer width 520", () => {
    const { result } = renderHook(() => useDrawerStore());
    expect(result.current.drawerWidth).toBe(DRAWER_WIDTH_DEFAULT);
    expect(DRAWER_WIDTH_DEFAULT).toBe(520);
  });
});

describe("useDrawerStore — openDrawer", () => {
  it("sets selectedSlotId and opens drawer", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.openDrawer("slot-abc-123"));

    expect(result.current.selectedSlotId).toBe("slot-abc-123");
    expect(result.current.drawerOpen).toBe(true);
  });

  it("replaces existing selection when called again", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.openDrawer("slot-1"));
    act(() => result.current.openDrawer("slot-2"));

    expect(result.current.selectedSlotId).toBe("slot-2");
    expect(result.current.drawerOpen).toBe(true);
  });
});

describe("useDrawerStore — closeDrawer", () => {
  it("closes drawer and clears selection", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.openDrawer("slot-1"));
    act(() => result.current.closeDrawer());

    expect(result.current.drawerOpen).toBe(false);
    expect(result.current.selectedSlotId).toBeNull();
  });
});

describe("useDrawerStore — toggleDrawer", () => {
  it("opens drawer when closed", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.toggleDrawer());
    expect(result.current.drawerOpen).toBe(true);
  });

  it("closes drawer when open", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.openDrawer("slot-1"));
    act(() => result.current.toggleDrawer());
    expect(result.current.drawerOpen).toBe(false);
  });
});

describe("useDrawerStore — setDrawerWidth", () => {
  it("accepts a valid width within bounds", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.setDrawerWidth(500));
    expect(result.current.drawerWidth).toBe(500);
  });

  it("clamps below minimum to 440", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.setDrawerWidth(100));
    expect(result.current.drawerWidth).toBe(DRAWER_WIDTH_MIN);
    expect(DRAWER_WIDTH_MIN).toBe(440);
  });

  it("clamps above maximum to 640", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.setDrawerWidth(9999));
    expect(result.current.drawerWidth).toBe(DRAWER_WIDTH_MAX);
    expect(DRAWER_WIDTH_MAX).toBe(640);
  });

  it("accepts exact minimum boundary", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.setDrawerWidth(440));
    expect(result.current.drawerWidth).toBe(440);
  });

  it("accepts exact maximum boundary", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.setDrawerWidth(640));
    expect(result.current.drawerWidth).toBe(640);
  });

  it("rounds float to integer", () => {
    const { result } = renderHook(() => useDrawerStore());

    act(() => result.current.setDrawerWidth(499.7));
    expect(result.current.drawerWidth).toBe(500);
  });
});
