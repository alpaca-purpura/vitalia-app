/**
 * Unit tests — [agent]/[subtab]/page.tsx (Server Component).
 *
 * Vitest + @testing-library/react.
 *
 * SubtabPage valida tanto el agent como el subtab. Si inválido → notFound().
 * Si válido → renderiza SubTabContent con el data-testid correcto (T-9).
 *
 * TDD RED-first → GREEN: tests escritos antes de la implementación.
 * T-9 update: F1-S10 reemplazó placeholder estático "Contenido próximamente"
 * con <SubTabContent agent subtab /> → assertions actualizadas a data-testid
 * del wrapper SubTabContent: `subtab-content-{agent}-{subtab}`.
 *
 * spec_anchor: 03-arch-fe.md § 9.6 verbatim + 06-tickets.yaml T-4 SC-3 + T-9
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// vi.mock is hoisted — use vi.fn() inline.
vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
  redirect: vi.fn(),
}));

import * as navigation from "next/navigation";
import SubtabPage from "./page";

const mockNotFound = vi.mocked(navigation.notFound);

const makeParams = (tenantId: string, agent: string, subtab: string) =>
  Promise.resolve({ tenantId, agent, subtab });

describe("SubtabPage", () => {
  beforeEach(() => {
    mockNotFound.mockClear();
  });

  describe("happy path — agent y subtab válidos", () => {
    it("renderiza SubTabContent para mateo/pacientes (v1.2 — pacientes migrado a mateo)", async () => {
      // v1.2 (2026-05-30): mateo.pacientes is a valid subtab (agenda is shipped static)
      render(
        await SubtabPage({
          params: makeParams("clinic-x", "mateo", "pacientes"),
        }),
      );
      expect(
        screen.getByTestId("subtab-content-mateo-pacientes"),
      ).toBeInTheDocument();
    });

    it("renderiza SubTabContent para lisa/marca", async () => {
      render(
        await SubtabPage({ params: makeParams("clinic-x", "lisa", "marca") }),
      );
      expect(
        screen.getByTestId("subtab-content-lisa-marca"),
      ).toBeInTheDocument();
    });

    it("renderiza SubTabContent para lucas/lanzar", async () => {
      render(
        await SubtabPage({ params: makeParams("clinic-x", "lucas", "lanzar") }),
      );
      expect(
        screen.getByTestId("subtab-content-lucas-lanzar"),
      ).toBeInTheDocument();
    });

    it("renderiza SubTabContent para camila/reputacion", async () => {
      render(
        await SubtabPage({
          params: makeParams("clinic-x", "camila", "reputacion"),
        }),
      );
      expect(
        screen.getByTestId("subtab-content-camila-reputacion"),
      ).toBeInTheDocument();
    });

    it("renderiza SubTabContent para config/cuenta", async () => {
      render(
        await SubtabPage({
          params: makeParams("clinic-x", "config", "cuenta"),
        }),
      );
      expect(
        screen.getByTestId("subtab-content-config-cuenta"),
      ).toBeInTheDocument();
    });

    it("renderiza SubTabContent para config/avanzado", async () => {
      render(
        await SubtabPage({
          params: makeParams("clinic-x", "config", "avanzado"),
        }),
      );
      expect(
        screen.getByTestId("subtab-content-config-avanzado"),
      ).toBeInTheDocument();
    });
  });

  describe("error path — subtab inválido → notFound()", () => {
    it("llama notFound() cuando subtab es inválido para camila (foo)", async () => {
      await expect(
        SubtabPage({ params: makeParams("clinic-x", "camila", "foo") }),
      ).rejects.toThrow("NEXT_NOT_FOUND");
      expect(mockNotFound).toHaveBeenCalledTimes(1);
    });

    it("llama notFound() cuando subtab es inválido para lisa (agenda — de mateo, no lisa)", async () => {
      await expect(
        SubtabPage({ params: makeParams("clinic-x", "lisa", "agenda") }),
      ).rejects.toThrow("NEXT_NOT_FOUND");
      expect(mockNotFound).toHaveBeenCalledTimes(1);
    });

    it("llama notFound() cuando subtab vacío", async () => {
      await expect(
        SubtabPage({ params: makeParams("clinic-x", "mateo", "") }),
      ).rejects.toThrow("NEXT_NOT_FOUND");
      expect(mockNotFound).toHaveBeenCalledTimes(1);
    });
  });

  describe("error path — agent inválido → notFound()", () => {
    it("llama notFound() cuando agent es inválido (valeria — supervisor sidebar, no ribbon v1.2)", async () => {
      // v1.2 (2026-05-30): valeria is NOT a valid ribbon agent (isValidAgent('valeria') = false)
      await expect(
        SubtabPage({ params: makeParams("clinic-x", "valeria", "agenda") }),
      ).rejects.toThrow("NEXT_NOT_FOUND");
      expect(mockNotFound).toHaveBeenCalledTimes(1);
    });

    it("llama notFound() cuando agent es inválido (foo)", async () => {
      await expect(
        SubtabPage({ params: makeParams("clinic-x", "foo", "bar") }),
      ).rejects.toThrow("NEXT_NOT_FOUND");
      expect(mockNotFound).toHaveBeenCalledTimes(1);
    });
  });
});
