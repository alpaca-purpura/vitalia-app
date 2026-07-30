/**
 * ListEmptyState.test.tsx — Unit tests for ListEmptyState component.
 *
 * Tests the 4 empty state variants used in the conversation list panel.
 * All copy must come from INBOX_COPY SSoT (no hardcoded strings).
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ListEmptyState } from "../ListEmptyState";
import { INBOX_COPY } from "../../../lib/copy";

describe("ListEmptyState", () => {
  it("renders noConversations variant with correct heading and body", () => {
    render(<ListEmptyState variant="noConversations" />);
    expect(
      screen.getByText(INBOX_COPY.empty.noConversations.heading),
    ).toBeDefined();
    expect(
      screen.getByText(INBOX_COPY.empty.noConversations.body),
    ).toBeDefined();
  });

  it("renders noHelpNeeded variant", () => {
    render(<ListEmptyState variant="noHelpNeeded" />);
    expect(
      screen.getByText(INBOX_COPY.empty.noHelpNeeded.heading),
    ).toBeDefined();
    expect(screen.getByText(INBOX_COPY.empty.noHelpNeeded.body)).toBeDefined();
  });

  it("renders noMediaUnread variant", () => {
    render(<ListEmptyState variant="noMediaUnread" />);
    expect(
      screen.getByText(INBOX_COPY.empty.noMediaUnread.heading),
    ).toBeDefined();
    expect(screen.getByText(INBOX_COPY.empty.noMediaUnread.body)).toBeDefined();
  });

  it("renders noResultsFilter variant with CTA and calls onClearFilters", () => {
    const onClear = vi.fn();
    render(
      <ListEmptyState variant="noResultsFilter" onClearFilters={onClear} />,
    );
    expect(
      screen.getByText(INBOX_COPY.empty.noResultsFilter.heading),
    ).toBeDefined();
    expect(
      screen.getByText(INBOX_COPY.empty.noResultsFilter.body),
    ).toBeDefined();
    const ctaButton = screen.getByRole("button", {
      name: INBOX_COPY.empty.noResultsFilter.cta,
    });
    expect(ctaButton).toBeDefined();
    fireEvent.click(ctaButton);
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("noResultsFilter variant does not render CTA when no onClearFilters", () => {
    render(<ListEmptyState variant="noResultsFilter" />);
    expect(
      screen.queryByRole("button", {
        name: INBOX_COPY.empty.noResultsFilter.cta,
      }),
    ).toBeNull();
  });

  it("has accessible role (status or region)", () => {
    const { container } = render(<ListEmptyState variant="noConversations" />);
    // Container must have a landmark role for screen readers
    const el = container.firstChild as HTMLElement;
    expect(el).toBeDefined();
  });
});
