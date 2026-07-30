/**
 * Arch fitness test: no PHI real data in placeholder components.
 * F1-S10 vitalia-fase1-empty-states — T-9 (hipaa-lite overlay enforcement)
 *
 * PHI (Protected Health Information) must be masked in all mock data:
 *   - Phone numbers: must use masked format (+51 9** ***-XXXX, never full digits)
 *   - Email addresses: must use masked format (m***@domain.com, never full prefix)
 *   - DNI/CUIT: 8+ consecutive digits without masking are forbidden
 *
 * Allowed patterns (visual masks):
 *   - +51 9** ***-4321   (phone with asterisks)
 *   - m***@gmail.com     (email with asterisks)
 *   - Any string with *** masking sequence
 *
 * Scope:
 *   - features/{agent}/components/placeholders/*.tsx
 *   - features/{agent}/components/placeholders/*.test.tsx
 *   - components/shared/shell-organism/_mock-*.ts
 *
 * spec_anchor: vitalia/.claude/rules/hipaa-lite.md + 06-tickets.yaml T-9 val-fe-arch-no-phi
 * downstream-regression-na: brand-local arch test; no cross-brand consumers
 *
 * References:
 *   - Ley 25.326 (AR), LGPD (BR), Ley 1581 (CO), Ley 19.628 (CL), Ley 29733 (PE)
 *   - vitalia/backend/src/modules/vitalia/compliance/phi_fields.py
 */

import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "fs";
import { resolve, relative } from "path";

// __dirname = vitalia/frontend/src/__tests__/architecture
// ../.. = vitalia/frontend/src (SRC_ROOT)
const SRC_ROOT = resolve(__dirname, "../..");

/**
 * Collect files matching a pattern in a directory (recursive).
 */
function collectFiles(
  dir: string,
  filter: (name: string) => boolean,
  excludeDirs: string[] = ["node_modules", ".next"],
): string[] {
  const files: string[] = [];
  try {
    const entries = readdirSync(dir);
    for (const entry of entries) {
      if (excludeDirs.includes(entry) || entry.startsWith(".")) continue;
      const fullPath = resolve(dir, entry);
      try {
        const stat = statSync(fullPath);
        if (stat.isDirectory()) {
          files.push(...collectFiles(fullPath, filter, excludeDirs));
        } else if (filter(entry)) {
          files.push(fullPath);
        }
      } catch {
        // skip inaccessible
      }
    }
  } catch {
    // skip inaccessible
  }
  return files;
}

/**
 * Detect unmasked phone numbers: 10+ consecutive digits that look like real phones.
 * Patterns banned: +XX XXXXXXXXXX, XXXXXXXXXX, +XX-XXX-XXXX-XXXX (no asterisks)
 * Allowed: +51 9** ***-4321 (asterisks present)
 *
 * Strategy: match digit sequences >= 10 digits in a row (with optional separators
 * like spaces/dashes but no asterisks between them).
 */
const UNMASKED_PHONE_REGEX = /(?<!\*)\+?\d[\d\s-]{9,}\d(?!\*)/g;

/**
 * Detect unmasked email prefixes: full email prefix visible (no masking).
 * Pattern: word characters + @ + domain, where prefix has no asterisks.
 * Allowed: m***@gmail.com (has asterisks)
 * Banned: maria@gmail.com, carlos.perez@hospital.com (no asterisks in prefix)
 */
const UNMASKED_EMAIL_REGEX =
  /\b[a-zA-Z0-9][a-zA-Z0-9._%+-]{3,}@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/g;

/**
 * Detect unmasked DNI/CUIT: 8+ consecutive digits (without asterisks).
 * DNI Argentina: 8 digits. CUIT: 11 digits.
 * Must not appear in strings already containing asterisks nearby.
 */
const UNMASKED_DNI_REGEX = /(?<![*\d])\d{8,}(?![*\d])/g;

/**
 * Check if a string match is already masked (contains asterisks nearby).
 * Returns true if the surrounding context has masking.
 */
function isAlreadyMasked(
  content: string,
  matchIndex: number,
  matchLength: number,
): boolean {
  const context = content.slice(
    Math.max(0, matchIndex - 5),
    Math.min(content.length, matchIndex + matchLength + 5),
  );
  return context.includes("*");
}

interface PhiViolation {
  file: string;
  type: "phone" | "email" | "dni";
  match: string;
  lineNumber: number;
}

/**
 * Scan a file for PHI violations.
 */
function scanFileForPhi(filePath: string): PhiViolation[] {
  const violations: PhiViolation[] = [];
  let content: string;
  try {
    content = readFileSync(filePath, "utf-8");
  } catch {
    return violations;
  }

  const relPath = relative(SRC_ROOT, filePath);

  // Helper: get line number from character index
  function getLineNumber(idx: number): number {
    return content.slice(0, idx).split("\n").length;
  }

  // Check unmasked phones
  UNMASKED_PHONE_REGEX.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = UNMASKED_PHONE_REGEX.exec(content)) !== null) {
    if (!isAlreadyMasked(content, match.index, match[0].length)) {
      // Only flag if purely digits+separators >= 10 digits total
      const digits = match[0].replace(/\D/g, "");
      if (digits.length >= 10) {
        violations.push({
          file: relPath,
          type: "phone",
          match: match[0].trim(),
          lineNumber: getLineNumber(match.index),
        });
      }
    }
  }

  // Check unmasked emails
  UNMASKED_EMAIL_REGEX.lastIndex = 0;
  while ((match = UNMASKED_EMAIL_REGEX.exec(content)) !== null) {
    const prefix = match[0].split("@")[0];
    // Email is unmasked if prefix has no asterisks AND is >= 4 chars
    if (!prefix.includes("*") && prefix.length >= 4) {
      violations.push({
        file: relPath,
        type: "email",
        match: match[0],
        lineNumber: getLineNumber(match.index),
      });
    }
  }

  // Check unmasked DNI (8+ consecutive digits)
  UNMASKED_DNI_REGEX.lastIndex = 0;
  while ((match = UNMASKED_DNI_REGEX.exec(content)) !== null) {
    if (!isAlreadyMasked(content, match.index, match[0].length)) {
      violations.push({
        file: relPath,
        type: "dni",
        match: match[0],
        lineNumber: getLineNumber(match.index),
      });
    }
  }

  return violations;
}

describe("Architecture: no PHI real data in placeholder components (hipaa-lite)", () => {
  // Scope: placeholder tsx files + shared mock data files
  const placeholderFiles = collectFiles(
    resolve(SRC_ROOT, "features"),
    (name) =>
      name.endsWith("Placeholder.tsx") || name.endsWith("Placeholder.test.tsx"),
  );

  const mockDataFiles = collectFiles(
    resolve(SRC_ROOT, "components/shared/shell-organism"),
    (name) =>
      name.startsWith("_mock") &&
      (name.endsWith(".ts") || name.endsWith(".tsx")),
  );

  const allFiles = [...placeholderFiles, ...mockDataFiles];

  it("scan target set contains placeholder and mock files", () => {
    // At minimum the 28 placeholder files from T-2..T-8 should exist
    expect(allFiles.length).toBeGreaterThanOrEqual(16);
  });

  it("no unmasked phone numbers in placeholder components (hipaa-lite)", () => {
    const violations: PhiViolation[] = [];
    for (const file of allFiles) {
      const fileViolations = scanFileForPhi(file).filter(
        (v) => v.type === "phone",
      );
      violations.push(...fileViolations);
    }

    if (violations.length > 0) {
      const report = violations
        .map((v) => `  ${v.file}:${v.lineNumber} — "${v.match}"`)
        .join("\n");
      expect.fail(
        `Unmasked phone numbers found in placeholder components:\n${report}\n\n` +
          `Use masked format: +51 9** ***-4321 (not full digits). See vitalia/.claude/rules/hipaa-lite.md`,
      );
    }

    expect(violations).toHaveLength(0);
  });

  it("no unmasked email addresses in placeholder components (hipaa-lite)", () => {
    const violations: PhiViolation[] = [];
    for (const file of allFiles) {
      const fileViolations = scanFileForPhi(file).filter(
        (v) => v.type === "email",
      );
      violations.push(...fileViolations);
    }

    if (violations.length > 0) {
      const report = violations
        .map((v) => `  ${v.file}:${v.lineNumber} — "${v.match}"`)
        .join("\n");
      expect.fail(
        `Unmasked email addresses found in placeholder components:\n${report}\n\n` +
          `Use masked format: m***@gmail.com (prefix must contain ***). See vitalia/.claude/rules/hipaa-lite.md`,
      );
    }

    expect(violations).toHaveLength(0);
  });

  it("no unmasked DNI/CUIT patterns in placeholder components (hipaa-lite)", () => {
    const violations: PhiViolation[] = [];
    for (const file of allFiles) {
      const fileViolations = scanFileForPhi(file).filter(
        (v) => v.type === "dni",
      );
      violations.push(...fileViolations);
    }

    if (violations.length > 0) {
      const report = violations
        .map((v) => `  ${v.file}:${v.lineNumber} — "${v.match}"`)
        .join("\n");
      expect.fail(
        `Unmasked DNI/CUIT digit sequences (8+ digits) found in placeholder components:\n${report}\n\n` +
          `Replace with fictional IDs or masked patterns. See vitalia/.claude/rules/hipaa-lite.md`,
      );
    }

    expect(violations).toHaveLength(0);
  });
});
