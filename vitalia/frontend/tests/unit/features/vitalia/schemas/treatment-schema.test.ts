import { describe, it, expect } from "vitest";
import { startFollowupSchema } from "@/features/vitalia/schemas/treatment-schema";

describe("startFollowupSchema", () => {
  it("accepts valid start followup data", () => {
    const result = startFollowupSchema.safeParse({
      plan_template_slug: "dental_implant",
      procedure_date: "2026-06-15T14:00:00Z",
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty plan_template_slug", () => {
    const result = startFollowupSchema.safeParse({
      plan_template_slug: "",
      procedure_date: "2026-06-15T14:00:00Z",
    });
    expect(result.success).toBe(false);
  });

  it("rejects plan_template_slug longer than 64 chars", () => {
    const result = startFollowupSchema.safeParse({
      plan_template_slug: "a".repeat(65),
      procedure_date: "2026-06-15T14:00:00Z",
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing procedure_date", () => {
    const result = startFollowupSchema.safeParse({
      plan_template_slug: "dental_implant",
    });
    expect(result.success).toBe(false);
  });
});
