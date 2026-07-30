/**
 * ModeToggle.test.tsx — Unit tests for ModeToggle (2 modos · Chris UI #3).
 *
 * Gherkin coverage per 06-tickets.yaml:
 *   SC-01: test_2_states_aria_radiogroup — renders 2 buttons, role=radiogroup,
 *           each button has role=radio + aria-checked.
 *   SC-01: test_onchange_dispatches_set_mode — clicking segment calls onChange.
 *   SC-03: test_optimistic_rollback_on_409 — isConflict=true shows conflict state.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ModeToggle } from "../ModeToggle";
import { INBOX_COPY } from "../../../lib/copy";
import type { SegmentedModeValue } from "../../../hooks/use-mode-toggle";

describe("ModeToggle — SC-01 2-state aria-radiogroup", () => {
  it("test_2_states_aria_radiogroup: renders container with role=radiogroup", () => {
    const onChange = vi.fn();
    render(<ModeToggle value="adrian-decide" onChange={onChange} />);
    const group = screen.getByRole("radiogroup");
    expect(group).toBeDefined();
    expect(group.getAttribute("aria-label")).toBe(
      INBOX_COPY.segmentedMode.ariaLabel,
    );
  });

  it("test_2_states_aria_radiogroup: renders 2 radio buttons", () => {
    const onChange = vi.fn();
    render(<ModeToggle value="adrian-decide" onChange={onChange} />);
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(2);
  });

  it("test_2_states_aria_radiogroup: active segment has aria-checked=true, other false", () => {
    const onChange = vi.fn();
    render(<ModeToggle value="adrian-consulta" onChange={onChange} />);
    const radios = screen.getAllByRole("radio");
    const checkedStates = radios.map((r) => r.getAttribute("aria-checked"));
    // Only "adrian-consulta" (index 1) should be checked
    expect(checkedStates[0]).toBe("false");
    expect(checkedStates[1]).toBe("true");
  });

  it("test_2_states_aria_radiogroup: segment labels match INBOX_COPY", () => {
    const onChange = vi.fn();
    render(<ModeToggle value="adrian-decide" onChange={onChange} />);
    expect(screen.getByTestId("segment-adrian-decide")).toBeDefined();
    expect(screen.getByTestId("segment-adrian-consulta")).toBeDefined();
    expect(screen.getByTestId("segment-adrian-decide").textContent).toContain(
      INBOX_COPY.segmentedMode.adrianDecide,
    );
    expect(screen.getByTestId("segment-adrian-consulta").textContent).toContain(
      INBOX_COPY.segmentedMode.adrianConsulta,
    );
  });

  it("test_onchange_dispatches_set_mode: clicking inactive segment calls onChange with new value", () => {
    const onChange = vi.fn();
    render(<ModeToggle value="adrian-decide" onChange={onChange} />);
    fireEvent.click(screen.getByTestId("segment-adrian-consulta"));
    expect(onChange).toHaveBeenCalledTimes(1);
    const expected: SegmentedModeValue = "adrian-consulta";
    expect(onChange).toHaveBeenCalledWith(expected);
  });

  it("test_onchange_dispatches_set_mode: clicking already active segment does NOT call onChange", () => {
    const onChange = vi.fn();
    render(<ModeToggle value="adrian-decide" onChange={onChange} />);
    fireEvent.click(screen.getByTestId("segment-adrian-decide"));
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe("ModeToggle — SC-03 OCC conflict (409 rollback)", () => {
  it("test_optimistic_rollback_on_409: isConflict=true adds conflict indicator", () => {
    const onChange = vi.fn();
    render(
      <ModeToggle value="adrian-decide" onChange={onChange} isConflict={true} />,
    );
    const group = screen.getByTestId("segmented-control-3-modes");
    expect(group.getAttribute("data-conflict")).toBe("true");
  });

  it("test_optimistic_rollback_on_409: isConflict=false has no conflict indicator", () => {
    const onChange = vi.fn();
    render(
      <ModeToggle
        value="adrian-decide"
        onChange={onChange}
        isConflict={false}
      />,
    );
    const group = screen.getByTestId("segmented-control-3-modes");
    expect(group.getAttribute("data-conflict")).toBeNull();
  });

  it("test_optimistic_rollback_on_409: isPending=true disables all buttons", () => {
    const onChange = vi.fn();
    render(
      <ModeToggle value="adrian-decide" onChange={onChange} isPending={true} />,
    );
    const radios = screen.getAllByRole("radio");
    radios.forEach((radio) => {
      expect((radio as HTMLButtonElement).disabled).toBe(true);
    });
  });

  it("test_optimistic_rollback_on_409: isPending=true blocks onChange on click", () => {
    const onChange = vi.fn();
    render(
      <ModeToggle value="adrian-decide" onChange={onChange} isPending={true} />,
    );
    fireEvent.click(screen.getByTestId("segment-adrian-consulta"));
    expect(onChange).not.toHaveBeenCalled();
  });
});
