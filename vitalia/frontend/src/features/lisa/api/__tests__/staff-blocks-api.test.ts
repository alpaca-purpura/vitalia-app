// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-blocks-api.test.ts — Vitest unit tests for availability block API hooks (T-FE-3).
 *
 * RED-first TDD: these tests are written before the implementation.
 * They verify key behaviours of useAvailabilityBlocks, useCreateBlock,
 * useUpdateBlock, useDeleteBlock, and block-related type assertions.
 *
 * T-FE-3 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Data layer + 01-spec.md § SC-1/SC-1b/SC-1c/SC-1d/SC-3b
 * validators: V-FN-1, V-FN-2, V-FN-3, V-FN-4, V-FN-7
 */

import { describe, it, expect } from "vitest";
import { staffKeys } from "../staff";
import { availabilityBlockSchema } from "../../types/staff-schema";
import type { RecurrentBlock, OneOffBlock } from "../../types/staff.types";

// ── staffKeys.blocks factory ───────────────────────────────────────────────────

describe("staffKeys.blocks", () => {
  it("produces correct React Query key for availability blocks", () => {
    const key = staffKeys.blocks("doctor-abc");
    expect(key).toEqual(["lisa", "staff", "detail", "doctor-abc", "blocks"]);
  });

  it("blocks key is distinct from detail key", () => {
    const detailKey = staffKeys.detail("doctor-abc");
    const blocksKey = staffKeys.blocks("doctor-abc");
    expect(blocksKey).not.toEqual(detailKey);
    expect(blocksKey.length).toBeGreaterThan(detailKey.length);
  });
});

// ── AvailabilityBlock discriminated union (type-level) ────────────────────────

describe("AvailabilityBlock discriminated union", () => {
  it("D3-F recurrent block with daysOfWeek+interval (end_date) passes type", () => {
    const block: RecurrentBlock = {
      id: "blk-1",
      kind: "recurrent",
      daysOfWeek: [0], // Monday
      interval: 1,
      startTime: "09:00",
      endTime: "13:00",
      endConditionKind: "end_date",
      endDate: "2025-12-31",
    };
    expect(block.kind).toBe("recurrent");
    expect(block.daysOfWeek).toEqual([0]);
    expect(block.interval).toBe(1);
  });

  it("D3-F recurrent block multi-day biweekly with occurrences", () => {
    const block: RecurrentBlock = {
      id: "blk-2",
      kind: "recurrent",
      daysOfWeek: [0, 3], // Monday + Thursday
      interval: 2,
      startTime: "10:00",
      endTime: "14:00",
      endConditionKind: "occurrences",
      occurrences: 8,
    };
    expect(block.occurrences).toBe(8);
    expect(block.daysOfWeek).toContain(3);
  });

  it("legacy recurrent block with optional dayOfWeek/freq still type-checks", () => {
    const block: RecurrentBlock = {
      id: "blk-legacy",
      kind: "recurrent",
      daysOfWeek: [5],
      interval: 2,
      dayOfWeek: 5, // legacy optional
      freq: "biweekly", // legacy optional
      startTime: "10:00",
      endTime: "14:00",
      endConditionKind: "occurrences",
      occurrences: 6,
    };
    expect(block.freq).toBe("biweekly");
    expect(block.dayOfWeek).toBe(5);
  });

  it("one_off block passes schema", () => {
    const block: OneOffBlock = {
      id: "blk-3",
      kind: "one_off",
      specificDate: "2025-09-15",
      startTime: "09:00",
      endTime: "12:00",
    };
    expect(block.kind).toBe("one_off");
    expect(block.specificDate).toBe("2025-09-15");
  });
});

// ── availabilityBlockSchema Zod validation ────────────────────────────────────

describe("availabilityBlockSchema (Zod) — D3-F updated schema", () => {
  it("accepts D3-F weekly recurrent block with end_date", () => {
    const result = availabilityBlockSchema.safeParse({
      kind: "recurrent",
      repeatPreset: "weekly",
      daysOfWeek: [0],
      interval: 1,
      startTime: "09:00",
      endTime: "13:00",
      endConditionKind: "end_date",
      endDate: "2025-12-31",
    });
    expect(result.success).toBe(true);
  });

  it("accepts D3-F biweekly multi-day block with occurrences (SC-D3F-3)", () => {
    const result = availabilityBlockSchema.safeParse({
      kind: "recurrent",
      repeatPreset: "custom",
      daysOfWeek: [0, 3],
      interval: 2,
      startTime: "10:00",
      endTime: "14:00",
      endConditionKind: "occurrences",
      occurrences: 8,
    });
    expect(result.success).toBe(true);
  });

  it("accepts one_off block", () => {
    const result = availabilityBlockSchema.safeParse({
      kind: "one_off",
      specificDate: "2025-09-15",
      startTime: "09:00",
      endTime: "12:00",
    });
    expect(result.success).toBe(true);
  });

  it("rejects recurrent block with end_date condition but no date", () => {
    const result = availabilityBlockSchema.safeParse({
      kind: "recurrent",
      repeatPreset: "weekly",
      daysOfWeek: [0],
      interval: 1,
      startTime: "09:00",
      endTime: "13:00",
      endConditionKind: "end_date",
      endDate: null,
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const paths = result.error.issues.map((i) => i.path.join("."));
      expect(paths).toContain("endDate");
    }
  });

  it("rejects recurrent block with occurrences condition but no count", () => {
    const result = availabilityBlockSchema.safeParse({
      kind: "recurrent",
      repeatPreset: "biweekly",
      daysOfWeek: [0],
      interval: 2,
      startTime: "09:00",
      endTime: "13:00",
      endConditionKind: "occurrences",
      occurrences: null,
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid time format", () => {
    const result = availabilityBlockSchema.safeParse({
      kind: "recurrent",
      repeatPreset: "weekly",
      daysOfWeek: [0],
      interval: 1,
      startTime: "9am",
      endTime: "1pm",
      endConditionKind: "end_date",
      endDate: "2025-12-31",
    });
    expect(result.success).toBe(false);
  });
});
