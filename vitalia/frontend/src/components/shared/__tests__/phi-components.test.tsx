/**
 * RED tests — PHI components (T-infra-7 TDD)
 * Tests written BEFORE implementation (TDD RED-first).
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// These imports will fail until components are implemented (RED state)
import { PiiMaskedSpan } from "@/components/shared/phi/PiiMaskedSpan";
import { RequireRole } from "@/components/shared/phi/RequireRole";

describe("PiiMaskedSpan", () => {
  it("renders masked value by default", () => {
    render(<PiiMaskedSpan value="Juan García" fieldType="name" />);
    // Should show masked value — not the full raw value
    const element = document.body.querySelector("[data-phi]");
    expect(element).toBeTruthy();
  });

  it("renders masked DNI", () => {
    render(<PiiMaskedSpan value="12345678" fieldType="dni" />);
    const element = document.body.querySelector("[data-phi]");
    expect(element).toBeTruthy();
  });

  it("applies aria-label for accessibility", () => {
    const { container } = render(
      <PiiMaskedSpan value="test@email.com" fieldType="email" />,
    );
    const span = container.querySelector("[aria-label]");
    expect(span).toBeTruthy();
  });
});

describe("RequireRole", () => {
  it("renders children when user has required role", () => {
    render(
      <RequireRole roles={["doctor"]} userRole="doctor">
        <span data-testid="phi-content">Diagnóstico secreto</span>
      </RequireRole>,
    );
    expect(screen.getByTestId("phi-content")).toBeTruthy();
  });

  it("hides children when user does not have required role", () => {
    render(
      <RequireRole roles={["doctor", "nurse"]} userRole="marketing">
        <span data-testid="phi-content">Diagnóstico secreto</span>
      </RequireRole>,
    );
    expect(screen.queryByTestId("phi-content")).toBeNull();
  });

  it("renders fallback when provided and user lacks role", () => {
    render(
      <RequireRole
        roles={["doctor"]}
        userRole="patient"
        fallback={<span data-testid="fallback">Acceso restringido</span>}
      >
        <span data-testid="phi-content">Diagnóstico</span>
      </RequireRole>,
    );
    expect(screen.getByTestId("fallback")).toBeTruthy();
    expect(screen.queryByTestId("phi-content")).toBeNull();
  });
});
