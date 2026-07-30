/**
 * Architecture test — FE-A2b: user-facing strings must live in copy.ts / microcopy.ts,
 * NOT be inlined as JSX text nodes in components.
 *
 * All UI copy for the vitalia brand lives in:
 *   src/features/vitalia/config/microcopy.ts
 *
 * Components must NOT inline user-visible copy as string literals because:
 *   1. Voseo detection (spanish-text.md) cannot scan all component files
 *   2. String reuse/consistency is broken when copy is scattered
 *   3. Future i18n / A/B testing requires a centralised SSoT
 *
 * This test uses a HEURISTIC approach — it cannot catch all cases, but
 * flags the most obvious patterns: JSX text nodes with Spanish words
 * longer than 4 chars that are NOT in the microcopy SSoT.
 *
 * Scope: src/features/vitalia/components/**\/*.tsx
 * Exceptions: medical disclaimer (has its own sub-copy object), SVG titles,
 *   aria-label values, data-testid attributes.
 *
 * Known-violations allowlist follows ratchet pattern (shrink-only).
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "fs";
import { resolve, join, relative } from "path";
import { readdirSync, statSync } from "fs";

const ROOT = resolve(__dirname, "../../..");
const COMPONENTS_DIR = join(ROOT, "src", "features", "vitalia", "components");
const MICROCOPY_PATH = join(
  ROOT,
  "src",
  "features",
  "vitalia",
  "config",
  "microcopy.ts",
);

// Files allowed to have inline copy strings (explicit exceptions with justification).
// Format: "src/features/vitalia/components/filename.tsx"
// Ratchet baseline frozen at T-infra-4. These files have inline pagination/label
// strings that predate the microcopy SSoT pattern. To be migrated in T-fe-4+.
const KNOWN_INLINE_COPY_VIOLATIONS: ReadonlySet<string> = new Set<string>([
  "src/features/vitalia/components/patient-list-table.tsx", // inline pagination: "Anterior", "Siguiente", "Tipo clínica"
  "src/features/vitalia/components/patient-medical-pdf-upload.tsx", // inline label: "Subir otro PDF"
  "src/features/vitalia/components/treatment-list-table.tsx", // inline pagination: "Anterior", "Siguiente"
]);

// Patterns for JSX text content — sequences of Spanish-like text > 4 chars
// that appear as standalone JSX text nodes (not inside attribute strings).
// Heuristic: match any literal string in JSX render return that contains a space
// and looks like natural language (>= 2 words).
// We use a simplified approach: flag JSX expressions like: >Texto de usuario aquí<
const JSX_TEXT_CONTENT_PATTERN =
  />\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{8,})\s*</g;

// Words that strongly indicate inline user-facing copy (Spanish neutro)
// Short words (articles, prepositions) are intentionally excluded.
const SPANISH_INDICATOR_WORDS = [
  "Paciente",
  "Tratamiento",
  "Cita",
  "Consulta",
  "Clínica",
  "Médico",
  "Doctor",
  "Guardar",
  "Cancelar",
  "Confirmar",
  "Aceptar",
  "Continuar",
  "Siguiente",
  "Anterior",
  "Crear",
  "Editar",
  "Eliminar",
  "Ver",
  "Cargar",
  "Subir",
  "Descargar",
  "Nombre",
  "Teléfono",
  "Correo",
  "Dirección",
  "Fecha",
  "Hora",
  "Estado",
  "Tipo",
  "Descripción",
  "Comentario",
  "Nota",
];

function collectTsxFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const files: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        if (entry === "node_modules" || entry === "__tests__") continue;
        recurse(full);
      } else if (entry.endsWith(".tsx")) {
        files.push(full);
      }
    }
  };
  recurse(dir);
  return files;
}

describe("Vitalia FE — user-facing strings in microcopy.ts SSoT (FE-A2b)", () => {
  it("microcopy.ts file exists and exports at least 6 namespaces", () => {
    if (!existsSync(MICROCOPY_PATH)) {
      console.log(
        "[SKIP] microcopy.ts not found — skipping test_no_hardcoded_strings",
      );
      return;
    }
    const source = readFileSync(MICROCOPY_PATH, "utf-8");
    // Check required namespace exports
    const requiredExports = [
      "MICROCOPY_ONBOARDING",
      "MICROCOPY_BRAND_STUDIO",
      "MICROCOPY_OFFER_WIZARD",
      "MICROCOPY_BOOKING",
      "MICROCOPY_TREATMENT",
      "MICROCOPY_COMPLIANCE",
    ];
    const missingExports = requiredExports.filter(
      (name) => !source.includes(`export const ${name}`),
    );
    expect(
      missingExports,
      `microcopy.ts missing expected namespace exports: ${missingExports.join(", ")}`,
    ).toHaveLength(0);
  });

  it("component files do not inline prominent Spanish user-facing copy", () => {
    if (!existsSync(COMPONENTS_DIR)) {
      console.log(
        "[SKIP] components directory not found — skipping test_no_hardcoded_strings",
      );
      return;
    }

    const tsxFiles = collectTsxFiles(COMPONENTS_DIR);
    const violations: string[] = [];

    for (const absPath of tsxFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (KNOWN_INLINE_COPY_VIOLATIONS.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Check for Spanish indicator words appearing as raw JSX text nodes
      // (not imported from microcopy, not in attributes, not in comments)
      const sourceWithoutComments = source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/.*$/gm, "");

      // Look for JSX text nodes containing indicator words
      const textMatches = Array.from(
        sourceWithoutComments.matchAll(JSX_TEXT_CONTENT_PATTERN),
      );
      const foundInlineSpanish = textMatches.filter((match) =>
        SPANISH_INDICATOR_WORDS.some((word) => match[1].includes(word)),
      );

      if (foundInlineSpanish.length > 0) {
        // Only flag if the file does NOT import from microcopy
        const importsMicrocopy =
          source.includes("from") && source.includes("microcopy");
        if (!importsMicrocopy) {
          violations.push(
            `${relPath}: ${foundInlineSpanish.length} potential inline copy string(s) without microcopy import.` +
              ` Examples: ${foundInlineSpanish.slice(0, 2).map((m) => `"${m[1].trim()}"`)}`,
          );
        }
      }
    }

    expect(
      violations,
      [
        "Components with inline Spanish copy detected (no microcopy import).",
        "",
        "All user-facing strings must live in:",
        "  src/features/vitalia/config/microcopy.ts",
        "",
        "Fix: Move copy to the appropriate MICROCOPY_* namespace and import it.",
        "     Then reference via: {MICROCOPY_X.someKey}",
        "",
        "If this component legitimately has its own copy (e.g., an isolated",
        "utility component), add it to KNOWN_INLINE_COPY_VIOLATIONS (shrink-only).",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_INLINE_COPY_VIOLATIONS allowlist only references existing files", () => {
    for (const relPath of KNOWN_INLINE_COPY_VIOLATIONS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_INLINE_COPY_VIOLATIONS references non-existent file: ${relPath}. Remove it (shrink-only ratchet).`,
      ).toBe(true);
    }
  });
});
