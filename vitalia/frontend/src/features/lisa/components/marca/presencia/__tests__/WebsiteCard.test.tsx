// voseo-allowed: test fixture uses voseo regex patterns as negative assertions (verifies no voseo in rendered DOM)
/**
 * WebsiteCard.test.tsx — Unit tests for WebsiteCard component.
 *
 * TDD per tdd-mandatory.md.
 * Tests: renders, conn-status indicator, autosave trigger on change.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 A2 (Zod validation) + A3 (Spanish neutro)
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { WebsiteCard } from "../WebsiteCard";

// Minimal RHF + Zod requires no extra mocks — component is self-contained

function renderWebsiteCard(props?: Partial<Parameters<typeof WebsiteCard>[0]>) {
  const onScheduleAutosave = vi.fn();
  render(
    <WebsiteCard
      websiteUrl={props?.websiteUrl ?? null}
      onScheduleAutosave={props?.onScheduleAutosave ?? onScheduleAutosave}
      className={props?.className}
    />,
  );
  return { onScheduleAutosave };
}

describe("WebsiteCard", () => {
  it("renders with heading 'Sitio web'", () => {
    renderWebsiteCard();
    expect(screen.getByText("Sitio web")).toBeDefined();
  });

  it("shows conn-status 'Sin URL' when no URL provided", () => {
    renderWebsiteCard({ websiteUrl: null });
    expect(screen.getByText("Sin URL")).toBeDefined();
  });

  it("shows conn-status 'URL válida' when valid URL provided", () => {
    renderWebsiteCard({ websiteUrl: "https://example.com" });
    expect(screen.getByText("URL válida")).toBeDefined();
  });

  it("renders URL input with correct placeholder", () => {
    renderWebsiteCard();
    const input = screen.getByRole("textbox", { name: /URL del sitio web/i });
    expect(input).toBeDefined();
  });

  it("calls onScheduleAutosave on input change", () => {
    const onScheduleAutosave = vi.fn();
    renderWebsiteCard({ onScheduleAutosave });
    const input = screen.getByRole("textbox", { name: /URL del sitio web/i });
    fireEvent.change(input, { target: { value: "https://nuevaurl.com" } });
    expect(onScheduleAutosave).toHaveBeenCalledWith(
      expect.objectContaining({ websiteUrl: "https://nuevaurl.com" }),
    );
  });

  it("hint text is present — Spanish neutro (no voseo)", () => {
    renderWebsiteCard();
    expect(screen.getByText(/Incluye el protocolo/i)).toBeDefined();
    // Verify no voseo imperatives
    const el = screen.getByText(/Incluye el protocolo/i);
    expect(el.textContent).not.toMatch(/incluí|usá|ingresá/);
  });
});
