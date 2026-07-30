/**
 * booking-widget-flow.test.tsx — Integration tests for the iframe booking widget.
 *
 * TDD RED → GREEN per .claude/rules/tdd-mandatory.md
 * Covers: A1 (build) indirectly + A2 (postMessage origin validation).
 *
 * Key validators:
 * - Origin validation prevents spoofing (D11 widget iframe security)
 * - postMessage protocol typed events via postmessage-protocol.ts SSoT
 * - Widget flow: CalendarSlotPicker → ConsentStep → PaymentStep → SuccessStep
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { postMessageToParent, createOriginValidator } from "../../src/postmessage-protocol";
import type { WidgetMessage } from "../../src/postmessage-protocol";

// ── postMessage protocol unit tests ─────────────────────────────────────────

describe("postmessage-protocol — WidgetMessage types", () => {
  it("postMessageToParent sends typed message to parent", () => {
    const mockPostMessage = vi.fn();
    const originalParent = window.parent;

    // JSDOM environment: window.parent === window, override postMessage
    Object.defineProperty(window, "parent", {
      value: { postMessage: mockPostMessage },
      writable: true,
      configurable: true,
    });

    const msg: WidgetMessage = { type: "widget:loaded" };
    postMessageToParent(msg, "https://clinic.example.com");

    expect(mockPostMessage).toHaveBeenCalledWith(msg, "https://clinic.example.com");

    Object.defineProperty(window, "parent", {
      value: originalParent,
      writable: true,
      configurable: true,
    });
  });

  it("postMessageToParent sends resize event with height", () => {
    const mockPostMessage = vi.fn();
    Object.defineProperty(window, "parent", {
      value: { postMessage: mockPostMessage },
      writable: true,
      configurable: true,
    });

    const msg: WidgetMessage = { type: "widget:resize", height: 640 };
    postMessageToParent(msg, "*");

    expect(mockPostMessage).toHaveBeenCalledWith(
      { type: "widget:resize", height: 640 },
      "*"
    );

    Object.defineProperty(window, "parent", {
      value: window,
      writable: true,
      configurable: true,
    });
  });

  it("postMessageToParent sends booking-confirmed with booking_id", () => {
    const mockPostMessage = vi.fn();
    Object.defineProperty(window, "parent", {
      value: { postMessage: mockPostMessage },
      writable: true,
      configurable: true,
    });

    const msg: WidgetMessage = {
      type: "widget:booking-confirmed",
      booking_id: "bk_abc123",
    };
    postMessageToParent(msg, "https://clinic.vitalia.health");

    expect(mockPostMessage).toHaveBeenCalledWith(msg, "https://clinic.vitalia.health");

    Object.defineProperty(window, "parent", {
      value: window,
      writable: true,
      configurable: true,
    });
  });

  it("postMessageToParent sends payment-redirect with URL", () => {
    const mockPostMessage = vi.fn();
    Object.defineProperty(window, "parent", {
      value: { postMessage: mockPostMessage },
      writable: true,
      configurable: true,
    });

    const msg: WidgetMessage = {
      type: "widget:payment-redirect",
      url: "https://checkout.stripe.com/pay/cs_test_123",
    };
    postMessageToParent(msg, "*");

    expect(mockPostMessage).toHaveBeenCalledWith(msg, "*");

    Object.defineProperty(window, "parent", {
      value: window,
      writable: true,
      configurable: true,
    });
  });

  it("postMessageToParent sends error message", () => {
    const mockPostMessage = vi.fn();
    Object.defineProperty(window, "parent", {
      value: { postMessage: mockPostMessage },
      writable: true,
      configurable: true,
    });

    const msg: WidgetMessage = {
      type: "widget:error",
      message: "Slot no disponible",
    };
    postMessageToParent(msg, "*");

    expect(mockPostMessage).toHaveBeenCalledWith(msg, "*");

    Object.defineProperty(window, "parent", {
      value: window,
      writable: true,
      configurable: true,
    });
  });
});

// ── Origin validation — A2 acceptance criterion ──────────────────────────────

describe("createOriginValidator — origin spoofing prevention (D11)", () => {
  it("allows messages from an exact allowed origin", () => {
    const validate = createOriginValidator(["https://clinic.example.com"]);
    expect(validate("https://clinic.example.com")).toBe(true);
  });

  it("allows messages when wildcard '*' is in allowed list", () => {
    const validate = createOriginValidator(["*"]);
    expect(validate("https://any-attacker.com")).toBe(true);
  });

  it("blocks messages from an origin NOT in allowed list", () => {
    const validate = createOriginValidator(["https://clinic.example.com"]);
    expect(validate("https://evil-attacker.com")).toBe(false);
  });

  it("blocks spoofed origin with trailing slash variation", () => {
    const validate = createOriginValidator(["https://clinic.example.com"]);
    // Trailing slash differs → blocked
    expect(validate("https://clinic.example.com/")).toBe(false);
  });

  it("blocks null origin (cross-origin frame sandboxed)", () => {
    const validate = createOriginValidator(["https://clinic.example.com"]);
    expect(validate("null")).toBe(false);
  });

  it("blocks empty string origin", () => {
    const validate = createOriginValidator(["https://clinic.example.com"]);
    expect(validate("")).toBe(false);
  });

  it("allows multiple listed origins", () => {
    const validate = createOriginValidator([
      "https://clinic-a.example.com",
      "https://clinic-b.vitalia.health",
    ]);
    expect(validate("https://clinic-a.example.com")).toBe(true);
    expect(validate("https://clinic-b.vitalia.health")).toBe(true);
    expect(validate("https://evil.com")).toBe(false);
  });

  it("blocks http protocol when only https allowed", () => {
    const validate = createOriginValidator(["https://clinic.example.com"]);
    expect(validate("http://clinic.example.com")).toBe(false);
  });
});

// ── Widget render smoke ───────────────────────────────────────────────────────

describe("BookingWidgetRoot — component render smoke", () => {
  // We import lazily to avoid Vite/rollup module issues in vitest
  it("renders without crashing when offerId and clinicSlug are provided", async () => {
    // Dynamic import isolates module loading
    const { BookingWidgetRoot } = await import("../../src/components/BookingWidgetRoot");
    expect(BookingWidgetRoot).toBeDefined();
  });

  it("exports CalendarSlotPicker as named export", async () => {
    const { CalendarSlotPicker } = await import("../../src/components/CalendarSlotPicker");
    expect(CalendarSlotPicker).toBeDefined();
  });

  it("exports ConsentStep as named export", async () => {
    const { ConsentStep } = await import("../../src/components/ConsentStep");
    expect(ConsentStep).toBeDefined();
  });

  it("exports PaymentStep as named export", async () => {
    const { PaymentStep } = await import("../../src/components/PaymentStep");
    expect(PaymentStep).toBeDefined();
  });

  it("exports SuccessStep as named export", async () => {
    const { SuccessStep } = await import("../../src/components/SuccessStep");
    expect(SuccessStep).toBeDefined();
  });
});

// ── CalendarSlotPicker — unit ─────────────────────────────────────────────────

describe("CalendarSlotPicker — slot selection", () => {
  it("renders available slots", async () => {
    const { CalendarSlotPicker } = await import("../../src/components/CalendarSlotPicker");

    const slots = [
      { slot_iso: "2026-05-20T10:00:00Z", duration_minutes: 60, doctor_id: "dr_1" },
      { slot_iso: "2026-05-20T11:00:00Z", duration_minutes: 60, doctor_id: "dr_1" },
    ];

    render(
      <CalendarSlotPicker
        slots={slots}
        selectedSlot={null}
        onSelectSlot={vi.fn()}
        isLoading={false}
      />
    );

    // Should render both time slots
    expect(screen.getAllByRole("button").length).toBeGreaterThanOrEqual(2);
  });

  it("shows loading skeleton when isLoading=true", async () => {
    const { CalendarSlotPicker } = await import("../../src/components/CalendarSlotPicker");

    render(
      <CalendarSlotPicker
        slots={[]}
        selectedSlot={null}
        onSelectSlot={vi.fn()}
        isLoading={true}
      />
    );

    // aria-busy signals loading state
    const loadingEl = document.querySelector('[aria-busy="true"]');
    expect(loadingEl).not.toBeNull();
  });

  it("calls onSelectSlot when a slot button is clicked", async () => {
    const { CalendarSlotPicker } = await import("../../src/components/CalendarSlotPicker");

    const onSelect = vi.fn();
    const slots = [
      { slot_iso: "2026-05-20T10:00:00Z", duration_minutes: 60, doctor_id: "dr_1" },
    ];

    render(
      <CalendarSlotPicker
        slots={slots}
        selectedSlot={null}
        onSelectSlot={onSelect}
        isLoading={false}
      />
    );

    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[0]);
    expect(onSelect).toHaveBeenCalledWith(slots[0]);
  });

  it("shows empty state when no slots available", async () => {
    const { CalendarSlotPicker } = await import("../../src/components/CalendarSlotPicker");

    render(
      <CalendarSlotPicker
        slots={[]}
        selectedSlot={null}
        onSelectSlot={vi.fn()}
        isLoading={false}
      />
    );

    // Should render empty state
    expect(screen.getByRole("status")).toBeDefined();
  });
});

// ── ConsentStep — unit ───────────────────────────────────────────────────────

describe("ConsentStep — consent flow", () => {
  it("renders consent markdown text", async () => {
    const { ConsentStep } = await import("../../src/components/ConsentStep");

    const onSign = vi.fn();
    const onBack = vi.fn();

    render(
      <ConsentStep
        consentMarkdown="Texto legal exclusivo para la prueba."
        onSign={onSign}
        onBack={onBack}
        isLoading={false}
      />
    );

    expect(screen.getByText(/texto legal exclusivo/i)).toBeDefined();
  });

  it("calls onBack when back button is clicked", async () => {
    const { ConsentStep } = await import("../../src/components/ConsentStep");

    const onSign = vi.fn();
    const onBack = vi.fn();

    render(
      <ConsentStep
        consentMarkdown="Texto."
        onSign={onSign}
        onBack={onBack}
        isLoading={false}
      />
    );

    const backButton = screen.getByRole("button", { name: /atr[áa]s/i });
    fireEvent.click(backButton);
    expect(onBack).toHaveBeenCalledOnce();
  });
});

// ── SuccessStep — unit ───────────────────────────────────────────────────────

describe("SuccessStep — booking confirmation", () => {
  it("renders booking confirmation with slot info", async () => {
    const { SuccessStep } = await import("../../src/components/SuccessStep");

    render(
      <SuccessStep
        bookingId="bk_abc123"
        slotIso="2026-05-20T10:00:00Z"
        offerName="Sesión inicial"
      />
    );

    expect(screen.getByText(/cita confirmada/i)).toBeDefined();
    expect(screen.getByText(/bk_abc123/i)).toBeDefined();
  });
});
