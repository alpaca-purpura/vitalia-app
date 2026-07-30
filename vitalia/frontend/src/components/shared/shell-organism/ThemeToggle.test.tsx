/**
 * ThemeToggle unit tests — F1-S1 vitalia-fase1-design-tokens-theme
 * TDD: RED written before ThemeToggle.tsx (GREEN) per .claude/rules/tdd-mandatory.md
 *
 * 03-arch.md § 2.8
 */
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ThemeProvider } from "next-themes";
import { ThemeToggle } from "./ThemeToggle";

// next-themes uses localStorage — vitest jsdom environment provides it.
// However, we need to wait for theme to resolve (next-themes is async on first render).

function renderWithProvider(defaultTheme: "light" | "dark") {
  return render(
    <ThemeProvider
      attribute="data-theme"
      defaultTheme={defaultTheme}
      enableSystem={false}
      storageKey="vitalia-theme"
    >
      <ThemeToggle />
    </ThemeProvider>,
  );
}

describe("ThemeToggle", () => {
  it("renders a button with data-testid='theme-toggle'", () => {
    renderWithProvider("light");
    const button = screen.getByTestId("theme-toggle");
    expect(button).toBeDefined();
    expect(button.tagName.toLowerCase()).toBe("button");
  });

  it("renders with Moon icon when theme is light (default)", () => {
    renderWithProvider("light");
    const button = screen.getByTestId("theme-toggle");
    // Moon icon from lucide-react renders as SVG; aria-label should contain "claro"
    expect(button.getAttribute("aria-label")).toMatch(/claro/i);
    // aria-pressed should be false (not dark)
    expect(button.getAttribute("aria-pressed")).toBe("false");
  });

  it("renders with Sun icon when theme is dark", async () => {
    renderWithProvider("dark");
    const button = screen.getByTestId("theme-toggle");
    // In dark mode: aria-label should contain "oscuro" and aria-pressed true
    // Note: next-themes needs a tick to resolve theme from localStorage/defaultTheme
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(button.getAttribute("aria-label")).toMatch(/oscuro/i);
    expect(button.getAttribute("aria-pressed")).toBe("true");
  });

  it("aria-label matches Spanish neutro pattern (no voseo)", () => {
    renderWithProvider("light");
    const button = screen.getByTestId("theme-toggle");
    const label = button.getAttribute("aria-label") ?? "";
    // Must match 'Cambiar tema (actual: claro)' or 'Cambiar tema (actual: oscuro)'
    expect(label).toMatch(/^Cambiar tema \(actual: (claro|oscuro)\)$/);
  });

  it("toggles theme on click (light → aria-pressed changes)", async () => {
    renderWithProvider("light");
    const button = screen.getByTestId("theme-toggle");
    expect(button.getAttribute("aria-pressed")).toBe("false");

    await act(async () => {
      fireEvent.click(button);
    });

    // After click: aria-pressed should reflect dark state
    // (theme state managed by next-themes ThemeProvider)
    expect(button.getAttribute("aria-pressed")).toBe("true");
  });

  it("has accessible name via aria-label (not just aria-label alone)", () => {
    renderWithProvider("light");
    const button = screen.getByTestId("theme-toggle");
    const label = button.getAttribute("aria-label");
    expect(label).toBeTruthy();
    expect(label).not.toBe("");
  });

  it("has sr-only span for additional screen reader context", () => {
    renderWithProvider("light");
    const srOnly = screen.getByText("Cambiar tema");
    expect(srOnly.className).toContain("sr-only");
  });
});
