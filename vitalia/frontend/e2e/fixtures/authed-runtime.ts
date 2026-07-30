/**
 * authed-runtime.ts — gate anti-burbuja de `base.ts` (#37: pageerror / console.error
 * / 4xx-5xx /api/ / overlay de error de Next) + auth de Clerk + contexto de shell
 * (tenant) para specs que ejercen rutas autenticadas del shell-organism.
 *
 * Origen 2026-06-04 (live-verify vitalia-fase2-adrian-embudo): los specs del embudo
 * importaban solo `base.ts` → (1) `page` sin token de Clerk → bot-detection / sesión
 * no reconocida server-side → /sign-in; (2) sin mocks de shell, el hook cliente
 * `useTenants` pega a `/api/v1/iam/users/me/tenants` (bug de path global del shell:
 * el BE sirve `/me/tenants`) → 404 que el gate anti-burbuja caza. La SSR del layout
 * resuelve el tenant contra el backend real (por eso el board renderiza), pero el
 * fetch cliente fallaba.
 *
 * Composición MÍNIMA (probada live 2026-06-04): `base.ts` (anti-burbuja) + un
 * AUTO-fixture que (a) aplica `setupClerkTestingToken`, (b) inyecta x-tenant-id /
 * __vitalia_e2e__, (c) mockea el contexto de shell (tenant/profile, iam/me, doctors)
 * vía `setupClinicContextMocks` + la lista `/me/tenants`. La storageState autenticada
 * la aporta el project `smoke`.
 *
 * NO se hace `mergeTests` con `auth.fixture`: su option `baseUrl` (default :3000) +
 * `authedPage` rompían la storageState/baseURL del project (verificado 2026-06-04).
 */
import { test as base, expect } from "./base";
import { setupClerkTestingToken } from "@clerk/testing/playwright";
import {
  CLINIC_CONTEXT,
  setupClinicContextMocks,
} from "./clinic-context.fixture";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

export const test = base.extend<{ _embudoAuth: void }>({
  _embudoAuth: [
    async ({ page }, use) => {
      // (a) Token de testing: que server (auth.protect) + client reconozcan la sesión.
      await setupClerkTestingToken({ page });

      // (b) Tenant scope para el fetchClient (lee x-tenant-id) + flag e2e.
      await page.addInitScript((tid: string) => {
        localStorage.setItem("x-tenant-id", tid);
        localStorage.setItem("__vitalia_e2e__", "true");
      }, TENANT_ID);

      // (c) Contexto de shell (mismos mocks que usa inbox) + lista de tenants del
      //     usuario (el hook cliente useTenants pega a /users/me/tenants — path bug
      //     global del shell, lo servimos para no fallar el gate por una deuda ajena).
      await setupClinicContextMocks(page);
      await page.route("**/api/v1/iam/users/me/tenants", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: TENANT_ID,
              name: CLINIC_CONTEXT.clinicName,
              slug: "sanare",
              role: "owner",
            },
          ]),
        });
      });

      await use();
    },
    { auto: true },
  ],
});

export { expect };
