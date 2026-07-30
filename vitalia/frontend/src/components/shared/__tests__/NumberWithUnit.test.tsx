// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { NumberWithUnit } from "../NumberWithUnit";

/** Stateful harness: a controlled input needs its value to track onChange. */
function StatefulNumber({
  initial,
  min,
  onChange,
}: {
  initial: number;
  min?: number;
  onChange: (n: number) => void;
}) {
  const [v, setV] = useState(initial);
  return (
    <NumberWithUnit
      value={v}
      min={min}
      unit="min"
      onChange={(n) => {
        setV(n);
        onChange(n);
      }}
    />
  );
}

describe("NumberWithUnit", () => {
  it("renders the numeric value and a static unit", () => {
    render(<NumberWithUnit value={45} onChange={() => {}} unit="min" />);
    const input = screen.getByRole("spinbutton") as HTMLInputElement;
    expect(input.value).toBe("45");
    expect(screen.getByText("min")).toBeInTheDocument();
  });

  it("calls onChange with the parsed numeric value on edit", () => {
    const onChange = vi.fn();
    render(<StatefulNumber initial={10} onChange={onChange} />);
    const input = screen.getByRole("spinbutton");
    // fireEvent.change sets the value atomically (no append) — happy-dom's
    // user.clear() on type=number is flaky and leaves the prior digits.
    fireEvent.change(input, { target: { value: "30" } });
    expect(onChange).toHaveBeenLastCalledWith(30);
  });

  it("does NOT emit a value below min (min validation)", () => {
    const onChange = vi.fn();
    render(<StatefulNumber initial={5} min={1} onChange={onChange} />);
    const input = screen.getByRole("spinbutton") as HTMLInputElement;
    expect(input.min).toBe("1");
    fireEvent.change(input, { target: { value: "0" } });
    // value below min must be clamped/rejected — never propagated as 0
    expect(onChange).not.toHaveBeenCalledWith(0);
  });

  it("renders a unit selector (combobox) showing the current unitValue when units[] provided", () => {
    render(
      <NumberWithUnit
        value={1}
        onChange={() => {}}
        units={["sesiones", "semanas", "meses"]}
        unitValue="sesiones"
        onUnitChange={() => {}}
      />,
    );
    // Radix Select trigger exposes role=combobox; open/click flow is exercised
    // via Playwright (Radix portal + pointer-capture is brittle in happy-dom).
    const unitTrigger = screen.getByRole("combobox");
    expect(unitTrigger).toBeInTheDocument();
    expect(unitTrigger).toHaveTextContent("sesiones");
  });
});
