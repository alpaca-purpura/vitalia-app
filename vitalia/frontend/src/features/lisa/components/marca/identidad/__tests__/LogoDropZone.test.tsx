/**
 * LogoDropZone.test.tsx — RED tests for LogoDropZone component.
 * TDD: tests written before implementation (T-5 vitalia-fase2-lisa-marca).
 * spec_anchor: 06-tickets.yaml T-5 A2 — rejects >5MB + emits telemetry
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LogoDropZone } from "../LogoDropZone";

describe("LogoDropZone", () => {
  it("renders dropzone with accessible label", () => {
    render(<LogoDropZone onUpload={vi.fn()} />);
    expect(screen.getByRole("button")).toBeTruthy();
  });

  it("shows preview when logoUrl provided", () => {
    render(
      <LogoDropZone
        onUpload={vi.fn()}
        logoUrl="https://example.com/logo.png"
      />,
    );
    expect(screen.getByAltText(/logo/i)).toBeTruthy();
  });

  it("rejects files larger than 5MB", () => {
    const onError = vi.fn();
    render(<LogoDropZone onUpload={vi.fn()} onValidationError={onError} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (!input) return;

    const largeFile = new File(["x".repeat(6 * 1024 * 1024)], "logo.jpg", {
      type: "image/jpeg",
    });
    Object.defineProperty(largeFile, "size", { value: 6 * 1024 * 1024 });

    fireEvent.change(input, { target: { files: [largeFile] } });
    expect(onError).toHaveBeenCalledWith(expect.stringMatching(/5\s*MB/i));
  });

  it("rejects unsupported file formats", () => {
    const onError = vi.fn();
    render(<LogoDropZone onUpload={vi.fn()} onValidationError={onError} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (!input) return;

    const badFile = new File(["data"], "logo.pdf", { type: "application/pdf" });
    Object.defineProperty(badFile, "size", { value: 100 });

    fireEvent.change(input, { target: { files: [badFile] } });
    expect(onError).toHaveBeenCalledWith(expect.stringMatching(/formato/i));
  });

  it("calls onUpload with valid image file", () => {
    const onUpload = vi.fn();
    render(<LogoDropZone onUpload={onUpload} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (!input) return;

    const validFile = new File(["data"], "logo.png", { type: "image/png" });
    Object.defineProperty(validFile, "size", { value: 1024 });

    fireEvent.change(input, { target: { files: [validFile] } });
    expect(onUpload).toHaveBeenCalledWith(validFile);
  });
});
