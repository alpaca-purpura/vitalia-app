/**
 * Architecture test — semantic Badge tokens (obs#4 vitalia-fase2-mateo-nueva-cita).
 *
 * @luana/ui-kit Badge (core/@luana/ui-kit/src/badge.tsx) has `success` and `warning`
 * variants that emit `bg-success text-success-foreground` / `bg-warning
 * text-warning-foreground`. For those classes to PAINT, vitalia's tailwind.config must
 * define `success` and `warning` color keys (each with DEFAULT + foreground) bound to
 * the CSS vars `--success*` / `--warning*` in globals.css.
 *
 * The gap obs#4 cazó: the variant was applied correctly but the token didn't exist in
 * the brand → `bg-success`/`bg-warning` resolved to nothing → chips rendered as plain
 * text. Unit tests assert the variant is applied (orthogonal to whether the token
 * paints) — this gate closes that hole deterministically.
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";

const TW_CONFIG = resolve(__dirname, "../../../tailwind.config.ts");
const twConfig = readFileSync(TW_CONFIG, "utf8");

const GLOBALS = resolve(__dirname, "../../app/globals.css");
const css = readFileSync(GLOBALS, "utf8");

describe("semantic Badge tokens — @luana/ui-kit success/warning must paint in vitalia", () => {
  for (const key of ["success", "warning"] as const) {
    it(`tailwind.config defines '${key}' color with DEFAULT bound to --${key}`, () => {
      // Matches:  success: { DEFAULT: "hsl(var(--success))", foreground: "hsl(var(--success-foreground))" },
      const re = new RegExp(
        `${key}\\s*:\\s*\\{[^}]*DEFAULT\\s*:\\s*"hsl\\(var\\(--${key}\\)\\)"`,
        "s",
      );
      expect(
        re.test(twConfig),
        `tailwind.config must define '${key}' DEFAULT = hsl(var(--${key})) so bg-${key} from the kit Badge paints`,
      ).toBe(true);
    });

    it(`tailwind.config defines '${key}.foreground' bound to --${key}-foreground`, () => {
      const re = new RegExp(
        `${key}\\s*:\\s*\\{[^}]*foreground\\s*:\\s*"hsl\\(var\\(--${key}-foreground\\)\\)"`,
        "s",
      );
      expect(
        re.test(twConfig),
        `tailwind.config must define '${key}.foreground' = hsl(var(--${key}-foreground)) so text-${key}-foreground paints`,
      ).toBe(true);
    });

    it(`globals.css :root declares --${key} and --${key}-foreground`, () => {
      expect(css, `--${key} must exist in globals.css`).toMatch(
        new RegExp(`--${key}\\s*:`),
      );
      expect(css, `--${key}-foreground must exist in globals.css`).toMatch(
        new RegExp(`--${key}-foreground\\s*:`),
      );
    });
  }
});
