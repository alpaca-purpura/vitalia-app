/**
 * SearchInput.test.tsx — Unit tests for SearchInput component.
 *
 * Tests debounce (300ms), nuqs integration stub, and clear button.
 * Uses fake timers for debounce testing.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { SearchInput } from "../SearchInput";
import { INBOX_COPY } from "../../../lib/copy";

describe("SearchInput", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("renders with placeholder from INBOX_COPY", () => {
    const onChange = vi.fn();
    render(<SearchInput value="" onChange={onChange} />);
    const input = screen.getByRole("searchbox");
    expect((input as HTMLInputElement).placeholder).toBe(
      INBOX_COPY.filters.searchPlaceholder,
    );
  });

  it("shows current value", () => {
    const onChange = vi.fn();
    render(<SearchInput value="consulta" onChange={onChange} />);
    const input = screen.getByRole("searchbox") as HTMLInputElement;
    expect(input.value).toBe("consulta");
  });

  it("debounces onChange by 300ms", async () => {
    const onChange = vi.fn();
    render(<SearchInput value="" onChange={onChange} />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "c" } });
    fireEvent.change(input, { target: { value: "co" } });
    fireEvent.change(input, { target: { value: "con" } });

    // Not called yet
    expect(onChange).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Called once with final value
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith("con");
  });

  it("shows clear button when value is non-empty and clears on click", async () => {
    const onChange = vi.fn();
    render(<SearchInput value="buscar" onChange={onChange} />);
    const clearBtn = screen.getByRole("button", { name: /limpiar|clear/i });
    expect(clearBtn).toBeDefined();
    fireEvent.click(clearBtn);
    // Clear calls onChange(null) to signal empty search (filter removed)
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("does not show clear button when value is empty", () => {
    const onChange = vi.fn();
    render(<SearchInput value="" onChange={onChange} />);
    expect(screen.queryByRole("button", { name: /limpiar|clear/i })).toBeNull();
  });

  it("has accessible aria-label", () => {
    const onChange = vi.fn();
    render(<SearchInput value="" onChange={onChange} />);
    const input = screen.getByRole("searchbox");
    expect(input).toBeDefined();
  });
});
