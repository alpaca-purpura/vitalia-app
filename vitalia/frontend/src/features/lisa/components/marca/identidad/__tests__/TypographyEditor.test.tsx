// cap: brand_studio.lisa-marca
import { render } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { TypographyEditor } from "../TypographyEditor";

describe("TypographyEditor", () => {
  beforeEach(() => {
    document.head.querySelectorAll('link[id^="gfont-"]').forEach((l) => {
      l.remove();
    });
  });

  it("injects a Google Fonts stylesheet for the selected fonts (so the preview can render them)", () => {
    render(<TypographyEditor headingFont="Montserrat" bodyFont="Lato" />);

    const headingLink = document.getElementById("gfont-montserrat") as HTMLLinkElement | null;
    const bodyLink = document.getElementById("gfont-lato") as HTMLLinkElement | null;

    expect(headingLink).not.toBeNull();
    expect(bodyLink).not.toBeNull();
    expect(headingLink?.href).toContain("family=Montserrat");
    expect(headingLink?.rel).toBe("stylesheet");
  });

  it("uses '+' for multi-word font families in the Google Fonts URL", () => {
    render(<TypographyEditor headingFont="Open Sans" bodyFont="Source Sans 3" />);
    const link = document.getElementById("gfont-open-sans") as HTMLLinkElement | null;
    expect(link?.href).toContain("family=Open+Sans");
  });

  it("applies the selected font-family to the preview text", () => {
    const { getByText } = render(<TypographyEditor headingFont="Poppins" bodyFont="Merriweather" />);
    expect(getByText("Clínica Dental Lima Centro")).toHaveStyle({
      fontFamily: '"Poppins", sans-serif',
    });
    expect(getByText(/Tu salud bucal/)).toHaveStyle({
      fontFamily: '"Merriweather", sans-serif',
    });
  });
});
