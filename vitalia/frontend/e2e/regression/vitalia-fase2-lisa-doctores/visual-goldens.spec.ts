// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
// T-FIX-2 vitalia-fase2-lisa-doctores
/**
 * visual-goldens.spec.ts — V-VIS-1..4 visual regression baselines
 *
 * Covers: SC-9 visual goldens (AC-9):
 *   V-VIS-1: directorio light/dark
 *   V-VIS-2: hoja Perfil light/dark
 *   V-VIS-3: hoja Horarios light/dark
 *   V-VIS-4: hoja Servicios placeholder light
 *
 * Lives in e2e/regression/vitalia-fase2-lisa-doctores/ to match
 * project=visual testMatch: /.*\/e2e\/regression\/.*\/visual-goldens\.spec\.ts$/
 * and testIgnore in project=smoke: /.*\/visual-goldens\.spec\.ts/
 *
 * Regenerate baselines:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/visual-goldens.spec.ts \
 *     --project=visual --update-snapshots
 *
 * Baselines stored at:
 *   e2e/__screenshots__/e2e/regression/vitalia-fase2-lisa-doctores/visual-goldens.spec.ts/
 *
 * spec_anchor: 04-validators.yaml § V-VIS-1..4
 * Requires Chris ratification per ADR-vitalia-003 before story merge.
 *
 * Relocated from staff-large-dataset.spec.ts (T-FIX-2 2026-06-01): that file
 * ran in project=smoke (no snapshotPathTemplate) causing golden failures.
 */

import { expect } from "@playwright/test";
import { test, STAFF_SEED } from "../../fixtures/vitalia-fase2-lisa-doctores.fixture";
import { StaffDirectoryPage } from "../../pages/StaffDirectoryPage";
import { DoctorWorkspacePage } from "../../pages/DoctorWorkspacePage";
import { AvailabilityCalendarPage } from "../../pages/AvailabilityCalendarPage";

const TENANT_ID = STAFF_SEED.tenantA.id;
const DOCTOR_ID = STAFF_SEED.tenantA.doctors[0]!.id;

// Visual goldens run serial to avoid viewport/theme race conditions
test.describe.configure({ mode: "serial" });

// ---------------------------------------------------------------------------
// V-VIS-1: directorio
// ---------------------------------------------------------------------------

test.describe("V-VIS-1 — directorio visual golden", () => {
  test("directorio light mode", async ({ staffPage }) => {
    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    await staffPage.emulateMedia({ colorScheme: "light" });

    await expect(directory.staffDirectoryView).toHaveScreenshot(
      "directorio-light.png",
    );
  });

  test("directorio dark mode", async ({ staffPage }) => {
    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    await staffPage.emulateMedia({ colorScheme: "dark" });
    await staffPage.evaluate(() =>
      document.documentElement.classList.add("dark"),
    );

    await expect(directory.staffDirectoryView).toHaveScreenshot(
      "directorio-dark.png",
    );
  });
});

// ---------------------------------------------------------------------------
// V-VIS-2: hoja Perfil (autosave form)
// ---------------------------------------------------------------------------

test.describe("V-VIS-2 — hoja Perfil visual golden", () => {
  test("perfil light mode", async ({ staffPage }) => {
    const workspace = new DoctorWorkspacePage(staffPage);
    await workspace.navigateToPerfil(TENANT_ID, DOCTOR_ID);
    await expect(workspace.autosaveHint).toBeVisible({ timeout: 10_000 });

    await staffPage.emulateMedia({ colorScheme: "light" });

    // Real assert: if doctor-perfil-view doesn't render, test should FAIL honestly
    // (not silently skip). If testid is missing from DoctorPerfilView, that's a bug.
    const perfilSection = staffPage.getByTestId("doctor-perfil-view");
    await expect(perfilSection).toBeVisible({ timeout: 8_000 });
    await expect(perfilSection).toHaveScreenshot("perfil-light.png");
  });

  test("perfil dark mode", async ({ staffPage }) => {
    const workspace = new DoctorWorkspacePage(staffPage);
    await workspace.navigateToPerfil(TENANT_ID, DOCTOR_ID);
    await expect(workspace.autosaveHint).toBeVisible({ timeout: 10_000 });

    await staffPage.emulateMedia({ colorScheme: "dark" });
    await staffPage.evaluate(() =>
      document.documentElement.classList.add("dark"),
    );

    const perfilSection = staffPage.getByTestId("doctor-perfil-view");
    await expect(perfilSection).toBeVisible({ timeout: 8_000 });
    await expect(perfilSection).toHaveScreenshot("perfil-dark.png");
  });
});

// ---------------------------------------------------------------------------
// V-VIS-3: hoja Horarios (calendario semana)
// ---------------------------------------------------------------------------

test.describe("V-VIS-3 — hoja Horarios visual golden", () => {
  test("horarios light mode", async ({ staffPage }) => {
    const calendar = new AvailabilityCalendarPage(staffPage);
    await calendar.goto(TENANT_ID, DOCTOR_ID);
    await calendar.calendar.waitFor({ state: "visible", timeout: 10_000 });

    await staffPage.emulateMedia({ colorScheme: "light" });

    await expect(calendar.calendar).toHaveScreenshot("horarios-light.png");
  });

  test("horarios dark mode", async ({ staffPage }) => {
    const calendar = new AvailabilityCalendarPage(staffPage);
    await calendar.goto(TENANT_ID, DOCTOR_ID);
    await calendar.calendar.waitFor({ state: "visible", timeout: 10_000 });

    await staffPage.emulateMedia({ colorScheme: "dark" });
    await staffPage.evaluate(() =>
      document.documentElement.classList.add("dark"),
    );

    await expect(calendar.calendar).toHaveScreenshot("horarios-dark.png");
  });
});

// ---------------------------------------------------------------------------
// V-VIS-4: hoja Servicios — placeholder pendiente
// ---------------------------------------------------------------------------

test.describe("V-VIS-4 — hoja Servicios placeholder visual golden", () => {
  test("servicios placeholder light mode", async ({ staffPage }) => {
    const workspace = new DoctorWorkspacePage(staffPage);
    await workspace.navigateToServicios(TENANT_ID, DOCTOR_ID);
    await expect(workspace.serviciosPlaceholder).toBeVisible({
      timeout: 10_000,
    });

    await staffPage.emulateMedia({ colorScheme: "light" });

    await expect(workspace.serviciosPlaceholder).toHaveScreenshot(
      "servicios-pendiente-light.png",
    );
  });
});
