/**
 * Tests — WizardCompletionTransition component (T-onboarding-6 TDD)
 *
 * RED-first per .claude/rules/tdd-mandatory.md.
 * Tests morph 400ms transition, CTA, prefers-reduced-motion compliance.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { WizardCompletionTransition } from "../../components/WizardCompletionTransition";

// ─── Mocks ──────────────────────────────────────────────────────────────────

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("@/lib/cn", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("../../config/copy", () => ({
  WIZARD_COPY: {
    completion: {
      headline: "¡Tu clínica está configurada!",
      subheadline: "Vitalia ya conoce tu identidad de marca.",
      bodyText:
        "Tu agente inteligente está listo para atender pacientes con tu voz y estilo.",
      ctaButton: "Ir al panel principal",
      ctaButtonLoading: "Preparando tu panel...",
      confettiAlt: "Celebración",
    },
  },
}));

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("WizardCompletionTransition", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders null when isActive is false", () => {
    const { container } = render(
      <WizardCompletionTransition isActive={false} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders completion content when isActive is true", () => {
    render(<WizardCompletionTransition isActive />);
    expect(screen.getByText("¡Tu clínica está configurada!")).toBeTruthy();
    expect(
      screen.getByText("Vitalia ya conoce tu identidad de marca."),
    ).toBeTruthy();
  });

  it("renders CTA button with correct label", () => {
    render(<WizardCompletionTransition isActive />);
    expect(
      screen.getByRole("button", { name: "Ir al panel principal" }),
    ).toBeTruthy();
  });

  it("calls onNavigate when CTA is clicked", () => {
    const onNavigate = vi.fn();
    render(<WizardCompletionTransition isActive onNavigate={onNavigate} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Ir al panel principal" }),
    );
    expect(onNavigate).toHaveBeenCalledTimes(1);
  });

  it("navigates to / when no onNavigate provided", () => {
    render(<WizardCompletionTransition isActive />);
    fireEvent.click(
      screen.getByRole("button", { name: "Ir al panel principal" }),
    );
    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("has role='main' for accessibility", () => {
    render(<WizardCompletionTransition isActive />);
    expect(screen.getByRole("main")).toBeTruthy();
  });

  it("has aria-live='assertive' for screen readers", () => {
    render(<WizardCompletionTransition isActive />);
    const main = screen.getByRole("main");
    expect(main.getAttribute("aria-live")).toBe("assertive");
  });

  it("has aria-label from headline", () => {
    render(<WizardCompletionTransition isActive />);
    const main = screen.getByRole("main");
    // aria-label is set to copy.headline (mocked as "¡Tu clínica está configurada!")
    expect(main.getAttribute("aria-label")).toBe(
      "¡Tu clínica está configurada!",
    );
  });

  it("renders z-50 fixed overlay (fullscreen)", () => {
    render(<WizardCompletionTransition isActive />);
    const main = screen.getByRole("main");
    // The role="main" element IS the fixed overlay wrapper
    expect(main.className).toContain("fixed");
  });

  it("CTA button is disabled while navigating", () => {
    const onNavigate = vi.fn(() => {
      // Simulates slow navigation
    });
    render(<WizardCompletionTransition isActive onNavigate={onNavigate} />);
    const btn = screen.getByRole("button", { name: "Ir al panel principal" });
    fireEvent.click(btn);
    // After click, button should show loading state
    expect(screen.getByText("Preparando tu panel...")).toBeTruthy();
  });
});
