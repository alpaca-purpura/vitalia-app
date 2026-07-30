/**
 * VoiceTextareaWithWarning.test.tsx — RED tests for VoiceTextareaWithWarning.
 *
 * TDD: tests written before implementation (tdd-mandatory.md).
 * Critical: soft warning ONLY (never blocks save). Alert + override button.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A2 + 04-validators.yaml fe_test_voice_warning_inline
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { VoiceTextareaWithWarning } from "../VoiceTextareaWithWarning";

describe("VoiceTextareaWithWarning", () => {
  it("renders textarea without warning when no phrases detected", () => {
    const onChange = vi.fn();
    render(
      <VoiceTextareaWithWarning
        value="Texto limpio sin frases problemáticas"
        onChange={onChange}
        prohibitedPhrases={[]}
        label="ASÍ HABLO"
        placeholder="Escribe cómo hablas..."
      />,
    );

    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("shows Alert variant=warning when prohibited phrase is detected", () => {
    const onChange = vi.fn();
    render(
      <VoiceTextareaWithWarning
        value="Garantizamos curar tu sonrisa"
        onChange={onChange}
        prohibitedPhrases={[
          {
            id: "phrase-1",
            phrase: "garantizamos curar",
            suggestedAlternative: "Acompañamos tu tratamiento con protocolos clínicos avalados.",
            severity: "high",
            countryScope: null,
            isSeed: true,
          },
        ]}
        label="ASÍ NO HABLO"
        placeholder="Escribe qué evitas..."
      />,
    );

    // Alert is shown
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();

    // Shows suggestion
    expect(screen.getByText(/protocolos clínicos avalados/i)).toBeInTheDocument();

    // "Aplicar sugerencia" button present
    expect(screen.getByRole("button", { name: /aplicar sugerencia/i })).toBeInTheDocument();

    // "Guardar igual" override button present
    expect(screen.getByRole("button", { name: /guardar igual/i })).toBeInTheDocument();
  });

  it("does NOT disable textarea when warning is shown (soft warning — no block)", () => {
    const onChange = vi.fn();
    render(
      <VoiceTextareaWithWarning
        value="Garantizamos curar tu sonrisa"
        onChange={onChange}
        prohibitedPhrases={[
          {
            id: "phrase-1",
            phrase: "garantizamos curar",
            suggestedAlternative: "Acompañamos tu tratamiento.",
            severity: "high",
            countryScope: null,
            isSeed: true,
          },
        ]}
        label="ASÍ NO HABLO"
        placeholder="Escribe qué evitas..."
      />,
    );

    const textarea = screen.getByRole("textbox");
    expect(textarea).not.toBeDisabled();
  });

  it("calls onApplySuggestion when 'Aplicar sugerencia' is clicked", () => {
    const onChange = vi.fn();
    const onApply = vi.fn();
    render(
      <VoiceTextareaWithWarning
        value="Garantizamos curar tu sonrisa"
        onChange={onChange}
        onApplySuggestion={onApply}
        prohibitedPhrases={[
          {
            id: "phrase-1",
            phrase: "garantizamos curar",
            suggestedAlternative: "Acompañamos tu tratamiento.",
            severity: "high",
            countryScope: null,
            isSeed: true,
          },
        ]}
        label="ASÍ NO HABLO"
        placeholder="Escribe qué evitas..."
      />,
    );

    const applyBtn = screen.getByRole("button", { name: /aplicar sugerencia/i });
    fireEvent.click(applyBtn);
    expect(onApply).toHaveBeenCalledWith("phrase-1", "Acompañamos tu tratamiento.");
  });

  it("calls onOverride when 'Guardar igual' is clicked", () => {
    const onChange = vi.fn();
    const onOverride = vi.fn();
    render(
      <VoiceTextareaWithWarning
        value="Garantizamos curar tu sonrisa"
        onChange={onChange}
        onOverride={onOverride}
        prohibitedPhrases={[
          {
            id: "phrase-1",
            phrase: "garantizamos curar",
            suggestedAlternative: "Acompañamos tu tratamiento.",
            severity: "high",
            countryScope: null,
            isSeed: true,
          },
        ]}
        label="ASÍ NO HABLO"
        placeholder="Escribe qué evitas..."
      />,
    );

    const overrideBtn = screen.getByRole("button", { name: /guardar igual/i });
    fireEvent.click(overrideBtn);
    expect(onOverride).toHaveBeenCalledWith("phrase-1");
  });

  it("calls onChange when user types", () => {
    const onChange = vi.fn();
    render(
      <VoiceTextareaWithWarning
        value=""
        onChange={onChange}
        prohibitedPhrases={[]}
        label="ASÍ HABLO"
        placeholder="Escribe..."
      />,
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Acompañamos tu cuidado" } });
    expect(onChange).toHaveBeenCalledWith("Acompañamos tu cuidado");
  });
});
