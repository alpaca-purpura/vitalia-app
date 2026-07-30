/**
 * FilterChips.test.tsx — Unit tests for FilterChips component.
 *
 * Key test: single-active filter per dimension (SC-01 gherkin coverage).
 * Tests chip rendering, toggling, collapsible "Más filtros" section.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FilterChips } from "../FilterChips";
import type { FilterChipsValue } from "../FilterChips";
import { INBOX_COPY } from "../../../lib/copy";

const defaultFilters: FilterChipsValue = {
  channel: null,
  status: null,
  stage: null,
  mode: null,
  period: null,
  helpNeeded: null,
  unreadMedia: null,
};

describe("FilterChips", () => {
  // SC-01 gherkin coverage: test_single_active_per_dimension
  it("test_single_active_per_dimension: clicking a channel chip deselects others in channel dimension", () => {
    const onChange = vi.fn();
    render(
      <FilterChips
        value={{ ...defaultFilters, channel: "whatsapp" }}
        onChange={onChange}
      />,
    );
    // Click instagram chip — should call onChange with instagram, replacing whatsapp
    const instagramChip = screen.getByRole("button", {
      name: new RegExp(INBOX_COPY.filters.channels.instagram, "i"),
    });
    fireEvent.click(instagramChip);
    // onChange should be called with channel: "instagram" (new selection)
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ channel: "instagram" }),
    );
  });

  it("renders primary filter chips (channel + status + help/media)", () => {
    render(<FilterChips value={defaultFilters} onChange={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: INBOX_COPY.filters.all }),
    ).toBeDefined();
    expect(
      screen.getByRole("button", {
        name: new RegExp(INBOX_COPY.filters.channels.whatsapp, "i"),
      }),
    ).toBeDefined();
    expect(
      screen.getByRole("button", {
        name: new RegExp(INBOX_COPY.filters.channels.instagram, "i"),
      }),
    ).toBeDefined();
    expect(
      screen.getByRole("button", {
        name: new RegExp(INBOX_COPY.filters.channels.email, "i"),
      }),
    ).toBeDefined();
  });

  // UI-AUDIT-2 #4 — status chips removed (too operational; conversation count small).
  it("does NOT render status chips (removed)", () => {
    render(<FilterChips value={defaultFilters} onChange={vi.fn()} />);
    expect(
      screen.queryByRole("button", {
        name: new RegExp(INBOX_COPY.filters.status.active, "i"),
      }),
    ).toBeNull();
  });

  // UI-AUDIT-2 #4 — helpNeeded/unreadMedia moved under "Más filtros".
  it("renders helpNeeded and unreadMedia under Más filtros", () => {
    render(<FilterChips value={defaultFilters} onChange={vi.fn()} />);
    // Collapsed → not visible in the primary line
    expect(
      screen.queryByRole("button", {
        name: new RegExp(INBOX_COPY.filters.helpNeeded, "i"),
      }),
    ).toBeNull();
    // Expand
    fireEvent.click(
      screen.getByRole("button", {
        name: new RegExp(INBOX_COPY.filters.moreFilters, "i"),
      }),
    );
    expect(
      screen.getByRole("button", {
        name: new RegExp(INBOX_COPY.filters.helpNeeded, "i"),
      }),
    ).toBeDefined();
    expect(
      screen.getByRole("button", {
        name: new RegExp(INBOX_COPY.filters.unreadMedia, "i"),
      }),
    ).toBeDefined();
  });

  it("clicking 'Todas' resets all filters", () => {
    const onChange = vi.fn();
    render(
      <FilterChips
        value={{
          ...defaultFilters,
          channel: "whatsapp",
          status: "active",
          helpNeeded: true,
        }}
        onChange={onChange}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: INBOX_COPY.filters.all }),
    );
    expect(onChange).toHaveBeenCalledWith({
      channel: null,
      status: null,
      stage: null,
      mode: null,
      period: null,
      helpNeeded: null,
      unreadMedia: null,
    });
  });

  it("clicking an active chip toggles it off (deselects)", () => {
    const onChange = vi.fn();
    render(
      <FilterChips
        value={{ ...defaultFilters, channel: "whatsapp" }}
        onChange={onChange}
      />,
    );
    const whatsappChip = screen.getByRole("button", {
      name: new RegExp(INBOX_COPY.filters.channels.whatsapp, "i"),
    });
    fireEvent.click(whatsappChip);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ channel: null }),
    );
  });

  it("renders 'Más filtros' button and toggles advanced filters", () => {
    render(<FilterChips value={defaultFilters} onChange={vi.fn()} />);
    const moreBtn = screen.getByRole("button", {
      name: new RegExp(INBOX_COPY.filters.moreFilters, "i"),
    });
    expect(moreBtn).toBeDefined();
    // Initially stage filter is not visible
    expect(
      screen.queryByRole("button", {
        name: new RegExp(INBOX_COPY.filters.stage.label, "i"),
      }),
    ).toBeNull();
    // Click to expand
    fireEvent.click(moreBtn);
    // "Menos filtros" should now appear
    expect(
      screen.getByRole("button", {
        name: new RegExp(INBOX_COPY.filters.lessFilters, "i"),
      }),
    ).toBeDefined();
  });

  it("applies aria-pressed to active channel chip", () => {
    render(
      <FilterChips
        value={{ ...defaultFilters, channel: "instagram" }}
        onChange={vi.fn()}
      />,
    );
    const instagramChip = screen.getByRole("button", {
      name: new RegExp(INBOX_COPY.filters.channels.instagram, "i"),
    });
    expect(instagramChip.getAttribute("aria-pressed")).toBe("true");
  });
});
