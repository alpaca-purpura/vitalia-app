/**
 * ClinicVerticalReadOnly.test.tsx — Vitest unit tests para componente read-only de vertical.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md D3-clinic
 *
 * Tests cubiertos:
 *   - Render vertical pill (clinicVertical como texto visible)
 *   - Render specialty pills (hasta 5 visibles)
 *   - "+N más" badge cuando hay más de 5 especialidades
 *   - Sin specialties: sección especialidades no visible
 *   - Sin vertical: texto "Sin especialidad registrada"
 *   - Edit link apunta a /{tenantId}/onboarding/clinic-config
 *   - aria-label de sección presente ("Especialidad clínica (solo lectura)")
 *   - aria-label de especialidades presente ("Especialidades de la clínica")
 *
 * downstream-regression-na: brand-local vitalia FE component tests; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ClinicVerticalReadOnly } from "../ClinicVerticalReadOnly";

// ── Mock next/link ──────────────────────────────────────────────────────────────

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

// ── Fixtures ───────────────────────────────────────────────────────────────────

const BASE_PROPS = {
  clinicVertical: "Odontología General",
  primarySpecialties: ["Ortodoncia", "Implantes", "Blanqueamiento"],
  tenantId: "tenant-abc",
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("ClinicVerticalReadOnly — vertical pill", () => {
  it("muestra el nombre de la vertical clínica", () => {
    render(<ClinicVerticalReadOnly {...BASE_PROPS} />);
    expect(screen.getByText("Odontología General")).toBeTruthy();
  });

  it("muestra 'Sin especialidad registrada' cuando clinicVertical está vacío", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        clinicVertical=""
      />,
    );
    expect(screen.getByText("Sin especialidad registrada")).toBeTruthy();
  });
});

describe("ClinicVerticalReadOnly — specialty pills", () => {
  it("muestra hasta 5 especialidades visibles", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        primarySpecialties={["A", "B", "C", "D", "E"]}
      />,
    );
    expect(screen.getByText("A")).toBeTruthy();
    expect(screen.getByText("E")).toBeTruthy();
  });

  it("muestra todas las especialidades cuando son 3 (menos de 5)", () => {
    render(<ClinicVerticalReadOnly {...BASE_PROPS} />);
    expect(screen.getByText("Ortodoncia")).toBeTruthy();
    expect(screen.getByText("Implantes")).toBeTruthy();
    expect(screen.getByText("Blanqueamiento")).toBeTruthy();
  });

  it("no muestra sección de especialidades cuando la lista está vacía", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        primarySpecialties={[]}
      />,
    );
    // No debe haber aria-label de especialidades si la lista está vacía
    const specialtiesContainer = screen.queryByRole("generic", {
      name: "Especialidades de la clínica",
    });
    expect(specialtiesContainer).toBeNull();
  });
});

describe("ClinicVerticalReadOnly — badge '+N más'", () => {
  it("muestra '+1 más' cuando hay 6 especialidades", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        primarySpecialties={["A", "B", "C", "D", "E", "F"]}
      />,
    );
    expect(screen.getByText("+1 más")).toBeTruthy();
  });

  it("muestra '+3 más' cuando hay 8 especialidades", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        primarySpecialties={["A", "B", "C", "D", "E", "F", "G", "H"]}
      />,
    );
    expect(screen.getByText("+3 más")).toBeTruthy();
  });

  it("NO muestra badge de ocultos cuando hay exactamente 5 especialidades", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        primarySpecialties={["A", "B", "C", "D", "E"]}
      />,
    );
    expect(screen.queryByText(/\+\d+ más/)).toBeNull();
  });

  it("muestra la especialidad #6 en el badge, no como pill visible", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        primarySpecialties={["A", "B", "C", "D", "E", "Especialidad Oculta"]}
      />,
    );
    // La 6ª especialidad no debe aparecer como texto propio
    expect(screen.queryByText("Especialidad Oculta")).toBeNull();
    expect(screen.getByText("+1 más")).toBeTruthy();
  });
});

describe("ClinicVerticalReadOnly — edit link", () => {
  it("contiene enlace a /{tenantId}/onboarding/clinic-config", () => {
    render(<ClinicVerticalReadOnly {...BASE_PROPS} tenantId="mi-clinica" />);
    const editLink = screen.getByRole("link", {
      name: /editar especialidad/i,
    });
    expect(editLink).toBeTruthy();
    expect(editLink.getAttribute("href")).toBe("/mi-clinica/onboarding/clinic-config");
  });

  it("texto del enlace es 'Editar'", () => {
    render(<ClinicVerticalReadOnly {...BASE_PROPS} />);
    expect(screen.getByText("Editar")).toBeTruthy();
  });
});

describe("ClinicVerticalReadOnly — accesibilidad (ARIA)", () => {
  it("sección tiene aria-label 'Especialidad clínica (solo lectura)'", () => {
    render(<ClinicVerticalReadOnly {...BASE_PROPS} />);
    const section = screen.getByRole("region", {
      name: "Especialidad clínica (solo lectura)",
    });
    expect(section).toBeTruthy();
  });

  it("contenedor de especialidades tiene aria-label 'Especialidades de la clínica'", () => {
    render(
      <ClinicVerticalReadOnly
        {...BASE_PROPS}
        primarySpecialties={["Ortodoncia", "Implantes"]}
      />,
    );
    // Buscar por texto del aria-label
    const specialtiesEl = screen.getByLabelText("Especialidades de la clínica");
    expect(specialtiesEl).toBeTruthy();
  });
});
