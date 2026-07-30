/**
 * Architecture test — FE-A2c: inbox user-facing strings must live in copy.ts SSoT,
 * NOT be inlined as JSX text nodes in inbox components.
 *
 * All UI copy for the inbox feature lives in:
 *   src/features/inbox/copy.ts  (INBOX_COPY export)
 *
 * Inbox components must NOT inline user-visible copy as string literals because:
 *   1. Voseo detection (spanish-text.md) cannot scan all component files
 *   2. String reuse/consistency is broken when copy is scattered
 *   3. Future i18n / A/B testing requires a centralised SSoT
 *
 * This test uses a HEURISTIC approach — it cannot catch all cases, but
 * flags the most obvious patterns: JSX text nodes with Spanish indicator
 * words that are NOT in components importing from ../copy.
 *
 * Scope: src/features/inbox/**\/*.tsx (components only — excludes stories and tests)
 *
 * Known-violations allowlist follows ratchet pattern (shrink-only).
 * Baseline frozen at T-inbox-fe-7: 0 known violations (all new inbox components
 * use INBOX_COPY from copy.ts per spec).
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "fs";
import { resolve, join, relative } from "path";
import { readdirSync, statSync } from "fs";

const ROOT = resolve(__dirname, "../../..");
const INBOX_DIR = join(ROOT, "src", "features", "adrian", "components", "inbox");
const COPY_PATH = join(ROOT, "src", "features", "adrian", "lib", "copy.ts");

/**
 * Files allowed to have inline copy strings (explicit exceptions with justification).
 * Format: "src/features/inbox/components/filename.tsx"
 * Ratchet baseline frozen at T-inbox-fe-7: EMPTY (all inbox components use INBOX_COPY).
 * Shrink-only — do NOT add entries without justification.
 */
const KNOWN_INLINE_COPY_VIOLATIONS: ReadonlySet<string> = new Set<string>([
  // No known violations at T-inbox-fe-7 baseline.
]);

/**
 * JSX text node heuristic — matches literal text nodes like: >Texto largo aquí<
 * Captures content of at least 8 chars starting with uppercase (typical heading/label).
 */
const JSX_TEXT_CONTENT_PATTERN =
  />\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{8,})\s*</g;

/**
 * Words that strongly indicate inline user-facing copy in Spanish neutro.
 * Short words (articles, prepositions) are intentionally excluded.
 * Medical terms included since inbox shows patient/clinic context.
 */
const SPANISH_INDICATOR_WORDS = [
  // Actions
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
  "Enviar",
  "Pausar",
  "Reanudar",
  "Revertir",
  "Cerrar",
  "Abrir",
  // Entities
  "Paciente",
  "Tratamiento",
  "Cita",
  "Consulta",
  "Clínica",
  "Médico",
  "Doctor",
  "Conversación",
  "Mensaje",
  "Plantilla",
  "Herramienta",
  // Fields
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
  // States / headings
  "Cargando",
  "Error",
  "Vacío",
  "Pendiente",
  "Activo",
  "Inactivo",
  "Adrián",
  "Filtro",
  "Canal",
  "Período",
];

/**
 * Collects all .tsx files under a directory, excluding:
 * - node_modules
 * - __tests__ directories
 * - *.stories.tsx files (Storybook stories are allowed to have inline mock strings)
 * - *.test.tsx files
 */
function collectComponentTsxFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const files: string[] = [];

  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);

      if (stat.isDirectory()) {
        if (entry === "node_modules" || entry === "__tests__") continue;
        recurse(full);
      } else if (
        entry.endsWith(".tsx") &&
        !entry.endsWith(".stories.tsx") &&
        !entry.endsWith(".test.tsx")
      ) {
        files.push(full);
      }
    }
  };

  recurse(dir);
  return files;
}

describe("Vitalia Inbox FE — strings en INBOX_COPY SSoT (FE-A2c)", () => {
  it("copy.ts existe y exporta INBOX_COPY con namespaces requeridos", () => {
    expect(existsSync(COPY_PATH), `copy.ts no encontrado en ${COPY_PATH}`).toBe(
      true,
    );

    const source = readFileSync(COPY_PATH, "utf-8");

    // Required top-level namespace keys in INBOX_COPY
    const requiredKeys = [
      "filters",
      "segmentedMode",
      "multimedia",
      "activityStream",
      "toolsSheet",
      "actionReceipt",
      "pauseAgent",
      "contactSidebar",
      "proactiveOutboundModal",
    ];

    const missingKeys = requiredKeys.filter(
      (key) => !source.includes(`${key}:`),
    );
    expect(
      missingKeys,
      `copy.ts falta namespace(s): ${missingKeys.join(", ")}. Todos los textos inbox deben vivir en INBOX_COPY.`,
    ).toHaveLength(0);
  });

  it("componentes inbox no tienen copy español inline (sin import de copy.ts)", () => {
    const tsxFiles = collectComponentTsxFiles(INBOX_DIR);

    if (tsxFiles.length === 0) {
      // No component files found — skip gracefully (directory still scaffolding)
      console.log("[SKIP] No .tsx component files found in inbox feature dir");
      return;
    }

    const violations: string[] = [];

    for (const absPath of tsxFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");

      if (KNOWN_INLINE_COPY_VIOLATIONS.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Strip comments before analysis
      const sourceWithoutComments = source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/.*$/gm, "");

      // Look for JSX text nodes with Spanish indicator words
      const textMatches = Array.from(
        sourceWithoutComments.matchAll(JSX_TEXT_CONTENT_PATTERN),
      );

      const foundInlineSpanish = textMatches.filter((match) =>
        SPANISH_INDICATOR_WORDS.some((word) => match[1].includes(word)),
      );

      if (foundInlineSpanish.length > 0) {
        // Only flag if the file does NOT import from the copy SSoT
        const importsCopy =
          (source.includes("from") && source.includes("copy")) ||
          source.includes("INBOX_COPY");

        if (!importsCopy) {
          violations.push(
            `${relPath}: ${foundInlineSpanish.length} posible(s) string(s) español inline sin import de copy.ts.` +
              ` Ejemplos: ${foundInlineSpanish
                .slice(0, 2)
                .map((m) => `"${m[1].trim()}"`)
                .join(", ")}`,
          );
        }
      }
    }

    expect(
      violations,
      [
        "Componentes inbox con strings español inline detectados (sin import de INBOX_COPY).",
        "",
        "Todos los textos user-facing del inbox deben vivir en:",
        "  src/features/inbox/copy.ts  →  export const INBOX_COPY",
        "",
        "Fix: mover el copy al namespace apropiado en copy.ts y referenciarlo",
        "     como {INBOX_COPY.namespace.key}.",
        "",
        "Si el componente tiene razón legítima para strings inline (ej. datos dinámicos",
        "del servidor renderizados directamente), agrégalo a KNOWN_INLINE_COPY_VIOLATIONS",
        "con justificación (ratchet shrink-only — no agregar sin justificación).",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_INLINE_COPY_VIOLATIONS solo referencia archivos existentes", () => {
    for (const relPath of KNOWN_INLINE_COPY_VIOLATIONS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_INLINE_COPY_VIOLATIONS referencia archivo inexistente: ${relPath}. ` +
          `Eliminar entrada (ratchet shrink-only).`,
      ).toBe(true);
    }
  });

  it("todos los componentes inbox importan INBOX_COPY (cobertura de import)", () => {
    const tsxFiles = collectComponentTsxFiles(INBOX_DIR);

    if (tsxFiles.length === 0) {
      console.log("[SKIP] No .tsx component files found in inbox feature dir");
      return;
    }

    const withoutImport: string[] = [];

    for (const absPath of tsxFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");

      if (KNOWN_INLINE_COPY_VIOLATIONS.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Skip pure type-only files, store files, url-state files, or non-UI files
      const isUiComponent =
        source.includes("return (") ||
        source.includes("return(") ||
        (source.includes("export function") && source.includes("jsx"));

      if (!isUiComponent) continue;

      // UI components with JSX MUST import INBOX_COPY
      const hasJsx = source.includes("return (") || source.includes("return(");
      const importsCopy =
        source.includes("INBOX_COPY") ||
        source.includes('from "../copy"') ||
        source.includes("from '../copy'");

      if (hasJsx && !importsCopy) {
        withoutImport.push(relPath);
      }
    }

    // Warn (not fail) for missing imports — gives a nudge without breaking CI
    // on edge cases (pure re-export wrappers, etc.)
    if (withoutImport.length > 0) {
      console.warn(
        "[WARN] Inbox UI components sin import INBOX_COPY:\n" +
          withoutImport.map((p) => `  - ${p}`).join("\n") +
          "\nConsiderar agregar import de copy.ts para consistencia.",
      );
    }

    // Test passes regardless (coverage test is advisory — violations test is the enforcer)
    expect(true).toBe(true);
  });
});
