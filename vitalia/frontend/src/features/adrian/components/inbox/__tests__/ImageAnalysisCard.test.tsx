/**
 * ImageAnalysisCard.test.tsx — Slice 1 stub for image analysis card.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ImageAnalysisCard } from "../ImageAnalysisCard";
import { INBOX_COPY } from "../../../lib/copy";

describe("ImageAnalysisCard", () => {
  it("renders with correct aria-label", () => {
    render(<ImageAnalysisCard mediaUrl="https://cdn.example.com/image.jpg" />);
    expect(
      screen.getByRole("figure", {
        name: INBOX_COPY.multimedia.imagePlaceholder.ariaLabel,
      }),
    ).toBeInTheDocument();
  });

  it("renders the placeholder heading and body from INBOX_COPY", () => {
    render(<ImageAnalysisCard mediaUrl="https://cdn.example.com/image.jpg" />);
    expect(
      screen.getByText(INBOX_COPY.multimedia.imagePlaceholder.heading),
    ).toBeInTheDocument();
    expect(
      screen.getByText(INBOX_COPY.multimedia.imagePlaceholder.body),
    ).toBeInTheDocument();
  });

  it("renders an img element with the provided media URL", () => {
    const url = "https://cdn.example.com/image.jpg";
    render(<ImageAnalysisCard mediaUrl={url} />);
    // Next/Image renders an <img> with that src (proxied)
    const img = screen.getByRole("img");
    expect(img).toBeInTheDocument();
    // alt should match copy
    expect(img).toHaveAttribute(
      "alt",
      INBOX_COPY.multimedia.imagePlaceholder.ariaLabel,
    );
  });

  it("accepts className prop without errors", () => {
    const { container } = render(
      <ImageAnalysisCard
        mediaUrl="https://cdn.example.com/image.jpg"
        className="custom-class"
      />,
    );
    expect(container.firstChild).toBeInTheDocument();
  });
});
