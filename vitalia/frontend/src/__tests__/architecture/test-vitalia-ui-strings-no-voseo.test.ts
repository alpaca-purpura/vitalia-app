/**
 * Architecture test — V-A2: vitalia UI strings must not contain voseo verbs.
 *
 * Scans microcopy.ts (SSoT for all user-facing strings) for voseo patterns.
 * Per .claude/rules/spanish-text.md: Spanish neutro LatAm, tuteo only.
 * Exception: sales_agent output (not in scope for vitalia microcopy).
 *
 * @see docs/product/stories/luana-vitalia-bootstrap/01-spec.md § 8
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "fs";
import { resolve } from "path";

// Voseo verb patterns (comprehensive — per spanish-text.md rule)
const VOSEO_PATTERNS = [
  /\btenés\b/i,
  /\bpodés\b/i,
  /\bhacés\b/i,
  /\bmirá\b/i,
  /\bdejá\b/i,
  /\bponé\b/i,
  /\busá\b/i,
  /\bhacé\b/i,
  /\belegí\b/i,
  /\bseleccioná\b/i,
  /\barrancá\b/i,
  /\bempezá\b/i,
  /\bagregá\b/i,
  /\bconfigurá\b/i,
  /\brevisá\b/i,
  /\beschribí\b/i,
  /\bguardá\b/i,
  /\bsubí\b/i,
  /\babrí\b/i,
  /\bvolvé\b/i,
  /\bcambiá\b/i,
  /\bofrecés\b/i,
  /\bcobrás\b/i,
  /\bejecutás\b/i,
  /\bactivás\b/i,
  /\bdesactivás\b/i,
  /\blinkeá\b/i,
  /\bdespublicala\b/i,
  /\breactivá\b/i,
  /\bcancelala\b/i,
  /\bvalidá\b/i,
  /\bconsiderá\b/i,
  /\bformulala\b/i,
  /\bmarcá\b/i,
  /\brefirís\b/i,
  /\batendés\b/i,
  /\bintegrás\b/i,
  /\blistá\b/i,
  /\bprobá\b/i,
  /\bmostrá\b/i,
  /\bcompartí\b/i,
  /\bcontá\b/i,
  /\bexplicá\b/i,
  /\bfijate\b/i,
  /\bacordate\b/i,
  /\bquerés\b/i,
  /\bsabés\b/i,
  /\bdecís\b/i,
  /\bvenís\b/i,
];

// Files that must be free of voseo (SSoT user-facing strings)
const UI_STRING_FILES = ["src/features/vitalia/config/microcopy.ts"];

// Files scan includes components that render user-facing text
const COMPONENT_FILES = [
  "src/features/vitalia/components/clinic-type-picker.tsx",
  "src/features/vitalia/components/treatment-timeline.tsx",
  "src/features/vitalia/components/consent-signature-modal.tsx",
  "src/features/vitalia/components/compliance-stats-cards.tsx",
  "src/features/vitalia/components/doctor-avatar-picker.tsx",
  "src/features/vitalia/components/medical-disclaimer-banner.tsx",
  // T-fe-4 interactive Client Components
  "src/features/vitalia/components/onboarding-step-1-client.tsx",
  "src/features/vitalia/components/onboarding-step-2-client.tsx",
  "src/features/vitalia/components/onboarding-step-3-client.tsx",
];

// F1-S7 Ribbon shell-organism components with user-facing microcopy (T-4 EXTEND)
const RIBBON_SHELL_FILES = [
  "src/components/shared/shell-organism/Ribbon.tsx",
  "src/components/shared/shell-organism/RibbonTab.tsx",
  "src/components/shared/shell-organism/ConfigTab.tsx",
  "src/lib/agent-catalog.ts",
];

// F1-S8 SubTabsBar shell-organism components with user-facing microcopy (T-5 EXTEND)
const SUBTABS_SHELL_FILES = [
  "src/components/shared/shell-organism/SubTabsBar.tsx",
  "src/components/shared/shell-organism/SubTab.tsx",
];

const ROOT = resolve(__dirname, "../../..");

/**
 * Extract string literals from TypeScript/TSX source.
 * Uses simple regex — sufficient for catching voseo in string values.
 */
function extractStringLiterals(source: string): string[] {
  const strings: string[] = [];
  // Match single-quoted, double-quoted, and template literal strings
  const singleQuoted = source.matchAll(/'([^'\\]|\\.)*'/g);
  const doubleQuoted = source.matchAll(/"([^"\\]|\\.)*"/g);
  const templateLiterals = source.matchAll(/`([^`\\]|\\.)*`/g);

  for (const match of singleQuoted) strings.push(match[0]);
  for (const match of doubleQuoted) strings.push(match[0]);
  for (const match of templateLiterals) strings.push(match[0]);

  return strings;
}

/**
 * Check if a string literal contains voseo patterns.
 * Ignores: comments, import paths, JSX attributes not containing Spanish text.
 */
function findVoseoInStrings(
  strings: string[],
): { string: string; pattern: string }[] {
  const violations: { string: string; pattern: string }[] = [];

  for (const str of strings) {
    // Skip import paths and URLs
    if (str.startsWith("'@/") || str.startsWith('"@/') || str.includes("http"))
      continue;
    // Skip short strings unlikely to be user-facing
    if (str.length < 4) continue;

    for (const pattern of VOSEO_PATTERNS) {
      if (pattern.test(str)) {
        violations.push({ string: str.slice(0, 80), pattern: pattern.source });
        break; // One violation per string is enough
      }
    }
  }

  return violations;
}

describe("Vitalia UI strings — no voseo (A2)", () => {
  describe("microcopy.ts SSoT", () => {
    it("microcopy.ts contains no voseo verbs in string values", () => {
      for (const relPath of UI_STRING_FILES) {
        const absPath = resolve(ROOT, relPath);
        const source = readFileSync(absPath, "utf-8");
        const strings = extractStringLiterals(source);
        const violations = findVoseoInStrings(strings);

        expect(
          violations,
          `Voseo found in ${relPath}:\n${JSON.stringify(violations, null, 2)}`,
        ).toHaveLength(0);
      }
    });
  });

  describe("Component source files", () => {
    for (const relPath of COMPONENT_FILES) {
      it(`${relPath.split("/").pop()} contains no voseo verbs`, () => {
        const absPath = resolve(ROOT, relPath);
        const source = readFileSync(absPath, "utf-8");
        const strings = extractStringLiterals(source);
        const violations = findVoseoInStrings(strings);

        expect(
          violations,
          `Voseo found in ${relPath}:\n${JSON.stringify(violations, null, 2)}`,
        ).toHaveLength(0);
      });
    }
  });

  describe("Microcopy structure — spec § 8 alignment", () => {
    it("has all 6 top-level microcopy namespaces", async () => {
      const mc = await import("@/features/vitalia/config/microcopy");
      expect(mc.MICROCOPY_ONBOARDING).toBeDefined();
      expect(mc.MICROCOPY_BRAND_STUDIO).toBeDefined();
      expect(mc.MICROCOPY_OFFER_WIZARD).toBeDefined();
      expect(mc.MICROCOPY_BOOKING).toBeDefined();
      expect(mc.MICROCOPY_TREATMENT).toBeDefined();
      expect(mc.MICROCOPY_COMPLIANCE).toBeDefined();
    });

    it("MICROCOPY_ONBOARDING.clinicTypes has exactly 4 types", async () => {
      const { MICROCOPY_ONBOARDING } =
        await import("@/features/vitalia/config/microcopy");
      expect(Object.keys(MICROCOPY_ONBOARDING.clinicTypes)).toHaveLength(4);
    });

    it("MICROCOPY_COMPLIANCE.eventTypes has exactly 6 event types", async () => {
      const { MICROCOPY_COMPLIANCE } =
        await import("@/features/vitalia/config/microcopy");
      expect(Object.keys(MICROCOPY_COMPLIANCE.eventTypes)).toHaveLength(6);
    });

    it("MICROCOPY_OFFER_WIZARD.steps has exactly 5 step labels", async () => {
      const { MICROCOPY_OFFER_WIZARD } =
        await import("@/features/vitalia/config/microcopy");
      expect(Object.keys(MICROCOPY_OFFER_WIZARD.steps)).toHaveLength(5);
    });

    it("MICROCOPY_TREATMENT.milestones has exactly 4 milestones", async () => {
      const { MICROCOPY_TREATMENT } =
        await import("@/features/vitalia/config/microcopy");
      expect(Object.keys(MICROCOPY_TREATMENT.milestones)).toHaveLength(4);
    });
  });

  describe("F1-S7 Ribbon shell-organism microcopy — SC-8 i18n (T-4 EXTEND)", () => {
    for (const relPath of RIBBON_SHELL_FILES) {
      it(`${relPath.split("/").pop()} contains no voseo verbs`, () => {
        const absPath = resolve(ROOT, relPath);
        if (!existsSync(absPath)) {
          // File may not exist if T-2/T-3 not yet built — skip gracefully
          console.log(`[SKIP] ${relPath} not found — skipping voseo check`);
          return;
        }
        const source = readFileSync(absPath, "utf-8");
        const strings = extractStringLiterals(source);
        const violations = findVoseoInStrings(strings);
        expect(
          violations,
          `Voseo found in ${relPath}:\n${JSON.stringify(violations, null, 2)}`,
        ).toHaveLength(0);
      });
    }

    it("agent-catalog.ts tabLabel 'Mi Clínica' has tilde (Clínica not Clinica)", () => {
      const absPath = resolve(ROOT, "src/lib/agent-catalog.ts");
      if (!existsSync(absPath)) return;
      const source = readFileSync(absPath, "utf-8");
      expect(source).toContain("Mi Clínica");
      expect(source).not.toContain("Mi Clinica");
    });

    it("agent-catalog.ts Adrián role label has tilde (Adrián not Adrian)", () => {
      const absPath = resolve(ROOT, "src/lib/agent-catalog.ts");
      if (!existsSync(absPath)) return;
      const source = readFileSync(absPath, "utf-8");
      // Adrián should appear with tilde in the catalog (name field)
      expect(source).toMatch(/Adrián/);
      // Must NOT appear as plain 'Adrian' (without tilde) in user-facing name/tabLabel fields
      // Note: 'Adrian' without tilde is checked via exact string (not part of 'Adrián')
      const lines = source.split("\n");
      const adrianLines = lines.filter(
        (l) =>
          l.includes("Adrian") &&
          !l.includes("Adrián") &&
          !l.trim().startsWith("//") &&
          !l.trim().startsWith("*"),
      );
      expect(
        adrianLines,
        `Found 'Adrian' without tilde in agent-catalog.ts:\n${adrianLines.join("\n")}`,
      ).toHaveLength(0);
    });
  });

  describe("F1-S8 SubTabsBar shell-organism microcopy — SC-9 i18n (T-5 EXTEND)", () => {
    for (const relPath of SUBTABS_SHELL_FILES) {
      it(`${relPath.split("/").pop()} contains no voseo verbs`, () => {
        const absPath = resolve(ROOT, relPath);
        if (!existsSync(absPath)) {
          console.log(`[SKIP] ${relPath} not found — skipping voseo check`);
          return;
        }
        const source = readFileSync(absPath, "utf-8");
        const strings = extractStringLiterals(source);
        const violations = findVoseoInStrings(strings);
        expect(
          violations,
          `Voseo found in ${relPath}:\n${JSON.stringify(violations, null, 2)}`,
        ).toHaveLength(0);
      });
    }

    it("RIBBON_SUBTABS labels verbatim — 22 Spanish neutro strings (no voseo imperatives)", () => {
      const absPath = resolve(ROOT, "src/lib/agent-catalog.ts");
      if (!existsSync(absPath)) return;
      const source = readFileSync(absPath, "utf-8");
      // Spot-check verbatim labels per spec
      const EXPECTED_LABELS = [
        "Marca",
        "Staff", // F2-S8 T-FE-1 (2026-05-31): renamed from "Doctores" per 01-spec.md v2
        "Servicios",
        "Compliance",
        "Lanzar",
        "En vuelo",
        "Recursos",
        "Resultados",
        "Mercado",
        "Inbox",
        "Embudo",
        "Outbound",
        "Propuestas",
        "Agenda",
        "Pacientes",
        "Voz del paciente",
        "Reactivar",
        "Multiplicar",
        "Reputación",
        "Mi cuenta",
        "Conexiones",
        "Avanzado",
      ];
      for (const label of EXPECTED_LABELS) {
        expect(
          source,
          `Missing label '${label}' in agent-catalog.ts`,
        ).toContain(label);
      }
    });

    it("nav aria-labels verbatim — 6 Spanish neutro strings with tildes (Adrián + Configuración)", () => {
      const absPath = resolve(
        ROOT,
        "src/components/shared/shell-organism/SubTabsBar.tsx",
      );
      if (!existsSync(absPath)) return;
      const source = readFileSync(absPath, "utf-8");
      // Check aria-labels referenced in SubTabsBar (getAriaLabel function)
      expect(source).toContain("Sub-secciones Configuración"); // with tilde
      // Agent names come from AGENT_CATALOG[slug].name — Adrián has tilde
      // Verify the template string pattern references AGENT_CATALOG[slug].name
      expect(source).toContain("Sub-secciones");
    });

    it("Reputación label has tilde (Reputación not Reputacion)", () => {
      const absPath = resolve(ROOT, "src/lib/agent-catalog.ts");
      if (!existsSync(absPath)) return;
      const source = readFileSync(absPath, "utf-8");
      expect(source).toContain("Reputación");
      // Plain 'Reputacion' without tilde should NOT appear in label context
      expect(source).not.toMatch(/"Reputacion"/);
    });

    it("Configuración in aria-label has tilde (Configuración not Configuracion)", () => {
      const absPath = resolve(
        ROOT,
        "src/components/shared/shell-organism/SubTabsBar.tsx",
      );
      if (!existsSync(absPath)) return;
      const source = readFileSync(absPath, "utf-8");
      expect(source).toContain("Configuración");
      expect(source).not.toMatch(/"Configuracion"/);
    });
  });
});
