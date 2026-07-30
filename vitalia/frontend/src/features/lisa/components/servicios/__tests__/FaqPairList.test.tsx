// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { useState } from "react";
import userEvent from "@testing-library/user-event";
import { FaqPairList, type FaqPair } from "../FaqPairList";

const sample: FaqPair[] = [
  { id: "q1", question: "¿Duele?", answer: "Molestias leves los primeros días." },
  { id: "q2", question: "¿Cuánto tarda?", answer: "2-3 semanas." },
];

describe("FaqPairList", () => {
  it("renders one row per Q/A pair", () => {
    render(<FaqPairList value={sample} onChange={() => {}} />);
    expect(screen.getByTestId("faq-row-q1")).toBeInTheDocument();
    expect(screen.getByTestId("faq-row-q2")).toBeInTheDocument();
  });

  it("shows an empty state with no pairs", () => {
    render(<FaqPairList value={[]} onChange={() => {}} />);
    expect(screen.getByTestId("faq-empty")).toBeInTheDocument();
  });

  it("adds a pair when 'Agregar pregunta' is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<FaqPairList value={sample} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: /agregar pregunta/i }));
    expect(onChange.mock.calls[0][0]).toHaveLength(3);
  });

  it("removes a pair by its delete button", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<FaqPairList value={sample} onChange={onChange} />);
    await user.click(screen.getByTestId("faq-del-q2"));
    expect(onChange).toHaveBeenCalledWith([sample[0]]);
  });

  it("patches the answer on edit", () => {
    const onChange = vi.fn();
    render(<FaqPairList value={sample} onChange={onChange} />);
    const firstAnswer = screen.getAllByLabelText("Respuesta")[0];
    fireEvent.change(firstAnswer, { target: { value: "Respuesta nueva" } });
    expect(onChange).toHaveBeenCalledWith([{ ...sample[0], answer: "Respuesta nueva" }, sample[1]]);
  });

  /**
   * ADR-009 regression — local-state binding.
   *
   * Simulate the autosave re-render loop: parent re-renders (e.g. status changes)
   * and passes the SAME stale `value` prop. The input MUST retain what the user
   * typed, not revert to the prop value.
   */
  it("ADR-009: typed text survives a parent re-render with the same stale value prop", () => {
    /**
     * Wrapper that simulates a parent whose state changes (e.g. setStatus)
     * but passes the SAME frozen `value` array it started with (the "stale server data").
     */
    function Wrapper() {
      const [tick, setTick] = useState(0);
      // `value` never changes — simulates server data that hasn't refreshed yet
      return (
        <>
          <button onClick={() => setTick((n) => n + 1)} data-testid="force-rerender">
            Force re-render
          </button>
          <span data-testid="tick">{tick}</span>
          <FaqPairList
            value={sample}
            onChange={() => {
              /* autosave — does NOT update value in this test */
            }}
          />
        </>
      );
    }

    render(<Wrapper />);

    const firstQuestion = screen.getAllByLabelText("Pregunta")[0];

    // User types something — the local state inside FaqPairList should capture it
    fireEvent.change(firstQuestion, { target: { value: "Pregunta editada" } });
    expect(firstQuestion).toHaveValue("Pregunta editada");

    // Now simulate the parent re-render (e.g. autosave setStatus cycle) with the SAME stale value
    act(() => {
      screen.getByTestId("force-rerender").click();
    });

    // The input MUST still show what the user typed — not the stale prop value
    expect(firstQuestion).toHaveValue("Pregunta editada");
    expect(firstQuestion).not.toHaveValue("¿Duele?"); // the stale server value
  });
});
