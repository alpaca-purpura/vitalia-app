/**
 * Architecture test — no middleware.ts in repo (Next.js 16 canonical).
 *
 * Next.js 16 deprecates `middleware.ts` and uses `proxy.ts` instead.
 * This ratchet test ensures we NEVER accidentally create a `middleware.ts`
 * file going forward (would break or conflict with the canonical `proxy.ts`).
 *
 * AC-15: NO middleware.ts in vitalia/frontend/src/ — only proxy.ts exists.
 *
 * spec_anchor: 03-arch-fe.md § 2.2 MODIFY proxy.ts + 06-tickets.yaml T-3
 * downstream-regression-na: brand-local arch test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { existsSync } from "fs";
import { resolve, join } from "path";
import { readdirSync, statSync } from "fs";

const ROOT = resolve(__dirname, "../../..");
const SRC = join(ROOT, "src");

function findMiddlewareTsFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const found: string[] = [];

  const recurse = (current: string) => {
    let entries: string[];
    try {
      entries = readdirSync(current);
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = join(current, entry);
      let stat: ReturnType<typeof statSync>;
      try {
        stat = statSync(full);
      } catch {
        continue;
      }
      if (stat.isDirectory()) {
        if (entry === "node_modules" || entry === ".next") continue;
        recurse(full);
      } else if (entry === "middleware.ts" || entry === "middleware.js") {
        found.push(full);
      }
    }
  };

  recurse(dir);
  return found;
}

describe("Vitalia FE — no middleware.ts (Next.js 16 uses proxy.ts)", () => {
  it("middleware.ts MUST NOT exist anywhere in src/", () => {
    const found = findMiddlewareTsFiles(SRC);

    expect(
      found,
      [
        "middleware.ts detected — Next.js 16 uses proxy.ts instead.",
        "",
        "Next.js 16 deprecated the middleware.ts file convention in favour of",
        "proxy.ts (same location: src/proxy.ts). Any middleware.ts file in the",
        "repo will conflict with or duplicate the canonical proxy.ts.",
        "",
        "To fix: rename middleware.ts → proxy.ts and update the export name",
        "from 'middleware' to 'proxy'. Clerk SDK clerkMiddleware() is unchanged.",
        "",
        "Offending files:",
        ...found,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("proxy.ts MUST exist in src/", () => {
    const proxyPath = join(SRC, "proxy.ts");
    expect(
      existsSync(proxyPath),
      "src/proxy.ts not found — this is the canonical Next.js 16 routing file. " +
        "Create src/proxy.ts with clerkMiddleware() as per 03-arch-fe.md § 2.2.",
    ).toBe(true);
  });
});
