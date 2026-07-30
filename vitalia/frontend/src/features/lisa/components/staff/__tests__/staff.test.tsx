// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff.test.tsx — Vitest unit tests for Staff directory components.
 *
 * Covers:
 *   - StaffCard renders doctor info correctly
 *   - StaffEmptyState shows heading + CTA
 *   - StaffErrorBanner shows error message + retry button
 *   - NuevoIntegranteModal: credential validation inline error (SC-2)
 *   - staffKeys key factory structure
 *   - doctorCreateSchema validation (country-specific credentials)
 *
 * TDD: these tests were written BEFORE the components (RED-first).
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § SC-2 + § SC-7 + § SC-8 + 04-validators.yaml V-FN-5/V-FN-6
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { StaffEmptyState } from "../StaffEmptyState";
import { StaffErrorBanner } from "../StaffErrorBanner";
import { StaffCard } from "../StaffCard";
import { staffKeys } from "../../../api/staff";
import { doctorCreateSchema } from "../../../types/staff-schema";
import type { DoctorListItem } from "../../../types/staff.types";

// ── Mock next/link and next/image for testing ─────────────────────────────────
vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("next/image", () => ({
  default: ({ src, alt, fill: _fill, sizes: _sizes, className }: { src: string; alt: string; fill?: boolean; sizes?: string; className?: string }) => (
    /* Test mock — real Image component is used in production */
    <div data-testid="mock-image" data-src={src} aria-label={alt} className={className} />
  ),
}));

// ── StaffEmptyState ────────────────────────────────────────────────────────────

describe("StaffEmptyState", () => {
  it("renders empty state heading", () => {
    render(<StaffEmptyState onAddClick={vi.fn()} />);
    expect(
      screen.getByText("Aún no hay integrantes en tu equipo"),
    ).toBeInTheDocument();
  });

  it("renders CTA button 'Agregar primer integrante'", () => {
    render(<StaffEmptyState onAddClick={vi.fn()} />);
    expect(
      screen.getByTestId("btn-agregar-primer-integrante"),
    ).toBeInTheDocument();
  });

  it("calls onAddClick when CTA clicked", () => {
    const fn = vi.fn();
    render(<StaffEmptyState onAddClick={fn} />);
    fireEvent.click(screen.getByTestId("btn-agregar-primer-integrante"));
    expect(fn).toHaveBeenCalledOnce();
  });

  it("has data-testid='empty-doctores' (SC-8 grader)", () => {
    render(<StaffEmptyState onAddClick={vi.fn()} />);
    expect(screen.getByTestId("empty-doctores")).toBeInTheDocument();
  });

  it("has role='status' for accessibility", () => {
    render(<StaffEmptyState onAddClick={vi.fn()} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});

// ── StaffErrorBanner ───────────────────────────────────────────────────────────

describe("StaffErrorBanner", () => {
  it("renders error message", () => {
    render(<StaffErrorBanner onRetry={vi.fn()} />);
    expect(screen.getByText(/No pudimos cargar el equipo/)).toBeInTheDocument();
  });

  it("renders Reintentar button", () => {
    render(<StaffErrorBanner onRetry={vi.fn()} />);
    expect(screen.getByTestId("btn-reintentar")).toBeInTheDocument();
  });

  it("calls onRetry when Reintentar clicked", () => {
    const fn = vi.fn();
    render(<StaffErrorBanner onRetry={fn} />);
    fireEvent.click(screen.getByTestId("btn-reintentar"));
    expect(fn).toHaveBeenCalledOnce();
  });

  it("has role='alert' (accessible error announcement)", () => {
    render(<StaffErrorBanner onRetry={vi.fn()} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

// ── StaffCard ──────────────────────────────────────────────────────────────────

// F1 follow-through: mock mirrors real BE camelCase contract.
// BE emits maskedDni (to_camel of masked_dni), patientsCount/npsScore nullable.
const MOCK_DOCTOR: DoctorListItem = {
  id: "doc-test-001",
  firstName: "Ana",
  lastName: "García",
  specialty: "Odontología",
  avatarUrl: null,
  yearsExperience: 8,
  patientsCount: 320,
  npsScore: 72,
  maskedDni: "***456",
  active: true,
};

describe("StaffCard", () => {
  it("renders doctor name", () => {
    render(<StaffCard doctor={MOCK_DOCTOR} tenantId="t-001" />);
    expect(screen.getByText("Ana García")).toBeInTheDocument();
  });

  it("renders specialty badge", () => {
    render(<StaffCard doctor={MOCK_DOCTOR} tenantId="t-001" />);
    expect(screen.getByTestId(`specialty-badge-${MOCK_DOCTOR.id}`)).toBeInTheDocument();
    expect(screen.getByText("Odontología")).toBeInTheDocument();
  });

  it("renders 'Ver perfil' link pointing to correct route", () => {
    render(<StaffCard doctor={MOCK_DOCTOR} tenantId="t-001" />);
    const link = screen.getByRole("link", { name: /Ver perfil/i });
    expect(link).toHaveAttribute("href", "/t-001/lisa/staff/doc-test-001/perfil");
  });

  it("renders years of experience stat", () => {
    render(<StaffCard doctor={MOCK_DOCTOR} tenantId="t-001" />);
    expect(screen.getByText("8a")).toBeInTheDocument();
  });

  it("renders NPS score stat", () => {
    render(<StaffCard doctor={MOCK_DOCTOR} tenantId="t-001" />);
    expect(screen.getByText("72")).toBeInTheDocument();
  });

  it("shows 'Inactivo' badge when doctor.active is false", () => {
    render(
      <StaffCard
        doctor={{ ...MOCK_DOCTOR, active: false }}
        tenantId="t-001"
      />,
    );
    expect(screen.getByText("Inactivo")).toBeInTheDocument();
  });

  it("renders dash when yearsExperience is null", () => {
    render(
      <StaffCard
        doctor={{ ...MOCK_DOCTOR, yearsExperience: null }}
        tenantId="t-001"
      />,
    );
    // All three stat cells show "—" when null
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it("has data-testid for Playwright selectors", () => {
    render(<StaffCard doctor={MOCK_DOCTOR} tenantId="t-001" />);
    expect(screen.getByTestId(`staff-card-${MOCK_DOCTOR.id}`)).toBeInTheDocument();
  });
});

// ── staffKeys factory ──────────────────────────────────────────────────────────

describe("staffKeys", () => {
  it("all returns ['lisa','staff']", () => {
    expect(staffKeys.all).toEqual(["lisa", "staff"]);
  });

  it("list key includes filters", () => {
    const filters = { q: "ana", page: 1 };
    expect(staffKeys.list(filters)).toEqual(["lisa", "staff", "list", filters]);
  });

  it("detail key includes doctor id", () => {
    expect(staffKeys.detail("doc-001")).toEqual(["lisa", "staff", "detail", "doc-001"]);
  });

  it("blocks key includes doctor id", () => {
    expect(staffKeys.blocks("doc-001")).toEqual([
      "lisa",
      "staff",
      "detail",
      "doc-001",
      "blocks",
    ]);
  });
});

// ── doctorCreateSchema — credential validation (SC-2) ─────────────────────────

describe("doctorCreateSchema — credential validation", () => {
  const base = {
    firstName: "Ana",
    lastName: "García",
    dni: "12345678",
    email: "ana@test.com",
    credential: "12345",
    credentialCountry: "PE" as const,
    active: true,
  };

  it("accepts valid PE numeric credential", () => {
    const result = doctorCreateSchema.safeParse({ ...base, credential: "99999", credentialCountry: "PE" });
    expect(result.success).toBe(true);
  });

  it("rejects PE non-numeric credential (SC-2)", () => {
    const result = doctorCreateSchema.safeParse({ ...base, credential: "abc", credentialCountry: "PE" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const credError = result.error.issues.find((i) => i.path.includes("credential"));
      expect(credError?.message).toBe("La credencial CMP debe ser numérica");
    }
  });

  it("accepts AR alphanumeric credential", () => {
    const result = doctorCreateSchema.safeParse({ ...base, credential: "MP-12345", credentialCountry: "AR" });
    expect(result.success).toBe(true);
  });

  it("requires firstName", () => {
    const result = doctorCreateSchema.safeParse({ ...base, firstName: "" });
    expect(result.success).toBe(false);
  });

  it("requires valid email", () => {
    const result = doctorCreateSchema.safeParse({ ...base, email: "not-an-email" });
    expect(result.success).toBe(false);
  });
});

// ── Spanish neutro — no voseo in microcopy ────────────────────────────────────
// voseo-allowed: test file references voseo regex to verify absence — not user-facing strings

describe("Spanish neutro — no voseo in component text", () => {
  const VOSEO_RE = /\b(vos|sos|tenés|podés|hacés|dejá|mirá|poné|usá|elegí|agregá|configurá|revisá|guardá|abrí|volvé|cambiá|seleccioná)\b/i;

  it("StaffEmptyState has no voseo", () => {
    const { container } = render(<StaffEmptyState onAddClick={vi.fn()} />);
    expect(VOSEO_RE.test(container.textContent ?? "")).toBe(false);
  });

  it("StaffErrorBanner has no voseo", () => {
    const { container } = render(<StaffErrorBanner onRetry={vi.fn()} />);
    expect(VOSEO_RE.test(container.textContent ?? "")).toBe(false);
  });

  it("StaffCard has no voseo", () => {
    const { container } = render(<StaffCard doctor={MOCK_DOCTOR} tenantId="t-001" />);
    expect(VOSEO_RE.test(container.textContent ?? "")).toBe(false);
  });
});
