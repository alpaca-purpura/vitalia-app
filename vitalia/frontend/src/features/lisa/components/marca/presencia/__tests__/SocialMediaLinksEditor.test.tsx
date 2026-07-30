// voseo-allowed: test fixture uses voseo regex patterns as negative assertions (verifies no voseo in rendered DOM)
/**
 * SocialMediaLinksEditor.test.tsx — Unit tests for SocialMediaLinksEditor.
 *
 * TDD per tdd-mandatory.md.
 * Tests: 5 social rows rendered, autosave trigger, disabled "+ Agregar otra red",
 * Spanish neutro labels, no voseo.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 + fe_test_social_media_links validator
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { SocialMediaLinksEditor } from "../SocialMediaLinksEditor";

function renderEditor(props?: Partial<Parameters<typeof SocialMediaLinksEditor>[0]>) {
  const onScheduleAutosave = vi.fn();
  render(
    <SocialMediaLinksEditor
      onScheduleAutosave={props?.onScheduleAutosave ?? onScheduleAutosave}
      instagram={props?.instagram ?? null}
      tiktok={props?.tiktok ?? null}
      facebook={props?.facebook ?? null}
      googleBusiness={props?.googleBusiness ?? null}
      whatsapp={props?.whatsapp ?? null}
    />,
  );
  return { onScheduleAutosave };
}

describe("SocialMediaLinksEditor", () => {
  it("renders card heading 'Redes sociales'", () => {
    renderEditor();
    expect(screen.getByText("Redes sociales")).toBeDefined();
  });

  it("renders all 5 social channel labels", () => {
    renderEditor();
    // Each channel has label (FormLabel sr-only) + visible span — use getAllByText
    expect(screen.getAllByText("Instagram").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("TikTok").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Facebook").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Google Business").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("WhatsApp Business").length).toBeGreaterThanOrEqual(1);
  });

  it("renders 5 accessible inputs (one per channel)", () => {
    renderEditor();
    expect(screen.getByRole("textbox", { name: /Usuario de Instagram/i })).toBeDefined();
    expect(screen.getByRole("textbox", { name: /Usuario de TikTok/i })).toBeDefined();
    expect(screen.getByRole("textbox", { name: /Página de Facebook/i })).toBeDefined();
    expect(screen.getByRole("textbox", { name: /URL de Google Business/i })).toBeDefined();
    expect(screen.getByRole("textbox", { name: /Número de WhatsApp Business/i })).toBeDefined();
  });

  it("populates instagram field from props", () => {
    renderEditor({ instagram: "@clinicaejemplo" });
    const input = screen.getByRole("textbox", { name: /Usuario de Instagram/i });
    expect((input as HTMLInputElement).value).toBe("@clinicaejemplo");
  });

  it("calls onScheduleAutosave when instagram input changes", () => {
    const onScheduleAutosave = vi.fn();
    renderEditor({ onScheduleAutosave });
    const input = screen.getByRole("textbox", { name: /Usuario de Instagram/i });
    fireEvent.change(input, { target: { value: "@nuevaclínica" } });
    expect(onScheduleAutosave).toHaveBeenCalledWith(
      expect.objectContaining({ instagramHandle: "@nuevaclínica" }),
    );
  });

  it("renders disabled '+ Agregar otra red' button (future story)", () => {
    renderEditor();
    const btn = screen.getByRole("button", { name: /Agregar otra red/i });
    expect(btn).toBeDefined();
    expect((btn as HTMLButtonElement).disabled).toBe(true);
  });

  it("hint texts use Spanish neutro — no voseo imperatives", () => {
    renderEditor();
    // Check Instagram hint
    const hints = screen.getAllByText(/Ingresa el nombre/i);
    hints.forEach((el) => {
      expect(el.textContent).not.toMatch(/ingresá|ponelo|colocá/);
    });
  });
});
