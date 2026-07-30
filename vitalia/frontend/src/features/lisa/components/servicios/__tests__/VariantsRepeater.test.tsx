// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VariantsRepeater, type ServiceVariant } from "../VariantsRepeater";

const VARIANTS: ServiceVariant[] = [
  { id: "v1", name: "Limpieza simple", price: 80, note: "30 min" },
  { id: "v2", name: "Limpieza profunda", price: 150, note: "60 min" },
];

describe("VariantsRepeater", () => {
  it("renders one row per variant", () => {
    render(<VariantsRepeater value={VARIANTS} onChange={() => {}} currency="PEN" />);
    expect(screen.getAllByTestId(/^variant-row-/)).toHaveLength(2);
  });

  it("adds an empty variant when 'Agregar' is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<VariantsRepeater value={VARIANTS} onChange={onChange} currency="PEN" />);
    await user.click(screen.getByRole("button", { name: /agregar/i }));
    expect(onChange).toHaveBeenCalledTimes(1);
    const next = onChange.mock.calls[0][0] as ServiceVariant[];
    expect(next).toHaveLength(3);
  });

  it("removes a variant when its delete control is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<VariantsRepeater value={VARIANTS} onChange={onChange} currency="PEN" />);
    await user.click(screen.getByTestId("variant-del-v1"));
    const next = onChange.mock.calls[0][0] as ServiceVariant[];
    expect(next).toHaveLength(1);
    expect(next[0].id).toBe("v2");
  });

  it("renders an empty state when there are no variants", () => {
    render(<VariantsRepeater value={[]} onChange={() => {}} currency="PEN" />);
    expect(screen.queryByTestId(/^variant-row-/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /agregar/i })).toBeInTheDocument();
  });
});
