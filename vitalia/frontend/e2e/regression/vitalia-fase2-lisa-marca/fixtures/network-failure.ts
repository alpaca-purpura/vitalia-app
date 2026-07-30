/**
 * network-failure.ts — F2-S7 vitalia-fase2-lisa-marca
 *
 * page.route abort helper for autosave timeout scenarios (SC-7).
 * Simulates network failures, timeouts, and flaky connectivity.
 *
 * Usage in specs:
 *   import { abortAutosaveRoute, simulateOfflineMode } from '../fixtures/network-failure';
 *   await abortAutosaveRoute(page, 'identity');
 *
 * downstream-regression-na: brand-local vitalia e2e fixture F2-S7 network test
 *
 * @see 04-validators.yaml § test_construction_plan step 4
 */

import type { Page, Route } from "@playwright/test";

// ---------------------------------------------------------------------------
// Abort types
// ---------------------------------------------------------------------------

export type NetworkFailureMode =
  | "abort" // Network connection reset
  | "timeout" // Connection timeout (no response)
  | "serverError" // 500 Internal Server Error
  | "gatewayTimeout" // 504 Gateway Timeout
  | "serviceUnavailable"; // 503 Service Unavailable

export type MarcaEndpoint =
  | "identity"
  | "visuals"
  | "personality"
  | "contact"
  | "trust-signals"
  | "voice-blocklist"
  | "voice-preview"
  | "trust-catalog"
  | "all";

// ---------------------------------------------------------------------------
// Endpoint URL pattern mapper
// ---------------------------------------------------------------------------

function getEndpointPattern(endpoint: MarcaEndpoint): string | string[] {
  if (endpoint === "all") {
    return "**/api/v1/lisa/marca/**";
  }
  return `**/api/v1/lisa/marca/${endpoint}`;
}

// ---------------------------------------------------------------------------
// abortAutosaveRoute — abort PATCH calls for a specific endpoint
// Models network failure during autosave debounce cycle
// ---------------------------------------------------------------------------

export async function abortAutosaveRoute(
  page: Page,
  endpoint: MarcaEndpoint = "identity",
  mode: NetworkFailureMode = "abort",
): Promise<void> {
  const pattern = getEndpointPattern(endpoint);

  const patterns = Array.isArray(pattern) ? pattern : [pattern];

  for (const p of patterns) {
    await page.route(p, async (route: Route) => {
      // Only intercept mutation methods (PATCH/POST/DELETE). Reads delegate via
      // route.fallback() to the next handler (the real-backend forwarding fixture)
      // so GET /<endpoint> hits the REAL backend (RN-1: no mock of reads).
      const method = route.request().method();
      if (!["PATCH", "POST", "DELETE"].includes(method)) {
        await route.fallback();
        return;
      }

      switch (mode) {
        case "abort": {
          await route.abort("connectionreset");
          break;
        }

        case "timeout": {
          // Simulate timeout by aborting with timedout error
          await route.abort("timedout");
          break;
        }

        case "serverError": {
          await route.fulfill({
            status: 500,
            contentType: "application/json",
            body: JSON.stringify({
              detail: "Error interno del servidor.",
              code: "INTERNAL_SERVER_ERROR",
            }),
          });
          break;
        }

        case "gatewayTimeout": {
          await route.fulfill({
            status: 504,
            contentType: "application/json",
            body: JSON.stringify({
              detail: "El servidor no respondió a tiempo.",
              code: "GATEWAY_TIMEOUT",
            }),
          });
          break;
        }

        case "serviceUnavailable": {
          await route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({
              detail:
                "El servicio no está disponible en este momento. Intenta en unos momentos.",
              code: "SERVICE_UNAVAILABLE",
            }),
          });
          break;
        }

        default: {
          await route.continue();
        }
      }
    });
  }
}

// ---------------------------------------------------------------------------
// simulateOfflineMode — abort ALL marca API calls (reads + writes)
// Used to test complete offline behavior + error boundary display
// ---------------------------------------------------------------------------

export async function simulateOfflineMode(page: Page): Promise<void> {
  await page.route("**/api/v1/lisa/marca/**", async (route: Route) => {
    await route.abort("connectionreset");
  });
}

// ---------------------------------------------------------------------------
// restoreNetworkForEndpoint — remove failure route and resume normal mocks
// Use after verifying error state to test recovery
// ---------------------------------------------------------------------------

export async function restoreNetworkForEndpoint(
  page: Page,
  endpoint: MarcaEndpoint = "identity",
): Promise<void> {
  const pattern = getEndpointPattern(endpoint);
  const patterns = Array.isArray(pattern) ? pattern : [pattern];
  for (const p of patterns) {
    await page.unroute(p);
  }
}

// ---------------------------------------------------------------------------
// simulateFlakyNetwork — first N calls fail, then succeed
// Models intermittent connectivity (SC-7 retry behavior test)
// ---------------------------------------------------------------------------

export async function simulateFlakyNetwork(
  page: Page,
  endpoint: MarcaEndpoint,
  failFirstN: number = 2,
  successBody: object = { updatedAt: new Date().toISOString() },
): Promise<void> {
  let callCount = 0;
  const pattern = getEndpointPattern(endpoint);
  const patterns = Array.isArray(pattern) ? pattern : [pattern];

  for (const p of patterns) {
    await page.route(p, async (route: Route) => {
      const method = route.request().method();
      if (!["PATCH", "POST", "DELETE"].includes(method)) {
        // Reads delegate to the real-backend forwarding fixture (RN-1).
        await route.fallback();
        return;
      }

      callCount++;
      if (callCount <= failFirstN) {
        await route.abort("connectionreset");
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(successBody),
        });
      }
    });
  }
}

// ---------------------------------------------------------------------------
// buildNetworkFailureInfo — helper to extract failure info for assertions
// ---------------------------------------------------------------------------

export function buildNetworkFailureInfo(mode: NetworkFailureMode) {
  const statusMap: Record<NetworkFailureMode, number | null> = {
    abort: null,
    timeout: null,
    serverError: 500,
    gatewayTimeout: 504,
    serviceUnavailable: 503,
  };

  const messageMap: Record<NetworkFailureMode, string> = {
    abort: "Error de conexión al guardar los cambios.",
    timeout: "La solicitud tardó demasiado. Verifica tu conexión.",
    serverError: "Error interno del servidor.",
    gatewayTimeout: "El servidor no respondió a tiempo.",
    serviceUnavailable:
      "El servicio no está disponible en este momento. Intenta en unos momentos.",
  };

  return {
    status: statusMap[mode],
    expectedErrorMessage: messageMap[mode],
    isAbort: mode === "abort" || mode === "timeout",
  };
}
