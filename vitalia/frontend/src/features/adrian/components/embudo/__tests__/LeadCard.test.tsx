// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadCard.test.tsx — RED-first tests for LeadCard component (T-FE-2).
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { LeadCard } from "../LeadCard";
import type { LeadCardDTO } from "../../../types/embudo.types";

vi.mock("@/components/shared/phi/PiiMaskedSpan", () => ({
  PiiMaskedSpan: ({ value }: { value: string }) => (
    <span data-testid="pii-masked">{value}</span>
  ),
}));
vi.mock("@/components/shared/shell-organism/ChannelBadge", () => ({
  ChannelBadge: ({ channel }: { channel: string }) => (
    <span data-testid={`channel-badge-${channel}`}>{channel}</span>
  ),
}));
vi.mock("@/components/shared/score/ScoreDonut", () => ({
  ScoreDonut: ({ score }: { score: number }) => (
    <div data-testid="score-donut" aria-label={`Puntuación: ${score}/100`}>{score}</div>
  ),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "tenant-test" }));
vi.mock("@/hooks/useTenantLocale", () => ({ useTenantLocale: () => ({ currency: "PEN", timezone: "America/Lima" }) }));
vi.mock("@/lib/format/formatMoney", () => ({ formatMoney: (v: number, c: string) => `${c} ${v}` }));
vi.mock("@dnd-kit/core", () => ({
  useDraggable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    isDragging: false,
    transform: null,
  }),
}));

const MOCK_LEAD: LeadCardDTO = {
  id: "lead-001",
  tenantId: "tenant-test",
  name: "María García",
  stage: "interesado",
  stageEnteredAt: "2026-06-01T10:00:00Z",
  score: 48,
  temperature: "warm",
  operatedBy: "agent",
  channel: "whatsapp",
  estimatedValue: 7000,
  currency: "PEN",
  buyingSignals: ["pregunto_precio"],
  isFrozen: false,
  frozenReason: null,
  depositStatus: null,
  closureReason: null,
  reactivationCohortAt: null,
  serviceInterest: "Ortodoncia",
  assignedDoctorId: null,
  version: 1,
  isBlacklisted: false,
};

describe("LeadCard", () => {
  // U1 fix (2026-06-04): lead name is now plain text — lead is non_phi marketing prospect.
  // PiiMaskedSpan was removed from LeadCard; the vendor must identify the lead in the board.
  it("renders lead name as plain text (not PiiMaskedSpan) in the link", () => {
    render(<LeadCard lead={MOCK_LEAD} onDragStart={vi.fn()} />);
    // Name must appear in a link element as plain text
    const nameLink = screen.getByRole("link", { name: /María García/i });
    expect(nameLink).toBeInTheDocument();
    expect(nameLink).toHaveTextContent("María García");
    // data-testid pii-masked must NOT exist (it no longer wraps the name)
    expect(screen.queryByTestId("pii-masked")).not.toBeInTheDocument();
  });

  it("renders ChannelBadge with correct channel (whatsapp)", () => {
    render(<LeadCard lead={MOCK_LEAD} onDragStart={vi.fn()} />);
    expect(screen.getByTestId("channel-badge-whatsapp")).toBeInTheDocument();
  });

  it("renders ScoreDonut with score value", () => {
    render(<LeadCard lead={MOCK_LEAD} onDragStart={vi.fn()} />);
    const donut = screen.getByTestId("score-donut");
    expect(donut).toBeInTheDocument();
    expect(donut).toHaveTextContent("48");
  });

  it("renders agent operated_by indicator", () => {
    render(<LeadCard lead={MOCK_LEAD} onDragStart={vi.fn()} />);
    expect(screen.getByText(/adrián/i)).toBeInTheDocument();
  });

  it("renders buying signal chip", () => {
    render(<LeadCard lead={MOCK_LEAD} onDragStart={vi.fn()} />);
    expect(screen.getByText(/precio/i)).toBeInTheDocument();
  });

  it("is accessible: article element exists", () => {
    render(<LeadCard lead={MOCK_LEAD} onDragStart={vi.fn()} />);
    expect(screen.getByRole("article")).toBeInTheDocument();
  });
});
