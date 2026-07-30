/**
 * large-dataset.fixture.ts — F2-S7 vitalia-fase2-lisa-marca (HONEST · backend real)
 *
 * Fixture para el spec de rendimiento SC-9. El mock canned de 50 trust-signals
 * fue ELIMINADO (era mock del backend-bajo-prueba, RN-1; el grep-gate SC-2 ahora
 * cubre trust-signals). El `largeDatasetPage` compone el transporte honesto
 * (auth + forwarding a :8002 + anti-burbuja base.ts) — renderiza los datos REALES
 * del tenant. Los builders `buildLargeTrustSignals/Team` quedan como data para
 * aserciones unit-style del propio builder (in-memory, no de la página).
 *
 * Usage in specs:
 *   import { test, expect, buildLargeTrustSignals } from './fixtures/large-dataset.fixture';
 *
 * downstream-regression-na: brand-local vitalia e2e fixture F2-S7 perf test
 *
 * @see e2e/fixtures/real-backend-forward.fixture.ts
 * @see 04-validators.yaml § scenario_coverage (large_dataset: de-mockeado)
 */

import type { Page } from "@playwright/test";
import {
  test as realBackendTest,
  expect,
} from "../../../fixtures/real-backend-forward.fixture";
import { LISA_MARCA_FIXTURE } from "./lisa-marca.fixture";

// ---------------------------------------------------------------------------
// Large dataset builders (in-memory test data for builder unit assertions)
// ---------------------------------------------------------------------------

export interface TrustSignalItem {
  id: string;
  type: string;
  value: string;
  displayOrder: number;
}

export interface TeamMemberItem {
  id: string;
  name: string;
  role: string;
  specialty: string;
  displayOrder: number;
}

export function buildLargeTrustSignals(count: number = 50): TrustSignalItem[] {
  const types = [
    "certification",
    "award",
    "rating",
    "professional_association",
    "regulatory",
    "patient_satisfaction",
    "custom",
  ];
  const typeLabels: Record<string, string> = {
    certification: "Certificación",
    award: "Premio",
    rating: "Calificación",
    professional_association: "Asociación profesional",
    regulatory: "Habilitación",
    patient_satisfaction: "Satisfacción",
    custom: "Reconocimiento",
  };

  return Array.from({ length: count }, (_, i) => {
    const type = types[i % types.length];
    return {
      id: `ts-large-${String(i + 1).padStart(3, "0")}`,
      type: type ?? "custom",
      value: `${typeLabels[type ?? "custom"] ?? "Reconocimiento"} ${String(i + 1).padStart(2, "0")} — Salud Vitalia PE`,
      displayOrder: i + 1,
    };
  });
}

export function buildLargeTeamMembers(count: number = 30): TeamMemberItem[] {
  const roles = [
    "Médico especialista",
    "Médico general",
    "Enfermera",
    "Nutricionista",
    "Psicóloga",
  ];
  const specialties = [
    "Medicina interna",
    "Cardiología",
    "Nutrición clínica",
    "Salud mental",
    "Medicina general",
  ];
  const firstNames = [
    "Ana",
    "Carlos",
    "María",
    "José",
    "Patricia",
    "Luis",
    "Rosa",
    "Fernando",
  ];
  const lastNames = [
    "García",
    "López",
    "Martínez",
    "Rodríguez",
    "Sánchez",
    "Pérez",
  ];

  return Array.from({ length: count }, (_, i) => ({
    id: `team-large-${String(i + 1).padStart(3, "0")}`,
    name: `Dra. ${firstNames[i % firstNames.length]} ${lastNames[i % lastNames.length]}`,
    role: roles[i % roles.length] ?? "Médico general",
    specialty: specialties[i % specialties.length] ?? "Medicina general",
    displayOrder: i + 1,
  }));
}

// ---------------------------------------------------------------------------
// Fixture types
// ---------------------------------------------------------------------------

export type LargeDatasetFixtures = {
  /** Authenticated page with real-backend forwarding (renders real data) */
  largeDatasetPage: Page;
  /** 50 trust signal items (in-memory builder data for unit assertions) */
  largeTrustSignals: TrustSignalItem[];
  /** 30 team member items (in-memory builder data for unit assertions) */
  largeTeamMembers: TeamMemberItem[];
  /** Base fixture constants */
  fixture: typeof LISA_MARCA_FIXTURE;
};

// ---------------------------------------------------------------------------
// Fixture extension — composed on the honest real-backend transport
// ---------------------------------------------------------------------------

export const test = realBackendTest.extend<LargeDatasetFixtures>({
  // eslint-disable-next-line no-empty-pattern -- Playwright fixture API requires the empty destructure
  fixture: async ({}, use) => {
    await use(LISA_MARCA_FIXTURE);
  },

  // eslint-disable-next-line no-empty-pattern -- Playwright fixture API requires the empty destructure
  largeTrustSignals: async ({}, use) => {
    await use(buildLargeTrustSignals(50));
  },

  // eslint-disable-next-line no-empty-pattern -- Playwright fixture API requires the empty destructure
  largeTeamMembers: async ({}, use) => {
    await use(buildLargeTeamMembers(30));
  },

  // The honest, forwarded, authenticated page IS the large-dataset page.
  largeDatasetPage: async ({ page }, use) => {
    await use(page);
  },
});

export { expect };

// Re-export gotoMarca for spec ergonomics.
export { gotoMarca } from "./lisa-marca.fixture";
