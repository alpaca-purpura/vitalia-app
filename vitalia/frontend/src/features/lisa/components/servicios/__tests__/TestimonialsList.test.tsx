// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TestimonialsList, type Testimonial } from "../TestimonialsList";

const sample: Testimonial[] = [
  { id: "a", quote: "Quedé feliz con mi sonrisa", author: "Sofía M.", source: "Google" },
  { id: "b", quote: "Trato excelente", author: "Juan P.", source: "Instagram" },
];

describe("TestimonialsList", () => {
  it("renders one row per testimonial", () => {
    render(<TestimonialsList value={sample} onChange={() => {}} />);
    expect(screen.getByTestId("testi-row-a")).toBeInTheDocument();
    expect(screen.getByTestId("testi-row-b")).toBeInTheDocument();
  });

  it("shows an empty state when there are no testimonials", () => {
    render(<TestimonialsList value={[]} onChange={() => {}} />);
    expect(screen.getByTestId("testi-empty")).toBeInTheDocument();
  });

  it("adds an empty testimonial when 'Agregar testimonio' is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<TestimonialsList value={sample} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: /agregar testimonio/i }));
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange.mock.calls[0][0]).toHaveLength(3);
  });

  it("removes a testimonial by its row delete button", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<TestimonialsList value={sample} onChange={onChange} />);
    await user.click(screen.getByTestId("testi-del-a"));
    expect(onChange).toHaveBeenCalledWith([sample[1]]);
  });

  it("patches the quote text on edit", () => {
    const onChange = vi.fn();
    render(<TestimonialsList value={sample} onChange={onChange} />);
    const firstQuote = screen.getAllByLabelText("Testimonio")[0];
    fireEvent.change(firstQuote, { target: { value: "Nuevo texto" } });
    expect(onChange).toHaveBeenCalledWith([{ ...sample[0], quote: "Nuevo texto" }, sample[1]]);
  });
});
