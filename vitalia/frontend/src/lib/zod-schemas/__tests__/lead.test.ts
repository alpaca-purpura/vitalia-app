/**
 * lead.test.ts — Tests for lead Zod schema runtime validation.
 *
 * Validates: leadSchema parses valid API responses, rejects invalid shapes,
 * and provides correct inferred types.
 * TDD per tdd-mandatory.md: RED tests written first (T-inbox-fe-1).
 *
 * Gherkin coverage: cross-story type contracts produced (06-tickets.yaml).
 */
import { describe, it, expect } from "vitest";

import {
  leadSchema,
  leadStageSchema,
  leadOriginSchema,
  leadListResponseSchema,
} from "../lead";

/** Valid lead fixture */
const validLead = {
  id: "550e8400-e29b-41d4-a716-446655440001",
  tenant_id: "550e8400-e29b-41d4-a716-446655440002",
  clinic_id: "550e8400-e29b-41d4-a716-446655440003",
  name: "María Rodríguez",
  phone: "+54 9 11 1234-5678",
  email: "maria.rodriguez@email.com",
  stage: "interesado" as const,
  attribution: {
    origin: "sales_agent" as const,
    channel: "whatsapp",
    attributed_at: "2026-05-19T14:00:00Z",
  },
  last_conversation_id: "550e8400-e29b-41d4-a716-446655440004",
  created_at: "2026-05-19T10:00:00Z",
  updated_at: "2026-05-19T14:30:00Z",
};

describe("leadSchema", () => {
  it("parses a valid lead response", () => {
    const result = leadSchema.safeParse(validLead);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.id).toBe(validLead.id);
      expect(result.data.name).toBe("María Rodríguez");
      expect(result.data.stage).toBe("interesado");
    }
  });

  it("accepts null phone", () => {
    const lead = { ...validLead, phone: null };
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(true);
  });

  it("accepts null email", () => {
    const lead = { ...validLead, email: null };
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(true);
  });

  it("accepts null last_conversation_id", () => {
    const lead = { ...validLead, last_conversation_id: null };
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(true);
  });

  it("rejects invalid UUID for id", () => {
    const lead = { ...validLead, id: "not-a-uuid" };
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(false);
  });

  it("rejects invalid stage value", () => {
    const lead = { ...validLead, stage: "unknown_stage" };
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(false);
  });

  it("rejects missing required field (tenant_id)", () => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars -- intentional omission for test
    const { tenant_id, ...lead } = validLead;
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(false);
  });

  it("rejects missing clinic_id", () => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars -- intentional omission for test
    const { clinic_id, ...lead } = validLead;
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(false);
  });

  it("rejects empty name", () => {
    const lead = { ...validLead, name: "" };
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(false);
  });

  it("validates invalid ISO 8601 datetime string", () => {
    const lead = { ...validLead, created_at: "not-a-date" };
    const result = leadSchema.safeParse(lead);
    expect(result.success).toBe(false);
  });
});

describe("leadStageSchema", () => {
  it("accepts all 6 valid stage values", () => {
    const stages = [
      "interesado",
      "calificando",
      "considerando",
      "listo",
      "reservado_deposito",
      "decidio_no",
    ] as const;
    stages.forEach((stage) => {
      const result = leadStageSchema.safeParse(stage);
      expect(result.success).toBe(true);
    });
  });

  it("rejects invalid stage", () => {
    const result = leadStageSchema.safeParse("activo");
    expect(result.success).toBe(false);
  });
});

describe("leadOriginSchema", () => {
  it("accepts all 4 valid origin values", () => {
    const origins = [
      "sales_agent",
      "walk_in",
      "phone_manual",
      "proactive_outbound",
    ] as const;
    origins.forEach((origin) => {
      const result = leadOriginSchema.safeParse(origin);
      expect(result.success).toBe(true);
    });
  });
});

describe("leadListResponseSchema", () => {
  it("parses a valid paginated response", () => {
    const response = {
      items: [validLead],
      total: 1,
      page: 1,
      page_size: 20,
    };
    const result = leadListResponseSchema.safeParse(response);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.items).toHaveLength(1);
      expect(result.data.total).toBe(1);
    }
  });

  it("accepts empty items array", () => {
    const response = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    };
    const result = leadListResponseSchema.safeParse(response);
    expect(result.success).toBe(true);
  });

  it("rejects negative total", () => {
    const response = {
      items: [],
      total: -1,
      page: 1,
      page_size: 20,
    };
    const result = leadListResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });
});
