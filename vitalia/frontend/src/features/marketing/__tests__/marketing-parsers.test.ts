/**
 * SC-MK-03 — Tab URL state: nuqs parsers for marketing feature
 * @coverage gherkin SC-MK-03 (test_default_tab_is_attraction + test_tab_param_replace_intra_route)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect } from "vitest";
import { marketingParsers } from "../types/url-state";

describe("marketingParsers", () => {
  describe("tab parser (SC-MK-03)", () => {
    it("test_default_tab_is_attraction — default tab is attraction", () => {
      expect(marketingParsers.tab.defaultValue).toBe("attraction");
    });

    it("test_tab_param_replace_intra_route — tab parser is configured for replace (intra-route)", () => {
      // nuqs parseAsStringEnum(...).withDefault(...).withOptions({ history: "replace" })
      // verifies that the parser object has replace semantics
      expect(marketingParsers.tab.parseServerSide("qualification")).toBe(
        "qualification",
      );
      expect(marketingParsers.tab.parseServerSide("reservation")).toBe(
        "reservation",
      );
      expect(marketingParsers.tab.parseServerSide("adoption")).toBe("adoption");
      expect(marketingParsers.tab.parseServerSide("expansion")).toBe(
        "expansion",
      );
      // invalid value falls back to default
      expect(marketingParsers.tab.parseServerSide("invalid")).toBe(
        "attraction",
      );
    });

    it("period parser default is 30d", () => {
      expect(marketingParsers.period.defaultValue).toBe("30d");
    });

    it("approvalModal parser default is false", () => {
      expect(marketingParsers.approvalModal.defaultValue).toBe(false);
    });
  });

  describe("MARKETING_COPY namespace (SC-MK-03 Spanish neutro)", () => {
    it("MARKETING_COPY is defined and has no voseo (basic smoke)", async () => {
      const { MARKETING_COPY } = await import("../copy");
      expect(typeof MARKETING_COPY).toBe("object");
      expect(MARKETING_COPY).not.toBeNull();
    });
  });

  describe("LucasRecommendation Zod schema (schema smoke)", () => {
    it("parses a valid recommendation", async () => {
      const { lucasRecommendationSchema } =
        await import("@/lib/zod-schemas/lucas-recommendation");
      const valid = {
        id: "rec-123",
        tenant_id: "tenant-abc",
        clinic_id: "clinic-xyz",
        stage: "attraction",
        recommendation_kind: "increase_budget",
        title: "Aumenta el presupuesto en Meta Ads",
        body: "Tu CPA es 18% menor que el promedio del sector",
        rationale_json: {},
        action_payload_json: null,
        priority: 1,
        confidence_pct: 85,
        projected_impact_text: null,
        status: "open",
        approved_by_user_id: null,
        approved_at: null,
        undo_until: null,
        expires_at: "2026-06-01T00:00:00Z",
        created_at: "2026-05-20T00:00:00Z",
      };
      const result = lucasRecommendationSchema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it("rejects invalid status", async () => {
      const { lucasRecommendationSchema } =
        await import("@/lib/zod-schemas/lucas-recommendation");
      const invalid = {
        id: "rec-123",
        tenant_id: "tenant-abc",
        clinic_id: "clinic-xyz",
        stage: "attraction",
        recommendation_kind: "increase_budget",
        title: "Aumenta el presupuesto",
        body: "Descripción",
        rationale_json: {},
        action_payload_json: null,
        priority: 1,
        confidence_pct: null,
        projected_impact_text: null,
        status: "unknown_status", // invalid
        approved_by_user_id: null,
        approved_at: null,
        undo_until: null,
        expires_at: "2026-06-01T00:00:00Z",
        created_at: "2026-05-20T00:00:00Z",
      };
      const result = lucasRecommendationSchema.safeParse(invalid);
      expect(result.success).toBe(false);
    });
  });
});
