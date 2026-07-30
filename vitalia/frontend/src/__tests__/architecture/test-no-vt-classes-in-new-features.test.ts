import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync } from "fs";
import { join } from "path";

/**
 * Arch fitness test — ADR-vitalia-002 § 6
 *
 * Shell-organism new features (F1-S4+) MUST NOT use .vt-* legacy utility
 * classes. New code uses Tailwind direct + semantic tokens (bg-background,
 * text-foreground, bg-agent-lisa, etc.).
 *
 * GREEN by emptiness in F1-S0: shell-organism paths don't exist yet.
 * Created F1-S4 (shell-layout-5050) — test enforces no .vt-* from that point.
 *
 * Ratchet: allowlist shrink-only. Adding to allowlist requires justification.
 */

const SHELL_PATHS = [
  "src/app/[tenantId]/(shell-organism)",
  "src/components/shared/shell-organism",
];

const VT_PATTERN = /\bvt-[a-z]/;

function* walkFiles(dir: string): Generator<string> {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      yield* walkFiles(full);
    } else if (/\.(tsx?|css)$/.test(entry)) {
      yield full;
    }
  }
}

describe("no .vt-* classes in shell-organism new features (ADR-vitalia-002 § 6)", () => {
  it("every file under SHELL_PATHS is free of .vt-* utility classes", () => {
    const root = process.cwd();
    const offenders: string[] = [];

    for (const relPath of SHELL_PATHS) {
      const abs = join(root, relPath);
      let exists = false;
      try {
        statSync(abs);
        exists = true;
      } catch {
        /* path doesnt exist yet — GREEN by emptiness */
      }

      if (!exists) continue;

      for (const f of walkFiles(abs)) {
        const content = readFileSync(f, "utf-8");
        if (VT_PATTERN.test(content)) {
          offenders.push(f);
        }
      }
    }

    expect(offenders).toEqual([]);
  });
});
