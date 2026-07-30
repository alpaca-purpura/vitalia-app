/**
 * Architecture test — no (dashboard)/ or (app)/ route groups in repo.
 *
 * Chris dictum 2026-05-25: no legacy en pre-prod. app/(dashboard)/** and
 * app/(app)/** must be deleted as part of F1-S9 (T-5 legacy cleanup).
 *
 * This ratchet test ensures we NEVER accidentally re-create legacy route
 * groups. It will be RED while (dashboard)/ still exists (T-4 phase) and
 * GREEN after T-5 deletes them.
 *
 * AC-T4: NO app/(dashboard)/ or app/(app)/ in vitalia/frontend/src/app/
 *
 * spec_anchor: 03-arch-fe.md § 2.3 DELETE + 04-validators.yaml arch-no-dashboard-route-group
 * downstream-regression-na: brand-local arch test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { existsSync } from "fs";
import { join, resolve } from "path";

const ROOT = resolve(__dirname, "../../..");
const APP_DIR = join(ROOT, "src", "app");

describe("Vitalia FE — no legacy route groups (dashboard)/(app)", () => {
  it("app/(dashboard)/ MUST NOT exist — legacy route group deleted per F1-S9 T-5", () => {
    const dashboardPath = join(APP_DIR, "(dashboard)");
    const exists = existsSync(dashboardPath);

    expect(
      exists,
      [
        "app/(dashboard)/ detected — this legacy route group must be deleted.",
        "",
        "Chris dictum 2026-05-25: 'no legacy en pre-prod'. The (dashboard) route",
        "group was built before the shell-organism architecture (F1-S0..F1-S8).",
        "Post-F1-S9 merge, all FE functionality moves to app/[tenantId]/(shell-organism)/.",
        "",
        "To fix: run `rm -rf vitalia/frontend/src/app/(dashboard)/` as part of T-5 cleanup.",
        "Then update 6 capability YAMLs to strip (dashboard) from package_path.",
        "",
        "Offending path: " + dashboardPath,
      ].join("\n"),
    ).toBe(false);
  });

  it("app/(app)/ MUST NOT exist — legacy route group deleted per F1-S9 T-5", () => {
    const appGroupPath = join(APP_DIR, "(app)");
    const exists = existsSync(appGroupPath);

    expect(
      exists,
      [
        "app/(app)/ detected — this legacy route group must be deleted.",
        "",
        "Chris dictum 2026-05-25: 'no legacy en pre-prod'. The (app) route group",
        "contained a single inbox/ sub-route that is superseded by the shell-organism.",
        "",
        "To fix: run `rm -rf vitalia/frontend/src/app/(app)/` as part of T-5 cleanup.",
        "",
        "Offending path: " + appGroupPath,
      ].join("\n"),
    ).toBe(false);
  });

  it("app/[tenantId]/(shell-organism)/ MUST exist — canonical shell route group", () => {
    const shellPath = join(APP_DIR, "[tenantId]", "(shell-organism)");
    expect(
      existsSync(shellPath),
      "app/[tenantId]/(shell-organism)/ not found — " +
        "this is the canonical shell route group (created by F1-S4). " +
        "It must exist post-F1-S9.",
    ).toBe(true);
  });
});
