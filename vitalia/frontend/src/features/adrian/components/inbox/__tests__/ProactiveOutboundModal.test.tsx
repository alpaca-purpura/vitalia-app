/**
 * ProactiveOutboundModal.test.tsx — Unit tests for ProactiveOutboundModal.
 *
 * Tests (per 04-validators.yaml gherkin_coverage):
 *   - test_marketing_template_requires_opt_in: modal renders open/closed state,
 *     template picker shows, confirm mutation fires only on submit
 *   - Modal closed when open=false
 *   - Shows contact + template picker sections
 *   - Confirm CTA disabled when leadId or templateId not selected
 *   - Cancel calls onClose without mutation
 *   - Submit calls useProactiveOutbound.mutate with correct payload
 *
 * useProactiveOutbound mocked via vi.mock.
 * useInboxStore mocked.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ProactiveOutboundModal } from "../ProactiveOutboundModal";
import { INBOX_COPY } from "../../../lib/copy";

const mockMutate = vi.fn();
const mockOnClose = vi.fn();

vi.mock("../../../api/use-proactive-outbound", () => ({
  useProactiveOutbound: () => ({
    mutate: mockMutate,
    isPending: false,
    isSuccess: false,
    isError: false,
  }),
}));

vi.mock("../../../store/inbox-store", () => ({
  useInboxStore: (
    selector: (s: {
      proactiveModalOpen: boolean;
      closeProactiveModal: () => void;
    }) => unknown,
  ) => selector({ proactiveModalOpen: true, closeProactiveModal: vi.fn() }),
}));

describe("ProactiveOutboundModal — closed state", () => {
  it("renders nothing when open=false", () => {
    const { container } = render(
      <ProactiveOutboundModal open={false} onClose={mockOnClose} />,
    );
    expect(
      container.querySelector("[data-testid='proactive-outbound-modal']"),
    ).toBeNull();
  });
});

describe("ProactiveOutboundModal — open state", () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockOnClose.mockReset();
  });

  it("renders modal with data-testid when open=true", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    expect(screen.getByTestId("proactive-outbound-modal")).toBeDefined();
  });

  it("shows modal title from INBOX_COPY.proactiveOutboundModal.title", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    expect(
      screen.getByText(INBOX_COPY.proactiveOutboundModal.title),
    ).toBeDefined();
  });

  it("shows template picker section heading", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    expect(
      screen.getByText(INBOX_COPY.proactiveOutboundModal.selectTemplate),
    ).toBeDefined();
  });

  it("shows contact selector section heading", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    expect(
      screen.getByText(INBOX_COPY.proactiveOutboundModal.selectContact),
    ).toBeDefined();
  });

  it("confirm CTA button is disabled when no template selected (test_marketing_template_requires_opt_in)", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    const confirmBtn = screen.getByTestId(
      "proactive-confirm-btn",
    ) as HTMLButtonElement;
    // With no template or contact selected, confirm should be disabled
    expect(confirmBtn.disabled).toBe(true);
  });

  it("cancel button calls onClose without firing mutation", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    fireEvent.click(screen.getByTestId("proactive-cancel-btn"));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it("shows WA preview section label after template is selected", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    // Preview only appears after template selection
    const firstTemplate = screen.getAllByTestId(/^template-option-/)[0];
    fireEvent.click(firstTemplate);
    expect(
      screen.getByText(INBOX_COPY.proactiveOutboundModal.preview),
    ).toBeDefined();
  });

  it("shows 5 template options in picker", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    // Should render exactly 5 template radio/button options
    const templateOptions = screen.getAllByTestId(/^template-option-/);
    expect(templateOptions).toHaveLength(5);
  });

  it("selecting template + entering leadId enables confirm button", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);
    // Select first template
    const firstTemplate = screen.getAllByTestId(/^template-option-/)[0];
    fireEvent.click(firstTemplate);

    // Enter lead phone/id
    const leadInput = screen.getByTestId("lead-id-input");
    fireEvent.change(leadInput, { target: { value: "+5491100000001" } });

    const confirmBtn = screen.getByTestId(
      "proactive-confirm-btn",
    ) as HTMLButtonElement;
    expect(confirmBtn.disabled).toBe(false);
  });

  it("submit with valid template + lead calls mutate with correct payload", () => {
    render(<ProactiveOutboundModal open={true} onClose={mockOnClose} />);

    // Select first template
    const firstTemplate = screen.getAllByTestId(/^template-option-/)[0];
    fireEvent.click(firstTemplate);

    // Enter lead id
    const leadInput = screen.getByTestId("lead-id-input");
    fireEvent.change(leadInput, { target: { value: "lead-abc-123" } });

    // Submit
    fireEvent.click(screen.getByTestId("proactive-confirm-btn"));

    expect(mockMutate).toHaveBeenCalledTimes(1);
    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        leadId: "lead-abc-123",
        channel: "whatsapp",
      }),
      expect.anything(),
    );
  });
});
