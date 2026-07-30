// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { useState } from "react";
import userEvent from "@testing-library/user-event";
import { ObjecionPairList, type ObjecionPair } from "../ObjecionPairList";

const sample: ObjecionPair[] = [
  { id: "o1", tag: "Precio", response: "Tenemos planes en cuotas." },
  { id: "o2", tag: "Miedo", response: "Procedimiento suave con anestesia." },
];

describe("ObjecionPairList", () => {
  it("renders one row per objection", () => {
    render(<ObjecionPairList value={sample} onChange={() => {}} />);
    expect(screen.getByTestId("obj-row-o1")).toBeInTheDocument();
    expect(screen.getByTestId("obj-row-o2")).toBeInTheDocument();
  });

  it("shows an empty state with no objections", () => {
    render(<ObjecionPairList value={[]} onChange={() => {}} />);
    expect(screen.getByTestId("obj-empty")).toBeInTheDocument();
  });

  it("adds an objection when 'Agregar objeción' is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ObjecionPairList value={sample} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: /agregar objeci/i }));
    expect(onChange.mock.calls[0][0]).toHaveLength(3);
  });

  it("removes an objection by its delete button", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ObjecionPairList value={sample} onChange={onChange} />);
    await user.click(screen.getByTestId("obj-del-o1"));
    expect(onChange).toHaveBeenCalledWith([sample[1]]);
  });

  it("patches the response on edit", () => {
    const onChange = vi.fn();
    render(<ObjecionPairList value={sample} onChange={onChange} />);
    const firstResponse = screen.getAllByLabelText("Cómo responder")[0];
    fireEvent.change(firstResponse, { target: { value: "Respuesta distinta" } });
    expect(onChange).toHaveBeenCalledWith([
      { ...sample[0], response: "Respuesta distinta" },
      sample[1],
    ]);
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
          <ObjecionPairList
            value={sample}
            onChange={() => {
              /* autosave — does NOT update value in this test */
            }}
          />
        </>
      );
    }

    render(<Wrapper />);

    const firstTag = screen.getAllByLabelText("Objeción")[0];

    // User types something — the local state inside ObjecionPairList should capture it
    fireEvent.change(firstTag, { target: { value: "Costo elevado" } });
    expect(firstTag).toHaveValue("Costo elevado");

    // Now simulate the parent re-render (e.g. autosave setStatus cycle) with the SAME stale value
    act(() => {
      screen.getByTestId("force-rerender").click();
    });

    // The input MUST still show what the user typed — not the stale prop value
    expect(firstTag).toHaveValue("Costo elevado");
    expect(firstTag).not.toHaveValue("Precio"); // the stale server value
  });
});
