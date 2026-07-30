// story-origin: core-ds-foundation · review Chris (segmented TimePicker + TimeRangePicker)
/**
 * TimePicker.test.tsx — pure-helper coverage (parse/format/clamp) + segment render.
 * The keyboard/typing UX is verified live (Chrome) per #37; this locks the value contract.
 */
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { formatTime, parseTime, TimePicker } from "../TimePicker";

describe("TimePicker helpers", () => {
  it("parses HH:mm into clamped segments", () => {
    expect(parseTime("09:30")).toEqual({ h: 9, m: 30 });
    expect(parseTime("")).toEqual({ h: null, m: null });
    expect(parseTime("9:5")).toEqual({ h: 9, m: 5 });
    expect(parseTime("99:99")).toEqual({ h: 23, m: 59 }); // clamps out-of-range
  });

  it("formats segments to HH:mm, '' when incomplete", () => {
    expect(formatTime(9, 0)).toBe("09:00");
    expect(formatTime(14, 30)).toBe("14:30");
    expect(formatTime(9, null)).toBe("");
    expect(formatTime(null, 30)).toBe("");
  });

  it("renders two segments showing the padded value", () => {
    render(<TimePicker value="09:05" onChange={() => {}} />);
    expect(screen.getByLabelText("Hora — hora")).toHaveValue("09");
    expect(screen.getByLabelText("Hora — minutos")).toHaveValue("05");
  });

  it("retains the hour while the minute is typed (partial buffer)", () => {
    // regression (review Chris): emitting "" on partial state must not wipe the hour
    const onChange = vi.fn();
    render(<TimePicker onChange={onChange} />);
    const hour = screen.getByLabelText("Hora — hora");
    fireEvent.change(hour, { target: { value: "9" } });
    fireEvent.change(screen.getByLabelText("Hora — minutos"), { target: { value: "30" } });
    expect(onChange).toHaveBeenLastCalledWith("09:30"); // emit always padded
    expect(hour).toHaveValue("9"); // raw while editing, NOT wiped
    fireEvent.blur(hour);
    expect(hour).toHaveValue("09"); // padded on blur
  });

  it("auto-advance blur does not clobber a two-digit hour (00 bug)", () => {
    // regression (review Chris): focus→minute fires hour blur synchronously with a
    // stale closure; blur must read the DOM value ("09"), not pad the old "0" to "00".
    render(<TimePicker onChange={() => {}} />);
    const hour = screen.getByLabelText("Hora — hora");
    fireEvent.change(hour, { target: { value: "0" } });
    fireEvent.change(hour, { target: { value: "09" } }); // 2 digits → auto-advance + blur
    expect(hour).toHaveValue("09");
  });
});
