// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * ToolCallCard.test.tsx — T-5 tests.
 *
 * Verifies collapsible inline tool-call card renders correctly.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ToolCallCard } from "../ToolCallCard";

describe("ToolCallCard — tool-call inline display", () => {
  it("test_renders: has data-testid=tool-call-card", () => {
    render(<ToolCallCard toolName="check_availability" />);
    expect(screen.getByTestId("tool-call-card")).toBeDefined();
  });

  it("test_tool_name: shows tool name in card", () => {
    render(<ToolCallCard toolName="check_availability" resultSummary="3 turnos disponibles" />);
    const card = screen.getByTestId("tool-call-card");
    expect(card.textContent).toContain("check_availability");
  });

  it("test_result_summary: shows result summary when provided", () => {
    render(<ToolCallCard toolName="get_patient" resultSummary="Paciente encontrado" />);
    expect(screen.getByTestId("tool-call-card").textContent).toContain("Paciente encontrado");
  });

  it("test_default_summary: shows Completado when no summary provided", () => {
    render(<ToolCallCard toolName="some_tool" />);
    expect(screen.getByTestId("tool-call-card").textContent).toContain("Completado");
  });

  it("test_error_state: shows error summary when isError=true and no resultSummary", () => {
    render(<ToolCallCard toolName="tool_x" isError={true} />);
    expect(screen.getByTestId("tool-call-card").textContent).toContain("Error al ejecutar");
  });

  it("test_error_attribute: data-is-error=true when isError=true", () => {
    render(<ToolCallCard toolName="tool_x" isError={true} />);
    expect(screen.getByTestId("tool-call-card").getAttribute("data-is-error")).toBe("true");
  });

  it("test_no_error_attribute: data-is-error not set when isError=false", () => {
    render(<ToolCallCard toolName="tool_x" isError={false} />);
    expect(screen.getByTestId("tool-call-card").getAttribute("data-is-error")).toBeNull();
  });

  it("test_expandable: renders details element when resultPayload provided", () => {
    render(<ToolCallCard toolName="tool_x" resultPayload={{ slots: 3 }} />);
    const card = screen.getByTestId("tool-call-card");
    expect(card.querySelector("details")).toBeTruthy();
  });

  it("test_not_expandable: no details element when no resultPayload", () => {
    render(<ToolCallCard toolName="tool_x" />);
    const card = screen.getByTestId("tool-call-card");
    expect(card.querySelector("details")).toBeNull();
  });

  it("test_data_tool_name: data-tool-name attribute is set", () => {
    render(<ToolCallCard toolName="check_availability" />);
    expect(screen.getByTestId("tool-call-card").getAttribute("data-tool-name")).toBe("check_availability");
  });
});
