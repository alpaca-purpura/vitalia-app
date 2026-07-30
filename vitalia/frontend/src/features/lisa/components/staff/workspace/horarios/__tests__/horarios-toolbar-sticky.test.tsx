// cap: clinics.lisa.doctores
// story-origin: vitalia-bugfix-horarios-toolbar-sticky
/**
 * horarios-toolbar-sticky.test.tsx — STRUCTURAL-CLASS PRESENCE GUARD ONLY.
 *
 * ⚠️ HONEST SCOPE (reframed 2026-06-15 · refutes the prior "RED→GREEN proves the
 * toolbar stays fixed" claim):
 *
 *   This file pins the load-bearing Tailwind classes on the vitalia-local leaf
 *   components (DoctorHorariosView + AvailabilityCalendar). It does NOT — and
 *   CANNOT — verify the actual scroll behaviour. jsdom has NO layout engine: it
 *   cannot measure clientHeight/scrollHeight or honour `overflow`/`flex`, so a
 *   behavioural scroll test is impossible in Vitest. A green run here means
 *   "the classes are present", NOT "the toolbar stays fixed when you scroll".
 *
 *   In fact the bug survived an earlier green run of this exact guard
 *   (verde-fantasma) — the real root cause was a CORE component mismatch
 *   (@luana/ui-kit AppPanelSlot content area was a `block`, not a flex-column,
 *   so the panel scrolled and dragged the toolbar; the vitalia leaf classes were
 *   already correct). See T-1-LIVE-VERIFY.md. This is the verification-real-≠-verde
 *   anti-pattern: a structural jsdom guard for a *layout* bug gives false
 *   confidence.
 *
 * WHERE THE BEHAVIOUR IS ACTUALLY VERIFIED:
 *   - e2e/regression/vitalia-bugfix-horarios-toolbar-sticky/toolbar-sticky.spec.ts
 *     (Playwright: scrolls the real grid in a real browser, asserts toolbar
 *     boundingBox().top does not move) — the behavioural guard.
 *   - core/@luana/ui-kit/.../AppPanelSlot.test.tsx — pins the root-cause class
 *     (content host is `flex flex-col … overflow-y-auto`) so the core clamp for
 *     EWL sheets cannot be reverted silently.
 *   - The PM live-verify on dev-app (Chrome DevTools MCP, scroll + measure rect).
 *
 * What THESE asserts buy us: a cheap, fast tripwire so the vitalia leaf classes
 * (`overflow-hidden`/`min-h-0` etc.) are not stripped by a future refactor — a
 * necessary-but-not-sufficient complement to the Playwright/live behavioural guards.
 *
 * spec_anchor: story-origin § "barra de opciones fixed igual que N2/N3"
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Mocks (mirror horarios.test.tsx — store + API + dnd + clerk) ───────────────

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useQueryClient: vi.fn(() => ({ invalidateQueries: vi.fn() })),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(async () => "test-token"),
    isLoaded: true,
    isSignedIn: true,
  })),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));
vi.mock("@/hooks/useClinicId", () => ({ useClinicId: vi.fn(() => "clinic-001") }));

vi.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "dnd-context" }, children),
  useDraggable: vi.fn(() => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    isDragging: false,
  })),
  useDroppable: vi.fn(() => ({ isOver: false, setNodeRef: vi.fn() })),
  PointerSensor: class {},
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
}));

const mockStoreState = {
  calendarWeek: "2025-09-01",
  dragDraft: null as
    | null
    | { dayOfWeek: number; startHour: number; endHour: number },
  setCalendarWeek: vi.fn(),
  setDragDraft: vi.fn(),
};

vi.mock("@/features/lisa/store/staff-ui-store", () => ({
  useStaffUiStore: vi.fn(
    (selector: (s: typeof mockStoreState) => unknown) =>
      selector(mockStoreState),
  ),
}));
vi.mock("../../../../../store/staff-ui-store", () => ({
  useStaffUiStore: vi.fn(
    (selector: (s: typeof mockStoreState) => unknown) =>
      selector(mockStoreState),
  ),
}));

// API mock: path from this __tests__/ to features/lisa/api/staff = 5 levels up
vi.mock("../../../../../api/staff", () => ({
  useAvailabilityBlocks: vi.fn(() => ({
    data: [],
    isLoading: false,
    isError: false,
  })),
  useAvailabilityOccurrences: vi.fn(() => ({
    data: [],
    isLoading: false,
    isError: false,
  })),
  useCreateBlock: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useUpdateBlock: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useDeleteBlock: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  staffKeys: {
    all: ["lisa", "staff"],
    detail: (id: string) => ["lisa", "staff", "detail", id],
    blocks: (id: string) => ["lisa", "staff", "detail", id, "blocks"],
    occurrences: (id: string, from: string, to: string) => [
      "lisa",
      "staff",
      "detail",
      id,
      "occurrences",
      from,
      to,
    ],
  },
}));

vi.mock("lucide-react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("lucide-react")>();
  return { ...actual };
});

// ── Static imports (after mocks) ──────────────────────────────────────────────

import { DoctorHorariosView } from "../DoctorHorariosView";
import { AvailabilityCalendar } from "../AvailabilityCalendar";

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("Horarios toolbar sticky — structural-class presence guard (NOT a behaviour test)", () => {
  it("DoctorHorariosView root carries the clamp classes (overflow-hidden/h-full/min-h-0)", () => {
    render(React.createElement(DoctorHorariosView, { doctorId: "doctor-123" }));
    const root = screen.getByTestId("horarios-view");
    // The leaf root must NOT let its content overflow the (core) parent slot.
    // overflow-hidden here forces the inner grid to own the scroll → toolbar fixed.
    expect(root.className).toContain("overflow-hidden");
    expect(root.className).toContain("h-full");
    expect(root.className).toContain("min-h-0");
  });

  it("page toolbar franja (Disponibilidad heading + Semana|Mes) is flex-shrink-0", () => {
    render(React.createElement(DoctorHorariosView, { doctorId: "doctor-123" }));
    // The heading lives inside the toolbar franja; walk up to the franja wrapper.
    const heading = screen.getByText("Disponibilidad");
    // heading → div(text col) → div(flex justify-between) → toolbar franja
    const franja = heading.closest('[class*="flex-shrink-0"]');
    expect(franja).not.toBeNull();
    expect(franja?.className).toContain("flex-shrink-0");
  });

  it("AvailabilityCalendar hour grid carries the scroll-owner classes (flex-1 + min-h-0 + overflow-auto)", () => {
    render(React.createElement(AvailabilityCalendar, { doctorId: "doctor-123" }));
    const grid = screen.getByRole("grid", {
      name: /calendario de disponibilidad/i,
    });
    // All three classes must coexist: without min-h-0 the flex item never shrinks
    // below content height and overflow-auto never engages (the bug).
    expect(grid.className).toContain("flex-1");
    expect(grid.className).toContain("min-h-0");
    expect(grid.className).toContain("overflow-auto");
  });

  it("calendar header franja (week nav + 24h toggle) carries flex-shrink-0", () => {
    render(React.createElement(AvailabilityCalendar, { doctorId: "doctor-123" }));
    const weekLabel = screen.getByTestId("week-label");
    const headerFranja = weekLabel.closest('[class*="flex-shrink-0"]');
    expect(headerFranja).not.toBeNull();
    expect(headerFranja?.className).toContain("flex-shrink-0");
  });

  it("day-header row carries sticky+top-0 classes", () => {
    render(React.createElement(AvailabilityCalendar, { doctorId: "doctor-123" }));
    // The first day-col lives inside the sticky day-header row.
    const dayCol = screen.getByTestId("day-col-0");
    const stickyRow = dayCol.closest('[class*="sticky"]');
    expect(stickyRow).not.toBeNull();
    expect(stickyRow?.className).toContain("sticky");
    expect(stickyRow?.className).toContain("top-0");
  });
});
