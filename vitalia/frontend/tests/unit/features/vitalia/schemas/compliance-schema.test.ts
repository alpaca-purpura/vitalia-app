import { describe, it, expect } from "vitest";
import { complianceFilterSchema } from "@/features/vitalia/schemas/compliance-schema";

describe("complianceFilterSchema", () => {
  it("accepts empty filter (all optional)", () => {
    const result = complianceFilterSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it("accepts valid severity filter", () => {
    const result = complianceFilterSchema.safeParse({
      severity: "high",
      page: 1,
      page_size: 20,
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid severity", () => {
    const result = complianceFilterSchema.safeParse({
      severity: "critical",
    });
    expect(result.success).toBe(false);
  });

  it("rejects page_size above 100", () => {
    const result = complianceFilterSchema.safeParse({
      page_size: 200,
    });
    expect(result.success).toBe(false);
  });

  it("accepts date range filter", () => {
    const result = complianceFilterSchema.safeParse({
      date_from: "2026-01-01",
      date_to: "2026-06-01",
    });
    expect(result.success).toBe(true);
  });
});
