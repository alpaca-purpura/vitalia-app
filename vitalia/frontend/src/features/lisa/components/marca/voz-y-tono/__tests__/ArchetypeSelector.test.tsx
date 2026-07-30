/**
 * ArchetypeSelector.test.tsx — RED tests for ArchetypeSelector component.
 *
 * TDD: tests written before implementation (tdd-mandatory.md).
 * Critical: 4 archetypes ONLY (test_archetype_4_salud validator from 04-validators.yaml).
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A1 + 04-validators.yaml fe_test_archetype_4_salud
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ArchetypeSelector } from "../ArchetypeSelector";

describe("ArchetypeSelector", () => {
  it("renders exactly 4 archetype cards", () => {
    const onSelect = vi.fn();
    render(
      <ArchetypeSelector
        selected="caregiver"
        onSelect={onSelect}
        isLoading={false}
      />,
    );

    // Exactly 4 cards — Caregiver, Sage, Healer, Hero
    expect(screen.getByText("Cuidador")).toBeInTheDocument();
    expect(screen.getByText("Sabio")).toBeInTheDocument();
    expect(screen.getByText("Sanador")).toBeInTheDocument();
    expect(screen.getByText("Héroe")).toBeInTheDocument();

    // Exactly 4 clickable cards (role=radio or button)
    const cards = screen.getAllByRole("radio");
    expect(cards).toHaveLength(4);
  });

  it("does NOT render Outlaw, Magician, Lover, Innocent (anti-creep OQ-B)", () => {
    const onSelect = vi.fn();
    render(
      <ArchetypeSelector
        selected="caregiver"
        onSelect={onSelect}
        isLoading={false}
      />,
    );

    expect(screen.queryByText(/outlaw/i)).toBeNull();
    expect(screen.queryByText(/magician/i)).toBeNull();
    expect(screen.queryByText(/lover/i)).toBeNull();
    expect(screen.queryByText(/innocent/i)).toBeNull();
    // Spanish names for excluded archetypes
    expect(screen.queryByText(/proscrito/i)).toBeNull();
    expect(screen.queryByText(/mago/i)).toBeNull();
    expect(screen.queryByText(/amante/i)).toBeNull();
    expect(screen.queryByText(/inocente/i)).toBeNull();
  });

  it("marks Caregiver as default selected", () => {
    const onSelect = vi.fn();
    render(
      <ArchetypeSelector
        selected="caregiver"
        onSelect={onSelect}
        isLoading={false}
      />,
    );

    const caregiverCard = screen.getByRole("radio", { name: /cuidador/i });
    expect(caregiverCard).toBeChecked();
  });

  it("shows recommended badge for Caregiver when vertical=dental", () => {
    const onSelect = vi.fn();
    render(
      <ArchetypeSelector
        selected="caregiver"
        onSelect={onSelect}
        isLoading={false}
        recommendedArchetype="caregiver"
      />,
    );

    expect(screen.getByText(/sugerido/i)).toBeInTheDocument();
  });

  it("calls onSelect when another archetype is clicked", () => {
    const onSelect = vi.fn();
    render(
      <ArchetypeSelector
        selected="caregiver"
        onSelect={onSelect}
        isLoading={false}
      />,
    );

    const sageCard = screen.getByRole("radio", { name: /sabio/i });
    fireEvent.click(sageCard);
    expect(onSelect).toHaveBeenCalledWith("sage");
  });

  it("renders skeleton when isLoading=true", () => {
    const onSelect = vi.fn();
    render(
      <ArchetypeSelector
        selected={null}
        onSelect={onSelect}
        isLoading={true}
      />,
    );

    expect(screen.getByRole("region", { name: /cargando arquetipos/i })).toBeInTheDocument();
  });
});
