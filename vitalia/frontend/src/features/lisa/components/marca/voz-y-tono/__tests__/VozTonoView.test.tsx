// voseo-allowed: test fixture verifies no voseo appears in rendered DOM (negative assertion)
/**
 * VozTonoView.test.tsx — RED tests for VozTonoView client root.
 *
 * TDD: tests written before implementation (tdd-mandatory.md).
 * Critical: OQ-E single BrandVoicePreview instance + T-6 A3 acceptance.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 A3 (single BrandVoicePreview) + A5 (Spanish neutro)
 */

import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    orgId: "org-tenant-123",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../../../api/marca-voice-api", () => ({
  getPersonality: vi.fn().mockResolvedValue({
    tenantId: "tenant-abc",
    personalityProfileId: "profile-xyz",
    archetype: "caregiver",
    soISpeak: "- Acompañamos con cuidado",
    soIDontSpeak: "- Sin frases milagrosas",
    technicalContext: "Odontología general",
    formatInstructions: "Respuestas cortas, cálidas",
    identityAnchor: "Clínica Dental Lima Centro",
    domainContext: "Salud dental, Lima PE",
    compiledAt: "2026-05-27T10:00:00Z",
    compilerVersion: "v2",
  }),
  getProhibitedPhrases: vi.fn().mockResolvedValue({
    items: [],
    total: 0,
  }),
  getVoicePreview: vi.fn().mockResolvedValue({
    personalityProfileId: "profile-xyz",
    sampleWhatsapp: "Hola, soy Valeria.",
    sampleEmailReactivacion: "Hola Carlos, te recordamos.",
    compiledAt: "2026-05-27T10:00:00Z",
    compilerVersion: "v2",
    cacheHit: false,
  }),
}));

// Lazy import after mocks
async function renderVozTonoView(tenantId = "tenant-abc") {
  const { VozTonoView } = await import("../VozTonoView");
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <VozTonoView tenantId={tenantId} />
    </QueryClientProvider>,
  );
}

describe("VozTonoView", () => {
  // coverage_update Bug #3 (vitalia-bugfix-shell-nav-scroll-errors T-6): se removió
  // el h2-eco "Voz y tono" (duplicaba el SubSubTab activo). Se conserva el AutosaveBadge.
  it("ya NO renderiza el h2-eco 'Voz y tono' (Bug #3 removido), conserva el AutosaveBadge", async () => {
    await renderVozTonoView();
    expect(
      screen.queryByRole("heading", { name: /^voz y tono$/i }),
    ).toBeNull();
    // AutosaveBadge (role status) sigue presente.
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders ArchetypeSelector section", async () => {
    await renderVozTonoView();
    expect(screen.getByText(/arquetipo principal/i)).toBeInTheDocument();
  });

  it("renders exactly ONE BrandVoicePreview (OQ-E footer único)", async () => {
    await renderVozTonoView();
    // Single footer preview instance
    const previews = screen.getAllByTestId("brand-voice-preview");
    expect(previews).toHaveLength(1);
  });

  it("renders TreatmentLanguageCard section", async () => {
    await renderVozTonoView();
    expect(screen.getByText(/tratamiento e idioma/i)).toBeInTheDocument();
  });

  it("does NOT contain voseo (Spanish neutro A5)", async () => {
    await renderVozTonoView();
    const body = document.body.textContent ?? "";
    // Check common voseo imperatives
    expect(body).not.toMatch(/\b(tenés|podés|escribí|elegí|configurá|mirá)\b/i);
  });
});
