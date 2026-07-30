/**
 * IdentityCard.test.tsx — RED tests for IdentityCard component.
 * TDD: tests written before implementation (T-5 vitalia-fase2-lisa-marca).
 * spec_anchor: 06-tickets.yaml T-5
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock react-hook-form + zod resolver to avoid provider dependency
vi.mock("@/features/lisa/hooks/useIdentityAutosave", () => ({
  useIdentityAutosave: () => ({
    autosaveStatus: "idle",
    savedAt: null,
  }),
}));

import { IdentityCard } from "../IdentityCard";

const defaultValues = {
  brand_name: "Clínica Dental Lima Centro",
  tagline: "Tu sonrisa, nuestra misión",
  website: "https://clinicadentalima.com",
};

describe("IdentityCard", () => {
  it("renders brand name input", () => {
    render(<IdentityCard defaultValues={defaultValues} onSave={vi.fn()} />);
    expect(screen.getByLabelText(/nombre/i)).toBeTruthy();
  });

  it("renders tagline input", () => {
    render(<IdentityCard defaultValues={defaultValues} onSave={vi.fn()} />);
    expect(screen.getByLabelText(/tagline/i)).toBeTruthy();
  });

  it("validates brand_name is required", async () => {
    const user = userEvent.setup();
    render(<IdentityCard defaultValues={{ brand_name: "Test" }} onSave={vi.fn()} />);

    const nameInput = screen.getByLabelText(/nombre/i);
    // Type then clear to trigger onChange validation
    await user.clear(nameInput);
    await user.type(nameInput, "x");
    await user.clear(nameInput);
    await user.tab();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    }, { timeout: 2000 });
  });

  it("shows URL as read-only when website provided", () => {
    render(<IdentityCard defaultValues={defaultValues} onSave={vi.fn()} />);
    const websiteEl = screen.getByText(/clinicadentalima/i);
    expect(websiteEl).toBeTruthy();
  });

  it("calls onSave when form changes (autosave)", async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();

    render(<IdentityCard defaultValues={defaultValues} onSave={onSave} />);

    const nameInput = screen.getByLabelText(/nombre/i);
    await user.type(nameInput, " Nueva");

    await waitFor(() => {
      expect(onSave).toHaveBeenCalled();
    }, { timeout: 1500 }); // autosave 600ms debounce
  });
});
