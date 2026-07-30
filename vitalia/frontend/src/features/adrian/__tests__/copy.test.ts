/**
 * copy.test.ts — Tests for INBOX_COPY microcopy constants.
 *
 * Validates: Spanish neutro LatAm (no voseo), completeness of copy object,
 * and formatCopy interpolation utility.
 * TDD per tdd-mandatory.md: RED tests written first (T-inbox-fe-1).
 *
 * Gherkin coverage: spanish_neutro_voseo_check (04-validators.yaml).
 */
import { describe, it, expect } from "vitest";

import { INBOX_COPY } from "../lib/copy";
import { formatCopy } from "@/lib/copy";

/** Voseo forms to detect (per spanish-text.md § R2 glosario) */
const VOSEO_PATTERNS = [
  /\bvos\b/i,
  /\bsos\b/i,
  /\btenés\b/i,
  /\bpodés\b/i,
  /\bquería\b/i,
  /\bmirá\b/i,
  /\bdejá\b/i,
  /\bponé\b/i,
  /\busá\b/i,
  /\bhacé\b/i,
  /\belegí\b/i,
  /\bagregá\b/i,
  /\bconfigurá\b/i,
  /\brevisá\b/i,
  /\bescribí\b/i,
  /\bguardá\b/i,
  /\babrí\b/i,
  /\bvolvé\b/i,
  /\bcambiá\b/i,
];

/** Flatten INBOX_COPY to an array of all string leaf values */
function flattenCopyStrings(
  obj: unknown,
  path = "",
): Array<{ path: string; value: string }> {
  if (typeof obj === "string") {
    return [{ path, value: obj }];
  }
  if (typeof obj === "object" && obj !== null) {
    return Object.entries(obj as Record<string, unknown>).flatMap(
      ([key, val]) => flattenCopyStrings(val, path ? `${path}.${key}` : key),
    );
  }
  return [];
}

describe("INBOX_COPY", () => {
  it("is defined and is an object", () => {
    expect(INBOX_COPY).toBeDefined();
    expect(typeof INBOX_COPY).toBe("object");
  });

  it("has pageTitle 'Inbox'", () => {
    expect(INBOX_COPY.pageTitle).toBe("Inbox");
  });

  it("has all required top-level sections", () => {
    const sections = [
      "empty",
      "filters",
      "segmentedMode",
      "composerDock",
      "pauseAgent",
      "composer",
      "multimedia",
      "toolsSheet",
      "activityStream",
      "actionReceipt",
      "contactSidebar",
      "helpNeededBanner",
      "proposalCardBanner",
      "proactiveOutboundModal",
      "errors",
    ];
    sections.forEach((section) => {
      expect(INBOX_COPY).toHaveProperty(section);
    });
  });

  it("empty.noConversations has heading and body", () => {
    expect(INBOX_COPY.empty.noConversations.heading).toBeTruthy();
    expect(INBOX_COPY.empty.noConversations.body).toBeTruthy();
  });

  it("empty.noResultsFilter has cta", () => {
    expect(INBOX_COPY.empty.noResultsFilter.cta).toBeTruthy();
  });

  it("segmentedMode has both mode labels (2 modos · Chris UI #3)", () => {
    expect(INBOX_COPY.segmentedMode.adrianDecide).toBeTruthy();
    expect(INBOX_COPY.segmentedMode.adrianConsulta).toBeTruthy();
  });

  it("activityStream.eventKinds has all 10 event kind labels", () => {
    const kinds = [
      "tool_call",
      "llm_call",
      "turn_start",
      "turn_end",
      "proposal_generated",
      "mode_changed",
      "message_sent",
      "message_retracted",
      "adrian_paused",
      "compliance_blocked",
    ] as const;
    kinds.forEach((kind) => {
      expect(INBOX_COPY.activityStream.eventKinds[kind]).toBeTruthy();
    });
  });

  describe("Spanish neutro — NO voseo (spanish-text.md § R2)", () => {
    const allStrings = flattenCopyStrings(INBOX_COPY);

    it("has copy strings to check", () => {
      expect(allStrings.length).toBeGreaterThan(0);
    });

    VOSEO_PATTERNS.forEach((pattern) => {
      it(`no copy string matches voseo pattern ${pattern}`, () => {
        const violations = allStrings.filter(({ value }) =>
          pattern.test(value),
        );
        expect(violations).toEqual([]);
      });
    });
  });

  it("all string values are non-empty", () => {
    const allStrings = flattenCopyStrings(INBOX_COPY);
    const empty = allStrings.filter(({ value }) => value.trim() === "");
    expect(empty).toEqual([]);
  });
});

describe("formatCopy (lib/copy.ts)", () => {
  it("interpolates a single variable", () => {
    const result = formatCopy("Hola {name}", { name: "María" });
    expect(result).toBe("Hola María");
  });

  it("interpolates multiple variables", () => {
    const result = formatCopy("Escribe a {patient} en {channel}", {
      patient: "Juan",
      channel: "WhatsApp",
    });
    expect(result).toBe("Escribe a Juan en WhatsApp");
  });

  it("leaves unknown keys as-is", () => {
    const result = formatCopy("Hola {unknown}", { name: "María" });
    expect(result).toBe("Hola {unknown}");
  });

  it("returns template unchanged when no vars provided", () => {
    const result = formatCopy("Sin variables", {});
    expect(result).toBe("Sin variables");
  });

  it("works with composer placeholder template", () => {
    const result = formatCopy(INBOX_COPY.composer.placeholder.yoEscribo, {
      patient_name: "Rosa López",
    });
    expect(result).toContain("Rosa López");
  });
});
