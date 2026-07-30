/**
 * conversation.test.ts — Tests for conversation Zod schemas.
 *
 * Validates: conversationSchema, messageSchema, conversationDetailSchema,
 * activityEventSchema parse valid API responses and reject invalid shapes.
 * TDD per tdd-mandatory.md: RED tests written first (T-inbox-fe-1).
 *
 * Gherkin coverage: cross-story type contracts produced (06-tickets.yaml).
 */
import { describe, it, expect } from "vitest";

import {
  conversationSchema,
  conversationChannelSchema,
  handlerModeSchema,
  messageSchema,
  actionReceiptSchema,
  toolsStateSchema,
  conversationDetailSchema,
  activityEventSchema,
  activityEventKindSchema,
  conversationListResponseSchema,
} from "../conversation";

/** Valid conversation fixture */
const validConversation = {
  id: "660e8400-e29b-41d4-a716-446655440001",
  lead_id: "550e8400-e29b-41d4-a716-446655440001",
  tenant_id: "550e8400-e29b-41d4-a716-446655440002",
  clinic_id: "550e8400-e29b-41d4-a716-446655440003",
  patient_id: null,
  channel: "whatsapp" as const,
  status: "active" as const,
  handler_mode: "ai" as const,
  proposal_required: false,
  pause_until: null,
  help_needed: false,
  help_needed_reason: null,
  unread_media_count: 0,
  last_message_at: "2026-05-19T14:30:00Z",
  last_message_preview: "Hola, quiero información sobre blanqueamiento",
  messages_count: 3,
  stage_decision: null,
  linked_offer_id: null,
  updated_at: "2026-05-19T14:30:00Z",
};

/** Valid message fixture */
const validMessage = {
  id: "770e8400-e29b-41d4-a716-446655440001",
  conversation_id: validConversation.id,
  sender_type: "patient" as const,
  sender_user_id: null,
  body_text: "Hola, quiero información sobre blanqueamiento",
  media_kind: null,
  media_url: null,
  media_duration_s: null,
  transcription_text: null,
  transcription_confidence: null,
  retracted_at: null,
  retract_succeeded: null,
  handler_mode: "ai" as const,
  sent_at: "2026-05-19T14:00:00Z",
  action_receipt_expires_at: null,
};

/** Valid lead fixture for detail response */
const validLeadDetail = {
  id: "550e8400-e29b-41d4-a716-446655440001",
  tenant_id: "550e8400-e29b-41d4-a716-446655440002",
  clinic_id: "550e8400-e29b-41d4-a716-446655440003",
  name: "María Rodríguez",
  phone: "+54 9 11 1234-5678",
  email: "maria@email.com",
  stage: "interesado" as const,
  last_conversation_id: validConversation.id,
};

describe("conversationSchema", () => {
  it("parses a valid conversation response", () => {
    const result = conversationSchema.safeParse(validConversation);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.id).toBe(validConversation.id);
      expect(result.data.handler_mode).toBe("ai");
      expect(result.data.proposal_required).toBe(false);
    }
  });

  it("parses conversation with handler_mode='human'", () => {
    const conv = { ...validConversation, handler_mode: "human" as const };
    const result = conversationSchema.safeParse(conv);
    expect(result.success).toBe(true);
  });

  it("parses conversation with proposal_required=true", () => {
    const conv = { ...validConversation, proposal_required: true };
    const result = conversationSchema.safeParse(conv);
    expect(result.success).toBe(true);
  });

  it("rejects invalid channel value", () => {
    const conv = { ...validConversation, channel: "tiktok" };
    const result = conversationSchema.safeParse(conv);
    expect(result.success).toBe(false);
  });

  it("rejects invalid status value", () => {
    const conv = { ...validConversation, status: "open" };
    const result = conversationSchema.safeParse(conv);
    expect(result.success).toBe(false);
  });

  it("rejects negative unread_media_count", () => {
    const conv = { ...validConversation, unread_media_count: -1 };
    const result = conversationSchema.safeParse(conv);
    expect(result.success).toBe(false);
  });

  it("updated_at is valid ISO datetime (OCC ETag)", () => {
    const result = conversationSchema.safeParse(validConversation);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.updated_at).toBe("2026-05-19T14:30:00Z");
    }
  });
});

describe("conversationChannelSchema", () => {
  it("accepts all 6 valid channel values", () => {
    const channels = [
      "whatsapp",
      "instagram",
      "facebook_messenger",
      "web",
      "walk_in",
      "phone",
    ] as const;
    channels.forEach((ch) => {
      expect(conversationChannelSchema.safeParse(ch).success).toBe(true);
    });
  });
});

describe("handlerModeSchema", () => {
  it("accepts 'ai' and 'human'", () => {
    expect(handlerModeSchema.safeParse("ai").success).toBe(true);
    expect(handlerModeSchema.safeParse("human").success).toBe(true);
  });

  it("rejects other values", () => {
    expect(handlerModeSchema.safeParse("both").success).toBe(false);
  });
});

describe("messageSchema", () => {
  it("parses a valid text message", () => {
    const result = messageSchema.safeParse(validMessage);
    expect(result.success).toBe(true);
  });

  it("parses an audio message with transcription", () => {
    const audioMsg = {
      ...validMessage,
      body_text: null,
      media_kind: "audio" as const,
      media_url: "https://cdn.vitalia.com/audio/123.ogg",
      media_duration_s: 12.5,
      transcription_text: "Hola, quiero info",
      transcription_confidence: 0.93,
    };
    const result = messageSchema.safeParse(audioMsg);
    expect(result.success).toBe(true);
  });

  it("parses a retracted message", () => {
    const retracted = {
      ...validMessage,
      retracted_at: "2026-05-19T14:01:00Z",
      retract_succeeded: true,
    };
    const result = messageSchema.safeParse(retracted);
    expect(result.success).toBe(true);
  });

  it("parses message with action receipt (ai message with undo window)", () => {
    const aiMsg = {
      ...validMessage,
      sender_type: "agent_ai" as const,
      action_receipt_expires_at: "2026-05-19T14:05:00Z",
    };
    const result = messageSchema.safeParse(aiMsg);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.action_receipt_expires_at).toBe(
        "2026-05-19T14:05:00Z",
      );
    }
  });

  it("rejects transcription_confidence > 1", () => {
    const msg = { ...validMessage, transcription_confidence: 1.5 };
    const result = messageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });

  it("rejects negative media_duration_s", () => {
    const msg = { ...validMessage, media_duration_s: -1 };
    const result = messageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});

describe("actionReceiptSchema", () => {
  it("parses a valid action receipt", () => {
    const receipt = {
      message_id: "770e8400-e29b-41d4-a716-446655440001",
      expires_at: "2026-05-19T14:05:00Z",
    };
    const result = actionReceiptSchema.safeParse(receipt);
    expect(result.success).toBe(true);
  });

  it("rejects invalid message_id UUID", () => {
    const receipt = {
      message_id: "not-uuid",
      expires_at: "2026-05-19T14:05:00Z",
    };
    const result = actionReceiptSchema.safeParse(receipt);
    expect(result.success).toBe(false);
  });
});

describe("toolsStateSchema", () => {
  it("parses a valid tools state with invocations", () => {
    const toolsState = {
      conversation_id: validConversation.id,
      invocations: [
        {
          tool_name: "schedule_appointment",
          invoked_at: "2026-05-19T14:10:00Z",
          status: "success" as const,
          result_summary: "Cita agendada para martes 12:00",
        },
      ],
      updated_at: "2026-05-19T14:10:00Z",
    };
    const result = toolsStateSchema.safeParse(toolsState);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.invocations).toHaveLength(1);
    }
  });

  it("parses empty invocations array", () => {
    const toolsState = {
      conversation_id: validConversation.id,
      invocations: [],
      updated_at: "2026-05-19T14:00:00Z",
    };
    const result = toolsStateSchema.safeParse(toolsState);
    expect(result.success).toBe(true);
  });
});

describe("conversationDetailSchema", () => {
  it("parses a valid full conversation detail response", () => {
    const detail = {
      conversation: validConversation,
      lead: validLeadDetail,
      messages: [validMessage],
      action_receipts: [],
      tools_state: null,
    };
    const result = conversationDetailSchema.safeParse(detail);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.messages).toHaveLength(1);
      expect(result.data.tools_state).toBeNull();
    }
  });

  it("parses detail with action receipts", () => {
    const detail = {
      conversation: { ...validConversation, handler_mode: "ai" as const },
      lead: validLeadDetail,
      messages: [
        {
          ...validMessage,
          sender_type: "agent_ai" as const,
          action_receipt_expires_at: "2026-05-19T14:05:00Z",
        },
      ],
      action_receipts: [
        { message_id: validMessage.id, expires_at: "2026-05-19T14:05:00Z" },
      ],
      tools_state: null,
    };
    const result = conversationDetailSchema.safeParse(detail);
    expect(result.success).toBe(true);
  });
});

describe("activityEventSchema", () => {
  it("parses a valid activity event", () => {
    const event = {
      id: "880e8400-e29b-41d4-a716-446655440001",
      conversation_id: validConversation.id,
      kind: "tool_call" as const,
      summary: "Adrián consultó precio de Blanqueamiento Premium ($24.000)",
      payload_redacted: { tool: "get_pricing", result_ok: true },
      occurred_at: "2026-05-19T14:21:00Z",
    };
    const result = activityEventSchema.safeParse(event);
    expect(result.success).toBe(true);
  });

  it("accepts null payload_redacted", () => {
    const event = {
      id: "880e8400-e29b-41d4-a716-446655440001",
      conversation_id: validConversation.id,
      kind: "turn_start" as const,
      summary: "Adrián comenzó turno",
      payload_redacted: null,
      occurred_at: "2026-05-19T14:00:00Z",
    };
    const result = activityEventSchema.safeParse(event);
    expect(result.success).toBe(true);
  });

  it("rejects invalid kind value", () => {
    const event = {
      id: "880e8400-e29b-41d4-a716-446655440001",
      conversation_id: validConversation.id,
      kind: "unknown_event",
      summary: "Unknown",
      payload_redacted: null,
      occurred_at: "2026-05-19T14:00:00Z",
    };
    const result = activityEventSchema.safeParse(event);
    expect(result.success).toBe(false);
  });
});

describe("activityEventKindSchema", () => {
  it("accepts all 10 valid event kind values", () => {
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
      expect(activityEventKindSchema.safeParse(kind).success).toBe(true);
    });
  });
});

describe("conversationListResponseSchema", () => {
  it("parses a valid paginated conversation list", () => {
    const response = {
      items: [validConversation],
      total: 1,
      page: 1,
      page_size: 20,
    };
    const result = conversationListResponseSchema.safeParse(response);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.items).toHaveLength(1);
    }
  });

  it("accepts empty conversation list", () => {
    const response = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    };
    const result = conversationListResponseSchema.safeParse(response);
    expect(result.success).toBe(true);
  });
});
