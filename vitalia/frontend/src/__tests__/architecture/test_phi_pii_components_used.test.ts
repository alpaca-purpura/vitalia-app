/**
 * Architecture test — FE-A6: PHI/PII field names in JSX must be wrapped in
 * PiiMaskedSpan or RequireRole components (HIPAA-lite FE enforcement).
 *
 * Per vitalia/.claude/rules/hipaa-lite.md:
 *   - PHI fields must not be rendered naked in components.
 *   - Sensitive fields (patient.name, patient.dni, diagnosis, etc.) must be
 *     wrapped in `<PiiMaskedSpan>` (masks value unless role permits) or
 *     `<RequireRole roles={["doctor","nurse","admin_clinic"]}>`.
 *
 * This test uses a HEURISTIC approach: it scans TSX files for access patterns
 * referencing known PHI field names as JSX expressions AND flags files that
 * render them WITHOUT using PiiMaskedSpan/RequireRole wrappers.
 *
 * PHI fields (canonical list per hipaa-lite.md):
 *   patient.name, patient.dni, patient.cuit, patient.date_of_birth,
 *   patient.phone, patient.email, patient.address,
 *   diagnosis, treatment_plan, medication, dosage, allergies,
 *   symptoms, medical_notes, lab_results, vital_signs,
 *   imaging_url, xray_filename, ultrasound_report,
 *   previous_treatments, family_history, surgical_history
 *
 * Note: PiiMaskedSpan and RequireRole components will be created in T-infra-7.
 * Until then, this test auto-skips when those components don't exist.
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
const SRC = join(ROOT, "src");
const PHI_COMPONENT_PATHS = [
  join(SRC, "components", "shared", "phi", "PiiMaskedSpan.tsx"),
  join(SRC, "components", "shared", "phi", "RequireRole.tsx"),
];

// PHI field identifier patterns (from hipaa-lite.md + phi_fields.py).
// These represent field names that should be wrapped when rendered in JSX.
const PHI_FIELD_PATTERNS = [
  // Patient identity fields
  /patient\??\.(name|dni|cuit|date_of_birth|phone|email|address)\b/g,
  // Clinical fields (standalone access patterns)
  /\bdiagnosis\b/g,
  /\btreatment_plan\b/g,
  /\bmedication\b/g,
  /\bdosage\b/g,
  /\ballergies\b/g,
  /\bsymptoms\b/g,
  /\bmedical_notes\b/g,
  /\blab_results\b/g,
  /\bvital_signs\b/g,
  // Imaging
  /\bimaging_url\b/g,
  /\bxray_filename\b/g,
  /\bultrasound_report\b/g,
  // History
  /\bprevious_treatments\b/g,
  /\bfamily_history\b/g,
  /\bsurgical_history\b/g,
];

// Wrapper patterns that indicate proper PHI protection.
const PHI_WRAPPER_PATTERNS = [/PiiMaskedSpan/, /RequireRole/, /AuditedSection/];

// Ratchet baseline — known violations at T-infra-4 creation (shrink-only).
// These files are known to render PHI before T-infra-7 wrappers are implemented.
// They will be cleaned up when T-infra-7 ships.
const KNOWN_PHI_WRAPPER_VIOLATIONS: ReadonlySet<string> = new Set<string>([
  // T-infra-7 populates PiiMaskedSpan/RequireRole. These components will be
  // wrapped after T-infra-7 is done. Baseline allows current PHI-rendering
  // components to proceed without wrapper (they mask at BE level currently).
  "src/features/vitalia/components/patient-detail-panel.tsx",
  "src/features/vitalia/components/patient-list-table.tsx",
  "src/features/vitalia/components/treatment-list-table.tsx",
  "src/features/vitalia/components/treatment-timeline.tsx",
  "src/features/vitalia/components/patient-medical-pdf-upload.tsx",
  // vitalia-fase2-adrian-embudo (U1): FrozenLeadRow renderiza `diagnosis` de
  // DiagnoseResponse {recommendation, suggestedAction} — el diagnóstico COMERCIAL
  // de Adrián (por qué el lead se enfrió + qué acción tomar), NO un diagnóstico
  // clínico de paciente. El scanner FE-A6 matchea el nombre de campo `diagnosis`
  // (que SÍ es PHI clínico en otro contexto), pero acá es lead non_phi (marketing).
  // Justificado: no se enmascara consejo de reactivación que el vendedor debe leer.
  // (Antes pasaba por el import de PiiMaskedSpan en el componente; U1 lo removió del
  // nombre del prospecto — non_phi — exponiendo este match de campo.)
  "src/features/adrian/components/recuperar/FrozenLeadRow.tsx",
]);

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

function containsPhiFieldAccess(source: string): string[] {
  const foundFields: string[] = [];
  // Strip comments first
  const stripped = source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/.*$/gm, "");

  for (const pattern of PHI_FIELD_PATTERNS) {
    pattern.lastIndex = 0;
    const match = pattern.exec(stripped);
    if (match) {
      foundFields.push(match[0]);
    }
  }
  return foundFields;
}

function hasPhiWrappers(source: string): boolean {
  return PHI_WRAPPER_PATTERNS.some((p) => p.test(source));
}

describe("Vitalia FE — PHI fields must be wrapped in PiiMaskedSpan/RequireRole (FE-A6)", () => {
  it("auto-skip when PiiMaskedSpan/RequireRole components don't exist yet", () => {
    // If T-infra-7 hasn't shipped yet, the wrapper components don't exist.
    // We verify their existence — if absent, the CHECK gate is advisory only.
    const wrappersExist = PHI_COMPONENT_PATHS.some((p) => existsSync(p));
    if (!wrappersExist) {
      console.log(
        "[ADVISORY] PiiMaskedSpan/RequireRole components not found (T-infra-7 pending). " +
          "PHI wrapping enforcement will be REQUIRED after T-infra-7 ships.",
      );
      // Advisory only — not a hard fail until wrappers exist
      expect(true).toBe(true);
      return;
    }
  });

  it("components with PHI field access use PiiMaskedSpan or RequireRole wrapper", () => {
    if (!existsSync(SRC)) {
      console.log(
        "[SKIP] src/ directory not found — skipping test_phi_pii_components_used",
      );
      return;
    }

    // Check if wrappers exist (T-infra-7). If not, advisory only.
    const wrappersExist = PHI_COMPONENT_PATHS.some((p) => existsSync(p));
    if (!wrappersExist) {
      console.log(
        "[SKIP] PiiMaskedSpan/RequireRole not yet created (T-infra-7 pending)",
      );
      return;
    }

    const tsxFiles = collectTsxFiles(SRC);
    const violations: string[] = [];

    for (const absPath of tsxFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (KNOWN_PHI_WRAPPER_VIOLATIONS.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");
      const phiFields = containsPhiFieldAccess(source);
      if (phiFields.length === 0) continue;

      // File accesses PHI fields — check it also uses wrappers
      if (!hasPhiWrappers(source)) {
        violations.push(
          `${relPath}: accesses PHI fields [${phiFields.slice(0, 3).join(", ")}${phiFields.length > 3 ? "..." : ""}] ` +
            `without PiiMaskedSpan/RequireRole wrapper`,
        );
      }
    }

    expect(
      violations,
      [
        "Components rendering PHI fields without HIPAA-lite wrappers detected.",
        "",
        "Per vitalia/.claude/rules/hipaa-lite.md, PHI field values rendered in JSX",
        "MUST be wrapped in PiiMaskedSpan or RequireRole components.",
        "",
        "Fix:",
        "  import { PiiMaskedSpan } from '@/components/shared/phi/PiiMaskedSpan';",
        "  <PiiMaskedSpan value={patient.name} />",
        "",
        "  OR for role-gated sections:",
        "  import { RequireRole } from '@/components/shared/phi/RequireRole';",
        "  <RequireRole roles={['doctor', 'nurse', 'admin_clinic']}>",
        "    {patient.diagnosis}",
        "  </RequireRole>",
        "",
        "If masking is handled at the BE level (not FE), add to",
        "KNOWN_PHI_WRAPPER_VIOLATIONS (shrink-only ratchet) with justification.",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_PHI_WRAPPER_VIOLATIONS allowlist only references existing files", () => {
    for (const relPath of KNOWN_PHI_WRAPPER_VIOLATIONS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_PHI_WRAPPER_VIOLATIONS references non-existent file: ${relPath}. Remove it (shrink-only ratchet).`,
      ).toBe(true);
    }
  });
});
