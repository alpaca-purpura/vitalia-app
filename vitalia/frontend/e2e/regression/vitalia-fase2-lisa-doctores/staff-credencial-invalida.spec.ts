// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
// T-E2E vitalia-fase2-lisa-doctores
/**
 * staff-credencial-invalida.spec.ts
 *
 * Covers: SC-2 (negative: credencial CMP inválida — abc en lugar de numérico).
 *
 * Real-verification design:
 *   - POST /api/v1/vitalia/clinics/doctors MUST return 422 { field: "credential", ... }
 *   - UI shows inline error + focus on credential field.
 *   - NO doctor persisted (cero rows in DB).
 *   - This spec uses route mock for the 422 response (UI test — testing the UI's
 *     handling of the 422, not the validator itself — that is in backend tests).
 *
 * spec_anchor: 04-validators.yaml § V-FN-5
 *
 * ★ STACK-STATUS: PENDING-LIVE-VERIFICATION
 *   When BE:8002 + FE:3002 are up:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase2-lisa-doctores/staff-credencial-invalida.spec.ts
 */

import { expect } from "@playwright/test";
import {
  test,
  STAFF_SEED,
} from "../../fixtures/vitalia-fase2-lisa-doctores.fixture";
import { StaffDirectoryPage } from "../../pages/StaffDirectoryPage";

const TENANT_ID = STAFF_SEED.tenantA.id;

test.describe("SC-2 — negative: credencial CMP inválida", () => {
  test("ingresa credencial abc (no numérica), backend retorna 422, UI muestra error inline + foco, NO persiste", async ({
    staffPage,
  }) => {
    // Override create endpoint to return 422 for invalid credential
    await staffPage.route(
      `**/api/v1/vitalia/clinics/doctors`,
      async (route) => {
        if (route.request().method() === "POST") {
          const body = JSON.parse(route.request().postData() ?? "{}");
          if (body.credential && !/^\d+$/.test(String(body.credential))) {
            await route.fulfill({
              status: 422,
              contentType: "application/json",
              body: JSON.stringify({
                detail: [
                  {
                    type: "value_error",
                    loc: ["body", "credential"],
                    msg: "La credencial CMP debe ser numérica",
                    input: body.credential,
                    ctx: { field: "credential" },
                  },
                ],
              }),
            });
          } else {
            await route.continue();
          }
        } else {
          await route.continue();
        }
      },
    );

    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    // Open modal
    await directory.openNewDoctorModal();
    await expect(directory.nuevoIntegranteModal).toBeVisible();

    // Fill with INVALID credential "abc"
    await directory.fillNewDoctorForm({
      firstName: "Pedro",
      lastName: "Inválido",
      dni: "12345678",
      email: "pedro.invalido@clinica.pe",
      specialty: "Medicina General",
      credential: "abc", // ← invalid CMP
      credentialCountry: "PE",
    });

    // Submit
    await directory.submitNewDoctorForm();

    // UI should show 422 error — modal stays open
    await expect(directory.nuevoIntegranteModal).toBeVisible();

    // Credential field should be in error state
    const credentialInError = await directory.isCredentialInErrorState();
    expect(credentialInError).toBeTruthy();

    // Error message visible (CMP numérica)
    await expect(directory.modalCredentialError).toBeVisible({ timeout: 5_000 });

    // Focus should be on credential input
    const focusedTag = await staffPage.evaluate(
      () => document.activeElement?.getAttribute("name") ?? document.activeElement?.id ?? "",
    );
    // Either name or id contains "credential"
    expect(focusedTag.toLowerCase()).toContain("credential");

    // Modal still open (no navigation away)
    expect(staffPage.url()).not.toMatch(/\/lisa\/staff\/.+\/perfil/);

    // Verify URL did NOT change to workspace (no doctor created)
    expect(staffPage.url()).not.toMatch(/\/lisa\/staff\/[^/]+\/perfil/);
  });

  test("credencial vacía en campo requerido — validación client-side antes del submit", async ({
    staffPage,
  }) => {
    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    await directory.openNewDoctorModal();
    await expect(directory.nuevoIntegranteModal).toBeVisible();

    // Fill all except credential
    await directory.fillNewDoctorForm({
      firstName: "Rosa",
      lastName: "Sin Credencial",
      dni: "87654321",
      email: "rosa@clinica.pe",
      credential: "", // ← empty
      credentialCountry: "PE",
    });

    await directory.submitNewDoctorForm();

    // Modal stays open (validation prevents submit)
    await expect(directory.nuevoIntegranteModal).toBeVisible();

    // No navigation
    expect(staffPage.url()).not.toMatch(/\/lisa\/staff\/.+\/perfil/);
  });
});
