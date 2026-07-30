// story-origin: vitalia-fase2-mateo-nueva-cita (P-0) — success/warning variants
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { Badge } from "../badge";

describe("Badge", () => {
  it("renders the default variant", () => {
    render(<Badge>Activa</Badge>);
    const badge = screen.getByText("Activa");
    expect(badge.className).toContain("bg-primary");
  });

  it("renders the success variant with the semantic success class", () => {
    render(<Badge variant="success">Pago confirmado</Badge>);
    const badge = screen.getByText("Pago confirmado");
    expect(badge.className).toContain("bg-success");
    expect(badge.className).toContain("text-success-foreground");
  });

  it("renders the warning variant with the semantic warning class", () => {
    render(<Badge variant="warning">Pago pendiente</Badge>);
    const badge = screen.getByText("Pago pendiente");
    expect(badge.className).toContain("bg-warning");
    expect(badge.className).toContain("text-warning-foreground");
  });

  it("keeps the existing destructive variant intact (no regression)", () => {
    render(<Badge variant="destructive">Vencida</Badge>);
    expect(screen.getByText("Vencida").className).toContain("bg-destructive");
  });
});
