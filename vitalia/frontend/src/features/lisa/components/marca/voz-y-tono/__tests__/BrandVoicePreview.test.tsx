/**
 * BrandVoicePreview.test.tsx — RED tests for BrandVoicePreview footer.
 *
 * TDD: tests written before implementation (tdd-mandatory.md).
 * Critical: OQ-E — SINGLE footer instance per VozTonoView.
 *           Accepts debounceHash for React Query key stability.
 *           Renders Valeria (purple) + Camila (indigo) bubbles.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A3 + A4 + 04-validators.yaml fe_test_voice_preview_footer
 */

import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import { BrandVoicePreview } from "../BrandVoicePreview";

// Mock the API call
vi.mock("../../../../api/marca-voice-api", () => ({
  getVoicePreview: vi.fn().mockResolvedValue({
    personalityProfileId: "profile-123",
    sampleWhatsapp: "Hola Sofía, soy Valeria de la clínica. ¿Confirmas tu cita?",
    sampleEmailReactivacion: "Hola Carlos, en nuestra clínica nos preocupamos por tu salud.",
    compiledAt: "2026-05-27T10:00:00Z",
    compilerVersion: "v2",
    cacheHit: false,
  }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("BrandVoicePreview", () => {
  it("renders the 'Preview compilado' heading", async () => {
    render(
      <TestWrapper>
        <BrandVoicePreview
          tenantId="tenant-abc"
          personalityProfileId="profile-123"
          debounceHash="abc123"
          isLoading={false}
        />
      </TestWrapper>,
    );

    // Section heading visible
    expect(screen.getByText(/preview compilado/i)).toBeInTheDocument();
  });

  it("renders Valeria WhatsApp bubble label", async () => {
    render(
      <TestWrapper>
        <BrandVoicePreview
          tenantId="tenant-abc"
          personalityProfileId="profile-123"
          debounceHash="abc123"
          isLoading={false}
        />
      </TestWrapper>,
    );

    expect(screen.getByText(/valeria/i)).toBeInTheDocument();
  });

  it("renders Camila email bubble label", async () => {
    render(
      <TestWrapper>
        <BrandVoicePreview
          tenantId="tenant-abc"
          personalityProfileId="profile-123"
          debounceHash="abc123"
          isLoading={false}
        />
      </TestWrapper>,
    );

    expect(screen.getByText(/camila/i)).toBeInTheDocument();
  });

  it("uses debounceHash in data-testid for React Query key stability", () => {
    render(
      <TestWrapper>
        <BrandVoicePreview
          tenantId="tenant-abc"
          personalityProfileId="profile-123"
          debounceHash="myhash999"
          isLoading={false}
        />
      </TestWrapper>,
    );

    const section = screen.getByTestId("brand-voice-preview");
    expect(section).toBeInTheDocument();
    // Hash embedded in data attr for key stability tracking
    expect(section).toHaveAttribute("data-hash", "myhash999");
  });

  it("shows skeleton when isLoading=true", () => {
    render(
      <TestWrapper>
        <BrandVoicePreview
          tenantId="tenant-abc"
          personalityProfileId="profile-123"
          debounceHash="abc123"
          isLoading={true}
        />
      </TestWrapper>,
    );

    expect(screen.getByRole("region", { name: /cargando preview de voz/i })).toBeInTheDocument();
  });

  it("shows BRAND_VOICE slot chip", () => {
    render(
      <TestWrapper>
        <BrandVoicePreview
          tenantId="tenant-abc"
          personalityProfileId="profile-123"
          debounceHash="abc123"
          isLoading={false}
        />
      </TestWrapper>,
    );

    expect(screen.getByText(/brand_voice/i)).toBeInTheDocument();
  });
});
