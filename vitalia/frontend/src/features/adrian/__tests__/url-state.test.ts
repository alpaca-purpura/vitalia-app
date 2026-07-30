/**
 * url-state.test.ts — Tests for inbox URL state schema.
 *
 * Validates: INBOX_URL_SCHEMA parser configurations + useInboxUrlState hook type.
 * TDD per tdd-mandatory.md: RED tests written first (T-inbox-fe-1).
 *
 * Gherkin coverage: SC-01 URL state parsing (06-tickets.yaml::gherkin_coverage).
 */
import { describe, it, expect } from "vitest";

import {
  INBOX_URL_SCHEMA,
  type InboxUrlState,
  type InboxChannelFilter,
  type InboxStatusFilter,
  type InboxStageFilter,
  type InboxModeFilter,
  type InboxPeriodFilter,
} from "../lib/url-state";

describe("INBOX_URL_SCHEMA", () => {
  it("exports the schema as a const object", () => {
    expect(INBOX_URL_SCHEMA).toBeDefined();
    expect(typeof INBOX_URL_SCHEMA).toBe("object");
  });

  it("has all 9 expected keys", () => {
    const keys = Object.keys(INBOX_URL_SCHEMA);
    expect(keys).toContain("conv");
    expect(keys).toContain("channel");
    expect(keys).toContain("status");
    expect(keys).toContain("stage");
    expect(keys).toContain("mode");
    expect(keys).toContain("period");
    expect(keys).toContain("helpNeeded");
    expect(keys).toContain("unreadMedia");
    expect(keys).toContain("search");
    expect(keys).toHaveLength(9);
  });

  it("conv parser has parseServerSide method (nuqs parser contract)", () => {
    expect(typeof INBOX_URL_SCHEMA.conv.parseServerSide).toBe("function");
  });

  it("channel parser parses valid channel values", () => {
    const validChannels: InboxChannelFilter[] = [
      "whatsapp",
      "instagram",
      "email",
    ];
    validChannels.forEach((channel) => {
      const result = INBOX_URL_SCHEMA.channel.parseServerSide(channel);
      expect(result).toBe(channel);
    });
  });

  it("channel parser returns null for invalid channel", () => {
    // tiktok/telegram/facebook are valid channels now; use a non-channel value.
    const result = INBOX_URL_SCHEMA.channel.parseServerSide("snapchat");
    expect(result).toBeNull();
  });

  it("status parser parses valid status values", () => {
    const validStatuses: InboxStatusFilter[] = [
      "active",
      "waiting-deposit",
      "nps-pending",
      "closed",
    ];
    validStatuses.forEach((status) => {
      const result = INBOX_URL_SCHEMA.status.parseServerSide(status);
      expect(result).toBe(status);
    });
  });

  it("stage parser parses valid stage values", () => {
    const validStages: InboxStageFilter[] = [
      "interested",
      "considering",
      "ready-to-book",
      "decided-no",
    ];
    validStages.forEach((stage) => {
      const result = INBOX_URL_SCHEMA.stage.parseServerSide(stage);
      expect(result).toBe(stage);
    });
  });

  it("mode parser parses valid mode values", () => {
    const validModes: InboxModeFilter[] = [
      "adrian-decide",
      "adrian-consulta",
      "yo-escribo",
    ];
    validModes.forEach((mode) => {
      const result = INBOX_URL_SCHEMA.mode.parseServerSide(mode);
      expect(result).toBe(mode);
    });
  });

  it("period parser parses valid period values", () => {
    const validPeriods: InboxPeriodFilter[] = [
      "today",
      "yesterday",
      "week",
      "month",
    ];
    validPeriods.forEach((period) => {
      const result = INBOX_URL_SCHEMA.period.parseServerSide(period);
      expect(result).toBe(period);
    });
  });

  it("helpNeeded parser parses 'true' string to boolean true", () => {
    const result = INBOX_URL_SCHEMA.helpNeeded.parseServerSide("true");
    expect(result).toBe(true);
  });

  it("helpNeeded parser parses 'false' string to boolean false", () => {
    const result = INBOX_URL_SCHEMA.helpNeeded.parseServerSide("false");
    expect(result).toBe(false);
  });

  it("unreadMedia parser parses 'true' string to boolean true", () => {
    const result = INBOX_URL_SCHEMA.unreadMedia.parseServerSide("true");
    expect(result).toBe(true);
  });

  it("search parser returns null for undefined input", () => {
    const result = INBOX_URL_SCHEMA.search.parseServerSide(undefined);
    expect(result).toBeNull();
  });

  it("search parser returns string value when present", () => {
    const result = INBOX_URL_SCHEMA.search.parseServerSide("maría rodríguez");
    expect(result).toBe("maría rodríguez");
  });

  it("lead parser returns null for undefined input", () => {
    const result = INBOX_URL_SCHEMA.conv.parseServerSide(undefined);
    expect(result).toBeNull();
  });

  it("lead parser returns UUID string when valid", () => {
    const uuid = "550e8400-e29b-41d4-a716-446655440000";
    const result = INBOX_URL_SCHEMA.conv.parseServerSide(uuid);
    expect(result).toBe(uuid);
  });
});

/**
 * Type-level tests (compile-time assertions via TypeScript).
 * These will fail to compile if types are wrong — validates type contracts.
 */
describe("InboxUrlState type contract", () => {
  it("InboxUrlState type matches schema keys", () => {
    // Type-level assertion: verify the type satisfies the expected shape
    const state: InboxUrlState = {
      conv: null,
      channel: null,
      status: null,
      stage: null,
      mode: null,
      period: null,
      helpNeeded: null,
      unreadMedia: null,
      search: null,
    };
    expect(state.conv).toBeNull();
    expect(state.channel).toBeNull();
  });
});
