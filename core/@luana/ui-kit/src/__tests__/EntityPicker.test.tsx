// canon: design-system-canon.md §2.4 · story-origin: core-ds-foundation
/**
 * EntityPicker.test.tsx — Validator F-9 for the canon §2.4 entity selector (@luana/ui-kit).
 *
 * Covers:
 *   - typing in the search calls searchFn DEBOUNCED (once after the window, not per keystroke)
 *   - renders the items returned by searchFn (windowed listbox)
 *   - empty state when searchFn returns []
 *   - selecting an item fires onChange + closes the popover
 *   - searchFn is ALWAYS called with a `limit` (never "fetch the whole collection")
 *
 * jsdom workaround: @tanstack/react-virtual (virtual-core) measures the scroll element
 * via `element.offsetWidth/offsetHeight`, which jsdom reports as 0 → nothing virtualizes
 * (the total-size div has height but getVirtualItems() returns []). We (1) install a
 * ResizeObserver stub (jsdom has none) and (2) define non-zero `offsetWidth/offsetHeight`
 * on HTMLElement.prototype so the scroll container measures a real viewport. Rows still
 * size deterministically via the component's `estimateSize`, so the first window renders.
 */

import { render, screen, fireEvent, act, waitFor, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from "vitest";

import * as React from "react";

import {
  EntityPicker,
  type EntityPickerItem,
  type EntitySearchArgs,
  type EntitySearchResult,
} from "../EntityPicker";

// ── jsdom layout stubs (so react-virtual measures a real window) ──────────────────

const VIEWPORT_H = 300;
const VIEWPORT_W = 320;
let origOffsetH: PropertyDescriptor | undefined;
let origOffsetW: PropertyDescriptor | undefined;
const origRO = (globalThis as { ResizeObserver?: unknown }).ResizeObserver;

beforeAll(() => {
  // jsdom has no ResizeObserver — virtual-core falls back to offset* on a no-op observer.
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  (globalThis as { ResizeObserver?: unknown }).ResizeObserver = ResizeObserverStub;

  origOffsetH = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "offsetHeight");
  origOffsetW = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "offsetWidth");
  Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
    configurable: true,
    get() {
      return VIEWPORT_H;
    },
  });
  Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
    configurable: true,
    get() {
      return VIEWPORT_W;
    },
  });
});

afterAll(() => {
  if (origOffsetH) Object.defineProperty(HTMLElement.prototype, "offsetHeight", origOffsetH);
  if (origOffsetW) Object.defineProperty(HTMLElement.prototype, "offsetWidth", origOffsetW);
  (globalThis as { ResizeObserver?: unknown }).ResizeObserver = origRO;
});

// ── Fixtures ──────────────────────────────────────────────────────────────────────

interface Doctor extends EntityPickerItem {
  specialty: string;
}

const DATASET: Doctor[] = Array.from({ length: 40 }, (_, i) => ({
  id: `doc-${i + 1}`,
  name: `Dra. Persona ${i + 1}`,
  specialty: "Odontología",
}));

/** Paginated, query-aware mock fetcher. */
function makeSearchFn(data: Doctor[] = DATASET) {
  return vi.fn(async (args: EntitySearchArgs): Promise<EntitySearchResult<Doctor>> => {
    const filtered = args.q
      ? data.filter((d) => d.name.toLowerCase().includes(args.q.toLowerCase()))
      : data;
    const start = args.cursor ? Number(args.cursor) : 0;
    const slice = filtered.slice(start, start + args.limit);
    const nextStart = start + args.limit;
    return {
      items: slice,
      nextCursor: nextStart < filtered.length ? String(nextStart) : null,
      total: filtered.length,
    };
  });
}

async function openPicker() {
  fireEvent.click(screen.getByTestId("entity-picker-trigger"));
  // first page resolves
  await screen.findByTestId("entity-picker-listbox");
}

beforeEach(() => {
  vi.clearAllMocks();
});

// ── Tests ───────────────────────────────────────────────────────────────────────

describe("EntityPicker", () => {
  it("calls searchFn DEBOUNCED — once after the debounce window, not per keystroke", async () => {
    vi.useFakeTimers();
    const searchFn = makeSearchFn();
    try {
      render(<EntityPicker searchFn={searchFn} debounceMs={200} />);

      // open → fires the initial empty-query page
      await act(async () => {
        fireEvent.click(screen.getByTestId("entity-picker-trigger"));
        await vi.advanceTimersByTimeAsync(0);
      });
      const initialCalls = searchFn.mock.calls.length;
      expect(initialCalls).toBeGreaterThanOrEqual(1);

      const input = screen.getByTestId("entity-picker-search");
      // Type fast: each keystroke updates `query` but must NOT call searchFn yet.
      await act(async () => {
        fireEvent.change(input, { target: { value: "P" } });
        fireEvent.change(input, { target: { value: "Pe" } });
        fireEvent.change(input, { target: { value: "Per" } });
        fireEvent.change(input, { target: { value: "Pers" } });
      });
      // Debounce not elapsed → no new searchFn calls beyond the initial page.
      expect(searchFn.mock.calls.length).toBe(initialCalls);

      // Advance past the debounce window → exactly ONE additional call for the typed query.
      await act(async () => {
        await vi.advanceTimersByTimeAsync(200);
      });
      expect(searchFn.mock.calls.length).toBe(initialCalls + 1);
      const lastArgs = searchFn.mock.calls[searchFn.mock.calls.length - 1]![0];
      expect(lastArgs.q).toBe("Pers");
    } finally {
      vi.useRealTimers();
    }
  });

  it("ALWAYS passes a `limit` to searchFn (never fetches the whole collection)", async () => {
    const searchFn = makeSearchFn();
    render(<EntityPicker searchFn={searchFn} limit={20} />);
    await openPicker();

    expect(searchFn).toHaveBeenCalled();
    for (const call of searchFn.mock.calls) {
      const args = call[0];
      expect(args.limit).toBe(20);
      expect(typeof args.limit).toBe("number");
    }
  });

  it("renders items returned by searchFn (windowed listbox)", async () => {
    const searchFn = makeSearchFn();
    render(<EntityPicker searchFn={searchFn} limit={20} />);
    await openPicker();

    const listbox = screen.getByTestId("entity-picker-listbox");
    expect(listbox).toHaveAttribute("role", "listbox");

    // At least the first window of options must be present (role=option).
    await waitFor(() => {
      const options = within(listbox).getAllByRole("option");
      expect(options.length).toBeGreaterThan(0);
    });
    expect(within(listbox).getByTestId("entity-picker-option-doc-1")).toBeInTheDocument();

    // Footer reflects the total from the paginated result.
    expect(screen.getByTestId("entity-picker-footer")).toHaveTextContent("de 40");
  });

  it("shows the empty state when searchFn returns []", async () => {
    const searchFn = makeSearchFn([]); // empty dataset
    render(<EntityPicker searchFn={searchFn} />);
    fireEvent.click(screen.getByTestId("entity-picker-trigger"));

    const empty = await screen.findByTestId("entity-picker-empty");
    expect(empty).toBeInTheDocument();
    expect(empty).toHaveTextContent("Sin resultados");
    // No listbox when empty.
    expect(screen.queryByTestId("entity-picker-listbox")).not.toBeInTheDocument();
  });

  it("selecting an item fires onChange and closes the popover", async () => {
    const onChange = vi.fn();
    const searchFn = makeSearchFn();
    render(<EntityPicker searchFn={searchFn} onChange={onChange} />);
    await openPicker();

    const option = await screen.findByTestId("entity-picker-option-doc-1");
    fireEvent.click(option);

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange.mock.calls[0]![0]).toMatchObject({ id: "doc-1", name: "Dra. Persona 1" });

    // Popover closed → content unmounts.
    await waitFor(() => {
      expect(screen.queryByTestId("entity-picker-listbox")).not.toBeInTheDocument();
    });
  });

  it("renders the selected entity in the trigger label", () => {
    const searchFn = makeSearchFn();
    render(
      <EntityPicker
        searchFn={searchFn}
        value={{ id: "doc-7", name: "Dra. Persona 7", specialty: "Odontología" }}
      />,
    );
    expect(screen.getByTestId("entity-picker-trigger")).toHaveTextContent("Dra. Persona 7");
  });

  // Regression (vitalia lisa-servicios G2-F3): a value whose `name` is missing
  // (e.g. a stale/partial cache entry) must NOT crash deriveInitials.
  it("does not crash when the selected value has no name (null-safe)", () => {
    const searchFn = makeSearchFn();
    expect(() =>
      render(
        // @ts-expect-error — intentionally simulating a partial cache entry (name undefined)
        <EntityPicker searchFn={searchFn} value={{ id: "doc-x" }} placeholder="Buscar servicio…" />,
      ),
    ).not.toThrow();
    // Falls back to the placeholder label + "?" initials, never an exception.
    expect(screen.getByTestId("entity-picker-trigger")).toHaveTextContent("Buscar servicio…");
  });
});

// ── createAction (pick-or-create) ─────────────────────────────────────────────────

describe("EntityPicker · createAction", () => {
  it("renders the create row when there's a query with no exact match + fires onCreate(query)", async () => {
    const onCreate = vi.fn();
    const searchFn = makeSearchFn();
    render(
      <EntityPicker
        searchFn={searchFn}
        createAction={{ label: (q) => `Crear «${q}»`, onCreate }}
      />,
    );
    await openPicker();

    // Type a query that matches NO existing entity (dataset names are "Dra. Persona N").
    const input = screen.getByTestId("entity-picker-search");
    fireEvent.change(input, { target: { value: "Nuevo Servicio" } });

    const createRow = await screen.findByTestId("entity-picker-create");
    expect(createRow).toBeInTheDocument();
    expect(createRow).toHaveAttribute("role", "option");
    expect(createRow).toHaveTextContent("Crear «Nuevo Servicio»");

    fireEvent.click(createRow);
    expect(onCreate).toHaveBeenCalledTimes(1);
    expect(onCreate).toHaveBeenCalledWith("Nuevo Servicio");
  });

  it("does NOT render the create row when createAction is omitted (additive — same as before)", async () => {
    const searchFn = makeSearchFn();
    render(<EntityPicker searchFn={searchFn} />);
    await openPicker();

    const input = screen.getByTestId("entity-picker-search");
    fireEvent.change(input, { target: { value: "Nuevo Servicio" } });

    await waitFor(() => {
      expect(screen.queryByTestId("entity-picker-create")).not.toBeInTheDocument();
    });
  });

  it("does NOT render the create row when the query is empty", async () => {
    const onCreate = vi.fn();
    const searchFn = makeSearchFn();
    render(
      <EntityPicker
        searchFn={searchFn}
        createAction={{ label: (q) => `Crear «${q}»`, onCreate }}
      />,
    );
    await openPicker();

    // No query typed → no create row even though createAction is present.
    expect(screen.queryByTestId("entity-picker-create")).not.toBeInTheDocument();
  });

  it("does NOT render the create row when the query exactly matches an existing entity", async () => {
    const onCreate = vi.fn();
    const searchFn = makeSearchFn();
    render(
      <EntityPicker
        searchFn={searchFn}
        createAction={{ label: (q) => `Crear «${q}»`, onCreate }}
      />,
    );
    await openPicker();

    // "Dra. Persona 1" is an exact (case-insensitive) match → no create row.
    const input = screen.getByTestId("entity-picker-search");
    fireEvent.change(input, { target: { value: "Dra. Persona 1" } });

    await waitFor(() => {
      expect(screen.getByTestId("entity-picker-option-doc-1")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("entity-picker-create")).not.toBeInTheDocument();
  });

  it("renders the create row even when there are zero results", async () => {
    const onCreate = vi.fn();
    const searchFn = makeSearchFn([]); // empty dataset → zero results
    render(
      <EntityPicker
        searchFn={searchFn}
        createAction={{ label: (q) => `Crear «${q}»`, onCreate }}
      />,
    );
    fireEvent.click(screen.getByTestId("entity-picker-trigger"));

    const input = await screen.findByTestId("entity-picker-search");
    fireEvent.change(input, { target: { value: "Algo nuevo" } });

    const createRow = await screen.findByTestId("entity-picker-create");
    expect(createRow).toHaveTextContent("Crear «Algo nuevo»");
    fireEvent.click(createRow);
    expect(onCreate).toHaveBeenCalledWith("Algo nuevo");
  });
});
